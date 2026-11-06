# ЦЕНА ВЫБОРА / THE PRICE OF CHOICE — Episode 01 «СТАКАН ВОДЫ»

Vertical (9:16) psychological-thriller mini-series for TikTok. Russian, first-person narration by Alex.

> **Status:** sound, subtitles, phone UI, timeline, prompts and bibles are finished. The **30 live-action shots still need an AI
> generator** that was not available here, so the final MP4 has not been rendered yet. `renders/EP01_ANIMATIC_PREVIEW.mp4` is a timing
> preview with storyboard cards. See [`docs/PRODUCTION_STATUS.md`](docs/PRODUCTION_STATUS.md).

## Structure
```
PRICE_OF_CHOICE/
├─ audio/        approved ElevenLabs VO (unchanged) · EP01_final_mix.wav · stems/ (vo, sfx, music)
├─ assets/       ui/ (8 final UI shots + screens/ plates for compositing) · fonts/ (Inter, OFL) · overlays/ (peephole mask)
├─ characters/   ALEX, DOUBLE, POLICEMAN bibles + reference-sheet prompts  (put approved ref images here)
├─ locations/    hallway, door, stairwell, props (glass, phone, UI language)
├─ scenes/       ← generated shots go here as <SHOT>.mp4 (or .png / .jpg)
├─ prompts/      EP01_prompts.md / .json — per-shot prompt, negative, references, camera, light, continuity
├─ subtitles/    EP01_ru.srt (plain) · EP01_ru.ass (styled, burned in)
├─ timeline/     asr_raw.json · EP01_words.json (word timings) · EP01_timeline.json (edit decision list)
├─ renders/      EP01_ANIMATIC_PREVIEW.mp4 → later EP01_PRICE_OF_CHOICE_FINAL.mp4
├─ project/      the pipeline (Python + FFmpeg)
└─ docs/         transcript, scene map, style guide, continuity, production status/QC
```

## Pipeline
Requirements: Python 3.10+, `pip install numpy pillow scipy soundfile`, FFmpeg with libx264 + libass.

| Step | Command | Produces |
|---|---|---|
| ASR (optional, done) | `project/00_transcribe.py` (see its header for the models) | `timeline/asr_raw.json` |
| Align | `python3 project/01_align.py` | `timeline/EP01_words.json` |
| Timeline + prompts | `python3 project/02_timeline.py` | `timeline/EP01_timeline.json`, `prompts/*`, `docs/EP01_SCENE_MAP.md` |
| Sound | `python3 project/03_sound.py` | `audio/stems/*`, `audio/EP01_final_mix.wav` (−14 LUFS) |
| Phone UI | `python3 project/04_ui.py` | `assets/ui/*.mp4`, `assets/ui/screens/*.png` |
| Subtitles | `python3 project/05_subtitles.py` | `subtitles/EP01_ru.srt`, `.ass` |
| Edit | `python3 project/06_build.py` · `--animatic` | final MP4 · preview |

**The single source of truth for the edit is `project/shots.py`** (shot list, timings in source-VO seconds, prompts, SFX cues,
pauses). After changing it, re-run steps 02 → 06.

## Finishing the episode
1. Generate and approve the reference images (`characters/*.md`, `locations/*.md` contain the prompts).
2. For every live shot in `prompts/EP01_prompts.md`, generate with the listed references and save as `scenes/<SHOT>.mp4`
   (3–6 s, ≥1080×1920, 24 fps), or as a still `scenes/<SHOT>.png` (the editor adds the camera move).
3. Phone shots (S02_A, S02_C, S03_B, S07_B, S11_A): composite the matching plate from `assets/ui/screens/` onto the phone screen.
4. `python3 project/06_build.py` → `renders/EP01_PRICE_OF_CHOICE_FINAL.mp4` (1080×1920, H.264 High, AAC, 24 fps, faststart).
5. Run the QC checklist in `docs/PRODUCTION_STATUS.md` on the real footage (face identity, hands, door layout).

## Rules that must not be broken
Do not replace, re-generate, speed up or pitch the voice; do not add a second voice; phone text is never AI-generated;
do not reveal the game, the doubles' origin or Alex's role. Long-arc notes: `docs/SERIES_CONTINUITY.md`.

All music and sound effects are synthesised by `project/03_sound.py`. No third-party audio is used.
