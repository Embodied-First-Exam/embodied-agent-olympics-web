import * as THREE from '../../vendor/three/three.module.js';

// A short diagram of each recorded camera, rather than a page-spanning view volume.
function edges(segments, colour, opacity) {
  const starts = [], ends = [], corners = [];
  for (const [a, b] of segments) for (const [t, side] of [[0,-1],[1,-1],[1,1],[0,-1],[1,1],[0,1]]) {
    starts.push(...a); ends.push(...b); corners.push(t, side);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(starts, 3));
  geometry.setAttribute('end', new THREE.Float32BufferAttribute(ends, 3));
  geometry.setAttribute('corner', new THREE.Float32BufferAttribute(corners, 2));
  const material = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    uniforms: { ink: { value: colour }, alpha: { value: opacity }, resolution: { value: new THREE.Vector2(1440,900) } },
    vertexShader: `attribute vec3 end; attribute vec2 corner; uniform vec2 resolution;
      void main() {
        vec4 a = projectionMatrix * modelViewMatrix * vec4(position,1.0);
        vec4 b = projectionMatrix * modelViewMatrix * vec4(end,1.0);
        vec2 d = normalize((b.xy / b.w - a.xy / a.w) * resolution);
        vec2 n = vec2(-d.y,d.x); vec4 p = mix(a,b,corner.x);
        p.xy += n * corner.y * 1.25 / resolution * p.w; gl_Position = p;
      }`,
    fragmentShader: `uniform vec3 ink; uniform float alpha;
      void main() { gl_FragColor = vec4(ink,alpha);
        #include <colorspace_fragment>
      }`
  });
  return new THREE.Mesh(geometry, material);
}

export function createCameraRig(cameras) {
  const group = new THREE.Group(), diagrams = [];
  cameras.forEach((camera, index) => {
    const colour = new THREE.Color(index === 0 ? '#FFD447' : '#69727f');
    const rig = new THREE.Group(); rig.position.copy(camera.position); rig.quaternion.copy(camera.quaternion);
    const length = 0.65, y = length * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)), x = y * camera.aspect;
    const apex = [0,0,0], far = [[-x,-y,-length],[x,-y,-length],[x,y,-length],[-x,y,-length]];
    const triangles = [];
    for (let i=0;i<4;i++) triangles.push(...apex,...far[i],...far[(i+1)%4]);
    triangles.push(...far[0],...far[1],...far[2],...far[0],...far[2],...far[3]);
    const faces = new THREE.Mesh(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(triangles,3)),
      new THREE.MeshBasicMaterial({color:colour,transparent:true,opacity:0.06,depthWrite:false,side:THREE.DoubleSide,toneMapped:false}));
    const wire = edges(far.flatMap((p,i)=>[[apex,p],[p,far[(i+1)%4]]]),colour,index===0?0.8:0.4);
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.09,0.06,0.075),new THREE.MeshStandardMaterial({color:colour,roughness:0.5,metalness:0.08}));
    body.position.z = 0.045;
    const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.024,0.024,0.035,16),new THREE.MeshStandardMaterial({color:'#1f2937',roughness:0.7}));
    lens.rotation.x=Math.PI/2; lens.position.z=-0.01;
    rig.add(faces,wire,body,lens); group.add(rig); diagrams.push({rig,faces,wire,body,index});
  });
  function theme() {
    for (const d of diagrams) {
      const colour = new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue(d.index===0?'--ball':'--ink-3').trim());
      d.faces.material.color.copy(colour); d.wire.material.uniforms.ink.value.copy(colour); d.body.material.color.copy(colour);
    }
  }
  function resize(w,h) { for (const d of diagrams) d.wire.material.uniforms.resolution.value.set(w,h); }
  theme(); return {group,theme,resize,diagrams};
}
