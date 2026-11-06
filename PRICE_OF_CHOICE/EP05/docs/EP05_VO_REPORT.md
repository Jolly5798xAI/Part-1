# EP05 — voiceover intake report

File: `audio/ElevenLabs_2026-11-06T14_00_00_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `ad20d36b21d25dc3947d4b7d7528b554`  
Duration: **86.126 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -17.1 LUFS · true peak -1.0 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -17.1 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -1.0 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 86.13 s |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.13 | 1.68 | 0.54 |
| 3.15 | 3.80 | 0.65 |
| 5.60 | 6.69 | 1.09 |
| 12.01 | 12.37 | 0.36 |
| 13.86 | 14.11 | 0.25 |
| 15.87 | 16.14 | 0.27 |
| 18.75 | 19.78 | 1.03 |
| 20.64 | 21.28 | 0.64 |
| 23.61 | 23.92 | 0.31 |
| 25.42 | 25.85 | 0.43 |
| 31.00 | 31.28 | 0.28 |
| 32.78 | 33.52 | 0.74 |
| 36.38 | 36.82 | 0.43 |
| 38.02 | 38.75 | 0.73 |
| 40.08 | 40.97 | 0.88 |
| 43.57 | 43.83 | 0.26 |
| 45.10 | 45.68 | 0.58 |
| 52.35 | 52.72 | 0.37 |
| 54.55 | 54.85 | 0.29 |
| 57.61 | 58.15 | 0.54 |
| 59.34 | 59.70 | 0.36 |
| 62.11 | 62.77 | 0.66 |
| 65.67 | 66.82 | 1.14 |
| 67.88 | 68.14 | 0.26 |
| 69.13 | 70.17 | 1.04 |
| 77.47 | 78.03 | 0.56 |
| 80.16 | 81.19 | 1.03 |
| 83.52 | 83.85 | 0.33 |

## Next

1. Set `VO_END = 86.13` in `scripts/timeline_ep05.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
