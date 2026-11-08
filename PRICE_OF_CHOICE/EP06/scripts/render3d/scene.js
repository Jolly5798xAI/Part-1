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
  sweater: '#b8863c', sweaterDk: '#9b6f2e', // EP04: the sister's mustard knit
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
  // EP03 tokens (combine with "_", e.g. "tape_tears_down"): tape over the mouth, tears, eyes down / to the side, wide eyes
  const tk = v.split('_');
  if (tk.includes('worried')) { f[5] = 'sssbbssssssbbsss'; f[4] = 'ssbsssssssssbsss'; }
  if (tk.includes('wide')) { f[4] = 'ssbbbssssssbbbss'; f[5] = 'ssssssssssssssss'; f[6] = 'ssswwsssssswwsss'; }
  if (tk.includes('down')) { f[7] = 'ssswwsssssswwsss'; f[8] = 'ssseesssssseesss'; }
  if (tk.includes('tape')) { f[11] = 'ssssGGGGGGGsssss'; f[12] = 'sssGGGGGGGGGssss'; f[13] = 'sssGGGGGGGGGssss'; f[14] = 'ssssGGGGGGGsssss'; }
  if (tk.includes('tears')) { const put = (r, c) => { f[r] = f[r].slice(0, c) + 'T' + f[r].slice(c + 1); }; for (const r of [9, 10, 11, 12]) { put(r, 3); put(r, 12); } }
  // EP04 tokens: mouth shapes for lip-sync on any face (open / ee / oo), skin reddened where the tape was ripped off,
  // eyes looking to the side (past the camera); 'pale' is applied to the colours in headMats()
  if (tk.includes('open') && v !== 'open') { f[12] = 'ssssssMOOMssssss'; f[13] = 'sssstMOOMttsssss'; }
  if (tk.includes('ee') && v !== 'ee') { f[12] = 'sssssMOOOOMsssss'; f[13] = 'sssstttttttsssss'; }
  if (tk.includes('oo') && v !== 'oo') { f[12] = 'sssssssMMsssssss'; f[13] = 'sssstttOOttsssss'; f[14] = 'ssssstMMMtssssss'; }
  if (tk.includes('side')) { f[7] = 'sssewssssssewsss'; f[8] = 'sssewssssssewsss'; }
  if (tk.includes('redmark')) for (const r of [11, 12, 13, 14]) f[r] = f[r].split('').map((ch, c) => (ch === 's' && c >= 3 && c <= 12) ? 'R' : ch).join('');
  // EP06 token 'old': the same face thirty years on — receding grey hairline, forehead lines, crow's feet, bags under the
  // eyes, nasolabial folds and grey stubble (colours in headMats). Applied last, only on bare skin, so mouth shapes still work.
  if (tk.includes('old')) {
    f[2] = 'HHHsHHHHHHHHsHHH'; f[3] = 'HssssHHsHHHsssHH';
    const put = (r, c, ch = 'd') => { if (f[r][c] === 's') f[r] = f[r].slice(0, c) + ch + f[r].slice(c + 1); };
    for (let c = 4; c <= 11; c++) put(4, c);                       // forehead line
    for (const [r, c] of [[7, 1], [8, 1], [7, 14], [8, 14], [9, 3], [9, 4], [9, 11], [9, 12], [11, 4], [12, 4], [11, 11], [12, 11]]) put(r, c);
    for (const r of [13, 14, 15]) for (let c = 2; c <= 13; c++) put(r, c, (r + c) % 2 ? 'g' : 's');   // stubble
  }
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

const FACE_MASK = [ // EP04: the officer's black balaclava — one eye slit
  'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk',
  'kksssssssssssskk', 'kksswesssssewsskk'.slice(0, 16), 'kksswesssssewssk', 'kksssssssssssskk', 'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk',
  'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk', 'kkkkkkkkkkkkkkkk',
];
FACE_MASK[7] = 'kksswesssssewssk'; FACE_MASK[8] = 'kksswesssssewssk';
const FACE_SISTER = [ // EP04: Alex's sister — same hair colour, longer hair framing the face, lashes, lips
  'HHHHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHHH', 'HHHHHHHHHHsHHHHH', 'HHHHsssssssssHHH', 'HsbbbssssssbbbsH',
  'HssssssssssssssH', 'HsLwessssssewLsH', 'HsswessssssewssH', 'HssssssssssssssH', 'HssssssnnssssssH', 'HsppsssssssssppH',
  'HssssssssssssssH', 'HssssrrrrrrssssH', 'HsssssrrrrsssssH', 'HHssssssssssssHH',
];
// EP05: the sister's face tokens (combine with "_"): worried brows, mouth shapes open / ee / oo for lip-sync, eyes down.
// 'neutral' returns FACE_SISTER unchanged, so EP04's sheet and photo are pixel-identical.
function sisterFace(v = 'neutral') {
  const f = FACE_SISTER.slice(); const tk = v.split('_');
  if (tk.includes('worried')) { f[4] = 'HHHbssssssssbHHH'; f[5] = 'HssbbssssssbbssH'; }
  if (tk.includes('down')) { f[7] = 'HsLsssssssssLssH'; f[8] = 'HsswwsssssswwssH'; }
  if (tk.includes('open')) { f[13] = 'HsssssrOOrsssssH'; f[14] = 'HsssssrOOrsssssH'; }
  if (tk.includes('ee')) { f[13] = 'HssssrOOOOrssssH'; f[14] = 'HsssssrrrrsssssH'; }
  if (tk.includes('oo')) { f[13] = 'HssssssOOssssssH'; f[14] = 'HsssssrrrrsssssH'; }
  // EP06 'cold': she no longer smiles — heavy lids, brows drawn down to the nose, a flat closed mouth
  if (tk.includes('cold')) { f[4] = 'HHHHsssssssssHHH'; f[5] = 'HsbbbbssssbbbbsH'; f[7] = 'HsLLLssssssLLLsH'; f[13] = 'HssssssssssssssH'; f[14] = 'HssssrrrrrrssssH'; }
  return f;
}
function headMats(kind, variant = 'neutral') {
  if (kind === 'cop' && variant.includes('mask')) {
    const L = { s: PAL.skinCop, w: PAL.eyeW, e: PAL.pupil, k: '#121214' };
    const blk = Array(16).fill('kkkkkkkkkkkkkkkk');
    return [MT(pixTex(blk, L)), MT(pixTex(blk, L)), MT(pixTex(blk, L)), MT(pixTex(blk, L)), MT(pixTex(FACE_MASK, L)), MT(pixTex(blk, L))];
  }
  if (kind === 'sister') {
    const L = { H: PAL.hairAlex, s: PAL.skinAlex, d: PAL.skinAlexSh, w: PAL.eyeW, e: PAL.pupil, b: PAL.brow, n: PAL.skinAlexSh, L: '#1b1b20', p: '#e2957f', r: '#b4524a' };
    const side = SIDE_ALEX.map(r => r.replace(/s/g, (m, i) => i < 12 ? 'H' : 's'));
    L.O = PAL.mouthIn;                                                 // EP05: mouth shapes for her lip-sync
    return [MT(pixTex(side.map(r => r.split('').reverse().join('')), L)), MT(pixTex(side, L)), MT(pixTex(ALL_H, L)), MT(pixTex(ALL_S, L)), MT(pixTex(sisterFace(variant), L)), MT(pixTex(ALL_H, L))];
  }
  if (kind === 'cop') {
    const L = { s: PAL.skinCop, d: PAL.skinCopSh, w: PAL.eyeW, e: PAL.pupil, b: PAL.brow, n: PAL.skinCopSh, K: PAL.mustache, H: PAL.skinCop };
    const side = SIDE_ALEX.map(r => r.replace(/H/g, 's'));
    return [MT(pixTex(side, L)), MT(pixTex(side, L)), MT(pixTex(ALL_S, L)), MT(pixTex(ALL_S, L)), MT(pixTex(FACE_COP, L)), MT(pixTex(ALL_S, L))];
  }
  const L = { H: PAL.hairAlex, s: PAL.skinAlex, d: PAL.skinAlexSh, t: '#c99372', w: PAL.eyeW, e: PAL.pupil, b: PAL.brow, n: PAL.skinAlexSh, M: PAL.mouth, O: PAL.mouthIn, G: '#a7a59b', T: '#8fd0f0' };
  L.R = '#d98a78';                                                   // EP04: reddened skin where the tape was
  if (variant.split('_').includes('old')) Object.assign(L, { H: '#9c9893', b: '#8b8580', d: '#a8775e', n: '#b98a6e', g: '#a99c92', t: '#c08c6c' }); // EP06
  if (variant.split('_').includes('pale')) Object.assign(L, { s: '#dcc0b0', d: '#c4a898', t: '#cdb0a0', n: '#c4a898', R: '#d9a596', M: '#6e4a46' });
  const face = variant === 'neutral' ? FACE_ALEX : faceVariant(FACE_ALEX, variant);
  // box material order: +x, -x, +y, -y, +z(front), -z(back)
  return [MT(pixTex(SIDE_ALEX.map(r => r.split('').reverse().join('')), L)), MT(pixTex(SIDE_ALEX, L)), MT(pixTex(ALL_H, L)), MT(pixTex(ALL_S, L)), MT(pixTex(face, L)), MT(pixTex(BACK_ALEX, L))];
}

