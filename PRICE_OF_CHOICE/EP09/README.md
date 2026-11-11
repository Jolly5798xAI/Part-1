# ЦЕНА ВЫБОРА — EP09 «ПЕРВЫЙ АЛЕКС»

Ninth episode of the vertical mini-series (TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC). Same style as EP01–EP08:
blocky low-poly 3D with night thriller lighting, every frame rendered from the same 3D world, so Alex (all four versions of him),
his sister, the police officer and flat 47 (EP01's entryway, door and lock, EP08's kitchen) match the earlier episodes.

**Final file:** `renders/EP09_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 96.13 s = the MP3).
EP09 starts on EP08's last frame (the front door's lock close-up, the thumb-turn fully turned, EP08's end framing) — the same second,
his own voice behind the door — and ends on a hard cut to black on the last word of «Оригинал должен умереть».

**Length.** The approved voiceover is **96.13 s** (6.13 s over the 75–90 s target; speech ends at 96.02 s). As instructed it was not
sped up, shortened or regenerated; the video is exactly as long as the MP3, with no intro, recap, end card or call to action.

* voiceover (final, unchanged, md5 `62650f06…e1d1`): `audio/ElevenLabs_2026-11-10T23_44_38_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP09_transcript.txt`](docs/EP09_transcript.txt) · VO check: [`docs/EP09_VO_REPORT.md`](docs/EP09_VO_REPORT.md)
* shot-by-shot plan, on-screen texts: [`docs/EP09_SHOT_PLAN.md`](docs/EP09_SHOT_PLAN.md)
* QC report: [`docs/EP09_QC.md`](docs/EP09_QC.md) · 3D additions (wrist numbers 49 / 0, the unmasked officer, the balaclava, the strike on the phone, the cracked screen, the final screen): [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP09_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

## Story beats → picture
The lock, his voice behind the door → ALEX_48 frozen in the hall → ALEX_ZERO grabs his shoulder: «Прячься! Он не должен нас увидеть»
→ both flat against the kitchen wall either side of the doorway → the latch clicks, the door opens: ALEX_49 walks in with the glass of
water → the cyan «49» lights up on his wrist → ALEX_48 looks at his own «48» (the hand still being deleted) → «Почему он следующий?» →
«Потому что тебя уже списали» → ALEX_49's phone: «Задание выполнено», «Уничтожить предыдущую копию» → he turns his head straight into
the lens → ALEX_48 backs off; ALEX_ZERO takes the knife from the table → EP08's recording: the same knife → ALEX_ZERO comes at ALEX_48
with it… and chops it down onto the phone → the phone on the tiles, the screen cracks → the three of them over it → the sister through
the broken screen: «Алекс, не верь оригиналу!» → ALEX_ZERO freezes, his face changes → a red «0» burns up on his wrist → «Теперь ты
понимаешь, почему я не могу выйти отсюда?» → the front door opens again → the officer on the threshold, backlit, the balaclava in his
hand → his face: old Alex → he holds out his phone: «Создатель обнаружен», «Начать последнюю проверку», «Оригинал должен умереть» → cut.

## Structure
```
EP09/
├─ audio/       the EP09 VO (unchanged); mix_ep09.wav / music_ep09.wav are generated, not stored in git
├─ scenes/      EP09 frames from the 3D world (stills in git; animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_versions9, REF_wrists9 (models are procedural)
├─ timeline/    transcript_words.json (word timings), vo_envelope.json (lip-sync), ep09_timeline.json (exported edit)
├─ subtitles/   EP09_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 3 new EP09 sounds (EP01–EP08 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP08 copy, switched to timeline_ep09) + render3d/ (scene.js, shots.js with the E9_* shots)
├─ renders/     EP09_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```
Shared, read-only resources: `../EP08/scenes` (`E8_rec_knife` — the recording of tomorrow, `E8_feedc_*` — the sister's close feed
lip-sync, reused unchanged), `../EP07/scenes`…`../EP02/illustrations` (meta only), `../EP02/effects/fonts`. EP01–EP08 files are not modified.

## Pipeline
Run from the `EP09/` folder.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine

python3 scripts/00_check_vo.py                       # VO intake check (read-only) -> docs/EP09_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model_dir> # word timings (faster-whisper small, CT2 int8)
python3 scripts/timeline_ep09.py                     # check + export the edit -> timeline/ep09_timeline.json
python3 scripts/02_render_illustrations.py           # every E9_* frame + reference sheets (~13 min; --scale 0.25 for tests)
python3 scripts/04_sound.py                          # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/08_shot_plan.py                      # docs/EP09_SHOT_PLAN.md from the timeline
python3 scripts/07_qc.py                             # QC of the finished file -> docs/EP09_QC.md + contact sheet
```
One command for the whole build: `bash scripts/build_ep09.sh`.

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (the sister's and the Alexes' lines are the narrator's).
Screen text is drawn only in code. Do not touch EP01–EP08 files. ALEX_48 / ALEX_49 / ALEX_ZERO / ALEX_OLD_POLICE are production names only.
Do not show the original's death, who really runs the game, or what «0» finally means; nothing after the last line.
