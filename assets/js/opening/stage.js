// The 3D stage shared by the opening and the play section: a quiet studio. The background is the page's own colour (or,
// for a stage in a card, the card's), the floor only catches shadows and carries a faint measuring grid, one key light
// casts soft shadows, a fill and a sky light lift the darks, and a dim room environment gives metal its reflections.
// Two looks, day and night.
import * as THREE from '../../vendor/three/three.module.js';
import { RoomEnvironment } from '../../vendor/three/addons/environments/RoomEnvironment.js';

export const STAGE_THEMES = {
  light: { bg: 0xf4f6f9, surface: 0xffffff, grid: 0x2563b4, gridMinor: 0.09, gridMajor: 0.17, shadow: 0.15, hemiSky: 0xffffff, hemiGround: 0xd4d9e0,
    hemi: 1.15, key: 2.1, fill: 0.55, env: 0.6, exposure: 1.0 },
  dark: { bg: 0x121417, surface: 0x1b1e22, grid: 0x8a919a, gridMinor: 0.07, gridMajor: 0.15, shadow: 0.45, hemiSky: 0x9aa6b8, hemiGround: 0x15181b,
    hemi: 0.5, key: 2.3, fill: 0.35, env: 0.45, exposure: 1.05 },
};
export const currentTheme = () => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');

/** A floor grid: fine lines every `cell`, stronger ones every `every` cells, fading out with distance. */
function makeGrid(size, cell, every) {
  const minor = [], major = [];
  const n = Math.round(size / cell);
  for (let i = -n; i <= n; i++) {
    const v = i * cell, list = i % every === 0 ? major : minor;
    list.push(-size, 0, v, size, 0, v, v, 0, -size, v, 0, size);
  }
  const mat = (opacity) => new THREE.ShaderMaterial({
    transparent: true, depthWrite: false,
    uniforms: { uColor: { value: new THREE.Color() }, uOpacity: { value: opacity }, uFade: { value: size * 0.55 } },
    vertexShader: 'varying vec3 vW; void main() { vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
    fragmentShader: 'uniform vec3 uColor; uniform float uOpacity; uniform float uFade; varying vec3 vW; void main() { float r = length(vW.xz); gl_FragColor = vec4(uColor, uOpacity * (1.0 - smoothstep(uFade * 0.35, uFade, r))); }',
  });
  const group = new THREE.Group();
  for (const [list, kind] of [[minor, 'minor'], [major, 'major']]) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(list, 3));
    const lines = new THREE.LineSegments(g, mat(0));
    lines.userData.kind = kind;
    lines.renderOrder = -1;
    group.add(lines);
  }
  return group;
}

