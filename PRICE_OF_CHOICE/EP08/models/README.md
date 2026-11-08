# EP08 — 3D models

As in EP01–EP07 there are no separate model files: every character, prop and room is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP08 uses the EP07 copy of that world and only adds to it.
EP07 frames reused unchanged are read from `../EP07/scenes` (`E7_mon` — EP07's last shot, `E7_feedm_*` — the sister's feed lip-sync).

## Production names (code and docs only — never on screen)

| Name | Who | How it is built |
|---|---|---|
| **ALEX_48** | the hero: an artificial copy, «48» on the wrist, the left hand being deleted | `makePerson('alex')` + `vanishLeft()` (EP07's `dissolve` on the left arm, cyan edge, fingertips first); macro: EP07's `makeForearm7({num: 1, clear: 1})` + `dissolve` |
| **ALEX_ORIGINAL** | the Alex at the kitchen table | `makePerson('alex')`, plain (no number, no deletion), `seatPerson()` |
| **ALEX_FIRST** | the voice behind the front door | **not built, never shown** — only the lock turning |

## Reused unchanged

| Model | Function | Notes |
|---|---|---|
| Alex | `makePerson('alex')` | same proportions, hoodie, face tokens (`wide_worried`, `side`, `down`, lip shapes) |
| The sister | `makePerson('sister')`, `buildOperatorRoom()` | EP04–EP07 model; `cold` face that speaks (EP07), `worried_open` |
| Flat 47 — entryway, padded front door, lock with thumb-turn, coat rack, shoe rack, hall mirror, bedroom doorway | `buildWorld()` | EP01 layout, **nothing moved** |
| The glass of water | `makeGlass()` | EP01's glass |
| Room 204, mirror 204's empty frame, the monitor room, live feed screens, voxel dissolve, the «48» forearm | EP05–EP07 functions | EP07 state: mirror shattered, monitor room behind it |

## New in EP08 (kept for future episodes — use these, do not redesign)

| Model / effect | Function | Notes |
|---|---|---|
| **Kitchen of flat 47** | `buildKitchen(W, {glass, lamp})` | behind the entryway's back doorway (x 0.3 ± 0.45, h 2.05) — **the same doorway the warm light always came from in EP01–EP03**. The back wall is rebuilt with a real opening in the same place (same wallpaper, same thickness); nothing else in the entryway moves. Checked floor tiles, oilcloth table under a red enamel pendant lamp, counter with sink, stove, fridge, radiator, night window onto the block across the yard. Sheet: `REF_kitchen.png` |
| **Glass falling and breaking** | `makeGlassBreak(k)` | EP01's glass tips off the table edge (k < 0.42), breaks: blocky shards, water cubes, a spreading puddle; k = 1 aftermath |
| **Knife** | `makeKnife()` | stylised kitchen knife (steel blade with a bright edge, black handle, two rivets). Only on the recording; no blood, no strike shown |
| **Monitor cracks** | `monitorCracks(screen, {k})` | mirror-204 crack language on a monitor screen (the punch); the same crack is drawn into the screen UI so it survives the overlay |
| **Monitor room being deleted** | `collapseMonitorRoom(W, k)` | ceiling first, then walls come apart into cubes with the cyan deletion edge; blocks drop and bounce; small monitors tear loose |
| **Flat 47 behind mirror 204's frame** | `flatBehindMirror(W, {k204, k, ajar})` | the *same* `buildWorld()` flat, moved and turned to face the monitor room (not a copy that could drift). Room 204 behind the frame dissolves out (`k204`) while the flat assembles (`k`) — the deletion run backwards. Its door's landing side (never seen before) gets the peephole ring, key cylinder, lever and a brass plate «47» in the series' 5×7 pixel digits |
| **Recording of tomorrow** | `recCast()` / `recCam()` (shots.js) | the flat's entryway: ALEX_48 by the door with the knife, ALEX_ORIGINAL facing him with raised hands; seen by a corner security camera (and live on the centre monitor) |
| Lock turning from outside | `lockTurn(u)` (shots.js) | EP01 S20's jerky thumb-turn motion: three tries, then the full turn |
| Reference sheets | `REF_kitchen.png`, `REF_versions.png` | the kitchen; ALEX_48 vs ALEX_ORIGINAL + knife + broken glass |

Small fixes in the EP08 copy of the world (EP07's files are untouched): `buildWorld` now names the back wall (`W.objs.backWall`)
so the kitchen can open it; the live feed screen no longer recurses when its camera can see its own screen; the monitor room's
second light sits under the ceiling in EP08 shots (it was at head height by the frame, where ALEX_48 now runs).

All on-screen Russian text (monitors, the recording's REC stamp, the timer, the phone's lock screen) is drawn only by
`scripts/phone_ui.py` / `scripts/06_render_video.py` with the series fonts (Rubik, PT Serif), never inside a rendered image.
The «47» on the door and the «48» on the wrist are pixel digits in 3D textures (no font).
