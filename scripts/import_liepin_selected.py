#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把逐条读完、判定通过的猎聘岗位写进 backend/main.py 的 JOBS。

来源与判据（这一批的完整口径，别改动这段说明）：
  · 信源＝猎聘。企业官网不一定维护这类岗位——京东官网社招 1751 个岗位里，
    「AI型组织人才发展专家」「HR AI产品专家」一条都没有。
  · 覆盖方式＝按公司扫（liepin_discover_companies.py 发现公司 →
    scan_liepin_batch.py 逐家扫全）。45 家公司、494 条原始候选。
  · 机器筛两道：HR 判据（标题含 HR 词 或 正文≥3 个不同 HR 词）＋ AI 强信号，剩 189 条；
    按公司限额 3 条防止被一两家灌满，剩 72 条。
  · **最后一道是人读的**：72 条逐条读 JD，按四条排除规则剔——
    ①只要求「对 AI 有热情/好奇心」 ②AI 只是并列加分项之一
    ③给 AI 业务/团队做 HR（业务是 AI，活没变） ④招 AI 人才（招的对象是 AI，活没变）
    最终通过 36 条。

高亮词不手写：用下面这张「关键词→能力项」字典去每条 JD 里找**真实存在的子串**，
找到才标。这样高亮永远锚得住（verify_jobs_jd.py 会把锚不住的当错误）。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEL = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sel.json"
MAIN = os.path.join(ROOT, "backend", "main.py")

# ── 关键词 → 能力项。只在 JD 原文里出现时才会被标上 ──────────────────
KW2CAP = {
    # S · 动手
    "Vibe Coding": "vibecoding", "Vibe coding": "vibecoding", "webcoding": "vibecoding",
    "codex": "vibecoding", "低代码/无代码工具": "vibecoding", "快速搭建并迭代": "vibecoding",
    "自研轻量化工具": "vibecoding", "动手用AI": "vibecoding",
    "Prompt 工程": "prompt", "Prompt工程": "prompt", "Prompt Engineering": "prompt",
    "RAG": "prompt", "知识图谱": "prompt", "知识库": "prompt", "智能问答": "prompt",
    "智能客服": "prompt", "AI问答": "prompt",
    "数据治理": "data_prep", "数据建模": "data_prep", "人力数据治理": "data_prep",
    "数据整理与报表自动化": "data_prep", "数据分析": "data_prep",
    "评估体系": "eval", "评测": "eval", "效果复盘": "eval", "持续复盘效果": "eval",
    "量化提效成果": "eval", "指标看板": "eval", "效果指标": "eval",
    "落地效果": "eval", "验证AI应用的落地效果": "eval",
    "上线": "ship", "规模化落地": "ship", "推广": "ship", "迭代": "ship",
    # K · 概念
    "模型输出的不确定性": "hallucination", "人工接管": "hallucination",
    "能力边界": "hallucination", "校验、审批": "hallucination", "AI 面试辅助": "hallucination",
    "智能筛选": "hallucination", "简历筛选": "hallucination", "AI辅助筛选": "hallucination",
    "Agent": "agent_vs_wf", "智能体": "agent_vs_wf", "多Agent协作": "agent_vs_wf",
    "流程自动化": "agent_vs_wf", "RPA": "agent_vs_wf", "人机协同": "agent_vs_wf",
    "AI+人工高效协同": "agent_vs_wf", "数字员工": "agent_vs_wf",
    "人力数据": "hr_data", "人效": "hr_data", "口径": "hr_data", "数据洞察": "hr_data",
    "人力成本": "hr_data", "组织诊断": "hr_data",
    "合规": "compliance", "劳动法": "compliance", "用工风险": "compliance",
    "员工体验": "compliance", "隐私": "compliance",
    # A · 判断
    "识别可 AI 化优化的环节": "scoping", "识别可AI化优化的环节": "scoping",
    "场景": "scoping", "优先级": "scoping", "路线图": "scoping", "不盲目追新": "scoping",
    "痛点": "scoping",
    "转化为": "elicitation", "梳理": "elicitation", "标准化": "elicitation",
    "流程重塑": "elicitation", "机制设计": "elicitation",
    "跨部门": "influence", "推动落地": "influence", "跨团队": "influence",
    "使用渗透率": "influence",
    "前沿趋势": "learning_agility", "持续学习": "learning_agility", "探索": "learning_agility",
    "产品设计": "product", "需求分析": "product", "产品方案": "product", "原型": "product",
    "报告": "structured", "洞察成果": "structured",
    "逻辑": "logic", "归因": "logic",
}

