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
const menuLinks = $('#nav-links');
const narrowNav = matchMedia('(max-width: 860px)');
function menuOrder() {
  if (!menuLinks) return;
  // Keep the disclosure's links next in forward Tab order on phones.
  if (narrowNav.matches) menu?.after(menuLinks);
  else $('.wordmark', nav || document)?.after(menuLinks);
}
menuOrder();
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
    event.preventDefault();
    openMenu(false);
    menu?.focus();
  }
});
narrowNav.addEventListener('change', () => { openMenu(false); menuOrder(); });

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
  if (chain.closest('[data-intelligence-arc]')) return;
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

$$('[data-control-room]').forEach((room) => {
  const video = $('[data-control-video]', room), strip = $('[data-control-channels]', room);
  const channels = $$('button[data-control-channel]', strip || room);
  if (!video || !channels.length) return;
  const progress = $('[data-control-progress]', room);
  const caption = $('[data-control-caption]', room), renderer = $('[data-control-renderer]', room);
  const title = $('[data-control-title]', room), summary = $('[data-control-summary]', room);
  const description = $('[data-control-description]', room);
  const link = $('[data-control-link]', room);
  const replay = $('[data-control-replay]', room);
  let current = -1, inView = false, holdUntil = 0, timer = 0;
  const available = (channel) => !channel.classList.contains('is-dim') && !channel.hidden && !!channel.dataset.src;
  function updateProgress() {
    const fraction = Number.isFinite(video.duration) && video.duration > 0 ? Math.min(1, video.currentTime / video.duration) : 0;
    if (progress) {
      progress.style.transform = `scaleX(${fraction})`;
      progress.dataset.progress = fraction.toFixed(4);
      if (progress.getAttribute('role') === 'progressbar') progress.setAttribute('aria-valuenow', String(Math.round(fraction * 100)));
    }
  }
  function reflect() {
    channels.forEach((channel, index) => {
      const on = index === current;
      channel.classList.toggle('on', on);
      channel.classList.toggle('is-selected', on);
      channel.classList.toggle('is-on-air', on);
      channel.setAttribute('aria-pressed', String(on));
      if (channel.hasAttribute('aria-selected')) channel.setAttribute('aria-selected', String(on));
      channel.setAttribute('aria-disabled', String(!available(channel)));
      channel.tabIndex = on && available(channel) ? 0 : -1;
    });
    room.dataset.currentChannel = channels[current]?.dataset.controlChannel || '';
    room.dataset.rotationHeld = String(performance.now() < holdUntil);
  }
  function revealChannel(channel) {
    if (!strip || getComputedStyle(strip).display !== 'flex') return;
    // Scroll the channel strip alone, keeping the page and monitor in place.
    const item = channel.getBoundingClientRect(), bounds = strip.getBoundingClientRect();
    strip.scrollTo({ left: strip.scrollLeft + item.left - bounds.left - (strip.clientWidth - item.width) / 2,
      behavior: reducedMotion.matches ? 'instant' : 'smooth' });
  }
  function show(index, manual = false, userTriggered = false) {
    if (!available(channels[index])) return;
    clearTimeout(timer);
    current = index;
    if (manual) holdUntil = performance.now() + 30000;
    const channel = channels[index], data = $('[data-control-meta]', channel)?.content;
    const lower = data && $('.lower-third', data), tag = data && $('.renderer-label', data);
    const prototype = data && $('.control-prototype', data);
    if (caption) caption.replaceChildren(...[lower, prototype].filter(Boolean).map((node) => node.cloneNode(true)));
    if (renderer) renderer.replaceChildren(...(tag ? [tag.cloneNode(true)] : []));
    if (title) title.textContent = channel.dataset.title || '';
    if (summary) {
      summary.textContent = channel.dataset.summary || '';
      summary.title = channel.dataset.summary || '';
    }
    if (description) description.textContent = channel.dataset.description || '';
    if (link && channel.dataset.href) link.href = channel.dataset.href;
    if (replay) {
      replay.hidden = !channel.dataset.replayHref;
      if (channel.dataset.replayHref) replay.href = channel.dataset.replayHref;
      else replay.removeAttribute('href');
    }
    if (channel.dataset.title) video.setAttribute('aria-label', channel.dataset.title);
    video.loop = false;
    reflect();
    revealChannel(channel);
    window.eaoSetVideoSource(video, {
      src: channel.dataset.src, poster: channel.dataset.poster,
      width: channel.dataset.width, height: channel.dataset.height,
      explicit: userTriggered && !reducedMotion.matches,
    });
    updateProgress();
    dispatchEvent(new Event('eaocontrolchange'));
  }
  function nextIndex(from = current, delta = 1) {
    for (let distance = 1; distance <= channels.length; distance++) {
      const index = (from + delta * distance % channels.length + channels.length) % channels.length;
      if (available(channels[index])) return index;
    }
    return channels.findIndex(available);
  }
  function rotate() {
    clearTimeout(timer);
    reflect();
    if (!inView || document.hidden || reducedMotion.matches || !video.ended) return;
    const remaining = holdUntil - performance.now();
    if (remaining > 0) { timer = setTimeout(rotate, remaining + 10); return; }
    const index = nextIndex();
    if (index >= 0) show(index);
  }
  channels.forEach((channel, index) => {
    channel.addEventListener('click', (event) => show(index, true, event.isTrusted));
    channel.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        show(index, true, event.isTrusted);
        return;
      }
      const grid = strip && getComputedStyle(strip);
      const columns = grid?.display === 'grid' ? grid.gridTemplateColumns.trim().split(/\s+/).length : 1;
      const steps = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns, ArrowUp: -columns };
      let target;
      if (event.key === 'Home') target = channels.findIndex(available);
      else if (event.key === 'End') target = channels.findLastIndex(available);
      else if (steps[event.key]) target = nextIndex(index, steps[event.key]);
      else return;
      event.preventDefault();
      if (target >= 0) { show(target, true, event.isTrusted); channels[target].focus({ preventScroll: true }); }
    });
  });
  addEventListener('eaofilterchange', () => {
    reflect();
    if (current >= 0 && !available(channels[current])) {
      const next = nextIndex();
      if (next >= 0) show(next);
    }
  });
  video.addEventListener('ended', rotate);
  ['timeupdate', 'durationchange', 'loadedmetadata', 'emptied'].forEach((event) => video.addEventListener(event, updateProgress));
  document.addEventListener('visibilitychange', rotate);
  reducedMotion.addEventListener('change', () => { clearTimeout(timer); reflect(); if (!reducedMotion.matches) rotate(); });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      inView = entries.some((entry) => entry.isIntersecting && entry.intersectionRatio >= .35);
      room.dataset.inView = String(inView);
      if (inView) rotate();
    }, { threshold: [0, .35] });
    observer.observe(video);
  } else { inView = true; room.dataset.inView = 'true'; }
  show(Math.max(0, channels.findIndex((channel) => channel.dataset.controlChannel === 'tabletennis' && available(channel))));
  room.eaoStatus = () => ({ selected: room.dataset.currentChannel,
    enabledChannels: channels.filter(available).length, inView,
    holdRemainingSeconds: Math.max(0, (holdUntil - performance.now()) / 1000),
    reducedMotion: reducedMotion.matches, progress: Number(progress?.dataset.progress || 0), ended: video.ended });
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

