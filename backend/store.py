# -*- coding: utf-8 -*-
"""
持久层 —— 一个接口，两种实现，启动时按环境变量选。

为什么存在：这个站此前所有状态都在内存里（埋点环形缓冲、限流滑窗），
Render free 计划重启即清空、15 分钟无访问还会休眠。课程反馈一旦丢，
用户白说了——而"我们会很快改进"是已经对用户许下的承诺，不能建在会蒸发的地基上。

选型规则（`Store.mode` 报告实际选中的）：
  SUPABASE_URL + SUPABASE_KEY 都在  → supabase（持久，跨重启跨实例）
  否则                              → memory（内存 + 尽力写 JSONL，重启即丢）

调用方不需要知道用的是哪个。等 Supabase 建好、把两个变量填进 Render，
本文件之外一行都不用改。建表 SQL 见 docs/supabase-schema.sql。
"""
import json
import os
import time
from collections import deque
from typing import Optional

import requests as _rq

_SB_URL = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
_SB_KEY = (os.getenv("SUPABASE_KEY") or "").strip()
_FILE_DIR = os.getenv("FEEDBACK_DIR", "/tmp/hab")
_MEM_MAX = 4000


class _Base:
    mode = "?"

    def add(self, table: str, rec: dict) -> bool:
        raise NotImplementedError

    def recent(self, table: str, limit: int = 50) -> list:
        raise NotImplementedError


class MemStore(_Base):
    """内存 + 尽力落盘。重启即丢——这是明确的降级，不是"看起来在工作"。

    同时把每条记录打一行结构化 stdout，Render 的日志面板能搜到；
    在没有库的日子里，那份日志是唯一跨重启还在的副本。
    """
    mode = "memory"

    def __init__(self):
        self._buf: dict = {}
        try:
            os.makedirs(_FILE_DIR, exist_ok=True)
            self._dir = _FILE_DIR
        except Exception:
            self._dir = None

    def add(self, table: str, rec: dict) -> bool:
        self._buf.setdefault(table, deque(maxlen=_MEM_MAX)).append(rec)
        line = json.dumps(rec, ensure_ascii=False)
        print(f"[STORE:{table}] {line}", flush=True)     # 唯一跨重启的副本
        if self._dir:
            try:
                with open(os.path.join(self._dir, f"{table}.jsonl"), "a",
                          encoding="utf-8") as fh:
                    fh.write(line + "\n")
            except Exception:
                pass
        return True

    def recent(self, table: str, limit: int = 50) -> list:
        rows = list(self._buf.get(table, []))
        # 落盘的比内存全（同一进程内两者一致，但重启后文件可能还在）
        if self._dir:
            try:
                p = os.path.join(self._dir, f"{table}.jsonl")
                if os.path.exists(p):
                    with open(p, encoding="utf-8") as fh:
                        rows = [json.loads(x) for x in fh if x.strip()]
            except Exception:
                pass
        return rows[-limit:][::-1]


class SupabaseStore(_Base):
    """走 PostgREST。不引新依赖（requests 已在），失败自动降级到内存副本。"""
    mode = "supabase"

    def __init__(self):
        self._h = {
            "apikey": _SB_KEY,
            "Authorization": f"Bearer {_SB_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        self._fallback = MemStore()

    def add(self, table: str, rec: dict) -> bool:
        try:
            r = _rq.post(f"{_SB_URL}/rest/v1/{table}", headers=self._h,
                         json=rec, timeout=6)
            if r.status_code < 300:
                return True
            print(f"[STORE] supabase insert {table} -> {r.status_code} {r.text[:160]}",
                  flush=True)
        except Exception as e:
            print(f"[STORE] supabase insert {table} 异常: {e}", flush=True)
        return self._fallback.add(table, rec)      # 写不进也不能把用户的话弄丢

    def recent(self, table: str, limit: int = 50) -> list:
        try:
            r = _rq.get(f"{_SB_URL}/rest/v1/{table}",
                        headers={**self._h, "Prefer": ""},
                        params={"select": "*", "order": "created_at.desc",
                                "limit": str(limit)}, timeout=6)
            if r.status_code < 300:
                return r.json()
            print(f"[STORE] supabase select {table} -> {r.status_code}", flush=True)
        except Exception as e:
            print(f"[STORE] supabase select {table} 异常: {e}", flush=True)
        return self._fallback.recent(table, limit)


store: _Base = SupabaseStore() if (_SB_URL and _SB_KEY) else MemStore()
print(f"[STORE] 持久层模式 = {store.mode}"
      + ("" if store.mode == "supabase" else "（重启即丢；填 SUPABASE_URL/KEY 后自动切换）"),
      flush=True)


# ---------------------------------------------------------------- 业务封装
FEEDBACK = "hab_feedback"      # 用户明说的：某节难 / 有建议
SIGNAL = "hab_signal"          # 行为侧的匿名难度信号：卡住


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def add_feedback(lesson: Optional[str], kind: str, note: str,
                 visitor: str = "", source: str = "chat") -> bool:
    return store.add(FEEDBACK, {
        "created_at": now_iso(), "lesson": (lesson or "")[:120],
        "kind": kind[:24], "note": note[:2000],
        "visitor": (visitor or "")[:40], "source": source[:16],
    })


def add_signal(lesson: str, dwell_s: int, kind: str = "stuck",
               visitor: str = "") -> bool:
    return store.add(SIGNAL, {
        "created_at": now_iso(), "lesson": lesson[:120],
        "dwell_s": int(dwell_s), "kind": kind[:24],
        "visitor": (visitor or "")[:40],
    })


def hard_lessons(idx: dict, limit: int = 20) -> list:
    """哪几节最常把人卡住 —— 行为数据，不是意见数据，用户一个字都不用说。"""
    rows = store.recent(SIGNAL, 2000)
    agg: dict = {}
    for r in rows:
        f = r.get("lesson")
        if not f:
            continue
        a = agg.setdefault(f, {"file": f, "n": 0, "dwell": []})
        a["n"] += 1
        a["dwell"].append(int(r.get("dwell_s") or 0))
    out = []
    for f, a in agg.items():
        meta = idx.get(f, {})
        d = a["dwell"]
        out.append({
            "file": f, "title": meta.get("title", f), "part": meta.get("part", ""),
            "declared_min": meta.get("min", 0), "stuck_n": a["n"],
            "median_dwell_min": round(sorted(d)[len(d) // 2] / 60, 1) if d else 0,
        })
    return sorted(out, key=lambda x: -x["stuck_n"])[:limit]
