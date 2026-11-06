# EP01 — production status, environment audit and QC

_Status date: 2026-11-06._

## Verdict
**The final MP4 has not been produced, because no AI image/video generator was available in the production environment.**
Everything that does not depend on generated footage is finished. A timing animatic
(`renders/EP01_ANIMATIC_PREVIEW.mp4`) contains the final sound, the final subtitles, the eight final phone-UI shots, and labelled
storyboard cards in place of the 30 live-action shots. It is a preview, **not** the episode.
`project/06_build.py` refuses to write `EP01_PRICE_OF_CHOICE_FINAL.mp4` until every live shot exists in `scenes/`.

## Stage A — environment audit
| Item | Result |
|---|---|
| Approved MP3 | ✅ present; md5 `9c0071d76a423890ae066d11c0fa2fad`; 74.919 s, mono 44.1 kHz, 128 kb/s, −16.6 LUFS. Copied unchanged to `audio/` |
| FFmpeg 6.1 (libx264, AAC, libass) / Python 3.13, numpy, Pillow, scipy | ✅ |
| GPU | ❌ none (CPU only, 4 cores) — no local diffusion/video models feasible |
| Image/video generator API keys (OpenAI, Replicate, Stability, Runway, Kling, Luma, Fal, etc.) | ❌ none configured |
| Network to generator APIs | ❌ blocked by the environment's proxy (api.openai.com, api.replicate.com, api.stability.ai → 403) |
| Hugging Face | ❌ blocked; ASR models taken from GitHub releases instead |
| Stock/SFX libraries (pixabay, freesound) | ❌ blocked — not needed: all sound is synthesised |
| Paid operations | none performed |

## What is needed to finish
1. Access to an AI generator with character/image reference support. Image-to-video is preferred, e.g. Kling, Runway Gen-4,
   Veo, or Luma; a still-image model with reference images is the minimum (Flux/Midjourney/GPT-image).
2. Its API key (stored as an environment secret, not in the repo), the host allowed in the environment's network policy, and your
   go-ahead for the cost. Rough volume: ~6 reference images + 30 shots × 2–4 takes.
3. Then: generate the references (`characters/`, `locations/`), approve them, generate each shot from
   `prompts/EP01_prompts.md`, save as `scenes/<SHOT>.mp4` (or `.png`), composite the phone screens on the 5 phone shots, and run
   `python3 project/06_build.py`.

## Stage B — voiceover analysis (done)
- Recognised by two independent models (GigaAM-v2 RU + Whisper large-v3-turbo); texts agree except one word, «две» («две тысячи»),
  re-checked on an isolated fragment and confirmed. Transcript: `docs/EP01_transcript.txt`.
- Word-level timing for all 180 words: `timeline/EP01_words.json` (only «две» is interpolated, inside a measured 0.34 s gap).
- 12 scenes / 38 shots mapped to the actual speech: `timeline/EP01_timeline.json`, `docs/EP01_SCENE_MAP.md`.
- Three atmospheric pauses inserted into existing silences (+0.70 s before the knocks, +0.35 s after «Он замолчал», +0.45 s before
  the face reveal). Speech is not cut, sped up or pitch-shifted.

## QC checklist
| # | Check | Status |
|---|---|---|
| 1 | On-screen events match the VO | ✅ timeline shot-by-shot; ⏳ re-check with real footage |
| 2 | Alex = double (identical face) | ⏳ needs generated footage; rules + reference workflow in `characters/` |
| 3 | Door / lock / peephole layout constant | ⏳ footage; locked spec in `locations/ENTRANCE_DOOR.md` |
| 4 | Hand anatomy | ⏳ footage |
| 5 | Distorted faces | ⏳ footage |
| 6 | Message texts correct | ✅ UI rendered programmatically; line breaks fixed (no hanging «у», «кв. 37» kept together) |
| 7 | Every narrator word audible | ✅ VO ≥ 10.2 dB above music+SFX in every 2 s speech window (most ≥ 12 dB); music dipped under the whispered «Не верь телефону» |
| 8 | Subtitles don't cover key details | ✅ found and fixed an overlap with the timer cards (compact card, UI zoom anchored above the subtitle zone, subtitles at y≈1420) |
| 9 | First frame works as a hook | ✅ structurally: glass ECU + money pop at 0.92 s + door attack at 4.5 s; ⏳ footage quality |
| 10 | Reveal tension | ✅ silence + music drop + 0.45 s pause + soft sting + real-Alex reaction cut |
| 11 | Ending reveals nothing | ✅ only the lock turning; hard cut mid-turn at 77.05 s |
| 12 | MP4 playback | ✅ (animatic) 1080×1920, 24 fps, H.264 High yuv420p, AAC 48 kHz stereo, faststart; A/V durations 78.42/78.45 s; the only black is the intended end card (77.04–78.38) |
| — | Loudness | ✅ −14.1 LUFS integrated, −1.5 dBTP |
| — | Subtitles = transcript | ✅ automated assertion in `05_subtitles.py` (every word once, in order) |
| — | Build paths for stills / video clips / peephole mask | ✅ tested with dummy inputs: exact frame counts, short clips held on their last frame |
