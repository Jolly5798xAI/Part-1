// «ЦЕНА ВЫБОРА» — blocky low-poly 3D world (browser side, three.js r160 global THREE).
// Every illustration of the series is rendered from this ONE world, so characters,
// the entryway, the door and the stairwell stay identical from shot to shot.
// Units: metres. Door plane z = 0. Apartment interior z > 0. Stairwell landing z < 0.
/* global THREE */

const PAL = {
  skinAlex: '#d9a27e', skinAlexSh: '#c08866', hairAlex: '#3b2a20',
  hoodie: '#5b6168', hoodieDk: '#474c52', jeans: '#2f3d55', socks: '#2b2b2e',
  skinCop: '#cf9672', skinCopSh: '#b47e5d', copNavy: '#1f2a44', copNavyDk: '#172036',
  copShirt: '#8fa7c4', gold: '#d1a93c', black: '#141416', mustache: '#3a2618',
  eyeW: '#f2efe6', pupil: '#1b1b20', brow: '#2e2018', mouth: '#7a3f35', mouthIn: '#3a1612',
  blood: '#8e0f12', bloodDk: '#5c0709',
  wallpaper: '#8c8a6f', wallpaperLine: '#7d7b62', laminate: '#7a5a3c', laminateLine: '#5f4430',
  doorLeather: '#5a2e22', doorLeatherDk: '#43211a', brass: '#c9a24a', steel: '#9aa0a6',
  hallGreen: '#4e7458', hallWhite: '#d8d4c4', hallTile1: '#8a6f55', hallTile2: '#b39a7a',
  ceiling: '#dcdad2',
};

// ---------- helpers ----------
function pixTex(rows, legend, opts = {}) {
  const h = rows.length, w = rows[0].length, s = opts.scale || 8;
  const c = document.createElement('canvas'); c.width = w * s; c.height = h * s;
  const g = c.getContext('2d');
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const ch = rows[y][x]; const col = legend[ch]; if (!col) continue;
    g.fillStyle = col; g.fillRect(x * s, y * s, s, s);
  }
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function canvasTex(w, h, draw, opts = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  if (opts.nearest) { t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; }
  if (opts.repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(opts.repeat[0], opts.repeat[1]); }
  t.anisotropy = 4;
  return t;
}
function M(color, o = {}) {
  return new THREE.MeshStandardMaterial(Object.assign({ color, roughness: 0.92, metalness: 0.0, flatShading: true }, o));
}
function MT(map, o = {}) { return new THREE.MeshStandardMaterial(Object.assign({ map, roughness: 0.92, metalness: 0 }, o)); }
function box(w, h, d, mat, x = 0, y = 0, z = 0, parent = null, name = '') {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; if (name) m.name = name;
  if (parent) parent.add(m); return m;
}

