// 页面顺序
const SLIDE_ORDER = [
  { file: 'llm-story.html',            title: '完整目录',               num: 0  },
  { file: '0-intro.html',               title: '我们在哪里',             num: 0  },
  { file: '0-how.html',                 title: '怎样学才有效',           num: 0  },
  { file: '0-why.html',                 title: '为什么要打基础',          num: 0  },
  { file: 'zero-0.html',                title: 'AI 能干哪些神奇的活',     num: 0  },
  { file: 'zero-1.html',                title: '它其实在玩「接话茬」',    num: 0  },
  { file: 'zero-2.html',                title: '它不是搜索引擎',          num: 0  },
  { file: 'zero-3.html',                title: '它会一本正经地胡说',      num: 0  },
  { file: 'zero-4.html',                title: '把它当不了解你的新同事',   num: 0  },
  { file: 'zero-5.html',                title: '万能开场白：先问我',       num: 0  },
  { file: 'zero-q-prompt.html',         title: '提示词到底怎么写才好',     num: 0  },
  { file: 'zero-q-prompt-engineering.html', title: '提示词工程有什么意义', num: 0  },
  { file: 'zero-q-model-agent-app.html', title: '模型、Agent、应用的关系', num: 0  },
  { file: 'zero-q-agent.html',          title: 'Agent 到底强在哪',        num: 0  },
  { file: 'zero-q-skill.html',          title: '最近很火的 Skill 是什么',  num: 0  },
  { file: 'zero-q-china-models.html',   title: '国产大模型怎么选',        num: 0  },
  { file: 'zero-q-companies.html',      title: '还有哪些重要的 AI 公司',   num: 0  },
  { file: 'zero-q-multimodal.html',     title: '为什么有的 AI 看不懂图',   num: 0  },
  { file: 'zero-q-image-cost.html',     title: '生成一张图为什么贵',       num: 0  },
  { file: 'zero-q-video-cost.html',     title: 'AI 视频为什么按秒收费',    num: 0  },
  { file: 'zero-q-relay.html',          title: '什么是 API 中转站',       num: 0  },
  { file: 'zero-q-reverse-proxy.html',  title: '拼车号、共享号是什么',     num: 0  },
  { file: 'zero-6.html',                title: '放心用，还是要核实',       num: 0  },
  { file: 'zero-final.html',            title: '你的下一步',              num: 0  },
  { file: 'training-data.html',         title: '训练数据规模',          num: 1  },
  { file: 'train-vs-infer.html',        title: '训练 vs 推理',          num: 2  },
  { file: '1-2-vocab.html',             title: '词表与训练',             num: 3  },
  { file: '1-2-base.html',              title: 'Base 模型',              num: 4  },
  { file: '1-2-gpt.html',               title: 'GPT 的跃进',             num: 5  },
  { file: '1-2-api.html',               title: 'chat/completions 之谜',  num: 6  },
  { file: '1-2-fake-chat.html',         title: '伪造聊天记录',           num: 7  },
  { file: '1-2-sft.html',               title: 'Chat Template + SFT',    num: 8  },
  { file: '1-2-prompt-power.html',      title: '上下文窗口是关键',       num: 9  },
  { file: '1-2-hallucination.html',     title: '大模型幻觉',             num: 10 },
  { file: '1-2-mitigation-prompt.html', title: 'Prompt Engineering',     num: 11 },
  { file: '1-2-mitigation-rag.html',    title: 'RAG 检索增强',           num: 12 },
  { file: 'rag-advanced.html',          title: 'RAG 代价与优化',         num: 13 },
  { file: '1-2-mitigation-temp.html',   title: 'Temperature & Top-P',    num: 14 },
  { file: '1-2-mitigation-eval.html',   title: '评测 + 人工审核',        num: 15 },
  { file: 'summary-1.html',            title: '第一篇章汇总（上）',      num: 0  },
  { file: 'summary-1b.html',           title: '第一篇章汇总（下）',      num: 0  },
  { file: 'interview-1.html',          title: '他们会这样考你 · 30 问',   num: 0  },
  { file: '5-1.html',                  title: '上下文窗口',              num: 16 },
  { file: '5-2.html',                  title: '上下文溢出策略',          num: 17 },
  { file: '6-0a.html',                title: '为什么选 Markdown',        num: 18 },
  { file: '6-0b.html',                title: 'MD 语法与工程渲染',        num: 19 },
  { file: '6-1.html',                  title: 'Prompt 角色扮演',         num: 20 },
  { file: '6-2.html',                  title: 'Prompt 进阶技巧',         num: 21 },
  { file: '6-3.html',                  title: '输出格式取舍',            num: 22 },
  { file: '6-4.html',                  title: '流式返回与格式',          num: 23 },
  { file: 'prompt-attack.html',        title: 'Prompt 注入原理',         num: 24 },
  { file: 'prompt-attack-cases.html', title: '12 个攻击案例',           num: 25 },
  { file: 'prompt-defense.html',      title: 'Prompt 防御实战',         num: 26 },
  { file: '7-1.html',                  title: 'Agent 概念',              num: 27 },
  { file: '7-2.html',                  title: '工具调用',                num: 28 },
  { file: '7-2a.html',                 title: '一次对话背后的5条消息',     num: 0  },
  { file: '7-2b.html',                 title: '工具描述的学问',            num: 0  },
  { file: '7-2c.html',                 title: '多工具编排',               num: 0  },
  { file: '7-2d.html',                 title: 'MCP 协议',                num: 0  },
  { file: '7-3.html',                  title: 'ReAct 实战',              num: 29 },
  { file: '7-3a.html',                 title: '上下文窗口',               num: 0  },
  { file: '7-3b.html',                 title: '上下文压缩四层策略',        num: 0  },
  { file: '7-3c.html',                 title: '长期记忆',                 num: 0  },
  { file: '7-4a.html',                 title: 'ReAct 循环',              num: 0  },
  { file: '7-4b.html',                 title: 'Agent 卡死的5种模式',      num: 0  },
  { file: '7-4c.html',                 title: '权限与安全',               num: 0  },
  { file: '7-5.html',                  title: 'Skill 技能',              num: 30 },
  { file: '7-5a.html',                 title: 'Skill 的本质',             num: 0  },
  { file: '7-5b.html',                 title: '解剖一个真实 Skill',        num: 0  },
  { file: '7-4.html',                  title: '脚手架工程',              num: 31 },
  { file: '7-6a.html',                 title: '5道工程护栏',              num: 0  },
  { file: '7-6b.html',                 title: '多 Agent 协作',            num: 0  },
  { file: '7-6c.html',                 title: '可观测性',                 num: 0  },
  { file: '7-summary.html',            title: 'Agent 工程全景图',          num: 0  },
  { file: '8-1.html',                  title: '多轮对话成本',            num: 32 },
  { file: '8-2.html',                  title: 'KV Cache',                num: 33 },
  { file: '8-2b.html',                 title: '显式缓存',                num: 34 },
  { file: '8-3.html',                  title: '动态时间戳',              num: 35 },
  { file: '8-4.html',                  title: '综合成本优化',            num: 36 },
  { file: '8-5.html',                  title: '图片 Token 计费',          num: 37 },
  { file: '8-5b.html',                 title: '按任务匹配分辨率',          num: 38 },
  { file: '8-6.html',                  title: '语法层优化',               num: 39 },
  { file: '8-7.html',                  title: '语义层优化',               num: 40 },
  { file: '8-8.html',                  title: '输出层+KV进阶',            num: 41 },
  { file: 'cost-eval.html',            title: '模型选型：能力 vs 成本',   num: 42 },
  { file: 'engineering-philosophy.html', title: '大道至简',               num: 0  },
  { file: 'summary-2.html',            title: '第二篇章汇总（上）',      num: 0  },
  { file: 'summary-2b.html',           title: '第二篇章汇总（下）',      num: 0  },
  { file: 'ai-tips-boundary.html',     title: '人机知识边界',            num: 0  },
  { file: 'ai-tips-context.html',      title: '好提问 vs 坏提问',       num: 0  },
  { file: 'ai-tips-verify.html',       title: 'AI 说的能信吗',          num: 0  },
  { file: 'ai-tips-iterate.html',      title: '迭代的艺术',              num: 0  },
  { file: 'ai-tips-scenarios.html',    title: '场景速查',                num: 0  },
  { file: 'summary-final.html',        title: '课程总结',                num: 0  },
  { file: 'summary-final-1.html',      title: '总结（上）',              num: 0  },
  { file: 'summary-final-2.html',      title: '总结（下）',              num: 0  },
  { file: 'interview-2.html',          title: '他们会这样考你 · 30 问',   num: 0  },
  { file: '9-1.html',                  title: '文生图 vs 垫图',          num: 43 },
  { file: '9-2.html',                  title: '用 AI 给 AI 写 Prompt',   num: 44 },
  { file: '9-3.html',                  title: '角色一致性',              num: 45 },
  { file: '9-4.html',                  title: '模型会挂，然后呢',        num: 46 },
  { file: '9-5.html',                  title: '生图产品化清单',          num: 47 },
  { file: '9-6.html',                  title: '教科书 vs 真实 N 步',     num: 48 },
  { file: '9-7.html',                  title: 'Agent 为什么会卡死',      num: 49 },
  { file: '9-8.html',                  title: '防呆设计',                num: 50 },
  { file: '9-9.html',                  title: '流式体验',                num: 51 },
  { file: '9-10.html',                 title: '一条消息的真实成本',      num: 52 },
  { file: '9-11.html',                 title: '越长越贵越笨',            num: 53 },
  { file: '9-12.html',                 title: '压缩的艺术',              num: 54 },
  { file: '9-13.html',                 title: '用户的话能删吗',          num: 55 },
  { file: '9-14.html',                 title: '本地 vs LLM 压缩',       num: 56 },
  { file: '9-15.html',                 title: '上下文 ≠ 记忆',          num: 57 },
  { file: '9-16.html',                 title: '什么值得记',              num: 58 },
  { file: '9-17.html',                 title: '记忆冲突',                num: 59 },
  { file: '9-18.html',                 title: '记忆注入的成本',          num: 60 },
  { file: '9-19.html',                 title: 'System Prompt 分层',     num: 61 },
  { file: '9-20.html',                 title: '按需加载',                num: 62 },
  { file: '9-21.html',                 title: 'Skill 模块化',           num: 63 },
  { file: '9-22.html',                 title: '提示词与缓存',            num: 64 },
  { file: '9-23.html',                 title: '何时需要多 Agent',       num: 65 },
  { file: '9-24.html',                 title: '并发的代价',              num: 66 },
  { file: '9-25.html',                 title: '脑暴模式',                num: 67 },
  { file: '9-26.html',                 title: '定时任务成本',            num: 68 },
  { file: '9-27.html',                 title: 'AI 的自由度',            num: 69 },
  { file: '9-28.html',                 title: '弹窗与安全平衡',          num: 70 },
  { file: '9-29.html',                 title: '可观测性',                num: 71 },
  { file: '9-30.html',                 title: 'MCP 双向协议',           num: 72 },
  { file: '9-31.html',                 title: '懒连接',                  num: 73 },
  { file: '9-32.html',                 title: 'AI 自加工具',            num: 74 },
  { file: '9-summary.html',            title: '实战全景图',              num: 0  },
  { file: '9-final.html',              title: '聊天套壳 vs Agent 产品', num: 0  },
  { file: 'interview-3.html',          title: '他们会这样考你 · 30 问',   num: 0  },
  { file: '10-1.html',                 title: 'Workflow vs Agent',      num: 75 },
  { file: '10-2.html',                 title: '五种 Workflow 模式',     num: 76 },
  { file: '10-3.html',                 title: '上下文工程方法论',        num: 77 },
  { file: '10-4.html',                 title: '上下文三板斧',            num: 78 },
  { file: '10-5.html',                 title: 'ACI 工具界面设计',       num: 79 },
  { file: '10-6.html',                 title: 'Think Tool',             num: 80 },
  { file: '10-7.html',                 title: '用 Agent 优化工具',      num: 81 },
  { file: '10-8.html',                 title: '评测方法论',              num: 82 },
  { file: '10-9.html',                 title: '三种 Grader',           num: 83 },
  { file: '10-10.html',                title: '评测的坑',                num: 84 },
  { file: '10-11.html',                title: '长任务失败模式',          num: 85 },
  { file: '10-12.html',                title: '双角色 Harness',        num: 86 },
  { file: '10-13.html',                title: 'Managed Agent',         num: 87 },
  { file: '10-14.html',                title: 'Session vs Context',    num: 88 },
  { file: '10-15.html',                title: '三类安全风险',            num: 89 },
  { file: '10-16.html',                title: '沙箱与凭证隔离',          num: 90 },
  { file: '10-17.html',                title: 'Contextual Retrieval',  num: 91 },
  { file: '10-summary.html',           title: '进阶全景图',              num: 0  },
  { file: '10-final.html',             title: 'Do the simplest thing', num: 0  },
  { file: 'interview-4.html',          title: '他们会这样考你 · 30 问',   num: 0  },
  { file: '11-1.html',                 title: '从脚手架到自我改进',      num: 92 },
  { file: '11-2.html',                 title: 'Harness 三大设计模式',   num: 93 },
  { file: '11-3.html',                 title: '上下文工程自动进化',      num: 94 },
  { file: '11-4.html',                 title: '工作流自动搜索',          num: 95 },
  { file: '11-5.html',                 title: '让 Harness 改进自己',    num: 96 },
  { file: '11-6.html',                 title: '进化搜索',                num: 97 },
  { file: '11-7.html',                 title: '未来挑战七道关',          num: 98 },
  { file: 'interview-5.html',          title: '他们会这样考你 · 30 问',   num: 0  },
  { file: 'oss-1.html',                title: '权重是什么',              num: 0  },
  { file: 'oss-2.html',                title: '真开源 vs 假开源',        num: 0  },
  { file: 'oss-3.html',                title: '开源是一门生意',          num: 0  },
  { file: 'oss-4.html',                title: '涌现',                    num: 0  },
  { file: 'oss-5.html',                title: '为什么要把模型做小',       num: 0  },
  { file: 'oss-6.html',                title: '蒸馏是怎么做的',          num: 0  },
  { file: 'oss-7.html',                title: '蒸馏的代价',              num: 0  },
  { file: 'oss-8.html',                title: '你的电脑能跑多大的模型',   num: 0  },
  { file: 'oss-9.html',                title: 'Ollama 与 LM Studio',    num: 0  },
  { file: 'exam.html',                 title: '自测中心',                num: 0  },
  { file: 'exam-1.html',               title: '第一篇章自测 · 50 题',    num: 0  },
  { file: 'exam-2.html',               title: '第二篇章自测 · 50 题',    num: 0  },
  { file: 'exam-3.html',               title: '第三篇章自测 · 50 题',    num: 0  },
  { file: 'exam-4.html',               title: '第四篇章自测 · 50 题',    num: 0  },
  { file: 'exam-5.html',               title: '第五篇章自测 · 50 题',    num: 0  },
  { file: 'exam-6.html',               title: '第六篇章自测 · 50 题',    num: 0  },
  { file: 'exam-7.html',               title: '第七篇章自测 · 50 题',    num: 0  },
  { file: 'exam-all.html',             title: '全站综合考 · 35 题',      num: 0  },
];

