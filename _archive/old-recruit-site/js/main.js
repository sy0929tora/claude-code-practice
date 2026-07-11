/* ============================================================
   神奈川ITエンジニア転職ラボ — Shared JS Components
   ============================================================ */

/* ---------- Header HTML ---------- */
const HEADER_HTML = `
<header id="site-header">
  <nav class="nav-inner">
    <a href="/claude-code-practice/" class="site-logo">神奈川IT<span>転職ラボ</span></a>
    <ul class="nav-links">
      <li><a href="/claude-code-practice/jobs.html">求人一覧</a></li>
      <li class="nav-dropdown">
        <a href="/claude-code-practice/salary.html">情報 ▾</a>
        <ul class="dropdown-menu">
          <li><a href="/claude-code-practice/salary.html">💰 年収相場</a></li>
          <li><a href="/claude-code-practice/companies.html">🏢 おすすめ企業</a></li>
          <li><a href="/claude-code-practice/remote-work.html">💻 リモートワーク実態</a></li>
        </ul>
      </li>
      <li class="nav-dropdown">
        <a href="/claude-code-practice/career-change-guide.html">ガイド ▾</a>
        <ul class="dropdown-menu">
          <li><a href="/claude-code-practice/career-change-guide.html">📘 転職完全ガイド</a></li>
          <li><a href="/claude-code-practice/interview-guide.html">🎯 面接対策</a></li>
          <li><a href="/claude-code-practice/skill-guide.html">🛠️ スキルガイド</a></li>
          <li><a href="/claude-code-practice/engineer-types.html">💼 職種別ガイド</a></li>
          <li><a href="/claude-code-practice/rankings.html">🏆 企業ランキング</a></li>
          <li><a href="/claude-code-practice/success-stories.html">✨ 成功事例</a></li>
        </ul>
      </li>
      <li><a href="/claude-code-practice/contact.html" class="btn-nav">無料相談</a></li>
    </ul>
    <button class="hamburger" aria-label="メニューを開く" id="hamburgerBtn">
      <span></span><span></span><span></span>
    </button>
  </nav>
  <nav class="mobile-nav" id="mobileNav">
    <a href="/claude-code-practice/jobs.html">📋 求人一覧</a>
    <a href="/claude-code-practice/salary.html">💰 年収相場</a>
    <a href="/claude-code-practice/companies.html">🏢 おすすめ企業</a>
    <a href="/claude-code-practice/remote-work.html">💻 リモートワーク実態</a>
    <a href="/claude-code-practice/career-change-guide.html">📘 転職完全ガイド</a>
    <a href="/claude-code-practice/interview-guide.html">🎯 面接対策ガイド</a>
    <a href="/claude-code-practice/skill-guide.html">🛠️ スキルガイド</a>
    <a href="/claude-code-practice/engineer-types.html">💼 職種別ガイド</a>
    <a href="/claude-code-practice/rankings.html">🏆 企業ランキング</a>
    <a href="/claude-code-practice/success-stories.html">✨ 成功事例</a>
    <a href="/claude-code-practice/contact.html" class="btn-nav-mobile">無料転職相談（無料）</a>
  </nav>
</header>`;

