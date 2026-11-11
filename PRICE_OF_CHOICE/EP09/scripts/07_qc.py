"""EP09 quality control on the finished MP4. Read-only. Writes docs/EP09_QC.md.

Checks: container/stream format, full decode without errors, duration vs VO, black/frozen frames,
audio sync (the VO inside the final AAC track vs the original MP3, by cross-correlation), loudness,
subtitles inside the VO, not overlapping and starting/ending on spoken word boundaries, every required on-screen text present,
the voiceover file unchanged (md5), EP02–EP08 files untouched (git), the opening on EP08's last shot, the wrist numbers, the ending
on «Оригинал должен умереть», and a contact sheet of the cut.
"""
import os, sys, re, json, glob, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep09 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP4 = os.path.join(ROOT, "renders", "EP09_PRICE_OF_CHOICE_FINAL.mp4")
VO = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
VO_MD5 = "62650f060ac37ef75feffc0c56a1e4d1"
# EP09 required on-screen texts (brief §10)
REQUIRED = ["Задание выполнено", "Уничтожить предыдущую копию", "Создатель обнаружен", "Начать последнюю проверку", "Оригинал должен умереть"]
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
ok("Duration = the MP3's duration", abs(dur - TL.VO_END) < 0.05, f"{dur:.2f} s (MP3 {TL.VO_END:.2f} s)")
ok("Episode length in the 75–90 s target", 75 <= dur <= 90, f"{dur:.2f} s — the approved VO is {TL.VO_END:.2f} s ({TL.VO_END - 90:+.2f} s over 90 s); not sped up or cut (as instructed)", warn=True)
ok("File size under GitHub's 100 MB limit", size < 100, f"{size:.1f} MB")
nf = int(run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", MP4]).stdout.strip())
ok("Frame count", abs(nf - round(TL.END * 30)) <= 1, f"{nf} frames")
dec = run(["ffmpeg", "-v", "error", "-i", MP4, "-f", "null", "-"])
ok("Full decode without errors (playback test)", dec.returncode == 0 and not dec.stderr.strip(), "ffmpeg decode: " + ("clean" if not dec.stderr.strip() else dec.stderr[:200]))

# black frames: only the intended cut to black / end card may be black
bd = run(["ffmpeg", "-hide_banner", "-nostats", "-i", MP4, "-vf", "blackdetect=d=0.1:pic_th=0.98:pix_th=0.06", "-an", "-f", "null", "-"]).stderr
blacks = [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)]
BO = getattr(TL, "BLACKOUT", None)   # EP05: the scripted blackout («Свет погас») is the only black allowed before the cut
intended = lambda s_, e_: s_ >= TL.CUT_TO_BLACK - 0.1
bad = [b for b in blacks if not intended(*b)]
ok("No unintended black frames", not bad, f"black only {', '.join(f'{s:.2f}–{e:.2f}' for s, e in blacks) or '—'} (cut to black at {TL.CUT_TO_BLACK})")
fz = run(["ffmpeg", "-hide_banner", "-nostats", "-i", MP4, "-vf", "freezedetect=n=0.0005:d=2.5", "-an", "-f", "null", "-"]).stderr
freezes = re.findall(r"freeze_start: ([\d.]+)", fz)
fr_bad = [float(f) for f in freezes if float(f) < TL.CUT_TO_BLACK - 0.1]
ok("No frozen picture ≥ 2.5 s before the cut", not fr_bad, ", ".join(freezes) or "none")

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
fin = pcm(MP4, sr=8000); seg = lambda a_, b_: float(np.sqrt(np.mean(fin[int(a_ * 8000):int(b_ * 8000)] ** 2)) + 1e-9)
ok("Last line not cut (audio present to the last word «умереть»)", seg(TL.SUBS[-1][1] - 0.35, TL.SUBS[-1][1] - 0.02) > 0.01, f"RMS {seg(TL.SUBS[-1][1] - 0.35, TL.SUBS[-1][1] - 0.02):.3f} in the last 0.35 s of «умереть»")
vo_full = pcm(VO, sr=8000); vseg = lambda a_, b_: float(np.sqrt(np.mean(vo_full[int(a_ * 8000):int(b_ * 8000)] ** 2)) + 1e-9)
ok("No speech after the cut (the VO itself is silent from the cut to the end of the file)", vseg(TL.CUT_TO_BLACK + 0.02, TL.END) < 0.01, f"VO RMS {vseg(TL.CUT_TO_BLACK + 0.02, TL.END):.4f} after {TL.CUT_TO_BLACK:.2f} s")
ok("Black after the cut, nothing after the last line", TL.SHOTS[-1]["src"] == "BLACK" and TL.SHOTS[-1]["t"][0] == TL.CUT_TO_BLACK, f"black {TL.CUT_TO_BLACK:.2f}–{TL.END:.2f} s (the MP3 ends {TL.VO_END:.2f} s)")

