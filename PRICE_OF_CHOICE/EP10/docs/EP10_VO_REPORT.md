# EP10 — voiceover intake report

File: `audio/ElevenLabs_2026-11-11T01_39_45_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `f09ce98e8261e676fe39c7814f4e920d`  
Duration: **121.809 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -17.0 LUFS · true peak -0.9 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -17.0 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.9 dBFS |
| Length fits TikTok short (40–120 s) | ⚠️ | 121.81 s |
| EP10 target 75–90 s | ⚠️ | 121.81 s — +31.81 s over 90 s; reported, VO not altered |
| Decodes without errors | ✅ | ffmpeg full decode: clean |
| No clipped samples (|x| ≥ 0.999) | ✅ | 0 samples, sample peak 0.901 |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.97 | 2.57 | 0.60 |
| 5.50 | 6.07 | 0.57 |
| 7.41 | 8.63 | 1.21 |
| 10.75 | 11.26 | 0.51 |
| 12.27 | 12.80 | 0.52 |
| 14.64 | 15.59 | 0.94 |
| 17.58 | 18.04 | 0.47 |
| 19.40 | 19.68 | 0.27 |
| 20.76 | 21.54 | 0.78 |
| 25.89 | 26.21 | 0.31 |
| 27.35 | 28.05 | 0.70 |
| 29.08 | 29.59 | 0.51 |
| 32.57 | 32.90 | 0.33 |
| 35.37 | 35.70 | 0.33 |
| 38.37 | 39.07 | 0.70 |
| 40.42 | 40.88 | 0.46 |
| 43.74 | 44.18 | 0.45 |
| 45.93 | 46.70 | 0.77 |
| 49.05 | 49.31 | 0.26 |
| 51.30 | 51.91 | 0.61 |
| 53.88 | 54.64 | 0.77 |
| 55.49 | 55.74 | 0.26 |
| 56.47 | 56.89 | 0.42 |
| 63.10 | 63.98 | 0.88 |
| 67.13 | 67.53 | 0.40 |
| 68.89 | 69.35 | 0.46 |
| 76.97 | 77.60 | 0.62 |
| 80.02 | 80.60 | 0.58 |
| 92.00 | 92.27 | 0.27 |
| 93.05 | 93.35 | 0.30 |
| 93.95 | 94.77 | 0.82 |
| 96.51 | 96.78 | 0.28 |
| 98.08 | 98.47 | 0.39 |
| 102.29 | 103.09 | 0.80 |
| 104.37 | 104.78 | 0.42 |
| 107.58 | 108.39 | 0.80 |
| 111.78 | 112.26 | 0.48 |
| 114.02 | 114.33 | 0.31 |
| 115.44 | 115.73 | 0.29 |
| 116.34 | 117.16 | 0.82 |

## Next

1. Set `VO_END = 121.81` in `scripts/timeline_ep10.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
