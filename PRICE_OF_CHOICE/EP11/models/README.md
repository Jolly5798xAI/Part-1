# EP11 — 3D models

As in EP01–EP10 there are no separate model files: every character, prop and room is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP11 uses the EP10 copy of that world and only adds to it (EP01–EP10 files untouched).
Reused unchanged from earlier episodes (read-only): `../EP10/scenes/E10_pov_end.png` (EP10's last phone frame — the first shot of EP11).

## Production names (code and docs only — never on screen)

| Name | Who | How it is built |
|---|---|---|
| **ALEX_48** | the hero: «48», left hand being deleted (a little further gone than in EP10) | `makePerson('alex')` + EP08 `vanishLeft()`; macro `E11_hand` = EP07 `makeForearm7({num: 1})` + `dissolve` |
| **ALEX_49** | the copy with the cyan «49» | EP09 `a49()`, `wristBadge('49')`; falls apart in the corridor (`E11_a49_dust`, EP07 `dissolve`) |
| **ALEX_OLD_POLICE** | the officer = old Alex | EP09 `makeOldCop()` + the balaclava in his left hand; holds ALEX_48 back, then falls apart in the doorway (`E11_cop_dust`) |
| **SISTER** (Елена) | Alex's sister | EP04 `makePerson('sister')`, EP07 `sisterSeated()`, EP05 `worried` face + mouth shapes — unchanged; now chained (`chainedChair`) |
| **ALEX_ORIGINAL_CONSCIOUSNESS** | the real Alex, connected to the system | never a 3D figure: Alex's own 16×16 face map drawn on the computer's screen (`phone_ui.draw_face11`), pale and cold, eyes closed → open, mouth from the VO |
| **ALEX** (hospital, three years ago) | the real Alex unconscious after the accident | `makePerson('alex', {face: 'closed'})` lying in `buildHospital()`; new face token `closed`; a white bandage, no injuries shown |

ALEX_ZERO is not on screen in EP11 and is never identified with the face on the screen.

## New in EP11 (kept for future episodes)

| Model / effect | Function | Notes |
|---|---|---|
| Chained chair | `chainedChair(G, {x, z, face, raise})` (scene.js) | EP10's chair + armrests, steel wrist and ankle cuffs, blocky chain links bolted to the armrests / front legs; `raise` lifts her cuffed hand |
| Room 204 desk, EP11 | `desk11(W, o)` | EP10's computer on a swivel neck (`turn` 0 → 1 swings the screen round to the door), thick cables into the floor and back wall with travelling light (`pulse`), a second side monitor (`sideScreen`), the chained sister behind the table; `red` = the zero level |
| Hospital ward | `buildHospital(W, o)` | a separate set (x = 60): two-tone walls, tiled floor, fluorescent panel, night blinds, steel bed, blanket, IV stand, heart monitor with a green pixel trace (no text), a visitor's chair with the sister's mustard cardigan |
| Eyes closed | `faceVariant` token `closed` | eyes become skin with a dark lash line (applied only when asked, every earlier face is pixel-identical) |
| Copies deleted | EP07 `dissolve` on the officer and ALEX_49 | bottom-up, cyan edge, red room light |
| Screens | `phone_ui.draw_choice11 / draw_zero11 / draw_hosp11 / draw_face11` | «Выберите, кого сохранить» · «Создателя» «или» «игрока» · «Нулевой уровень активирован» · «Удаление всех копий» · the hospital recording (REC 06.11.2023) · the face · «Подключение к оригиналу установлено» · «Оригинал проснулся» — text only in code, series fonts (Rubik) |
| Reference sheets | `REF_versions11.png`, `REF_room204_ep11.png`, `REF_hospital.png` | the characters in their EP11 states; room 204 with the chained chair and the swivel computer; the hospital ward |
