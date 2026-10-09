import * as THREE from '../../vendor/three/three.module.js';

export const CAMERA_TRANSITIONS = [[0.060, 0.195], [0.345, 0.475], [0.535, 0.660], [0.800, 0.940]];
export const DAMPING_MS = 300;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const ease = x => { const t = clamp(x); return t * t * t * (10 + t * (-15 + 6 * t)); };
// All five views stay on the same side of the table. The continuous curve goes
// around the venue instead of cutting through it when a shot changes.
const DESKTOP = [
  { eye: [1.40, 0.34, 0.75], look: [-0.24, 0.28, -1.08], fov: 42, shift: 0.025, rise: 0.055 },
  { eye: [3.80, 1.15, 0.50], look: [0, 0.23, 0], fov: 48, shift: 0.025, rise: 0.055 },
  { eye: [3.80, 3.50, 5.00], look: [-1.00, 0.40, 0], fov: 46, shift: 0, rise: 0.025 },
  { eye: [4.80, 1.50, 1.20], look: [0, 0.25, 0], fov: 44, shift: 0.025, rise: 0.055 },
  { eye: [3.00, 7.00, 3.00], look: [0, 0.08, 0], fov: 34, shift: 0.225, rise: 0.025 },
];
const PHONE = [
  { eye: [1.70, 0.34, 0.65], look: [-0.20, 0.29, -1.08], fov: 66, shift: 0, rise: 0.08 },
  { eye: [4.00, 3.30, 1.50], look: [0, 0.23, 0], fov: 66, shift: 0, rise: 0.16 },
  { eye: [5.00, 5.80, 9.00], look: [-1.05, 0.40, 0], fov: 58, shift: 0.05, rise: 0.075 },
  { eye: [5.70, 2.10, 2.20], look: [0, 0.25, 0], fov: 55, shift: 0, rise: 0.16 },
  { eye: [3.60, 8.40, 3.60], look: [0, 0.08, 0], fov: 59, shift: 0, rise: 0.215 },
];
function curves(keys) {
  return {
    eye: new THREE.CatmullRomCurve3(keys.map(k => new THREE.Vector3(...k.eye)), false, 'centripetal'),
    look: new THREE.CatmullRomCurve3(keys.map(k => new THREE.Vector3(...k.look)), false, 'centripetal'),
  };
}
const desktop = curves(DESKTOP), phone = curves(PHONE);
export function shotPhase(s) {
  for (let i = 0; i < CAMERA_TRANSITIONS.length; i++) {
    const [a, b] = CAMERA_TRANSITIONS[i];
    if (s < a) return i;
    if (s <= b) return i + ease((s - a) / (b - a));
  }
  return 4;
}
export function cameraState(s, aspect = 1.6) {
  const portrait = aspect < 0.8, keys = portrait ? PHONE : DESKTOP, path = portrait ? phone : desktop;
  const phase = shotPhase(clamp(s)), i = Math.min(3, Math.floor(phase)), u = phase - i;
  const a = keys[i], b = keys[i + 1], mix = name => a[name] + (b[name] - a[name]) * u;
  const eye = path.eye.getPoint(phase / 4).toArray(), look = path.look.getPoint(phase / 4).toArray();
  // Intermediate tablet widths share the desktop path with a continuous dolly.
  if (!portrait && aspect < 1.2) {
    const distance = 1.2 / aspect;
    for (let k = 0; k < 3; k++) eye[k] = look[k] + (eye[k] - look[k]) * distance;
  }
  return { eye, look, fov: mix('fov'), shift: mix('shift'), rise: mix('rise'), phase };
}
export function dampScroll(previous, target, elapsedMs, bypass = false) {
  return bypass ? target : previous + (target - previous) * -Math.expm1(-Math.max(0, elapsedMs) / DAMPING_MS);
}
