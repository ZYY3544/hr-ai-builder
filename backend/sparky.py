# -*- coding: utf-8 -*-
"""
Sparky —— 学习站的分诊 + 陪走助手。

设计纪律（结构强制，不靠 prompt 自觉）：
1. 只在封闭集合里指路：模型把推荐节写进末尾 REFS 行，服务端逐个对
   _index.json 校验，不存在的直接丢弃并记日志——它永远给不出一节不存在的课。
2. 不重新讲课：prompt 层要求指路不复述；REFS 机制让"指路"成为唯一的强化路径。
3. 挂了说人话：无 key / 上游超时 / 限流，全部返回给用户一句能读懂的话，
   绝不转圈装正常——这是一个教防幻觉的站，它的助手不能在故障时说谎。

4. 课程反馈闭环：对方说某节难/有建议时，模型在末尾多输出一行 FB，服务端解析后
   落进持久层——跟 REFS 同一套尾部标记机制，同一套校验（lesson 必须真实存在）。
   反馈是改课的输入，所以它必须是结构化的数据，不能只是聊天记录里的一句话。

对话历史仍由客户端携带（localStorage），服务端不落库；但反馈与难度信号落库。
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

from store import add_feedback, add_signal, hard_lessons, store

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
- **不替人做人生判断**：该不该转行、该去哪家公司、值不值得跳槽——这超出你的职责。\
拒绝之后必须补一句：「这类事想找真人聊透，首页最底下的联系入口能找到站主。」\
然后再把话题拉回你能帮的部分（把大决定拆成可验证的小动作、对照岗位要求看差距）。\
学习路怎么走你管，人生路怎么走你不管。
- 每次回复**最多推荐 3 节**，按先后顺序排。全都读完约几分钟要说。
- 数据安全问题从严：任何真实员工数据相关的问题，先提第六篇章《你的数据到底走了哪条线》。

## 收集课程反馈（这个站正在靠它改课，是你的第三件正事）
对方说某节看不懂、写得绕、例子不对、或者提改进建议时：
- **别辩解，也别当场把那节重讲一遍**（重讲违反上面的铁律，而且掩盖了课本身写得不好这个事实）。
- 先用一句话确认你听懂了是哪一节、卡在哪个点上——**确认的是具体位置，不是"好的收到"**。
- 然后在末尾多输出一行 FB（格式见下）。
- 可以说「记下来了，会改」。**绝不承诺具体时间**，不说"马上改好""今天就改"——这个站是一个人在维护，
  兑现不了的承诺比不承诺伤得多。
- 只在对方**真的表达了困惑或建议**时才输出 FB 行。别替对方脑补，别把"我没看懂你这句话"当成课程反馈。

## 回复格式（三段，顺序不能乱）
**第一段：正文。永远排在最前面。**平实中文，可用 **加粗**，不用标题层级；\
提到某节时用它的中文标题，不要出现文件名。
⚠️ 你的回复**绝不能以 FB: 或 REFS: 开头**。那两行是给系统读的、用户看不见，\
放在最前面会导致用户只看到一片空白。

第二段（可选，只有这一轮真的收到课程反馈时才输出，否则整行不要）：
FB: {"lesson":"文件名.html","kind":"hard|confusing|error|suggest","note":"一句话转述对方原意"}

第三段（每次都有，全文最后一行，没有推荐就写空数组）：
REFS: ["文件名1.html","文件名2.html"]"""


_MARKERS = ("REFS:", "FB:")


def _marker_cut(text: str, leading_nl: bool = True) -> int:
    """正文到哪儿为止——尾部标记（FB/REFS）出现的最早位置，没有则 -1。

    两个标记都可能出现，顺序不保证，所以取最小值；只取一个的话另一个会被当正文发给用户。
    """
    hits = []
    for tag in _MARKERS:
        i = text.find(("\n" + tag) if leading_nl else tag)
        if i != -1:
            hits.append(i)
    if leading_nl and any(text.startswith(t) for t in _MARKERS):
        hits.append(0)
    return min(hits) if hits else -1


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
    trigger: Optional[str] = None       # 主动开口触发器 id（stuck/skim/comeback/…）
    trigger_note: Optional[str] = None  # 触发的一句话描述（前端规则引擎给出）
    behavior: Optional[str] = None      # 行为轨迹摘要（最近浏览序列+停留时长）
    visitor: Optional[str] = None       # 匿名访客 id（track.js 的 hab_vid，不含个人信息）


