/* =========================================================
   ArioSport — Interactions & Animations
   ========================================================= */
(function () {
  'use strict';

  /* ---- Icons (Lucide) ---- */
  function renderIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  /* ---- Navbar scroll state ---- */
  const navbar = document.querySelector('.navbar');
  function onScrollNav() {
    if (!navbar) return;
    navbar.classList.toggle('scrolled', window.scrollY > 24);
  }

  /* ---- Mobile menu ---- */
  const mobileNav = document.getElementById('mobileNav');
  const openBtn = document.getElementById('menuOpen');
  const closeBtn = document.getElementById('menuClose');
  function openMenu() { mobileNav && mobileNav.classList.add('open'); document.body.style.overflow = 'hidden'; }
  function closeMenu() { mobileNav && mobileNav.classList.remove('open'); document.body.style.overflow = ''; }
  openBtn && openBtn.addEventListener('click', openMenu);
  closeBtn && closeBtn.addEventListener('click', closeMenu);
  mobileNav && mobileNav.addEventListener('click', function (e) { if (e.target === mobileNav) closeMenu(); });

  /* ---- Back to top ---- */
  const toTop = document.getElementById('toTop');
  function onScrollTop() {
    if (!toTop) return;
    toTop.classList.toggle('show', window.scrollY > 500);
  }
  toTop && toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* ---- Reading progress (post page) ---- */
  const readingBar = document.getElementById('readingBar');
  const article = document.querySelector('.article');
  function onScrollReading() {
    if (!readingBar || !article) return;
    const start = article.offsetTop;
    const end = start + article.offsetHeight - window.innerHeight;
    const p = Math.min(Math.max((window.scrollY - start) / (end - start), 0), 1);
    readingBar.style.width = (p * 100) + '%';
  }

  /* ---- Scroll reveal ---- */
  function initReveal() {
    const els = document.querySelectorAll('[data-reveal]');
    if (!('IntersectionObserver' in window)) { els.forEach(function (el) { el.classList.add('in'); }); return; }
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add('in'); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ---- Counter animation ---- */
  function animateCounter(el) {
    const target = parseFloat(el.getAttribute('data-count'));
    const suffix = el.getAttribute('data-suffix') || '';
    const dur = 1600;
    const start = performance.now();
    function tick(now) {
      const t = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      const val = target * eased;
      el.textContent = (target % 1 === 0 ? Math.round(val) : val.toFixed(1)) + suffix;
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  function initCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { animateCounter(entry.target); io.unobserve(entry.target); }
      });
    }, { threshold: 0.5 });
    counters.forEach(function (c) { io.observe(c); });
  }

  /* ---- Hero parallax ---- */
  const heroBg = document.querySelector('.hero-bg img');
  function onScrollParallax() {
    if (!heroBg) return;
    const y = window.scrollY;
    if (y < window.innerHeight) heroBg.style.transform = 'translateY(' + (y * 0.18) + 'px) scale(1.05)';
  }

  /* ---- Password visibility toggle ---- */
  document.querySelectorAll('.toggle-pass').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const input = btn.parentElement.querySelector('input');
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.innerHTML = show ? '<i data-lucide="eye-off"></i>' : '<i data-lucide="eye"></i>';
      renderIcons();
    });
  });

  /* ---- Filter chips (blog) ---- */
  const chips = document.querySelectorAll('.filter-bar .chip');
  const cards = document.querySelectorAll('[data-cat]');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      const f = chip.getAttribute('data-filter');
      cards.forEach(function (card) {
        const show = f === 'all' || card.getAttribute('data-cat') === f;
        card.style.display = show ? '' : 'none';
      });
    });
  });

  /* ---- Forms (demo, prevent submit) ---- */
  document.querySelectorAll('form[data-demo]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const note = form.querySelector('.form-note');
      if (note) { note.style.display = 'flex'; }
      form.reset();
      setTimeout(function () { if (note) note.style.display = 'none'; }, 4000);
    });
  });

  /* ---- Master scroll handler ---- */
  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      onScrollNav(); onScrollTop(); onScrollReading(); onScrollParallax();
      ticking = false;
    });
  }

  /* ---- Reply toggle ---- */
  window.toggleReply = function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    var isHidden = el.style.display === 'none' || !el.style.display;
    document.querySelectorAll('.reply-form-wrap').forEach(function (f) { f.style.display = 'none'; });
    el.style.display = isHidden ? 'block' : 'none';
    if (isHidden) {
      var ta = el.querySelector('textarea');
      if (ta) ta.focus();
      renderIcons();
    }
  };

  /* ---- Init ---- */
  document.addEventListener('DOMContentLoaded', function () {
    renderIcons();
    initReveal();
    initCounters();
    onScrollNav();
    window.addEventListener('scroll', onScroll, { passive: true });
  });
})();
