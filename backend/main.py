"""
HR AI Builder — 内容与测评 API

现阶段所有内容以 Python 常量形式内置，前端为静态站（利于 SEO），
本服务提供：内容读取接口 + 测评判分接口，供前端渐进接入。
"""
from fastapi import FastAPI, HTTPException, Depends, Response, Header
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional
from urllib.parse import quote
import os

import requests as _rq
import wechat as wx
import auth

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
    {"track": "hr", "id": "tx-tech", "company": "腾讯 · S3", "title": "AI-HR 培训生（技术&应用方向）",
     "type": "应届实习", "location": "深圳总部 · 成都", "verified": True,
     "intent": "一口气开了四个方向（创意/分析/技术&应用/沟通）——不是想清楚了，是还没想清楚这个角色该长什么样，在试。",

     "jd_text": "官方方向说明：潜在岗位方向有 HR AI 应用科学家、HR 数字化产品经理、数据工程师、后台开发等。",
     "jd_kind": "brief", "apply_url": "https://join.qq.com/post_detail.html?pid=2&id=350&tid=6",
     "hl": {"HR AI 应用科学家": "vibecoding", "数据工程师": "hr_data", "后台开发": "vibecoding"},
     "must": ["vibecoding", "hallucination", "hr_data"],
     "plus": ["prompt", "agent_vs_wf", "eval"]},
    {"track": "hr", "id": "tx-ana", "company": "腾讯 · S3", "title": "AI-HR 培训生（分析方向）",
     "type": "应届实习", "location": "深圳总部 · 上海", "verified": True,
     "intent": "分析方向单开，说明已经有一批数据在手但用不起来的场景。真正缺的不是会跑模型的人，是能把口径吵清楚的人。",

     "jd_text": "官方方向说明：潜在岗位方向有人力规划、组织发展、人才发展、薪酬管理、绩效管理等。",
     "jd_kind": "brief", "apply_url": "https://join.qq.com/post.html?query=2_93%2Cp_2",
     "hl": {"人力规划": "hr_data", "绩效管理": "data_prep"},
     "must": ["hr_data", "hallucination", "data_prep"],
     "plus": ["eval", "vibecoding", "logic"]},
    {"track": "tech", "id": "oai-people", "company": "OpenAI · People Innovation", "title": "Software Engineer, Full Stack",
     "type": "全职", "location": "Remote - US", "verified": True,
     "intent": "注意形态：这是工程师进 HR 部门，不是 HR 学 AI。这个角色正在从两头往中间长。",

     "jd_text": "About the Team\nPeople Innovation Labs is a fast-moving engineering team embedded in the People organization, focused on rethinking how we find and retain the best talent and empower everyone to do their best work. Projects range from greenfield products like OpenHouse to AI-powered automations and recruiting tools.\n\nIn this role you will\n· Own the full product development lifecycle for new people products end-to-end\n· Talk to internal stakeholders to understand their problems and design solutions to address them\n· Work with the research team, sharing feedback and iterating on applying their latest models\n· Collaborate across engineers, HRBPs, recruiters, researchers, product managers, designers, and operations personnel\n\nYour background might look like\n· 4+ years professional engineering experience in tech and product-driven companies\n· Interest in company culture and recruiting talent\n· Proficiency with JavaScript, React, and other web technologies; a backend language (Python preferred); relational databases like Postgres/MySQL\n· Interest in AI/ML (direct experience not required)\n· Ability to move quickly in an environment with loosely defined tasks and competing priorities",
     "jd_kind": "excerpt", "apply_url": "https://openai.com/careers/software-engineer-full-stack-(people-innovation)/",
     "hl": {"full product development lifecycle": "vibecoding", "end-to-end": "ship", "relational databases like Postgres/MySQL": "data_prep", "recruiting tools": "hr_data", "applying their latest models": "prompt", "AI-powered automations": "vibecoding"},
     "must": ["vibecoding", "data_prep", "ship", "compliance"],
     "plus": ["hallucination", "prompt", "hr_data"]},
    {"track": "tech", "id": "el-transform", "company": "ElevenLabs · Engineering", "title": "Internal AI Transformation",
     "type": "全职", "location": "Amsterdam · Berlin", "verified": True,
     "intent": "岗位名一个 HR 字都没有，做的却是同一件事。这是「命名空缺」最直接的证据。",

     "jd_text": "About the Role\nAs an Internal AI Engineer at ElevenLabs, you'll be embedded at the frontier of how we scale — acting as a forward-deployed engineer across our GTM, Operations, and Finance teams.\n\nWhat you'll work on\n· Designing and iterating on AI agents and workflow orchestrations using tools like Claude and n8n\n· Integrating AI systems with our core business stack — Salesforce, Slack, Ashby, and more\n· Building reusable automation services, patterns and shared templates that multiply the output of every team you touch\n· Owning experiments end-to-end: spotting the opportunity, building the solution, and measuring the impact\n· Developing evaluation and monitoring frameworks so our AI-native workflows are reliable, auditable, and safe\n\nWho you are\n· Proven experience building and shipping automations or applications in production\n· Strong familiarity with LLM capabilities, prompting strategies, RAG patterns, and a genuine passion for building agentic workflows\n· Strong Python and SQL and system design patterns (APIs, webhooks, orchestration layers)\n· A systems-thinking mindset: you design with security, auditability, and blast radius in mind",
     "jd_kind": "excerpt", "apply_url": "https://elevenlabs.io/careers/a3097257-a07a-4a7e-b9fe-b8555c1a0fa7/engineering-internal-ai-transformation",
     "hl": {"AI agents and workflow orchestrations": "agent_vs_wf", "spotting the opportunity": "scoping", "evaluation and monitoring frameworks": "eval", "measuring the impact": "eval", "building and shipping automations": "vibecoding", "multiply the output of every team": "influence"},
     "must": ["scoping", "vibecoding", "agent_vs_wf", "influence"],
     "plus": ["eval", "structured", "learning_agility"]},
    {"track": "tech", "id": "cog-tm", "company": "Cognition · Applied AI", "title": "Applied AI Transformation Manager",
     "type": "全职", "location": "New York · London", "verified": True,
     "intent": "客户侧的转型岗——说服是主业，构建是佐证。对 HR / 咨询背景友好，核心是把技术判断翻译成生意语言。",

     "jd_text": "About the Role\nTechnically oriented strategic advisors and operators who serve as trusted advisor to senior and functional leaders at enterprise accounts — identifying strategic opportunities for customers to realize value from agentic AI, and driving program delivery across several strategic accounts.\n\nWhat you'll do\n· Partner with customer leadership to identify, quantify and report value targets for productivity gains and financial impact\n· Design and build the operating model and delivery model for agentic AI\n· Oversee onboarding and rollout to thousands of engineers; build centers of excellence within accounts through tailored enablement\n· Apply world-class analytical and technical program management skills to support customer executives\n\nWhat we look for\n· 3–5 years at a major strategy consulting firm, with background in value targeting and realization and technology strategy\n· Software engineering internship or full-time experience; CS or EE degree\n· Ability to operate in ambiguous, fast-changing environments with rapid learning capacity",
     "jd_kind": "excerpt", "apply_url": "https://jobs.ashbyhq.com/cognition/2f6d29d9-1e3e-43a6-8b92-8ca5a1b23ede",
     "hl": {"identify, quantify and report value targets": "scoping", "trusted advisor": "influence", "agentic AI": "agent_vs_wf", "operating model and delivery model": "product", "value targeting and realization": "scoping"},
     "must": ["scoping", "influence", "hallucination", "agent_vs_wf"],
     "plus": ["structured", "vibecoding", "product"]},

    # ── 字节跳动（2026-08-20 官方职位接口核实；JD 为官方原文节选）──────────
    # track: tech=技术/产品侧长过来 · hr=HR 侧长出来 · rethought=老岗位被重估
    {"track": "tech", "id": "bd-vibe-pm", "company": "字节跳动 · 人力与管理部",
     "title": "AI 提效产品经理（Vibe Coding 招聘管理方向）",
     "type": "社招", "location": "北京 · 上海", "verified": True,
     "intent": "「Vibe Coding」从社区黑话变成任职要求里的硬指标，也就是最近一年的事。这条 JD 把话说白了：不是给你配工程师，是要你自己把想法变成能上线的系统。",
     "jd_text": "主导招聘业务与组织管理系统从 0 到 1 建设：深入招聘一线，围绕招聘交付、人才运营、项目管理、经营分析等场景，与业务策略团队协同完成需求分析与产品设计，并借助 AI 编程工具直接完成系统开发与上线，实现「想法→可用产品」的极短闭环；推动 AI Agent 在招聘流程落地：结合大模型能力，在简历开源、候选人评估、流程推进、信息补全等关键环节深度嵌入 Agent，探索定义招聘工作流中人与 AI 的分工模式。\n任职要求：3 年以上 B 端产品经理经验，有人力资源系统（ATS/HRIS）经验者优先；具备 Vibe Coding 实战能力，有编程基础，熟练使用至少一种 AI 编程工具。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7664901558106409221/detail",
     "hl": {"具备 Vibe Coding 实战能力": "vibecoding", "借助 AI 编程工具直接完成系统开发与上线": "vibecoding",
            "探索定义招聘工作流中人与 AI 的分工模式": "agent_vs_wf", "候选人评估": "hallucination",
            "需求分析与产品设计": "product"},
     "must": ["vibecoding", "agent_vs_wf", "product"],
     "plus": ["scoping", "ship", "hr_data"]},

    {"track": "tech", "id": "bd-talent-pm", "company": "字节跳动 · 管理研究院",
     "title": "人才系统 AI 产品经理",
     "type": "社招", "location": "上海 · 北京", "verified": True,
     "intent": "同一个岗位在四个坑上同时开——招聘这件事被重做一遍，字节是当成一条产品线在投人，不是试水。",
     "jd_text": "负责 AI 招聘的系统规划和设计，深入招聘场景，探索和设计全新的 Agent 系统形态，重新构建招聘业务流程；建立和完善数据指标体系，做好数据跟踪和问题归因分析；理解模型的能力边界，构建反馈评估体系，推动技术团队开展开发与优化工作。\n任职要求：有 AI Native / 大模型应用 / Agent 产品相关项目经验，或有 Vibe Coding 能力。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7659340330676029749/detail",
     "hl": {"探索和设计全新的 Agent 系统形态": "agent_vs_wf", "理解模型的能力边界": "hallucination",
            "构建反馈评估体系": "eval", "有 Vibe Coding 能力": "vibecoding",
            "数据指标体系": "hr_data"},
     "must": ["agent_vs_wf", "hallucination", "product"],
     "plus": ["eval", "vibecoding", "elicitation"]},

    {"track": "tech", "id": "bd-talent-aiops", "company": "字节跳动 · 人力与管理部",
     "title": "人才 AI 策略产品运营",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "JD 里直接点名 Prompt Engineering 和 RAG——这两个词进 HR 岗位的任职要求，说明招聘方已经知道自己要的是什么，不是喊口号。",
     "jd_text": "负责提升公司招聘秩序与体验，通过数据洞察与策略设计，系统性解决人才线索收集、流转、转化与整体招聘流程中存在的问题；AI 探索与应用：深入理解招聘机制、渠道、开源 / 主投动机等，挖掘影响体验、秩序和质量的关键因素；基于 Prompt Engineering、RAG 等 AI 能力，优化投递链路、人才线索管理、用户触达和运营机制执行效率。\n任职要求：能精准定义问题，并形成可执行、有优先级判断的解决策略；能够将业务问题转化为机制、流程或系统方案。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7674848577354270981/detail",
     "hl": {"基于 Prompt Engineering、RAG 等 AI 能力": "prompt", "能精准定义问题": "scoping",
            "转化为机制、流程或系统方案": "product", "数据洞察与策略设计": "hr_data"},
     "must": ["prompt", "scoping", "product"],
     "plus": ["hr_data", "logic", "eval"]},

    {"track": "tech", "id": "bd-hr-data-eng", "company": "字节跳动 · 集团信息系统",
     "title": "数据 AI 开发及应用工程师（人力方向）",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "任职要求里出现了 Agent、MCP、Skill——这是工程侧的词汇表，但岗位挂在人力方向下。两头往中间长的另一头长这样。",
     "jd_text": "负责数据开发的 AI 提效，建设端到端的 AI 开发能力；负责人力数据的 AI 应用建设，使用户可以通过 bot 等快速获取、分析、应用数据。\n任职要求：有较强的 SQL/ETL 开发能力，包括实时和离线数据处理经验，掌握大数据技术栈；掌握 AI 相关知识，如 Agent、MCP、Skill 等，有相关应用经验。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7597330156443617541/detail",
     "hl": {"掌握 AI 相关知识，如 Agent、MCP、Skill 等": "agent_vs_wf",
            "SQL/ETL 开发能力": "data_prep", "负责人力数据的 AI 应用建设": "hr_data"},
     "must": ["data_prep", "agent_vs_wf", "hr_data"],
     "plus": ["vibecoding", "ship", "prompt"]},

    {"track": "tech", "id": "bd-hr-data-ai", "company": "字节跳动 · 集团信息系统",
     "title": "人力数据 AI 应用专家",
     "type": "社招", "location": "上海", "verified": True,
     "intent": "「AI 动手能力很强」被写成任职要求第一条——排在学历和年限前面。这个排序本身就是信号。",
     "jd_text": "探索并落地 AI 在各类垂直场景中的应用，善用 Vibe coding 等方式端到端交付智能产品与解决方案，持续提升数据赋能业务的效率与体验。\n任职要求：AI 动手能力很强，能熟练运用大语言模型等智能化工具辅助数据分析与问题诊断，善用 Vibe coding 等方式端到端交付智能产品与解决方案。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7495740227756607752/detail",
     "hl": {"AI 动手能力很强": "vibecoding", "善用 Vibe coding 等方式端到端交付": "vibecoding",
            "辅助数据分析与问题诊断": "data_prep", "垂直场景中的应用": "scoping"},
     "must": ["vibecoding", "data_prep", "hr_data"],
     "plus": ["prompt", "ship", "product"]},

    {"track": "tech", "id": "bd-talent-sys", "company": "字节跳动 · 管理研究院",
     "title": "人才系统专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "「不限专业和经验」——这句写在一个要求你设计 AI 人才方案的岗位上。它赌的不是你的履历，是你能不能现在就上手。",
     "jd_text": "任职要求：本科及以上学历，不限专业和经验，有策略 / 产品或 AI 相关经验者优先；敏捷创新，对 AI 方向感兴趣，设计 AI 驱动的人才解决方案。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7507182439711803655/detail",
     "hl": {"设计 AI 驱动的人才解决方案": "scoping", "不限专业和经验": "learning_agility",
            "有策略 / 产品或 AI 相关经验者优先": "product"},
     "must": ["product", "scoping", "learning_agility"],
     "plus": ["agent_vs_wf", "elicitation", "vibecoding"]},

    {"track": "hr", "id": "bd-rec-eff", "company": "字节跳动 · Data 业务线",
     "title": "招聘效能分析师",
     "type": "社招", "location": "上海", "verified": True,
     "intent": "「人机协作效率比」——这个指标现在还没有行业标准算法，谁先把它定义清楚，谁就在定义这个岗位。",
     "jd_text": "探索 AI 工具对招聘效能的提升，如 AI 辅助筛选、AI 触达、人机协作效率比等。\n任职要求：扎实的数据分析能力，熟练使用 SQL 进行数据提取，能独立搭建 BI 看板（至少一种），熟悉 AI/RPA/低代码工具，有招聘自动化落地经验者优先。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7311574968642357554/detail",
     "hl": {"AI 辅助筛选": "hallucination", "人机协作效率比": "eval",
            "熟悉 AI/RPA/低代码工具": "vibecoding", "熟练使用 SQL 进行数据提取": "data_prep",
            "有招聘自动化落地经验": "ship"},
     "must": ["hr_data", "data_prep", "eval"],
     "plus": ["vibecoding", "scoping", "logic"]},

    {"track": "hr", "id": "bd-rec-strat", "company": "字节跳动 · Data 业务线",
     "title": "招聘策略与运营专家",
     "type": "社招", "location": "上海", "verified": True,
     "intent": "「能通过 AI 快速生产原型」写进了招聘岗的任职要求。做原型这件事，正在从工程师的活变成策略岗的基本功。",
     "jd_text": "利用 AI 工具，探索新型招聘方式，提升招聘各环节运营效率；战略支持与数据分析：研究前沿技术领域和 AI 市场动态，为业务战略提供人才洞察。\n任职要求：了解 AI 模型及相关 AI 工具，能通过 AI 快速生产原型并提高工作效率。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7628823285392378117/detail",
     "hl": {"能通过 AI 快速生产原型": "vibecoding", "探索新型招聘方式": "scoping",
            "了解 AI 模型及相关 AI 工具": "hallucination", "为业务战略提供人才洞察": "hr_data"},
     "must": ["vibecoding", "scoping", "hallucination"],
     "plus": ["prompt", "hr_data", "product"]},

    {"track": "hr", "id": "bd-channel-ops", "company": "字节跳动 · 人力与管理部",
     "title": "人才渠道策略运营",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "渠道运营是招聘里最像采购的一段。这条 JD 说明连这一段也开始要求你自己判断哪里该上模型、哪里该上规则。",
     "jd_text": "探索并落地 AI / 自动化在招聘渠道场景的应用（如渠道智能匹配、效果预测、供应商评估等），持续提升渠道运营效率与决策质量。\n任职要求：对 AI / 自动化工具在招聘或运营场景的应用有兴趣或实践。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7631490970744654085/detail",
     "hl": {"渠道智能匹配、效果预测": "agent_vs_wf", "探索并落地 AI / 自动化": "scoping",
            "决策质量": "eval"},
     "must": ["hr_data", "scoping", "agent_vs_wf"],
     "plus": ["data_prep", "eval", "logic"]},

    {"track": "hr", "id": "bd-channel-data", "company": "字节跳动 · 人力与管理部",
     "title": "人才渠道数据分析及系统运营专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "招聘 ROI 是 HR 里最难算清的一笔账——口径一换结论就翻。要 AI 来做，先得有人把口径吵定。",
     "jd_text": "探索并推动 AI 技术在招聘 ROI 管理、渠道运营及各类数据分析场景的落地应用，提升运营效率与数据处理能力。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7630737066057632005/detail",
     "hl": {"招聘 ROI 管理": "hr_data", "各类数据分析场景的落地应用": "data_prep",
            "提升运营效率": "scoping"},
     "must": ["hr_data", "data_prep", "scoping"],
     "plus": ["eval", "logic", "vibecoding"]},

    {"track": "hr", "id": "bd-mobility", "company": "字节跳动 · 人力运营",
     "title": "全球流动流程专家",
     "type": "社招", "location": "上海 · 北京", "verified": True,
     "intent": "外派、签证、跨境调动——最讲规则也最讲例外的一段流程。JD 要求「愿意深度运用」，这个措辞承认了一件事：他们也还没试出边界在哪。",
     "jd_text": "负责全球人才流动运营全链路流程梳理与优化，运用数据分析与 AI 工具提升运营质量、效率和体验。\n任职要求：熟悉或愿意深度运用 AI 工具，能将 AI 能力应用于运营提效、信息分析、流程优化和项目创新。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7530628301947242759/detail",
     "hl": {"能将 AI 能力应用于运营提效、信息分析、流程优化": "scoping",
            "全链路流程梳理与优化": "agent_vs_wf", "运营质量": "eval"},
     "must": ["hr_data", "scoping", "compliance"],
     "plus": ["prompt", "agent_vs_wf", "logic"]},

    {"track": "hr", "id": "bd-talent-strat", "company": "字节跳动 · 人力与管理部",
     "title": "人才策略运营专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "「兼顾探索用 AI 工具优化」——一个「兼顾」暴露了真实状态：这还是加在本职之外的活，不是本职本身。多数公司现在都在这一格。",
     "jd_text": "负责运营流程优化，从识别运营卡点及问题，经过综合分析提出优化方案，推动机制迭代升级，兼顾探索用 AI 工具优化相关工作。\n任职要求：过往经历不限，可用英语工作优先，对 AI 工具有探索和应用的兴趣者优先。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7669680969608546565/detail",
     "hl": {"识别运营卡点及问题": "scoping", "兼顾探索用 AI 工具优化相关工作": "learning_agility",
            "推动机制迭代升级": "ship"},
     "must": ["scoping", "logic", "learning_agility"],
     "plus": ["prompt", "hr_data", "ship"]},

    {"track": "rethought", "id": "bd-ssgjj", "company": "字节跳动 · 人力运营",
     "title": "社保公积金专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "整个 HR 里最事务、最不可能被认为需要 AI 的岗位之一——它的任职要求里现在写着「具备 AI 辅助工作的实践经验」。要看岗位是不是真的在被重估，看这一条就够了。",
     "jd_text": "推动 AI 与数字化在社保公积金运营场景中的应用落地，包括流程自动化、数据看板、智能问答等建设。\n任职要求：具备 AI 辅助工作的实践经验，或愿意探索 AI 的实际应用。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7568320293900978437/detail",
     "hl": {"具备 AI 辅助工作的实践经验": "vibecoding", "智能问答": "hallucination",
            "流程自动化": "agent_vs_wf", "数据看板": "hr_data"},
     "must": ["hr_data", "compliance", "hallucination"],
     "plus": ["prompt", "agent_vs_wf", "scoping"]},

    {"track": "rethought", "id": "bd-huzheng", "company": "字节跳动 · 人力运营",
     "title": "人才户政运营专员",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "落户政策咨询、材料审核——典型的「答案都在文件里，但没人读得完」。这正是 RAG 的原生场景，JD 里点了「知识库沉淀」。",
     "jd_text": "结合人才政策运营场景，探索并推动 AI 工具在政策咨询、申报指引、材料审核、知识库沉淀等环节的应用落地，持续提升业务处理效率、服务准确性及员工体验。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7385004077949815078/detail",
     "hl": {"政策咨询、申报指引、材料审核": "hallucination", "知识库沉淀": "prompt",
            "服务准确性": "eval"},
     "must": ["compliance", "hallucination", "prompt"],
     "plus": ["hr_data", "eval", "scoping"]},

    {"track": "rethought", "id": "bd-hrop-qa", "company": "字节跳动 · 人力运营",
     "title": "人力运营质量保障专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "质检本身就是一套 eval——先定标准、再抽样、再看抓没抓住。这个岗位的老本行，恰好是做 AI 最缺的那项能力。",
     "jd_text": "质检体系建设与优化：建立并持续完善人力运营流程的质量检查标准、流程及工具，搭建系统化的质检体系；质量问题分析与持续改进：基于质检结果进行深入分析，识别关键问题及潜在风险点；质检智能化升级：探索并实施 AI 质检等智能化手段，或引入其他工具，提高质检覆盖率与执行效率。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7511938755609364744/detail",
     "hl": {"探索并实施 AI 质检等智能化手段": "eval", "质量检查标准": "eval",
            "识别关键问题及潜在风险点": "compliance", "提高质检覆盖率": "scoping"},
     "must": ["eval", "hr_data", "compliance"],
     "plus": ["hallucination", "scoping", "logic"]},

    {"track": "rethought", "id": "bd-ethics-sys", "company": "字节跳动 · 职业道德合规",
     "title": "职业道德合规专家（系统与治理方向）",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "合规是 HR 里最保守的一格，因为出事代价最高。连它都在写「以 AI 为系统基础搭建、迭代系统」——注意措辞是「以 AI 为基础」，不是「用 AI 辅助」。",
     "jd_text": "牵头推动合规系统智能协作系统的升级落地，推动系统成为深度融合 AI 能力的智能协作平台，以 AI 为系统基础搭建、迭代系统，通过自然语言交互、数字化和自动化流程等方式提升治理效率；梳理与沉淀标准化的数据口径、指标体系与历史案件数据资产，为系统智能化与 AI 辅助能力建设夯实数据基础。\n任职要求：熟悉 AI 产品或能力者优先；具备产品思维，能够将业务需求转化为清晰的产品方案，有 AI 产品或自动化工作流相关经验者优先。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7554029852888090888/detail",
     "hl": {"以 AI 为系统基础搭建、迭代系统": "agent_vs_wf", "自然语言交互": "prompt",
            "标准化的数据口径、指标体系": "hr_data", "有 AI 产品或自动化工作流相关经验": "product",
            "历史案件数据资产": "data_prep"},
     "must": ["compliance", "hr_data", "product"],
     "plus": ["agent_vs_wf", "data_prep", "elicitation"]},

    {"track": "rethought", "id": "bd-perf-data", "company": "字节跳动 · 人力与管理部",
     "title": "绩效与激励数据分析专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "绩效和职级数据是全公司最敏感的一张表。要 AI 进这张表，先要有人把「谁能看到什么」这条线划死——JD 没写这句，但它是这个岗位真正的门槛。",
     "jd_text": "负责绩效、职级、激励相关数据体系建设，依托 AI 工具、数据看板搭建提升分析效率。\n任职要求：对组织管理和激励有好奇心，对 AI 技术和实践有好奇心。",
     "jd_kind": "excerpt",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7636610736177989893/detail",
     "hl": {"绩效、职级、激励相关数据体系建设": "hr_data", "依托 AI 工具、数据看板搭建提升分析效率": "data_prep"},
     "must": ["hr_data", "data_prep", "compliance"],
     "plus": ["eval", "logic", "vibecoding"]},
]

