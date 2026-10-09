import * as THREE from '../../vendor/three/three.module.js';
import { createStage } from './stage.js';
import { loadReplay, createReplay } from './replay.js';
import { createCameraRig } from './cameras.js';
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;
const WINDOWS = { kicker: [null, null, 0.10, 0.14], cue: [null, null, 0.02, 0.04], l1: [0.01, 0.04, 0.11, 0.14], l2: [0.15, 0.18, 0.30, 0.335], l3: [0.35, 0.38, 0.515, 0.555], l4: [0.58, 0.61, 0.72, 0.76], title: [0.76, 0.88, 9, 9] };
// Eye and target in the exported y-up frame. The camera moves; the recorded geometry never changes.
const CAMERA = [
  { s: 0.00, eye: [1.40, 0.32, 0.65], look: [-0.25, 0.26, -1.40], fov: 28 },
  { s: 0.13, eye: [1.35, 0.34, 0.72], look: [-0.25, 0.28, -1.40], fov: 24 },
  { s: 0.14, eye: [3.10, 0.65, 0.50], look: [0.0, 0.27, 0.0], fov: 53 },
  { s: 0.30, eye: [3.1, 1.6, 1.05], look: [0.0, 0.19, 0.0], fov: 48 },
  { s: 0.36, eye: [-6.10, 3.20, 5.30], look: [-1.25, 0.46, 0.25], fov: 44 },
  { s: 0.54, eye: [-5.80, 3.05, 5.50], look: [-1.20, 0.46, 0.20], fov: 44 },
  { s: 0.61, eye: [2.7, 0.55, 0.65], look: [0.0, 0.23, 0.0], fov: 52 },
  { s: 0.73, eye: [2.9, 0.65, -0.35], look: [0.0, 0.23, 0.0], fov: 52 },
  { s: 0.80, eye: [3.3, 2.5, 4.0], look: [0.0, 0.1, 0.0], fov: 42 },
  { s: 1.00, eye: [2.70, 3.25, 3.30], look: [0.0, 0.05, 0.0], fov: 34 },
];
const fmt = t => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
const fromMJ = a => [a[0], a[2], -a[1]];
function retainSelftest(callback) {
  new MutationObserver(() => {
    try { if (!JSON.parse(document.body.dataset.selftest || '{}').opening) callback(); } catch { callback(); }
  }).observe(document.body, { attributes: true, attributeFilter: ['data-selftest'] });
}
function cameraFrom(def, width, height) {
  const c = new THREE.PerspectiveCamera(def.fovy_deg ?? def.fovy ?? 45, width / height, 0.01, 50);
  const y = def.y_up ?? def.yup;
  c.position.fromArray(y?.pos ?? fromMJ(def.pos));
  c.up.fromArray(y?.up ?? fromMJ(def.up ?? [0, 0, 1]));
  c.lookAt(new THREE.Vector3().fromArray(y?.lookat ?? fromMJ(def.lookat)));
  c.updateMatrixWorld(true); return c;
}
function containExit(section) {
  const sticky = section.querySelector('.eao-opening-sticky');
  const copy = section.querySelector('.eao-opening-copy');
  const nav = document.querySelector('.nav');
  const update = () => {
    // Scroll progress clamps at 1 before the sticky stage leaves. Use its real
    // viewport position, independently of replay easing and render scheduling.
    const top = sticky.getBoundingClientRect().top, released = Math.max(0, -top);
    const staticMode = section.matches('.is-overview, .is-fallback');
    // Portrait content leaves with the stage. Fading it at the start of the
    // release otherwise leaves almost a viewport of paper before the statement.
    const phone = matchMedia('(max-width: 760px), (pointer: coarse) and (max-aspect-ratio: 4/5)').matches;
    const alpha = staticMode || phone ? 1 : 1 - smooth(0, Math.min(96, innerHeight * 0.12), released);
    const clipTop = released && nav ? Math.max(0, nav.getBoundingClientRect().bottom + 8 - top) : 0;
    section.style.setProperty('--opening-exit-opacity', alpha.toFixed(4));
    sticky.style.setProperty('--opening-exit-clip', `${clipTop.toFixed(2)}px`);
    copy.inert = alpha < 0.001;
  };
  addEventListener('scroll', update, { passive: true });
  addEventListener('resize', update, { passive: true });
  new MutationObserver(update).observe(section, { attributes: true, attributeFilter: ['class'] });
  update();
}
function fallback(section, motionPreference = matchMedia('(prefers-reduced-motion: reduce)')) {
  section.classList.add('is-fallback', 'is-overview');
  section.querySelector('#opening-fallback').hidden = false;
  section.querySelector('#opening-canvas').hidden = true;
  const video = section.querySelector('#opening-fallback-video');
  if (video && !video.dataset.openingFallbackBound) {
    video.dataset.openingFallbackBound = 'true';
    let explicit = false, automaticRequest = false, playRequest = 0;
    const play = video.play.bind(video);
    // Native media controls bypass this instance method. Flag every JS start,
    // including the manager's scheduled starts, before its play event arrives.
    video.play = (...args) => {
      const request = ++playRequest;
      automaticRequest = true;
      const clear = () => { if (request === playRequest) automaticRequest = false; };
      try {
        const promise = play(...args);
        Promise.resolve(promise).then(clear, clear);
        return promise;
      } catch (error) { clear(); throw error; }
    };
    const managed = () => typeof window.eaoPlaybackStatus === 'function';
    const poster = () => {
      video.pause(); video.preload = 'none'; video.load();
      video.dataset.playbackIntent = 'paused';
    };
    const reconcile = () => {
      if (managed()) {
        // The reel is idle/manual while WebGL works. Request automatic
        // scheduling only for visible fallback, within the manager's budget.
        if (typeof window.eaoStartAutomaticVideo === 'function') window.eaoStartAutomaticVideo(video);
        else dispatchEvent(new Event('eaoviewchange'));
        if (motionPreference.matches) requestAnimationFrame(() => {
          if (motionPreference.matches && video.paused) poster();
        });
        return;
      }
      if (motionPreference.matches) {
        if (!explicit) poster();
        return;
      }
      if (!video.paused) return;
      explicit = false; automaticRequest = true; video.dataset.playbackIntent = 'automatic';
      video.preload = 'auto';
      video.play().then(() => {
        if (motionPreference.matches && !explicit) poster();
      }).catch(() => { automaticRequest = false; });
    };
    const userStart = event => {
      if (event.isTrusted && video.paused) { explicit = true; video.dataset.playbackIntent = 'explicit'; }
    };
    video.addEventListener('pointerdown', userStart, true);
    video.addEventListener('keydown', event => {
      if ([' ', 'Enter', 'k', 'MediaPlayPause'].includes(event.key)) userStart(event);
    }, true);
    video.addEventListener('play', () => {
      // Chrome's native controls can consume their pointer event inside the
      // user-agent shadow tree. A native play still carries user activation;
      // our own guarded automatic request never becomes an explicit start.
      if (!video.paused && !automaticRequest && navigator.userActivation?.isActive) {
        explicit = true;
        // Bridge the native UA control before C1's bubbling play listener.
        // This is a deliberate user start and still consumes its shared budget.
        if (managed()) window.eaoPlayVideo?.(video);
      }
      automaticRequest = false;
      video.dataset.playbackIntent = explicit ? 'explicit' : 'automatic';
    }, true);
    video.addEventListener('pause', () => {
      explicit = false; video.dataset.playbackIntent = 'paused';
    });
    // Installed here before init's early failure return, and only once even
    // if a successfully created context is later lost.
    motionPreference.addEventListener('change', reconcile);
    reconcile();
  }
  if (new URLSearchParams(location.search).has('selftest')) {
    const report = () => { let data = {}; try { data = JSON.parse(document.body.dataset.selftest || '{}'); } catch {} document.body.dataset.selftest = JSON.stringify({ ...data, opening: { ready: true, webgl: false, fallback: true } }); };
    report(); retainSelftest(report);
  }
}
export async function initOpening(section = document.getElementById('opening')) {
  if (!section) return null;
  containExit(section);
  const canvas = section.querySelector('#opening-canvas'), params = new URLSearchParams(location.search);
  const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
  let reduced = motionPreference.matches;
  const coarse = matchMedia('(pointer: coarse)').matches;
  const freezeValue = params.has('hero') ? Number(params.get('hero')) : null;
  const frozen = freezeValue != null && Number.isFinite(freezeValue) ? clamp(freezeValue) : null;
  let overview = params.get('overview') === '1' || reduced;
  if (overview) section.classList.add('is-overview');
  let stage;
  try { stage = createStage(canvas, { span: 2.4, cell: 0.1, every: 5, coarse, maxDpr: coarse ? 1.5 : 1.25 }); }
  catch { fallback(section, motionPreference); return null; }
  const { scene, camera, renderer } = stage;
  camera.near = 0.1;
  stage.floor.position.y = -0.76; stage.grid.position.y = -0.7595;
  let replay;
  try { replay = createReplay(await loadReplay()); } catch (error) { console.error(error); fallback(section, motionPreference); return null; }
  stage.root.add(replay.root);
  const meta = replay.meta, duration = (replay.frames - 1) / meta.fps;
  const seats = Object.keys(meta.score_timeline[0].score);
  section.querySelectorAll('[data-opening-seat]').forEach((el, i) => { const label = el.querySelector('[data-opening-seat-label]'); if (!label.textContent.trim()) label.textContent = seats[i]; });
  section.dataset.openingScoreLabels = 'recorded';
  const playerDefs = meta.cameras_a;
  const playerCameras = playerDefs.map(d => cameraFrom(d.source, d.width ?? 480, d.height ?? 360));
  const cameraRig = createCameraRig(playerCameras), helpers = cameraRig.group;
  scene.add(helpers);
  const copy = [...section.querySelectorAll('[data-opening]')].filter(e => WINDOWS[e.dataset.opening]).map(el => ({ el, w: WINDOWS[el.dataset.opening] }));
  const hud = { shot: section.querySelector('#opening-shot'), clock: section.querySelector('#opening-clock'), bar: section.querySelector('#opening-progress'), a: section.querySelector('#opening-score-a'), b: section.querySelector('#opening-score-b') };
  const scorebug = section.querySelector('#opening-score'), inset = section.querySelector('#opening-inset'), insetCanvas = section.querySelector('#opening-inset-canvas');
  const override = params.get('cam')?.split(',').map(Number);
  let shown = overview ? 1 : frozen ?? 0, visible = true, running = false, dirty = true, loopStart = null, previous = performance.now();
  let testActive = false, readyAt = 0, forcedProgress = null, lastTick = performance.now();
  const renderTimes = [], rafTimes = [];
  let scoreFrame = null, scoreTotal = 0, pulseTimer;
  const eye = new THREE.Vector3(), look = new THREE.Vector3(), ball = new THREE.Vector3();
  // Give the first ball beat time to read, then reach the same B strike before
  // S1 ends. Match time remains monotonic; S4 retains its half-speed interval.
  const timeAt = s => duration * (s <= 0.04 ? 0.3 * s : s <= 0.14 ? 0.012 + 1.56 * (s - 0.04) : s <= 0.56 ? s + 0.028 : s <= 0.76 ? 0.588 + (s - 0.56) * 0.5 : 0.688 + s - 0.76) / 0.928;
  const pointStarts = meta.point_starts ?? meta.pointStarts ?? [];
  const finalStart = typeof pointStarts.at(-1) === 'number' ? pointStarts.at(-1) : pointStarts.at(-1)?.launch_frame ?? pointStarts.at(-1)?.frame ?? Math.round(replay.frames * 0.55);
  function progress() {
    if (overview) return 1;
    if (forcedProgress != null) return forcedProgress;
    if (frozen != null) return frozen;
    const r = section.getBoundingClientRect();
    return clamp(-r.top / Math.max(1, section.offsetHeight - innerHeight));
  }
  function setCamera(s, driftTime = 0) {
    let i = CAMERA.findIndex(c => c.s > s); if (i < 0) i = CAMERA.length - 1;
    const a = CAMERA[Math.max(0, i - 1)], b = CAMERA[i], u = a === b ? 1 : smooth(a.s, b.s, s);
    eye.fromArray(a.eye).lerp(new THREE.Vector3(...b.eye), u); look.fromArray(a.look).lerp(new THREE.Vector3(...b.look), u);
    const wide = camera.aspect > 1.2, reveal = smooth(0.76, 1, s);
    if (s > 0.56 && s < 0.76) {
      replay.ball.getWorldPosition(ball);
      if (ball.y > -0.3) { ball.x = clamp(ball.x, -0.8, 0.8); ball.y = clamp(ball.y, 0.12, 0.6); ball.z = clamp(ball.z, -1.4, 1.4); look.lerp(ball, 0.22 * Math.sin((s - 0.56) / 0.2 * Math.PI)); }
    }
    const portraitScreen = camera.aspect < 0.8;
    const desktopCameras = wide ? smooth(0.31, 0.36, s) * (1 - smooth(0.54, 0.58, s)) : 0;
    const side2 = portraitScreen ? smooth(0.13, 0.14, s) * (1 - smooth(0.31, 0.36, s)) : 0;
    const side4 = portraitScreen ? smooth(0.56, 0.61, s) * (1 - smooth(0.73, 0.80, s)) : 0;
    const sideAmount = side2 + side4;
    const portraitReveal = smooth(0.73,0.80,s);
    // Portrait broadcast angles keep depth in the table and a large foreground arm.
    eye.lerp(new THREE.Vector3(1.3, 1.5, 3.4), side2);
    eye.lerp(new THREE.Vector3(1.6, 0.72, 3.4), side4);
    const portraitBase = wide ? 1 : Math.min(2.85, Math.max(1, lerp(0.78,1.30,portraitReveal) / camera.aspect));
    const portrait = lerp(portraitBase, 1.55, sideAmount);
    eye.sub(look).multiplyScalar(portrait).add(look);
    camera.fov = lerp(a.fov, b.fov, u) + 4 * sideAmount;
    if (portraitScreen && s < 0.14) {
      const close = 1 - smooth(0.13, 0.14, s);
      eye.lerp(new THREE.Vector3(1.70, 0.34, 0.65), close);
      const firstBeat = 1 - smooth(0.04, 0.07, s);
      look.lerp(new THREE.Vector3(-0.10 * firstBeat, 0.29, -1.30 + 0.05 * firstBeat), close);
      camera.fov = lerp(camera.fov, 49, close);
    }
    const cameraShot = portraitScreen ? smooth(0.34,0.38,s) * (1 - smooth(0.52,0.56,s)) : 0;
    if (cameraShot) {
      eye.lerp(new THREE.Vector3(1.03,4.15,7.31),cameraShot);
      look.lerp(new THREE.Vector3(-1.0,0.50,0.0),cameraShot);
      camera.fov = lerp(camera.fov,65,cameraShot);
    }
    camera.fov -= 6 * desktopCameras;
    if (driftTime && !reduced && !override) eye.sub(look).applyAxisAngle(new THREE.Vector3(0,1,0), Math.sin(driftTime / 9000) * 0.035).add(look);
    if (override?.length >= 6 && override.every(Number.isFinite)) { eye.fromArray(override); look.fromArray(override.slice(3)); camera.fov = override[6] ?? camera.fov; }
    camera.position.copy(eye); camera.lookAt(look);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    const lateralReveal = smooth(0.73, 0.80, s);
    const shift = override ? 0 : wide ? w * (0.025 * (1 - lateralReveal) + 0.225 * lateralReveal) * (1 - desktopCameras) : w * 0.10 * cameraShot;
    const rise = override ? 0 : wide ? h * lerp(0.055 * (1 - reveal) + 0.025 * reveal, 0.025, desktopCameras) : h * (0.08 + 0.08 * smooth(0.13,0.18,s) + 0.085 * portraitReveal);
    if (shift || rise) camera.setViewOffset(w, h, -shift, rise, w, h); else camera.clearViewOffset();
    camera.updateProjectionMatrix(); camera.updateMatrixWorld(true);
    cameraRig.resize(w,h);
  }
  function updateCopy(s, f) {
    for (const c of copy) {
      const alpha = (c.w[0] == null ? 1 : smooth(c.w[0], c.w[1], s)) * (1 - smooth(c.w[2], c.w[3], s));
      c.el.style.opacity = alpha.toFixed(3); c.el.style.visibility = alpha > 0.001 ? 'visible' : 'hidden';
      c.el.style.transform = `translateY(${((1 - alpha) * 14).toFixed(1)}px)`; c.el.style.pointerEvents = alpha > 0.5 ? 'auto' : 'none';
    }
    const score = replay.score(f), contacts = meta.contact_frames ?? meta.contacts;
    hud.a.textContent = score.A; hud.b.textContent = score.B;
    const total = score.A + score.B;
    if (scoreFrame != null && f > scoreFrame && total > scoreTotal && !reduced && !testActive) {
      scorebug.classList.remove('is-point'); void scorebug.offsetWidth;
      scorebug.classList.add('is-point'); clearTimeout(pulseTimer);
      pulseTimer = setTimeout(() => scorebug.classList.remove('is-point'), 300);
    }
    scoreFrame = f; scoreTotal = total;
    const count = contacts.filter(c => (typeof c === 'number' ? c : c.frame) <= f).length;
    hud.shot.textContent = `${count} / ${contacts.length}`;
    hud.clock.textContent = `${fmt(f / meta.fps)} / ${fmt(duration)}`;
    hud.bar.style.width = `${100 * f / (replay.frames - 1)}%`;
    scorebug.style.setProperty('--opening-score-opacity', smooth(0.14, 0.18, s));
    scorebug.style.right = s > 0.76 && camera.aspect > 1.2 ? `calc(var(--gutter) + ${smooth(0.76,0.88,s) * canvas.clientWidth * 0.20}px)` : '';
    scorebug.style.left = s > 0.76 && camera.aspect < 0.8 ? 'var(--gutter)' : '';
    if (s > 0.76 && camera.aspect < 0.8) scorebug.style.right = 'auto';
    const insetAlpha = smooth(0.34, 0.38, s) * (1 - smooth(0.52, 0.56, s));
    inset.style.setProperty('--opening-inset-opacity', insetAlpha); inset.style.visibility = insetAlpha > 0.001 ? 'visible' : 'hidden';
    helpers.visible = insetAlpha > 0.02;
  }
  function render(s) {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setViewport(0, 0, w, h); renderer.setScissorTest(false); renderer.render(scene, camera);
    if (s > 0.34 && s < 0.56) {
      const r = insetCanvas.getBoundingClientRect(), base = canvas.getBoundingClientRect();
      helpers.visible = false; stage.grid.visible = false; replay.trail.visible = false;
      const x = r.left - base.left, y = h - (r.bottom - base.top);
      // A player's native 4:3 image fits the required 16:9 screen without changing its intrinsics.
      const iw = r.height * 4 / 3, pad = (r.width - iw) / 2;
      const background = scene.background; scene.background = new THREE.Color('#0f141a');
      renderer.setScissorTest(true); renderer.setScissor(x, y, r.width, r.height); renderer.setViewport(x, y, r.width, r.height); renderer.clear(true, true, false);
      scene.background = background;
      renderer.setScissor(x + pad, y, iw, r.height); renderer.setViewport(x + pad, y, iw, r.height); renderer.clearDepth();
      renderer.render(scene, playerCameras[0]);
      const ctx = insetCanvas.getContext('2d'), dpr = renderer.getPixelRatio();
      ctx.drawImage(canvas, x * dpr, (r.top - base.top) * dpr, r.width * dpr, r.height * dpr, 0, 0, insetCanvas.width, insetCanvas.height);
      renderer.setScissorTest(false); renderer.setViewport(0, 0, w, h);
      helpers.visible = true; stage.grid.visible = true; replay.updateTrail(reduced);
    }
  }
  function draw(now = performance.now(), force = false) {
    if (testActive || section.classList.contains('is-fallback')) return;
    const target = progress(), before = shown;
    const easing = 1 - Math.exp(-Math.min(100, Math.max(0, now - lastTick)) * 0.009); lastTick = now;
    shown = frozen != null || overview ? target : shown + (target - shown) * easing;
    if (Math.abs(target - shown) < 0.0001) shown = target;
    const looping = shown >= 0.9999 && frozen == null && !reduced;
    if (!looping) loopStart = null;
    let f = timeAt(shown) * meta.fps;
    if (looping) {
      loopStart ??= now;
      f = Math.min(replay.frames - 1, finalStart + ((now - loopStart) * meta.fps * 0.24 / 1000) % (replay.frames - 1 - finalStart + meta.fps * 0.24 * 1.2));
    }
    if (!dirty && !force && Math.abs(before - shown) < 0.00001 && !looping) return;
    dirty = false;
    const begin = performance.now();
    replay.pose(f);
    if (reduced) { replay.ball.getWorldPosition(ball); replay.ball.parent.position.set(0.3, 0.02, 0.45); replay.root.updateMatrixWorld(true); }
    replay.updateTrail(reduced); setCamera(shown, looping ? now - loopStart : 0); updateCopy(shown, f); render(shown);
    renderTimes.push(performance.now() - begin); if (renderTimes.length > 240) renderTimes.shift();
    rafTimes.push(now - previous); if (rafTimes.length > 240) rafTimes.shift(); previous = now;
  }
  function loop(now) { if (!visible || section.classList.contains('is-fallback')) { running = false; return; } draw(now); requestAnimationFrame(loop); }
  function start() { if (!running && !section.classList.contains('is-fallback')) { running = true; previous = performance.now(); requestAnimationFrame(loop); } }
  function selftest() {
    if (section.classList.contains('is-fallback')) {
      let previous = {}; try { previous = JSON.parse(document.body.dataset.selftest || '{}'); } catch {}
      const result = { ready: true, webgl: false, fallback: true };
      document.body.dataset.selftest = JSON.stringify({ ...previous, opening: result });
      return result;
    }
    const timeline = meta.score_timeline ?? meta.scoreTimeline;
    const result = { ready: true, revision: meta.source_revision ?? meta.source?.revision, frames: replay.frames, fps: meta.fps, golden: meta.replay,
      pointEnds: timeline.filter(e => e.point), score: replay.score(replay.frame), scoreTimelineValid: timeline.every(e => { const a = replay.score(e.frame); return a.A === (e.score ?? e.scores).A && a.B === (e.score ?? e.scores).B; }),
      firstFrameMs: readyAt, coarse, reducedMotion: reduced, overview, frame: replay.frame, scroll: shown, webgl: true, threeRevision: THREE.REVISION };
    let previous = {}; try { previous = JSON.parse(document.body.dataset.selftest || '{}'); } catch {}
    document.body.dataset.selftest = JSON.stringify({ ...previous, opening: result });
    return result;
  }
  function truthSample({ frame, camera: def, width = def.width, height = def.height, mask = null }) {
    testActive = true;
    replay.pose(frame); updateCopy(shown, frame); replay.trail.visible = false; helpers.visible = false;
    const c = cameraFrom(def, width, height);
    const points = replay.points().map(p => { const v = new THREE.Vector3(...p.world).project(c); return { ...p, uv: [(v.x + 1) * width / 2, (1 - v.y) * height / 2] }; });
    let png;
    if (mask) {
      const visibility = replay.geomNodes.map(m => m.visible), oldBackground = scene.background, oldOverride = scene.overrideMaterial;
      const oldDpr = renderer.getPixelRatio(), oldShadow = renderer.shadowMap.enabled;
      const oldSize = renderer.getSize(new THREE.Vector2());
      renderer.setPixelRatio(1); renderer.setSize(width, height, false); renderer.setViewport(0, 0, width, height); renderer.setScissorTest(false); renderer.shadowMap.enabled = false;
      scene.background = new THREE.Color(0); scene.overrideMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });
      stage.grid.visible = false; stage.floor.visible = false;
      replay.geomNodes.forEach(m => { const name = meta.bodies[m.userData.body]?.name ?? ''; m.visible = mask === 'arms' ? /^link[0-7](_b)?$/.test(name) : m.name === 'geom_ball'; });
      renderer.render(scene, c); png = canvas.toDataURL('image/png');
      replay.geomNodes.forEach((m, i) => m.visible = visibility[i]); scene.background = oldBackground; scene.overrideMaterial.dispose(); scene.overrideMaterial = oldOverride;
      renderer.shadowMap.enabled = oldShadow; renderer.setPixelRatio(oldDpr); renderer.setSize(oldSize.x, oldSize.y, false); stage.grid.visible = true; stage.floor.visible = true;
    }
    testActive = false; dirty = true;
    return { frame: replay.frame, score: replay.score(frame), scorebug: { A: Number(hud.a.textContent), B: Number(hud.b.textContent) }, points, png };
  }
  window.__opening = {
    meta, replay, stage, cameraRig, ready: true, truthSample, selftest,
    setProgress(s) { forcedProgress = clamp(s); shown = forcedProgress; replay.pose(timeAt(shown) * meta.fps); replay.updateTrail(reduced); setCamera(shown); updateCopy(shown, replay.frame); render(shown); },
    async measure(count = 90, from = 0.15, to = 0.73) {
      const values = []; testActive = true; const started = performance.now();
      for (let i = 0; i < count; i++) {
        await new Promise(requestAnimationFrame); const begin = performance.now();
        const s = lerp(from,to,i / Math.max(1,count - 1)); replay.pose(timeAt(s) * meta.fps); replay.updateTrail(); setCamera(s); updateCopy(s, replay.frame); render(s);
        renderer.getContext().finish(); values.push(performance.now() - begin);
      }
      testActive = false; dirty = true;
      return { count, from, to, meanFrameMs: (performance.now() - started) / count, meanMs: values.reduce((a, b) => a + b, 0) / count, p95Ms: values.sort((a, b) => a - b)[Math.floor(count * 0.95)], firstFrameMs: readyAt, dpr: renderer.getPixelRatio(), coarse,
        loadedBytes: performance.getEntriesByType('resource').filter(r => /\/opening\/|\/vendor\/three\//.test(r.name)).reduce((sum, r) => sum + r.encodedBodySize, 0) };
    }
  };
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) { dirty = true; start(); } }).observe(section);
  addEventListener('resize', () => { stage.resize(); dirty = true; if (!running) draw(); });
  addEventListener('themechange', () => { cameraRig.theme(); dirty = true; if (!running) draw(); if (params.has('selftest')) setTimeout(selftest, 0); });
  motionPreference.addEventListener('change', () => {
    reduced = motionPreference.matches;
    if (section.classList.contains('is-fallback')) return;
    overview = params.get('overview') === '1' || reduced;
    section.classList.toggle('is-overview', overview); dirty = true; loopStart = null;
    draw(performance.now(), true); start(); if (params.has('selftest')) selftest();
  });
  canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); visible = false; fallback(section, motionPreference); });
  stage.resize(); draw(performance.now(), true); renderer.getContext().finish(); readyAt = performance.now(); section.dataset.ready = 'true';
  if (params.has('selftest')) { selftest(); retainSelftest(selftest); } start();
  return window.__opening;
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => initOpening()); else initOpening();
