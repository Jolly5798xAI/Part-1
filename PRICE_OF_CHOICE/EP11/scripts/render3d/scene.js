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
  // EP11 token 'closed': eyes shut — the whites and pupils become skin, a dark lash line underneath (ALEX in the hospital bed)
  if (tk.includes('closed')) { f[7] = 'ssssssssssssssss'; f[8] = 'sssbbssssssbbsss'; }
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
  // EP07: the cold face can speak — mouth shapes are applied again after 'cold' (EP06's plain 'cold' is unchanged)
  if (tk.includes('cold')) {
    if (tk.includes('open')) { f[13] = 'HsssssrOOrsssssH'; f[14] = 'HsssssrOOrsssssH'; }
    if (tk.includes('ee')) { f[13] = 'HssssrOOOOrssssH'; f[14] = 'HsssssrrrrsssssH'; }
    if (tk.includes('oo')) { f[13] = 'HssssssOOssssssH'; f[14] = 'HsssssrrrrsssssH'; }
  }
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
  const head = box(headS, headS, headS, headMats(o.head || (kind === 'double' ? 'alex' : kind), o.face || 'neutral'), 0, headS / 2 + 0.01, 0, headPivot, 'head');
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
  const backWall = box(E.x1 - E.x0, E.h, 0.1, wpM, (E.x0 + E.x1) / 2, E.h / 2, E.z1 + 0.05, scene); // EP08: named so the kitchen can open it
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
  W.objs = { doorPivot, door, lock, lever, leak, E, S, mirror, BD, bed, stairwell: SW, backWall, backDark: dark, wpM, lamM, ceilM, bbM }; // EP08: + back wall refs
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
  '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'], '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'], // EP07: 8
  '9': ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'], // EP09: 9
  '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'], '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
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


