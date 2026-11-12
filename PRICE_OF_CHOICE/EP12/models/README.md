# EP12 — 3D models

As in EP01–EP11 there are no separate model files: every character, prop and set is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP12 uses the EP11 copy of that world and only adds to it (EP01–EP11 files untouched).
Reused unchanged from EP11 (read-only, not copied): `../EP11/scenes/E11_face_close.png`, `E11_face.png` (the turned computer — EP11's last
frame is EP12's first) and the red lip-sync close-up of the chained sister `E11_sisr_*.png`. The second recording on the main screen uses
EP12's own render of EP10's room-204 desk (`room204Desk`).

## Production names (code and docs only — never on screen)

| Name | Who | How it is built |
|---|---|---|
| **ALEX_48** | the hero, «48»; left hand being deleted (EP11's state, `vanishLeft 0.74`) until the handover; whole from «Она перестала исчезать» | `makePerson('alex')` + EP08 `vanishLeft()`; macros `E12_hand` (still going, red light) and `E12_hand_stop` (the blocks fly back, EP07 `makeForearm7({num: 1})` + `dissolve` run backwards) |
| **ALEX_ORIGINAL_CONSCIOUSNESS** | the real Alex, on the turned computer | never a 3D figure: Alex's own 16×16 face map on the screen (`phone_ui.draw_face12`): blink, lip-sync from the VO, a smirk, afraid at the end. Not ALEX_ZERO |
| **ELENA_204** | the sister in room 204 | EP04 `makePerson('sister')` / EP07 `sisterSeated()`, EP05 faces + mouth shapes, unchanged; chained (EP11's `chainedChair`) until the chair opens, then standing beside ALEX_48 |
| **ELENA_APARTMENT** | the second Elena, live on the side monitor | the very same `sisterSeated('worried', …)` at flat 47's kitchen table (EP08 `buildKitchen`) — no extra marks, nothing that tells them apart |
| **ALEX** (the recording, three years ago) | Alex driving | `makePerson('alex', {face: 'neutral'})` seated at the wheel (`seatDriver`), no number on the wrist |
| person on the road | unknown | `makeSilhouette()`: a hooded dark shape, no face, no colours |

ALEX_OLD_POLICE and ALEX_49 were deleted in EP11 and are not placed in any E12 shot.

## New in EP12 (kept for future episodes)

| Model / effect | Function | Notes |
|---|---|---|
| The chair opening | `releasedChair(G, {x, z, open, seated})` (scene.js) | `open` 0 = EP11's chained chair; 0–0.35 the four cuffs spring open (hinged halves, a cyan flash in the lock); 0.35–1 cuffs + chains drop to the floor; `seated:false` = empty chair, cuffs on the floor |
| Room 204 desk, EP12 | `desk12(W, o)` | EP11's `desk11` with `release` / `free`; `desk11` got an optional `chairFn` hook (default = EP11 behaviour, pixel-identical) |
| Night road | `buildRoad(W, o)` | a separate set (x = −80): wet glossy asphalt, dashed centre line, verges, blocky pines, sodium lamps (`lamps`, `lampSide`), dark-blue fog |
| Rain | `rain(W, centre, o)` + `06_render_video` fx `rain` | instanced slanted streaks in 3D (new pattern per frame through `seed`) + 2D streaks over the frame |
| The car | `makeCar(o)` | blocky hatchback: body, cabin, see-through glass, wheels, headlights (shadow spots + glare), brake lights, dashboard glow, steering wheel, phone in a dash holder (`phone` = screen mesh for the UI), pedals, wipers (`wiper` 0..1) |
| Driver pose | `seatDriver(p, o)` | seated legs to the pedals, both hands forward to the wheel |
| Person on the road | `makeSilhouette(o)` | hooded figure, `raise` lifts the arms (blinded by the headlights) |
| Brake macro | shot `E12_brake` | a small footwell set: hinged brake pedal, accelerator, the jeans leg + trainer slamming down, brake-light glow |
| Screens | `phone_ui.draw_task12 / draw_face12 / draw_admin12 / draw_retry12 / draw_live12` | «Первое задание» · «Не тормози» · «Награда — пятьсот долларов» · «> Повторить испытание» · 47 red copies + one cyan · «Передача управления» · «Новый администратор:» «48» · «Прямой эфир» «Квартира 47» · «Обнаружены две Елены» — text only in code, series fonts (Rubik) |
| Reference sheets | `REF_versions12.png`, `REF_car12.png` | ALEX_48 (hand going / whole), ELENA_204 and ELENA_APARTMENT side by side (identical), the person on the road; the car with Alex and the sister |
