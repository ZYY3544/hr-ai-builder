/* ═══════════════════════════════════════════════════════════
   oss-calc.js —— 显存换算与机型匹配（oss-8 / PlayGround 共用）

   背景：oss-8 要回答「我这台机器能跑多大的模型」。这个判断本身有明确公式，
   但散落在各处的说法口径不一（有的按参数量 ×2 估，有的忘了算 KV Cache），
   学员照着算会得到跑不起来的结论。
   设计意图：把换算规则、设备参数、模型清单集中在一个文件里，浏览器与 Node
   共用同一份实现，单测直接验证这份代码本身，避免测试与页面各算各的。
   约束：所有系数取自 luoxiaoshan.cn/llm 的公开对照表，改动系数必须同步更新
   tests/test_oss_calc.py 的预期值与页面上的公式说明，三者不允许漂移。
   ═══════════════════════════════════════════════════════════ */

(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  if (root) { root.OSSCalc = api; }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  /* 精度系数：显存(GB) ≈ 参数量(B) × 系数。
     系数里已经含约 30% 到 50% 的运行时开销（主要是 KV Cache），
     所以不要在外部再乘一次开销，否则会高估到没有机器跑得动。 */
  var PRECISION = {
    fp32: { label: 'FP32', factor: 4.0 },
    fp16: { label: 'FP16', factor: 2.6 },
    int8: { label: 'INT8', factor: 1.3 },
    int4: { label: 'INT4', factor: 0.65 },
  };

  /* ── oss-8：量化为什么会掉分 ──
     背景：页面原先只写「位数越少损失越大」，读者记住了结论但不知道损失从哪来，
     也就无法判断自己的任务该选哪一档。
     设计意图：量化的本质是把连续的权重四舍五入到有限个档位，这件事可以精确算，
     所以这里只做真实的数学，不编造「掉几分」这类跑分。
     约束：INT 走对称均匀量化，档位数与步长都是定义直接推出来的；FP16 是浮点，
     档位不均匀（越靠近 0 越密），必须按指数分段算，不能当成均匀格子，否则
     会把「浮点在小数值上精度更高」这个关键差异抹掉。 */
  var QUANT = {
    fp16: { label: 'FP16', bits: 16, uniform: false },
    int8: { label: 'INT8', bits: 8, uniform: true },
    int4: { label: 'INT4', bits: 4, uniform: true },
  };

  /**
   * 一个数值在该精度下能落到的档位间隔。
   * INT：整个范围被均分成 2^bits - 1 段，步长处处相同。
   * FP16：10 位尾数，同一个二进制指数区间内均分 1024 份，所以步长随数值大小变化。
   */
  function quantStep(precision, absMax, value) {
    var q = QUANT[precision];
    if (!q) { throw new Error('未知精度: ' + precision); }
    if (!(absMax > 0)) { throw new Error('取值范围必须为正数: ' + absMax); }
    if (q.uniform) {
      return (2 * absMax) / (Math.pow(2, q.bits) - 1);
    }
    var a = Math.abs(value || 0);
    /* 非正规数以下直接用 FP16 能表示的最小间隔，避免 log2(0) */
    if (a < Math.pow(2, -14)) { return Math.pow(2, -24); }
    return Math.pow(2, Math.floor(Math.log2(a)) - 10);
  }

  /** 把一个权重值四舍五入到该精度最近的档位上。 */
  function quantize(value, precision, absMax) {
    var step = quantStep(precision, absMax, value);
    var v = Math.max(-absMax, Math.min(absMax, value));
    return Math.round(v / step) * step;
  }

  /**
   * 一组权重在该精度下的舍入误差。
   * 返回的 relMax 是「最大误差占取值范围的比例」，这是页面上最能说明问题的数：
   * INT4 为 6.67%、INT8 为 0.39%，相差 17 倍（255/15，即两者档位数之比）。
   */
  function quantStats(values, precision, absMax) {
    var errs = values.map(function (v) {
      return Math.abs(quantize(v, precision, absMax) - v);
    });
    var sum = errs.reduce(function (a, b) { return a + b; }, 0);
    return {
      avg: sum / errs.length,
      max: Math.max.apply(null, errs),
      /* 均匀量化下最大舍入误差恒为半个步长，与具体取到哪些样本无关 */
      relMax: quantStep(precision, absMax, absMax) / 2 / absMax,
    };
  }

  /**
   * 背景：读者真正要判断的是「这点误差会不会影响我的任务」。
   * 设计意图：把误差换算成「一条 n 步推理链全程不出错的概率」。单步翻车概率
   * 很低也架不住连乘，这正是页面上「日常问答没感觉、长链推理掉分明显」的由来。
   * 约束：p 是每步出错概率，这里假设各步独立。真实推理链前后相关，独立假设会
   * 低估风险，页面必须写明这是示意而非实测。
   */
  function chainSurvival(p, steps) {
    if (p < 0 || p > 1) { throw new Error('单步出错概率必须在 0 与 1 之间: ' + p); }
    return Math.pow(1 - p, steps);
  }

  /* 界面文案：本模块同时被中英韩三套页面加载，渲染出来的文字必须跟着页面语言走。
     早期版本把中文写死在渲染函数里，导致 .en / .ko 页面上的计算器显示中文。
     新增语言时在这里补一份即可，渲染逻辑不需要改。 */
  var I18N = {
    zh: {
      tier: { edge: '端侧', light: '轻量', main: '主流', high: '高配', moe: 'MoE', flagship: '旗舰' },
      state: { ok: '可以跑', tight: '勉强，留意上下文', no: '跑不动' },
      avail: '可用于载入模型：',
      formula: function (f, label) {
        return '显存 ≈ 参数量(B) × ' + f + '（' + label + '，已含 KV Cache 开销）';
      },
      vramNote: function (gb) { return '独立显存 ' + gb + ' GB'; },
      memNote: function (gb, pct) {
        return '统一内存 ' + gb + ' GB，按可分配给 GPU 的约 ' + pct + '% 计';
      },
      optVram: function (gb) { return gb + ' GB 显存'; },
      optMem: function (gb) { return gb + ' GB 统一内存'; },
      wrap: function (s) { return '（' + s + '）'; },
      moeTag: function (total, active) {
        return '总参 ' + total + 'B / 激活 ' + active + 'B';
      },
      need: function (gb) { return '需 ' + gb + ' GB'; },
      deviceMissing: '设备数据缺失，请重新选择',
      copy: '复制',
      copied: '已复制',
      copyManual: '请手动选中复制',
      recWhy: function (need, avail) {
        return '这台机器可用 ' + avail + ' GB，它需要 ' + need + ' GB，留得出余量。';
      },
      recNone: '这台机器带不动官方库里已上架的型号',
      recNoneWhy: '先换更低的精度档试试，或者按上一节的结论挑一个更小的尺寸。',
      recCmdTip: '复制这条，装好 Ollama 后直接敲',
      recUse: { chat: '日常问答', code: '写代码 / 数学' },
      recQuant: function (q) { return '想更稳可以试 ' + q + ' 档，拉之前先到 library 的 tags 页确认这个尺寸有没有这一档。'; },
      recTop: '这已经是官方库里<b>能下到本机的最大 Qwen 尺寸</b>了。再往上的 397B 只提供云端版本（<code>qwen3.5:397b-cloud</code>），跑在别人的机器上，不落到你这里。',
      recVer: '注意它是 <b>3.5</b> 那一代，不是最新的 3.6。3.6 目前只出到 35B，<b>版本号更新不等于全尺寸跟进</b>，挑本地模型要看尺寸，不能只看版本号。',
      qLevels: function (n) { return n.toLocaleString('zh-CN') + ' 档'; },
      qLevelsNote: { fp16: '浮点，越靠近 0 档位越密', int8: '整个范围均分', int4: '整个范围均分' },
      qOrig: '原始值', qAfter: '存进去变成', qErr: '差了',
      qZero: '被抹成 0',
      qRelMax: function (pct) { return '最大误差 ' + pct + '%'; },
      qVsInt8: function (x) { return '是 INT8 的 ' + x + ' 倍'; },
      qHintFp16: '这是模型发布时的原始格式，后面两档都拿它当基准。误差小到看不出来。',
      qHintInt8: '误差还在千分之四以内。日常任务上基本察觉不到差别，显存够就选它。',
      qHintInt4: '误差跳到 6.7%，而且<b>绝对值小的权重会被直接抹成 0</b>——那个参数在这份文件里就不存在了。',
      qFlipTitle: '一次预测里会发生什么',
      qFlipHint: '模型每写一个词，都是在若干候选里挑概率最高的那个。下面这组候选前两名咬得很紧。',
      qFlipKeep: '排序没变，这一步不受影响',
      qFlipTurn: '<b>排序翻了</b>，这一步会写出另一个词',
      qChainHint: '单看一步，出问题的机会不大。但推理是一步接一步往下走的：',
      qChainSteps: function (n) { return n + ' 步'; },
      qChainLive: function (pct) { return '全程不出错的概率 ' + pct + '%'; },
      qChainNote: function (n) {
        return n + ' 步里只要有一步选错，后面就顺着错的往下走。这也是为什么长链条推理对精度更敏感，而问个天气怎么样感觉不出区别。';
      },
      recLM: function (n) { return 'LM Studio 用户：在模型库里搜 <b>' + n + '</b>，界面会直接标出哪些量化版本你带得动。'; },
    },
    en: {
      tier: { edge: 'On-device', light: 'Light', main: 'Mainstream', high: 'High-end', moe: 'MoE', flagship: 'Flagship' },
      state: { ok: 'Runs fine', tight: 'Tight, watch context length', no: 'Too large' },
      avail: 'Available for loading a model: ',
      formula: function (f, label) {
        return 'VRAM ≈ params(B) × ' + f + ' (' + label + ', KV Cache included)';
      },
      vramNote: function (gb) { return 'Dedicated VRAM ' + gb + ' GB'; },
      memNote: function (gb, pct) {
        return 'Unified memory ' + gb + ' GB, about ' + pct + '% assumed available to the GPU';
      },
      optVram: function (gb) { return gb + ' GB VRAM'; },
      optMem: function (gb) { return gb + ' GB unified memory'; },
      wrap: function (s) { return ' (' + s + ')'; },
      moeTag: function (total, active) {
        return total + 'B total / ' + active + 'B active';
      },
      need: function (gb) { return 'Needs ' + gb + ' GB'; },
      deviceMissing: 'Device data missing, please select again',
      copy: 'Copy',
      copied: 'Copied',
      copyManual: 'Please select and copy manually',
      recWhy: function (need, avail) {
        return 'This machine has ' + avail + ' GB available and this model needs ' + need + ' GB, which leaves real headroom.';
      },
      recNone: 'This machine cannot run anything currently in the official library',
      recNoneWhy: 'Try a lower precision first, or pick a smaller size based on the previous lesson.',
      recCmdTip: 'Copy this and run it once Ollama is installed',
      recUse: { chat: 'Everyday chat', code: 'Code / math' },
      recQuant: function (q) { return 'For more quality headroom, try the ' + q + ' build, but check the tags page in the library first to confirm this size offers it.'; },
      recTop: 'This is the <b>largest Qwen you can pull down to your own machine</b> from the official library. Anything bigger, such as the 397B, is cloud-only (<code>qwen3.5:397b-cloud</code>) and runs on someone else\'s hardware, never on yours.',
      recVer: 'Note that it comes from the <b>3.5</b> generation, not the newer 3.6. The 3.6 line currently tops out at 35B, so a <b>higher version number does not mean every size followed</b>. Pick a local model by size, not by version.',
      qLevels: function (n) { return n.toLocaleString('en-US') + ' levels'; },
      qLevelsNote: { fp16: 'Floating point: levels cluster near zero', int8: 'Range split evenly', int4: 'Range split evenly' },
      qOrig: 'Original', qAfter: 'Stored as', qErr: 'Off by',
      qZero: 'flattened to 0',
      qRelMax: function (pct) { return 'Max error ' + pct + '%'; },
      qVsInt8: function (x) { return x + '\u00d7 that of INT8'; },
      qHintFp16: 'This is the format models ship in, and the baseline the other two are measured against. The error is too small to notice.',
      qHintInt8: 'Error stays under 0.4%. On everyday tasks you will not feel a difference, so pick this whenever the memory allows.',
      qHintInt4: 'Error jumps to 6.7%, and <b>weights with small magnitudes get flattened to exactly 0</b> — that parameter no longer exists in this file.',
      qFlipTitle: 'What this does to one prediction',
      qFlipHint: 'Every word the model writes is the highest-scoring candidate of several. In the set below the top two are neck and neck.',
      qFlipKeep: 'Order held. This step is unaffected',
      qFlipTurn: '<b>The order flipped.</b> This step now writes a different word',
      qChainHint: 'One step alone is unlikely to go wrong. But reasoning runs step after step:',
      qChainSteps: function (n) { return n + (n === 1 ? ' step' : ' steps'); },
      qChainLive: function (pct) { return pct + '% chance of getting through cleanly'; },
      qChainNote: function (n) {
        var where = n === 1 ? 'in that one step' : 'anywhere in those ' + n + ' steps';
        return 'A single wrong pick ' + where + ' and everything after it follows the wrong path. That is why long reasoning chains are sensitive to precision while asking about the weather is not.';
      },
      recLM: function (n) { return 'LM Studio users: search for <b>' + n + '</b> in the model library and the app will mark which quantized builds your machine can handle.'; },
    },
    ko: {
      tier: { edge: '온디바이스', light: '경량', main: '주력', high: '고사양', moe: 'MoE', flagship: '플래그십' },
      state: { ok: '실행 가능', tight: '빠듯함, 컨텍스트 주의', no: '실행 불가' },
      avail: '모델 로딩에 쓸 수 있는 용량: ',
      formula: function (f, label) {
        return 'VRAM ≈ 파라미터 수(B) × ' + f + ' (' + label + ', KV Cache 포함)';
      },
      vramNote: function (gb) { return '전용 VRAM ' + gb + ' GB'; },
      memNote: function (gb, pct) {
        return '통합 메모리 ' + gb + ' GB, GPU에 할당 가능한 약 ' + pct + '% 기준';
      },
      optVram: function (gb) { return gb + ' GB VRAM'; },
      optMem: function (gb) { return gb + ' GB 통합 메모리'; },
      wrap: function (s) { return ' (' + s + ')'; },
      moeTag: function (total, active) {
        return '총 ' + total + 'B / 활성 ' + active + 'B';
      },
      need: function (gb) { return gb + ' GB 필요'; },
      deviceMissing: '기기 데이터가 없습니다. 다시 선택해 주세요',
      copy: '복사',
      copied: '복사됨',
      copyManual: '직접 선택해 복사해 주세요',
      recWhy: function (need, avail) {
        return '이 기기는 ' + avail + ' GB를 쓸 수 있고 이 모델은 ' + need + ' GB가 필요하므로 여유가 남습니다.';
      },
      recNone: '이 기기로는 공식 라이브러리에 올라온 모델을 돌리기 어렵습니다',
      recNoneWhy: '먼저 더 낮은 정밀도를 시도하거나, 앞 강의의 결론에 따라 더 작은 크기를 고르세요.',
      recCmdTip: 'Ollama 설치 후 이 명령을 그대로 복사해 실행하세요',
      recUse: { chat: '일상 대화', code: '코딩 / 수학' },
      recQuant: function (q) { return '품질에 여유를 더 두고 싶다면 ' + q + ' 빌드를 시도해 보세요. 다만 받기 전에 library의 tags 페이지에서 해당 크기에 그 등급이 있는지 확인해야 합니다.'; },
      recTop: '공식 라이브러리에서 <b>내 컴퓨터로 내려받을 수 있는 가장 큰 Qwen</b>입니다. 이보다 큰 397B는 클라우드 전용(<code>qwen3.5:397b-cloud</code>)이라 남의 장비에서 돌 뿐, 내 컴퓨터로는 오지 않습니다.',
      recVer: '이 모델이 최신 3.6이 아니라 <b>3.5</b> 세대라는 점에 유의하세요. 3.6은 현재 35B까지만 나와 있습니다. <b>버전이 올라갔다고 모든 크기가 따라 나오지는 않습니다.</b> 로컬 모델은 버전이 아니라 크기를 보고 골라야 합니다.',
      qLevels: function (n) { return n.toLocaleString('ko-KR') + '단계'; },
      qLevelsNote: { fp16: '부동소수점, 0에 가까울수록 촘촘', int8: '전체 범위를 균등 분할', int4: '전체 범위를 균등 분할' },
      qOrig: '원래 값', qAfter: '저장되면', qErr: '차이',
      qZero: '0으로 뭉개짐',
      qRelMax: function (pct) { return '최대 오차 ' + pct + '%'; },
      qVsInt8: function (x) { return 'INT8의 ' + x + '배'; },
      qHintFp16: '모델이 배포될 때의 원본 형식이며, 나머지 두 등급의 기준선입니다. 오차는 알아챌 수 없을 만큼 작습니다.',
      qHintInt8: '오차가 0.4% 이내입니다. 일상적인 작업에서는 차이를 느끼기 어려우니 메모리가 허락하면 이 등급을 고르세요.',
      qHintInt4: '오차가 6.7%로 뛰고, <b>절댓값이 작은 가중치는 아예 0으로 뭉개집니다.</b> 그 파라미터는 이 파일 안에 더 이상 존재하지 않습니다.',
      qFlipTitle: '예측 한 번에서 벌어지는 일',
      qFlipHint: '모델은 단어를 하나 쓸 때마다 여러 후보 중 확률이 가장 높은 것을 고릅니다. 아래 후보들은 1위와 2위가 아슬아슬합니다.',
      qFlipKeep: '순서가 그대로입니다. 이 단계는 영향을 받지 않습니다',
      qFlipTurn: '<b>순서가 뒤집혔습니다.</b> 이 단계에서 다른 단어가 나옵니다',
      qChainHint: '한 단계만 보면 잘못될 가능성은 크지 않습니다. 하지만 추론은 한 단계씩 이어집니다:',
      qChainSteps: function (n) { return n + '단계'; },
      qChainLive: function (pct) { return '전 과정을 무사히 통과할 확률 ' + pct + '%'; },
      qChainNote: function (n) {
        return n + '단계 중 한 번만 잘못 골라도 그 뒤는 틀린 쪽을 따라 흘러갑니다. 긴 추론이 정밀도에 민감하고, 날씨를 묻는 정도로는 차이를 못 느끼는 이유입니다.';
      },
      recLM: function (n) { return 'LM Studio 사용자: 모델 라이브러리에서 <b>' + n + '</b>를 검색하면 어떤 양자화 빌드를 돌릴 수 있는지 앱이 표시해 줍니다.'; },
    },
  };

  /**
   * 背景：同一份计算模块被三种语言的页面加载，需要知道当前该用哪套文案。
   * 设计意图：直接读 html 标签的 lang，页面已经声明过语言，不再另设配置项，
   * 避免出现 lang 与文案不一致的状态。
   * 约束：未知语言回退到中文，保证任何情况下都有可显示的文案而不是 undefined。
   */
  function dict() {
    if (typeof document === 'undefined') { return I18N.zh; }
    var lang = (document.documentElement.getAttribute('lang') || '').toLowerCase();
    if (lang.indexOf('ko') === 0) { return I18N.ko; }
    if (lang.indexOf('en') === 0) { return I18N.en; }
    return I18N.zh;
  }

  /* NVIDIA 显卡：显存独占，标称容量基本可全部用于载入模型。 */
  var NVIDIA = [
    { id: 'rtx5090d', name: 'RTX 5090 D', vram: 32 },
    { id: 'rtx4090',  name: 'RTX 4090',   vram: 24 },
    { id: 'rtx5080',  name: 'RTX 5080',   vram: 16 },
    { id: 'rtx4080',  name: 'RTX 4080',   vram: 16 },
    { id: 'rtx5070',  name: 'RTX 5070',   vram: 12 },
    { id: 'rtx3060',  name: 'RTX 3060',   vram: 12 },
    { id: 'rtx3080',  name: 'RTX 3080',   vram: 10 },
    { id: 'rtx4060',  name: 'RTX 4060',   vram: 8 },
    { id: 'rtx2080',  name: 'RTX 2080',   vram: 8 },
    { id: 'gtx1080',  name: 'GTX 1080',   vram: 8 },
    { id: 'rtx2060',  name: 'RTX 2060',   vram: 6 },
    { id: 'gtx1060',  name: 'GTX 1060',   vram: 6 },
  ];

  /* Apple Silicon：统一内存由 CPU 与 GPU 共享，系统不允许全部划给 GPU。
     这里按可用比例折算，避免直接拿 128GB 去比对导致高估。 */
  var APPLE_GPU_RATIO = 0.75;

  var APPLE = [
    { id: 'm2ultra192', name: 'M2 Ultra · 192GB', mem: 192 },
    { id: 'm4max128',   name: 'M4 Max · 128GB',   mem: 128 },
    { id: 'm1ultra128', name: 'M1 Ultra · 128GB', mem: 128 },
    { id: 'm3max96',    name: 'M3 Max · 96GB',    mem: 96 },
    { id: 'm2max96',    name: 'M2 Max · 96GB',    mem: 96 },
    { id: 'm4max64',    name: 'M4 Max · 64GB',    mem: 64 },
    { id: 'm4pro64',    name: 'M4 Pro · 64GB',    mem: 64 },
    { id: 'm3max64',    name: 'M3 Max · 64GB',    mem: 64 },
    { id: 'm1max64',    name: 'M1 Max · 64GB',    mem: 64 },
    { id: 'm4max48',    name: 'M4 Max · 48GB',    mem: 48 },
    { id: 'm3max48',    name: 'M3 Max · 48GB',    mem: 48 },
    { id: 'm4max36',    name: 'M4 Max · 36GB',    mem: 36 },
    { id: 'm3pro36',    name: 'M3 Pro · 36GB',    mem: 36 },
    { id: 'm4_32',      name: 'M4 · 32GB',        mem: 32 },
    { id: 'm2max32',    name: 'M2 Max · 32GB',    mem: 32 },
    { id: 'm2pro32',    name: 'M2 Pro · 32GB',    mem: 32 },
    { id: 'm1max32',    name: 'M1 Max · 32GB',    mem: 32 },
    { id: 'm4_24',      name: 'M4 · 24GB',        mem: 24 },
    { id: 'm4pro24',    name: 'M4 Pro · 24GB',    mem: 24 },
    { id: 'm3_24',      name: 'M3 · 24GB',        mem: 24 },
    { id: 'm3pro18',    name: 'M3 Pro · 18GB',    mem: 18 },
    { id: 'm4_16',      name: 'M4 · 16GB',        mem: 16 },
    { id: 'm3_16',      name: 'M3 · 16GB',        mem: 16 },
    { id: 'm2pro16',    name: 'M2 Pro · 16GB',    mem: 16 },
    { id: 'm1_16',      name: 'M1 · 16GB',        mem: 16 },
    { id: 'm4_8',       name: 'M4 · 8GB',         mem: 8 },
    { id: 'm3_8',       name: 'M3 · 8GB',         mem: 8 },
    { id: 'm1_8',       name: 'M1 · 8GB',         mem: 8 },
  ];

  /* 候选模型：除最后一行外，全部为已经放出权重、可以真正下载到本机的型号。
     MoE 模型的 params 记总参数量（决定显存），active 记激活参数量（决定速度），
     两者不能混用，这也是页面上要讲清楚的一个点。 */
  var MODELS = [
    { name: 'Qwen3-0.6B',        params: 0.6,   tier: 'edge' },
    { name: 'Qwen3-1.7B',        params: 1.7,   tier: 'edge' },
    { name: 'Qwen3-4B',          params: 4,     tier: 'light' },
    { name: 'Qwen3-8B',          params: 8,     tier: 'main' },
    { name: 'Qwen3-14B',         params: 14,    tier: 'main' },
    { name: 'Qwen3.6-27B',       params: 27,    tier: 'high' },
    { name: 'Qwen3-32B',         params: 32,    tier: 'high' },
    { name: 'Qwen3-30B-A3B',     params: 30,    active: 3,  tier: 'moe' },
    { name: 'Qwen3.6-35B-A3B',   params: 35,    active: 3,  tier: 'moe' },
    /* 大内存 Mac 的意义全在这一行。128 GB 以上的统一内存刚好吃得下它，
       而同价位的独显机器塞不进去。没有这一行，192 GB 的用户会停在 32B，
       看不出自己那台机器到底买到了什么。 */
    { name: 'Qwen3.5-122B-A10B', params: 122,   active: 10, tier: 'moe' },
    { name: 'Qwen3-235B-A22B',   params: 235,   active: 22, tier: 'moe' },
    /* 这一行在任何消费级设备上都判定为跑不动，是故意的。oss-3 提到这个模型时
       预告了读者会在这里撞到天花板，亲眼看到 1560 GB 这个数字比读一句「很大」有用。
       删掉它会让 oss-3 的那句交叉引用变成空指。 */
    { name: 'Qwen3.8-Max',       params: 2400,  active: 95, tier: 'flagship' },
  ];

  /**
   * 背景：页面上每一行模型都要显示「需要多少显存」，这是全页最核心的一个数。
   * 设计意图：只做参数量乘系数，把 KV Cache 开销留在系数里，让公式在页面上
   * 一行就能写清楚，学员能拿计算器自己复算。
   * 约束：MoE 模型必须传总参数量，传激活参数量会严重低估显存需求。
   */
  function estimateVram(paramsB, precision) {
    var p = PRECISION[precision];
    if (!p) { throw new Error('未知精度: ' + precision); }
    if (typeof paramsB !== 'number' || !(paramsB > 0)) {
      throw new Error('参数量必须为正数: ' + paramsB);
    }
    return Math.round(paramsB * p.factor * 10) / 10;
  }

  /**
   * 背景：Apple 的统一内存和 NVIDIA 的独立显存不是一回事，直接拿标称容量
   * 比大小会让 Mac 用户以为自己能跑远超实际的模型。
   * 设计意图：在这里统一折算成「可用于载入模型的显存」，页面与单测都只认
   * 这个函数的输出，不各自去乘比例。
   * 约束：APPLE_GPU_RATIO 是经验值，macOS 可通过 iogpu.wired_limit_max 调整，
   * 页面上需要注明这一点，不能让读者以为是硬上限。
   */
  function availableVram(device) {
    if (device.vram != null) { return device.vram; }
    return Math.round(device.mem * APPLE_GPU_RATIO * 10) / 10;
  }

  /**
   * 背景：算出需求和可用之后还要给一个结论，学员真正想要的是「能不能跑」。
   * 设计意图：留出 15% 余量作为 ok 与 tight 的分界。显存刚好卡满时模型能载入，
   * 但上下文一长就会 OOM，直接判定「可以跑」会误导人。
   * 约束：阈值调整需同步更新 tests/test_oss_calc.py 的边界用例。
   */
  var HEADROOM = 0.85;

  function judge(needGb, availGb) {
    if (needGb <= availGb * HEADROOM) { return 'ok'; }
    if (needGb <= availGb) { return 'tight'; }
    return 'no';
  }

  /**
   * 背景：页面需要一次性拿到某台机器在某个精度下对全部候选模型的判定结果。
   * 设计意图：把遍历与排序收在这里，渲染层只负责把结果画出来，便于单测覆盖。
   * 约束：返回顺序与 MODELS 一致，页面依赖这个顺序来体现从小到大的递进。
   */
  function evaluate(device, precision) {
    var avail = availableVram(device);
    return MODELS.map(function (m) {
      var need = estimateVram(m.params, precision);
      return {
        name: m.name,
        tier: m.tier,
        params: m.params,
        active: m.active || null,
        need: need,
        avail: avail,
        ratio: Math.min(need / avail, 1),
        state: judge(need, avail),
      };
    });
  }

  /* ── oss-9：从机型推出该敲的命令 ──
     背景：oss-8 算出「你能跑 14B」，学员到了 oss-9 还是不知道该敲哪一条。
     设计意图：把机型直接映射到一条可以复制就用的命令，把两节课接上。
     约束：这里只登记**确实存在于 ollama library 的标签**。给出一条拉不下来的
     命令比不给更糟，学员会以为是自己装错了。下表逐条核对于 2026-08-07，来源为
     ollama.com/library/<name>/tags。未上架的型号一律返回 null。
     注意 qwen3.6 目前只有 27b 与 35b-a3b 两档，本地能跑的最大尺寸反而在 3.5 那一代
     （122b-a10b，81 GB）。版本号更新不等于全尺寸跟进，这一点页面上要说明。 */
  var OLLAMA_TAG = {
    'Qwen3-0.6B': 'qwen3:0.6b',
    'Qwen3-1.7B': 'qwen3:1.7b',
    'Qwen3-4B': 'qwen3:4b',
    'Qwen3-8B': 'qwen3:8b',
    'Qwen3-14B': 'qwen3:14b',
    'Qwen3-32B': 'qwen3:32b',
    'Qwen3-30B-A3B': 'qwen3:30b-a3b',
    'Qwen3.6-27B': 'qwen3.6:27b',
    'Qwen3.6-35B-A3B': 'qwen3.6:35b-a3b',
    'Qwen3.5-122B-A10B': 'qwen3.5:122b-a10b',
  };

  function ollamaTag(name) {
    return OLLAMA_TAG[name] || null;
  }

  /* 本地能拉到的最大尺寸。再往上（qwen3.5:397b-cloud）只跑在云端，不落到本机，
     所以不算进本地天花板。页面用它来判断该不该提示「你已经到顶了」。 */
  function largestLocal() {
    var best = null;
    MODELS.forEach(function (m) {
      if (!ollamaTag(m.name)) { return; }
      if (!best || m.params > best.params) { best = m; }
    });
    return best ? best.name : null;
  }

  /**
   * 背景：学员真正想问的是「那我该装哪个」，不是「我能装哪些」。
   * 设计意图：在判定为 ok 的模型里取最大的一个。刻意排除 tight，因为
   * tight 的含义是「装得下但上下文一长就 OOM」，作为第一次上手的推荐
   * 会让人以为本地部署很不稳。
   * 约束：只推荐有 ollama 标签的型号，否则给不出可复制的命令。
   */
  function recommend(device, precision) {
    var rows = evaluate(device, precision);
    var best = null;
    rows.forEach(function (r) {
      if (r.state !== 'ok') { return; }
      if (!ollamaTag(r.name)) { return; }
      if (!best || r.params > best.params) { best = r; }
    });
    if (!best) { return null; }
    return {
      name: best.name,
      tag: ollamaTag(best.name),
      params: best.params,
      need: best.need,
      avail: best.avail,
      /* 推到顶和推不上去是两种情况，页面要说不一样的话，所以在这里就分好 */
      isTop: best.name === largestLocal(),
    };
  }

  function findDevice(id) {
    var all = NVIDIA.concat(APPLE);
    for (var i = 0; i < all.length; i++) {
      if (all[i].id === id) { return all[i]; }
    }
    return null;
  }

  /* ── 以下为浏览器渲染部分，Node 环境不会执行 ── */

  /**
   * 背景：PlayGround 与 oss-8 正式页要用同一套渲染，避免调好的样式上线后不一致。
   * 设计意图：接收一组已有的 DOM 节点而非自己创建结构，让两个页面可以各自决定
   * 布局，只共享行为与计算。
   * 约束：调用方必须保证六个节点都存在，缺任意一个直接返回，不做静默降级渲染。
   */
  function mount(opts) {
    if (typeof document === 'undefined') { return null; }
    if (!opts || !opts.platformEl || !opts.deviceEl || !opts.precEl
        || !opts.readoutEl || !opts.resultsEl) {
      console.error('[OSSCalc] mount 缺少必要节点，已跳过初始化', opts);
      return null;
    }

    var state = { platform: 'nvidia', deviceId: NVIDIA[0].id, precision: 'int4' };
    var t = dict();

    function deviceList() {
      return state.platform === 'nvidia' ? NVIDIA : APPLE;
    }

    function fillDevices() {
      var list = deviceList();
      opts.deviceEl.innerHTML = list.map(function (d) {
        var cap = d.vram != null ? t.optVram(d.vram) : t.optMem(d.mem);
        return '<option value="' + d.id + '">' + d.name + t.wrap(cap) + '</option>';
      }).join('');
      state.deviceId = list[0].id;
      opts.deviceEl.value = state.deviceId;
    }

    function render() {
      var device = findDevice(state.deviceId);
      if (!device) {
        console.error('[OSSCalc] 找不到设备', state.deviceId);
        opts.resultsEl.innerHTML = '<div class="oc-row is-no"><div class="ocr-name">'
          + t.deviceMissing + '</div></div>';
        return;
      }
      var avail = availableVram(device);
      var rows = evaluate(device, state.precision);
      var p = PRECISION[state.precision];

      var memNote = device.vram != null
        ? t.vramNote(device.vram)
        : t.memNote(device.mem, Math.round(APPLE_GPU_RATIO * 100));

      opts.readoutEl.innerHTML =
        '<span>' + t.avail + '</span><b>' + avail + ' GB</b>' +
        '<span class="ocr-formula">' + t.formula(p.factor, p.label) + '</span>' +
        '<span class="ocr-formula">' + memNote + '</span>';

      opts.resultsEl.innerHTML = rows.map(function (r) {
        var moe = r.active
          ? '<span class="ocr-tag">' + t.moeTag(r.params, r.active) + '</span>'
          : '';
        return '' +
          '<div class="oc-row is-' + r.state + '">' +
            '<div class="ocr-name">' + r.name
              + '<span class="ocr-tag">' + (t.tier[r.tier] || r.tier) + '</span>' + moe + '</div>' +
            '<div class="ocr-need">' + t.need(r.need) + '</div>' +
            '<div class="ocr-bar"><i style="width:' + Math.round(r.ratio * 100) + '%"></i></div>' +
            '<div class="ocr-state">' + t.state[r.state] + '</div>' +
          '</div>';
      }).join('');
    }

    opts.platformEl.addEventListener('click', function (e) {
      var btn = e.target.closest('.oc-seg-btn');
      if (!btn) { return; }
      state.platform = btn.dataset.platform;
      opts.platformEl.querySelectorAll('.oc-seg-btn').forEach(function (b) {
        b.classList.toggle('is-on', b === btn);
      });
      fillDevices();
      render();
    });

    opts.precEl.addEventListener('click', function (e) {
      var btn = e.target.closest('.oc-seg-btn');
      if (!btn) { return; }
      state.precision = btn.dataset.prec;
      opts.precEl.querySelectorAll('.oc-seg-btn').forEach(function (b) {
        b.classList.toggle('is-on', b === btn);
      });
      render();
    });

    opts.deviceEl.addEventListener('change', function () {
      state.deviceId = opts.deviceEl.value;
      render();
    });

    fillDevices();
    render();
    return { render: render, state: state };
  }

  /**
   * 背景：oss-9 的命令行块需要一键复制，移动端与非安全上下文下
   * navigator.clipboard 不可用。
   * 设计意图：优先用标准 API，失败时回退到临时 textarea，两条路都失败时
   * 给用户可见提示，不静默失败。
   * 约束：需绑定在用户手势事件里，否则浏览器会拒绝写入剪贴板。
   */
  function bindCopy(scope) {
    if (typeof document === 'undefined') { return; }
    var t = dict();
    (scope || document).querySelectorAll('.ocmd-copy').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var text = btn.dataset.copy || '';
        var done = function () {
          var old = btn.innerHTML;
          btn.classList.add('is-done');
          btn.innerHTML = t.copied;
          setTimeout(function () {
            btn.classList.remove('is-done');
            btn.innerHTML = old;
          }, 1600);
        };
        var fallback = function (err) {
          console.warn('[OSSCalc] 剪贴板 API 不可用，改用 textarea 回退', err);
          try {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            done();
          } catch (e2) {
            console.error('[OSSCalc] 复制失败', e2);
            btn.innerHTML = t.copyManual;
            setTimeout(function () { btn.innerHTML = t.copy; }, 2200);
          }
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done).catch(fallback);
        } else {
          fallback(new Error('navigator.clipboard 不存在'));
        }
      });
    });
  }

  return {
    PRECISION: PRECISION,
    I18N: I18N,
    dict: dict,
    NVIDIA: NVIDIA,
    APPLE: APPLE,
    APPLE_GPU_RATIO: APPLE_GPU_RATIO,
    MODELS: MODELS,
    HEADROOM: HEADROOM,
    estimateVram: estimateVram,
    availableVram: availableVram,
    judge: judge,
    evaluate: evaluate,
    findDevice: findDevice,
    OLLAMA_TAG: OLLAMA_TAG,
    largestLocal: largestLocal,
    ollamaTag: ollamaTag,
    recommend: recommend,
    QUANT: QUANT,
    quantStep: quantStep,
    quantize: quantize,
    quantStats: quantStats,
    chainSurvival: chainSurvival,
    mount: mount,
    bindCopy: bindCopy,
  };
});
