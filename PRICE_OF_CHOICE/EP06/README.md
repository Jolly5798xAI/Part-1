# ЦЕНА ВЫБОРА — EP06 «ПЕРВАЯ ПОПЫТКА»

Sixth episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). Same style as EP01–EP05:
blocky low-poly 3D with night thriller lighting, every frame rendered from the same 3D world, so Alex, his sister (EP04 model),
room 204 and the table of phones match EP05.

**Final file:** `renders/EP06_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 88.30 s).
EP06 starts on EP05's last shot (the sister's close-up behind Alex in room 204, while the VO repeats «Зачем ты снова запустил игру?»)
and ends on a hard cut to black on the choice «Сестру… или себя».

* voiceover (final, unchanged, 85.89 s): `audio/ElevenLabs_2026-11-08T00_02_37_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP06_transcript.txt`](docs/EP06_transcript.txt) · VO check: [`docs/EP06_VO_REPORT.md`](docs/EP06_VO_REPORT.md)
* shot-by-shot plan, on-screen texts, new sounds: [`docs/EP06_SHOT_PLAN.md`](docs/EP06_SHOT_PLAN.md)
* QC report: [`docs/EP06_QC.md`](docs/EP06_QC.md) · 3D additions (old Alex, the sister's cold face, walled-up doorway, mirror 204): [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP06_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

## Structure
```
EP06/
├─ audio/       the EP06 VO (unchanged); mix_ep06.wav / music_ep06.wav are generated, not stored in git
├─ scenes/      EP06 frames from the 3D world (stills in git; animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_old_alex, REF_sister_cold, REF_mirror204 (models are procedural)
├─ timeline/    transcript_words.json (word timings), vo_envelope.json (lip-sync), ep06_timeline.json (exported edit)
├─ subtitles/   EP06_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 8 new EP06 sounds (EP01–EP05 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP05 copy, switched to timeline_ep06) + render3d/ (scene.js, shots.js with the E6_* shots)
├─ renders/     EP06_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```
Shared, read-only resources: `../EP05/scenes` (EP05 frames reused unchanged: `E5_sis_*`, `E5_room_lit`, `E5_phones_low`,
`E5_phone_hero`), `../EP04/scenes` (`E4_sister_photo`), `../EP03/scenes`, `../EP02/illustrations`, `../EP02/effects/fonts`.
EP01–EP05 files are not modified.

## Pipeline
Run from the `EP06/` folder.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine

python3 scripts/00_check_vo.py                       # VO intake check (read-only) -> docs/EP06_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model_dir> # word timings (NB: the stored file has a hand-corrected tail, see the transcript)
python3 scripts/timeline_ep06.py                     # check + export the edit -> timeline/ep06_timeline.json
python3 scripts/02_render_illustrations.py           # every E6_* frame + reference sheets (~20 min; --scale 0.25 for tests)
python3 scripts/04_sound.py                          # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/07_qc.py                             # QC of the finished file -> docs/EP06_QC.md + contact sheet
```
One command for the whole build: `bash scripts/build_ep06.sh`.

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (the sister's and the old Alex's lines are the narrator's).
Phone text is drawn only in code. Do not touch EP01–EP05 files. Do not show Alex's choice, do not reveal whether she is
really his sister, do not explain the game or how the memory is erased.