// 嵌入模式：被 learn.html 的 iframe 加载时（?embed=1 或在 iframe 内），
// 不注入顶部浮条 / 底部翻页条 / 拍脸图广告，避免与 Wiki 外层 UI 重复。
// PV 统计仍照常上报。
const EMBED_MODE = (function(){
  try {
    if (/[?&]embed=1\b/.test(location.search)) return true;
    if (window.self !== window.top) return true; // 在 iframe 内
  } catch (e) { return true; }
  return false;
})();

// ── i18n 适配：i18n.js 未加载时按中文兜底 ──
const I18N = window.XUEAI_I18N || {
  lang: 'zh',
  t: function (k) { return ({
    toc: '目录', tocTitle: '在课程阅读器中打开，左侧带完整目录', askAuthor: '请教作者',
    today: '今日', total: '总学习', backHomeTitle: '返回首页 (Cmd+↑返回目录)',
    prevTitle: '上一页 (Cmd+←)', nextTitle: '下一页 (Cmd+→)', lastPage: '已是最后一页',
    navHint: '→ 下一步<br>⌘→ 换页', rotateTitle: '请横屏观看',
    rotateSub: '横屏后内容会按比例完整显示<br/>竖屏可关闭后继续浏览', rotateClose: '继续竖屏浏览'
  })[k] || k; },
  baseFile: function (f) { return f; },
  locFile: function (f) { return f; },
  slideTitle: function (f, zh) { return zh; }
};