/* ---------- Footer HTML ---------- */
const FOOTER_HTML = `
<footer id="site-footer">
  <div class="footer-main">
    <div class="footer-brand">
      <a href="/claude-code-practice/" class="site-logo">神奈川IT<span>転職ラボ</span></a>
      <p>現役転職エージェントが発信する<br>神奈川エリア特化のITエンジニア向け転職情報メディアです。</p>
    </div>
    <div class="footer-col">
      <h4>求人・情報</h4>
      <ul>
        <li><a href="/claude-code-practice/jobs.html">求人一覧</a></li>
        <li><a href="/claude-code-practice/salary.html">年収相場</a></li>
        <li><a href="/claude-code-practice/companies.html">おすすめ企業</a></li>
        <li><a href="/claude-code-practice/remote-work.html">リモートワーク実態</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>転職ガイド</h4>
      <ul>
        <li><a href="/claude-code-practice/career-change-guide.html">転職完全ガイド</a></li>
        <li><a href="/claude-code-practice/interview-guide.html">面接対策ガイド</a></li>
        <li><a href="/claude-code-practice/skill-guide.html">スキルガイド</a></li>
        <li><a href="/claude-code-practice/engineer-types.html">職種別ガイド</a></li>
        <li><a href="/claude-code-practice/rankings.html">企業ランキング</a></li>
        <li><a href="/claude-code-practice/success-stories.html">転職成功事例</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>エリア情報</h4>
      <ul>
        <li><a href="/claude-code-practice/area-yokohama.html">横浜エリア</a></li>
        <li><a href="/claude-code-practice/area-kawasaki.html">川崎エリア</a></li>
        <li><a href="/claude-code-practice/area-sagamihara.html">相模原エリア</a></li>
        <li><a href="/claude-code-practice/area-atsugi.html">厚木エリア</a></li>
        <li><a href="/claude-code-practice/area-fujisawa.html">藤沢エリア</a></li>
        <li><a href="/claude-code-practice/area-ebina.html">海老名エリア</a></li>
        <li><a href="/claude-code-practice/area-yokosuka.html">横須賀エリア</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>サポート</h4>
      <ul>
        <li><a href="/claude-code-practice/contact.html">無料転職相談</a></li>
        <li><a href="/claude-code-practice/for-companies.html">企業の方へ</a></li>
        <li><a href="/claude-code-practice/about.html">運営者情報</a></li>
        <li><a href="/claude-code-practice/faq.html">よくある質問</a></li>
        <li><a href="/claude-code-practice/privacy.html">プライバシーポリシー</a></li>
        <li><a href="/claude-code-practice/terms.html">利用規約</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© 2026 神奈川ITエンジニア転職ラボ. All rights reserved.</span>
    <span>当サイトの情報は転職エージェントによる調査に基づきます。</span>
  </div>
</footer>`;

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
  injectHeader();
  injectFooter();
  initMobileMenu();
  highlightActiveNav();
  initFAQ();
  initTabs();
  initFadeUp();
  initFilterBar();
  initScrollTop();
  initReadingProgress();
});

function injectHeader() {
  const placeholder = document.getElementById('header-placeholder');
  if (placeholder) {
    placeholder.outerHTML = HEADER_HTML;
  } else if (!document.getElementById('site-header')) {
    document.body.insertAdjacentHTML('afterbegin', HEADER_HTML);
  }
}

function injectFooter() {
  const placeholder = document.getElementById('footer-placeholder');
  if (placeholder) {
    placeholder.outerHTML = FOOTER_HTML;
  } else if (!document.getElementById('site-footer')) {
    document.body.insertAdjacentHTML('beforeend', FOOTER_HTML);
  }
}

function initMobileMenu() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('#hamburgerBtn');
    const nav = document.getElementById('mobileNav');
    if (!nav) return;
    if (btn) {
      nav.classList.toggle('open');
      return;
    }
    if (!e.target.closest('#mobileNav') && !e.target.closest('#hamburgerBtn')) {
      nav.classList.remove('open');
    }
  });
  // Close on link click
  document.addEventListener('click', e => {
    if (e.target.closest('#mobileNav a')) {
      const nav = document.getElementById('mobileNav');
      if (nav) nav.classList.remove('open');
    }
  });
}

function highlightActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('#site-header .nav-links a, #site-header .mobile-nav a').forEach(a => {
    if (a.getAttribute('href') && path.endsWith(a.getAttribute('href').split('/').pop())) {
      a.classList.add('active');
    }
  });
}

function initFAQ() {
  document.querySelectorAll('.faq-item').forEach(item => {
    const q = item.querySelector('.faq-q');
    if (!q) return;
    q.addEventListener('click', () => {
      const isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));
      if (!isOpen) item.classList.add('open');
    });
  });
}