# 能力 → 对应练习课程（岗位库右栏「学这几节」用）
TERM_LESSONS = {
 "hallucination":  ["hallu-first-scene.html","hallu-fix-eval.html","hr-recall-vs-judge.html","zero-3.html"],
 "agent_vs_wf":    ["agent-what.html","agent-vs-workflow.html","agent-react.html","agent-stuck.html"],
 "hr_data":        ["hr-caliber-1.html","hr-caliber-2.html","context-overflow.html"],
 "compliance":     ["hr-compliance.html","ai-safety-redlines.html","harness-audit.html"],
 "vibecoding":     ["vibe-rules.html","vibe-workflow.html","vibe-debug.html","hr-project-build.html"],
 "prompt":         ["prompt-system.html","prompt-advanced.html","hr-cite-not-summarize.html","context-window.html"],
 "data_prep":      ["hr-caliber-3.html","hr-project-data.html","hr-caliber-1.html"],
 "eval":           ["eval-why.html","eval-graders.html","eval-pitfalls.html","hr-eval-negative.html"],
 "comp_design":    ["hr-caliber-2.html","hr-caliber-1.html"],
 "ship":           ["vibe-safety.html","hr-rollout.html","cc-permissions.html"],
 "logic":          ["hr-elicitation-1.html","hr-elicitation-2.html","ai-tips-boundary.html"],
 "product":        ["hr-inventory-2.html","ai-tips-scenarios.html"],
 "structured":     ["hr-project-tell.html","psy-error-comms.html","taste-spec.html"],
 "learning_agility":["ai-tips-iterate.html","start-how-to-learn.html","hr-org-3.html"],
 "influence":      ["hr-inventory-3.html","psy-captive.html","hr-rollout.html"],
 "elicitation":    ["hr-elicitation-1.html","hr-elicitation-2.html","hr-elicitation-3.html"],
 "scoping":        ["hr-inventory-1.html","hr-inventory-2.html","hr-inventory-3.html"],
}

