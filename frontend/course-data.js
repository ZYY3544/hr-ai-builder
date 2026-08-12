/* HR AI Builder 课程数据 v2 —— 单一真相源。
   面向 HR 领域的 AI 课程数据，AGPL-3.0 开源。
   action: copy=沿用 / adapt=重写成 HR 场景 / new=原创
   free:   true=静态直读(SEO) / false=登录后经 API 读
   seo:    页面 title（长·含中文问句），与目录标题(短·带术语)解耦 */
window.COURSE = {
 "meta": {
  "title": "HR AI Builder",
  "subtitle": "读懂 AI 的底层逻辑，做 AI Native 组织的先驱者",
  "attribution": {
   "note": "面向 HR 领域的 AI 课程，依 AGPL-3.0 开源。",
   "author": "HR AI Builder",
   "repo": "https://github.com/ZYY3544/hr-ai-builder",
   "site": "https://github.com/ZYY3544/hr-ai-builder",
   "license": "AGPL-3.0"
  },
  "stats": {
   "parts": 9,
   "lessons": 101,
   "copy": 40,
   "adapt": 20,
   "new": 41,
   "ready": 101,
   "todo": 0
  },
  "access": {
   "free": 82,
   "locked": 19,
   "rule": "开篇与第零篇章全免费；其余篇章每个主题前 2 节免费。免费≠收费墙——全部内容永久免费，登录只用于同步进度与防止内容被批量贩卖。",
   "gate": "off",
   "method": "Google Flexible Sampling —— 正文始终在 HTML 里可被索引，客户端遮挡 + JSON-LD 声明 isAccessibleForFree"
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
       "file": "start-dunning-kruger.html",
       "action": "copy",
       "ksa": "K",
       "title": "我们在哪里？达克效应",
       "seo": "AI 学习者的达克曲线：你现在在哪一段？",
       "desc": "用达克曲线定位你现在的位置",
       "free": true,
       "ready": true
      },
      {
       "file": "start-how-to-learn.html",
       "action": "copy",
       "ksa": "K",
       "title": "怎样学，知识才能过脑子",
       "seo": "看完 ≠ 学到：AI 课程怎么学才真的过脑子",
       "desc": "每节都要代入自己的场景",
       "free": true,
       "ready": true
      },
      {
       "file": "start-why-principles.html",
       "action": "adapt",
       "ksa": "K",
       "title": "为什么 HR 也要弄懂原理",
       "seo": "HR 学 AI 需要懂原理吗？——原理决定你能不能判断它什么时候会错",
       "desc": "HR 犯错的代价是人的职业生涯",
       "free": true,
       "ready": true
      }
     ]
    }
   ],
   "color": "#64748B"
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
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "日常用它的手感",
     "desc": "一份用 AI 的日常指南，读完就能上手",
     "lessons": [
      {
       "file": "ai-tips-boundary.html",
       "action": "copy",
       "ksa": "A",
       "title": "人机知识边界：四象限策略",
       "seo": "什么该问 AI，什么该问人？一张四象限图",
       "desc": "",
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
       "free": true,
       "ready": true
      }
     ]
    }
   ],
   "color": "#0891B2"
  },
  {
   "id": "p-1",
   "num": "第一篇章",
   "title": "幻觉与边界：它靠不靠得住",
   "desc": "HR 犯错的代价是人的职业生涯。所以先学它会怎么错，再学它能干什么。",
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
       "free": true,
       "ready": true
      },
      {
       "file": "hallu-fake-chat.html",
       "action": "adapt",
       "ksa": "K",
       "title": "它为什么像在聊天：伪造聊天记录",
       "seo": "大模型的本质是补全，不是理解——伪造一段聊天记录就看懂了",
       "desc": "",
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
       "file": "hallu-first-scene.html",
       "action": "adapt",
       "ksa": "K",
       "title": "它会编：筛简历现场",
       "seo": "AI 筛简历会编造候选人没写过的经历吗？——幻觉的第一现场",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hallu-fix-prompt.html",
       "action": "adapt",
       "ksa": "S",
       "title": "应对 1：把约束写进 Prompt",
       "seo": "怎么用 Prompt 减少 AI 幻觉？",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hallu-fix-rag.html",
       "action": "adapt",
       "ksa": "S",
       "title": "应对 2：RAG——让它只答制度里有的",
       "seo": "RAG 是什么？让 AI 只回答公司制度里写过的内容",
       "desc": "换员工政策问答场景",
       "free": false,
       "ready": true
      },
      {
       "file": "hallu-fix-temp.html",
       "action": "copy",
       "ksa": "K",
       "title": "应对 3：它为什么每次都不一样",
       "seo": "Temperature 是什么？为什么同一个问题 AI 每次答得都不同",
       "desc": "",
       "free": false,
       "ready": true
      },
      {
       "file": "hallu-fix-eval.html",
       "action": "adapt",
       "ksa": "S",
       "title": "应对 4：评测 + 人工审核",
       "seo": "怎么评测 AI 的输出质量？评测加人工复核的组合拳",
       "desc": "",
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "上下文窗口：它为什么会忘",
     "desc": "会忘也是不靠谱的一种",
     "lessons": [
      {
       "file": "context-window.html",
       "action": "copy",
       "ksa": "K",
       "title": "上下文窗口：它的工作记忆",
       "seo": "什么是上下文窗口？AI 的工作记忆有多大",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "context-overflow.html",
       "action": "copy",
       "ksa": "K",
       "title": "上下文溢出：三种处理策略",
       "seo": "对话太长 AI 就失忆？上下文溢出的三种处理办法",
       "desc": "一场组织盘点跑到一半失忆",
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
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hr-cite-not-summarize.html",
       "action": "new",
       "ksa": "S",
       "title": "怎么让它只引用、不概括",
       "seo": "怎么让 AI 引用原文而不是自己概括？一个可执行的 Prompt 约束",
       "desc": "",
       "free": true,
       "ready": true
      }
     ]
    }
   ],
   "color": "#3370FF"
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
       "file": "prompt-system.html",
       "action": "adapt",
       "ksa": "S",
       "title": "System Prompt：你说什么，它就变什么",
       "seo": "System Prompt 是什么？一句话改变 AI 的全部行为",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "prompt-advanced.html",
       "action": "adapt",
       "ksa": "S",
       "title": "Prompt 进阶技巧",
       "seo": "AI 提示词进阶技巧：角色、示例、约束、格式",
       "desc": "",
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
       "free": true,
       "ready": true
      },
      {
       "file": "hr-resume-injection.html",
       "action": "new",
       "ksa": "K",
       "title": "简历里的白色字体：HR 场景的注入攻击",
       "seo": "候选人在简历里藏白色字体骗过 AI 筛选，怎么防？",
       "desc": "",
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
       "file": "agent-what.html",
       "action": "copy",
       "ksa": "K",
       "title": "Agent：能干活的 AI",
       "seo": "AI Agent 是什么？和普通聊天有什么不同",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "agent-vs-workflow.html",
       "action": "adapt",
       "ksa": "A",
       "title": "Workflow vs Agent：HR 大多不该给自主权",
       "seo": "Workflow 和 Agent 怎么选？HR 场景为什么大多不该给自主权",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "agent-react.html",
       "action": "copy",
       "ksa": "K",
       "title": "ReAct 循环：思考 → 行动 → 观察",
       "seo": "ReAct 是什么？Agent 的思考-行动-观察循环",
       "desc": "",
       "free": false,
       "ready": true
      },
      {
       "file": "agent-stuck.html",
       "action": "adapt",
       "ksa": "K",
       "title": "Agent 卡死的 5 种模式",
       "seo": "AI Agent 为什么会卡死？五种典型失败模式",
       "desc": "",
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "Token 与成本：它花你多少钱",
     "desc": "知道它花你多少钱，才知道什么值得做",
     "lessons": [
      {
       "file": "token-cost.html",
       "action": "copy",
       "ksa": "K",
       "title": "多轮对话为什么越来越贵",
       "seo": "AI 多轮对话为什么越聊越贵？Token 是怎么算钱的",
       "desc": "",
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
       "free": true,
       "ready": true
      }
     ]
    }
   ],
   "color": "#DB2777"
  },
  {
   "id": "p-3",
   "num": "第三篇章",
   "title": "RAG 与 Eval：怎么让它干你这家公司的活",
   "desc": "通用 AI 谁都能用。想让它干你这家公司的活，得把你的判断和你的数据喂进去，再验证它有没有学对。这是这个角色真正的护城河。",
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
       "desc": "",
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
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hr-elicitation-2.html",
       "action": "new",
       "ksa": "A",
       "title": "拆到哪一层为止：哪些永远进不了 Prompt",
       "seo": "知识萃取拆到什么程度为止？哪些判断永远无法交给 AI",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hr-elicitation-3.html",
       "action": "new",
       "ksa": "S",
       "title": "从规则到 Prompt：判断链怎么落地",
       "seo": "把萃取出来的判断规则写成 Prompt 的具体做法",
       "desc": "",
       "free": false,
       "ready": true
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
       "desc": "薪酬/花名册",
       "free": true,
       "ready": true
      },
      {
       "file": "hr-caliber-2.html",
       "action": "new",
       "ksa": "A",
       "title": "Garbage in：口径不确认，它算出来的全是假的",
       "seo": "口径没对齐，AI 算出来的数字全是假的——而且假得很像真的",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hr-caliber-3.html",
       "action": "new",
       "ksa": "S",
       "title": "切片与清洗：喂进 RAG 之前要做什么",
       "seo": "文档怎么切片、数据怎么清洗，才能喂进 RAG",
       "desc": "",
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "Eval：怎么知道它真学会了",
     "desc": "不评测就是在裸奔",
     "lessons": [
      {
       "file": "eval-why.html",
       "action": "adapt",
       "ksa": "S",
       "title": "为什么评测比调 prompt 重要",
       "seo": "为什么 AI 评测比调 Prompt 更重要？",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "eval-graders.html",
       "action": "adapt",
       "ksa": "S",
       "title": "三种 Grader：代码判、模型判、人工判",
       "seo": "AI 输出怎么打分？代码判、模型判、人工判三种方式",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "eval-pitfalls.html",
       "action": "adapt",
       "ksa": "S",
       "title": "Eval 的坑：噪音、作弊与退化",
       "seo": "做 AI 评测最容易踩的三个坑",
       "desc": "",
       "free": false,
       "ready": true
      },
      {
       "file": "hr-eval-negative.html",
       "action": "new",
       "ksa": "S",
       "title": "阴性对照：先注入已知的错，看它抓不抓得住",
       "seo": "怎么验证你的 AI 评测本身是有效的？先做阴性对照",
       "desc": "往简历堆里埋假简历",
       "free": false,
       "ready": true
      }
     ]
    }
   ],
   "color": "#7C3AED"
  },
  {
   "id": "p-4",
   "num": "第四篇章",
   "title": "Code Interpreter 与分析模式：让 AI 算得准，也说得对",
   "desc": "数据活分两段，架构相反：算得准的那段必须走代码，模型不碰数字；说得对的那段才是模型的活，但它得学你的分析模式。第一段正在被通用工具吃掉，第二段永远是你的。",
   "freeWhole": true,
   "color": "#65A30D",
   "topics": [
    {
     "title": "生成 vs 执行：它给的数是算的还是猜的",
     "lessons": [
      {
       "file": "data-gen-vs-exec.html",
       "action": "new",
       "ksa": "K",
       "title": "同一张表问三遍出三个数",
       "seo": "把表格贴给 AI 算数，为什么每次结果都不一样？",
       "desc": "先不讲原理，先看现象。这个实验你自己跑一遍，比读十遍解释管用。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-token.html",
       "action": "new",
       "ksa": "K",
       "title": "它在预测 token，不在做运算",
       "seo": "大模型为什么算不准数学？因为它在预测 token 而不是计算",
       "desc": "不是模型「不够聪明」，是这件事从机制上就不是它干的活。理解这一层，你就知道该在哪里设防。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-when-code.html",
       "action": "new",
       "ksa": "A",
       "title": "三问判据：什么时候必须走代码",
       "seo": "什么时候可以直接问 AI，什么时候必须让它写代码？三个判据",
       "desc": "「所有数据都不能贴给 AI」是句假话，你三分钟就能找到反例。真正该学的是判断——什么时候贴一下没事，什么时候必须走代码。",
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "Code Interpreter 与沙箱：代码在哪跑，数据去哪了",
     "lessons": [
      {
       "file": "data-ci-how.html",
       "action": "new",
       "ksa": "K",
       "title": "工具调用怎么发生的",
       "seo": "Code Interpreter 是什么？AI 写代码算数据的完整机制",
       "desc": "上一节的结论是「必须走代码」。这一节讲清楚：代码是谁写的、在哪跑的、你怎么确认它真的跑了。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-ci-first.html",
       "action": "new",
       "ksa": "S",
       "title": "第一次工具调用：五分钟揪重名",
       "seo": "第一次让 AI 写代码处理数据：五分钟揪出花名册里的重名",
       "desc": "原理够了，动手。一份编好的假花名册，一段可以整段抄走的话术，五分钟拿到第一次成功。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-ci-sandbox.html",
       "action": "new",
       "ksa": "K",
       "title": "沙箱：你的数据去了哪",
       "seo": "把员工数据上传给 AI 安全吗？沙箱机制与 HR 的数据红线",
       "desc": "上一节让你用假数据，不是谨慎过头。要用真数据之前，你必须知道文件上传之后发生了什么。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-ci-where.html",
       "action": "new",
       "ksa": "K",
       "title": "三条路：代码在哪跑",
       "seo": "公司电脑装不了软件，AI 写的代码在哪运行？三条路",
       "desc": "这可能是最卡人的一关，但几乎没人教。三条路，按数据敏感度和使用频率选，没有一条需要你「会编程」。",
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "需求规格：把口径写成它能执行的东西",
     "lessons": [
      {
       "file": "data-spec-four.html",
       "action": "new",
       "ksa": "S",
       "title": "四要素模板",
       "seo": "怎么向 AI 描述一个数据处理需求？四要素模板",
       "desc": "AI 写的代码出错，八成不是代码写错了，是它把你的活理解错了。而理解偏差几乎都发生在同一个地方——你没说的那部分。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-spec-cleaning.html",
       "action": "new",
       "ksa": "S",
       "title": "清洗规则必须逐条写",
       "seo": "AI 做数据清洗为什么最危险？静默错误与逐条写规则",
       "desc": "计算错了，数字可能看着离谱，你还有机会发现。清洗错了，数据看起来完全正常——错误会一路传到汇报，全程没有任何信号。",
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "验收与对账：怎么知道它算对了",
     "lessons": [
      {
       "file": "data-check-three.html",
       "action": "new",
       "ksa": "S",
       "title": "小样、抽查、对总数",
       "seo": "AI 写的脚本跑通了怎么验证算得对？验收三招",
       "desc": "脚本零报错、顺利出结果、数字看起来合理——这三件事加起来也不能证明它算对了。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-check-canary.html",
       "action": "new",
       "ksa": "A",
       "title": "埋雷：给脚本做阴性对照",
       "seo": "怎么验证你的数据脚本本身有效？往里埋一条已知的错",
       "desc": "三招验的是「这次算对了吗」。还有一个更狠的问题：你的验收方式本身，抓得住错吗？",
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "分析模式：让它按你的方式看数",
     "lessons": [
      {
       "file": "data-two-stage.html",
       "action": "new",
       "ksa": "A",
       "title": "两段架构：数据干净之后",
       "seo": "数据干净之后 AI 该干什么？数据活的两段架构",
       "desc": "前面四节全在讲同一件事：别让模型碰数字。这一节要说反过来的一半——有一段活，恰恰只有模型干得了，而且那一段才是你的价值所在。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-pattern.html",
       "action": "new",
       "ksa": "S",
       "title": "把你的分析模式写下来",
       "seo": "怎么把自己的数据分析思路写成 AI 能用的规格？",
       "desc": "「分析模式」听起来抽象，其实它就三件事：你按什么顺序看、什么算异常、什么值得写进结论。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-output.html",
       "action": "new",
       "ksa": "S",
       "title": "从数字到观点",
       "seo": "怎么让 AI 输出判断而不是复述数字？分析输出的纪律",
       "desc": "把分析模式喂进去之后，还差最后一道纪律。这道纪律不设，前面所有功夫会在最后一步全废。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-monthly.html",
       "action": "new",
       "ksa": "S",
       "title": "月报改造全程",
       "seo": "一份经营月报的完整 AI 改造：从口径到一键运行",
       "desc": "前面所有功夫拼起来是什么样？拿一份每月三小时的经营月报走一遍——包括报错和返工，不顺利的部分不剪辑，那才是流程本身。",
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "自动化边界：什么该固化，什么留给人",
     "lessons": [
      {
       "file": "data-auto-three.html",
       "action": "new",
       "ksa": "A",
       "title": "固化三问",
       "seo": "哪些数据活值得固化成脚本？三个问题",
       "desc": "学会一门手艺之后最大的风险，是看什么都像钉子。",
       "free": true,
       "ready": true
      },
      {
       "file": "data-human.html",
       "action": "new",
       "ksa": "A",
       "title": "评价人的活永远留给人",
       "seo": "哪些 HR 数据判断绝对不能自动化？边界与 Skill 判据",
       "desc": "这一节是这一章的刹车。会做不等于该做，尤其当处理对象是人的时候。",
       "free": true,
       "ready": true
      }
     ]
    }
   ]
  },
  {
   "id": "p-5",
   "num": "第五篇章",
   "title": "Vibe Coding：自己做出来",
   "desc": "不是教你写代码，是教你怎么指挥它写。学完能自己做出一个真跑起来的东西 —— 这一项在真实岗位要求里出现得最多。",
   "freeWhole": false,
   "topics": [
    {
     "title": "先立规矩",
     "desc": "",
     "lessons": [
      {
       "file": "vibe-rules.html",
       "action": "copy",
       "ksa": "S",
       "title": "为什么要给 AI 立规矩",
       "seo": "用 AI 写代码为什么要先立规矩？",
       "desc": "",
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
       "file": "vibe-workflow.html",
       "action": "copy",
       "ksa": "S",
       "title": "四步流程：复述、PRD、确认、编码",
       "seo": "不会写代码怎么指挥 AI 做东西？四步协作流程",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "vibe-debug.html",
       "action": "copy",
       "ksa": "S",
       "title": "调试铁律：先 Log 再改码",
       "seo": "AI 写的代码出错了怎么调？先看日志再改代码",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "vibe-complete.html",
       "action": "copy",
       "ksa": "S",
       "title": "不接受分期交付",
       "seo": "让 AI 一次交付完整功能，不接受半成品",
       "desc": "",
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
       "file": "vibe-safety.html",
       "action": "copy",
       "ksa": "S",
       "title": "破坏性操作的三道闸",
       "seo": "怎么防止 AI 误删数据？破坏性操作的三道闸",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "vibe-env.html",
       "action": "copy",
       "ksa": "S",
       "title": "把环境事实写进 Rule",
       "seo": "为什么要把环境信息写进 AI 的规则文件",
       "desc": "",
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
       "file": "vibe-docs.html",
       "action": "copy",
       "ksa": "S",
       "title": "三份文档与方法论沉淀",
       "seo": "跟 AI 协作要维护哪三份文档",
       "desc": "",
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
       "free": true,
       "ready": true
      }
     ]
    },
    {
     "title": "做出你的第一个作品",
     "desc": "把方法用在 HR 场景上，交出一个真能跑的东西",
     "lessons": [
      {
       "file": "hr-project-pick.html",
       "action": "new",
       "ksa": "A",
       "title": "选题：什么样的第一个作品站得住",
       "seo": "HR 做 AI 作品选什么题？六个能站住的选题",
       "desc": "简历初筛是第一选题",
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
       "free": true,
       "ready": true
      },
      {
       "file": "hr-project-build.html",
       "action": "new",
       "ksa": "S",
       "title": "一周做出能点的原型：从想法到 demo",
       "seo": "一周内把一个 HR 场景做成能演示的原型",
       "desc": "",
       "free": false,
       "ready": true
      },
      {
       "file": "hr-project-tell.html",
       "action": "new",
       "ksa": "A",
       "title": "作品怎么讲：别人在追问什么",
       "seo": "AI 作品怎么讲才有说服力？别人真正会追问的问题",
       "desc": "",
       "free": false,
       "ready": true
      }
     ]
    }
   ],
   "color": "#E11D48"
  },
  {
   "id": "p-6",
   "num": "第六篇章",
   "title": "从 Demo 到落地：让它在组织里活下来",
   "desc": "做出来 ≠ 被采用。这一层决定你的天花板。三步走：盘 → 推 → 改。",
   "freeWhole": false,
   "topics": [
    {
     "title": "场景盘点：哪些活能交给它",
     "desc": "不是讲观点，是给可执行的动作",
     "lessons": [
      {
       "file": "hr-inventory-1.html",
       "action": "new",
       "ksa": "A",
       "title": "把一个部门的活拆成任务清单",
       "seo": "怎么盘点一个部门有哪些活能交给 AI？先拆任务清单",
       "desc": "",
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
       "free": true,
       "ready": true
      },
      {
       "file": "hr-inventory-3.html",
       "action": "new",
       "ksa": "A",
       "title": "算账：省多少、风险多大、第一刀切哪",
       "seo": "AI 场景的 ROI 怎么算？第一刀该切哪里",
       "desc": "简历初筛为什么是好的第一刀",
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
       "file": "perm-levels.html",
       "action": "adapt",
       "ksa": "A",
       "title": "AI 该有多大的自由",
       "seo": "AI Agent 该有多大权限？它能不能自己发拒信",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "perm-confirm.html",
       "action": "adapt",
       "ksa": "A",
       "title": "弹窗太多没人用，不弹又不安全",
       "seo": "AI 的确认弹窗怎么设计才不烦人又安全",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "perm-audit.html",
       "action": "adapt",
       "ksa": "A",
       "title": "它干了什么你知道吗：留痕与可申诉",
       "seo": "AI 参与人事决策必须留痕且可申诉",
       "desc": "",
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
       "desc": "",
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
       "free": false,
       "ready": true
      }
     ]
    },
    {
     "title": "人机分工：组织会变成什么样",
     "desc": "AI 接管之后，岗位和能力会怎么变",
     "lessons": [
      {
       "file": "hr-org-1.html",
       "action": "new",
       "ksa": "A",
       "title": "把岗位拆开重组：它接管之后这个岗位还剩什么",
       "seo": "AI 接管之后，HR 岗位该怎么重新设计？",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hr-org-2.html",
       "action": "new",
       "ksa": "A",
       "title": "你会的哪些东西正在被模型吃掉",
       "seo": "HR 的哪些技能正在被 AI 取代？哪些反而更值钱",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "hr-org-3.html",
       "action": "new",
       "ksa": "A",
       "title": "哪些能力反而更值钱了",
       "seo": "AI 时代 HR 哪些能力在升值？按 KSA 拆开看",
       "desc": "接能力词典",
       "free": false,
       "ready": true
      }
     ]
    }
   ],
   "color": "#D97706"
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
       "file": "oss-local-size.html",
       "action": "copy",
       "ksa": "K",
       "title": "你的电脑能跑多大的模型",
       "seo": "普通电脑能跑多大的大模型？",
       "desc": "",
       "free": true,
       "ready": true
      },
      {
       "file": "oss-local-tools.html",
       "action": "copy",
       "ksa": "S",
       "title": "Ollama 与 LM Studio 怎么上手",
       "seo": "Ollama 和 LM Studio 怎么用？本地跑大模型入门",
       "desc": "",
       "free": true,
       "ready": true
      }
     ]
    }
   ],
   "color": "#475569"
  }
 ]
};
