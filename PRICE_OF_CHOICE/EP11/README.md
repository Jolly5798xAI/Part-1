# ЦЕНА ВЫБОРА — EP11 «НУЛЕВОЙ УРОВЕНЬ»

Eleventh episode (first of the season-1 final arc, finale planned for EP15). TikTok, 9:16, 1080×1920, 30 fps, H.264 + AAC. Same style as
EP01–EP10: blocky low-poly 3D, night thriller lighting, every frame rendered from the same 3D world (the hotel corridor behind flat 47,
door 204, room 204 with the table of phones; ALEX_48 / ALEX_49 / ALEX_OLD_POLICE / the sister with their established models).

**Final file:** `renders/EP11_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 High + AAC 48 kHz stereo, 108.12 s = the MP3, 84.4 MB).
EP11 opens on EP10's last phone frame («Следующий игрок: Елена») and door 204 under its red lamp as her scream comes from behind it — the
same second, no recap — and ends dead on «Оригинал проснулся» on the turned screen (the speech runs to the very end of the MP3).

**Length.** The approved voiceover is **108.12 s** (speech 0.13–108.12 s): **18.1 s over** the 75–90 s target. As instructed it was not
sped up, shortened or regenerated; the video is exactly as long as the MP3, with no intro, recap, end card or call to action.

* voiceover (final, unchanged, md5 `5974a54f…542f`): `audio/ElevenLabs_2026-11-12T12_15_57_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* verified text: [`docs/EP11_transcript.txt`](docs/EP11_transcript.txt) · VO check: [`docs/EP11_VO_REPORT.md`](docs/EP11_VO_REPORT.md)
* shot plan with on-screen texts: [`docs/EP11_SHOT_PLAN.md`](docs/EP11_SHOT_PLAN.md) · QC: [`docs/EP11_QC.md`](docs/EP11_QC.md) · 3D additions: [`models/README.md`](models/README.md)
* subtitles: `subtitles/EP11_PRICE_OF_CHOICE.srt` (the same subtitles are burned into the MP4)

**VO notes.** The narration says «За ней *стояла* моя сестра, прикованная к креслу»; she is shown seated and chained, as the plot says.
The MP3 has no silent tail: «…проснулся» ends on the file's last sample, so the picture ends there too.

## Story beats → picture
«Следующий игрок: Елена» (EP10's phone) → her scream: door 204, red lamp → ALEX_48 runs down the corridor → the officer catches him at the
door: «Не входи. Там начинается нулевой уровень» → he tears free, throws the door open → the sister chained to her chair behind the
table of lit phones (cuffs, chains) → the screen in front of her: «Выберите, кого сохранить» / «Создателя» «или» «игрока» → «Алекс. Я не
создавала эту игру» → «Но на экране было твоё имя» → «Я создала только копии, чтобы спасти тебя» → she turns to the side monitor → the
hospital recording (REC 06.11.2023, three years before EP10's 06.11): Alex unconscious, bandage, drip, heart monitor → «Ты попал в аварию
три года назад…» → the recording breaks into copies of his face → his disappearing hand → «Значит, настоящий Алекс всё ещё жив?» → she
nods → the screen goes red: «Нулевой уровень активирован», «Удаление всех копий» → the officer falls apart in the doorway → ALEX_49 falls
apart in the corridor → ALEX_48 lunges for the computer → «Не трогай его!» — «Почему?» — «Потому что это не компьютер» → the screen swivels
round, light running along its cables → his face, eyes closed → the eyes open → «Елена, отойди от него. Эта копия уже знает слишком
много» (the face's mouth moves with the VO) → «Подключение к оригиналу установлено» → «Оригинал проснулся» — end.

## Structure
```
EP11/
├─ audio/       the EP11 VO (unchanged); mix_ep11.wav / music_ep11.wav are generated, not stored in git
├─ scenes/      EP11 stills from the 3D world (animation frame folders are regenerated) + meta.json
├─ models/      README + reference sheets REF_versions11, REF_room204_ep11, REF_hospital (models are procedural)
├─ timeline/    transcript_raw.json (ASR), transcript_words.json (verified phrases/words), vo_envelope.json (lip-sync), ep11_timeline.json
├─ subtitles/   EP11_PRICE_OF_CHOICE.srt
├─ effects/     sfx/: the 5 new EP11 sounds (EP01–EP10 sounds and fonts are shared, not copied)
├─ scripts/     pipeline (EP10 copy, switched to timeline_ep11) + render3d/ (scene.js, shots.js with the E11_* shots)
├─ renders/     EP11_PRICE_OF_CHOICE_FINAL.mp4
└─ docs/        transcript, VO report, shot plan, QC + contact sheet
```

## Pipeline
Run from the `EP11/` folder (or `bash scripts/build_ep11.sh`).
```bash
pip install scipy fonttools brotli pillow numpy sherpa-onnx
(cd scripts/render3d && npm install)        # three@0.160; Chromium/Playwright as installed on the machine
python3 scripts/00_check_vo.py               # VO intake check (read-only) -> docs/EP11_VO_REPORT.md
python3 scripts/01_transcribe.py <sherpa-onnx-whisper-small dir> && python3 scripts/01b_verified_transcript.py   # optional: timings are stored
python3 scripts/timeline_ep11.py             # check + export the edit -> timeline/ep11_timeline.json
python3 scripts/02_render_illustrations.py   # every E11_* frame + reference sheets (~12 min; --scale 0.25 for tests)
python3 scripts/04_sound.py                  # SFX + music + mix (voice unchanged)
python3 scripts/05_subtitles.py              # SRT
python3 scripts/06_render_video.py           # final MP4   (--preview A B, --stills t1,t2)
python3 scripts/08_shot_plan.py              # docs/EP11_SHOT_PLAN.md
python3 scripts/07_qc.py                     # QC of the finished file -> docs/EP11_QC.md + contact sheet
```
Hugging Face is not reachable from the build machine, so the VO was transcribed with Whisper *small* in its sherpa-onnx export (GitHub
release `k2-fsa/sherpa-onnx` asr-models), cut at the VO's own pauses, then the text was fixed by ear (`01b_verified_transcript.py`).

## Rules
Do not replace, speed up or re-pitch the voice; no second voice (every line is the narrator's, the original's lines included). Screen text
is drawn only in code. Do not touch EP01–EP10 files. Not shown, on purpose: what the original does next, why he wants the copies gone,
who really controls the system, whether ALEX_ZERO and the original are one being (ALEX_ZERO is not on screen in EP11).