export function createStage(canvas, opts = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  const initialDpr = Math.min(window.devicePixelRatio || 1, opts.maxDpr ?? 2);
  renderer.setPixelRatio(initialDpr);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  // One key is the only shadow caster, including on phones. The soft filter
  // matches the sibling venues; phones keep the same light at half resolution.
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  // The opening marks needsUpdate once before its main render. The inset then
  // reuses that pose's light-space map instead of repeating the shadow pass.
  renderer.shadowMap.autoUpdate = false;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();

  const camera = new THREE.PerspectiveCamera(opts.fov ?? 30, 1, 0.01, 40);

  const span = opts.span ?? 1;                         // how big the scene is, metres: sizes the shadow and the grid
  const key = new THREE.DirectionalLight(0xffffff, 2);
  // Lower the studio key's elevation to lengthen floor shadows. Background,
  // dim room environment and theme light intensities retain the series values.
  key.position.set(-1.05 * span, 1.35 * span, 1.6 * span);
  key.castShadow = true;
  key.shadow.mapSize.set(opts.coarse ? 1024 : 2048, opts.coarse ? 1024 : 2048);
  key.shadow.bias = -0.0002;
  key.shadow.normalBias = 0.004 * span;
  Object.assign(key.shadow.camera, { left: -span, right: span, top: span, bottom: -span, near: 0.1 * span, far: 6 * span });
  key.shadow.radius = 3.5;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xdfe8ff, 0.5);
  fill.position.set(1.5 * span, 0.8 * span, -1.0 * span);
  scene.add(fill);
  const hemi = new THREE.HemisphereLight(0xffffff, 0xd8d4cc, 1);
  scene.add(hemi);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(40 * span, 40 * span), new THREE.ShadowMaterial({ opacity: 0.16 }));
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);
  const grid = opts.grid === false ? null : makeGrid(3 * span, opts.cell ?? 0.05 * span, opts.every ?? 5);
  if (grid) { grid.position.y = 0.0005; scene.add(grid); }

  const root = new THREE.Group();
  scene.add(root);

  const stage = { renderer, scene, camera, root, key, floor, grid, theme: 'light' };

  // Delivered intervals from consecutive active RAF frames drive adaptation.
  // GPU timers remain nonblocking diagnostics, including time spent drawing
  // the shadow map. Screenshot/CDP delays must never be passed as RAF time.
  // Callers without an active interval can fall back to GPU/CPU render timing.
  // Adaptive resolution never changes geometry, camera projection or the
  // shadow map, and ignores temporary test resolutions.
  const gl = renderer.getContext();
  const timer = gl.getExtension('EXT_disjoint_timer_query_webgl2');
  const quality = stage.quality = {
    initialDpr, dpr: initialDpr, source: timer ? 'gpu' : 'cpu-submit',
    thresholdMs: 22, sampleCount: 30, warmupFrames: 5, samples: 0, history: [],
    gpuSamples: 0, gpuLastMs: null, gpuHistory: [],
  };
  const lowerDprs = [1.75, 1.5].filter(dpr => dpr < initialDpr);
  const timings = [];
  const gpuTimings = [];
  const pending = [];
  let activeQuery = null, warmup = 0, presentationTiming = false;
  function recordFrame(ms, source = 'external') {
    if (!Number.isFinite(ms) || ms <= 0 || gl.isContextLost()) return;
    if (Math.abs(renderer.getPixelRatio() - quality.dpr) > 1e-6) return;
    if (source === 'active-raf') presentationTiming = true;
    // A completed GPU query and the RAF interval describe the same frame, so
    // they must not become two adaptive samples or mix timing methods.
    if (presentationTiming && (source === 'gpu' || source === 'cpu-submit')) return;
    if (source !== quality.source) {
      timings.length = 0; quality.samples = 0; warmup = 0;
      quality.source = source;
    }
    if (warmup++ < quality.warmupFrames) return;
    timings.push(ms); quality.samples = timings.length;
    if (timings.length < quality.sampleCount) return;
    const meanMs = timings.reduce((sum, value) => sum + value, 0) / timings.length;
    const p95Ms = [...timings].sort((a, b) => a - b)[Math.floor((timings.length - 1) * 0.95)];
    const next = meanMs > quality.thresholdMs ? lowerDprs.shift() : null;
    quality.history.push({ dpr: quality.dpr, source, meanMs, p95Ms, nextDpr: next ?? quality.dpr });
    if (quality.history.length > 12) quality.history.shift();
    timings.length = 0; quality.samples = 0;
    if (next != null) {
      quality.dpr = next;
      gpuTimings.length = 0; quality.gpuSamples = 0;
      renderer.setPixelRatio(next);
      resize();
    }
  }
  function collectTimers() {
    if (!timer || gl.isContextLost()) return;
    if (gl.getParameter(timer.GPU_DISJOINT_EXT)) {
      for (const entry of pending) gl.deleteQuery(entry.query);
      pending.length = 0; gpuTimings.length = 0; quality.gpuSamples = 0;
      if (!presentationTiming) { timings.length = 0; quality.samples = 0; }
      return;
    }
    while (pending.length && gl.getQueryParameter(pending[0].query, gl.QUERY_RESULT_AVAILABLE)) {
      const entry = pending.shift();
      const ms = gl.getQueryParameter(entry.query, gl.QUERY_RESULT) / 1e6;
      gl.deleteQuery(entry.query);
      // Results arrive later. A queued frame from the previous resolution must
      // not enter the new resolution's 30-frame batch after a quality step.
      if (Math.abs(entry.dpr - quality.dpr) < 1e-6) {
        quality.gpuLastMs = ms; gpuTimings.push(ms); quality.gpuSamples = gpuTimings.length;
        if (gpuTimings.length === quality.sampleCount) {
          const meanMs = gpuTimings.reduce((sum, value) => sum + value, 0) / gpuTimings.length;
          const p95Ms = [...gpuTimings].sort((a, b) => a - b)[Math.floor((gpuTimings.length - 1) * 0.95)];
          quality.gpuHistory.push({ dpr: entry.dpr, meanMs, p95Ms });
          if (quality.gpuHistory.length > 12) quality.gpuHistory.shift();
          gpuTimings.length = 0; quality.gpuSamples = 0;
        }
        recordFrame(ms, 'gpu');
      }
    }
  }
  function beginFrame(activeRafIntervalMs = null) {
    if (activeRafIntervalMs != null) recordFrame(activeRafIntervalMs, 'active-raf');
    collectTimers();
    if (!timer || activeQuery || pending.length >= 5 || gl.isContextLost()) return;
    activeQuery = { query: gl.createQuery(), dpr: renderer.getPixelRatio() };
    gl.beginQuery(timer.TIME_ELAPSED_EXT, activeQuery.query);
  }
  function endFrame(cpuMs) {
    if (activeQuery && !gl.isContextLost()) {
      gl.endQuery(timer.TIME_ELAPSED_EXT);
      pending.push(activeQuery); activeQuery = null;
      collectTimers();
    } else if (!timer) recordFrame(cpuMs, 'cpu-submit');
  }
  function setTheme(name) {
    const t = STAGE_THEMES[name] || STAGE_THEMES.light;
    stage.theme = name;
    scene.background.set(getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || (opts.surface ? t.surface : t.bg));         // the page's paper, or a card's surface
    floor.material.opacity = t.shadow;
    hemi.color.set(t.hemiSky); hemi.groundColor.set(t.hemiGround); hemi.intensity = t.hemi;
    key.intensity = t.key; fill.intensity = t.fill;
    scene.environmentIntensity = t.env;
    renderer.toneMappingExposure = t.exposure;
    if (grid) for (const l of grid.children) { l.material.uniforms.uColor.value.set(t.grid); l.material.uniforms.uOpacity.value = l.userData.kind === 'major' ? t.gridMajor : t.gridMinor; }
  }
  setTheme(currentTheme());
  addEventListener('themechange', () => setTheme(currentTheme()));

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  return Object.assign(stage, { resize, setTheme, beginFrame, endFrame, recordFrame, update() {} });
}