_TERM_BY_ID = {t["id"]: t for t in TERMS}

# 可判分题库（K/S/A 分类，三种题型）—— 与课程篇章同源
import json as __json
from pathlib import Path as __Path
_QUIZ = __json.loads((__Path(__file__).parent / "quiz_bank.json").read_text("utf-8"))


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


def _term_full(tid: str):
    t = _TERM_BY_ID.get(tid)
    if not t:
        return None
    files = TERM_LESSONS.get(tid, [])
    return {**t, "lessons": [{"file": f,
                              "title": _LESSON_IDX.get(f, {}).get("title", f),
                              "free": _LESSON_IDX.get(f, {}).get("free", True)}
                             for f in files if f in _LESSON_IDX]}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    for j in JOBS:
        if j["id"] == job_id:
            return {**j,
                    "must_detail": [x for x in (_term_full(t) for t in j["must"]) if x],
                    "plus_detail": [x for x in (_term_full(t) for t in j["plus"]) if x]}
    raise HTTPException(404, "job not found")


@app.get("/api/quiz")
def get_quiz(chapter: Optional[str] = None, ksa: Literal["K", "S", "A"] | None = None,
             limit: Optional[int] = None):
    """题干与选项，**不含答案**。前端拿不到 ans，只能提交后由服务端判分。"""
    items = [q for q in _QUIZ["items"]
             if (not chapter or q["chapter"] == chapter) and (not ksa or q["ksa"] == ksa)]
    if limit:
        items = items[:limit]
    return {"count": len(items), "stats": _QUIZ["stats"], "chapters": _QUIZ["chapters"],
            "items": [{k: v for k, v in q.items() if k not in ("ans", "exp")} for q in items]}


