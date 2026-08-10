/* HR AI Builder 课程数据 v2 —— 单一真相源。
   衍生自洛小山 learn-ai (AGPL-3.0)，面向 HR 重构。
   action: copy=沿用 / adapt=重写成 HR 场景 / new=原创
   free:   true=静态直读(SEO) / false=登录后经 API 读
   spine:  是否属于「简历初筛」主线案例
   seo:    页面 title（长·含中文问句），与目录标题(短·带术语)解耦 */
window.COURSE = {
 "meta": {
  "title": "HR AI Builder",
  "subtitle": "读懂 AI 的底层逻辑，做 AI Native 组织的先驱者",
  "spine": {
   "case": "简历初筛",
   "note": "主线案例，从第一篇章「它会编：筛简历现场」一路贯穿到第五篇章「AI 该有多大的自由」。各章另配薪酬/组织/政策问答等副线例子，避免全课只剩招聘一个场景。"
  },
  "attribution": {
   "note": "本课程在洛小山《AI 产品从入门到精通》基础上衍生，面向 HR 领域重构。依 AGPL-3.0 开源并保留原作者署名。",
   "author": "洛小山",
   "repo": "https://github.com/itshen/learn-ai",
   "site": "https://xueai.app",
   "license": "AGPL-3.0"
  },
  "stats": {
   "parts": 8,
   "lessons": 87,
   "copy": 40,
   "adapt": 20,
   "new": 27,
   "ready": 76,
   "todo": 11,
   "spine": 18
  },
  "access": {
   "free": 68,
   "locked": 19,
   "rule": "开篇与第零篇章全免费；其余篇章每个主题前 2 节免费。免费≠收费墙——全部内容永久免费，登录只用于同步进度与防止内容被批量贩卖。"
  }
 },
 "parts": [
  {
   "id": "p-start",
   "num": "开篇",
   "title": "开始之前",
   "desc": "先搞清楚你在哪、怎么学，以及为什么 HR 也值得花时间弄懂原理。",
   "freeWhole": true,
   "topics": [
    {
     "title": "入门与定位",
     "desc": "先搞清楚我们在哪里、为什么要打基础",
     "lessons": [
      {
       "file": "0-intro.html",
       "action": "copy",
       "ksa": "K",
       "title": "我们在哪里？达克效应",
       "seo": "AI 学习者的达克曲线：你现在在哪一段？",
       "desc": "用达克曲线定位你现在的位置",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "0-how.html",
       "action": "copy",
       "ksa": "K",
       "title": "怎样学，知识才能过脑子",
       "seo": "看完 ≠ 学到：AI 课程怎么学才真的过脑子",
       "desc": "每节都要代入自己的场景",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "0-why.html",
       "action": "adapt",
       "ksa": "K",
       "title": "为什么 HR 也要弄懂原理",
       "seo": "HR 学 AI 需要懂原理吗？——原理决定你能不能判断它什么时候会错",
       "desc": "HR 犯错的代价是人的职业生涯",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    }
   ]
  },
  {
   "id": "p-zero",
   "num": "第零篇章",
   "title": "写给第一次接触 AI 的 HR",
   "desc": "零基础到会用。读完这一章，你就能拿 AI 干活了。全章免费，不预设你懂任何术语。",
   "freeWhole": true,
   "topics": [
    {
     "title": "AI 是个什么东西",
     "desc": "先看它的能力，再看穿它的底牌",
     "lessons": [
      {
       "file": "zero-0.html",
       "action": "copy",
       "ksa": "K",
       "title": "AI 能干哪些神奇的活",
       "seo": "AI 到底能干什么？先看它的能力清单",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-1.html",
       "action": "copy",
       "ksa": "K",
       "title": "它其实在玩「接话茬」",
       "seo": "AI 是怎么工作的？它其实在玩接话茬",
       "desc": "全课最重要的一个隐喻",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-2.html",
       "action": "copy",
       "ksa": "K",
       "title": "它不是搜索引擎",
       "seo": "AI 和搜索引擎有什么区别？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-3.html",
       "action": "copy",
       "ksa": "K",
       "title": "它会一本正经地胡说",
       "seo": "AI 为什么会一本正经地胡说八道？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "怎么和它说话",
     "desc": "两个立刻能用的技巧",
     "lessons": [
      {
       "file": "zero-4.html",
       "action": "copy",
       "ksa": "K",
       "title": "把它当不了解你的新同事",
       "seo": "AI 提示词怎么写？把它当不了解你的新同事",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-5.html",
       "action": "copy",
       "ksa": "S",
       "title": "万能开场白：先问我几个问题",
       "seo": "一句万能开场白，让 AI 主动问你需求",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "HR 三千问",
     "desc": "一页一问，把最常见的疑惑一次说清",
     "lessons": [
      {
       "file": "zero-q-prompt.html",
       "action": "copy",
       "ksa": "S",
       "title": "提示词到底怎么写才好？",
       "seo": "提示词到底怎么写才好？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-q-prompt-engineering.html",
       "action": "copy",
       "ksa": "K",
       "title": "「提示词工程」有什么意义？",
       "seo": "提示词工程是什么，对普通人有意义吗？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-q-model-agent-app.html",
       "action": "copy",
       "ksa": "K",
       "title": "模型、Agent、应用是什么关系？",
       "seo": "大模型、Agent、AI 应用是什么关系？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-q-agent.html",
       "action": "copy",
       "ksa": "K",
       "title": "Agent 到底强在哪？",
       "seo": "AI Agent 到底强在哪里？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-q-skill.html",
       "action": "copy",
       "ksa": "K",
       "title": "最近很火的 Skill 是什么？",
       "seo": "AI 的 Skill 是什么？和插件有什么区别？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-q-china-models.html",
       "action": "copy",
       "ksa": "K",
       "title": "国产大模型有哪些？该怎么选？",
       "seo": "国产大模型有哪些？企业该怎么选？",
       "desc": "内网合规场景尤其相关",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-q-companies.html",
       "action": "copy",
       "ksa": "K",
       "title": "还有哪些重要的 AI 公司？",
       "seo": "除了 OpenAI，还有哪些重要的 AI 公司？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "日常用它的手感",
     "desc": "一份用 AI 的日常指南 —— 从原第二篇章挪来，免费模块就完整了",
     "lessons": [
      {
       "file": "ai-tips-boundary.html",
       "action": "copy",
       "ksa": "A",
       "title": "人机知识边界：四象限策略",
       "seo": "什么该问 AI，什么该问人？一张四象限图",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "ai-tips-context.html",
       "action": "copy",
       "ksa": "S",
       "title": "好提问 vs 坏提问",
       "seo": "同一个问题，怎么问 AI 才给得出好答案",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "ai-tips-verify.html",
       "action": "copy",
       "ksa": "S",
       "title": "AI 说的能信吗？找出幻觉",
       "seo": "AI 说的话怎么验证？三步找出幻觉",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "ai-tips-iterate.html",
       "action": "copy",
       "ksa": "A",
       "title": "迭代的艺术：知道何时收手",
       "seo": "跟 AI 来回改了十轮还不满意，什么时候该收手",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "ai-tips-scenarios.html",
       "action": "copy",
       "ksa": "A",
       "title": "场景速查：什么时候放心用",
       "seo": "哪些场景可以放心用 AI，哪些必须人工复核",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "什么能放心交给它",
     "desc": "一套三秒钟的信任判断法",
     "lessons": [
      {
       "file": "zero-6.html",
       "action": "copy",
       "ksa": "A",
       "title": "放心用，还是要核实？",
       "seo": "什么活能放心交给 AI？一套三秒判断法",
       "desc": "全章对 HR 最有价值的两节之一",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "zero-final.html",
       "action": "copy",
       "ksa": "K",
       "title": "你的下一步",
       "seo": "零基础学完 AI 之后，下一步该学什么",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    }
   ]
  },
  {
   "id": "p-1",
   "num": "第一篇章",
   "title": "幻觉与边界：它靠不靠得住",
   "desc": "HR 犯错的代价是人的职业生涯。所以先学它会怎么错，再学它能干什么。本章起进入主线案例 —— 简历初筛，它会一路贯穿到第五篇章。",
   "freeWhole": false,
   "topics": [
    {
     "title": "生成 vs 检索：它为什么会编",
     "desc": "只讲够用的原理，不讲词表和预训练",
     "lessons": [
      {
       "file": "training-data.html",
       "action": "adapt",
       "ksa": "K",
       "title": "AI 的食物：训练数据",
       "seo": "大模型的训练数据是什么？为什么它决定了 AI 会说什么",
       "desc": "换成 HR 语料的例子",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "train-vs-infer.html",
       "action": "copy",
       "ksa": "K",
       "title": "训练 vs 推理：两个不同的过程",
       "seo": "大模型训练和推理有什么区别？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "1-2-fake-chat.html",
       "action": "adapt",
       "ksa": "K",
       "title": "它为什么像在聊天：伪造聊天记录",
       "seo": "大模型的本质是补全，不是理解——伪造一段聊天记录就看懂了",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "幻觉的四种应对",
     "desc": "幻觉不是 bug，是它的工作方式本身",
     "lessons": [
      {
       "file": "1-2-hallucination.html",
       "action": "adapt",
       "ksa": "K",
       "title": "它会编：筛简历现场",
       "seo": "AI 筛简历会编造候选人没写过的经历吗？——幻觉的第一现场",
       "desc": "★主线起点",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "1-2-mitigation-prompt.html",
       "action": "adapt",
       "ksa": "S",
       "title": "应对 1：把约束写进 Prompt",
       "seo": "怎么用 Prompt 减少 AI 幻觉？",
       "desc": "",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "1-2-mitigation-rag.html",
       "action": "adapt",
       "ksa": "S",
       "title": "应对 2：RAG——让它只答制度里有的",
       "seo": "RAG 是什么？让 AI 只回答公司制度里写过的内容",
       "desc": "换员工政策问答场景（副线）",
       "spine": false,
       "free": false,
       "ready": true
      },
      {
       "file": "1-2-mitigation-temp.html",
       "action": "copy",
       "ksa": "K",
       "title": "应对 3：它为什么每次都不一样",
       "seo": "Temperature 是什么？为什么同一个问题 AI 每次答得都不同",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      },
      {
       "file": "1-2-mitigation-eval.html",
       "action": "adapt",
       "ksa": "S",
       "title": "应对 4：评测 + 人工审核",
       "seo": "怎么评测 AI 的输出质量？评测加人工复核的组合拳",
       "desc": "",
       "spine": true,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "上下文窗口：它为什么会忘",
     "desc": "从原第二篇章挪来 —— 会忘也是不靠谱的一种",
     "lessons": [
      {
       "file": "5-1.html",
       "action": "copy",
       "ksa": "K",
       "title": "上下文窗口：它的工作记忆",
       "seo": "什么是上下文窗口？AI 的工作记忆有多大",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "5-2.html",
       "action": "copy",
       "ksa": "K",
       "title": "上下文溢出：三种处理策略",
       "seo": "对话太长 AI 就失忆？上下文溢出的三种处理办法",
       "desc": "一场组织盘点跑到一半失忆（副线）",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "召回 vs 判定：HR 必须设的那道闸",
     "desc": "把认知变成流程",
     "lessons": [
      {
       "file": "hr-recall-vs-judge.html",
       "action": "new",
       "ksa": "A",
       "title": "召回 vs 判定：它编的理由你验不出来",
       "seo": "AI 筛简历给的理由是编的怎么办？召回与判定必须拆开",
       "desc": "★主线",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-cite-not-summarize.html",
       "action": "new",
       "ksa": "S",
       "title": "怎么让它只引用、不概括",
       "seo": "怎么让 AI 引用原文而不是自己概括？一个可执行的 Prompt 约束",
       "desc": "★主线·从原节拆出",
       "spine": true,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "他们会这样考你",
     "desc": "老板、业务、技术同事会怎么考察你",
     "lessons": [
      {
       "file": "interview-1.html",
       "action": "new",
       "ksa": "A",
       "title": "幻觉与边界 · 30 问",
       "seo": "AI 幻觉相关的 30 个面试问题（HR 版）",
       "desc": "每题带 KSA 标签，回流能力画像",
       "spine": false,
       "free": true,
       "ready": false
      }
     ]
    }
   ]
  },
  {
   "id": "p-2",
   "num": "第二篇章",
   "title": "Prompt 与 Agent：怎么指挥它",
   "desc": "从「能用」到「指挥得动」：怎么说话、它会听谁的、什么时候不该给它自主权、以及它花你多少钱。",
   "freeWhole": false,
   "topics": [
    {
     "title": "Prompt 工程：怎么把话说对",
     "desc": "不是调措辞，是设计信息结构",
     "lessons": [
      {
       "file": "6-1.html",
       "action": "adapt",
       "ksa": "S",
       "title": "System Prompt：你说什么，它就变什么",
       "seo": "System Prompt 是什么？一句话改变 AI 的全部行为",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "6-2.html",
       "action": "adapt",
       "ksa": "S",
       "title": "Prompt 进阶技巧",
       "seo": "AI 提示词进阶技巧：角色、示例、约束、格式",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "Prompt Injection：它会听谁的话",
     "desc": "员工和候选人填进来的内容，能不能信",
     "lessons": [
      {
       "file": "prompt-attack.html",
       "action": "adapt",
       "ksa": "K",
       "title": "指令和数据走同一个通道",
       "seo": "什么是 Prompt Injection？为什么 AI 分不清指令和数据",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-resume-injection.html",
       "action": "new",
       "ksa": "K",
       "title": "简历里的白色字体：HR 场景的注入攻击",
       "seo": "候选人在简历里藏白色字体骗过 AI 筛选，怎么防？",
       "desc": "★主线",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "prompt-defense.html",
       "action": "adapt",
       "ksa": "S",
       "title": "三层拦截：清洗、隔离、兜底",
       "seo": "Prompt Injection 怎么防？清洗、隔离、兜底三层拦截",
       "desc": "",
       "spine": true,
       "free": false,
       "ready": true
      },
      {
       "file": "ai-safety-redlines.html",
       "action": "adapt",
       "ksa": "A",
       "title": "AI 红线：HR 版四条底线",
       "seo": "HR 用 AI 的四条安全底线",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "Agent 与 Workflow：它能自己干活吗",
     "desc": "只讲概念，不讲工程实现",
     "lessons": [
      {
       "file": "7-1.html",
       "action": "copy",
       "ksa": "K",
       "title": "Agent：能干活的 AI",
       "seo": "AI Agent 是什么？和普通聊天有什么不同",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "10-1.html",
       "action": "adapt",
       "ksa": "A",
       "title": "Workflow vs Agent：HR 大多不该给自主权",
       "seo": "Workflow 和 Agent 怎么选？HR 场景为什么大多不该给自主权",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "7-4a.html",
       "action": "copy",
       "ksa": "K",
       "title": "ReAct 循环：思考 → 行动 → 观察",
       "seo": "ReAct 是什么？Agent 的思考-行动-观察循环",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      },
      {
       "file": "7-4b.html",
       "action": "adapt",
       "ksa": "K",
       "title": "Agent 卡死的 5 种模式",
       "seo": "AI Agent 为什么会卡死？五种典型失败模式",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "Token 与成本：它花你多少钱",
     "desc": "决定什么值得做 —— 归位，原提纲漏了这个主题",
     "lessons": [
      {
       "file": "8-1.html",
       "action": "copy",
       "ksa": "K",
       "title": "多轮对话为什么越来越贵",
       "seo": "AI 多轮对话为什么越聊越贵？Token 是怎么算钱的",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "cost-eval.html",
       "action": "copy",
       "ksa": "K",
       "title": "模型选型：能力 vs 成本",
       "seo": "AI 模型怎么选？能力和成本怎么权衡",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "他们会这样考你",
     "desc": "",
     "lessons": [
      {
       "file": "interview-2.html",
       "action": "new",
       "ksa": "A",
       "title": "Prompt 与 Agent · 30 问",
       "seo": "Prompt 与 Agent 相关的 30 个面试问题（HR 版）",
       "desc": "每题带 KSA 标签",
       "spine": false,
       "free": true,
       "ready": false
      }
     ]
    }
   ]
  },
  {
   "id": "p-3",
   "num": "第三篇章",
   "title": "RAG 与 Eval：怎么让它干你这家公司的活",
   "desc": "通用 AI 谁都能用。想让它干你这家公司的活，得把你的判断和你的数据喂进去，再验证它有没有学对。★ learn-ai 完全没有这一章 —— 这是这个角色真正的护城河。",
   "freeWhole": false,
   "topics": [
    {
     "title": "从「会用」到「担责」",
     "desc": "腔调换挡点：前面主语是「它」，从这里开始是「你」",
     "lessons": [
      {
       "file": "hr-bridge.html",
       "action": "new",
       "ksa": "A",
       "title": "你已经会用了，接下来的问题不一样了",
       "seo": "会用 AI 之后呢？从「它靠不靠谱」到「你担什么责」",
       "desc": "★过渡节·归位",
       "spine": true,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "知识萃取：把判断变成它能执行的规则",
     "desc": "把老法师脑子里的东西掏出来",
     "lessons": [
      {
       "file": "hr-elicitation-1.html",
       "action": "new",
       "ksa": "A",
       "title": "隐性知识显性化：老法师那一眼在看什么",
       "seo": "老 HR「看一眼就知道这人行不行」，那一眼到底在看什么？",
       "desc": "★主线·需素材",
       "spine": true,
       "free": true,
       "ready": false
      },
      {
       "file": "hr-elicitation-2.html",
       "action": "new",
       "ksa": "A",
       "title": "拆到哪一层为止：哪些永远进不了 Prompt",
       "seo": "知识萃取拆到什么程度为止？哪些判断永远无法交给 AI",
       "desc": "需素材",
       "spine": false,
       "free": true,
       "ready": false
      },
      {
       "file": "hr-elicitation-3.html",
       "action": "new",
       "ksa": "S",
       "title": "从规则到 Prompt：判断链怎么落地",
       "seo": "把萃取出来的判断规则写成 Prompt 的具体做法",
       "desc": "需素材",
       "spine": true,
       "free": false,
       "ready": false
      }
     ]
    },
    {
     "title": "RAG 与知识库：把公司的东西喂给它",
     "desc": "所有 HR 数据项目翻车的第一现场",
     "lessons": [
      {
       "file": "hr-caliber-1.html",
       "action": "new",
       "ksa": "K",
       "title": "知识库的原料：三个系统、五种口径、人名对不上",
       "seo": "HR 数据为什么这么脏？三个系统五种口径的真实现场",
       "desc": "薪酬/花名册（副线）·需素材",
       "spine": false,
       "free": true,
       "ready": false
      },
      {
       "file": "hr-caliber-2.html",
       "action": "new",
       "ksa": "A",
       "title": "Garbage in：口径不确认，它算出来的全是假的",
       "seo": "口径没对齐，AI 算出来的数字全是假的——而且假得很像真的",
       "desc": "需素材",
       "spine": false,
       "free": true,
       "ready": false
      },
      {
       "file": "hr-caliber-3.html",
       "action": "new",
       "ksa": "S",
       "title": "切片与清洗：喂进 RAG 之前要做什么",
       "seo": "文档怎么切片、数据怎么清洗，才能喂进 RAG",
       "desc": "需素材",
       "spine": false,
       "free": false,
       "ready": false
      }
     ]
    },
    {
     "title": "Eval：怎么知道它真学会了",
     "desc": "不评测就是在裸奔",
     "lessons": [
      {
       "file": "10-8.html",
       "action": "adapt",
       "ksa": "S",
       "title": "为什么评测比调 prompt 重要",
       "seo": "为什么 AI 评测比调 Prompt 更重要？",
       "desc": "",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "10-9.html",
       "action": "adapt",
       "ksa": "S",
       "title": "三种 Grader：代码判、模型判、人工判",
       "seo": "AI 输出怎么打分？代码判、模型判、人工判三种方式",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "10-10.html",
       "action": "adapt",
       "ksa": "S",
       "title": "Eval 的坑：噪音、作弊与退化",
       "seo": "做 AI 评测最容易踩的三个坑",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      },
      {
       "file": "hr-eval-negative.html",
       "action": "new",
       "ksa": "S",
       "title": "阴性对照：先注入已知的错，看它抓不抓得住",
       "seo": "怎么验证你的 AI 评测本身是有效的？先做阴性对照",
       "desc": "★主线·往简历堆里埋假简历",
       "spine": true,
       "free": false,
       "ready": true
      }
     ]
    }
   ]
  },
  {
   "id": "p-4",
   "num": "第四篇章",
   "title": "Vibe Coding：自己做出来",
   "desc": "不是教你写代码，是教你怎么指挥它写。学完能自己做出一个真跑起来的东西 —— 这一项在真实岗位要求里出现得最多。",
   "freeWhole": false,
   "topics": [
    {
     "title": "先立规矩",
     "desc": "",
     "lessons": [
      {
       "file": "vibe-1.html",
       "action": "copy",
       "ksa": "S",
       "title": "为什么要给 AI 立规矩",
       "seo": "用 AI 写代码为什么要先立规矩？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "怎么跟它协作",
     "desc": "非技术背景的人最需要的部分",
     "lessons": [
      {
       "file": "vibe-2.html",
       "action": "copy",
       "ksa": "S",
       "title": "四步流程：复述、PRD、确认、编码",
       "seo": "不会写代码怎么指挥 AI 做东西？四步协作流程",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "vibe-5.html",
       "action": "copy",
       "ksa": "S",
       "title": "调试铁律：先 Log 再改码",
       "seo": "AI 写的代码出错了怎么调？先看日志再改代码",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "vibe-6.html",
       "action": "copy",
       "ksa": "S",
       "title": "不接受分期交付",
       "seo": "让 AI 一次交付完整功能，不接受半成品",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "别让它把你搞砸",
     "desc": "HR 数据敏感，这两条是刚需",
     "lessons": [
      {
       "file": "vibe-9.html",
       "action": "copy",
       "ksa": "S",
       "title": "破坏性操作的三道闸",
       "seo": "怎么防止 AI 误删数据？破坏性操作的三道闸",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "vibe-8.html",
       "action": "copy",
       "ksa": "S",
       "title": "把环境事实写进 Rule",
       "seo": "为什么要把环境信息写进 AI 的规则文件",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "沉淀下来",
     "desc": "",
     "lessons": [
      {
       "file": "vibe-7.html",
       "action": "copy",
       "ksa": "S",
       "title": "三份文档与方法论沉淀",
       "seo": "跟 AI 协作要维护哪三份文档",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "vibe-final.html",
       "action": "copy",
       "ksa": "A",
       "title": "规则的价值：每条都解决一个真实问题",
       "seo": "为什么每条 AI 协作规则都对应一次真实踩坑",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "做出你的第一个作品",
     "desc": "★ 把方法用在 HR 场景上，交出一个真能跑的东西",
     "lessons": [
      {
       "file": "hr-project-pick.html",
       "action": "new",
       "ksa": "A",
       "title": "选题：什么样的第一个作品站得住",
       "seo": "HR 做 AI 作品选什么题？六个能站住的选题",
       "desc": "★主线·简历初筛是第一选题",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-project-data.html",
       "action": "new",
       "ksa": "S",
       "title": "数据：真数据碰不得，合成数据怎么造得像",
       "seo": "做 HR AI 作品没有数据怎么办？合成数据怎么造得像真的",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-project-build.html",
       "action": "new",
       "ksa": "S",
       "title": "一周做出能点的原型：从想法到 demo",
       "seo": "一周内把一个 HR 场景做成能演示的原型",
       "desc": "★主线",
       "spine": true,
       "free": false,
       "ready": true
      },
      {
       "file": "hr-project-tell.html",
       "action": "new",
       "ksa": "A",
       "title": "作品怎么讲：别人在追问什么",
       "seo": "AI 作品怎么讲才有说服力？别人真正会追问的问题",
       "desc": "★主线",
       "spine": true,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "他们会这样考你",
     "desc": "",
     "lessons": [
      {
       "file": "interview-7.html",
       "action": "new",
       "ksa": "A",
       "title": "Vibe Coding · 30 问",
       "seo": "AI 协作编程相关的 30 个面试问题（HR 版）",
       "desc": "每题带 KSA 标签",
       "spine": false,
       "free": true,
       "ready": false
      }
     ]
    }
   ]
  },
  {
   "id": "p-5",
   "num": "第五篇章",
   "title": "从 Demo 到落地：让它在组织里活下来",
   "desc": "做出来 ≠ 被采用。这一层决定你的天花板。三步走：盘 → 推 → 改。",
   "freeWhole": false,
   "topics": [
    {
     "title": "场景盘点：哪些活能交给它",
     "desc": "★ 全新 —— 不是讲观点，是给可执行的动作",
     "lessons": [
      {
       "file": "hr-inventory-1.html",
       "action": "new",
       "ksa": "A",
       "title": "把一个部门的活拆成任务清单",
       "seo": "怎么盘点一个部门有哪些活能交给 AI？先拆任务清单",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-inventory-2.html",
       "action": "new",
       "ksa": "A",
       "title": "每条标：它能干 / 干不了 / 干了得有人兜",
       "seo": "AI 场景盘点怎么打标？三类任务的判断标准",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-inventory-3.html",
       "action": "new",
       "ksa": "A",
       "title": "算账：省多少、风险多大、第一刀切哪",
       "seo": "AI 场景的 ROI 怎么算？第一刀该切哪里",
       "desc": "★主线·简历初筛为什么是好的第一刀",
       "spine": true,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "Agent 权限设计：给它多大自由",
     "desc": "",
     "lessons": [
      {
       "file": "9-27.html",
       "action": "adapt",
       "ksa": "A",
       "title": "AI 该有多大的自由",
       "seo": "AI Agent 该有多大权限？它能不能自己发拒信",
       "desc": "★主线",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "9-28.html",
       "action": "adapt",
       "ksa": "A",
       "title": "弹窗太多没人用，不弹又不安全",
       "seo": "AI 的确认弹窗怎么设计才不烦人又安全",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "9-29.html",
       "action": "adapt",
       "ksa": "A",
       "title": "它干了什么你知道吗：留痕与可申诉",
       "seo": "AI 参与人事决策必须留痕且可申诉",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "从试点到铺开",
     "desc": "",
     "lessons": [
      {
       "file": "hr-persuade.html",
       "action": "new",
       "ksa": "A",
       "title": "怎么跟老板讲清楚「它有 8% 会错」",
       "seo": "AI 有 8% 会出错，怎么跟老板汇报才通得过",
       "desc": "★主线",
       "spine": true,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-rollout.html",
       "action": "new",
       "ksa": "A",
       "title": "换个团队它就不准了：AI 为什么不像软件那样可复制",
       "seo": "AI 试点成功后推广就失败？为什么它不像软件那样可复制",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "hr-compliance.html",
       "action": "new",
       "ksa": "K",
       "title": "它算错了，谁负责：内网 · n 阈值 · 可申诉",
       "seo": "AI 做错了人事决策谁负责？合规的四条红线",
       "desc": "",
       "spine": false,
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "人机分工：组织会变成什么样",
     "desc": "★ 全新 —— 必须挂真实案例，否则就是 PPT 废话",
     "lessons": [
      {
       "file": "hr-org-1.html",
       "action": "new",
       "ksa": "A",
       "title": "把岗位拆开重组：它接管之后这个岗位还剩什么",
       "seo": "AI 接管之后，HR 岗位该怎么重新设计？",
       "desc": "需素材",
       "spine": false,
       "free": true,
       "ready": false
      },
      {
       "file": "hr-org-2.html",
       "action": "new",
       "ksa": "A",
       "title": "你会的哪些东西正在被模型吃掉",
       "seo": "HR 的哪些技能正在被 AI 取代？哪些反而更值钱",
       "desc": "需素材",
       "spine": false,
       "free": true,
       "ready": false
      },
      {
       "file": "hr-org-3.html",
       "action": "new",
       "ksa": "A",
       "title": "哪些能力反而更值钱了",
       "seo": "AI 时代 HR 哪些能力在升值？按 KSA 拆开看",
       "desc": "接能力词典",
       "spine": false,
       "free": false,
       "ready": true
      }
     ]
    }
   ]
  },
  {
   "id": "p-oss",
   "num": "专题",
   "title": "别忘了这两件事",
   "desc": "HR 数据不出内网是硬约束 —— 所以本地部署对 HR 是真问题，不是极客爱好。",
   "freeWhole": false,
   "topics": [
    {
     "title": "本地部署",
     "desc": "",
     "lessons": [
      {
       "file": "oss-8.html",
       "action": "copy",
       "ksa": "K",
       "title": "你的电脑能跑多大的模型",
       "seo": "普通电脑能跑多大的大模型？",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      },
      {
       "file": "oss-9.html",
       "action": "copy",
       "ksa": "S",
       "title": "Ollama 与 LM Studio 怎么上手",
       "seo": "Ollama 和 LM Studio 怎么用？本地跑大模型入门",
       "desc": "",
       "spine": false,
       "free": true,
       "ready": true
      }
     ]
    }
   ]
  }
 ]
};
