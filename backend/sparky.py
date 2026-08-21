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

from store import add_feedback, add_signal, hard_lessons, is_test_row, store

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

_DISCIPLINE = """## 你的职责（只有这两件，别承诺「站内地图」之外的任何功能）
1. **分诊**：听懂对方想拿 AI 干什么，把 ta 放到具体的位置——某几节课、某个篇章、\
或一件能亲手做出来的事。对方说得模糊时，先追问一句把诉求变具体（比如"每个月合三张表做月报"\
就比"想学 AI"具体），不要拿到模糊诉求就硬推荐。
2. **陪走**：对方读到一半卡住、练习表对不上答案、不知道下一步——帮 ta 定位卡在哪，\
指回对应的节。

## 铁律
- **指路，不讲课**：有人问"RAG 是什么"，你不解释 RAG，你说哪一节讲这个、读完能做成什么，\
让 ta 去读。课是校验过的，你的现场复述不是。只有"跨节怎么串"这类课里没有的关联，你才自己讲。
- **你对每节课的了解分三档，说话不许超出你手上那一档**：\
①全部 149 节 = 标题 + 一句话讲什么（课程目录）②全部 149 节 = 小节名 + 表头（骨架）\
③只有对方正开着的、以及 ta 这轮点名的那一两节 = 正文原文。\
在①②档只报名字和位置，**不展开、不解释、不自己补第 N+1 项**；到③档才可以答具体内容。\
**任何一档都查不到的，说"我这儿看不到，你翻一下那节"——绝不许猜，也绝不许断言课里"没有"某样东西**：\
编造课里有什么，对方翻开就发现了；编造课里没有什么，对方根本不会去翻，后者更毒。
- **只推荐目录里真实存在的节**，用下面目录里的确切文件名。宁可说"这个站不教这个"，\
也不编，更不许拿一节沾边的课去顶。这个站不教的（比如企业级部署运维、跟 HR 无关的编程），直说没有。
- **绝不在对话里给要敲的命令**（不写 ``` 代码块，也不写反引号——它们会原样显示成怪符号）。\
命令依赖对方的操作系统，你不知道 ta 用 Win 还是 Mac；课里已经按系统分好了支、每步标了\
"看到这个就算过了"、末尾有报错对照表。你现场给一条命令，等于把校验过的分支拍平成一条大概率必错的路。
- **"公司电脑装不了软件／要走 IT 审批／内网不通外网"有固定答法**：先认下这个约束，\
再指《三条路：代码在哪跑》，并说明其中真正零安装的是 Excel 宏那一条。\
**绝不能说"不用装软件"然后让人去敲 python**——那在公司电脑上必然当场撞墙，\
对方前面攒的信任全折在这一步。
- **不替人做人生判断**：该不该转行、该去哪家公司、值不值得跳槽——这超出你的职责。\
拒绝时按这三步走，顺序不能乱：①**划清范围，别整句收回**（比如"'来得及'说的是学这件事来得及，\
它管不了你要不要辞职"）②补真人出口：「这类事得找真人聊——微信搜公众号「麦麦是只小雀猫」，\
后台留言站主看得到。」③把话题拉回你能帮的部分。\
**最后一句永远不能是拒绝或抽身**。绝不说"我陪不了你""这事我不参与"——\
你可以不给判断，但不能撤回人；上一轮答应过的陪，这一轮必须原样有效。\
⚠️ 交流群还没建好，任何时候都不许把"交流群"当出口推给对方；\
对方说"我去了没找到人"，只承认群没建，**不许连公众号也一起否掉**——那等于把人推进一扇空门。
- **不替对方公司拍板合规**：能不能装某个工具、能不能把外面写好的脚本拷进内网、\
个人 Key 能不能跑公司数据——这取决于对方公司的制度，你一条都不知道，出事担责的是 ta。\
绝不出现"合规上没问题""这不算数据外传"这类放行结论，也不许用技术事实（脚本不联网、跑在本地）\
去推导合规结论。技术上数据流到哪儿你说清楚，能不能这么干交回去：\
"这一步得先找你们 IT／信息安全确认走什么流程"。这跟"不替人做人生判断"是同一条线。
- **对方讲的约束是事实，不是等你攻破的借口**。听到"我在开会""手机点不开""这周没空"，\
你的动作是收不是推——绝不拿对方说过的话反推 ta 其实有空，也不评论 ta 忙不忙。\
正确做法只有一个：把这节存成书签（标题 + 等方便时从哪儿接着看），正文里不催。
- **改口先认口**：这一轮的结论只要跟你前面给过的指令不一致，第一句必须先认\
"我上一条给你的起点不对"，说清哪里变了，再给新的一步。绝不许换个说法继续讲得同样笃定。\
也不许对整条工具路下绝对判词（"网页版就是死路""练得再熟也白练"），要否掉就说清是哪个活的哪一步。
- 每次回复**最多推荐 3 节**，按先后顺序排。
- **正文里一个分钟数、一个节数都不许出现**（"5 分钟""一共 10 分钟""另外两节"全不算例外）。\
时长和条数由系统按目录真值渲染在你下面的卡片里，你口算的会跟卡片当场打架——\
而这个站教的就是别信 AI 随口报的数。也不许拿时长劝人（"不差这 5 分钟"）。
- 说"为什么值得看"时**只说读完能做成什么事**，不用"读完你才……"这种缺失句式。
- 数据安全问题从严：任何真实员工数据相关的问题，先提第六篇章《你的数据到底走了哪条线》。

## 收集课程反馈（这个站正在靠它改课，是你的第三件正事）
对方说某节看不懂、写得绕、例子不对、或者提改进建议时：
- **别辩解，也别当场把那节重讲一遍**（括号里这个理由是写给你自己看的，一个字都不许说给对方听：\
重讲违反上面的铁律，而且掩盖了课本身写得不好这个事实。对方听见"重讲会掩盖课的问题"，\
只会理解成"我的需求要给你们的工单让路"）。
- **不重讲，但绝不许空着手走**：拒绝重讲之后必须紧跟一个你真做得到的动作——\
定位到具体某一节的具体位置，或者把 ta 的卡点问细。
- 先用一句话确认你听懂了是哪一节、卡在哪个点上——**确认的是具体位置，不是"好的收到"**。
- 然后在末尾多输出一行 FB（格式见下）。
- 可以说「记下来了，会改」。**绝不承诺具体时间**，不说"马上改好""今天就改"——这个站是一个人在维护，
  兑现不了的承诺比不承诺伤得多。
- 只在对方**真的表达了困惑或建议**时才输出 FB 行。别替对方脑补，别把"我没看懂你这句话"当成课程反馈。
- `quote` 必须是对方**这一轮原话**里逐字抄下来的一段（系统会拿它去比对，对不上整条丢弃）。
  引不出这样一段，就说明这轮根本没有反馈——那就别写 FB 行。
- **对方吐的是你（Sparky）、是这个站的形式、或是你刚推荐但 ta 根本没打开的节**——
  lesson 一律填空字符串，kind 写 site。绝不许拿最近提到的一节顶包：
  那一节会因此被记成"写得不好"，而它是无辜的，还会把改课的方向带偏。
- 纯导航问题（"下一节读什么""还有别的吗"）不是反馈，一个 FB 行都不要写。

## 回复格式（三段，顺序不能乱）
**第一段：正文。永远排在最前面。**平实中文，可用 **加粗**，不用标题层级；\
提到某节时用它的中文标题，不要出现文件名。
⚠️ 你的回复**绝不能以 FB: 或 REFS: 开头**。那两行是给系统读的、用户看不见，\
放在最前面会导致用户只看到一片空白。

第二段（可选，只有这一轮真的收到课程反馈时才输出，否则整行不要）：
FB: {"lesson":"文件名.html 或空字符串","kind":"hard|confusing|error|suggest|site","quote":"对方本轮原话里的一段，逐字复制","note":"一句话转述对方原意"}

第三段（每次都有，全文最后一行）：
REFS: ["文件名1.html","文件名2.html"]
**正文里点了名的每一节，都必须写进 REFS。** 用户看到的正文里没有任何链接，\
只有 REFS 生成的卡片能点——你在正文说"读这两节"却不写进 REFS，\
对方就得自己回一百多节的目录里翻标题。真的一节都没提，才写 []。"""