const HOODIE_FRONT = [
  'GGGGGGGGGGGG', 'GGGgGGGGgGGG', 'GGGgGGGGgGGG', 'GGGwGGGGwGGG', 'GGGGGGzGGGGG', 'GGGGGGzGGGGG',
  'GGGGGGzGGGGG', 'GGggggggggGG', 'GGgGGGGGGgGG', 'GGgGGGGGGgGG', 'GGggggggggGG', 'gggggggggggg',
];
const SWEATER_FRONT = [ // EP04: knit sweater, white collar, small pendant
  'YYYYccccYYYY', 'YYYYYccYYYYY', 'YyYYYpYYYyYY', 'YYYyYYYYyYYY', 'YyYYYYYYYYyY', 'YYYyYYYYyYYY',
  'YyYYYYYYYYyY', 'YYYyYYYYyYYY', 'YyYYYYYYYYyY', 'YYYyYYYYyYYY', 'yyyyyyyyyyyy', 'YyYyYyYyYyYy',
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
  const isCop = kind === 'cop', isSis = kind === 'sister'; // EP04: 'sister' (Alex's sister, same blocky rig)
  const skin = isCop ? PAL.skinCop : PAL.skinAlex;
  const legH = 0.78, torsoH = 0.58, headS = 0.36;
  const pantsM = M(isCop ? PAL.copNavyDk : (isSis ? '#3c4a66' : PAL.jeans));
  const shoeM = M(isCop ? PAL.black : (isSis ? '#e6e3dc' : PAL.socks));
  const legL = new THREE.Group(); legL.position.set(-0.105, legH, 0); g.add(legL);
  const legR = new THREE.Group(); legR.position.set(0.105, legH, 0); g.add(legR);
  for (const L of [legL, legR]) { box(0.2, legH - 0.08, 0.22, pantsM, 0, -(legH - 0.08) / 2, 0, L); box(0.21, 0.08, 0.27, shoeM, 0, -legH + 0.04, 0.025, L); }
  const torsoFront = isCop
    ? pixTex(COP_FRONT, { N: PAL.copNavy, C: PAL.copShirt, y: PAL.gold, o: PAL.gold, k: PAL.black })
    : isSis ? pixTex(SWEATER_FRONT, { Y: PAL.sweater, y: PAL.sweaterDk, c: '#e9e4d6', p: '#c9a24a' })
    : pixTex(HOODIE_FRONT, { G: PAL.hoodie, g: PAL.hoodieDk, w: '#d8d8d8', z: '#3a3e44' });
  const tM = M(isCop ? PAL.copNavy : (isSis ? PAL.sweater : PAL.hoodie));
  const torso = box(0.44, torsoH, 0.25, [tM, tM, tM, tM, MT(torsoFront), tM], 0, legH + torsoH / 2, 0, g, 'torso');
  // head pivot at neck so head turns look right
  const headPivot = new THREE.Group(); headPivot.name = 'headPivot'; headPivot.position.set(0, legH + torsoH, 0); g.add(headPivot);
  const head = box(headS, headS, headS, headMats(kind === 'double' ? 'alex' : kind, o.face || 'neutral'), 0, headS / 2 + 0.01, 0, headPivot, 'head');
  if (isSis) { // EP04: long hair — crown, side locks to the shoulders, back panel
    const hairM = M(PAL.hairAlex);
    box(0.39, 0.06, 0.39, hairM, 0, headS + 0.03, -0.005, headPivot);
    box(0.06, 0.5, 0.2, hairM, -0.205, headS - 0.2, -0.07, headPivot); box(0.06, 0.5, 0.2, hairM, 0.205, headS - 0.2, -0.07, headPivot);
    box(0.4, 0.58, 0.07, hairM, 0, headS - 0.24, -0.205, headPivot);
    box(0.12, 0.05, 0.1, hairM, 0.09, headS + 0.06, 0.12, headPivot); // side-swept fringe
  } else if (!isCop) { // hair volume
    const hairM = M((o.face || '').split('_').includes('old') ? '#9c9893' : PAL.hairAlex); // EP06: old Alex is grey
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
  const sleeveM = M(isCop ? PAL.copNavy : (isSis ? PAL.sweater : PAL.hoodie));
  const handM = o.gloves ? M('#151517', { roughness: 0.6 }) : (o.bloodyRight ? MT(bloodHandTex(skin)) : M(skin)); // EP04: black gloves
  const handML = o.gloves ? M('#151517', { roughness: 0.6 }) : M(skin);
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
  // EP03: the right wall now has the bedroom doorway (z 2.5..3.3, h 2.05); split into three panels with the same wallpaper scale
  const BD = { z0: 2.5, z1: 3.3, h: 2.05 };
  const wallSeg = (z0, z1, y0, y1) => {
    const t = wpTex.clone(); t.needsUpdate = true; t.repeat.set((z1 - z0) / E.z1 * 6, (y1 - y0) / E.h * 3); t.offset.set(z0 / E.z1 * 6, y0 / E.h * 3);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(z1 - z0, y1 - y0), MT(t)); m.rotation.y = -Math.PI / 2; m.position.set(E.x1, (y0 + y1) / 2, (z0 + z1) / 2); m.receiveShadow = true; scene.add(m); return m;
  };
  wallSeg(0, BD.z0, 0, E.h); wallSeg(BD.z1, E.z1, 0, E.h); wallSeg(BD.z0, BD.z1, BD.h, E.h);
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
  box(0.02, 0.08, E.z1, bbM, E.x0 + 0.01, 0.04, E.z1 / 2, scene); box(0.02, 0.08, BD.z0, bbM, E.x1 - 0.01, 0.04, BD.z0 / 2, scene); box(0.02, 0.08, E.z1 - BD.z1, bbM, E.x1 - 0.01, 0.04, (BD.z1 + E.z1) / 2, scene);

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
  // EP03: the hall mirror becomes a full-size one (0.62 x 1.0 m, same wall, same place); it was never in frame in EP01/EP02
  box(0.03, 1.08, 0.7, M('#2c2f33'), E.x0 + 0.02, 1.38, 2.3, scene); // mirror frame
  const mirror = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 1.0), new THREE.MeshStandardMaterial({ color: '#56656e', roughness: 0.05, metalness: 0.8 })); mirror.rotation.y = Math.PI / 2; mirror.position.set(E.x0 + 0.04, 1.38, 2.3); scene.add(mirror);
  box(0.08, 0.08, 0.015, M('#e8e5dc'), 0.6, 1.1, 0.008, scene); // light switch
  // ceiling lamp (off)
  const lampShade = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.2, 0.12, 6), M('#e9e2c8')); lampShade.position.set(0.15, E.h - 0.2, 1.6); scene.add(lampShade);
  box(0.01, 0.14, 0.01, M('#333'), 0.15, E.h - 0.07, 1.6, scene);

  // ===== stairwell landing (z from 0 to -3.2) =====
  // EP05: grouped (identity transform, same geometry) so the hotel-corridor shots can hide it
  const SW = new THREE.Group(); SW.name = 'stairwell'; scene.add(SW);
  const S = { x0: -2.4, x1: 2.3, z0: -3.2, h: 2.75 };
  const tileTex = canvasTex(128, 128, (g, w, h) => { for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.fillStyle = (x + y) % 2 ? PAL.hallTile1 : PAL.hallTile2; g.fillRect(x * 32, y * 32, 32, 32); } g.fillStyle = 'rgba(0,0,0,0.15)'; for (let i = 0; i <= 4; i++) { g.fillRect(i * 32 - 1, 0, 2, h); g.fillRect(0, i * 32 - 1, w, 2); } }, { repeat: [6, 4], nearest: true });
  const hallWall = canvasTex(64, 256, (g, w, h) => { g.fillStyle = PAL.hallWhite; g.fillRect(0, 0, w, h); g.fillStyle = PAL.hallGreen; g.fillRect(0, h * 0.42, w, h); g.fillStyle = '#3b5b44'; g.fillRect(0, h * 0.42, w, 6); const r = mulberry(11); for (let i = 0; i < 18; i++) { g.fillStyle = 'rgba(40,50,40,' + (r() * 0.18) + ')'; g.fillRect(r() * w, h * 0.42 + r() * h * 0.58, 4 + r() * 10, 4 + r() * 10); } }, { repeat: [5, 1] });
  const hwM = MT(hallWall);
  const hf = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, -S.z0), MT(tileTex)); hf.rotation.x = -Math.PI / 2; hf.position.set((S.x0 + S.x1) / 2, 0, S.z0 / 2); hf.receiveShadow = true; SW.add(hf);
  const hc = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, -S.z0), M('#cfccbf')); hc.rotation.x = Math.PI / 2; hc.position.set((S.x0 + S.x1) / 2, S.h, S.z0 / 2); SW.add(hc);
  // far wall (z = S.z0) — the man stands facing it
  const fw = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, S.h), hwM); fw.position.set((S.x0 + S.x1) / 2, S.h / 2, S.z0); fw.receiveShadow = true; SW.add(fw);
  const sl = new THREE.Mesh(new THREE.PlaneGeometry(-S.z0, S.h), hwM); sl.rotation.y = Math.PI / 2; sl.position.set(S.x0, S.h / 2, S.z0 / 2); sl.receiveShadow = true; SW.add(sl);
  const sr = new THREE.Mesh(new THREE.PlaneGeometry(-S.z0, S.h), hwM); sr.rotation.y = -Math.PI / 2; sr.position.set(S.x1, S.h / 2, S.z0 / 2); sr.receiveShadow = true; SW.add(sr);
  // outside face of front wall
  const ow = new THREE.Mesh(new THREE.PlaneGeometry(S.x1 - S.x0, S.h), hwM); ow.rotation.y = Math.PI; ow.position.set((S.x0 + S.x1) / 2, S.h / 2, -0.2005); SW.add(ow);
  // neighbour door on the far-left wall + electrical panel + stair rail opening
  box(0.9, 2.05, 0.06, M('#5e4b3c'), -1.45, 1.025, S.z0 + 0.03, SW);
  box(0.03, 0.03, 0.04, M(PAL.steel, { metalness: 0.6 }), -1.1, 1.0, S.z0 + 0.07, SW);
  box(0.12, 0.08, 0.01, M('#c9c3a8'), -1.45, 1.75, S.z0 + 0.065, SW); // number plate (blank)
  box(0.55, 0.75, 0.12, M('#6f7a6c'), 1.65, 1.55, S.z0 + 0.06, SW); // electrical panel
  box(0.5, 0.02, 0.02, M('#3b3b3b'), 1.65, 1.15, S.z0 + 0.13, SW);
  // radiator under window on left side wall
  for (let i = 0; i < 6; i++) box(0.06, 0.55, 0.09, M('#d8d4c8'), S.x0 + 0.06, 0.55, -2.2 + i * 0.08, SW);
  // fluorescent tube
  const tube = box(1.1, 0.05, 0.08, new THREE.MeshBasicMaterial({ color: '#f1fbe8' }), 0.1, S.h - 0.04, -1.6, SW); tube.castShadow = false;
  box(1.2, 0.03, 0.14, M('#bcbab0'), 0.1, S.h - 0.01, -1.6, SW);

  const bed = buildBedroom(scene, E, BD, { wpTex, lamTex, ceilM, caseM, bbM });
  W.objs = { doorPivot, door, lock, lever, leak, E, S, mirror, BD, bed, stairwell: SW };
  return W;
}

