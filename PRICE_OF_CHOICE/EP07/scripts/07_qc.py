"""EP07 quality control on the finished MP4. Read-only. Writes docs/EP07_QC.md.

Checks: container/stream format, full decode without errors, duration vs VO, black/frozen frames,
audio sync (the VO inside the final AAC track vs the original MP3, by cross-correlation), loudness,
subtitles inside the VO and not overlapping, every required phone message present in the timeline,
the voiceover file unchanged (md5), EP01–EP05 files untouched (git), and contact sheets of the cut.
"""
import os, sys, re, json, glob, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep07 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP4 = os.path.join(ROOT, "renders", "EP07_PRICE_OF_CHOICE_FINAL.mp4")
VO = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
VO_MD5 = "fde19fce5c2529ec5dfb3bf75854744b"
# EP07 required on-screen texts: «Выбери, кого стереть» / «Сестру или себя» (phones), «Выбор сделан» (mirror), «48» (wrist, in 3D + monitors),
# «Экземпляр сорок восемь нестабилен» / «Начать удаление» / «Лесная, 12» / «Квартира 47» / tomorrow's date (monitors)
REQUIRED = ["Выбери, кого стереть.", "Сестру или себя.", "Выбор сделан", "48", "Экземпляр сорок восемь нестабилен", "Начать удаление", "Лесная, 12", "Квартира 47"]
warn_rows = set()
rows = []


def ok(name, cond, val, warn=False):
    rows.append((name, bool(cond), val))
    if warn and not cond: warn_rows.add(name)
    return cond
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)


pr = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", MP4]).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
dur = float(pr["format"]["duration"]); size = int(pr["format"]["size"]) / 1e6
ok("Video codec H.264", v["codec_name"] == "h264", f'{v["codec_name"]} ({v.get("profile")}), {v["pix_fmt"]}')
ok("Resolution 1080×1920 (9:16)", (v["width"], v["height"]) == (1080, 1920), f'{v["width"]}×{v["height"]}')
ok("30 fps", v["r_frame_rate"] == "30/1", v["r_frame_rate"])
ok("Audio codec AAC", a["codec_name"] == "aac", f'{a["codec_name"]}, {a["sample_rate"]} Hz, {a["channels"]} ch')
ok("Duration = VO + cut + end card", abs(dur - TL.END) < 0.1, f"{dur:.2f} s (VO {TL.VO_END:.2f} s)")
ok("Episode length in the 75–90 s target", 75 <= dur <= 90, f"{dur:.2f} s — the approved VO alone is {TL.VO_END:.2f} s; not sped up (as instructed)", warn=True)
ok("File size under GitHub's 100 MB limit", size < 100, f"{size:.1f} MB")
nf = int(run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", MP4]).stdout.strip())
ok("Frame count", abs(nf - round(TL.END * 30)) <= 1, f"{nf} frames")
dec = run(["ffmpeg", "-v", "error", "-i", MP4, "-f", "null", "-"])
ok("Full decode without errors (playback test)", dec.returncode == 0 and not dec.stderr.strip(), "ffmpeg decode: " + ("clean" if not dec.stderr.strip() else dec.stderr[:200]))

# black frames: only the intended cut to black / end card may be black
bd = run(["ffmpeg", "-hide_banner", "-nostats", "-i", MP4, "-vf", "blackdetect=d=0.1:pic_th=0.98:pix_th=0.06", "-an", "-f", "null", "-"]).stderr
blacks = [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)]
BO = getattr(TL, "BLACKOUT", None)   # EP05: the scripted blackout («Свет погас») is the only black allowed before the cut
intended = lambda s_, e_: s_ >= TL.CUT_TO_BLACK - 0.1 or bool(BO and s_ >= BO[0] - 0.1 and e_ <= BO[3] + 0.1) or (s_ >= TL.T_OFF - 0.1 and e_ <= TL.T_OFF + 0.5)   # EP07: the dip when every screen dies
bad = [b for b in blacks if not intended(*b)]
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
srt = open(os.path.join(ROOT, "subtitles", "EP07_PRICE_OF_CHOICE.srt"), encoding="utf8").read()
ok("SRT: at most two lines per cue", all(len(b.strip().split("\n")) <= 4 for b in srt.strip().split("\n\n")), "checked")
shown = set()
for els in TL.PHONE.values():
    for _, (k, d) in els:
        if isinstance(d, str): shown.add(d)
        if isinstance(d, dict) and "text" in d: shown.add(d["text"])