// ---------- faces (16x16 pixel art, front of head) ----------
const FACE_ALEX = [
  'HHHHHHHHHHHHHHHH',
  'HHHHHHHHHHHHHHHH',
  'HHHHHHHHHHHHHHHH',
  'HHsHHHHsHHHHHsHH',
  'ssssssssssssssss',
  'ssbbbssssssbbbss',
  'ssssssssssssssss',
  'ssswessssssewsss',
  'ssswessssssewsss',
  'ssssssssssssssss',
  'sssssssnnsssssss',
  'ssssssssssssssss',
  'ssssssMMMMssssss',
  'sssstttttttsssss',
  'ssssstttttssssss',
  'ssssssssssssssss',
];
function faceVariant(base, v) {
  const f = base.slice();
  if (v === 'worried') { f[5] = 'sssbbssssssbbsss'; f[4] = 'ssbsssssssssbsss'; }
  if (v === 'open') { f[12] = 'ssssssMOOMssssss'; f[13] = 'sssstMOOMttsssss'; }
  if (v === 'ee') { f[12] = 'sssssMOOOOMsssss'; f[13] = 'sssstttttttsssss'; }
  if (v === 'oo') { f[12] = 'sssssssMMsssssss'; f[13] = 'sssstttOOttsssss'; f[14] = 'ssssstMMMtssssss'; }
  if (v === 'dead') { f[7] = 'ssswwsssssswwsss'; f[8] = 'sssewssssssweses'.slice(0, 16); f[8] = 'ssswesssssseasss'.replace('a', 'w'); }
  return f;
}
const FACE_COP = [
  'ssssssssssssssss',
  'ssssssssssssssss',
  'ssssssssssssssss',
  'ssssssssssssssss',
  'ssssssssssssssss',
  'ssbbbbssssbbbbss',
  'ssssssssssssssss',
  'ssswesssssseewss'.slice(0, 16),
  'ssswessssssewsss',
  'ssssssssssssssss',
  'sssssssnnsssssss',
  'sssKKKKKKKKKKsss',
  'ssssKKssssKKssss',
  'ssssssssssssssss',
  'ssssssssssssssss',
  'ssssssssssssssss',
];
FACE_COP[7] = 'ssswessssssewsss';
const SIDE_ALEX = [
  'HHHHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHHH',
  'HHHHHHHHHHHHHHss', 'HHHHHHHHHHHHssss', 'HHHHHsssssssssss', 'HHHssssddsssssss',
  'HHHsssdddsssssss', 'HHsssssddsssssss', 'Hsssssssssssssss', 'ssssssssssssssss',
  'ssssssssssssssss', 'ssssssssssssssss', 'ssssssssssssssss', 'ssssssssssssssss',
];
const BACK_ALEX = Array(12).fill('HHHHHHHHHHHHHHHH').concat(['HHHHHHHHHHHHHHHH', 'sHHHHHHHHHHHHHHs', 'ssssssssssssssss', 'ssssssssssssssss']);
const ALL_H = Array(16).fill('HHHHHHHHHHHHHHHH');
const ALL_S = Array(16).fill('ssssssssssssssss');

function headMats(kind, variant = 'neutral') {
  if (kind === 'cop') {
    const L = { s: PAL.skinCop, d: PAL.skinCopSh, w: PAL.eyeW, e: PAL.pupil, b: PAL.brow, n: PAL.skinCopSh, K: PAL.mustache, H: PAL.skinCop };
    const side = SIDE_ALEX.map(r => r.replace(/H/g, 's'));
    return [MT(pixTex(side, L)), MT(pixTex(side, L)), MT(pixTex(ALL_S, L)), MT(pixTex(ALL_S, L)), MT(pixTex(FACE_COP, L)), MT(pixTex(ALL_S, L))];
  }
  const L = { H: PAL.hairAlex, s: PAL.skinAlex, d: PAL.skinAlexSh, t: '#c99372', w: PAL.eyeW, e: PAL.pupil, b: PAL.brow, n: PAL.skinAlexSh, M: PAL.mouth, O: PAL.mouthIn };
  const face = variant === 'neutral' ? FACE_ALEX : faceVariant(FACE_ALEX, variant);
  // box material order: +x, -x, +y, -y, +z(front), -z(back)
  return [MT(pixTex(SIDE_ALEX.map(r => r.split('').reverse().join('')), L)), MT(pixTex(SIDE_ALEX, L)), MT(pixTex(ALL_H, L)), MT(pixTex(ALL_S, L)), MT(pixTex(face, L)), MT(pixTex(BACK_ALEX, L))];
}

const HOODIE_FRONT = [
  'GGGGGGGGGGGG', 'GGGgGGGGgGGG', 'GGGgGGGGgGGG', 'GGGwGGGGwGGG', 'GGGGGGzGGGGG', 'GGGGGGzGGGGG',
  'GGGGGGzGGGGG', 'GGggggggggGG', 'GGgGGGGGGgGG', 'GGgGGGGGGgGG', 'GGggggggggGG', 'gggggggggggg',
];
const COP_FRONT = [
  'NNNNCCCCNNNN', 'NNNNNCCNNNNN', 'NNNNNNNNNNNN', 'NNyNNNoNNyNN', 'NNNNNNNNNNNN', 'NNNNNNoNNNNN',
  'NNNNNNNNNNNN', 'NNNNNNoNNNNN', 'NNNNNNNNNNNN', 'kkkkkkkkkkkk', 'kkkkkyykkkkk', 'NNNNNNNNNNNN',
];