// ====================================================================== EP03 additions
// Bedroom behind the doorway in the entryway's right wall (x > 1.05). Same low-poly language, colder wallpaper.
function buildBedroom(scene, E, BD, T) {
  const R = { x0: E.x1, x1: 4.05, z0: 1.55, z1: 4.6, h: E.h };
  const bwTex = canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#6b7079'; g.fillRect(0, 0, w, h); g.fillStyle = '#5f646c'; for (let x = 0; x < w; x += 32) g.fillRect(x, 0, 10, h); g.fillStyle = '#7a7f88'; for (let y = 16; y < h; y += 32) for (let x = 2; x < w; x += 32) g.fillRect(x, y, 6, 6); }, { repeat: [5, 3] });
  const bwM = MT(bwTex);
  const lt = T.lamTex.clone(); lt.needsUpdate = true; lt.repeat.set(3, 3);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(R.x1 - R.x0, R.z1 - R.z0), MT(lt)); fl.rotation.x = -Math.PI / 2; fl.position.set((R.x0 + R.x1) / 2, 0, (R.z0 + R.z1) / 2); fl.receiveShadow = true; scene.add(fl);
  const ce = new THREE.Mesh(new THREE.PlaneGeometry(R.x1 - R.x0, R.z1 - R.z0), T.ceilM); ce.rotation.x = Math.PI / 2; ce.position.set((R.x0 + R.x1) / 2, R.h, (R.z0 + R.z1) / 2); scene.add(ce);
  // wall shared with the entryway (bedroom side), with the doorway
  const t = 0.09, xw = R.x0 + 0.005 + t / 2;
  box(t, R.h, BD.z0 - R.z0, bwM, xw, R.h / 2, (R.z0 + BD.z0) / 2, scene); box(t, R.h, R.z1 - BD.z1, bwM, xw, R.h / 2, (BD.z1 + R.z1) / 2, scene);
  box(t, R.h - BD.h, BD.z1 - BD.z0, bwM, xw, (BD.h + R.h) / 2, (BD.z0 + BD.z1) / 2, scene);
  // side walls + far wall with the window (z 2.55..3.55, y 0.85..2.05)
  box(R.x1 - R.x0, R.h, 0.1, bwM, (R.x0 + R.x1) / 2, R.h / 2, R.z0 - 0.05, scene);
  box(R.x1 - R.x0, R.h, 0.1, bwM, (R.x0 + R.x1) / 2, R.h / 2, R.z1 + 0.05, scene);
  const W0 = { z0: 2.55, z1: 3.55, y0: 0.85, y1: 2.05 };
  box(0.1, R.h, W0.z0 - R.z0, bwM, R.x1 + 0.05, R.h / 2, (R.z0 + W0.z0) / 2, scene); box(0.1, R.h, R.z1 - W0.z1, bwM, R.x1 + 0.05, R.h / 2, (W0.z1 + R.z1) / 2, scene);
  box(0.1, W0.y0, W0.z1 - W0.z0, bwM, R.x1 + 0.05, W0.y0 / 2, (W0.z0 + W0.z1) / 2, scene); box(0.1, R.h - W0.y1, W0.z1 - W0.z0, bwM, R.x1 + 0.05, (W0.y1 + R.h) / 2, (W0.z0 + W0.z1) / 2, scene);
  // night sky behind the window + frame cross + sill
  const sky = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 1.6), new THREE.MeshBasicMaterial({ color: '#1a2a48' })); sky.rotation.y = -Math.PI / 2; sky.position.set(R.x1 + 0.4, 1.45, 3.05); scene.add(sky);
  const frM = M('#d9d6cc');
  box(0.05, W0.y1 - W0.y0, 0.05, frM, R.x1 + 0.03, (W0.y0 + W0.y1) / 2, 3.05, scene); box(0.05, 0.05, W0.z1 - W0.z0, frM, R.x1 + 0.03, 1.55, 3.05, scene);
  box(0.16, 0.04, W0.z1 - W0.z0 + 0.1, frM, R.x1 - 0.05, W0.y0 - 0.02, 3.05, scene);
  // curtains (half drawn)
  const cuM = M('#3b3f5a');
  box(0.06, 1.75, 0.3, cuM, R.x1 - 0.1, 1.5, W0.z0 - 0.05, scene); box(0.06, 1.75, 0.3, cuM, R.x1 - 0.1, 1.5, W0.z1 + 0.05, scene);
  // bed against the far side wall (z1), blanket, pillow
  box(1.3, 0.3, 1.05, M('#5a4030'), 3.25, 0.15, 4.05, scene); box(1.26, 0.14, 1.0, M('#8b8f9e'), 3.25, 0.37, 4.05, scene);
  box(0.4, 0.1, 0.7, M('#d6d3c8'), 3.7, 0.49, 4.05, scene); box(0.08, 0.75, 1.05, M('#4a3426'), 3.93, 0.375, 4.05, scene);
  // nightstand + lamp (off), wardrobe, rug
  box(0.4, 0.45, 0.38, M('#5a4030'), 3.7, 0.225, 3.25, scene);
  const lamp = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 0.16, 6), M('#cfc6a8')); lamp.position.set(3.7, 0.62, 3.25); scene.add(lamp);
  box(1.0, 2.1, 0.55, M('#4e3a2c'), 2.0, 1.05, R.z0 + 0.3, scene); box(0.01, 1.9, 0.01, M('#2d2018'), 2.0, 1.05, R.z0 + 0.58, scene);
  box(1.4, 0.01, 1.0, M('#5b2c2c'), 2.45, 0.005, 3.0, scene);
  box(t, 0.08, 0.02, T.bbM, R.x1 - 0.01, 0.04, R.z0 + 0.2, scene);
  // casing on the entryway side + interior door (hinge at z = BD.z1, opens into the bedroom)
  box(0.03, BD.h + 0.06, 0.06, T.caseM, E.x1 - 0.015, (BD.h + 0.06) / 2, BD.z0 - 0.03, scene); box(0.03, BD.h + 0.06, 0.06, T.caseM, E.x1 - 0.015, (BD.h + 0.06) / 2, BD.z1 + 0.03, scene);
  box(0.03, 0.06, BD.z1 - BD.z0 + 0.12, T.caseM, E.x1 - 0.015, BD.h + 0.03, (BD.z0 + BD.z1) / 2, scene);
  const pivot = new THREE.Group(); pivot.position.set(E.x1 + 0.03, 0, BD.z0 + 0.01); scene.add(pivot); // hinge on the wardrobe side
  const pTex = canvasTex(128, 256, (g, w, h) => { g.fillStyle = '#c9c4b6'; g.fillRect(0, 0, w, h); g.strokeStyle = '#a9a496'; g.lineWidth = 6; g.strokeRect(16, 16, w - 32, h * 0.42); g.strokeRect(16, h * 0.5, w - 32, h * 0.46); });
  const pM = MT(pTex), pS = M('#a9a496');
  const bdoor = box(0.04, BD.h - 0.01, BD.z1 - BD.z0 - 0.02, [pM, pM, pS, pS, pS, pS], 0, (BD.h - 0.01) / 2, (BD.z1 - BD.z0) / 2, pivot, 'bedroomDoor');
  const knM = M(PAL.brass, { metalness: 0.65, roughness: 0.35 });
  for (const sx of [-1, 1]) { box(0.05, 0.03, 0.12, knM, sx * 0.04, 1.0, (BD.z1 - BD.z0) - 0.12, pivot); }
  // light leak under the bedroom door (colour/intensity set by shots)
  const bleak = new THREE.Mesh(new THREE.PlaneGeometry(BD.z1 - BD.z0 - 0.04, 0.012), new THREE.MeshBasicMaterial({ color: '#000000' }));
  bleak.rotation.y = -Math.PI / 2; bleak.position.set(E.x1 - 0.002, 0.006, (BD.z0 + BD.z1) / 2); scene.add(bleak);
  return { R, pivot, bdoor, bleak, W0 };
}

