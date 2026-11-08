#!/usr/bin/env bash
# Reproducible build of EP06 from the final voiceover.  usage: bash scripts/build_ep06.sh [whisper_model_dir]
# Without a model dir the stored word timings (timeline/transcript_words.json, tail corrected by hand — see docs/EP06_transcript.txt) are used.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/00_check_vo.py
if [ $# -ge 1 ]; then python3 scripts/01_transcribe.py "$1"; fi
python3 scripts/timeline_ep06.py
[ -d scripts/render3d/node_modules/three ] || (cd scripts/render3d && npm install)
python3 scripts/02_render_illustrations.py
mkdir -p models && mv -f scenes/REF_*.png models/ 2>/dev/null || true
python3 scripts/04_sound.py
python3 scripts/05_subtitles.py
python3 scripts/06_render_video.py
python3 scripts/07_qc.py                     # QC report -> docs/EP06_QC.md