function bloodHandTex(base) {
  return canvasTex(64, 64, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    const rnd = mulberry(7);
    for (let i = 0; i < 14; i++) {
      g.fillStyle = rnd() < 0.6 ? PAL.blood : PAL.bloodDk;
      const s = 4 + Math.floor(rnd() * 3) * 4; g.fillRect(Math.floor(rnd() * 16) * 4, Math.floor(rnd() * 16) * 4, s, s);
    }
  }, { nearest: true });
}
function mulberry(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ---------- characters ----------
// Proportions: head 0.36 cube, torso 0.56 x 0.42 x 0.24, arms 0.15 x 0.6, legs 0.19 x 0.76.
function makePerson(kind, o = {}) {
  const g = new THREE.Group(); g.name = kind;
  const isCop = kind === 'cop';
  const skin = isCop ? PAL.skinCop : PAL.skinAlex;
  const legH = 0.78, torsoH = 0.58, headS = 0.36;
  const pantsM = M(isCop ? PAL.copNavyDk : PAL.jeans);
  const shoeM = M(isCop ? PAL.black : PAL.socks);
  const legL = new THREE.Group(); legL.position.set(-0.105, legH, 0); g.add(legL);
  const legR = new THREE.Group(); legR.position.set(0.105, legH, 0); g.add(legR);
  for (const L of [legL, legR]) { box(0.2, legH - 0.08, 0.22, pantsM, 0, -(legH - 0.08) / 2, 0, L); box(0.21, 0.08, 0.27, shoeM, 0, -legH + 0.04, 0.025, L); }
  const torsoFront = isCop
    ? pixTex(COP_FRONT, { N: PAL.copNavy, C: PAL.copShirt, y: PAL.gold, o: PAL.gold, k: PAL.black })
    : pixTex(HOODIE_FRONT, { G: PAL.hoodie, g: PAL.hoodieDk, w: '#d8d8d8', z: '#3a3e44' });
  const tM = M(isCop ? PAL.copNavy : PAL.hoodie);
  const torso = box(0.44, torsoH, 0.25, [tM, tM, tM, tM, MT(torsoFront), tM], 0, legH + torsoH / 2, 0, g, 'torso');
  // head pivot at neck so head turns look right
  const headPivot = new THREE.Group(); headPivot.name = 'headPivot'; headPivot.position.set(0, legH + torsoH, 0); g.add(headPivot);
  const head = box(headS, headS, headS, headMats(isCop ? 'cop' : 'alex', o.face || 'neutral'), 0, headS / 2 + 0.01, 0, headPivot, 'head');
  if (!isCop) { // hair volume
    const hairM = M(PAL.hairAlex);
    box(0.39, 0.07, 0.39, hairM, 0, headS + 0.03, -0.005, headPivot);
    box(0.08, 0.05, 0.1, hairM, 0.1, headS + 0.08, 0.06, headPivot);
    box(0.1, 0.04, 0.12, hairM, -0.08, headS + 0.07, -0.05, headPivot);
  } else { // peaked cap
    const capM = M(PAL.copNavy), bandM = M('#20335c');
    box(0.42, 0.06, 0.42, bandM, 0, headS + 0.03, 0, headPivot);
    box(0.46, 0.08, 0.46, capM, 0, headS + 0.1, -0.01, headPivot);
    box(0.4, 0.025, 0.14, M(PAL.black), 0, headS + 0.0, 0.25, headPivot);
    box(0.07, 0.07, 0.02, M(PAL.gold, { metalness: 0.6, roughness: 0.4 }), 0, headS + 0.07, 0.22, headPivot);
  }
  const sleeveM = M(isCop ? PAL.copNavy : PAL.hoodie);
  const handM = o.bloodyRight ? MT(bloodHandTex(skin)) : M(skin);
  const handML = M(skin);
  const arms = {};
  for (const side of [-1, 1]) {
    const a = new THREE.Group(); a.name = side < 0 ? 'armL' : 'armR';
    a.position.set(side * 0.3, legH + torsoH - 0.06, 0); g.add(a);
    box(0.16, 0.5, 0.18, sleeveM, 0, -0.22, 0, a);
    box(0.15, 0.13, 0.16, side > 0 ? handM : handML, 0, -0.53, 0, a, side < 0 ? 'handL' : 'handR');
    if (isCop && side < 0) box(0.1, 0.12, 0.06, M('#222'), 0.02, 0.0, 0.11, torso); // radio
    arms[side] = a;
  }
  if (isCop) { box(0.06, 0.06, 0.02, M(PAL.gold), -0.3, legH + torsoH - 0.18, 0.1, g); }
  g.userData = { headPivot, arms, legL, legR, head };
  return g;
}

// open blocky hand (for the palm on the peephole)
function makeOpenHand(bloody = true) {
  const g = new THREE.Group();
  const tex = bloody ? bloodHandTex(PAL.skinAlex) : null;
  const m = tex ? MT(tex) : M(PAL.skinAlex);
  box(0.11, 0.12, 0.03, m, 0, 0, 0, g);
  const fx = [-0.04, -0.013, 0.013, 0.04], fl = [0.075, 0.09, 0.085, 0.07];
  fx.forEach((x, i) => box(0.024, fl[i], 0.026, m, x, 0.06 + fl[i] / 2, 0, g));
  const th = box(0.03, 0.06, 0.026, m, -0.07, -0.005, 0, g); th.rotation.z = 0.5;
  return g;
}

// ---------- props ----------
function makeGlass() {
  const g = new THREE.Group(); g.name = 'glass';
  const glassM = new THREE.MeshStandardMaterial({ color: '#cfe6ef', transparent: true, opacity: 0.28, roughness: 0.05, metalness: 0.1, flatShading: true, depthWrite: false });
  const waterM = new THREE.MeshStandardMaterial({ color: '#6fb3cf', transparent: true, opacity: 0.55, roughness: 0.1, flatShading: true, depthWrite: false });
  const topM = new THREE.MeshStandardMaterial({ color: '#bfe8f5', emissive: '#2a5560', transparent: true, opacity: 0.85, roughness: 0.05, flatShading: true });
  const outer = new THREE.Mesh(new THREE.CylinderGeometry(0.041, 0.034, 0.12, 8, 1, true), glassM); outer.position.y = 0.06; g.add(outer);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.034, 0.034, 0.012, 8), glassM); base.position.y = 0.006; g.add(base);
  const water = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.032, 0.1, 8), waterM); water.position.y = 0.062; g.add(water);
  const top = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.038, 0.002, 8), topM); top.position.y = 0.113; g.add(top);
  g.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}
