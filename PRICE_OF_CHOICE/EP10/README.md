# ЦЕНА ВЫБОРА — EP10 «СОЗДАТЕЛЬ»

Tenth episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). Same style as EP01–EP09: blocky low-poly 3D,
night thriller lighting, every frame rendered from the same 3D world (flat 47, room 204, the hotel corridor; ALEX_48 / ALEX_49 /
ALEX_ZERO / the old officer / the sister with their established models).

**Final file:** `renders/EP10_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, = the MP3's length).
EP10 opens on EP09's last frame (the officer's red phone, «Оригинал должен умереть») — the same second, no recap — and ends on door 204
under its red lamp after the sister's scream: hard cut to black on the last word.

**Length.** The approved voiceover is **121.81 s** (speech 0.12–121.73 s): **31.8 s over** the 75–90 s target. As instructed it was not
sped up, shortened or regenerated; the video is exactly as long as the MP3, with no intro, recap, end card or call to action.

* voiceover (final, unchanged, md5 `f09ce98e…920d`): `audio/ElevenLabs_2026-11-11T01_39_45_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP10_transcript.txt`](docs/EP10_transcript.txt) · VO check: [`docs/EP10_VO_REPORT.md`](docs/EP10_VO_REPORT.md)
* shot plan with on-screen texts: [`docs/EP10_SHOT_PLAN.md`](docs/EP10_SHOT_PLAN.md) · QC: [`docs/EP10_QC.md`](docs/EP10_QC.md) · 3D additions: [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP10_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

**The sister's name.** «Елена» is spoken for the first time in EP10's voiceover; EP01–EP09 never name her (checked: transcripts, docs, code), so there is no conflict.

## Story beats → picture
EP09's red phone → the officer swings it onto ALEX_ZERO → ALEX_ZERO doesn't move → ALEX_48: «Почему именно он?» → old Alex: «Потому что он
создал нас» → ALEX_ZERO raises his head: «Я создал игру. Но не для этого» → every phone in the hall lights up: a grid of Alex's face
zooming out to hundreds → «Те, кто не прошёл испытания» → ALEX_48's hand dissolving → «А деньги? Задания? Стакан воды?» → «Мы проверяли,
способен ли ты отказаться. Каждый раз ты выбирал награду» → EP01 flashback: the glass by the door, +500 $ → «Но я не знал…» — «Теперь
знаешь» → the officer holds out his phone: «Уничтожить оригинал» / «Остановить игру» → the thumb presses «Остановить игру» → red →
«Недостаточно прав» → the officer afraid: «Этого не должно быть!» → the sister's voice from every phone: «Потому что создатель — не он» →
ALEX_ZERO turns → the video: room 204 (the table of lit phones), the sister at a computer → «Проект «Алекс»» → «Создатель: Елена» →
ALEX_ZERO starts to disappear → the officer drops to his knees → the sister into the lens: «Поздравляю, Алекс! Ты наконец дошёл до
последнего уровня» → the phone dies → «Уровень десять завершён» → «Следующий игрок: Елена» → her scream → door 204 → cut.

## Structure
```
EP10/
├─ audio/       the EP10 VO (unchanged); mix_ep10.wav / music_ep10.wav are generated, not stored in git
├─ scenes/      EP10 stills from the 3D world (animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_versions10, REF_room204_desk (models are procedural)
├─ timeline/    transcript_words.json (phrase/word timings), vo_envelope.json (lip-sync), ep10_timeline.json (exported edit)
├─ subtitles/   EP10_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 4 new EP10 sounds (EP01–EP09 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP09 copy, switched to timeline_ep10) + render3d/ (scene.js, shots.js with the E10_* shots)
├─ renders/     EP10_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```

## Pipeline
Run from the `EP10/` folder.
```bash
pip install scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine
python3 scripts/00_check_vo.py               # VO intake check (read-only) -> docs/EP10_VO_REPORT.md
python3 scripts/timeline_ep10.py             # check + export the edit -> timeline/ep10_timeline.json
python3 scripts/02_render_illustrations.py   # every E10_* frame + reference sheets (~25 min; --scale 0.3 for tests)
python3 scripts/04_sound.py                  # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py              # SRT
python3 scripts/06_render_video.py           # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/08_shot_plan.py              # docs/EP10_SHOT_PLAN.md
python3 scripts/07_qc.py                     # QC of the finished file -> docs/EP10_QC.md + contact sheet
```
Word timings: Hugging Face was not reachable from the build machine, so instead of `01_transcribe.py` (faster-whisper) the VO was
transcribed with the same Whisper *small* model in its sherpa-onnx export (GitHub release `k2-fsa/sherpa-onnx` asr-models), cut at the
VO's own pauses; the stored `timeline/transcript_words.json` is what the build uses.

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (every line is the narrator's). Screen text is drawn only in code.
Do not touch EP01–EP09 files. The scream is a short procedural, wordless, muffled cry made in `04_sound.py` (no third-party audio).
Do not show what happened to the sister, who runs the game now, or anything of EP11.