function closestOnPath(path, node, explicit) {
  if (explicit !== undefined && Number.isFinite(Number(explicit))) return Math.max(0, Math.min(1, Number(explicit)));
  const icon = node.querySelector('.node-icon, [data-stage-icon], circle') || node;
  const rect = icon.getBoundingClientRect();
  const matrix = path.getScreenCTM();
  if (!matrix || !rect.width) return null;
  const target = new DOMPoint(rect.left + rect.width / 2, rect.top + rect.height / 2).matrixTransform(matrix.inverse());
  const length = path.getTotalLength();
  const distance = (position) => {
    const point = path.getPointAtLength(position);
    return (point.x - target.x) ** 2 + (point.y - target.y) ** 2;
  };
  let best = 0, error = Infinity;
  for (let i = 0; i <= 256; i++) {
    const position = length * i / 256;
    const next = distance(position);
    if (next < error) { error = next; best = position; }
  }
  let low = Math.max(0, best - length / 256), high = Math.min(length, best + length / 256);
  for (let i = 0; i < 18; i++) {
    const a = low + (high - low) / 3, b = high - (high - low) / 3;
    if (distance(a) < distance(b)) high = b;
    else low = a;
  }
  return ((low + high) / 2) / length;
}

function placeBall(path, ball, progress) {
  const point = path.getPointAtLength(path.getTotalLength() * Math.max(0, Math.min(1, progress)));
  ball.setAttribute('cx', point.x.toFixed(3));
  ball.setAttribute('cy', point.y.toFixed(3));
}