class QuizSubmission(BaseModel):
    answers: dict          # {题目id: 答案}  single/judge→int, multi→int 列表


def _correct(q, given) -> bool:
    if q["type"] == "multi":
        return sorted(given or []) == sorted(q["ans"])
    return given == q["ans"]


@app.post("/api/quiz/submit")
def submit_quiz(sub: QuizSubmission):
    """按 K / S / A 三类**分开**给分。

    刻意不给总分：合并会掩盖「你差的到底是能补的还是补不了的」——
    K 缺口几天能补，A 缺口以年计、甚至补不了只能重新证明。一个总分把这个区别抹平了。
    """
    by_id = {q["id"]: q for q in _QUIZ["items"]}
    unknown = [k for k in sub.answers if k not in by_id]
    if unknown:
        raise HTTPException(400, f"unknown question ids: {unknown[:5]}")

    buckets = {"K": [0, 0], "S": [0, 0], "A": [0, 0]}
    details = []
    for qid, given in sub.answers.items():
        q = by_id[qid]
        ok = _correct(q, given)
        buckets[q["ksa"]][1] += 1
        buckets[q["ksa"]][0] += int(ok)
        details.append({"id": qid, "ksa": q["ksa"], "type": q["type"],
                        "correct": ok, "ans": q["ans"], "exp": q["exp"], "tag": q.get("tag", "")})

    # 分档评语 —— 每一档给的是**下一步动作**，不是评价。
    # 「有缺口」这种词说明不了任何事；「用顺序刷题把这一章全量过一遍」才是能执行的。
    VERDICT = {
        "K": [
            (0.9, "扎实", "这一章的概念你吃透了。**别在 K 上再花时间**——知识的获取成本已经趋近于零，它不构成差异。"),
            (0.7, "基本够用", "大概念有了，丢分在边界题上。**去「顺序刷题」把这一章全量过一遍**，把模糊的钉死。"),
            (0.4, "有洞", "错题集中在哪个考点，就回哪一节重读。**K 是唯一几天就能补上的一类，先把它补齐再谈别的。**"),
            (0.0, "先回去读", "概念还没建立起来，做题会一直靠猜。**先按课程顺序读完这一章，再回来重考**——题目会重新抽。"),
        ],
        "S": [
            (0.9, "扎实", "做法你是清楚的。**下一步是把它用在一个真作品上**——会做和做过是两回事，面试问的是后者。"),
            (0.7, "会做但不熟", "知道该怎么做，细节上还会踩坑。**挑一个作品选题动手做一遍**，坑会自己冒出来。"),
            (0.4, "只停在概念", "你知道有这回事，但没真做过。**S 类靠做作品补，几周到几个月**，光看课补不上来。"),
            (0.0, "还没上手", "从「一周做出能点的原型」那一节开始，**先做出一个最小的东西**，比读十节课有用。"),
        ],
        "A": [
            (0.9, "扎实", "判断力是这个角色最稀缺的东西，你有。**现在的问题是能不能讲出来**——去准备真实案例，A 类考的都是「你有没有一个例子」。"),
            (0.7, "有直觉但不稳", "多数场景判断对了，个别地方还会被带偏。**去看错题解析里的干扰项**——每个错误选项都对应一种真实的失败模式。"),
            (0.4, "判断还没成形", "A 类补不了，**只能被重新证明**：从你已有的经历里挖出证据。多数人的问题不是没有，是有但没这么归类过。"),
            (0.0, "这是最该补的一类", "**A 是唯一的长期资产，也是唯一补起来以年计的。**但先别慌——先把 K 和 S 补上，A 在做事的过程中长。"),
        ],
    }

    scores = {}
    for k, (c, t) in buckets.items():
        if not t:
            continue
        rate = round(c / t, 2)
        tier, act = next((tr, a) for lo, tr, a in VERDICT[k] if rate >= lo)
        scores[k] = {"correct": c, "total": t, "rate": rate, "level": tier, "advice": act}
    return {"scores": scores, "details": details,
            "note": "三类分开计分，不给总分 —— 合并会掩盖「差的是能补的还是补不了的」。"}


