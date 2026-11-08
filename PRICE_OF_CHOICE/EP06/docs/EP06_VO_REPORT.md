# EP06 — voiceover intake report

File: `audio/ElevenLabs_2026-11-08T00_02_37_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `8889e1001e7ac63829866ea166e648c5`  
Duration: **85.891 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -17.2 LUFS · true peak -0.8 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -17.2 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.8 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 85.89 s |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.85 | 2.37 | 0.52 |
| 3.24 | 3.65 | 0.41 |
| 7.63 | 8.03 | 0.40 |
| 10.30 | 10.62 | 0.32 |
| 12.53 | 12.86 | 0.34 |
| 14.25 | 14.58 | 0.33 |
| 16.58 | 17.18 | 0.60 |
| 20.24 | 20.74 | 0.50 |
| 22.39 | 22.72 | 0.33 |
| 24.49 | 25.20 | 0.70 |
| 32.08 | 32.50 | 0.42 |
| 35.62 | 36.39 | 0.77 |
| 38.21 | 38.48 | 0.27 |
| 39.92 | 40.37 | 0.45 |
| 40.90 | 41.60 | 0.70 |
| 46.14 | 46.40 | 0.26 |
| 46.95 | 47.33 | 0.39 |
| 47.92 | 48.25 | 0.34 |
| 48.87 | 49.59 | 0.72 |
| 51.43 | 51.82 | 0.40 |
| 53.45 | 53.83 | 0.38 |
| 55.17 | 55.81 | 0.64 |
| 66.46 | 66.78 | 0.32 |
| 67.58 | 68.16 | 0.58 |
| 69.02 | 69.41 | 0.39 |
| 71.32 | 72.21 | 0.89 |
| 77.75 | 78.13 | 0.38 |
| 79.84 | 80.27 | 0.43 |
| 81.46 | 81.72 | 0.26 |
| 82.29 | 82.54 | 0.25 |
| 83.35 | 83.92 | 0.57 |
| 84.54 | 85.07 | 0.53 |

## Next

1. Set `VO_END = 85.89` in `scripts/timeline_ep06.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
