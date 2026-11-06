# ЦЕНА ВЫБОРА — EP02

Вторая серия вертикального мини-сериала (TikTok, 9:16, 1080×1920, 30 fps). Стиль тот же, что в EP01:
низкополигональный блочный 3D, ночной триллерный свет. Кадры рендерятся из того же 3D-мира, поэтому персонажи и квартира
совпадают с первой серией один в один.

**Статус:** серия собрана. Итог: `renders/EP02_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, 30 fps, H.264 + AAC 48 кГц, 97,5 с).
EP02 начинается с последнего кадра EP01: снаружи открывают замок.

* озвучка (окончательная, без изменений): `audio/ElevenLabs_2026-11-06T09_25_44_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`
* текст, сверенный с распознаванием: [`docs/EP02_transcript.txt`](docs/EP02_transcript.txt)
* покадровый план и список новых 3D-сцен: [`docs/EP02_SHOT_PLAN.md`](docs/EP02_SHOT_PLAN.md)
* проверка озвучки: [`docs/EP02_VO_REPORT.md`](docs/EP02_VO_REPORT.md) · инвентаризация EP01: [`docs/EP02_PREP.md`](docs/EP02_PREP.md)

## Структура
```
EP02/
├─ audio/           ← сюда кладётся озвучка EP02 (см. audio/README.md); incoming/, если имя файла нестандартное
├─ reference/       стилевой референс + листы персонажей (из EP01)
├─ illustrations/   кадры EP02 (рендерятся скриптом)
├─ effects/         fonts/ (PT Serif, Rubik, OFL) · sfx/ (20 синтезированных звуков EP01 + 4 новых)
├─ prompts/         style_prompt_en.txt (на случай, если кадры будут генерироваться)
├─ timeline/        transcript_words.json, ep02_timeline.json
├─ subtitles/       EP02_PRICE_OF_CHOICE.srt
├─ renders/         EP02_PRICE_OF_CHOICE_FINAL.mp4 (в git не хранится)
├─ scripts/         пайплайн (копия EP01, переключён на timeline_ep02)
└─ docs/            EP02_PREP.md, VISUAL_BIBLE.md, континуити и транскрипт EP01, EP02_VO_REPORT.md (после проверки озвучки)
```

## Пайплайн
Запускать из папки `EP02/`.
```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)

python3 scripts/00_check_vo.py                      # проверка новой озвучки (только чтение) -> docs/EP02_VO_REPORT.md
python3 scripts/01_transcribe.py <whisper_model>    # таймкоды слов -> timeline/transcript_words.json (faster-whisper small,
#   CTranslate2 int8; HuggingFace закрыт, модель взята из npm @skillninja/shortmovie-telop-model-p0…p3, sha256 сверен)
#   монтажный лист EP02: scripts/timeline_ep02.py; новые ракурсы E2_* в render3d/shots.js
python3 scripts/timeline_ep02.py                    # проверка и экспорт монтажного листа
python3 scripts/02_render_illustrations.py S20_lock_turns S12_phone_rack S13_door_bang S05_place_glass S06_phone_bank \
    S03_phone_msg1 S19_phone_final S04_alex_phone_face S08_peephole_lean 'E2_*'   # кадры EP02 (~5 мин)
python3 scripts/04_sound.py                         # SFX + музыка + микс (голос без изменений)
python3 scripts/05_subtitles.py                     # SRT
python3 scripts/06_render_video.py                  # финальный MP4  (--preview A B, --stills t1,t2)
```

## Правила
Голос не заменять, не ускорять и не менять тон. Текст на телефоне рисуется только программно. Файлы EP01 не трогать.
Не раскрывать раньше времени правила игры, происхождение двойников и роль Алекса.
