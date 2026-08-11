/* ═══════════════════════════════════════════════════════════
   lesson.js —— 课程子页统一交互助手
   核心原则：内容随滚动自然展现，无需点击"下一步"。
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* 滚动渐入：页面上所有 .reveal 元素进入视野时自动加 .show。
     无需任何配置，引入本文件即生效。 */
  function initReveal() {
    var els = document.querySelectorAll('.reveal:not(.show)');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach ? els.forEach(function (el) { el.classList.add('show'); })
                  : Array.prototype.forEach.call(els, function (el) { el.classList.add('show'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('show');
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    Array.prototype.forEach.call(els, function (el) { io.observe(el); });
  }

  /* 进入视野触发一次回调（用于自动播放演示动画）。
     用法：lessonOnView(document.getElementById('demo'), function(){ playDemo(); }); */
  window.lessonOnView = function (el, cb, threshold) {
    if (!el || typeof cb !== 'function') return;
    if (!('IntersectionObserver' in window)) { cb(); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { io.disconnect(); cb(); }
      });
    }, { threshold: typeof threshold === 'number' ? threshold : 0.35 });
    io.observe(el);
  };


  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { initReveal(); });
  } else {
    initReveal();
  }
})();
