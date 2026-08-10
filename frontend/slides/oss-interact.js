/* ═══════════════════════════════════════════════════════════
   oss-interact.js —— 开源篇章 oss-1 到 oss-7 的动手 demo 逻辑

   背景：这一章原本七节全是纯文字。参数量与体积的换算、许可证档次的判定、
   能力在某个规模突然涌现、温度系数把概率分布调软，这些东西读一遍是「知道有
   这回事」，拖一次滑块才是「有手感」。
   设计意图：把七个 demo 的计算部分从页面里抽出来集中在这里，浏览器与 Node
   共用同一份实现。这些数字会直接出现在课程结论里（比如「差一到两个数量级」
   「8B 在 FP16 下装不进 8GB 显卡」），必须能被单测锁死，不能散在各页脚本里。
   约束：精度系数与 oss-8 的 oss-calc.js 共用同一套口径，此处只保留「每个数
   占几个字节」的存储换算，运行时显存一律走 oss-calc.js，避免一章里两套数。
   ═══════════════════════════════════════════════════════════ */

(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  if (root) { root.OSSInteract = api; }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  /* ── oss-1：参数量 → 权重文件体积 ──
     这里是纯存储换算，一个参数占几个字节，跟运行时要多少显存是两件事。
     页面上必须把这个区别说清楚，否则学员会拿 16GB 去买 16GB 的显卡。 */
  var BYTES = {
    fp32: { label: 'FP32', bytes: 4 },
    fp16: { label: 'FP16', bytes: 2 },
    int8: { label: 'INT8', bytes: 1 },
    int4: { label: 'INT4', bytes: 0.5 },
  };

  /* 滑块要跨越 0.5B 到 2400B 共四个数量级，线性刻度会让 90% 的行程都堆在
     几百 B 以上，小模型区间根本拖不准。所以滑块位置走对数。
     刻度取 0 到 1000 而不是 0 到 100：四个数量级分成 100 档的话每档要跳
     9%，学员想停在 8B 这种整数档位会停不住，只能在 7.6 和 8.3 之间反复。
     分成 1000 档后每档不到 1%，拖起来才有停得住的手感。 */
  var PARAM_MIN = 0.5;
  var PARAM_MAX = 2400;
  var SLIDER_STEPS = 1000;

  function posToParams(pos) {
    var p = Math.max(0, Math.min(SLIDER_STEPS, Number(pos)));
    var lo = Math.log(PARAM_MIN), hi = Math.log(PARAM_MAX);
    var v = Math.exp(lo + (hi - lo) * (p / SLIDER_STEPS));
    return v < 10 ? Math.round(v * 10) / 10 : Math.round(v);
  }

  function paramsToPos(params) {
    var v = Math.max(PARAM_MIN, Math.min(PARAM_MAX, Number(params)));
    var lo = Math.log(PARAM_MIN), hi = Math.log(PARAM_MAX);
    return Math.round((Math.log(v) - lo) / (hi - lo) * SLIDER_STEPS);
  }

  function fileSize(paramsB, precision) {
    var b = BYTES[precision];
    if (!b) { throw new Error('未知精度: ' + precision); }
    if (typeof paramsB !== 'number' || !(paramsB > 0)) {
      throw new Error('参数量必须为正数: ' + paramsB);
    }
    return Math.round(paramsB * b.bytes * 10) / 10;
  }

  /* 三档常见显存，用来给出「装得进 / 装不进」的即时反馈。
     判定只看权重能否载入，不含运行开销，页面上标注了这一点。 */
  var CARDS = [8, 16, 24];

  function fitCards(sizeGb) {
    return CARDS.map(function (c) {
      return { vram: c, fit: sizeGb <= c };
    });
  }

  /* ── oss-2：许可证三问 → 档次判定 ──
     三个问题按顺序问，任何一问答「否」就不必再往下问了，这本身就是教学点：
     判断一个模型是不是真开源，第一关就能筛掉大部分。 */
  var LICENSE_Q = ['download', 'commercial', 'distill'];

  function judgeLicense(answers) {
    if (!answers || typeof answers !== 'object') {
      throw new Error('answers 必须是对象');
    }
    if (answers.download === 'no') { return 'closed'; }
    if (answers.download == null) { return null; }
    if (answers.commercial == null) { return null; }
    if (answers.commercial === 'no') { return 'restricted'; }
    if (answers.distill == null) { return null; }
    if (answers.commercial === 'limited' || answers.distill === 'no') {
      return 'conditional';
    }
    return 'open';
  }

  /* 每一档配几个真实样本，学员走完流程后能立刻对照「哦，我判出来的这一档
     里都有谁」。样本与 oss-2 页面上的三档表保持一致。
     这里一律只放模型名。曾经用过「部分研究许可模型」这种描述性写法，
     结果英韩页面上直接漏出中文，专有名词三语通用才不会有这个问题。 */
  var TIER_SAMPLE = {
    /* 这里只放许可证已经公布、且确实归得进这一档的模型。
       Qwen3.8-Max 曾经列在这里，但它的权重尚未放出、许可证也没公布，
       归档所需的信息都还不存在，列进来等于替它做了判断。 */
    open: ['Qwen3-8B', 'DeepSeek-R1', 'Mistral-7B'],
    conditional: ['Llama 3', 'Gemma'],
    restricted: ['LLaMA 1', 'OPT-175B'],
    closed: ['GPT', 'Claude', 'Gemini'],
  };

  /* ── oss-3：商业模式 → 开源策略 ──
     这一节要让学员意识到开源不是慷慨，是算过账的。选自己的主营业务，
     看到对应的策略，比读一张六行的表印象深。 */
  var BIZ = [
    { id: 'ads',      strategy: 'open',   who: 'Meta' },
    { id: 'cloud',    strategy: 'open',   who: 'Alibaba Cloud / Google' },
    { id: 'api',      strategy: 'closed', who: 'OpenAI / Anthropic' },
    { id: 'service',  strategy: 'open',   who: 'Mistral' },
    { id: 'research', strategy: 'open',   who: 'DeepSeek' },
    { id: 'model',    strategy: 'closed', who: 'OpenAI' },
  ];

  function bizStrategy(id) {
    for (var i = 0; i < BIZ.length; i++) {
      if (BIZ[i].id === id) { return BIZ[i]; }
    }
    return null;
  }

  /* ── oss-4：规模 → 能力是否涌现 ──
     阈值取自 oss-4 页面上引用的公开观察，都是示意值而非精确测量，
     页面上必须标明这一点。换架构或换训练方法阈值会整体偏移。 */
  var ABILITIES = [
    { id: 'translate', threshold: 1,   emergent: false },
    { id: 'multiling', threshold: 7,   emergent: true },
    { id: 'tooljson',  threshold: 7,   emergent: true },
    { id: 'math',      threshold: 10,  emergent: true },
    { id: 'roleplay',  threshold: 13,  emergent: true },
    { id: 'cot',       threshold: 100, emergent: true },
  ];

  function abilitiesAt(paramsB) {
    if (typeof paramsB !== 'number' || !(paramsB > 0)) {
      throw new Error('参数量必须为正数: ' + paramsB);
    }
    return ABILITIES.map(function (a) {
      return { id: a.id, threshold: a.threshold, on: paramsB >= a.threshold };
    });
  }

  /* 两条曲线的取值：一条平滑上升代表常规能力，一条在阈值前贴地、
     跨过之后陡升代表涌现能力。用于页面上的探针跟随。 */
  function smoothScore(paramsB) {
    var t = Math.log(paramsB / PARAM_MIN) / Math.log(PARAM_MAX / PARAM_MIN);
    return Math.round(Math.max(0, Math.min(1, t)) * 100);
  }

  function emergentScore(paramsB, threshold) {
    var th = threshold || 10;
    if (paramsB < th) {
      /* 阈值前不是恒等于零，是贴着地面缓慢爬，写死为 0 会让曲线看起来
         像开关而不是涌现。 */
      return Math.round(Math.min(6, (paramsB / th) * 6));
    }
    var over = Math.log(paramsB / th) / Math.log(PARAM_MAX / th);
    return Math.round(6 + Math.min(1, over * 2.2) * 88);
  }

  /* ── oss-5：请求量 → 成本与延迟 ──
     单价为公开价目的数量级示意，页面上标注了「示意，非实测报价」。
     这里要的是让学员看到两条曲线的开口差距，不是精确报价。 */
  var TIER_COST = {
    flagship: { perK: 0.06, latencyMs: 2800 },
    small:    { perK: 0.001, latencyMs: 320 },
  };

  function monthlyCost(dailyCalls, tier) {
    var t = TIER_COST[tier];
    if (!t) { throw new Error('未知档位: ' + tier); }
    if (typeof dailyCalls !== 'number' || dailyCalls < 0) {
      throw new Error('请求量不能为负: ' + dailyCalls);
    }
    return Math.round(dailyCalls / 1000 * t.perK * 30 * 100) / 100;
  }

  function costRatio(dailyCalls) {
    var a = monthlyCost(dailyCalls, 'flagship');
    var b = monthlyCost(dailyCalls, 'small');
    if (b <= 0) { return 0; }
    return Math.round(a / b);
  }

  /* ── oss-6：温度系数 → 软标签分布 ──
     这是本章最抽象的一个概念，也是最适合动手的一个。教师模型原始的
     打分（logits）经过 softmax(z/T) 得到概率，T 越大分布越平缓，
     学生能学到的「猫像狗但不像兔」这类信息就越多。 */
  var TEACHER_LOGITS = [
    { id: 'cat', z: 6.0 },
    { id: 'dog', z: 4.7 },
    { id: 'rabbit', z: 3.4 },
    { id: 'car', z: 0.2 },
  ];

  function softmax(logits, temperature) {
    var T = Number(temperature);
    if (!(T > 0)) { throw new Error('温度必须大于 0: ' + temperature); }
    if (!Array.isArray(logits) || logits.length === 0) {
      throw new Error('logits 不能为空');
    }
    /* 减去最大值再取指数，避免 T 很小时 Math.exp 溢出成 Infinity。
       T=0.1 时 z/T 会到 60，exp(60) 已经很接近浮点上限。 */
    var scaled = logits.map(function (l) { return l / T; });
    var max = Math.max.apply(null, scaled);
    var exps = scaled.map(function (s) { return Math.exp(s - max); });
    var sum = exps.reduce(function (a, b) { return a + b; }, 0);
    return exps.map(function (e) { return e / sum; });
  }

  function teacherDist(temperature) {
    var probs = softmax(TEACHER_LOGITS.map(function (t) { return t.z; }), temperature);
    return TEACHER_LOGITS.map(function (t, i) {
      return { id: t.id, p: Math.round(probs[i] * 1000) / 10 };
    });
  }

  /* 用分布的熵衡量「学生能学到多少信息」。硬标签的熵是 0，因为除了
     正确答案之外什么都没说；温度越高熵越大，携带的相似性信息越多。
     归一化到 0 到 100，页面上显示为一条信息量的条。 */
  function infoRichness(temperature) {
    var probs = softmax(TEACHER_LOGITS.map(function (t) { return t.z; }), temperature);
    var h = 0;
    probs.forEach(function (p) { if (p > 0) { h -= p * Math.log(p); } });
    var hMax = Math.log(probs.length);
    return Math.round(h / hMax * 100);
  }

  /* ── oss-7：血缘追溯 ──
     学员挑三个「看起来不同」的模型做交叉验证，追溯之后发现同源。
     base 字段是这些模型公开的底座信息。 */
  var LINEAGE = [
    { id: 'a', base: 'qwen' },
    { id: 'b', base: 'qwen' },
    { id: 'c', base: 'qwen' },
    { id: 'd', base: 'llama' },
    { id: 'e', base: 'llama' },
    { id: 'f', base: 'independent' },
  ];

  function lineageOf(ids) {
    if (!Array.isArray(ids)) { throw new Error('ids 必须是数组'); }
    return ids.map(function (id) {
      for (var i = 0; i < LINEAGE.length; i++) {
        if (LINEAGE[i].id === id) { return LINEAGE[i]; }
      }
      return null;
    }).filter(Boolean);
  }

  /* 交叉验证是否可靠：只要选中的模型全部同源，就是虚假的安全感。
     只有当血缘里出现两种以上底座，这次交叉验证才算数。 */
  function crossCheckVerdict(ids) {
    var picked = lineageOf(ids);
    if (picked.length < 2) { return null; }
    var bases = {};
    picked.forEach(function (p) { bases[p.base] = true; });
    var kinds = Object.keys(bases).length;
    return { kinds: kinds, reliable: kinds > 1, bases: Object.keys(bases) };
  }

  /* ── 界面文案 ──
     本模块被中英韩三套页面加载。oss-calc.js 早期版本把中文写死在渲染里，
     导致译版页面显示中文，这里从一开始就走语言包，新增语言只需补一份。 */
  var I18N = {
    zh: {
      fileOf: function (gb) { return gb + ' GB'; },
      fitYes: '装得下', fitNo: '装不下',
      cardLabel: function (gb) { return gb + ' GB 显卡'; },
      paramLabel: function (b) { return b >= 1000 ? (b / 1000) + ' 万亿' : b + ' B'; },
      bytesNote: function (n, label) {
        return label + '：每个参数占 ' + n + ' 字节';
      },
      tier: {
        open: '第一档：标准开源许可',
        conditional: '第二档：附加条件',
        restricted: '第二档：限制商用',
        closed: '第三档：只给 API',
      },
      tierDesc: {
        open: '权重可下载、可商用、可用于训练新模型，没有额外门槛。',
        conditional: '权重给了，但许可证里加了自己的条款，商用或再训练受限。',
        restricted: '权重能拿到，但不允许商业使用，只能研究。',
        closed: '拿不到权重，只能调接口。能力再强也不是开源。',
      },
      sampleLabel: '这一档里有：',
      listSep: '、',
      qDownload: '权重能下载吗？',
      qCommercial: '能商用吗？',
      qDistill: '能用它的输出训练新模型吗？',
      ansYes: '能', ansNo: '不能', ansLimited: '有条件',
      restart: '重新判断',
      bizName: {
        ads: '卖广告', cloud: '卖云和算力', api: '卖 API 订阅',
        service: '卖企业定制服务', research: '做研究攒声誉', model: '直接卖模型',
      },
      bizLogic: {
        ads: '模型是你主业的互补品。互补品越便宜，你的主业越值钱，所以你会希望全世界都能免费拿到好模型。',
        cloud: '开发者拿模型去微调和部署，算力需求最终回到你的云上。模型免费，算力收费。',
        api: '模型本身就是你在卖的东西。开源等于把自己的商品免费送出去，跟收入结构直接冲突。',
        service: '模型用来建立技术声誉，钱从私有化部署和定制合同里来，不靠接口锁住客户。',
        research: '用最宽松的许可换全球范围的关注度，一次发布带来的声誉远超同等投入的营销费用。',
        model: '你的收入直接来自模型授权。把权重放出去，等于取消了自己的收费理由。',
      },
      youLean: '按这个收入结构，你多半会',
      strategy: { open: '倾向开源', closed: '倾向闭源' },
      bizWho: function (who) { return '代表：' + who; },
      abilityOn: '已涌现', abilityOff: '还没有',
      abilityName: {
        translate: '照着例子续写', multiling: '跨语言问答', tooljson: '稳定输出 JSON',
        math: '多步数学推理', roleplay: '长对话里守住人设', cot: '思维链推理',
      },
      emergedCount: function (n, total) { return total + ' 项里已经出现 ' + n + ' 项'; },
      thresholdAt: function (b) { return '约 ' + b + 'B'; },
      scaleNow: function (b) { return '当前规模：' + (b >= 1000 ? (b / 1000) + ' 万亿' : b + ' B'); },
      costMonthly: function (v) { return '￥' + v.toLocaleString('zh-CN'); },
      costFlagship: '旗舰模型', costSmall: '蒸馏小模型',
      costRatio: function (n) { return '差 ' + n + ' 倍'; },
      costGap: function (v) { return '每月多付 ￥' + v.toLocaleString('zh-CN'); },
      costBarNote: '两条的长度比就是成本比。这个比例由单价决定，不随规模变化——所以拖滑块时变的是上面的金额，不是条的长短。',
      latency: function (ms) { return ms + ' ms'; },
      dailyCalls: function (n) { return '每天 ' + n.toLocaleString('zh-CN') + ' 次请求'; },
      labelCat: '猫', labelDog: '狗', labelRabbit: '兔', labelCar: '汽车',
      hardLabel: '硬标签', softLabel: '软标签',
      tempNow: function (t) { return 'T = ' + t; },
      infoLabel: '学生能学到的信息量',
      tempHintLow: '分布很尖，几乎只告诉学生「是猫」，跟硬标签差不多。',
      tempHintMid: '分布软下来了，学生开始知道猫比较像狗、不太像兔。',
      tempHintHigh: '太平了，各类差异被抹掉，噪音开始盖过有用信息。',
      pickAtLeast: '再选一个模型，才能做交叉验证',
      verdictSame: '这三个都从同一个底座蒸馏而来。它们答错的时候，会错得一模一样，交叉验证在这里给不了你任何保障。',
      verdictMixed: '血缘里有不同的底座，这次交叉验证才算数。',
      traceBtn: '追溯血缘',
      lineageName: {
        a: '星尘助手', b: '灵犀对话', c: '明析问答',
        d: '岩层 Chat', e: '海图助理', f: '自研模型 X',
      },
      lineageVendor: {
        a: '星尘科技', b: '灵犀网络', c: '明析数据',
        d: '岩层智能', e: '海图云', f: '内部团队',
      },
      pickHint: '挑三个看起来最不相干的产品，然后点下面的按钮。',
      baseName: { qwen: 'Qwen 底座', llama: 'Llama 底座', independent: '独立训练' },
    },
    en: {
      fileOf: function (gb) { return gb + ' GB'; },
      fitYes: 'Fits', fitNo: 'Too big',
      cardLabel: function (gb) { return gb + ' GB card'; },
      paramLabel: function (b) { return b >= 1000 ? (b / 1000) + 'T' : b + 'B'; },
      bytesNote: function (n, label) {
        return label + ': ' + n + ' bytes per parameter';
      },
      tier: {
        open: 'Tier 1: standard open-source license',
        conditional: 'Tier 2: extra conditions',
        restricted: 'Tier 2: no commercial use',
        closed: 'Tier 3: API only',
      },
      tierDesc: {
        open: 'Weights downloadable, commercial use allowed, training new models allowed, no extra hurdles.',
        conditional: 'Weights are released, but the license adds custom clauses limiting commercial use or retraining.',
        restricted: 'You can get the weights, but commercial use is off the table. Research only.',
        closed: 'No weights, only an endpoint. However capable, it is not open source.',
      },
      sampleLabel: 'Also in this tier: ',
      listSep: ', ',
      qDownload: 'Can you download the weights?',
      qCommercial: 'Can you use it commercially?',
      qDistill: 'Can you train a new model on its output?',
      ansYes: 'Yes', ansNo: 'No', ansLimited: 'With conditions',
      restart: 'Start over',
      bizName: {
        ads: 'Selling ads', cloud: 'Selling cloud and compute', api: 'Selling API subscriptions',
        service: 'Selling enterprise customization', research: 'Building reputation through research', model: 'Selling the model itself',
      },
      bizLogic: {
        ads: 'The model is a complement to your real business. The cheaper the complement, the more valuable your core product, so you want everyone to have a good model for free.',
        cloud: 'Developers fine-tune and deploy the model, and the compute demand comes back to your cloud. Free models, paid compute.',
        api: 'The model is the product you sell. Open-sourcing it means giving away your inventory, which collides head-on with your revenue.',
        service: 'The model builds technical credibility. The money comes from private deployments and custom contracts, not from locking customers into an endpoint.',
        research: 'The most permissive license buys worldwide attention. One release earns more reputation than a marketing budget of the same size.',
        model: 'Your revenue comes directly from licensing the model. Releasing the weights removes the reason anyone would pay you.',
      },
      youLean: 'Given that revenue structure, you would most likely ',
      strategy: { open: 'lean open', closed: 'lean closed' },
      bizWho: function (who) { return 'Example: ' + who; },
      abilityOn: 'Emerged', abilityOff: 'Not yet',
      abilityName: {
        translate: 'Continuing from an example', multiling: 'Cross-lingual question answering', tooljson: 'Reliably emitting JSON',
        math: 'Multi-step math reasoning', roleplay: 'Holding a persona across a long chat', cot: 'Chain-of-thought reasoning',
      },
      emergedCount: function (n, total) { return n + ' of ' + total + ' have appeared'; },
      thresholdAt: function (b) { return 'around ' + b + 'B'; },
      scaleNow: function (b) { return 'Current scale: ' + (b >= 1000 ? (b / 1000) + 'T' : b + 'B'); },
      costMonthly: function (v) { return '$' + v.toLocaleString('en-US'); },
      costFlagship: 'Flagship model', costSmall: 'Distilled small model',
      costRatio: function (n) { return n + 'x difference'; },
      costGap: function (v) { return '$' + v.toLocaleString('en-US') + ' extra every month'; },
      costBarNote: 'The ratio between the two bars is the cost ratio. It is set by the per-token price and does not shift with scale, which is why dragging the slider changes the figure above rather than the length of the bars.',
      latency: function (ms) { return ms + ' ms'; },
      dailyCalls: function (n) { return n.toLocaleString('en-US') + ' calls per day'; },
      labelCat: 'Cat', labelDog: 'Dog', labelRabbit: 'Rabbit', labelCar: 'Car',
      hardLabel: 'Hard label', softLabel: 'Soft label',
      tempNow: function (t) { return 'T = ' + t; },
      infoLabel: 'Information the student can pick up',
      tempHintLow: 'Very peaked. It essentially just says "cat", which is barely better than a hard label.',
      tempHintMid: 'The distribution has softened. The student now learns that a cat is closer to a dog than to a rabbit.',
      tempHintHigh: 'Too flat. The distinctions are washed out and noise starts to drown the useful signal.',
      pickAtLeast: 'Pick one more model to run a cross-check',
      verdictSame: 'All three were distilled from the same base. When they are wrong, they are wrong in exactly the same way, and cross-checking buys you nothing here.',
      verdictMixed: 'The lineage covers different bases, so this cross-check actually counts.',
      traceBtn: 'Trace lineage',
      lineageName: {
        a: 'Stardust Assistant', b: 'Lingxi Chat', c: 'Clarity QA',
        d: 'Bedrock Chat', e: 'SeaChart Helper', f: 'In-house Model X',
      },
      lineageVendor: {
        a: 'Stardust Tech', b: 'Lingxi Networks', c: 'Clarity Data',
        d: 'Bedrock AI', e: 'SeaChart Cloud', f: 'Internal team',
      },
      pickHint: 'Pick the three products that look least related to each other, then press the button.',
      baseName: { qwen: 'Qwen base', llama: 'Llama base', independent: 'Trained independently' },
    },
    ko: {
      fileOf: function (gb) { return gb + ' GB'; },
      fitYes: '들어감', fitNo: '안 들어감',
      cardLabel: function (gb) { return gb + ' GB 그래픽카드'; },
      paramLabel: function (b) { return b >= 1000 ? (b / 1000) + '조' : b + 'B'; },
      bytesNote: function (n, label) {
        return label + ': 파라미터 하나당 ' + n + ' 바이트';
      },
      tier: {
        open: '1등급: 표준 오픈소스 라이선스',
        conditional: '2등급: 추가 조건 있음',
        restricted: '2등급: 상업적 이용 불가',
        closed: '3등급: API만 제공',
      },
      tierDesc: {
        open: '가중치를 내려받을 수 있고, 상업적 이용도 새 모델 학습도 가능하며 별도의 문턱이 없습니다.',
        conditional: '가중치는 공개했지만 라이선스에 자체 조항을 넣어 상업적 이용이나 재학습을 제한합니다.',
        restricted: '가중치는 받을 수 있지만 상업적 이용은 불가능하고 연구용으로만 쓸 수 있습니다.',
        closed: '가중치는 주지 않고 API만 제공합니다. 성능이 아무리 좋아도 오픈소스는 아닙니다.',
      },
      sampleLabel: '이 등급에 속한 모델: ',
      listSep: ', ',
      qDownload: '가중치를 내려받을 수 있나요?',
      qCommercial: '상업적으로 쓸 수 있나요?',
      qDistill: '그 출력으로 새 모델을 학습시킬 수 있나요?',
      ansYes: '가능', ansNo: '불가', ansLimited: '조건부',
      restart: '다시 판단하기',
      bizName: {
        ads: '광고 판매', cloud: '클라우드와 연산 판매', api: 'API 구독 판매',
        service: '기업 맞춤 서비스 판매', research: '연구로 평판 쌓기', model: '모델 자체를 판매',
      },
      bizLogic: {
        ads: '모델은 본업의 보완재입니다. 보완재가 쌀수록 본업의 가치가 올라가므로, 좋은 모델을 모두가 무료로 쓰기를 바라게 됩니다.',
        cloud: '개발자가 모델을 파인튜닝하고 배포하면 연산 수요가 결국 자사 클라우드로 돌아옵니다. 모델은 무료, 연산은 유료입니다.',
        api: '모델 자체가 판매 상품입니다. 오픈소스로 푸는 것은 상품을 공짜로 주는 셈이라 수익 구조와 정면으로 충돌합니다.',
        service: '모델로 기술적 신뢰를 쌓고, 수익은 온프레미스 배포와 맞춤 계약에서 나옵니다. API로 고객을 묶어 두지 않습니다.',
        research: '가장 관대한 라이선스로 전 세계의 주목을 얻습니다. 릴리스 한 번이 같은 비용의 마케팅보다 큰 평판을 가져옵니다.',
        model: '수익이 모델 라이선스에서 직접 나옵니다. 가중치를 공개하면 돈을 받을 이유가 사라집니다.',
      },
      youLean: '이런 수익 구조라면 여러분은 아마도 ',
      strategy: { open: '오픈소스 쪽일 겁니다', closed: '클로즈드 쪽일 겁니다' },
      bizWho: function (who) { return '대표 사례: ' + who; },
      abilityOn: '창발함', abilityOff: '아직',
      abilityName: {
        translate: '예시를 보고 이어 쓰기', multiling: '교차 언어 질의응답', tooljson: 'JSON 안정적으로 출력',
        math: '다단계 수학 추론', roleplay: '긴 대화에서 캐릭터 유지', cot: '사고 사슬 추론',
      },
      emergedCount: function (n, total) { return total + '개 중 ' + n + '개가 나타남'; },
      thresholdAt: function (b) { return '약 ' + b + 'B'; },
      scaleNow: function (b) { return '현재 규모: ' + (b >= 1000 ? (b / 1000) + '조' : b + 'B'); },
      costMonthly: function (v) { return '$' + v.toLocaleString('en-US'); },
      costFlagship: '플래그십 모델', costSmall: '증류한 소형 모델',
      costRatio: function (n) { return n + '배 차이'; },
      costGap: function (v) { return '매달 $' + v.toLocaleString('en-US') + ' 추가 지출'; },
      costBarNote: '두 막대의 길이 비율이 곧 비용 비율입니다. 이 비율은 단가로 정해지며 규모에 따라 달라지지 않습니다. 그래서 슬라이더를 움직이면 막대 길이가 아니라 위의 금액이 바뀝니다.',
      latency: function (ms) { return ms + ' ms'; },
      dailyCalls: function (n) { return '하루 ' + n.toLocaleString('en-US') + '회 요청'; },
      labelCat: '고양이', labelDog: '개', labelRabbit: '토끼', labelCar: '자동차',
      hardLabel: '하드 레이블', softLabel: '소프트 레이블',
      tempNow: function (t) { return 'T = ' + t; },
      infoLabel: '학생이 얻을 수 있는 정보량',
      tempHintLow: '분포가 매우 뾰족합니다. 사실상 「고양이」라고만 알려주는 셈이라 하드 레이블과 별 차이가 없습니다.',
      tempHintMid: '분포가 부드러워졌습니다. 고양이가 토끼보다 개에 가깝다는 것을 학생이 배우기 시작합니다.',
      tempHintHigh: '너무 평평합니다. 항목 간 차이가 지워지고 노이즈가 유용한 신호를 덮기 시작합니다.',
      pickAtLeast: '교차 검증을 하려면 모델을 하나 더 선택하세요',
      verdictSame: '세 모델 모두 같은 베이스에서 증류되었습니다. 틀릴 때는 똑같이 틀리기 때문에, 여기서 교차 검증은 아무것도 보장해 주지 못합니다.',
      verdictMixed: '계보에 서로 다른 베이스가 섞여 있으므로 이번 교차 검증은 의미가 있습니다.',
      traceBtn: '계보 추적',
      lineageName: {
        a: '스타더스트 어시스턴트', b: '링시 챗', c: '클래리티 QA',
        d: '베드록 챗', e: '씨차트 헬퍼', f: '자체 개발 모델 X',
      },
      lineageVendor: {
        a: '스타더스트 테크', b: '링시 네트웍스', c: '클래리티 데이터',
        d: '베드록 AI', e: '씨차트 클라우드', f: '내부 팀',
      },
      pickHint: '서로 가장 관련 없어 보이는 제품 세 개를 골라 아래 버튼을 눌러 보세요.',
      baseName: { qwen: 'Qwen 베이스', llama: 'Llama 베이스', independent: '독자 학습' },
    },
  };

  /**
   * 背景：同一份逻辑要给中英韩三套页面用，文案必须跟着页面语言走。
   * 设计意图：直接读 html 标签的 lang，页面已经声明过语言，不再另设配置项。
   * 约束：Node 环境没有 document，返回中文包供单测取默认值。
   */
  function dict() {
    if (typeof document === 'undefined') { return I18N.zh; }
    var lang = (document.documentElement.getAttribute('lang') || '').toLowerCase();
    if (lang.indexOf('ko') === 0) { return I18N.ko; }
    if (lang.indexOf('en') === 0) { return I18N.en; }
    return I18N.zh;
  }

  /**
   * 背景：多个 demo 都要在「用户改了输入」之后重画，各页各写一套绑定容易漏
   * 键盘事件，导致滑块只能用鼠标拖。
   * 设计意图：统一在这里绑 input 事件，原生 range 控件本身支持方向键，
   * 只要不自己造滑块就能免费拿到键盘可达性。
   */
  function bindRange(el, fn) {
    if (!el || typeof fn !== 'function') { return; }
    el.addEventListener('input', function () { fn(Number(el.value)); });
    fn(Number(el.value));
  }

  /**
   * 背景：部分学员开了系统的「减少动态效果」，逐帧动画对他们是干扰。
   * 设计意图：页面在播放任何过程动画前问一次，该模式下直接跳到终态。
   */
  function reducedMotion() {
    if (typeof window === 'undefined' || !window.matchMedia) { return false; }
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /**
   * 背景：滑块拖过去数字确实变了，但变化太安静。学员盯着控件本身，
   * 输出区在视线之外悄悄换了个数，等于白改。
   * 设计意图：只在状态真的跳变时给一次短促反馈，稳态下不播任何动画。
   * 加类前先摘类并强制重排，否则连续跳变时同一个 animation 不会重播。
   * 约束：reduced-motion 下直接返回，CSS 那边也关了动画，两处都要挡住，
   * 只关一处会让这类学员白等一个动画时长。
   */
  function fire(el) {
    if (!el || typeof el.classList === 'undefined') { return; }
    if (reducedMotion()) { return; }
    el.classList.remove('fire');
    void el.offsetWidth;
    el.classList.add('fire');
  }

  /**
   * 背景：render 每次输入都会跑一遍，但绝大多数时候结论没变。每次都闪一下
   * 会让整块一直在抖，反而看不出哪一次是真的跨过了阈值。
   * 设计意图：调用方给一个能代表当前状态的值，只有跟上次不同才触发动效。
   * 返回是否真的变了，页面可以据此决定要不要连带播别的反馈。
   * 约束：状态值要能用 !== 比较，对象请先自行序列化。
   */
  function fireOnChange(el, key, store, slot) {
    if (!store) { return false; }
    var name = slot || 'last';
    var changed = store[name] !== key;
    store[name] = key;
    if (changed && store.primed) { fire(el); }
    store.primed = true;
    return changed;
  }

  return {
    fire: fire,
    fireOnChange: fireOnChange,
    BYTES: BYTES,
    PARAM_MIN: PARAM_MIN,
    PARAM_MAX: PARAM_MAX,
    SLIDER_STEPS: SLIDER_STEPS,
    posToParams: posToParams,
    paramsToPos: paramsToPos,
    fileSize: fileSize,
    CARDS: CARDS,
    fitCards: fitCards,
    LICENSE_Q: LICENSE_Q,
    judgeLicense: judgeLicense,
    TIER_SAMPLE: TIER_SAMPLE,
    BIZ: BIZ,
    bizStrategy: bizStrategy,
    ABILITIES: ABILITIES,
    abilitiesAt: abilitiesAt,
    smoothScore: smoothScore,
    emergentScore: emergentScore,
    TIER_COST: TIER_COST,
    monthlyCost: monthlyCost,
    costRatio: costRatio,
    TEACHER_LOGITS: TEACHER_LOGITS,
    softmax: softmax,
    teacherDist: teacherDist,
    infoRichness: infoRichness,
    LINEAGE: LINEAGE,
    lineageOf: lineageOf,
    crossCheckVerdict: crossCheckVerdict,
    I18N: I18N,
    dict: dict,
    bindRange: bindRange,
    reducedMotion: reducedMotion,
  };
});
