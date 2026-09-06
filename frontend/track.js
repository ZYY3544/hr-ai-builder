/**
 * track.js —— 行为埋点
 *
 * 为什么要：没有它，你只知道「有人来过」，不知道「从哪进、看了几节、在哪一节流失」。
 * 而这个站的全部目的是漏斗，漏斗看不见就等于没做。
 *
 * 设计：
 *   visitor_id  localStorage 持久，标识匿名访客（不含任何个人信息）
 *   session_id  30 分钟无操作即新开一个会话
 *   停留时长    用 visibilitychange + beforeunload 上报，切后台不计时
 *   iframe      课件在 learn.html 的 iframe 里，必须单独上报，否则阅读行为全丢
 *
 * ⚠️ 命名禁区（同类站点用真实数据换来的教训）：
 *   文件名 / 路径 / DOM id / localStorage 键里都不得出现
 *   ad / ads / banner / promo / sponsor / popup —— 会被 EasyList 规则整条拦掉。
 *   实测同一天：命名带 -ad 的脚本被请求 141 次，同页正常命名的脚本 23,039 次。
 */
(function () {
  'use strict';
  if (window.__HAB_TRACK__) return;
  window.__HAB_TRACK__ = true;

  var API = (location.hostname === 'localhost' || location.protocol === 'file:')
    ? 'http://localhost:8001' : 'https://hr-ai-builder-api.onrender.com';
  var KV = 'hab_vid', KS = 'hab_sid', KT = 'hab_sid_at';
  var SESSION_MS = 30 * 60 * 1000;

  function rnd() { return Math.random().toString(36).slice(2, 10) + Date.now().toString(36); }
  function ls(k, v) {
    try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); return v; }
    catch (e) { return null; }
  }

  var vid = ls(KV) || ls(KV, rnd());
  var last = parseInt(ls(KT) || '0', 10);
  var sid = (Date.now() - last < SESSION_MS && ls(KS)) ? ls(KS) : ls(KS, rnd());
  ls(KT, String(Date.now()));

  // 页面身份：课件页取文件名，其余取路径
  var path = location.pathname.replace(/\/+$/, '') || '/';
  var page = /\/slides\//.test(path) ? path.split('/').pop() : (path.split('/').pop() || 'index.html');
  var kind = /\/slides\//.test(path) ? 'lesson'
           : /learn\.html/.test(path) ? 'reader'
           : 'page';
  var inFrame = window.top !== window.self;

  var t0 = Date.now(), visible = document.visibilityState !== 'hidden', accum = 0, sent = false;

  function activeMs() {
    return accum + (visible ? Date.now() - t0 : 0);
  }
  function send(ev, extra) {
    var body = {
      visitor_id: vid, session_id: sid, event: ev, page: page, kind: kind,
      in_frame: inFrame, ref: document.referrer || null,
      dwell_ms: ev === 'view' ? 0 : activeMs(),
      ts: new Date().toISOString(),
    };
    if (extra) for (var k in extra) body[k] = extra[k];
    /* 不用 sendBeacon：application/json 的 Blob 跨域发不出去（CORS 不放行、还静默失败），
       leave 事件曾整条丢在这上面。fetch keepalive 是它的正牌替代，卸载页面时同样能送达。 */
    fetch(API + '/api/t', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body), keepalive: true,
    }).catch(function () {});
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') { accum += Date.now() - t0; visible = false; }
    else { t0 = Date.now(); visible = true; }
  });
  function leave() { if (sent) return; sent = true; ls(KT, String(Date.now())); send('leave'); }
  window.addEventListener('pagehide', leave);
  window.addEventListener('beforeunload', leave);

  send('view');
  window.habTrack = function (ev, extra) { send(ev, extra); };   // 供业务事件调用

  /* ── 头像账户菜单（2026-08-26 成长地图 tab 下线后，退出登录的新家）──
     点登录后的头像(.uava)弹一个小菜单：昵称 + 退出登录。放这里因为 track.js
     是全站 9 个页面唯一都加载的脚本——各页头像代码不用再各改一份。 */
  document.addEventListener('click', function (e) {
    var menu = document.getElementById('hab-acct-menu');
    var av = e.target.closest && e.target.closest('#loginBtn');
    /* 判据必须是「有没有 token」，不能看 .uava 类——那个类未登录时也在元素上，
       用它当判据会让退出后再点头像仍弹账户菜单，把登录入口彻底挡死（2026-08-26 用户实测抓到）。
       未登录时这里必须原样放行，让各页自己的 onclick=openLogin 正常触发。 */
    var authed = false;
    try { authed = !!localStorage.getItem('hab_token'); } catch (err) {}
    if (!av || !authed) { if (menu && !menu.contains(e.target)) menu.remove(); return; }
    e.preventDefault(); e.stopPropagation();
    if (menu) { menu.remove(); return; }
    var u = {};
    try { u = JSON.parse(localStorage.getItem('hab_user') || '{}') || {}; } catch (err) {}
    var m = document.createElement('div');
    m.id = 'hab-acct-menu';
    m.style.cssText = 'position:fixed;z-index:9999;background:#fff;border:1px solid #E5E7EB;' +
      'border-radius:12px;box-shadow:0 10px 28px rgba(15,23,42,.14);padding:6px;min-width:150px;' +
      'font-size:13px;color:#0F172A';
    var r = av.getBoundingClientRect();
    m.style.top = (r.bottom + 8) + 'px';
    m.style.right = Math.max(8, window.innerWidth - r.right) + 'px';
    m.innerHTML = '<div style="padding:8px 12px;color:#64748B;font-size:12px;border-bottom:1px solid #F1F5F9;' +
        'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + ((u.nickname || '已登录')) + '</div>' +
      '<button id="hab-logout" style="display:block;width:100%;text-align:left;font:inherit;padding:9px 12px;' +
        'border:none;background:none;color:#DC2626;cursor:pointer;border-radius:8px">退出登录</button>';
    document.body.appendChild(m);
    m.querySelector('#hab-logout').onclick = function () {
      try { localStorage.removeItem('hab_token'); localStorage.removeItem('hab_user'); } catch (err) {}
      location.reload();
    };
  }, true);
  /* ── 手机端站内导航（2026-09-06）──
     ≤960px 时各页顶栏的 .glinks 直接 display:none，之前没有任何替代入口：
     手机（也就是微信里点开的绝大多数人）到不了岗位机会 / 实战任务 / 职业辅导 / 关于。
     这里全站统一注入一个菜单按钮 + 顶栏下方的下拉面板；链接是从各页自己的 .glinks
     克隆出来的，所以 tab 增删、当前页高亮(.cur) 都只需改各页那一份，不会漂移。
     z-index 放在账户菜单(9999)之下、页面内容之上。 */
  function mountMobileNav() {
    var links = document.querySelector('.glinks');
    var right = document.querySelector('.gright');
    if (!links || !right || document.getElementById('hab-mnav-btn')) return;
    var hdr = right.closest ? (right.closest('header') || right.closest('.top')) : null;

    var css = document.createElement('style');
    css.textContent =
      '#hab-mnav-btn{display:none;align-items:center;justify-content:center;width:36px;height:36px;border:0;' +
        'background:none;border-radius:9px;color:var(--muted,#64748B);cursor:pointer;padding:0;margin-right:2px;-webkit-tap-highlight-color:transparent}' +
      '#hab-mnav-btn svg{width:22px;height:22px;display:block}' +
      '#hab-mnav-btn.open{color:var(--ink,#0F172A);background:#F1F5F9}' +
      '#hab-mnav{display:none;position:fixed;left:0;right:0;z-index:9990;background:#fff;' +
        'border-bottom:1px solid var(--line,#E2E8F0);box-shadow:0 18px 40px -12px rgba(15,23,42,.18);padding:4px 0 8px}' +
      '#hab-mnav.open{display:block}' +
      '#hab-mnav a{display:flex;align-items:center;justify-content:space-between;padding:14px 24px;font-size:15px;' +
        'font-weight:600;color:var(--ink,#0F172A);text-decoration:none;border-top:1px solid #F1F5F9}' +
      '#hab-mnav a:first-child{border-top:0}' +
      '#hab-mnav a.cur{color:var(--pri,#00A88A)}' +
      '#hab-mnav a.cur::after{content:"";width:6px;height:6px;border-radius:50%;background:var(--pri,#00A88A)}' +
      '#hab-mnav-mask{display:none;position:fixed;left:0;right:0;bottom:0;z-index:9989;background:rgba(15,23,42,.22)}' +
      '#hab-mnav-mask.open{display:block}' +
      '@media(max-width:960px){#hab-mnav-btn{display:inline-flex}.gright{margin-left:auto}}';
    document.head.appendChild(css);

    var ICON_MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></svg>';
    var ICON_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';

    var btn = document.createElement('button');
    btn.id = 'hab-mnav-btn'; btn.type = 'button';
    btn.setAttribute('aria-label', '站内导航'); btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = ICON_MENU;
    right.insertBefore(btn, right.firstChild);

    var panel = document.createElement('nav');
    panel.id = 'hab-mnav'; panel.setAttribute('aria-label', '站内导航');
    var as = links.querySelectorAll('a');
    for (var i = 0; i < as.length; i++) {
      var a = document.createElement('a');
      a.href = as[i].getAttribute('href'); a.textContent = as[i].textContent.trim();
      if (as[i].classList.contains('cur')) a.className = 'cur';
      panel.appendChild(a);
    }
    var mask = document.createElement('div'); mask.id = 'hab-mnav-mask';
    document.body.appendChild(mask); document.body.appendChild(panel);

    function place() {
      var top = hdr ? Math.max(0, Math.round(hdr.getBoundingClientRect().bottom)) : 60;
      panel.style.top = top + 'px'; mask.style.top = top + 'px';
    }
    function setOpen(on) {
      place();
      panel.classList.toggle('open', on); mask.classList.toggle('open', on); btn.classList.toggle('open', on);
      btn.innerHTML = on ? ICON_X : ICON_MENU; btn.setAttribute('aria-expanded', on ? 'true' : 'false');
    }
    btn.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); setOpen(!panel.classList.contains('open')); });
    mask.addEventListener('click', function () { setOpen(false); });
    window.addEventListener('resize', function () { if (panel.classList.contains('open')) setOpen(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && panel.classList.contains('open')) setOpen(false); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountMobileNav);
  else mountMobileNav();
})();
