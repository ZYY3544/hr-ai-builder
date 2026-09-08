"""进程内限流 + 真实客户端 IP（2026-09-08 安全体检后新增）。

为什么单独一个模块：main.py 和 sparky.py 都要用同一套判据，之前各自写了一份
「取 X-Forwarded-For 第一段」——那一段是客户端随手能伪造的，限流等于没有。

IP 取值顺序：
  1. cf-connecting-ip / true-client-ip —— 由边缘代理覆盖写入，客户端伪造不了
  2. X-Forwarded-For 的**末位** —— 代理把真实来源追加在末尾，首位才是可伪造的
  3. 连接层 request.client.host 兜底

单实例单进程内存态；重启清零、多 worker 各算各的——对这个站的量级够用。
"""
import hmac
import os
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Request

_buckets: dict = defaultdict(lambda: defaultdict(lambda: deque(maxlen=600)))


def client_ip(request: Request) -> str:
    h = request.headers
    ip = (h.get("cf-connecting-ip") or h.get("true-client-ip") or "").strip()
    if not ip:
        xff = (h.get("x-forwarded-for") or "").strip()
        if xff:
            # 从末位往前找第一个公网地址：Render 内网代理会在最末追加 10.x，真实来源在它前面
            for cand in reversed([x.strip() for x in xff.split(",") if x.strip()]):
                if not _private(cand):
                    ip = cand
                    break
    if not ip:
        ip = request.client.host if request.client else "?"
    return ip[:64]


def _private(ip: str) -> bool:
    return (ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127.")
            or ip == "::1" or ip.startswith("fc") or ip.startswith("fd")
            or any(ip.startswith(f"172.{n}.") for n in range(16, 32)))


def hit(bucket: str, key: str, limit: int, window_s: int) -> bool:
    """记一次命中；超过 limit 次/window_s 秒返回 True（此次不计入）。"""
    q = _buckets[bucket][key]
    now = time.time()
    while q and now - q[0] > window_s:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def admin_ok(code: Optional[str], request: Optional[Request] = None) -> bool:
    """ADMIN_CODE 校验：没配=关死；常量时间比较；优先读 X-Admin-Code 头（query 会进访问日志）。"""
    admin = (os.getenv("ADMIN_CODE") or "").strip()
    if not admin:
        return False
    cand = ""
    if request is not None:
        cand = (request.headers.get("x-admin-code") or "").strip()
    if not cand:
        cand = (code or "").strip()
    return bool(cand) and hmac.compare_digest(cand, admin)
