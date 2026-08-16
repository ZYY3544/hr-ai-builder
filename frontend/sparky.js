/* Sparky —— 全站悬浮伴学助手（分诊 + 陪走）。
   自建 DOM，四个页面共用一份。历史存 localStorage（无状态后端，登录后可升级服务端存储）。
   纪律：推荐链接只来自后端校验过的 refs 事件——正文永远不含链接，编不出死链。 */
(function () {
  'use strict';
  var API = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:8001' : 'https://hr-ai-builder-api.onrender.com';
  var HKEY = 'sparky_hist', MAX_H = 40;
  var PAGE = (location.pathname.split('/').pop() || 'index.html').replace('.html', '');


  /* ---------------- 像素小猫（逐像素移植自 meansights PixelCat.tsx，SMIL 动画）---------------- */
  var CAT_C = { P: '#CA7C5E', D: '#a8604a', W: '#FFFFFF', E: '#3d2c24' };
  var CAT_STATIC = [[0,2,'P'],[0,9,'P'],[1,1,'P'],[1,2,'D'],[1,3,'P'],[1,8,'P'],[1,9,'D'],[1,10,'P'],
    [2,1,'P'],[2,2,'P'],[2,3,'P'],[2,4,'P'],[2,5,'P'],[2,6,'P'],[2,7,'P'],[2,8,'P'],[2,9,'P'],[2,10,'P'],
    [3,0,'P'],[3,1,'P'],[3,2,'P'],[3,3,'P'],[3,4,'P'],[3,5,'P'],[3,6,'P'],[3,7,'P'],[3,8,'P'],[3,9,'P'],[3,10,'P'],[3,11,'P'],
    [4,0,'P'],[4,1,'P'],[4,4,'P'],[4,5,'P'],[4,6,'P'],[4,7,'P'],[4,10,'P'],[4,11,'P'],
    [5,0,'P'],[5,1,'P'],[5,4,'P'],[5,5,'P'],[5,6,'P'],[5,7,'P'],[5,10,'P'],[5,11,'P'],
    [6,0,'P'],[6,1,'P'],[6,2,'P'],[6,3,'P'],[6,4,'P'],[6,5,'P'],[6,6,'P'],[6,7,'P'],[6,8,'P'],[6,9,'P'],[6,10,'P'],[6,11,'P'],
    [7,0,'P'],[7,1,'P'],[7,2,'P'],[7,3,'P'],[7,4,'P'],[7,5,'P'],[7,6,'P'],[7,7,'P'],[7,8,'P'],[7,9,'P'],[7,10,'P'],[7,11,'P'],
    [8,0,'P'],[8,1,'P'],[8,2,'P'],[8,3,'P'],[8,4,'P'],[8,5,'P'],[8,6,'P'],[8,7,'P'],[8,8,'P'],[8,9,'P'],[8,10,'P'],[8,11,'P'],
    [9,1,'P'],[9,2,'P'],[9,3,'P'],[9,4,'P'],[9,5,'P'],[9,6,'P'],[9,7,'P'],[9,8,'P'],[9,9,'P'],[9,10,'P'],
    [10,2,'P'],[10,3,'P'],[10,4,'P'],[10,5,'P'],[10,6,'P'],[10,7,'P'],[10,8,'P'],[10,9,'P']];
  var CAT_EYES = [[4,2],[4,3],[5,2],[5,3],[4,8],[4,9],[5,8],[5,9]];
  var CAT_LEG_L = [[11,2,'P'],[11,3,'P'],[12,2,'P'],[12,3,'P'],[13,2,'D'],[13,3,'D']];
  var CAT_LEG_R = [[11,8,'P'],[11,9,'P'],[12,8,'P'],[12,9,'P'],[13,8,'D'],[13,9,'D']];

  function catSVG(size, mode) {
    var cell = size / 14, offX = (size - 12 * cell) / 2, offY = 0;
    var lift = Math.max(1, Math.round(cell * 0.9));
    var anim = mode !== 'still';
    var ph = { blink: -(Math.random() * 6).toFixed(2), dart: -(Math.random() * 9).toFixed(2),
               walk: -(Math.random() * 0.44).toFixed(2) };
    function rect(r, c, k) {
      return '<rect x="' + (c * cell + offX) + '" y="' + (r * cell + offY) + '" width="' + cell +
             '" height="' + cell + '" fill="' + CAT_C[k] + '"/>';
    }
    var px = CAT_STATIC.map(function (p) { return rect(p[0], p[1], p[2]); }).join('') +
             CAT_EYES.map(function (p) { return rect(p[0], p[1], 'W'); }).join('');
    var bo = '1;1;0;0;1;1', bc = '0;0;1;1;0;0', bt = '0;0.94;0.95;0.98;0.99;1';
    var blink = anim ? '<animate attributeName="opacity" values="' + bo + '" keyTimes="' + bt +
      '" dur="6s" repeatCount="indefinite" begin="' + ph.blink + 's"/>' : '';
    var dart = anim ? '<animateTransform attributeName="transform" type="translate" values="0,0; ' +
      (-cell) + ',0; 0,0; 0,' + (-cell) + '; 0,0; ' + (-cell) + ',' + (-cell) +
      '; 0,0" keyTimes="0;0.16;0.3;0.46;0.6;0.78;1" dur="9s" repeatCount="indefinite" calcMode="discrete" begin="' +
      ph.dart + 's"/>' : '';
    function pupil(x) {
      return '<rect x="' + (x * cell + offX) + '" y="' + (5 * cell + offY) + '" width="' + cell +
             '" height="' + cell + '" fill="' + CAT_C.E + '">' + blink + '</rect>';
    }
    var lineH = Math.max(1, Math.round(cell * .5)), lineY = 5 * cell + offY - lineH / 2;
    function closed(x) {
      return anim ? '<rect x="' + (x * cell + offX) + '" y="' + lineY + '" width="' + (2 * cell) +
        '" height="' + lineH + '" fill="' + CAT_C.E + '" opacity="0">' +
        '<animate attributeName="opacity" values="' + bc + '" keyTimes="' + bt +
        '" dur="6s" repeatCount="indefinite" begin="' + ph.blink + 's"/></rect>' : '';
    }
    function leg(pxs, first) {
      var a = mode === 'walk' ? '<animateTransform attributeName="transform" type="translate" values="' +
        (first ? '0,' + (-lift) + ';0,0' : '0,0;0,' + (-lift)) +
        '" keyTimes="0;0.5" dur="0.44s" repeatCount="indefinite" calcMode="discrete" begin="' + ph.walk + 's"/>' : '';
      return '<g>' + a + pxs.map(function (p) { return rect(p[0], p[1], p[2]); }).join('') + '</g>';
    }
    return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size +
      '" style="overflow:visible">' + px +
      '<g>' + dart + pupil(3) + pupil(9) + '</g>' + closed(2) + closed(8) +
      leg(CAT_LEG_L, true) + leg(CAT_LEG_R, false) + '</svg>';
  }

  /* ---------------- DOM ---------------- */
  var css = [
    '#spk-ball{position:fixed;right:22px;bottom:20px;width:64px;height:64px;background:none;border:none;',
    ' cursor:pointer;z-index:9998;display:flex;align-items:flex-end;justify-content:center;padding:0;',
    ' transition:transform .15s;filter:drop-shadow(0 5px 10px rgba(15,23,42,.28))}',
    '#spk-ball:hover{transform:scale(1.1)}',
    '#spk-panel{position:fixed;right:0;top:0;bottom:0;width:390px;max-width:100vw;background:#fff;z-index:9999;',
    ' box-shadow:-8px 0 32px rgba(15,23,42,.14);display:flex;flex-direction:column;',
    ' transform:translateX(105%);transition:transform .22s ease}',
    '#spk-panel.on{transform:none}',
    '#spk-head{padding:14px 18px;border-bottom:1px solid #E2E8F0;display:flex;align-items:center;gap:10px}',
    '#spk-head .t{font-weight:700;color:#0F172A;font-size:15px}',
    '#spk-head .s{font-size:11.5px;color:#94A3B8}',
    '#spk-x{margin-left:auto;border:none;background:none;font-size:20px;color:#94A3B8;cursor:pointer;padding:4px 8px}',
    '#spk-log{flex:1;overflow-y:auto;padding:16px;background:#F8FAFC}',
    '.spk-m{max-width:86%;margin-bottom:10px;padding:10px 13px;border-radius:12px;font-size:13.5px;line-height:1.8;',
    ' white-space:pre-wrap;word-break:break-word}',
    '.spk-m.u{margin-left:auto;background:linear-gradient(135deg,#00A88A,#0891B2);color:#fff;border-bottom-right-radius:4px}',
    '.spk-m.a{background:#fff;border:1px solid #E2E8F0;color:#0F172A;border-bottom-left-radius:4px}',
    '.spk-m.a b{color:#00795F}',
    '.spk-m.err{background:rgba(217,119,6,.08);border:1px solid rgba(217,119,6,.3);color:#92400E}',
    '.spk-refs{display:flex;flex-direction:column;gap:6px;margin:2px 0 12px;max-width:86%}',
    '.spk-refs a{display:flex;align-items:center;gap:8px;font-size:12.5px;text-decoration:none;color:#0F172A;',
    ' background:#fff;border:1.5px solid rgba(0,168,138,.4);border-radius:10px;padding:8px 12px}',
    '.spk-refs a:hover{border-color:#00A88A;background:#E8FBF6}',
    '.spk-refs a i{font-style:normal;font-size:10.5px;color:#94A3B8;flex:0 0 auto}',
    '.spk-refs a em{font-style:normal;margin-left:auto;font-size:11px;color:#94A3B8}',
    '.spk-chips{display:flex;flex-wrap:wrap;gap:7px;margin:4px 0 12px}',
    '.spk-chips button{border:1px solid #E2E8F0;background:#fff;border-radius:18px;padding:6px 13px;',
    ' font-size:12.5px;color:#475569;cursor:pointer}',
    '.spk-chips button:hover{border-color:#00A88A;color:#00795F}',
    '#spk-inp{display:flex;gap:8px;padding:12px 14px;border-top:1px solid #E2E8F0;background:#fff}',
    '#spk-inp textarea{flex:1;border:1.5px solid #E2E8F0;border-radius:10px;padding:9px 12px;font-size:13.5px;',
    ' font-family:inherit;resize:none;height:40px;line-height:1.6;outline:none}',
    '#spk-inp textarea:focus{border-color:#00A88A}',
    '#spk-send{border:none;border-radius:10px;background:linear-gradient(135deg,#00A88A,#0891B2);color:#fff;',
    ' padding:0 16px;font-size:13.5px;cursor:pointer;font-weight:600}',
    '#spk-send:disabled{opacity:.45;cursor:default}',
    '.spk-typing{color:#94A3B8;font-size:12px;padding:2px 0 10px}',
    '#spk-bubble{position:fixed;right:24px;bottom:92px;max-width:240px;background:#fff;border:1px solid #E2E8F0;',
    ' border-radius:14px;border-bottom-right-radius:4px;padding:11px 30px 11px 14px;font-size:13px;line-height:1.7;',
    ' color:#0F172A;box-shadow:0 8px 28px rgba(15,23,42,.16);z-index:9998;cursor:pointer;',
    ' opacity:0;transform:translateY(8px);transition:.25s;pointer-events:none}',
    '#spk-bubble.on{opacity:1;transform:none;pointer-events:auto}',
    '#spk-bubble b{color:#00795F}',
    '#spk-bubble .bx{position:absolute;top:4px;right:7px;color:#94A3B8;font-size:15px;padding:2px 5px;cursor:pointer}',
    '@media(max-width:480px){#spk-panel{width:100vw}}',
    '@media print{#spk-ball,#spk-panel{display:none}}'
  ].join('\n');

  var style = document.createElement('style'); style.textContent = css;
  document.head.appendChild(style);

  var ball = document.createElement('button');
  ball.id = 'spk-ball'; ball.title = 'Sparky · 伴学助手';
  ball.innerHTML = catSVG(52, 'idle');
  // hover 时小猫原地踏步（与 meansights 同款交互）
  ball.onmouseenter = function () { ball.innerHTML = catSVG(52, 'walk'); };
  ball.onmouseleave = function () { ball.innerHTML = catSVG(52, 'idle'); };
  var panel = document.createElement('div');
  panel.id = 'spk-panel';
  panel.innerHTML =
    '<div id="spk-head"><span id="spk-avatar" style="display:flex">' + catSVG(30, 'idle') + '</span>' +
    '<div><div class="t">Sparky</div><div class="s">帮你找到该读哪儿 · 不替课本讲课</div></div>' +
    '<button id="spk-x">×</button></div>' +
    '<div id="spk-log"></div>' +
    '<div id="spk-inp"><textarea rows="1" placeholder="说说你想拿 AI 干什么…"></textarea>' +
    '<button id="spk-send">发送</button></div>';
  var bub = document.createElement('div'); bub.id = 'spk-bubble';
  document.body.appendChild(ball); document.body.appendChild(panel); document.body.appendChild(bub);

  var log = panel.querySelector('#spk-log'),
      ta = panel.querySelector('textarea'),
      send = panel.querySelector('#spk-send');

  /* ---------------- 状态 ---------------- */
  var hist = [];
  try { hist = JSON.parse(localStorage.getItem(HKEY) || '[]'); } catch (e) {}
  var busy = false, enabled = null;   // enabled: null=未知 true/false=health 结果

  function save() { try { localStorage.setItem(HKEY, JSON.stringify(hist.slice(-MAX_H))); } catch (e) {} }
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function md(s) { return esc(s).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>'); }
  function scroll() { log.scrollTop = log.scrollHeight; }

  function bubble(role, text, cls) {
    var d = document.createElement('div');
    d.className = 'spk-m ' + (cls || (role === 'user' ? 'u' : 'a'));
    d.innerHTML = md(text);
    log.appendChild(d); scroll(); return d;
  }

  function refsBlock(items) {
    if (!items || !items.length) return;
    var w = document.createElement('div'); w.className = 'spk-refs';
    w.innerHTML = items.map(function (r) {
      return '<a href="learn.html#' + encodeURIComponent(r.file) + '"><i>' + esc(r.part || '') +
             '</i>' + esc(r.title) + '<em>' + (r.min || 0) + '′</em></a>';
    }).join('');
    log.appendChild(w); scroll();
  }

  /* ---------------- 行为采集（全部本地，只在点开气泡时才把摘要发给后端） ---------------- */
  var DBG = localStorage.getItem('spk_debug') === '1';
  var TK = DBG ? 0.02 : 1;                       // debug 模式阈值缩到 2%
  var LMAP = {};                                  // file -> {title,min,topic}
  try { if (typeof CO !== 'undefined') CO.parts.forEach(function (p) {
    p.topics.forEach(function (t) { t.lessons.forEach(function (l) {
      LMAP[l.file] = { title: l.title, min: l.min || 0, topic: t.title,
                       sibs: t.lessons.map(function (x) { return x.file; }) };
    }); });
  }); } catch (e) {}

  var trail = [];                                 // [{f, t0, d(秒)}]
  var hidT0 = null;
  function trailNow() { return trail.length ? trail[trail.length - 1] : null; }
  function trailSettle() {
    var c = trailNow();
    if (c) c.d = Math.round((Date.now() - c.t0) / 1000 - (c.pause || 0));
  }
  function trailPush(f) {
    trailSettle();
    trail.push({ f: f, t0: Date.now(), pause: 0 });
    if (trail.length > 20) trail.shift();
  }
  function trailSummary() {
    trailSettle();
    return trail.slice(-5).map(function (x) {
      var t = (LMAP[x.f] || {}).title || x.f;
      return '《' + t + '》停留' + (x.d >= 60 ? Math.round(x.d / 60) + '分' : (x.d || 0) + '秒');
    }).join(' → ') || '（无浏览记录）';
  }
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { hidT0 = Date.now(); }
    else if (hidT0) { var c = trailNow(); if (c) c.pause = (c.pause || 0) + (Date.now() - hidT0) / 1000; hidT0 = null; }
  });
  if (PAGE === 'learn') {
    var f0 = decodeURIComponent(location.hash.slice(1) || '');
    if (f0) trailPush(f0);
    window.addEventListener('hashchange', function () {
      var f = decodeURIComponent(location.hash.slice(1) || '');
      if (f && (!trailNow() || trailNow().f !== f)) { trailPush(f); trigSkim(); }
    });
  }
  // 心跳：给"回访"触发器留下上次足迹
  setInterval(function () {
    try { localStorage.setItem('spk_last', JSON.stringify({
      t: Date.now(), lesson: PAGE === 'learn' ? (trailNow() || {}).f : null })); } catch (e) {}
  }, 10000);

  /* ---------------- 触发引擎：宁可错过，不可打扰 ---------------- */
  function fired() { return +(sessionStorage.getItem('spk_fired') || 0); }
  function canFire(id, coolH) {
    if ((document.hidden && !DBG) || panel.classList.contains('on') || busy) return false;
    if (+(sessionStorage.getItem('spk_x') || 0) >= 2) return false;          // 连按两次×→全程闭嘴
    if (fired() >= 2) return false;                                          // 每次访问最多2泡
    var last = +(sessionStorage.getItem('spk_bt') || 0);
    if (Date.now() - last < 5 * 60000 * TK) return false;                    // 两泡间隔≥5分钟
    var cool = {}; try { cool = JSON.parse(localStorage.getItem('spk_cool') || '{}'); } catch (e) {}
    if (cool[id] && Date.now() - cool[id] < coolH * 3600000 * TK) return false;
    return true;
  }
  var bubTimer = null, bubTrig = null;
  function fire(id, coolH, text, note) {
    if (!canFire(id, coolH)) return;
    var cool = {}; try { cool = JSON.parse(localStorage.getItem('spk_cool') || '{}'); } catch (e) {}
    cool[id] = Date.now();
    try { localStorage.setItem('spk_cool', JSON.stringify(cool)); } catch (e) {}
    sessionStorage.setItem('spk_fired', fired() + 1);
    sessionStorage.setItem('spk_bt', Date.now());
    bubTrig = { id: id, note: note };
    bub.innerHTML = md(text) + '<span class="bx">×</span>';
    bub.classList.add('on');
    bub.querySelector('.bx').onclick = function (e) {
      e.stopPropagation(); hideBub();
      sessionStorage.setItem('spk_x', +(sessionStorage.getItem('spk_x') || 0) + 1);
    };
    clearTimeout(bubTimer);
    bubTimer = setTimeout(hideBub, 45000);                                   // 45秒没人理自己缩回
  }
  function hideBub() { bub.classList.remove('on'); clearTimeout(bubTimer); }
  bub.onclick = function () {
    var tg = bubTrig; hideBub();
    openPanel();
    if (tg) autoAsk(tg.id, tg.note);
  };

  // ① 卡住：同一节停留超过声明时长3倍（至少5分钟）
  if (PAGE === 'learn') setInterval(function () {
    var c = trailNow(); if (!c || (document.hidden && !DBG)) return;
    var min = (LMAP[c.f] || {}).min || 3;
    var th = Math.max(300, min * 60 * 3) * TK;
    var dwell = (Date.now() - c.t0) / 1000 - (c.pause || 0);
    if (dwell > th) fire('stuck', 6, '这一节停了挺久——**卡住了？**',
      '用户在《' + ((LMAP[c.f] || {}).title || c.f) + '》停留了 ' + Math.round(dwell / 60) + ' 分钟（声明阅读时长 ' + min + ' 分钟），可能卡住了');
  }, 20000 * TK);

  // ② 乱翻：5分钟内翻≥5节、每节<40秒
  function trigSkim() {
    var recent = trail.slice(-6, -1);
    if (recent.length < 5) return;
    var fast = recent.every(function (x) { return (x.d || 0) < Math.max(40 * TK, 4); });
    var span = (Date.now() - recent[0].t0) / 1000 < Math.max(300 * TK, 20);
    if (fast && span) fire('skim', 12, '翻了好几节都没停下来。**在找什么？**',
      '用户快速翻过多节都没细读：' + trailSummary() + '——像是在找某个具体的东西没找到');
  }

  // ③ 回访：隔天回来、上次有在读的节
  try {
    var lastRec = JSON.parse(localStorage.getItem('spk_last') || 'null');
    if (lastRec && lastRec.lesson && Date.now() - lastRec.t > 20 * 3600000 * TK) {
      var lt = (LMAP[lastRec.lesson] || {}).title || lastRec.lesson;
      setTimeout(function () {
        fire('comeback', 20, '回来了。上次停在**《' + lt + '》**。',
          '用户隔了至少一天回来了，上次离开时停在《' + lt + '》');
      }, 4000);
    }
  } catch (e) {}

  // ④ 读完一组：某主题的节全部学完
  var doneN0 = null;
  setInterval(function () {
    var d = []; try { d = JSON.parse(localStorage.getItem('hab_done') || '[]'); } catch (e) { return; }
    if (doneN0 === null) { doneN0 = d.length; return; }
    if (d.length <= doneN0) { doneN0 = d.length; return; }
    var newest = d[d.length - 1]; doneN0 = d.length;
    var m = LMAP[newest]; if (!m || !m.sibs) return;
    var all = m.sibs.every(function (f) { return d.indexOf(f) >= 0; });
    if (all) fire('topicdone', 1, '「**' + m.topic + '**」这一组读完了。',
      '用户刚读完《' + m.title + '》，至此「' + m.topic + '」主题下的所有节都学完了。给出紧接着最值得读的下一组（按课程顺序），并肯定一句');
  }, 2500);

  // ⑤ 新客迷茫：首页90秒没点任何课
  if (PAGE === 'index') (function () {
    var d = []; try { d = JSON.parse(localStorage.getItem('hab_done') || '[]'); } catch (e) {}
    if (d.length || localStorage.getItem('spk_seen_idle')) return;
    var clicked = false;
    document.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a[href*="learn.html"]')) clicked = true;
    }, true);
    setTimeout(function () {
      if (!clicked) {
        localStorage.setItem('spk_seen_idle', '1');
        fire('idlefirst', 999, '**不知道从哪开始？**说说你想拿 AI 干什么。',
          '新访客在首页停了一分半，还没点进任何课程——可能不知道从哪开始');
      }
    }, 90000 * TK);
  })();

  // ⑥ 下载练习表
  document.addEventListener('click', function (e) {
    var a2 = e.target.closest && e.target.closest('a[href*="2026-08"]');
    if (!a2 || localStorage.getItem('spk_seen_ds')) return;
    localStorage.setItem('spk_seen_ds', '1');
    setTimeout(function () {
      fire('dataset', 999, '表下好了。**做完记得对答案卡**，卡住了找我。',
        '用户刚下载了三张练习表（花名册/考勤/业绩，埋了8类脏数据）。提醒对答案卡，说明可以带着具体的坑来问');
    }, 2500);
  }, true);

  /* ---------------- 上下文 ---------------- */
  function ctx() {
    var done = [];
    try { done = JSON.parse(localStorage.getItem('hab_done') || '[]'); } catch (e) {}
    var lesson = null;
    if (PAGE === 'learn' && location.hash) {
      lesson = decodeURIComponent(location.hash.slice(1));
    }
    return { page: PAGE, lesson: lesson, done: done };
  }

  /* ---------------- 共享流式请求 ---------------- */
  function streamChat(payloadCtx, onDone) {
    var typing = document.createElement('div');
    typing.className = 'spk-typing'; typing.textContent = 'Sparky 正在想…';
    log.appendChild(typing); scroll();
    var av = panel.querySelector('#spk-avatar');
    if (av) av.innerHTML = catSVG(30, 'walk');
    var reply = '', replyEl = null, refs = [];
    busy = true; send.disabled = true;

    fetch(API + '/api/sparky/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: hist.slice(-12).map(function (m) { return { role: m.role, content: m.content }; }),
        ctx: payloadCtx
      })
    }).then(function (r) {
      if (!r.ok) {
        return r.json().then(function (j) {
          var e = new Error((j && j.detail) || '');
          e.human = !!(j && j.detail);
          throw e;
        }, function () { throw new Error(''); });
      }
      var rd = r.body.getReader(), dec = new TextDecoder(), buf = '';
      function pump() {
        return rd.read().then(function (x) {
          if (x.done) return;
          buf += dec.decode(x.value, { stream: true });
          var lines = buf.split('\n\n'); buf = lines.pop();
          lines.forEach(function (ln) {
            if (ln.slice(0, 6) !== 'data: ') return;
            var ev; try { ev = JSON.parse(ln.slice(6)); } catch (e) { return; }
            if (ev.t === 'delta') {
              if (typing.parentNode) typing.remove();
              reply += ev.text;
              if (!replyEl) replyEl = bubble('assistant', '');
              replyEl.innerHTML = md(reply); scroll();
            } else if (ev.t === 'refs') {
              refs = ev.items || []; refsBlock(refs);
            } else if (ev.t === 'err') {
              if (typing.parentNode) typing.remove();
              bubble('assistant', ev.msg, 'err');
            }
          });
          return pump();
        });
      }
      return pump();
    }).then(function () {
      if (typing.parentNode) typing.remove();
      if (reply) { hist.push({ role: 'assistant', content: reply, refs: refs }); save(); }
    }).catch(function (e) {
      if (typing.parentNode) typing.remove();
      bubble('assistant', e.human && e.message ? e.message
        : '我这会儿连不上了。你可以直接翻目录，或者过会儿再来。', 'err');
    }).then(function () {
      busy = false; send.disabled = false;
      var av2 = panel.querySelector('#spk-avatar');
      if (av2) av2.innerHTML = catSVG(30, 'idle');
      if (onDone) onDone();
    });
  }

  /* ---------------- 主动开口（点开气泡后才请求，才花钱） ---------------- */
  function autoAsk(trigId, note) {
    if (busy || enabled === false) return;
    var c = ctx();
    c.trigger = trigId; c.trigger_note = note; c.behavior = trailSummary();
    streamChat(c, function () { ta.focus(); });
  }

  /* ---------------- 开场（脚本化，零 LLM 成本） ---------------- */
  function opener() {
    var done = ctx().done.length;
    var t = done > 0
      ? '又见面了。你已经读完 ' + done + ' 节了。\n\n卡在哪儿了，还是想找下一步读什么？'
      : '你好，我是 Sparky。\n\n**你想拿 AI 干点什么？**说得越具体越好——「每个月要合三张表做人力报表」就比「想学 AI」有用得多。\n\n也可以直接问某个概念、某节课。';
    bubble('assistant', t);
    var chips = document.createElement('div'); chips.className = 'spk-chips';
    var qs = done > 0
      ? ['我卡住了', '接下来读什么', '练习表对不上答案']
      : ['帮我挑从哪儿开始', '我每个月要做人力月报', '下个月要见 AI 供应商', '我想搭一个自己的 agent'];
    qs.forEach(function (q) {
      var b = document.createElement('button'); b.textContent = q;
      b.onclick = function () { ta.value = q; submit(); };
      chips.appendChild(b);
    });
    log.appendChild(chips); scroll();
  }

  function restore() {
    if (!hist.length) { opener(); return; }
    hist.slice(-14).forEach(function (m) {
      bubble(m.role, m.content);
      if (m.refs) refsBlock(m.refs);
    });
  }

  /* ---------------- 发送 ---------------- */
  function submit() {
    var q = ta.value.trim();
    if (!q || busy) return;
    if (enabled === false) {
      bubble('assistant', 'Sparky 还在接线中——课都能正常读，先去翻目录吧。', 'err');
      return;
    }
    ta.value = '';
    bubble('user', q);
    hist.push({ role: 'user', content: q }); save();
    var c = ctx(); c.behavior = trailSummary();
    streamChat(c);
  }

  send.onclick = submit;
  ta.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  });

  /* ---------------- 开合 ---------------- */
  var opened = false;
  function openPanel() {
    hideBub();
    panel.classList.add('on'); ball.style.display = 'none';
    if (!opened) {
      opened = true; restore();
      fetch(API + '/api/sparky/health').then(function (r) { return r.json(); })
        .then(function (j) {
          enabled = !!j.enabled;
          if (!enabled) bubble('assistant', 'Sparky 还在接线中（模型没接好）——先去翻目录，课都能正常读。', 'err');
        }).catch(function () { enabled = null; });
    }
    ta.focus();
  }
  ball.onclick = openPanel;
  panel.querySelector('#spk-x').onclick = function () {
    panel.classList.remove('on'); ball.style.display = 'flex';
  };
})();
