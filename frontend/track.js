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
           : /quiz\.html/.test(path) ? 'quiz'
           : /learn\.html/.test(path) ? 'reader'
           : /demo\.html/.test(path) ? 'demo' : 'page';
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
})();
