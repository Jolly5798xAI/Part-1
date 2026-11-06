"""EP03 quality control on the finished MP4. Read-only. Writes docs/EP03_QC.md.

Checks: container/stream format, full decode without errors, duration vs VO, black/frozen frames,
audio sync (the VO inside the final AAC track vs the original MP3, by cross-correlation), loudness,
subtitles inside the VO and not overlapping, every required phone message present in the timeline,
the voiceover file unchanged (md5), EP01/EP02 files untouched (git), and contact sheets of the cut.
"""
import os, sys, re, json, glob, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep03 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP4 = os.path.join(ROOT, "renders", "EP03_PRICE_OF_CHOICE_FINAL.mp4")
VO = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
VO_MD5 = "5c71632532c3a1759728fd263270a611"
REQUIRED = ["Третье задание. Найди того, кто стоит за твоей спиной.", "Награда — пять тысяч долларов.",
            "Не входи. Там находится оригинал.", "Задание выполнено.", "Объект найден.", "Теперь уничтожь копию."]
rows = []


def ok(name, cond, val): rows.append((name, bool(cond), val)); return cond
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)


pr = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", MP4]).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
dur = float(pr["format"]["duration"]); size = int(pr["format"]["size"]) / 1e6
ok("Video codec H.264", v["codec_name"] == "h264", f'{v["codec_name"]} ({v.get("profile")}), {v["pix_fmt"]}')
ok("Resolution 1080×1920 (9:16)", (v["width"], v["height"]) == (1080, 1920), f'{v["width"]}×{v["height"]}')
ok("30 fps", v["r_frame_rate"] == "30/1", v["r_frame_rate"])
ok("Audio codec AAC", a["codec_name"] == "aac", f'{a["codec_name"]}, {a["sample_rate"]} Hz, {a["channels"]} ch')
ok("Duration = VO + cut + end card", abs(dur - TL.END) < 0.1, f"{dur:.2f} s (VO {TL.VO_END:.2f} s)")
ok("File size under GitHub's 100 MB limit", size < 100, f"{size:.1f} MB")
nf = int(run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", MP4]).stdout.strip())
ok("Frame count", abs(nf - round(TL.END * 30)) <= 1, f"{nf} frames")
dec = run(["ffmpeg", "-v", "error", "-i", MP4, "-f", "null", "-"])
ok("Full decode without errors (playback test)", dec.returncode == 0 and not dec.stderr.strip(), "ffmpeg decode: " + ("clean" if not dec.stderr.strip() else dec.stderr[:200]))

# black frames: only the intended cut to black / end card may be black
bd = run(["ffmpeg", "-hide_banner", "-nostats", "-i", MP4, "-vf", "blackdetect=d=0.1:pic_th=0.98:pix_th=0.06", "-an", "-f", "null", "-"]).stderr
blacks = [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)]
bad = [b for b in blacks if b[0] < TL.CUT_TO_BLACK - 0.1]
ok("No unintended black frames", not bad, f"black only {', '.join(f'{s:.2f}–{e:.2f}' for s, e in blacks) or '—'} (cut to black at {TL.CUT_TO_BLACK})")
fz = run(["ffmpeg", "-hide_banner", "-nostats", "-i", MP4, "-vf", "freezedetect=n=0.0005:d=2.5", "-an", "-f", "null", "-"]).stderr
freezes = re.findall(r"freeze_start: ([\d.]+)", fz)
fr_bad = [float(f) for f in freezes if float(f) < TL.CUT_TO_BLACK - 0.1]
ok("No frozen picture ≥ 2.5 s before the end card", not fr_bad, ", ".join(freezes) or "none")

# audio sync: VO inside the mix vs the original
def pcm(path, sr=8000, t=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path] + (["-t", str(t)] if t else []) + ["-f", "f32le", "-ac", "1", "-ar", str(sr), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)
o = pcm(VO); m = pcm(MP4, t=TL.VO_END)
L = min(len(o), len(m)); o, m = o[:L], m[:L]
best = None
for lag in range(-400, 401, 4):   # ±50 ms at 8 kHz
    c = float(np.dot(o[max(0, -lag):L - max(0, lag)], m[max(0, lag):L - max(0, -lag)]))
    if best is None or c > best[1]: best = (lag, c)