# ══════════════════════════════════════════════════════════════════
#  微信登录（双轨：开放平台网站应用 OAuth 优先，回落小程序扫码）
# ══════════════════════════════════════════════════════════════════
def _front_base() -> str:
    return (os.getenv("FRONTEND_URL") or "https://hr-ai-builder-web.onrender.com").rstrip("/")


# ── SSO 委托：登录复用 meansights 的微信登录 ─────────────────────────
# 为什么不走自有轨道：微信开放平台的授权回调域是严格同域校验，铭曦的网站应用配的
# 是 selarin.com，本站的 onrender.com 域挂不进去；小程序轨道的合法域名又要求备案。
# 而扫码、建号、发 token 在铭曦侧本来就是闭环——本站只需要当一个 HTTP 客户端：
# 拿扫码地址、轮询结果、用铭曦 token 换用户资料、签自己的 JWT。铭曦零改动。
# 附带的产品收益：两边账号天然互通（同一套 unionid 建号），漏斗不会断在注册这一步。
_MS_API = os.getenv("MS_SSO_BASE", "https://meansights-backend.onrender.com").rstrip("/")
_SSO_PREFIX = "ms:"          # scene 带此前缀 = 会话在铭曦侧，轮询走代理分支


@app.post("/api/wx/login-session")
def wx_login_session():
    """建一个登录会话。自有轨道配置了走自有；没配则委托 meansights SSO。"""
    if wx.is_any_configured():
        scene = wx.new_scene()
        out = {"scene": scene, "mode": "miniprogram"}
        if wx.web_is_configured():
            out["oauth_url"] = wx.web_authorize_url(wx.web_callback_url(), scene)
            out["mode"] = "oauth"
        return out
    # 铭曦后端睡着时冷启动要 20+ 秒——第一枪超时就直接报"没配置"是误导（实测踩过）。
    # 首次给足 28 秒等它醒，还不行再快试一枪；错误码也分开：waking ≠ not_configured。
    last_err = ""
    for tmo in (28, 8):
        try:
            r = _rq.post(f"{_MS_API}/api/wx/oauth/url", timeout=tmo)
            if r.status_code == 200:
                d = r.json()
                return {"scene": _SSO_PREFIX + d["scene"], "mode": "oauth",
                        "oauth_url": d["url"]}
            last_err = f"{r.status_code} {r.text[:120]}"
            print(f"[SSO] 铭曦 oauth/url -> {last_err}", flush=True)
        except Exception as e:
            last_err = str(e)
            print(f"[SSO] 铭曦不可达(timeout={tmo}s): {e}", flush=True)
    raise HTTPException(503, "sso_waking" if "timed out" in last_err.lower() or "timeout" in last_err.lower()
                        else "sso_unavailable")


