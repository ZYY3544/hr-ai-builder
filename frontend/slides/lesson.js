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


  /* 可抄走的内容块，右上角给一个复制按钮：
     .say  = prompt / 话术素材（浅色代码块）
     .cmd  = 终端命令（深色，自带「终端里敲这个」标签）
     pre.tpl = 明确标为「模板」的配置/表格骨架
     文本在【点击时】现取——而不是初始化时——因为有些块的内容是 JS 动态注入的
     （例如 Prompt 模板会随场景切换重写），初始化时抓等于永远抄到第一份或空。 */
  function initSayCopy() {
    var blocks = document.querySelectorAll('.say, .cmd, pre.tpl');

    function mkBtn(b) {
      if (b.querySelector('.say-copy')) return;          /* 已有就别重复插 */
      var btn = document.createElement('button');
      btn.className = 'say-copy' + (b.classList.contains('cmd') ? ' on-dark' : '');
      btn.type = 'button'; btn.textContent = '复制';
      btn.addEventListener('click', function () {
        /* 克隆去掉按钮自身再取文本，否则会把「复制」两个字也抄进去 */
        var clone = b.cloneNode(true);
        var inner = clone.querySelector('.say-copy');
        if (inner) inner.parentNode.removeChild(inner);
        var txt = clone.innerText;
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
    }

    Array.prototype.forEach.call(blocks, mkBtn);

    /* 有些块的内容是 JS 动态重写的（如 Prompt 模板随场景切换），
       页面用 textContent = '…' 赋值会清空所有子节点、把按钮一起抹掉。
       实测：切一次场景按钮就没了。所以盯住内容变化，掉了就补回来。
       补按钮本身也会触发一次 childList，但 mkBtn 开头有存在性判断，不会循环。 */
    if (window.MutationObserver) {
      var mo = new MutationObserver(function (muts) {
        for (var i = 0; i < muts.length; i++) mkBtn(muts[i].target);
      });
      Array.prototype.forEach.call(blocks, function (b) { mo.observe(b, { childList: true }); });
    }
  }



  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { initReveal(); initSayCopy(); });
  } else {
    initReveal(); initSayCopy();
  }
})();