$$('[data-three-intelligences]').forEach((group) => {
  const paths = $$('[data-intelligence-path]', group);
  const variants = paths.map((path) => ({ path, ball: $('[data-intelligence-ball]', path.closest('svg')) })).filter((item) => item.ball);
  if (!variants.length) return;
  let progress = reducedMotion.matches ? 1 : 0, frame = 0, played = reducedMotion.matches;
  function draw(fraction) {
    progress = fraction;
    variants.forEach(({ path, ball }) => placeBall(path, ball, fraction));
    group.dataset.intelligenceProgress = fraction.toFixed(4);
    group.dataset.activeGroup = String(Math.round(fraction * 2));
  }
  function measurePhone() {
    const cards = $$('[data-intelligence-group]', group);
    const bounds = group.getBoundingClientRect();
    if (cards.length < 3 || bounds.height < 1) return;
    variants.forEach(({ path, ball }) => {
      const svg = path.closest('svg');
      if (!svg.classList.contains('intelligence-flight-phone') || getComputedStyle(svg).display === 'none') return;
      const start = cards[0].getBoundingClientRect().bottom - bounds.top + 12;
      const end = cards[2].getBoundingClientRect().top - bounds.top - 20;
      if (end <= start) return;
      svg.setAttribute('viewBox', `0 0 20 ${bounds.height.toFixed(3)}`);
      path.setAttribute('d', `M10 ${start.toFixed(3)} V${end.toFixed(3)}`);
      ball.setAttribute('r', '7');
      group.dataset.phoneFlightStart = start.toFixed(3);
      group.dataset.phoneFlightEnd = end.toFixed(3);
    });
    draw(progress);
  }
  function rest() {
    cancelAnimationFrame(frame);
    played = true;
    draw(1);
    group.dataset.motionRunning = 'false';
  }
  function flight() {
    if (played || reducedMotion.matches) return;
    played = true;
    const start = performance.now();
    group.dataset.motionRunning = 'true';
    function tick(now) {
      const fraction = Math.min(1, (now - start) / 2600);
      draw(fraction);
      if (fraction < 1) frame = requestAnimationFrame(tick);
      else group.dataset.motionRunning = 'false';
    }
    frame = requestAnimationFrame(tick);
  }
  measurePhone();
  draw(progress);
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) { flight(); observer.disconnect(); }
    }, { threshold: .15 });
    observer.observe(group);
  } else flight();
  if ('ResizeObserver' in window) new ResizeObserver(measurePhone).observe(group);
  addEventListener('resize', measurePhone, { passive: true });
  document.fonts?.ready.then(measurePhone);
  reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) rest(); });
});

