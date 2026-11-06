# EP05 — 3D models

As in EP01–EP04 there are no separate model files: every character, prop and room is built in code in one shared
world (`scripts/render3d/scene.js`, shots in `shots.js`), so the cast and flat 47 look the same in every episode.
EP05 uses the EP04 copy of that world and only adds to it. EP04 frames reused unchanged are read from `../EP04/scenes`.

## Reused unchanged

| Model | Function | Notes |
|---|---|---|
| Alex, the tied double | `makePerson('alex')`, `tiedMan4()` | the double stays pale with the red tape mark (EP04 face tokens `worried_redmark_pale`) |
| Masked officer | `makePerson('cop', { face: 'mask', gloves: true })` | EP04 balaclava + gloves, sheet `../EP04/models/REF_masked_cop.png` |
| **Alex's sister** | `makePerson('sister')` | **the EP04 model, not redesigned** (sheet `../EP04/models/REF_sister.png`): long dark hair, mustard sweater with white collar and pendant, jeans, white sneakers. With the default face she is pixel-identical to EP04 |
| Flat 47 (Лесная, 12): hallway, front door, mirror, bedroom, chair | `buildWorld()`, `buildBedroom()` | the stairwell geometry is now inside a group `W.objs.stairwell` (identity transform, same meshes) so it can be hidden |
| Alex's cracked phone | `E4_phone_floor` framing + `phone_ui.py` `crack: 7` | the same seeded crack, now with a live screen under it |

## New in EP05 (kept for future episodes — use these, do not redesign)

| Model | Function | Notes |
|---|---|---|
| **Key of room 204** | `makeKey()` | old brass key on a ring + burgundy hotel fob; «204» in the same 5×7 pixel digits as the EP04 door plate (`plateTex`, no fonts). Origin = top of the ring; `userData.fob` is the fob pivot so it can hang straight. Sheet: `REF_key204.png` |
| **Door 204** | `makeDoor204()` | the EP04 insert door (`E4_room204`) with the same sizes, colours and plate — now hinged (right) with a keyhole under the handle; `pivot.rotation.y` opens it |
| **Hotel corridor** | `buildCorridor(W, {L, sconces, red, gap, feet, open, phonesOn})` | replaces the stairwell straight behind flat 47's front door: 13 m, two-tone walls in the door-204 palette, wooden room doors with blank plates, sconces, burgundy runner. Sheet: `REF_corridor.png` |
| **Red lamp** | inside `buildCorridor` (`red`) | caged red bulb above door 204, shadow-casting red point light |
| **Light under door 204** | `gap: 1`, `feet: 1` | cold strip of light; `feet` adds the shadows of someone standing behind the door |
| **Room 204 + table of phones** | inside `buildCorridor` (`phonesOn`) | dark room behind door 204, a table with 35 phones (7×5, seeded layout). `W.objs.corridor.screens` → `meta.screens` (one screen quad per phone) so the editor draws the message on every screen in code. Sheet: `REF_room204.png` |
| **Sister's mouth shapes** | `sisterFace(variant)` in `scene.js` | tokens `worried`, `open`, `ee`, `oo`, `down`, combined with `_`, for lip-sync. Sheet: `REF_sister_mouths.png` |

On-screen Russian text (phone messages) is drawn only by `scripts/phone_ui.py` with the series font (Rubik), never inside
a generated image. The numbers on the fob and the door are pixel digits drawn in code.
