/* Sparky —— 全站悬浮伴学助手（分诊 + 陪走）。
   自建 DOM，四个页面共用一份。历史存 localStorage（无状态后端，登录后可升级服务端存储）。
   纪律：推荐链接只来自后端校验过的 refs 事件——正文永远不含链接，编不出死链。 */
(function () {
  'use strict';
  var API = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:8001' : 'https://hr-ai-builder-api.onrender.com';
  var HKEY = 'sparky_hist', MAX_H = 40;
  var PAGE = (location.pathname.split('/').pop() || 'index.html').replace('.html', '');

  /* ---------------- DOM ---------------- */
  var css = [
    '#spk-ball{position:fixed;right:22px;bottom:22px;width:54px;height:54px;border-radius:50%;',
    ' background:linear-gradient(135deg,#00A88A,#0891B2);color:#fff;font-size:24px;border:none;cursor:pointer;',
    ' box-shadow:0 6px 20px rgba(8,145,178,.35);z-index:9998;display:flex;align-items:center;justify-content:center;',
    ' transition:transform .15s}',
    '#spk-ball:hover{transform:scale(1.08)}',
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
  ball.innerHTML = '<img src="sparky-cat.png" alt="Sparky" style="width:38px;height:38px;border-radius:8px">';
  var panel = document.createElement('div');
  panel.id = 'spk-panel';
  panel.innerHTML =
    '<div id="spk-head"><img src="sparky-cat.png" alt="" style="width:28px;height:28px;border-radius:7px">' +
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
          throw new Error((j && j.detail) || '连不上');
        }, function () { throw new Error('连不上'); });
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
      bubble('assistant', String(e.message || '我这会儿连不上了。你可以直接翻目录，或者过会儿再来。'), 'err');
    }).then(function () { busy = false; send.disabled = false; ta.focus(); });
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
