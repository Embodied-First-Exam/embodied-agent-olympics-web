const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
document.documentElement.classList.add('js');

function selected(button, on) {
  button.classList.toggle('on', on);
  button.classList.toggle('active', on);
  button.classList.toggle('selected', on);
  button.setAttribute('aria-pressed', String(on));
  if (button.hasAttribute('aria-selected')) button.setAttribute('aria-selected', String(on));
}

function applyTheme(theme, remember = true) {
  document.documentElement.dataset.theme = theme;
  if (remember) {
    try { localStorage.setItem('eao-theme', theme); } catch (_) { /* A private session keeps the choice on this page. */ }
  }
  const meta = $('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'dark' ? '#121417' : '#f4f6f9';
  const button = $('#theme-toggle');
  if (button) {
    button.setAttribute('aria-pressed', String(theme === 'dark'));
    const label = theme === 'dark' ? button.dataset.lightLabel : button.dataset.darkLabel;
    if (label) button.setAttribute('aria-label', label);
  }
  dispatchEvent(new Event('themechange'));
}
applyTheme(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light', false);
$('#theme-toggle')?.addEventListener('click', () => applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));

const nav = $('.nav');
const menu = $('#menu-toggle');
const narrowNav = matchMedia('(max-width: 860px)');
function openMenu(open) {
  nav?.classList.toggle('open', open);
  menu?.setAttribute('aria-expanded', String(open));
}
menu?.addEventListener('click', () => openMenu(!nav?.classList.contains('open')));
$$('.nav-links a').forEach((link) => link.addEventListener('click', () => openMenu(false)));
addEventListener('pointerdown', (event) => {
  if (nav?.classList.contains('open') && !nav.contains(event.target)) openMenu(false);
});
addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && nav?.classList.contains('open')) {
    openMenu(false);
    menu?.focus();
  }
});
narrowNav.addEventListener('change', () => openMenu(false));

const revealElements = $$('.reveal');
if (reducedMotion.matches || !('IntersectionObserver' in window)) {
  revealElements.forEach((element) => element.classList.add('in', 'is-visible'));
} else {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) if (entry.isIntersecting) {
      entry.target.classList.add('in', 'is-visible');
      observer.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -6% 0px' });
  revealElements.forEach((element) => observer.observe(element));
}
reducedMotion.addEventListener('change', () => {
  if (reducedMotion.matches) revealElements.forEach((element) => element.classList.add('in', 'is-visible'));
});

function countUp(element) {
  if (element.dataset.counted === 'true') return;
  element.dataset.counted = 'true';
  const value = Number(element.dataset.count);
  if (!Number.isFinite(value)) return;
  if (reducedMotion.matches) { element.textContent = String(value); return; }
  const start = performance.now();
  const duration = 850;
  function tick(now) {
    if (reducedMotion.matches) { element.textContent = String(value); return; }
    const progress = Math.min(1, (now - start) / duration);
    element.textContent = String(Math.round(value * (1 - Math.pow(1 - progress, 3))));
    if (progress < 1) requestAnimationFrame(tick);
    else element.textContent = String(value);
  }
  requestAnimationFrame(tick);
}
const countElements = $$('[data-count]');
if ('IntersectionObserver' in window && !reducedMotion.matches) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) if (entry.isIntersecting) {
      countUp(entry.target);
      observer.unobserve(entry.target);
    }
  }, { threshold: .5 });
  countElements.forEach((element) => observer.observe(element));
} else countElements.forEach(countUp);

