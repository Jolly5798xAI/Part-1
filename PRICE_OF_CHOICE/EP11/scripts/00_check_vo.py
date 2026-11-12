"""Intake check for the EP11 voiceover. Read-only: the audio file is never modified, re-encoded or renamed.

usage:  python3 scripts/00_check_vo.py [path/to/file.mp3]
        (default: the only audio file in audio/ named ElevenLabs_*.mp3, or in audio/incoming/)

Writes docs/EP11_VO_REPORT.md: md5, duration, format, loudness, silences (candidate pauses) and the continuity checks
from EP01 (same ElevenLabs voice «Artem Lebedev — Captivating and Engaging», Eleven v3, mono 44.1 kHz).
"""
import glob, hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP01 = dict(voice="Artem Lebedev - Captivating and Engaging", model="eleven_v3", sr=44100, ch=1, lufs=-16.6)
AUDIO_EXT = (".mp3", ".wav", ".flac", ".m4a")


def find_vo():
    if len(sys.argv) > 1: return sys.argv[1]
    c = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*")))
    c = [p for p in c if p.lower().endswith(AUDIO_EXT)]
    if not c:
        c = [p for p in sorted(glob.glob(os.path.join(ROOT, "audio", "incoming", "*"))) if p.lower().endswith(AUDIO_EXT)]
    if len(c) != 1:
        raise SystemExit(f"expected exactly one voiceover file in audio/ (ElevenLabs_*) or audio/incoming/, found {len(c)}: {c}")
    return c[0]


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", VO] + args + ["-f", "null", "-"],
                          capture_output=True, text=True).stderr


VO = find_vo()
md5 = hashlib.md5(open(VO, "rb").read()).hexdigest()
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", VO],
                                  capture_output=True, text=True, check=True).stdout)
st = next(s for s in probe["streams"] if s["codec_type"] == "audio")
dur = float(probe["format"]["duration"])
sr, ch = int(st["sample_rate"]), int(st["channels"])
br = int(probe["format"].get("bit_rate", 0)) // 1000
e = ff(["-af", "ebur128=peak=true"])
lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])
tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)
tp = float(tp[-1]) if tp else float("nan")
DEC_ERR = subprocess.run(["ffmpeg", "-v", "error", "-i", VO, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
import numpy as _np
_pcm = _np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", VO, "-f", "f32le", "-ac", "1", "-"], capture_output=True, check=True).stdout, _np.float32)
CLIP, SPEAK = int((_np.abs(_pcm) >= 0.999).sum()), float(_np.abs(_pcm).max())
sil = ff(["-af", "silencedetect=noise=-40dB:d=0.25"])
starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", sil)]
ends = [(float(a), float(b)) for a, b in re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", sil)]
pauses = [(max(0, s), en, d) for s, (en, d) in zip(starts, ends)]

name = os.path.basename(VO)
checks = [
    ("Same narrator voice in file name", EP01["voice"] in name.replace("_", " "), f"`{EP01['voice']}` (EP01)"),
    ("Eleven v3", EP01["model"] in name, "eleven_v3"),
    ("Mono 44.1 kHz like EP01", sr == EP01["sr"] and ch == EP01["ch"], f"{sr} Hz, {ch} ch"),
    ("Loudness near EP01 (−16.6 LUFS ± 2)", abs(lufs - EP01["lufs"]) <= 2, f"{lufs:.1f} LUFS"),
    ("No clipping (true peak < −0.5 dBFS)", tp < -0.5, f"{tp:.1f} dBFS"),
    ("Length fits TikTok short (40–120 s)", 40 <= dur <= 120, f"{dur:.2f} s"),
    ("EP11 target 75–90 s", 75 <= dur <= 90, f"{dur:.2f} s" + ("" if 75 <= dur <= 90 else f" — {dur - 90:+.2f} s over 90 s; reported, VO not altered")),
    ("Decodes without errors", not DEC_ERR, "ffmpeg full decode: " + ("clean" if not DEC_ERR else DEC_ERR[:120])),
    ("No clipped samples (|x| ≥ 0.999)", CLIP == 0, f"{CLIP} samples, sample peak {SPEAK:.3f}"),
]
rel = os.path.relpath(VO, ROOT)
lines = [
    "# EP11 — voiceover intake report", "",
    f"File: `{rel}`  ", f"md5: `{md5}`  ",
    f"Duration: **{dur:.3f} s** · {st['codec_name']} · {sr} Hz · {ch} ch · {br} kb/s  ",
    f"Integrated loudness: {lufs:.1f} LUFS · true peak {tp:.1f} dBFS", "",
    "The file was only read. It must stay byte-identical (md5 above) through the whole pipeline.", "",
    "## Continuity checks against EP01", "", "| Check | Result | Value |", "|---|---|---|",
] + [f"| {n} | {'✅' if ok else '⚠️'} | {v} |" for n, ok, v in checks] + [
    "", "## Pauses ≥ 0.25 s (candidate cut points)", "", "| from | to | length |", "|---|---|---|",
] + [f"| {a:.2f} | {b:.2f} | {d:.2f} |" for a, b, d in pauses] + [
    "", "## Next", "",
    f"1. Set `VO_END = {dur:.2f}` in `scripts/timeline_ep11.py`.",
    "2. `python3 scripts/01_transcribe.py <whisper-model-dir>` → `timeline/transcript_words.json`.",
]
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
out = os.path.join(ROOT, "docs", "EP11_VO_REPORT.md")
open(out, "w", encoding="utf8").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("\nwrote", out)
if VO.startswith(os.path.join(ROOT, "audio", "incoming")):
    print("\nNOTE: file is in audio/incoming/. Move it (unchanged) to audio/ so 01_transcribe.py and 04_sound.py find it.")
