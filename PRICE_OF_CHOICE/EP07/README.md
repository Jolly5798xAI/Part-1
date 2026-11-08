# ЦЕНА ВЫБОРА — EP07 «ТОТ, КОГО СТЁРЛИ»

Seventh episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). Same style as EP01–EP06:
blocky low-poly 3D with night thriller lighting, every frame rendered from the same 3D world, so Alex, the old Alex (EP06),
his sister (EP04 model), room 204, mirror 204 and the table of phones match EP06.

**Final file:** `renders/EP07_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 103.15 s).
EP07 starts on EP06's last shot (the phone in the sister's hand with the choice «Сестру или себя», EP06's end framing) while the
VO repeats «Сестру… или себя…», and ends on a hard cut to black on the address «Лесная, 12 · Квартира 47» and «ЗАВТРА».

**Length.** The approved voiceover alone is **101.15 s** (more than the 75–90 s target). As instructed it was not sped up,
shortened or regenerated; the episode is the VO + a 2-second end card = 103.15 s.

* voiceover (final, unchanged, md5 `fde19fce…744b`): `audio/ElevenLabs_2026-11-08T01_07_44_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP07_transcript.txt`](docs/EP07_transcript.txt) · VO check: [`docs/EP07_VO_REPORT.md`](docs/EP07_VO_REPORT.md)
* shot-by-shot plan, on-screen texts, new sounds: [`docs/EP07_SHOT_PLAN.md`](docs/EP07_SHOT_PLAN.md)
* QC report: [`docs/EP07_QC.md`](docs/EP07_QC.md) · 3D additions (dissolve, cracks, shattering mirror, monitor room, operator room, the «48» forearm): [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP07_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

## Structure
```
EP07/
├─ audio/       the EP07 VO (unchanged); mix_ep07.wav / music_ep07.wav are generated, not stored in git
├─ scenes/      EP07 frames from the 3D world (stills in git; animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_monitor_room, REF_operator_room, REF_arm48 (models are procedural)
├─ timeline/    transcript_words.json (word timings), vo_envelope.json (lip-sync), ep07_timeline.json (exported edit)
├─ subtitles/   EP07_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 11 new EP07 sounds (EP01–EP06 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP06 copy, switched to timeline_ep07) + render3d/ (scene.js, shots.js with the E7_* shots)
├─ renders/     EP07_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```
Shared, read-only resources: `../EP06/scenes` (EP06 frames reused unchanged: `E6_show_cold`, `E6_sis_cold`, `E6_mirror_old`,
`E6_old_*`, `E6_room_red`, `E6_alex_portrait`), `../EP05/scenes`, `../EP04/scenes` (`E4_sister_photo`), `../EP02/effects/fonts`.
EP01–EP06 files are not modified.

## Pipeline
Run from the `EP07/` folder.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine

python3 scripts/00_check_vo.py                       # VO intake check (read-only) -> docs/EP07_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model_dir> # word timings (faster-whisper small, CT2 int8)
python3 scripts/timeline_ep07.py                     # check + export the edit -> timeline/ep07_timeline.json
python3 scripts/02_render_illustrations.py           # every E7_* frame + reference sheets (~30 min; --scale 0.25 for tests)
python3 scripts/04_sound.py                          # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/07_qc.py                             # QC of the finished file -> docs/EP07_QC.md + contact sheet
```
One command for the whole build: `bash scripts/build_ep07.sh`.

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (the sister's and the old Alex's lines are the narrator's).
Screen text is drawn only in code. Do not touch EP01–EP06 files. Do not reveal where the real Alex is, do not explain who runs
the system, do not show the next day.