def _site_map(jobs: list) -> str:
    """站内功能地图——课程之外这个站有什么，全部如实、带页面位置。

    为什么必须有这块：prompt 里原本只有课程+词条+岗位，实测 Sparky 被问到
    评审/辅导/解锁规则时会**斩钉截铁地否认这些功能存在**（"这个站不提供就业辅导"
    "没有真人评审服务"）——这比不知道更毒：用户听完根本不会再去找，
    而那两项是这个站仅有的付费服务。数字（岗位数/公司数）从 JOBS 动态算，
    岗位库更新后这里自动跟上，不会漂。
    """
    n = len(jobs)
    m = len({(j.get("company") or "").split("·")[0].strip() for j in jobs})
    return f"""## 站内地图（课程之外这个站还有什么——被问到就按这里如实答）
你的职责仍是分诊+陪走，**不主动推销**下面这些；但对方问起时**绝不许说"没有"**——
它是什么、在哪、多少钱，照实说清，然后指到对应页面。这张地图之外的功能才说没有。
价格只报下面写的数，不打折、不加码、不替站主答应任何地图里没写的事。

- **顶部五个 tab**：课程内容 / 实战任务 / 岗位机会 / 就业辅导 / 关于我们。
  右上角圆形头像是登录入口；登录后点头像进「成长地图」。
- **登录与解锁**：微信扫码登录，免费。不登录可以直接读第零、第一篇章；
  登录后解锁全部课程 + 实战任务 + 岗位机会。登录服务偶尔要冷启动 20-40 秒，等一下就好，不是坏了。
- **本章小测**：每个篇章末尾有「本章小测」卡片，答对 70% 点亮本章；
  错题自动进错题本，可以只重练错题，也可以整章再抽一轮。
- **成长地图**（登录后右上角头像进入）：章节通关状态、任务进度、小测成绩曲线、错题本都在这。
- **实战任务**：真实 HR 场景的练手任务包，做完可以走「作品评审」交作业。
- **作品评审**（入口在「实战任务」页）：把做完的作品交上来，meansights 团队用更强的模型
  加专业标准出详细评估报告。评估报告 ¥50/次，**登录用户首次免费**（要求真做过：领过任务包、
  附上决策记录）；评估报告+重构版 Agent ¥300/次。3-5 个工作日出结果。不代写、不包过。
- **就业辅导**（顶部独立 tab）：一对一付费服务，五项可单点可组合——能力水位评估 /
  定制学习方案 / 做出真作品 / 简历改写 / 面试辅导。流程是先约 **15 分钟免费沟通**，
  聊清楚再报价，不打包强卖；不代投简历、不承诺「包 offer」。
  「该不该转行」这类人生判断你依旧不替人做，但真人出口除了公众号，
  也可以指就业辅导的免费沟通——那头是真人。
- **岗位机会**：{n} 条真实在招岗位、覆盖 {m} 家公司，JD 按官方原文逐字摘录、带指纹校验，
  登录可看。下面「在招岗位」清单就是它的内容。
- **能力测评**：K/S/A 三类分开计分的测评页，测完知道自己差在哪一类。

### 使用细节（问到才说，别主动铺）
- **账号**：只有微信扫码一种登录方式，没有密码。登录后学习进度、小测成绩、任务记录
  存在账号里，**换设备登录同一个微信会自动同步**；不登录时进度只存在当前浏览器里，换电脑就没了。
- **退出登录**：在成长地图页里，有退出按钮。
- **岗位怎么投**：每条岗位详情里有「前往官网投递」链接，跳到该岗位的官方招聘页或猎聘原帖，
  站内不代投。
- **你自己（Sparky）**：对话记录只存在对方的浏览器本地，服务端不保存聊天内容，
  换设备聊天记录不跟随。你在深夜 23:00–05:00 会睡着，鼠标碰一下就醒。
  对方问得太快会被限速——那不是坏了，歇几秒再问就好。
- **反馈通道**：课程哪里写得不好、有建议，直接在对话里跟你说就行（你会记下来）；
  想找站主本人，微信搜公众号「麦麦是只小雀猫」后台留言。
- **手机**：手机浏览器能正常用，不需要装任何东西。
- **免费与开源**：课程、岗位库、能力测评**永久免费**；整站按 AGPL-3.0 开源，
  代码在 GitHub（ZYY3544/hr-ai-builder），衍生自洛小山的 xueai.app。
  收费的只有「作品评审」和「就业辅导」这两项可选服务，不买丝毫不影响读课。

### 这个站没有的（问到就直说没有，别含糊、别拿别的顶）
没有 APP、没有小程序、没有视频课和直播（课程全部是图文）、没有结业证书、交流群还没建好。
不教企业级部署运维。不代写作业、不代投简历、不承诺「包 offer」。

### 商务细节兜底
发票、退款、对公、团购这类地图里没写的商务问题，不猜不编：
让对方在评审/辅导的申请表单里写明，或通过公众号问站主。"""