(function() {

  const cur = I18N.baseFile(location.pathname.split('/').pop());
  const idx = SLIDE_ORDER.findIndex(s => s.file === cur);

  // 无论是否在序列中，都注入顶部栏（请教作者 + PV）
  (function injectTopBar() {
    if (EMBED_MODE) {
      // 嵌入模式下仅静默上报 PV，不渲染浮条
      fetch('/pv').catch(() => {});
      return;
    }
    const style = document.createElement('style');
    style.textContent = `
      #nav-top-bar {
        position: fixed; top: 14px; left: 50%; transform: translateX(-50%);
        display: flex; align-items: center;
        background: rgba(255,255,255,0.82); backdrop-filter: blur(16px);
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 40px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        padding: 0;
        z-index: 9999; font-family: -apple-system, "PingFang SC", sans-serif;
        overflow: hidden;
        max-width: calc(100vw - 16px);
      }
      #nav-author-link, #nav-toc-link {
        font-size: 12px; font-weight: 600; color: #6b6b70;
        text-decoration: none;
        padding: 7px 16px;
        transition: background 0.15s, color 0.15s;
        white-space: nowrap;
        display: flex; align-items: center; gap: 5px;
      }
      #nav-author-link:hover, #nav-toc-link:hover { background: rgba(0,102,255,0.06); color: #0066ff; }
      #nav-toc-link { color: #0066ff; }
      .nav-top-sep {
        width: 1px; height: 20px; background: rgba(0,0,0,0.08); flex-shrink: 0;
      }
      #nav-pv-badge {
        display: flex; align-items: center; gap: 6px;
        padding: 7px 16px;
        font-size: 12px;
      }
      .nav-pv-label { color: #9a9a9f; font-weight: 500; }
      .nav-pv-num-today { color: #0066ff; font-weight: 800; }
      .nav-pv-sep { width:1px; height:12px; background:rgba(0,0,0,0.1); margin: 0 2px; }
      .nav-pv-num-total { color: #7c3aed; font-weight: 800; }
      @media (max-width: 768px) {
        #nav-top-bar { top: 8px; border-radius: 20px; }
        #nav-author-link, #nav-toc-link, #nav-pv-badge { padding: 6px 10px; font-size: 11px; }
        .nav-pv-sep { margin: 0; }
      }
    `;
    document.head.appendChild(style);

    const topBar = document.createElement('div');
    topBar.id = 'nav-top-bar';
    topBar.innerHTML = `
      <a id="nav-toc-link" href="${I18N.locFile('learn.html')}#${encodeURIComponent(cur)}" title="${I18N.t('tocTitle')}">☰ ${I18N.t('toc')}</a>
      <div class="nav-top-sep"></div>
      <a id="nav-author-link" href="https://luoxiaoshan.cn/" target="_blank">${I18N.t('askAuthor')}</a>
      <div class="nav-top-sep"></div>
      <div id="nav-pv-badge">
        <span class="nav-pv-label">${I18N.t('today')}</span>
        <span class="nav-pv-num-today" id="nav-pv-today">—</span>
        <div class="nav-pv-sep"></div>
        <span class="nav-pv-label">${I18N.t('total')}</span>
        <span class="nav-pv-num-total" id="nav-pv-total">—</span>
      </div>
    `;
    document.body.appendChild(topBar);

    fetch('/pv')
      .then(r => r.json())
      .then(d => {
        function fmt(n) {
          n = Number(n) || 0;
          if (I18N.lang === 'zh' && n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, '') + ' 万';
          if (I18N.lang !== 'zh' && n >= 10000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
          return n.toLocaleString('en-US');
        }
        document.getElementById('nav-pv-today').textContent = fmt(d.today);
        document.getElementById('nav-pv-total').textContent = fmt(d.total);
      })
      .catch(() => {});
  })();

  // 嵌入模式 或 不在序列中：不注入底部翻页条（外层 Wiki 已有上一节/下一节）
  if (EMBED_MODE || idx < 0) return;

  const total = SLIDE_ORDER.length;
  const prev  = idx > 0           ? SLIDE_ORDER[idx - 1] : null;
  const next  = idx < total - 1   ? SLIDE_ORDER[idx + 1] : null;

  // 注入样式
  const style = document.createElement('style');
  style.textContent = `
    #slide-nav {
      position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%) translateY(80px);
      display: flex; align-items: center; gap: 10px;
      background: rgba(28,28,30,0.88); backdrop-filter: blur(12px);
      border-radius: 40px; padding: 8px 14px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.18);
      z-index: 9999; font-family: -apple-system, "PingFang SC", sans-serif;
      user-select: none;
      opacity: 0;
      transition: opacity 0.25s ease, transform 0.25s ease;
      pointer-events: none;
      max-width: calc(100vw - 16px);
    }
    #slide-nav.visible {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
      pointer-events: auto;
    }
    /* 触发区：底部不可见热区 */
    #slide-nav-trigger {
      position: fixed; bottom: 0; left: 0; right: 0; height: 60px;
      z-index: 9998; pointer-events: auto;
    }
    .snav-btn {
      background: transparent; border: none; color: rgba(255,255,255,0.55);
      font-size: 13px; font-weight: 600; cursor: pointer;
      padding: 5px 12px; border-radius: 20px; transition: all 0.15s;
      display: flex; align-items: center; gap: 4px;
      max-width: 34vw;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .snav-btn:hover:not(:disabled) { background: rgba(255,255,255,0.1); color: white; }
    .snav-btn:disabled { opacity: 0.25; cursor: not-allowed; }
    .snav-info {
      font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.7);
      padding: 0 8px; min-width: 64px; text-align: center;
    }
    .snav-sep { width: 1px; height: 16px; background: rgba(255,255,255,0.15); }
    .snav-home {
      background: transparent; border: none; color: rgba(255,255,255,0.45);
      font-size: 12px; cursor: pointer; padding: 5px 10px; border-radius: 20px;
      transition: all 0.15s;
    }
    .snav-home:hover { color: white; background: rgba(255,255,255,0.08); }
    @media (max-width: 768px) {
      #slide-nav { bottom: 10px; gap: 6px; padding: 6px 8px; }
      .snav-btn { font-size: 12px; padding: 4px 8px; max-width: 30vw; }
      .snav-info { min-width: 48px; padding: 0 4px; font-size: 11px; }
      .snav-home { padding: 4px 8px; font-size: 11px; }
    }
  `;
  document.head.appendChild(style);

  // 注入 DOM
  const nav = document.createElement('div');
  nav.id = 'slide-nav';
  nav.innerHTML = `
    <button class="snav-home" onclick="location.href='${I18N.locFile('home.html')}'" title="${I18N.t('backHomeTitle')}">☰</button>
    <div class="snav-sep"></div>
    <button class="snav-btn" id="snav-prev" onclick="location.href='${prev ? I18N.locFile(prev.file) : ''}'" ${!prev ? 'disabled' : ''} title="${I18N.t('prevTitle')}">
      ← ${prev ? I18N.slideTitle(prev.file, prev.title) : ''}
    </button>
    <div class="snav-info">${idx + 1} / ${total}</div>
    <button class="snav-btn" id="snav-next" onclick="location.href='${next ? I18N.locFile(next.file) : ''}'" ${!next ? 'disabled' : ''} title="${I18N.t('nextTitle')}">
      ${next ? I18N.slideTitle(next.file, next.title) : I18N.t('lastPage')} ${next ? '→' : ''}
    </button>
    <div class="snav-sep"></div>
    <div style="font-size:10px;color:rgba(255,255,255,0.3);padding:0 4px;line-height:1.4;text-align:center">${I18N.t('navHint')}</div>
  `;
  // 触发热区
  const trigger = document.createElement('div');
  trigger.id = 'slide-nav-trigger';
  document.body.appendChild(trigger);
  document.body.appendChild(nav);

  // 鼠标移入底部热区或导航条时显示
  let hideTimer = null;
  function showNav() {
    clearTimeout(hideTimer);
    nav.classList.add('visible');
  }
  function scheduleHide() {
    hideTimer = setTimeout(() => nav.classList.remove('visible'), 800);
  }
  trigger.addEventListener('mouseenter', showNav);
  trigger.addEventListener('mouseleave', scheduleHide);
  nav.addEventListener('mouseenter', showNav);
  nav.addEventListener('mouseleave', scheduleHide);

  // 前 3 次访问自动弹出 2 秒
  const AUTO_SHOW_KEY = 'slide_nav_auto_count';
  const count = parseInt(localStorage.getItem(AUTO_SHOW_KEY) || '0', 10);
  if (count < 3) {
    localStorage.setItem(AUTO_SHOW_KEY, count + 1);
    setTimeout(() => {
      showNav();
      setTimeout(() => scheduleHide(), 2000);
    }, 600);
  }

  // 键盘快捷键
  document.addEventListener('keydown', e => {
    const cmd = e.metaKey || e.ctrlKey;

    // Cmd + ↑ → 返回目录
    if (cmd && e.key === 'ArrowUp') {
      e.preventDefault();
      // 判断当前页属于哪个篇章
      const base = cur.replace('.html','');
      const ch4Files = ['10-1','10-2','10-3','10-4','10-5','10-6','10-7',
        '10-8','10-9','10-10','10-11','10-12','10-13','10-14','10-15','10-16',
        '10-17','10-summary','10-final'];
      const ch3Files = ['9-1','9-2','9-3','9-4','9-5','9-6','9-7','9-8','9-9','9-10',
        '9-11','9-12','9-13','9-14','9-15','9-16','9-17','9-18','9-19','9-20',
        '9-21','9-22','9-23','9-24','9-25','9-26','9-27','9-28','9-29','9-30',
        '9-31','9-32','9-summary','9-final'];
      const ch2Files = ['5-1','5-2','6-0a','6-0b','6-1','6-2','6-3','6-4',
        'prompt-attack','prompt-attack-cases','prompt-defense',
        '7-1','7-2','7-3','7-4','7-5','8-1','8-2','8-2b','8-3','8-4','8-5','8-5b',
        '8-6','8-7','8-8','cost-eval','engineering-philosophy','summary-2','summary-2b'];
      if (ch4Files.includes(base)) { location.href = I18N.locFile('learn.html') + '#10-1.html'; }
      else if (ch3Files.includes(base)) { location.href = I18N.locFile('learn.html') + '#9-1.html'; }
      else { location.href = I18N.locFile(ch2Files.includes(base) ? 'story-2.html' : 'llm-story.html'); }
      return;
    }

    // Cmd + → → 下一页
    if (cmd && e.key === 'ArrowRight') {
      e.preventDefault();
      if (next) location.href = I18N.locFile(next.file);
      return;
    }

    // Cmd + ← → 上一页
    if (cmd && e.key === 'ArrowLeft') {
      e.preventDefault();
      if (prev) location.href = I18N.locFile(prev.file);
      return;
    }

    // 单独 → → 页面内下一步（nextStep 或 playDemo）
    if (!cmd && e.key === 'ArrowRight') {
      if (typeof window.nextStep === 'function') {
        e.preventDefault();
        window.nextStep();
      } else if (typeof window.playDemo === 'function') {
        e.preventDefault();
        window.playDemo();
      }
      return;
    }

    // 单独 ← → 页面内上一步（如果有）
    if (!cmd && e.key === 'ArrowLeft') {
      if (typeof window.prevStep === 'function') {
        e.preventDefault();
        window.prevStep();
      }
      return;
    }
  });

  // ── 触摸滑动翻页 ──────────────────────────────────────────
  (function initTouchSwipe() {
    let startX = 0, startY = 0;
    document.addEventListener('touchstart', e => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    }, { passive: true });
    document.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - startX;
      const dy = e.changedTouches[0].clientY - startY;
      if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy)) return;
      if (dx < 0 && next) location.href = I18N.locFile(next.file);   // 左滑 → 下一页
      if (dx > 0 && prev) location.href = I18N.locFile(prev.file);   // 右滑 → 上一页
    }, { passive: true });
  })();

})();

