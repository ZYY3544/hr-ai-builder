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
     "jd_text": "职位描述\n1、主导招聘业务与组织管理系统从0到1建设：深入招聘一线，围绕招聘交付、人才运营、项目管理、经营分析等场景，与业务策略团队协同完成需求分析与产品设计，并借助AI编程工具直接完成系统开发与上线，实现“想法→可用产品”的极短闭环；\n2、推动AI Agent在招聘流程落地：结合大模型能力，在简历开源、候选人评估、流程推进、信息补全等关键环节深度嵌入Agent，探索定义招聘工作流中人与AI的分工模式；\n3、搭建招聘数据体系与管理看板：整合多源数据，构建统一的数据底座，设计面向一线、管理者等多层级看板，支持数据驱动的管理决策，实现指标自动监控、异常预警与归因下钻；\n4、推动系统规模化使用与持续演进：与招聘交付团队紧密协同，持续挖掘高价值场景，推动系统在千人规模组织中落地，基于使用数据与一线反馈反向驱动产品迭代。\n\n职位要求\n1、本科及以上学历，计算机、软件工程、信息管理、人力资源管理等相关专业优先；\n2、3年以上B端产品经理经验，有人力资源系统（ATS/HRIS）、CRM、线索/销售管理、流程运营、ERP或企业内部管理系统经验者优先；\n3、具备Vibe Coding实战能力，有编程基础，熟练使用至少一种AI编程工具（TRAE/Cursor/扣子等）独立完成过可运行的Web应用开发，能处理前后端功能、API对接、数据处理与部署上线；\n4、理解LLM/Agent/RAG/Prompt Engineering等概念，有AI应用落地经验，对模型能力边界有清晰认知，能通过评测反馈体系持续优化效果；\n5、强自驱与执行力，能在不确定环境中，独立推动从需求到上线的全流程，对系统应用效果负责。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7664901558106409221/detail",
     "hl": {"借助AI编程工具直接完成系统开发与上线": "vibecoding", "具备Vibe Coding实战能力": "vibecoding", "独立完成过可运行的Web应用开发，能处理前后端功能、API对接、数据处理与部署上线": "ship", "探索定义招聘工作流中人与AI的分工模式": "agent_vs_wf", "理解LLM/Agent/RAG/Prompt Engineering等概念": "prompt", "对模型能力边界有清晰认知": "hallucination", "能通过评测反馈体系持续优化效果": "eval", "需求分析与产品设计": "product", "构建统一的数据底座": "hr_data", "持续挖掘高价值场景": "scoping"},
     "must": ["vibecoding", "agent_vs_wf", "product"],
     "plus": ["scoping", "ship", "hr_data"]},

    {"track": "tech", "id": "bd-talent-pm", "company": "字节跳动 · 管理研究院",
     "title": "人才系统 AI 产品经理",
     "type": "社招", "location": "上海 · 北京", "verified": True,
     "intent": "同一个岗位在四个坑上同时开——招聘这件事被重做一遍，字节是当成一条产品线在投人，不是试水。",
     "jd_text": "职位描述\n1、负责AI招聘的系统规划和设计，深入招聘场景，探索和设计全新的Agent系统形态，重新构建招聘业务流程；\n2、建立和完善数据指标体系，负责数据跟踪和问题归因分析，挖掘问题转化为产品设计；\n3、深入业务场景，负责需求分析，制定策略和实验，验证假设、敏捷迭代，推动产品实现目标；\n4、理解模型的能力边界，构建反馈评估体系，推动技术团队开展开发与优化工作。\n\n职位要求\n1、本科及以上学历，不限专业；\n2、有AI Native/大模型应用/Agent产品相关项目经验或有Vibe coding能力；\n3、理解Prompt、RAG、评测反馈、策略调优等AI产品落地常见方法；\n4、对“从0到1定义产品形态”有兴趣，愿意在不确定性中快速探索、迭代和验证。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7659340330676029749/detail",
     "hl": {"探索和设计全新的Agent系统形态": "agent_vs_wf", "理解模型的能力边界": "hallucination", "构建反馈评估体系": "eval", "有Vibe coding能力": "vibecoding", "理解Prompt、RAG、评测反馈、策略调优等AI产品落地常见方法": "prompt", "建立和完善数据指标体系": "hr_data", "挖掘问题转化为产品设计": "product"},
     "must": ["agent_vs_wf", "hallucination", "product"],
     "plus": ["eval", "vibecoding", "elicitation"]},

    {"track": "tech", "id": "bd-talent-aiops", "company": "字节跳动 · 人力与管理部",
     "title": "人才 AI 策略产品运营",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "JD 里直接点名 Prompt Engineering 和 RAG——这两个词进 HR 岗位的任职要求，说明招聘方已经知道自己要的是什么，不是喊口号。",
     "jd_text": "职位描述\n1、负责提升公司招聘秩序与体验，通过数据洞察与策略设计，系统性解决人才线索收集、流转、转化与整体招聘流程中存在的问题和挑战，让更多优秀的人才更顺畅地流入公司，持续提升人才密度；\n2、问题洞察与策略设计：建立并持续优化招聘秩序与体验，将复杂现象转化为清晰、有说服力的问题叙事与行动方向；围绕字节跳动在人才招聘中的核心问题，结合产品与AI能力设计并推行有效的解决方案，形式包括但不限于政策优化、流程机制、产品功能等；\n3、AI探索与应用：深入理解招聘机制、渠道、开源/主投动机等，挖掘影响体验、秩序和质量的关键因素；基于Prompt Engineering、RAG等AI能力，优化投递链路、人才线索管理、用户触达和运营机制执行效率，推动AI能力在招聘秩序与体验中的应用；\n4、指标建设与效果优化：拆解业务核心指标，搭建AI运营评估体系，建设评测集、负面案例分析机制和效果归因方法，结合离线评测、在线数据分析及AB实验等，持续验证并优化AI策略效果；通过数据分析、用户调研和案例复盘持续发现招聘秩序与体验场景中的效率问题与优化点，沉淀AI运营方法论，推动重点场景的智能化提效和运营质量；\n5、项目管理：全周期管理关键人才项目，通过高效的沟通协同，建立组织共识，推动项目落地。\n\n职位要求\n1、策略思维：能精准定义问题，并形成可执行、有优先级判断的解决策略，具备良好的业务理解与判断力；\n2、产品设计：能够将业务问题转化为机制、流程或系统方案，对用户流程、功能设计和上线迭代有较强判断；熟悉Figma或Axure，有B端产品或产品运营相关经验者优先；\n3、数据分析：数据敏感、逻辑清晰且结果导向，能独立完成业务指标拆解、效果归因和策略复盘；具备SQL能力者优先，有通过数据驱动运营优化的经验优先；\n4、结构化叙事：善于数据分析和逻辑构建，能够形成清晰、流畅、有说服力的提案和文档；\n5、项目管理：具备较强的韧性及良好的项目规划、推动和跨团队协同能力，能够以结果为导向推动复杂项目落地；有主导或深度参与复杂人才/组织/业务项目的成功实践，并能清晰阐述其策略与成果者优先；\n6、AI应用与语言能力：有AI项目相关经验，或为AI深度使用者，能够结合业务场景推动AI应用的设计与落地；具备评测集建设、效果评估或AI工作流搭建经验者优先；英文可以作为工作语言者优先。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7674848577354270981/detail",
     "hl": {"基于Prompt Engineering、RAG等AI能力": "prompt", "搭建AI运营评估体系，建设评测集、负面案例分析机制和效果归因方法": "eval", "具备评测集建设、效果评估或AI工作流搭建经验者优先": "eval", "能精准定义问题": "scoping", "能够将业务问题转化为机制、流程或系统方案": "product", "结构化叙事": "structured", "能独立完成业务指标拆解、效果归因和策略复盘": "hr_data"},
     "must": ["prompt", "scoping", "product"],
     "plus": ["hr_data", "logic", "eval"]},

    {"track": "tech", "id": "bd-hr-data-eng", "company": "字节跳动 · 集团信息系统",
     "title": "数据 AI 开发及应用工程师（人力方向）",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "任职要求里出现了 Agent、MCP、Skill——这是工程侧的词汇表，但岗位挂在人力方向下。两头往中间长的另一头长这样。",
     "jd_text": "职位描述\n1、负责字节跳动集团人力数仓建设，深入业务，理解并合理抽象业务需求，发挥数据价值，与业务团队紧密合作；\n2、负责数据开发的AI提效，建设端到端的AI开发能力；\n3、负责人力数据的AI应用建设，使用户可以通过bot等快速获取、分析、应用数据。\n\n职位要求\n1、熟悉数据仓库体系架构、数据建模方法、数据治理等知识；\n2、有较强的SQL/ETL开发能力，包括实时和离线数据处理经验，掌握大数据技术栈，包括Hadoop/Hive/Spark/OLAP引擎/Flink/Paimon等；\n3、思维逻辑清晰，具备良好的自驱力及沟通能力；\n4、掌握AI相关知识，如Agent、MCP、Skill等，有相关应用经验；\n5、有人力相关背景，熟悉人力数据优先。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7597330156443617541/detail",
     "hl": {"掌握AI相关知识，如Agent、MCP、Skill等": "agent_vs_wf", "有较强的SQL/ETL开发能力": "data_prep", "负责人力数据的AI应用建设": "hr_data", "建设端到端的AI开发能力": "vibecoding", "熟悉数据仓库体系架构、数据建模方法、数据治理等知识": "data_prep"},
     "must": ["data_prep", "agent_vs_wf", "hr_data"],
     "plus": ["vibecoding", "ship", "prompt"]},

    {"track": "tech", "id": "bd-hr-data-ai", "company": "字节跳动 · 集团信息系统",
     "title": "人力数据 AI 应用专家",
     "type": "社招", "location": "上海", "verified": True,
     "intent": "「AI 动手能力很强」被写成任职要求第一条——排在学历和年限前面。这个排序本身就是信号。",
     "jd_text": "职位描述\n1、深入了解业务场景，结合场景建设稳定、可靠的底层数据，确保数据准确、可用；同时挖掘业务背后的规律和底层逻辑，建立分析框架和模型，产出高质量的诊断报告；\n2、通过数据分析方法识别、预测业务中的关键问题并提出可落地的建议，推动拿到实际收益；\n3、探索并落地AI在各类垂直场景中的应用，善用Vibe coding等方式端到端交付智能产品与解决方案，持续提升数据赋能业务的效率与体验。\n\n职位要求\n1、AI动手能力很强，能熟练运用大语言模型等智能化工具辅助数据分析与问题诊断，善用Vibe coding等方式端到端交付智能产品与解决方案；同时对SQL、Python等常用数据处理语言有扎实的掌握和较深的理解；\n2、具备深厚的业务理解力，对数字敏感，有洞察力和框架思维，能准确定义问题、提出假设并设计解决方案；充满好奇心，能触类旁通、举一反三；\n3、具备数据分析功底，有成体系的分析框架和方法论，有丰富的实战分析经验，能独立完成从问题定义、假设拆解到深度归因的完整分析，并沉淀可复用的方法；\n4、自驱力强、主观能动性突出，跨团队推动能力好，能主动发现问题、定义目标，协调多方资源把事情实际推进落地，而非等着被安排；\n5、坚信智能化变革一定会发生，愿意主动投入、推动变革而非随波逐流；有韧性，以拿结果为最终目标，不设边界；\n6、具备数据安全与隐私保护意识，严格遵守数据管理相关规范，防范数据泄露、滥用等风险。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7495740227756607752/detail",
     "hl": {"AI动手能力很强": "vibecoding", "善用Vibe coding等方式端到端交付智能产品与解决方案": "vibecoding", "结合场景建设稳定、可靠的底层数据，确保数据准确、可用": "data_prep", "能准确定义问题、提出假设并设计解决方案": "scoping", "具备数据安全与隐私保护意识": "compliance", "对SQL、Python等常用数据处理语言有扎实的掌握": "data_prep"},
     "must": ["vibecoding", "data_prep", "hr_data"],
     "plus": ["prompt", "ship", "product"]},

    {"track": "tech", "id": "bd-talent-sys", "company": "字节跳动 · 管理研究院",
     "title": "人才系统专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "「不限专业和经验」——这句写在一个要求你设计 AI 人才方案的岗位上。它赌的不是你的履历，是你能不能现在就上手。",
     "jd_text": "职位描述\n1、负责公司人才系统的产品规划和机制设计，优化业务流程，提升人才质量；\n2、深入了解人才政策和业务目标，建立数据指标体系、洞察问题，为系统迭代提供决策；\n3、结合招聘业务需求和外部研究，完成系统规划梳理，推动立项、开发与上线。\n\n职位要求\n1、本科及以上学历，不限专业和经验，有策略/产品或AI相关经验者优先；\n2、有目标感、自驱力强，不局限于现状，能推动上下游解决复杂问题，综合多种手段找最优解；\n3、敏捷创新，对AI方向感兴趣，设计AI驱动的人才解决方案；\n4、数据敏感，基于数据找问题和机会，迭代现有的流程/机制/系统。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7507182439711803655/detail",
     "hl": {"设计AI驱动的人才解决方案": "scoping", "不限专业和经验": "learning_agility", "负责公司人才系统的产品规划和机制设计": "product", "建立数据指标体系、洞察问题": "hr_data"},
     "must": ["product", "scoping", "learning_agility"],
     "plus": ["agent_vs_wf", "elicitation", "vibecoding"]},

    {"track": "hr", "id": "bd-rec-eff", "company": "字节跳动 · Data 业务线",
     "title": "招聘效能分析师",
     "type": "社招", "location": "上海", "verified": True,
     "intent": "「人机协作效率比」——这个指标现在还没有行业标准算法，谁先把它定义清楚，谁就在定义这个岗位。",
     "jd_text": "职位描述\n1、招聘指标体系设计与运营：\n1）设计并落地分层指标考核体系，并搭建多类型员工的考核框架；\n2）定义招聘场景下不同业务和岗位的北极星指标，如交付标准、人效基线、质量底线等，并建立动态校准机制；\n3）建立指标体系的迭代机制，评估指标有效性；\n2、数据看板搭建与效能诊断：\n1）搭建招聘效能看板，根据招聘全流程数据链路，统一数据口径；\n2）输出招聘效能诊断报告和预警机制，精准定位影响招聘效率和业务效能的卡点，并给出可落地的优化建议；\n3、效能优化项目推动：\n1）主导招聘优化项目、提出关键的人才策略，追踪并提升招聘效能指标，推动招聘资源配置优化；\n2）深入理解业务特点，确保分析结论贴合实际；\n4、协作机制与组织赋能：\n1）组织并主持定期诊断会，推动数据分析、问题诊断和落地方案的执行；\n2）推动招聘团队的数据能力提升，让招聘团队“能看懂数据、会用数据做决策”；\n3）探索AI工具对招聘效能的提升，如AI辅助筛选、AI触达、人机协作效率比等。\n\n职位要求\n1、3年以上商业分析（BA）、数据分析、管理咨询或HR数据分析相关经验，有管理咨询、商业策略分析背景且做过组织人效、经营分析者优先；\n2、扎实的数据分析能力：熟练使用SQL进行数据提取，能独立搭建BI看板（至少一种），熟悉AI/RPA/低代码工具，有招聘自动化落地经验者优先；\n3、数据分析和解决方案经验：能从数据中发现瓶颈、定义问题、推动解决，而非仅停留在“描述现象”；\n4、优秀的指标设计能力：能从业务目标出发，定义North Star Metric并拆解为可执行的过程指标；\n5、强项目推动力：能跨团队推动流程变革，具备推动业务变革的积极态度；\n6、结构化思维和表达能力：能将复杂分析翻译为能看懂、一线能执行的方案。\n\n加分项\n1、理解招聘的完整链路、人才Mapping等招聘专业领域；\n2、有从0到1搭建过数据驱动的运营体系的经验；\n3、深入理解云计算、广告、电商、大模型某一领域的业务模式。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7311574968642357554/detail",
     "hl": {"探索AI工具对招聘效能的提升，如AI辅助筛选、AI触达、人机协作效率比等": "eval", "熟悉AI/RPA/低代码工具，有招聘自动化落地经验者优先": "vibecoding", "统一数据口径": "hr_data", "熟练使用SQL进行数据提取": "data_prep", "结构化思维和表达能力": "structured", "能从数据中发现瓶颈、定义问题、推动解决": "scoping"},
     "must": ["hr_data", "data_prep", "eval"],
     "plus": ["vibecoding", "scoping", "logic"]},

    {"track": "hr", "id": "bd-rec-strat", "company": "字节跳动 · Data 业务线",
     "title": "招聘策略与运营专家",
     "type": "社招", "location": "上海", "verified": True,
     "intent": "「能通过 AI 快速生产原型」写进了招聘岗的任职要求。做原型这件事，正在从工程师的活变成策略岗的基本功。",
     "jd_text": "职位描述\n1、核心负责技术与研发团队的人才供应链建设，通过数据驱动的策略优化、跨域招聘项目运营及人才生态布局，提升招聘效率与质量，支持业务长远发展；\n2、招聘效率提升与体系优化：分析全流程数据，定位瓶颈，推动系统工具优化或流程改进；建立招聘质量评估体系，跟踪差异化指标，反哺甄选标准；\n3、人才开源与渠道创新：基于业务战略，规划并制定人才地图，通过定向寻源、活动、社群运营等方式，积累潜在人才；管理和评估现有渠道效能，持续优化投入；利用AI工具，探索新型招聘方式，提升招聘各环节运营效率；\n4、专项招聘项目运营：校招人才计划：统筹目标院校合作、选拔流程设计，打造品牌项目；跨境招聘探索：研究全球人才市场，搭建跨境渠道，支持国际化人才引进；\n5、战略支持与数据分析：研究前沿技术领域和AI市场动态，为业务战略提供人才洞察；构建人效模型，分析招聘投入产出，支持人力资源规划决策。\n\n职位要求\n1、学历专业：本科及以上学历，数据科学、商业分析、管理学、经济学等相关专业优先；\n2、经验背景：HR数据分析与洞察、项目管理与运营、HR产品及系统建设等，有行业研究或研发招聘支持背景者佳；\n3、核心能力：战略与商业洞察力，能理解业务逻辑并进行战略解码；了解AI模型及相关AI工具，能通过AI快速生产原型并提高工作效率；熟练使用数据分析工具，能从数据中发现问题、驱动决策；出色的项目管理和沟通能力，能主导复杂项目，协调多方资源；中英文听说读写熟练，可作为工作语言使用。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7628823285392378117/detail",
     "hl": {"能通过AI快速生产原型并提高工作效率": "vibecoding", "利用AI工具，探索新型招聘方式": "scoping", "了解AI模型及相关AI工具": "hallucination", "建立招聘质量评估体系": "eval", "构建人效模型，分析招聘投入产出": "hr_data"},
     "must": ["vibecoding", "scoping", "hallucination"],
     "plus": ["prompt", "hr_data", "product"]},

    {"track": "hr", "id": "bd-channel-ops", "company": "字节跳动 · 人力与管理部",
     "title": "人才渠道策略运营",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "渠道运营是招聘里最像采购的一段。这条 JD 说明连这一段也开始要求你自己判断哪里该上模型、哪里该上规则。",
     "jd_text": "职位描述\n1、制定并迭代公司级人才获取渠道的策略与政策，制定各渠道的使用规则、准入标准与成本红线；\n2、基于业务人才需求与区域差异，设计渠道组合与资源分配；\n3、建立渠道效果指标体系与监测机制，定期输出洞察报告，精准定位流程与转化痛点，并将洞察转化为可落地的资源优化决策；\n4、深度对接招聘团队，支持日常招聘资源需求，推动渠道策略在一线业务中落地；\n5、探索并落地AI/自动化在招聘渠道场景的应用(如渠道智能匹配、效果预测、供应商评估等)，持续提升渠道运营效率与决策质量。\n\n职位要求\n1、本科及以上学历，3–5年渠道策略或运营相关工作经验；\n2、英语可作为工作语言，能适应跨国家/地区的沟通与协作；\n3、具备敏锐的数据洞察力与逻辑分析能力，能熟练运用数据驱动业务决策，并沉淀可复用的运营方法论与指标体系；\n4、具备体系化与策略思维，能从单点运营上升到流程优化、政策制定与资源分配决策；\n5、自我驱动力强，具备出色的跨部门沟通协调能力与端到端项目管理能力；\n6、对AI/自动化工具在招聘或运营场景的应用有兴趣或实践。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7631490970744654085/detail",
     "hl": {"探索并落地AI/自动化在招聘渠道场景的应用": "scoping", "如渠道智能匹配、效果预测、供应商评估等": "agent_vs_wf", "建立渠道效果指标体系与监测机制": "hr_data", "具备敏锐的数据洞察力与逻辑分析能力": "logic", "能从单点运营上升到流程优化、政策制定与资源分配决策": "scoping"},
     "must": ["hr_data", "scoping", "agent_vs_wf"],
     "plus": ["data_prep", "eval", "logic"]},

    {"track": "hr", "id": "bd-channel-data", "company": "字节跳动 · 人力与管理部",
     "title": "人才渠道数据分析及系统运营专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "招聘 ROI 是 HR 里最难算清的一笔账——口径一换结论就翻。要 AI 来做，先得有人把口径吵定。",
     "jd_text": "职位描述\n1、协助搭建公司招聘ROI管理体系，通过数据分析定位问题、输出管理洞察，并推动方案落地执行，持续提升整体招聘效能；\n2、负责招聘全渠道数据归集与治理，搭建并迭代渠道数据处理框架及测算模型，为渠道策略制定提供数据支撑；\n3、结合业务场景差异，探索招聘渠道的精准匹配与优化，赋能渠道使用方法和工具；\n4、开展招聘漏斗全链路数据分析，定期输出渠道效果洞察报告，提供建设性解决方案助力业务侧招聘管理优化及公司整体招聘效能提升；\n5、统筹协调招聘渠道及ROI管理相关系统需求，梳理需求优先级，协同各招聘团队推进系统建设与工具迭代落地；探索并推动AI技术在招聘ROI管理、渠道运营及各类数据分析场景的落地应用，提升运营效率与数据处理能力。\n\n职位要求\n1、本科及以上学历，5年以上HR数据运营相关工作经验；\n2、具备扎实的数据处理与分析能力、出色的业务理解力与需求转化能力；\n3、有招聘数据运营、HR数据分析或相关系统建设经验者优先；有与产品/技术团队合作推动系统需求落地的实际经验优先；\n4、英语能作为工作语言；\n5、逻辑思维清晰，具备自驱力及跨部门项目推进能力，能在复杂的多任务场景中高效交付成果。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7630737066057632005/detail",
     "hl": {"探索并推动AI技术在招聘ROI管理、渠道运营及各类数据分析场景的落地应用": "scoping", "协助搭建公司招聘ROI管理体系": "hr_data", "负责招聘全渠道数据归集与治理": "data_prep", "具备扎实的数据处理与分析能力": "data_prep", "逻辑思维清晰": "logic"},
     "must": ["hr_data", "data_prep", "scoping"],
     "plus": ["eval", "logic", "vibecoding"]},

    {"track": "hr", "id": "bd-mobility", "company": "字节跳动 · 人力运营",
     "title": "全球流动流程专家",
     "type": "社招", "location": "上海 · 北京", "verified": True,
     "intent": "外派、签证、跨境调动——最讲规则也最讲例外的一段流程。JD 要求「愿意深度运用」，这个措辞承认了一件事：他们也还没试出边界在哪。",
     "jd_text": "职位描述\n1、负责全球人才流动运营全链路流程梳理与优化，运用数据分析与AI工具提升运营质量、效率和体验；\n2、承接公司跨境人才管理重点项目，推动政策落地、流程升级与运营创新；\n3、主导相关HR系统的持续迭代与功能开发优化，联合技术团队提升自动化水平和用户体验；\n4、负责相关供应商招标采购评估、合作管理和服务质量把控，建立标准化评价机制，保障交付质量。\n\n职位要求\n1、具备优秀的中英文口头及书面沟通能力，能在跨文化、跨部门场景中清晰表达并推动共识；\n2、熟悉或愿意深度运用AI工具，能将AI能力应用于运营提效、信息分析、流程优化和项目创新；\n3、自驱力强，有韧性，能在不确定性中拆解问题、形成方案并推动执行；\n4、有跨国工作、留学经历，或全球人才流动、跨境HR项目、HR系统建设经验者优先。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7530628301947242759/detail",
     "hl": {"能将AI能力应用于运营提效、信息分析、流程优化和项目创新": "scoping", "全链路流程梳理与优化": "agent_vs_wf", "联合技术团队提升自动化水平": "ship", "能在不确定性中拆解问题、形成方案并推动执行": "logic", "推动政策落地": "compliance"},
     "must": ["hr_data", "scoping", "compliance"],
     "plus": ["prompt", "agent_vs_wf", "logic"]},

    {"track": "hr", "id": "bd-talent-strat", "company": "字节跳动 · 人力与管理部",
     "title": "人才策略运营专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "「兼顾探索用 AI 工具优化」——一个「兼顾」暴露了真实状态：这还是加在本职之外的活，不是本职本身。多数公司现在都在这一格。",
     "jd_text": "职位描述\n1、负责背调等人才引进相关规则落地，识别运行中的问题，提出解决方案并跟进实施；\n2、负责相关合规报告审核，推动相关方完成所需的后续闭环处理，主动识别问题与风险并完善后续管理机制；\n3、负责供应商管理，建立并实施质检及考核机制，持续优化服务质量与交付效率；\n4、负责运营流程优化，从识别运营卡点及问题，经过综合分析提出优化方案，推动机制迭代升级，兼顾探索用AI工具优化相关工作；\n5、参与人才引进及雇佣风险管理相关的其他专项工作。\n\n职位要求\n1、思维体系化：思路清晰，逻辑性强，能用数据说明问题；\n2、持续改进的意愿与能力：关注细节，具备主动发现、分析和解决问题的意愿和能力；\n3、协同能力强：善于沟通协调，统筹项目推动，目标感强；\n4、过往经历不限，可用英语工作优先，对AI工具有探索和应用的兴趣者优先。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7669680969608546565/detail",
     "hl": {"兼顾探索用AI工具优化相关工作": "learning_agility", "从识别运营卡点及问题": "scoping", "负责相关合规报告审核": "compliance", "建立并实施质检及考核机制": "eval", "思路清晰，逻辑性强，能用数据说明问题": "logic"},
     "must": ["scoping", "logic", "learning_agility"],
     "plus": ["prompt", "hr_data", "ship"]},

    {"track": "rethought", "id": "bd-ssgjj", "company": "字节跳动 · 人力运营",
     "title": "社保公积金专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "整个 HR 里最事务、最不可能被认为需要 AI 的岗位之一——它的任职要求里现在写着「具备 AI 辅助工作的实践经验」。要看岗位是不是真的在被重估，看这一条就够了。",
     "jd_text": "职位描述\n1、负责中国大陆社保公积金申报与缴费、员工待遇申领业务运营，包括但不限于；\n2、负责日常运营过程及结果管理，确保运营高效且交付质量达标；\n3、负责供应商驻场团队搭建和人员管理；\n4、持续发掘运营流程中的改进机会，涵盖规则、流程、系统流程、职责分工设计等方面，带领团队推进优化，实现持续改进；\n5、推动AI与数字化在社保公积金运营场景中的应用落地，包括流程自动化、数据看板、智能问答等建设。\n\n职位要求\n1、2-3年以上社保公积金运营交付相关经验，需熟悉社保公积金政策和运营实操场景，且具备持续学习能力，关注行业实践；\n2、具备良好的沟通表达和协调能力、基本的项目管理能力、业务规划能力，以及具备较强的优化意识和用户导向思维；\n3、对数据敏感，能通过数据驱动运营提升工作效果；\n4、具备AI辅助工作的实践经验，或愿意探索AI的实际应用；\n5、有过团队管理经验者优先。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7568320293900978437/detail",
     "hl": {"具备AI辅助工作的实践经验": "vibecoding", "智能问答": "hallucination", "流程自动化": "agent_vs_wf", "数据看板": "hr_data", "熟悉社保公积金政策和运营实操场景": "compliance", "涵盖规则、流程、系统流程、职责分工设计等方面": "elicitation"},
     "must": ["hr_data", "compliance", "hallucination"],
     "plus": ["prompt", "agent_vs_wf", "scoping"]},

    {"track": "rethought", "id": "bd-huzheng", "company": "字节跳动 · 人力运营",
     "title": "人才户政运营专员",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "落户政策咨询、材料审核——典型的「答案都在文件里，但没人读得完」。这正是 RAG 的原生场景，JD 里点了「知识库沉淀」。",
     "jd_text": "职位描述\n1、关注并掌握人才政策发展动向，解读并制定内部运营实施方案；\n2、协调人才政策运营实操团队分工，执行与实施人才政策运营业务操作流程，并监控业务运营质量；\n3、梳理业务痛点及运营现状分析，通过标准化、系统化方式主导推动业务运营提升改善，不断提高团队运营效率及员工申报体验；\n4、通过日常业务交互，拓展与维护公司人才政策渠道；\n5、结合人才政策运营场景，探索并推动AI工具在政策咨询、申报指引、材料审核、知识库沉淀等环节的应用落地，持续提升业务处理效率、服务准确性及员工体验。\n\n职位要求\n1、本科及以上学历，1-3年人才政策运营相关经验，熟悉区域人才政策优先；\n2、具备项目管理思维与方法，能主导项目立项到落地运营；\n3、具备良好的跨团队协作能力，内外部沟通能力；\n4、掌握Excel或其他数据分析工具，对数据有敏感度，善于从数据分析中发现并解决问题。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7385004077949815078/detail",
     "hl": {"政策咨询、申报指引、材料审核、知识库沉淀": "prompt", "持续提升业务处理效率、服务准确性": "eval", "关注并掌握人才政策发展动向": "compliance", "通过标准化、系统化方式主导推动业务运营提升改善": "agent_vs_wf", "掌握Excel或其他数据分析工具": "data_prep"},
     "must": ["compliance", "hallucination", "prompt"],
     "plus": ["hr_data", "eval", "scoping"]},

    {"track": "rethought", "id": "bd-hrop-qa", "company": "字节跳动 · 人力运营",
     "title": "人力运营质量保障专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "质检本身就是一套 eval——先定标准、再抽样、再看抓没抓住。这个岗位的老本行，恰好是做 AI 最缺的那项能力。",
     "jd_text": "职位描述\n1、质检体系建设与优化：建立并持续完善人力运营流程的质量检查标准、流程及工具，搭建系统化的质检体系；\n2、质量监控：定期对人力运营各类流程进行质检，重点监控合规性、准确性和时效性，确保运营质量稳定达标；\n3、质量问题分析与持续改进：基于质检结果进行深入分析，周期性输出质检报告，识别关键问题及潜在风险点；与HROP Global流程专家、区域团队及上下游团队协同，制定改进方案并推动落地，持续提升整体运营质量；\n4、风险事件管理：针对重大质检问题或质量事件进行及时跟踪与复盘，定位成因，推动整改闭环，完善预防机制；\n5、质检智能化升级：探索并实施AI质检等智能化手段，或引入其他工具，提高质检覆盖率与执行效率。\n\n职位要求\n1、具备独立思考和判断能力、持续学习能力和清晰的目标感，善于通过深入了解与探索，不断优化工作方法，对工作有沉淀与总结意识；\n2、逻辑清晰，熟练使用Excel等数据分析工具，具备扎实的基础数据处理与分析能力，和问题分析与报告撰写能力；\n3、有较强的推动与落地能力，能够将想法有效转化为可执行方案并跟进落实，具备良好的跨团队协作意识；\n4、责任心&韧性强，对细节高度敏感，行动敏捷，结果导向能够识别潜在风险并快速响应；\n5、英语可作为工作语言，用于跨区域沟通与协作。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7511938755609364744/detail",
     "hl": {"探索并实施AI质检等智能化手段": "eval", "建立并持续完善人力运营流程的质量检查标准、流程及工具": "eval", "重点监控合规性、准确性和时效性": "compliance", "识别关键问题及潜在风险点": "hallucination", "提高质检覆盖率与执行效率": "scoping", "熟练使用Excel等数据分析工具": "data_prep"},
     "must": ["eval", "hr_data", "compliance"],
     "plus": ["hallucination", "scoping", "logic"]},

    {"track": "rethought", "id": "bd-ethics-sys", "company": "字节跳动 · 职业道德合规",
     "title": "职业道德合规专家（系统与治理方向）",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "合规是 HR 里最保守的一格，因为出事代价最高。连它都在写「以 AI 为系统基础搭建、迭代系统」——注意措辞是「以 AI 为基础」，不是「用 AI 辅助」。",
     "jd_text": "职位描述\n1、负责中国区合规系统的整体运营与产品建设，深入理解合规团队的业务场景与使用痛点，将需求转化为清晰的产品方案，与产品、研发团队协作推动重点功能落地与配置优化，保障系统稳定、高效运行；\n2、牵头推动合规系统智能协作系统的升级落地，推动系统成为深度融合AI能力的智能协作平台，以AI为系统基础搭建、迭代系统，通过自然语言交互、数字化和自动化流程等AI能力，打通合规系统和其他内部系统，解决合规业务的瓶颈，提高工作效率；\n3、负责合规业务的数据分析与可视化建设，为案件调查、制度治理与管理决策提供数据支撑，为合规治理项目，如组织健康度调研、合规调查等提供数据分析和汇总的支持，确保数据处理准确高效；\n4、基于调查与处罚数据识别关键趋势并进行研判，提供根因分析与解决方案，撰写报告为管理决策提供支撑；\n5、梳理与沉淀标准化的数据口径、指标体系与历史案件数据资产，为系统智能化与AI辅助能力建设夯实数据基础。\n\n职位要求\n1、本科及以上学历，具备合规、调查、风控治理等相关经验，熟悉内部产品与系统（案件管理系统、人力系统、法务系统等），或者熟悉AI产品或能力者优先；\n2、数据敏感度高，具备优秀的数据统计、问题分析与洞察能力，熟练掌握Excel、SQL或其他数据分析工具；\n3、具备产品思维，能够将业务需求转化为清晰的产品方案并推动产品研发团队落地，有AI产品或自动化工作流相关经验者优先；\n4、沟通协调能力优秀，能够与调查、产品及国际化团队建立有效的合作关系；\n5、保密性和原则性强，具备良好的自我驱动力与问题解决能力，高度注重细节与准确性；\n6、英语可作为工作语言。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7554029852888090888/detail",
     "hl": {"以AI为系统基础搭建、迭代系统": "agent_vs_wf", "通过自然语言交互、数字化和自动化流程等AI能力": "prompt", "梳理与沉淀标准化的数据口径、指标体系与历史案件数据资产": "hr_data", "有AI产品或自动化工作流相关经验者优先": "product", "保密性和原则性强": "compliance", "熟练掌握Excel、SQL或其他数据分析工具": "data_prep"},
     "must": ["compliance", "hr_data", "product"],
     "plus": ["agent_vs_wf", "data_prep", "elicitation"]},

    {"track": "rethought", "id": "bd-perf-data", "company": "字节跳动 · 人力与管理部",
     "title": "绩效与激励数据分析专家",
     "type": "社招", "location": "北京", "verified": True,
     "intent": "绩效和职级数据是全公司最敏感的一张表。要 AI 进这张表，先要有人把「谁能看到什么」这条线划死——JD 没写这句，但它是这个岗位真正的门槛。",
     "jd_text": "职位描述\n1、通过数据分析、市场调研、内部访谈等方式梳理管理问题，输出匹配业务需求的优化方案；\n2、负责绩效、职级、激励相关数据体系建设，依托AI工具、数据看板搭建提升分析效率；\n3、开展跨团队协作，联动业务需求方、产品、研发等团队输出体系化数据解决方案。\n\n职位要求\n1、对组织管理和激励有好奇心，对AI技术和实践有好奇心；\n2、熟悉数据分析方法，精通SQL/Python等基本工具；\n3、有较强沟通表达和协作能力；\n4、本科及以上学历；\n5、英语可作为工作语言加分。",
     "jd_kind": "full",
     "apply_url": "https://jobs.bytedance.com/experienced/position/7636610736177989893/detail",
     "hl": {"负责绩效、职级、激励相关数据体系建设": "hr_data", "依托AI工具、数据看板搭建提升分析效率": "data_prep", "精通SQL/Python等基本工具": "data_prep", "通过数据分析、市场调研、内部访谈等方式梳理管理问题": "elicitation"},
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
    # 铭曦后端睡着时冷启动要 20-30 秒。这里只打一枪、但给足 25 秒——
    # 重试交给前端做（前端还要覆盖"本服务自己在重启"的窗口），
    # 两边各自重试会叠加成几分钟，那比失败更难受。
    try:
        r = _rq.post(f"{_MS_API}/api/wx/oauth/url", timeout=25)
        if r.status_code == 200:
            d = r.json()
            return {"scene": _SSO_PREFIX + d["scene"], "mode": "oauth",
                    "oauth_url": d["url"]}
        print(f"[SSO] 铭曦 oauth/url -> {r.status_code} {r.text[:120]}", flush=True)
    except Exception as e:
        print(f"[SSO] 铭曦不可达: {e}", flush=True)
    raise HTTPException(503, "sso_waking")


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