function makePhone(screenColor = '#18202c') {
  const g = new THREE.Group(); g.name = 'phone';
  box(0.078, 0.162, 0.01, M('#16171a', { roughness: 0.4 }), 0, 0, 0, g);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.07, 0.15), new THREE.MeshBasicMaterial({ color: screenColor }));
  scr.position.z = 0.0052; scr.name = 'screen'; g.add(scr);
  return g;
}

// door, seen from inside (+z side) — padded leather door with diamond quilting
function doorTex() {
  return canvasTex(256, 576, (g, w, h) => {
    g.fillStyle = PAL.doorLeather; g.fillRect(0, 0, w, h);
    g.strokeStyle = PAL.doorLeatherDk; g.lineWidth = 6;
    const step = 64;
    for (let k = -h; k < w + h; k += step) { g.beginPath(); g.moveTo(k, 0); g.lineTo(k + h, h); g.stroke(); g.beginPath(); g.moveTo(k, 0); g.lineTo(k - h, h); g.stroke(); }
    g.fillStyle = PAL.brass;
    for (let y = 0; y < h + step; y += step / 2) for (let x = (y / (step / 2)) % 2 ? step / 2 : 0; x <= w; x += step) { g.fillRect(x - 4, y - 4, 8, 8); }
    g.strokeStyle = '#2e1610'; g.lineWidth = 14; g.strokeRect(0, 0, w, h);
  });
}