@app.get("/api/wx/qrcode")
def wx_qrcode(scene: str, env: str = "trial"):
    """按 scene 生成小程序码 PNG（轨道 B）。"""
    if not scene:
        raise HTTPException(400, "scene_required")
    if not wx.is_configured():
        raise HTTPException(503, "miniprogram_not_configured")
    try:
        png = wx.get_qrcode(scene, env_version=("release" if env == "release" else "trial"))
    except Exception as e:
        raise HTTPException(502, f"qrcode_failed: {str(e)[:200]}")
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


class WxBind(BaseModel):
    code: str
    scene: str
    nickname: str = ""
    avatar: str = ""


@app.post("/api/wx/bind")
def wx_bind(body: WxBind):
    """壳小程序回传 {code, scene}：code2session 得 openid → 签 token → 挂到 scene 上。"""
    if not body.code or not body.scene:
        raise HTTPException(400, "code_and_scene_required")
    res = wx.code2session(body.code)
    openid = res.get("openid")
    if not openid:
        raise HTTPException(401, f"wx_code2session_failed: {res.get('errmsg', '')}")
    nickname = (body.nickname or "").strip()[:64] or f"微信用户{openid[-4:]}"
    avatar = (body.avatar or "").strip()[:512]
    token = auth.issue(openid, nickname, avatar, source="miniprogram")
    user = {"nickname": nickname, "avatar": avatar}
    if not wx.set_scene_authed(body.scene, token, user):
        raise HTTPException(410, "scene_expired")
    return {"ok": True}


@app.get("/api/wx/oauth/callback")
def wx_oauth_callback(code: str = "", state: str = ""):
    """开放平台回调（轨道 A）。签 token 后跳回前端，token 放 URL fragment——
    fragment 不会随请求发到服务器，比 query 安全。"""
    front = _front_base()
    if not code:
        return RedirectResponse(f"{front}/#login_error=no_code")
    tok = wx.web_code2token(code)
    access_token, openid = tok.get("access_token"), tok.get("openid")
    if not access_token or not openid:
        return RedirectResponse(f"{front}/#login_error={quote(str(tok.get('errmsg', 'oauth_failed')))}")

    info = wx.web_userinfo(access_token, openid) or {}
    nickname = (info.get("nickname") or "").strip()[:64] or f"微信用户{openid[-4:]}"
    avatar = (info.get("headimgurl") or "").strip()[:512]
    jwt_token = auth.issue(openid, nickname, avatar, source="oauth")

    # 会话仍在（同浏览器轮询中）→ 挂上去让轮询拿到；同时也直接把 token 带回前端。
    if state:
        wx.set_scene_authed(state, jwt_token, {"nickname": nickname, "avatar": avatar})
    return RedirectResponse(f"{front}/#token={quote(jwt_token)}")


@app.get("/api/wx/login-status")
def wx_login_status(scene: str):
    """网页轮询。authed 后返回 token，并让 scene 一次性失效。"""
    if scene.startswith(_SSO_PREFIX):
        return _sso_poll(scene[len(_SSO_PREFIX):])
    st = wx.get_scene(scene)
    if not st:
        return {"status": "expired"}
    if st.get("status") == "authed":
        wx.set_scene_authed(scene, "", None)   # 一次性：取走即作废
        return {"status": "authed", "token": st["token"], "user": st.get("user")}
    return {"status": "pending"}


