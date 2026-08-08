"""
HR AI Builder — 内容与测评 API

现阶段所有内容以 Python 常量形式内置，前端为静态站（利于 SEO），
本服务提供：内容读取接口 + 测评判分接口，供前端渐进接入。
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal
import os

app = FastAPI(title="HR AI Builder API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- 能力词典
# ksa: K=知识（天~周可补） S=技能（周~月） A=能力（年，或补不了只能重新证明）
TERMS = [
    {"id": "logic", "name": "逻辑思维", "ksa": "A",
     "generic": "能把复杂问题拆成清晰的因果链",
     "in_context": "能把「我们招聘效率低」这种模糊诉求，拆成哪一步是死规则、哪一步需要判断、哪一步必须回到人。分不清这三段，做出来的 agent 一定在该停的地方不停。",
     "assessed_by": "行为面试：问你过去怎么拆一个没人给过答案的问题"},
    {"id": "product", "name": "产品思维", "ksa": "A",
     "generic": "从用户和价值出发做取舍",
     "in_context": "知道 HR 的「用户」是三拨人（员工 / 业务负责人 / HR 自己），而他们要的东西经常冲突。能说清这个功能优先服务谁、牺牲谁。",
     "assessed_by": "追问：你砍掉过什么功能，为什么"},
    {"id": "structured", "name": "结构化表达", "ksa": "A",
     "generic": "把想法讲得让人一遍听懂",
     "in_context": "能把一条 agent 的判断链讲清楚，让完全不懂技术的业务负责人点头——不是讲技术怎么实现，是讲它什么情况下会错、错了谁兜。",
     "assessed_by": "现场讲你的作品，看你是否需要对方懂技术"},
    {"id": "learning_agility", "name": "学习敏锐度", "ksa": "A",
     "generic": "快速吸收新东西并改变做法",
     "in_context": "模型三个月一变。你上一次主动废掉自己已经跑通的做法是什么时候、为什么？答不出的人，做的东西半年就过时。",
     "assessed_by": "行为面试：最近一次你推翻自己的经历"},
    {"id": "influence", "name": "向上说服 / 影响力", "ksa": "A",
     "generic": "让没有汇报关系的人支持你",
     "in_context": "把技术判断翻译成老板能算的账：不是「这个 agent 准确率 92%」，是「这件事现在要 3 个人 2 周，之后是 1 个人 2 天，风险在这里」。",
     "assessed_by": "追问：你推不动的时候做了什么"},
    {"id": "elicitation", "name": "判断类知识萃取", "ksa": "A",
     "generic": "把隐性经验变成显性规则",
     "in_context": "把老法师「看一眼就知道这人行不行」拆成 agent 能执行的规则，并且知道哪一部分永远拆不出来、必须留给人。这是整个角色最稀缺的能力，而且不在任何一门课里。",
     "assessed_by": "给一个真实判断场景，让你现场拆"},
    {"id": "scoping", "name": "场景选择与 ROI 判断", "ksa": "A",
     "generic": "决定先做哪件事",
     "in_context": "第一刀切哪里，说得清为什么不是别处。多数人切的是「最容易做的」，对的答案通常是「最痛但还没人碰的」。",
     "assessed_by": "追问：为什么选它不选另一个"},

    {"id": "vibecoding", "name": "Vibe coding", "ksa": "S",
     "generic": "用 AI 协作写出能跑的东西",
     "in_context": "一周内把一个 HR 场景做成能点、能演示的原型，不需要排工程师的期。不是「会用 Cursor」，是能自己收敛需求、调试、上线。",
     "assessed_by": "看作品 + 现场追问实现细节"},
    {"id": "prompt", "name": "Prompt 与上下文工程", "ksa": "S",
     "generic": "设计信息如何进入模型",
     "in_context": "不是调措辞，是决定哪些信息进上下文、什么顺序、什么时候切段——HR 场景里这直接决定它会不会把 A 部门的口径套到 B 部门。",
     "assessed_by": "给一个失效的 prompt，让你改并说明理由"},
    {"id": "data_prep", "name": "数据接入与清洗", "ksa": "S",
     "generic": "把脏数据变成可用输入",
     "in_context": "HR 系统导出来的表是三个系统、五种口径、人名还对不上。这一步做不完，后面全是假的。",
     "assessed_by": "给一份脏表，看你先问什么问题"},
    {"id": "eval", "name": "评估设计（eval）", "ksa": "S",
     "generic": "证明它做对了",
     "in_context": "能建一套自己的题来验证 agent，而不是跑几个 case 靠肉眼判。做新量具时先做阴性对照——注入已知的错，看它抓不抓得住。",
     "assessed_by": "追问：你怎么知道它是对的"},
    {"id": "comp_design", "name": "薪酬设计", "ksa": "S",
     "generic": "带宽、分位、套改",
     "in_context": "在这个角色里它不是终点，是判断素材——你要能把带宽逻辑喂给 agent，也要能看出它算错了。",
     "assessed_by": "给一份薪酬明细，看你先看哪一列"},
    {"id": "ship", "name": "部署与迭代", "ksa": "S",
     "generic": "推上线并持续改",
     "in_context": "做出来只是一半。有没有真人在用、用了多久、你根据反馈改了什么——别人问的是这三个。",
     "assessed_by": "追问：有人真的在用吗"},

    {"id": "hallucination", "name": "幻觉与能力边界", "ksa": "K",
     "generic": "模型什么时候会编",
     "in_context": "筛简历时它会编出候选人没写过的经历，因为它在补全一个「像简历」的文本。所以筛选只能做召回，判定必须回原文——这是一道闸，要写进流程。",
     "assessed_by": "概念题 + 场景判断"},
    {"id": "agent_vs_wf", "name": "Agent 与 Workflow 的分界", "ksa": "K",
     "generic": "什么时候不该上 Agent",
     "in_context": "HR 场景里大部分事该用固定流程，不该给自主权。分不清就会把一件三步的事做成一个会跑飞的 agent。",
     "assessed_by": "给场景让你判断该用哪个"},
    {"id": "hr_data", "name": "HR 数据现状与口径", "ksa": "K",
     "generic": "数据在哪、脏在哪",
     "in_context": "知道薪酬口径（月薪/年薪/含不含奖金）、编制口径、在职口径在哪两个部门之间打架——这是所有 HR 数据项目翻车的第一现场。",
     "assessed_by": "追问：你按谁的口径"},
    {"id": "compliance", "name": "合规、隐私与信任红线", "ksa": "K",
     "generic": "什么碰不得",
     "in_context": "员工数据不出内网、匿名要保证真实 n 不低于阈值、AI 参与的人事决策必须留痕且可申诉。踩了就不是技术问题。",
     "assessed_by": "场景题：这个数据能不能用"},
]

# ---------------------------------------------------------------- 测评题库
QUESTIONS = [
    {"id": "q1", "ksa": "K", "term": "hallucination",
     "how": "知识题 · 直接考概念边界 · 答错说明还没建立风险直觉",
     "stem": "你让 AI 从 200 份简历里筛出「有大厂 AI 项目经验」的候选人。以下哪个风险是 LLM 特有的，传统关键词筛选不会出现？",
     "options": ["可能漏掉一些其实符合条件的人",
                 "可能编造出候选人简历里根本没写过的经历",
                 "可能因为简历格式混乱而解析失败",
                 "可能对同一份简历给出不一致的排序"],
     "answer": 1,
     "explain": "B。漏筛（A）和解析失败（C）关键词方案一样会有；排序不一致（D）调温度就能压。只有「编造原文没有的内容」是生成式模型独有的——它在补全一个看起来像简历的文本。这条直接决定一道流程闸：AI 只能做召回，判定必须回到原文。"},
    {"id": "q2", "ksa": "S", "term": "data_prep",
     "how": "技能题 · 考做法顺序 · 答错说明没真做过数据活",
     "stem": "你要做一个薪酬带宽诊断工具，手上是一份 500 行的薪酬明细 Excel。第一步你会做什么？",
     "options": ["把整个 Excel 贴给大模型，让它先分析一遍",
                 "先选一个合适的模型和框架",
                 "先逐列确认口径——月薪还是年薪、含不含奖金、是否含股权",
                 "先把前端界面搭出来，方便演示"],
     "answer": 2,
     "explain": "C。口径不确认，后面所有数字都是假的，而且假得很像真的——这比报错危险得多。选 A 的人通常还没被数据坑过：模型会很自信地把月薪和年薪混在一起算分位，你看不出来。"},
    {"id": "q3", "ksa": "A", "term": "scoping",
     "how": "能力题 · 情景判断（SJT）· 没有知识点可背，测的是判断",
     "stem": "你做的简历初筛 agent 测下来效果不错。HRD 看完说：「那从下周开始，所有岗位都用它。」你的第一反应是？",
     "options": ["太好了，立刻安排全量上线",
                 "先问清楚：「效果不错」在她眼里是什么标准，以及漏掉一个好候选人的代价有多大",
                 "先做一份汇报材料，把成果讲清楚",
                 "直接说还不成熟，建议再等等"],
     "answer": 1,
     "explain": "B。这题测的不是 AI 知识，是你会不会在被认可的时刻仍然去校准标准。A 是最常见的死法——她说的「不错」可能只是「看着挺快」，而全量上线后第一个被误筛的高管内推候选人就会让整件事停摆。D 看似谨慎，但没给任何信息，等于把判断推回去。C 是把精力花在包装上。"},
]

# ---------------------------------------------------------------- 课程主题
TOPICS = [
    {"no": "00", "chapter": "前菜", "free": True, "kp": 3,
     "name": "AI 到底是什么，和 HR 有什么关系", "desc": "不讲原理，先讲它在你手上能变成什么"},
    {"no": "00", "chapter": "前菜", "free": True, "kp": 4,
     "name": "你手上哪些活它能干，哪些不能", "desc": "把 HR 六大模块的活逐条过一遍，标出边界"},
    {"no": "01", "chapter": "第一篇章", "free": False, "kp": 4,
     "name": "幻觉：它为什么会编，在 HR 场景怎么坑你", "desc": "筛简历时它会编出候选人没写过的经历"},
    {"no": "02", "chapter": "第一篇章", "free": False, "kp": 2,
     "name": "召回 vs 判定：一道必须设的闸", "desc": "AI 只能做召回，判定必须回原文"},
    {"no": "03", "chapter": "第一篇章", "free": False, "kp": 3,
     "name": "Agent 还是 Workflow：HR 场景怎么选", "desc": "大部分 HR 的事该用固定流程，不该给自主权"},
    {"no": "04", "chapter": "第二篇章", "free": False, "kp": 5,
     "name": "判断萃取：把老法师的经验拆成规则", "desc": "拆到哪一层为止，哪一部分必须留给人"},
    {"no": "05", "chapter": "第二篇章", "free": False, "kp": 4,
     "name": "Prompt 不是调措辞，是设计信息结构", "desc": "哪些信息进上下文、什么顺序、什么时候切段"},
    {"no": "06", "chapter": "第二篇章", "free": False, "kp": 3,
     "name": "上下文与记忆：为什么长任务会崩", "desc": "一场组织盘点跑到一半失忆，是怎么发生的"},
    {"no": "07", "chapter": "第三篇章", "free": False, "kp": 3,
     "name": "选题：什么样的作品站得住", "desc": "六个选题，各标工期、所需数据与常被追问的地方"},
    {"no": "08", "chapter": "第三篇章", "free": False, "kp": 4,
     "name": "数据：HR 数据从哪来、怎么脱敏", "desc": "真数据碰不得，合成数据怎么造得像"},
    {"no": "09", "chapter": "第三篇章", "free": False, "kp": 5,
     "name": "Vibe coding：一周做出能点的原型", "desc": "能自己收敛需求、调试、上线"},
    {"no": "10", "chapter": "第三篇章", "free": False, "kp": 4,
     "name": "评估：怎么证明它做对了", "desc": "建自己的题来验，先做阴性对照"},
    {"no": "11", "chapter": "第四篇章", "free": False, "kp": 3,
     "name": "第一刀切哪里：场景选择与 ROI", "desc": "对的答案通常是最痛但还没人碰的"},
    {"no": "12", "chapter": "第四篇章", "free": False, "kp": 3,
     "name": "向上说服：把技术判断翻译成账", "desc": "不说准确率，说人天和风险"},
    {"no": "13", "chapter": "第四篇章", "free": False, "kp": 2,
     "name": "试点到铺开：从 1 个团队到全公司", "desc": "跑通一个团队之后，最容易死在第二个"},
    {"no": "14", "chapter": "第四篇章", "free": False, "kp": 3,
     "name": "合规、隐私与信任红线", "desc": "留痕、可申诉、匿名的真实 n 阈值"},
    {"no": "15", "chapter": "第五篇章", "free": False, "kp": 3,
     "name": "能力词典：把经历翻译成能力语言", "desc": "用能力词还是技能词描述，含义完全不同"},
    {"no": "16", "chapter": "第五篇章", "free": False, "kp": 4,
     "name": "作品怎么讲：别人在追问什么", "desc": "「有人真的在用吗」问倒了大多数人"},
    {"no": "17", "chapter": "第五篇章", "free": False, "kp": 3,
     "name": "职级与薪酬带宽：这个角色值多少", "desc": "求职网站给不准的那部分"},
]

# ---------------------------------------------------------------- 岗位库
# 数据状态：岗位真实存在（2026-08 核实到公司/部门/地点）；JD 正文待补，未编造原文；
# 能力匹配与职级薪酬为示意，真数据接入后重跑。
JOBS = [
    {"id": "tx-tech", "company": "腾讯 · S3", "title": "AI-HR 培训生（技术&应用方向）",
     "type": "应届实习", "location": "深圳总部 · 成都", "verified": True, "jd_text": None,
     "intent": "一口气开了四个方向（创意/分析/技术&应用/沟通）——不是想清楚了，是还没想清楚这个角色该长什么样，在试。",
     "must": ["vibecoding", "hallucination", "hr_data"],
     "plus": ["prompt", "agent_vs_wf", "eval"]},
    {"id": "tx-ana", "company": "腾讯 · S3", "title": "AI-HR 培训生（分析方向）",
     "type": "应届实习", "location": "深圳总部 · 上海", "verified": True, "jd_text": None,
     "intent": "分析方向单开，说明已经有一批数据在手但用不起来的场景。真正缺的不是会跑模型的人，是能把口径吵清楚的人。",
     "must": ["hr_data", "hallucination", "data_prep"],
     "plus": ["eval", "vibecoding", "logic"]},
    {"id": "oai-people", "company": "OpenAI · People Innovation", "title": "Software Engineer, Full Stack",
     "type": "全职", "location": "Remote - US", "verified": True, "jd_text": None,
     "intent": "注意形态：这是工程师进 HR 部门，不是 HR 学 AI。这个角色正在从两头往中间长。",
     "must": ["vibecoding", "data_prep", "ship", "compliance"],
     "plus": ["hallucination", "prompt", "hr_data"]},
    {"id": "el-transform", "company": "ElevenLabs · Engineering", "title": "Internal AI Transformation",
     "type": "全职", "location": "Amsterdam · Berlin", "verified": True, "jd_text": None,
     "intent": "岗位名一个 HR 字都没有，做的却是同一件事。这是「命名空缺」最直接的证据。",
     "must": ["scoping", "vibecoding", "agent_vs_wf", "influence"],
     "plus": ["eval", "structured", "learning_agility"]},
    {"id": "cog-tm", "company": "Cognition · Applied AI", "title": "Applied AI Transformation Manager",
     "type": "全职", "location": "New York · London", "verified": True, "jd_text": None,
     "intent": "客户侧的转型岗——说服是主业，构建是佐证。对 HR / 咨询背景友好，核心是把技术判断翻译成生意语言。",
     "must": ["scoping", "influence", "hallucination", "agent_vs_wf"],
     "plus": ["structured", "vibecoding", "product"]},
]

_TERM_BY_ID = {t["id"]: t for t in TERMS}


# ---------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    return {"ok": True, "service": "hr-ai-builder-api", "version": app.version}


@app.get("/api/terms")
def list_terms(ksa: Literal["K", "S", "A"] | None = None):
    items = [t for t in TERMS if ksa is None or t["ksa"] == ksa]
    return {"count": len(items), "items": items}


@app.get("/api/topics")
def list_topics():
    return {"count": len(TOPICS), "knowledge_points": sum(t["kp"] for t in TOPICS), "items": TOPICS}


@app.get("/api/jobs")
def list_jobs():
    return {"count": len(JOBS), "items": JOBS}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    for j in JOBS:
        if j["id"] == job_id:
            return {**j,
                    "must_detail": [_TERM_BY_ID[t] for t in j["must"] if t in _TERM_BY_ID],
                    "plus_detail": [_TERM_BY_ID[t] for t in j["plus"] if t in _TERM_BY_ID]}
    raise HTTPException(404, "job not found")


@app.get("/api/quiz")
def get_quiz():
    """题干与选项，不含答案。"""
    return {"count": len(QUESTIONS),
            "items": [{k: v for k, v in q.items() if k not in ("answer", "explain")} for q in QUESTIONS]}


class QuizSubmission(BaseModel):
    answers: List[int]


@app.post("/api/quiz/submit")
def submit_quiz(sub: QuizSubmission):
    """按 K / S / A 三类分别给分——三类的补法完全不同，所以不合并成一个总分。"""
    if len(sub.answers) != len(QUESTIONS):
        raise HTTPException(400, f"expected {len(QUESTIONS)} answers, got {len(sub.answers)}")

    buckets = {"K": [0, 0], "S": [0, 0], "A": [0, 0]}   # [correct, total]
    details = []
    for q, picked in zip(QUESTIONS, sub.answers):
        correct = picked == q["answer"]
        buckets[q["ksa"]][1] += 1
        buckets[q["ksa"]][0] += int(correct)
        details.append({"id": q["id"], "ksa": q["ksa"], "correct": correct,
                        "answer": q["answer"], "explain": q["explain"]})

    advice = {
        "K": "知识缺口最容易补——按课程顺序读几章就能补上，几天的事。",
        "S": "技能缺口靠做作品补——选一个选题，配套数据集直接开工，几周到几个月。",
        "A": "能力缺口补不了，只能被重新证明——从你已有的经历里挖出证据，重构成别人认的故事。",
    }
    return {
        "scores": {k: {"correct": v[0], "total": v[1],
                       "rate": round(v[0] / v[1], 2) if v[1] else None,
                       "advice": advice[k]}
                   for k, v in buckets.items()},
        "details": details,
    }
