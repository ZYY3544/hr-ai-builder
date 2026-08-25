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


  /* .say 素材块右上角复制按钮（2026-08-26 用户拍板，替代「可以整段抄走」标签）。
     文本在插按钮前取（innerText 在 pre-wrap 下保留换行）；clipboard 不可用时走 textarea 兜底。 */
  function initSayCopy() {
    var blocks = document.querySelectorAll('.say');
    Array.prototype.forEach.call(blocks, function (b) {
      var txt = b.innerText;
      var btn = document.createElement('button');
      btn.className = 'say-copy'; btn.type = 'button'; btn.textContent = '复制';
      btn.addEventListener('click', function () {
        var done = function () {
          btn.textContent = '✓ 已复制'; btn.classList.add('ok');
          setTimeout(function () { btn.textContent = '复制'; btn.classList.remove('ok'); }, 1600);
        };
        var fallback = function () {
          var ta = document.createElement('textarea'); ta.value = txt;
          ta.style.position = 'fixed'; ta.style.opacity = '0';
          document.body.appendChild(ta); ta.select();
          try { document.execCommand('copy'); done(); } catch (e) {}
          document.body.removeChild(ta);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(txt).then(done).catch(fallback);
        } else fallback();
      });
      b.appendChild(btn);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { initReveal(); initSayCopy(); });
  } else {
    initReveal(); initSayCopy();
  }
})();