# ── 逐条：id / 赛道 / 组织意图 / 硬门槛 / 加分项 ────────────────────
# track: tech=技术产品侧长过来 · hr=HR 侧长出来 · rethought=老岗位被重估
META = {
 "用友网络|HRIS专家": ("uf-hris", "tech",
  "这条 JD 里有一句罕见的清醒话：「务实推动 AI 大模型、RPA、知识图谱等新技术在 HR 共享服务场景中的应用，不盲目追新」。"
  "在满屏都是「拥抱 AI」的招聘市场里，把「不盲目追新」写进职责，本身就是一种能力要求。",
  ["agent_vs_wf", "hr_data", "prompt"], ["scoping", "ship", "product"]),
 "盛伦物流|HRIS经理(J10195)": ("sl-hris", "rethought",
  "一家物流公司的 HRIS 经理，职责里写着「自研轻量化工具」。"
  "注意是「自研」不是「采购」——这就是把工程能力下放到 HR 手里的那一步。",
  ["vibecoding", "hr_data", "agent_vs_wf"], ["scoping", "ship", "data_prep"]),
 "嘉楠科技|HR 数字化 & AI 转型专员": ("kn-hr-ai", "hr",
  "岗位名直接叫「HR 数字化 & AI 转型专员」，职责第一条是「协同人力资源部负责人共同探索部门 AI 转型落地」。"
  "这不是给某个流程加个工具，是整个 HR 部门要被重做一遍，而且专门为此设了岗。",
  ["scoping", "elicitation", "agent_vs_wf"], ["hr_data", "influence", "learning_agility"]),
 "美团|美团金融-招聘经理（AI驱动）": ("mt-rec-ai", "hr",
  "招聘方自己把话说得最直白：「当 AI 正在改写招聘的每一个环节，我们希望找到一位既能『动手用 AI』、"
  "又能『懂业务语境』的招聘伙伴」「你会用 AI 工具和数据分析来做判断，而不是只靠表格和直觉」。"
  "两个能力缺一个都不行——这正是这个角色难招的原因。",
  ["vibecoding", "hr_data", "scoping"], ["hallucination", "agent_vs_wf", "logic"]),
 "美团|企业文化 AI Builder": ("mt-culture-builder", "hr",
  "岗位名叫「AI Builder」，但挂在企业文化线下。连最软的那一格——舆情、员工社区、企业文化——"
  "也开始要求你会搭东西，而不只是会写稿。",
  ["vibecoding", "prompt", "scoping"], ["agent_vs_wf", "structured", "eval"]),
 "联想|HRBP": ("lenovo-hrbp", "rethought",
  "标题还是最传统的 HRBP，职责里已经写进「依托 AI 工具、智能化管理手段优化人力流程」"
  "和「可结合人机协同场景落地人力优化方案」。老岗位被重估，长这样。",
  ["agent_vs_wf", "hr_data", "influence"], ["scoping", "learning_agility", "compliance"]),
 "锐捷网络|国际SSC专员": ("ruijie-ssc", "rethought",
  "SSC 是 HR 里最像流水线的一段。这条要求你「运用 AI 工具优化 SSC 服务流程」并「验证 AI 应用的落地效果」——"
  "注意后半句：不是用了就算，要能证明它真的更好。",
  ["agent_vs_wf", "eval", "prompt"], ["scoping", "hr_data", "ship"]),
 "新华三集团|HRSSC": ("h3c-ssc", "rethought",
  "9-20k 的基层 SSC 岗，任职要求写着「擅长运用 AI 工具处理简单重复操作性工作」。"
  "门槛最低的那一格也开始要求了——这比高薪岗位更能说明事情已经铺开。",
  ["agent_vs_wf", "hr_data"], ["prompt", "compliance", "scoping"]),
 "新华三集团|招聘专员": ("h3c-rec", "rethought",
  "「熟练 AI 招聘落地能力：智能筛选、AI 面试辅助、人才画像、招聘数据分析、招聘流程智能化」——"
  "五项全写进一个招聘专员的任职要求里，而且用的词是「熟练」不是「了解」。",
  ["hallucination", "hr_data", "agent_vs_wf"], ["prompt", "eval", "data_prep"]),
 "新华三集团|HRBP": ("h3c-hrbp", "rethought",
  "任职要求里造了个词叫「AI 力」，还要求「具备 AI HR 工作思维」。"
  "词造得糙，但意思清楚：这不是加一项技能，是换一种做 HR 的方式。",
  ["scoping", "agent_vs_wf", "influence"], ["hr_data", "learning_agility", "compliance"]),
 "英特利普(上海)信息技术有限公司北京分公司|HRSSC（员工关系）": ("intel-ssc", "rethought",
  "员工关系岗要求「推动 AI Agent 在员工服务场景的落地应用」，并且点名要「AI Agent 实操经验」。"
  "员工关系是 HR 里最讲人情的一段，连它也开始要 Agent。",
  ["agent_vs_wf", "compliance", "prompt"], ["scoping", "eval", "hr_data"]),
 "小米|COE-绩效运营": ("mi-perf-coe", "hr",
  "COE 岗写着「参与 AI Agent 的设计、调试与落地应用」——「调试」这个词很关键，"
  "它说明这不是把需求提给技术团队，是你自己要坐进去改。",
  ["agent_vs_wf", "vibecoding", "hr_data"], ["eval", "scoping", "prompt"]),
 "360|组织与人才发展专家": ("q360-otd", "hr",
  "职责第一条就是「跟踪全球 AI Native 组织、未来人才管理等前沿趋势」，还要建一个「AI+人才」信息雷达。"
  "组织与人才发展这门手艺，正在被要求先回答一个更前置的问题：组织本身会变成什么样。",
  ["scoping", "structured", "learning_agility"], ["hr_data", "influence", "elicitation"]),
 "360|组织效能AI专家": ("q360-oe-ai", "hr",
  "岗位名把「组织效能」和「AI」直接焊在一起。职责是研究 AI 原生组织的转型路径，"
  "并「设计组织效能诊断和评估指标体系」——先有量具，才谈得上变革。",
  ["scoping", "eval", "hr_data"], ["elicitation", "structured", "influence"]),
 "中关村科金|AI应用先锋（HR）(A168435)": ("zgc-ai-pioneer", "hr",
  "岗位定位写的是「作为 HR 团队的 AI 应用先锋」。「先锋」两个字暴露了真实处境："
  "公司知道 HR 该用 AI，但还没人趟过这条路，所以专门招一个人去趟。",
  ["agent_vs_wf", "scoping", "prompt"], ["hr_data", "ship", "eval"]),
 "北京思明启创科技有限公司|HRSSC": ("smqc-ssc", "hr",
  "把 AI 落进 SSC 写得极具体：基于企微/钉钉/飞书 + 大模型搭 HR 智能客服机器人，"
  "再用 RPA/AI Agent 吃掉批量入职、社保增减员这类高频重复场景。"
  "「识别高频重复、规则明确的场景」——这一句就是 Agent 与 Workflow 分界的实操版。",
  ["agent_vs_wf", "prompt", "scoping"], ["hallucination", "eval", "hr_data"]),
 "北京思明启创科技有限公司|HRIS": ("smqc-hris", "tech",
  "任职要求里出现了「熟练使用飞书 AI、webcoding、codex 等」。"
  "codex 这种词进 HR 岗位的要求栏，是这一两年才有的事。",
  ["vibecoding", "product", "hr_data"], ["agent_vs_wf", "ship", "prompt"]),
 "泰康保险集团股份有限公司|智能体架构（人力系统方向）": ("tk-agent-arch", "tech",
  "100-120k 月薪，是这个库里的天花板。职责是「设计多 Agent 协作框架，实现 HR 业务流程的自动化与智能化」，"
  "还要「构建 Agent 开发平台与工具链，降低业务场景 Agent 开发门槛」——"
  "注意最后半句：目标是让 HR 自己也能造 Agent。",
  ["agent_vs_wf", "vibecoding", "ship"], ["hr_data", "eval", "product"]),
 "泰康保险集团股份有限公司|人力资源AI产品经理（生成式AI方向）(J74435)": ("tk-hr-genai-pm", "tech",
  "「智能招聘助手、AI 晋升助手、薪酬预测模型、AI 人才发现助手」——六大模块被逐个点名。"
  "更值得看的是下一句：要「搭建 HR+AI 应用评估体系」并「量化提效成果」。做出来只是一半，证明它有用才是另一半。",
  ["product", "eval", "hallucination"], ["hr_data", "agent_vs_wf", "prompt"]),
 "歌尔股份|AI产品经理（HR领域）": ("goertek-hr-ai-pm", "tech",
  "一家做声学和智能硬件的制造业公司，专门开了「AI 产品经理（HR 领域）」。"
  "这类岗位从互联网外溢到制造业，说明它不再是大厂的实验田。",
  ["product", "hallucination", "hr_data"], ["agent_vs_wf", "prompt", "ship"]),
 "理想汽车|HR AI / HR智能化岗(A215082)": ("li-hr-ai", "hr",
  "这条几乎是我们这门课的岗位说明书：把 HR 业务问题「转化为 AI Agent 的应用场景」，"
  "再用「Prompt 工程、低代码/无代码工具或 AI 辅助工具，快速搭建并迭代 HR AI Agent 的原型（MVP/POC）」。"
  "从定义问题到做出能点的东西，全在一个人身上。",
  ["vibecoding", "agent_vs_wf", "prompt"], ["scoping", "eval", "hr_data"]),
 "理想汽车|绩效管理(A242002)": ("li-perf", "rethought",
  "标题只写「绩效管理」，职责里已经是「支持绩效管理 Agent 研发设计，能够 AI 技术嵌入绩效管理全场景」。"
  "绩效是 HR 里最讲判断、最不敢自动化的一段，它也开始了。",
  ["agent_vs_wf", "hr_data", "eval"], ["scoping", "compliance", "prompt"]),
 "中科创达|AI产品经理": ("tcl-agent-pm", "tech",
  "任职要求里有一句极其内行的话：「理解知识检索、工具调用和模型输出的不确定性，"
  "能设计校验、审批、人工接管」。承认模型会错、并为出错设计兜底——这才是把 Agent 用进企业的真门槛。",
  ["hallucination", "agent_vs_wf", "product"], ["eval", "prompt", "compliance"]),
 "众合云科集团(51社保)|AI产品经理（人力资源方向）": ("zhyk-hr-ai-pm", "tech",
  "定位写的是「业务与技术之间的桥梁」，扎在社保、薪酬、人事这些最讲口径的模块里。"
  "这类岗位真正难的不是 AI，是先把口径吵清楚。",
  ["product", "hr_data", "compliance"], ["prompt", "agent_vs_wf", "eval"]),
 "Baidu|AI产品经理（企业效能方向）(J101301)": ("baidu-eff-pm", "tech",
  "职责里点名要把 Agent 框架落进「工作会议、企业招聘、数字员工」场景，"
  "并且「搭建效果指标看板，保障企业组织效率问题可观测、可量化」。可观测、可量化——这是工程语言进了组织领域。",
  ["agent_vs_wf", "eval", "hr_data"], ["product", "scoping", "ship"]),
 "宜信公司|EHR产品经理/HRIS": ("yx-ehr-pm", "tech",
  "任职要求把「实际参与过 AI Agent 搭建、AI 智能化人力项目经验」列为优先。"
  "注意用词是「实际参与过」——招聘方已经开始区分做过和听过。",
  ["agent_vs_wf", "product", "hr_data"], ["prompt", "ship", "eval"]),
 "中航金网(北京)科技有限公司|人力资源专员HR": ("zhjw-hr", "rethought",
  "10-15k 的人力资源专员，职责里写着「主动将 AI 工具引入日常工作场景（如简历筛选、报表生成、员工服务等）」。"
  "这个薪资档位的岗位都这么写，说明要求已经沉到底层，不再只是高薪岗的点缀。",
  ["hallucination", "data_prep", "hr_data"], ["prompt", "agent_vs_wf", "scoping"]),
 "海鸿达(北京)餐饮管理有限公司|绩效管理运营专家-北京": ("hhd-perf", "rethought",
  "餐饮公司的绩效岗，写着「以 AI 思维搭建绩效管理系统，主导 AI 在绩效场景的落地应用"
  "（如 AI 评语生成、AI 结果分析、AI 异常预警等）」。三个场景各自都踩在「模型会编」的雷区上，"
  "所以这个岗位真正的难点是知道哪一步不能全交给它。",
  ["agent_vs_wf", "hallucination", "hr_data"], ["eval", "scoping", "compliance"]),
 "海鸿达(北京)餐饮管理有限公司|人力资源部制度主管-北京": ("hhd-policy", "rethought",
  "制度管理岗要「牵头搭建制度 AI 问答场景」。制度问答是 RAG 的原生场景——"
  "答案都在文件里，但没人读得完，而且答错要担责。",
  ["prompt", "compliance", "hallucination"], ["elicitation", "eval", "scoping"]),
 "新东方教育科技集团有限公司|HRSSC数字化经理(J66125)": ("xdf-ssc", "hr",
  "职责写的是「推动团队以 AI / RPA 自动化消化事务性工作量，降低人工依赖」。"
  "「降低人工依赖」这五个字，招聘方写得比大多数公司诚实。",
  ["agent_vs_wf", "scoping", "elicitation"], ["hr_data", "eval", "influence"]),
 "水滴公司|招聘运营专家(A240434)": ("sd-rec-ops", "hr",
  "开篇就写「主导 AI 在招聘全流程的落地与运营，推动公司招聘体系的智能化转型」，"
  "接着是「识别可 AI 化优化的环节，推动 AI+人工高效协同模式落地」。"
  "哪一步给 AI、哪一步留给人——这个划分本身就是这个岗位的核心产出。",
  ["scoping", "agent_vs_wf", "eval"], ["hallucination", "hr_data", "influence"]),
 "水滴公司|薪酬策略(A71504)": ("sd-comp", "rethought",
  "薪酬岗要求「将 AI 工具切实应用于薪酬分析、数据建模、方案模拟」。"
  "薪酬是最不容出错的一段数——用 AI 做方案模拟，前提是你比它更清楚口径在哪儿会打架。",
  ["hr_data", "data_prep", "eval"], ["scoping", "compliance", "logic"]),
 "水滴公司|HRBP（业务增长）(A254164)": ("sd-hrbp", "rethought",
  "有意思的是最后一条职责：「提升业务部门 AI 工具的使用渗透率与使用深度」。"
  "HRBP 不只是自己用 AI，还要负责让业务部门用起来——这是把 HR 变成了组织的 AI 推广者。",
  ["influence", "scoping", "agent_vs_wf"], ["hr_data", "learning_agility", "eval"]),
 "中粮可口可乐饮料(中国)投资有限公司|人力数智化发展经理": ("cofco-hr-digital", "hr",
  "一家快消公司的 HR 岗，职责是「推动 HR 全模块业务流程数字化重构与智能化升级，主导人力数据治理与分析」。"
  "注意是「重构」不是「优化」——传统行业动手起来，往往比互联网更狠。",
  ["hr_data", "data_prep", "elicitation"], ["scoping", "agent_vs_wf", "influence"]),
 "北森|HR SaaS资深产品经理（AI方向）": ("bs-saas-pm", "tech",
  "北森是 HR SaaS 厂商，所以这条代表的是供给侧：「探索 LLM / Agent 等 AI 技术在人力资源管理场景中的应用路径，"
  "将技术能力转化为客户可感知的产品价值」。买方在招人用 AI，卖方在招人做 AI，两头同时在动。",
  ["agent_vs_wf", "product", "scoping"], ["prompt", "eval", "hr_data"]),
 "北森|AI测评产品负责人（PBG/北京）": ("bs-assess-pm", "tech",
  "「聚焦企业招聘场景，持续研究 AI 在人才识别和评价中的应用」。"
  "人才评价是 HR 里最需要证明自己没错的一段——把 AI 放进来，评估设计的分量立刻压过模型本身。",
  ["eval", "hallucination", "product"], ["hr_data", "agent_vs_wf", "compliance"]),
}