// ====================================================================== EP07 additions «ТОТ, КОГО СТЁРЛИ»
// Voxel dissolve: whatever it is applied to falls apart into cubes of 1/cell m that blink out with a cold cyan edge.
// k 0 = whole, 1 = gone. The cubes go in a seeded random order biased along o.dir (from o.a to o.b along that axis).
// Works on every Standard/Basic material of the object (materials are cloned, so other objects keep theirs).
function dissolve(obj, k, o = {}) {
  if (k <= 0) return obj;
  const dir = o.dir || new THREE.Vector3(0, 1, 0), a = o.a ?? 0, b = o.b ?? 1.8, cell = o.cell ?? 24, sweep = o.sweep ?? 0.7;
  const glow = new THREE.Color(o.glow || '#5fe6ff');
  obj.traverse(m => {
    if (!m.isMesh || m.material.isShaderMaterial) return;
    const patch = (mat) => {
      const c = mat.clone();
      c.onBeforeCompile = (sh) => {
        Object.assign(sh.uniforms, { uK: { value: k }, uCell: { value: cell }, uDir: { value: dir }, uA: { value: a }, uB: { value: b }, uSw: { value: sweep }, uGlow: { value: glow } });
        sh.vertexShader = 'varying vec3 vWPd;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvWPd = (modelMatrix * vec4(transformed, 1.0)).xyz;');
        sh.fragmentShader = 'uniform float uK; uniform float uCell; uniform vec3 uDir; uniform float uA; uniform float uB; uniform float uSw; uniform vec3 uGlow; varying vec3 vWPd;\n' +
          'float hh7(vec3 p){ return fract(sin(dot(p, vec3(12.9898,78.233,37.719))) * 43758.5453); }\n' +
          sh.fragmentShader.replace('#include <clipping_planes_fragment>', '#include <clipping_planes_fragment>\n' +
            'float hv7 = hh7(floor(vWPd * uCell)); float s7 = clamp((dot(vWPd, uDir) - uA) / (uB - uA), 0.0, 1.0);\n' +
            'float th7 = uK * (1.0 + uSw) - uSw * s7; if (hv7 < th7) discard;')
            .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\nif (hv7 < th7 + 0.1) totalEmissiveRadiance += uGlow * 2.2;')
            .replace('#include <map_fragment>', sh.fragmentShader.includes('totalEmissiveRadiance') ? '#include <map_fragment>' : '#include <map_fragment>\nif (hv7 < th7 + 0.1) diffuseColor.rgb = uGlow * 1.6;');
      };
      c.customProgramCacheKey = () => 'dissolve7';
      return c;
    };
    m.material = Array.isArray(m.material) ? m.material.map(patch) : patch(m.material);
    m.castShadow = false;
  });
  return obj;
}
// The cracks in mirror 204 where the old Alex's fist hit: a spider-web of thin pale bars round (cx, cy) on the glass,
// k grows them outward (0..1). Seen by the camera only (layer 2), so the mirror does not reflect its own cracks.
function mirrorCracks(W, M_, o = {}) {
  const g = new THREE.Group(); g.name = 'cracks'; const k = o.k ?? 1;
  const cx = o.cx ?? 0, cy = o.cy ?? 1.4, z = M_.z - 0.004, GW = 0.86, GH = 1.86, gy = M_.cy;
  const mat = new THREE.MeshBasicMaterial({ color: '#e4f0f4' }), dk = new THREE.MeshBasicMaterial({ color: '#202a30' });
  const inside = (x, y) => Math.abs(x) < GW / 2 - 0.01 && Math.abs(y - gy) < GH / 2 - 0.01;
  const seg = (x0, y0, x1, y1, w, m = mat) => {
    const len = Math.hypot(x1 - x0, y1 - y0); if (len < 1e-3) return;
    const b = new THREE.Mesh(new THREE.BoxGeometry(len, w, 0.003), m); b.position.set((x0 + x1) / 2, (y0 + y1) / 2, z); b.rotation.z = Math.atan2(y1 - y0, x1 - x0); g.add(b);
  };
  const rnd = mulberry(o.seed ?? 48), rays = o.rays ?? 11, R = 1.15 * k, ends = [];
  for (let i = 0; i < rays; i++) {
    let ang = (i / rays) * Math.PI * 2 + (rnd() - 0.5) * 0.4, x = cx, y = cy, r = 0; const pts = [[x, y]];
    while (r < R * (0.55 + rnd() * 0.45)) {
      const l = 0.035 + rnd() * 0.07; ang += (rnd() - 0.5) * 0.5; const nx = x + Math.cos(ang) * l, ny = y + Math.sin(ang) * l;
      if (!inside(nx, ny)) break;
      seg(x, y, nx, ny, 0.007 * (1 - 0.5 * r / 1.2)); x = nx; y = ny; r = Math.hypot(x - cx, y - cy); pts.push([x, y]);
    }
    ends.push(pts);
  }
  // concentric rings joining neighbouring rays (the web)
  for (const rr of [0.07, 0.17, 0.3, 0.46]) {
    if (rr > R * 0.8) break;
    for (let i = 0; i < rays; i++) {
      const pa = ends[i].find(p => Math.hypot(p[0] - cx, p[1] - cy) >= rr), pb = ends[(i + 1) % rays].find(p => Math.hypot(p[0] - cx, p[1] - cy) >= rr);
      if (pa && pb && rnd() < 0.8) seg(pa[0], pa[1], pb[0], pb[1], 0.005);
    }
  }
  // the impact: a small dark-and-white star where the fist landed
  if (k > 0.05) { for (let i = 0; i < 6; i++) { const a2 = i * Math.PI / 3 + 0.3; seg(cx, cy, cx + Math.cos(a2) * 0.03, cy + Math.sin(a2) * 0.03, 0.012, dk); } }
  g.traverse(c => c.layers.set(2)); W.objs.corridor.C.add(g);
  return g;
}
// Room 204's front wall with the mirror's opening cut out (after the mirror shatters): four strips round the hole.
function room204WallHole(W) {
  const C = W.objs.corridor, R = C.R; C.door204.group.visible = false;
  const rwT = canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#2c3033'; g.fillRect(0, 0, w, h); g.fillStyle = '#262a2d'; for (let x = 0; x < w; x += 32) g.fillRect(x, 0, 12, h); }, { repeat: [2, 3] });
  const m = MT(rwT), GW = 0.86, GH = 1.86, cy = 1.08, z = R.z0 - 0.03;
  box((R.x1 - R.x0) / 2 - GW / 2, R.h, 0.04, m, R.x0 / 2 - GW / 4, R.h / 2, z, C.C); box((R.x1 - R.x0) / 2 - GW / 2, R.h, 0.04, m, R.x1 / 2 + GW / 4, R.h / 2, z, C.C);
  box(GW, cy - GH / 2, 0.04, m, 0, (cy - GH / 2) / 2, z, C.C); box(GW, R.h - cy - GH / 2, 0.04, m, 0, (R.h + cy + GH / 2) / 2, z, C.C);
  return R.z0 - 0.05;
}
// Mirror 204 breaking: the frame stays, the glass (6 x 12 dark glossy tiles, the same grid it assembled from in EP06)
// bursts into the room. k 0 = whole glass with gaps (cracked), 1 = every tile on the floor or gone.
function shatterMirror204(W, k, o = {}) {
  const zf = room204WallHole(W), C = W.objs.corridor.C, GW = 0.86, GH = 1.86, cy = 1.08, fz = zf - 0.03;
  const fr = M('#17191c', { roughness: 0.45, metalness: 0.3 });
  box(0.07, GH + 0.14, 0.06, fr, -GW / 2 - 0.035, cy, fz, C); box(0.07, GH + 0.14, 0.06, fr, GW / 2 + 0.035, cy, fz, C);
  box(GW + 0.14, 0.07, 0.06, fr, 0, cy + GH / 2 + 0.035, fz, C); box(GW + 0.14, 0.07, 0.06, fr, 0, cy - GH / 2 - 0.035, fz, C);
  const rnd = mulberry(470), glass = M('#56656e', { roughness: 0.08, metalness: 0.85 }), edge = new THREE.MeshBasicMaterial({ color: '#cfe3ea' });
  const nx = 6, ny = 12, tw = GW / nx, th = GH / ny, hx = o.cx ?? 0.05, hy = o.cy ?? 1.43;
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    const x0 = -GW / 2 + tw * (i + 0.5), y0 = cy - GH / 2 + th * (j + 0.5);
    const dx = x0 - hx, dy = y0 - hy, d = Math.hypot(dx, dy) + 0.05;
    const delay = d * 0.25 + rnd() * 0.08, tt = Math.max(0, k - delay) * 1.6;           // tiles near the impact go first
    const vx = dx / d * (0.6 + rnd() * 0.8), vy = dy / d * 0.5 + 0.4 + rnd() * 0.6, vz = -(1.2 + rnd() * 1.6);
    let px = x0 + vx * tt, py = y0 + vy * tt - 4.9 * tt * tt, pz = zf - 0.02 + vz * tt;
    if (py < 0.01) { py = 0.01; } if (tt > 0 && rnd() < k * 0.5) continue;              // some shards have already flown out of frame
    const sc = tt > 0 ? 0.55 + rnd() * 0.4 : 0.94;
    const b = box(tw * sc, th * sc, 0.012, glass, px, py, pz, C); b.castShadow = false;
    b.rotation.set(tt * (rnd() - 0.5) * 14, tt * (rnd() - 0.5) * 14, tt * (rnd() - 0.5) * 8);
    if (tt > 0) { const e2 = box(tw * sc * 0.9, 0.004, 0.014, edge, 0, th * sc * 0.45, 0, b); e2.castShadow = false; }
  }
  return { z: zf - 0.015, cy };
}
// A screen that shows a live camera: every time it is drawn, `feedCam` renders the scene into its own texture
// (the same trick as the mirror). Used for the monitors behind the mirror that show the sister at her computer.
function makeFeedScreen(w, h, feedCam, o = {}) {
  const rt = new THREE.WebGLRenderTarget(o.tw || 800, o.th || Math.round(800 * h / w), { samples: 4 });
  const mat = new THREE.ShaderMaterial({
    uniforms: { tDiffuse: { value: rt.texture }, uTime: { value: o.seed ?? 0 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'uniform sampler2D tDiffuse; uniform float uTime; varying vec2 vUv; void main(){ vec3 c = texture2D(tDiffuse, vUv).rgb; float g = dot(c, vec3(0.3,0.59,0.11));' +
      ' c = mix(vec3(g), c, 0.55) * vec3(0.85,1.0,1.08) * 1.35; c *= 0.82 + 0.18 * step(0.5, fract(vUv.y * 160.0)); gl_FragColor = vec4(c, 1.0);\n#include <colorspace_fragment>\n}',
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); mesh.name = 'mirrorReflector';   // disposed like the mirror
  feedCam.aspect = w / h; feedCam.updateProjectionMatrix();
  mesh.onBeforeRender = function (renderer, scene) {
    if (mesh._busy) return; mesh._busy = true;   // EP08: a feed camera that can see its own screen (frustum, not occlusion) must not recurse
    const cur = renderer.getRenderTarget(), sau = renderer.shadowMap.autoUpdate;
    renderer.shadowMap.autoUpdate = false; renderer.setRenderTarget(rt); renderer.clear(); renderer.render(scene, feedCam);
    renderer.shadowMap.autoUpdate = sau; renderer.setRenderTarget(cur); mesh._busy = false;
  };
  mesh.dispose = () => { rt.dispose(); mat.dispose(); };
  return mesh;
}
function staticTex(seed, o = {}) {   // a dead monitor: cold-blue static with a few data bars (no letters)
  return canvasTex(160, 100, (g, w, h) => {
    const r = mulberry(seed); g.fillStyle = o.bg || '#0b1a24'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 900; i++) { const v = Math.floor(r() * 120); g.fillStyle = `rgb(${v * 0.5 | 0},${v * 0.9 | 0},${v})`; g.fillRect(Math.floor(r() * w / 2) * 2, Math.floor(r() * h / 2) * 2, 2, 2); }
    g.fillStyle = o.bar || '#5fd0ff'; for (let y = 10; y < h - 10; y += 12) g.fillRect(10, y, 20 + r() * (w - 60), 4);
  }, { nearest: true });
}
// The room behind the mirror (EP07): where the corridor used to be, a dark room with a wall of monitors and an empty
// operator desk. Every corridor-side mesh is hidden; room 204 stays. o.feedCam: the centre monitor shows that camera live.
// Returns { screens: [planes with userData.hw/hh], centre } (screens[0] is the big centre monitor).
function buildMonitorRoom(W, o = {}) {
  const Cc = W.objs.corridor, C = Cc.C, zE = -Cc.L, zr = Cc.R.z0;
  W.scene.updateMatrixWorld(true);
  const bb = new THREE.Box3(), wp = new THREE.Vector3();
  for (const ch of C.children.slice()) {
    if (ch.name === 'wall204' || ch.name === 'cracks') continue;
    bb.setFromObject(ch); const zmin = bb.isEmpty() ? ch.getWorldPosition(wp).z : bb.min.z;
    if (zmin > zr - 0.02) ch.visible = false;
  }
  const G = new THREE.Group(); G.name = 'monitorRoom'; W.scene.add(G);
  const z0 = zr, z1 = zr + 3.3, X = 1.7, H = 2.5, zc = (z0 + z1) / 2;
  const wallT = canvasTex(64, 64, (g, w, h) => { g.fillStyle = '#15191e'; g.fillRect(0, 0, w, h); g.fillStyle = '#1b2026'; g.fillRect(0, 0, w, 4); g.fillRect(0, 0, 4, h); }, { repeat: [8, 4], nearest: true });
  const wm = MT(wallT, { roughness: 0.8 }), fm = M('#101317', { roughness: 0.7 });
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(2 * X, z1 - z0), fm); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, zc); fl.receiveShadow = true; G.add(fl);
  const ce = new THREE.Mesh(new THREE.PlaneGeometry(2 * X, z1 - z0), M('#0b0d10')); ce.rotation.x = Math.PI / 2; ce.position.set(0, H, zc); G.add(ce);
  box(0.1, H, z1 - z0, wm, -X - 0.05, H / 2, zc, G); box(0.1, H, z1 - z0, wm, X + 0.05, H / 2, zc, G); box(2 * X, H, 0.1, wm, 0, H / 2, z1 + 0.05, G);
  // cable trays + red standby LEDs along the walls
  for (const sd of [-1, 1]) for (let i = 0; i < 9; i++) { const l = box(0.02, 0.02, 0.02, new THREE.MeshBasicMaterial({ color: i % 3 ? '#ff2a20' : '#3cff8a' }), sd * (X - 0.02), 0.9 + (i % 3) * 0.05, z0 + 0.4 + i * 0.32, G); l.castShadow = false; }
  // the monitor wall: a big centre monitor (screens[0]) and 12 smaller ones round it, on a dark steel frame
  const steel = M('#1e2329', { roughness: 0.5, metalness: 0.5 }), bez = M('#0d0f12', { roughness: 0.4 });
  box(3.1, 1.75, 0.08, steel, 0, 1.42, z1 - 0.06, G);
  const screens = [], zm = z1 - 0.12;
  const mon = (x, y, w, h, tex, feed) => {
    box(w + 0.05, h + 0.05, 0.05, bez, x, y, zm, G);
    let s;
    if (feed) s = makeFeedScreen(w, h, feed, { seed: x });
    else s = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, color: '#ffffff' }));
    s.position.set(x, y, zm - 0.027); s.rotation.y = Math.PI; s.userData.hw = w / 2; s.userData.hh = h / 2; G.add(s); screens.push(s); return s;
  };
  const red = o.red, mk = (i) => red ? staticTex(100 + i, { bg: '#2a0608', bar: '#ff4a40' }) : staticTex(100 + i);
  mon(0, 1.38, 0.98, 0.6, mk(0), o.feedCam);
  let i = 1;
  for (const [x, y] of [[-1.05, 1.9], [-0.37, 1.9], [0.37, 1.9], [1.05, 1.9], [-1.05, 1.38], [1.05, 1.38], [-1.05, 0.86], [-0.37, 0.86], [0.37, 0.86], [1.05, 0.86]]) mon(x, y, 0.56, 0.36, mk(i++));
  // the operator desk in front of the wall, empty chair pushed back, keyboard, a desk microphone — nobody here
  const dk = M('#23272c', { roughness: 0.6 });
  box(1.8, 0.05, 0.6, dk, 0, 0.74, z1 - 0.75, G); for (const sx of [-0.85, 0.85]) box(0.05, 0.72, 0.55, dk, sx, 0.36, z1 - 0.75, G);
  box(0.46, 0.02, 0.16, M('#0e1013'), 0.0, 0.775, z1 - 0.88, G);
  const ch = makeChair(); ch.position.set(0.35, 0, z1 - 1.5); ch.rotation.y = 2.6; G.add(ch);
  const glowC = red ? '#ff4a3a' : '#7fc6ff';
  const l1 = new THREE.PointLight(glowC, red ? 1.6 : 1.3, 4.5, 1.4); l1.position.set(0, 1.4, z1 - 0.8); G.add(l1);
  const l2 = new THREE.PointLight(glowC, 0.6, 3.5, 1.5); l2.position.set(0, 1.6, z0 + 0.6); G.add(l2);
  W.objs.monitorRoom = { G, screens, z1 };
  return W.objs.monitorRoom;
}
// The operator's room where the sister sits (far from everything else, z ≈ +40): a desk, her monitor, a keyboard,
// a red console button and a desk microphone; racks of blinking lights behind her. o.lean 0..1 (to the microphone),
// o.press 0..1 (her finger on the button). Returns { s, cam: webcam (on top of her monitor, looking at her), button }.
const OPS = new THREE.Vector3(0, 0, 40);
function sisterSeated(face, o = {}) {
  const s = makePerson('sister', { face }); const legH = 0.78, seat = 0.47; s.position.y = seat - legH;
  s.userData.legL.visible = false; s.userData.legR.visible = false;
  const pantsM = M('#3c4a66'), shoeM = M('#e6e3dc');
  for (const sx of [-1, 1]) { box(0.2, 0.2, 0.46, pantsM, sx * 0.105, legH, 0.2, s); box(0.2, 0.44, 0.22, pantsM, sx * 0.105, legH - 0.24, 0.41, s); box(0.21, 0.08, 0.27, shoeM, sx * 0.105, legH - 0.47 + 0.04, 0.44, s); }
  const lean = o.lean ?? 0, torso = s.getObjectByName('torso');
  torso.rotation.x = 0.35 * lean; torso.position.z += 0.1 * lean;
  s.userData.headPivot.position.z += 0.24 * lean; s.userData.headPivot.position.y -= 0.07 * lean; s.userData.headPivot.rotation.x = 0.12 * lean;
  for (const sd of [-1, 1]) { const a = s.userData.arms[sd]; a.position.z += 0.16 * lean; a.position.y -= 0.04 * lean; a.rotation.x = -1.05; a.rotation.z = -sd * 0.12; }
  return s;
}
function buildOperatorRoom(W, o = {}) {
  const G = new THREE.Group(); G.position.copy(OPS); W.scene.add(G);
  const wallT = canvasTex(64, 64, (g, w, h) => { g.fillStyle = '#14171b'; g.fillRect(0, 0, w, h); g.fillStyle = '#191d22'; g.fillRect(0, 0, w, 3); }, { repeat: [6, 3], nearest: true });
  const wm = MT(wallT);
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(5, 5), M('#0f1114')); fl.rotation.x = -Math.PI / 2; G.add(fl);
  box(5, 2.6, 0.1, wm, 0, 1.3, -1.6, G); box(0.1, 2.6, 5, wm, -2.0, 1.3, 0, G); box(0.1, 2.6, 5, wm, 2.0, 1.3, 0, G); box(5, 2.6, 0.1, wm, 0, 1.3, 1.8, G);
  // server racks with blinking lights behind her
  const rnd = mulberry(12);
  for (const x of [-1.2, -0.55, 0.55, 1.2]) {
    box(0.55, 2.0, 0.5, M('#0c0e11', { roughness: 0.5 }), x, 1.0, -1.3, G);
    for (let i = 0; i < 26; i++) { const c = rnd() < 0.3 ? '#ff3328' : (rnd() < 0.5 ? '#38ff86' : '#4fb8ff'); const l = box(0.025, 0.018, 0.01, new THREE.MeshBasicMaterial({ color: c }), x - 0.2 + rnd() * 0.4, 0.3 + rnd() * 1.6, -1.04, G); l.castShadow = false; }
  }
  // desk (she faces +z, toward her monitor and the webcam on it)
  const dk = M('#262a30', { roughness: 0.6 });
  box(1.4, 0.05, 0.7, dk, 0, 0.74, 0.55, G); for (const sx of [-0.65, 0.65]) box(0.05, 0.72, 0.65, dk, sx, 0.36, 0.55, G);
  // her monitor (back to us when seen from behind; its screen faces her) + webcam
  box(0.7, 0.44, 0.04, M('#0d0f12'), 0, 1.05, 0.85, G); box(0.06, 0.24, 0.06, M('#0d0f12'), 0, 0.87, 0.88, G);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.64, 0.38), new THREE.MeshBasicMaterial({ color: '#cfe6ff' })); scr.position.set(0, 1.05, 0.828); scr.rotation.y = Math.PI; G.add(scr);
  box(0.06, 0.03, 0.04, M('#0a0a0a'), 0, 1.29, 0.85, G); box(0.012, 0.012, 0.005, new THREE.MeshBasicMaterial({ color: '#ff2a1e' }), 0.02, 1.29, 0.828, G);
  // keyboard, the console with the red button, the desk microphone
  box(0.44, 0.02, 0.15, M('#15181c'), -0.08, 0.775, 0.5, G);
  box(0.16, 0.04, 0.16, M('#1a1d21'), 0.33, 0.785, 0.48, G);
  const press = o.press ?? 0, btn = box(0.08, 0.03 - 0.018 * press, 0.08, new THREE.MeshStandardMaterial({ color: '#d4241c', emissive: '#ff2016', emissiveIntensity: 0.4 + 1.2 * press }), 0.33, 0.82 - 0.009 * press, 0.48, G);
  box(0.12, 0.015, 0.1, M('#111316'), -0.32, 0.772, 0.6, G); box(0.02, 0.28, 0.02, M('#2a2d31', { metalness: 0.5 }), -0.32, 0.92, 0.6, G);
  const arm2 = box(0.02, 0.02, 0.2, M('#2a2d31', { metalness: 0.5 }), -0.32, 1.06, 0.52, G); arm2.rotation.x = 0.3;
  box(0.06, 0.1, 0.06, M('#3a3e44', { metalness: 0.6, roughness: 0.35 }), -0.32, 1.02, 0.42, G, 'mic');
  // her chair + the sister
  const ch = makeChair(); ch.position.set(0, 0, 0.0); G.add(ch);
  const s = sisterSeated(o.face || 'cold', { lean: o.lean ?? 0 }); G.add(s);
  if (o.pressArm) { const a = s.userData.arms[1]; a.rotation.x = -1.15 - 0.15 * press; a.rotation.z = -0.55; a.position.y -= 0.03 * press; }
  // light: her monitor on her face (cold), a red rim from the racks
  const lf = new THREE.PointLight('#bcd8ff', 1.2 * (1 - 0.85 * (o.lean ?? 0)), 2.2, 1.6); lf.position.set(0, 1.15, 0.7); G.add(lf);
  const lr = new THREE.PointLight('#ff3a2e', 0.7, 2.6, 1.6); lr.position.set(0.6, 1.6, -0.9); G.add(lr);
  const fill = new THREE.PointLight('#5a6878', 0.9, 4.5, 1.2); fill.position.set(0, 2.2, 0.9); G.add(fill);   // local fill (no global light: room 204 keeps its look)
  G.updateMatrixWorld(true);
  const cam = new THREE.PerspectiveCamera(o.fov ?? 34, 1.6, 0.01, 30);
  cam.position.copy(G.localToWorld(new THREE.Vector3(0, 1.3, 0.83))); cam.lookAt(G.localToWorld(new THREE.Vector3(0, 1.32 - 0.22 * (o.lean ?? 0), 0.1)));
  return { s, cam, G, btn };
}
// Alex's forearm for EP07 (EP04 makeForearm + the same EP04 scar): o.num 0..1 the number «48» surfacing on the inner
// wrist pixel by pixel (dark ink, under the scar, just above the hand); o.clear 0..1 the skin turning to clear glass
// over blocky wires, a steel rod and a small board (stylised, no anatomy). Inner wrist = +z face, hand at local y −0.5.
function scar48Tex(num) {
  return canvasTex(64, 128, (g) => {
    const px = (x, y, c, s = 4) => { g.fillStyle = c; g.fillRect(x * s, y * s, s, s); };
    g.fillStyle = PAL.skinAlex; g.fillRect(0, 0, 64, 128);
    for (let i = 0; i <= 11; i++) { const x = 2 + i, y = 24 - Math.round(i * 0.5); px(x, y, '#9c3e37'); px(x, y + 1, '#c9665a'); px(x, y + 2, '#eaa792'); }
    for (const i of [1, 4, 7, 10]) { const x = 2 + i, y = 24 - Math.round(i * 0.5); px(x, y - 1, '#7a2e29'); px(x, y + 3, '#7a2e29'); }
    if (num > 0) {
      const r = mulberry(4848); let xo = 9;
      for (const ch of '48') { const d = DIGITS[ch]; for (let yy = 0; yy < 7; yy++) for (let xx = 0; xx < 5; xx++) { const on = d[yy][xx] === '#'; const v = r(); if (on && v < num) px(31 - (xo + xx), 62 - yy, '#232c38', 2); } xo += 7; }   // drawn turned 180°: reads upright from Alex's eyes (hand away from him)
    }
  }, { nearest: true });
}
function makeForearm7(o = {}) {
  const g = new THREE.Group(); const clear = o.clear ?? 0;
  const skinM = () => { const m = M(PAL.skinAlex); if (clear > 0) { m.transparent = true; m.opacity = 1 - 0.82 * clear; m.depthWrite = false; m.color.lerp(new THREE.Color('#bfe9f2'), 0.5 * clear); } return m; };
  const skin = skinM();
  box(0.18, 0.13, 0.2, M(o.sleeve || PAL.hoodie), 0, -0.02, 0, g); box(0.18, 0.04, 0.2, M(PAL.hoodieDk), 0, -0.09, 0, g);
  const fm = MT(scar48Tex(o.num ?? 0)); if (clear > 0) { fm.transparent = true; fm.opacity = 1 - 0.8 * clear; fm.depthWrite = false; }
  const fa = box(0.13, 0.34, 0.14, [skin, skin, skin, skin, fm, skin], 0, -0.27, 0, g, 'forearm');
  const hand = new THREE.Group(); hand.position.set(0, -0.44, 0); g.add(hand);
  const hs = o.clearHand ? skin : M(PAL.skinAlex);
  box(0.15, 0.13, 0.1, hs, 0, -0.06, -0.005, hand, 'palm');
  for (let i = 0; i < 4; i++) { const f = new THREE.Group(); f.position.set(-0.052 + i * 0.035, -0.125, 0.0); hand.add(f); box(0.028, 0.075 - (i === 3 ? 0.015 : 0), 0.03, hs, 0, -0.035, 0, f); }
  const th = box(0.03, 0.06, 0.03, hs, 0.085, -0.04, 0.03, hand); th.rotation.z = -0.4;
  if (clear > 0) {   // inside: wires in the series palette, a steel rod, a tiny board with a blinking cyan light
    const inner = new THREE.Group(); g.add(inner);
    box(0.022, 0.36, 0.022, M('#9aa3ab', { metalness: 0.8, roughness: 0.3 }), -0.01, -0.27, -0.02, inner);
    [['#d8322a', -0.04, 0.02], ['#2f7fe0', 0.035, 0.03], ['#e8c43a', 0.0, 0.045], ['#3fbf6a', 0.045, -0.02], ['#e8e8e8', -0.045, -0.03]].forEach(([c, x, z], i) => {
      for (let j = 0; j < 6; j++) box(0.012, 0.062, 0.012, M(c, { roughness: 0.5, emissive: c, emissiveIntensity: 0.15 * clear }), x + 0.008 * Math.sin(j * 1.7 + i), -0.12 - j * 0.058, z, inner);
    });
    box(0.06, 0.045, 0.01, M('#1d5a3a', { roughness: 0.6 }), 0.0, -0.36, 0.04, inner);
    const led = box(0.012, 0.012, 0.012, new THREE.MeshBasicMaterial({ color: '#7ff4ff' }), 0.015, -0.355, 0.048, inner); led.castShadow = false;
    const l = new THREE.PointLight('#6fe8ff', 0.35 * clear, 0.5, 1.6); l.position.set(0, -0.3, 0.12); g.add(l);
  }
  g.userData = { hand, forearm: fa };
  return g;
}


