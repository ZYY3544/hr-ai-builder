#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sparky 对话探针 —— 给测试用，把一轮对话打到线上 Sparky 并解析出结构化结果。

为什么存在：Sparky 是 SSE 流式接口，正文分片、结构化事件（refs/fb）走同一条流。
肉眼 curl 看不清"用户实际看到什么"和"后台记了什么"，而这两件恰恰是要分开评的：
正文是体验，refs/fb 是纪律。

用法：
    python3 scripts/sparky_probe.py '<对话JSON>'
其中对话 JSON = {"messages":[{"role":"user","content":"..."}], "ctx":{...}}

输出 JSON：{reply, refs, fb, error, http, elapsed_s}
    reply  用户实际看到的正文（尾部标记已被服务端切掉）
    refs   服务端校验通过的推荐节（不存在的会被拦掉，所以这里只会是真实的）
    fb     本轮是否被记为课程反馈
    leak   正文里是否漏出了 FB:/REFS: 这类内部标记（漏了就是 bug）

限流：线上是 8次/分、80次/天（按 IP）。本脚本自带退避重试，撞限流会等着而不是报错，
      但**并发跑多个 agent 时仍要各自间隔 ≥20 秒**，否则会把当天配额烧光。
"""
import json
import sys
import time
import urllib.request
import urllib.error

API = "https://hr-ai-builder-api.onrender.com/api/sparky/chat"


def probe(payload: dict, max_retry: int = 4) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode()
    for attempt in range(max_retry):
        t0 = time.time()
        req = urllib.request.Request(
            API, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=150) as r:
                text, events = "", []
                for raw in r:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data: "):
                        continue
                    try:
                        ev = json.loads(line[6:])
                    except Exception:
                        continue
                    if ev.get("t") == "delta":
                        text += ev.get("text", "")
                    else:
                        events.append(ev)
                refs = next((e["items"] for e in events if e.get("t") == "refs"), [])
                fb = next((e for e in events if e.get("t") == "fb"), None)
                err = next((e.get("msg") for e in events if e.get("t") == "err"), None)
                return {
                    "http": 200,
                    "reply": text.strip(),
                    "refs": [{"file": x["file"], "title": x["title"]} for x in refs],
                    "fb": fb,
                    "error": err,
                    "leak": ("REFS:" in text) or ("FB:" in text),
                    "elapsed_s": round(time.time() - t0, 1),
                }
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read().decode()).get("detail", "")
            except Exception:
                pass
            if e.code == 429 and attempt < max_retry - 1:
                time.sleep(35 * (attempt + 1))     # 撞限流就等，别把失败误报成 bug
                continue
            return {"http": e.code, "reply": "", "refs": [], "fb": None,
                    "error": detail or str(e), "leak": False, "elapsed_s": 0}
        except Exception as e:
            if attempt < max_retry - 1:
                time.sleep(8)
                continue
            return {"http": 0, "reply": "", "refs": [], "fb": None,
                    "error": f"{type(e).__name__}: {e}", "leak": False, "elapsed_s": 0}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法: sparky_probe.py '<对话JSON>'")
    print(json.dumps(probe(json.loads(sys.argv[1])), ensure_ascii=False, indent=1))
