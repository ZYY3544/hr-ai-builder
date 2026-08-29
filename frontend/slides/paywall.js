/**
 * paywall.js —— 未登录访客的正文预览限制（Google Flexible Sampling）
 *
 * 做法说明（改动前务必读完）：
 *   页面 HTML **始终包含完整正文**，供搜索引擎与 AI 引擎抓取；未登录访客在
 *   客户端只看到前一段，其余隐藏并引导登录。受限范围由 .paywall-locked 类界定，
 *   并在页面 JSON-LD 里以 isAccessibleForFree + hasPart.cssSelector 声明——
 *   这是 Google Flexible Sampling 的标准做法，**与 cloaking 的区别就在于这份声明**，
 *   改动时不要把它拆掉。
 *
 *   为什么不把受限内容搬到后端：本仓库是 AGPL 公开的，内容就在 GitHub 上，
 *   搬走保护不了任何东西，却会白白丢掉这些页面的全部 SEO。
 *
 * 闸门开关：window.COURSE.meta.access.gate（"on" / "off"）。
 *   微信登录跑通前保持 off —— 此时只在正文顶部提示可登录同步进度，不遮挡内容。
 */
(function () {
  'use strict';
  var LOCK = document.querySelector('.paywall-locked');
  if (!LOCK) return;

  var TK = 'hab_token';
  var inFrame = window.top !== window.self;   // learn.html 的 iframe 里也要拦，否则等于把墙拆了

  function tokenOK() {
    try { return !!localStorage.getItem(TK); } catch (e) { return false; }
  }

  // 闸门状态：优先读 course-data（阅读器 iframe 内父页已加载），否则问一次 API，默认 off
  function gateOn(cb) {
    try {
      var g = (window.COURSE && window.COURSE.meta && window.COURSE.meta.access || {}).gate;
      if (g) return cb(g === 'on');
      if (window.top !== window.self && window.top.COURSE) {
        g = (window.top.COURSE.meta.access || {}).gate;
        if (g) return cb(g === 'on');
      }
    } catch (e) {}
    var API = (location.hostname === 'localhost' || location.protocol === 'file:')
      ? 'http://localhost:8001' : 'https://hr-ai-builder-api.onrender.com';
    fetch(API + '/api/auth/config')
      .then(function (r) { return r.json(); })
      .then(function (d) { cb(d.gate === 'on'); })
      .catch(function () { cb(false); });   // 服务不可用时不拦，宁可少收也不错杀
  }

  function reveal() {
    LOCK.classList.remove('xa-locked');
    var g = document.getElementById('xa-gate');
    if (g) g.remove();
  }

  function lock() {
    LOCK.classList.add('xa-locked');
    if (document.getElementById('xa-gate')) return;
    var box = document.createElement('div');
    box.id = 'xa-gate';
    box.innerHTML =
      '<div class="xa-gate-in">' +
        '<div class="xa-gate-t">登录后继续免费阅读</div>' +
        '<div class="xa-gate-s">这一课还没结束。登录即可解锁余下内容与全部课程——' +
          '<b>完全免费，不花一分钱</b>。</div>' +
        '<div class="xa-gate-why">' +
          '<div><b>为什么要登录</b></div>' +
          '<div>· 同步你的学习进度与小测成绩，换设备接着学</div>' +
          '<div>· 防止课程内容被批量抓走后包装成付费课程贩卖</div>' +
        '</div>' +
        '<a class="xa-gate-b" href="' + (inFrame ? '../index.html' : '../index.html') + '#login" target="_top">去登录</a>' +
        '<div class="xa-gate-f">开篇、第零篇章与大部分章节，不登录也能直接读。</div>' +
      '</div>';
    LOCK.parentNode.insertBefore(box, LOCK);
  }

  /* 「这一节不登录也能读完」软提示已删（2026-08-26 用户拍板）：句式+锁图标反而暗示
     别的节要解锁，是付费墙误导；登录入口右上角常驻，不缺这条。gate 机制本身保留。 */
  gateOn(function (on) {
    if (!on) { reveal(); return; }
    if (tokenOK()) { reveal(); return; }
    lock();
  });
})();