$$('[data-intelligence-arc]').forEach((arc) => {
  const path = $('[data-arc-path]', arc), ball = $('[data-arc-ball]', arc);
  const nodes = $$('[data-arc-step]', arc).sort((a, b) => Number(a.dataset.arcStep) - Number(b.dataset.arcStep));
  const hint = $('[data-chain-hint]', arc) || $('[data-chain-hint]', arc.closest('section') || document);
  if (!path || !ball || !nodes.length) return;
  let positions = [], progress = 0, frame = 0, played = false;
  const last = nodes.length - 1;
  function measure() {
    positions = nodes.map((node, index) => closestOnPath(path, node, node.dataset.arcProgress) ?? index / Math.max(1, last));
    placeBall(path, ball, progress);
  }
  function active(index, showHint = true) {
    if (arc.dataset.activeStep !== String(index)) nodes.forEach((node, i) => {
      node.classList.toggle('is-active', i === index);
      node.setAttribute('aria-pressed', String(i === index));
    });
    if (showHint && hint && nodes[index].dataset.hint && hint.textContent !== nodes[index].dataset.hint) hint.textContent = nodes[index].dataset.hint;
    arc.dataset.activeStep = String(index);
  }
  function cancel() {
    cancelAnimationFrame(frame);
    arc.dataset.motionRunning = 'false';
  }
  function set(position) {
    progress = position;
    placeBall(path, ball, progress);
    arc.dataset.arcProgress = progress.toFixed(4);
  }
  function move(index, duration = 240) {
    cancel();
    played = true;
    active(index);
    if (reducedMotion.matches) { set(positions[last]); return; }
    const from = progress, to = positions[index], start = performance.now();
    arc.dataset.motionRunning = 'true';
    function tick(now) {
      const fraction = Math.min(1, (now - start) / duration);
      set(from + (to - from) * (1 - (1 - fraction) ** 3));
      if (fraction < 1) frame = requestAnimationFrame(tick);
      else arc.dataset.motionRunning = 'false';
    }
    frame = requestAnimationFrame(tick);
  }
  function flight() {
    if (played || reducedMotion.matches) return;
    played = true;
    const start = performance.now(), from = positions[0], to = positions[last];
    arc.dataset.motionRunning = 'true';
    function tick(now) {
      const fraction = Math.min(1, (now - start) / 2600);
      set(from + (to - from) * fraction);
      let nearest = 0;
      positions.forEach((position, i) => { if (Math.abs(position - progress) < Math.abs(positions[nearest] - progress)) nearest = i; });
      active(nearest, false);
      if (fraction < 1) frame = requestAnimationFrame(tick);
      else { set(to); active(last); arc.dataset.motionRunning = 'false'; }
    }
    frame = requestAnimationFrame(tick);
  }
  measure();
  active(reducedMotion.matches ? last : 0);
  set(positions[reducedMotion.matches ? last : 0]);
  nodes.forEach((node, index) => {
    const show = () => move(index);
    const restore = () => {
      const focused = nodes.indexOf(document.activeElement);
      move(focused >= 0 ? focused : last);
    };
    node.addEventListener('pointerenter', show);
    node.addEventListener('focus', show);
    node.addEventListener('click', show);
    node.addEventListener('pointerleave', restore);
    node.addEventListener('blur', restore);
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) { flight(); observer.disconnect(); }
    }, { threshold: .2 });
    observer.observe(arc);
  } else flight();
  if ('ResizeObserver' in window) new ResizeObserver(measure).observe(arc);
  else addEventListener('resize', measure, { passive: true });
  reducedMotion.addEventListener('change', () => {
    if (reducedMotion.matches) { cancel(); played = true; set(positions[last]); active(last); }
  });
});

