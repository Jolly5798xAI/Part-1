# ЦЕНА ВЫБОРА — EP08 «ЗАВТРАШНИЙ ДЕНЬ»

Eighth episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). Same style as EP01–EP07:
blocky low-poly 3D with night thriller lighting, every frame rendered from the same 3D world, so Alex, his sister, the monitor room
behind mirror 204 and flat 47 (EP01's entryway, door and lock) match the earlier episodes.

**Final file:** `renders/EP08_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 91.64 s = the MP3).
EP08 starts on EP07's last shot (the centre monitor with «Лесная, 12 · Квартира 47», «суббота, 7 ноября», «ЗАВТРА», EP07's end
framing) — ALEX_48 still in the monitor room, his left hand still being deleted — and ends on a hard cut to black on the last
word of EP01's first line, heard through the front door while the lock turns: «Мне заплатили пятьсот долларов за стакан воды…».

**Length.** The approved voiceover is **91.64 s** (1.64 s over the 75–90 s target; speech ends at 90.97 s). As instructed it was not
sped up, shortened or regenerated; the video is exactly as long as the MP3, with no intro, recap, end card or call to action.

* voiceover (final, unchanged, md5 `72d29ba8…666c`): `audio/ElevenLabs_2026-11-08T02_20_42_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP08_transcript.txt`](docs/EP08_transcript.txt) · VO check: [`docs/EP08_VO_REPORT.md`](docs/EP08_VO_REPORT.md)
* shot-by-shot plan, on-screen texts: [`docs/EP08_SHOT_PLAN.md`](docs/EP08_SHOT_PLAN.md)
* QC report: [`docs/EP08_QC.md`](docs/EP08_QC.md) · 3D additions (kitchen, knife, glass breaking, monitor cracks, the room being deleted, flat 47 behind the mirror frame): [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP08_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

## Story beats → picture
Monitor room: the address and tomorrow → the hand keeps vanishing → «Что будет завтра?» → the sister on her feed: «Ты убьёшь
настоящего Алекса» / «Ты его последняя копия» → the monitor shows tomorrow's recording (flat 47's security camera: ALEX_48 at the
front door with a knife, the other Alex facing him, pleading — cut before anything happens) → the fist cracks the screen → she
switches the recording off: «Тогда измени будущее» → the room starts to be deleted, the timer «Удаление через десять секунд» →
he runs to the broken mirror: room 204 behind the frame comes apart and flat 47's front door (brass plate «47») assembles there →
«Не бери нож!» → through the door on the last second → inside flat 47 the door shuts behind him → the phone: «Дата изменена»,
«Завтра наступило» → a glass breaks in the kitchen → he turns → ALEX_ORIGINAL at the kitchen table → «Ты пришёл раньше» →
«Прячься. Сейчас появится первый» → the key in the lock → «Мне заплатили пятьсот долларов за стакан воды…» → cut.

## Structure
```
EP08/
├─ audio/       the EP08 VO (unchanged); mix_ep08.wav / music_ep08.wav are generated, not stored in git
├─ scenes/      EP08 frames from the 3D world (stills in git; animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_kitchen, REF_versions (models are procedural)
├─ timeline/    transcript_words.json (word timings), vo_envelope.json (lip-sync), ep08_timeline.json (exported edit)
├─ subtitles/   EP08_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 9 new EP08 sounds (EP01–EP07 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP07 copy, switched to timeline_ep08) + render3d/ (scene.js, shots.js with the E8_* shots)
├─ renders/     EP08_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```
Shared, read-only resources: `../EP07/scenes` (`E7_mon` — EP07's last shot, `E7_feedm_*` — the sister's feed lip-sync, reused
unchanged), `../EP06/scenes`…`../EP02/illustrations` (meta only), `../EP02/effects/fonts`. EP01–EP07 files are not modified.

## Pipeline
Run from the `EP08/` folder.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine

python3 scripts/00_check_vo.py                       # VO intake check (read-only) -> docs/EP08_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model_dir> # word timings (faster-whisper small, CT2 int8)
python3 scripts/timeline_ep08.py                     # check + export the edit -> timeline/ep08_timeline.json
python3 scripts/02_render_illustrations.py           # every E8_* frame + reference sheets (~25 min; --scale 0.25 for tests)
python3 scripts/04_sound.py                          # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/08_shot_plan.py                      # docs/EP08_SHOT_PLAN.md from the timeline
python3 scripts/07_qc.py                             # QC of the finished file -> docs/EP08_QC.md + contact sheet
```
One command for the whole build: `bash scripts/build_ep08.sh`.

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (the sister's and both Alexes' lines are the narrator's).
Screen text is drawn only in code. Do not touch EP01–EP07 files. ALEX_48 / ALEX_ORIGINAL / ALEX_FIRST are production names only.
Do not show who is behind the door, how many copies exist, or how the loop works; nothing after the last line.