// ====================================================================== EP08 additions «ЗАВТРАШНИЙ ДЕНЬ»
// The kitchen of flat 47 — behind the dark doorway in the entryway's back wall (x 0.3 ± 0.45, h 2.05: the EP01 doorway
// the warm light always came from). The back wall is rebuilt with a real opening in the same place, same wallpaper;
// nothing else in the entryway moves. Soviet kitchen in the series' blocky language: checked tiles, oilcloth table under a
// warm pendant lamp, counter with a sink, stove, fridge, a night window. o.glass: 'table' (a full glass on the table edge),
// 'broken' (shards + water on the floor by the table) or 'none'. o.lamp: pendant intensity. Returns W.objs.kitchen.
function buildKitchen(W, o = {}) {
  const scene = W.scene, E = W.objs.E, O = W.objs;
  O.backWall.visible = false; O.backDark.visible = false;
  const D = { x0: -0.15, x1: 0.75, h: 2.05 }, zw = E.z1 + 0.05;
  box(D.x0 - E.x0, E.h, 0.1, O.wpM, (E.x0 + D.x0) / 2, E.h / 2, zw, scene);
  box(E.x1 - D.x1, E.h, 0.1, O.wpM, (D.x1 + E.x1) / 2, E.h / 2, zw, scene);
  box(D.x1 - D.x0, E.h - D.h, 0.1, O.wpM, (D.x0 + D.x1) / 2, (E.h + D.h) / 2, zw, scene);
  const caseM = M('#e2ddd0');                                   // casing like the front door's
  box(0.06, D.h + 0.05, 0.02, caseM, D.x0 - 0.03, (D.h + 0.05) / 2, E.z1 - 0.01, scene); box(0.06, D.h + 0.05, 0.02, caseM, D.x1 + 0.03, (D.h + 0.05) / 2, E.z1 - 0.01, scene);
  box(D.x1 - D.x0 + 0.12, 0.06, 0.02, caseM, (D.x0 + D.x1) / 2, D.h + 0.03, E.z1 - 0.01, scene);
  const K = { x0: -1.0, x1: 1.9, z0: E.z1 + 0.1, z1: 7.0, h: E.h }, kc = (K.z0 + K.z1) / 2, kx = (K.x0 + K.x1) / 2;
  const G = new THREE.Group(); G.name = 'kitchen'; scene.add(G);
  const tileT = canvasTex(128, 128, (g, w, h) => { for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.fillStyle = (x + y) % 2 ? '#a99a7c' : '#cfc3a6'; g.fillRect(x * 32, y * 32, 32, 32); } g.fillStyle = 'rgba(0,0,0,0.12)'; for (let i = 0; i <= 4; i++) { g.fillRect(i * 32 - 1, 0, 2, h); g.fillRect(0, i * 32 - 1, w, 2); } }, { repeat: [5, 5], nearest: true });
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(K.x1 - K.x0, K.z1 - K.z0), MT(tileT)); fl.rotation.x = -Math.PI / 2; fl.position.set(kx, 0, kc); fl.receiveShadow = true; G.add(fl);
  const ce = new THREE.Mesh(new THREE.PlaneGeometry(K.x1 - K.x0, K.z1 - K.z0), O.ceilM); ce.rotation.x = Math.PI / 2; ce.position.set(kx, K.h, kc); G.add(ce);
  const paintT = canvasTex(64, 256, (g, w, h) => {      // pale green paint over a white-blue tiled band (the backsplash height)
    g.fillStyle = '#a7b493'; g.fillRect(0, 0, w, h); g.fillStyle = '#9aa886'; for (let x = 0; x < w; x += 16) g.fillRect(x, 0, 3, h * 0.45);
    g.fillStyle = '#d6e0dc'; g.fillRect(0, h * 0.45, w, h * 0.55); g.fillStyle = '#b9c6c2'; for (let y = Math.floor(h * 0.45); y < h; y += 16) g.fillRect(0, y, w, 2); for (let x = 0; x < w; x += 16) g.fillRect(x, h * 0.45, 2, h * 0.55);
    g.fillStyle = '#7f8c74'; g.fillRect(0, h * 0.45 - 4, w, 4);
  }, { repeat: [3, 1], nearest: true });
  const pm = MT(paintT);
  const wall = (len, x, z, ry) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(len, K.h), pm.clone()); m.material.map = paintT.clone(); m.material.map.needsUpdate = true; m.material.map.repeat.set(len / 0.9, 1); m.rotation.y = ry; m.position.set(x, K.h / 2, z); m.receiveShadow = true; G.add(m); return m; };
  wall(K.z1 - K.z0, K.x0, kc, Math.PI / 2); wall(K.z1 - K.z0, K.x1, kc, -Math.PI / 2);
  // far wall with the night window (x 0.05..1.05, y 1.0..2.0)
  const Wn = { x0: 0.05, x1: 1.05, y0: 1.0, y1: 2.0 };
  const farM = pm.clone(); farM.map = paintT.clone(); farM.map.needsUpdate = true;
  const far = (x0, x1, y0, y1) => { const t = paintT.clone(); t.needsUpdate = true; t.repeat.set((x1 - x0) / 0.9, (y1 - y0) / K.h); t.offset.set(0, y0 / K.h); const m = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, y1 - y0), MT(t)); m.rotation.y = Math.PI; m.position.set((x0 + x1) / 2, (y0 + y1) / 2, K.z1); m.receiveShadow = true; G.add(m); };
  far(K.x0, Wn.x0, 0, K.h); far(Wn.x1, K.x1, 0, K.h); far(Wn.x0, Wn.x1, 0, Wn.y0); far(Wn.x0, Wn.x1, Wn.y1, K.h);
  const night = new THREE.Mesh(new THREE.PlaneGeometry(Wn.x1 - Wn.x0, Wn.y1 - Wn.y0), new THREE.MeshBasicMaterial({ color: '#1a2640' })); night.rotation.y = Math.PI; night.position.set((Wn.x0 + Wn.x1) / 2, (Wn.y0 + Wn.y1) / 2, K.z1 + 0.05); G.add(night);
  const lit = new THREE.MeshBasicMaterial({ color: '#e8c87a' }), off = new THREE.MeshBasicMaterial({ color: '#28324a' });   // the block across the yard: a few windows still lit at 3 a.m.
  const r8 = mulberry(808); for (let j = 0; j < 4; j++) for (let i = 0; i < 6; i++) { const b = box(0.09, 0.1, 0.005, r8() < 0.18 ? lit : off, Wn.x0 + 0.12 + i * 0.155, Wn.y0 + 0.12 + j * 0.2, 0.0, G); b.position.z = K.z1 + 0.04; b.castShadow = false; }
  const frM = M('#e9e6dc');
  box(0.05, Wn.y1 - Wn.y0 + 0.1, 0.08, frM, Wn.x0, (Wn.y0 + Wn.y1) / 2, K.z1 - 0.02, G); box(0.05, Wn.y1 - Wn.y0 + 0.1, 0.08, frM, Wn.x1, (Wn.y0 + Wn.y1) / 2, K.z1 - 0.02, G);
  box(Wn.x1 - Wn.x0, 0.05, 0.08, frM, (Wn.x0 + Wn.x1) / 2, Wn.y1, K.z1 - 0.02, G); box(Wn.x1 - Wn.x0 + 0.1, 0.05, 0.22, frM, (Wn.x0 + Wn.x1) / 2, Wn.y0, K.z1 - 0.09, G);
  box(0.04, Wn.y1 - Wn.y0, 0.06, frM, (Wn.x0 + Wn.x1) / 2, (Wn.y0 + Wn.y1) / 2, K.z1 - 0.02, G);
  for (let i = 0; i < 5; i++) box(0.06, 0.45, 0.07, M('#d8d4c8'), Wn.x0 + 0.2 + i * 0.13, 0.55, K.z1 - 0.08, G);   // radiator under the window
  // kitchen side of the shared wall, where the kitchen is wider than the entryway
  box(E.x0 - K.x0, K.h, 0.1, pm, (K.x0 + E.x0) / 2, K.h / 2, zw, G); box(K.x1 - E.x1, K.h, 0.1, pm, (E.x1 + K.x1) / 2, K.h / 2, zw, G);
  // counter with a sink along the left wall + wall cupboards; stove; fridge in the right corner
  const cabM = M('#d9d2bf'), cabDk = M('#b8af99'), topM = M('#6b6d6a', { roughness: 0.5 }), steel = M('#a9afb5', { metalness: 0.7, roughness: 0.3 });
  box(0.6, 0.86, 2.2, cabM, K.x0 + 0.3, 0.43, 5.75, G); box(0.64, 0.04, 2.24, topM, K.x0 + 0.32, 0.88, 5.75, G);
  for (let i = 0; i < 4; i++) { box(0.01, 0.7, 0.5, cabDk, K.x0 + 0.605, 0.43, 4.85 + i * 0.55, G); box(0.02, 0.12, 0.03, steel, K.x0 + 0.615, 0.72, 4.72 + i * 0.55, G); }
  box(0.42, 0.03, 0.5, M('#7d858c', { metalness: 0.6, roughness: 0.25 }), K.x0 + 0.3, 0.905, 5.1, G); box(0.04, 0.26, 0.04, steel, K.x0 + 0.1, 1.02, 5.1, G); box(0.16, 0.03, 0.03, steel, K.x0 + 0.18, 1.14, 5.1, G);
  box(0.36, 0.7, 2.2, cabM, K.x0 + 0.18, 1.95, 5.75, G); for (let i = 0; i < 4; i++) box(0.01, 0.6, 0.5, cabDk, K.x0 + 0.365, 1.95, 4.85 + i * 0.55, G);
  box(0.6, 0.86, 0.6, M('#e4e1d8'), K.x0 + 0.3, 0.43, 6.55, G); box(0.6, 0.02, 0.6, M('#2a2b2e'), K.x0 + 0.3, 0.87, 6.55, G);
  for (const [dx, dz] of [[-0.14, -0.14], [0.14, -0.14], [-0.14, 0.14], [0.14, 0.14]]) box(0.16, 0.01, 0.16, M('#151618'), K.x0 + 0.3 + dx, 0.885, 6.55 + dz, G);
  box(0.62, 1.75, 0.62, M('#ecebe4', { roughness: 0.5 }), K.x1 - 0.33, 0.875, 6.6, G); box(0.02, 0.3, 0.04, steel, K.x1 - 0.65, 1.15, 6.4, G); box(0.62, 0.01, 0.62, M('#c9c7bf'), K.x1 - 0.33, 1.2, 6.6, G);
  // the table under the lamp, straight through the doorway (x 0.3), oilcloth in a faded check; two stools/chairs
  const T = { x: 0.3, z: 5.6, y: 0.74, w: 1.0, d: 0.7 };
  const ocT = canvasTex(64, 64, (g, w, h) => { g.fillStyle = '#ddd5c1'; g.fillRect(0, 0, w, h); g.fillStyle = 'rgba(176,72,58,0.55)'; for (let i = 0; i < w; i += 16) { g.fillRect(i, 0, 8, h); g.fillRect(0, i, w, 8); } }, { repeat: [3, 2], nearest: true });
  const ocM = MT(ocT), legM = M('#5e4330');
  box(T.w, 0.04, T.d, [ocM, ocM, ocM, ocM, ocM, ocM], T.x, T.y - 0.02, T.z, G);
  for (const [dx, dz] of [[-0.44, -0.29], [0.44, -0.29], [-0.44, 0.29], [0.44, 0.29]]) box(0.05, T.y - 0.04, 0.05, legM, T.x + dx, (T.y - 0.04) / 2, T.z + dz, G);
  const chairPos = new THREE.Vector3(T.x, 0, T.z + 0.52);
  const ch = makeChair(); ch.position.copy(chairPos); ch.rotation.y = Math.PI; G.add(ch);
  const ch2 = makeChair(); ch2.position.set(T.x + 0.72, 0, T.z - 0.05); ch2.rotation.y = -Math.PI / 2 + 0.25; G.add(ch2);
  // on the table: a mug, a plate with bread, his phone face down
  const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.09, 8), M('#e6e2d6')); mug.position.set(T.x - 0.3, T.y + 0.045, T.z + 0.12); mug.castShadow = true; G.add(mug);
  const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.09, 0.015, 10), M('#f0ede4')); plate.position.set(T.x + 0.12, T.y + 0.008, T.z + 0.15); G.add(plate);
  box(0.09, 0.04, 0.06, M('#a8743e'), T.x + 0.12, T.y + 0.035, T.z + 0.15, G);
  box(0.078, 0.01, 0.162, M('#16171a', { roughness: 0.4 }), T.x - 0.08, T.y + 0.005, T.z + 0.2, G).rotation.y = 0.4;
  // the pendant lamp: an enamel cone on a cord, warm
  const lampY = 2.02;
  const LZ = T.z - 0.32;   // over the front half of the table (ALEX_ORIGINAL's dark hair must not turn orange under it)
  box(0.01, K.h - lampY - 0.1, 0.01, M('#222'), T.x, (K.h + lampY + 0.1) / 2, LZ, G);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.24, 0.16, 8, 1, true), M('#c84a32', { side: THREE.DoubleSide })); shade.position.set(T.x, lampY, LZ); G.add(shade);
  const bulb = new THREE.Mesh(new THREE.IcosahedronGeometry(0.045, 0), new THREE.MeshBasicMaterial({ color: '#fff0c8' })); bulb.position.set(T.x, lampY - 0.05, LZ); G.add(bulb);
  const lampLight = new THREE.PointLight('#ffbf80', (o.lamp ?? 2.4) * 0.3, 5.5, 1.5); lampLight.position.set(T.x, lampY - 0.12, LZ); lampLight.castShadow = true; lampLight.shadow.mapSize.set(1024, 1024); lampLight.shadow.bias = -0.002; G.add(lampLight);
  const fill = new THREE.PointLight('#efdcc6', 0.95, 3.0, 1.6); fill.position.set(T.x, 1.3, T.z - 1.1); G.add(fill);
  const moonK = new THREE.PointLight('#7f95c8', 0.75, 3.5, 1.5); moonK.position.set(0.45, 1.75, K.z1 - 0.35); G.add(moonK);
  // the glass
  const glassAt = new THREE.Vector3(T.x + 0.44, T.y, T.z - 0.24);
  if (o.glass === 'table') { const g = makeGlass(); g.position.copy(glassAt); G.add(g); }
  if (o.glass === 'broken') { const b = makeGlassBreak(1, { seed: 47 }); b.position.set(glassAt.x + 0.08, 0, glassAt.z - 0.05); G.add(b); }
  W.objs.kitchen = { G, K, T, chairPos, lampLight, glassAt, D };
  return W.objs.kitchen;
}
// The glass of water falling off the table edge and breaking (EP01's glass: makeGlass). Origin = where it lands on the floor.
// k 0..0.42: it tips and falls (from table height); 0.42: impact; then blocky shards skid outward, water cubes splash and
// a puddle spreads. k = 1: the aftermath (still shot).
function makeGlassBreak(k, o = {}) {
  const g = new THREE.Group(); g.name = 'glassBreak'; const KI = 0.42, H = o.h ?? 0.74;
  const glassM = new THREE.MeshStandardMaterial({ color: '#d6ecf3', transparent: true, opacity: 0.5, roughness: 0.05, metalness: 0.1, flatShading: true, depthWrite: false });
  const edgeM = new THREE.MeshBasicMaterial({ color: '#eaf7fb' });
  const waterM = new THREE.MeshStandardMaterial({ color: '#6fb3cf', emissive: '#12313b', transparent: true, opacity: 0.7, roughness: 0.1, flatShading: true });
  if (k < KI) {
    const u = k / KI, gl = makeGlass(); gl.position.set(-0.08 * (1 - u), H * (1 - u * u), 0.05 * (1 - u)); gl.rotation.z = 1.9 * u; gl.rotation.x = 0.5 * u; g.add(gl);
    if (u > 0.15) for (let i = 0; i < 5; i++) { const c = box(0.02, 0.02, 0.02, waterM, gl.position.x + 0.03 * i * u, gl.position.y + 0.05 - 0.04 * i, 0.0, g); c.castShadow = false; }   // water leaving the tipped glass
    return g;
  }
  const v = (k - KI) / (1 - KI), e = 1 - Math.pow(1 - v, 3), rnd = mulberry(o.seed ?? 47);
  for (let i = 0; i < 16; i++) {                               // shards
    const a = rnd() * Math.PI * 2, d = (0.05 + rnd() * 0.32) * e, sz = 0.012 + rnd() * 0.03;
    const s = box(sz, 0.006 + rnd() * 0.02, sz * (0.6 + rnd()), glassM, Math.cos(a) * d, 0.006 + (v < 0.25 ? 0.06 * Math.sin(Math.PI * v / 0.25) * rnd() : 0), Math.sin(a) * d, g);
    s.rotation.set(rnd() * 3, rnd() * 3, rnd() * 3); s.castShadow = false;
    if (i % 3 === 0) { const ed = box(sz * 0.9, 0.003, 0.003, edgeM, 0, 0.005, 0, s); ed.castShadow = false; }
  }
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.034, 0.034, 0.014, 8), glassM); base.position.set(0.02 * e, 0.007, -0.03 * e); g.add(base);   // the heavy base survives
  if (v < 0.6) for (let i = 0; i < 14; i++) {                  // the splash: water cubes in short arcs
    const a = rnd() * Math.PI * 2, sp = 0.15 + rnd() * 0.35, w = v / 0.6, y = 0.25 * (0.5 + rnd()) * Math.sin(Math.PI * w);
    const c = box(0.018, 0.018, 0.018, waterM, Math.cos(a) * sp * w, Math.max(0.01, y), Math.sin(a) * sp * w, g); c.castShadow = false;
  }
  const pr = 0.06 + 0.22 * e;                                  // the puddle (flat low-poly blobs, like EP02's)
  for (let i = 0; i < 6; i++) { const a = i * 1.1 + rnd(), rr = pr * (0.45 + 0.4 * rnd()); const b = new THREE.Mesh(new THREE.CylinderGeometry(rr, rr, 0.003, 7), waterM); b.position.set(Math.cos(a) * pr * 0.45, 0.002 + i * 0.0003, Math.sin(a) * pr * 0.45); b.receiveShadow = true; g.add(b); }
  return g;
}
// A plain kitchen knife, stylised: steel blade (bright edge), black handle with two rivets. Origin = the middle of the
// handle (where the fist closes); the blade points along local -y. No blood, nothing realistic.
function makeKnife() {
  const g = new THREE.Group(); g.name = 'knife';
  const steel = M('#c9d0d6', { metalness: 0.8, roughness: 0.22 }), edge = new THREE.MeshBasicMaterial({ color: '#f2f7fa' }), hm = M('#17181b', { roughness: 0.5 });
  box(0.03, 0.11, 0.024, hm, 0, 0, 0, g);
  for (const y of [-0.03, 0.03]) box(0.008, 0.008, 0.026, M('#b9bec4', { metalness: 0.8 }), 0, y, 0, g);
  box(0.036, 0.012, 0.03, steel, 0, -0.06, 0, g);              // bolster
  box(0.034, 0.16, 0.006, steel, 0.002, -0.145, 0, g);          // blade
  box(0.022, 0.035, 0.006, steel, -0.004, -0.24, 0, g); box(0.01, 0.02, 0.006, steel, -0.008, -0.265, 0, g);   // tapering tip, in steps
  const e1 = box(0.004, 0.19, 0.007, edge, -0.015, -0.16, 0, g); e1.castShadow = false;
  return g;
}
// Cracks on a monitor screen where a fist hit it: the same spider-web language as mirror 204's cracks, on any screen plane
// (child of the screen, on its viewer side). k grows them; (cx, cy) in the screen's local metres.
function monitorCracks(screen, o = {}) {
  const g = new THREE.Group(); g.name = 'monCracks'; const k = o.k ?? 1, hw = screen.userData.hw, hh = screen.userData.hh, cx = o.cx ?? 0.08, cy = o.cy ?? 0.04;
  const mat = new THREE.MeshBasicMaterial({ color: '#b9c6cc' }), dk = new THREE.MeshBasicMaterial({ color: '#05070a' });
  const seg = (x0, y0, x1, y1, w, m = mat) => { const len = Math.hypot(x1 - x0, y1 - y0); if (len < 1e-3) return; const b = new THREE.Mesh(new THREE.BoxGeometry(len, w, 0.002), m); b.position.set((x0 + x1) / 2, (y0 + y1) / 2, 0.003); b.rotation.z = Math.atan2(y1 - y0, x1 - x0); g.add(b); };
  const rnd = mulberry(o.seed ?? 34), R = 0.75 * k, ends = [];
  for (let i = 0; i < 12; i++) {
    let a = i / 12 * Math.PI * 2 + (rnd() - 0.5) * 0.4, x = cx, y = cy; const pts = [[x, y]];
    while (Math.hypot(x - cx, y - cy) < R * (0.5 + rnd() * 0.5)) { const l = 0.025 + rnd() * 0.05; a += (rnd() - 0.5) * 0.5; const nx = x + Math.cos(a) * l, ny = y + Math.sin(a) * l; if (Math.abs(nx) > hw - 0.01 || Math.abs(ny) > hh - 0.01) break; seg(x, y, nx, ny, 0.0026); x = nx; y = ny; pts.push([x, y]); }
    ends.push(pts);
  }
  for (const rr of [0.05, 0.12, 0.21]) for (let i = 0; i < 12; i++) { if (rr > R * 0.8) break; const pa = ends[i].find(p => Math.hypot(p[0] - cx, p[1] - cy) >= rr), pb = ends[(i + 1) % 12].find(p => Math.hypot(p[0] - cx, p[1] - cy) >= rr); if (pa && pb && rnd() < 0.8) seg(pa[0], pa[1], pb[0], pb[1], 0.002); }
  if (k > 0.05) { const b = new THREE.Mesh(new THREE.PlaneGeometry(0.07, 0.06), dk); b.position.set(cx, cy, 0.0025); g.add(b); for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; seg(cx, cy, cx + Math.cos(a) * 0.05, cy + Math.sin(a) * 0.05, 0.005); } }
  screen.add(g); return g;
}
// The monitor room being deleted (k 0..1): ceiling first, then the walls come apart into cubes with the cyan deletion edge
// (dissolve), blocks drop from the ceiling and bounce, a few small monitors tear loose and tilt. The centre monitor and the
// mirror frame stay readable. Returns the debris group.
function collapseMonitorRoom(W, k, o = {}) {
  const R = W.objs.monitorRoom; if (!R || k <= 0) return null;
  const keep = new Set(o.keep || [R.screens[0]]);
  for (const ch of R.G.children) {
    if (keep.has(ch) || ch.isLight) continue;
    if (R.screens.indexOf(ch) > 0 && R.screens.indexOf(ch) % 3 === 1) { ch.rotation.z = 0.5 * Math.min(1, k * 1.6) * (R.screens.indexOf(ch) % 2 ? 1 : -1); ch.position.y -= 0.25 * Math.min(1, k * 1.4) ** 2; }
    dissolve(ch, k * 0.62, { dir: new THREE.Vector3(0, -1, 0), a: -2.5, b: 0.0, cell: 12, sweep: 1.4, glow: '#5fe6ff' });
  }
  const D = new THREE.Group(); D.name = 'debris'; W.scene.add(D);
  const rnd = mulberry(o.seed ?? 808), dm = M('#1b2026', { roughness: 0.7 }), gm = new THREE.MeshStandardMaterial({ color: '#0c1a20', emissive: '#5fe6ff', emissiveIntensity: 1.4 });
  const z0 = R.z1 - 3.2, z1 = R.z1 - 0.3, n = o.n ?? 46;
  for (let i = 0; i < n; i++) {
    const delay = rnd() * 0.75, tt = Math.max(0, k - delay) * 2.2, x = -1.5 + rnd() * 3.0, z = z0 + rnd() * (z1 - z0), s = 0.05 + rnd() * 0.13;
    if (tt <= 0) continue;
    let y = 2.45 - 4.9 * tt * tt * 0.6; if (y < s / 2) { const b = (tt - Math.sqrt(2.45 / 2.94)) ; y = s / 2 + Math.max(0, 0.12 * Math.sin(Math.min(Math.PI, b * 9)) * Math.exp(-b * 3)); }
    const c = box(s, s, s, rnd() < 0.25 ? gm : dm, x, y, z, D); c.rotation.set(tt * rnd() * 4, tt * rnd() * 4, 0); c.castShadow = false;
  }
  return D;
}
// Flat 47 rebuilt behind mirror 204's empty frame, turned to face the monitor room: the door of flat 47 (seen from the
// landing side, as you would walk home) stands where room 204 was. It is the same buildWorld() flat (same door, same
// entryway, same kitchen light), moved, not a copy that could drift. Room 204's contents behind the frame are hidden (or
// dissolved out with o.k204). o.ajar: the door swings into the flat. o.k: 0..1 the flat assembling (1 = whole).
function flatBehindMirror(W, o = {}) {
  const Cc = W.objs.corridor, C = Cc.C, zr = Cc.R.z0;
  W.scene.updateMatrixWorld(true);
  const bb = new THREE.Box3(), wp = new THREE.Vector3(), gone = [];
  for (const ch of C.children.slice()) {
    if (ch.name === 'wall204') continue;
    bb.setFromObject(ch); const zmin = bb.isEmpty() ? ch.getWorldPosition(wp).z : bb.min.z;
    if (zmin < zr - 0.3) gone.push(ch);
  }
  const k204 = o.k204 ?? 1;
  for (const ch of gone) { if (k204 >= 1 || ch.isLight) ch.visible = false; else if (k204 > 0) dissolve(ch, k204, { dir: new THREE.Vector3(0, 0, 1), a: zr - 4, b: zr, cell: 14, sweep: 0.8, glow: '#5fe6ff' }); }
  const W2 = buildWorld(); W2.objs.stairwell.visible = false; W2.objs.bed.group && (W2.objs.bed.group.visible = false);
  if (o.kitchen !== false) buildKitchen(W2, { glass: 'none', lamp: 1.6 });
  W2.objs.doorPivot.rotation.y = o.ajar ?? 0;
  // the door's landing side (never in frame before): the peephole's outer ring, the key cylinder under the lever, a lever, and a
  // small brass plate «47» in the 5x7 pixel digits of the series (same as the room-204 plates; no fonts in the 3D world)
  const dp = W2.objs.doorPivot, brassO = M(PAL.brass, { metalness: 0.65, roughness: 0.35 });
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.012, 12), brassO); ring.rotation.x = Math.PI / 2; ring.position.set(-0.45, 1.58, -0.04); dp.add(ring);
  box(0.05, 0.12, 0.008, brassO, -0.82, 1.18, -0.039, dp); box(0.016, 0.016, 0.006, M('#1a1208'), -0.82, 1.15, -0.044, dp);
  box(0.05, 0.2, 0.012, brassO, -0.82, 0.98, -0.041, dp); box(0.14, 0.025, 0.03, brassO, -0.76, 1.0, -0.07, dp);
  const pl = MT(plateTex('47', '#2a1d10', '#c9a24a'), { metalness: 0.4, roughness: 0.4 }), pb = M('#a8853a', { metalness: 0.5 });
  box(0.17, 0.1, 0.008, [pb, pb, pb, pb, pb, pl], -0.45, 1.78, -0.04, dp);
  const F = new THREE.Group(); F.name = 'flatPortal';
  for (const ch of W2.scene.children.slice()) F.add(ch);
  const k = o.k ?? 1;
  const warm = new THREE.PointLight('#ffb36b', 1.6 * k, 6, 1.6); warm.position.set(0.5, 1.6, 3.7); F.add(warm);
  const hall = new THREE.PointLight('#ffd2a0', 0.9 * k, 3.5, 1.6); hall.position.set(0.15, 2.0, 1.4); F.add(hall);
  const out = new THREE.PointLight('#e8d8c0', 1.1 * k, 2.4, 1.5); out.position.set(-0.1, 1.95, -0.7); F.add(out);   // a landing light on the door's outer face
  F.rotation.y = Math.PI; F.position.set(0, 0, zr - 0.29);
  W.scene.add(F); F.updateMatrixWorld(true);
  if (k < 1) dissolve(F, 1 - k, { dir: new THREE.Vector3(0, 1, 0), a: 0, b: 2.6, cell: 14, sweep: 0.9, glow: '#5fe6ff' });
  return { F, W2, zDoor: zr - 0.29 };
}

