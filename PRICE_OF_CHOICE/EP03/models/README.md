# EP03 — 3D models

The series has no separate model files: every character, prop and room is built in code, in one shared world,
so the cast and the flat look the same in every shot of every episode. EP03 uses the EP02 copy of that world
(`scripts/render3d/scene.js`) and only adds to it.

## Reused unchanged (same code as EP01/EP02)

| Model | Function in `scene.js` | Notes |
|---|---|---|
| Alex | `makePerson('alex')` | grey hoodie, jeans, dark socks, 16×16 pixel face |
| The double | `makePerson('alex', { bloodyRight: true })` | the same model as Alex; blood on the right hand |
| Police officer | `makePerson('cop')` | heard only in EP03 |
| Entryway, front door (flat 47), lock, peephole, shoe rack, coats | `buildWorld()` | same geometry and materials |
| Glass (empty), puddle | `makeGlass()`, `puddle()` in `shots.js` | EP02's aftermath stays in every hallway shot |
| Phone | `makePhone()` | the screen is drawn by `scripts/phone_ui.py` |

## New in EP03

| Model | Function | Notes |
|---|---|---|
| Bedroom | `buildBedroom()` (called from `buildWorld()`) | behind a doorway in the entryway's right wall (z 2.5–3.3): bed, nightstand, wardrobe, rug, moonlit window. EP01/EP02 cameras never see that part of the wall |
| Bedroom door | inside `buildBedroom()` | painted panel door, hinge on the wardrobe side, opens into the room (`bedDoor()` in `shots.js`) |
| Light leak under the bedroom door | `objs.bed.bleak` | colour/intensity per shot (the second phone's glow) |
| Hall mirror (real reflection) | `makeMirror()`, `enableMirror()` | a planar reflector (three.js Reflector, ported). The mirror's virtual camera also sees **layer 1**; objects put on layer 1 with `mirrorOnly()` exist only in the reflection. That is the second Alex in the mirror. The mirror is 0.62 × 1.0 m on the same wall and place as before (the earlier small 0.44 × 0.64 m one was never in frame) |
| Wet footprints | `makeFootprint()`, `footprints()` | blocky bare foot, glossy water material, droplets; trails are laid with `trail()` in `shots.js` |
| Chair | `makeChair()` | wooden, seat 0.46 m |
| Seated / tied pose | `seatPerson()`, `makeRopes()` | the standing rig has no knees, so legs are rebuilt as thigh + shin; arms behind the chair back; ropes round chest, wrists and ankles |
| Taped mouth, tears, eyes down/wide | face tokens in `faceVariant()` | e.g. `tape_worried_tears`; the tape is also a thin 3D strip so it catches light |

All doubles (in the mirror and on the chair) are the same `makePerson('alex')` model. No other face is used for Alex.
