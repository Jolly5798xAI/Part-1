# EP09 — 3D models

As in EP01–EP08 there are no separate model files: every character, prop and room is built in code in one shared world
(`scripts/render3d/scene.js`, shots in `shots.js`). EP09 uses the EP08 copy of that world and only adds to it (EP01–EP08 files untouched).
Reused unchanged from earlier episodes (read-only): `../EP08/scenes/E8_rec_knife.png` (the recording of tomorrow) and
`../EP08/scenes/E8_feedc_*` (the sister's close feed lip-sync).

## Production names (code and docs only — never on screen)

| Name | Who | How it is built |
|---|---|---|
| **ALEX_48** | the hero: «48» on the wrist, the left hand being deleted | `makePerson('alex')` + EP08's `vanishLeft()`; macro: EP07's `makeForearm7({num: 1})` + `dissolve` (`E9_wrist48`) |
| **ALEX_49** | the new copy who comes in with the glass of water | `makePerson('alex')` + EP01's `makeGlass()` in his left hand + **`wristBadge(p, '49', cyan)`**; macro: **`makeForearm9({text: '49'})`** |
| **ALEX_ZERO** | EP08's ALEX_ORIGINAL — the Alex from the kitchen table | `makePerson('alex')`, plain until the red **«0»** burns up (`wristBadge(p, '0', red)`, macro `makeForearm9({text: '0'})`); faces `worried`, `pale` |
| **ALEX_OLD_POLICE** | the officer from EP04–EP06, unmasked: old Alex | **`makeOldCop()`** = `makePerson('cop', {head: 'alex', face: 'old', gloves: true})` — the same police model and cap, with old Alex's head (EP06 `old` face) |

All four are the same base model: the differences are age, clothes, the state of the left hand and the number on the wrist.

## Reused unchanged

| Model | Function | Notes |
|---|---|---|
| Alex, the old face, the police model, the sister | `makePerson`, EP06 `old` token, EP04 cop | same proportions, face tokens, lip shapes |
| Flat 47 — entryway, padded front door, lock with thumb-turn, kitchen (EP08) | `buildWorld()`, `buildKitchen()` | EP01 layout, nothing moved; EP08's broken glass still on the kitchen floor |
| The glass of water | `makeGlass()` | EP01's glass (×1.35 in ALEX_49's hand) |
| The knife | `makeKnife()` | EP08's knife from the recording — now lying by the bread plate on the kitchen table (`flat9()`) |
| Lock close-up | EP08 shot `E8_lock` | re-rendered as `E9_lock`: EP09 opens on EP08's last frame |

## New in EP09 (kept for future episodes — use these, do not redesign)

| Model / effect | Function | Notes |
|---|---|---|
| Glowing wrist number (macro) | `wristNumTex(text, o)`, `makeForearm9({text, glow, g, flip})` | the EP04 scar + the number in the series' 5×7 pixel digits (×3), below the scar, lit from inside (emissive map); `g` 0..1 = how many pixels have surfaced / brightness. Digit «9» added to `DIGITS` |
| Glowing wrist number (full body) | `wristBadge(p, text, colour)` | small additive plane + light on the inside of the left cuff: «49» readable in medium shots |
| The unmasked officer | `makeOldCop()` + `makePerson(..., {head})` | `o.head` overrides the head kind (default unchanged for every earlier call) |
| The balaclava, taken off | `makeBalaclava()` | EP04's black mask as a soft blocky hood with the empty eye slit, hanging from his glove |
| Knife onto the phone | shot `E9_strike` | the knife chops down onto the phone in ALEX_49's hand; the phone flies to the tiles. No person is touched, no blood |
| Cracked phone screen | `phone_ui.draw_task9` (+ EP04 `draw_crack`, seed 909) | the crack is drawn into the screen UI; the same crack is laid over the sister's feed (`fx crackscreen`) — heard through the broken phone |
| Final screen | `phone_ui.draw_cop9` | «Создатель обнаружен», «Начать последнюю проверку», then the whole screen red: «Оригинал должен умереть» |
| Reference sheets | `REF_versions9.png`, `REF_wrists9.png` | the four versions side by side; forearms 48 / 49 / 0 |

All on-screen Russian text (phones) is drawn only by `scripts/phone_ui.py` with the series fonts (Rubik), never inside a rendered
image. The numbers on the wrists are pixel digits in 3D textures (no font).
