// Recorded world poses only. No simulation or joint kinematics run in the browser.
import * as THREE from '../../vendor/three/three.module.js';
const BASE = new URL('../../opening/', import.meta.url);
const get = async (name, json = false) => {
  const r = await fetch(new URL(name, BASE));
  if (!r.ok) throw new Error(`Opening asset ${name}: ${r.status}`);
  return json ? r.json() : r.arrayBuffer();
};
export async function loadReplay() {
  const [meta, motion, meshes, buffer] = await Promise.all([get('rally.json', true), get('rally.bin'), get('meshes.json', true), get('meshes.bin')]);
  const list = meshes.meshes ?? meshes;
  const geometries = list.map(m => {
    const packed = new Uint16Array(buffer, m.position_offset, m.vertex_count * 3);
    const p = new Float32Array(packed.length);
    const lo = m.min, step = m.extent.map(x => x / 65535);
    for (let i = 0; i < p.length; i++) p[i] = lo[i % 3] + packed[i] * (Array.isArray(step) ? step[i % 3] : step);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    g.setIndex(new THREE.BufferAttribute(new Uint16Array(buffer, m.index_offset ?? ((m.position_offset) + packed.byteLength), m.index_count), 1));
    g.computeVertexNormals();
    return g;
  });
  return { meta, poses: new Int16Array(motion), geometries };
}
export function createReplay({ meta, poses, geometries }) {
  const coarse = matchMedia('(pointer: coarse)').matches;
  const root = new THREE.Group(), materials = new Map(), nodes = meta.bodies.map(b => {
    const o = new THREE.Group(); o.name = b.name; root.add(o); return o;
  });
  const geomNodes = [];
  function material(g) {
    let color = g.rgba.slice(0, 3), alpha = g.rgba[3];
    const name = g.name || '';
    const tick = name.startsWith('scale_tick_');
    const role = name === 'geom_table' ? 'table' : name === 'geom_ball' ? 'ball' :
      tick ? `tick-${g.size[0] >= g.size[2] ? 'x' : 'z'}` :
      g.material === 'dark_grey' ? 'joint' :
      g.material === 'white' || g.material === 'off_white' ? 'shell' :
      name.startsWith('paddle_blade') ? 'rubber' : 'hardware';
    if (name === 'geom_table') color = '#1f5fa8';
    if (name === 'geom_ball') color = '#FFD447';
    if (name.includes('pedestal')) color = name.endsWith('_b') ? '#2F7BEA' : '#E8573A';
    if (role === 'joint') color = '#22262c';
    if (tick) { color = '#ffffff'; alpha = 0.35; }
    // Include surface role: equal colours can have different rubber, shell and
    // table finishes without accidentally sharing a texture or roughness.
    const key = JSON.stringify([role, color, alpha]);
    if (!materials.has(key)) {
      const c = Array.isArray(color) ? new THREE.Color().setRGB(...color, THREE.SRGBColorSpace) : new THREE.Color(color);
      const roughness = role === 'shell' ? 0.35 : role === 'joint' ? 0.82 :
        role === 'table' ? 0.58 : role === 'rubber' ? 0.76 : role === 'ball' ? 0.32 : 0.62;
      const m = new THREE.MeshStandardMaterial({ color: c, roughness,
        metalness: role === 'shell' ? 0.04 : 0.015,
        opacity: alpha, transparent: alpha < 1, depthWrite: alpha === 1 });
      if (name === 'geom_table') {
        // Venue finish only: the recorded table's geometry stays exact.
        const paint = document.createElement('canvas'); paint.width = 1024; paint.height = 512;
        const ctx = paint.getContext('2d'); ctx.fillStyle = '#1f5fa8'; ctx.fillRect(0, 0, 1024, 512);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 8, 512); ctx.fillRect(1016, 0, 8, 512);
        ctx.fillRect(0, 0, 1024, 7); ctx.fillRect(0, 505, 1024, 7); ctx.fillRect(0, 255, 1024, 1);
        m.map = new THREE.CanvasTexture(paint); m.map.colorSpace = THREE.SRGBColorSpace; m.color.set('#ffffff');
      }
      if (name === 'geom_ball') { m.emissive.set('#FFD447'); m.emissiveIntensity = 0.16; }
      if (tick) {
        // A thin white painted stripe on the top of each original scale-mark
        // box. Alpha changes its appearance; no source vertices or pose change.
        const paint = document.createElement('canvas'); paint.width = paint.height = 64;
        const ctx = paint.getContext('2d'); ctx.clearRect(0, 0, 64, 64); ctx.fillStyle = '#ffffff';
        if (role === 'tick-x') ctx.fillRect(0, 27, 64, 10);
        else ctx.fillRect(27, 0, 10, 64);
        m.map = new THREE.CanvasTexture(paint); m.map.colorSpace = THREE.SRGBColorSpace;
      }
      materials.set(key, m);
    }
    return materials.get(key);
  }
  function primitive(g) {
    const s = g.size;
    if (g.type === 'mesh') return geometries[g.mesh];
    if (g.type === 'box') return new THREE.BoxGeometry(s[0] * 2, s[1] * 2, s[2] * 2);
    if (g.type === 'sphere') return new THREE.SphereGeometry(s[0], 20, 12);
    if (g.type === 'cylinder') return new THREE.CylinderGeometry(s[0], s[0], s[1] * 2, 32);
    if (g.type === 'capsule') return new THREE.CapsuleGeometry(s[0], s[1] * 2, 6, 16);
    return null;
  }
  function netVisual(g) {
    // Source envelope is 1.83 m across, 0.1525 m high and 0.01 m thick. Its
    // 0.1525 m overhang outside each table edge is recorded geometry. The old
    // opaque slab is replaced by presentation details INSIDE that envelope.
    // Local X is its thickness, local Y its height, local Z its full span.
    const [halfThickness, halfHeight, halfSpan] = g.size;
    const net = new THREE.Group();
    const weave = document.createElement('canvas'); weave.width = 1024; weave.height = 86;
    const ctx = weave.getContext('2d'); ctx.clearRect(0, 0, weave.width, weave.height);
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 0.7; ctx.beginPath();
    for (let x = 0.5; x <= weave.width; x += 8) { ctx.moveTo(x, 0); ctx.lineTo(x, weave.height); }
    for (let y = 0.5; y <= weave.height; y += 8) { ctx.moveTo(0, y); ctx.lineTo(weave.width, y); }
    ctx.stroke();
    const weaveMap = new THREE.CanvasTexture(weave); weaveMap.colorSpace = THREE.SRGBColorSpace;
    weaveMap.anisotropy = 4;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(halfSpan * 2, halfHeight * 2),
      new THREE.MeshStandardMaterial({ color: '#1f2937', map: weaveMap, roughness: 0.9,
        metalness: 0, transparent: true, opacity: 0.55, depthWrite: false, side: THREE.DoubleSide }));
    mesh.name = 'net-weave'; mesh.rotation.y = Math.PI / 2; net.add(mesh);
    const tapeHeight = Math.min(0.006, halfHeight * 0.1);
    const tape = new THREE.Mesh(new THREE.BoxGeometry(halfThickness * 1.8, tapeHeight, halfSpan * 2),
      new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.67, metalness: 0 }));
    tape.name = 'net-top-tape'; tape.position.y = halfHeight - tapeHeight / 2; net.add(tape);
    const postRadius = Math.min(0.004, halfThickness * 0.8);
    const postGeometry = new THREE.CylinderGeometry(postRadius, postRadius, halfHeight * 2, 12);
    const postMaterial = new THREE.MeshStandardMaterial({ color: '#1f2937', roughness: 0.74, metalness: 0.02 });
    for (const side of [-1, 1]) {
      const post = new THREE.Mesh(postGeometry, postMaterial);
      post.name = side < 0 ? 'net-post-left' : 'net-post-right';
      post.position.z = side * (halfSpan - postRadius); net.add(post);
    }
    // Only this source parent enters geomNodes. Masking it excludes every net
    // decoration together; none can contaminate arm or ball silhouette masks.
    net.children.forEach(child => { child.userData.decorative = true; child.castShadow = false; child.receiveShadow = false; });
    return net;
  }
  for (const g of meta.geoms) {
    if (g.stage_floor || g.type === 'plane') continue;
    const geo = g.name === 'geom_net' ? null : primitive(g);
    if (!geo && g.name !== 'geom_net') continue;
    const m = g.name === 'geom_net' ? netVisual(g) : new THREE.Mesh(geo, material(g));
    m.name = g.name; m.position.fromArray(g.pos); m.quaternion.fromArray(g.quat);
    m.castShadow = g.rgba[3] === 1 && !g.name.startsWith('scale_tick_'); m.receiveShadow = true;
    m.userData.body = g.body; m.userData.source = g;
    (g.body == null ? root : nodes[g.body]).add(m);
    geomNodes.push(m);
  }
  const p0 = new THREE.Vector3(), p1 = new THREE.Vector3(), q0 = new THREE.Quaternion(), q1 = new THREE.Quaternion();
  const width = nodes.length * 7, positionStep = meta.quantization?.position_step ?? meta.position_step ?? 0.0001;
  const quatStep = meta.quantization?.quaternion_step ?? 1 / 32767;
  const frames = typeof meta.frames === 'number' ? meta.frames : meta.frames.count;
  let frame = 0;
  function rawPose(i, b, p, q) {
    const off = i * width + b * 7;
    p.set(poses[off] * positionStep, poses[off + 1] * positionStep, poses[off + 2] * positionStep);
    q.set(poses[off + 3] * quatStep, poses[off + 4] * quatStep, poses[off + 5] * quatStep, poses[off + 6] * quatStep).normalize();
  }
  function pose(f) {
    frame = THREE.MathUtils.clamp(f, 0, frames - 1);
    const i = Math.floor(frame), j = Math.min(i + 1, frames - 1), u = frame - i;
    for (let b = 0; b < nodes.length; b++) {
      rawPose(i, b, p0, q0); rawPose(j, b, p1, q1);
      nodes[b].position.copy(p0).lerp(p1, u); nodes[b].quaternion.copy(q0).slerp(q1, u);
    }
    root.updateMatrixWorld(true);
  }
  const ball = geomNodes.find(g => g.name === 'geom_ball');
  const ballBody = meta.bodies.findIndex(b => b.name === 'ball');
  // Trail is a presentation aid only. The recorded ball remains radius 0.02 m.
  const trailN = 25, trail = new THREE.Group(), ballGeo = new THREE.SphereGeometry(coarse ? 0.014 : 0.009, 8, 5);
  for (let k = 0; k < trailN; k++) {
    const mat = new THREE.MeshBasicMaterial({ color: '#FFD447', transparent: true, opacity: (coarse ? 0.46 : 0.38) * (1 - k / trailN), depthWrite: false });
    const dot = new THREE.Mesh(ballGeo, mat); trail.add(dot);
  }
  root.add(trail);
  function updateTrail(rest = false) {
    const inPlay = meta.in_play_ranges.find(([a, b]) => frame >= a && frame <= b);
    // The sport's player view hides the ball between serves. Never trail across a point reset.
    ball.visible = rest || Boolean(inPlay);
    trail.visible = !rest && Boolean(inPlay) && ball?.getWorldPosition(p0).y > -0.5;
    if (!trail.visible || ballBody < 0) return;
    const stride = meta.fps * 0.25 / trailN;
    for (let k = 0; k < trailN; k++) {
      rawPose(Math.max(0, Math.floor(frame - k * stride)), ballBody, p0, q0);
      const d = trail.children[k]; d.position.copy(p0); d.visible = p0.y > -0.5;
      d.visible &&= frame - k * stride >= inPlay[0];
      d.scale.setScalar(1 - 0.65 * k / trailN);
    }
  }
  function score(f) {
    const timeline = meta.score_timeline ?? meta.scoreTimeline;
    let out = { A: 0, B: 0 };
    for (const event of timeline) if (event.frame <= f) out = event.score ?? event.scores;
    return out;
  }
  function points() {
    const out = [];
    for (let b = 0; b < nodes.length; b++) if (/^link[0-7](_b)?$/.test(meta.bodies[b].name)) out.push({ name: meta.bodies[b].name, world: nodes[b].getWorldPosition(new THREE.Vector3()).toArray() });
    for (const [geom, name] of [['geom_ball', 'ball'], ['paddle_blade', 'paddle_a'], ['paddle_blade_b', 'paddle_b']]) {
      const o = geomNodes.find(g => g.name === geom); if (o) out.push({ name, world: o.getWorldPosition(new THREE.Vector3()).toArray() });
    }
    return out;
  }
  pose(0);
  return { root, nodes, geomNodes, meta, frames, pose, updateTrail, trail, ball, points, score, get frame() { return frame; } };
}