def py_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def main():
    sel = json.load(open(SEL, encoding="utf-8"))
    src = open(MAIN, encoding="utf-8").read()
    out, miss, skipped = [], [], []
    for h in sel:
        key = f"{h['company']}|{h['title']}"
        if key not in META:
            miss.append(key)
            continue
        jid, track, intent, must, plus = META[key]
        if f'"id": "{jid}"' in src:
            skipped.append(jid)
            continue
        jd = h["full"]
        hl = {}
        for kw, cap in KW2CAP.items():
            if kw in jd and cap not in hl.values():      # 一个能力项只标一次，避免糊满
                hl[kw] = cap
        hl = dict(list(hl.items())[:8])
        loc = h.get("city", "").split("-")[0] or "—"
        entry = (
            f'    {{"track": "{track}", "id": "{jid}", "company": {py_str(h["company"])}, '
            f'"title": {py_str(h["title"])},\n'
            f'     "type": "社招", "location": {py_str(loc)}, "verified": True,\n'
            f'     "intent": {py_str(intent)},\n'
            f'     "jd_text": {py_str(jd)},\n'
            f'     "jd_kind": "full", "jd_sha": "{h["sha"]}", "source": "liepin",\n'
            f'     "apply_url": "{h["url"]}",\n'
            f'     "hl": {{{", ".join(f"{py_str(k)}: {py_str(v)}" for k, v in hl.items())}}},\n'
            f'     "must": {json.dumps(must, ensure_ascii=False)},\n'
            f'     "plus": {json.dumps(plus, ensure_ascii=False)}}},\n')
        out.append(entry)

    if miss:
        print("META 里没有这些岗位，先补上再跑：")
        for k in miss:
            print("  ·", k)
        sys.exit(1)
    if not out:
        print(f"没有新岗位可插（已存在 {len(skipped)} 条）")
        return
    m = re.search(r"^JOBS = \[", src, re.M)
    i, depth = m.end(), 1
    while depth:
        c = src[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        i += 1
    block = "    # ── 猎聘批量导入（2026-08-20）。判据见本文件顶部说明 ──\n" + "".join(out)
    src = src[:i - 1] + block + src[i - 1:]
    open(MAIN, "w", encoding="utf-8").write(src)
    print(f"插入 {len(out)} 条（跳过已存在 {len(skipped)} 条）")


if __name__ == "__main__":
    main()
