# -*- coding: utf-8 -*-
"""
Sparky —— 学习站的分诊 + 陪走助手。

设计纪律（结构强制，不靠 prompt 自觉）：
1. 只在封闭集合里指路：模型把推荐节写进末尾 REFS 行，服务端逐个对
   _index.json 校验，不存在的直接丢弃并记日志——它永远给不出一节不存在的课。
2. 不重新讲课：prompt 层要求指路不复述；REFS 机制让"指路"成为唯一的强化路径。
3. 挂了说人话：无 key / 上游超时 / 限流，全部返回给用户一句能读懂的话，
   绝不转圈装正常——这是一个教防幻觉的站，它的助手不能在故障时说谎。

无状态：对话历史由客户端携带（localStorage），服务端不落库。
等登录 + Supabase 到位后再加服务端持久化，届时本文件只加存储层不改协议。
"""
import json
import os
import re
import time
from collections import defaultdict, deque
from typing import Optional

import requests as _rq
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ---------------------------------------------------------------- 配置
_DS_BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
_DS_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def _key() -> str:
    return (os.getenv("DEEPSEEK_API_KEY") or "").strip()


# 限流：内存滑窗，按 IP。免费站 + 开源仓库 = 一定会被刷，这层不是可选项。
_RL_MIN = int(os.getenv("SPARKY_RPM", "8"))        # 每分钟
_RL_DAY = int(os.getenv("SPARKY_RPD", "80"))       # 每天
_hits: dict = defaultdict(lambda: deque(maxlen=200))


def _limited(ip: str) -> Optional[str]:
    now = time.time()
    q = _hits[ip]
    if sum(1 for t in q if now - t < 60) >= _RL_MIN:
        return "你问得有点快，歇几秒再发。"
    if sum(1 for t in q if now - t < 86400) >= _RL_DAY:
        return "今天聊得够多了——把已经指给你的那几节读完，明天再来。"
    q.append(now)
    return None


# ---------------------------------------------------------------- 系统提示词
_PERSONA = """你是 Sparky，HR AI Builder 学习站的伴学小助手。你的风格：极其聪明、\
同理心强、阳光乐观、温和且坚定有力、有极强的洞察力和鲜明的观点，不谄媚也不疏离。\
用中文，说话短，一次只推进一步。"""

_DISCIPLINE = """## 你的职责（只有这两件，别承诺任何别的功能）
1. **分诊**：听懂对方想拿 AI 干什么，把 ta 放到具体的位置——某几节课、某个篇章、\
或一件能亲手做出来的事。对方说得模糊时，先追问一句把诉求变具体（比如"每个月合三张表做月报"\
就比"想学 AI"具体），不要拿到模糊诉求就硬推荐。
2. **陪走**：对方读到一半卡住、练习表对不上答案、不知道下一步——帮 ta 定位卡在哪，\
指回对应的节。

## 铁律
- **指路，不讲课**：有人问"RAG 是什么"，你不解释 RAG，你说哪一节讲这个、几分钟、\
为什么值得看，让 ta 去读。课是校验过的，你的现场复述不是。只有"跨节怎么串"这类\
课里没有的关联，你才自己讲。
- **只推荐目录里真实存在的节**，用下面目录里的确切文件名。宁可说"这个站不教这个"，\
也不编。这个站不教的（比如企业级部署运维、跟 HR 无关的编程），直说没有。
- **不替人做人生判断**：该不该转行、该去哪家公司、值不值得跳槽——这超出你的职责，\
建议 ta 通过站上「联系」入口找站主聊。学习路怎么走你管，人生路怎么走你不管。
- 每次回复**最多推荐 3 节**，按先后顺序排。全都读完约几分钟要说。
- 数据安全问题从严：任何真实员工数据相关的问题，先提第六篇章《你的数据到底走了哪条线》。

## 回复格式
正文用平实中文，可用 **加粗**，不用标题层级。
最后一行固定输出（没有推荐就写空数组）：
REFS: ["文件名1.html","文件名2.html"]
正文里提到某节时用它的中文标题，不要出现文件名。"""


def _catalog(idx: dict) -> str:
    """把 149 节压成模型可用的目录。按篇章分组：文件名|标题|分钟。"""
    parts: dict = {}
    for f, v in idx.items():
        parts.setdefault(v.get("part", "?") + " " + v.get("part_title", ""), []) \
             .append(f"{f}|{v['title']}|{v.get('min', 0)}′")
    lines = []
    for p, items in parts.items():
        lines.append(f"### {p}")
        lines.extend(items)
    return "## 课程目录（唯一可推荐的集合：文件名|标题|阅读分钟）\n" + "\n".join(lines)


def _extras(terms: list, jobs: list, term_lessons: dict) -> str:
    t = "\n".join(f"- {x['id']}({x['name']}/{x['ksa']}): {x['generic']}" for x in terms)
    j = "\n".join(f"- {x['company']} {x['title']}（{x['type']}）核心要求:"
                  f"{','.join(x['must'])} 加分:{','.join(x['plus'])}" for x in jobs)
    m = "\n".join(f"- {k}: {','.join(v)}" for k, v in term_lessons.items())
    return (f"## 能力词条（岗位要求的语言）\n{t}\n\n"
            f"## 在招岗位（岗位库页可看详情）\n{j}\n\n"
            f"## 词条→对应课程（做差距映射时用这张表，别自己配）\n{m}")


# ---------------------------------------------------------------- 请求协议
class ChatCtx(BaseModel):
    page: Optional[str] = None          # index / learn / quiz / jobs
    lesson: Optional[str] = None        # learn.html 当前节文件名
    done: Optional[list] = None         # 已读完的节（文件名列表）


