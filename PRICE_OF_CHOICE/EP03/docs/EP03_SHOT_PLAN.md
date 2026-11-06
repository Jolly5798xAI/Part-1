# EP03 «КТО ЗА МОЕЙ СПИНОЙ?» — shot-by-shot edit plan

Voiceover: `audio/ElevenLabs_2026-11-06T10_51_16_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
(md5 `5c716325…`, 102.77 s, unchanged). Text checked against speech recognition: `docs/EP03_transcript.txt`.
The source of truth for the edit is `scripts/timeline_ep03.py`. This page describes it in plain language.

Running time: VO 0.00–102.77 → hard cut to black at 102.85 → end card «ЦЕНА ВЫБОРА · Серия 3 · «Кто за моей спиной?» ·
Продолжение следует» until 105.30. The episode is 105.3 s. That is longer than the 75–90 s target because the final VO
is 102.8 s, and the voice is not sped up.
1080×1920, 30 fps. The style, grade, subtitles (PT Serif, yellow and red highlights), phone UI and sound are the same as in EP01/EP02.

**Join with EP02.** EP02 ends on `E2_double_ear`: the double whispers «Ты выбрал не того» at Alex's ear, then cuts to black.
EP03 opens on the same frames (same lip shapes, same framing, zoom 1.12) while the VO repeats the line. There is no recap and no intro.

Key: **EP02** = frame from the earlier episodes, used unchanged (read from `../EP02/illustrations`). **NEW** = new scene in the same 3D world.

| # | Time, s | Shot | Source | Text / event | Sound |
|---|---|---|---|---|---|
| 1 | 0.00–1.25 | The double's face at Alex's ear, lips moving | EP02 `E2_double_ear_*` | «Ты выбрал не того» (big red subtitle) | |
| 2 | 1.25–4.80 | Down the hallway: Alex at the peephole, the double in the dark behind him; slow push | EP02 `E2_double_behind` | «Эти слова прозвучали прямо у моего уха» | breath |
| 3 | 4.80–6.25 | Alex whips round from the door | NEW `E3_turn` (24 frames) | «Я резко обернулся» | whoosh, cloth, shake |
| 4 | 6.25–7.95 | POV: the hallway is empty | NEW `E3_hall_empty` | «за спиной никого не было» | |
| 5 | 7.95–10.25 | Low angle: wet bare-foot prints appear one at a time from the puddle | NEW `E3_prints_appear` (40 frames) | «но на полу появились мокрые следы» | 8 wet steps, one per print |
| 6 | 10.25–13.60 | High angle: the trail goes from the door, past Alex, and ends in a pair facing him | NEW `E3_prints_path` | «Они вели от входной двери прямо ко мне» | |
| 7 | 13.60–17.35 | Floor level: Alex steps back; then a new pair of prints steps after him | NEW `E3_step_back` (40 frames) | «Я сделал шаг назад, следы тоже сдвинулись» | step, two wet steps at 15.62 / 15.98 |
| 8 | 17.35–20.45 | Side view: Alex against the door, facing prints that nobody stands in | NEW `E3_invisible` | «Будто кто-то невидимый…» | breath |
| 9 | 20.45–22.05 | POV: phone in hand, chat «Номер скрыт», typing… | NEW `E3_pov_door` + UI | «Телефон завибрировал» | vibration |
| 10 | 22.05–25.55 | Red message: «Третье задание. Найди того, кто стоит за твоей спиной.» | same, closer | quote | alert |
| 11 | 25.55–28.15 | + «Награда — пять тысяч долларов.» | same | quote | notify + coin |
| 12 | 28.15–30.40 | Alex at the hall mirror (wide) | NEW `E3_mirror_wide` | «Я посмотрел в зеркало в прихожей» | steps |
| 13 | 30.40–32.15 | Over his shoulder into the mirror: only his reflection | NEW `E3_mirror` | «в отражении стоял я» | |
| 14 | 32.15–35.30 | The same angle: **a second Alex in the reflection** behind him; push in | NEW `E3_mirror_dbl` | «а позади меня — ещё один Алекс» | sting + white flash 32.30 |
| 15 | 35.30–36.55 | Alex spins round toward the camera | NEW `E3_look_back` | «Я обернулся» | whoosh, cloth |
| 16 | 36.55–37.75 | His POV: nobody; a fresh pair of wet prints where the double stood | NEW `E3_behind_empty_m` | «никого» | low hit |
| 17 | 37.75–39.50 | Mirror close: both faces again | NEW `E3_mirror_dbl_close` | «Снова посмотрел в зеркало» | |
| 18 | 39.50–41.95 | In the mirror the double raises a finger to his lips. The real Alex does not move | NEW `E3_mirror_shh` (16 frames) | «Двойник поднял палец к губам» | breathy «тсс»; music almost silent |
| 19 | 41.95–44.10 | The double turns his head and points across, toward the front door | NEW `E3_mirror_point` (16 frames) | «и указал на входную дверь» | cloth |
| 20 | 44.10–46.75 | Front door from inside: prints, puddle, shadows of feet under the door | NEW `E3_door_outside` | «Снаружи послышался голос полицейского» | three muffled knocks |
| 21 | 46.75–49.45 | Door lever close-up | EP02 `S13_door_bang` | «Алекс, открой. Он уже внутри» | knock 46.70 |
| 22 | 49.45–52.45 | The lock: thumb-turn locked | NEW `E3_lock_closed` | «…он был закрыт» | lock click |
| 23 | 52.45–55.80 | The prints now lead from the mirror to the closed bedroom door | NEW `E3_prints_bedroom` | «…вели к моей спальне» | |
| 24 | 55.80–58.40 | POV dolly up to the bedroom door; cold light appears under it | NEW `E3_approach` (40 frames) | «Я медленно подошёл…» | three steps |
| 25 | 58.40–61.05 | Bedroom door close: phone light pulsing in the gap | NEW `E3_beddoor_close` | «…звук моего телефона» | muffled ringing and buzzing behind the door |
| 26 | 61.05–64.05 | POV: his own phone in his hand, screen off | NEW `E3_pov_beddoor` + UI | «…хотя настоящий телефон был у меня в руке» | |
| 27 | 64.05–66.55 | The screen wakes, typing… | same | «На экране появилось новое сообщение» | vibration |
| 28 | 66.55–70.05 | Red message: «Не входи. Там находится оригинал.» | same, closer | quote | alert |
| 29 | 70.05–72.10 | Alex's face in the phone light | NEW `E3_alex_face_bed` | «Я не понял, что это значит» | |
| 30 | 72.10–74.75 | POV: the bedroom door swings open by itself | NEW `E3_beddoor_open` (40 frames) | «пока дверь спальни не приоткрылась» | long creak |
| 31 | 74.75–77.05 | A man on a chair in the dark, against the moonlit window | NEW `E3_room_dark` | «В темноте сидел человек» | low hit |
| 32 | 77.05–80.30 | Tied to the chair, mouth taped over | NEW `E3_tied` | «…привязан к стулу с заклеенным ртом» | |
| 33 | 80.30–82.85 | Close-up: Alex's face | NEW `E3_tied_face` | «и у него было моё лицо» | sting + white flash 81.24 |
| 34 | 82.85–85.75 | He shakes his head desperately (three head angles cut fast) | NEW `E3_tied_head_{l,c,r}` | «…отчаянно замотал головой» | muffled «м-м-м!», chair creak |
| 35 | 85.75–88.30 | From behind the chair: his head turns down to the glowing phone in Alex's hand in the doorway | NEW `E3_from_chair` | «…посмотрел на телефон в моей руке» | |
| 36 | 88.30–91.95 | POV in the doorway: phone, the tied man beyond, typing… | NEW `E3_pov_room` + UI | «На экране появилось последнее сообщение» | vibration, riser |
| 37 | 91.95–95.65 | «Задание выполнено.» → «Объект найден.» | same, closer | quotes | two notifications |
| 38 | 95.65–97.85 | Red: «Теперь уничтожь копию.» | same, tighter, red glow, glitch | quote (big red subtitle) | alert + hit + red flash |
| 39 | 97.85–100.45 | The tied man's face, tears | NEW `E3_tied_face_tears` | «И в этот момент человек на стуле…» | muffled sobbing through the tape |
| 40 | 100.45–102.85 | Extreme close-up on his wet eyes | NEW `E3_tied_face_tears_eyes` | «…начал плакать моим голосом» | |
| 41 | 102.85–105.30 | **Hard cut to black** → end card | — | | music cut, sting + low tail |

The episode does not reveal who the original is, and Alex is never shown carrying out the order.

## Mirror: how the reflection is controlled

The hall mirror is a real planar reflection (render-to-texture from a reflected camera, with an oblique clip plane).
The reflection camera sees one extra render layer. The second Alex is put **only** on that layer (`mirrorOnly()`), so:
* the real camera never sees him. When Alex turns round (shots 15–16) the hallway is empty;
* the reflection of the real Alex stays physically correct in every frame;
* the double's gestures (finger to the lips, pointing at the door) happen only in the mirror. The real Alex stands still.

The gestures use the double's arm on the side away from Alex's reflection, so his reflection never covers them.

## Phone messages (`scripts/phone_ui.py`, drawn in code)

| Time | Message | Style |
|---|---|---|
| 22.16 | «Третье задание. Найди того, кто стоит за твоей спиной.» | red bubble |
| 25.72 | «Награда — пять тысяч долларов.» | bubble |
| 66.70 | «Не входи. Там находится оригинал.» | red bubble |
| 92.08 | «Задание выполнено.» | bubble |
| 93.56 | «Объект найден.» | bubble |
| 95.78 | «Теперь уничтожь копию.» | red bubble |

The chat is the same «Номер скрыт» thread as in EP01/EP02. Its first visible bubble is EP02's last message.
Clock 02:50 (EP02: 02:49). New in the UI: a sleeping screen (shot 26).

## New sounds (`scripts/04_sound.py`, synthesized, no third-party samples)
`whoosh`, `cloth`, `wet_step`, `step`, `breath`, `sting`, `sting_soft`, `knock_muffled`, `ring_muffled` (a phone behind a door),
`mmph` (a protest through tape), `chair_creak`, `sob` (crying through tape). The 24 EP01/EP02 one-shots are re-synthesized
bit-identically (checked against `../EP02/effects/sfx`).
