# EP08 — voiceover intake report

File: `audio/ElevenLabs_2026-11-08T02_20_42_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `72d29ba82434e0534d17d7f3e27b666c`  
Duration: **91.638 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -17.3 LUFS · true peak -1.2 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -17.3 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -1.2 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 91.64 s |
| EP08 target 75–90 s | ⚠️ | 91.64 s — +1.64 s over 90 s; reported, VO not altered |
| Decodes without errors | ✅ | ffmpeg full decode: clean |
| No clipped samples (|x| ≥ 0.999) | ✅ | 0 samples, sample peak 0.871 |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 2.40 | 3.46 | 1.06 |
| 4.52 | 5.30 | 0.78 |
| 9.43 | 9.93 | 0.51 |
| 11.44 | 11.94 | 0.50 |
| 14.16 | 14.72 | 0.56 |
| 15.45 | 15.78 | 0.33 |
| 17.31 | 17.74 | 0.43 |
| 18.96 | 19.57 | 0.61 |
| 21.22 | 22.08 | 0.86 |
| 23.71 | 24.00 | 0.28 |
| 26.04 | 26.69 | 0.65 |
| 29.46 | 29.82 | 0.37 |
| 31.95 | 32.22 | 0.27 |
| 33.70 | 34.28 | 0.58 |
| 36.52 | 37.26 | 0.74 |
| 38.95 | 39.43 | 0.47 |
| 40.68 | 41.44 | 0.76 |
| 45.20 | 45.52 | 0.32 |
| 47.48 | 48.15 | 0.67 |
| 52.59 | 52.88 | 0.30 |
| 54.47 | 54.95 | 0.47 |
| 56.96 | 57.44 | 0.49 |
| 58.62 | 58.91 | 0.30 |
| 61.03 | 61.57 | 0.54 |
| 64.46 | 64.72 | 0.26 |
| 66.19 | 66.98 | 0.79 |
| 73.25 | 73.58 | 0.33 |
| 75.94 | 76.63 | 0.69 |
| 77.65 | 78.28 | 0.63 |
| 79.36 | 79.86 | 0.50 |
| 82.14 | 83.06 | 0.92 |
| 84.51 | 84.82 | 0.31 |
| 87.13 | 88.06 | 0.94 |
| 90.97 | 91.62 | 0.65 |

## Next

1. Set `VO_END = 91.64` in `scripts/timeline_ep08.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
