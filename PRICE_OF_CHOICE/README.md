# ЦЕНА ВЫБОРА — производство серий

Вертикальный мини-сериал для TikTok (психологический триллер). Серия 1 — «Стакан воды».

**Итог:** `renders/EP01_PRICE_OF_CHOICE_FINAL.mp4`, 1080×1920, 9:16, 30 fps, H.264 + AAC 48 кГц, 77,2 с (озвучка 74,9 с + финальная карточка).
Само видео в git не хранится: GitHub не принимает файлы больше 100 МБ. Пересобирается командами ниже.

## Структура

```
audio/        озвучка ElevenLabs (оригинал, не изменяется) + mix_ep01.wav (финальный микс)
reference/    стилевой референс + листы персонажей (рендеры)
illustrations/ кадры 1620×2880 (+ папки анимаций, генерируются скриптом), meta.json — углы экрана телефона
prompts/      стиль и промпты на английском (если захотите заменить кадры генерацией)
subtitles/    EP01_PRICE_OF_CHOICE.srt
timeline/     transcript_words.json (таймкоды слов), ep01_timeline.json (монтажный лист)
effects/      sfx/*.wav (синтезированные звуки), fonts/ (PT Serif, Rubik — OFL)
scripts/      весь конвейер
renders/      готовое видео
docs/         визуальная библия, описание конвейера
```

## Конвейер (воспроизводимый)

```bash
pip install faster-whisper scipy fonttools brotli pillow numpy
(cd scripts/render3d && npm install)                 # three.js r160 + playwright (Chromium уже есть в среде)

python3 scripts/01_transcribe.py <путь_к_модели_whisper>   # таймкоды слов -> timeline/transcript_words.json
python3 scripts/02_render_illustrations.py           # все кадры и анимации из 3D-сцены (~5 мин)
python3 scripts/timeline_ep01.py                     # экспорт монтажного листа в JSON
python3 scripts/04_sound.py                          # SFX + музыка + микс (голос без изменений)
python3 scripts/05_subtitles.py                      # SRT
python3 scripts/06_render_video.py                   # финальный MP4 (~7 мин на 4 ядрах)
#   --preview 40 50      быстрый кусок;   --stills 12.5,43.6   контрольные кадры
```

Модель Whisper: HuggingFace из этой среды заблокирован. Использовалась faster-whisper **small** (CTranslate2 int8) из npm-пакетов `@skillninja/shortmovie-telop-model-p0…p3`: части склеиваются в `model.bin`, sha256 сверен.

## Как сделать следующую серию

1. Положить MP3 в `audio/`, прогнать `01_transcribe.py`.
2. Скопировать `scripts/timeline_ep01.py` → `timeline_ep02.py`: SHOTS / PHONE / SUBS / SFX по новым таймкодам.
3. Новые ракурсы добавить в `scripts/render3d/shots.js`. Персонажи и квартира уже есть в `scene.js`.
4. Запустить шаги 02–06 (импорт `timeline_ep01` в скриптах заменить на новую серию).

Подробности: `docs/PRODUCTION_PIPELINE.md`, стиль: `docs/VISUAL_BIBLE.md`.
