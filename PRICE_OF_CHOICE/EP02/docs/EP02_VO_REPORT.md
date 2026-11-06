# EP02 — voiceover intake report

File: `audio/ElevenLabs_2026-11-06T09_25_44_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `53ee1618bbdde060847b3250e1f1ea99`  
Duration: **95.164 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -16.7 LUFS · true peak -0.7 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -16.7 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.7 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 95.16 s |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 2.48 | 2.79 | 0.31 |
| 8.25 | 9.69 | 1.44 |
| 10.82 | 11.60 | 0.79 |
| 13.81 | 14.69 | 0.88 |
| 16.09 | 16.40 | 0.31 |
| 20.00 | 20.39 | 0.38 |
| 21.53 | 21.79 | 0.26 |
| 23.48 | 24.43 | 0.95 |
| 30.53 | 30.83 | 0.30 |
| 33.39 | 33.80 | 0.41 |
| 36.70 | 37.61 | 0.91 |
| 38.92 | 39.38 | 0.46 |
| 42.78 | 43.45 | 0.67 |
| 49.01 | 49.37 | 0.35 |
| 52.70 | 53.36 | 0.66 |
| 58.34 | 59.36 | 1.02 |
| 63.83 | 64.16 | 0.32 |
| 66.22 | 67.00 | 0.78 |
| 68.93 | 69.27 | 0.33 |
| 71.01 | 71.70 | 0.69 |
| 74.07 | 74.93 | 0.86 |
| 76.55 | 76.84 | 0.30 |
| 77.92 | 78.51 | 0.59 |
| 81.68 | 82.03 | 0.34 |
| 83.36 | 83.72 | 0.36 |
| 86.19 | 86.53 | 0.34 |
| 88.64 | 89.51 | 0.87 |
| 92.61 | 93.65 | 1.04 |

## Next

1. Set `VO_END = 95.16` in `scripts/timeline_ep02.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