// ── 幻灯片适配：CSS 等比缩放 + 竖屏提示（可关闭，不强拦截）──────────
(function initSlideAdapt() {

  // 注入 meta viewport
  if (!document.querySelector('meta[name="viewport"]')) {
    const m = document.createElement('meta');
    m.name = 'viewport';
    m.content = 'width=device-width, initial-scale=1, viewport-fit=cover';
    document.head.appendChild(m);
  }

  // 纯 CSS 方案：避免 iOS Safari 的 vh / scale / autosize 陷阱
  const style = document.createElement('style');
  style.textContent = `
    html, body {
      -webkit-text-size-adjust: 100%;
      text-size-adjust: 100%;
    }

    :root {
      --slide-pad-x: 8px;
      --slide-pad-top: 40px;
      --slide-pad-bottom: 56px;
    }

    /* 横屏：按 16:9 反推宽度，确保上下留白且不裁剪 */
    @media (orientation: landscape) {
      .slide {
        width: min(94vw, calc((100vh - var(--slide-pad-top) - var(--slide-pad-bottom)) * 16 / 9)) !important;
        max-width: 1440px !important;
      }
    }

    /* 支持 dvh 的浏览器优先用 dvh（iOS 更稳定） */
    @supports (height: 100dvh) {
      @media (orientation: landscape) {
        .slide {
          width: min(94vw, calc((100dvh - var(--slide-pad-top) - var(--slide-pad-bottom)) * 16 / 9)) !important;
        }
      }
    }

    #slide-rotate-mask {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 99999;
      background: rgba(28, 28, 30, 0.9);
      color: #fff;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 14px;
      font-family: -apple-system, "PingFang SC", sans-serif;
      padding: 20px;
      text-align: center;
    }
    #slide-rotate-mask .icon {
      font-size: 34px;
      line-height: 1;
    }
    #slide-rotate-mask .title {
      font-size: 17px;
      font-weight: 700;
    }
    #slide-rotate-mask .sub {
      font-size: 13px;
      color: rgba(255,255,255,0.45);
      text-align: center;
      line-height: 1.6;
    }
    #slide-rotate-close {
      margin-top: 6px;
      border: 1px solid rgba(255,255,255,0.3);
      background: rgba(255,255,255,0.08);
      color: #fff;
      border-radius: 999px;
      font-size: 14px;
      font-weight: 600;
      padding: 8px 18px;
      cursor: pointer;
    }
    #slide-rotate-close:active {
      transform: scale(0.98);
    }

    /* 仅小屏竖屏显示遮罩，避免误伤桌面窄窗口 */
    @media (orientation: portrait) and (max-width: 1024px) {
      #slide-rotate-mask { display: flex; }
      #slide-rotate-mask.dismissed { display: none; }
    }
  `;
  document.head.appendChild(style);

  const mask = document.createElement('div');
  mask.id = 'slide-rotate-mask';
  mask.innerHTML = '<div class="icon">↻</div>' +
    '<div class="title">' + I18N.t('rotateTitle') + '</div>' +
    '<div class="sub">' + I18N.t('rotateSub') + '</div>' +
    '<button id="slide-rotate-close" type="button">' + I18N.t('rotateClose') + '</button>';
  document.body.appendChild(mask);

  const MASK_DISMISS_KEY = 'slide_rotate_mask_dismissed';
  const closeBtn = document.getElementById('slide-rotate-close');

  function updateMaskState() {
    const isPortrait = window.matchMedia('(orientation: portrait)').matches;
    const isSmallScreen = window.matchMedia('(max-width: 1024px)').matches;
    const dismissed = sessionStorage.getItem(MASK_DISMISS_KEY) === '1';
    if (isPortrait && isSmallScreen && dismissed) {
      mask.classList.add('dismissed');
    } else {
      mask.classList.remove('dismissed');
    }
  }

  closeBtn?.addEventListener('click', () => {
    sessionStorage.setItem(MASK_DISMISS_KEY, '1');
    mask.classList.add('dismissed');
  });

  // ── 竖屏画布缩放：强制设定桌面分辨率后整体缩小 ──
  function applyCanvasScale() {
    const isPortrait = window.matchMedia('(orientation: portrait)').matches;
    const isSmallScreen = window.matchMedia('(max-width: 1024px)').matches;
    
    let styleEl = document.getElementById('mobile-canvas-scale');
    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = 'mobile-canvas-scale';
      document.head.appendChild(styleEl);
    }

    if (isPortrait && isSmallScreen) {
      const vw = window.innerWidth;
      
      // 基准设计分辨率：宽 960px，高 540px
      const designW = 960;
      const designH = 540;
      
      // 缩放比例
      const scale = vw / designW;
      const topGap = 60; // 顶部导航栏空间
      const leftOffset = (vw - designW * scale) / 2;
      const bodyH = Math.round(designH * scale + topGap + 20);

      styleEl.textContent = `
        body {
          height: ${bodyH}px !important;
          overflow-y: auto !important;
          overflow-x: hidden !important;
          display: block !important;
        }
        .slide, .slide-container {
          width: ${designW}px !important;
          height: ${designH}px !important;
          max-width: none !important;
          max-height: none !important;
          aspect-ratio: auto !important;
          margin: 0 !important;
          flex-shrink: 0 !important;
          position: absolute !important;
          left: ${leftOffset}px !important;
          top: ${topGap}px !important;
          transform-origin: top left !important;
          transform: scale(${scale}) !important;
        }
      `;
    } else {
      styleEl.textContent = '';
    }
  }

  window.addEventListener('orientationchange', () => {
    setTimeout(updateMaskState, 150);
    setTimeout(applyCanvasScale, 150);
  });
  window.addEventListener('resize', () => {
    updateMaskState();
    applyCanvasScale();
  });
  
  updateMaskState();
  applyCanvasScale();
})();