function makeLock() {
  // upper lock: brass escutcheon with thumb-turn (inside) — thumb turn rotates around z
  const g = new THREE.Group(); g.name = 'lock';
  const brassM = M(PAL.brass, { metalness: 0.65, roughness: 0.35 });
  box(0.07, 0.16, 0.012, brassM, 0, 0, 0.006, g);
  const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.026, 0.02, 10), brassM); cyl.rotation.x = Math.PI / 2; cyl.position.set(0, 0.02, 0.02); g.add(cyl);
  const turn = new THREE.Group(); turn.name = 'thumbTurn'; turn.position.set(0, 0.02, 0.032); g.add(turn);
  box(0.016, 0.06, 0.02, M('#b8923f', { metalness: 0.7, roughness: 0.3 }), 0, 0, 0, turn);
  const key = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.014, 10), M('#8f7230', { metalness: 0.7, roughness: 0.3 })); key.rotation.x = Math.PI / 2; key.position.set(0, -0.045, 0.016); g.add(key);
  box(0.004, 0.014, 0.004, M('#1a1208'), 0, -0.045, 0.024, g, 'keyhole');
  return g;
}

// ---------- world ----------
function buildWorld(opt = {}) {
  const scene = new THREE.Scene();
  const W = { scene, objs: {} };

  // ===== apartment entryway (z from 0 to 4) =====
  const wpTex = canvasTex(128, 128, (g, w, h) => { g.fillStyle = PAL.wallpaper; g.fillRect(0, 0, w, h); g.fillStyle = PAL.wallpaperLine; for (let x = 0; x < w; x += 32) g.fillRect(x, 0, 6, h); g.fillStyle = '#9a987c'; for (let y = 8; y < h; y += 32) for (let x = 16; x < w; x += 32) g.fillRect(x, y, 6, 6); }, { repeat: [6, 3] });
  const lamTex = canvasTex(256, 256, (g, w, h) => { g.fillStyle = PAL.laminate; g.fillRect(0, 0, w, h); const r = mulberry(3); for (let y = 0; y < h; y += 32) { g.fillStyle = PAL.laminateLine; g.fillRect(0, y, w, 3); const off = Math.floor(r() * 4) * 64; for (let x = off % 128; x < w; x += 128) g.fillRect(x, y, 3, 32); g.fillStyle = 'rgba(0,0,0,' + (r() * 0.12) + ')'; g.fillRect(0, y + 3, w, 29); } }, { repeat: [2, 4] });
  const wpM = MT(wpTex), lamM = MT(lamTex), ceilM = M(PAL.ceiling);
  const E = { x0: -0.75, x1: 1.05, z1: 4.0, h: 2.6 };
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(E.x1 - E.x0, E.z1), lamM); floor.rotation.x = -Math.PI / 2; floor.position.set((E.x0 + E.x1) / 2, 0, E.z1 / 2); floor.receiveShadow = true; scene.add(floor);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(E.x1 - E.x0, E.z1), ceilM); ceil.rotation.x = Math.PI / 2; ceil.position.set((E.x0 + E.x1) / 2, E.h, E.z1 / 2); scene.add(ceil);
  const wl = new THREE.Mesh(new THREE.PlaneGeometry(E.z1, E.h), wpM); wl.rotation.y = Math.PI / 2; wl.position.set(E.x0, E.h / 2, E.z1 / 2); wl.receiveShadow = true; scene.add(wl);
  const wr = new THREE.Mesh(new THREE.PlaneGeometry(E.z1, E.h), wpM); wr.rotation.y = -Math.PI / 2; wr.position.set(E.x1, E.h / 2, E.z1 / 2); wr.receiveShadow = true; scene.add(wr);
  // front wall (inside face, z = 0) with door opening x[-0.45,0.45], y[0,2.05]
  const fwM = wpM;
  box(E.x1 - 0.5, E.h, 0.2, fwM, (0.5 + E.x1) / 2 - 0.025, E.h / 2, -0.1, scene);
  box(0.3, E.h, 0.2, fwM, -0.6, E.h / 2, -0.1, scene);
  box(0.95, E.h - 2.08, 0.2, fwM, 0, 2.08 + (E.h - 2.08) / 2, -0.1, scene);
  // door frame (casing)
  const caseM = M('#e2ddd0');
  box(0.07, 2.12, 0.03, caseM, -0.49, 1.06, 0.015, scene); box(0.07, 2.12, 0.03, caseM, 0.49, 1.06, 0.015, scene); box(1.05, 0.07, 0.03, caseM, 0, 2.1, 0.015, scene);
  // back wall (z = 4) with dark doorway into living room
  box(E.x1 - E.x0, E.h, 0.1, wpM, (E.x0 + E.x1) / 2, E.h / 2, E.z1 + 0.05, scene);
  const dark = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 2.05), new THREE.MeshBasicMaterial({ color: '#0b0e14' })); dark.position.set(0.3, 1.025, E.z1 - 0.001); dark.rotation.y = Math.PI; scene.add(dark);
  // baseboards
  const bbM = M('#5b4331');
  box(0.02, 0.08, E.z1, bbM, E.x0 + 0.01, 0.04, E.z1 / 2, scene); box(0.02, 0.08, E.z1, bbM, E.x1 - 0.01, 0.04, E.z1 / 2, scene);

  // door (pivot on hinge at x = +0.45)
  const doorPivot = new THREE.Group(); doorPivot.position.set(0.45, 0, -0.035); scene.add(doorPivot);
  const dT = doorTex(); const dM = MT(dT); const dSide = M(PAL.doorLeatherDk);
  const outT = canvasTex(64, 128, (g, w, h) => { g.fillStyle = '#4a3a30'; g.fillRect(0, 0, w, h); g.strokeStyle = '#3a2c24'; g.lineWidth = 3; g.strokeRect(6, 6, w - 12, h - 12); });
  const door = box(0.9, 2.04, 0.07, [dSide, dSide, dSide, dSide, dM, MT(outT)], -0.45, 1.02, 0, doorPivot, 'door');
  // peephole at y = 1.58
  const brassM = M(PAL.brass, { metalness: 0.65, roughness: 0.35 });
  const ph = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.02, 12), brassM); ph.rotation.x = Math.PI / 2; ph.position.set(-0.45, 1.58, 0.04); doorPivot.add(ph);
  const phLens = new THREE.Mesh(new THREE.CircleGeometry(0.009, 12), new THREE.MeshStandardMaterial({ color: '#9fb5b0', emissive: '#4a5a52', roughness: 0.1 })); phLens.position.set(-0.45, 1.58, 0.0505); doorPivot.add(phLens);
  // lock + handle (lock on the left side, x ≈ -0.37 relative to world)
  const lock = makeLock(); lock.position.set(-0.82, 1.18, 0.035); doorPivot.add(lock);
  const handleBase = box(0.05, 0.2, 0.012, brassM, -0.82, 0.98, 0.041, doorPivot);
  const lever = box(0.14, 0.025, 0.03, brassM, -0.76, 1.0, 0.07, doorPivot);
  box(0.022, 0.022, 0.05, brassM, -0.82, 1.0, 0.055, doorPivot);
  // light leak under the door from the stairwell
  const leak = new THREE.Mesh(new THREE.PlaneGeometry(0.86, 0.012), new THREE.MeshBasicMaterial({ color: '#e8f3d8' })); leak.position.set(0, 0.006, 0.001); scene.add(leak);

  // entryway props: shoe rack, coat hooks + coat, mat, mirror, switch
  const woodM = M('#6b4a32');
  box(0.32, 0.45, 0.8, woodM, E.x1 - 0.17, 0.225, 1.0, scene);
  box(0.3, 0.02, 0.78, M('#7b583d'), E.x1 - 0.17, 0.46, 1.0, scene);
  box(0.14, 0.09, 0.28, M('#2a2a2a'), E.x1 - 0.17, 0.515, 0.8, scene); // shoe on top? sneaker
  box(0.12, 0.08, 0.27, M('#e8e8e8'), E.x1 - 0.2, 0.06, 0.55, scene); box(0.12, 0.08, 0.27, M('#e8e8e8'), E.x1 - 0.2, 0.06, 0.3, scene).rotation.y = 0.2;
  box(0.04, 0.06, 1.0, woodM, E.x0 + 0.02, 1.75, 1.3, scene);
  const coat = box(0.14, 0.9, 0.42, M('#3d4a3a'), E.x0 + 0.1, 1.33, 1.05, scene); coat.rotation.z = 0.03;
  box(0.12, 0.25, 0.3, M('#7a2a22'), E.x0 + 0.09, 1.55, 1.55, scene); // red scarf/bag
  const mat_ = box(0.7, 0.012, 0.45, M('#3c3a36'), 0, 0.006, 0.38, scene);
  box(0.03, 0.7, 0.5, M('#2c2f33'), E.x0 + 0.02, 1.45, 2.3, scene); // mirror frame
  const mirror = new THREE.Mesh(new THREE.PlaneGeometry(0.44, 0.64), new THREE.MeshStandardMaterial({ color: '#56656e', roughness: 0.05, metalness: 0.8 })); mirror.rotation.y = Math.PI / 2; mirror.position.set(E.x0 + 0.04, 1.45, 2.3); scene.add(mirror);
  box(0.08, 0.08, 0.015, M('#e8e5dc'), 0.6, 1.1, 0.008, scene); // light switch
  // ceiling lamp (off)
  const lampShade = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.2, 0.12, 6), M('#e9e2c8')); lampShade.position.set(0.15, E.h - 0.2, 1.6); scene.add(lampShade);
  box(0.01, 0.14, 0.01, M('#333'), 0.15, E.h - 0.07, 1.6, scene);

  // ===== stairwell landing (z from 0 to -3.2) =====
  const S = { x0: -2.4, x1: 2.3, z0: -3.2, h: 2.75 };
  const tileTex = canvasTex(128, 128, (g, w, h) => { for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.fillStyle = (x + y) % 2 ? PAL.hallTile1 : PAL.hallTile2; g.fillRect(x * 32, y * 32, 32, 32); } g.fillStyle = 'rgba(0,0,0,0.15)'; for (let i = 0; i <= 4; i++) { g.fillRect(i * 32 - 1, 0, 2, h); g.fillRect(0, i * 32 - 1, w, 2); } }, { repeat: [6, 4], nearest: true });
  const hallWall = canvasTex(64, 256, (g, w, h) => { g.fillStyle = PAL.hallWhite; g.fillRect(0, 0, w, h); g.fillStyle = PAL.hallGreen; g.fillRect(0, h * 0.42, w, h); g.fillStyle = '#3b5b44'; g.fillRect(0, h * 0.42, w, 6); const r = mulberry(11); for (let i = 0; i < 18; i++) { g.fillStyle = 'rgba(40,50,40,' + (r() * 0.18) + ')'; g.fillRect(r() * w, h * 0.42 + r() * h * 0.58, 4 + r() * 10, 4 + r() * 10); } }, { repeat: [5, 1] });
  const hwM = MT(hallWall);
  const hf = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, -S.z0), MT(tileTex)); hf.rotation.x = -Math.PI / 2; hf.position.set((S.x0 + S.x1) / 2, 0, S.z0 / 2); hf.receiveShadow = true; scene.add(hf);
  const hc = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, -S.z0), M('#cfccbf')); hc.rotation.x = Math.PI / 2; hc.position.set((S.x0 + S.x1) / 2, S.h, S.z0 / 2); scene.add(hc);
  // far wall (z = S.z0) — the man stands facing it
  const fw = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, S.h), hwM); fw.position.set((S.x0 + S.x1) / 2, S.h / 2, S.z0); fw.receiveShadow = true; scene.add(fw);
  const sl = new THREE.Mesh(new THREE.PlaneGeometry(-S.z0, S.h), hwM); sl.rotation.y = Math.PI / 2; sl.position.set(S.x0, S.h / 2, S.z0 / 2); sl.receiveShadow = true; scene.add(sl);
  const sr = new THREE.Mesh(new THREE.PlaneGeometry(-S.z0, S.h), hwM); sr.rotation.y = -Math.PI / 2; sr.position.set(S.x1, S.h / 2, S.z0 / 2); sr.receiveShadow = true; scene.add(sr);
  // outside face of front wall
  const ow = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, S.h), hwM); ow.rotation.y = Math.PI; ow.position.set((S.x0 + S.x1) / 2, S.h / 2, -0.2005); scene.add(ow);
  // neighbour door on the far-left wall + electrical panel + stair rail opening
  box(0.9, 2.05, 0.06, M('#5e4b3c'), -1.45, 1.025, S.z0 + 0.03, scene);
  box(0.03, 0.03, 0.04, M(PAL.steel, { metalness: 0.6 }), -1.1, 1.0, S.z0 + 0.07, scene);
  box(0.12, 0.08, 0.01, M('#c9c3a8'), -1.45, 1.75, S.z0 + 0.065, scene); // number plate (blank)
  box(0.55, 0.75, 0.12, M('#6f7a6c'), 1.65, 1.55, S.z0 + 0.06, scene); // electrical panel
  box(0.5, 0.02, 0.02, M('#3b3b3b'), 1.65, 1.15, S.z0 + 0.13, scene);
  // radiator under window on left side wall
  for (let i = 0; i < 6; i++) box(0.06, 0.55, 0.09, M('#d8d4c8'), S.x0 + 0.06, 0.55, -2.2 + i * 0.08, scene);
  // fluorescent tube
  const tube = box(1.1, 0.05, 0.08, new THREE.MeshBasicMaterial({ color: '#f1fbe8' }), 0.1, S.h - 0.04, -1.6, scene); tube.castShadow = false;
  box(1.2, 0.03, 0.14, M('#bcbab0'), 0.1, S.h - 0.01, -1.6, scene);

  W.objs = { doorPivot, door, lock, lever, leak, E, S, mirror };
  return W;
}