// ====================================================================== EP09 additions «ПЕРВЫЙ АЛЕКС»
// Wrist numbers for the other versions of Alex. Same inner-wrist skin + EP04 scar as scar48Tex (they are all the same man),
// the number in the series' 5x7 pixel digits, larger (scale 3), and lit from inside: o.glow = colour, o.g 0..1 = brightness /
// how many pixels have surfaced. ALEX_49: cyan «49»; ALEX_ZERO: red «0». o.flip: drawn turned 180° (reads upright from the
// owner's eyes, like EP07's «48"); default reads upright for someone looking at the other man's wrist.
function wristNumTex(text, o = {}, emissive = false) {
  return canvasTex(64, 128, (g) => {
    const px = (x, y, c, s = 4) => { g.fillStyle = c; g.fillRect(x * s, y * s, s, s); };
    g.fillStyle = emissive ? '#000000' : PAL.skinAlex; g.fillRect(0, 0, 64, 128);
    if (!emissive) {
      for (let i = 0; i <= 11; i++) { const x = 2 + i, y = 24 - Math.round(i * 0.5); px(x, y, '#9c3e37'); px(x, y + 1, '#c9665a'); px(x, y + 2, '#eaa792'); }
      for (const i of [1, 4, 7, 10]) { const x = 2 + i, y = 24 - Math.round(i * 0.5); px(x, y - 1, '#7a2e29'); px(x, y + 3, '#7a2e29'); }
    }
    const k = o.g ?? 1; if (k <= 0) return;
    const r = mulberry(4949); const S = 3, gw = text.length * 6 - 1; let xo = Math.round((64 / S - gw) / 2);
    const y0 = Math.round(50 / S);
    for (const ch of text) {
      const d = DIGITS[ch];
      for (let yy = 0; yy < 7; yy++) for (let xx = 0; xx < 5; xx++) {
        if (d[yy][xx] !== '#' || r() > k * 1.15) continue;
        const X = o.flip ? (64 / S - 1 - (xo + xx)) : xo + xx, Y = o.flip ? (y0 + 6 - yy) : y0 + yy;
        g.fillStyle = emissive ? o.glow : (o.ink || '#1d2330'); g.fillRect(Math.round(X * S), Math.round(Y * S), S, S);
      }
      xo += 6;
    }
  }, { nearest: true });
}
// a forearm (EP07 rig) with a glowing number; o.text '49' | '0', o.glow colour, o.g 0..1, o.sleeve
function makeForearm9(o = {}) {
  const g = makeForearm7({ num: 0, sleeve: o.sleeve });
  const fa = g.userData.forearm; const mats = fa.material.slice();
  const m = new THREE.MeshStandardMaterial({ map: wristNumTex(o.text || '49', o), emissiveMap: wristNumTex(o.text || '49', o, true),
    emissive: new THREE.Color('#ffffff'), emissiveIntensity: 1.3 * (o.g ?? 1), roughness: 0.9 });
  mats[4] = m; fa.material = mats;
  if ((o.g ?? 1) > 0) { const l = new THREE.PointLight(o.glow, 0.14 * (o.g ?? 1), 0.6, 1.6); l.position.set(0, -0.3, 0.16); g.add(l); }
  return g;
}
// a small lit number on the inside of a full-body figure's wrist (the sleeve cuff, facing forward): readable in medium shots
function wristBadge(p, text, col, o = {}) {
  const a = p.userData.arms[o.side ?? -1];
  const t = canvasTex(64, 40, (g) => { g.fillStyle = '#000'; g.fillRect(0, 0, 64, 40);
    const S = 4, gw = text.length * 6 - 1; let xo = Math.round((16 - gw) / 2);
    for (const ch of text) { const d = DIGITS[ch]; for (let yy = 0; yy < 7; yy++) for (let xx = 0; xx < 5; xx++) if (d[yy][xx] === '#') { g.fillStyle = col; g.fillRect((xo + xx) * S, (1.5 + yy) * S, S, S); } xo += 6; }
  }, { nearest: true });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(0.13, 0.08), new THREE.MeshBasicMaterial({ map: t, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  m.position.set(0, -0.43, 0.093); a.add(m);
  const l = new THREE.PointLight(col, o.light ?? 0.35, 0.9, 1.6); l.position.set(0, -0.45, 0.2); a.add(l);
  return m;
}
// the officer's black balaclava from EP04, taken off: a soft blocky hood with the eye slit, hanging from a hand
function makeBalaclava() {
  const g = new THREE.Group(); g.name = 'balaclava'; const k = M('#2c2c32', { roughness: 0.9 });
  box(0.24, 0.3, 0.05, k, 0, -0.15, 0, g); box(0.2, 0.06, 0.08, k, 0.0, -0.31, 0.01, g);
  box(0.16, 0.03, 0.052, M('#2a2a2e'), 0, -0.1, 0.001, g);
  for (const x of [-0.05, 0.05]) box(0.05, 0.02, 0.054, M('#050505'), x, -0.1, 0.002, g);   // the eye slit, empty
  box(0.06, 0.1, 0.06, k, 0.0, 0.02, 0, g).rotation.z = 0.3;                                 // the fold in the fist
  return g;
}
// the unmasked officer: the EP04–EP06 police model with old Alex's head (EP06 'old' face) under the peaked cap
function makeOldCop(o = {}) { return makePerson('cop', { head: 'alex', face: o.face || 'old', gloves: o.gloves }); }


// ====================================================================== EP10 additions «СОЗДАТЕЛЬ»
// The sister's computer in room 204 (EP05's room, the table of 35 phones): a desktop monitor on the table facing her, a keyboard,
// her chair behind the table. The phones in front of the monitor are cleared away (hidden), every other phone stays where EP05 put it.
// Returns { s (seated sister, EP07 sisterSeated), screen (monitor plane, userData.hw/hh), cam (webcam on top of the monitor) }.
function room204Desk(W, o = {}) {
  const C = W.objs.corridor, T = C.table, G = C.C;
  for (const ph of C.phones) if (Math.abs(ph.position.x - T.x) < 0.45 && ph.position.z < T.z - 0.1) ph.visible = false;
  const zm = T.z - 0.3, ym = T.y;
  const bez = M('#0d0f12', { roughness: 0.4 });
  box(0.6, 0.38, 0.04, bez, T.x, ym + 0.32, zm, G); box(0.06, 0.14, 0.05, bez, T.x, ym + 0.07, zm + 0.02, G); box(0.24, 0.015, 0.16, bez, T.x, ym + 0.008, zm + 0.02, G);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.56, 0.34), new THREE.MeshBasicMaterial({ color: o.screenCol || '#cfe6ff' }));
  scr.position.set(T.x, ym + 0.32, zm - 0.021); scr.rotation.y = Math.PI; scr.userData.hw = 0.28; scr.userData.hh = 0.17; scr.name = 'monScreen'; G.add(scr);
  box(0.06, 0.03, 0.04, M('#0a0a0a'), T.x, ym + 0.525, zm, G); box(0.012, 0.012, 0.005, new THREE.MeshBasicMaterial({ color: '#ff2a1e' }), T.x + 0.02, ym + 0.525, zm - 0.021, G);
  box(0.44, 0.02, 0.15, M('#15181c'), T.x - 0.04, ym + 0.01, T.z - 0.48, G);
  const ch = makeChair(); ch.position.set(T.x, 0, T.z - 0.9); G.add(ch);
  const s = sisterSeated(o.face || 'cold', { lean: o.lean ?? 0 }); s.position.x = T.x; s.position.z = T.z - 0.9; G.add(s);
  if (o.head !== undefined) s.userData.headPivot.rotation.x = o.head;
  const lf = new THREE.PointLight('#bcd8ff', o.monLight ?? 0.25, 1.6, 1.6); lf.position.set(T.x, ym + 0.42, zm - 0.3); G.add(lf);
  G.updateMatrixWorld(true);
  const cam = new THREE.PerspectiveCamera(o.fov ?? 34, 1.6, 0.01, 30);
  cam.position.set(T.x, ym + 0.56, zm - 0.06); cam.lookAt(T.x, 1.2, T.z - 0.92);
  return { s, screen: scr, cam };
}
// a figure falling to its knees, e 0..1. The standing rig has one-piece legs, so (like EP03's seatPerson) the legs are rebuilt:
// up to e = 0.7 the hips drop and the legs buckle; from 0.7 the thighs stand upright on the floor and the shins lie flat behind.
function kneelPose(p, e, o = {}) {
  const legH = 0.78, d = 0.34;
  const u = Math.min(1, e / 0.7);
  p.position.y = -d * (u * u);
  p.userData.headPivot.rotation.x = 0.4 * e;
  for (const sd of [-1, 1]) { const a = p.userData.arms[sd]; a.rotation.x = -0.3 * e; a.rotation.z = -sd * 0.1 * e; }
  if (e < 0.7) { for (const L of [p.userData.legL, p.userData.legR]) L.rotation.x = 0.45 * u; return; }
  p.userData.legL.visible = false; p.userData.legR.visible = false;
  const pantsM = M(o.pants || PAL.copNavyDk), shoeM = M(o.shoe || PAL.black);
  for (const sx of [-1, 1]) {
    box(0.2, 0.42, 0.2, pantsM, sx * 0.105, legH - 0.21, 0.0, p);               // thigh, upright
    box(0.2, 0.15, 0.44, pantsM, sx * 0.105, legH - 0.42 + 0.075 - 0.0, -0.2, p); // shin flat behind the knee
    box(0.19, 0.1, 0.14, shoeM, sx * 0.105, legH - 0.42 + 0.05, -0.45, p);        // boot, sole up
  }
}