// ── 站内推荐弹层（后台称「拍脸图」，独立脚本，下架时删除此段及 splash.js 即可） ──
// 嵌入模式（Wiki iframe 内）不弹。
// 脚本名不得含 ad：旧名 interstitial-ad.js 命中广告拦截插件的 `-ad.js` 规则，
// 当天 23,039 次页面加载里只有 141 次真正请求到它，详见 splash.js 头部注释。
(function () {
  if (EMBED_MODE) return;
  var s = document.createElement('script');
  s.src = 'splash.js?v=20260807';
  s.async = true;
  document.head.appendChild(s);
})();

// ── 行为埋点（管理后台用户画像；带 xueai_sess Cookie 自动关联登录用户） ──
// 原先此处直接一发 /api/visit（只记路径，且 EMBED 模式不上报，阅读器内
// 行为全丢）。现由 track.js 接管：会话 + 行为链路 + 每页停留时长上报到
// /api/track，服务端同步写回 legacy visits/users 表，旧统计口径不断档。
// EMBED 模式（learn.html iframe 内）也照常加载，学习行为不再丢失。
(function () {
  try {
    var s = document.createElement('script');
    s.src = 'track.js?v=20260806';
    s.async = true;
    document.head.appendChild(s);
  } catch (e) { /* 埋点加载失败不影响浏览 */ }
})();

