import * as THREE from '../../vendor/three/three.module.js';
import { cameraState } from './path.js?v=20261009-r5';

// A point reset is an actual discontinuity in the recording. Keep each rally
// continuous and cut directly to its next serve, rather than showing the hidden
// ball during the sport's between-point waiting period.
const ANCHORS = [[0, 0], [0.060, 0.20], [0.195, 0.60], [0.345, 2.96], [0.475, 3.80], [0.535, 4.249], [0.660, 5.85], [0.800, 7.50], [0.940, 8.65], [0.999, 8.909], [1, 8.91]];
const clamp = x => Math.min(1, Math.max(0, x));
export function createTimeline(replay, width, height) {
  const duration = (replay.frames - 1) / replay.meta.fps;
  const fps = replay.meta.fps, ranges = replay.meta.in_play_ranges;
  const flightRanges = [[0, 1.479], [2.29, 4.249], [5.06, 8.909]];
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.10, 50);
  const point = new THREE.Vector3(), previous = new THREE.Vector3(), projected = new THREE.Vector3();
  const rows = [], cuts = [];
  const activeTime = time => flightRanges.some(([a, b]) => time >= a && time <= b);
  function setCamera(s) {
    const state = cameraState(s, width / height);
    camera.position.fromArray(state.eye); camera.lookAt(new THREE.Vector3(...state.look)); camera.fov = state.fov;
    if (state.shift || state.rise) camera.setViewOffset(width, height, -state.shift * width, state.rise * height, width, height);
    else camera.clearViewOffset();
    camera.updateProjectionMatrix(); camera.updateMatrixWorld(true);
  }
  function screenDistance(a, b) {
    const pa = a.clone().project(camera), pb = b.clone().project(camera);
    return Math.hypot((pa.x - pb.x) * width / 2, (pa.y - pb.y) * height / 2);
  }
  for (let block = 0; block < ANCHORS.length - 1; block++) {
    const [sa, rawA] = ANCHORS[block], [sb, rawB] = ANCHORS[block + 1];
    const ta = Math.min(duration, rawA), tb = Math.min(duration, rawB);
    const times = [ta];
    for (let frame = Math.ceil(ta * 1000); frame < tb * 1000; frame += 2) {
      if (activeTime(frame / 1000) && frame / 1000 > ta) times.push(frame / 1000);
    }
    for (const [a, b] of flightRanges) for (const edge of [a, b]) if (edge > ta && edge < tb) times.push(edge);
    times.sort((a, b) => a - b);
    times.push(tb);
    let positions = times.map(t => sa + (sb - sa) * (t - ta) / (tb - ta));
    // Reweight within each shot by projected flight distance. A faster stretch
    // gets more scroll; the floor leaves time for small/near-stationary motion.
    for (let pass = 0; pass < 3; pass++) {
      const weights = [0]; let total = 0;
      replay.ballAt(times[0], previous);
      for (let i = 1; i < times.length; i++) {
        const dt = times[i] - times[i - 1];
        replay.ballAt(times[i], point); setCamera((positions[i] + positions[i - 1]) / 2);
        // A zero-width cut preserves the exact reset and never blends across it.
        const weight = dt > 0.03 ? 0 : screenDistance(previous, point) + dt * height * 0.12;
        total += weight; weights.push(total); previous.copy(point);
      }
      positions = weights.map(w => sa + (sb - sa) * (total ? w / total : 0));
    }
    for (let i = 0; i < times.length; i++) {
      if (i && times[i] - times[i - 1] > 0.03) cuts.push({ s: positions[i], from: times[i - 1], to: times[i], kind: 'recorded point reset' });
      rows.push({ s: positions[i], time: times[i] });
    }
  }
  function timeAt(s) {
    s = clamp(s);
    let lo = 0, hi = rows.length - 1;
    while (lo < hi) { const mid = Math.ceil((lo + hi) / 2); if (rows[mid].s <= s) lo = mid; else hi = mid - 1; }
    const a = rows[lo], b = rows[Math.min(rows.length - 1, lo + 1)];
    const u = b.s > a.s ? clamp((s - a.s) / (b.s - a.s)) : 0;
    return a.time + (b.time - a.time) * u;
  }
  cuts.push({ s: 1, from: 8.909, to: 8.91, kind: 'recorded point end reset' });
  return { timeAt, rows, cuts, anchors: ANCHORS };
}
