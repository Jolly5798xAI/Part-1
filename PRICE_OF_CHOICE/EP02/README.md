# ЦЕНА ВЫБОРА — EP02 (подготовка)

Вторая серия вертикального мини-сериала (TikTok, 9:16, 1080×1920, 30 fps). Стиль тот же, что в EP01:
низкополигональный блочный 3D, ночной триллерный свет. Кадры рендерятся из того же 3D-мира, поэтому персонажи и квартира
совпадают с первой серией один в один.

**Статус:** структура готова, ждём одобренную озвучку EP02. Инвентаризация EP01 и список того, что можно взять повторно:
[`docs/EP02_PREP.md`](docs/EP02_PREP.md).

## Структура
```
EP02/
├─ audio/           ← сюда кладётся озвучка EP02 (см. audio/README.md); incoming/, если имя файла нестандартное
├─ reference/       стилевой референс + листы персонажей (из EP01)
├─ illustrations/   кадры EP02 (рендерятся скриптом)
├─ effects/         fonts/ (PT Serif, Rubik, OFL) · sfx/ (20 синтезированных звуков из EP01)
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
python3 scripts/01_transcribe.py <whisper_model>    # таймкоды слов -> timeline/transcript_words.json
#   заполнить scripts/timeline_ep02.py (образец: timeline_ep01_reference.py), новые ракурсы E2_* добавить в render3d/shots.js
python3 scripts/timeline_ep02.py                    # проверка и экспорт монтажного листа
python3 scripts/02_render_illustrations.py [ID...]  # кадры (только нужные: передайте ID)
python3 scripts/04_sound.py                         # SFX + музыка + микс (голос без изменений)
python3 scripts/05_subtitles.py                     # SRT
python3 scripts/06_render_video.py                  # финальный MP4  (--preview A B, --stills t1,t2)
```

## Правила
Голос не заменять, не ускорять и не менять тон. Текст на телефоне рисуется только программно. Файлы EP01 не трогать.
Не раскрывать раньше времени правила игры, происхождение двойников и роль Алекса.