// ── 问问 Alice：划词提问/吐槽 + Alice 悬浮窗（独立脚本，下架删除此段即可）──
// 「我要吐槽」也在这个脚本里：由 Alice 对话式引导后转交 /api/feedback，
// 独立的 feedback.js 表单面板已于 2026-08-08 下线。
// EMBED 模式（learn.html iframe 内）也照常加载：阅读器里同样可以划词提问。
(function () {
  try {
    var s = document.createElement('script');
    s.src = 'ask-alice.js?v=20260809s';
    s.async = true;
    document.head.appendChild(s);
  } catch (e) { /* 加载失败不影响浏览 */ }
})();

// ── 嵌入模式下的站内跳页：交给外壳换 hash，别让 iframe 自己跳 ──
// 课件正文里的站内链接（如 interview-* 的「用这些课程页组织答案」）写的是相对
// 路径。iframe 自己跳过去的话，外壳 learn.html 的 hash 和左侧目录都不会动，用户
// 落在一个没有目录、没有翻页条的裸页上，回不来。改成通知外壳换 hash 后，进度、
// 目录高亮、上一节/下一节都照常跟随。
// hash 里存的是中文基名（三个语言外壳共用一套 hash），所以要先还原语言后缀。
(function () {
  if (!EMBED_MODE) return;

  // 只接管指向同目录课程页的链接，外链和目录外的页面一律放行
  function targetLesson(a) {
    if (a.target && a.target !== '_self') return null;
    const href = a.getAttribute('href') || '';
    if (!/^[\w.-]+\.html(#.*)?$/.test(href)) return null;
    const file = I18N.baseFile(href.split('#')[0]);
    return SLIDE_ORDER.some(s => s.file === file) ? file : null;
  }

  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; // 新标签页打开，不拦
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    const file = targetLesson(a);
    if (!file) return;
    try {
      window.top.location.hash = '#' + encodeURIComponent(file);
      e.preventDefault();
    } catch (err) { /* 拿不到外壳（理论上跨域）时按普通链接走 */ }
  }, true);
})();

// 付费墙已停用，课程全部免费开放。