$$('[data-mode-toggle]').forEach((toggle) => {
  const scope = toggle.closest('[data-mode-control]') || document;
  const buttons = $$('button[data-mode]', toggle);
  function apply(mode) {
    const engineer = mode === 'engineer';
    buttons.forEach((button) => selected(button, button.dataset.mode === mode));
    $$('.control-chain [data-step]', scope).forEach((step) => {
      const active = Number(step.dataset.step) <= (engineer ? 4 : 1);
      step.classList.toggle('active', active);
      step.classList.toggle('on', active);
      step.classList.toggle('is-active', active);
    });
    $$('[data-mode-line]', scope).forEach((line) => {
      if (line.dataset[mode]) line.textContent = line.dataset[mode];
    });
    $$('[data-mode-status]', scope).forEach((status) => { status.hidden = !engineer; });
    toggle.dataset.currentMode = mode;
  }
  buttons.forEach((button) => button.addEventListener('click', () => apply(button.dataset.mode)));
  apply(buttons.find((button) => button.getAttribute('aria-pressed') === 'true')?.dataset.mode || 'athlete');
});

$$('.intelligence-chain, [data-intelligence-chain]').forEach((chain) => {
  const scope = chain.closest('section') || document;
  const hint = $('[data-chain-hint]', scope);
  if (!hint) return;
  const original = hint.textContent;
  const restore = () => {
    const focused = $('[data-hint]:focus', chain);
    hint.textContent = focused?.dataset.hint || original;
  };
  $$('[data-hint]', chain).forEach((node) => {
    const show = () => { hint.textContent = node.dataset.hint; };
    node.addEventListener('pointerenter', show);
    node.addEventListener('focus', show);
    node.addEventListener('click', show);
    node.addEventListener('pointerleave', restore);
    node.addEventListener('blur', restore);
  });
});

const normalize = (value) => {
  const key = String(value || '').toLowerCase().trim().replace(/[\s_]+/g, '-');
  if (key === 'real-time' || key === 'realtime') return 'realtime';
  if (key === 'turnbased' || key === 'turn-based') return 'turn-based';
  if (key === 'multiparty' || key === 'multi-party') return 'multi-party';
  if (key.includes('sport') && key.includes('specific')) return 'sport-specific';
  return key;
};

$$('[data-wall-filter]').forEach((button) => {
  button.addEventListener('click', () => {
    const value = normalize(button.dataset.wallFilter);
    $$('[data-wall-filter]').forEach((other) => selected(other, other === button));
    $$('[data-wall] [data-timing]').forEach((tile) => {
      tile.classList.toggle('is-dim', value !== 'all' && normalize(tile.dataset.timing) !== value);
    });
    dispatchEvent(new Event('eaofilterchange'));
  });
});

$$('[data-sports-filters], [data-sports-filter]').forEach((filters) => {
  const choices = { timing: 'all', format: 'all', physics: 'all' };
  const buttons = $$('button[data-filter-group][data-filter-value], [data-filter-group] button[data-filter]', filters);
  function apply() {
    let found = 0;
    $$('[data-sport-card]').forEach((card) => {
      const timing = normalize(card.dataset.timing);
      const physics = (card.dataset.physics || '').split(/[\s,]+/).map(normalize);
      const formats = (card.dataset.formats || '').split(/[\s,]+/).map(normalize);
      const matches = (choices.timing === 'all' || timing === choices.timing)
        && (choices.physics === 'all' || physics.includes(choices.physics))
        && (choices.format === 'all' || formats.includes(choices.format));
      card.hidden = !matches;
      if (matches) found++;
    });
    $$('[data-filter-empty]').forEach((notice) => { notice.hidden = found > 0; });
    dispatchEvent(new Event('eaofilterchange'));
  }
  buttons.forEach((button) => button.addEventListener('click', () => {
    const group = button.dataset.filterGroup || button.closest('[data-filter-group]').dataset.filterGroup;
    const value = normalize(button.dataset.filterValue || button.dataset.filter);
    choices[group] = value;
    buttons.forEach((other) => {
      const otherGroup = other.dataset.filterGroup || other.closest('[data-filter-group]').dataset.filterGroup;
      if (otherGroup === group) selected(other, other === button);
    });
    apply();
  }));
});

