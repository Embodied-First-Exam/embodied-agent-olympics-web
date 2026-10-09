// One playback budget for the whole page, including native-control clips.
const videos = [...document.querySelectorAll('video')];
const motion = matchMedia('(prefers-reduced-motion: reduce)');
const pointer = matchMedia('(pointer: coarse)');
const states = new Map();
let scheduled = false;

const isTouch = () => pointer.matches || navigator.maxTouchPoints > 0;
const budget = () => isTouch() ? 2 : 4;
const frameOf = (video) => video.closest('.media-frame, .media, .frame') || video.parentElement;
const isHidden = (video) => !!video.closest('[hidden], .is-dim') || getComputedStyle(video).display === 'none';

function syncControls(state) {
  const playing = !state.video.paused && !state.video.ended;
  state.frame?.classList.toggle('is-playing', playing);
  state.frame?.classList.toggle('is-paused', !playing);
  state.frame?.classList.toggle('controls-visible', state.video.controls && (!playing || state.hovered || state.focused));
  if (state.heroControl) {
    const label = playing ? state.heroControl.dataset.pauseLabel : state.heroControl.dataset.playLabel;
    if (label) state.heroControl.setAttribute('aria-label', label);
    state.heroControl.setAttribute('aria-pressed', String(playing));
    const playIcon = state.heroControl.querySelector('[data-play-icon]');
    const pauseIcon = state.heroControl.querySelector('[data-pause-icon]');
    if (playIcon) playIcon.hidden = playing;
    if (pauseIcon) pauseIcon.hidden = !playing;
  }
}

function showButton(state, show) {
  syncControls(state);
  if (!state.button) return;
  state.button.hidden = !show;
  state.button.setAttribute('aria-pressed', String(!state.video.paused));
}

function stop(state) {
  state.wanted = false;
  state.explicit = false;
  if (!state.video.paused) state.video.pause();
  clearTimeout(state.captionTimer);
  state.frame?.classList.remove('caption-faded');
  showButton(state, motion.matches || state.blocked);
}

function fadeCaption(state) {
  clearTimeout(state.captionTimer);
  state.started = performance.now();
  state.frame?.classList.remove('caption-faded');
  state.captionTimer = setTimeout(() => {
    if (!state.hovered && !state.focused && !state.video.paused) state.frame?.classList.add('caption-faded');
  }, 3000);
}

function start(state, explicit = false) {
  state.wanted = true;
  if (explicit) {
    state.explicit = true;
    state.blocked = false;
    state.userPaused = false;
  }
  if (!state.video.paused || state.pending) return;
  state.pending = true;
  const request = ++state.playRequest;
  let promise;
  try { promise = state.video.play(); }
  catch (_) {
    state.pending = false;
    state.blocked = true;
    state.explicit = false;
    showButton(state, true);
    return;
  }
  Promise.resolve(promise).then(() => {
    if (request !== state.playRequest) return;
    state.pending = false;
    if (!state.wanted) state.video.pause();
    else showButton(state, false);
  }).catch(() => {
    if (request !== state.playRequest) return;
    state.pending = false;
    if (state.wanted && state.video.paused) {
      state.blocked = true;
      state.explicit = false;
      showButton(state, true);
    }
  });
}

function distance(state) {
  const box = state.video.getBoundingClientRect();
  return Math.abs(box.top + box.height / 2 - innerHeight / 2);
}

function visible(state) {
  if (isHidden(state.video)) return false;
  const modal = document.querySelector('[data-replay-modal][open]');
  if (modal && !modal.contains(state.video)) return false;
  const box = state.video.getBoundingClientRect();
  return box.bottom > 0 && box.top < innerHeight && box.right > 0 && box.left < innerWidth;
}

function reconcile() {
  scheduled = false;
  const touch = isTouch();
  const all = [...states.values()];
  const explicit = all.filter((s) => s.explicit && visible(s));
  // A deliberate click takes priority over decorative autoplay.
  explicit.sort((a, b) => b.clicked - a.clicked);
  const selected = [];
  let explicitCards = 0;
  for (const state of explicit) {
    if (selected.length >= budget()) break;
    if (state.kind === 'inview' && explicitCards >= (touch ? 2 : 4)) continue;
    selected.push(state);
    if (state.kind === 'inview') explicitCards++;
  }
  if (!motion.matches && !document.hidden) {
    const candidates = all.filter((s) => {
      if (selected.includes(s) || s.blocked || s.userPaused || !visible(s)) return false;
      if (s.kind === 'manual') return false;
      if (s.kind === 'control-room') return s.ratio >= .35 && !s.video.ended;
      if (s.kind === 'hero') return s.ratio >= .15;
      if (s.kind === 'hover' || s.kind === 'wall') return touch ? s.ratio >= .25 : s.hovered || s.focused;
      return s.ratio >= .35;
    });
    candidates.sort((a, b) => {
      if (touch) return distance(a) - distance(b);
      const priority = (s) => ['hero', 'control-room'].includes(s.kind) ? 0 : (s.kind === 'hover' || s.kind === 'wall') ? 1 : 2;
      return priority(a) - priority(b) || distance(a) - distance(b);
    });
    let cards = selected.filter((s) => s.kind === 'inview').length;
    for (const state of candidates) {
      if (selected.length >= budget()) break;
      if (state.kind === 'inview' && cards >= (touch ? 2 : 4)) continue;
      selected.push(state);
      if (state.kind === 'inview') cards++;
    }
  }
  if (document.hidden) selected.length = 0;
  // Pause before starting another clip, so the cap holds during handovers.
  for (const state of all) if (!selected.includes(state)) stop(state);
  for (const state of selected) start(state, state.explicit);
}

function schedule() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(reconcile);
}

