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
  document.body.appendChild(ball); document.body.appendChild(panel);

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
    ta.value = ''; busy = true; send.disabled = true;
    bubble('user', q);
    hist.push({ role: 'user', content: q }); save();

    var typing = document.createElement('div');
    typing.className = 'spk-typing'; typing.textContent = 'Sparky 正在想…';
    log.appendChild(typing); scroll();
    var av = panel.querySelector('#spk-avatar');
    if (av) av.innerHTML = catSVG(30, 'walk');

    var reply = '', replyEl = null, refs = [];

    fetch(API + '/api/sparky/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: hist.slice(-12).map(function (m) { return { role: m.role, content: m.content }; }),
        ctx: ctx()
      })
    }).then(function (r) {
      if (!r.ok) {
        return r.json().then(function (j) {
          var e = new Error((j && j.detail) || '');
          e.human = !!(j && j.detail);   // 服务端 detail 本身就是人话，才可直出
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
      busy = false; send.disabled = false; ta.focus();
      var av2 = panel.querySelector('#spk-avatar');
      if (av2) av2.innerHTML = catSVG(30, 'idle');
    });
  }

  send.onclick = submit;
  ta.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  });

  /* ---------------- 开合 ---------------- */
  var opened = false;
  ball.onclick = function () {
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
  };
  panel.querySelector('#spk-x').onclick = function () {
    panel.classList.remove('on'); ball.style.display = 'flex';
  };
})();
