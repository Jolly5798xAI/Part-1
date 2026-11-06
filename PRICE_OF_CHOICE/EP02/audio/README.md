# EP02 — озвучка

Сюда кладётся **одобренная** озвучка ElevenLabs для EP02, без изменений и с исходным именем файла, например:

`ElevenLabs_<дата>_Artem Lebedev - Captivating and Engaging_eleven_v3.mp3`

* Голос тот же, что в EP01: **Artem Lebedev — Captivating and Engaging, Eleven v3**. Замену голоса не генерировать.
* Файл не обрезать, не ускорять, не менять тон, не перекодировать. Пайплайн только читает его.
* В `audio/` должен лежать ровно один файл `ElevenLabs_*.mp3`. Если имя другое, положите файл в `incoming/`:
  `00_check_vo.py` найдёт его там.

После загрузки: `python3 scripts/00_check_vo.py` → `docs/EP02_VO_REPORT.md`.

Генерируется пайплайном: `mix_ep02.wav` (финальный микс), `music_ep02.wav` (в git не хранится).
