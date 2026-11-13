# EP13 — voiceover intake report

File: `audio/ElevenLabs_2026-11-13T01_03_09_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `1b88f317c35291d93b1e933f0c30e1de`  
Duration: **116.611 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -17.6 LUFS · true peak -0.9 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -17.6 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.9 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 116.61 s |
| EP13 target 75–90 s | ⚠️ | 116.61 s — +26.61 s over 90 s; reported, VO not altered |
| Decodes without errors | ✅ | ffmpeg full decode: clean |
| No clipped samples (|x| ≥ 0.999) | ✅ | 0 samples, sample peak 0.894 |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 2.42 | 2.77 | 0.34 |
| 3.61 | 4.57 | 0.97 |
| 6.73 | 6.98 | 0.25 |
| 13.09 | 13.81 | 0.72 |
| 16.92 | 17.61 | 0.69 |
| 19.53 | 19.83 | 0.30 |
| 21.94 | 22.46 | 0.53 |
| 23.18 | 23.46 | 0.28 |
| 25.78 | 26.08 | 0.30 |
| 28.08 | 28.68 | 0.60 |
| 32.64 | 32.96 | 0.32 |
| 35.42 | 35.67 | 0.26 |
| 37.26 | 37.65 | 0.39 |
| 39.01 | 39.74 | 0.74 |
| 41.91 | 42.44 | 0.53 |
| 46.89 | 47.35 | 0.45 |
| 47.98 | 48.32 | 0.34 |
| 49.85 | 50.12 | 0.27 |
| 54.03 | 54.38 | 0.36 |
| 56.33 | 56.62 | 0.29 |
| 58.79 | 59.29 | 0.50 |
| 61.42 | 61.72 | 0.30 |
| 63.56 | 63.87 | 0.31 |
| 65.05 | 65.63 | 0.58 |
| 66.97 | 67.31 | 0.34 |
| 68.00 | 68.31 | 0.31 |
| 69.48 | 69.81 | 0.33 |
| 71.78 | 72.28 | 0.50 |
| 77.12 | 77.49 | 0.38 |
| 79.50 | 79.76 | 0.27 |
| 81.58 | 81.89 | 0.31 |
| 84.82 | 85.16 | 0.34 |
| 87.58 | 87.90 | 0.32 |
| 89.15 | 89.41 | 0.26 |
| 90.94 | 91.33 | 0.39 |
| 91.94 | 92.43 | 0.49 |
| 93.03 | 93.63 | 0.60 |
| 94.23 | 94.81 | 0.58 |
| 96.97 | 97.43 | 0.45 |
| 99.12 | 99.59 | 0.48 |
| 100.10 | 100.48 | 0.37 |
| 102.11 | 102.54 | 0.43 |
| 107.13 | 107.57 | 0.44 |
| 108.99 | 109.29 | 0.30 |
| 110.61 | 110.90 | 0.29 |
| 112.64 | 113.36 | 0.72 |
| 116.31 | 116.61 | 0.30 |

## Next

1. Set `VO_END = 116.61` in `scripts/timeline_ep13.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