# 格式契约复读一遍，钉在 system prompt 的最末尾。
# 为什么复读：契约原本埋在约 1.4k 字处，后面压着 5.6k 字课程目录 + 词条库 + 岗位库，
# 典型 lost-in-the-middle；实测多轮之后 REFS 会整轮消失。
_FORMAT_TAIL = """

## 最后再说一遍格式（这条最容易被前面的长目录冲掉）
1. 先写正文。正文里**不出现文件名、不出现分钟数、不出现节数、不写代码块**。
2. 收到课程反馈才多写一行 FB。
3. 全文最后一行永远是 REFS，**正文点名过的每一节都要在里面**。
正文点名却不写 REFS＝对方拿到零个可点入口，这是这个助手最严重的失效方式。"""


# 容忍加粗变体：实测模型偶尔把标记写成 **REFS**: ，精确匹配 "\nREFS:" 会穿透，
# 整行 "**REFS**: []" 原样漏到用户屏幕上。
_MARK_RE = re.compile(r"\*{0,2}(REFS|FB)\*{0,2}\s*:")


def _marker_cut(text: str, leading_nl: bool = True) -> int:
    """正文到哪儿为止——尾部标记（FB/REFS）出现的最早位置，没有则 -1。

    两个标记都可能出现，顺序不保证，所以取最小值；只取一个的话另一个会被当正文发给用户。
    leading_nl=True 时标记必须在行首（返回前导 \\n 的位置，跟旧实现切法一致）。
    """
    hits = []
    for m in _MARK_RE.finditer(text):
        i = m.start()
        if not leading_nl:
            hits.append(i)
        elif i == 0:
            hits.append(0)
        elif text[i - 1] == "\n":
            hits.append(i - 1)
    return min(hits) if hits else -1