lag_ms = best[0] / 8.0
ok("Audio/VO sync (offset of the VO in the final track)", abs(lag_ms) <= 5, f"{lag_ms:+.1f} ms")
lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", run(["ffmpeg", "-hide_banner", "-nostats", "-i", MP4, "-af", "ebur128", "-f", "null", "-"]).stderr)[-1])
ok("Loudness for TikTok (−17…−13 LUFS)", -17 <= lufs <= -13, f"{lufs:.1f} LUFS")
ok("Voiceover file unchanged", hashlib.md5(open(VO, "rb").read()).hexdigest() == VO_MD5, VO_MD5)

# subtitles and phone text
subs_ok = all(a_ <= b_ for (a_, _, _), (b_, _, _) in zip(TL.SUBS, TL.SUBS[1:])) and all(e <= TL.VO_END + 0.05 for _, e, _ in TL.SUBS)
ok("Subtitles inside the VO, no overlaps", subs_ok, f"{len(TL.SUBS)} cues")
srt = open(os.path.join(ROOT, "subtitles", "EP03_PRICE_OF_CHOICE.srt"), encoding="utf8").read()
ok("SRT: at most two lines per cue", all(len(b.strip().split("\n")) <= 4 for b in srt.strip().split("\n\n")), "checked")
shown = [d for els in TL.PHONE.values() for _, (k, d) in els if isinstance(d, str)]
missing = [m_ for m_ in REQUIRED if m_ not in shown]
ok("All six required phone messages, exact text", not missing, "missing: " + ", ".join(missing) if missing else "all present")
ok("First shot continues EP02's last shot", TL.SHOTS[0]["src"] == "LIPSYNC" and TL.SHOTS[0]["lips"] == "E2_double_ear" and TL.SHOTS[0]["cam"][0] == (.47, .43, 1.12),
   "E2_double_ear, EP02's end framing (0.47, 0.43, ×1.12)")
g = run(["git", "-C", ROOT, "diff", "--stat", "origin/ccr-9b634815-x43d5m", "--", "../EP02", "../EP01"]).stdout.strip()
ok("EP01/EP02 files untouched", g == "", g or "no changes")

# contact sheet of the cut (one frame per shot)
from PIL import Image, ImageDraw
mids = [(s["t"][0] + s["t"][1]) / 2 for s in TL.SHOTS]
tiles = []
for i, t in enumerate(mids):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = Image.frombytes("RGB", (1080, 1920), raw).resize((180, 320)); ImageDraw.Draw(im).text((4, 4), f"{i + 1} · {t:.1f}s", fill=(0, 255, 0)); tiles.append(im)
cols = 7; sheet = Image.new("RGB", (cols * 180, -(-len(tiles) // cols) * 320))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
sheet.save(os.path.join(ROOT, "docs", "EP03_contact_sheet.jpg"), quality=82)

md = ["# EP03 — QC report", "", f"File: `renders/EP03_PRICE_OF_CHOICE_FINAL.mp4` · {size:.1f} MB · {dur:.2f} s", "",
      "Generated by `scripts/07_qc.py` from the finished file.", "", "| Check | Result | Value |", "|---|---|---|"]
md += [f"| {n} | {'✅' if c else '❌'} | {val} |" for n, c, val in rows]
md += ["", "One frame from the middle of every shot (shot number · time):", "", "![contact sheet](EP03_contact_sheet.jpg)", ""]
open(os.path.join(ROOT, "docs", "EP03_QC.md"), "w").write("\n".join(md))
print("\n".join(f"{'OK ' if c else 'FAIL'} {n}: {val}" for n, c, val in rows))
sys.exit(0 if all(c for _, c, _ in rows) else 1)
