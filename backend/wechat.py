# -*- coding: utf-8 -*-
"""微信登录服务（双轨，移植自铭曦 app/services/wechat.py）。

轨道 A · 开放平台「网站应用」OAuth（优先）
    前端打开 qrconnect 扫码页 → 微信回调 /api/wx/oauth/callback?code=&state=
    → web_code2token → web_userinfo 拿到 **真实昵称与头像**（小程序拿不到这部分）

轨道 B · 小程序扫码（兜底）
    new_scene() 建会话 → get_qrcode(scene) 生成小程序码 → 用户扫 → 壳小程序 wx.login 拿 code
    → 回传 /api/wx/bind → code2session 得 openid → set_scene_authed → 网页轮询拿 token

两轨都没配 → is_any_configured() 为 False，接口回 503，前端据此隐藏微信入口。
AppSecret 只从环境变量读，绝不入库、绝不进日志。
"""
import os
import time
import secrets
import threading
from urllib.parse import quote

import requests

# ────────────────────────────── 轨道 B：小程序 ──────────────────────────────
WX_APPID = os.getenv("WX_APPID", "").strip()


def _secret() -> str:
    return (os.getenv("WX_APPSECRET") or "").strip()


def is_configured() -> bool:
    return bool(WX_APPID and _secret())


_tok = {"value": None, "exp": 0.0}
_tok_lock = threading.Lock()


def get_access_token() -> str:
    with _tok_lock:
        if _tok["value"] and time.time() < _tok["exp"] - 120:
            return _tok["value"]
        r = requests.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={"grant_type": "client_credential", "appid": WX_APPID, "secret": _secret()},
            timeout=10,
        )
        d = r.json()
        if "access_token" not in d:
            raise RuntimeError(f"wx token error: {d.get('errcode')} {d.get('errmsg')}")
        _tok["value"] = d["access_token"]
        _tok["exp"] = time.time() + int(d.get("expires_in", 7200))
        return _tok["value"]


def code2session(js_code: str) -> dict:
    """js_code → {openid, session_key, ...} 或 {errcode, errmsg}。"""
    r = requests.get(
        "https://api.weixin.qq.com/sns/jscode2session",
        params={"appid": WX_APPID, "secret": _secret(), "js_code": js_code,
                "grant_type": "authorization_code"},
        timeout=10,
    )
    return r.json()


def get_qrcode(scene: str, page: str = "pages/login/login", env_version: str = "trial") -> bytes:
    """小程序码（getUnlimited）。check_path=False → page 未发布也能生成（体验版必需）。"""
    at = get_access_token()
    r = requests.post(
        "https://api.weixin.qq.com/wxa/getwxacodeunlimit",
        params={"access_token": at},
        json={"scene": scene, "page": page, "check_path": False,
              "env_version": env_version, "width": 280},
        timeout=10,
    )
    if r.headers.get("Content-Type", "").startswith("image"):
        return r.content
    raise RuntimeError(f"wx qrcode error: {r.text[:200]}")


# ─────────────────────── 轨道 A：开放平台网站应用 OAuth ───────────────────────
WX_WEB_APPID = os.getenv("WX_WEB_APPID", "").strip()


def _web_secret() -> str:
    return (os.getenv("WX_WEB_APPSECRET") or "").strip()


def web_callback_url() -> str:
    """OAuth 回调地址（单一真相源）。

    ⚠️ 必须与开放平台「授权回调域」**严格同域**——微信不支持二级域名通配，
    配了 a.example.com 就只认 a.example.com。换域名时改 WX_OAUTH_CALLBACK，不用改代码。
    """
    return (os.getenv("WX_OAUTH_CALLBACK")
            or "https://hr-ai-builder-api.onrender.com/api/wx/oauth/callback").strip()


def web_authorize_url(redirect_uri: str, state: str) -> str:
    return ("https://open.weixin.qq.com/connect/qrconnect"
            f"?appid={WX_WEB_APPID}&redirect_uri={quote(redirect_uri, safe='')}"
            f"&response_type=code&scope=snsapi_login&state={state}#wechat_redirect")


# 「微信登录」接口权限要在开放平台**单独申请开通**（应用审核通过 ≠ 有此权限）。
# 没开通时 qrconnect 页会返回「Scope 参数错误」——探测一次并缓存，没开通就当未配置，
# 前端自动回落小程序扫码；等权限批下来无需改配置即自动升级。
_web_ok = {"value": None, "checked_at": 0.0}
_web_ok_lock = threading.Lock()
_WEB_PROBE_TTL = 600


def _probe_web_scope() -> bool:
    """必须用**真实回调地址**探测：用别的 URL 探会因 redirect_uri 对不上而误判为无权限。"""
    try:
        r = requests.get(web_authorize_url(web_callback_url(), "probe"), timeout=8)
        body = r.content.decode("utf-8", errors="ignore")
        return not any(k in body for k in ("Scope 参数错误", "redirect_uri 参数错误", "抱歉，出错了"))
    except Exception:
        return False


def web_is_configured() -> bool:
    """env 配齐 **且**「微信登录」权限确实已开通。"""
    if not (WX_WEB_APPID and _web_secret()):
        return False
    with _web_ok_lock:
        if _web_ok["value"] is not None and time.time() - _web_ok["checked_at"] < _WEB_PROBE_TTL:
            return _web_ok["value"]
        ok = _probe_web_scope()
        _web_ok["value"], _web_ok["checked_at"] = ok, time.time()
        return ok


def web_code2token(code: str) -> dict:
    r = requests.get(
        "https://api.weixin.qq.com/sns/oauth2/access_token",
        params={"appid": WX_WEB_APPID, "secret": _web_secret(),
                "code": code, "grant_type": "authorization_code"},
        timeout=10,
    )
    r.encoding = "utf-8"
    return r.json()


def web_userinfo(access_token: str, openid: str) -> dict:
    """→ {nickname, headimgurl, unionid, ...}。这就是小程序拿不到的那部分。"""
    r = requests.get(
        "https://api.weixin.qq.com/sns/userinfo",
        params={"access_token": access_token, "openid": openid, "lang": "zh_CN"},
        timeout=10,
    )
    r.encoding = "utf-8"   # 微信这个接口不带 charset，不显式指定昵称会乱码
    return r.json()


def is_any_configured() -> bool:
    return is_configured() or web_is_configured()


# ──────────────────────────── scene store（登录会话）────────────────────────────
# 模块级 dict + 锁：Render free 单实例单进程，全线程共享。多 worker 会失效。
_scenes: dict = {}
_scene_lock = threading.Lock()
_TTL = 300   # 5 分钟没扫就过期


def _clean_locked():
    now = time.time()
    for k in [k for k, v in _scenes.items() if now - v["created"] > _TTL]:
        _scenes.pop(k, None)


def new_scene() -> str:
    s = secrets.token_hex(8)   # 小程序码 scene 限 32 位且字符集受限，hex 安全
    with _scene_lock:
        _clean_locked()
        _scenes[s] = {"status": "pending", "token": None, "user": None, "created": time.time()}
    return s


def set_scene_authed(scene: str, token: str, user: dict) -> bool:
    with _scene_lock:
        if scene in _scenes:
            _scenes[scene].update(status="authed", token=token, user=user)
            return True
    return False


def get_scene(scene: str) -> dict:
    with _scene_lock:
        return dict(_scenes.get(scene) or {})
