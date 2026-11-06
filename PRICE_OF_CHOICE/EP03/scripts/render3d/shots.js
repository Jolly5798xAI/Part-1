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

  function screenQuad(screen, cam, W, H) {
    screen.updateWorldMatrix(true, false); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
    const hw = 0.035, hh = 0.075;
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