class ChatBody(BaseModel):
    messages: list                      # [{role:'user'|'assistant', content:str}]
    ctx: Optional[ChatCtx] = None


def make_router(TERMS, JOBS, TERM_LESSONS, LESSON_IDX) -> APIRouter:
    router = APIRouter()
    system_static = (_PERSONA + "\n\n" + _DISCIPLINE + "\n\n"
                     + _catalog(LESSON_IDX) + "\n\n"
                     + _extras(TERMS, JOBS, TERM_LESSONS))

    def _ctx_block(ctx: Optional[ChatCtx]) -> str:
        if not ctx:
            return ""
        bits = []
        if ctx.lesson and ctx.lesson in LESSON_IDX:
            v = LESSON_IDX[ctx.lesson]
            bits.append(f"对方此刻正在读：{v['part']}《{v['title']}》")
        done = [f for f in (ctx.done or []) if f in LESSON_IDX][:60]
        if done:
            names = "、".join(LESSON_IDX[f]["title"] for f in done[-8:])
            bits.append(f"已读完 {len(done)} 节，最近读的：{names}")
        elif ctx.done is not None:
            bits.append("还一节都没读过（新访客）")
        if ctx.page:
            bits.append(f"当前页面：{ctx.page}")
        return ("\n\n## 对方的实时状态（按此调整推荐，别推荐已读完的节）\n"
                + "\n".join(bits)) if bits else ""

    @router.get("/api/sparky/health")
    def health():
        return {"enabled": bool(_key()), "model": _DS_MODEL}

    @router.post("/api/sparky/chat")
    def chat(body: ChatBody, request: Request):
        if not _key():
            raise HTTPException(503, "Sparky 还在接线中（管理员没配模型 key）。课都能正常读，先去翻目录。")
        ip = (request.headers.get("x-forwarded-for") or
              (request.client.host if request.client else "?")).split(",")[0].strip()
        msg = _limited(ip)
        if msg:
            raise HTTPException(429, msg)

        # 载荷收口：只认 user/assistant，截最近 12 条，总字数封顶
        msgs = [{"role": m.get("role"), "content": str(m.get("content", ""))[:2000]}
                for m in body.messages[-12:]
                if m.get("role") in ("user", "assistant") and m.get("content")]
        if not msgs or msgs[-1]["role"] != "user":
            raise HTTPException(400, "last message must be from user")
        while sum(len(m["content"]) for m in msgs) > 8000 and len(msgs) > 1:
            msgs.pop(0)

        payload = {
            "model": _DS_MODEL,
            "messages": [{"role": "system",
                          "content": system_static + _ctx_block(body.ctx)}] + msgs,
            "stream": True,
            "max_tokens": 900,
            "temperature": 0.6,
        }

        def sse(obj) -> bytes:
            return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode()

        def gen():
            full, sent = [], 0          # full=全文缓冲；sent=已发出的字符数
            HOLD = 8                    # 尾部滞留，防 "REFS:" 被拆进两个 chunk
            try:
                r = _rq.post(f"{_DS_BASE}/chat/completions",
                             headers={"Authorization": f"Bearer {_key()}"},
                             json=payload, stream=True, timeout=(10, 120))
                if r.status_code != 200:
                    print(f"[SPARKY] upstream {r.status_code} {r.text[:200]}", flush=True)
                    yield sse({"t": "err", "msg": "我这会儿连不上模型了。你可以先翻目录，或者过几分钟再来。"})
                    return
                stopped = False
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content", "")
                    except Exception:
                        continue
                    if not delta:
                        continue
                    full.append(delta)
                    if stopped:
                        continue
                    text = "".join(full)
                    cut = text.find("\nREFS:")
                    if cut == -1 and text.startswith("REFS:"):
                        cut = 0
                    if cut != -1:
                        if cut > sent:
                            yield sse({"t": "delta", "text": text[sent:cut]})
                            sent = cut
                        stopped = True
                    else:
                        emit_to = max(sent, len(text) - HOLD)
                        if emit_to > sent:
                            yield sse({"t": "delta", "text": text[sent:emit_to]})
                            sent = emit_to
                text = "".join(full)
                if not stopped and len(text) > sent:
                    tail = text[sent:]
                    cut = tail.find("REFS:")
                    yield sse({"t": "delta", "text": tail if cut == -1 else tail[:cut]})

                # ── 校验闸：REFS 里的每一节都必须真实存在 ──
                refs = []
                m = re.search(r"REFS:\s*(\[.*?\])", text, re.S)
                if m:
                    try:
                        cand = json.loads(m.group(1))
                    except Exception:
                        cand = []
                    for f in cand[:3]:
                        if isinstance(f, str) and f in LESSON_IDX:
                            v = LESSON_IDX[f]
                            refs.append({"file": f, "title": v["title"],
                                         "min": v.get("min", 0), "part": v.get("part", "")})
                        else:
                            print(f"[SPARKY] 拦下不存在的推荐: {f!r}", flush=True)
                yield sse({"t": "refs", "items": refs})
                yield sse({"t": "done"})
                print(f"[SPARKY] ip={ip[:12]} turns={len(msgs)} out={len(text)}ch refs={len(refs)}",
                      flush=True)
            except _rq.exceptions.RequestException as e:
                print(f"[SPARKY] network error: {e}", flush=True)
                yield sse({"t": "err", "msg": "我这会儿连不上模型了。你可以先翻目录，或者过几分钟再来。"})

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    return router
