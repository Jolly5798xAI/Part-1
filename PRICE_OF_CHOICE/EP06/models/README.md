# EP06 — 3D models

As in EP01–EP05 there are no separate model files: every character, prop and room is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP06 uses the EP05 copy of that world and only adds to it.
EP05 frames reused unchanged are read from `../EP05/scenes` (`E5_sis_*`, `E5_room_lit`, `E5_phones_low`, `E5_phone_hero`),
the EP04 photo of the sister from `../EP04/scenes/E4_sister_photo.png`.

## Reused unchanged

| Model | Function | Notes |
|---|---|---|
| Alex | `makePerson('alex')` | same proportions, hoodie, face; EP03/EP04 face tokens (`wide_worried`, `worried`, lip shapes) |
| Alex's sister | `makePerson('sister')` | **the EP04/EP05 model, not redesigned**; EP05 face tokens `worried`, `open`, `ee`, `oo` |
| Hotel corridor, door 204, room 204, table of 35 phones | `buildCorridor()` | EP05; `meta.screens` gives every screen quad so the editor draws the UI on all 35 phones |
| Chair | `makeChair()`, `seatPerson()` | EP03 (now used for Alex sitting at the table on the recording) |
| Planar mirror | `makeMirror()`, `mirrorOnly()` | EP03 reflector; objects on layer 1 exist only in the reflection |

## New in EP06 (kept for future episodes — use these, do not redesign)

| Model | Function | Notes |
|---|---|---|
| **Old Alex** | `makePerson('alex', { face: 'old…' })` | **the same model** — same head, haircut shape, hoodie and proportions — with the face token `old`: receding grey hairline, grey hair volume, forehead line, crow's feet, bags under the eyes, nasolabial folds, grey stubble (applied only on bare skin, so it combines with `worried` and the lip shapes `open`/`ee`/`oo`). Sheet: `REF_old_alex.png` |
| **Sister, "cold" face** | `sisterFace('cold')` | she no longer smiles: heavy lids, brows drawn down, a flat closed mouth. Sheet: `REF_sister_cold.png` (neutral EP04 · worried · cold) |
| **Red countdown light** | `buildCorridor(W, { screenCol, lightCol })` | the table of phones lit red (screens `#ff8a7a`, lights `#ff5a48`) |
| **Walled-up doorway** | `room204Wall(W)` | the door of room 204 vanishes: door 204 hidden, one seamless wall over the front of the room in the same striped paper |
| **Mirror 204** | `makeMirror204(W, { k, glowX, glowD, glow })` | a tall dark frame (0.86 × 1.86 m glass) on the walled-up doorway; `k < 1` assembles it from 6 × 12 glossy blocks in a seeded order (frame first), `k = 1` is a real reflection; a faint cold light from the glass. Sheet: `REF_mirror204.png` |
| **Camera-only layer** | `cameraOnly(obj)` + `camera.layers.enable(2)` | the young Alex is seen by the camera but not by the mirror, so the glass shows only the old Alex (`mirrorOnly`) where his reflection should be — the only deliberate difference in the reflection; the room, the table and the phones reflect correctly |
| Palm on the glass | `makeOpenHand(false)` on layer 1 | the old Alex's open hand pressed to the mirror (reflection only) |
| Alex portrait | shot `E6_alex_portrait` | photo for the final choice card «СЕБЯ» (same warm style as the sister's EP04 photo on «СЕСТРУ») |

All on-screen Russian text (the recording's caption, the attempt counter, the countdown, the last task and the choice) is drawn
only by `scripts/phone_ui.py` with the series font (Rubik), never inside a rendered image.
