# ЦЕНА ВЫБОРА — EP13 «ПОСЛЕДНЯЯ КОПИЯ»

Thirteenth episode (third from the end of season 1; the finale is EP15). TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC. Same style as
EP01–EP12: blocky low-poly 3D, night-thriller lighting, every frame rendered from the same 3D world — room 204 after the handover, flat 47's
kitchen (on the live feed) and EP12's night road and car, seen from new angles.

**Final file:** `renders/EP13_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 116.61 s = the MP3).
EP13 opens on EP12's last frame — ELENA_1 beside ALEX_48, ELENA_0 on the side monitor, both saying «Не верь мне» — same second, no recap;
it ends dead on «…одновременно показали моё лицо»: every screen in room 204 shows ALEX_48's face, hard cut.

**Length.** The approved voiceover is **116.61 s** (speech 0.16–116.30 s): **26.6 s over** the 75–90 s target. This was reported before
editing; as instructed the voice was not sped up, shortened or regenerated — the video is exactly as long as the MP3, no intro, recap or end card.

* voiceover (final, unchanged, md5 `1b88f317…0de`): `audio/ElevenLabs_2026-11-13T01_03_09_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP13_transcript.txt`](docs/EP13_transcript.txt) · VO check: [`docs/EP13_VO_REPORT.md`](docs/EP13_VO_REPORT.md)
* shot plan with on-screen texts: [`docs/EP13_SHOT_PLAN.md`](docs/EP13_SHOT_PLAN.md) · QC: [`docs/EP13_QC.md`](docs/EP13_QC.md) · 3D additions: [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP13_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

**VO notes.** Every line is read by the narrator (ALEX_48) — both Elenas, the original and the system included; no second voice was made.
The VO adds small details the brief did not list («Я смотрел то на сестру, то на монитор», «Она врёт», «Она опустила глаза», «Я дёрнул руку»,
«Алекс.», «Какой?»): the picture follows the VO.

## Story beats → picture
EP12's last frame: both Elenas «Не верь мне» → ALEX_48 looks from ELENA_1 to the monitor and back → «Которая из вас настоящая?» → ELENA_1
raises her hand: a cold «1» lights on her wrist (macro) → on the feed ELENA_0 raises hers: a red «0» → «Я настоящая… а та, что рядом, создана
системой» (ELENA_0 lip-synced on the feed) → he steps back → ELENA_1 grabs his arm: «Она врёт. Проверь запись аварии» → he touches the screen:
the admin panel («Администратор: 48») → «Скрытая запись» lights red and plays → the hidden recording (REC, rain): high behind EP12's car on the
night road → from the back seat: the dashboard phone with EP12's task → the camera turns to the back seat: someone in the dark, his phone
lights his face — the real Alex, smirking → the second phone in his hands: «Отключить тормоза», he flips the switch, a red brake warning →
«Я замер» → «Ты сам устроил аварию?» → the original smiles on the screen: «Мне нужен был идеальный выбор» → ELENA_1: «Он проверял, кто
пожертвует собой» → the room goes red: «Обнаружена последняя копия» / «Номер сорок восемь» + «48» on the screen and on every phone on the
table → «А ты кто?» — she lowers her eyes — «Та, которая пыталась тебя остановить» → the choice: «Удалить все копии» / «Сохранить последнюю»,
under it «Цена — жизнь Елены» → he jerks his hand back: «Нет. Я не буду выбирать» → the original's face comes up through the choice: «Выбор
уже сделан» → the countdown 10 (screen), 9 (every phone), 8 (screen), then a small timer over the room → «Алекс. Есть третий вариант» —
«Какой?» → she points at his wrist → macro: «48» leaves pixel by pixel → «СОЗДАТЕЛЬ» burns in → «Для остановки игры удалите её создателя» →
every screen — the computer, the side monitor, every phone — shows ALEX_48's face → cut.

## Structure
```
EP13/
├─ audio/       the EP13 VO (unchanged); mix_ep13.wav / music_ep13.wav are generated, not stored in git
├─ scenes/      EP13 stills from the 3D world (animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_versions13, REF_car13 (models are procedural)
├─ timeline/    transcript_raw.json (ASR), transcript_words.json (verified phrases), vo_envelope.json (lip-sync), ep13_timeline.json
├─ subtitles/   EP13_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 9 new EP13 sounds (EP01–EP12 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP12 copy, switched to timeline_ep13) + render3d/ (scene.js, shots.js with the E13_* shots)
├─ renders/     EP13_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```

## Pipeline
Run from the `EP13/` folder (or `bash scripts/build_ep13.sh`). Needs `../EP12/scenes` (E12_two_*) and `../EP02/effects/fonts`.
```bash
pip install scipy fonttools brotli pillow numpy sherpa-onnx
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine
python3 scripts/00_check_vo.py               # VO intake check (read-only) -> docs/EP13_VO_REPORT.md
python3 scripts/01_transcribe.py <sherpa-onnx-whisper-small dir> && python3 scripts/01b_verified_transcript.py   # optional: timings are stored
python3 scripts/timeline_ep13.py             # check + export the edit -> timeline/ep13_timeline.json
python3 scripts/02_render_illustrations.py   # every E13_* frame + reference sheets (--scale 0.25 for tests)
python3 scripts/04_sound.py                  # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py              # SRT
python3 scripts/06_render_video.py           # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/08_shot_plan.py              # docs/EP13_SHOT_PLAN.md
python3 scripts/07_qc.py                     # QC of the finished file -> docs/EP13_QC.md + contact sheet
```

## Rules / open questions kept for EP14–EP15
Do not replace, speed up or re-pitch the voice; no second voice. Screen text is drawn only in code. Do not touch EP01–EP12 files.
Not shown, on purpose: why the system calls copy 48 its creator, who really started the first test, why the original disabled the brakes,
which Elena tells the truth, whether the game can be stopped without Elena dying, what deleting the creator would do. ALEX_ZERO is not on screen.
