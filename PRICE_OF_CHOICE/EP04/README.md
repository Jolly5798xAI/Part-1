# ЦЕНА ВЫБОРА — EP04 «НЕ ТОТ АЛЕКС»

Fourth episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). Same style as EP01–EP03:
blocky low-poly 3D with night thriller lighting. Every frame is rendered from the same 3D world, so Alex, the double,
the officer, flat 47 (Лесная, 12), the hall mirror and the bedroom match the earlier episodes exactly.

**Final file:** `renders/EP04_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 110.75 s).
EP04 starts on EP03's last frame (the tied double's wet eyes) and ends on a hard cut to black after «…не открывай дверь».

* voiceover (final, unchanged): `audio/ElevenLabs_2026-11-06T12_03_21_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP04_transcript.txt`](docs/EP04_transcript.txt) · VO check: [`docs/EP04_VO_REPORT.md`](docs/EP04_VO_REPORT.md)
* shot-by-shot plan, on-screen texts, key moments, new sounds: [`docs/EP04_SHOT_PLAN.md`](docs/EP04_SHOT_PLAN.md)
* QC report: [`docs/EP04_QC.md`](docs/EP04_QC.md) · 3D models (scar, masked officer, sister): [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP04_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

## Structure
```
EP04/
├─ audio/       the EP04 VO (unchanged); mix_ep04.wav / music_ep04.wav are generated, not stored in git
├─ scenes/      EP04 frames from the 3D world (stills in git; animation frame folders are regenerated) + meta.json
├─ models/      README + character sheets REF_sister.png, REF_masked_cop.png (all models are procedural, in scripts/render3d)
├─ timeline/    transcript_words.json (word timings), vo_envelope.json (lip-sync), ep04_timeline.json (exported edit)
├─ subtitles/   EP04_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 10 new EP04 sounds (EP01–EP03 sounds and fonts are shared from ../EP02, ../EP03, not copied)
├─ scripts/     pipeline (EP03 copy, switched to timeline_ep04) + render3d/ (scene.js, shots.js with the E4_* shots)
├─ renders/     EP04_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```
Shared, read-only resources: `../EP03/scenes` (EP03 frames reused unchanged: `E3_tied_face_tears_eyes`, `E3_tied_face_tears`,
`E3_pov_room_close`), `../EP02/illustrations/E2_photo_cop.png`, `../EP02/effects/fonts`, `../EP02/effects/sfx`, `../EP03/effects/sfx`.
EP01–EP03 files are not modified.

## Pipeline
Run from the `EP04/` folder.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine

python3 scripts/00_check_vo.py                       # VO intake check (read-only) -> docs/EP04_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model_dir> # word timings -> timeline/transcript_words.json
#   faster-whisper small (CTranslate2 int8): npm packages @skillninja/shortmovie-telop-model-p0…p3,
#   concatenate model.bin.part0..3; sha256 ca732cb1…ce73 is checked (same model as EP03)
python3 scripts/timeline_ep04.py                     # check + export the edit -> timeline/ep04_timeline.json
python3 scripts/02_render_illustrations.py           # every E4_* frame (~20 min; --scale 0.25 for quick tests)
python3 scripts/04_sound.py                          # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/07_qc.py                             # QC of the finished file -> docs/EP04_QC.md + contact sheet
```
One command for the whole build: `bash scripts/build_ep04.sh [whisper_model_dir]`.

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (the sister's line is the narrator's, as approved).
Phone and mirror text is drawn only in code. Do not touch EP01–EP03 files. Do not reveal where the sister is, where
the doubles come from, or what room 204 is.
