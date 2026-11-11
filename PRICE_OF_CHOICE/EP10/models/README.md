# EP10 — 3D models

As in EP01–EP09 there are no separate model files: every character, prop and room is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP10 uses the EP09 copy of that world and only adds to it (EP01–EP09 files untouched).
Reused unchanged from earlier episodes (read-only): `../EP09/scenes/E9_cop_screen_close.png` (EP09's last frame — the first shot),
`../EP08/scenes/E8_feedc_*` (the sister's close feed lip-sync), `../EP02/illustrations/S05_place_glass.png`, `S06_phone_bank.png` (EP01, flashback).

## Production names (code and docs only — never on screen)

| Name | Who | How it is built |
|---|---|---|
| **ALEX_48** | the hero: «48», left hand being deleted | `makePerson('alex')` + EP08 `vanishLeft()`; macro `E10_hand48` = EP07 `makeForearm7({num: 1})` + `dissolve` |
| **ALEX_49** | the copy with the cyan «49» | EP09 `a49()` (glass put down), `wristBadge('49')` |
| **ALEX_ZERO** | the supposed original, red «0» | EP09 `zero(…, {num0: true})`, the knife still in his fist (EP09); disappears with `dissolve` (EP07 cyan edge) |
| **ALEX_OLD_POLICE** | the officer = old Alex | EP09 `makeOldCop()` + the balaclava in his left hand; kneels with the new `kneelPose()` |
| **SISTER** (Елена) | Alex's sister | EP04 `makePerson('sister')`, EP07 `sisterSeated()`, EP06 `cold` face + mouth shapes — unchanged |

## New in EP10 (kept for future episodes)

| Model / effect | Function | Notes |
|---|---|---|
| The sister's computer in room 204 | `room204Desk(W, o)` (scene.js) | a desktop monitor (screen plane with `userData.hw/hh`, text drawn by `phone_ui.draw_proj10`), keyboard, her chair; the phones in front of the monitor are hidden, the other EP05 phones stay lit |
| Kneeling | `kneelPose(p, e)` | hips drop and the legs buckle, from e = 0.7 rebuilt as upright thighs + shins flat on the floor (like EP03's `seatPerson`) |
| Hall staging | `cast10()`, `flat10()` (shots.js) | everyone's positions in flat 47's hall right after EP09 (officer on the doormat → stepped up to ALEX_48) |
| Faces on the screens | `phone_ui.draw_faces10` | Alex's own 16×16 pixel face map (scene.js `FACE_ALEX` + tokens) tiled, zooming out from a few faces to hundreds |
| Choice / denial | `phone_ui.draw_choice10` | «Уничтожить оригинал», «Остановить игру», tap ripple, red flood, «Недостаточно прав» |
| Sister feed / recording / final screen | `draw_sis10`, `draw_video10`, `draw_end10`, `draw_proj10` | text only in code, series fonts (Rubik) |
| Reference sheets | `REF_versions10.png`, `REF_room204_desk.png` | the five characters in their EP10 states; room 204 with the computer |
