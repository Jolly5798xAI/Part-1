# EP11 — voiceover intake report

File: `audio/ElevenLabs_2026-11-12T12_15_57_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `5974a54f41fada113993a12605b97d1a`  
Duration: **108.121 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -16.8 LUFS · true peak -0.8 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -16.8 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.8 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 108.12 s |
| EP11 target 75–90 s | ⚠️ | 108.12 s — +18.12 s over 90 s; reported, VO not altered |
| Decodes without errors | ✅ | ffmpeg full decode: clean |
| No clipped samples (|x| ≥ 0.999) | ✅ | 0 samples, sample peak 0.907 |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.27 | 1.90 | 0.63 |
| 2.51 | 3.06 | 0.55 |
| 4.62 | 5.23 | 0.61 |
| 7.45 | 7.78 | 0.33 |
| 9.49 | 9.82 | 0.33 |
| 10.61 | 10.86 | 0.26 |
| 12.62 | 13.19 | 0.57 |
| 14.64 | 15.01 | 0.37 |
| 19.64 | 20.39 | 0.75 |
| 21.90 | 22.41 | 0.51 |
| 24.38 | 24.97 | 0.59 |
| 26.42 | 27.05 | 0.62 |
| 27.48 | 27.89 | 0.41 |
| 29.70 | 30.29 | 0.59 |
| 32.27 | 33.09 | 0.82 |
| 36.19 | 36.78 | 0.59 |
| 42.08 | 42.95 | 0.86 |
| 44.94 | 45.60 | 0.66 |
| 47.51 | 48.13 | 0.63 |
| 49.14 | 49.42 | 0.28 |
| 52.01 | 52.84 | 0.83 |
| 55.27 | 55.99 | 0.72 |
| 58.86 | 59.59 | 0.73 |
| 60.58 | 61.04 | 0.46 |
| 62.83 | 63.17 | 0.34 |
| 65.20 | 65.75 | 0.55 |
| 67.21 | 68.01 | 0.80 |
| 72.02 | 72.32 | 0.30 |
| 74.54 | 75.12 | 0.57 |
| 79.34 | 79.89 | 0.56 |
| 80.47 | 81.32 | 0.86 |
| 82.42 | 82.68 | 0.26 |
| 83.54 | 84.34 | 0.79 |
| 86.14 | 86.42 | 0.28 |
| 90.02 | 90.75 | 0.73 |
| 92.15 | 92.48 | 0.33 |
| 94.83 | 95.69 | 0.86 |
| 96.22 | 96.62 | 0.40 |
| 97.50 | 98.00 | 0.50 |
| 98.79 | 99.08 | 0.29 |
| 100.83 | 101.66 | 0.83 |
| 103.37 | 103.62 | 0.25 |
| 106.17 | 106.89 | 0.72 |

## Next

1. Set `VO_END = 108.12` in `scripts/timeline_ep11.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