$$('[data-track-path]').forEach((path) => {
  const svg = path.closest('svg'), ball = $('[data-track-ball]', svg);
  const stages = $$('[data-track-stage]', svg).sort((a, b) => Number(a.dataset.trackStage) - Number(b.dataset.trackStage));
  if (!ball || !stages.length) return;
  let positions = [], intervals = [], elapsed = 0, started = 0, frame = 0, inView = false;
  const lap = 12000, pause = 450;
  function measure() {
    positions = stages.map((stage, index) => closestOnPath(path, stage, stage.dataset.trackProgress) ?? index / stages.length);
    let start = 0;
    intervals = positions.map((position, index) => {
      const next = positions[(index + 1) % positions.length];
      const distance = (next - position + 1) % 1;
      const duration = pause + distance * (lap - pause * positions.length);
      const interval = { start, duration, from: position, distance };
      start += duration;
      return interval;
    });
    if (reducedMotion.matches) {
      placeBall(path, ball, positions[positions.length - 1]);
      svg.dataset.trackProgress = positions[positions.length - 1].toFixed(4);
    }
  }
  function mark(index, all = false) {
    stages.forEach((stage, i) => stage.classList.toggle('is-active', all || i === index));
    svg.dataset.activeStage = String(index);
  }
  function stop() {
    cancelAnimationFrame(frame);
    svg.dataset.motionRunning = 'false';
  }
  function draw(now) {
    if (!inView || document.hidden || reducedMotion.matches) { stop(); return; }
    elapsed = (now - started) % lap;
    let index = intervals.length - 1;
    for (let i = 0; i < intervals.length; i++) if (elapsed < intervals[i].start + intervals[i].duration) { index = i; break; }
    const interval = intervals[index];
    const fraction = Math.max(0, Math.min(1, (elapsed - interval.start - pause) / (interval.duration - pause)));
    const progress = (interval.from + interval.distance * fraction) % 1;
    placeBall(path, ball, progress);
    mark(index);
    svg.dataset.trackProgress = progress.toFixed(4);
    frame = requestAnimationFrame(draw);
  }
  function start() {
    stop();
    if (reducedMotion.matches) {
      const last = positions.length - 1;
      placeBall(path, ball, positions[last]);
      svg.dataset.trackProgress = positions[last].toFixed(4);
      mark(last, true);
      return;
    }
    if (!inView || document.hidden) return;
    started = performance.now() - elapsed;
    svg.dataset.motionRunning = 'true';
    frame = requestAnimationFrame(draw);
  }
  measure();
  placeBall(path, ball, positions[0]);
  mark(0);
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      inView = entries.some((entry) => entry.isIntersecting);
      start();
    }, { threshold: .15 });
    observer.observe(svg);
  } else { inView = true; start(); }
  if ('ResizeObserver' in window) new ResizeObserver(measure).observe(svg);
  document.addEventListener('visibilitychange', start);
  reducedMotion.addEventListener('change', start);
  if (reducedMotion.matches) start();
});

$$('[data-renderer-compare]').forEach((compare) => {
  const range = $('[data-compare-range]', compare);
  if (!range) return;
  function update() {
    const value = Math.max(0, Math.min(100, Number(range.value)));
    compare.style.setProperty('--compare', value + '%');
    compare.dataset.comparePosition = String(value);
    const left = range.dataset.leftLabel || '', right = range.dataset.rightLabel || '';
    range.setAttribute('aria-valuetext', `${left} ${Math.round(value)}%; ${right} ${Math.round(100 - value)}%`.trim());
  }
  range.addEventListener('input', update);
  range.addEventListener('change', update);
  update();
});

const docsSelect = $('[data-docs-select]');
const tocLinks = $$('.docs-toc a[href^="#"]');
if (docsSelect || tocLinks.length) {
  const targets = tocLinks.map((link) => document.getElementById(link.hash.slice(1))).filter(Boolean);
  let queued = false;
  function spy() {
    queued = false;
    let active = targets[0];
    const padding = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
    for (const target of targets) {
      const margin = parseFloat(getComputedStyle(target).scrollMarginTop) || 0;
      if (target.getBoundingClientRect().top <= Math.max(150, padding + margin + 1)) active = target;
    }
    if (!active) return;
    tocLinks.forEach((link) => {
      const on = link.hash === '#' + active.id;
      link.classList.toggle('active', on);
      if (on) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    if (docsSelect) docsSelect.value = active.id;
  }
  docsSelect?.addEventListener('change', () => {
    const target = document.getElementById(docsSelect.value);
    if (!target) return;
    history.replaceState(null, '', '#' + target.id);
    target.scrollIntoView({ block: 'start', behavior: reducedMotion.matches ? 'instant' : 'smooth' });
  });
  addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(spy); } }, { passive: true });
  addEventListener('resize', spy, { passive: true });
  spy();
}