// Planar mirror (three.js r160 Reflector, ported to the global THREE build). The virtual camera can see extra
// layers, so objects on layer 1 exist ONLY in the reflection — that is how the second Alex appears in the mirror.
function makeMirror(geometry, o = {}) {
  const mesh = new THREE.Mesh(geometry); mesh.name = 'mirrorReflector';
  const vcam = new THREE.PerspectiveCamera(); if (o.layers) o.layers.forEach(l => vcam.layers.enable(l));
  const rt = new THREE.WebGLRenderTarget(o.tw || 1024, o.th || 1024, { samples: 4, type: THREE.HalfFloatType });
  const textureMatrix = new THREE.Matrix4();
  mesh.material = new THREE.ShaderMaterial({
    uniforms: { tDiffuse: { value: rt.texture }, textureMatrix: { value: textureMatrix }, tint: { value: new THREE.Color(o.tint || '#e2ebe7') } },
    vertexShader: 'uniform mat4 textureMatrix; varying vec4 vUv; void main(){ vUv = textureMatrix * vec4(position,1.0); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'uniform vec3 tint; uniform sampler2D tDiffuse; varying vec4 vUv; void main(){ vec4 b = texture2DProj(tDiffuse, vUv); gl_FragColor = vec4(b.rgb * tint, 1.0);\n#include <tonemapping_fragment>\n#include <colorspace_fragment>\n}',
  });
  const plane = new THREE.Plane(), normal = new THREE.Vector3(), rp = new THREE.Vector3(), cp = new THREE.Vector3(), rot = new THREE.Matrix4();
  const look = new THREE.Vector3(), clip = new THREE.Vector4(), view = new THREE.Vector3(), target = new THREE.Vector3(), q = new THREE.Vector4();
  mesh.onBeforeRender = function (renderer, scene, camera) {
    rp.setFromMatrixPosition(mesh.matrixWorld); cp.setFromMatrixPosition(camera.matrixWorld);
    rot.extractRotation(mesh.matrixWorld); normal.set(0, 0, 1).applyMatrix4(rot);
    view.subVectors(rp, cp); if (view.dot(normal) > 0) return;
    view.reflect(normal).negate().add(rp);
    rot.extractRotation(camera.matrixWorld); look.set(0, 0, -1).applyMatrix4(rot).add(cp);
    target.subVectors(rp, look).reflect(normal).negate().add(rp);
    vcam.position.copy(view); vcam.up.set(0, 1, 0).applyMatrix4(rot).reflect(normal); vcam.lookAt(target);
    vcam.far = camera.far; vcam.updateMatrixWorld(); vcam.projectionMatrix.copy(camera.projectionMatrix);
    textureMatrix.set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1);
    textureMatrix.multiply(vcam.projectionMatrix).multiply(vcam.matrixWorldInverse).multiply(mesh.matrixWorld);
    plane.setFromNormalAndCoplanarPoint(normal, rp).applyMatrix4(vcam.matrixWorldInverse);
    clip.set(plane.normal.x, plane.normal.y, plane.normal.z, plane.constant);
    const pm = vcam.projectionMatrix;
    q.x = (Math.sign(clip.x) + pm.elements[8]) / pm.elements[0]; q.y = (Math.sign(clip.y) + pm.elements[9]) / pm.elements[5]; q.z = -1; q.w = (1 + pm.elements[10]) / pm.elements[14];
    clip.multiplyScalar(2 / clip.dot(q));
    pm.elements[2] = clip.x; pm.elements[6] = clip.y; pm.elements[10] = clip.z + 1; pm.elements[14] = clip.w;
    mesh.visible = false;
    const cur = renderer.getRenderTarget(), sau = renderer.shadowMap.autoUpdate;
    renderer.shadowMap.autoUpdate = false; renderer.setRenderTarget(rt); renderer.state.buffers.depth.setMask(true);
    if (renderer.autoClear === false) renderer.clear();
    renderer.render(scene, vcam);
    renderer.shadowMap.autoUpdate = sau; renderer.setRenderTarget(cur);
    if (camera.viewport !== undefined) renderer.state.viewport(camera.viewport);
    mesh.visible = true;
  };
  mesh.dispose = () => { rt.dispose(); mesh.material.dispose(); };
  return mesh;
}
// swap the entryway's flat grey mirror for the real reflector (same size and place)
function enableMirror(W, o = {}) {
  const old = W.objs.mirror; old.visible = false;
  const m = makeMirror(new THREE.PlaneGeometry(0.62, 1.0), Object.assign({ tw: 1240, th: 2000, layers: [1] }, o));
  m.position.copy(old.position); m.rotation.copy(old.rotation); m.position.x += 0.0005; W.scene.add(m); W.objs.reflector = m; return m;
}
// an object that exists only in the reflection
function mirrorOnly(obj) { obj.traverse(o => o.layers.set(1)); return obj; }

