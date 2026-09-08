# -*- coding: utf-8 -*-
"""微信支付 v3 · Native 扫码支付（从 meansights 主站原样移植，2026-09-08；主站 2026-08-09 已真钱验证）。

形态：网页展示二维码 → 用户微信扫码付款 → 微信回调我们 → 到账 credits → 前端轮询到"已支付"。

为什么自己实现而不装 SDK：只用到 3 个接口（下单/查单/回调验签），官方 SDK 依赖重、
更新慢；签名逻辑本身是标准 RSA-SHA256 + AES-GCM，cryptography 已经在依赖里。

安全约束（这是收钱的代码，每条都别省）：
  ① 回调【必须】验签——不验就等于任何人 POST 一个 JSON 过来就能白拿 credits
  ② 回调金额【必须】与订单表核对——防止改金额（付 1 分拿 300 元的额度）
  ③ 到账【必须】幂等——微信会重复推送同一笔，status 做闸
  ④ 私钥/APIv3 密钥只从环境变量读，绝不落代码、绝不进日志

凭证（全部走 Render 环境变量，见 is_configured()）：
  WXPAY_MCHID          商户号（10 位数字）
  WXPAY_APPID          绑定的 AppID（小程序/公众号，商户平台里关联过的那个）
  WXPAY_API_V3_KEY     APIv3 密钥（商户平台自己设的 32 位字符串）
  WXPAY_CERT_SERIAL    商户 API 证书序列号
  WXPAY_PRIVATE_KEY    apiclient_key.pem 的内容（整段，含 BEGIN/END 行）
  WXPAY_NOTIFY_URL     回调地址（https://<后端域名>/api/pay/notify）
"""
import base64
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_API_BASE = 'https://api.mch.weixin.qq.com'
_TIMEOUT = 20


def _env(k: str) -> str:
    return (os.getenv(k) or '').strip()


def is_configured() -> tuple[bool, list]:
    """凭证齐不齐。返回 (是否可用, 缺哪些)——缺凭证时前端要如实说"支付未开通"，不能假装能付。"""
    need = ['WXPAY_MCHID', 'WXPAY_APPID', 'WXPAY_API_V3_KEY',
            'WXPAY_CERT_SERIAL', 'WXPAY_PRIVATE_KEY', 'WXPAY_NOTIFY_URL']
    missing = [k for k in need if not _env(k)]
    return (not missing), missing


def _private_key():
    """商户私钥。环境变量里可能是带真实换行的，也可能是 \\n 转义的（Render 面板粘贴常见）——都兼容。"""
    raw = _env('WXPAY_PRIVATE_KEY').replace('\\n', '\n')
    return serialization.load_pem_private_key(raw.encode('utf-8'), password=None)


