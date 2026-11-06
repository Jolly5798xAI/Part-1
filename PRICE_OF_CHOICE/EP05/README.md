# ЦЕНА ВЫБОРА — EP05 «КОМНАТА 204»

Fifth episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). Same style as EP01–EP04:
blocky low-poly 3D with night thriller lighting. Every frame is rendered from the same 3D world, so Alex, the tied double,
the masked officer, the sister (EP04 model), flat 47 (Лесная, 12) and its hallway and bedroom match the earlier episodes.

**Final file:** `renders/EP05_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 88.60 s).
EP05 starts on EP04's last frame (the officer's phone with the sister's photo and her played voice message, while the VO says
«…не открывай дверь») and ends on a hard cut to black on «…зачем ты снова запустил игру?».

* voiceover (final, unchanged, 86.13 s): `audio/ElevenLabs_2026-11-06T14_00_00_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP05_transcript.txt`](docs/EP05_transcript.txt) · VO check: [`docs/EP05_VO_REPORT.md`](docs/EP05_VO_REPORT.md)
* shot-by-shot plan, on-screen texts, key moments, new sounds: [`docs/EP05_SHOT_PLAN.md`](docs/EP05_SHOT_PLAN.md)
* QC report: [`docs/EP05_QC.md`](docs/EP05_QC.md) · 3D models (key 204, hotel corridor, door 204, room 204, sister's mouths): [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP05_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

## Structure
```
EP05/
├─ audio/       the EP05 VO (unchanged); mix_ep05.wav / music_ep05.wav are generated, not stored in git
├─ scenes/      EP05 frames from the 3D world (stills in git; animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_key204, REF_corridor, REF_room204, REF_sister_mouths (models are procedural)
├─ timeline/    transcript_words.json (word timings), vo_envelope.json (lip-sync), ep05_timeline.json (exported edit)
├─ subtitles/   EP05_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 7 new EP05 sounds (EP01–EP04 sounds and fonts are shared from ../EP02–../EP04, not copied)
├─ scripts/     pipeline (EP04 copy, switched to timeline_ep05) + render3d/ (scene.js, shots.js with the E5_* shots)
├─ renders/     EP05_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```
Shared, read-only resources: `../EP04/scenes` (EP04 frames reused unchanged: `E4_cop_phone_close`, `E4_sister_photo`,
`E4_dbl_pale_*`), `../EP03/scenes`, `../EP02/illustrations`, `../EP02/effects/fonts`. EP01–EP04 files are not modified.

## Pipeline
Run from the `EP05/` folder.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine

python3 scripts/00_check_vo.py                       # VO intake check (read-only) -> docs/EP05_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model_dir> # word timings -> timeline/transcript_words.json
#   faster-whisper small (CTranslate2 int8): npm packages @skillninja/shortmovie-telop-model-p0…p3,
#   concatenate model.bin.part0..3; sha256 ca732cb1…ce73 (same model as EP03/EP04)
python3 scripts/timeline_ep05.py                     # check + export the edit -> timeline/ep05_timeline.json
python3 scripts/02_render_illustrations.py           # every E5_* frame + reference sheets (~15 min; --scale 0.25 for tests)
python3 scripts/04_sound.py                          # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/07_qc.py                             # QC of the finished file -> docs/EP05_QC.md + contact sheet
```
One command for the whole build: `bash scripts/build_ep05.sh [whisper_model_dir]`.
`02_render_illustrations.py` writes the reference sheets into `scenes/`; they are kept in `models/`.

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (the sister's lines are the narrator's, as approved).
Phone text is drawn only in code; the numbers «204» are pixel digits in the 3D world. Do not touch EP01–EP04 files.
Do not explain the game, do not reveal whether Alex is its creator, who spoke behind door 204, or where the sister has been.