def _sso_poll(ms_scene: str):
    """代理轮询铭曦。authed 时用铭曦 token 换用户资料，签发本站 JWT。"""
    try:
        r = _rq.get(f"{_MS_API}/api/wx/login-status",
                    params={"scene": ms_scene}, timeout=10)
        st = r.json()
    except Exception as e:
        print(f"[SSO] 轮询铭曦失败: {e}", flush=True)
        return {"status": "pending"}          # 网络抖动别把会话判死，下轮再试
    if st.get("status") != "authed":
        return {"status": st.get("status", "pending")}
    ms_token = st.get("token") or ""
    try:
        me = _rq.get(f"{_MS_API}/api/auth/me",
                     headers={"Authorization": f"Bearer {ms_token}"},
                     timeout=10).json()
        u = (me.get("user") or {})
    except Exception as e:
        print(f"[SSO] 换用户资料失败: {e}", flush=True)
        return {"status": "expired"}
    if not u.get("id"):
        return {"status": "expired"}
    user = {"nickname": (u.get("display_name") or "微信用户")[:64],
            "avatar": (u.get("avatar_url") or "")[:512]}
    token = auth.issue(openid=f"ms:{u['id']}", nickname=user["nickname"],
                       avatar=user["avatar"], source="ms-sso")
    print(f"[SSO] 登录成功 ms_user={u['id']}", flush=True)
    return {"status": "authed", "token": token, "user": user}


@app.get("/api/auth/config")
def auth_config():
    """前端据此决定登录入口显示什么。未配置时不报错，返回 enabled:false 让前端优雅降级。"""
    return {"wechat_enabled": wx.is_any_configured(),
            "mode": "oauth" if wx.web_is_configured() else ("miniprogram" if wx.is_configured() else None),
            "gate": "on" if _gate_on() else "off"}


@app.get("/api/me")
def me(user: dict = Depends(auth.current_user)):
    return user


# ══════════════════════════════════════════════════════════════════
#  课件内容（分层：免费章节走前端静态利于 SEO；其余走此处鉴权）
# ══════════════════════════════════════════════════════════════════
import json as _json
import re as _re
from pathlib import Path

_LESSON_DIR = Path(__file__).parent / "lessons"
_LESSON_IDX = _json.loads((_LESSON_DIR / "_index.json").read_text("utf-8"))

# ── Sparky（分诊 + 陪走）────────────────────────────────────────────
# 课程知识三层：目录(全量) / 骨架(全量) / 正文(按需)。都由 scripts/sync_backend_index.py
# 从 frontend/slides 生成——后端在 Render 上读不到 frontend/，必须提交时抽好。
def _load_layer(name: str) -> dict:
    p = _LESSON_DIR / name
    if not p.exists():                       # 缺文件不能让整个服务起不来
        print(f"[SPARKY] 缺少 {name}，该层降级为空（跑一次 scripts/sync_backend_index.py）",
              flush=True)
        return {}
    return _json.loads(p.read_text("utf-8"))


_LESSON_SKEL = _load_layer("_skeleton.json")
_LESSON_TEXT = _load_layer("_text.json")

import sparky as _sparky
app.include_router(_sparky.make_router(TERMS, JOBS, TERM_LESSONS, _LESSON_IDX,
                                       _LESSON_SKEL, _LESSON_TEXT))


# ══════════════════════════════════════════════════════════════════
#  成长记录（登录用户）：学完的节 / 章末小测成绩 / 战役状态
#  append-only：曲线需要历史；「最新态」在读取时聚合。
#  已知债：quiz 的 correct/n 是前端聚合上报的（单题判分在服务端，但一次作答的
#  汇总可被伪造）——热场站先接受，等有作弊动机的那天再把作答会话搬到服务端。
# ══════════════════════════════════════════════════════════════════
import store as _store


class ProgressIn(BaseModel):
    kind: Literal["done", "quiz", "task"]
    key: str
    value: dict = {}


_TASK_KEYS = ("monthly", "survey", "interview", "weekend")


@app.post("/api/progress")
def post_progress(p: ProgressIn, user: dict = Depends(auth.current_user)):
    if p.kind == "done" and p.key not in _LESSON_IDX:
        raise HTTPException(400, "unknown lesson")
    if p.kind == "quiz" and p.key not in _QUIZ["chapters"]:
        raise HTTPException(400, "unknown chapter")
    if p.kind == "task" and p.key not in _TASK_KEYS:
        raise HTTPException(400, "unknown task")
    v = p.value or {}
    if p.kind == "done":
        v = {"on": bool(v.get("on", True))}
    elif p.kind == "quiz":
        v = {"correct": int(v.get("correct", 0)), "n": int(v.get("n", 0))}
        if not (0 < v["n"] <= 20 and 0 <= v["correct"] <= v["n"]):
            raise HTTPException(400, "bad quiz result")
    else:
        v = {"status": str(v.get("status", ""))[:24]}
    _store.add_progress(user["openid"], p.kind, p.key, v)
    return {"ok": True}


@app.get("/api/progress")
def get_progress(user: dict = Depends(auth.current_user)):
    rows = _store.user_progress(user["openid"])          # 新→旧
    done, seen = [], set()
    quiz, task = [], {}
    for r in rows:
        k, key, v = r.get("kind"), r.get("key", ""), r.get("value") or {}
        if isinstance(v, str):                            # 内存降级模式下 value 已是 dict；库里是 jsonb 也为 dict
            try:
                v = _json.loads(v)
            except Exception:
                v = {}
        if k == "done":
            if key not in seen:                           # 新→旧：首见即最新态
                seen.add(key)
                if v.get("on"):
                    done.append(key)
        elif k == "quiz":
            quiz.append({"chapter": key, "correct": v.get("correct", 0),
                         "n": v.get("n", 0), "ts": r.get("created_at", "")})
        elif k == "task":
            task.setdefault(key, v.get("status", ""))
    best = {}
    for a in quiz:
        if a["n"]:
            pct = a["correct"] / a["n"]
            if pct > best.get(a["chapter"], -1):
                best[a["chapter"]] = pct
    return {"done": done, "quiz": quiz[::-1],             # 曲线旧→新
            "best": {c: round(p, 2) for c, p in best.items()}, "task": task}

# 登录闸开关。默认 off——全部内容匿名可读，18 节"登录内容"只显示轻提示。
# ⚠️ 开闸要动两处：paywall.js 优先读 course-data.js 的 meta.access.gate（阅读器 iframe 场景），
# 读不到才回落到这里的 /api/auth/config（直访 slides 场景）。只拨 Render 的 CONTENT_GATE
# 而不改 course-data 的 "gate":"on"，阅读器里的墙不会立起来。
def _gate_on() -> bool:
    return (os.getenv("CONTENT_GATE", "off") or "").strip().lower() in ("1", "on", "true")