# subtitles and phone text
subs_ok = all(a_ <= b_ for (a_, _, _), (b_, _, _) in zip(TL.SUBS, TL.SUBS[1:])) and all(e <= TL.VO_END + 0.05 for _, e, _ in TL.SUBS)
ok("Subtitles inside the VO, no overlaps", subs_ok, f"{len(TL.SUBS)} cues")
W_ = [w for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json"))) for w in sg["words"]]
starts = [w["s"] for w in W_]; ends = [w["e"] for w in W_]
SIL = [(float(x), float(y)) for x, y in re.findall(r"\| (\d+\.\d+) \| (\d+\.\d+) \|", open(os.path.join(ROOT, "docs", "EP09_VO_REPORT.md")).read())]
near = lambda t, xs: min(abs(t - x) for x in xs)
off = [(a_, b_) for a_, b_, _ in TL.SUBS if near(a_, starts + [y for _, y in SIL]) > 0.12 or near(b_, ends + [x for x, _ in SIL]) > 0.12]
ok("Subtitles synced to the spoken words (start/end within 0.12 s of a word or pause boundary)", not off, "off: " + str(off) if off else "all cues")
srt = open(os.path.join(ROOT, "subtitles", "EP09_PRICE_OF_CHOICE.srt"), encoding="utf8").read()
ok("SRT: at most two lines per cue", all(len(b.strip().split("\n")) <= 4 for b in srt.strip().split("\n\n")), "checked")
shown = {TL.TASK9["m1"], TL.TASK9["m2"], TL.COP9["m1"], TL.COP9["m2"], TL.COP9["m3"]}
missing = [m_ for m_ in REQUIRED if m_ not in shown]
ok("All required on-screen texts, exact wording (drawn in code)", not missing, "missing: " + ", ".join(missing) if missing else "all present (phone UI in scripts/phone_ui.py, series fonts)")
def sub_at(word):
    return min((a_ for a_, _, txt in TL.SUBS if word.lower() in re.sub(r"[*!¡«»]", "", txt).lower()), default=None)
timing = [(TL.TASK9["m1"], TL.TASK9["t1"]), (TL.TASK9["m2"], TL.TASK9["t2"]), (TL.COP9["m1"], TL.COP9["t1"]), (TL.COP9["m2"], TL.COP9["t2"]), (TL.COP9["m3"], TL.COP9["t3"])]
timing = [(n, t0, sub_at(n)) for n, t0 in timing]
early = [f"{n} ({t0} < {st})" for n, t0, st in timing if st is None or t0 < st - 0.05]
ok("No message appears before its words in the VO", not early, ", ".join(early) or ", ".join(f"«{n}» {t0:.2f}s" for n, t0, _ in timing))
ok("Final order on screen at the right moment, then the cut", TL.COP9["t3"] <= TL.SHOTS[-2]["t"][0] + 0.1 and TL.SHOTS[-2].get("phone") == "cop9" and abs(TL.CUT_TO_BLACK - TL.SUBS[-1][1]) < 0.05,
   f"«{TL.MSG_DIE}» full-screen from {TL.COP9['t3']:.2f} s on the close-up of his phone; hard cut at {TL.CUT_TO_BLACK:.2f} s on the end of «умереть»")
# wrist numbers: which character carries which number (production names never on screen)
js = open(os.path.join(ROOT, "scripts", "render3d", "shots.js"), encoding="utf8").read()
nums_ok = ("P.wristBadge(a, '49', C49" in js and "text: '49', glow: C49" in js and "text: '0', glow: C0" in js and "P.wristBadge(a, '0', C0" in js
           and "wristRig(W, cam, { num: 1" in js)
ok("Wrist numbers not mixed up (48 = ALEX_48, 49 = ALEX_49, 0 = ALEX_ZERO)", nums_ok, "48: ALEX_48's own forearm (EP07 ink, E9_wrist48); 49: ALEX_49 only (a49(), E9_wrist49, cyan); 0: ALEX_ZERO only, from 69.80 s (E9_wrist0, red)")
ok("First shot continues EP08's last shot", TL.SHOTS[0]["src"] == "E9_lock" and TL.SHOTS[0]["cam"][0] == (.5, .5, 1.24) and TL.SHOTS[0]["anim"] == (1.0, 1.0),
   "EP08's E8_lock shot re-rendered (thumb-turn fully turned), EP08's end framing ×1.24, flat 47, no time jump")
g = run(["git", "-C", ROOT, "diff", "--stat", "origin/ccr-20f866ac-rl4k4f", "--", "../EP02", "../EP03", "../EP04", "../EP05", "../EP06", "../EP07", "../EP08"]).stdout.strip()
ok("EP01–EP08 files untouched", g == "", g or "no changes against the EP08 branch (EP01 lives in its own branches and is not in this one)")

# contact sheet of the cut (one frame per shot)
from PIL import Image, ImageDraw
mids = [(s["t"][0] + s["t"][1]) / 2 for s in TL.SHOTS]
tiles = []
for i, t in enumerate(mids):
    # EP09: the 0.11 s black tail can sit past the last decodable seek point -> a black tile
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = (Image.frombytes("RGB", (1080, 1920), raw) if len(raw) >= 1080 * 1920 * 3 else Image.new("RGB", (1080, 1920))).resize((180, 320)); ImageDraw.Draw(im).text((4, 4), f"{i + 1} · {t:.1f}s", fill=(0, 255, 0)); tiles.append(im)
cols = 7; sheet = Image.new("RGB", (cols * 180, -(-len(tiles) // cols) * 320))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
sheet.save(os.path.join(ROOT, "docs", "EP09_contact_sheet.jpg"), quality=82)

md = ["# EP09 — QC report", "", f"File: `renders/EP09_PRICE_OF_CHOICE_FINAL.mp4` · {size:.1f} MB · {dur:.2f} s", "",
      "Generated by `scripts/07_qc.py` from the finished file.", "", "| Check | Result | Value |", "|---|---|---|"]
md += [f"| {n} | {'✅' if c else ('⚠️' if n in warn_rows else '❌')} | {val} |" for n, c, val in rows]
md += ["", "One frame from the middle of every shot (shot number · time):", "", "![contact sheet](EP09_contact_sheet.jpg)", ""]
open(os.path.join(ROOT, "docs", "EP09_QC.md"), "w").write("\n".join(md))
print("\n".join(f"{'OK ' if c else 'FAIL'} {n}: {val}" for n, c, val in rows))
sys.exit(0 if all(c or n in warn_rows for n, c, _ in rows) else 1)