function initTabs() {
  document.querySelectorAll('.tabs').forEach(tabGroup => {
    tabGroup.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tab;
        const parent = btn.closest('.tab-container') || document;
        parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        parent.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const panel = parent.querySelector(`#${target}`);
        if (panel) panel.classList.add('active');
      });
    });
  });
}

function initFadeUp() {
  if (!('IntersectionObserver' in window)) return;
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.anim-up').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity .5s ease, transform .5s ease';
    obs.observe(el);
  });
}

function initFilterBar() {
  const filterSelects = document.querySelectorAll('.filter-select[data-filter]');
  if (!filterSelects.length) return;
  filterSelects.forEach(sel => {
    sel.addEventListener('change', applyFilters);
  });
}

function applyFilters() {
  const filterSelects = document.querySelectorAll('.filter-select[data-filter]');
  const filters = {};
  filterSelects.forEach(sel => {
    filters[sel.dataset.filter] = sel.value;
  });

  document.querySelectorAll('[data-tags]').forEach(card => {
    const tags = card.dataset.tags || '';
    let visible = true;
    Object.entries(filters).forEach(([key, val]) => {
      if (val && !tags.includes(val)) visible = false;
    });
    card.style.display = visible ? '' : 'none';
  });

  // Update count
  const countEl = document.getElementById('result-count');
  if (countEl) {
    const visible = document.querySelectorAll('[data-tags]:not([style*="display: none"])').length;
    countEl.textContent = visible;
  }
}

/* ---------- Salary Calculator ---------- */
window.calcSalary = function() {
  const role    = document.getElementById('calc-role')?.value || 'backend';
  const years   = parseInt(document.getElementById('calc-years')?.value || '3');
  const skill   = document.getElementById('calc-skill')?.value || 'mid';
  const remote  = document.getElementById('calc-remote')?.value || 'hybrid';

  // Base salary by role (万円)
  const bases = {
    backend:  550, frontend: 520, fullstack: 580, infra: 560,
    mobile:   540, data:     600, security:  620, pm:    560,
    embedded: 500, qa:       460,
  };
  let base = bases[role] || 540;

  // Experience multiplier
  const expMult = years <= 1 ? .78 : years <= 3 ? .92 : years <= 5 ? 1.0
               : years <= 8 ? 1.15 : years <= 10 ? 1.28 : 1.38;

  // Skill multiplier
  const skillMult = { low: .88, mid: 1.0, high: 1.12, expert: 1.25 };

  // Remote premium
  const remoteMult = { full: 1.04, hybrid: 1.0, office: .97 };

  const salary = Math.round(base * expMult * (skillMult[skill] || 1) * (remoteMult[remote] || 1) / 10) * 10;
  const low  = Math.round(salary * .88 / 10) * 10;
  const high = Math.round(salary * 1.12 / 10) * 10;

  const el = document.getElementById('calc-result');
  if (el) {
    el.innerHTML = `
      <div class="result-label">神奈川エリア 推定年収</div>
      <div class="result-num">${salary}<sub>万円</sub></div>
      <div class="result-range">想定レンジ： ${low}万円 〜 ${high}万円</div>`;
    el.classList.add('show');
  }
};

/* ---------- Scroll-to-top ---------- */
function initScrollTop() {
  const btn = document.createElement('button');
  btn.id = 'scroll-top';
  btn.setAttribute('aria-label', 'ページトップへ');
  btn.innerHTML = '↑';
  document.body.appendChild(btn);
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

/* ---------- Reading progress bar ---------- */
function initReadingProgress() {
  const bar = document.createElement('div');
  bar.id = 'reading-progress';
  document.body.appendChild(bar);
  window.addEventListener('scroll', () => {
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docH > 0 ? (window.scrollY / docH) * 100 : 0;
    bar.style.width = pct + '%';
  }, { passive: true });
}
