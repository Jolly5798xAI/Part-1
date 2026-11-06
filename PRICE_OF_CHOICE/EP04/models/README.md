# EP04 — 3D models

As in EP01–EP03 there are no separate model files: every character, prop and room is built in code in one shared
world, so the cast and the flat look the same in every shot of every episode. EP04 uses the EP03 copy of that world
(`scripts/render3d/scene.js`, `shots.js`) and only adds to it. EP03's frames reused unchanged are read from `../EP03/scenes`.

## Reused unchanged

| Model | Function | Notes |
|---|---|---|
| Alex, the double | `makePerson('alex')` | the tied double is the same model, seated with `seatPerson()` and `makeRopes()` (EP03) |
| Police officer | `makePerson('cop')` | same uniform and cap |
| Flat 47 (Лесная, 12): entryway, front door, hall mirror, bedroom, chair | `buildWorld()`, `buildBedroom()`, `makeChair()` | same geometry and materials as EP03; the wet trail and puddle from EP03 stay on the floor |
| Phone | `makePhone()` | screens drawn by `scripts/phone_ui.py` |

## New in EP04 (kept for future episodes — use these, do not redesign)

| Model | Function | Notes |
|---|---|---|
| **The scar** | `scarTex()` + `makeForearm()` in `scene.js` | ONE texture function, so Alex's and the double's scars are pixel-identical: a diagonal raised scar across the **inner left wrist** with four stitch marks. `makeForearm()` is a forearm with the hoodie sleeve pushed up (inner wrist = +z face), options `bound` (rope round the hand) and `grip` (fingers curl) |
| Untaped double | face tokens `redmark` (skin reddened where the tape was), `open`/`ee`/`oo` (mouth shapes on any face), `side` (eyes past the camera), `pale` (colour change) | `faceVariant()`, `headMats()` |
| Tape being ripped off | `tiedMan4({ tape: k })` in `shots.js` | the 3D strip peels round its left end |
| **Masked officer** | `makePerson('cop', { face: 'mask', gloves: true })` | black balaclava with one eye slit (`FACE_MASK`), black gloves; cap and uniform unchanged. Sheet: `models/REF_masked_cop.png` |
| **Alex's sister** | `makePerson('sister')` | same rig and hair colour as Alex; long hair (side locks + back panel, side-swept fringe), lashes, blush, mustard knit sweater with white collar and a small pendant (`SWEATER_FRONT`, `PAL.sweater`), blue jeans, white sneakers. Sheet: `models/REF_sister.png`. Her name and where she is are **not** established |
| Sister's covert photo | `E4_sister_photo` (`sisterRoom()`) | reading at a desk under a warm lamp, shot through a window; an anonymous small set — it is not her real location and reveals nothing |
| Door 204 | `E4_room204` + `plateTex('204')` | a closed painted-metal door with a dark number plate (5×7 pixel digits, no fonts) under a flickering tube; seen only as a flash insert |
| Phone: cracked glass, glitch, dead screen, photo message, voice message | `scripts/phone_ui.py` (`crack`, `glitch`, `off`, `photo_msg`, `voice`) | the crack is seeded (`crack: 7`) so it is identical in every frame |
| Message on the mirror | `mirror_text()` in `scripts/06_render_video.py` | red text drawn in code (Rubik Bold, same red alert style as the phone), mapped onto the hall mirror's quad from `scenes/meta.json` |