// wet footprint (blocky bare foot, toes point to local -z); side -1 left / +1 right
function makeFootprint(side = 1, o = {}) {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: '#41697c', emissive: '#071a22', roughness: 0.06, metalness: 0.0, transparent: true, opacity: o.opacity ?? 0.82, flatShading: true, depthWrite: false });
  const add = (w, d, x, z) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, 0.002, d), m); b.position.set(x * side, 0, z); b.receiveShadow = true; g.add(b); };
  add(0.062, 0.075, 0.0, 0.085); add(0.042, 0.06, 0.012, 0.02); add(0.082, 0.085, 0.004, -0.05);
  [[-0.03, -0.115, 0.026], [-0.006, -0.112, 0.016], [0.012, -0.108, 0.015], [0.027, -0.1, 0.014], [0.04, -0.09, 0.012]].forEach(([x, z, s]) => add(s, s, x, z));
  // a few droplets around the print
  const r = mulberry(Math.floor((o.seed ?? 1) * 1000));
  for (let i = 0; i < 3; i++) add(0.008 + r() * 0.008, 0.008 + r() * 0.008, (r() - 0.5) * 0.16, (r() - 0.5) * 0.26);
  g.userData.mat = m;
  return g;
}
// lay a trail: steps = [[x, z, heading(rad, 0 = toes toward -z), side], ...]; k = how many are visible (fractional fades the last one in)
function footprints(scene, steps, k = steps.length, o = {}) {
  steps.forEach(([x, z, a, side], i) => {
    const vis = Math.max(0, Math.min(1, k - i)); if (vis <= 0) return;
    const f = makeFootprint(side, { seed: i + 1 + (o.seed || 0), opacity: (o.opacity ?? 0.82) * vis });
    const onMat = x > -0.36 && x < 0.36 && z > 0.15 && z < 0.61;
    f.position.set(x, onMat ? 0.0145 : 0.0022, z); f.rotation.y = a; scene.add(f);
  });
}

// wooden chair, seat top at 0.46; faces local +z
function makeChair() {
  const g = new THREE.Group(); g.name = 'chair'; const w = M('#5e4330'), wd = M('#4a3425');
  box(0.46, 0.05, 0.44, w, 0, 0.435, 0, g);
  for (const [x, z] of [[-0.2, -0.19], [0.2, -0.19], [-0.2, 0.19], [0.2, 0.19]]) box(0.045, 0.41, 0.045, wd, x, 0.205, z, g);
  for (const x of [-0.2, 0.2]) box(0.045, 0.55, 0.045, wd, x, 0.73, -0.2, g);
  box(0.46, 0.09, 0.04, w, 0, 0.92, -0.2, g); box(0.46, 0.06, 0.035, w, 0, 0.7, -0.2, g);
  return g;
}
// seat a makePerson figure on a chair (no knees in the standing rig, so legs are rebuilt as thigh + shin)
function seatPerson(p, o = {}) {
  const legH = 0.78, seat = 0.47; p.position.y = seat - legH;
  p.userData.legL.visible = false; p.userData.legR.visible = false;
  const pantsM = M(PAL.jeans), shoeM = M(PAL.socks);
  for (const sx of [-1, 1]) {
    box(0.2, 0.2, 0.46, pantsM, sx * 0.105, legH, 0.2, p);
    box(0.2, 0.44, 0.22, pantsM, sx * 0.105, legH - 0.24, 0.41, p);
    box(0.21, 0.08, 0.27, shoeM, sx * 0.105, legH - 0.47 + 0.04, 0.44, p);
  }
  // arms pulled behind the chair back
  for (const side of [-1, 1]) { const a = p.userData.arms[side]; a.rotation.x = 0.55; a.rotation.z = side * 0.12; }
  return p;
}
// ropes around chest, arms and ankles (world group positioned with the chair)
function makeRopes() {
  const g = new THREE.Group(); const rM = M('#b39662'), rD = M('#8f7546');
  for (const [y, m] of [[1.02, rM], [0.9, rD], [0.8, rM]]) { box(0.66, 0.035, 0.05, m, 0, y, 0.15, g); box(0.035, 0.035, 0.42, m, -0.33, y, -0.05, g); box(0.035, 0.035, 0.42, m, 0.33, y, -0.05, g); box(0.66, 0.035, 0.05, m, 0, y, -0.24, g); }
  box(0.04, 0.24, 0.04, rD, 0.0, 0.86, 0.15, g); // knot
  for (const sx of [-1, 1]) { box(0.26, 0.035, 0.26, rM, sx * 0.105, 0.17, 0.41, g); box(0.035, 0.12, 0.035, rD, sx * 0.2, 0.25, 0.25, g); }
  box(0.5, 0.035, 0.05, rM, 0, 0.62, -0.32, g); // wrists bound behind the back
  return g;
}
// the second phone (the one ringing inside the bedroom) lies on the floor, screen up

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