// ====================================================================== EP11 additions «НУЛЕВОЙ УРОВЕНЬ»
// The sister chained to her own chair in room 204: EP10's sisterSeated figure, forearms down on new armrests, steel cuffs at both
// wrists and ankles, short chains bolted to the armrests and the front legs. Returns the figure; o.place = {x, z} puts chair + figure.
function chainedChair(G, o = {}) {
  const x = o.x ?? 0, z = o.z ?? 0;
  const ch = makeChair(); ch.position.set(x, 0, z); G.add(ch);
  const s = sisterSeated(o.face || 'worried', { lean: 0 }); s.position.x = x; s.position.z = z; G.add(s);
  const steel = M('#aab0b6', { metalness: 0.8, roughness: 0.3 }), dark = M('#2a2c30', { metalness: 0.6, roughness: 0.4 });
  const wd = M('#4a3425');
  const ring = (par, y, w = 0.2, d = 0.22) => { box(w, 0.05, 0.025, steel, 0, y, d / 2, par); box(w, 0.05, 0.025, steel, 0, y, -d / 2, par); box(0.025, 0.05, d, steel, w / 2, y, 0, par); box(0.025, 0.05, d, steel, -w / 2, y, 0, par); };
  const raise = o.raise ?? 0;                                            // the right hand lifting off the armrest as far as the chain allows
  for (const sd of [-1, 1]) {
    const a = s.userData.arms[sd]; a.rotation.x = -0.9 - (sd < 0 ? 0.35 * raise : 0); a.rotation.z = 0;
    ring(a, -0.45);
    if (sd < 0 && raise > 0) { const h = a.getObjectByName('handL'); if (h) h.rotation.x = -0.6 * raise; }
  }
  // armrests (bolted onto the chair's posts), just under the cuffs
  for (const sd of [-1, 1]) {
    box(0.07, 0.04, 0.56, wd, x + sd * 0.3, 0.6, z + 0.06, G);
    box(0.045, 0.16, 0.045, wd, x + sd * 0.3, 0.52, z + 0.3, G); box(0.06, 0.035, 0.06, wd, x + sd * 0.27, 0.45, z + 0.3, G);
    box(0.09, 0.02, 0.06, dark, x + sd * 0.3, 0.625, z + 0.33, G);      // the bolt plate
  }
  s.updateMatrixWorld(true);
  const chain = (p0, p1, n) => {                                       // blocky links, alternating flat / edge-on
    const d = p1.clone().sub(p0);
    for (let i = 0; i < n; i++) {
      const p = p0.clone().add(d.clone().multiplyScalar((i + 0.5) / n));
      const l = box(i % 2 ? 0.012 : 0.03, Math.max(0.03, d.length() / n * 1.25), i % 2 ? 0.03 : 0.012, steel, p.x, p.y, p.z, G);
      l.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.clone().normalize());
    }
  };
  for (const sd of [-1, 1]) {
    const a = s.userData.arms[sd], c = a.localToWorld(new THREE.Vector3(0, -0.47, 0));
    chain(c, new THREE.Vector3(x + sd * 0.3, 0.63, z + 0.33), 4);
    // ankle cuffs + a chain to the chair's front leg
    const ax = x + sd * 0.105, ay = 0.11, az = z + 0.43;
    box(0.25, 0.045, 0.025, steel, ax, ay, az + 0.13, G); box(0.25, 0.045, 0.025, steel, ax, ay, az - 0.13, G);
    box(0.025, 0.045, 0.26, steel, ax + 0.12, ay, az, G); box(0.025, 0.045, 0.26, steel, ax - 0.12, ay, az, G);
    chain(new THREE.Vector3(ax, ay, az - 0.13), new THREE.Vector3(x + sd * 0.2, 0.09, z + 0.19), 3);
  }
  return { s, chair: ch };
}