// lighting presets
function lightsInterior(scene, o = {}) {
  scene.add(new THREE.HemisphereLight('#8798bd', '#3a2c20', (o.amb ?? 0.55) * 1.7));
  const moon = new THREE.DirectionalLight('#9fb4e0', (o.moon ?? 0.9) * 1.3); moon.position.set(-1.5, 3.5, 6); moon.target.position.set(0, 0.8, 0.5);
  moon.castShadow = true; moon.shadow.mapSize.set(2048, 2048); Object.assign(moon.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 15 }); moon.shadow.bias = -0.0008; moon.shadow.radius = 4;
  scene.add(moon, moon.target);
  // cold stairwell light leaking under the door
  const leak = new THREE.SpotLight('#dff0d0', (o.leak ?? 6) * 0.22, 1.6, 0.9, 0.9, 2); leak.position.set(0, 0.012, 0.02); leak.target.position.set(0, 0, 1.0); scene.add(leak, leak.target);
  // warm practical from the kitchen behind
  const warm = new THREE.PointLight('#ffb36b', o.warm ?? 1.6, 6, 1.6); warm.position.set(0.5, 1.6, 3.7); scene.add(warm);
}
function lightsStairwell(scene, o = {}) {
  scene.add(new THREE.HemisphereLight('#d9e8d0', '#3a3a30', o.amb ?? 0.9));
  const t = new THREE.PointLight('#eef8e2', o.tube ?? 9, 9, 1.4); t.position.set(0.1, 2.55, -1.6); t.castShadow = true; t.shadow.mapSize.set(2048, 2048); t.shadow.bias = -0.002; t.shadow.radius = 3; scene.add(t);
  // weak fill from the landing window/door side so faces turned to the door read
  const f = new THREE.PointLight('#cfdcc8', o.fill ?? 1.4, 3.5, 1.5); f.position.set(0.2, 1.9, -0.35); scene.add(f);
}
function phoneLight(scene, pos, color = '#9fc4ff', intensity = 1.2) {
  const l = new THREE.PointLight(color, intensity, 1.6, 1.8); l.position.copy(pos); scene.add(l); return l;
}

window.PRICE = { THREE, PAL, buildWorld, makePerson, makeGlass, makePhone, makeOpenHand, lightsInterior, lightsStairwell, phoneLight, box, M };
