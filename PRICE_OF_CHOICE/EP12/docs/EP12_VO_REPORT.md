# EP12 — voiceover intake report

File: `audio/ElevenLabs_2026-11-12T22_43_31_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `097cedfe5c6498c64ff763cd0faf69a2`  
Duration: **110.916 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
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
| Length fits TikTok short (40–120 s) | ✅ | 110.92 s |
| EP12 target 75–90 s | ⚠️ | 110.92 s — +20.92 s over 90 s; reported, VO not altered |
| Decodes without errors | ✅ | ffmpeg full decode: clean |
| No clipped samples (|x| ≥ 0.999) | ✅ | 0 samples, sample peak 0.917 |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.34 | 2.14 | 0.81 |
| 4.50 | 4.81 | 0.31 |
| 5.95 | 6.39 | 0.44 |
| 8.75 | 9.39 | 0.64 |
| 10.18 | 10.50 | 0.32 |
| 11.13 | 11.63 | 0.51 |
| 13.71 | 14.18 | 0.47 |
| 16.46 | 17.04 | 0.58 |
| 19.80 | 20.08 | 0.28 |
| 20.50 | 20.75 | 0.26 |
| 21.24 | 21.53 | 0.29 |
| 25.17 | 25.76 | 0.59 |
| 26.86 | 27.20 | 0.34 |
| 28.09 | 28.38 | 0.29 |
| 29.29 | 29.60 | 0.31 |
| 31.35 | 32.16 | 0.81 |
| 36.85 | 37.64 | 0.78 |
| 40.19 | 40.77 | 0.58 |
| 42.02 | 42.61 | 0.59 |
| 43.34 | 43.64 | 0.29 |
| 45.80 | 46.07 | 0.28 |
| 47.81 | 48.49 | 0.69 |
| 53.52 | 53.83 | 0.32 |
| 55.21 | 55.73 | 0.52 |
| 57.04 | 57.59 | 0.55 |
| 58.75 | 59.20 | 0.45 |
| 62.14 | 62.67 | 0.53 |
| 64.32 | 64.79 | 0.47 |
| 66.83 | 67.21 | 0.38 |
| 68.62 | 69.25 | 0.62 |
| 71.16 | 71.78 | 0.62 |
| 73.78 | 74.44 | 0.66 |
| 74.74 | 75.30 | 0.56 |
| 77.53 | 77.86 | 0.33 |
| 80.24 | 80.90 | 0.65 |
| 87.05 | 87.49 | 0.43 |
| 89.76 | 90.29 | 0.53 |
| 96.45 | 96.80 | 0.35 |
| 97.78 | 98.19 | 0.41 |
| 99.66 | 100.05 | 0.39 |
| 106.92 | 107.36 | 0.45 |
| 109.65 | 110.05 | 0.40 |

## Next

1. Set `VO_END = 110.92` in `scripts/timeline_ep12.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
