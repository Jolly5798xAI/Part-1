# ЦЕНА ВЫБОРА — EP03 «КТО ЗА МОЕЙ СПИНОЙ?»

Third episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). The style is the same as in
EP01/EP02: blocky low-poly 3D with night thriller lighting. Every frame is rendered from the same 3D world, so Alex, the
double, the officer, flat 47 and the front door match the earlier episodes exactly.

**Final file:** `renders/EP03_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 105.3 s).
EP03 picks up on EP02's last shot, the double whispering «Ты выбрал не того», and ends on a hard cut to black.

* voiceover (final, unchanged): `audio/ElevenLabs_2026-11-06T10_51_16_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP03_transcript.txt`](docs/EP03_transcript.txt) · VO check: [`docs/EP03_VO_REPORT.md`](docs/EP03_VO_REPORT.md)
* shot-by-shot plan, mirror method, phone texts, new sounds: [`docs/EP03_SHOT_PLAN.md`](docs/EP03_SHOT_PLAN.md)
* QC report: [`docs/EP03_QC.md`](docs/EP03_QC.md) · 3D models: [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP03_PRICE_OF_CHOICE.srt` (the same subtitles are also burned into the MP4)

## Structure
```
EP03/
├─ audio/       the EP03 VO (unchanged); mix_ep03.wav / music_ep03.wav are generated, not stored in git
├─ scenes/      EP03 frames rendered from the 3D world (stills in git; animation frame folders are regenerated) + meta.json
├─ models/      README: which code builds each model (all models are procedural, in scripts/render3d/scene.js)
├─ timeline/    transcript_words.json (word timings), ep03_timeline.json (exported edit)
├─ subtitles/   EP03_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 12 new EP03 sounds (EP01/EP02 sounds and fonts are shared from ../EP02/effects, not copied)
├─ scripts/     pipeline (EP02 copy, switched to timeline_ep03) + render3d/ (scene.js, shots.js with the E3_* shots)
├─ renders/     EP03_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC
```
Shared, read-only resources from EP02: `../EP02/illustrations` (3 EP01/EP02 frames reused unchanged: `E2_double_ear_*`,
`E2_double_behind`, `S13_door_bang`), `../EP02/effects/fonts`, `../EP02/effects/sfx`. EP01 and EP02 files are not modified.

## Pipeline
Run from the `EP03/` folder.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine

python3 scripts/00_check_vo.py                       # VO intake check (read-only) -> docs/EP03_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model_dir> # word timings -> timeline/transcript_words.json
#   faster-whisper small (CTranslate2 int8). HuggingFace is not reachable here, so the model comes from npm packages
#   @skillninja/shortmovie-telop-model-p0…p3: concatenate model.bin.part0..3; sha256 ca732cb1…ce73 is checked
python3 scripts/timeline_ep03.py                     # check + export the edit -> timeline/ep03_timeline.json
python3 scripts/02_render_illustrations.py           # every E3_* frame (~12 min; --scale 0.25 for quick tests)
python3 scripts/04_sound.py                          # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/07_qc.py                             # QC of the finished file -> docs/EP03_QC.md + contact sheet
```
One command for the whole build: `bash scripts/build_ep03.sh <whisper_model_dir>`.

## Rules
Do not replace, speed up or re-pitch the voice. Phone text is drawn only in code. Do not touch EP01/EP02 files.
Do not reveal who the original is. Do not show Alex carrying out the order.