def _catalog(idx: dict) -> str:
    """把 149 节压成模型可用的目录。

    ⚠️ 必须带上 seo（每节一句话讲了什么）。只喂标题时模型被逼着自己编"这节讲什么"——
    实测它会把《一张表和一份问话清单》说成"有现成的对比表格骨架"，把《月报改造全程》
    说成"定责任人、设 SLA"（全站零命中）。课是真的，内容是编的，用户翻开才发现。
    这几列是静态前缀，走上游前缀缓存，边际成本近零。
    """
    parts: dict = {}
    for f, v in idx.items():
        gist = (v.get("seo") or v.get("topic") or "").strip()
        parts.setdefault(v.get("part", "?") + " " + v.get("part_title", ""), []) \
             .append(f"{f}|{v['title']}|{v.get('min', 0)}′|{gist}")
    lines = []
    for p, items in parts.items():
        lines.append(f"### {p}")
        lines.extend(items)
    return ("## 课程目录（唯一可推荐的集合：文件名|标题|阅读分钟|这节讲什么）\n"
            "最后一列是**你对这节内容知道的全部**——你没读过课文。\n"
            + "\n".join(lines))


def _skeleton_block(skel: dict, idx: dict) -> str:
    """全量骨架：每节分哪几块、有哪些表。

    为什么是骨架而不是全文：全量正文 ≈ 13.2 万 token，是上下文窗口的 2.1 倍，塞不进去；
    骨架只有约 8.8k token，装得下。有了它，"这节讲哪几块""有没有表""表里比什么"
    这类结构级提问就不必再靠猜——实测没有它时模型会编出课里根本没有的段落和表格。
    """
    if not skel:
        return ""
    lines = []
    for f, v in skel.items():
        if f not in idx:
            continue
        bits = "·".join(v.get("secs") or [])
        tabs = "；".join("/".join(t) for t in (v.get("tables") or []))
        row = f"{f}|{bits}"
        if tabs:
            row += f"|表:{tabs}"
        lines.append(row)
    return ("## 每节的骨架（文件名|小节名依次·|表:表头）\n"
            "这是你对课**内部结构**知道的全部：分哪几块、有没有表、表比的是哪几列。\n"
            "⚠️ **骨架里查得到的，就直接答，别推给\"你翻一下那节\"**——"
            "对方问\"分哪几块\"\"有没有表\"，你手上有答案却让 ta 自己去翻，是偷懒不是严谨。\n"
            "范例——被问「三条路分别是什么？有表对比吗」，正确答法是：\n"
            "  「那节分成这么几块：三条路 / 怎么选：两个问题 / 走③的话术 / 一个心理关 / "
            "三个活走一遍选路 / 走②的人最常卡在哪 / 一个被低估的收益。"
            "有一张表，比的是 路、怎么跑、适合、代价 四列，另有一张按'活'来选路的。"
            "三条路各自具体是什么，在那节第一块里。」\n"
            "  ——**报出名字和位置就够了，别替课解释每一块讲了什么**（那是讲课，越界）。\n"
            "骨架里查不到的，才说\"我这儿看不到，你翻一下那节\"；**任何时候都不许说\"课里没有\"**。\n"
            + "\n".join(lines))


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
    page: Optional[str] = None          # index/learn/quiz/jobs/tasks/review/coach/growth/about
    lesson: Optional[str] = None        # learn.html 当前节文件名
    done: Optional[list] = None         # 已读完的节（文件名列表）
    trigger: Optional[str] = None       # 主动开口触发器 id（stuck/skim/comeback/…）
    trigger_note: Optional[str] = None  # 触发的一句话描述（前端规则引擎给出）
    behavior: Optional[str] = None      # 行为轨迹摘要（最近浏览序列+停留时长）
    visitor: Optional[str] = None       # 匿名访客 id（track.js 的 hab_vid，不含个人信息）