// ====================================================================== EP04 additions
// The scar: ONE texture function, so Alex's and the double's scars are pixel-identical. A diagonal raised line across
// the inner wrist with four stitch marks (16 x 32 pixel art, mapped onto the inner face of a forearm).
function scarTex(skin = PAL.skinAlex) {
  return canvasTex(64, 128, (g) => {
    const px = (x, y, c) => { g.fillStyle = c; g.fillRect(x * 4, y * 4, 4, 4); };
    g.fillStyle = skin; g.fillRect(0, 0, 64, 128);
    for (let i = 0; i <= 11; i++) { const x = 2 + i, y = 24 - Math.round(i * 0.5); px(x, y, '#9c3e37'); px(x, y + 1, '#c9665a'); px(x, y + 2, '#eaa792'); }
    for (const i of [1, 4, 7, 10]) { const x = 2 + i, y = 24 - Math.round(i * 0.5); px(x, y - 1, '#7a2e29'); px(x, y + 3, '#7a2e29'); }
  }, { nearest: true });
}
// forearm with the hoodie sleeve pushed up: elbow at the origin, hand at local y ≈ -0.5; the inner wrist is the +z face.
// o.scar (default true), o.sleeve colour, o.grip (0..1 curls the fingers round something), o.bound (rope round the wrist)
function makeForearm(o = {}) {
  const g = new THREE.Group(); const skin = M(PAL.skinAlex);
  box(0.18, 0.13, 0.2, M(o.sleeve || PAL.hoodie), 0, -0.02, 0, g);                       // pushed-up sleeve
  box(0.18, 0.04, 0.2, M(PAL.hoodieDk), 0, -0.09, 0, g);                                // its rolled cuff
  const fm = o.scar === false ? skin : MT(scarTex());
  box(0.13, 0.34, 0.14, [skin, skin, skin, skin, fm, skin], 0, -0.27, 0, g, 'forearm');  // inner face (+z) carries the scar
  const hand = new THREE.Group(); hand.position.set(0, -0.44, 0); g.add(hand);
  box(0.15, 0.13, 0.1, skin, 0, -0.06, -0.005, hand, 'palm');
  const k = o.grip || 0;
  for (let i = 0; i < 4; i++) {
    const f = new THREE.Group(); f.position.set(-0.052 + i * 0.035, -0.125, 0.0); hand.add(f); f.rotation.x = 1.5 * k;
    box(0.028, 0.075 - (i === 3 ? 0.015 : 0), 0.03, skin, 0, -0.035, 0, f);
  }
  const th = box(0.03, 0.06, 0.03, skin, 0.085, -0.04, 0.03, hand); th.rotation.z = -0.4 - 0.6 * k;
  if (o.bound) { const rM = M('#b39662'), rD = M('#8f7546'); box(0.175, 0.035, 0.13, rM, 0, -0.47, -0.005, g); box(0.175, 0.035, 0.13, rD, 0, -0.51, -0.005, g); } // rope round the hand, below the scar
  return g;
}
// 5 x 7 pixel digits for door number plates (no fonts in the 3D world)
const DIGITS = {
  '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'], '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
  '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
};
function plateTex(text, fg = '#e8e2cf', bg = '#1d2a33') {
  const rows = Array.from({ length: 11 }, () => '');
  for (let r = 0; r < 11; r++) rows[r] = '..';
  for (const ch of text) { const d = DIGITS[ch]; for (let r = 0; r < 11; r++) rows[r] += (r >= 2 && r < 9 ? d[r - 2] : '.....') + '.'; }
  for (let r = 0; r < 11; r++) rows[r] += '.';
  return pixTex(rows, { '.': bg, '#': fg }, { scale: 12 });
}