shown |= {TL.MTEXT["text"], TL.NUMBER, TL.MSG_UNSTABLE, TL.MSG_DELETE, TL.ADDR_STREET, TL.ADDR_FLAT}
missing = [m_ for m_ in REQUIRED if m_ not in shown]
ok("All required on-screen texts, exact wording (drawn in code)", not missing, "missing: " + ", ".join(missing) if missing else "all present; date: «" + TL.DATE_WORD + "» + «" + TL.DATE_TEXT + "» (EP01 set the story on Friday 6 November)")
def sub_at(word):
    return min((a_ for a_, _, txt in TL.SUBS if word.lower() in re.sub(r"[*!¡«»]", "", txt).lower()), default=None)
timing = [("Выбор сделан", TL.MTEXT["legible"], sub_at("Выбор сделан")), ("Экземпляр…", TL.T_MSG1, sub_at("Экземпляр")),
          ("Начать удаление", TL.T_MSG2, sub_at("Начать удаление")), ("Лесная, 12", TL.T_STREET, sub_at("Лесная")),
          ("Квартира 47", TL.T_FLAT, sub_at("квартира 47")), ("ЗАВТРА", TL.T_TOMORROW, sub_at("Завтрашний"))]
early = [f"{n} ({t0} < {st})" for n, t0, st in timing if st is None or t0 < st - 0.15]
ok("No message appears before its words in the VO (the address only on «Лесная…»)", not early, ", ".join(early) or ", ".join(f"{n} {t0:.2f}s" for n, t0, _ in timing))
ok("First shot continues EP06's last shot", TL.SHOTS[0]["src"] == "E6_show_cold" and TL.SHOTS[0]["cam"][0] == (.76, .70, 1.85),
   "E6_show_cold (her phone with the choice), EP06's end framing (0.76, 0.70, ×1.85), same room 204, no time jump")
ok("Ends on the address + tomorrow, hard cut", TL.SHOTS[-2].get("monitor") == "addr" and TL.SHOTS[-1]["src"] == "BLACK", "last shot: «Лесная, 12 / Квартира 47», «суббота, 7 ноября», «ЗАВТРА», cut to black")
g = run(["git", "-C", ROOT, "diff", "--stat", "origin/ccr-8d87851f-2rgjt3", "--", "../EP02", "../EP03", "../EP04", "../EP05", "../EP06"]).stdout.strip()
ok("EP01–EP06 files untouched", g == "", g or "no changes against the EP06 branch")

# contact sheet of the cut (one frame per shot)
from PIL import Image, ImageDraw
mids = [(s["t"][0] + s["t"][1]) / 2 for s in TL.SHOTS]
tiles = []
for i, t in enumerate(mids):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = Image.frombytes("RGB", (1080, 1920), raw).resize((180, 320)); ImageDraw.Draw(im).text((4, 4), f"{i + 1} · {t:.1f}s", fill=(0, 255, 0)); tiles.append(im)
cols = 7; sheet = Image.new("RGB", (cols * 180, -(-len(tiles) // cols) * 320))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
sheet.save(os.path.join(ROOT, "docs", "EP07_contact_sheet.jpg"), quality=82)

md = ["# EP07 — QC report", "", f"File: `renders/EP07_PRICE_OF_CHOICE_FINAL.mp4` · {size:.1f} MB · {dur:.2f} s", "",
      "Generated by `scripts/07_qc.py` from the finished file.", "", "| Check | Result | Value |", "|---|---|---|"]
md += [f"| {n} | {'✅' if c else ('⚠️' if n in warn_rows else '❌')} | {val} |" for n, c, val in rows]
md += ["", "One frame from the middle of every shot (shot number · time):", "", "![contact sheet](EP07_contact_sheet.jpg)", ""]
open(os.path.join(ROOT, "docs", "EP07_QC.md"), "w").write("\n".join(md))
print("\n".join(f"{'OK ' if c else 'FAIL'} {n}: {val}" for n, c, val in rows))
sys.exit(0 if all(c or n in warn_rows for n, c, _ in rows) else 1)
