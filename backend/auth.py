# -*- coding: utf-8 -*-
"""无状态 JWT 会话。

第一版刻意不落库：Render free 实例无持久磁盘，用户信息直接签进 token。
等真要存学习进度、测评历史时再上 DB，届时 token 里的 sub（openid）就是主键。
"""
import os
import time
from typing import Optional

import jwt
from fastapi import Header, HTTPException

_ALGO = "HS256"
_TTL = 60 * 60 * 24 * 30   # 30 天


def _secret() -> str:
    s = (os.getenv("JWT_SECRET") or "").strip()
    if not s:
        # 未配置时用进程内随机串：服务重启即登出，避免出现"人人可伪造"的固定弱密钥。
        global _fallback
        try:
            return _fallback
        except NameError:
            import secrets as _s
            _fallback = _s.token_hex(32)
            return _fallback
    return s


def issue(openid: str, nickname: str = "", avatar: str = "", source: str = "wx") -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": openid, "name": nickname, "avatar": avatar, "src": source,
         "iat": now, "exp": now + _TTL},
        _secret(), algorithm=_ALGO,
    )


def decode(token: str) -> dict:
    try:
        return jwt.decode(token, _secret(), algorithms=[_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "invalid token")


def current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    claims = decode(authorization.split(" ", 1)[1].strip())
    return {"openid": claims["sub"], "nickname": claims.get("name", ""),
            "avatar": claims.get("avatar", ""), "source": claims.get("src", "")}