def _safe_name(name: str) -> str:
    """只允许 _index.json 里登记过的文件名，杜绝路径穿越。"""
    if not _re.fullmatch(r"[A-Za-z0-9._-]+\.html", name or "") or name not in _LESSON_IDX:
        raise HTTPException(404, "lesson not found")
    return name


@app.get("/api/lessons/manifest")
def lessons_manifest():
    """前端据此渲染目录与锁标。不含正文。"""
    free = sum(1 for v in _LESSON_IDX.values() if v["free"])
    return {"gate": "on" if _gate_on() else "off",
            "free": free, "locked": len(_LESSON_IDX) - free,
            "items": _LESSON_IDX}


@app.get("/api/lessons/{name}")
def get_lesson(name: str):
    """已退役。

    课件改为全部静态托管 + 客户端 paywall（Google Flexible Sampling）——
    正文留在 HTML 里可被索引，受限部分由 .paywall-locked + JSON-LD 声明。
    把内容搬到后端保护不了任何东西（仓库 AGPL 公开），却会丢掉这些页面的 SEO。
    """
    name = _safe_name(name)
    raise HTTPException(410, {
        "gone": "lessons are served statically now",
        "static_path": f"/slides/{name}",
        "why": "Google Flexible Sampling：正文在 HTML 里可索引，客户端遮挡 + JSON-LD 声明",
    })


# ── 三章 30 问题库（KSA 分类）—— 让能力测评从 3 道样题扩到 90 题 ──
_QBANK = _json.loads((Path(__file__).parent / "question_bank.json").read_text("utf-8"))


@app.get("/api/questions")
def questions(ksa: Literal["K", "S", "A"] | None = None, chapter: Optional[str] = None):
    """面试型开放题，无标准答案——用于自评方向与准备清单，不参与自动判分。

    与 /api/quiz 的区别：quiz 是选择题、能机器判分；这里是开放题、只给「他在考什么」。
    两者按同一套 K/S/A 归类，所以能合并成一张能力画像。
    """
    items = []
    for f, qs in _QBANK["sets"].items():
        if chapter and chapter != f:
            continue
        for q in qs:
            if ksa and q["ksa"] != ksa:
                continue
            items.append({**q, "chapter": f, "title": _LESSON_IDX.get(f, {}).get("title", f)})
    return {"count": len(items), "by_ksa": _QBANK["by_ksa"],
            "note": _QBANK["note"], "items": items}


# ── 题目报错 ──────────────────────────────────────────────────────────
# 题库一定会有错题，而唯一能发现的人是做题的人。没有这个入口，错题就永远在那里。
# 注：Render free 无持久磁盘，这里只写进服务日志（Render Logs 可查），
#     不落库。等接了数据库再改成入表 —— 先有通道比先有存储重要。
class QuizReport(BaseModel):
    question_id: str
    reason: str
    contact: Optional[str] = None


@app.post("/api/quiz/report")
def report_question(body: QuizReport):
    by_id = {q["id"] for q in _QUIZ["items"]}
    if body.question_id not in by_id:
        raise HTTPException(400, "unknown question id")
    detail = (body.reason or "").strip()
    if len(detail) < 4:
        raise HTTPException(400, "reason too short")
    q = next(x for x in _QUIZ["items"] if x["id"] == body.question_id)
    print(f"[QUIZ-REPORT] id={body.question_id} ksa={q['ksa']} chapter={q['chapter']} "
          f"contact={(body.contact or '-')[:60]} reason={detail[:500]}", flush=True)
    return {"ok": True, "note": "已收到，我们会核对这道题。谢谢你帮忙纠错。"}


# ── 行为埋点接收 ───────────────────────────────────────────────────────
# Render free 无持久磁盘 —— 先进内存环形缓冲 + 打服务日志（Render Logs 可查）。
# 接了数据库再改成入表；先有数据比先有存储重要，现在是全瞎的状态。
from collections import deque as _deque

_EVENTS = _deque(maxlen=3000)


class TrackEvent(BaseModel):
    visitor_id: str
    session_id: str
    event: str
    page: str
    kind: Optional[str] = None
    in_frame: Optional[bool] = None
    ref: Optional[str] = None
    dwell_ms: Optional[int] = 0
    ts: Optional[str] = None
    extra: Optional[dict] = None


@app.post("/api/t")
def track(e: TrackEvent):
    rec = e.model_dump()
    _EVENTS.append(rec)
    if e.event != "view" or not e.in_frame:      # iframe 的 view 太吵，只记离开
        print(f"[T] {e.event} {e.kind}/{e.page} v={e.visitor_id[:8]} s={e.session_id[:8]} "
              f"dwell={e.dwell_ms}ms frame={e.in_frame}", flush=True)
    return {"ok": True}


@app.get("/api/t/stats")
def track_stats():
    """粗粒度自查（内存态，重启即清）。真正的分析等接了库再说。"""
    from collections import Counter
    views = [x for x in _EVENTS if x["event"] == "view"]
    leaves = [x for x in _EVENTS if x["event"] == "leave" and (x.get("dwell_ms") or 0) > 0]
    pages = Counter(x["page"] for x in views)
    dwell = {}
    for x in leaves:
        dwell.setdefault(x["page"], []).append(x["dwell_ms"])
    top = sorted(((p, len(v), round(sum(v) / len(v) / 1000)) for p, v in dwell.items()),
                 key=lambda r: -r[1])[:15]
    downloads = Counter((x.get("extra") or {}).get("file", "?")
                        for x in _EVENTS if x["event"] == "download")
    qz = [x.get("extra") or {} for x in _EVENTS if x["event"] == "quiz"]
    quiz_by_ch = {}
    for e in qz:
        ch = e.get("chapter", "?")
        a = quiz_by_ch.setdefault(ch, [0, 0])
        a[1] += 1
        a[0] += int(bool(e.get("correct")))
    quiz_stats = [{"chapter": c, "answered": n, "correct": k,
                   "rate": round(k / n, 2)} for c, (k, n) in quiz_by_ch.items()]
    return {
        "buffered": len(_EVENTS), "note": "内存环形缓冲，最多 3000 条，重启清空",
        "visitors": len({x["visitor_id"] for x in _EVENTS}),
        "sessions": len({x["session_id"] for x in _EVENTS}),
        "views": len(views),
        "top_pages": pages.most_common(15),
        "downloads": downloads.most_common(20),
        "avg_dwell_sec": [{"page": p, "n": n, "sec": s} for p, n, s in top],
    }