const resultsFilters = $$('select[data-results-filter]');
if (resultsFilters.length) {
  const rows = $$('tr[data-match-id], [data-heat-row]');
  function filterMatches() {
    const values = Object.fromEntries(resultsFilters.map((filter) => [filter.dataset.resultsFilter, filter.value]));
    let count = 0;
    rows.forEach((row) => {
      const sport = !values.sport || values.sport === 'all' || row.dataset.sport === values.sport;
      const model = !values.model || values.model === 'all' || (row.dataset.models || '').split(/\s+/).includes(values.model);
      row.hidden = !(sport && model);
      if (!row.hidden) count++;
    });
    $$('[data-results-count]').forEach((counter) => {
      counter.textContent = (counter.dataset.countFormat || '{n}').replace('{n}', String(count));
    });
    $$('[data-results-empty]').forEach((empty) => { empty.hidden = count > 0; });
    dispatchEvent(new Event('eaofilterchange'));
  }
  resultsFilters.forEach((filter) => filter.addEventListener('change', filterMatches));
  function showEvent(sport) {
    const sportFilter = resultsFilters.find((filter) => filter.dataset.resultsFilter === 'sport');
    if (!sportFilter || ![...sportFilter.options].some((option) => option.value === sport)) return;
    resultsFilters.forEach((filter) => { filter.value = filter.dataset.resultsFilter === 'sport' ? sport : 'all'; });
    filterMatches();
    document.getElementById('matches')?.scrollIntoView({ block: 'start', behavior: reducedMotion.matches ? 'instant' : 'smooth' });
  }
  $$('[data-event-filter]').forEach((link) => link.addEventListener('click', (event) => {
    event.preventDefault();
    showEvent(link.dataset.eventFilter);
    history.replaceState(null, '', '#matches');
  }));
  function eventFromHash() {
    if (!location.hash.startsWith('#event-')) return;
    try { showEvent(decodeURIComponent(location.hash.slice(7))); } catch (_) { /* Ignore an incomplete fragment. */ }
  }
  addEventListener('hashchange', eventFromHash);
  filterMatches();
  eventFromHash();
}

