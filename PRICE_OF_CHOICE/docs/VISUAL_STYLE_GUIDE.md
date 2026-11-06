# «ЦЕНА ВЫБОРА» — visual style guide (series-wide)

**One sentence:** grounded, photoreal psychological thriller at night, seen through Alex's eyes. Plausibility beats spectacle.

## Format
- Vertical 9:16, delivery 1080×1920, **24 fps** (locked for the series), H.264 High + AAC 48 kHz.
- Episode length follows the approved voiceover (EP01: 74.9 s VO → 78.45 s cut with pauses and end card).

## Image
| Parameter | Rule |
|---|---|
| Palette | cold blue-grey; red appears only as blood and in threat UI |
| Skin | neutral, natural; never blue-faced or orange |
| Light | practicals only: under-door strip, peephole point, streetlight spill, phone screen. Low key, motivated |
| Shadows | deep but not crushed — black level lifted ~3.5% (grade curve `0/0.035`) |
| Grain | moderate, temporal, applied once in post (`noise=alls=7`) |
| Lens | 24–35 mm for POV / wide, 50–85 mm for inserts, true fisheye for the peephole |
| Camera | locked or slow motivated moves (push-ins 3–6%), POV micro-motion; shake **only** on door impacts |
| Grade (post, applied by `06_build.py`) | contrast 1.05, saturation 0.82, blue in shadows/mids, slight red pull |

## Never
cartoon / anime / 3D-render look, plastic skin, face drift between shots, random appearance changes, surrealism without a story reason,
heavy glitch, horror filters, constant shake, decorative transitions, mangled hands/faces/doors, AI-generated text on screens.

## Edit grammar
- Hard cuts. The only "transition" is the motivated match cut into the peephole lens (S05_D → S05_E).
- Pace accelerates with the threat: average shot 2.3 s in scenes 1–4 → ~1.6 s in scenes 9–12.
- Phone text is always composited UI (exact Cyrillic), never generated.
- End on a hard cut to black mid-action + silent title card.

## Subtitles
Inter Bold 74 px, white, 5 px black outline, bottom-centre with the baseline at y≈1420 (clear of TikTok's caption and right-hand
buttons: MarginL 110, MarginR 170). 2–5 words per cue, never ending on a preposition. Threat words red `#FF4A4F`, money/time ice-blue `#9CD3FF`.

## Sound
VO always on top (≥10 dB over the bed while speaking). Original synthesized dark ambient; no licensed music. Silence is a tool:
the room goes quiet after «Он замолчал» and before the face reveal. Hard audio cut with the picture.
