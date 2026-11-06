# EP03 — voiceover intake report

File: `audio/ElevenLabs_2026-11-06T10_51_16_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `5c71632532c3a1759728fd263270a611`  
Duration: **102.766 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -16.9 LUFS · true peak -0.6 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -16.9 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.6 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 102.77 s |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.33 | 2.16 | 0.83 |
| 11.94 | 12.45 | 0.51 |
| 13.29 | 14.05 | 0.76 |
| 17.17 | 17.47 | 0.31 |
| 20.25 | 20.57 | 0.32 |
| 21.68 | 22.22 | 0.55 |
| 26.34 | 26.67 | 0.33 |
| 27.85 | 28.48 | 0.64 |
| 31.93 | 32.24 | 0.31 |
| 34.90 | 35.49 | 0.59 |
| 36.35 | 36.64 | 0.28 |
| 37.31 | 37.84 | 0.53 |
| 41.51 | 42.00 | 0.49 |
| 43.49 | 44.30 | 0.81 |
| 46.34 | 46.83 | 0.49 |
| 48.65 | 49.67 | 1.02 |
| 55.62 | 56.27 | 0.66 |
| 63.57 | 64.17 | 0.60 |
| 66.21 | 66.68 | 0.47 |
| 67.47 | 67.74 | 0.27 |
| 69.38 | 70.35 | 0.97 |
| 71.90 | 72.29 | 0.38 |
| 74.51 | 74.83 | 0.32 |
| 76.76 | 77.27 | 0.51 |
| 81.31 | 81.59 | 0.28 |
| 82.54 | 83.27 | 0.72 |
| 88.07 | 88.41 | 0.34 |
| 89.58 | 89.84 | 0.26 |
| 91.13 | 91.99 | 0.86 |
| 93.28 | 93.55 | 0.27 |
| 94.19 | 94.48 | 0.29 |
| 95.10 | 95.86 | 0.76 |
| 97.32 | 97.89 | 0.56 |
| 100.54 | 101.05 | 0.51 |
| 101.72 | 101.98 | 0.26 |

## Next

1. Set `VO_END = 102.77` in `scripts/timeline_ep03.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
