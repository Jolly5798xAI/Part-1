# EP04 — voiceover intake report

File: `audio/ElevenLabs_2026-11-06T12_03_21_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `604dc263c830c8817cd0f29c01cd713b`  
Duration: **108.278 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -17.5 LUFS · true peak -1.2 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -17.5 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -1.2 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 108.28 s |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.29 | 1.75 | 0.45 |
| 3.06 | 4.25 | 1.19 |
| 4.92 | 5.17 | 0.26 |
| 5.76 | 6.07 | 0.31 |
| 7.22 | 8.63 | 1.41 |
| 13.78 | 14.56 | 0.78 |
| 16.08 | 16.36 | 0.28 |
| 17.43 | 17.93 | 0.50 |
| 20.09 | 21.01 | 0.93 |
| 22.01 | 23.03 | 1.02 |
| 23.59 | 24.34 | 0.75 |
| 25.75 | 26.56 | 0.80 |
| 26.95 | 27.49 | 0.54 |
| 27.72 | 28.53 | 0.81 |
| 30.48 | 31.63 | 1.15 |
| 34.84 | 35.25 | 0.41 |
| 36.58 | 37.27 | 0.69 |
| 38.42 | 38.71 | 0.29 |
| 39.33 | 39.58 | 0.25 |
| 41.27 | 41.90 | 0.63 |
| 47.08 | 47.35 | 0.26 |
| 48.20 | 48.95 | 0.75 |
| 50.65 | 51.17 | 0.52 |
| 52.36 | 52.98 | 0.61 |
| 55.28 | 55.77 | 0.49 |
| 56.95 | 57.59 | 0.64 |
| 58.53 | 59.42 | 0.89 |
| 60.20 | 60.81 | 0.60 |
| 61.40 | 61.76 | 0.36 |
| 63.97 | 64.62 | 0.65 |
| 67.54 | 67.90 | 0.36 |
| 68.61 | 68.96 | 0.35 |
| 69.59 | 70.27 | 0.68 |
| 71.86 | 72.33 | 0.48 |
| 75.57 | 76.36 | 0.79 |
| 79.53 | 80.31 | 0.78 |
| 86.31 | 86.63 | 0.31 |
| 89.40 | 89.74 | 0.34 |
| 93.65 | 94.47 | 0.82 |
| 95.00 | 95.33 | 0.33 |
| 96.33 | 97.35 | 1.02 |
| 100.50 | 101.47 | 0.98 |
| 104.27 | 105.17 | 0.90 |
| 105.63 | 106.13 | 0.50 |
| 106.77 | 107.19 | 0.42 |

## Next

1. Set `VO_END = 108.28` in `scripts/timeline_ep04.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