class ChatBody(BaseModel):
    messages: list                      # [{role:'user'|'assistant', content:str}]
    ctx: Optional[ChatCtx] = None


_FB_KINDS = {"hard", "confusing", "error", "suggest"}


class FeedbackBody(BaseModel):
    lesson: Optional[str] = None
    kind: str = "hard"
    note: str = ""
    visitor: Optional[str] = None


class SignalBody(BaseModel):
    lesson: str
    dwell_s: int = 0
    kind: str = "stuck"
    visitor: Optional[str] = None


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
        if ctx.behavior:
            bits.append(f"最近的行为轨迹：{str(ctx.behavior)[:600]}")
        out = ("\n\n## 对方的实时状态（按此调整推荐，别推荐已读完的节）\n"
               + "\n".join(bits)) if bits else ""
        if ctx.trigger:
            out += (f"\n\n## 本次是你主动开口（不是用户提问）\n"
                    f"触发原因：{(ctx.trigger_note or ctx.trigger)[:200]}\n"
                    f"要求：1-3 句话。直接说你观察到的具体事实（引用轨迹里的节名和时长，"
                    f"这是你显得聪明的唯一方式），给一个明确的下一步；别道歉、别客套、"
                    f"别说'我注意到'这种监控感的话，像同桌探头看了一眼那样自然。"
                    f"REFS 最多 2 节。结尾留一个对方一句话就能答的问题。")
            if ctx.trigger == "stuck":
                out += ("\n结尾那个问题**固定问这一句**，一字不改："
                        "「是这节写得绕，还是概念本身就难？」"
                        "——这两个答案指向完全不同的修法（重写 vs 拆节补前置），"
                        "是我们判断该怎么改这节课的唯一依据。对方答了之后，按上面的规则输出 FB 行。")
            if ctx.trigger == "night":
                out += ("\n这一条是关心，不是催学。**不许说教**，不许出现'早点休息''注意身体'"
                        "这种谁都会说的空话——那是廉价关怀，说了等于没说。"
                        "只陈述你看到的疲态事实（读了多久、最近几节停留时间怎么变的），"
                        "再给一句为对方省力的建议（比如明早接着读哪儿）。"
                        "REFS 写空数组，深夜不要再塞新的课给对方。")
        return out

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
        proactive = bool(body.ctx and body.ctx.trigger)
        if not proactive and (not msgs or msgs[-1]["role"] != "user"):
            raise HTTPException(400, "last message must be from user")
        while sum(len(m["content"]) for m in msgs) > 8000 and len(msgs) > 1:
            msgs.pop(0)

        if proactive and (not msgs or msgs[-1]["role"] != "user"):
            msgs = msgs + [{"role": "user", "content": "（用户此刻没有说话，请按触发原因主动开口）"}]
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
                    cut = _marker_cut(text)
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
                    cut = _marker_cut(tail, leading_nl=False)
                    yield sse({"t": "delta", "text": tail if cut == -1 else tail[:cut]})

                # 兜底：模型偶尔会把 FB:/REFS: 顶到最前面，那样正文会被整条切掉，
                # 用户看到一片空白。宁可把顺序摆正后补发，也不能让人对着空气。
                if sent == 0:
                    body_only = re.sub(r"^\s*(FB|REFS)\s*:.*$", "", text,
                                       flags=re.M).strip()
                    if body_only:
                        print("[SPARKY] 模型把标记放到了正文前面，已补发正文", flush=True)
                        yield sse({"t": "delta", "text": body_only})

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

                # ── 反馈闸：FB 行落库，同样要求 lesson 真实存在 ──
                got_fb = False
                mf = re.search(r"FB:\s*(\{.*?\})", text, re.S)
                if mf:
                    try:
                        fb = json.loads(mf.group(1))
                    except Exception:
                        fb = None
                    if isinstance(fb, dict):
                        les = fb.get("lesson") or (body.ctx.lesson if body.ctx else "")
                        note = str(fb.get("note") or "").strip()
                        kind = str(fb.get("kind") or "hard").strip()
                        if les and les not in LESSON_IDX:
                            print(f"[SPARKY] FB 里的节不存在，改挂当前节: {les!r}", flush=True)
                            les = (body.ctx.lesson if body.ctx else "") or ""
                        if note:
                            got_fb = add_feedback(
                                les, kind if kind in _FB_KINDS else "hard", note,
                                visitor=(body.ctx.visitor if body.ctx else "") or "",
                                source="chat")
                            yield sse({"t": "fb", "ok": bool(got_fb),
                                       "lesson": les,
                                       "title": LESSON_IDX.get(les, {}).get("title", "")})
                yield sse({"t": "done"})
                print(f"[SPARKY] ip={ip[:12]} turns={len(msgs)} out={len(text)}ch "
                      f"refs={len(refs)} fb={int(got_fb)}", flush=True)
            except _rq.exceptions.RequestException as e:
                print(f"[SPARKY] network error: {e}", flush=True)
                yield sse({"t": "err", "msg": "我这会儿连不上模型了。你可以先翻目录，或者过几分钟再来。"})

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    # ------------------------------------------------------------ 反馈直投
    @router.post("/api/sparky/feedback")
    def feedback(body: FeedbackBody, request: Request):
        """不经模型的直投通道。

        为什么单独留一条：反馈的主路径走对话（模型负责问清楚是哪一节、卡在哪），
        但对话会被限流、模型也会挂。反馈是这个阶段最贵的东西，不能因为
        「Sparky today 说不了话」就整条丢掉。
        """
        if not (body.note or "").strip():
            raise HTTPException(400, "说点具体的——哪一节、哪句话看不懂。")
        les = body.lesson or ""
        if les and les not in LESSON_IDX:
            les = ""
        ok = add_feedback(les, body.kind if body.kind in _FB_KINDS else "hard",
                          body.note.strip(), visitor=body.visitor or "", source="direct")
        return {"ok": bool(ok), "lesson": les,
                "title": LESSON_IDX.get(les, {}).get("title", "")}

    # ------------------------------------------------------------ 匿名难度信号
    _sig_hits: dict = defaultdict(lambda: deque(maxlen=60))

    @router.post("/api/sparky/signal")
    def signal(body: SignalBody, request: Request):
        """行为侧的难度信号：谁在哪节卡了多久。不含任何用户说的话。

        这半是免费的——用户一个字都不用讲，哪节最常把人卡住自己会浮出来。
        """
        if body.lesson not in LESSON_IDX:
            return {"ok": False, "why": "unknown lesson"}
        ip = (request.headers.get("x-forwarded-for") or
              (request.client.host if request.client else "?")).split(",")[0].strip()
        q, now = _sig_hits[ip], time.time()
        if sum(1 for t in q if now - t < 3600) >= 40:      # 信号也得防刷
            return {"ok": False, "why": "rate"}
        q.append(now)
        return {"ok": add_signal(body.lesson, body.dwell_s, body.kind or "stuck",
                                 visitor=body.visitor or "")}

    # ------------------------------------------------------------ 站主看板
    @router.get("/api/sparky/insights")
    def insights(code: str = ""):
        """哪几节最难 + 最近的反馈原文。给站主看的，不对外。"""
        admin = (os.getenv("ADMIN_CODE") or "").strip()
        if not admin or code != admin:      # 没配就是关着的（fail closed）
            raise HTTPException(404, "Not Found")
        return {
            "store_mode": store.mode,
            "warning": None if store.mode == "supabase"
                       else "当前是内存模式，Render 重启/休眠即清空；填 SUPABASE_URL/KEY 后自动持久化",
            "hard_lessons": hard_lessons(LESSON_IDX, 20),
            "recent_feedback": store.recent("hab_feedback", 60),
        }

    return router