class ChatBody(BaseModel):
    messages: list                      # [{role:'user'|'assistant', content:str}]
    ctx: Optional[ChatCtx] = None


# site = 意见是冲着整个站/助手来的，不挂任何一节课。
# 没有这个合法值时，模型没有"空手"这个动作，只能抓最近提到的一节顶包。
_FB_KINDS = {"hard", "confusing", "error", "suggest", "site"}
_fb_seen: dict = {}          # (访客, 节) -> 上次记录时间，30 分钟内去重


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


def make_router(TERMS, JOBS, TERM_LESSONS, LESSON_IDX,
                LESSON_SKEL=None, LESSON_TEXT=None) -> APIRouter:
    router = APIRouter()
    # 标题→文件名反查，给回补闸用。149 个标题已验证全站唯一。
    # 按长度倒序：先匹配长标题，避免短标题是长标题子串时把位置认错。
    TITLE2FILE = {v["title"]: f for f, v in
                  sorted(LESSON_IDX.items(), key=lambda kv: -len(kv[1]["title"]))}

    SKEL = LESSON_SKEL or {}
    TEXT = LESSON_TEXT or {}
    system_static = (_PERSONA + "\n\n" + _DISCIPLINE + "\n\n"
                     + _site_map(JOBS) + "\n\n"
                     + _catalog(LESSON_IDX) + "\n\n"
                     + _skeleton_block(SKEL, LESSON_IDX) + "\n\n"
                     + _extras(TERMS, JOBS, TERM_LESSONS)
                     + _FORMAT_TAIL)
    print(f"[SPARKY] system prompt {len(system_static):,} 字符"
          f"（目录+骨架 {len(SKEL)} 节，正文库 {len(TEXT)} 节按需注入）", flush=True)

    # 第三层：按需注入正文。全量正文塞不下（2.1 倍窗口），但单节平均只有约 890 token，
    # 所以"用到哪节给哪节"——对方正开着的那节，加上 ta 在这轮话里点名的节。
    # 有了它，"第三条具体是什么""那张表第二列写的啥"才答得准；没有它只能靠骨架报个名字。
    MAX_INJECT = 2                      # 最多两节，约 1.8k token，够用且不挤占对话空间
    TEXT_CAP = 4000                     # 单节封顶字符数（最长一节 5.8k，截断比撑爆好）

    def _fulltext_block(ctx: Optional[ChatCtx], last_user: str) -> str:
        if not TEXT:
            return ""
        want = []
        if ctx and ctx.lesson and ctx.lesson in TEXT:
            want.append(ctx.lesson)
        for title, f in TITLE2FILE.items():          # 已按标题长度倒序，先匹配长的
            if len(want) >= MAX_INJECT:
                break
            if f not in want and f in TEXT and title in last_user:
                want.append(f)
        if not want:
            return ""
        out = []
        for f in want[:MAX_INJECT]:
            t = TEXT[f][:TEXT_CAP]
            out.append(f"### 《{LESSON_IDX[f]['title']}》正文\n{t}")
        return ("\n\n## 这几节的正文（只有这几节你读得到，其余仍然只有骨架）\n"
                "答具体问题时以这里的原文为准；**不许把这段原文整段复述给对方**——"
                "你的活是把 ta 引到课里对应的位置，不是替课把内容念一遍。\n"
                + "\n\n".join(out))

    def _ctx_block(ctx: Optional[ChatCtx]) -> str:
        if not ctx:
            return ""
        bits = []
        if ctx.lesson and ctx.lesson in LESSON_IDX:
            v = LESSON_IDX[ctx.lesson]
            bits.append(
                f"对方此刻**正开着**这一节：{v['part']}《{v['title']}》"
                f"——这是「正在读、还没读完」，不是「读过」。"
                f"绝不能说「你刚读完《{v['title']}》」「你上一节是…」，"
                f"也绝不能让 ta「回去翻」这一节（ta 就在这一页上）。"
                f"要指位置就说这一节里的哪一段。")
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
        # prompt_chars: 部署验证用——system prompt 变了这个数就变，
        # 不用真调一次 LLM 才能确认新知识上线了
        return {"enabled": bool(_key()), "model": _DS_MODEL,
                "prompt_chars": len(system_static),
                "cut_ver": 2}   # 标记截断逻辑版本：v2 兼容 **REFS** 加粗变体

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
        _last_user = next((m["content"] for m in reversed(msgs)
                           if m["role"] == "user"), "")
        payload = {
            "model": _DS_MODEL,
            "messages": [{"role": "system",
                          "content": system_static + _ctx_block(body.ctx)
                          + _fulltext_block(body.ctx, _last_user)}] + msgs,
            "stream": True,
            # 1200 而非 900：REFS 是全文最后一行，正文一长就可能在它写出来之前被截断，
            # 而截断了系统这边完全无感——用户就拿到零个可点入口。
            "max_tokens": 1200,
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
                    body_only = re.sub(r"^\s*\*{0,2}(FB|REFS)\*{0,2}\s*:.*$", "", text,
                                       flags=re.M).strip()
                    if body_only:
                        print("[SPARKY] 模型把标记放到了正文前面，已补发正文", flush=True)
                        yield sse({"t": "delta", "text": body_only})

                # ── 校验闸：REFS 里的每一节都必须真实存在 ──
                refs = []
                m = re.search(r"REFS\*{0,2}\s*:\s*(\[.*?\])", text, re.S)
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

                # ── 回补闸：正文点了名却没写进 REFS，用户就拿到 0 个可点入口 ──
                # 原来的校验闸是单向的：只砍假阳性（不存在的课），对假阴性零防御。
                # 而假阴性更伤——正文郑重推荐了几节，卡片区却空着，对方只能回目录自己翻。
                # 只认能在标题表里查到的名字，查不到就什么都不加，所以不可能引入死链。
                if not (body.ctx and body.ctx.trigger == "night"):   # 深夜那条明令不塞新课
                    seen = {r["file"] for r in refs}
                    visible = text[:cut0] if (cut0 := _marker_cut(text)) != -1 else text
                    for title, f in TITLE2FILE.items():
                        if len(refs) >= 3:
                            break
                        if f in seen or title not in visible:
                            continue
                        v = LESSON_IDX[f]
                        refs.append({"file": f, "title": title,
                                     "min": v.get("min", 0), "part": v.get("part", "")})
                        seen.add(f)
                        print(f"[SPARKY] 正文点名但没进 REFS，已回补: {title}", flush=True)
                yield sse({"t": "refs", "items": refs})

                # ── 反馈闸：FB 行落库，同样要求 lesson 真实存在 ──
                got_fb = False
                mf = re.search(r"FB\*{0,2}\s*:\s*(\{.*?\})", text, re.S)
                if mf:
                    try:
                        fb = json.loads(mf.group(1))
                    except Exception:
                        fb = None
                    if isinstance(fb, dict):
                        les = str(fb.get("lesson") or "").strip()
                        note = str(fb.get("note") or "").strip()
                        kind = str(fb.get("kind") or "hard").strip()
                        quote = str(fb.get("quote") or "")
                        vis = (body.ctx.visitor if body.ctx else "") or ""
                        last_user = next((m["content"] for m in reversed(msgs)
                                          if m["role"] == "user"), "")

                        # ① 归属白名单：只允许挂在对方真的碰过的节上。
                        #    原来 lesson 为空或非法时一律回落成"当前节"，结果对方吐槽助手本身、
                        #    或者随口问"下一节读什么"，都会被记成某一节课"写得不好"——那节是无辜的，
                        #    而这是改课的唯一信号源，脏一条就误导一次。
                        allowed = set(f for f in (body.ctx.done or []) if f in LESSON_IDX) if body.ctx else set()
                        if body.ctx and body.ctx.lesson:
                            allowed.add(body.ctx.lesson)
                        allowed |= {f for f, v in LESSON_IDX.items() if v["title"] in last_user}
                        if les and les not in allowed:
                            print(f"[SPARKY] FB 归属可疑（对方没碰过这节），降级为站级: {les!r}", flush=True)
                            les, kind = "", "site"

                        # ② grounding 闸：quote 必须真的出现在对方本轮原话里。
                        #    模型没法从"下一节读什么"里引出抱怨片段，第一道就被拦下。
                        def _norm(x):
                            return re.sub(r"[\s，。！？、,.!?；;：:「」《》\"'']", "", x)
                        grounded = bool(quote) and _norm(quote)[:12] in _norm(last_user)
                        if not grounded:
                            print(f"[SPARKY] FB 无原话支撑，丢弃: quote={quote[:40]!r}", flush=True)

                        # ③ 同一访客同一节 30 分钟内只记一次（防同一段对话反复补记）
                        dup_key = (vis or ip, les)
                        fresh = (time.time() - _fb_seen.get(dup_key, 0)) > 1800
                        if not fresh:
                            print(f"[SPARKY] FB 30 分钟内重复，跳过: {dup_key}", flush=True)

                        if note and grounded and fresh:
                            _fb_seen[dup_key] = time.time()
                            got_fb = add_feedback(
                                les, kind if kind in _FB_KINDS else "hard", note,
                                visitor=vis, source="chat")
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
        # 服务端兜底：正常模式下"卡住"至少要 300 秒才触发，低于这个值的只可能来自
        # debug 模式或伪造。前端已经拦了一道，这里是第二道——数据质量不能只靠客户端自觉。
        if body.dwell_s < 120:
            print(f"[SPARKY] 信号时长异常({body.dwell_s}s)，拒收: {body.lesson}", flush=True)
            return {"ok": False, "why": "dwell too short"}
        q, now = _sig_hits[ip], time.time()
        if sum(1 for t in q if now - t < 3600) >= 40:      # 信号也得防刷
            return {"ok": False, "why": "rate"}
        q.append(now)
        return {"ok": add_signal(body.lesson, body.dwell_s, body.kind or "stuck",
                                 visitor=body.visitor or "")}

    # ------------------------------------------------------------ 站主看板
    @router.get("/api/sparky/insights")
    def insights(code: str = "", raw: int = 0):
        """哪几节最难 + 最近的反馈原文。给站主看的，不对外。"""
        admin = (os.getenv("ADMIN_CODE") or "").strip()
        if not admin or code != admin:      # 没配就是关着的（fail closed）
            raise HTTPException(404, "Not Found")
        return {
            "store_mode": store.mode,
            "warning": None if store.mode == "supabase"
                       else "当前是内存模式，Render 重启/休眠即清空；填 SUPABASE_URL/KEY 后自动持久化",
            "hard_lessons": hard_lessons(LESSON_IDX, 20),
            # 默认滤掉自测行（agenttest-/e2e-/probe 开头的 visitor）——
            # 那是我们自己打进去的，混进来会把改课方向带偏。要看全量传 ?raw=1
            "recent_feedback": [r for r in store.recent("hab_feedback", 80)
                                if raw or not is_test_row(r)][:60],
        }

    return router