for (const video of videos) {
  const frame = frameOf(video);
  const interaction = frame?.closest('a, button') || frame;
  const state = {
    video, frame, kind: video.dataset.video || (video.controls ? 'manual' : 'inview'),
    button: frame?.querySelector('[data-video-play]'), ratio: 0,
    heroControl: frame?.querySelector('[data-hero-control]'), userPaused: false,
    hovered: false, focused: false, wanted: false, explicit: false,
    pending: false, blocked: false, clicked: 0, started: 0, captionTimer: null,
    playRequest: 0,
  };
  states.set(video, state);
  video.muted = true;
  video.defaultMuted = true;
  video.playsInline = true;
  video.setAttribute('playsinline', '');
  video.preload = state.kind === 'hero' && !motion.matches ? 'auto' : 'none';
  // The scheduler also handles the hero's declarative autoplay attribute.
  video.removeAttribute('autoplay');
  if (!video.paused) video.pause();
  showButton(state, motion.matches);
  state.button?.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (!video.paused) {
      state.userPaused = true;
      stop(state);
      showButton(state, true);
    } else {
      state.explicit = true;
      state.blocked = false;
      state.userPaused = false;
      state.clicked = performance.now();
      reconcile();
    }
  });
  state.heroControl?.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (!video.paused) {
      state.userPaused = true;
      stop(state);
    } else {
      state.userPaused = false;
      state.explicit = true;
      state.blocked = false;
      state.clicked = performance.now();
      reconcile();
    }
  });
  interaction?.addEventListener('pointerenter', () => {
    state.hovered = true;
    frame.classList.remove('caption-faded');
    syncControls(state);
    schedule();
  });
  interaction?.addEventListener('pointerleave', () => {
    state.hovered = false;
    syncControls(state);
    if (!state.focused && !video.paused && performance.now() - state.started >= 3000) frame.classList.add('caption-faded');
    schedule();
  });
  interaction?.addEventListener('focusin', () => {
    state.focused = true;
    frame.classList.remove('caption-faded');
    syncControls(state);
    schedule();
  });
  interaction?.addEventListener('focusout', (event) => {
    state.focused = interaction.contains(event.relatedTarget);
    syncControls(state);
    if (!state.focused && !state.hovered && !video.paused && performance.now() - state.started >= 3000) frame.classList.add('caption-faded');
    schedule();
  });
  video.addEventListener('play', () => {
    if (!state.wanted) {
      state.explicit = true;
      state.wanted = true;
      state.clicked = performance.now();
    }
    // Native controls enter through this path, and consume the same budget.
    reconcile();
    showButton(state, false);
  });
  video.addEventListener('playing', () => { syncControls(state); fadeCaption(state); });
  video.addEventListener('pause', () => {
    clearTimeout(state.captionTimer);
    frame?.classList.remove('caption-faded');
    if (state.explicit && video.paused) state.explicit = false;
    showButton(state, motion.matches || state.blocked);
  });
  video.addEventListener('ended', () => {
    state.explicit = false;
    state.wanted = false;
    schedule();
  });
  video.addEventListener('emptied', schedule);
}

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) states.get(entry.target).ratio = entry.intersectionRatio;
    schedule();
  }, { threshold: [0, .15, .25, .35, .6, 1] });
  videos.forEach((video) => observer.observe(video));
} else {
  states.forEach((state) => { state.ratio = 1; });
}
addEventListener('scroll', schedule, { passive: true });
addEventListener('resize', schedule, { passive: true });
addEventListener('eaofilterchange', schedule);
addEventListener('eaoviewchange', schedule);
addEventListener('eaoreplaychange', schedule);
document.addEventListener('visibilitychange', schedule);
pointer.addEventListener('change', schedule);
motion.addEventListener('change', () => {
  states.forEach((state) => {
    state.video.preload = state.kind === 'hero' && !motion.matches ? 'auto' : 'none';
    if (motion.matches && !state.explicit) stop(state);
    showButton(state, motion.matches || state.blocked);
  });
  schedule();
});
schedule();

export function playbackStatus() {
  const playing = videos.filter((video) => !video.paused && !video.ended);
  return {
    found: videos.length,
    playing: playing.length,
    cap: budget(),
    touch: isTouch(),
    reducedMotion: motion.matches,
    cardsPlaying: playing.filter((video) => states.get(video)?.kind === 'inview').length,
    wallPlaying: playing.filter((video) => ['hover', 'wall'].includes(states.get(video)?.kind)).length,
    modalPlaying: playing.filter((video) => video.closest('[data-replay-modal]')).length,
    autoplaying: playing.filter((video) => !states.get(video)?.explicit).length,
    controlRoomPlaying: playing.filter((video) => states.get(video)?.kind === 'control-room').length,
  };
}
window.eaoPlaybackStatus = playbackStatus;
window.eaoPlayVideo = (video) => {
  const state = states.get(video);
  if (!state) return;
  state.explicit = true;
  state.userPaused = false;
  state.blocked = false;
  state.clicked = performance.now();
  reconcile();
};
window.eaoSetVideoSource = (video, source) => {
  const state = states.get(video);
  if (!state || !source?.src) return;
  // A source change invalidates the previous play promise before touching media.
  state.playRequest++;
  state.pending = false;
  state.wanted = false;
  state.explicit = false;
  state.blocked = false;
  state.userPaused = false;
  video.pause();
  video.preload = 'none';
  video.loop = false;
  video.src = source.src;
  if (source.poster) video.poster = source.poster;
  else video.removeAttribute('poster');
  if (source.width) video.width = Number(source.width);
  if (source.height) video.height = Number(source.height);
  state.frame?.classList.remove('caption-faded');
  showButton(state, motion.matches);
  if (source.explicit) window.eaoPlayVideo(video);
  else schedule();
};
