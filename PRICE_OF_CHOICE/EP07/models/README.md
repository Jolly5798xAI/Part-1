# EP07 — 3D models

As in EP01–EP06 there are no separate model files: every character, prop and room is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP07 uses the EP06 copy of that world and only adds to it.
EP06 frames reused unchanged are read from `../EP06/scenes` (`E6_show_cold`, `E6_sis_cold`, `E6_mirror_old`, `E6_old_*`,
`E6_room_red`, `E6_alex_portrait`); the EP04 photo of the sister from `../EP04/scenes/E4_sister_photo.png`.

## Reused unchanged

| Model | Function | Notes |
|---|---|---|
| Alex | `makePerson('alex')` | same proportions, hoodie, face; face tokens `wide_worried`, `down`, `pale`, lip shapes |
| The old Alex | `makePerson('alex', { face: 'old…' })` | **the EP06 model** (grey hair, lines, stubble) — only in the mirror (`mirrorOnly`) |
| Alex's sister | `makePerson('sister')` | **the EP04–EP06 model, not redesigned**; EP06 `cold` face |
| Room 204, the table of 35 phones, mirror 204 | `buildCorridor()`, `makeMirror204()` | EP05/EP06; the phones red (countdown) or dead (`phonesOn: false`) |
| Phone, open hand, chair | `makePhone()`, `makeOpenHand()`, `makeChair()` | EP01–EP03 |
| The EP04 scar | `scarTex()` pixels | redrawn pixel-for-pixel inside `scar48Tex()` |

## New in EP07 (kept for future episodes — use these, do not redesign)

| Model / effect | Function | Notes |
|---|---|---|
| **Cold face that speaks** | `sisterFace('cold_open' …)` | `cold` + mouth shapes (EP06's plain `cold` is unchanged) |
| **Voxel dissolve** | `dissolve(obj, k, {dir, a, b, cell, sweep, glow})` | any object falls apart into blinking cubes with a cyan edge, in a seeded order along `dir`; used for the sister vanishing and Alex's left hand being deleted |
| **Mirror cracks** | `mirrorCracks(W, M_, {k, cx, cy})` | spider-web of thin pale bars round the fist's impact (camera-only layer 2, so the mirror does not reflect them) |
| **Mirror bursting** | `shatterMirror204(W, k)` + `room204WallHole(W)` | the frame stays, the 6 × 12 glass tiles (the EP06 assembly grid) fly into the room; the wall gets the mirror-sized opening |
| **Monitor room** (behind the mirror) | `buildMonitorRoom(W, {feedCam, red})` | where the corridor was: dark panelled room, a wall of 11 monitors (big centre one = `screens[0]`), empty operator desk and chair, red/green standby LEDs. Sheet: `REF_monitor_room.png` |
| **Live feed screen** | `makeFeedScreen(w, h, feedCam)` | a monitor that renders another camera in real time (the centre monitor shows the sister) |
| **Operator room** (the sister's) | `buildOperatorRoom(W, {face, lean, press})`, `sisterSeated()` | far away (z ≈ +40): her desk, monitor with webcam, keyboard, red console button, desk microphone, server racks; she can lean to the mic and press the button. Sheet: `REF_operator_room.png` |
| **Alex's forearm «48»** | `makeForearm7({num, clear})`, `scar48Tex(num)` | the EP04 forearm + scar, the number «48» surfacing pixel by pixel between the scar and the hand; `clear` turns the skin to tinted glass over blocky wires (red/blue/yellow/green/white), a steel rod and a small board with a cyan light — stylised, no anatomy. Sheet: `REF_arm48.png` |
| Digits 1, 7, 8 | `DIGITS` | added to the 5 × 7 pixel font |

All on-screen Russian text (the phones' timer, «Выбор сделан» on the mirror, the monitors' message, the address and the date)
is drawn only by `scripts/phone_ui.py` / `scripts/06_render_video.py` with the series font (Rubik), never inside a rendered image.
The «48» on the wrist is pixel digits in the 3D texture (no font), as the room-204 plates are.