// Room 204 in EP11: EP10's computer (same place, same size), but the monitor now stands on a swivel neck (o.turn 0 = facing the
// sister, 1 = swung round to face the door), thick cables from its back into the floor and the back wall (o.pulse: cold light
// running along them — "это не компьютер"); a second, smaller monitor on the table's near-left corner (the hospital recording);
// the sister chained in her chair behind the table. Screen planes carry userData.hw/hh for the editor's UI.
function desk11(W, o = {}) {
  const C = W.objs.corridor, T = C.table, G = C.C;
  for (const ph of C.phones) if (Math.abs(ph.position.x - T.x) < 0.45 && ph.position.z < T.z - 0.1) ph.visible = false;
  for (const ph of C.phones) if (ph.position.x < T.x - 0.45 && ph.position.z > T.z + 0.15) ph.visible = false;   // room for the side monitor
  const zm = T.z - 0.3, ym = T.y;
  const bez = M('#0d0f12', { roughness: 0.4 });
  // base + swivel
  box(0.24, 0.015, 0.16, bez, T.x, ym + 0.008, zm + 0.02, G); box(0.05, 0.1, 0.05, bez, T.x, ym + 0.06, zm + 0.02, G);
  const piv = new THREE.Group(); piv.position.set(T.x, ym + 0.1, zm + 0.02); G.add(piv);
  const turn = o.turn ?? 0, ee = turn * turn * (3 - 2 * turn); piv.rotation.y = Math.PI * ee;
  box(0.06, 0.08, 0.05, bez, 0, 0.02, 0, piv);
  box(0.6, 0.38, 0.04, bez, 0, 0.22, -0.02, piv);
  box(0.36, 0.22, 0.05, M('#15181c', { roughness: 0.5 }), 0, 0.22, 0.02, piv);                      // the back housing
  const col = o.red ? '#ff3a30' : (o.screenCol || '#cfe6ff');
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.56, 0.34), new THREE.MeshBasicMaterial({ color: col }));
  scr.position.set(0, 0.22, -0.041); scr.rotation.y = Math.PI; scr.userData.hw = 0.28; scr.userData.hh = 0.17; scr.name = 'monScreen'; piv.add(scr);
  box(0.06, 0.03, 0.04, M('#0a0a0a'), 0, 0.425, -0.02, piv); box(0.012, 0.012, 0.005, new THREE.MeshBasicMaterial({ color: '#ff2a1e' }), 0.02, 0.425, -0.041, piv);
  // cables: out of the housing's back, over the table's far edge, down to the floor and along it into the back wall
  const cab = M('#0b0c0e', { roughness: 0.7 }), pulse = o.pulse ?? 0;
  const glow = new THREE.MeshBasicMaterial({ color: o.red ? '#ff4a3a' : '#5fe6ff' });
  W.scene.updateMatrixWorld(true);
  const back = piv.localToWorld(new THREE.Vector3(0, 0.2, 0.06));
  const run = (pts, w, seed) => {
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], b = pts[i + 1], d = b.clone().sub(a), L = d.length();
      const m = box(w, L, w, cab, (a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2, G); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.clone().normalize());
      if (pulse > 0) for (let k = 0; k < 3; k++) {                    // light blocks travelling along the cable
        const u = ((pulse * 1.7 + k / 3 + seed * 0.13 + i * 0.21) % 1), p = a.clone().lerp(b, u);
        const g = box(w * 1.15, Math.min(0.03, L * 0.2), w * 1.15, glow, p.x, p.y, p.z, G); g.quaternion.copy(m.quaternion); g.castShadow = false;
      }
    }
  };
  const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
  for (const [dx, sd] of [[-0.09, 0], [0.0, 1], [0.1, 2]]) {
    const p0 = back.clone().add(V3(dx, -0.04 * sd, 0));
    run([p0, V3(p0.x, ym + 0.03, p0.z + 0.04), V3(T.x + dx * 2 + 0.55, ym + 0.03, zm + 0.3 + dx), V3(T.x + dx * 2 + 1.02, ym - 0.02, zm + 0.3 + dx),
         V3(T.x + dx * 2 + 1.05, 0.03, zm + 0.3), V3(1.62, 0.03, zm + 0.3 + dx * 2), V3(1.66, 1.1 + sd * 0.3, zm + 0.3 + dx * 2)], 0.035, sd);
  }
  if (pulse > 0) { const l = new THREE.PointLight(o.red ? '#ff4a3a' : '#5fe6ff', 0.35, 1.6, 1.6); l.position.set(T.x + 0.9, 0.5, zm + 0.3); G.add(l); }
  // the keyboard (EP10)
  box(0.44, 0.02, 0.15, M('#15181c'), T.x - 0.04, ym + 0.01, T.z - 0.48, G);
  // the side monitor on the near-left corner, turned toward the doorway (the hospital recording)
  const sx = T.x - 0.72, sz = T.z + 0.32, sry = 0.55;
  const sg = new THREE.Group(); sg.position.set(sx, ym, sz); sg.rotation.y = sry; G.add(sg);
  box(0.2, 0.012, 0.13, bez, 0, 0.006, 0, sg); box(0.04, 0.09, 0.04, bez, 0, 0.05, 0, sg);
  box(0.44, 0.3, 0.035, bez, 0, 0.24, 0, sg);
  const sideOn = o.side ?? true;
  const ss = new THREE.Mesh(new THREE.PlaneGeometry(0.41, 0.27), new THREE.MeshBasicMaterial({ color: sideOn ? '#bfe0d8' : '#07090b' }));
  ss.position.set(0, 0.24, 0.019); ss.userData.hw = 0.205; ss.userData.hh = 0.135; ss.name = 'sideScreen'; sg.add(ss);
  if (sideOn) { const l = new THREE.PointLight('#bfe0ff', 0.35, 1.4, 1.6); l.position.set(sx + 0.15, ym + 0.3, sz + 0.3); G.add(l); }
  // the sister, chained, behind the table
  const R = chainedChair(G, { x: T.x, z: T.z - 1.05, face: o.face || 'worried', raise: o.raise });
  const sp = R.s.userData.headPivot;
  sp.rotation.x = o.head ?? 0; sp.rotation.y = o.headY ?? 0;
  const lf = new THREE.PointLight(o.red ? '#ff3a30' : '#bcd8ff', o.monLight ?? 0.35, 1.6, 1.6);
  lf.position.copy(piv.localToWorld(new THREE.Vector3(0, 0.22, -0.3))); G.add(lf);
  W.scene.updateMatrixWorld(true);
  return { s: R.s, screen: scr, side: ss, piv };
}

