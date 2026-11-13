# EP13 — 3D models

As in EP01–EP12 there are no separate model files: every character, prop and set is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP13 uses the EP12 copy of that world and only adds to it (EP01–EP12 files untouched).
Reused unchanged from EP12 (read-only, not copied): `../EP12/scenes/E12_two_*.png` — EP12's last frame (ELENA_204 beside ALEX_48, the side
monitor) is EP13's first, the feed on it is drawn by `phone_ui.draw_live13`.

## Production names (code and docs only — never on screen)

| Name | Who | How it is built |
|---|---|---|
| **ALEX_48** | the hero; hand whole since EP12's handover; «48» lit cyan on the inner left wrist (`badge13(a, '48', C48)`) until «Номер сорок восемь исчез» | `makePerson('alex')` (EP01 model, unchanged); macro `E13_arm` = new `forearm13()` — the forearm across the frame, the EP04 scar, «48» in ink pixels that leave one by one in cyan sparks; the inner face carries a plane (`W.quad`) where the editor burns in «СОЗДАТЕЛЬ» |
| **ALEX_ORIGINAL_CONSCIOUSNESS** | the real Alex | on the turned computer: Alex's 16×16 face map (`phone_ui.draw_face13`, smile from «улыбнулся», lip-sync; red and ghosted when the system speaks in his voice — `draw_voice13`). In the hidden recording: a plain `makePerson('alex', {face: 'smirk'})` on the back seat of EP12's car. Never ALEX_ZERO |
| **ELENA_1** | the Elena in room 204, standing beside ALEX_48 | EP04 `makePerson('sister')`, EP05 faces + mouth shapes, unchanged; «1» on the wrist (`badge13(s, '1', C1)`, cold white-cyan) |
| **ELENA_0** | the Elena at flat 47's kitchen table, only on the side monitor's live feed | the very same `sisterSeated('worried', …)` (EP12's ELENA_APARTMENT); «0» on the wrist (`badge13(s, '0', C0)`, the series red) |
| **ALEX** (the recording) | the driver | EP12's `car12` cast, unchanged; the sister beside him, unchanged |

## New in EP13 (kept for future episodes)

| Model / effect | Function | Notes |
|---|---|---|
| Wrist numbers | `badge13(p, text, col, {side, scale, light})` | EP09 `wristBadge` + scale; the shots counter-rotate the badge so it reads upright on a raised arm |
| Forearm macro | `forearm13({num, spark})` + `arm13Tex` | 0.34 m forearm lying along x (elbow → hand), «48» written along it; `num` 1 → 0 removes the ink pixels, `spark` lights the leaving ones cyan; `userData.quad` = the inner face for the editor |
| The car with a back bench | `car13(W, R, z, o)` | EP12's `car12` + a back bench and the original seated on it, a second phone in his hands lit on his face (`phone2` = its screen mesh, `phLight`, `ph2` screen colour) |
| The second phone, macro | shot `E13_phone2` | a separate small set (x = −80, z = 40): back bench, his knees, both hands round the phone, a sodium lamp passing the window |
| Room 204 after the handover | `room13(W, {red})` | EP12's `room12` with the chair empty, the side monitor lit; `red` = the alarm light from the warning to the end |
| Face token `smirk` | `faceVariant` (scene.js) | one mouth corner up — the same smirk as his face on the monitor |
| ALEX_48 on camera | shot `E13_selfcam` | the turned computer's webcam view of ALEX_48 (16:10) — the picture every screen shows at the end |

## Reference sheets
* `REF_versions13.png` — ALEX_48 («48»), ELENA_1 («1»), ELENA_0 («0») — identical models —, the original (plain ALEX, smirk).
* `REF_car13.png` — EP12's car with the back bench: the original with the second phone.
