# EP09 — voiceover intake report

File: `audio/ElevenLabs_2026-11-10T23_44_38_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3`  
md5: `62650f060ac37ef75feffc0c56a1e4d1`  
Duration: **96.131 s** · mp3 · 44100 Hz · 1 ch · 128 kb/s  
Integrated loudness: -16.8 LUFS · true peak -0.7 dBFS

The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.

## Continuity checks against EP01

| Check | Result | Value |
|---|---|---|
| Same narrator voice in file name | ✅ | `Artem Lebedev - Captivating and Engaging` (EP01) |
| Eleven v3 | ✅ | eleven_v3 |
| Mono 44.1 kHz like EP01 | ✅ | 44100 Hz, 1 ch |
| Loudness near EP01 (−16.6 LUFS ± 2) | ✅ | -16.8 LUFS |
| No clipping (true peak < −0.5 dBFS) | ✅ | -0.7 dBFS |
| Length fits TikTok short (40–120 s) | ✅ | 96.13 s |
| EP09 target 75–90 s | ⚠️ | 96.13 s — +6.13 s over 90 s; reported, VO not altered |
| Decodes without errors | ✅ | ffmpeg full decode: clean |
| No clipped samples (|x| ≥ 0.999) | ✅ | 0 samples, sample peak 0.913 |

## Pauses ≥ 0.25 s (candidate cut points)

| from | to | length |
|---|---|---|
| 1.80 | 2.32 | 0.52 |
| 2.98 | 3.32 | 0.35 |
| 4.65 | 5.57 | 0.92 |
| 7.61 | 7.90 | 0.28 |
| 9.87 | 10.41 | 0.54 |
| 12.26 | 12.55 | 0.30 |
| 13.56 | 13.88 | 0.32 |
| 16.32 | 16.71 | 0.38 |
| 18.39 | 18.97 | 0.58 |
| 23.36 | 23.69 | 0.33 |
| 25.22 | 25.66 | 0.45 |
| 27.21 | 27.54 | 0.33 |
| 28.55 | 29.11 | 0.56 |
| 30.26 | 30.57 | 0.32 |
| 32.21 | 32.64 | 0.43 |
| 34.74 | 35.36 | 0.62 |
| 37.56 | 37.85 | 0.28 |
| 41.53 | 42.17 | 0.64 |
| 43.81 | 44.07 | 0.25 |
| 49.19 | 49.63 | 0.44 |
| 51.97 | 52.39 | 0.42 |
| 55.08 | 55.48 | 0.40 |
| 59.22 | 59.47 | 0.25 |
| 61.97 | 62.31 | 0.34 |
| 64.01 | 64.46 | 0.45 |
| 67.38 | 67.68 | 0.30 |
| 70.72 | 71.20 | 0.48 |
| 71.65 | 72.07 | 0.42 |
| 73.15 | 73.76 | 0.61 |
| 76.63 | 77.27 | 0.64 |
| 82.91 | 83.49 | 0.59 |
| 85.66 | 86.00 | 0.34 |
| 87.19 | 87.46 | 0.26 |
| 90.35 | 90.65 | 0.30 |

## Next

1. Set `VO_END = 96.13` in `scripts/timeline_ep09.py`.
2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.
