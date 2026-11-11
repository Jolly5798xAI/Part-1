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


  // ---------- EP06 helpers (only used by E6_* shots) ----------
  // room 204 as EP05 left it (door open, every phone lit); o.red: the countdown's red glow on every screen
  function room6(W, o = {}) {
    const red = !!o.red;
    const C = corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: true, fogNear: 6, amb: o.amb ?? 0.2,
      screenCol: red ? '#ff8a7a' : undefined, lightCol: red ? '#ff5a48' : undefined });
    W.screens = C.screens; return C;
  }
  function lamp(W, col, i, pos, range = 2.0) { const l = new THREE.PointLight(col, i, range, 1.6); l.position.set(...pos); W.scene.add(l); return l; }
  function faceTo(p, x, z) { p.rotation.y = Math.atan2(x - p.position.x, z - p.position.z); return p; }
  function sis6(W, x, z, face = 'neutral') { const s = P.makePerson('sister', { face }); s.position.set(x, 0, z); W.scene.add(s); return s; }
  function alex6(W, x, z, face = 'wide_worried') { const a = alex({ face }); a.position.set(x, 0, z); W.scene.add(a); return a; }
  const SIS = [-0.45, ZE - 0.12];          // where the sister stands after stepping back (by the left jamb of the doorway)
  const SIS2 = [-0.55, ZE - 1.05];         // later: by the near left corner of the table
  const ALEX_M = [-0.25, ZE - 0.7];        // Alex in front of the mirror
  const OLD_M = [-0.25, ZE - 0.72];        // the old Alex in the reflection — exactly where Alex's own reflection should be
  // a phone held up by the sister in front of the camera (POV): her fingers + mustard sleeve; returns the screen mesh
  function sisPhonePOV(W, cam, o = {}) {
    W.scene.add(cam);
    const rig = new THREE.Group(); cam.add(rig);
    rig.position.set(o.x ?? 0.0, o.y ?? -0.01, o.z ?? -0.31); rig.rotation.set(o.rx ?? 0.05, o.ry ?? 0.12, o.rz ?? -0.07);
    const ph = P.makePhone('#d8e6ff'); rig.add(ph);
    const skin = P.M(P.PAL.skinAlex);
    P.box(0.092, 0.1, 0.03, skin, 0.004, -0.06, -0.022, rig);                                              // palm behind the phone
    P.box(0.022, 0.052, 0.022, skin, 0.05, -0.03, -0.002, rig).rotation.z = -0.3;                            // thumb
    for (let i = 0; i < 3; i++) P.box(0.02, 0.022, 0.024, skin, -0.047, -0.012 - i * 0.034, -0.002, rig);    // fingers
    P.box(0.13, 0.3, 0.13, P.M(P.PAL.sweater), 0.02, -0.25, -0.07, rig).rotation.x = -0.45;                 // sleeve
    const l = new THREE.PointLight(o.glowCol || '#bcd2ff', 0.06, 0.7, 2); l.position.set(0, 0.05, 0.18); rig.add(l);
    return ph.getObjectByName('screen');
  }
  // a phone in the sister's raised right hand (third person), screen toward +z of the hand; returns the screen mesh
  function sisHoldPhone(W, s, lift = 1.0) {
    const a = s.userData.arms[-1]; a.rotation.x = -1.05 * lift; a.rotation.z = 0.18 * lift;
    const ph = P.makePhone('#d8e6ff'); ph.position.set(0, -0.6, 0.06); ph.rotation.x = 1.05 * lift - 0.25; a.add(ph);
    const l = new THREE.PointLight('#bcd2ff', 0.25, 0.9, 1.7); l.position.set(0, -0.6, 0.2); a.add(l);
    W.scene.updateMatrixWorld(true); return ph.getObjectByName('screen');
  }
  // one blocky forearm (sleeve + hand) aimed from `from` to `to`
  function forearm(W, sleeveCol, from, to) {
    const g = new THREE.Group();
    P.box(0.15, 0.48, 0.16, P.M(sleeveCol), 0, -0.3, 0, g); P.box(0.13, 0.12, 0.15, P.M(P.PAL.skinAlex), 0, -0.6, 0, g, 'hand');
    aimArm(g, from, to); W.scene.add(g); return g;
  }


  // ---------- EP07 helpers (only used by E7_* shots) ----------
  const CRACK = [OLD_M[0] + 0.3, 1.43];        // where the old Alex's right fist hits the glass (his palm's EP06 spot)
  function cam7(fov, pos, look, A) { const c = camera(fov, pos, look, A); c.layers.enable(2); return c; }
  // room 204 in EP07. o.lit: the table still red (before the screens die); default: every phone dead, the room lit only by
  // the mirror's cold glow. o.mirror: 'whole' | 'cracked' | 'shattered' (k = o.k) | 'none' (blank wall, the camera faces away)
  function room7(W, o = {}) {
    const lit = !!o.lit;
    const C = corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: lit, fogNear: 6, amb: o.amb ?? (lit ? 0.2 : 0.12),
      screenCol: lit ? '#ff8a7a' : undefined, lightCol: lit ? '#ff5a48' : undefined });
    if (lit) W.screens = C.screens;
    const mode = o.mirror || 'cracked'; let M_ = null;
    if (mode === 'none') P.room204Wall(W);
    else if (mode === 'shattered') { M_ = P.shatterMirror204(W, o.k ?? 1, { cx: CRACK[0], cy: CRACK[1] }); P.buildMonitorRoom(W, { feedCam: o.feedCam, red: o.red }); }
    else { M_ = P.makeMirror204(W, { glowX: o.glowX ?? ALEX_M[0] + 0.5, glow: o.glow ?? (lit ? 0.4 : 0.85), glowD: o.glowD });
      if (mode === 'cracked') P.mirrorCracks(W, M_, { k: o.crack ?? 1, cx: CRACK[0], cy: CRACK[1] }); }
    if (!lit) { lamp(W, '#9fb6c8', 0.35, [0.0, 2.1, ZE - 1.6], 3.2); }
    return M_;
  }
  // the old Alex in the glass (exists only in the reflection); o.near: a step closer (POV shots); o.fist: punch 0..1; o.point
  function oldInMirror(W, o = {}) {
    const m = P.mirrorOnly(alex({ face: o.face || 'old_worried' })); m.position.set(OLD_M[0], 0, OLD_M[1] + (o.near ? 0.07 : 0)); W.scene.add(m);
    m.userData.headPivot.rotation.x = 0.04;
    const ar = m.userData.arms[1];
    if (o.fist !== undefined) { const f = o.fist; ar.rotation.x = f < 0.55 ? 0.35 * (f / 0.55) : 0.35 - 2.15 * Math.min(1, (f - 0.55) / 0.2); ar.rotation.z = 0.1; m.userData.headPivot.rotation.x = -0.05; }
    if (o.point) { ar.rotation.x = -1.15; ar.rotation.z = -0.35; m.userData.headPivot.rotation.x = 0.2; }
    if (o.palm) { ar.rotation.x = -1.86; const h = P.mirrorOnly(P.makeOpenHand(false)); h.position.set(OLD_M[0] + 0.3, 1.43, ZE - 0.165 - 0.016); W.scene.add(h); }
    W.scene.updateMatrixWorld(true); return m;
  }
  // the sister's live feed: the operator's room far away (z ≈ +40), seen by her webcam
  function opsFeed(W, o = {}) { return P.buildOperatorRoom(W, o); }
  // the forearm macro rig (camera space, like EP04's E4_scars): Alex's LEFT forearm, inner wrist up to the camera
  function wristRig(W, cam, o = {}) {
    W.scene.add(cam);
    const a = P.makeForearm7({ num: o.num ?? 1, clear: o.clear ?? 0, clearHand: o.clearHand });
    a.position.set(o.x ?? 0.03, o.y ?? -0.3, o.z ?? -0.95); a.rotation.set(o.rx ?? 0.0, 0, o.rz ?? (Math.PI - 0.12)); cam.add(a);
    const l = new THREE.PointLight(o.lightCol || '#b9d0ff', o.light ?? 0.6, 1.4, 1.6); l.position.set(0.1, 0.12, 0.05); cam.add(l);
    return a;
  }


  // ---------- EP08 helpers (only used by E8_* shots) ----------
  // ALEX_48 = the hero of EP08 (number 48 on the wrist, the left hand being deleted); ALEX_ORIGINAL = the Alex at the
  // kitchen table (plain model, no marks); ALEX_FIRST is never shown. These names live only in the code.
  const MON_A = [-0.15, ZE - 0.1 + 1.95];   // ALEX_48 in the monitor room, in front of the operator desk, facing the wall (+z)
  const MON_Z = ZE - 0.1 + 3.3 - 0.12 - 0.027;   // the monitor screens' plane (buildMonitorRoom: z1 - 0.12 - 0.027)
  // the monitor-room world: the same lights as EP07's room7 (bed4's two moon/hemi rigs + room 204's), but flat 47's door
  // shut and the flat left clean (no EP02/EP03 leftovers) because the recording shows its entryway "tomorrow"
  function world8(W, o = {}) {
    bedDoor(W, 1.25); bedroomLights(W, { moon: 1.3, amb: 0.28 }); P.lightsInterior(W.scene, { amb: 0.3, moon: 0.4, warm: 0.8 });
    ajar(W, o.door ?? 0);
    return P.buildCorridor(W, { sconces: 2, open: 1.35, phonesOn: false, fogNear: 6, amb: o.amb ?? 0.12 });
  }
  function room8(W, o = {}) {
    world8(W, o);
    P.shatterMirror204(W, 1, { cx: CRACK[0], cy: CRACK[1] });
    const R = P.buildMonitorRoom(W, { feedCam: o.feedCam, red: o.red });
    // EP08: ALEX_48 walks through this room — its second light goes up under the ceiling (it sat at head height by the frame),
    // and o.dim tones the room's lights down for faces close to the monitors
    const pl = R.G.children.filter(c => c.isPointLight); if (pl[1]) pl[1].position.y = 2.35;
    if (o.dim) pl.forEach(l => { l.intensity *= o.dim; });
    lamp(W, '#9fb6c8', 0.35, [0.0, 2.1, ZE - 1.6], 3.2);
    if (o.k) P.collapseMonitorRoom(W, o.k, { keep: o.keepAll ? R.screens : [R.screens[0]] });
    return R;
  }
  // flat 47 at night (the main world's entryway + the new kitchen): bedroom door as EP03 left it, the EP01 light rig
  function flat8(W, o = {}) {
    bedDoor(W, o.bed ?? 1.25); bedroomLights(W, { moon: 1.3, amb: 0.28 }); P.lightsInterior(W.scene, { amb: o.amb ?? 0.3, moon: 0.4, warm: o.warm ?? 0.8, leak: o.leak ?? 6 });
    return P.buildKitchen(W, { glass: o.glass || 'table', lamp: o.lamp ?? 2.4 });
  }
  // ALEX_48's left hand being deleted (EP07): forearm and hand dissolve from the fingertips, cyan edge, a faint cyan glow
  function vanishLeft(W, p, k = 0.55) {
    W.scene.updateMatrixWorld(true); const a = p.userData.arms[-1];
    const tip = a.localToWorld(V(0, -0.6, 0)), root = a.localToWorld(V(0, -0.08, 0)), d = root.clone().sub(tip).normalize();
    P.dissolve(a, k, { dir: d, a: tip.dot(d), b: root.dot(d), cell: 60, sweep: 1.0, glow: '#5fe6ff' });
    const l = new THREE.PointLight('#5fe6ff', 0.3, 0.8, 1.6); l.position.copy(a.localToWorld(V(0, -0.42, 0.12))); W.scene.add(l);
  }
  function alex48(W, x, z, face = 'wide_worried') { return alex6(W, x, z, face); }
  // a knife in a figure's right fist (blade down-forward)
  function giveKnife(p, o = {}) { const ar = p.userData.arms[1]; ar.rotation.x = o.rx ?? -0.42; ar.rotation.z = 0.12; const k = P.makeKnife(); k.scale.setScalar(1.25); k.position.set(0, -0.57, 0.04); k.rotation.x = o.kx ?? -0.55; ar.add(k); const g = new THREE.PointLight('#e8f2ff', 0.25, 0.5, 1.6); g.position.set(0.0, -0.75, 0.2); ar.add(g); return k; }
  // "tomorrow" on the recording: flat 47's entryway, ALEX_48 by the front door with a knife, ALEX_ORIGINAL facing him
  // (k: 0..1 he walks in from the kitchen and raises his hands; back: a half step back while he pleads)
  function recCast(W, o = {}) {
    const c = alex({ face: 'neutral' }); c.position.set(-0.05, 0, 0.58); c.rotation.y = 0.12; W.scene.add(c); giveKnife(c);
    let a = null;
    if (o.other !== false) {
      const k = o.k ?? 1, e = k * k * (3 - 2 * k), up = Math.max(0, Math.min(1, (k - 0.45) / 0.4));
      a = alex({ face: up > 0.3 ? 'wide_worried_open' : 'wide_worried' }); a.position.set(0.4 - 0.14 * e, 0, 3.7 - 2.2 * e + (o.back ?? 0)); a.rotation.y = Math.PI + 0.1; W.scene.add(a);
      if (k < 1) walkPose(a, e * 2.2, 0.35 * (1 - up));
      for (const sd of [-1, 1]) { const ar = a.userData.arms[sd]; ar.rotation.x = -1.25 * up + (o.shake ? 0.06 * Math.sin(o.shake * 40 + sd) : 0); ar.rotation.z = -sd * 0.28 * up; }
    }
    lamp(W, '#d6dee6', 0.55, [0.25, 1.85, 0.95], 2.2);                       // the landing light through the peephole side: faces read on the recording
    vanishLeft(W, c, 0.55);
    return { c, a };
  }
  function recCam(view, A) {
    if (view === 'door') return camera(38, V(0.95, 2.4, 3.85), V(-0.05, 1.15, 0.58), A);
    if (view === 'knife') return camera(17, V(0.95, 2.4, 3.85), V(0.24, 0.78, 0.86), A);
    if (view === 'plead') return camera(58, V(0.5, 2.3, 0.08), V(0.2, 1.1, 1.7), A);
    return camera(64, V(0.95, 2.45, 3.88), V(0.0, 0.9, 0.4), A);          // the security camera in the back corner
  }
  // a long arm (sleeve + fist) reaching from off-frame to `hand` along `dir` (for POV punches)
  function longArm(W, hand, from) {
    const g = new THREE.Group(), d = hand.clone().sub(from).normalize();
    P.box(0.15, 1.3, 0.17, P.M(P.PAL.hoodie), 0, 0.65 - 0.08, 0, g); P.box(0.13, 0.13, 0.15, P.M(P.PAL.skinAlex), 0, -0.02, 0, g);
    g.quaternion.setFromUnitVectors(V(0, 1, 0), d.clone().negate()); g.position.copy(hand); W.scene.add(g); return g;
  }
  // the lock's thumb-turn jerked round from outside: three tries, then the full turn (EP01 S20's motion), r 0..1
  function lockTurn(u) {
    const k = [[0, 0], [0.12, 0.1], [0.2, 0.04], [0.32, 0.22], [0.42, 0.16], [0.72, 0.85], [1, 1.0]];
    for (let i = 1; i < k.length; i++) if (u <= k[i][0]) { const v = (u - k[i - 1][0]) / (k[i][0] - k[i - 1][0]); return k[i - 1][1] + (k[i][1] - k[i - 1][1]) * v * v * (3 - 2 * v); }
    return 1;
  }


  // ---------- EP09 helpers (only used by E9_* shots) «ПЕРВЫЙ АЛЕКС»
  // Production names (code only, never on screen): ALEX_48 = the hero (the «48», the left hand being deleted); ALEX_49 = the new
  // copy who comes in with the glass of water (a lit «49» on his left wrist); ALEX_ZERO = the Alex from the kitchen table
  // (EP08's ALEX_ORIGINAL; a red «0» burns on his wrist late in the episode); ALEX_OLD_POLICE = the officer, unmasked: old Alex.
  // All four are the same makePerson('alex') model (the officer: the police model with old Alex's head).
  const A48_HIDE = [-0.42, 4.3];      // ALEX_48 pressed to the kitchen side of the shared wall, left of the doorway (x -0.15..0.75)
  const ZERO_HIDE = [1.02, 4.3];      // ALEX_ZERO on the other side of the doorway
  const PEEK = V(-0.1, 1.58, 4.2);    // ALEX_48's eye at the left jamb, looking down the hall to the front door
  const C49 = '#5fe6ff', C0 = '#ff3a2e';
  // flat 47 the moment EP08 ended (the glass broken by the table) + the bread knife by the plate (the knife ALEX_ZERO takes)
  function flat9(W, o = {}) {
    const K = flat8(W, { glass: o.glass ?? 'broken', leak: o.leak ?? 6, amb: o.amb, warm: o.warm, lamp: o.lamp });
    if (!o.noKnife) { const h = new THREE.Group(); h.position.set(0.56, 0.745, 5.78); h.rotation.y = 1.15; W.scene.add(h); const k = P.makeKnife(); k.rotation.x = -Math.PI / 2; k.position.set(0, 0.006, -0.05); h.add(k); }
    return K;
  }
  function a48(W, x, z, face = 'wide_worried', rot = 0) { const a = alex6(W, x, z, face); a.rotation.y = rot; return a; }
  // ALEX_49: the glass of water in his left hand (in front of the chest), the lit «49» at that wrist; o.phone: a phone in his
  // right hand (returns {a, screen}); o.glass false: hands free
  function a49(W, x, z, o = {}) {
    const a = alex6(W, x, z, o.face || 'neutral'); a.rotation.y = o.rot ?? 0;
    const L = a.userData.arms[-1];
    if (o.glass !== false) { L.rotation.x = o.lx ?? -0.95; L.rotation.z = 0.25; const g = P.makeGlass(); g.scale.setScalar(1.35); g.position.set(0.02, -0.6, 0.09); g.rotation.x = -(L.rotation.x); L.add(g); }
    P.wristBadge(a, '49', C49, { light: 0.3 });
    let screen = null;
    if (o.phone) { const R = a.userData.arms[1]; const lift = o.lift ?? 1; R.rotation.x = -1.05 * lift; R.rotation.z = -0.2 * lift; const ph = P.makePhone('#d8e6ff'); ph.position.set(0, -0.6, 0.06); ph.rotation.x = 1.05 * lift - 0.25; ph.rotation.y = 0.3; R.add(ph); screen = ph.getObjectByName('screen'); const l = new THREE.PointLight('#bcd2ff', 0.3, 0.9, 1.7); l.position.set(0, -0.6, 0.2); R.add(l); }
    W.scene.updateMatrixWorld(true); return { a, screen };
  }
  function zero(W, x, z, face = 'neutral', rot = Math.PI, o = {}) { const a = alex6(W, x, z, face); a.rotation.y = rot; if (o.num0) P.wristBadge(a, '0', C0, { light: 0.6 }); return a; }
  // the bread knife in a figure's right fist; o.up: raised (0..1), blade up and forward
  function knifeIn(p, o = {}) {
    const ar = p.userData.arms[1]; const up = o.up ?? 0; ar.rotation.x = o.rx ?? (-0.42 - 1.9 * up); ar.rotation.z = 0.12;
    const k = P.makeKnife(); k.scale.setScalar(1.25); k.position.set(0, -0.57, 0.04); k.rotation.x = o.kx ?? (-0.55 + 2.4 * up); ar.add(k);
    const g = new THREE.PointLight('#e8f2ff', 0.25, 0.5, 1.6); g.position.set(0.0, -0.75, 0.2); ar.add(g); return k;
  }
  // a forearm macro rig in camera space (EP07 wristRig) with a lit number: '49' cyan, '0' red
  function wrist9(W, cam, o = {}) {
    W.scene.add(cam);
    const a = P.makeForearm9({ text: o.text, glow: o.glow, g: o.g ?? 1, flip: o.flip });
    a.position.set(o.x ?? 0.03, o.y ?? -0.3, o.z ?? -0.95); a.rotation.set(o.rx ?? 0.0, 0, o.rz ?? (Math.PI - 0.12)); cam.add(a);
    const l = new THREE.PointLight(o.lightCol || '#ffd9b0', o.light ?? 0.45, 1.4, 1.6); l.position.set(0.1, 0.12, 0.05); cam.add(l);
    return a;
  }
  // the officer, unmasked (old Alex under the cap), on the landing just outside the front door; o.mask: the balaclava in his left
  // hand; o.phone: lift 0..1 the phone in his right hand held out toward the flat, screen first (returns {c, screen})
  function oldCop(W, o = {}) {
    const c = P.makeOldCop({ face: o.face || 'old', gloves: true }); c.position.set(o.x ?? 0.0, 0, o.z ?? -0.3); c.rotation.y = o.rot ?? 0; W.scene.add(c);
    c.userData.headPivot.rotation.x = o.head ?? 0;
    if (o.mask !== false) { const L = c.userData.arms[-1]; L.rotation.x = -0.55; L.rotation.z = 0.2; const b = P.makeBalaclava(); b.position.set(0, -0.6, 0.04); L.add(b); }
    let screen = null;
    if (o.phone !== undefined) {
      const R = c.userData.arms[1], u = o.phone, e = u * u * (3 - 2 * u); R.rotation.x = -1.48 * e; R.rotation.z = -0.12 * e;
      const ph = P.makePhone('#d8e6ff'); ph.scale.setScalar(1.15); ph.position.set(0, -0.62, 0.02); ph.rotation.x = Math.PI / 2 * e + (1 - e) * 0.0; R.add(ph); screen = ph.getObjectByName('screen');
      const l = new THREE.PointLight('#ff8a7a', 0.35 * e, 1.0, 1.7); l.position.set(0, -0.62, 0.0); R.add(l); l.position.z = 0; l.position.y = -0.62; l.translateZ(0.25);
    }
    W.scene.updateMatrixWorld(true); return { c, screen };
  }
  // the landing behind the open front door: cold, bright — the officer stands against it
  function landingLight(W, k = 1) { lamp(W, '#dfe8ff', 1.6 * k, [0.0, 2.1, -1.1], 3.2); lamp(W, '#b9c8e6', 0.8 * k, [0.0, 1.0, -0.9], 2.0); }

  // ---------- EP10 helpers (only used by E10_* shots) «СОЗДАТЕЛЬ»
  // Same production names as EP09 (code only): ALEX_48, ALEX_49, ALEX_ZERO, ALEX_OLD_POLICE; SISTER. EP10 starts the same second EP09
  // ended: flat 47, the front door open onto the cold landing, the officer (old Alex, unmasked, the balaclava in his left hand) has
  // stepped in over the threshold with his phone held out; the three Alexes in the hall facing him.
  const COP10 = [0.0, 0.8], COP10B = [-0.2, 1.75];     // the officer on the doormat / after he steps up to ALEX_48 with the phone
  const Z10 = [0.55, 2.35], A10 = [-0.35, 2.8], B10 = [0.78, 3.3];
  const EYE48 = V(-0.33, 1.55, 2.74);                  // ALEX_48's eyes (POV shots)
  const yaw = (from, to) => Math.atan2(to[0] - from[0], to[1] - from[1]);
  // flat 47 as EP09 left it: kitchen glass broken, the front door open, the landing light behind the officer; the hall dimmer than the landing
  function flat10(W, o = {}) {
    flat9(W, { noKnife: true, leak: 0, amb: o.amb ?? 0.22, warm: o.warm ?? 0.5, lamp: o.lamp });
    ajar(W, 1.3); landingLight(W, o.land ?? 0.9);
    lamp(W, '#b9c9e6', o.hall ?? 0.35, [0.15, 2.0, 2.2], 2.4);
  }
  // a phone held up in a figure's right hand, screen toward his own face (EP02 alexWithPhone pose); returns the screen mesh
  function holdPhone(p, o = {}) {
    const R = p.userData.arms[1]; R.rotation.x = o.rx ?? -1.2; R.rotation.z = o.rz ?? 0.25;
    const ph = P.makePhone(o.col || '#0b0e13'); ph.position.set(0.0, -0.62, 0.02); ph.rotation.x = -Math.PI / 2 + 0.25; R.add(ph);
    if (o.lit) { const l = new THREE.PointLight(o.lightCol || '#bcd2ff', o.light ?? 0.35, 0.9, 1.7); l.position.set(0, -0.62, 0.15); R.add(l); }
    return ph.getObjectByName('screen');
  }
  // the whole cast in the hall. o.cop: 'aim' (phone at ALEX_ZERO; o.aim 0..1 from ALEX_48 to ALEX_ZERO), 'give' (stepped up to ALEX_48,
  // phone held out; o.step 0..1), 'empty' (stepped up, hands empty), 'kneel' (o.kneel 0..1), false. o.zeroRot overrides ALEX_ZERO's yaw.
  function cast10(W, o = {}) {
    const R = {};
    if (o.cop !== false) {
      const mode = o.cop || 'aim';
      let pos = COP10, rot, phone;
      if (mode === 'aim') { const k = o.aim ?? 1; rot = yaw(COP10, A10) * (1 - k) + yaw(COP10, Z10) * k; phone = 1; }
      else { const k = mode === 'give' ? (o.step ?? 1) : 1, e = k * k * (3 - 2 * k); pos = [COP10[0] + (COP10B[0] - COP10[0]) * e, COP10[1] + (COP10B[1] - COP10[1]) * e]; rot = yaw(COP10, Z10) * (1 - e) + yaw(COP10B, A10) * e; phone = mode === 'give' ? 1 : undefined; }
      const r = oldCop(W, { x: pos[0], z: pos[1], rot, head: o.copHead ?? 0.0, phone, face: o.copFace || 'old' });
      if (mode === 'give' && (o.step ?? 1) < 1 && (o.step ?? 1) > 0) { const sw = 0.3 * Math.sin((o.step ?? 1) * Math.PI * 3.2); r.c.userData.legL.rotation.x = sw; r.c.userData.legR.rotation.x = -sw; }
      if (mode === 'kneel') P.kneelPose(r.c, o.kneel ?? 1);
      if (mode === 'empty' || mode === 'kneel') { const Rr = r.c.userData.arms[1]; Rr.rotation.x = mode === 'kneel' ? Rr.rotation.x : -0.15; }
      R.cop = r.c; R.copScreen = r.screen;
    }
    if (o.zero !== false) {
      const z = zero(W, Z10[0], Z10[1], o.zeroFace || 'neutral', o.zeroRot ?? yaw(Z10, o.cop === 'aim' || !o.cop ? COP10 : COP10B), { num0: true });
      knifeIn(z); z.userData.headPivot.rotation.x = o.zeroHead ?? 0.0; if (o.zeroHeadY !== undefined) z.userData.headPivot.rotation.y = o.zeroHeadY;
      if (o.vanish) { W.scene.updateMatrixWorld(true); P.dissolve(z, o.vanish, { dir: V(0, 1, 0), a: 0.0, b: 1.85, cell: 34, sweep: 0.9, glow: '#5fe6ff' }); }
      R.zero = z;
    }
    if (o.a48 !== false) {
      const a = a48(W, A10[0], A10[1], o.a48Face || 'wide_worried', o.a48Rot ?? yaw(A10, o.cop === 'aim' || !o.cop ? COP10 : COP10B));
      if (o.a48Phone) R.a48Screen = holdPhone(a, { lit: true, lightCol: o.a48Light });
      vanishLeft(W, a, 0.7); R.a48 = a;
    }
    if (o.a49 !== false) {
      const b = a49(W, B10[0], B10[1], { glass: false, rot: o.a49Rot ?? yaw(B10, COP10) });
      if (o.a49Phone) R.a49Screen = holdPhone(b.a, { lit: true, lightCol: o.a49Light });
      R.a49 = b.a;
    }
    W.scene.updateMatrixWorld(true);
    return R;
  }
  // room 204 (EP05's room, the table of phones lit), the sister at her computer — seen as a recording (the door of 204 stands open
  // as in EP05; no mirror). Returns room204Desk's {s, screen, cam}
  function room10(W, o = {}) {
    corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: true, fogNear: 6, amb: o.amb ?? 0.22 });
    return P.room204Desk(W, { face: o.face || 'cold', head: o.head });
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

    // ======================= EP06 «ПЕРВАЯ ПОПЫТКА» (room 204, straight after EP05's last line)
    // ANIM: Alex turns round from the table to his sister (camera behind her shoulder)
    E6_turn: { desc: 'Alex turns round from the table of phones to face his sister', frames: 16, make(W, t, A) {
      room6(W); const e = t * t * (3 - 2 * t);
      const a = alex6(W, 0.0, ZE - 0.62, 'wide_worried'); a.rotation.y = Math.PI * (1 - e) + 0.05;
      a.userData.headPivot.rotation.y = 0.45 * Math.sin(Math.PI * e); a.userData.headPivot.rotation.x = 0.25 * (1 - e);
      faceTo(sis6(W, -0.34, ZE - 0.2), 0, ZE - 0.62);
      lamp(W, '#b4caff', 0.35, [0.15, 1.45, ZE - 0.2], 1.6); lamp(W, '#ff3a2a', 0.5, [0.0, 2.0, ZE + 0.4], 3.0);
      return camera(50, V(-0.12, 1.6, ZE + 0.6), V(0.02, 1.4, ZE - 0.65), A);
    } },
    // close-up: the sister, seen from Alex (face param for lip-sync); red corridor light behind her through the open door
    E6_sisf: { desc: 'Close-up: the sister by the doorway of room 204, lit by the phones; red light behind her', make(W, t, A) {
      room6(W); const s = sis6(W, SIS[0], SIS[1], W.p.face || 'worried'); faceTo(s, 0.1, ZE - 0.95);
      s.userData.headPivot.rotation.x = 0.04;
      lamp(W, '#b4caff', 0.6, [0.0, 1.15, ZE - 0.85], 1.8); lamp(W, '#ff3a2a', 0.45, [0.1, 2.0, ZE + 0.5], 3.0);
      return camera(36, V(0.18, 1.5, ZE - 1.3), V(SIS[0], 1.52, SIS[1]), A);
    } },
    // ANIM: wide from the side — Alex steps toward her, she steps back, a hand up
    E6_step: { desc: 'Side wide: Alex goes to his sister; she backs away, one hand up', frames: 20, make(W, t, A) {
      room6(W); const e = t * t * (3 - 2 * t);
      const a = alex6(W, 0.0 - 0.12 * e, ZE - 0.62 + 0.18 * e, 'wide_worried'); faceTo(a, -0.3, ZE - 0.2);
      walkPose(a, e * 1.0, 0.35 * Math.sin(Math.PI * e)); a.userData.arms[1].rotation.x = -0.5 * e;
      const k = Math.min(1, Math.max(0, (t - 0.25) / 0.6)), f = k * k * (3 - 2 * k);
      const s = sis6(W, -0.3 - 0.15 * f, ZE - 0.25 + 0.13 * f, 'worried'); faceTo(s, a.position.x, a.position.z);
      walkPose(s, -f * 0.8, 0.25 * Math.sin(Math.PI * f)); const h = s.userData.arms[-1]; h.rotation.x = -1.3 * f; h.rotation.z = -0.15 * f;
      lamp(W, '#b4caff', 0.4, [0.6, 1.4, ZE - 0.6], 2.2); lamp(W, '#ff3a2a', 0.5, [0.0, 2.0, ZE + 0.4], 3.0);
      return camera(52, V(-1.5, 1.6, ZE - 1.75), V(-0.18, 1.36, ZE - 0.35), A);
    } },
    // the sister points at the table of phones; Alex beside her turns to look
    E6_point: { desc: 'The sister points at the table of phones; Alex turns to look', make(W, t, A) {
      room6(W); const s = sis6(W, SIS[0], SIS[1], 'worried'); faceTo(s, 0.2, ZE - 1.85);
      const ar = s.userData.arms[-1]; ar.rotation.x = -1.45; s.userData.headPivot.rotation.y = 0.35;
      lamp(W, '#b4caff', 0.5, [0.1, 1.3, ZE - 1.2], 2.0); lamp(W, '#ff3a2a', 0.45, [0.0, 2.0, ZE + 0.4], 3.0);
      return camera(44, V(-1.35, 1.42, ZE - 1.25), V(-0.3, 1.25, ZE - 0.3), A);
    } },
    // the recording: Alex sitting at THIS table, filmed by a phone propped on it; door 204 open behind him, red corridor
    E6_rec: { desc: 'The recording: Alex at the same table in room 204, filmed from a phone on the table', make(W, t, A) {
      const C = corridorWorld(W, { sconces: 2, open: 1.35, phonesOn: false, fogNear: 6, amb: 0.24 });
      const ch = P.makeChair(); ch.position.set(0.18, 0, ZE - 0.72); ch.rotation.y = Math.PI; W.scene.add(ch);
      const a = alex({ face: W.p.face || 'worried' }); a.position.set(0.18, 0, ZE - 0.72); a.rotation.y = Math.PI; W.scene.add(a);
      faceTo(a, -0.04, ZE - 1.72); P.seatPerson(a); for (const sd of [-1, 1]) { const ar = a.userData.arms[sd]; ar.rotation.x = -1.15; ar.rotation.z = 0; }
      a.userData.headPivot.rotation.x = 0.05;
      lamp(W, '#c9dbff', 0.75, [0.0, 1.05, ZE - 1.35], 1.8);
      return camera(62, V(-0.04, 0.88, ZE - 1.72), V(0.14, 1.08, ZE - 0.7), A);
    } },
    // close-up: Alex at the table, lit from below by the phones (o.red: the countdown)
    E6_alex: { desc: 'Close-up: Alex at the table, lit from below by the phones', make(W, t, A) {
      room6(W, { red: !!W.p.red }); const a = alexAtTable(W); a.userData.headPivot.rotation.x = 0.18;
      lamp(W, W.p.red ? '#ff6a58' : '#b4caff', 0.45, [0.0, 1.05, ZE - 1.2], 1.6);
      return camera(36, V(0.06, 1.3, ZE - 1.9), V(0.0, 1.47, ZE - 0.62), A);
    } },
    // the table in the countdown: every screen red (same framings as EP05's E5_phones_low / E5_room)
    E6_phones_low: { desc: 'Low across the table: rows of phones, every screen red', make(W, t, A) {
      room6(W, { red: !!W.p.red }); return camera(40, V(0.95, 0.98, ZE - 1.22), V(-0.35, 0.76, ZE - 1.95), A);
    } },
    E6_room: { desc: 'POV over the table of phones, every screen red', make(W, t, A) {
      room6(W, { red: !!W.p.red, amb: 0.16 }); return camera(50, V(0.05, 1.62, ZE - 0.45), V(0.0, 0.72, ZE - 1.85), A);
    } },
    // the sister holds a phone up to Alex (third person, by the table)
    E6_show_wide: { desc: 'The sister holds up a second phone to Alex', make(W, t, A) {
      room6(W, { red: !!W.p.red }); const s = sis6(W, SIS2[0], SIS2[1], W.p.face || 'worried'); faceTo(s, 0.05, ZE - 0.45);
      W.screen = sisHoldPhone(W, s, 1.3); lamp(W, W.p.red ? '#ff6a58' : '#b4caff', 0.35, [0.0, 1.3, ZE - 0.6], 2.0);
      return camera(52, V(0.12, 1.48, ZE - 0.22), V(SIS2[0] - 0.12, 1.25, SIS2[1] + 0.1), A);
    } },
    // POV: the phone in her hand, close enough to read; her face behind it
    E6_show: { desc: 'POV: the sister holds a phone right up to Alex; the screen readable, her face behind', phone: true, make(W, t, A) {
      const red = !!W.p.red; room6(W, { red }); if (red) P.room204Wall(W); const s = sis6(W, SIS2[0] + 0.1, SIS2[1] + 0.25, W.p.face || 'worried'); faceTo(s, 0.0, ZE - 0.55);
      s.userData.arms[-1].rotation.x = -0.9;
      lamp(W, red ? '#ff6a58' : '#b4caff', 0.5, [0.0, 1.2, ZE - 0.7], 1.8);
      if (red) lamp(W, '#b9c9d6', 0.35, [0.0, 1.6, ZE - 0.4], 2.0);
      const cam = camera(44, V(0.12, 1.5, ZE - 0.32), V(SIS2[0] + 0.12, 1.47, SIS2[1] + 0.25), A);
      W.screen = sisPhonePOV(W, cam, { glowCol: red ? '#ffb0a8' : '#bcd2ff', z: -0.44, x: 0.05, y: -0.055 }); return cam;
    } },
    // ANIM (k): macro — her hand grabs his wrist at the edge of the table (red light from the phones)
    E6_grab: { desc: 'Across the table: the sister grabs Alex by the arm (red light from the phones)', frames: 12, make(W, t, A) {
      room6(W, { red: true }); const k = W.p.k ?? 1, e = 1 - Math.pow(1 - k, 3);
      const a = alexAtTable(W); a.userData.headPivot.rotation.x = 0.12; a.userData.headPivot.rotation.y = 0.35 * e;
      const s2 = sis6(W, -0.52, ZE - 0.5, 'worried'); faceTo(s2, 0.0, ZE - 0.62);
      const ar = s2.userData.arms[-1]; ar.rotation.x = -1.25 * e; ar.rotation.z = 0.1 * e;
      s2.userData.arms[1].rotation.x = -0.9 * e;
      lamp(W, '#ff6a58', 0.5, [-0.2, 1.05, ZE - 1.3], 1.8);
      return camera(40, V(0.12, 1.45, ZE - 2.45), V(-0.22, 1.25, ZE - 0.55), A);
    } },
    // ANIM: from behind, Alex runs for the open door; the sister reaches after him
    E6_run: { desc: 'From behind: Alex runs for the door of room 204', frames: 20, make(W, t, A) {
      room6(W, { red: true }); const e = t;
      const a = alex6(W, ALEX_M[0] * e, ZE - 1.15 + 0.45 * e, 'wide_worried'); a.rotation.y = 0; walkPose(a, e * 2.2, 0.6);
      const s = sis6(W, SIS2[0], SIS2[1], 'worried'); faceTo(s, a.position.x, a.position.z); s.userData.arms[1].rotation.x = -1.0 * Math.min(1, t * 2);
      lamp(W, '#ff3a2a', 0.5, [0.0, 2.0, ZE + 0.4], 3.0);
      return camera(44, V(0.75, 1.72, ZE - 2.75), V(0.02, 1.15, ZE - 0.1), A);
    } },
    // the same camera: the door is gone — a blank wall (params.mirror: the mirror assembling, k 0..1; old: the old Alex)
    E6_exit: { desc: 'Same camera as E6_run: the doorway is a blank wall / a mirror forms on it', make(W, t, A) {
      room6(W, { red: true }); const a = alex6(W, ALEX_M[0], ALEX_M[1], 'wide_worried'); a.rotation.y = 0;
      a.userData.arms[1].rotation.x = -0.35; a.userData.arms[-1].rotation.x = -0.25;
      faceTo(sis6(W, SIS2[0], SIS2[1], 'worried'), ALEX_M[0], ALEX_M[1]);
      lamp(W, '#b9c9d6', 0.3, [0.0, 1.6, ZE - 0.6], 1.6);
      if (W.p.mirror) P.makeMirror204(W, { k: W.p.k ?? 1, glowX: ALEX_M[0] + 0.5, glow: 0.4 }); else P.room204Wall(W);
      return camera(44, V(0.75, 1.72, ZE - 2.75), V(0.02, 1.15, ZE - 0.1), A);
    } },
    // the mirror from the side, Alex in front of it: (young) his true reflection; (old) the old Alex instead of him
    E6_mirror: { desc: 'Over Alex\'s shoulder at the mirror: his reflection / an old Alex in the glass', make(W, t, A) {
      room6(W, { red: true }); P.makeMirror204(W, { glowX: ALEX_M[0] + 0.5, glow: 0.4 });
      const a = alex6(W, ALEX_M[0], ALEX_M[1], 'wide_worried'); a.rotation.y = 0;
      faceTo(sis6(W, -1.25, ZE - 2.9, 'cold'), ALEX_M[0], ALEX_M[1]);
      const cam = camera(44, V(0.75, 1.62, ZE - 2.0), V(0.0, 1.3, ZE - 0.16), A);
      if (W.p.old) {
        P.cameraOnly(a); cam.layers.enable(2);
        const o = P.mirrorOnly(alex({ face: 'old_worried' })); o.position.set(OLD_M[0], 0, OLD_M[1]); W.scene.add(o);
        o.userData.headPivot.rotation.x = 0.04;
      }
      return cam;
    } },
    // POV in front of the mirror: the old Alex fills the glass (face param for lip-sync; params.palm: hand pressed to the glass)
    E6_old: { desc: 'POV at the mirror: the old Alex in the glass, his palm on it', make(W, t, A) {
      room6(W, { red: true }); const M_ = P.makeMirror204(W, { glowX: OLD_M[0], glowD: 0.22, glow: 0.7 });
      const o = P.mirrorOnly(alex({ face: W.p.face || 'old_worried' })); o.position.set(OLD_M[0], 0, OLD_M[1] + 0.07); W.scene.add(o);
      const k = W.p.palm ?? 1, e = k * k * (3 - 2 * k);
      const ar = o.userData.arms[1]; ar.rotation.x = -1.86 * e;
      if (k >= 0.999) { const h = P.mirrorOnly(P.makeOpenHand(false)); h.position.set(OLD_M[0] + 0.3, 1.43, M_.z - 0.016); W.scene.add(h); }
      lamp(W, '#b9c9d6', 0.25, [OLD_M[0] + 0.3, 1.45, M_.z - 0.2], 0.8);
      W.scene.updateMatrixWorld(true);
      return camera(50, V(OLD_M[0] + 0.17, 1.5, ZE - 1.1), V(OLD_M[0] + 0.17, 1.44, M_.z), A);
    } },
    // ANIM: Alex turns from the mirror back to the room (the old Alex stays in the glass behind him, palm on it)
    E6_turn_back: { desc: 'Alex turns slowly from the mirror back to the room; the old Alex stays in the glass', frames: 16, make(W, t, A) {
      room6(W, { red: true }); P.makeMirror204(W, { glowX: ALEX_M[0] + 0.5, glow: 0.4 }); const e = t * t * (3 - 2 * t);
      const a = alex6(W, ALEX_M[0], ALEX_M[1], 'wide_worried'); a.rotation.y = Math.PI * e; P.cameraOnly(a);
      a.userData.headPivot.rotation.y = -0.4 * Math.sin(Math.PI * e);
      const o = P.mirrorOnly(alex({ face: 'old_worried' })); o.position.set(OLD_M[0], 0, OLD_M[1] + 0.07); W.scene.add(o);
      o.userData.arms[1].rotation.x = -1.86;
      const h = P.mirrorOnly(P.makeOpenHand(false)); h.position.set(OLD_M[0] + 0.3, 1.43, ZE - 0.165 - 0.016); W.scene.add(h);
      lamp(W, '#ff6a58', 0.35, [ALEX_M[0], 1.2, ZE - 1.3], 1.8);
      const cam = camera(44, V(0.35, 1.7, ZE - 2.6), V(-0.1, 1.3, ZE - 0.3), A); cam.layers.enable(2); return cam;
    } },
    // close-up: the sister no longer smiles (cold face), cold mirror light in front, red phone light behind (params.phone)
    E6_sis_cold: { desc: 'Close-up: the sister, no longer smiling; (phone) a phone in her hand', make(W, t, A) {
      room6(W, { red: true }); P.room204Wall(W); const s = sis6(W, SIS2[0], SIS2[1], 'cold'); faceTo(s, ALEX_M[0], ALEX_M[1]);
      lamp(W, '#b9c9d6', 0.6, [-0.1, 1.55, ZE - 0.55], 2.0);
      if (W.p.phone) { W.screen = sisHoldPhone(W, s, 1.3); return camera(54, V(0.3, 1.45, ZE - 0.3), V(SIS2[0] - 0.3, 1.22, SIS2[1] + 0.32), A); }
      return camera(38, V(0.3, 1.52, ZE - 0.3), V(SIS2[0], 1.52, SIS2[1]), A);
    } },
    // portrait of Alex for the choice screen (same style as the EP04 photo of his sister: warm room light, plain wall)
    E6_alex_portrait: { desc: 'Portrait of Alex for the final choice screen', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#6d5242');
      const a = alex(); W.scene.add(a); a.userData.headPivot.rotation.x = 0.03;
      W.scene.add(new THREE.HemisphereLight('#ffe2c4', '#3a2a20', 0.9)); const d = new THREE.DirectionalLight('#ffd2a0', 1.4); d.position.set(1.5, 2.5, 3); W.scene.add(d);
      return camera(22, V(0, 1.56, 1.7), V(0, 1.5, 0), A);
    } },

    // ======================= EP07 «ТОТ, КОГО СТЁРЛИ» (room 204, the same second EP06 ended on)
    // POV: Alex's own phone in his hand shows the same choice + 5 seconds; the sister in front of him, red light
    E7_phone_pov: { desc: 'POV: Alex\'s phone — the choice and the last five seconds; the sister in front of him', phone: true, make(W, t, A) {
      room7(W, { lit: true, mirror: 'none' });
      const s = sis6(W, -0.42, ZE - 1.75, 'cold'); faceTo(s, ALEX_M[0], ALEX_M[1]);
      lamp(W, '#ff6a58', 0.4, [-0.2, 1.3, ZE - 1.2], 1.8);
      const cam = camera(58, V(ALEX_M[0], 1.6, ALEX_M[1] + 0.05), V(-0.38, 1.38, ZE - 1.75), A);
      W.screen = povPhone(W.scene, cam, { screen: '#ffb0a8', x: 0.03, y: -0.05, z: -0.34, glow: 1.2 }); return cam;
    } },
    // ANIM (k): the same POV — she reaches for his phone
    E7_reach: { desc: 'POV: the sister reaches for the phone in Alex\'s hand', frames: 14, make(W, t, A) {
      room7(W, { lit: true, mirror: 'none' }); const k = W.p.k ?? 1, e = k * k * (3 - 2 * k);
      const s = sis6(W, -0.42 + 0.12 * e, ZE - 1.75 + 0.45 * e, 'cold'); faceTo(s, ALEX_M[0], ALEX_M[1]);
      const ar = s.userData.arms[-1]; ar.rotation.x = -0.2 - 1.4 * e; ar.rotation.z = 0.3 * e;
      lamp(W, '#ff6a58', 0.4, [-0.2, 1.3, ZE - 1.2], 1.8);
      const cam = camera(58, V(ALEX_M[0], 1.6, ALEX_M[1] + 0.05), V(-0.38, 1.38, ZE - 1.75), A);
      W.screen = povPhone(W.scene, cam, { screen: '#ffb0a8', x: 0.03, y: -0.05, z: -0.34, glow: 1.2 }); return cam;
    } },
    // close-up: the sister, cold, says «Выбирай себя…» (lip-sync stills by face), red phone light under her face
    E7_sisc: { desc: 'Close-up: the sister, cold, red light from the phones', make(W, t, A) {
      room7(W, { lit: true, mirror: 'none' }); const s = sis6(W, SIS2[0], SIS2[1], W.p.face || 'cold'); faceTo(s, ALEX_M[0], ALEX_M[1]);
      lamp(W, '#ff6a58', 0.5, [SIS2[0] + 0.25, 1.1, SIS2[1] + 0.35], 1.4); lamp(W, '#b9c9d6', 0.35, [-0.1, 1.6, ZE - 0.45], 2.0);
      return camera(48, V(0.22, 1.52, ZE - 0.38), V(SIS2[0], 1.5, SIS2[1]), A);
    } },
    // ANIM: low on the floor — the phone falls into frame, hits the floor and bounces (its screen still lit)
    E7_throw: { desc: 'Floor level: Alex throws the phone down; it smacks onto the floor and bounces', frames: 20, make(W, t, A) {
      room7(W, { lit: true, mirror: 'none' });
      const a = alex6(W, ALEX_M[0], ALEX_M[1] - 0.25, 'wide_worried'); a.rotation.y = Math.PI; a.userData.arms[1].rotation.x = -0.6 * (1 - t);
      const ph = P.makePhone('#ffb0a8'); W.scene.add(ph); W.screen = ph.getObjectByName('screen');
      const px = -0.12, pz = ZE - 1.2;
      let y, rx, rz;
      if (t < 0.7) { const u = t / 0.7; y = 1.05 * (1 - u * u) + 0.006; rx = -Math.PI / 2 + 1.8 * (1 - u); rz = 0.9 * (1 - u); }
      else { const u = (t - 0.7) / 0.3; y = 0.006 + 0.07 * Math.sin(Math.PI * Math.min(1, u / 0.55)) * (u < 0.55 ? 1 : 0); rx = -Math.PI / 2 + 0.25 * Math.sin(Math.PI * Math.min(1, u / 0.55)) * (u < 0.55 ? 1 : 0); rz = 0.3 * u; }
      ph.position.set(px, y, pz); ph.rotation.set(rx, 0, rz);
      lamp(W, '#ff8a7a', 0.25, [px, 0.15, pz], 0.7);
      return camera(48, V(0.32, 0.12, ZE - 1.75), V(-0.15, 0.22, ZE - 1.0), A);
    } },
    // top-down macro: the phone on the floor, glass cracked, the last seconds
    E7_floor_phone: { desc: 'Top-down macro: the phone on the floor of room 204, the countdown on its cracked screen', phone: true, make(W, t, A) {
      room7(W, { lit: true, mirror: 'none' });
      const ph = P.makePhone('#ffb0a8'); ph.position.set(-0.12, 0.006, ZE - 1.2); ph.rotation.set(-Math.PI / 2, 0, 0.3); W.scene.add(ph); W.screen = ph.getObjectByName('screen');
      lamp(W, '#ff8a7a', 0.4, [-0.12, 0.12, ZE - 1.2], 0.8);
      const c = new THREE.PerspectiveCamera(30, A, 0.01, 60); c.position.set(-0.1, 0.5, ZE - 1.15); c.up.set(Math.sin(0.3), 0, -Math.cos(0.3)); c.lookAt(V(-0.12, 0.0, ZE - 1.2)); return c;
    } },
    // POV over the table: every screen dead, the room dark (the same framing as EP06's E6_room)
    E7_room_dark: { desc: 'POV over the table: every phone dead, the room dark but for the mirror\'s cold light', make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 0, glow: 1.1 }); P.box(0.001, 0.001, 0.001, P.M('#000'), 0, -5, 0, W.scene);
      lamp(W, '#9fb6c8', 0.5, [0.05, 1.7, ZE - 0.3], 2.4);
      return camera(50, V(0.05, 1.62, ZE - 0.45), V(0.0, 0.72, ZE - 1.85), A);
    } },
    // ANIM (k): the sister dissolves into cubes, a dead phone in her hand
    E7_sis_vanish: { desc: 'The sister falls apart into blinking cubes and is gone', frames: 18, make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 0, glow: 1.0 }); const k = W.p.k ?? 1;
      const s = sis6(W, SIS2[0], SIS2[1], 'cold'); faceTo(s, ALEX_M[0], ALEX_M[1]);
      const a = s.userData.arms[-1]; a.rotation.x = -1.05 * 1.3; a.rotation.z = 0.18 * 1.3;
      const ph = P.makePhone('#0b0e13'); ph.position.set(0, -0.6, 0.06); ph.rotation.x = 1.05 * 1.3 - 0.25; a.add(ph);
      P.dissolve(s, k, { a: -1.9, b: 0.0, cell: 26, sweep: 0.8, dir: V(0, -1, 0) });   // head first, feet last
      lamp(W, '#b9c9d6', 0.55, [-0.1, 1.55, ZE - 0.55], 2.0); if (k > 0 && k < 1) lamp(W, '#5fe6ff', 0.6 * Math.sin(Math.PI * k), [SIS2[0], 1.2, SIS2[1] + 0.3], 1.6);
      return camera(60, V(0.3, 1.5, ZE - 0.3), V(SIS2[0] - 0.05, 1.12, SIS2[1]), A);
    } },
    // the mirror from the front: the old Alex in the glass, Alex's back at the edge of frame; the text quad for «Выбор сделан»
    E7_mirror_front: { desc: 'The mirror, almost head-on: the old Alex in the glass where Alex\'s reflection should be', make(W, t, A) {
      const M_ = room7(W, { mirror: W.p.crack ? 'cracked' : 'whole', crack: W.p.crack, glow: 1.0 });
      const a = alex6(W, ALEX_M[0] - 0.05, ALEX_M[1] - 0.45, 'wide_worried'); a.rotation.y = 0.1; P.cameraOnly(a);
      oldInMirror(W, { face: 'old_worried' });
      const ref = W.objs.reflector; W.quad = { obj: ref, hw: 0.43, hh: 0.93 };
      return cam7(40, V(0.32, 1.42, ZE - 2.0), V(-0.02, 1.18, M_.z), A);
    } },
    // close-up: Alex in the dark, lit by the mirror (lip-sync stills by face). params.shatter: the mirror is gone, the
    // monitors behind it light him (cold; red with params.red)
    E7_alexd: { desc: 'Close-up: Alex facing the mirror, lit by its cold light (or by the monitors behind it)', make(W, t, A) {
      let opsCam = null;
      if (W.p.shatter) { const O = opsFeed(W, { face: 'cold' }); opsCam = O.cam; }
      room7(W, W.p.shatter ? { mirror: 'shattered', k: 1, feedCam: opsCam, red: !!W.p.red } : { mirror: 'cracked', crack: W.p.crack ?? 0, glow: 1.1 });
      const a = alex6(W, ALEX_M[0], ALEX_M[1] - (W.p.back ? 0.35 : 0), W.p.face || 'wide_worried'); a.rotation.y = 0; P.cameraOnly(a);
      a.userData.headPivot.rotation.x = -0.04;
      lamp(W, W.p.shatter ? (W.p.red ? '#ff5a48' : '#8fc8ff') : '#b9c9d6', W.p.shatter ? 0.9 : 0.55, [ALEX_M[0] + 0.1, 1.6, ALEX_M[1] + 0.35], 1.4);
      const z = a.position.z;
      return cam7(56, V(ALEX_M[0] + 0.32, 1.6, z + 0.78), V(ALEX_M[0], 1.52, z), A);
    } },
    // ANIM: POV at the mirror — the old Alex draws back and punches the glass; it cracks round his fist
    E7_punch: { desc: 'POV at the mirror: the old Alex punches the glass from inside; it cracks', frames: 16, make(W, t, A) {
      const crack = Math.max(0, Math.min(1, (t - 0.72) / 0.22));
      const M_ = room7(W, { mirror: crack > 0 ? 'cracked' : 'whole', crack, glowX: OLD_M[0], glowD: 0.3, glow: 0.45 });
      oldInMirror(W, { near: true, fist: t, face: t > 0.5 ? 'old_worried_open' : 'old_worried' });
      lamp(W, '#b9c9d6', 0.3, [OLD_M[0] + 0.3, 1.45, M_.z - 0.2], 0.8);
      return cam7(50, V(OLD_M[0] + 0.17, 1.5, ZE - 1.1), V(OLD_M[0] + 0.17, 1.44, M_.z), A);
    } },
    // POV at the cracked mirror: the old Alex behind the cracks (lip-sync stills by face); params.point: he points down
    E7_oldc: { desc: 'POV at the cracked mirror: the old Alex behind the cracks', make(W, t, A) {
      const M_ = room7(W, { mirror: 'cracked', crack: 1, glowX: OLD_M[0], glowD: 0.3, glow: 0.45 });
      oldInMirror(W, { near: true, face: W.p.face || 'old_worried', point: !!W.p.point });
      lamp(W, '#b9c9d6', 0.3, [OLD_M[0] + 0.3, 1.45, M_.z - 0.2], 0.8);
      if (W.p.point) return cam7(50, V(OLD_M[0] + 0.12, 1.42, ZE - 1.3), V(OLD_M[0] + 0.1, 1.25, M_.z), A);
      return cam7(50, V(OLD_M[0] + 0.17, 1.5, ZE - 1.1), V(OLD_M[0] + 0.17, 1.44, M_.z), A);
    } },
    // ANIM: over his shoulder — Alex backs away from the cracked mirror; the old Alex stays in the glass
    E7_step_back: { desc: 'Alex backs away from the cracked mirror; the old Alex stays in it', frames: 16, make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 1, glow: 0.9 }); const e = t * t * (3 - 2 * t);
      const a = alex6(W, ALEX_M[0], ALEX_M[1] - 0.38 * e, 'wide_worried'); a.rotation.y = 0; P.cameraOnly(a); walkPose(a, -e * 0.9, 0.3 * Math.sin(Math.PI * e));
      oldInMirror(W, {});
      return cam7(44, V(0.75, 1.62, ZE - 2.0), V(0.0, 1.3, ZE - 0.16), A);
    } },
    // MACRO (num 0..1): Alex's left inner wrist; under the EP04 scar the number 48 surfaces pixel by pixel
    E7_wrist: { desc: 'Macro: Alex\'s inner wrist — the number 48 surfaces under the scar', frames: 16, make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 1, glow: 0.9 });
      const cam = cam7(40, V(-0.25, 1.25, ZE - 0.95), V(-0.25, 0.95, ZE - 1.6), A);
      wristRig(W, cam, { num: W.p.num ?? 1, light: 0.55 }); return cam;
    } },
    // MACRO (rub 0..1): his right thumb scrubs at the digits
    E7_wrist_rub: { desc: 'Macro: Alex tries to rub the number off with his other hand', frames: 16, make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 1, glow: 0.9 });
      const cam = cam7(40, V(-0.25, 1.25, ZE - 0.95), V(-0.25, 0.95, ZE - 1.6), A);
      wristRig(W, cam, { num: 1, light: 0.55 });
      const r = W.p.rub ?? 0, sw = Math.sin(r * Math.PI * 6) * 0.045;
      const h = P.makeForearm({ scar: false, grip: 0.35 }); h.position.set(0.25 + sw, -0.33, -0.9); h.rotation.set(0.0, 0.0, -2.62 + sw * 1.5); cam.add(h);
      return cam;
    } },
    // MACRO (clear 0..1): the skin goes clear over blocky wires
    E7_wrist_clear: { desc: 'Macro: the skin of his forearm turns clear — wires inside', frames: 16, make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 1, glow: 0.9 });
      const c = W.p.clear ?? 1, z = W.p.close ? -0.78 : -0.95;
      const cam = cam7(40, V(-0.25, 1.25, ZE - 0.95), V(-0.25, 0.95, ZE - 1.6), A);
      wristRig(W, cam, { num: 1, clear: c, z, light: 0.55 }); return cam;
    } },
    // close-up: Alex looks down at his arm, pale; cyan light from below (the wires)
    E7_realize: { desc: 'Close-up: Alex stares down at his own arm, pale, lit from below by a cyan glow', make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 1, glow: 0.7 });
      const a = alex6(W, ALEX_M[0], ALEX_M[1] - 0.38, 'wide_worried_down_pale'); a.rotation.y = 0; P.cameraOnly(a);
      a.userData.headPivot.rotation.x = 0.42; a.userData.arms[-1].rotation.x = -0.8; a.userData.arms[-1].rotation.z = 0.3;
      lamp(W, '#6fe8ff', 0.45, [ALEX_M[0] + 0.05, 1.05, ALEX_M[1] - 0.25], 0.9);
      const z = ALEX_M[1] - 0.38;
      return cam7(56, V(ALEX_M[0] + 0.28, 1.18, z + 0.7), V(ALEX_M[0], 1.5, z), A);
    } },
    // wide: Alex alone in the dark room, the cracked mirror, the dead table; where she stood — nothing
    E7_wide_copy: { desc: 'Wide: Alex alone in dark room 204 before the cracked mirror, a cyan glow at his wrist', make(W, t, A) {
      room7(W, { mirror: 'cracked', crack: 1, glow: 0.9 });
      const a = alex6(W, ALEX_M[0], ALEX_M[1] - 0.38, 'wide_worried_down_pale'); a.rotation.y = 0; P.cameraOnly(a);
      a.userData.headPivot.rotation.x = 0.35; a.userData.arms[-1].rotation.x = -1.2; a.userData.arms[-1].rotation.z = 0.35;
      lamp(W, '#6fe8ff', 0.5, [ALEX_M[0] - 0.05, 1.05, ALEX_M[1] - 0.6], 1.0);
      oldInMirror(W, {});
      return cam7(50, V(1.35, 2.15, ZE - 2.75), V(-0.2, 1.0, ZE - 0.4), A);
    } },
    // ANIM (k): from behind Alex — the mirror bursts; behind it, a room full of monitors
    E7_shatter: { desc: 'From behind Alex: the mirror bursts into the room; behind it a wall of monitors', frames: 18, make(W, t, A) {
      const k = W.p.k ?? 1; let opsCam = null;
      if (k > 0) { const O = opsFeed(W, { face: 'cold' }); opsCam = O.cam; }
      room7(W, k > 0 ? { mirror: 'shattered', k, feedCam: opsCam } : { mirror: 'cracked', crack: 1, glow: 0.9 });
      const a = alex6(W, ALEX_M[0], ALEX_M[1] - 0.38 - 0.12 * Math.min(1, k * 3), 'wide_worried'); a.rotation.y = 0; P.cameraOnly(a);
      a.userData.arms[1].rotation.x = -0.9 * Math.min(1, k * 3); a.userData.arms[-1].rotation.x = -0.9 * Math.min(1, k * 3);
      if (k <= 0) oldInMirror(W, {});
      if (k > 0) lamp(W, '#cfe6ff', 1.4 * Math.max(0, 1 - k * 2), [0.0, 1.4, ZE - 0.4], 2.5);
      return cam7(44, V(0.55, 1.62, ZE - 2.55), V(0.0, 1.2, ZE - 0.1), A);
    } },
    // POV through the empty mirror frame: the monitor room, the sister live on the big centre screen
    E7_reveal: { desc: 'POV through the broken mirror frame: a dark room with a wall of monitors; the sister on the big one', make(W, t, A) {
      const O = opsFeed(W, { face: 'cold' }); room7(W, { mirror: 'shattered', k: 1, feedCam: O.cam });
      return cam7(48, V(-0.08, 1.55, ZE - 0.85), V(0.0, 1.35, ZE + 3.0), A);
    } },
    // closer: the big centre monitor — the sister at her computer, looking straight into the lens
    E7_monitor_sis: { desc: 'In the monitor room: the big centre monitor shows the sister at her computer', make(W, t, A) {
      const O = opsFeed(W, { face: W.p.face || 'cold' }); room7(W, { mirror: 'shattered', k: 1, feedCam: O.cam });
      return cam7(40, V(0.08, 1.4, ZE + 1.25), V(0.0, 1.38, ZE + 3.2), A);
    } },
    // the feed itself, full frame: her webcam (lip-sync stills by face; params.lean 0..1 she leans to the microphone)
    E7_feed: { desc: 'Her webcam: the sister at her computer in a dark room of server racks, looking into the lens', make(W, t, A) {
      W.scene.background = new THREE.Color('#05070a');
      const O = opsFeed(W, { face: W.p.face || 'cold', lean: W.p.lean ?? 0, fov: 64 }); O.cam.aspect = A; O.cam.updateProjectionMatrix();
      if (W.p.close) { const G = O.G; O.cam.fov = 60; O.cam.updateProjectionMatrix(); O.cam.position.copy(G.localToWorld(V(-0.08, 1.33, 0.83))); O.cam.lookAt(G.localToWorld(V(-0.1, 1.12, 0.3))); }
      return O.cam;
    } },
    // ANIM (press 0..1): macro — her finger comes down on the red console button
    E7_press: { desc: 'Macro: the sister\'s finger presses the red button on her desk', frames: 12, make(W, t, A) {
      const k = W.p.press ?? 1, e = k < 0.6 ? 0 : Math.min(1, (k - 0.6) / 0.25), d = 1 - Math.min(1, k / 0.6);
      const O = opsFeed(W, { face: 'cold', press: e }); const G = O.G;
      const hand = new THREE.Group(); G.add(hand); const skin = P.M(P.PAL.skinAlex);
      hand.position.set(0.33, 0.9 + 0.1 * d - 0.012 * e, 0.42 - 0.08 * d); hand.rotation.x = 0.25;
      P.box(0.1, 0.035, 0.1, skin, 0, 0.0, -0.03, hand);                                     // back of the hand
      P.box(0.024, 0.06, 0.024, skin, 0.0, -0.035, 0.03, hand);                              // the index finger, down on the button
      for (const x of [-0.03, 0.03]) P.box(0.022, 0.035, 0.05, skin, x, -0.02, 0.005, hand);  // curled fingers
      P.box(0.12, 0.1, 0.3, P.M(P.PAL.sweater), 0, 0.03, -0.22, hand).rotation.x = -0.35;   // her sleeve
      const lb = new THREE.PointLight('#ffb0a0', 0.6 + 0.8 * e, 1.0, 1.6); lb.position.copy(G.localToWorld(V(0.33, 1.0, 0.65))); W.scene.add(lb);
      return camera(40, G.localToWorld(V(0.62, 1.08, 0.8)), G.localToWorld(V(0.32, 0.85, 0.46)), A);
    } },
    // the monitor wall head-on (the editor draws the deletion message on every screen)
    E7_wall: { desc: 'In the monitor room: the whole wall of monitors head-on', make(W, t, A) {
      const O = opsFeed(W, { face: 'cold' }); room7(W, { mirror: 'shattered', k: 1, feedCam: O.cam, red: !!W.p.red });
      W.screens = W.objs.monitorRoom.screens;
      return cam7(52, V(0.0, 1.42, ZE + 0.7), V(0.0, 1.4, ZE + 3.2), A);
    } },
    // one monitor, close enough to read (the editor draws the message / the address on it)
    E7_mon: { desc: 'Close: one monitor in the monitor room, its screen readable', phone: true, make(W, t, A) {
      const O = opsFeed(W, { face: 'cold' }); room7(W, { mirror: 'shattered', k: 1, feedCam: O.cam, red: !!W.p.red });
      const scr = W.objs.monitorRoom.screens[0]; scr.material = new THREE.MeshBasicMaterial({ color: '#101820' }); W.screen = scr;
      return cam7(36, V(0.0, 1.38, ZE + 1.4), V(0.0, 1.38, ZE + 3.2), A);
    } },
    // MACRO (k): his left hand and forearm come apart into cubes, from the fingertips up; red light from the monitors
    E7_hand_vanish: { desc: 'Macro: Alex\'s left hand dissolves into blinking cubes, fingers first', frames: 16, make(W, t, A) {
      const O = opsFeed(W, { face: 'cold' }); room7(W, { mirror: 'shattered', k: 1, feedCam: O.cam, red: true });
      const cam = cam7(40, V(-0.25, 1.3, ZE - 1.05), V(-0.2, 1.25, ZE + 0.5), A);
      const a = wristRig(W, cam, { num: 1, clear: 1, light: 0.5, lightCol: '#ff8a7a' });
      W.scene.updateMatrixWorld(true);
      const k = W.p.k ?? 1, tip = a.localToWorld(V(0, -0.58, 0)), root = a.localToWorld(V(0, -0.05, 0)), d = root.clone().sub(tip).normalize();
      P.dissolve(a, k, { dir: d, a: tip.dot(d), b: root.dot(d), cell: 60, sweep: 1.0, glow: '#5fe6ff' });
      return cam;
    } },

    // ======================= EP08 «ЗАВТРАШНИЙ ДЕНЬ» (the monitor room, the same second EP07 ended on; then flat 47)
    // the centre monitor, close (E7_mon framing). params.feed: 'ui' (the editor draws the address / the deletion screen),
    // 'sis' (the sister live), 'rec' (tomorrow's recording, params.rec = view), 'black'; params.crack, params.red, params.k (collapse)
    E8_mon: { desc: 'Close: the centre monitor in the monitor room (address / sister / recording / deletion)', phone: true, make(W, t, A) {
      const mode = W.p.feed || 'ui'; let fc = null;
      if (mode === 'sis') fc = opsFeed(W, { face: W.p.face || 'cold' }).cam;
      if (mode === 'rec') { recCast(W, { k: 1 }); fc = recCam(W.p.rec || 'wide', 1.6); }
      const R = room8(W, { feedCam: fc, red: !!W.p.red, k: W.p.k, keepAll: true });
      const scr = R.screens[0];
      if (mode === 'ui' || mode === 'black') scr.material = new THREE.MeshBasicMaterial({ color: mode === 'ui' ? '#101820' : '#020304' });
      if (W.p.crack) P.monitorCracks(scr, { k: W.p.crack });
      W.screen = scr;
      return cam7(36, V(0.0, 1.38, ZE + 1.4), V(0.0, 1.38, ZE + 3.2), A);
    } },
    // ANIM (k): macro, ALEX_48's left hand keeps coming apart (EP07's dissolve, further along), monitor light
    E8_hand: { desc: 'Macro in the monitor room: ALEX_48\'s left hand keeps dissolving into cubes', frames: 14, make(W, t, A) {
      room8(W, {});
      const cam = cam7(40, V(MON_A[0] - 0.1, 1.3, MON_A[1] - 0.05), V(MON_A[0] - 0.05, 1.25, MON_A[1] + 1.8), A);
      const a = wristRig(W, cam, { num: 1, clear: 1, light: 0.55, lightCol: '#8fc8ff' });
      W.scene.updateMatrixWorld(true);
      const k = 0.34 + 0.2 * (W.p.k ?? 1), tip = a.localToWorld(V(0, -0.58, 0)), root = a.localToWorld(V(0, -0.05, 0)), d = root.clone().sub(tip).normalize();
      P.dissolve(a, k, { dir: d, a: tip.dot(d), b: root.dot(d), cell: 60, sweep: 1.0, glow: '#5fe6ff' });
      return cam;
    } },
    // ALEX_48 in the monitor room, lit by the monitors, the broken mirror frame behind him (lip-sync stills by face);
    // params.close: tighter; params.red: the alarm light
    E8_alexm: { desc: 'ALEX_48 in the monitor room facing the screens; the empty mirror frame behind him', make(W, t, A) {
      room8(W, { red: !!W.p.red, k: W.p.k, dim: 0.35 });
      const a = alex48(W, MON_A[0], MON_A[1], W.p.face || 'wide_worried'); a.rotation.y = 0; a.userData.headPivot.rotation.x = -0.05;
      a.userData.arms[-1].rotation.x = -0.35; a.userData.arms[-1].rotation.z = 0.2; vanishLeft(W, a, 0.5);
      lamp(W, W.p.red ? '#ff5a48' : '#8fc8ff', 0.32, [MON_A[0] + 0.18, 1.62, MON_A[1] + 0.75], 1.6);
      if (W.p.close) return cam7(46, V(MON_A[0] + 0.2, 1.58, MON_A[1] + 0.62), V(MON_A[0], 1.53, MON_A[1]), A);
      return cam7(52, V(MON_A[0] + 0.32, 1.62, MON_A[1] + 0.85), V(MON_A[0], 1.48, MON_A[1]), A);
    } },
    // ANIM: her webcam — the sister shakes her head (close feed framing)
    E8_feed_shake: { desc: 'Her webcam: the sister slowly shakes her head', frames: 16, make(W, t, A) {
      W.scene.background = new THREE.Color('#05070a');
      const O = opsFeed(W, { face: 'cold', fov: 60 }); const G = O.G;
      O.s.userData.headPivot.rotation.y = 0.3 * Math.sin(Math.PI * 2 * 1.5 * t) * Math.sin(Math.PI * t);
      O.cam.aspect = A; O.cam.fov = 60; O.cam.updateProjectionMatrix(); O.cam.position.copy(G.localToWorld(V(-0.08, 1.33, 0.83))); O.cam.lookAt(G.localToWorld(V(-0.1, 1.12, 0.3)));
      return O.cam;
    } },
    // the security camera of flat 47, "tomorrow": params.view 'wide' | 'door' | 'knife' | 'two' (ANIM k: ALEX_ORIGINAL walks in) |
    // 'plead' (ANIM: over the knife's shoulder, he pleads, half a step back); params.empty: nobody there yet
    E8_rec: { desc: 'Flat 47\'s security camera, tomorrow: ALEX_48 by the front door with a knife, the other Alex facing him', make(W, t, A) {
      world8(W, {}); P.buildKitchen(W, { glass: 'table', lamp: 1.6 });
      const v = W.p.view || 'wide';
      if (!W.p.empty) recCast(W, { other: v !== 'door' && v !== 'knife', k: v === 'two' ? (W.p.k ?? 1) : 1, back: v === 'plead' ? 0.18 * (W.p.k ?? 0) : 0, shake: v === 'plead' ? (W.p.k ?? 0) + 0.01 : 0 });
      return recCam(v === 'two' ? 'wide' : v, A);
    } },
    // ANIM: POV — ALEX_48's right fist smashes into the centre monitor (the recording on it); the screen cracks
    E8_punch_mon: { desc: 'POV: ALEX_48 punches the centre monitor; the screen cracks over the recording', frames: 16, make(W, t, A) {
      recCast(W, { k: 1 }); const fc = recCam('plead', 1.6);
      const R = room8(W, { feedCam: fc }); const scr = R.screens[0];
      const crack = Math.max(0, Math.min(1, (t - 0.62) / 0.16)); if (crack > 0) P.monitorCracks(scr, { k: crack });
      const cpos = V(0.03, 1.45, MON_Z - 1.0), target = V(0.08, 1.42, MON_Z - 0.03), rest = V(0.22, 1.12, MON_Z - 0.55), back = V(0.3, 1.2, MON_Z - 0.78);
      let h; if (t < 0.35) h = rest.clone().lerp(back, t / 0.35); else if (t < 0.62) { const u = (t - 0.35) / 0.27; h = back.clone().lerp(target, u * u); } else h = target.clone().lerp(V(0.1, 1.38, MON_Z - 0.12), Math.min(1, (t - 0.62) / 0.38) * 0.6);
      longArm(W, h, V(0.42, 0.85, MON_Z - 1.45));
      lamp(W, '#8fc8ff', 0.8, [0.0, 1.5, MON_Z - 0.5], 1.5);
      return cam7(46, cpos, V(0.0, 1.38, MON_Z), A);
    } },
    // ANIM (k): the floor shakes — the monitor room starts to be deleted round ALEX_48 (wide, from the corner)
    E8_quake: { desc: 'Wide: the monitor room comes apart into cubes round ALEX_48; blocks drop from the ceiling', frames: 18, make(W, t, A) {
      const O = opsFeed(W, { face: 'cold' });
      const k = 0.08 + 0.42 * (W.p.k ?? 1); room8(W, { feedCam: O.cam, k });
      const a = alex48(W, MON_A[0], MON_A[1], 'wide_worried_open'); a.rotation.y = 0.5; const s = Math.sin(t * 30);
      a.userData.arms[1].rotation.z = -0.6 - 0.1 * s; a.userData.arms[-1].rotation.z = 0.6 + 0.1 * s; a.userData.legL.rotation.x = 0.2 * s; a.position.x += 0.03 * s;
      vanishLeft(W, a, 0.52);
      return cam7(56, V(1.25, 2.05, ZE + 0.35), V(-0.1, 1.05, MON_Z), A);
    } },
    // the monitor wall head-on while the room comes apart (the editor draws the timer on every screen); params.k
    E8_wall: { desc: 'The monitor wall head-on, red, the room breaking up round it', make(W, t, A) {
      const R = room8(W, { red: true, k: W.p.k ?? 0.55, keepAll: true });
      W.screens = R.screens;
      return cam7(52, V(0.0, 1.42, ZE + 0.7), V(0.0, 1.4, ZE + 3.2), A);
    } },
    // ANIM: from the desk — ALEX_48 runs back to the empty mirror frame; debris falls; room 204 dark behind the frame
    E8_run: { desc: 'ALEX_48 runs from the monitors back to the broken mirror frame while the room collapses', frames: 18, make(W, t, A) {
      const k = 0.62 + 0.15 * t; room8(W, { red: true, k });
      const e = t * t * (3 - 2 * t), a = alex48(W, -0.32 + 0.22 * e, MON_A[1] - 0.25 - 1.3 * e, 'wide_worried'); a.rotation.y = Math.PI;
      walkPose(a, t * 3.2, 0.7); vanishLeft(W, a, 0.56);
      lamp(W, '#cfe6ff', 0.5, [0.0, 1.8, ZE + 0.2], 1.8); lamp(W, '#9fb6c8', 0.9, [0.0, 1.2, ZE - 0.5], 1.6);   // the frame reads: room 204 still behind it
      return cam7(50, V(0.62, 1.72, MON_A[1] + 1.0), V(0.0, 1.1, ZE - 0.3), A);
    } },
    // ANIM (k): over ALEX_48's shoulder at the frame — room 204 comes apart into cubes and flat 47's front door assembles
    // in its place (same deletion language, run the other way)
    E8_portal: { desc: 'Over ALEX_48\'s shoulder: room 204 behind the frame dissolves and flat 47\'s front door assembles there', frames: 18, make(W, t, A) {
      const k = W.p.k ?? 1; room8(W, { red: true, k: 0.78 });
      P.flatBehindMirror(W, { k204: Math.min(1, k * 1.25), k: Math.max(0, Math.min(1, (k - 0.15) / 0.8)), ajar: 0.0 });
      const a = alex48(W, 0.4, ZE + 0.75, 'wide_worried'); a.rotation.y = Math.PI - 0.25; vanishLeft(W, a, 0.58);
      lamp(W, '#ff5a48', 0.5, [0.2, 1.9, ZE + 1.0], 1.6); lamp(W, '#9fb6c8', 0.9 * (1 - (W.p.k ?? 1)), [0.0, 1.2, ZE - 0.5], 1.6);
      return cam7(44, V(0.12, 1.66, ZE + 2.55), V(-0.03, 1.1, ZE - 0.5), A);
    } },
    // ANIM (ajar): flat 47's front door behind the frame, from the landing side; it swings open onto the warm entryway
    E8_door: { desc: 'Flat 47\'s front door stands behind the empty mirror frame and swings open onto the warm entryway', frames: 14, make(W, t, A) {
      room8(W, { red: true, k: 0.8 });
      P.flatBehindMirror(W, { ajar: 0.04 + 1.2 * (W.p.ajar ?? 1) });
      return cam7(46, V(-0.06, 1.5, ZE + 1.95), V(0.0, 1.1, ZE - 0.5), A);
    } },
    // ANIM: from behind ALEX_48 — he steps through the frame and the open door into the flat; the room behind falls apart
    E8_step_in: { desc: 'From behind: ALEX_48 steps through the frame and the open door into flat 47', frames: 18, make(W, t, A) {
      room8(W, { red: true, k: 0.82 + 0.12 * t });
      P.flatBehindMirror(W, { ajar: 1.15 });
      const e = t * t * (3 - 2 * t), a = alex48(W, 0.05, ZE + 0.5 - 1.25 * e, 'wide_worried'); a.rotation.y = Math.PI; walkPose(a, t * 1.6, 0.45); vanishLeft(W, a, 0.6);
      return cam7(50, V(0.25, 1.6, ZE + 1.7), V(0.0, 1.2, ZE - 0.8), A);
    } },
    // ANIM: inside flat 47 (EP01 S07's side of the hall, turned round): ALEX_48 comes in through the front door; it swings
    // shut behind him and the red glow of the deleted room is cut off
    E8_flat_in: { desc: 'Inside flat 47: ALEX_48 comes in through the front door, it shuts behind him, the red glow cut off', frames: 22, make(W, t, A) {
      flat8(W, { leak: 0 }); W.objs.stairwell.visible = false;
      const shut = Math.max(0, Math.min(1, (t - 0.55) / 0.35)), sh = shut * shut * (3 - 2 * shut);
      ajar(W, 1.2 * (1 - sh));
      const glow = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 2.4), new THREE.MeshBasicMaterial({ color: '#c8281e' })); glow.position.set(0, 1.2, -0.7); W.scene.add(glow);
      const rnd = P.mulberry(88); for (let i = 0; i < 14; i++) { const c = P.box(0.06, 0.06, 0.06, new THREE.MeshBasicMaterial({ color: rnd() < 0.5 ? '#5fe6ff' : '#ff8070' }), -0.5 + rnd(), 0.3 + rnd() * 1.8 - t * 0.6 * rnd(), -0.3 - rnd() * 0.3, W.scene); c.castShadow = false; }
      lamp(W, '#ff4a38', 2.2 * (1 - sh), [0.0, 1.3, -0.25], 2.6);
      const e = Math.min(1, t / 0.6), ee = e * e * (3 - 2 * e);
      const a = alex48(W, 0.05 + 0.1 * ee, -0.45 + 1.4 * ee, 'wide_worried'); a.rotation.y = 0.0; walkPose(a, e * 1.8, 0.4 * (1 - ee * 0.6)); vanishLeft(W, a, 0.6);
      return camera(50, V(-0.25, 1.4, 3.6), V(0.1, 1.05, 0.2), A);
    } },
    // POV in the entryway, facing the shut front door: his phone (right hand) — the editor draws the lock screen and the date
    E8_phone: { desc: 'POV in flat 47\'s entryway facing the front door: ALEX_48\'s phone', phone: true, make(W, t, A) {
      flat8(W, {});
      if (W.p.close) { const cam = camera(40, V(0.12, 1.5, 1.25), V(0.18, 1.0, 0.0), A); W.screen = povPhone(W.scene, cam, { rx: 0.08, ry: 0.06, rz: -0.06, z: -0.24, y: -0.015, glow: 1.2 }); return cam; }
      const cam = camera(44, V(0.2, 1.55, 1.6), V(0.1, 1.05, 0.0), A);
      W.screen = povPhone(W.scene, cam, { rx: 0.1, ry: -0.06, rz: 0.05, z: -0.29, glow: 1.2 }); return cam;
    } },
    // ANIM (k): kitchen floor, low — the glass of water slides off the table edge and breaks on the tiles; a seated figure's
    // feet under the table (no face)
    E8_glass: { desc: 'Kitchen floor, low: the glass falls off the table and breaks; someone\'s feet under the table', frames: 18, make(W, t, A) {
      const K = flat8(W, { glass: 'none' });
      const b = P.makeGlassBreak(W.p.k ?? 1, { seed: 47 }); b.position.set(K.glassAt.x + 0.08, 0, K.glassAt.z - 0.05); W.scene.add(b);
      const o = alex({ face: 'neutral' }); o.position.set(K.chairPos.x, 0, K.chairPos.z); o.rotation.y = Math.PI; P.seatPerson(o); W.scene.add(o);
      o.userData.arms[1].rotation.x = -0.9; o.userData.arms[-1].rotation.x = -0.9;
      lamp(W, '#ffc890', 0.5, [K.glassAt.x + 0.1, 0.4, K.glassAt.z - 0.5], 1.3);
      return camera(46, V(K.glassAt.x + 0.32, 0.16, K.glassAt.z - 0.62), V(K.glassAt.x - 0.05, 0.12, K.glassAt.z + 0.35), A);
    } },
    // ALEX_48 freezes in the hall (profile from the coat-rack side), warm kitchen light on him
    E8_alex_hall: { desc: 'ALEX_48 freezes in the hall, phone in hand, warm kitchen light on his face', make(W, t, A) {
      flat8(W, {});
      const a = alex48(W, 0.25, 1.3, 'wide_worried_side'); a.rotation.y = Math.PI + 0.5;
      a.userData.arms[1].rotation.x = -1.1; const ph = P.makePhone('#cfe0ff'); ph.position.set(0, -0.62, 0.02); ph.rotation.x = -Math.PI / 2 + 0.3; a.userData.arms[1].add(ph);
      vanishLeft(W, a, 0.6);
      lamp(W, '#ffb870', 0.8, [0.6, 1.7, 2.2], 1.8); lamp(W, '#aabbe0', 0.4, [-0.3, 1.6, 0.6], 1.6);
      return camera(44, V(-0.42, 1.56, 0.5), V(0.22, 1.46, 1.3), A);
    } },
    // ANIM: from the front door — ALEX_48 slowly turns away from us toward the kitchen doorway (his body hides the table)
    E8_turn: { desc: 'From the front door: ALEX_48 slowly turns from the door toward the kitchen', frames: 18, make(W, t, A) {
      flat8(W, {});
      const K = W.objs.kitchen; const o = alex({ face: 'neutral' }); o.position.set(K.chairPos.x, 0, K.chairPos.z); o.rotation.y = Math.PI; P.seatPerson(o); W.scene.add(o);
      o.userData.arms[1].rotation.x = -0.9; o.userData.arms[-1].rotation.x = -0.9;
      const e = t * t * (3 - 2 * t), a = alex48(W, 0.3, 1.9, 'wide_worried'); a.rotation.y = Math.PI - Math.PI * e;
      a.userData.headPivot.rotation.y = -0.35 * Math.sin(Math.PI * Math.min(1, t * 1.3)); vanishLeft(W, a, 0.6);
      lamp(W, '#b9c9e6', 0.45, [0.15, 1.7, 0.8], 2.0);
      return camera(54, V(0.27, 1.52, 0.24), V(0.3, 1.32, 1.9), A);
    } },
    // the reveal: over ALEX_48's shoulder, through the kitchen doorway — ALEX_ORIGINAL at the table under the lamp, shards on the floor
    E8_kitchen: { desc: 'Over ALEX_48\'s shoulder: ALEX_ORIGINAL sits at the kitchen table under the lamp; the broken glass on the floor', make(W, t, A) {
      const K = flat8(W, { glass: 'broken' });
      const o = alex({ face: 'neutral' }); o.position.set(K.chairPos.x, 0, K.chairPos.z); o.rotation.y = Math.PI; P.seatPerson(o); W.scene.add(o);
      o.userData.arms[1].rotation.x = -0.95; o.userData.arms[-1].rotation.x = -0.95; o.userData.arms[1].rotation.z = 0.15; o.userData.arms[-1].rotation.z = -0.15;
      const a = alex48(W, -0.36, 2.3, 'wide_worried'); a.rotation.y = 0.2; vanishLeft(W, a, 0.62);
      return camera(34, V(0.05, 1.62, 1.35), V(0.3, 1.15, 5.9), A);
    } },
    // ALEX_ORIGINAL close at the table (lip-sync stills by face). params.point: his right arm up, pointing at the front door
    // (past the camera); params.down: eyes on the hand
    E8_orig: { desc: 'ALEX_ORIGINAL at the kitchen table, close (POV of ALEX_48 from the doorway)', make(W, t, A) {
      const K = flat8(W, { glass: 'broken' });
      const o = alex({ face: W.p.face || 'neutral' }); o.position.set(K.chairPos.x, 0, K.chairPos.z); o.rotation.y = Math.PI; P.seatPerson(o); W.scene.add(o);
      o.userData.arms[1].rotation.x = -0.95; o.userData.arms[-1].rotation.x = -0.95; o.userData.headPivot.rotation.x = W.p.down ? 0.18 : -0.08;
      if (W.p.point) { o.userData.arms[1].rotation.x = -1.5; o.userData.arms[1].rotation.z = 0.32; o.userData.headPivot.rotation.y = 0.12; }
      lamp(W, '#ffc890', 0.55, [K.chairPos.x - 0.1, 1.45, K.chairPos.z - 0.6], 1.3);
      if (W.p.wide) return camera(44, V(1.45, 1.45, 5.05), V(0.05, 1.12, 4.75), A);
      return camera(W.p.point ? 34 : 30, V(0.24, 1.55, 3.95), V(K.chairPos.x, 1.22, K.chairPos.z), A);
    } },
    // two-shot from the kitchen's right side: ALEX_ORIGINAL points past ALEX_48 (in the doorway) at the front door
    E8_orig_point: { desc: 'Two-shot: ALEX_ORIGINAL points past ALEX_48 at the front door', make(W, t, A) {
      const K = flat8(W, { glass: 'broken' });
      const o = alex({ face: 'neutral' }); o.position.set(K.chairPos.x, 0, K.chairPos.z); o.rotation.y = Math.PI; P.seatPerson(o); W.scene.add(o);
      o.userData.arms[-1].rotation.x = -0.95; o.userData.arms[1].rotation.x = -1.55; o.userData.arms[1].rotation.z = 0.05;
      const a = alex48(W, 0.3, 4.0, 'wide_worried'); a.rotation.y = 0.0; vanishLeft(W, a, 0.62);
      lamp(W, '#ffc890', 0.5, [0.3, 1.6, 4.5], 1.4);
      return camera(48, V(0.62, 1.5, 6.75), V(0.3, 1.25, 3.6), A);
    } },
    // ANIM (k): macro, ALEX_48's hand in the warm kitchen light — the deletion goes on
    E8_hand_flat: { desc: 'Macro: ALEX_48\'s left hand keeps dissolving in the warm light of the kitchen doorway', frames: 14, make(W, t, A) {
      flat8(W, { glass: 'broken' });
      const cam = camera(40, V(0.15, 1.3, 3.15), V(0.25, 1.1, 5.2), A); W.scene.add(cam);
      const a = wristRig(W, cam, { num: 1, clear: 1, light: 0.5, lightCol: '#ffc890' });
      W.scene.updateMatrixWorld(true);
      const k = 0.55 + 0.15 * (W.p.k ?? 1), tip = a.localToWorld(V(0, -0.58, 0)), root = a.localToWorld(V(0, -0.05, 0)), d = root.clone().sub(tip).normalize();
      P.dissolve(a, k, { dir: d, a: tip.dot(d), b: root.dot(d), cell: 60, sweep: 1.0, glow: '#5fe6ff' });
      return cam;
    } },
    // ANIM (turn): the front door's lock from inside — the thumb-turn is jerked round from outside (EP01 S20, a new angle)
    E8_lock: { desc: 'Lock close-up from inside: the thumb-turn is turned from outside', frames: 30, make(W, t, A) {
      flat8(W, { leak: 10 });
      W.objs.lock.getObjectByName('thumbTurn').rotation.z = -lockTurn(W.p.turn ?? t) * Math.PI / 2;
      lamp(W, '#ffcf8a', 0.8, [-0.15, 1.35, 0.55], 1.1);
      const z = 0.38 - 0.06 * (W.p.turn ?? t);
      return camera(30, V(-0.2, 1.3, z), V(-0.37, 1.19, 0.03), A);
    } },
    // from the dark bedroom doorway, over ALEX_48's shoulder: the front door, a strip of light under it, two feet behind it
    E8_hide: { desc: 'From the hall by the kitchen doorway: the front door, a strip of light under it, two feet behind it', make(W, t, A) {
      flat8(W, { leak: 12 });
      for (const x of [-0.24, -0.12, 0.12, 0.23]) P.box(0.08, 0.014, 0.004, new THREE.MeshBasicMaterial({ color: '#0a0a0a' }), x, 0.006, 0.0035, W.scene);
      lamp(W, '#dff0d0', 0.5, [0.0, 0.25, 0.3], 1.4);
      return camera(46, V(0.28, 1.38, 3.35), V(0.0, 0.95, 0.0), A);
    } },
    // ======================= EP09 «ПЕРВЫЙ АЛЕКС» (flat 47, the same second EP08 ended on: the key in the lock, his own voice)
    // (the lock close-up itself is EP08's E8_lock shot, re-rendered as E9_lock)
    // ALEX_48 in the hall by the kitchen doorway, staring at the front door; the warm kitchen behind him
    E9_a48_hall: { desc: 'ALEX_48 frozen in the hall, staring at the front door; the kitchen doorway glowing behind him', make(W, t, A) {
      flat9(W, {});
      const a = a48(W, 0.3, 3.72, W.p.face || 'wide_worried', Math.PI); a.userData.headPivot.rotation.x = -0.05;
      a.userData.arms[-1].rotation.x = -0.3; a.userData.arms[-1].rotation.z = 0.15; vanishLeft(W, a, 0.64);
      lamp(W, '#b9c9e6', 0.55, [0.25, 1.75, 2.9], 1.8);
      return camera(42, V(0.1, 1.5, 1.95), V(0.3, 1.32, 3.72), A);
    } },
    // ANIM: ALEX_ZERO comes up out of the kitchen behind him and grabs his shoulder; ALEX_48 jerks his head round
    E9_grab: { desc: 'ALEX_ZERO comes out of the kitchen behind ALEX_48 and grabs him by the shoulder', frames: 18, make(W, t, A) {
      flat9(W, {});
      const e = Math.min(1, t / 0.55), ee = e * e * (3 - 2 * e), j = Math.max(0, Math.min(1, (t - 0.5) / 0.25));
      const a = a48(W, 0.3, 3.72 + 0.1 * j, 'wide_worried', Math.PI); a.userData.headPivot.rotation.y = -0.9 * j * (2 - j);
      a.userData.arms[-1].rotation.x = -0.3; vanishLeft(W, a, 0.64);
      const z = zero(W, 0.85, 4.95 - 0.7 * ee, j > 0.2 ? 'worried' : 'neutral'); walkPose(z, e * 1.4, 0.35 * (1 - ee));
      z.userData.arms[1].rotation.x = -0.25 - 0.62 * ee;
      lamp(W, '#b9c9e6', 0.55, [0.25, 1.75, 2.9], 1.8);
      return camera(46, V(0.98, 1.5, 2.55), V(0.55, 1.38, 4.0), A);
    } },
    // ALEX_ZERO close, in the kitchen doorway, hissing at him (lip-sync stills by face); W.p.whisper: turned, across the doorway
    E9_zero: { desc: 'ALEX_ZERO close in the kitchen doorway, urgent (POV of ALEX_48)', make(W, t, A) {
      flat9(W, {});
      if (W.p.across) {   // both pressed to the wall on either side of the doorway: ALEX_ZERO turns his head to ALEX_48 (whisper)
        const z = zero(W, ZERO_HIDE[0], ZERO_HIDE[1], W.p.face || 'neutral', 0); z.userData.headPivot.rotation.y = -1.0; if (W.p.num0) P.wristBadge(z, '0', C0, { light: 0.7 });
        if (W.p.red) lamp(W, C0, 0.7, [ZERO_HIDE[0] - 0.1, 1.0, ZERO_HIDE[1] + 0.35], 1.0); else lamp(W, '#ffc890', 0.45, [0.5, 1.6, 4.9], 1.4);
        return camera(36, V(-0.28, 1.56, 4.42), V(ZERO_HIDE[0], 1.53, ZERO_HIDE[1]), A);
      }
      const z = zero(W, 0.42, 4.28, W.p.face || 'worried', Math.PI + 0.15); z.userData.headPivot.rotation.x = -0.04;
      z.userData.arms[1].rotation.x = -1.1; z.userData.arms[1].rotation.z = -0.3;
      lamp(W, '#ffd2a0', 0.5, [0.3, 1.65, 3.6], 1.3);
      return camera(42, V(0.27, 1.5, 2.9), V(0.42, 1.38, 4.28), A);
    } },
    // ANIM: from inside the kitchen — ALEX_48 slides off the doorway along the wall and presses his back to it; ALEX_ZERO already
    // flat against the other side; through the doorway the hall and the front door
    E9_hide: { desc: 'From the kitchen: ALEX_48 slides along the wall beside the doorway and presses his back to it', frames: 18, make(W, t, A) {
      flat9(W, {});
      const e = t * t * (3 - 2 * t);
      const a = a48(W, 0.2 + (A48_HIDE[0] - 0.2) * e, 4.42 - 0.12 * e, 'wide_worried', 0); a.userData.headPivot.rotation.y = 1.0 * e;
      a.userData.legL.rotation.x = 0.15 * Math.sin(t * 9); a.userData.legR.rotation.x = -0.15 * Math.sin(t * 9); vanishLeft(W, a, 0.65);
      const z = zero(W, ZERO_HIDE[0], ZERO_HIDE[1], 'worried', 0); z.userData.headPivot.rotation.y = -0.8;
      lamp(W, '#ffc890', 0.45, [0.3, 1.6, 4.9], 1.6);
      return camera(50, V(0.55, 1.5, 6.3), V(-0.18, 1.15, 4.2), A);
    } },
    // ANIM: ALEX_48's eye at the jamb — the front door opens and ALEX_49 comes in with the glass of water
    E9_enter: { desc: 'Peeking past the doorway jamb: the front door opens, ALEX_49 walks in with a glass of water', frames: 22, make(W, t, A) {
      flat9(W, { leak: 0 });
      const dOpen = Math.min(1, t / 0.35), de = dOpen * dOpen * (3 - 2 * dOpen); ajar(W, 1.25 * de);
      landingLight(W, 0.7 * de + 0.05);
      const w = Math.max(0, Math.min(1, (t - 0.22) / 0.78)), we = w * (2 - w);
      if (t > 0.15) { const { a } = a49(W, 0.02 + 0.15 * we, -0.55 + 2.3 * we); walkPose(a, w * 2.4, 0.35 * (1 - 0.6 * we)); a.userData.arms[-1].rotation.x = -0.95; }
      lamp(W, '#b9c9e6', 0.4, [0.2, 1.8, 2.2], 2.0);
      return camera(42, PEEK.clone(), V(0.12, 1.22, 0.3), A);
    } },
    // ALEX_49 in the hall, holding the glass in front of him, the lit «49» at that wrist (seen from the kitchen side)
    E9_glass49: { desc: 'ALEX_49 in the hall holding the glass of water; a cyan number glows at his wrist', make(W, t, A) {
      flat9(W, {});
      const { a } = a49(W, 0.15, 1.75); a.userData.headPivot.rotation.x = 0.05;
      lamp(W, '#ffc890', 0.35, [0.3, 1.7, 3.2], 2.0); lamp(W, '#b9c9e6', 0.35, [-0.3, 1.9, 2.2], 1.6);
      return camera(34, V(0.02, 1.4, 3.55), V(0.15, 1.24, 1.75), A);
    } },
    // ALEX_48 close, back to the kitchen wall, head turned to the doorway (lip-sync stills by face)
    E9_a48w: { desc: 'ALEX_48 close, pressed to the kitchen wall, head turned toward the doorway', make(W, t, A) {
      flat9(W, {});
      const a = a48(W, A48_HIDE[0], A48_HIDE[1], W.p.face || 'wide_worried', 0); a.userData.headPivot.rotation.y = W.p.hall ? 0.75 : 0.95;
      a.userData.arms[-1].rotation.x = -0.15; vanishLeft(W, a, 0.66);
      lamp(W, '#ffc890', 0.4, [-0.1, 1.6, 4.95], 1.3); lamp(W, '#b9c9e6', 0.35, [0.3, 1.6, 4.0], 1.0);
      return camera(40, V(-0.08, 1.55, 5.62), V(A48_HIDE[0], 1.42, A48_HIDE[1]), A);
    } },
    // MACRO (g): ALEX_49's left wrist holding the glass, the «49» lights up under the skin (cyan)
    E9_wrist49: { desc: 'Macro: ALEX_49\'s wrist by the glass of water; the number 49 lights up cyan', frames: 16, make(W, t, A) {
      flat9(W, {});
      const cam = camera(40, V(0.2, 1.3, 2.75), V(0.15, 1.15, 1.6), A);
      const a = wrist9(W, cam, { text: '49', glow: C49, g: W.p.g ?? 1, flip: true, z: -0.85, light: 0.4 });
      const g = P.makeGlass(); g.scale.setScalar(1.5); g.position.set(0.08, 0.15, -0.8); cam.add(g);
      lamp(W, '#b9c9e6', 0.4, [0.3, 1.8, 2.2], 2.0);
      return cam;
    } },
    // MACRO (k): ALEX_48 looks down at his own forearm: the «48» (EP07's ink) and the hand still coming apart
    E9_wrist48: { desc: 'Macro: ALEX_48\'s own forearm — the 48 on the wrist, the hand dissolving', frames: 14, make(W, t, A) {
      flat9(W, {});
      const cam = camera(40, V(-0.42, 1.42, 4.4), V(-0.3, 1.0, 5.4), A); W.scene.add(cam);
      const a = wristRig(W, cam, { num: 1, clear: 0.12, light: 0.5, lightCol: '#ffc890' });
      W.scene.updateMatrixWorld(true);
      const k = 0.3 + 0.1 * (W.p.k ?? 1), tip = a.localToWorld(V(0, -0.62, 0)), root = a.localToWorld(V(0, -0.05, 0)), d = root.clone().sub(tip).normalize();
      P.dissolve(a, k, { dir: d, a: tip.dot(d), b: root.dot(d), cell: 60, sweep: 0.3, glow: '#5fe6ff' });
      return cam;
    } },
    // two-shot from inside the kitchen: the two of them flat against the wall either side of the doorway
    E9_two_wall: { desc: 'From the kitchen: ALEX_48 and ALEX_ZERO pressed to the wall either side of the doorway, ALEX_ZERO whispering', make(W, t, A) {
      flat9(W, {});
      const a = a48(W, A48_HIDE[0], A48_HIDE[1], 'wide_worried', 0); a.userData.headPivot.rotation.y = 0.9; vanishLeft(W, a, 0.66);
      const z = zero(W, ZERO_HIDE[0], ZERO_HIDE[1], 'neutral', 0); z.userData.headPivot.rotation.y = -1.0;
      lamp(W, '#ffc890', 0.4, [0.3, 1.6, 5.0], 1.6);
      return camera(62, V(0.3, 1.55, 6.9), V(0.3, 1.2, 4.2), A);
    } },
    // ALEX_49 in the hall, looking at the phone in his right hand (it lights his face), the glass in his left
    E9_vibrate: { desc: 'Peeking past the jamb: ALEX_49 in the hall, his phone lights up in his hand', phone: true, make(W, t, A) {
      flat9(W, {});
      const r = a49(W, 0.22, 2.35, { phone: true, rot: 0.25 }); r.a.userData.headPivot.rotation.x = 0.35;
      W.screen = r.screen;
      lamp(W, '#b9c9e6', 0.35, [0.2, 1.8, 3.0], 2.0);
      return camera(46, PEEK.clone(), V(0.2, 1.08, 2.35), A);
    } },
    // over ALEX_49's shoulder: his phone, the kitchen doorway (where they hide) behind it (the editor draws the task)
    E9_phone49: { desc: 'Over ALEX_49\'s shoulder: the phone in his hand; the kitchen doorway beyond it', phone: true, make(W, t, A) {
      flat9(W, {});
      const cam = camera(44, V(0.32, 1.6, 2.15), V(0.3, 1.15, 4.2), A);
      W.screen = povPhone(W.scene, cam, { rx: 0.08, ry: 0.05, rz: -0.05, z: -0.36, y: -0.03, x: -0.02, glow: 1.2 }); return cam;
    } },
    // ANIM: ALEX_49 in profile slowly turns his head from the phone straight toward the kitchen doorway — into the lens
    E9_turn49: { desc: 'Through the doorway: ALEX_49 slowly turns his head straight toward the hiding place', frames: 18, make(W, t, A) {
      flat9(W, {});
      const r = a49(W, 0.32, 2.75, { phone: true, rot: Math.PI / 2, lift: 0.75 }); const e = t * t * (3 - 2 * t);
      r.a.userData.headPivot.rotation.y = -1.45 * e; r.a.userData.headPivot.rotation.x = 0.3 * (1 - e);
      lamp(W, '#ffc890', 0.55, [0.25, 1.65, 3.6], 1.6);
      return camera(40, PEEK.clone().add(V(0.02, -0.02, 0)), V(0.32, 1.5, 2.75), A);
    } },
    // ANIM: ALEX_48 edges back along the wall; behind, ALEX_ZERO slips away from the wall toward the table
    E9_step_back: { desc: 'ALEX_48 edges back along the wall; ALEX_ZERO moves toward the kitchen table', frames: 14, make(W, t, A) {
      flat9(W, {});
      const e = t * t * (3 - 2 * t);
      const a = a48(W, A48_HIDE[0] - 0.2 * e, A48_HIDE[1], 'wide_worried_open', 0); a.userData.headPivot.rotation.y = 0.9; vanishLeft(W, a, 0.67);
      const z = zero(W, ZERO_HIDE[0] - 0.22 * e, ZERO_HIDE[1] + 0.75 * e, 'neutral', 0.6 * e); walkPose(z, t * 1.5, 0.3);
      lamp(W, '#ffc890', 0.45, [0.3, 1.6, 4.9], 1.6);
      return camera(56, V(0.6, 1.5, 6.45), V(-0.1, 1.15, 4.45), A);
    } },
    // ANIM: macro on the table — ALEX_ZERO's hand comes down on the bread knife by the plate and lifts it
    E9_knife_grab: { desc: 'Macro on the kitchen table: ALEX_ZERO\'s hand grabs the knife by the plate', frames: 16, make(W, t, A) {
      flat9(W, { noKnife: true });
      const kp = V(0.56, 0.75, 5.78), from = V(1.05, 1.15, 5.15);
      const h0 = V(0.92, 1.02, 5.3), hk = V(0.58, 0.79, 5.74), hl = V(0.66, 1.0, 5.52);
      let h; if (t < 0.45) { const u = t / 0.45; h = h0.clone().lerp(hk, u * u * (3 - 2 * u)); } else { const u = (t - 0.45) / 0.55; h = hk.clone().lerp(hl, u * u); }
      const g = new THREE.Group(), d = h.clone().sub(from).normalize();
      P.box(0.15, 0.7, 0.17, P.M(P.PAL.hoodie), 0, 0.35 - 0.05, 0, g); const fist = P.box(0.13, 0.11, 0.15, P.M(P.PAL.skinAlex), 0, -0.02, 0, g);
      g.quaternion.setFromUnitVectors(V(0, 1, 0), d.clone().negate()); g.position.copy(h); W.scene.add(g);
      const k = P.makeKnife();
      if (t < 0.45) { const hld = new THREE.Group(); hld.position.copy(kp); hld.rotation.y = 1.15; W.scene.add(hld); k.rotation.x = -Math.PI / 2; k.position.set(0, 0.006, -0.05); hld.add(k); }
      else { k.position.set(0, -0.03, 0.06); k.rotation.x = -1.35; fist.add(k); }
      lamp(W, '#ffd2a0', 0.6, [0.6, 1.25, 5.3], 1.2);
      return camera(40, V(0.12, 1.22, 5.0), V(0.58, 0.8, 5.74), A);
    } },
    // close: the knife in ALEX_ZERO's fist, low at his side, blade down and forward — the grip from EP08's recording
    E9_knife_fist: { desc: 'Close: the knife in ALEX_ZERO\'s fist, the same grip as on the recording of tomorrow', make(W, t, A) {
      flat9(W, { noKnife: true });
      const z = zero(W, 0.72, 5.0, 'neutral', Math.PI - 0.12); const k = knifeIn(z); W.scene.updateMatrixWorld(true);
      const kp = k.getWorldPosition(V(0, 0, 0));
      lamp(W, '#e8f2ff', 0.7, [kp.x - 0.25, kp.y + 0.2, kp.z - 0.35], 1.0);
      return camera(36, V(kp.x - 0.3, kp.y + 0.12, kp.z - 0.62), V(kp.x, kp.y - 0.1, kp.z), A);
    } },
    // ANIM (k): ALEX_48's POV low against the wall — ALEX_ZERO comes at him from the table, the knife coming up
    E9_zero_knife: { desc: 'POV of ALEX_48: ALEX_ZERO comes toward him from the table, raising the knife', frames: 18, make(W, t, A) {
      flat9(W, { noKnife: true });
      const k = W.p.k ?? 1, e = k * k * (3 - 2 * k);
      const z = zero(W, 0.88 - 0.3 * e, 5.4 - 0.45 * e, 'neutral', Math.PI + 0.75 * e); walkPose(z, k * 1.3, 0.3 * (1 - e)); knifeIn(z); z.userData.arms[1].rotation.z = 0.2;
      z.userData.headPivot.rotation.x = 0.08;
      lamp(W, '#ff8a6a', 0.35, [0.0, 0.9, 4.45], 1.4);
      return camera(50, V(-0.55, 1.45, 4.4), V(0.45, 1.42, 5.05), A);
    } },
    // ANIM: the strike, from the kitchen's left side — ALEX_49 has stepped through the doorway with the phone held out; ALEX_ZERO
    // swings the knife up and chops it down onto the phone: it is knocked out of the hand and drops to the tiles (t ≈ 0.55 impact)
    E9_strike: { desc: 'ALEX_ZERO swings the knife onto the phone in ALEX_49\'s hand; it flies to the floor', frames: 22, make(W, t, A) {
      flat9(W, { noKnife: true });
      const imp = 0.55, pre = Math.min(1, t / imp), post = Math.max(0, (t - imp) / (1 - imp));
      const r = a49(W, 0.32, 4.3, { glass: false, rot: 0 }); const R = r.a.userData.arms[1]; R.rotation.x = -1.2 + 0.6 * Math.min(1, post * 3); R.rotation.z = 0.0;
      if (post > 0) { r.a.userData.headPivot.rotation.x = 0.25 * Math.min(1, post * 2); r.a.position.z -= 0.08 * Math.min(1, post * 3); }
      const z = zero(W, 0.92, 5.1 - 0.06 * pre, 'neutral', Math.PI);
      const up = pre < 0.6 ? pre / 0.6 : 1 - (pre - 0.6) / 0.4;                       // knife up overhead, then a hard chop down
      knifeIn(z, post > 0 ? { rx: -1.05, kx: 0.2 } : { rx: -0.6 - 2.1 * up * (pre < 0.6 ? 1 : 1) - (pre >= 0.6 ? 0.45 * (1 - up) : 0), kx: 0.2 + 1.2 * up });
      W.scene.updateMatrixWorld(true);
      const ph = P.makePhone('#d8e6ff');
      if (post <= 0) { ph.position.set(0, -0.6, 0.06); ph.rotation.x = 1.2 - 0.25; R.add(ph); }
      else { const hand = V(0.62, 1.12, 4.82), fl = V(0.55, 0.006, 4.66), u = Math.min(1, post * 1.6), p = hand.clone().lerp(fl, u); p.y += 0.2 * Math.sin(Math.PI * u) * (1 - u); ph.position.copy(p); ph.rotation.set(-Math.PI / 2 * u + (1 - u) * 0.6, 2.4 * u, 0.6 * u); W.scene.add(ph); }
      lamp(W, '#ffc890', 0.55, [0.0, 1.6, 4.9], 1.6);
      return camera(66, V(-0.88, 1.5, 4.55), V(0.6, 1.2, 4.72), A);
    } },
    // macro: the phone on the kitchen tiles, screen up (the editor draws the task message and the crack on the screen)
    E9_phone_floor: { desc: 'Macro: ALEX_49\'s phone on the kitchen tiles, screen up', phone: true, make(W, t, A) {
      flat9(W, { noKnife: true });
      const ph = P.makePhone('#d8e6ff'); ph.position.set(0.55, 0.006, 4.66); ph.rotation.set(-Math.PI / 2, 0, 0.35); W.scene.add(ph);
      W.screen = ph.getObjectByName('screen');
      lamp(W, '#bcd2ff', 0.25, [0.55, 0.25, 4.74], 0.8);
      return camera(36, V(0.69, 0.58, 5.06), V(0.55, 0.0, 4.66), A);
    } },
    // wide from inside the kitchen: the three of them over the broken phone on the floor
    E9_three: { desc: 'Wide: ALEX_48, ALEX_ZERO (knife) and ALEX_49 all stare down at the broken phone on the floor', make(W, t, A) {
      flat9(W, { noKnife: true });
      const r = a49(W, 0.32, 4.3, { glass: false, rot: 0.2 }); r.a.userData.headPivot.rotation.x = 0.45;
      const z = zero(W, 0.92, 5.05, 'neutral', Math.PI - 0.3); knifeIn(z); z.userData.headPivot.rotation.x = 0.45;
      const a = a48(W, A48_HIDE[0] - 0.2, A48_HIDE[1], 'wide_worried', 0.5); a.userData.headPivot.rotation.x = 0.4; vanishLeft(W, a, 0.67);
      const ph = P.makePhone('#d8e6ff'); ph.position.set(0.55, 0.006, 4.66); ph.rotation.set(-Math.PI / 2, 0, 0.35); W.scene.add(ph);
      lamp(W, '#bcd2ff', 0.7, [0.55, 0.3, 4.66], 1.4); lamp(W, '#ffc890', 0.3, [0.3, 1.6, 5.4], 1.6);
      return camera(74, V(0.15, 2.05, 6.6), V(0.3, 0.45, 4.6), A);
    } },
    // ALEX_ZERO close, knife lowered — he freezes; params.face: 'neutral' then 'wide_pale' (his face changes); params.red: the «0» lit
    E9_zero_close: { desc: 'ALEX_ZERO close (POV of ALEX_48): he freezes, his face changes', make(W, t, A) {
      flat9(W, { noKnife: true });
      const z = zero(W, 0.92, 5.05, W.p.face || 'neutral', -2.0, { num0: !!W.p.red }); knifeIn(z); z.userData.headPivot.rotation.x = W.p.down ? 0.25 : -0.02;
      if (W.p.red) lamp(W, C0, 0.9, [0.7, 1.0, 4.85], 1.1); else lamp(W, '#ffd2a0', 0.45, [0.4, 1.6, 4.7], 1.2);
      return camera(40, V(-0.5, 1.55, 4.38), V(0.92, 1.42, 5.05), A);
    } },
    // MACRO (g): ALEX_ZERO's left wrist — a red «0» burns up under the skin
    E9_wrist0: { desc: 'Macro: ALEX_ZERO\'s wrist — a red 0 lights up under the skin', frames: 16, make(W, t, A) {
      flat9(W, { noKnife: true });
      const cam = camera(40, V(0.05, 1.3, 4.45), V(0.3, 1.1, 5.7), A);
      wrist9(W, cam, { text: '0', glow: C0, g: W.p.g ?? 1, flip: true, light: 0.35, lightCol: '#ffc890' });
      return cam;
    } },
    // ALEX_48 close by the wall — he opens his mouth to answer (head turned to ALEX_ZERO)
    // the front door from the kitchen doorway: it swings open again; ALEX_49's back in the foreground; cold landing light
    E9_door_open: { desc: 'From the kitchen doorway: the front door swings open again onto a cold lit landing; a figure on the threshold', frames: 18, make(W, t, A) {
      flat9(W, { noKnife: true, leak: 0, amb: 0.12, warm: 0.4 });
      const e = t * t * (3 - 2 * t); ajar(W, 1.3 * e); landingLight(W, 0.1 + 1.1 * e);
      oldCop(W, { x: -0.12, z: -0.35, head: 0.6 });
      const r = a49(W, 0.5, 3.3, { glass: false, rot: Math.PI }); r.a.userData.headPivot.rotation.y = -0.2 * e;
      lamp(W, '#b9c9e6', 0.25, [0.2, 1.8, 2.0], 2.0);
      return camera(40, PEEK.clone().add(V(0.12, 0, 0.1)), V(0.08, 1.25, 0.0), A);
    } },
    // the officer on the threshold, backlit, cap low — face in shadow; the black balaclava hanging from his hand
    E9_cop_sil: { desc: 'The officer on the threshold, backlit by the landing, face hidden under the cap; the balaclava in his hand', make(W, t, A) {
      flat9(W, { noKnife: true, leak: 0, amb: 0.04, warm: 0.12, lamp: 1.2 }); ajar(W, 1.3); landingLight(W, 1.4);
      oldCop(W, { x: -0.12, z: -0.35, head: 0.6 });
      return camera(40, V(0.05, 2.0, 2.4), V(-0.08, 1.3, -0.3), A);
    } },
    // macro: the balaclava hanging from his gloved fist (the mask from EP04)
    E9_mask: { desc: 'Macro: the black balaclava hanging from the officer\'s gloved hand', make(W, t, A) {
      flat9(W, { noKnife: true, leak: 0, amb: 0.2 }); ajar(W, 1.3); landingLight(W, 1.0);
      oldCop(W, { x: -0.12, z: -0.35, head: 0.6 }); lamp(W, '#cfdcff', 1.8, [-0.15, 0.9, 0.3], 1.1);
      return camera(40, V(-0.1, 0.95, 0.75), V(-0.3, 0.82, -0.05), A);
    } },
    // the reveal: close on the officer's face — old Alex under the police cap
    E9_cop_face: { desc: 'Close-up: under the police cap — Alex\'s face, thirty years older', make(W, t, A) {
      flat9(W, { noKnife: true, leak: 0, amb: 0.25 }); ajar(W, 1.3); landingLight(W, 0.9);
      oldCop(W, { x: -0.12, z: -0.35, head: -0.02, face: W.p.face || 'old' });
      lamp(W, '#dfe6f2', 0.75, [0.05, 1.65, 0.45], 1.3);
      return camera(34, V(-0.06, 1.58, 0.95), V(-0.12, 1.52, -0.35), A);
    } },
    // ANIM (lift): medium on the threshold — he raises the phone and holds it out toward them, screen first
    E9_cop_phone: { desc: 'The officer raises his phone and holds it out toward the flat, screen first', frames: 16, make(W, t, A) {
      flat9(W, { noKnife: true, leak: 0, amb: 0.25 }); ajar(W, 1.3); landingLight(W, 0.9);
      const r = oldCop(W, { x: -0.12, z: -0.35, head: 0.0, phone: W.p.lift ?? 1 });
      W.screen = r.screen; lamp(W, '#dfe6f2', 0.5, [0.0, 1.65, 0.8], 1.6);
      return camera(42, V(-0.2, 1.45, 1.75), V(0.0, 1.3, -0.3), A);
    } },
    // the phone held out at them, close (the editor draws «Создатель обнаружен» … «Оригинал должен умереть»); params.close tighter
    E9_cop_screen: { desc: 'The officer\'s phone held out toward the camera, his old face dim behind it', phone: true, make(W, t, A) {
      flat9(W, { noKnife: true, leak: 0, amb: 0.25 }); ajar(W, 1.3); landingLight(W, 0.9);
      const r = oldCop(W, { x: -0.12, z: -0.35, head: 0.0, phone: 1 }); W.screen = r.screen;
      W.scene.updateMatrixWorld(true); const sp = r.screen.getWorldPosition(V(0, 0, 0));
      lamp(W, '#dfe6f2', 0.35, [0.15, 1.65, 0.8], 1.6);
      if (W.p.close) return camera(38, V(sp.x - 0.01, sp.y + 0.07, sp.z + 0.55), V(sp.x, sp.y + 0.075, sp.z), A);   // the phone low in frame: the subtitle sits above it
      return camera(40, V(sp.x - 0.06, sp.y + 0.05, sp.z + 0.8), V(sp.x - 0.04, sp.y + 0.1, sp.z), A);
    } },
    // ======================================================== EP10 «СОЗДАТЕЛЬ» (E10_*)
    // ANIM (aim): behind ALEX_48's shoulder — the officer swings the phone (still red: «Оригинал должен умереть») from them onto ALEX_ZERO
    E10_cop_aim: { desc: 'Behind ALEX_48: the officer swings his red-lit phone round onto ALEX_ZERO', frames: 16, make(W, t, A) {
      flat10(W, {});
      const e = t * t * (3 - 2 * t); cast10(W, { cop: 'aim', aim: e, a48Rot: yaw(A10, COP10) + 0.1 });
      lamp(W, '#ff4a3a', 0.35 + 0.35 * e, [0.35, 1.45, 1.4], 1.8);
      return camera(50, V(-0.66, 1.6, 2.3), V(0.25, 1.3, 1.05), A);   // from beside ALEX_48, along the hall wall
    } },
    // ALEX_ZERO close, lit red by the phone pointed at him, not moving; params: face, head (rx), num0 always on
    E10_zero: { desc: 'ALEX_ZERO close, the phone\'s red light on his face; he does not move', make(W, t, A) {
      flat10(W, { hall: 0.2 });
      cast10(W, { cop: W.p.copB ? 'empty' : 'aim', a48: false, a49: false, zeroFace: W.p.face || 'neutral', zeroHead: W.p.head ?? 0.0 });
      lamp(W, '#ff4a3a', 0.6 * (W.p.red ?? 0.75), [0.35, 1.45, 1.75], 1.4); lamp(W, '#b9c9e6', 0.25, [0.9, 1.9, 2.0], 1.4);
      return camera(W.p.fov ?? 40, V(0.86, 1.6, 0.88), V(0.55, 1.45, 2.35), A);
    } },
    // ANIM (k): ALEX_ZERO slowly lifts his head (eyes down -> straight at the officer)
    E10_zero_head: { desc: 'ALEX_ZERO slowly raises his head', frames: 14, make(W, t, A) {
      flat10(W, { hall: 0.2 }); const k = W.p.k ?? 1, e = k * k * (3 - 2 * k);
      cast10(W, { cop: 'aim', a48: false, a49: false, zeroFace: e > 0.6 ? 'pale' : 'pale_down', zeroHead: 0.42 * (1 - e) - 0.02 * e });
      lamp(W, '#ff4a3a', 0.75, [0.35, 1.45, 1.75], 1.4); lamp(W, '#b9c9e6', 0.25, [0.9, 1.9, 2.0], 1.4);
      return camera(40, V(0.86, 1.55, 0.88), V(0.55, 1.4, 2.35), A);
    } },
    // ALEX_48 close, facing the officer (lip-sync stills by face); the hand still being deleted at his side; W.p.red: the screen glow red
    E10_a48: { desc: 'ALEX_48 close, facing the officer; his left hand still coming apart', make(W, t, A) {
      flat10(W, { hall: 0.25 });
      cast10(W, { cop: W.p.after ? 'kneel' : (W.p.copB ? 'empty' : 'aim'), copFace: W.p.after ? 'old_worried' : undefined, zero: (W.p.noZero || W.p.after) ? false : undefined, a49: false, a48Face: W.p.face || 'wide_worried', a48Phone: !!W.p.phone, a48Light: W.p.red ? '#ff4a3a' : '#bcd2ff' });
      lamp(W, W.p.red ? '#ff4a3a' : '#cfdcff', W.p.red ? 0.4 : 0.5, [-0.3, 1.5, 2.15], 1.2);
      return camera(40, V(0.5, 1.6, 1.57), V(-0.35, 1.42, 2.8), A);
    } },
    // the officer close: old Alex under the cap, phone held out (lip-sync by face); W.p.copB: after he has stepped up to ALEX_48 (no phone)
    E10_cop: { desc: 'The officer close-up: old Alex\'s face under the police cap', make(W, t, A) {
      flat10(W, {});
      const R = cast10(W, { cop: W.p.copB ? 'empty' : 'aim', a49: false, a48: W.p.copB ? false : undefined, zero: W.p.copB ? undefined : false, copFace: W.p.face || 'old', copHead: W.p.head ?? 0.0 });
      const cp = W.p.copB ? COP10B : COP10, fy = yaw(cp, W.p.copB ? A10 : Z10), dd = W.p.copB ? 1.2 : 1.5, off = W.p.copB ? 0.3 : 0.32;
      const cpos = V(cp[0] + Math.sin(fy) * dd - Math.cos(fy) * off, 1.6, cp[1] + Math.cos(fy) * dd + Math.sin(fy) * off);
      lamp(W, W.p.copB ? '#cfdcff' : '#ff5a4a', 0.55, [cpos.x, 1.5, cpos.z - 0.2], 1.2);
      return camera(40, cpos, V(cp[0], 1.47, cp[1]), A);
    } },
    // wide from the kitchen doorway: every phone in the hall lit (the officer's, ALEX_48's, ALEX_49's cracked one) — the editor draws on
    // each screen. W.p.copB: after the officer has given his phone to ALEX_48 (stood back, hands empty); a dropped phone on the floor too
    E10_phones: { desc: 'Wide from the kitchen doorway: all the phones in the hall light up at once', make(W, t, A) {
      flat10(W, { hall: 0.2, amb: 0.16 });
      const R = cast10(W, { cop: W.p.copB ? 'empty' : 'aim', a48Phone: true, a49Phone: true, a48Rot: yaw(A10, COP10) + 0.5, a49Rot: yaw(B10, COP10) - 0.4, zeroHeadY: W.p.copB ? 0 : undefined });
      R.a48.userData.headPivot.rotation.x = 0.3; R.a49.userData.headPivot.rotation.x = 0.3;
      const sc = [R.a48Screen, R.a49Screen];
      if (R.copScreen) sc.push(R.copScreen);
      if (W.p.copB) { const ph = P.makePhone('#d8e6ff'); ph.position.set(-0.12, 0.006, 2.45); ph.rotation.set(-Math.PI / 2, 0, 0.7); W.scene.add(ph); sc.push(ph.getObjectByName('screen')); lamp(W, '#bcd2ff', 0.35, [-0.12, 0.25, 2.45], 0.9); }
      W.screens = sc;
      lamp(W, '#bcd2ff', 0.6, [0.2, 1.3, 2.9], 2.2);
      return camera(60, V(0.3, 2.05, 5.05), V(0.1, 1.0, 1.4), A);
    } },
    // POV of ALEX_48: a phone in his hand in front of him (the editor draws the screen); W.p.look 'zero' | 'cop' | 'copB'; W.p.close: tighter
    E10_pov: { desc: 'POV of ALEX_48: the phone in his hand, the hall beyond it', phone: true, make(W, t, A) {
      flat10(W, { hall: 0.25 });
      const look = W.p.look || 'zero', copB = look !== 'zero' && look !== 'cop';
      cast10(W, { cop: W.p.after ? 'kneel' : (look === 'cop' ? 'aim' : 'empty'), a48: false, zero: W.p.after ? false : undefined, zeroRot: copB ? yaw(Z10, A10) : undefined, copFace: copB ? 'old_worried' : 'old' });
      const tgt = look === 'zero' ? V(Z10[0], 1.35, Z10[1]) : (look === 'cop' ? V(COP10[0], 1.35, COP10[1]) : V(COP10B[0], 1.32, COP10B[1]));
      const cam = camera(42, EYE48.clone(), tgt, A);
      W.screen = povPhone(W.scene, cam, W.p.close ? { z: -0.2, y: -0.012, x: 0.0, rx: 0.05, ry: 0.0, rz: 0.03, glow: 1.2 } : { z: -0.27, y: -0.03, x: 0.01, rx: 0.1, ry: -0.04, rz: 0.05, glow: 1.2 });
      lamp(W, W.p.red ? '#ff4a3a' : '#bcd2ff', 0.5, [EYE48.x + 0.05, 1.35, EYE48.z - 0.35], 1.0);
      return cam;
    } },
    // MACRO (k): ALEX_48 looks down at his left forearm — the «48» and the hand dissolving further, the red phone light on it
    E10_hand48: { desc: 'Macro: ALEX_48\'s disappearing hand and the 48 on his wrist', frames: 14, make(W, t, A) {
      flat10(W, {});
      const cam = camera(40, V(-0.35, 1.45, 2.95), V(-0.2, 1.0, 1.9), A); W.scene.add(cam);
      const a = wristRig(W, cam, { num: 1, clear: 0.15, light: 0.5, lightCol: '#ffb4a6' });
      W.scene.updateMatrixWorld(true);
      const k = 0.3 + 0.1 * (W.p.k ?? 1), tip = a.localToWorld(V(0, -0.62, 0)), root = a.localToWorld(V(0, -0.05, 0)), d = root.clone().sub(tip).normalize();
      P.dissolve(a, k, { dir: d, a: tip.dot(d), b: root.dot(d), cell: 60, sweep: 0.3, glow: '#5fe6ff' });
      lamp(W, '#ff4a3a', 0.4, [0.1, 1.4, 2.2], 1.6);
      return cam;
    } },
    // ANIM (step): from the bedroom-door side — the officer steps up to ALEX_48 and holds the phone out to him
    E10_cop_give: { desc: 'The officer steps up to ALEX_48 and holds his phone out to him', frames: 16, make(W, t, A) {
      flat10(W, {});
      cast10(W, { cop: 'give', step: t, a49: false, a48: false });
      lamp(W, '#ff4a3a', 0.35, [-0.1, 1.4, 2.1], 1.4); lamp(W, '#cfdcff', 0.4, [-0.35, 1.5, 2.55], 1.6);
      return camera(50, V(-0.5, 1.52, 3.55), V(-0.15, 1.25, 1.6), A);    // ALEX_48's POV: the officer walks up to him, phone held out
    } },
    // ANIM (k): the press — low close on ALEX_48's right hand: the thumb comes down on the screen; the screen goes from cold to red
    E10_press: { desc: 'Close: ALEX_48\'s thumb presses the screen; the phone glows red', frames: 14, make(W, t, A) {
      flat10(W, { hall: 0.2 });
      const k = W.p.k ?? 1, red = k > 0.62;
      const a = a48(W, A10[0], A10[1], red ? 'wide_worried' : 'worried', yaw(A10, COP10B)); vanishLeft(W, a, 0.7);
      const Rr = a.userData.arms[1]; Rr.rotation.x = -1.05; Rr.rotation.z = 0.35;
      const ph = P.makePhone(red ? '#ff3a30' : '#d8e6ff'); ph.position.set(0.0, -0.62, 0.03); ph.rotation.x = -Math.PI / 2 + 0.55; Rr.add(ph);
      const u = Math.min(1, k / 0.55), th = P.box(0.03, 0.03, 0.075, P.M(P.PAL.skinAlex), -0.03 + 0.03 * u, 0.04 - 0.035 * u, 0.04 - 0.028 * u, ph); th.rotation.x = 0.3;
      const l = new THREE.PointLight(red ? '#ff3a30' : '#bcd2ff', red ? 0.9 : 0.45, 1.1, 1.6); l.position.set(0, -0.62, 0.2); Rr.add(l);
      W.scene.updateMatrixWorld(true); const pp = ph.getWorldPosition(V(0, 0, 0));
      return camera(46, V(A10[0] + 0.04, 1.6, A10[1] - 0.16), V(pp.x, pp.y, pp.z), A);   // ALEX_48's own eyes, looking down at his thumb on the phone
    } },
    // ANIM (k): ALEX_ZERO turns sharply toward the phones (over ALEX_48's shoulder)
    E10_zero_turn: { desc: 'ALEX_ZERO turns sharply toward the phones', frames: 14, make(W, t, A) {
      flat10(W, {});
      const k = W.p.k ?? 1, e = 1 - Math.pow(1 - k, 3);
      const r0 = yaw(Z10, COP10B), r1 = yaw(Z10, A10) + 0.15;
      const R = cast10(W, { cop: 'empty', a49: false, zeroRot: r0 + (r1 - r0) * e, zeroFace: e > 0.5 ? 'wide_pale' : 'pale', a48Phone: true, a48Rot: yaw(A10, Z10) });
      lamp(W, '#bcd2ff', 0.5, [0.1, 1.4, 2.6], 1.4);
      return camera(42, V(-0.05, 1.75, 3.4), V(0.52, 1.42, 2.35), A);
    } },
    // ANIM (k): POV of ALEX_48 — ALEX_ZERO begins to disappear: blocks blink out from his feet up with EP07's cyan edge
    E10_zero_vanish: { desc: 'POV of ALEX_48: ALEX_ZERO starts to disappear, block by block', frames: 20, make(W, t, A) {
      flat10(W, {});
      const k = W.p.k ?? 1;
      cast10(W, { cop: 'empty', a48: false, zeroRot: yaw(Z10, A10) + 0.15, zeroFace: 'wide_pale', vanish: 0.05 + 0.5 * k, zeroHead: -0.05 });
      lamp(W, '#5fe6ff', 0.3 + 0.5 * k, [0.45, 0.6, 2.6], 1.4); lamp(W, '#cfdcff', 0.35, [0.1, 1.7, 2.6], 1.6);
      return camera(52, V(-0.55, 1.45, 3.9), V(0.52, 1.0, 2.35), A);
    } },
    // ANIM (kneel): the officer drops to his knees in front of ALEX_48 (seen from ALEX_48's side)
    E10_cop_kneel: { desc: 'The officer drops to his knees', frames: 16, make(W, t, A) {
      flat10(W, {});
      const k = W.p.kneel ?? 1, e = Math.min(1, k * k * 1.3);
      cast10(W, { cop: 'kneel', kneel: e, a48: false, zero: false, a49: false, copFace: 'old_worried', copHead: 0 });
      lamp(W, '#cfdcff', 0.5, [-0.35, 1.5, 2.55], 1.6);
      return camera(52, V(-0.55, 1.45, 3.6), V(-0.2, 0.85, 1.75), A);
    } },
    // room 204 as a recording: the security camera high in the corner — the sister at her computer, the lit phones round her
    E10_r204_wide: { desc: 'Room 204 on a recording: the sister at a computer at the table of lit phones', make(W, t, A) {
      const D = room10(W, {}); D.s.userData.headPivot.rotation.x = 0.06;
      return camera(56, V(1.45, 2.3, ZE - 0.45), V(0.0, 0.85, ZE - 2.55), A);
    } },
    // over the sister's shoulder: her monitor (the editor draws «Проект «Алекс»», «Создатель: Елена»); W.p.close: the monitor fills the frame
    E10_r204_mon: { desc: 'Over the sister\'s shoulder: the monitor of the computer in room 204', make(W, t, A) {
      const D = room10(W, {}); W.screen = D.screen; W.scene.updateMatrixWorld(true); const sp = D.screen.getWorldPosition(V(0, 0, 0));
      if (W.p.close) return camera(36, V(sp.x + 0.08, sp.y + 0.03, sp.z - 1.0), V(sp.x, sp.y, sp.z), A);
      return camera(40, V(sp.x + 0.58, sp.y + 0.4, sp.z - 1.25), V(sp.x - 0.02, sp.y - 0.02, sp.z), A);
    } },
    // the sister close, from the webcam on her monitor: she looks straight into the lens (lip-sync stills by face)
    E10_sis: { desc: 'Room 204: the sister close, looking straight into the camera', make(W, t, A) {
      const D = room10(W, { face: W.p.face || 'cold', head: -0.06 }); W.scene.updateMatrixWorld(true);
      const hp = D.s.userData.headPivot.getWorldPosition(V(0, 0, 0)), sp = D.screen.getWorldPosition(V(0, 0, 0));
      W.scene.traverse(o => { if (o.isPointLight && o.parent && o.parent.name === 'corridor') { const wp = o.getWorldPosition(V(0, 0, 0)); if (wp.z < ZE - 0.8) o.intensity *= 0.35; } });
      lamp(W, '#9fb8e0', 0.35, [hp.x + 0.5, hp.y + 0.6, hp.z + 0.9], 2.2);
      return camera(36, V(sp.x + 0.22, 1.7, sp.z + 0.8), V(hp.x, hp.y + 0.16, hp.z), A);   // from over the monitor, looking down at her
    } },
    // ANIM (d): the hotel corridor — the camera creeps toward door 204 under its caged red lamp, cold light under the door
    E10_door204: { desc: 'The hotel corridor: creeping up on door 204 under the red lamp, light under the door', frames: 20, make(W, t, A) {
      corridorWorld(W, { sconces: 2, open: 0, gap: true, fogNear: 4, fogFar: 14, amb: 0.14 });
      const d = W.p.d ?? 1, e = d * (2 - d);
      return camera(46, V(0.12 - 0.08 * e, 1.5, ZE + 4.8 - 1.4 * e), V(0.0, 1.12, ZE), A);
    } },
    REF_versions10: { desc: 'Character reference (EP10): ALEX_48, ALEX_49, ALEX_ZERO (half deleted), ALEX_OLD_POLICE kneeling, the sister', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const a = alex({ face: 'wide_worried' }); a.position.set(-1.6, 0, 0); W.scene.add(a); vanishLeft(W, a, 0.7);
      const r = a49(W, -0.8, 0, { glass: false }); r.a.rotation.y = 0;
      const z = alex({ face: 'wide_pale' }); z.position.set(0.0, 0, 0); W.scene.add(z); P.wristBadge(z, '0', C0, { light: 0.5 }); W.scene.updateMatrixWorld(true); P.dissolve(z, 0.4, { dir: V(0, 1, 0), a: 0, b: 1.85, cell: 34, sweep: 0.9 });
      const c = P.makeOldCop({ gloves: true, face: 'old_worried' }); c.position.set(0.8, 0, 0); W.scene.add(c); P.kneelPose(c, 1);
      const s = P.makePerson('sister', { face: 'cold' }); s.position.set(1.6, 0, 0); W.scene.add(s);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.05, 7.4), V(0, 0.9, 0), A);
    } },
    REF_room204_desk: { desc: 'Location reference (EP10): room 204 — the sister\'s computer at the table of phones', make(W, t, A) {
      room10(W, { amb: 0.7 });
      return camera(50, V(1.4, 2.0, ZE - 0.6), V(0.0, 0.8, ZE - 2.6), A);
    } },
    REF_versions9: { desc: 'Character reference (EP09): ALEX_48, ALEX_49 (glass, lit 49), ALEX_ZERO (lit 0), ALEX_OLD_POLICE (unmasked)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const a = alex({ face: 'wide_worried' }); a.position.set(-1.2, 0, 0); W.scene.add(a); vanishLeft(W, a, 0.66);
      const r = a49(W, -0.4, 0); r.a.rotation.y = 0;
      const z = alex({ face: 'pale' }); z.position.set(0.4, 0, 0); W.scene.add(z); P.wristBadge(z, '0', C0, { light: 0.5 }); z.userData.arms[-1].rotation.x = -0.6;
      const c = P.makeOldCop({ gloves: true }); c.position.set(1.2, 0, 0); W.scene.add(c); const b = P.makeBalaclava(); b.position.set(0, -0.6, 0.05); c.userData.arms[-1].add(b);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.05, 6.6), V(0, 0.95, 0), A);
    } },
    REF_wrists9: { desc: 'Prop reference (EP09): forearms — 48 (ink, EP07), 49 (cyan), 0 (red)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const f1 = P.makeForearm7({ num: 1 }); f1.position.set(-0.32, 0.3, 0); f1.rotation.z = Math.PI; W.scene.add(f1);
      const f2 = P.makeForearm9({ text: '49', glow: C49, g: 1, flip: true }); f2.position.set(0, 0.3, 0); f2.rotation.z = Math.PI; W.scene.add(f2);
      const f3 = P.makeForearm9({ text: '0', glow: C0, g: 1, flip: true }); f3.position.set(0.32, 0.3, 0); f3.rotation.z = Math.PI; W.scene.add(f3);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.0)); const d = new THREE.DirectionalLight('#fff', 1.0); d.position.set(1, 2, 4); W.scene.add(d);
      return camera(30, V(0, 0.55, 1.6), V(0, 0.55, 0), A);
    } },
    REF_kitchen: { desc: 'Location reference (EP08): the kitchen of flat 47 behind the entryway\'s back doorway', make(W, t, A) {
      flat8(W, { glass: 'table', amb: 0.7 });
      return camera(62, V(0.3, 1.75, 3.6), V(0.3, 0.95, 6.0), A);
    } },
    REF_versions: { desc: 'Character reference (EP08): ALEX_48 (left hand being deleted) and ALEX_ORIGINAL (no marks); knife and glass props', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      const a = alex({ face: 'wide_worried' }); a.position.set(-0.45, 0, 0); W.scene.add(a); vanishLeft(W, a, 0.6);
      const o = alex({ face: 'neutral' }); o.position.set(0.45, 0, 0); W.scene.add(o);
      const k = P.makeKnife(); k.position.set(0.0, 0.95, 0.2); k.rotation.z = 0.3; W.scene.add(k);
      const g = P.makeGlassBreak(1, { seed: 47 }); g.position.set(0.0, 0, 0.35); W.scene.add(g);
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.05, 4.6), V(0, 0.9, 0), A);
    } },
    REF_monitor_room: { desc: 'Location reference (EP07): the monitor room behind mirror 204 — monitor wall, empty operator desk', make(W, t, A) {
      const O = opsFeed(W, { face: 'cold' }); room7(W, { mirror: 'shattered', k: 1, feedCam: O.cam, amb: 0.5 });
      return cam7(54, V(1.2, 2.0, ZE + 0.3), V(-0.1, 1.1, ZE + 3.2), A);
    } },
    REF_operator_room: { desc: 'Location reference (EP07): the sister\'s operator room — desk, monitor + webcam, red button, microphone, racks', make(W, t, A) {
      const O = opsFeed(W, { face: 'cold' }); const G = O.G;
      return camera(50, G.localToWorld(V(1.55, 1.75, 1.4)), G.localToWorld(V(0.0, 0.9, 0.2)), A);
    } },
    REF_arm48: { desc: 'Prop reference (EP07): Alex\'s left forearm — scar + «48», half clear, fully clear (wires)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      [[0, -0.32], [0.5, 0.0], [1, 0.32]].forEach(([c, x]) => { const a = P.makeForearm7({ num: 1, clear: c }); a.position.set(x, 0.3, 0); a.rotation.z = Math.PI; W.scene.add(a); });
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.4); d.position.set(1, 2, 4); W.scene.add(d);
      return camera(30, V(0, 0.55, 1.6), V(0, 0.55, 0), A);
    } },
    REF_old_alex: { desc: 'Character reference: Alex and the old Alex (same model, aged)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      [['neutral', -0.75, 0], ['old', -0.25, 0], ['old_worried_open', 0.25, 0], ['old', 0.75, -0.7]].forEach(([f, x, r]) => { const p = alex({ face: f }); p.position.set(x, 0, 0); p.rotation.y = r; W.scene.add(p); });
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(30, V(0, 1.2, 4.6), V(0, 1.1, 0), A);
    } },
    REF_sister_cold: { desc: 'Character reference: the sister — neutral (EP04), worried, cold (EP06)', ref: true, make(W, t, A) {
      W.scene.background = new THREE.Color('#2a2f38');
      ['neutral', 'worried', 'cold'].forEach((f, i) => { const s = P.makePerson('sister', { face: f }); s.position.set(-0.5 + i * 0.5, 0, 0); W.scene.add(s); });
      W.scene.add(new THREE.HemisphereLight('#ffffff', '#555555', 1.2)); const d = new THREE.DirectionalLight('#fff', 1.5); d.position.set(2, 3, 4); W.scene.add(d);
      return camera(26, V(0, 1.45, 2.6), V(0, 1.45, 0), A);
    } },
    REF_mirror204: { desc: 'Location reference: room 204 after the door vanished — the mirror on the walled-up doorway', make(W, t, A) {
      corridorWorld(W, { sconces: 0, open: 1.35, phonesOn: true, amb: 0.7, fog: false, screenCol: '#ff8a7a', lightCol: '#ff5a48' });
      P.makeMirror204(W, {});
      return camera(48, V(1.25, 1.8, ZE - 2.6), V(-0.1, 1.05, ZE - 0.2), A);
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
