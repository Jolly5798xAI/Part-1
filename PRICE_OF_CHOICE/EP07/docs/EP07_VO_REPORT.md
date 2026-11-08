# EP07 — voiceover intake report

File: `audio/ElevenLabs_2026-11-08T01_07_44_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `fde19fce5c2529ec5dfb3bf75854744b`  
Duration: **101.146 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -17.7 LUFS · true peak -0.8 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -17.7 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.8 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 101.15 s |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 0.88 | 1.68 | 0.80 |
| 2.47 | 3.58 | 1.11 |
| 5.66 | 6.33 | 0.67 |
| 7.59 | 8.39 | 0.79 |
| 10.28 | 11.07 | 0.79 |
| 12.24 | 12.75 | 0.51 |
| 14.12 | 15.01 | 0.89 |
| 18.44 | 19.12 | 0.68 |
| 20.49 | 20.90 | 0.41 |
| 21.15 | 21.48 | 0.33 |
| 25.06 | 25.37 | 0.31 |
| 27.26 | 27.57 | 0.30 |
| 28.86 | 29.59 | 0.72 |
| 32.98 | 33.24 | 0.26 |
| 34.03 | 34.84 | 0.81 |
| 36.14 | 36.39 | 0.26 |
| 38.32 | 38.97 | 0.65 |
| 39.78 | 40.13 | 0.35 |
| 43.05 | 43.31 | 0.26 |
| 45.37 | 45.73 | 0.36 |
| 46.63 | 47.30 | 0.67 |
| 53.56 | 54.57 | 1.00 |
| 56.19 | 56.52 | 0.33 |
| 58.52 | 59.06 | 0.54 |
| 60.84 | 61.10 | 0.26 |
| 63.14 | 63.39 | 0.26 |
| 68.80 | 69.41 | 0.61 |
| 70.75 | 71.06 | 0.31 |
| 72.07 | 72.45 | 0.38 |
| 74.79 | 75.20 | 0.41 |
| 78.84 | 79.52 | 0.68 |
| 84.22 | 84.91 | 0.69 |
| 85.30 | 85.58 | 0.28 |
| 86.82 | 87.07 | 0.25 |
| 88.98 | 89.61 | 0.63 |
| 91.42 | 92.04 | 0.63 |
| 93.04 | 93.95 | 0.92 |
| 95.47 | 95.77 | 0.30 |
| 97.31 | 97.75 | 0.44 |
| 99.30 | 100.05 | 0.75 |

## Next

1. Set `VO_END = 101.15` in `scripts/timeline_ep06.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
