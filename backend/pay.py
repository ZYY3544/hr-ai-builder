"""作品评审收费：微信 Native 扫码支付（2026-09-08，从 meansights 主站移植的同一套安全闸）。

端点：
  GET  /api/pay/config           支付是否开通（凭证没配要如实说，不能让人点了才发现）
  POST /api/pay/order            登录用户下单 → {out_trade_no, code_url, qr_svg, yuan}
  GET  /api/pay/order/{no}       前端轮询（读自己库 + probe=1 时主动问微信）
  POST /api/pay/notify           微信回调（无鉴权，靠验签）

三道闸一条不少：回调验签 → 金额与订单核对 → 幂等（只认 pending 行）。
档位在服务端定义，绝不接受前端传金额。
"""
import json
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import auth
import store as _store
import wechat_pay as wxp
from ratelimit import client_ip, hit

router = APIRouter()

# 档位（元）。首次免费的判定在 main.py 的 review_apply 里，这里只管收钱。
TIERS = {
    "review:report": {"yuan": 50,  "desc": "meansights 作品评审 · 评估报告"},
    "review:agent":  {"yuan": 0.01, "desc": "meansights 作品评审 · 报告 + 重构版 Agent"},   # ⚠️ 临时联调价，验完必须改回 300
}
_EXPIRE_S = 15 * 60


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _age_s(rec: dict) -> float:
    try:
        t = datetime.fromisoformat(str(rec.get("created_at", "")).replace("Z", "+00:00"))
        return (_now() - t).total_seconds()
    except Exception:
        return 0.0


def _qr_svg(text: str) -> str:
    """把 code_url 渲染成 SVG 二维码字符串——前端用 data: URI 塞进 <img>，不引任何 JS 库。"""
    import qrcode
    from qrcode.image.svg import SvgPathImage
    img = qrcode.make(text, image_factory=SvgPathImage, box_size=10, border=2)
    return img.to_string(encoding="unicode")


class OrderIn(BaseModel):
    kind: str = Field("review", max_length=16)
    tier: str = Field(..., max_length=16)


@router.get("/api/pay/config")
def pay_config():
    ok, missing = wxp.is_configured()
    return {"enabled": ok, "tiers": {k.split(":")[1]: v["yuan"] for k, v in TIERS.items()
                                   if k.startswith("review:")},
            **({} if ok else {"reason": "支付通道尚未开通"})}


@router.post("/api/pay/order")
def create_order(body: OrderIn, request: Request, user: dict = Depends(auth.current_user)):
    ok, _missing = wxp.is_configured()
    if not ok:
        raise HTTPException(503, "支付通道还没开通，请先把作品链接发到邮箱，我们人工处理")
    if hit("pay_order", user["openid"], 6, 600):
        raise HTTPException(429, "下单太频繁，用之前的二维码或稍后再试")
    tier = TIERS.get(f"{body.kind}:{body.tier}")
    if not tier:
        raise HTTPException(400, "bad_tier")
    uid = user["openid"]
    no = wxp.gen_out_trade_no(uid)
    amount_fen = int(round(tier["yuan"] * 100))
    # 先落 pending 单再去微信下单：回调可能比下单响应先到，库里没单会对不上账
    _store.store.add(_store.ORDER, {
        "out_trade_no": no, "created_at": _store.now_iso(), "openid": uid,
        "kind": body.kind, "tier": body.tier, "amount_fen": amount_fen,
        "status": "pending", "used": False, "nick": (user.get("nickname") or "")[:64],
    })
    res = wxp.create_native_order(no, amount_fen, tier["desc"])
    if res.get("error"):
        raise HTTPException(502, res["error"])
    _store.store.update(_store.ORDER, {"out_trade_no": no}, {"code_url": res["code_url"]})
    return {"out_trade_no": no, "code_url": res["code_url"], "qr_svg": _qr_svg(res["code_url"]),
            "yuan": tier["yuan"], "expire_s": _EXPIRE_S}


def _settle(no: str, detail: dict, via: str) -> bool:
    """微信说这单成了 → 标 paid。金额核对 + 幂等（只改 status=pending 的行，回调与查单并发也只成一次）。"""
    paid_fen = ((detail.get("amount") or {}).get("payer_total")
                or (detail.get("amount") or {}).get("total"))
    rows = _store.store.find(_store.ORDER, {"out_trade_no": no}, 1)
    if not rows:
        print(f"[pay] {via}：找不到订单 {no}", flush=True)
        return False
    row = rows[0]
    if int(paid_fen or 0) != int(row.get("amount_fen") or -1):
        print(f"[pay] 🔴 {via}金额不符 {no} 微信={paid_fen} 本地={row.get('amount_fen')}，拒绝", flush=True)
        return False
    n = _store.store.update(_store.ORDER, {"out_trade_no": no, "status": "pending"},
                            {"status": "paid", "transaction_id": detail.get("transaction_id"),
                             "paid_at": _store.now_iso()})
    if n:
        print(f"[pay] ✅ {via}到账 {no} user={row.get('openid')} ¥{int(row.get('amount_fen') or 0)/100:.0f}", flush=True)
    return bool(n)


@router.get("/api/pay/order/{no}")
def order_status(no: str, request: Request, probe: int = 0, user: dict = Depends(auth.current_user)):
    rows = _store.store.find(_store.ORDER, {"out_trade_no": no}, 1)
    if not rows or rows[0].get("openid") != user["openid"]:
        raise HTTPException(404, "not_found")
    row = rows[0]
    status, scanned = row.get("status"), False
    age = _age_s(row)
    if status == "pending":
        if age > _EXPIRE_S + 60:
            status = "closed"
        elif (probe == 1 and age > 5) or age > 60:
            q = wxp.query_order(no) or {}
            ts = q.get("trade_state")
            if ts == "SUCCESS" and _settle(no, q, "查单"):
                status = "paid"
            elif ts == "USERPAYING":
                scanned = True
    return {"status": status, "scanned": scanned, "yuan": int(row.get("amount_fen") or 0) // 100,
            "used": bool(row.get("used"))}


@router.post("/api/pay/notify")
async def notify(request: Request):
    body_bytes = await request.body()
    if not wxp.verify_notify(request.headers, body_bytes):
        return JSONResponse({"code": "FAIL", "message": "签名验证失败"}, status_code=401)
    try:
        body = json.loads(body_bytes or b"{}")
    except ValueError:
        return JSONResponse({"code": "FAIL", "message": "报文异常"}, status_code=400)
    detail = wxp.decrypt_notify(body)
    if not detail:
        return JSONResponse({"code": "FAIL", "message": "解密失败"}, status_code=400)
    if detail.get("trade_state") != "SUCCESS":
        return {"code": "SUCCESS"}                 # 非成功态也回 200，别让微信重推
    _settle(str(detail.get("out_trade_no") or ""), detail, "回调")
    return {"code": "SUCCESS"}                     # 已处理过/金额不符也回 200（日志里有记录），重推无意义


def order_paid_for(no: str, uid: str, kind: str, tier: str) -> Optional[dict]:
    """给 review_apply 用：这张单是本人的、已付、档位对、还没用过 → 返回订单行，否则 None。"""
    rows = _store.store.find(_store.ORDER, {"out_trade_no": no}, 1)
    if not rows:
        return None
    r = rows[0]
    if r.get("openid") != uid or r.get("status") != "paid" or r.get("used"):
        return None
    if r.get("kind") != kind or r.get("tier") != tier:
        return None
    return r


def mark_used(no: str, application: dict) -> None:
    _store.store.update(_store.ORDER, {"out_trade_no": no, "used": False},
                        {"used": True, "application": application})