// A hospital ward three years ago (a separate set far from flat 47, x = 60): pale two-tone walls, a fluorescent panel, night blinds,
// a steel bed, ALEX lying unconscious (eyes closed, a white bandage round the head, no injuries shown), a blanket, an IV stand, a
// heart monitor with a green trace (no text). Returns {G, alex, bed:{x,z}, ecg}.
function buildHospital(W, o = {}) {
  const X = 60, G = new THREE.Group(); G.name = 'hospital'; W.scene.add(G); W.scene.fog = null;
  const w = 3.2, d = 3.6, h = 2.6;
  const tile = canvasTex(64, 64, (g, cw, ch) => { g.fillStyle = '#c7cfcc'; g.fillRect(0, 0, cw, ch); g.fillStyle = '#b3bcb9'; g.fillRect(0, 0, cw, 2); g.fillRect(0, 0, 2, ch); g.fillStyle = '#bcc5c2'; g.fillRect(32, 32, 32, 32); g.fillRect(0, 0, 32, 32); }, { repeat: [w / 0.6, d / 0.6], nearest: true });
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(w, d), MT(tile)); fl.rotation.x = -Math.PI / 2; fl.position.set(X, 0, 0); fl.receiveShadow = true; G.add(fl);
  const ce = new THREE.Mesh(new THREE.PlaneGeometry(w, d), M('#e6ebe8')); ce.rotation.x = Math.PI / 2; ce.position.set(X, h, 0); G.add(ce);
  const wallT = canvasTex(64, 256, (g, cw, ch) => { g.fillStyle = '#e3e9e5'; g.fillRect(0, 0, cw, ch); g.fillStyle = '#9fc2b8'; g.fillRect(0, ch * 0.6, cw, ch); g.fillStyle = '#7ea79b'; g.fillRect(0, ch * 0.6, cw, 5); }, { repeat: [3, 1] });
  const wall = (len, x, z, ry) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(len, h), MT(wallT.clone())); m.material.map.needsUpdate = true; m.rotation.y = ry; m.position.set(x, h / 2, z); m.receiveShadow = true; G.add(m); };
  wall(w, X, -d / 2, 0); wall(w, X, d / 2, Math.PI); wall(d, X - w / 2, 0, Math.PI / 2); wall(d, X + w / 2, 0, -Math.PI / 2);
  // window with blinds (night), on the right wall
  box(0.04, 1.1, 1.3, M('#d9dedb'), X + w / 2 - 0.02, 1.5, -0.3, G);
  box(0.02, 0.98, 1.18, new THREE.MeshBasicMaterial({ color: '#1a2a44' }), X + w / 2 - 0.04, 1.5, -0.3, G);
  for (let i = 0; i < 12; i++) box(0.03, 0.035, 1.16, M('#cfd6d3'), X + w / 2 - 0.07, 1.06 + i * 0.08, -0.3, G);
  // fluorescent ceiling panel
  const panel = box(0.6, 0.03, 1.2, new THREE.MeshBasicMaterial({ color: '#f2fbff' }), X, h - 0.02, 0, G); panel.castShadow = false;
  const L1 = new THREE.PointLight('#e9f4ff', o.light ?? 1.1, 5, 1.4); L1.position.set(X, h - 0.3, 0.1); L1.castShadow = true; L1.shadow.mapSize.set(1024, 1024); L1.shadow.bias = -0.003; G.add(L1);
  G.add(new THREE.HemisphereLight('#dfeaf0', '#606a68', 0.5));
  // the bed (head against the back wall, -z)
  const bx = X - 0.2, bz = -0.45, steel = M('#c9cfd3', { metalness: 0.5, roughness: 0.4 });
  for (const [dx, dz] of [[-0.45, -0.95], [0.45, -0.95], [-0.45, 0.95], [0.45, 0.95]]) box(0.05, 0.5, 0.05, steel, bx + dx, 0.25, bz + dz, G);
  box(0.96, 0.08, 2.0, steel, bx, 0.5, bz, G);
  box(0.96, 0.55, 0.05, steel, bx, 0.78, bz - 1.0, G); box(0.96, 0.32, 0.05, steel, bx, 0.66, bz + 1.0, G);
  box(0.05, 0.05, 0.9, steel, bx + 0.5, 0.78, bz - 0.2, G);                                                  // side rail
  box(0.9, 0.12, 1.94, M('#f2f4f3'), bx, 0.6, bz, G);                                                       // mattress
  box(0.6, 0.12, 0.34, M('#ffffff'), bx, 0.72, bz - 0.78, G);                                               // pillow
  // ALEX: lying on his back, head on the pillow (rotated: +y -> -z, face up)
  const a = makePerson('alex', { face: o.face || 'closed' }); a.rotation.x = -Math.PI / 2; a.position.set(bx, 0.79, bz + 0.86); G.add(a);
  a.userData.headPivot.rotation.x = 0.05;
  for (const sd of [-1, 1]) { const ar = a.userData.arms[sd]; ar.rotation.z = -sd * 0.08; }
  const band = M('#f4f4f0');
  box(0.385, 0.07, 0.385, band, 0, 0.36 / 2 + 0.01 + 0.08, 0, a.userData.headPivot);                        // the bandage round the head
  box(0.09, 0.05, 0.02, band, -0.08, 0.36 / 2 + 0.01 + 0.11, 0.195, a.userData.headPivot);
  box(0.94, 0.4, 1.42, M('#9cc3dc'), bx, 0.77, bz + 0.22, G);                                                // the blanket (over the body)
  box(0.96, 0.03, 0.18, M('#ffffff'), bx, 0.975, bz - 0.42, G);                                             // folded sheet edge
  // IV stand
  const ivx = bx + 0.75, ivz = bz - 0.55;
  box(0.03, 1.8, 0.03, steel, ivx, 0.9, ivz, G); box(0.4, 0.03, 0.03, steel, ivx, 1.8, ivz, G); box(0.3, 0.03, 0.3, steel, ivx, 0.02, ivz, G);
  const bag = box(0.12, 0.2, 0.05, M('#d7ecf5', { transparent: true, opacity: 0.75 }), ivx + 0.15, 1.66, ivz, G); bag.castShadow = false;
  // the heart monitor on a wall arm, screen toward the bed (green trace, no text)
  const ecg = canvasTex(128, 80, (g, cw, ch) => {
    g.fillStyle = '#04110b'; g.fillRect(0, 0, cw, ch); g.fillStyle = '#0f3a24'; for (let x = 0; x < cw; x += 16) g.fillRect(x, 0, 1, ch);
    g.fillStyle = '#5dff9a'; const base = 46, beat = [0, 0, -2, 0, 3, -22, 14, 0, -4, 0];
    let y = base; for (let x = 0; x < cw; x += 2) { const k = Math.floor(x / 2) % 24; const dy = k < beat.length ? beat[k] : 0; g.fillRect(x, base + dy, 2, 2); if (k === 5) g.fillRect(x, base - 22, 2, 22); if (k === 6) g.fillRect(x, base, 2, 14); }
    g.fillStyle = '#5dff9a'; g.fillRect(cw - 26, 8, 18, 3); g.fillRect(cw - 26, 16, 12, 3);
  }, { nearest: true });
  const mx = bx - 0.75, mz = bz - 0.85;
  box(0.04, 0.04, 0.3, steel, mx, 1.62, mz - 0.14, G);
  const mon = new THREE.Group(); mon.position.set(mx, 1.62, mz + 0.05); mon.rotation.y = 0.55; G.add(mon);
  box(0.42, 0.3, 0.08, M('#e9ecea'), 0, 0, 0, mon);
  const es = new THREE.Mesh(new THREE.PlaneGeometry(0.36, 0.24), new THREE.MeshBasicMaterial({ map: ecg })); es.position.set(0, 0, 0.041); mon.add(es);
  const gl = new THREE.PointLight('#5dff9a', 0.2, 1.0, 1.6); gl.position.set(mx + 0.1, 1.6, mz + 0.3); G.add(gl);
  // a visitor's chair by the bed (the sister's)
  const ch = makeChair(); ch.position.set(bx + 0.85, 0, bz + 0.25); ch.rotation.y = -Math.PI / 2 - 0.2; G.add(ch);
  box(0.36, 0.05, 0.3, M(PAL.sweater), bx + 0.85, 0.49, bz + 0.25, G);                                      // her mustard cardigan left on it
  W.scene.updateMatrixWorld(true);
  return { G, alex: a, bed: { x: bx, z: bz }, X };
}

window.PRICE = { THREE, PAL, buildWorld, makePerson, makeGlass, makePhone, makeOpenHand, lightsInterior, lightsStairwell, phoneLight, box, M,
  enableMirror, mirrorOnly, makeFootprint, footprints, makeChair, seatPerson, makeRopes,
  pixTex, canvasTex, MT, makeForearm, scarTex, plateTex, mulberry,
  makeKey, makeDoor204, buildCorridor, sisterFace,
  room204Wall, makeMirror204, cameraOnly, makeMirror,
  dissolve, mirrorCracks, room204WallHole, shatterMirror204, makeFeedScreen, staticTex, buildMonitorRoom, buildOperatorRoom, sisterSeated, OPS, makeForearm7,
  buildKitchen, makeGlassBreak, makeKnife, monitorCracks, collapseMonitorRoom, flatBehindMirror,
  wristNumTex, makeForearm9, wristBadge, makeBalaclava, makeOldCop,
  room204Desk, kneelPose,
  chainedChair, desk11, buildHospital };