// ====================================================================== EP05 additions «КОМНАТА 204»
// The key of room 204: an old brass hotel key on a ring with a burgundy fob carrying «204» in the same 5x7 pixel digits
// as the EP04 door plate (no fonts in the 3D world). Origin = top of the ring, the key hangs along local -y, the fob's
// +z face is the readable one. userData.fob is the fob's pivot (at the ring) so shots can let it hang straight down.
function makeKey(o = {}) {
  const g = new THREE.Group(); g.name = 'key204';
  const brass = M('#c9a24a', { metalness: 0.75, roughness: 0.32 }), dark = M('#5c4718', { metalness: 0.5, roughness: 0.5 });
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; const b = box(0.011, 0.004, 0.004, brass, Math.cos(a) * 0.019, -0.019 + Math.sin(a) * 0.019, 0, g); b.rotation.z = a + Math.PI / 2; }
  const key = new THREE.Group(); key.position.set(-0.008, -0.036, 0); key.rotation.z = 0.06; g.add(key);
  box(0.036, 0.032, 0.006, brass, 0, -0.016, 0, key); box(0.014, 0.012, 0.0075, dark, 0, -0.012, 0, key);     // bow with a dark eye
  box(0.007, 0.07, 0.007, brass, 0, -0.066, 0, key);                                                             // shaft
  box(0.016, 0.008, 0.005, brass, 0.009, -0.086, 0, key); box(0.012, 0.007, 0.005, brass, 0.008, -0.097, 0, key); // bit (teeth)
  box(0.009, 0.006, 0.005, brass, 0.007, -0.075, 0, key);
  const fob = new THREE.Group(); fob.position.set(0.006, -0.036, 0.007); g.add(fob);
  box(0.006, 0.016, 0.004, brass, 0, -0.008, 0, fob);                                                            // brass link
  const red = M('#6e1a1c', { roughness: 0.55 }), face = MT(plateTex('204', '#efe4c4', '#6e1a1c'), { roughness: 0.55 });
  const tag = box(0.084, 0.044, 0.008, [red, red, red, red, face, face], 0.012, -0.04, 0, fob, 'fob');
  tag.rotation.z = o.fobTilt ?? -0.12;
  g.userData = { key, fob, tag };
  return g;
}
// Door 204 — EXACTLY the EP04 insert's door (E4_room204: painted metal, dark number plate «204», same sizes and colours),
// now hinged so it can open (hinge on the right, handle on the left as in EP04) and with a keyhole under the handle.
// The EP04 backing panel is rebuilt as a surround (left/right/top strips, same outer size) so the doorway is open behind it.
function makeDoor204() {
  const g = new THREE.Group(); g.name = 'door204';
  const fr = M('#3c464c');
  box(0.05, 2.16, 0.03, fr, -0.515, 1.08, 0.012, g); box(0.05, 2.16, 0.03, fr, 0.515, 1.08, 0.012, g); box(1.08, 0.06, 0.03, fr, 0, 2.13, 0.012, g);
  const pivot = new THREE.Group(); pivot.position.set(0.49, 0, 0.03); g.add(pivot);
  const steel = M('#9aa0a6', { metalness: 0.7, roughness: 0.3 });
  box(0.98, 2.1, 0.05, M('#56636b', { roughness: 0.6, metalness: 0.3 }), -0.49, 1.05, 0, pivot, 'door');
  box(0.12, 0.03, 0.05, steel, -0.49 - 0.36, 1.0, 0.05, pivot);
  const pm = M('#1d2a33');
  box(0.26, 0.13, 0.012, [pm, pm, pm, pm, MT(plateTex('204')), pm], -0.49, 1.62, 0.032, pivot, 'plate');
  box(0.034, 0.064, 0.008, steel, -0.49 - 0.36, 0.9, 0.029, pivot); box(0.007, 0.024, 0.004, M('#0a0a0a'), -0.49 - 0.36, 0.9, 0.034, pivot, 'keyhole');
  return { group: g, pivot };
}
// The hotel corridor that replaces the stairwell behind flat 47's front door (EP05). Straight ahead from the door, 13 m long,
// two-tone walls in the EP04 door-204 palette, wooden room doors, sconces, a burgundy runner; at the far end door 204 under a
// caged red lamp; behind it room 204 with a table covered in phones. Reusable: buildCorridor(W, {L, sconces, red, phonesOn}).
function buildCorridor(W, o = {}) {
  const scene = W.scene, L = o.L ?? 13, X = 0.8, H = 2.5, z0 = -0.2;
  if (W.objs.stairwell) W.objs.stairwell.visible = false;
  const C = new THREE.Group(); C.name = 'corridor'; scene.add(C);
  const len = L + z0, zc = (z0 - L) / 2;
  const wallTex = (rep) => canvasTex(64, 256, (g, w, h) => {
    g.fillStyle = '#c9c7b4'; g.fillRect(0, 0, w, h); g.fillStyle = '#bebca8'; for (let x = 0; x < w; x += 16) g.fillRect(x, 0, 5, h * 0.45);
    g.fillStyle = '#5e7b72'; g.fillRect(0, h * 0.62, w, h); g.fillStyle = '#3d564f'; g.fillRect(0, h * 0.62, w, 6); g.fillRect(0, h - 10, w, 10);
  }, { repeat: [rep, 1] });
  const wl = new THREE.Mesh(new THREE.PlaneGeometry(len, H), MT(wallTex(len / 1.2))); wl.rotation.y = Math.PI / 2; wl.position.set(-X, H / 2, zc); wl.receiveShadow = true; C.add(wl);
  const wr = new THREE.Mesh(new THREE.PlaneGeometry(len, H), MT(wallTex(len / 1.2))); wr.rotation.y = -Math.PI / 2; wr.position.set(X, H / 2, zc); wr.receiveShadow = true; C.add(wr);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(2 * X, len), M('#33251c')); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, zc); fl.receiveShadow = true; C.add(fl);
  const runT = canvasTex(64, 128, (g, w, h) => {
    g.fillStyle = '#5a1418'; g.fillRect(0, 0, w, h); g.fillStyle = '#9c7a36'; g.fillRect(4, 0, 3, h); g.fillRect(w - 7, 0, 3, h);
    g.fillStyle = '#7a2228'; for (let y = 0; y < h; y += 32) { g.beginPath(); g.moveTo(w / 2, y + 4); g.lineTo(w - 16, y + 16); g.lineTo(w / 2, y + 28); g.lineTo(16, y + 16); g.fill(); }
    g.fillStyle = '#9c7a36'; for (let y = 0; y < h; y += 32) g.fillRect(w / 2 - 2, y + 14, 4, 4);
  }, { repeat: [1, len / 0.9], nearest: true });
  const run = new THREE.Mesh(new THREE.PlaneGeometry(1.0, len), MT(runT)); run.rotation.x = -Math.PI / 2; run.position.set(0, 0.003, zc); run.receiveShadow = true; C.add(run);
  const ce = new THREE.Mesh(new THREE.PlaneGeometry(2 * X, len), M('#a9a594')); ce.rotation.x = Math.PI / 2; ce.position.set(0, H, zc); C.add(ce);
  const wM = MT(wallTex(1.4));
  // the corridor side of flat 47's front wall (door opening x[-0.45,0.45], y[0,2.08])
  box(X - 0.45, H, 0.02, wM, -(X + 0.45) / 2, H / 2, z0 - 0.01, C); box(X - 0.45, H, 0.02, wM, (X + 0.45) / 2, H / 2, z0 - 0.01, C); box(0.9, H - 2.08, 0.02, wM, 0, (H + 2.08) / 2, z0 - 0.01, C);
  // wooden room doors along both walls (blank brass plates: only 204 has a number anyone can read)
  const wood = M('#4a3226'), woodDk = M('#2e1f17'), brass = M('#c9a24a', { metalness: 0.65, roughness: 0.35 });
  const doors = [[-1, -2.1], [1, -3.5], [-1, -5.0], [1, -6.4], [-1, -7.9], [1, -9.3], [-1, -10.7], [1, -11.7]];
  for (const [sd, z] of doors) {
    if (z < -L + 0.9) continue; const x = sd * (X - 0.03);
    box(0.05, 2.08, 0.96, woodDk, x, 1.04, z, C); box(0.06, 2.0, 0.84, wood, x - sd * 0.01, 1.0, z, C);
    box(0.02, 0.06, 0.12, brass, x - sd * 0.045, 1.0, z + 0.3, C); box(0.015, 0.07, 0.12, brass, x - sd * 0.042, 1.62, z, C);
  }
  // sconces between the doors (warm, dim; only o.sconces of them lit)
  const lit = o.sconces ?? 0; let n = 0;
  for (const [sd, z] of [[-1, -1.2], [1, -2.8], [-1, -4.2], [1, -5.7], [-1, -7.1], [1, -8.6], [-1, -9.95], [1, -11.0]]) {
    if (z < -L + 0.6) continue; const x = sd * (X - 0.06);
    box(0.04, 0.12, 0.08, brass, x + sd * 0.03, 1.78, z, C);
    const on = n < lit; n++;
    const sh = box(0.1, 0.12, 0.12, on ? new THREE.MeshBasicMaterial({ color: '#ffd08a' }) : M('#6b5a44'), x, 1.86, z, C); sh.castShadow = false;
    if (on) { const l = new THREE.PointLight('#ffb36b', 0.55, 2.6, 1.6); l.position.set(x - sd * 0.15, 1.85, z); C.add(l); }
  }
  // far end: wall with door 204, the caged red lamp above it
  const zE = -L;
  box(X - 0.54, H, 0.1, wM, -(X + 0.54) / 2, H / 2, zE - 0.05, C); box(X - 0.54, H, 0.1, wM, (X + 0.54) / 2, H / 2, zE - 0.05, C); box(1.08, H - 2.16, 0.1, wM, 0, (H + 2.16) / 2, zE - 0.05, C);
  const D = makeDoor204(); D.group.position.set(0, 0, zE); C.add(D.group); D.pivot.rotation.y = -(o.open ?? 0);
  const bulbOn = (o.red ?? 1) > 0;
  box(0.05, 0.05, 0.14, M('#222'), 0, 2.36, zE + 0.07, C);
  const bulb = new THREE.Mesh(new THREE.IcosahedronGeometry(0.055, 0), bulbOn ? new THREE.MeshBasicMaterial({ color: '#ff3a2a' }) : M('#5a1a14')); bulb.position.set(0, 2.29, zE + 0.16); C.add(bulb);
  const cage = M('#1a1a1a'); for (const [dx, dz] of [[-0.06, 0], [0.06, 0], [0, -0.06], [0, 0.06]]) box(0.008, 0.13, 0.008, cage, dx, 2.29, zE + 0.16 + dz, C);
  box(0.13, 0.008, 0.13, cage, 0, 2.225, zE + 0.16, C);
  if (bulbOn) {
    const r = new THREE.PointLight('#ff2a1e', 2.6 * (o.red ?? 1), 9, 1.25); r.position.set(0, 2.2, zE + 0.32); r.castShadow = true; r.shadow.mapSize.set(1024, 1024); r.shadow.bias = -0.003; C.add(r);
    const halo = new THREE.Mesh(new THREE.SphereGeometry(0.14, 8, 6), new THREE.MeshBasicMaterial({ color: '#ff2a1e', transparent: true, opacity: 0.18, depthWrite: false })); halo.position.copy(bulb.position); C.add(halo);
  }
  // light under door 204 (cold, from inside the room) and, optionally, two feet standing behind it
  const gap = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.012), new THREE.MeshBasicMaterial({ color: o.gap ? '#cfe0ff' : '#000000' })); gap.position.set(0, 0.006, zE + 0.056); C.add(gap);
  if (o.gap && o.feet) for (const x of [-0.2, -0.08, 0.1, 0.22]) box(0.08, 0.013, 0.003, new THREE.MeshBasicMaterial({ color: '#05060a' }), x, 0.0065, zE + 0.058, C);
  if (o.gap) { const gl = new THREE.SpotLight('#cfe0ff', 0.6, 1.4, 1.0, 0.9, 2); gl.position.set(0, 0.01, zE + 0.06); gl.target.position.set(0, 0, zE + 1.0); C.add(gl, gl.target); }
  // room 204 behind the door
  const R = { x0: -1.7, x1: 1.7, z0: zE - 0.1, z1: zE - 3.8, h: 2.5 };
  const rwT = canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#2c3033'; g.fillRect(0, 0, w, h); g.fillStyle = '#262a2d'; for (let x = 0; x < w; x += 32) g.fillRect(x, 0, 12, h); }, { repeat: [5, 3] });
  const rw = MT(rwT), rf = M('#2c2420');
  const rfl = new THREE.Mesh(new THREE.PlaneGeometry(R.x1 - R.x0, R.z0 - R.z1), rf); rfl.rotation.x = -Math.PI / 2; rfl.position.set(0, 0, (R.z0 + R.z1) / 2); rfl.receiveShadow = true; C.add(rfl);
  const rce = new THREE.Mesh(new THREE.PlaneGeometry(R.x1 - R.x0, R.z0 - R.z1), M('#1c1c1c')); rce.rotation.x = Math.PI / 2; rce.position.set(0, R.h, (R.z0 + R.z1) / 2); C.add(rce);
  box(R.x1 - R.x0, R.h, 0.1, rw, 0, R.h / 2, R.z1 - 0.05, C);
  box(0.1, R.h, R.z0 - R.z1, rw, R.x0 - 0.05, R.h / 2, (R.z0 + R.z1) / 2, C); box(0.1, R.h, R.z0 - R.z1, rw, R.x1 + 0.05, R.h / 2, (R.z0 + R.z1) / 2, C);
  box(-R.x0 - 0.54, R.h, 0.02, rw, (R.x0 - 0.54) / 2, R.h / 2, R.z0 + 0.0, C); box(R.x1 - 0.54, R.h, 0.02, rw, (R.x1 + 0.54) / 2, R.h / 2, R.z0, C);
  // the table with dozens of phones (7 x 5 = 35), screens up; o.phonesOn lights every screen at once
  const T = { x: 0, z: zE - 1.85, y: 0.76 };
  const tw = M('#4a3527'), td = M('#33241a');
  box(2.0, 0.05, 1.15, tw, T.x, T.y - 0.025, T.z, C);
  for (const [dx, dz] of [[-0.93, -0.5], [0.93, -0.5], [-0.93, 0.5], [0.93, 0.5]]) box(0.06, T.y - 0.05, 0.06, td, T.x + dx, (T.y - 0.05) / 2, T.z + dz, C);
  const rnd = mulberry(204), screens = [], phones = [];
  for (let r = 0; r < 5; r++) for (let c = 0; c < 7; c++) {
    const ph = makePhone(o.phonesOn ? (o.screenCol || '#d8e6ff') : '#0b0e13');
    ph.position.set(T.x - 0.81 + c * 0.27 + (rnd() - 0.5) * 0.06, T.y + 0.006, T.z - 0.44 + r * 0.22 + (rnd() - 0.5) * 0.04);
    ph.rotation.set(-Math.PI / 2, 0, (rnd() - 0.5) * 0.5); C.add(ph); phones.push(ph); screens.push(ph.getObjectByName('screen'));
  }
  if (o.phonesOn) {
    for (const x of [-0.6, 0.0, 0.6]) { const l = new THREE.PointLight(o.lightCol || '#a9c4ff', 0.9, 2.6, 1.5); l.position.set(T.x + x, T.y + 0.35, T.z); C.add(l); }
    const up = new THREE.PointLight(o.lightCol || '#bcd2ff', 0.8, 3.2, 1.4); up.position.set(T.x, T.y + 0.25, T.z + 0.75); C.add(up);
  }
  scene.add(new THREE.HemisphereLight('#7a6a5e', '#0c0a08', o.amb ?? 0.18));
  if (o.fog !== false) scene.fog = new THREE.Fog('#060404', o.fogNear ?? 5, o.fogFar ?? 16);
  W.objs.corridor = { C, L, door204: D, screens, phones, table: T, bulb, R };
  return W.objs.corridor;
}

