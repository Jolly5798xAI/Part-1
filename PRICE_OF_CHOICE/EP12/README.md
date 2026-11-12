# ЦЕНА ВЫБОРА — EP12 «ПЕРВОЕ ИСПЫТАНИЕ»

Twelfth episode (season-1 final arc, finale planned for EP15). TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC. Same style as EP01–EP11:
blocky low-poly 3D, night thriller lighting, every frame rendered from the same 3D world (room 204 with the turned computer, the chained
sister, flat 47's kitchen) plus two new sets: a night road in the rain and the car.

**Final file:** `renders/EP12_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 110.92 s = the MP3).
EP12 opens on EP11's last frame — the computer turned to ALEX_48, the original's face, «Оригинал проснулся» still on it — same second, no
recap; it ends dead on «Не верь мне» with ELENA_204 beside ALEX_48 and ELENA_APARTMENT on the side monitor's live feed.

**Length.** The approved voiceover is **110.92 s** (speech 0.15–110.92 s): **20.9 s over** the 75–90 s target. As instructed it was not
sped up, shortened or regenerated; the video is exactly as long as the MP3, with no intro, recap or end card.

* voiceover (final, unchanged, md5 `097cedfe…0faf69a2`): `audio/ElevenLabs_2026-11-12T22_43_31_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP12_transcript.txt`](docs/EP12_transcript.txt) · VO check: [`docs/EP12_VO_REPORT.md`](docs/EP12_VO_REPORT.md)
* shot plan with on-screen texts: [`docs/EP12_SHOT_PLAN.md`](docs/EP12_SHOT_PLAN.md) · QC: [`docs/EP12_QC.md`](docs/EP12_QC.md) · 3D additions: [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP12_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

**VO notes.** The VO opens by repeating «Оригинал проснулся» (EP11's last screen line) — the picture shows that screen. «Не верь мне» is read
by the narrator («обе одновременно сказали»): both Elenas mouth it in sync, no second voice was made.

## Story beats → picture
«Оригинал проснулся» on the turned screen → the face blinks and opens its eyes → «Сорок восемь. Ты должен исчезнуть» (the face lip-syncs) →
ALEX_48 steps back → «Почему?» → «Потому что ты вспомнил аварию» → the chained sister: «Не слушай его!» → the screen flashes white →
the recording (REC): a car on a country road at night in the rain → wipers → Alex at the wheel → the sister beside him → the dashboard
phone buzzes: «Первое задание», «Не тормози», «Награда — пятьсот долларов» → a hooded figure in the headlights → his foot slams the brake →
side-on: brake lights burning, wheels locked, the car still sliding → static: the recording dies before anything happens → the sister looks
down, says nothing → the original smirks: «А теперь покажи ему остальное» → the second recording: the sister alone at the computer in
room 204 typing «> Повторить испытание» → «Ты запускала его снова?» → she cries: «Я пыталась найти версию, которая спасёт нас обоих» →
47 red copies on the screen, one lit cyan: «Сорок семь копий выбрали деньги. А ты нажал на тормоз» → the disappearing hand → «Значит, я прошёл
испытание?» — «Да» → the original afraid: «И поэтому система выбрала тебя» → the cuffs spring open, cuffs and chains drop to the floor →
«Передача управления», «Новый администратор:» «48» → he raises his hand → the blocks fly back, the hand is whole → the side monitor lights:
«Прямой эфир», «Квартира 47», Elena at the kitchen table → he turns: Elena is still beside him → «Обнаружены две Елены» → both: «Не верь мне» — end.

## Structure
```
EP12/
├─ audio/       the EP12 VO (unchanged); mix_ep12.wav / music_ep12.wav are generated, not stored in git
├─ scenes/      EP12 stills from the 3D world (animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_versions12, REF_car12 (models are procedural)
├─ timeline/    transcript_raw.json (ASR), transcript_words.json (verified phrases), vo_envelope.json (lip-sync), ep12_timeline.json
├─ subtitles/   EP12_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 13 new EP12 sounds (EP01–EP11 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP11 copy, switched to timeline_ep12) + render3d/ (scene.js, shots.js with the E12_* shots)
├─ renders/     EP12_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```

## Pipeline
Run from the `EP12/` folder (or `bash scripts/build_ep12.sh`). Needs `../EP11/scenes` (E11_face*, E11_sisr_*) and `../EP02/effects/fonts`.
```bash
pip install scipy fonttools brotli pillow numpy sherpa-onnx
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine
python3 scripts/00_check_vo.py               # VO intake check (read-only) -> docs/EP12_VO_REPORT.md
python3 scripts/01_transcribe.py <sherpa-onnx-whisper-small dir> && python3 scripts/01b_verified_transcript.py   # optional: timings are stored
python3 scripts/timeline_ep12.py             # check + export the edit -> timeline/ep12_timeline.json
python3 scripts/02_render_illustrations.py   # every E12_* frame + reference sheets (--scale 0.25 for tests)
python3 scripts/04_sound.py                  # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py              # SRT
python3 scripts/06_render_video.py           # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/08_shot_plan.py              # docs/EP12_SHOT_PLAN.md
python3 scripts/07_qc.py                     # QC of the finished file -> docs/EP12_QC.md + contact sheet
```

## Rules / open questions kept for EP13–EP15
Do not replace, speed up or re-pitch the voice; no second voice. Screen text is drawn only in code. Do not touch EP01–EP11 files.
Not shown, on purpose: why the system chose 48, why the original fears the handover, who sent the first task, which Elena is real and
where the second came from, whether the game can be destroyed with the real Alex and Elena alive. ALEX_ZERO is not on screen.