$$('[data-ability-definition]').forEach((button) => {
  const definition = $('[data-matrix-definition]', button.closest('section') || document);
  if (!definition) return;
  const original = definition.textContent;
  const show = () => { definition.textContent = button.dataset.abilityDefinition; };
  button.addEventListener('pointerenter', show);
  button.addEventListener('focus', show);
  button.addEventListener('click', show);
  button.addEventListener('pointerleave', () => {
    if (document.activeElement !== button) definition.textContent = original;
  });
  button.addEventListener('blur', () => { definition.textContent = original; });
});

$$('[data-view-toggle]').forEach((toggle) => {
  const scope = toggle.closest('[data-player-view]') || $('[data-player-view]') || document;
  const buttons = $$('button[data-view]', toggle);
  function apply(view) {
    buttons.forEach((button) => selected(button, button.dataset.view === view));
    $$('[data-view-panel]', scope).forEach((panel) => { panel.hidden = panel.dataset.viewPanel !== view; });
    const broadcast = $('[data-broadcast]', scope);
    const player = $('[data-player-image]', scope);
    if (broadcast) broadcast.hidden = view !== 'broadcast';
    if (player) player.hidden = view !== 'player';
    if (view === 'player') $$('video', scope).forEach((video) => video.pause());
    toggle.dataset.currentView = view;
    dispatchEvent(new Event('eaoviewchange'));
  }
  buttons.forEach((button) => button.addEventListener('click', () => apply(button.dataset.view)));
});

// The diagnostic is deliberately read from the DOM after interaction and scrolling.
if (new URLSearchParams(location.search).get('selftest') === '1') {
  const pendingImage = (img) => !img.complete && (img.loading !== 'lazy' || (() => {
    const box = img.getBoundingClientRect();
    return box.top < innerHeight + 300 && box.bottom > -300;
  })());
  async function selftest() {
    const images = $$('img');
    await Promise.all(images.filter(pendingImage).map((img) => new Promise((resolve) => {
      const done = () => { clearTimeout(timeout); img.removeEventListener('load', done); img.removeEventListener('error', done); resolve(); };
      const timeout = setTimeout(done, 5000);
      img.addEventListener('load', done, { once: true });
      img.addEventListener('error', done, { once: true });
    })));
    const video = window.eaoPlaybackStatus();
    const brokenImages = images.filter((img) => img.complete && img.naturalWidth === 0).map((img) => img.getAttribute('src'));
    const width = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
    const overflow = Math.max(0, width - innerWidth);
    const failures = [];
    if (overflow > 0) failures.push('horizontal overflow');
    if (brokenImages.length) failures.push('broken images');
    if (video.playing > video.cap) failures.push('video playback cap');
    if (video.cardsPlaying > (video.touch ? 2 : 4)) failures.push('sport card playback cap');
    if (video.reducedMotion && video.autoplaying) failures.push('autoplay with reduced motion');
    const theme = document.documentElement.dataset.theme;
    if (theme !== 'light' && theme !== 'dark') failures.push('invalid theme');
    const result = {
      pass: failures.length === 0, passed: failures.length === 0,
      failures, errors: failures, videos: video, brokenImages,
      overflow: overflow > 0, overflowPixels: overflow,
      viewport: innerWidth, documentWidth: width, theme,
      components: {
        sportCards: $$('[data-sport-card]').length,
        visibleSportCards: $$('[data-sport-card]:not([hidden])').length,
        multiviewTiles: $$('[data-wall] [data-timing]').length,
        scoreboardTiles: $$('[data-count]').length,
        intelligenceNodes: $$('.intelligence-chain [data-hint], [data-intelligence-chain] [data-hint]').length,
        controlSteps: $$('.control-chain [data-step]').length,
        podiums: $$('.podium, .podium-card, [data-podium]').length,
        modeToggles: $$('[data-mode-toggle]').length,
        viewToggles: $$('[data-view-toggle]').length,
      },
    };
    document.body.dataset.selftest = JSON.stringify(result);
    return result;
  }
  window.eaoSelftest = selftest;
  selftest();
  addEventListener('load', () => selftest(), { once: true });
  addEventListener('themechange', () => selftest());
  addEventListener('eaofilterchange', () => selftest());
  addEventListener('eaoviewchange', () => selftest());
}