const replayModal = $('[data-replay-modal]');
if (replayModal) {
  const video = $('[data-replay-video]', replayModal), title = $('[data-replay-title]', replayModal);
  const caption = $('[data-replay-caption]', replayModal), meta = $('[data-replay-meta]', replayModal);
  let returnFocus = null, previousHash = '', current = '';
  function closeReplay() {
    if (!replayModal.open) return;
    replayModal.close();
  }
  function openReplay(id, trigger = null, userTriggered = false) {
    const data = $$('template[data-replay-data]').find((template) => template.dataset.replayData === id);
    if (!data?.dataset.src || !video) return;
    if (replayModal.open && current === id) return;
    if (!replayModal.open) {
      returnFocus = trigger || document.activeElement;
      previousHash = location.hash.startsWith('#match-') ? '#matches' : location.hash;
    }
    window.eaoSetVideoSource(video, {
      src: data.dataset.src, poster: data.dataset.poster,
      width: data.dataset.width, height: data.dataset.height,
    });
    if (title) title.textContent = data.dataset.title || '';
    if (data.dataset.title) video.setAttribute('aria-label', data.dataset.title);
    const score = $('.scorebug', data.content), detail = $('.match-meta', data.content);
    if (caption) caption.replaceChildren(...(score ? [score.cloneNode(true)] : []));
    if (meta) meta.replaceChildren(...(detail ? [detail.cloneNode(true)] : []));
    video.load();
    current = id;
    replayModal.dataset.currentMatch = id;
    if (!replayModal.open) replayModal.showModal();
    history.replaceState(null, '', '#match-' + encodeURIComponent(id));
    $('[data-replay-close]', replayModal)?.focus({ preventScroll: true });
    dispatchEvent(new Event('eaoreplaychange'));
    if (userTriggered) window.eaoPlayVideo?.(video);
  }
  $$('[data-replay-open]').forEach((button) => button.addEventListener('click', (event) => {
    event.preventDefault();
    openReplay(button.dataset.replayOpen, button, event.isTrusted);
  }));
  $$('[data-replay-close]', replayModal).forEach((button) => button.addEventListener('click', closeReplay));
  replayModal.addEventListener('cancel', (event) => { event.preventDefault(); closeReplay(); });
  // Native video controls keep their own tab order; restore the dialog boundary
  // when that order reaches browser chrome, without skipping any player control.
  function retainReplayFocus() {
    if (replayModal.open && !replayModal.contains(document.activeElement)) {
      $('[data-replay-close]', replayModal)?.focus({ preventScroll: true });
    }
  }
  replayModal.addEventListener('focusout', () => setTimeout(retainReplayFocus, 0));
  document.addEventListener('focusin', retainReplayFocus);
  document.addEventListener('keydown', (event) => {
    if (replayModal.open && event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      closeReplay();
    }
  }, true);
  replayModal.addEventListener('close', () => {
    video?.pause();
    video?.removeAttribute('src');
    video?.removeAttribute('poster');
    video?.load();
    if (location.hash.startsWith('#match-')) history.replaceState(null, '', location.pathname + location.search + previousHash);
    current = '';
    delete replayModal.dataset.currentMatch;
    if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
    dispatchEvent(new Event('eaoreplaychange'));
  });
  replayModal.addEventListener('click', (event) => {
    if (event.target !== replayModal) return;
    const rect = replayModal.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeReplay();
  });
  replayModal.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') { event.preventDefault(); closeReplay(); return; }
    if (event.key !== 'Tab') return;
    const focusable = $$('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), video[controls], [tabindex="0"]', replayModal).filter((node) => node.getClientRects().length && !node.hidden);
    if (!focusable.length) { event.preventDefault(); return; }
    // Native modal focus navigation preserves the video controls' own tab order.
    if (focusable.some((node) => node.tagName === 'VIDEO')) return;
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  function fromHash() {
    if (!location.hash.startsWith('#match-')) { closeReplay(); return; }
    try { openReplay(decodeURIComponent(location.hash.slice(7))); } catch (_) { /* Ignore an incomplete fragment. */ }
  }
  addEventListener('hashchange', fromHash);
  fromHash();
}

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
    if ($$('[data-replay-modal]:not([open]) video').some((clip) => !clip.paused)) failures.push('closed replay is playing');
    if (reducedMotion.matches && $$('[data-intelligence-arc], [data-three-intelligences], svg:has([data-track-path])').some((diagram) => diagram.dataset.motionRunning === 'true')) failures.push('diagram motion with reduced motion');
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
        intelligenceNodes: $$('.intelligence-chain [data-hint], [data-intelligence-chain] [data-hint], [data-intelligence-arc] [data-arc-step]').length,
        controlSteps: $$('.control-chain [data-step]').length,
        podiums: $$('.podium, .podium-card, [data-podium]').length,
        modeToggles: $$('[data-mode-toggle]').length,
        viewToggles: $$('[data-view-toggle]').length,
        matchWallTiles: $$('[data-match-wall] video').length,
        heatRows: $$('tr[data-match-id], [data-heat-row]').length,
        visibleHeatRows: $$('tr[data-match-id]:not([hidden]), [data-heat-row]:not([hidden])').length,
        replayTemplates: $$('template[data-replay-data]').length,
        replayModals: $$('[data-replay-modal]').length,
        openReplayModals: $$('[data-replay-modal][open]').length,
        rendererCompares: $$('[data-renderer-compare]').length,
        docsSections: tocLinks.length,
        intelligenceArcs: $$('[data-intelligence-arc]').length,
        tracks: $$('[data-track-path]').length,
        controlRooms: $$('[data-control-room]').length,
        controlChannels: $$('[data-control-channel]').length,
        availableControlChannels: $$('[data-control-channel]:not(.is-dim)').length,
        threeIntelligences: $$('[data-three-intelligences]').length,
        intelligenceGroups: $$('[data-intelligence-group]').length,
      },
      controlRooms: $$('[data-control-room]').map((room) => room.eaoStatus?.()).filter(Boolean),
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
  addEventListener('eaoreplaychange', () => selftest());
}