def _sign(method: str, url_path: str, body: str) -> str:
    """v3 请求签名：METHOD\\nURL\\nTIMESTAMP\\nNONCE\\nBODY\\n 用商户私钥 RSA-SHA256 签，Base64。
    返回完整的 Authorization 头。"""
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex.upper()
    message = f'{method}\n{url_path}\n{ts}\n{nonce}\n{body}\n'
    sig = _private_key().sign(message.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
    sig_b64 = base64.b64encode(sig).decode()
    return (f'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{_env("WXPAY_MCHID")}",'
            f'nonce_str="{nonce}",'
            f'signature="{sig_b64}",'
            f'timestamp="{ts}",'
            f'serial_no="{_env("WXPAY_CERT_SERIAL")}"')


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')) if payload else ''
    headers = {
        'Authorization': _sign(method, path, body),
        'Accept': 'application/json',
        'User-Agent': 'meansights-learning/1.0',
    }
    if body:
        headers['Content-Type'] = 'application/json'
    r = requests.request(method, _API_BASE + path, data=body.encode('utf-8') if body else None,
                         headers=headers, timeout=_TIMEOUT)
    try:
        data = r.json() if r.text else {}
    except ValueError:
        data = {'raw': r.text[:300]}
    return r.status_code, data


# ── 下单 ──────────────────────────────────────────────────────────────

def create_native_order(out_trade_no: str, amount_fen: int, description: str) -> dict:
    """Native 下单 → 返回 {'code_url': 'weixin://wxpay/bizpayurl?pr=xxx'} 或 {'error': ...}。
    code_url 就是二维码里的内容，前端把它渲染成二维码即可。"""
    ok, missing = is_configured()
    if not ok:
        return {'error': f'微信支付未配置（缺 {"/".join(missing)}）'}
    payload = {
        'appid': _env('WXPAY_APPID'),
        'mchid': _env('WXPAY_MCHID'),
        'description': description[:127],
        'out_trade_no': out_trade_no,
        'notify_url': _env('WXPAY_NOTIFY_URL'),
        'amount': {'total': int(amount_fen), 'currency': 'CNY'},
        # 15 分钟过期（微信默认挂 2 小时）：主流扫码付都是十几分钟，超时自动关单，
        # 免得用户翻出半天前的旧码去付、付完却对不上当时那笔的档位。
        'time_expire': (datetime.now(timezone.utc).astimezone()
                        + timedelta(minutes=15)).isoformat(timespec='seconds'),
    }
    try:
        code, data = _request('POST', '/v3/pay/transactions/native', payload)
    except Exception as e:
        print(f'[wxpay] 下单请求异常: {type(e).__name__}: {e}', flush=True)
        return {'error': '连不上微信支付，稍后再试'}
    if code == 200 and data.get('code_url'):
        return {'code_url': data['code_url']}
    # 微信的错误信息对排障很关键，但不要把它整段抛给用户（可能含商户信息）
    print(f'[wxpay] 下单失败 http={code} data={data}', flush=True)
    return {'error': f"下单失败（{data.get('code') or code}）", '_detail': data.get('message')}


def query_order(out_trade_no: str) -> dict:
    """按商户订单号查微信侧状态（回调没来时的兜底核对）。"""
    ok, _ = is_configured()
    if not ok:
        return {}
    path = f'/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={_env("WXPAY_MCHID")}'
    try:
        code, data = _request('GET', path, None)
        return data if code == 200 else {}
    except Exception as e:
        print(f'[wxpay] 查单异常: {e}', flush=True)
        return {}


# ── 回调：验签 + 解密 ──────────────────────────────────────────────────

_PLATFORM_CERTS: dict = {}      # serial_no → 公钥对象（进程内缓存，微信证书 5 年一换）
_CERTS_FETCHED_AT = 0.0


def _load_platform_certs(force: bool = False) -> dict:
    """拉微信平台证书（回调验签要用微信的公钥）。证书本身是用 APIv3 密钥 AES-GCM 加密下发的。
    缓存 12 小时——微信明确要求不要每次回调都拉。"""
    global _CERTS_FETCHED_AT
    now = time.time()
    if _PLATFORM_CERTS and not force and (now - _CERTS_FETCHED_AT) < 43200:
        return _PLATFORM_CERTS
    try:
        code, data = _request('GET', '/v3/certificates', None)
        if code != 200:
            print(f'[wxpay] 拉平台证书失败 http={code} {data}', flush=True)
            return _PLATFORM_CERTS
        from cryptography.x509 import load_pem_x509_certificate
        for item in (data.get('data') or []):
            enc = item.get('encrypt_certificate') or {}
            pem = _aes_gcm_decrypt(enc.get('associated_data'), enc.get('nonce'), enc.get('ciphertext'))
            if pem:
                cert = load_pem_x509_certificate(pem.encode('utf-8'))
                _PLATFORM_CERTS[item.get('serial_no')] = cert.public_key()
        _CERTS_FETCHED_AT = now
        print(f'[wxpay] 平台证书已缓存：{list(_PLATFORM_CERTS)}', flush=True)
    except Exception as e:
        print(f'[wxpay] 平台证书异常: {type(e).__name__}: {e}', flush=True)
    return _PLATFORM_CERTS


def _aes_gcm_decrypt(associated_data: str | None, nonce: str | None, ciphertext: str | None) -> str | None:
    """APIv3 的 AES-256-GCM 解密（平台证书、回调报文都用它）。"""
    if not nonce or not ciphertext:
        return None
    key = _env('WXPAY_API_V3_KEY').encode('utf-8')
    if len(key) != 32:
        print('[wxpay] APIv3 密钥长度不是 32 字节，解密不了', flush=True)
        return None
    try:
        data = base64.b64decode(ciphertext)
        aad = (associated_data or '').encode('utf-8')
        return AESGCM(key).decrypt(nonce.encode('utf-8'), data, aad).decode('utf-8')
    except Exception as e:
        print(f'[wxpay] AES-GCM 解密失败: {type(e).__name__}', flush=True)
        return None


def _merchant_platform_pubkey():
    """「微信支付公钥」模式（商户平台-API安全里申请的公钥，回调头 Wechatpay-Serial 以 PUB_KEY_ID_ 开头）。
    2026-09-08 上线实测：本商户已切此模式，/v3/certificates 直接 404，旧的平台证书路径永远验不过。
    公钥不是秘密，PEM 放 WXPAY_PUBLIC_KEY 环境变量（支持 \\n 转义单行）。"""
    raw = _env('WXPAY_PUBLIC_KEY').replace('\\n', '\n')
    if not raw:
        return None
    try:
        return serialization.load_pem_public_key(raw.encode('utf-8'))
    except Exception as e:
        print(f'[wxpay] WXPAY_PUBLIC_KEY 不是合法 PEM: {type(e).__name__}', flush=True)
        return None


def verify_notify(headers, body_bytes: bytes) -> bool:
    """回调验签：用微信平台公钥验 TIMESTAMP\\nNONCE\\nBODY\\n 的签名。
    验不过一律当伪造丢弃——这是防"任何人 POST 一下就白拿额度"的唯一屏障。"""
    ts = headers.get('Wechatpay-Timestamp') or ''
    nonce = headers.get('Wechatpay-Nonce') or ''
    signature = headers.get('Wechatpay-Signature') or ''
    serial = headers.get('Wechatpay-Serial') or ''
    if not (ts and nonce and signature and serial):
        print('[wxpay] 回调缺签名头', flush=True)
        return False
    # 时间戳偏差 >5 分钟视为重放
    try:
        if abs(time.time() - int(ts)) > 300:
            print('[wxpay] 回调时间戳偏差过大，拒绝', flush=True)
            return False
    except ValueError:
        return False
    if serial.startswith('PUB_KEY_ID_'):
        pub = _merchant_platform_pubkey()
        if pub is None:
            print('[wxpay] 商户平台是「微信支付公钥」模式，但 WXPAY_PUBLIC_KEY 没配——回调验不了签，'
                  '到账只能靠主动查单兜底', flush=True)
            return False
    else:
        certs = _load_platform_certs()
        pub = certs.get(serial)
        if pub is None:                      # 新证书轮换 → 强制刷一次再试
            pub = _load_platform_certs(force=True).get(serial)
        if pub is None:
            print(f'[wxpay] 找不到平台证书 serial={serial}', flush=True)
            return False
    message = f'{ts}\n{nonce}\n'.encode('utf-8') + body_bytes + b'\n'
    try:
        pub.verify(base64.b64decode(signature), message, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        print('[wxpay] 回调验签不通过', flush=True)
        return False


def decrypt_notify(body: dict) -> dict | None:
    """回调报文解密 → 交易明细（含 out_trade_no / transaction_id / trade_state / amount）。"""
    res = body.get('resource') or {}
    plain = _aes_gcm_decrypt(res.get('associated_data'), res.get('nonce'), res.get('ciphertext'))
    if not plain:
        return None
    try:
        return json.loads(plain)
    except ValueError:
        return None


def gen_out_trade_no(user_id: str) -> str:
    """商户订单号：时间 + 用户尾号 + 随机（≤32 位，微信要求唯一且只含字母数字）。"""
    return f"HL{datetime.utcnow().strftime('%y%m%d%H%M%S')}{(user_id or 'x')[-4:].replace('_', '')}{uuid.uuid4().hex[:6]}"[:32]
