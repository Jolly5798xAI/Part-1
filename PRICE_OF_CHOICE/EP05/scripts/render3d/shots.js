// Shot library. EP01 «Стакан воды» and EP02 angles are kept unchanged (same apartment, same characters);
// EP03 shots use the "E3_" prefix (bottom of the list). Each shot builds the shared world, places
// characters/props and a camera. t ∈ [0,1] drives animated shots (frames > 1).
/* global THREE, PRICE */
(function () {
  const P = PRICE;
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const PEEP = V(0, 1.58, -0.215); // outer lens of the peephole

  function camera(fov, pos, look, aspect) {
    const c = new THREE.PerspectiveCamera(fov, aspect, 0.01, 60);
    c.position.copy(pos); c.lookAt(look); return c;
  }
  function alex(o = {}) { return P.makePerson('alex', o); }

  // a sleeve + hand rig whose pivot is the shoulder end
  // place an arm so its hand sits at `hand` coming from `shoulder`
  function aimArm(a, shoulder, hand) {
    const d = hand.clone().sub(shoulder).normalize();
    a.quaternion.setFromUnitVectors(V(0, -1, 0), d);
    a.position.copy(hand.clone().sub(d.multiplyScalar(0.6)));
    return a;
  }
  function arm(bloody = false) {
    const g = new THREE.Group();
    P.box(0.16, 0.55, 0.18, P.M(P.PAL.hoodie), 0, -0.275, 0, g);
    P.box(0.15, 0.13, 0.16, P.M(P.PAL.skinAlex), 0, -0.6, 0, g, 'hand');
    return g;
  }

  // POV phone rig attached to the camera
  function povPhone(scene, cam, o = {}) {
    scene.add(cam);
    const rig = new THREE.Group(); cam.add(rig);
    rig.position.set(o.x ?? 0, o.y ?? -0.035, (o.z ?? -0.3) - 0.09);
    rig.rotation.set(o.rx ?? 0.12, o.ry ?? -0.05, o.rz ?? 0.06);
    const phone = P.makePhone(o.screen || '#141b26'); rig.add(phone);
    // fingers + palm behind the phone
    const skin = P.M(P.PAL.skinAlex);
    P.box(0.095, 0.11, 0.03, skin, 0.004, -0.055, -0.022, rig);
    P.box(0.022, 0.05, 0.022, skin, -0.05, -0.02, -0.004, rig).rotation.z = 0.3; // thumb side
    for (let i = 0; i < 3; i++) P.box(0.02, 0.022, 0.024, skin, 0.047, -0.01 - i * 0.035, -0.004, rig);
    P.box(0.13, 0.32, 0.14, P.M(P.PAL.hoodie), 0.02, -0.27, -0.06, rig).rotation.x = -0.5; // sleeve
    // glow on the hand & surroundings
    const l = new THREE.PointLight('#a9c8ff', (o.glow ?? 0.9) * 0.04, 0.6, 2); l.position.set(0, 0.12, 0.2); rig.add(l);
    return phone.getObjectByName('screen');
  }

  function screenQuad(screen, cam, W, H, hw = 0.035, hh = 0.075) {
    screen.updateWorldMatrix(true, false); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
    return [[-hw, hh], [hw, hh], [hw, -hh], [-hw, -hh]].map(([x, y]) => {
      const v = V(x, y, 0).applyMatrix4(screen.matrixWorld).project(cam);
      return [Math.round((v.x + 1) / 2 * W), Math.round((1 - v.y) / 2 * H)];
    });
  }

  function stairwellCast(W, o = {}) {
    const cop = P.makePerson('cop'); cop.position.set(-0.2, 0, -1.15); cop.rotation.y = 0.08; W.scene.add(cop);
    const dbl = alex({ bloodyRight: true, face: o.face || 'neutral' }); dbl.position.set(1.0, 0, -2.78); dbl.rotation.y = Math.PI; W.scene.add(dbl);
    if (o.dblNear) { dbl.position.set(0.12, 0, -0.78); dbl.rotation.y = 0; }
    if (o.headTurn !== undefined) dbl.userData.headPivot.rotation.y = o.headTurn;
    if (o.copArm) { cop.userData.arms[1].rotation.x = -1.2; }
    return { cop, dbl };
  }

  // ---------- EP02 helpers (only used by E2_* shots) ----------
  // open the door inward by `r` radians (hinge on the right, lock edge moves into the flat)
  function ajar(W, r) { W.objs.doorPivot.rotation.y = r; W.scene.updateMatrixWorld(true); }
  function leverPos(W) { W.scene.updateMatrixWorld(true); return W.objs.lever.getWorldPosition(V(0, 0, 0)); }
  // point an arm of a makePerson figure at a world-space target
  function reachTo(person, side, target) {
    person.updateMatrixWorld(true);
    const a = person.userData.arms[side];
    const sh = a.getWorldPosition(V(0, 0, 0));
    const d = target.clone().sub(sh).applyQuaternion(person.quaternion.clone().invert()).normalize();
    a.quaternion.setFromUnitVectors(V(0, -1, 0), d);
  }
  // the stairwell's fluorescent tube, shadow-casting, so it only spills in through the gap
  function gapLight(W, k = 1) {
    const l = new THREE.PointLight('#eef8e2', 9 * k, 9, 1.4); l.position.set(0.1, 2.55, -1.6);
    l.castShadow = true; l.shadow.mapSize.set(1024, 1024); l.shadow.bias = -0.002; W.scene.add(l);
    const l2 = new THREE.PointLight('#e6f3dc', 3 * k, 3, 1.5); l2.position.set(-0.6, 1.6, -0.5);
    l2.castShadow = true; l2.shadow.mapSize.set(1024, 1024); l2.shadow.bias = -0.002; W.scene.add(l2);
  }
  // water spreading in from under the door (t 0..1), flat low-poly blobs
  function puddle(W, t) {
    const m = new THREE.MeshStandardMaterial({ color: '#5b90a8', emissive: '#0f2d37', roughness: 0.12, metalness: 0.0, transparent: true, opacity: 0.8, flatShading: true });
    const rnd = (s => () => { s = (s * 16807) % 2147483647; return s / 2147483647; })(7);
    const blobs = [];
    for (let i = 0; i < 16; i++) blobs.push([-0.38 + 0.76 * rnd(), 0.03 + 0.42 * rnd(), 0.06 + 0.12 * rnd(), rnd() * 0.5]);
    for (const [x, z, r, delay] of blobs) {
      const k = Math.max(0, Math.min(1, (t - delay) / (1 - delay + 1e-6)));
      const reach = k * 0.5; if (z > reach + 0.02) continue;
      const rr = r * Math.min(1, (reach - z + 0.12) / 0.12) * (0.4 + 0.6 * k);
      if (rr <= 0.005) continue;
      const b = new THREE.Mesh(new THREE.CylinderGeometry(rr, rr, 0.003, 7), m); b.position.set(x, 0.0135 + 0.0002 * blobs.findIndex(q => q[0] === x), z); /* above the door mat */ b.rotation.y = x * 9; b.receiveShadow = true; W.scene.add(b);
    }
    if (t > 0.02) { const s = new THREE.Mesh(new THREE.BoxGeometry(0.86, 0.003, 0.04 + 0.05 * t), m); s.position.set(0, 0.0135, 0.02 + 0.025 * t); W.scene.add(s); }
  }


  // ---------- EP03 helpers (only used by E3_* shots) ----------
  // EP02 left the flat like this: puddle at the door, empty glass, door shut
  function aftermath(W) {
    const g = P.makeGlass(); g.children[2].visible = false; g.children[3].visible = false; g.position.set(0.12, 0, 0.26); W.scene.add(g);
    puddle(W, 1);
  }
  // alternate left/right prints along a polyline (stride ~0.27 m); heading follows the walking direction
  function trail(pts, stride = 0.27, first = -1) {
    const out = []; let side = first;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, z0] = pts[i], [x1, z1] = pts[i + 1]; const L = Math.hypot(x1 - x0, z1 - z0); const n = Math.max(1, Math.round(L / stride));
      for (let k = (i === 0 ? 0 : 1); k <= n; k++) {
        const u = k / n, dx = (x1 - x0) / L, dz = (z1 - z0) / L; const a = Math.atan2(-dx, -dz);
        out.push([x0 + (x1 - x0) * u + side * 0.07 * dz, z0 + (z1 - z0) * u - side * 0.07 * dx, a, side]); side = -side;
      }
    }
    return out;
  }
  // trail A: from the puddle at the front door, past Alex, turning round to stand facing him (EP03 0–20 s)
  const TRAIL_A = trail([[-0.3, 0.16], [-0.36, 0.7], [-0.25, 1.15], [0.0, 1.32]]);
  const PAIR_1 = [[-0.08, 0.98, 0.0, -1], [0.09, 0.96, 0.0, 1]];   // standing facing Alex
  const PAIR_2 = [[-0.08, 0.80, 0.0, -1], [0.09, 0.78, 0.0, 1]];   // after Alex's step back
  // where the double stood behind Alex at the mirror, and the trail from there into the bedroom
  const PAIR_M = [[0.25, 2.37, Math.PI / 2, -1], [0.27, 2.22, Math.PI / 2, 1]];
  const TRAIL_B = trail([[0.42, 2.48], [0.72, 2.75], [1.0, 2.9], [1.38, 2.98]], 0.27, 1);
  function prints(W, o = {}) {
    if (o.a !== undefined) P.footprints(W.scene, TRAIL_A, o.a);
    if (o.p1) P.footprints(W.scene, PAIR_1, o.p1);
    if (o.p2) P.footprints(W.scene, PAIR_2, o.p2);
    if (o.m) P.footprints(W.scene, PAIR_M, o.m);
    if (o.b !== undefined) P.footprints(W.scene, TRAIL_B, o.b);
  }
  // Alex positions in EP03
  const AT_DOOR = V(0.0, 0, 0.45), AT_MIRROR = V(-0.28, 0, 2.1), AT_BEDDOOR = V(0.55, 0, 2.78);
  const DBL_M = V(0.25, 0, 2.3), DBL_ROT = -1.6; // the double behind Alex at the mirror (reflection only)
  // the tied man in the bedroom (Alex's model) on a chair facing the doorway
  const CHAIR = V(2.4, 0, 2.92);
  function tiedMan(W, o = {}) {
    const ch = P.makeChair(); ch.position.copy(CHAIR); ch.rotation.y = -Math.PI / 2; W.scene.add(ch);
    const m = alex({ face: o.face || 'tape_worried' }); m.position.set(CHAIR.x, 0, CHAIR.z); m.rotation.y = -Math.PI / 2; P.seatPerson(m); W.scene.add(m);
    if (o.head !== undefined) m.userData.headPivot.rotation.y = o.head;
    if (o.tilt !== undefined) m.userData.headPivot.rotation.x = o.tilt;
    // tape strip (3D, so it catches the light)
    P.box(0.22, 0.085, 0.014, P.M('#b4b2a8', { roughness: 0.6 }), 0, 0.085, 0.186, m.userData.headPivot);
    const r = P.makeRopes(); r.position.copy(CHAIR); r.rotation.y = -Math.PI / 2; W.scene.add(r);
    return m;
  }
  function bedroomLights(W, o = {}) {
    const moon = new THREE.DirectionalLight('#86a2dc', (o.moon ?? 1.5) * 1.6); moon.position.set(7.5, 3.4, 3.2); moon.target.position.set(2.3, 0.5, 2.9);
    moon.castShadow = true; moon.shadow.mapSize.set(2048, 2048); Object.assign(moon.shadow.camera, { left: -2.5, right: 2.5, top: 2.5, bottom: -2.5, near: 1, far: 12 }); moon.shadow.bias = -0.0008;
    W.scene.add(moon, moon.target);
    W.scene.add(new THREE.HemisphereLight('#6f80aa', '#2a2218', (o.amb ?? 0.35) * 2.2));
  }
  // the second phone on the bedroom floor, screen up; lit = glowing
  function floorPhone(W, lit, k = 1) {
    const ph = P.makePhone(lit ? '#d8e6ff' : '#0c0f14'); ph.position.set(1.92, 0.006, 3.08); ph.rotation.set(-Math.PI / 2, 0, 0.5); W.scene.add(ph);
    if (lit) { const l = new THREE.PointLight('#a8c4ff', 1.6 * k, 2.2, 1.6); l.position.set(1.92, 0.25, 3.08); W.scene.add(l); }
    return ph;
  }
  function bedLeak(W, col, k = 1) { const m = W.objs.bed.bleak.material; m.color.set(col); m.color.multiplyScalar(k); }
  function bedDoor(W, r) { W.objs.bed.pivot.rotation.y = r; W.scene.updateMatrixWorld(true); }
  // Alex holding his phone up (right hand), screen glow on the face
  function alexWithPhone(o = {}) {
    const a = alex({ face: o.face || 'worried' });
    a.userData.arms[1].rotation.x = -1.25; a.userData.arms[1].rotation.z = 0.25;
    const ph = P.makePhone(o.screen || '#cfe0ff'); ph.position.set(0.0, -0.62, 0.02); ph.rotation.x = -Math.PI / 2 + 0.25; a.userData.arms[1].add(ph);
    return a;
  }

  // ---------- EP04 helpers (only used by E4_* shots) ----------
  const ALEX4 = V(1.78, 0, 2.92);                  // Alex in the bedroom, in front of the chair, facing it (+x)
  // the bedroom as EP03 left it: door open, wet trail in the hall, the second phone dark on the floor, moonlight
  function bed4(W, o = {}) {
    bedDoor(W, 1.25); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2, m: 1, b: TRAIL_B.length }); aftermath(W);
    if (o.floorPhone !== false) floorPhone(W, false);
    bedroomLights(W, { moon: o.moon ?? 1.3, amb: o.amb ?? 0.28 });
    P.lightsInterior(W.scene, { amb: 0.3, moon: 0.4, warm: o.warm ?? 0.8 });
  }
  // the tied double; o.tape: 1 = taped (EP03), 0 = tape gone, 0<k<1 = being ripped off (k = peel progress)
  function tiedMan4(W, o = {}) {
    const ch = P.makeChair(); ch.position.copy(CHAIR); ch.rotation.y = -Math.PI / 2; W.scene.add(ch);
    const m = alex({ face: o.face || 'worried_redmark' }); m.position.set(CHAIR.x, 0, CHAIR.z); m.rotation.y = -Math.PI / 2; P.seatPerson(m); W.scene.add(m);
    if (o.head !== undefined) m.userData.headPivot.rotation.y = o.head;
    if (o.tilt !== undefined) m.userData.headPivot.rotation.x = o.tilt;
    if (o.hideArms) { m.userData.arms[1].visible = false; m.userData.arms[-1].visible = false; }
    const tape = o.tape ?? 0; let strip = null;
    if (tape > 0) {
      const piv = new THREE.Group(); piv.position.set(-0.11, 0.085, 0.188); m.userData.headPivot.add(piv);
      strip = P.box(0.22, 0.085, 0.014, P.M('#b4b2a8', { roughness: 0.6 }), 0.11, 0, 0, piv);
      if (tape < 1) piv.rotation.y = -1.35 * Math.min(1, tape);
    }
    const r = P.makeRopes(); r.position.copy(CHAIR); r.rotation.y = -Math.PI / 2; W.scene.add(r);
    m.userData.strip = strip; return m;
  }
  // a cold glow from the phone in Alex's hand, near the camera
  function camGlow(W, cam, k = 1, pos = [0.08, -0.12, 0.05]) { W.scene.add(cam); const l = new THREE.PointLight('#a9c8ff', 0.5 * k, 2.2, 1.6); l.position.set(...pos); cam.add(l); }
  // the officer, now masked (black balaclava, black gloves), standing in the bedroom doorway facing into the room
  function maskedCop(o = {}) { const c = P.makePerson('cop', { face: 'mask', gloves: true }); return c; }
  // the front door left ajar, stairwell light spilling down the hall (how he got in is not shown)
  function frontDoorOpen(W, k = 1) { ajar(W, 0.42); gapLight(W, 0.55 * k); }
  // a phone held in a black glove, screen toward the camera (o.lit colour); returns the screen mesh
  function gloveWithPhone(parent, o = {}) {
    const g = new THREE.Group(); parent.add(g);
    const ph = P.makePhone(o.screen || '#d8e6ff'); g.add(ph);
    const gl = P.M('#151517', { roughness: 0.6 });
    P.box(0.095, 0.1, 0.03, gl, 0.0, -0.06, -0.022, g);
    for (let i = 0; i < 3; i++) P.box(0.022, 0.022, 0.026, gl, -0.048, -0.02 - i * 0.035, -0.002, g);
    P.box(0.024, 0.05, 0.024, gl, 0.05, -0.03, -0.004, g).rotation.z = -0.3;
    if (o.lit !== false) { const l = new THREE.PointLight('#bcd2ff', 0.35, 1.2, 1.7); l.position.set(0, 0, 0.12); g.add(l); }
    return { group: g, screen: ph.getObjectByName('screen') };
  }
  // sister's room for the covert photo (separate small set, not part of flat 47; deliberately anonymous)
  function sisterRoom(W) {
    const sc = W.scene; sc.background = new THREE.Color('#0d0b0a');
    const wall = P.canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#7d5f4f'; g.fillRect(0, 0, w, h); g.fillStyle = '#86685a'; for (let x = 0; x < w; x += 32) g.fillRect(x + 12, 0, 8, h); }, { repeat: [4, 3] });
    const back = new THREE.Mesh(new THREE.PlaneGeometry(4, 2.6), P.MT(wall)); back.position.set(0, 1.3, -0.9); back.receiveShadow = true; sc.add(back);
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(4, 3), P.M('#5a4232')); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 0.3); fl.receiveShadow = true; sc.add(fl);
    // she sits behind a desk that faces the window (the camera is outside it)
    const sis = P.makePerson('sister'); sis.position.set(0.0, -0.3, -0.2); sis.rotation.y = 0.12; sc.add(sis);
    sis.userData.headPivot.rotation.x = 0.36; sis.userData.headPivot.rotation.y = -0.12;            // reading, unaware
    sis.userData.arms[1].rotation.x = -0.75; sis.userData.arms[-1].rotation.x = -0.75;
    P.box(1.3, 0.05, 0.62, P.M('#6b4a32'), 0.1, 0.74, 0.28, sc); P.box(1.3, 0.7, 0.04, P.M('#5a3e2a'), 0.1, 0.37, 0.58, sc); // desk + front panel
    P.box(0.2, 0.025, 0.28, P.M('#e2dccb'), 0.02, 0.775, 0.22, sc); P.box(0.004, 0.03, 0.28, P.M('#9a9282'), 0.02, 0.78, 0.22, sc);    // open book
    P.box(0.07, 0.15, 0.07, P.M('#2f4a5a'), -0.42, 0.84, 0.35, sc);                                                                // a mug
    P.box(0.12, 0.02, 0.12, P.M('#2c2c2c'), 0.55, 0.775, 0.35, sc); P.box(0.02, 0.34, 0.02, P.M('#2c2c2c'), 0.55, 0.94, 0.35, sc);
    const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.13, 0.13, 6), P.M('#efe2c0', { emissive: '#8a6a32' })); shade.position.set(0.55, 1.14, 0.35); sc.add(shade);
    P.box(0.5, 1.4, 0.4, P.M('#3a3330'), -1.0, 0.7, -0.68, sc); P.box(0.7, 0.9, 0.04, P.M('#5b4a3e'), 0.9, 1.6, -0.87, sc);         // shelf + a picture frame (blank)
    const warm = new THREE.PointLight('#ffb36b', 1.9, 4, 1.4); warm.position.set(0.4, 1.2, 0.55); sc.add(warm);
    const fill = new THREE.PointLight('#ffcf9a', 0.6, 3, 1.5); fill.position.set(-0.4, 1.6, 0.9); sc.add(fill);
    sc.add(new THREE.HemisphereLight('#6a5a50', '#1a1410', 0.6));
    // the window it was taken through: dark frame bars in the foreground
    const fr = P.M('#141416'); P.box(0.09, 3, 0.05, fr, -0.42, 1.3, 1.5, sc); P.box(2, 0.09, 0.05, fr, 0, 0.58, 1.5, sc);
    return sis;
  }

  // ---------- EP05 helpers (only used by E5_* shots) ----------
  const ZE = -13;                                           // door 204 (end of the hotel corridor)
  // the bedroom as EP04 left it: the officer came in through the open front door
  function bed5(W, o = {}) { bed4(W, o); frontDoorOpen(W, o.gap ?? 1.3); }
  // the officer's raised hand holding the key out (key hangs from the glove); returns the key
  function copWithKey(W, e = 1, o = {}) {
    const c = maskedCop(); c.position.set(0.98, 0, 2.9); c.rotation.y = Math.PI / 2; W.scene.add(c);
    const a = c.userData.arms[-1]; a.rotation.x = -1.35 * e; a.rotation.z = 0.06 * e;
    const gl = P.M('#151517', { roughness: 0.6 });
    P.box(0.05, 0.03, 0.05, gl, 0, -0.6, 0.06, a);                                   // pinched fingers
    const k = P.makeKey(); k.position.set(0, -0.6, 0.075); k.rotation.x = 1.35 * e + (o.swing ?? 0); a.add(k);
    W.scene.updateMatrixWorld(true); return { cop: c, key: k };
  }
  // a blocky walk / run cycle on a makePerson figure (phase in cycles)
  function walkPose(p, ph, amp = 0.45) {
    const s = Math.sin(ph * Math.PI * 2);
    p.userData.legL.rotation.x = amp * s; p.userData.legR.rotation.x = -amp * s;
    p.userData.arms[1].rotation.x = amp * 0.8 * s; p.userData.arms[-1].rotation.x = -amp * 0.8 * s;
  }
  function corridorWorld(W, o = {}) {
    bed4(W, { floorPhone: false }); ajar(W, o.door ?? 1.45);
    return P.buildCorridor(W, o);
  }
  // Alex in room 204, in front of the table, facing it (-z); the sister behind him (k: 0 = hidden in the doorway's dark, 1 = at his shoulder)
  function sisterAt(W, k) {
    const s = P.makePerson('sister', { face: W.p.face || 'neutral' }); const e = k * k * (3 - 2 * k);
    s.position.set(-0.64 + 0.3 * e, 0, ZE + 0.3 - 0.5 * e); s.rotation.y = Math.PI - 0.15; W.scene.add(s);
    s.userData.headPivot.rotation.x = 0.1; return s;
  }
  function alexAtTable(W) {
    const a = alex({ face: W.p.alexFace || 'wide_worried' }); a.position.set(0.0, 0, ZE - 0.62); a.rotation.y = Math.PI; W.scene.add(a);
    a.userData.headPivot.rotation.x = 0.28; a.userData.arms[1].rotation.x = -0.15; a.userData.arms[-1].rotation.x = -0.15; return a;
  }

  const SHOTS = {
    // 0.0 — hook: the glass of water by the door
    S01_glass_hook: { desc: 'Glass of water on the floor by the front door, light leaking under the door', make(W, t, A) {
      const g = P.makeGlass(); g.position.set(0.12, 0, 0.26); W.scene.add(g);
      P.lightsInterior(W.scene, { leak: 9, amb: 0.45 });
      return camera(42, V(0.45, 0.24, 0.98), V(0.1, 0.17, 0.2), A);
    } },
    // door from inside, low angle (banging)
    S02_door_inside: { desc: 'Front door from inside, low dramatic angle, light under the door', make(W, t, A) {
      const g = P.makeGlass(); g.position.set(0.12, 0, 0.26); W.scene.add(g);
      P.lightsInterior(W.scene, { leak: 8 });
      return camera(48, V(-0.35, 0.75, 1.45), V(0.0, 1.15, 0.0), A);
    } },
    // POV phone — first message
    S03_phone_msg1: { desc: 'POV: phone in hand in the dark entryway, neutral screen', phone: true, make(W, t, A) {
      P.lightsInterior(W.scene, { amb: 0.4, moon: 0.6 });
      const cam = camera(42, V(0.25, 1.55, 2.3), V(0.1, 1.15, 0.0), A);
      W.screen = povPhone(W.scene, cam, { rx: 0.1, ry: -0.08, rz: 0.05, z: -0.28 });
      return cam;
    } },
    // Alex's face lit by the phone
    S04_alex_phone_face: { desc: 'Alex close-up, face lit cold-blue by the phone, worried', make(W, t, A) {
      const a = alex({ face: 'worried' }); a.position.set(0.15, 0, 1.6); a.rotation.y = Math.PI * 0.92; W.scene.add(a);
      a.userData.arms[1].rotation.x = -1.25; a.userData.arms[-1].rotation.x = -1.1;
      const ph = P.makePhone('#cfe0ff'); ph.position.set(0.0, -0.62, 0.02); ph.rotation.x = -Math.PI / 2 + 0.25; a.userData.arms[1].add(ph);
      P.lightsInterior(W.scene, { amb: 0.32, moon: 0.45, warm: 1.2 });
      const pl = new THREE.PointLight('#9cc0ff', 0.4, 1.2, 1.8); pl.position.set(0.12, 1.32, 1.15); W.scene.add(pl);
      return camera(36, V(0.0, 1.62, 0.25), V(0.14, 1.45, 1.6), A);
    } },
    // hand places the glass
    S05_place_glass: { desc: 'Alex\'s hand sets the full glass on the floor by the door; his feet behind', make(W, t, A) {
      const g = P.makeGlass(); g.position.set(0.12, 0, 0.26); W.scene.add(g);
      const a = alex(); a.position.set(0.05, 0, 0.85); a.rotation.y = Math.PI; W.scene.add(a);
      W.scene.add(aimArm(arm(), V(0.42, 0.95, 0.5), V(0.12, 0.19, 0.27)));
      P.lightsInterior(W.scene, { leak: 9, amb: 0.6 });
      return camera(44, V(-0.4, 0.42, 1.05), V(0.1, 0.2, 0.22), A);
    } },
    // POV phone — bank / second task (different angle)
    S06_phone_bank: { desc: 'POV: phone closer, lower angle', phone: true, make(W, t, A) {
      P.lightsInterior(W.scene, { amb: 0.4, moon: 0.6 });
      const cam = camera(40, V(0.1, 1.5, 1.4), V(0.2, 1.0, 0.0), A);
      W.screen = povPhone(W.scene, cam, { rx: 0.05, ry: 0.1, rz: -0.08, z: -0.26, y: -0.02 });
      return cam;
    } },
    // dark entryway, Alex from behind facing the door, shadows of feet under the door
    S07_entry_wide: { desc: 'Dark entryway, Alex from behind facing the front door, two shadows under the door', make(W, t, A) {
      const a = alex(); a.position.set(0.42, 0, 1.45); a.rotation.y = Math.PI * 1.04; W.scene.add(a);
      const g = P.makeGlass(); g.position.set(0.12, 0, 0.26); W.scene.add(g);
      for (const x of [-0.25, -0.12, 0.14, 0.24]) P.box(0.08, 0.014, 0.004, new THREE.MeshBasicMaterial({ color: '#0a0a0a' }), x, 0.006, 0.0035, W.scene);
      P.lightsInterior(W.scene, { leak: 10 });
      return camera(50, V(-0.3, 1.35, 3.75), V(0.08, 1.0, 0.0), A);
    } },
    // Alex leans to the peephole (profile)
    S08_peephole_lean: { desc: 'Alex in profile, eye pressed to the peephole', make(W, t, A) {
      const a = alex({ face: 'worried' }); a.position.set(0.0, 0.04, 0.27); a.rotation.y = Math.PI; W.scene.add(a);
            P.lightsInterior(W.scene, { amb: 0.5 });
      const l = new THREE.PointLight('#ffcf9a', 1.2, 2.0, 1.5); l.position.set(0.7, 1.9, 0.9); W.scene.add(l);
      return camera(44, V(0.5, 1.78, 1.05), V(-0.02, 1.52, 0.05), A);
    } },
    // peephole view: cop + the man facing the wall (fisheye applied in post)
    S09_peephole_wide: { desc: 'Through the peephole: police officer close, a man facing the far wall behind', peephole: true, make(W, t, A) {
      stairwellCast(W); P.lightsStairwell(W.scene);
      return camera(100, PEEP, V(0.2, 1.4, -2.0), A);
    } },
    // peephole, tight on the man at the wall
    S10_peephole_man: { desc: 'Through the peephole: tight on the man standing face to the wall', peephole: true, make(W, t, A) {
      stairwellCast(W); P.lightsStairwell(W.scene);
      return camera(34, PEEP, V(1.0, 1.25, -2.78), A);
    } },
    // reaching for the lock (t: 0 = far, 1 = touching; >1 not used)
    S11_hand_lock: { desc: 'Alex\'s hand reaching for the thumb-turn of the lock', frames: 30, make(W, t, A) {
      const r = W.p.reach ?? t * 0.4; W.scene.add(aimArm(arm(), V(0.25, 1.38, 0.62), V(-0.37 + 0.28 * (1 - r), 1.18 + 0.05 * (1 - r), 0.12 + 0.3 * (1 - r))));
      P.lightsInterior(W.scene, { amb: 0.55, leak: 6 });
      const l = new THREE.PointLight('#ffd9a0', 0.8, 1.5); l.position.set(0.2, 1.4, 0.8); W.scene.add(l);
      return camera(40, V(0.15, 0.98, 1.35), V(-0.3, 1.2, 0.05), A);
    } },
    // phone lights up on the shoe rack
    S12_phone_rack: { desc: 'Phone lying on the shoe rack lights up in the dark', phone: true, make(W, t, A) {
      const ph = P.makePhone('#2b1418'); ph.position.set(0.86, 0.476, 1.18); ph.rotation.set(-Math.PI / 2, 0, 0.35); W.scene.add(ph);
      W.screen = ph.getObjectByName('screen');
      P.lightsInterior(W.scene, { amb: 0.6, moon: 0.7 });
      const l = new THREE.PointLight('#b8c8ff', 0.05, 0.8, 2); l.position.set(0.86, 0.56, 0.75); W.scene.add(l);
      return camera(40, V(0.5, 1.05, 1.62), V(0.86, 0.47, 1.18), A);
    } },
    // door with lever, close, for banging
    S13_door_bang: { desc: 'Door lever and lock close-up from inside, for the banging', make(W, t, A) {
      P.lightsInterior(W.scene, { amb: 0.5, leak: 10 });
      return camera(44, V(0.15, 0.9, 0.85), V(-0.3, 1.1, 0.0), A);
    } },
    // peephole, tight on the silent cop
    S14_peephole_cop: { desc: 'Through the peephole: the officer, frozen, staring at the door', peephole: true, make(W, t, A) {
      stairwellCast(W); P.lightsStairwell(W.scene, { amb: 0.75 });
      return camera(62, PEEP, V(-0.2, 1.5, -1.15), A);
    } },
    // ANIM: the man slowly turns his head 170°
    S15_head_turn: { desc: 'Through the peephole: the man at the wall turns his head all the way round', peephole: true, frames: 60, make(W, t, A) {
      const e = t * t * (3 - 2 * t);
      stairwellCast(W, { headTurn: -e * Math.PI * 0.97 }); P.lightsStairwell(W.scene);
      return camera(30 - 4 * t, PEEP, V(0.95, 1.45, -2.78), A);
    } },
    // the double's face (Alex's face)
    S16_double_face: { desc: 'Through the peephole: the turned head has Alex\'s face', peephole: true, make(W, t, A) {
      stairwellCast(W, { headTurn: -Math.PI * 0.97, face: W.p.face }); P.lightsStairwell(W.scene);
      return camera(24, PEEP, V(0.98, 1.54, -2.78), A);
    } },
    // Alex steps back from the door, seen from the door
    S17_alex_steps_back: { desc: 'Alex stepping back from the door, face lit from below by the leak', make(W, t, A) {
      const a = alex({ face: 'worried' }); a.position.set(0.05, 0, 1.15); a.rotation.y = Math.PI * 0.96; W.scene.add(a);
      a.userData.arms[1].rotation.x = -0.4; a.userData.arms[-1].rotation.x = -0.3; a.userData.legL.rotation.x = -0.35;
      P.lightsInterior(W.scene, { amb: 0.45, leak: 12 });
      const l = new THREE.PointLight('#dff0d0', 1.6, 2.2, 1.4); l.position.set(0.0, 0.4, 0.15); W.scene.add(l);
      return camera(58, V(-0.25, 0.95, 0.06), V(0.05, 1.25, 1.2), A);
    } },
    // bloody palm against the peephole
    S18_bloody_palm: { desc: 'Through the peephole: a blood-smeared palm pressed against the lens', peephole: true, frames: 24, make(W, t, A) {
      stairwellCast(W, { dblNear: true }); P.lightsStairwell(W.scene);
      const h = P.makeOpenHand(true); h.position.set(0.0, 1.5, -0.6 + 0.14 * (W.p.press ?? t)); W.scene.add(h);
      const l = new THREE.PointLight('#eef8e2', 0.8, 0.8); l.position.set(0.2, 1.8, -0.5); W.scene.add(l);
      return camera(70, PEEP, V(0, 1.58, -1.0), A);
    } },
    // POV phone — final message, tight
    S19_phone_final: { desc: 'POV: phone close, final message', phone: true, make(W, t, A) {
      P.lightsInterior(W.scene, { amb: 0.35, moon: 0.5, leak: 10 });
      const cam = camera(38, V(-0.05, 1.4, 1.0), V(0.0, 0.9, 0.0), A);
      W.screen = povPhone(W.scene, cam, { rx: 0.0, ry: 0.0, rz: 0.12, z: -0.22, glow: 1.4 });
      return cam;
    } },
    // ANIM: the lock's thumb-turn rotates by itself — opened from outside
    S20_lock_turns: { desc: 'Lock close-up: the thumb-turn starts turning on its own', frames: 90, make(W, t, A) {
      // jerky rotation: three tries then a full turn
      const k = [[0, 0], [0.18, 0.12], [0.26, 0.05], [0.45, 0.28], [0.55, 0.2], [0.8, 0.85], [1, 1.0]];
      let r = 0; for (let i = 1; i < k.length; i++) if (t <= k[i][0]) { const u = (t - k[i - 1][0]) / (k[i][0] - k[i - 1][0]); r = k[i - 1][1] + (k[i][1] - k[i - 1][1]) * u * u * (3 - 2 * u); break; }
      W.objs.lock.getObjectByName('thumbTurn').rotation.z = -r * Math.PI / 2;
      P.lightsInterior(W.scene, { amb: 0.4, leak: 10 });
      const l = new THREE.PointLight('#ffcf8a', 0.9, 1.0); l.position.set(-0.2, 1.3, 0.5); W.scene.add(l);
      const z = 0.42 - 0.12 * t;
      return camera(32, V(-0.28, 1.24, z), V(-0.37, 1.2, 0.03), A);
    } },
    // ====================================================================== EP02 (same world, same cast)
    // door forced open from outside, Alex's hands on the lever (t: 0 closed -> 1 ajar ~0.2 rad); seen from the lock side
    E2_door_gap: { desc: 'Both of Alex\'s hands on the lever; the door is forced inward, cold light knifes through the gap', frames: 40, make(W, t, A) {
      const k = [[0, 0], [0.25, 0.015], [0.35, 0.01], [0.55, 0.07], [0.62, 0.055], [0.85, 0.17], [1, 0.2]];
      let r = 0; for (let i = 1; i < k.length; i++) if (t <= k[i][0]) { const u = (t - k[i - 1][0]) / (k[i][0] - k[i - 1][0]); r = k[i - 1][1] + (k[i][1] - k[i - 1][1]) * u * u * (3 - 2 * u); break; }
      ajar(W, r);
      const lv = leverPos(W);
      W.scene.add(aimArm(arm(), V(0.3, 1.3, 0.75), lv.clone().add(V(0.06, 0.0, 0.05))));
      W.scene.add(aimArm(arm(), V(-0.1, 1.35, 0.8), lv.clone().add(V(-0.03, 0.03, 0.06))));
      P.lightsInterior(W.scene, { amb: 0.45, leak: 8 }); gapLight(W, 1.2);
      return camera(44, V(-0.66, 1.2, 0.95), V(-0.3, 1.05, 0.0), A);
    } },
    // Alex braces against the ajar door, seen from the back-left of the hallway (params: leg)
    E2_alex_brace: { desc: 'Alex leans into the half-forced door, cold slit of light from the stairwell', make(W, t, A) {
      ajar(W, W.p.ajar ?? 0.17);
      const a = alex({ face: 'worried' }); a.position.set(-0.02, 0, W.p.leg ? 0.62 : 0.58); a.rotation.y = Math.PI * 1.08; W.scene.add(a);
      const lv = leverPos(W);
      reachTo(a, 1, lv.clone().add(V(0.05, 0, 0.04))); reachTo(a, -1, lv.clone().add(V(-0.04, 0.02, 0.05)));
      if (W.p.leg) { a.userData.legL.rotation.x = -0.85; }
      P.lightsInterior(W.scene, { amb: 0.4, moon: 0.6, leak: 7 }); gapLight(W, 1.2);
      return camera(46, V(-0.6, 1.2, 2.55), V(-0.18, 0.98, 0.15), A);
    } },
    // Alex's face in the slit of cold light
    E2_alex_face: { desc: 'Close-up: Alex\'s worried face cut by a slit of cold light from the gap', make(W, t, A) {
      ajar(W, 0.17);
      const a = alex({ face: 'worried' }); a.position.set(-0.02, 0, 0.58); a.rotation.y = Math.PI * 1.08; W.scene.add(a);
      const lv = leverPos(W); reachTo(a, 1, lv.clone().add(V(0.05, 0, 0.04))); reachTo(a, -1, lv.clone().add(V(-0.04, 0.02, 0.05)));
      a.userData.headPivot.rotation.y = -1.35; // turns to the phone on the shoe rack
      P.lightsInterior(W.scene, { amb: 0.32, moon: 0.4, warm: 0.9 }); gapLight(W, 1.4);
      const s = new THREE.SpotLight('#dff0d0', 4, 2.6, 0.35, 0.85, 1.2); s.position.set(-0.5, 1.55, -0.15); s.target.position.set(0.0, 1.55, 0.55); W.scene.add(s, s.target);
      const ph = new THREE.PointLight('#ff9a9a', 1.3, 1.6, 1.6); ph.position.set(0.7, 1.0, 0.9); W.scene.add(ph); // the red lock screen on the rack
      return camera(46, V(0.88, 1.56, 0.22), V(-0.02, 1.54, 0.6), A);
    } },
    // through the gap: a sliver of the stairwell (params: dbl, face)
    E2_gap: { desc: 'Tight on the gap between door edge and frame; the stairwell beyond (the double\'s face in the gap when dbl)', make(W, t, A) {
      ajar(W, 0.2);
      if (W.p.dbl) {
        const d = alex({ bloodyRight: true, face: W.p.face || 'neutral' }); d.position.set(-0.27, 0, -0.56); d.rotation.y = -0.35; W.scene.add(d);
      }
      P.lightsInterior(W.scene, { amb: 0.25, moon: 0.35, warm: 0.8 }); gapLight(W, 1.3);
      const f = new THREE.PointLight('#e6f3dc', W.p.dbl ? 1.6 : 0.9, 1.4, 1.6); f.position.set(-0.35, 1.75, -0.12); W.scene.add(f);
      return camera(W.p.dbl ? 26 : 30, V(-0.68, 1.55, 0.62), V(-0.3, 1.52, -0.42), A);
    } },
    // water seeping under the door (t: 0 dry -> 1 puddle)
    E2_water: { desc: 'Low close-up: water slowly seeps in under the door across the laminate', frames: 40, make(W, t, A) {
      puddle(W, t);
      P.lightsInterior(W.scene, { leak: 10, amb: 0.42 });
      return camera(40, V(0.32, 0.16, 0.95), V(-0.05, 0.02, 0.05), A);
    } },
    // the glass from EP01 — now empty, standing in the puddle
    E2_glass_empty: { desc: 'The glass by the door is empty, standing in the puddle (EP01 hook framing)', make(W, t, A) {
      const g = P.makeGlass(); g.children[2].visible = false; g.children[3].visible = false; g.position.set(0.12, 0, 0.26); W.scene.add(g);
      puddle(W, 1);
      P.lightsInterior(W.scene, { leak: 9, amb: 0.45 });
      return camera(42, V(0.45, 0.24, 0.98), V(0.1, 0.17, 0.2), A);
    } },
    // entryway from behind Alex (EP01 S07 framing), empty glass + puddle; params: shadows (feet under the door)
    E2_entry_wide: { desc: 'Dark entryway, Alex from behind facing the door, empty glass and the puddle (shadows under the door when shadows)', make(W, t, A) {
      const a = alex(); a.position.set(0.42, 0, 1.45); a.rotation.y = Math.PI * 1.04; W.scene.add(a);
      const g = P.makeGlass(); g.children[2].visible = false; g.children[3].visible = false; g.position.set(0.12, 0, 0.26); W.scene.add(g);
      puddle(W, 1);
      if (W.p.shadows) for (const x of [-0.25, -0.12, 0.14, 0.24]) P.box(0.08, 0.014, 0.004, new THREE.MeshBasicMaterial({ color: '#0a0a0a' }), x, 0.006, 0.0035, W.scene);
      P.lightsInterior(W.scene, { leak: 10 });
      return camera(50, V(-0.3, 1.35, 3.75), V(0.08, 1.0, 0.0), A);
    } },
    // door from inside, low angle (EP01 S02 framing), empty glass + puddle
    E2_door_low: { desc: 'Front door from inside, low angle, empty glass in the puddle', make(W, t, A) {
      const g = P.makeGlass(); g.children[2].visible = false; g.children[3].visible = false; g.position.set(0.12, 0, 0.26); W.scene.add(g);
      puddle(W, 1);
      P.lightsInterior(W.scene, { leak: 8 });
      return camera(48, V(-0.35, 0.75, 1.45), V(0.0, 1.15, 0.0), A);
    } },
    // peephole: the landing is empty
    E2_peep_empty: { desc: 'Through the peephole: the landing is empty', peephole: true, make(W, t, A) {
      P.lightsStairwell(W.scene);
      return camera(100, PEEP, V(0.2, 1.4, -2.0), A);
    } },
    // peephole, down: a phone like Alex's lying on the tiles (screen composited)
    E2_peep_phone: { desc: 'Through the peephole, looking down: a phone identical to Alex\'s lies on the landing floor', peephole: true, phone: true, make(W, t, A) {
      const ph = P.makePhone(W.p.lit ? '#cfe0ff' : '#0c0f14'); ph.position.set(0.12, 0.006, -0.62); ph.rotation.set(-Math.PI / 2, 0, -0.4); W.scene.add(ph);
      W.screen = ph.getObjectByName('screen');
      P.lightsStairwell(W.scene);
      return camera(80, PEEP, V(0.1, 0.0, -0.7), A);
    } },
    // the photo on that phone: Alex at the peephole, taken from right behind him
    E2_photo_back: { desc: 'Photo: Alex at the peephole, shot from right behind his back inside the entryway', make(W, t, A) {
      const a = alex({ face: 'worried' }); a.position.set(0.0, 0.04, 0.27); a.rotation.y = Math.PI; W.scene.add(a);
      a.userData.arms[-1].rotation.x = -1.6; a.userData.arms[-1].rotation.z = -0.25;
      const g = P.makeGlass(); g.children[2].visible = false; g.children[3].visible = false; g.position.set(0.12, 0, 0.26); W.scene.add(g);
      puddle(W, 1);
      P.lightsInterior(W.scene, { amb: 0.45, leak: 9 });
      const fl = new THREE.PointLight('#f4f1ea', 1.8, 3.0, 1.6); fl.position.set(0.15, 1.7, 1.6); W.scene.add(fl); // phone-camera flash
      return camera(50, V(0.15, 1.7, 1.65), V(0.0, 1.3, 0.1), A);
    } },
    // photos for the choice screen (3:4)
    E2_photo_cop: { desc: 'Photo for the choice screen: the officer on the landing, flash-lit', size: [600, 800], make(W, t, A) {
      const c = P.makePerson('cop'); c.position.set(-0.2, 0, -1.15); c.rotation.y = 0.08; W.scene.add(c);
      P.lightsStairwell(W.scene, { amb: 0.7 });
      const fl = new THREE.PointLight('#ffffff', 1.4, 2.5, 1.5); fl.position.set(-0.12, 1.6, -0.15); W.scene.add(fl);
      return camera(42, V(-0.14, 1.58, -0.1), V(-0.19, 1.4, -1.15), A);
    } },
    E2_photo_dbl: { desc: 'Photo for the choice screen: Alex (the double) on the landing, flash-lit', size: [600, 800], make(W, t, A) {
      const d = alex(); d.position.set(0.25, 0, -1.2); d.rotation.y = -0.1; W.scene.add(d);
      P.lightsStairwell(W.scene, { amb: 0.7 });
      const fl = new THREE.PointLight('#ffffff', 1.4, 2.5, 1.5); fl.position.set(0.2, 1.6, -0.15); W.scene.add(fl);
      return camera(42, V(0.2, 1.58, -0.1), V(0.24, 1.4, -1.2), A);
    } },
    // the double stands right behind Alex at the peephole, in the dark (seen down the hallway)
    E2_double_behind: { desc: 'Down the hallway: Alex at the peephole; in the dark right behind him stands his double (bloody hand)', make(W, t, A) {
      const a = alex({ face: 'worried' }); a.position.set(0.0, 0.04, 0.27); a.rotation.y = Math.PI; W.scene.add(a);
      a.userData.arms[-1].rotation.x = -1.6; a.userData.arms[-1].rotation.z = -0.25;
      const g = P.makeGlass(); g.children[2].visible = false; g.children[3].visible = false; g.position.set(0.12, 0, 0.26); W.scene.add(g);
      puddle(W, 1);
      const d = alex({ bloodyRight: true }); d.position.set(-0.43, 0, 0.42); d.rotation.y = Math.PI / 2; W.scene.add(d);
      P.lightsInterior(W.scene, { amb: 0.4, moon: 0.5, warm: 0.5, leak: 10 });
      return camera(46, V(0.35, 1.45, 2.7), V(-0.02, 1.2, 0.3), A);
    } },
    // close: the double's face by Alex's ear (params: face for the lip shapes)
    E2_double_ear: { desc: 'Close-up over Alex\'s shoulder: the double\'s face right by his ear, whispering', make(W, t, A) {
      const a = alex({ face: 'worried' }); a.position.set(0.0, 0.04, 0.27); a.rotation.y = Math.PI; W.scene.add(a);
      const d = alex({ bloodyRight: true, face: W.p.face || 'neutral' }); d.position.set(-0.43, 0, 0.42); d.rotation.y = Math.PI / 2; W.scene.add(d);
      P.lightsInterior(W.scene, { amb: 0.3, moon: 0.35, warm: 0.6, leak: 9 });
      const l = new THREE.PointLight('#dff0d0', 1.1, 1.4, 1.6); l.position.set(-0.05, 1.25, 0.75); W.scene.add(l);
      return camera(36, V(0.9, 1.6, 0.98), V(-0.36, 1.55, 0.42), A);
    } },

    // ====================================================================== EP03 «КТО ЗА МОЕЙ СПИНОЙ?» (same world, same cast)
    // ANIM: Alex spins round from the peephole (t 0 -> 1); seen from the hallway at his eye level
    E3_turn: { desc: 'Alex whips round from the peephole to face the empty hallway', frames: 24, make(W, t, A) {
      aftermath(W);
      const e = t < 0.15 ? 0 : Math.min(1, (t - 0.15) / 0.55); const k = 1 - Math.pow(1 - e, 3);
      const a = alex({ face: k > 0.5 ? 'wide_worried' : 'worried' }); a.position.set(0.0, 0.0, 0.3 + 0.15 * k); a.rotation.y = Math.PI * (1 - k) + 0.12 * k; W.scene.add(a);
      a.userData.arms[-1].rotation.x = -1.6 * (1 - k) - 0.3 * k; a.userData.arms[1].rotation.x = -0.35 * k; a.userData.headPivot.rotation.y = 0.35 * Math.sin(k * Math.PI);
      P.lightsInterior(W.scene, { amb: 0.42, moon: 0.55, leak: 10 });
      const l = new THREE.PointLight('#dff0d0', 0.9, 1.8, 1.5); l.position.set(0.1, 0.35, 0.2); W.scene.add(l);
      return camera(46, V(0.38, 1.45, 2.35), V(0.0, 1.3, 0.35), A);
    } },
    // POV from the door: the hallway behind him is empty (mirror on the left, bedroom door on the right)
    E3_hall_empty: { desc: 'POV from the front door down the empty dark hallway', make(W, t, A) {
      aftermath(W); if (W.p.prints) prints(W, { a: TRAIL_A.length, p1: 1 });
      P.lightsInterior(W.scene, { amb: 0.38, moon: 0.5, warm: 1.3, leak: 10 });
      return camera(56, V(0.05, 1.55, 0.35), V(0.12, 0.72, 3.0), A);
    } },
    // ANIM: wet prints appear one by one on the laminate (low angle from beside Alex's feet)
    E3_prints_appear: { desc: 'Low angle: wet bare-foot prints appear one by one from the puddle at the door', frames: 40, make(W, t, A) {
      aftermath(W);
      const a = alex(); a.position.copy(AT_DOOR); a.rotation.y = 0.12; W.scene.add(a);
      const n = t * (TRAIL_A.length + 2.2); prints(W, { a: n, p1: Math.max(0, n - TRAIL_A.length) }); // one print every 1/8.2 of the shot
      P.lightsInterior(W.scene, { amb: 0.45, leak: 11 });
      const l = new THREE.PointLight('#cfe3ff', 0.7, 2.4, 1.4); l.position.set(-0.2, 0.9, 1.4); W.scene.add(l);
      return camera(50, V(0.55, 0.42, 1.75), V(-0.15, 0.0, 0.7), A);
    } },
    // high angle: the whole trail from the door to Alex's feet
    E3_prints_path: { desc: 'High angle: the trail leads from the puddle at the door round to a pair of prints facing Alex', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1 });
      const a = alex({ face: 'worried' }); a.position.copy(AT_DOOR); a.rotation.y = 0.12; W.scene.add(a);
      a.userData.headPivot.rotation.x = 0.45;
      P.lightsInterior(W.scene, { amb: 0.5, leak: 10 });
      const l = new THREE.PointLight('#cfe3ff', 0.8, 2.6, 1.4); l.position.set(0.0, 1.6, 1.2); W.scene.add(l);
      return camera(50, V(0.75, 2.45, 2.75), V(-0.08, 0.0, 0.7), A);
    } },
    // ANIM: Alex steps back (t 0..0.45) — then a new pair of prints steps forward (t 0.55..1)
    E3_step_back: { desc: 'Floor level: Alex\'s feet step back toward the door; the invisible pair of prints steps after him', frames: 40, make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: Math.max(0, Math.min(2, (t - 0.55) / 0.2)) });
      const k = Math.min(1, t / 0.45); const e = k * k * (3 - 2 * k);
      const a = alex(); a.position.set(0.0, 0, 0.45 - 0.13 * e); a.rotation.y = 0.12; W.scene.add(a);
      a.userData.legL.rotation.x = -0.35 * Math.sin(Math.PI * k);
      P.lightsInterior(W.scene, { amb: 0.45, leak: 11 });
      const l = new THREE.PointLight('#cfe3ff', 0.8, 2.0, 1.4); l.position.set(0.6, 0.6, 1.1); W.scene.add(l);
      return camera(58, V(-0.5, 0.55, 1.9), V(0.05, 0.2, 0.55), A);
    } },
    // side view: Alex pressed back against the door, the pair of prints in front of him, nobody above them
    E3_invisible: { desc: 'Side view: Alex against the door facing a pair of wet prints with nobody standing in them', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2 });
      const a = alex({ face: 'wide_worried' }); a.position.set(0.0, 0, 0.32); a.rotation.y = 0.0; W.scene.add(a);
      a.userData.arms[1].rotation.x = -0.25; a.userData.arms[-1].rotation.x = -0.25;
      P.lightsInterior(W.scene, { amb: 0.42, leak: 10, warm: 1.4 });
      const l = new THREE.PointLight('#dff0d0', 0.45, 1.8, 1.5); l.position.set(0.45, 0.9, 1.25); W.scene.add(l);
      return camera(52, V(0.92, 1.65, 2.25), V(-0.05, 0.55, 0.6), A);
    } },
    // POV phone at the door: the trail on the floor below the phone
    E3_pov_door: { desc: 'POV: phone in hand at the front door, wet prints on the floor beyond', phone: true, make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2 });
      P.lightsInterior(W.scene, { amb: 0.42, moon: 0.6, warm: 1.4 });
      const cam = camera(44, V(0.02, 1.52, 0.38), V(0.1, 0.5, 1.6), A);
      W.screen = povPhone(W.scene, cam, { rx: 0.08, ry: -0.06, rz: 0.04, z: -0.27 });
      return cam;
    } },
    // Alex in front of the hall mirror (hallway wide); params: dbl (second Alex in the reflection only)
    E3_mirror_wide: { desc: 'Hallway: Alex steps up to the mirror on the wall; real reflection (second Alex only in the mirror when dbl)', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2 });
      P.enableMirror(W);
      const a = alex({ face: 'worried' }); a.position.copy(AT_MIRROR); a.rotation.y = -Math.PI / 2 + 0.15; W.scene.add(a);
      if (W.p.dbl) { const d = P.mirrorOnly(alex({ bloodyRight: true })); d.position.copy(DBL_M); d.rotation.y = DBL_ROT; W.scene.add(d); }
      P.lightsInterior(W.scene, { amb: 0.45, moon: 0.6, warm: 1.6 });
      const l = new THREE.PointLight('#ffd7a8', 0.9, 2.4, 1.5); l.position.set(0.4, 1.9, 2.6); W.scene.add(l);
      return camera(58, V(0.85, 1.5, 3.9), V(-0.5, 1.25, 2.15), A);
    } },
    // over the shoulder into the mirror; params: dbl (layer-1 double behind him), pose ('shh' | 'point'), face
    E3_mirror: { desc: 'Over Alex\'s shoulder into the hall mirror; the reflection may hold a second Alex who exists only there', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2 });
      P.enableMirror(W);
      const a = alex({ face: 'worried' }); a.position.copy(W.p.ax !== undefined ? V(W.p.ax, 0, W.p.az) : AT_MIRROR); a.rotation.y = -Math.PI / 2 + 0.15; W.scene.add(a);
      if (W.p.dbl) {
        const d = alex({ bloodyRight: true, face: W.p.face || 'neutral' }); d.position.copy(W.p.dx !== undefined ? V(W.p.dx, 0, W.p.dz) : DBL_M); d.rotation.y = DBL_ROT; W.scene.add(d);
        const k = W.p.k ?? 1;
        // gestures use the arm on the double's +z side (image-left in the mirror), so Alex's reflection never covers it
        const aimLocal = (arm, worldDir, k) => {
          d.updateMatrixWorld(true);
          const dl = worldDir.clone().normalize().applyQuaternion(d.quaternion.clone().invert());
          const q = new THREE.Quaternion().setFromUnitVectors(V(0, -1, 0), dl); arm.quaternion.identity().slerp(q, k);
        };
        if (W.p.pose === 'shh') { // index finger to the lips
          const arm = d.userData.arms[1]; d.updateMatrixWorld(true);
          const sh = arm.getWorldPosition(V(0, 0, 0)); const head = d.userData.headPivot.getWorldPosition(V(0, 0, 0));
          const mouth = head.clone().add(V(-0.26, 0.05, 0.07));          // in front of the face (he faces -x)
          aimLocal(arm, mouth.sub(sh), k);
          if (k > 0.85) P.box(0.032, 0.11, 0.032, P.M(P.PAL.skinAlex), 0.0, -0.66, 0.0, arm);
        }
        if (W.p.pose === 'point') { // across his chest toward the front door (-z), head turned to it
          const arm = d.userData.arms[1];
          const pd = W.p.pdir || [-0.6, -0.3, -0.75]; aimLocal(arm, V(pd[0], pd[1], pd[2]), k);
          d.userData.headPivot.rotation.y = (W.p.hy ?? -0.3) * k;
          if (k > 0.85) P.box(0.03, 0.11, 0.03, P.M(P.PAL.skinAlex), 0.0, -0.66, 0.0, arm);
        }
        P.mirrorOnly(d);
      }
      P.lightsInterior(W.scene, { amb: 0.42, moon: 0.55, warm: 1.5 });
      const l = new THREE.PointLight('#ffd7a8', 1.0, 2.4, 1.5); l.position.set(0.3, 1.9, 2.7); W.scene.add(l);
      const f = new THREE.PointLight('#cfe0ff', 0.5, 1.4, 1.5); f.position.set(-0.4, 1.55, 1.75); W.scene.add(f);
      const g2 = new THREE.PointLight('#ffd7a8', 0.6, 1.4, 1.5); g2.position.set(0.0, 1.95, 2.25); W.scene.add(g2);
      const g3 = new THREE.PointLight('#dfe6ff', 0.5, 1.1, 1.6); g3.position.set(-0.6, 1.95, 2.05); W.scene.add(g3);
      if (W.p.cam) return camera(W.p.cam[0], V(W.p.cam[1], W.p.cam[2], W.p.cam[3]), V(W.p.cam[4], W.p.cam[5], W.p.cam[6]), A);
      const fv = W.p.fov ?? 44, tg = fv < 40 ? V(-0.71, 1.52, 2.42) : V(-0.71, 1.45, 2.3);
      return camera(fv, V(0.9, 1.68, 2.9), tg, A);
    } },
    // Alex turns from the mirror and looks behind him (camera where the double stood) — nobody
    E3_look_back: { desc: 'Alex at the mirror whips his head round toward the camera — the space behind him is empty', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2 });
      P.enableMirror(W);
      const a = alex({ face: 'wide_worried' }); a.position.copy(AT_MIRROR); a.rotation.y = 0.1; W.scene.add(a);
      a.userData.headPivot.rotation.y = 0.5; a.userData.arms[1].rotation.x = -0.3;
      P.lightsInterior(W.scene, { amb: 0.45, moon: 0.55, warm: 1.4 });
      const l = new THREE.PointLight('#ffd7a8', 1.1, 2.0, 1.5); l.position.set(0.2, 1.8, 2.4); W.scene.add(l);
      return camera(50, V(0.3, 1.6, 2.95), V(-0.28, 1.4, 2.1), A);
    } },
    // POV from the mirror: the empty hallway toward the front door — a fresh pair of prints where the double stood
    E3_behind_empty: { desc: 'POV from the mirror: empty hallway to the front door, a fresh pair of wet prints right behind him', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2, m: W.p.m ? 1 : 0 });
      P.lightsInterior(W.scene, { amb: 0.42, moon: 0.55, leak: 10 });
      const l = new THREE.PointLight('#cfe3ff', 0.6, 2.0, 1.4); l.position.set(0.3, 1.2, 1.9); W.scene.add(l);
      return camera(60, V(-0.3, 1.55, 2.1), V(0.3, 0.3, 2.95), A);
    } },
    // the front door from inside: shadows of feet under it (the officer outside)
    E3_door_outside: { desc: 'Front door from inside, wet prints and puddle, shadows of feet in the light under the door', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2 });
      for (const x of [-0.14, 0.02]) P.box(0.09, 0.014, 0.004, new THREE.MeshBasicMaterial({ color: '#0a0a0a' }), x, 0.006, 0.0035, W.scene);
      P.lightsInterior(W.scene, { leak: 9, amb: 0.42 });
      return camera(46, V(0.3, 0.85, 2.2), V(0.0, 0.9, 0.0), A);
    } },
    // lock close-up: thumb-turn locked (EP01 S20 framing, t = 0)
    E3_lock_closed: { desc: 'Lock close-up: the thumb-turn is in the locked position', make(W, t, A) {
      P.lightsInterior(W.scene, { amb: 0.4, leak: 10 });
      const l = new THREE.PointLight('#ffcf8a', 0.9, 1.0); l.position.set(-0.2, 1.3, 0.5); W.scene.add(l);
      return camera(32, V(-0.28, 1.24, 0.42), V(-0.37, 1.2, 0.03), A);
    } },
    // the trail now leads from the mirror into the bedroom doorway; params: leak (phone glow under the door)
    E3_prints_bedroom: { desc: 'The wet prints now lead away from the mirror to the closed bedroom door', make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2, m: 1, b: TRAIL_B.length });
      bedLeak(W, '#9fb8ff', W.p.leak ? 1 : 0.15);
      P.lightsInterior(W.scene, { amb: 0.42, moon: 0.55, warm: 1.5 });
      const l = new THREE.PointLight('#cfe3ff', 0.7, 2.2, 1.4); l.position.set(0.3, 1.0, 2.0); W.scene.add(l);
      return camera(50, V(-0.45, 1.25, 1.35), V(0.95, 0.35, 2.85), A);
    } },
    // ANIM: slow dolly toward the bedroom door (Alex's POV)
    E3_approach: { desc: 'POV: slow walk up to the closed bedroom door, prints leading under it', frames: 40, make(W, t, A) {
      aftermath(W); prints(W, { a: TRAIL_A.length, p1: 1, p2: 2, m: 1, b: TRAIL_B.length });
      bedLeak(W, '#9fb8ff', 0.15 + 0.85 * Math.max(0, (t - 0.75) / 0.25));
      P.lightsInterior(W.scene, { amb: 0.4, moon: 0.5, warm: 1.3 });
      const e = t * t * (3 - 2 * t), bob = 0.012 * Math.sin(t * Math.PI * 6);
      return camera(54, V(-0.25 + 0.65 * e, 1.55 + bob, 2.05 + 0.75 * e), V(1.05, 1.0 - 0.15 * e, 2.95), A);
    } },
    // close: the bedroom door, the phone glowing on the other side (light under the door pulses)
    E3_beddoor_close: { desc: 'Close on the bedroom door: cold phone light pulses in the gap underneath', make(W, t, A) {
      prints(W, { b: TRAIL_B.length });
      bedLeak(W, '#a9c2ff', W.p.leak ?? 1);
      P.lightsInterior(W.scene, { amb: 0.35, moon: 0.45, warm: 1.0 });
      const lk = new THREE.SpotLight('#a9c2ff', 0.9 * (W.p.leak ?? 1), 1.4, 1.0, 0.9, 2); lk.position.set(1.04, 0.01, 2.9); lk.target.position.set(0.3, 0.0, 2.9); W.scene.add(lk, lk.target);
      return camera(48, V(0.35, 0.42, 2.55), V(1.05, 0.25, 2.92), A);
    } },
    // POV with Alex's own phone, in front of the bedroom door; params: dark screen until it lights
    E3_pov_beddoor: { desc: 'POV: Alex\'s own phone in his hand in front of the bedroom door', phone: true, make(W, t, A) {
      prints(W, { b: TRAIL_B.length }); bedLeak(W, '#a9c2ff', 0.9);
      P.lightsInterior(W.scene, { amb: 0.38, moon: 0.5, warm: 1.0 });
      const cam = camera(42, V(0.45, 1.5, 2.85), V(1.05, 1.0, 2.95), A);
      W.screen = povPhone(W.scene, cam, { rx: 0.1, ry: 0.06, rz: -0.05, z: -0.27 });
      return cam;
    } },
    // Alex's face lit by the phone, bedroom door beside him
    E3_alex_face_bed: { desc: 'Close-up: Alex\'s face in the phone light, the bedroom door at his shoulder', make(W, t, A) {
      prints(W, { b: TRAIL_B.length }); bedLeak(W, '#a9c2ff', 0.9);
      const a = alexWithPhone(); a.position.copy(AT_BEDDOOR); a.rotation.y = 1.95; W.scene.add(a);
      P.lightsInterior(W.scene, { amb: 0.3, moon: 0.4, warm: 1.0 });
      const pl = new THREE.PointLight('#9cc0ff', 0.6, 1.2, 1.8); pl.position.set(0.95, 1.35, 2.75); W.scene.add(pl);
      return camera(40, V(1.0, 1.58, 1.9), V(0.55, 1.48, 2.78), A);
    } },
    // ANIM: the bedroom door creaks open by itself (over Alex's shoulder; t 0 -> 1 = 0 -> 0.62 rad)
    E3_beddoor_open: { desc: 'POV: the bedroom door slowly swings open by itself onto darkness', frames: 40, make(W, t, A) {
      prints(W, { b: TRAIL_B.length });
      const k = [[0, 0], [0.12, 0.04], [0.22, 0.03], [0.6, 0.5], [1, 1.05]];
      let r = 0; for (let i = 1; i < k.length; i++) if (t <= k[i][0]) { const u = (t - k[i - 1][0]) / (k[i][0] - k[i - 1][0]); r = k[i - 1][1] + (k[i][1] - k[i - 1][1]) * u * u * (3 - 2 * u); break; }
      bedDoor(W, r); bedLeak(W, '#a9c2ff', 0.9);
      // POV: no Alex in frame, the door opens by itself
      tiedMan(W); floorPhone(W, true, 0.8); bedroomLights(W, { moon: 1.2 });
      P.lightsInterior(W.scene, { amb: 0.32, moon: 0.4, warm: 0.9 });
      return camera(52, V(0.0, 1.5, 2.72), V(1.2, 1.0, 2.95), A);
    } },
    // through the doorway: a man sitting in the dark (silhouette against the window)
    E3_room_dark: { desc: 'Through the open doorway: a man sits on a chair in the dark, backlit by the moonlit window', make(W, t, A) {
      bedDoor(W, 1.25); tiedMan(W, { face: 'tape_worried', tilt: 0.25 }); floorPhone(W, true, 0.35);
      bedroomLights(W, { moon: 1.4, amb: 0.18 });
      return camera(40, V(0.55, 1.5, 2.95), V(2.4, 0.95, 2.95), A);
    } },
    // medium: tied to the chair, mouth taped (params: face, head)
    E3_tied: { desc: 'Medium shot: the man is tied to the chair with rope, mouth taped over', make(W, t, A) {
      bedDoor(W, 1.25); tiedMan(W, { face: W.p.face || 'tape_worried', head: W.p.head }); floorPhone(W, true, 0.9);
      bedroomLights(W, { moon: 1.3, amb: 0.3 });
      const f = new THREE.PointLight('#dfe8ff', 0.7, 2.2, 1.5); f.position.set(1.4, 1.6, 2.9); W.scene.add(f);
      return camera(40, V(0.85, 1.3, 2.78), V(2.4, 0.78, 2.92), A);
    } },
    // close-up of the tied man's face (Alex's face) — params: face, head (shake), cam ('close' | 'eyes')
    E3_tied_face: { desc: 'Close-up: the tied man has Alex\'s face — tape over the mouth, eyes pleading', make(W, t, A) {
      bedDoor(W, 1.25); tiedMan(W, { face: W.p.face || 'tape_worried', head: W.p.head ?? 0 }); floorPhone(W, true, 1.0);
      bedroomLights(W, { moon: 1.2, amb: 0.3 });
      const f = new THREE.PointLight('#dfe8ff', 0.5, 1.6, 1.5); f.position.set(1.7, 1.6, 2.6); W.scene.add(f);
      const up = new THREE.PointLight('#a8c4ff', 0.9, 1.4, 1.6); up.position.set(1.95, 0.6, 3.0); W.scene.add(up);
      const eyes = W.p.cam === 'eyes';
      return camera(eyes ? 21 : 26, V(1.3, 1.3, 2.92), V(2.4, eyes ? 1.26 : 1.2, 2.92), A);
    } },
    // from behind the chair: the tied man looks at the phone in Alex's hand, Alex in the doorway
    E3_from_chair: { desc: 'From behind the chair: the tied man\'s head turns down toward the glowing phone in Alex\'s hand in the doorway', make(W, t, A) {
      bedDoor(W, 1.25); tiedMan(W, { face: 'tape_worried_down', tilt: 0.3 }); floorPhone(W, false);
      const a = alexWithPhone(); a.position.set(1.0, 0, 2.9); a.rotation.y = Math.PI / 2; W.scene.add(a);
      const pl = new THREE.PointLight('#9cc0ff', 1.0, 1.6, 1.7); pl.position.set(1.32, 1.25, 2.95); W.scene.add(pl);
      bedroomLights(W, { moon: 1.3, amb: 0.25 });
      P.lightsInterior(W.scene, { amb: 0.3, moon: 0.4, warm: 0.9 });
      return camera(42, V(3.15, 1.35, 3.25), V(1.2, 1.1, 2.88), A);
    } },
    // POV in the doorway: Alex's phone, the tied man behind it
    E3_pov_room: { desc: 'POV in the bedroom doorway: phone in hand, the tied man on the chair beyond', phone: true, make(W, t, A) {
      bedDoor(W, 1.25); tiedMan(W, { face: 'tape_worried' }); floorPhone(W, false);
      bedroomLights(W, { moon: 1.3, amb: 0.25 });
      P.lightsInterior(W.scene, { amb: 0.3, moon: 0.4, warm: 0.8 });
      const cam = camera(42, V(1.0, 1.5, 2.92), V(2.4, 0.95, 2.92), A);
      W.screen = W.p.center ? povPhone(W.scene, cam, { rx: 0.08, ry: -0.04, rz: 0.05, z: -0.27, glow: 1.3 }) : povPhone(W.scene, cam, { rx: 0.08, ry: 0.04, rz: 0.06, z: -0.26, y: -0.075, x: 0.03, glow: 1.3 });
      return cam;
    } },
    // ====================================================================== EP04 «НЕ ТОТ АЛЕКС» (same world, same cast; starts on EP03's last frame)
    // ANIM: POV — Alex walks from the doorway up to the chair
    E4_approach: { desc: 'POV: Alex walks from the bedroom doorway up to the tied double', frames: 30, make(W, t, A) {
      bed4(W); tiedMan4(W, { face: 'tape_worried_tears', tape: 1 });
      const e = t * t * (3 - 2 * t), bob = 0.01 * Math.sin(t * Math.PI * 5);
      const cam = camera(46, V(1.0 + 0.62 * e, 1.5 - 0.05 * e + bob, 2.92), V(2.4, 1.05 + 0.1 * e, 2.92), A); camGlow(W, cam, 0.8);
      return cam;
    } },
    // MACRO: the scars. Both forearms are built in camera space so the framing is exact. k (param) slides Alex's arm in.
    E4_scars: { desc: 'Macro behind the chair: the double\'s bound wrist with a scar; Alex holds his own wrist beside it — the same scar', make(W, t, A) {
      bed4(W, { moon: 1.1 }); tiedMan4(W, { face: 'worried_redmark', tape: 0, hideArms: true });
      const cam = camera(40, V(3.4, 0.72, 2.95), V(2.6, 0.62, 2.92), A); W.scene.add(cam);
      const d = P.makeForearm({ bound: true }); d.position.set(-0.072, 0.36, -0.75); d.rotation.z = 0.03; cam.add(d);
      const k = W.p.k ?? 1, e = 1 - Math.pow(1 - k, 3);
      if (k > 0) { const a = P.makeForearm({}); a.position.set(0.075 + 0.2 * (1 - e), -0.32 - 0.35 * (1 - e), -0.75); a.rotation.z = Math.PI - 0.03; cam.add(a); }
      const l = new THREE.PointLight('#b9d0ff', 0.55, 1.4, 1.6); l.position.set(0.12, 0.05, 0.05); cam.add(l);
      const l2 = new THREE.PointLight('#ffe2c4', 0.18, 1.0, 1.6); l2.position.set(-0.2, 0.2, -0.2); cam.add(l2);
      return cam;
    } },
    // ANIM: Alex's hand rips the tape off the double's mouth (close-up, EP03 E3_tied_face framing)
    E4_tape_off: { desc: 'Close-up: Alex\'s hand rips the tape off the double\'s mouth', frames: 16, make(W, t, A) {
      bed4(W, { moon: 1.2, amb: 0.3 });
      const peel = Math.max(0, Math.min(1, (t - 0.3) / 0.35));
      const m = tiedMan4(W, { face: peel > 0.15 ? 'wide_worried_redmark_tears_open' : 'tape_worried_tears', tape: peel >= 1 ? 0 : (peel > 0 ? peel : 1), head: -0.12 * peel });
      W.scene.updateMatrixWorld(true);
      // where the hand is: free end of the tape until it comes off, then away to the right carrying it
      let hand;
      if (m.userData.strip) { hand = m.userData.strip.localToWorld(V(0.11, 0, 0.0)); }
      else { hand = V(1.95, 1.2, 3.25); }
      const reach = Math.min(1, t / 0.3), ease = 1 - Math.pow(1 - reach, 3);
      const start = V(2.05, 0.85, 3.1); const h = t < 0.3 ? start.clone().lerp(hand, ease) : hand;
      if (t >= 0.65) { h.copy(hand.clone().lerp(V(1.95, 0.98, 3.2), Math.min(1, (t - 0.65) / 0.35))); const s = P.box(0.22, 0.085, 0.014, P.M('#b4b2a8', { roughness: 0.6 }), h.x - 0.03, h.y + 0.07, h.z, W.scene); s.rotation.set(0.3, 1.3, 0.5); }
      W.scene.add(aimArm(arm(), V(2.05, 0.45, 3.15), h));
      const f = new THREE.PointLight('#dfe8ff', 0.5, 1.6, 1.5); f.position.set(1.7, 1.6, 2.6); W.scene.add(f);
      const up = new THREE.PointLight('#a8c4ff', 0.7, 1.4, 1.6); up.position.set(1.6, 0.9, 2.9); W.scene.add(up);
      return camera(28, V(1.3, 1.3, 2.92), V(2.4, 1.18, 2.92), A);
    } },
    // close-up of the untaped double (lip-sync stills by face token); params: face, head, cam ('close' | 'eyes' | 'wide')
    E4_dbl: { desc: 'Close-up: the double, tape gone, red skin round the mouth; lit by Alex\'s phone', make(W, t, A) {
      bed4(W, { moon: 1.2, amb: 0.3 }); tiedMan4(W, { face: W.p.face || 'worried_redmark', tape: 0, head: W.p.head ?? 0, tilt: W.p.tilt });
      const f = new THREE.PointLight('#dfe8ff', 0.5, 1.6, 1.5); f.position.set(1.7, 1.6, 2.6); W.scene.add(f);
      const up = new THREE.PointLight('#a8c4ff', 0.75, 1.4, 1.6); up.position.set(1.7, 0.95, 2.85); W.scene.add(up);
      const c = W.p.cam || 'close';
      if (c === 'eyes') return camera(20, V(1.3, 1.3, 2.92), V(2.4, 1.26, 2.92), A);
      if (c === 'wide') return camera(34, V(1.25, 1.35, 3.08), V(2.4, 1.05, 2.9), A);
      return camera(26, V(1.3, 1.3, 2.92), V(2.4, 1.2, 2.92), A);
    } },
    // ANIM: Alex steps back from the chair (over the double's shoulder)
    E4_step_back: { desc: 'Over the double\'s shoulder: Alex steps back from the chair, phone glowing in his hand', frames: 20, make(W, t, A) {
      bed4(W); tiedMan4(W, { face: 'worried_redmark_tears', tape: 0, head: 0.1 });
      const e = t * t * (3 - 2 * t);
      const a = alexWithPhone({ face: 'wide_worried' }); a.position.set(ALEX4.x - 0.35 * e, 0, ALEX4.z + 0.04 * e); a.rotation.y = Math.PI / 2; W.scene.add(a);
      a.userData.legL.rotation.x = -0.35 * Math.sin(Math.PI * e);
      const pl = new THREE.PointLight('#9cc0ff', 0.7, 1.4, 1.7); pl.position.set(a.position.x + 0.3, 1.25, 2.92); W.scene.add(pl);
      return camera(44, V(2.9, 1.5, 3.45), V(1.55, 1.22, 2.9), A);
    } },
    // Alex's face in the phone light (lip-sync stills); background: the dark doorway
    E4_alex: { desc: 'Close-up: Alex\'s face lit by his phone, the dark bedroom doorway behind him', make(W, t, A) {
      bed4(W, { moon: 0.9 }); const a = alexWithPhone({ face: W.p.face || 'worried' }); a.position.copy(W.p.near ? V(1.98, 0, 2.92) : ALEX4); a.rotation.y = Math.PI / 2; W.scene.add(a);
      if (W.p.near) { a.rotation.z = -0.12; }
      const pl = new THREE.PointLight('#9cc0ff', 0.12, 1.0, 1.8); pl.position.set(a.position.x + 0.32, 1.25, 2.9); W.scene.add(pl);
      const rim = new THREE.PointLight('#86a2dc', 0.45, 1.6, 1.6); rim.position.set(a.position.x - 0.4, 1.8, 3.3); W.scene.add(rim);
      return camera(52, V(a.position.x + 0.82, 1.47, 2.48), V(a.position.x, 1.46, 2.93), A);
    } },
    // two-shot from the doorway corner: Alex, phone in hand, in front of the double
    E4_two_shot: { desc: 'Two-shot from the doorway corner: Alex with his phone in front of the tied double', make(W, t, A) {
      bed4(W); tiedMan4(W, { face: 'worried_redmark_tears', tape: 0 });
      const a = alexWithPhone(); a.position.copy(ALEX4); a.rotation.y = Math.PI / 2 + 0.1; W.scene.add(a);
      const pl = new THREE.PointLight('#9cc0ff', 0.8, 1.6, 1.7); pl.position.set(2.05, 1.25, 2.95); W.scene.add(pl);
      return camera(46, V(1.12, 1.62, 3.28), V(2.2, 1.0, 2.88), A);
    } },
    // POV: Alex's phone, the untaped double beyond it
    E4_pov_chair: { desc: 'POV in front of the chair: phone in hand, the double beyond it', phone: true, make(W, t, A) {
      bed4(W); tiedMan4(W, { face: W.p.face || 'worried_redmark_tears', tape: 0 });
      const cam = camera(54, V(1.6, 1.52, 2.92), V(2.4, 1.0, 2.92), A);
      W.screen = W.p.center ? povPhone(W.scene, cam, { rx: 0.08, ry: -0.04, rz: 0.05, z: -0.27, glow: 1.3 }) : povPhone(W.scene, cam, { rx: 0.08, ry: 0.04, rz: 0.06, z: -0.26, y: -0.075, x: 0.03, glow: 1.3 });
      return cam;
    } },
    // ANIM: the phone falls to the floor and hits it (floor-level camera; landing at t ≈ 0.72)
    E4_phone_throw: { desc: 'Floor level: Alex\'s phone falls and smacks onto the bedroom floor', frames: 16, make(W, t, A) {
      bed4(W); tiedMan4(W, { face: 'wide_worried_redmark_tears', tape: 0 });
      const a = alex({ face: 'wide_worried' }); a.position.copy(ALEX4); a.rotation.y = Math.PI / 2; W.scene.add(a);
      const L = V(2.0, 0.006, 3.42); const tl = 0.72;
      const ph = P.makePhone('#cfe0ff'); W.scene.add(ph);
      if (t < tl) { const u = t / tl; ph.position.set(L.x - 0.15 * (1 - u), 0.006 + 1.1 * (1 - u * u), L.z - 0.2 * (1 - u)); ph.rotation.set(-Math.PI / 2 + 2.6 * (1 - u), 0.3, 0.3 + 1.2 * (1 - u)); }
      else { const u = (t - tl) / (1 - tl); ph.position.set(L.x, 0.006 + 0.03 * Math.sin(Math.PI * Math.min(1, u * 2)) * (u < 0.5 ? 1 : 0), L.z); ph.rotation.set(-Math.PI / 2, 0, 0.3); }
      const pl = new THREE.PointLight('#a8c4ff', 0.5, 1.2, 1.6); pl.position.copy(ph.position).add(V(0, 0.15, 0)); W.scene.add(pl);
      return camera(44, V(1.35, 0.22, 3.75), V(2.05, 0.12, 3.25), A);
    } },
    // top-down macro on the phone on the floor (screen quad -> UI with the crack drawn in code)
    E4_phone_floor: { desc: 'Top-down macro: the phone on the floor, its screen cracked, still lit', phone: true, make(W, t, A) {
      bed4(W, { floorPhone: false });
      const ph = P.makePhone('#141b26'); ph.position.set(2.0, 0.006, 3.42); ph.rotation.set(-Math.PI / 2, 0, 0.3); W.scene.add(ph); W.screen = ph.getObjectByName('screen');
      const pl = new THREE.PointLight('#a8c4ff', 0.35, 0.8, 1.6); pl.position.set(2.0, 0.12, 3.42); W.scene.add(pl);
      const c = new THREE.PerspectiveCamera(30, A, 0.01, 60); c.position.set(2.02, 0.5, 3.47); c.up.set(Math.sin(0.3), 0, -Math.cos(0.3)); c.lookAt(V(2.0, 0.0, 3.42)); return c;
    } },
    // POV from the bedroom through the doorway to the hall mirror (quad meta -> red text drawn in code on the glass)
    E4_mirror_far: { desc: 'POV from the bedroom through the open doorway: the hall mirror across the hallway', make(W, t, A) {
      bed4(W, { warm: 1.2 }); const m = P.enableMirror(W); W.quad = { obj: m, hw: 0.31, hh: 0.5 };
      const l = new THREE.PointLight('#ffd7a8', 0.7, 2.4, 1.5); l.position.set(0.3, 1.9, 2.7); W.scene.add(l);
      return camera(40, V(1.8, 1.58, 2.98), V(-0.71, 1.36, 2.36), A);
    } },
    // close on the hall mirror from the hallway (real reflection; text in post)
    E4_mirror_close: { desc: 'Close on the hall mirror: its glass will carry the red message', make(W, t, A) {
      bed4(W, { warm: 1.2 }); const m = P.enableMirror(W); W.quad = { obj: m, hw: 0.31, hh: 0.5 };
      const l = new THREE.PointLight('#ffd7a8', 0.8, 2.4, 1.5); l.position.set(0.3, 1.9, 2.7); W.scene.add(l);
      const g3 = new THREE.PointLight('#ff6060', 0.35, 1.2, 1.6); g3.position.set(-0.45, 1.4, 2.3); W.scene.add(g3);   // red spill from the text
      return camera(40, V(1.0, 1.46, 2.95), V(-0.71, 1.38, 2.3), A);
    } },
    // ANIM: Alex leans in to the double (side view from the bed)
    E4_lean: { desc: 'Side view: Alex leans in close to the tied double', frames: 16, make(W, t, A) {
      bed4(W); tiedMan4(W, { face: 'worried_redmark_pale', tape: 0, head: 0.0 });
      const e = t * t * (3 - 2 * t);
      const piv = new THREE.Group(); piv.position.set(ALEX4.x + 0.12 * e, 0, ALEX4.z); piv.rotation.z = -0.28 * e; W.scene.add(piv);
      const a = alexWithPhone(); a.rotation.y = Math.PI / 2; piv.add(a);
      const pl = new THREE.PointLight('#9cc0ff', 0.7, 1.4, 1.7); pl.position.set(2.1, 1.2, 2.95); W.scene.add(pl);
      return camera(44, V(2.9, 1.5, 3.45), V(1.75, 1.3, 2.9), A);
    } },
    // ANIM: from the chair toward the doorway — light from the open front door, a shadow crosses the hall (footsteps)
    E4_doorway_steps: { desc: 'From the chair toward the dark doorway: stairwell light down the hall, a shadow moves across it', frames: 24, make(W, t, A) {
      bed4(W, { moon: 1.0 }); frontDoorOpen(W);
      const c = maskedCop(); c.position.set(0.22, 0, 0.75 + 0.75 * t); c.rotation.y = 0; W.scene.add(c);
      const s = Math.sin(t * Math.PI * 4); c.userData.legL.rotation.x = 0.35 * s; c.userData.legR.rotation.x = -0.35 * s;
      const sp = new THREE.SpotLight('#dff0d0', W.p.spk ?? 6, 8, 0.9, 0.4, 1.0); sp.position.set(0.9, 1.35, 0.35); sp.target.position.set(-0.75, 1.0, 2.3); sp.castShadow = true; sp.shadow.mapSize.set(1024, 1024); sp.shadow.bias = -0.002; W.scene.add(sp, sp.target);
      return camera(62, V(2.3, 1.25, 3.4), V(1.0, 0.95, 2.85), A);
    } },
    // ANIM: low in the hall — black boots walk up from the open front door (only legs in frame)
    E4_boots: { desc: 'Low in the hallway: heavy black boots walk in from the open front door', frames: 24, make(W, t, A) {
      bed4(W); frontDoorOpen(W, 1.4);
      const c = maskedCop(); c.position.set(-0.08, 0, 0.7 + 0.32 * t); W.scene.add(c);
      const s = Math.sin(t * Math.PI * 3); c.userData.legL.rotation.x = 0.4 * s; c.userData.legR.rotation.x = -0.4 * s; c.position.y = 0.012 * Math.abs(s);
      W.scene.add(new THREE.PointLight('#dff0d0', 0.6, 2.5, 1.5).translateX(-0.1).translateY(0.5).translateZ(0.3));
      return camera(34, V(0.5, 0.26, 3.2), V(-0.08, 0.3, 0.9), A);
    } },
    // MACRO: the double's bound hand grabs Alex's wrist (camera space, like E4_scars); k = grab progress
    E4_grab: { desc: 'Macro behind the chair: the double\'s bound hand clamps round Alex\'s wrist', make(W, t, A) {
      bed4(W, { moon: 1.1 }); tiedMan4(W, { face: 'worried_redmark_pale', tape: 0, hideArms: true });
      const cam = camera(40, V(3.4, 0.72, 2.95), V(2.6, 0.62, 2.92), A); W.scene.add(cam);
      const k = W.p.k ?? 1, e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      const a = P.makeForearm({}); a.position.set(0.48, -0.16, -0.86); a.rotation.z = -Math.PI / 2 - 0.08; cam.add(a);   // Alex's arm across the frame
      const d = P.makeForearm({ bound: true, grip: 0.1 + 0.9 * e }); d.position.set(-0.03, 0.56 - 0.1 * e, -0.8); d.rotation.z = 0.05; cam.add(d);
      const l = new THREE.PointLight('#b9d0ff', 0.55, 1.4, 1.6); l.position.set(0.12, 0.05, 0.05); cam.add(l);
      const l2 = new THREE.PointLight('#ffe2c4', 0.18, 1.0, 1.6); l2.position.set(-0.2, 0.2, -0.2); cam.add(l2);
      return cam;
    } },
    // a door numbered 204 — a flash insert (memory-like), a corridor nobody has seen before; nothing else is shown
    E4_room204: { desc: 'Flash insert: a closed door with the number plate 204 under a flickering tube', ref: true, make(W, t, A) {
      const sc = W.scene; sc.background = new THREE.Color('#050607'); sc.fog = new THREE.Fog('#050607', 1.2, 4.0);
      const hw = P.canvasTex(64, 256, (g, w, h) => { g.fillStyle = '#c9c7b4'; g.fillRect(0, 0, w, h); g.fillStyle = '#5e7b72'; g.fillRect(0, h * 0.45, w, h); g.fillStyle = '#3d564f'; g.fillRect(0, h * 0.45, w, 5); }, { repeat: [4, 1] });
      const wall = new THREE.Mesh(new THREE.PlaneGeometry(5, 2.8), P.MT(hw)); wall.position.set(0, 1.4, 0); wall.receiveShadow = true; sc.add(wall);
      const fl = new THREE.Mesh(new THREE.PlaneGeometry(5, 3), P.M('#4a4f4a')); fl.rotation.x = -Math.PI / 2; fl.position.set(0, 0, 1.5); sc.add(fl);
      P.box(0.98, 2.1, 0.05, P.M('#56636b', { roughness: 0.6, metalness: 0.3 }), 0, 1.05, 0.03, sc);              // painted metal door
      P.box(1.08, 2.16, 0.03, P.M('#3c464c'), 0, 1.08, 0.012, sc);
      P.box(0.12, 0.03, 0.05, P.M('#9aa0a6', { metalness: 0.7, roughness: 0.3 }), -0.36, 1.0, 0.08, sc);
      const plate = P.box(0.26, 0.13, 0.012, [P.M('#1d2a33'), P.M('#1d2a33'), P.M('#1d2a33'), P.M('#1d2a33'), P.MT(P.plateTex('204')), P.M('#1d2a33')], 0, 1.62, 0.062, sc);
      const tube = P.box(0.8, 0.04, 0.06, new THREE.MeshBasicMaterial({ color: '#e9f4ff' }), 0, 2.55, 0.6, sc); tube.castShadow = false;
      const tl = new THREE.PointLight('#dfeeff', 3.2, 4, 1.4); tl.position.set(0, 2.45, 0.7); tl.castShadow = true; sc.add(tl);
      sc.add(new THREE.HemisphereLight('#7f8f9a', '#101010', 0.35));
      return W.p.wide ? camera(46, V(0.35, 1.35, 1.85), V(0.0, 1.35, 0.0), A) : camera(30, V(0.18, 1.5, 0.95), V(0.0, 1.58, 0.05), A);
    } },
    // ANIM: Alex turns from the double toward the doorway (low angle, doorway out of frame)
    E4_alex_turn: { desc: 'Low angle: Alex turns away from the double to look behind him', frames: 16, make(W, t, A) {
      bed4(W, { moon: 1.1 });
      const e = t < 0.1 ? 0 : 1 - Math.pow(1 - Math.min(1, (t - 0.1) / 0.6), 3);
      const a = alex({ face: e > 0.4 ? 'wide_worried' : 'worried' }); a.position.copy(ALEX4); a.rotation.y = Math.PI / 2 - 1.25 * e; W.scene.add(a);
      a.userData.headPivot.rotation.y = -0.55 * e; a.userData.arms[1].rotation.x = -0.15; a.userData.arms[-1].rotation.x = -0.2;
      const pl = new THREE.PointLight('#9cc0ff', 0.35, 1.3, 1.7); pl.position.set(2.15, 1.3, 2.75); W.scene.add(pl);
      const rim = new THREE.PointLight('#86a2dc', 0.4, 1.6, 1.6); rim.position.set(1.5, 1.9, 3.3); W.scene.add(rim);
      return camera(36, V(2.75, 1.5, 2.45), V(1.78, 1.45, 2.95), A);
    } },
    // the masked officer in the bedroom doorway, backlit by the stairwell light from the open front door
    E4_cop_doorway: { desc: 'From inside the bedroom: the officer stands in the doorway, backlit, face black', make(W, t, A) {
      bed4(W, { moon: W.p.moon ?? 0.8 }); frontDoorOpen(W, 1.3);
      const c = maskedCop(); c.position.set(0.98, 0, 2.9); c.rotation.y = Math.PI / 2; W.scene.add(c);
      const rim = new THREE.PointLight('#dff0d0', 1.6, 2.4, 1.5); rim.position.set(0.35, 1.9, 2.75); W.scene.add(rim);
      if (W.p.cam === 'mask') {
        const f = new THREE.PointLight('#9fb4e0', 0.6, 1.4, 1.6); f.position.set(1.55, 1.6, 2.95); W.scene.add(f);
        return camera(22, V(2.95, 1.62, 3.0), V(0.98, 1.55, 2.9), A);
      }
      return camera(52, V(2.75, 1.3, 3.4), V(1.0, 1.0, 2.9), A);
    } },
    // ANIM: he raises a phone toward Alex (screen lit)
    E4_cop_raise: { desc: 'The masked officer raises a phone toward Alex, its screen lit', frames: 16, make(W, t, A) {
      bed4(W, { moon: 0.8 }); frontDoorOpen(W, 1.3);
      const c = maskedCop(); c.position.set(0.98, 0, 2.9); c.rotation.y = Math.PI / 2; W.scene.add(c);
      const e = 1 - Math.pow(1 - t, 3); const armR = c.userData.arms[-1]; armR.rotation.x = -1.45 * e; armR.rotation.z = 0.15 * e;
      const gp = gloveWithPhone(armR); gp.group.position.set(0, -0.62, 0.04); gp.group.rotation.set(Math.PI / 2, 0, 0);
      const rim = new THREE.PointLight('#dff0d0', 1.6, 2.4, 1.5); rim.position.set(0.35, 1.9, 2.75); W.scene.add(rim);
      const sl = new THREE.PointLight('#bcd2ff', 0.25 + 0.5 * e, 1.0, 1.7); sl.position.set(1.45, 1.4, 2.9); W.scene.add(sl);
      return camera(40, V(2.6, 1.4, 3.3), V(1.0, 1.3, 2.88), A);
    } },
    // the phone held out in a black glove, the mask behind it (screen quad -> photo + message drawn in code)
    E4_cop_phone: { desc: 'The officer holds the phone out at Alex: screen toward the camera, the black mask behind', phone: true, make(W, t, A) {
      bed4(W, { moon: 0.8 }); frontDoorOpen(W, 1.3);
      const c = maskedCop(); c.position.set(0.98, 0, 2.9); c.rotation.y = Math.PI / 2; W.scene.add(c);
      const armR = c.userData.arms[-1]; armR.rotation.x = -1.45; armR.rotation.z = 0.15;
      const ph = gloveWithPhone(W.scene); ph.group.position.set(1.52, 1.42, 2.82); ph.group.rotation.set(0, Math.PI / 2 - 0.12, 0.04); W.screen = ph.screen;
      const rim = new THREE.PointLight('#dff0d0', 1.6, 2.4, 1.5); rim.position.set(0.35, 1.9, 2.75); W.scene.add(rim);
      if (W.p.close) return camera(30, V(1.95, 1.45, 2.86), V(1.52, 1.42, 2.83), A);
      return camera(40, V(2.05, 1.48, 2.98), V(1.3, 1.45, 2.85), A);
    } },
    // the covert photo of Alex's sister shown on that phone (rendered once, used as an image in the phone UI)
    E4_sister_photo: { desc: 'Covert photo: Alex\'s sister reading at her desk under a warm lamp, taken through a window', ref: true, make(W, t, A) {
      sisterRoom(W);
      return camera(32, V(0.3, 1.3, 2.25), V(0.0, 1.0, 0.0), A);
    } },
    // character sheet for future episodes: Alex's sister (front + 3/4)
    REF_sister: { desc: 'Character reference: Alex\'s sister (front and three-quarter)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const s1 = P.makePerson('sister'); s1.position.set(-0.5, 0, 0); W.scene.add(s1);
      const s2 = P.makePerson('sister'); s2.position.set(0.5, 0, 0); s2.rotation.y = Math.PI * 0.75; W.scene.add(s2);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.0, 3.6), V(0, 0.95, 0), A);
    } },
    REF_masked_cop: { desc: 'Character reference: the officer in EP04 — black balaclava, black gloves (same uniform model)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const c1 = maskedCop(); c1.position.set(-0.5, 0, 0); W.scene.add(c1);
      const c2 = maskedCop(); c2.position.set(0.5, 0, 0); c2.rotation.y = Math.PI * 0.75; W.scene.add(c2);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.0, 3.6), V(0, 0.95, 0), A);
    } },

    // ====================================================================== EP05 «КОМНАТА 204» (same world, same cast; starts on EP04's last frame)
    // Alex hears his sister's voice from the officer's phone (facing the doorway, face lit by that phone)
    E5_alex_react: { desc: 'Close-up: Alex, turned to the doorway, his face lit by the officer\'s phone', make(W, t, A) {
      bed5(W, { moon: 0.9 }); tiedMan4(W, { face: 'worried_redmark_pale', tape: 0, head: -0.25 });
      const a = alex({ face: W.p.face || 'wide_worried' }); a.position.copy(ALEX4); a.rotation.y = -Math.PI / 2; W.scene.add(a);
      a.userData.arms[1].rotation.x = -0.1; a.userData.arms[-1].rotation.x = -0.1;
      const pl = new THREE.PointLight('#d4dcff', 0.5, 1.4, 1.6); pl.position.set(1.35, 1.45, 2.9); W.scene.add(pl);
      const rim = new THREE.PointLight('#86a2dc', 0.5, 1.8, 1.6); rim.position.set(2.3, 1.85, 3.25); W.scene.add(rim);
      return camera(34, V(0.3, 1.5, 3.05), V(1.78, 1.46, 2.92), A);
    } },
    // ANIM: POV — the masked officer raises his gloved hand and holds out a key on a red fob
    E5_key_offer: { desc: 'POV: the masked officer holds out a key with a red fob «204»', frames: 16, make(W, t, A) {
      bed5(W, { moon: 0.8 }); const e = 1 - Math.pow(1 - t, 3);
      copWithKey(W, e, { swing: 0.25 * Math.sin(t * 9) * (1 - t) });
      const rim = new THREE.PointLight('#dff0d0', 1.6, 2.4, 1.5); rim.position.set(0.35, 1.9, 2.75); W.scene.add(rim);
      const f = new THREE.PointLight('#cfd8ff', 0.45, 1.6, 1.6); f.position.set(1.65, 1.5, 2.85); W.scene.add(f);
      const cam = camera(48, V(2.35, 1.5, 2.98), V(1.15, 1.36, 3.02), A); camGlow(W, cam, 0.4); return cam;
    } },
    // MACRO: the key and its fob «204» hanging from the black glove
    E5_key_tag: { desc: 'Macro: the brass key and the burgundy fob «204» hanging from the black glove', make(W, t, A) {
      bed5(W, { moon: 0.8 }); const { key } = copWithKey(W, 1, { swing: 0.05 });
      const kp = key.getWorldPosition(V(0, 0, 0));
      const rim = new THREE.PointLight('#dff0d0', 1.6, 2.4, 1.5); rim.position.set(0.35, 1.9, 2.75); W.scene.add(rim);
      const f = new THREE.PointLight('#e6ecff', 0.32, 0.8, 1.6); f.position.copy(kp).add(V(0.25, 0.05, 0.08)); W.scene.add(f);
      const w = new THREE.PointLight('#ffd7a8', 0.12, 0.6, 1.6); w.position.copy(kp).add(V(0.15, 0.1, -0.15)); W.scene.add(w);
      return camera(30, kp.clone().add(V(0.36, -0.04, 0.0)), kp.clone().add(V(0, -0.06, -0.018)), A);
    } },
    // ANIM: POV — Alex's hand reaches for the key and stops short
    E5_reach: { desc: 'POV: Alex\'s hand reaches for the key, and stops short', frames: 16, make(W, t, A) {
      bed5(W, { moon: 0.8 }); const { key } = copWithKey(W, 1, { swing: 0.04 * Math.sin(t * 7) });
      const kp = key.getWorldPosition(V(0, 0, 0)).add(V(0.0, -0.05, 0));
      const e = Math.min(1, t / 0.8), ee = 1 - Math.pow(1 - e, 3);
      const h = V(1.95, 1.0, 2.9).lerp(kp.clone().add(V(0.13, -0.02, 0.02)), ee);
      W.scene.add(aimArm(arm(), V(2.2, 1.1, 2.86), h));
      const rim = new THREE.PointLight('#dff0d0', 1.6, 2.4, 1.5); rim.position.set(0.35, 1.9, 2.75); W.scene.add(rim);
      const f = new THREE.PointLight('#cfd8ff', 0.45, 1.6, 1.6); f.position.set(1.65, 1.5, 2.85); W.scene.add(f);
      return camera(48, V(2.35, 1.5, 2.98), V(1.15, 1.36, 3.02), A);
    } },
    // wide from the corner: the officer in the doorway holding out the key, Alex facing him, the tied double. params.empty: the
    // same frame with the officer gone and the key on the floor at Alex's feet (used across the blackout)
    E5_doorway: { desc: 'Wide: the officer in the doorway holds out the key to Alex; (empty) the same frame, the officer gone, key on the floor', make(W, t, A) {
      bed5(W, { moon: 0.95 }); tiedMan4(W, { face: 'wide_worried_redmark_pale', tape: 0, head: -0.35 });
      const a = alex({ face: 'wide_worried' }); a.position.copy(ALEX4); a.rotation.y = -Math.PI / 2; W.scene.add(a);
      if (!W.p.empty) copWithKey(W, 1);
      else { const k = P.makeKey({ fobTilt: 0.5 }); k.position.set(1.56, 0.012, 2.98); k.rotation.set(-Math.PI / 2, 0, 2.2); W.scene.add(k); }
      const rim = new THREE.PointLight('#dff0d0', 1.5, 2.4, 1.5); rim.position.set(0.35, 1.9, 2.75); W.scene.add(rim);
      const f = new THREE.PointLight('#cfd8ff', 0.35, 1.8, 1.6); f.position.set(1.4, 1.5, 3.1); W.scene.add(f);
      return camera(52, V(3.55, 1.62, 4.3), V(1.2, 1.05, 2.8), A);
    } },
    // low on the floor after the light comes back: the key at Alex's feet, his cracked phone behind (screen quad -> UI)
    E5_floor: { desc: 'Low on the floor: the key lies at Alex\'s feet', make(W, t, A) {
      bed5(W, { moon: 1.0, floorPhone: false }); tiedMan4(W, { face: 'worried_redmark_pale', tape: 0 });
      const a = alex({ face: 'worried' }); a.position.copy(ALEX4); a.rotation.y = -Math.PI / 2; W.scene.add(a);
      const k = P.makeKey({ fobTilt: 0.5 }); k.position.set(1.56, 0.012, 2.98); k.rotation.set(-Math.PI / 2, 0, 2.2 + Math.PI); W.scene.add(k);
      const ph = P.makePhone('#0c0f14'); ph.position.set(2.0, 0.006, 3.42); ph.rotation.set(-Math.PI / 2, 0, 0.3); W.scene.add(ph);
      const kl = new THREE.PointLight('#cfd8ff', 0.25, 1.0, 1.6); kl.position.set(1.4, 0.35, 3.2); W.scene.add(kl);
      const pl = new THREE.PointLight('#a8c4ff', 0.3, 0.9, 1.6); pl.position.set(2.0, 0.15, 3.42); W.scene.add(pl);
      return camera(40, V(1.12, 0.48, 3.32), V(1.58, 0.03, 2.97), A);
    } },
    // top-down macro on the cracked phone (EP04's E4_phone_floor framing), the key's fob at the edge of the frame
    E5_phone_task: { desc: 'Top-down macro: Alex\'s cracked phone wakes up on the floor', phone: true, make(W, t, A) {
      bed4(W, { floorPhone: false });
      const ph = P.makePhone('#141b26'); ph.position.set(2.0, 0.006, 3.42); ph.rotation.set(-Math.PI / 2, 0, 0.3); W.scene.add(ph); W.screen = ph.getObjectByName('screen');
      const pl = new THREE.PointLight('#a8c4ff', 0.45, 0.8, 1.6); pl.position.set(2.0, 0.12, 3.42); W.scene.add(pl);
      const c = new THREE.PerspectiveCamera(30, A, 0.01, 60); c.position.set(2.02, 0.5, 3.47); c.up.set(Math.sin(0.3), 0, -Math.cos(0.3)); c.lookAt(V(2.0, 0.0, 3.42)); return c;
    } },
    // over the double's shoulder: Alex holds the key up and asks what is in that room
    E5_alex_key: { desc: 'Over the double\'s shoulder: Alex holds up the key and asks', make(W, t, A) {
      bed5(W); tiedMan4(W, { face: 'worried_redmark_pale', tape: 0, head: 0.1 });
      const a = alex({ face: 'worried' }); a.position.set(ALEX4.x - 0.3, 0, ALEX4.z + 0.04); a.rotation.y = Math.PI / 2; W.scene.add(a);
      const arm_ = a.userData.arms[-1]; arm_.rotation.x = -1.35; arm_.rotation.z = -0.2;
      const k = P.makeKey(); k.position.set(0, -0.6, 0.07); k.rotation.x = 1.35; k.rotation.z = 0.2; arm_.add(k);
      const pl = new THREE.PointLight('#cfd8ff', 0.6, 1.4, 1.7); pl.position.set(a.position.x + 0.35, 1.35, 2.92); W.scene.add(pl);
      return camera(44, V(2.9, 1.5, 3.75), V(1.55, 1.25, 2.95), A);
    } },
    // from the bedroom through its doorway: the dark hallway, the front door ajar (the sister's voice comes from there)
    E5_hall_voice: { desc: 'From the bedroom through the doorway: the dark hallway and the front door ajar', make(W, t, A) {
      bed5(W, { moon: 1.0, gap: 0.9 });
      const w = new THREE.PointLight('#ffd7a8', 0.35, 2.4, 1.5); w.position.set(0.3, 1.9, 2.0); W.scene.add(w);
      return camera(50, V(1.32, 1.5, 3.25), V(0.05, 1.1, 0.4), A);
    } },
    // ANIM: Alex runs out of the bedroom into the hallway, toward the front door (camera by the front door)
    E5_run_out: { desc: 'Alex runs out of the bedroom into the hallway, toward the open front door', frames: 20, make(W, t, A) {
      bed4(W); ajar(W, 1.0); gapLight(W, 0.8);
      const pts = [V(1.7, 0, 2.92), V(0.95, 0, 2.86), V(0.45, 0, 2.45), V(0.28, 0, 1.95)];
      const u = t * 3, i = Math.min(2, Math.floor(u)), f = u - i; const pos = pts[i].clone().lerp(pts[i + 1], f);
      const dir = pts[i + 1].clone().sub(pts[i]).normalize();
      const a = alex({ face: 'wide_worried' }); a.rotation.order = 'YXZ'; a.position.copy(pos); a.rotation.y = Math.atan2(dir.x, dir.z); a.rotation.x = 0.16; W.scene.add(a);
      walkPose(a, t * 2.6, 0.7); a.position.y = 0.02 * Math.abs(Math.sin(t * 2.6 * Math.PI * 2));
      const w = new THREE.PointLight('#ffd7a8', 0.5, 2.6, 1.5); w.position.set(0.3, 1.9, 2.0); W.scene.add(w);
      return camera(50, V(-0.25, 1.35, 0.55), V(0.85, 1.12, 2.75), A);
    } },
    // the open front door seen from the hallway. mode: 'stair' = the usual stairwell (memory), 'dark' = black with a red point,
    // 'corridor' = the hotel corridor that is there now. Same camera for all three, so the change reads as one place.
    E5_view: { desc: 'From the hallway through the open front door: stairwell (memory) / darkness / the hotel corridor', make(W, t, A) {
      const m = W.p.mode || 'corridor';
      if (m === 'stair') { bed4(W, { floorPhone: false }); ajar(W, 1.45); gapLight(W, 1.0); }
      else if (m === 'dark') {
        bed4(W, { floorPhone: false }); ajar(W, 1.45); W.objs.stairwell.visible = false;
        const v = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 2.4), new THREE.MeshBasicMaterial({ color: '#020203' })); v.position.set(0, 1.1, -0.3); W.scene.add(v);
        const dot = new THREE.Mesh(new THREE.CircleGeometry(0.011, 10), new THREE.MeshBasicMaterial({ color: '#ff3a2a' })); dot.position.set(0.181, 1.68, -0.29); W.scene.add(dot);
        const halo = new THREE.Mesh(new THREE.CircleGeometry(0.035, 12), new THREE.MeshBasicMaterial({ color: '#ff2a1e', transparent: true, opacity: 0.25 })); halo.position.set(0.181, 1.68, -0.295); W.scene.add(halo);
      }
      else corridorWorld(W, { sconces: 5 });
      const w = new THREE.PointLight('#ffd7a8', 0.3, 2.4, 1.5); w.position.set(0.3, 1.9, 2.0); W.scene.add(w);
      return camera(44, V(0.22, 1.55, 2.45), V(0.0, 1.32, -4.0), A);
    } },
    // telephoto down the corridor from flat 47's door: at the far end, the red lamp
    E5_corridor_far: { desc: 'Down the hotel corridor: at the far end a red lamp burns', make(W, t, A) {
      corridorWorld(W, { sconces: 5 });
      return camera(30, V(0.05, 1.55, -0.85), V(0.0, 1.5, ZE), A);
    } },
    // door 204 under the red lamp (the EP04 door, same plate)
    E5_door204: { desc: 'Door 204 under the caged red lamp', make(W, t, A) {
      corridorWorld(W, { sconces: 2 });
      return camera(40, V(0.28, 1.45, ZE + 3.4), V(0.0, 1.32, ZE), A);
    } },
    E5_door204_plate: { desc: 'Close: the plate «204» and the red lamp above it', make(W, t, A) {
      corridorWorld(W, { sconces: 2 });
      return camera(32, V(0.12, 1.84, ZE + 1.8), V(0.0, 1.96, ZE), A);
    } },
    // ANIM: Alex walks along the runner to door 204 (camera follows behind)
    E5_corridor_walk: { desc: 'From behind: Alex walks down the corridor to door 204', frames: 24, make(W, t, A) {
      corridorWorld(W, { sconces: 5 });
      const z = ZE + 4.4 - 3.5 * t; const a = alex({ face: 'worried' }); a.position.set(0.02, 0, z); a.rotation.y = Math.PI; W.scene.add(a);
      walkPose(a, t * 3.2, 0.35); a.position.y = 0.01 * Math.abs(Math.sin(t * 3.2 * Math.PI * 2));
      return camera(46, V(0.3, 1.78, z + 2.5), V(0.0, 1.3, z - 2.6), A);
    } },
    // side: Alex at door 204, his ear almost on the metal, red light from above
    E5_door_listen: { desc: 'Side close: Alex at door 204, listening, in the red light', make(W, t, A) {
      corridorWorld(W, { sconces: 2, gap: 1 });
      const a = alex({ face: 'wide_worried' }); a.position.set(0.08, 0, ZE + 0.52); a.rotation.y = Math.PI; W.scene.add(a);
      a.userData.headPivot.rotation.y = -0.45; a.rotation.z = 0.04;
      return camera(34, V(0.55, 1.6, ZE + 3.0), V(0.0, 1.45, ZE + 0.4), A);
    } },
    // floor level: the cold strip of light under door 204, broken by the shadows of two feet (someone stands behind it)
    E5_door_gap: { desc: 'Floor level: light under door 204, broken by the shadows of two feet', make(W, t, A) {
      corridorWorld(W, { sconces: 2, gap: 1, feet: 1 });
      return camera(30, V(0.22, 0.13, ZE + 1.05), V(0.0, 0.06, ZE), A);
    } },
    // Alex's face in the red light, from the door
    E5_alex_red: { desc: 'Close-up: Alex\'s face in the red light, seen from the door', make(W, t, A) {
      corridorWorld(W, { sconces: 2, gap: 1 });
      const a = alex({ face: W.p.face || 'wide_worried' }); a.position.set(0.06, 0, ZE + 1.7); a.rotation.y = Math.PI; W.scene.add(a);
      const f = new THREE.PointLight('#ff4a3a', 0.6, 1.6, 1.6); f.position.set(0.05, 1.95, ZE + 1.2); W.scene.add(f);
      return camera(36, V(-0.05, 1.52, ZE + 0.12), V(0.06, 1.47, ZE + 1.7), A);
    } },
    // MACRO ANIM (k): the key slides into the keyhole of door 204 (k 0..0.6) and turns (0.6..1)
    E5_key_lock: { desc: 'Macro: the key goes into the keyhole of door 204 and turns', make(W, t, A) {
      corridorWorld(W, { sconces: 2, gap: 1 });
      const k = W.p.k ?? 1, ins = Math.min(1, k / 0.6), turn = Math.max(0, (k - 0.6) / 0.4), e = 1 - Math.pow(1 - ins, 3);
      const KH = V(-0.36, 0.9, ZE + 0.066);
      const g = new THREE.Group(); g.position.copy(KH); g.rotation.z = -Math.PI / 2 * turn; W.scene.add(g);
      const key = P.makeKey(); key.rotation.x = Math.PI / 2; key.position.set(0, 0, 0.142 - 0.075 * e); g.add(key);
      key.userData.fob.rotation.x = -Math.PI / 2 + 0.1 * Math.sin(k * 12);
      const skin = P.M(P.PAL.skinAlex);
      const hand = new THREE.Group(); hand.position.set(0.0, 0.0, 0.2 - 0.075 * e); g.add(hand);
      P.box(0.07, 0.1, 0.09, skin, 0.052, 0.0, 0.0, hand); P.box(0.03, 0.03, 0.05, skin, 0.012, 0.025, -0.03, hand);
      P.box(0.13, 0.14, 0.2, P.M(P.PAL.hoodie), 0.09, -0.02, 0.15, hand);
      const f = new THREE.PointLight('#ffd9c8', 0.12, 0.7, 1.6); f.position.set(-0.1, 1.05, ZE + 0.45); W.scene.add(f);
      return camera(36, V(-0.72, 1.02, ZE + 0.36), V(-0.34, 0.91, ZE + 0.1), A);
    } },
    // ANIM: from behind Alex, door 204 swings open into the dark room (a table, shapes on it)
    E5_door204_open: { desc: 'From behind Alex: door 204 swings open into a dark room', frames: 20, make(W, t, A) {
      const e = t < 0.08 ? 0 : 1 - Math.pow(1 - Math.min(1, (t - 0.08) / 0.92), 2.4);
      corridorWorld(W, { sconces: 2, open: 1.35 * e, gap: e < 0.02 ? 1 : 0, amb: 0.3 });
      const a = alex({ face: 'worried' }); a.position.set(0.04, 0, ZE + 0.78); a.rotation.y = Math.PI; W.scene.add(a);
      a.userData.arms[1].rotation.x = -0.55;
      return camera(44, V(0.42, 1.64, ZE + 2.2), V(0.0, 1.2, ZE - 1.2), A);
    } },
    // POV into room 204: the table with dozens of phones. params.on: every screen lit (screens -> UI in post)
    E5_room: { desc: 'POV in room 204: a table covered with dozens of phones; (on) every screen lit', make(W, t, A) {
      const C = corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: !!W.p.on, fogNear: 6, amb: W.p.on ? 0.18 : 0.32 });
      W.screens = C.screens;
      return camera(50, V(0.05, 1.62, ZE + 0.25), V(0.0, 0.72, ZE - 1.65), A);
    } },
    // low across the table: rows of lit phones receding
    E5_phones_low: { desc: 'Low across the table: rows of lit phones, all showing the same message', make(W, t, A) {
      const C = corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: true, fogNear: 6 });
      W.screens = C.screens;
      return camera(40, V(0.95, 0.98, ZE - 1.22), V(-0.35, 0.76, ZE - 1.95), A);
    } },
    // macro on one phone among the others (screen -> full chat UI)
    E5_phone_hero: { desc: 'Macro: one phone among dozens, its screen readable', phone: true, make(W, t, A) {
      const C = corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: true, fogNear: 6 });
      const hi = 2 * 7 + 3, hero = C.phones[hi]; W.screen = C.screens[hi]; W.screens = C.screens.filter((_, i) => i !== hi);
      W.scene.updateMatrixWorld(true); const hp = hero.getWorldPosition(V(0, 0, 0));
      const c = new THREE.PerspectiveCamera(40, A, 0.01, 60); const r = hero.rotation.z;
      c.position.set(hp.x + 0.07, hp.y + 0.27, hp.z + 0.2); c.up.set(-Math.sin(r), 0, -Math.cos(r)); c.lookAt(V(hp.x, hp.y, hp.z - 0.01)); return c;
    } },
    // ANIM (k): from across the table, Alex lit by the phones; behind him the sister steps out of the dark doorway
    E5_sister_behind: { desc: 'From across the table: Alex lit by the phones; his sister appears behind him', make(W, t, A) {
      const C = corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: true, fogNear: 6 });
      W.screens = C.screens; alexAtTable(W); const k = W.p.k ?? 1; sisterAt(W, k);
      const sl = new THREE.PointLight('#a9c4ff', 0.35 * k, 1.4, 1.6); sl.position.set(-0.3, 1.4, ZE - 0.6); W.scene.add(sl);
      return camera(44, V(0.12, 1.12, ZE - 2.7), V(-0.05, 1.36, ZE - 0.3), A);
    } },
    // close-up: the sister over Alex's shoulder, lit from below by the phones, red rim from the corridor (lip-sync stills by face)
    E5_sis: { desc: 'Close-up: the sister behind Alex, lit by the phones, red rim light from the corridor', make(W, t, A) {
      corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: true, fogNear: 6 }); alexAtTable(W); sisterAt(W, 1);
      const f = new THREE.PointLight('#b4caff', 0.5, 1.2, 1.6); f.position.set(-0.25, 1.15, ZE - 0.75); W.scene.add(f);
      return camera(30, V(-0.82, 1.56, ZE - 1.55), V(-0.36, 1.55, ZE - 0.2), A);
    } },
    // reference sheets for future episodes
    REF_key204: { desc: 'Prop reference: the key of room 204 (front and side)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const k1 = P.makeKey(); k1.position.set(-0.06, 0.06, 0); W.scene.add(k1);
      const k2 = P.makeKey(); k2.position.set(0.07, 0.06, 0); k2.rotation.y = -0.9; W.scene.add(k2);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.6); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 0.0, 0.42), V(0.005, -0.0, 0), A);
    } },
    REF_sister_mouths: { desc: 'Character reference: the sister\'s lip-sync mouth shapes (neutral, open, ee, oo)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      ['neutral', 'open', 'ee', 'oo'].forEach((f, i) => { const s = P.makePerson('sister', { face: f }); s.position.set(-0.75 + i * 0.5, 0, 0); W.scene.add(s); });
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(26, V(0, 1.45, 3.0), V(0, 1.45, 0), A);
    } },
    REF_corridor: { desc: 'Location reference: the hotel corridor behind flat 47 and door 204 at its end', make(W, t, A) {
      corridorWorld(W, { sconces: 8, amb: 0.6, fog: false });
      return camera(50, V(0.0, 2.1, -0.6), V(0.0, 1.2, ZE), A);
    } },
    REF_room204: { desc: 'Location reference: room 204 — the table with 35 phones (lit)', make(W, t, A) {
      corridorWorld(W, { sconces: 0, open: 1.35, phonesOn: true, amb: 0.7, fog: false });
      return camera(44, V(1.3, 2.2, ZE - 0.4), V(0.0, 0.6, ZE - 1.9), A);
    } },
    // reference turnarounds (character/location sheets)
    REF_alex: { desc: 'Character reference: Alex', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const a1 = alex(); a1.position.set(-0.5, 0, 0); W.scene.add(a1);
      const a2 = alex(); a2.position.set(0.5, 0, 0); a2.rotation.y = Math.PI * 0.75; W.scene.add(a2);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.05, 6.2), V(0, 0.95, 0), A);
    } },
    REF_cop: { desc: 'Character reference: police officer + the double (bloody right hand)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const c = P.makePerson('cop'); c.position.set(-0.5, 0, 0); W.scene.add(c);
      const d2 = alex({ bloodyRight: true }); d2.position.set(0.5, 0, 0); d2.rotation.y = -0.4; W.scene.add(d2);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.05, 6.2), V(0, 0.95, 0), A);
    } },
  };
  window.SHOTS = SHOTS;
  window.screenQuad = screenQuad;
})();
