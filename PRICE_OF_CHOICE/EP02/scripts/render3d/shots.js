// Shot library. EP01 «Стакан воды» angles are kept unchanged (same apartment, same characters) so EP02 can
// reuse them; add new EP02 shots with an "E2_" prefix. Each shot builds the shared world, places
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