// ====================================================================== EP06 additions «ПЕРВАЯ ПОПЫТКА»
// The doorway of room 204 walled up from the inside (the door has vanished): one seamless wall over the whole front of
// the room, the same dark striped paper as the other three walls. Returns the inner face z of that wall.
function room204Wall(W) {
  const C = W.objs.corridor, R = C.R;
  C.door204.group.visible = false;
  const rwT = canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#2c3033'; g.fillRect(0, 0, w, h); g.fillStyle = '#262a2d'; for (let x = 0; x < w; x += 32) g.fillRect(x, 0, 12, h); }, { repeat: [5, 3] });
  box(R.x1 - R.x0, R.h, 0.04, MT(rwT), 0, R.h / 2, R.z0 - 0.03, C.C, 'wall204');
  return R.z0 - 0.05;
}
// The mirror that takes the door's place: a tall dark frame on the walled-up doorway, real planar reflection (makeMirror).
// o.k < 1: the glass assembles out of dark glossy blocks (6 x 12) in a seeded order, the frame first; o.k = 1: the mirror.
// Objects on layer 1 exist only in the reflection (mirrorOnly) — the old Alex; layer 2 is seen by the camera but not
// reflected (camera.layers.enable(2)) — the young Alex in front of it.
function makeMirror204(W, o = {}) {
  const zf = room204Wall(W), k = o.k ?? 1, C = W.objs.corridor.C;
  const GW = 0.86, GH = 1.86, cy = 1.08;
  const fr = M('#17191c', { roughness: 0.45, metalness: 0.3 }), frE = Math.min(1, k / 0.25);
  const fz = zf - 0.03;
  box(0.07, (GH + 0.14) * frE, 0.06, fr, -GW / 2 - 0.035, cy, fz, C); box(0.07, (GH + 0.14) * frE, 0.06, fr, GW / 2 + 0.035, cy, fz, C);
  box((GW + 0.14) * frE, 0.07, 0.06, fr, 0, cy + GH / 2 + 0.035, fz, C); box((GW + 0.14) * frE, 0.07, 0.06, fr, 0, cy - GH / 2 - 0.035, fz, C);
  if (k < 1) {
    const rnd = mulberry(47), glass = M('#56656e', { roughness: 0.08, metalness: 0.85 });
    const nx = 6, ny = 12, tw = GW / nx, th = GH / ny;
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const thr = 0.2 + rnd() * 0.65; if (k < thr) continue;
      const e = Math.min(1, (k - thr) / 0.1);
      const b = box(tw * e, th * e, 0.02, glass, -GW / 2 + tw * (i + 0.5), cy - GH / 2 + th * (j + 0.5), zf - 0.02, C); b.castShadow = false;
    }
  } else {
    const m = makeMirror(new THREE.PlaneGeometry(GW, GH), { tw: o.tw || 900, th: o.th || 1946, layers: [1], tint: '#d9e4e2' });
    m.position.set(0, cy, zf - 0.015); m.rotation.y = Math.PI; C.add(m); W.objs.reflector = m;
  }
  // the glass throws a faint cold light back into the room (it lights whoever stands in front of it)
  const gl = new THREE.PointLight('#b9c9d6', o.glow ?? 0.55, 2.4, 1.6); gl.position.set(o.glowX ?? 0, 1.62, zf - (o.glowD ?? 0.25)); C.add(gl);
  return { z: zf - 0.015, cy };
}
// layer helper: seen by the camera, not by the mirror
function cameraOnly(obj) { obj.traverse(c => c.layers.set(2)); return obj; }

window.PRICE = { THREE, PAL, buildWorld, makePerson, makeGlass, makePhone, makeOpenHand, lightsInterior, lightsStairwell, phoneLight, box, M,
  enableMirror, mirrorOnly, makeFootprint, footprints, makeChair, seatPerson, makeRopes,
  pixTex, canvasTex, MT, makeForearm, scarTex, plateTex, mulberry,
  makeKey, makeDoor204, buildCorridor, sisterFace,
  room204Wall, makeMirror204, cameraOnly, makeMirror };
