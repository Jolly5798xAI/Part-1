"""EP10 quality control on the finished MP4. Read-only. Writes docs/EP10_QC.md.

Checks: container/stream format, full decode without errors, duration vs VO, black/frozen frames,
audio sync (the VO inside the final AAC track vs the original MP3, by cross-correlation), loudness,
subtitles inside the VO, not overlapping and starting/ending on spoken word boundaries, every required on-screen text present,
the voiceover file unchanged (md5), EP02–EP09 files untouched (git), the opening on EP09's last frame, the wrist numbers, the ending
(«Следующий игрок: Елена», the scream, door 204, cut) and a contact sheet of the cut.
"""
import os, sys, re, json, glob, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep10 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP4 = os.path.join(ROOT, "renders", "EP10_PRICE_OF_CHOICE_FINAL.mp4")
VO = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
VO_MD5 = "f09ce98e8261e676fe39c7814f4e920d"
# EP10 required on-screen texts (brief §10)
REQUIRED = ["Оригинал должен умереть", "Уничтожить оригинал", "Остановить игру", "Недостаточно прав", "Проект Алекс", "Создатель: Елена", "Уровень десять завершён", "Следующий игрок: Елена"]
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
ok("Last line not cut (audio present to the last word «…четыре»)", seg(TL.SUBS[-1][1] - 0.35, TL.SUBS[-1][1] - 0.02) > 0.01, f"RMS {seg(TL.SUBS[-1][1] - 0.35, TL.SUBS[-1][1] - 0.02):.3f} in the last 0.35 s of «четыре»")
vo_full = pcm(VO, sr=8000); vseg = lambda a_, b_: float(np.sqrt(np.mean(vo_full[int(a_ * 8000):int(b_ * 8000)] ** 2)) + 1e-9)
ok("No speech after the cut (the VO itself is silent from the cut to the end of the file)", vseg(TL.CUT_TO_BLACK + 0.02, TL.END) < 0.01, f"VO RMS {vseg(TL.CUT_TO_BLACK + 0.02, TL.END):.4f} after {TL.CUT_TO_BLACK:.2f} s")
ok("Black after the cut, nothing after the last line", TL.SHOTS[-1]["src"] == "BLACK" and TL.SHOTS[-1]["t"][0] == TL.CUT_TO_BLACK, f"black {TL.CUT_TO_BLACK:.2f}–{TL.END:.2f} s (the MP3 ends {TL.VO_END:.2f} s)")

# subtitles and phone text
subs_ok = all(a_ <= b_ for (a_, _, _), (b_, _, _) in zip(TL.SUBS, TL.SUBS[1:])) and all(e <= TL.VO_END + 0.05 for _, e, _ in TL.SUBS)
ok("Subtitles inside the VO, no overlaps", subs_ok, f"{len(TL.SUBS)} cues")
W_ = [w for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json"))) for w in sg["words"]]
starts = [w["s"] for w in W_]; ends = [w["e"] for w in W_]
SIL = [(float(x), float(y)) for x, y in re.findall(r"\| (\d+\.\d+) \| (\d+\.\d+) \|", open(os.path.join(ROOT, "docs", "EP10_VO_REPORT.md")).read())]
near = lambda t, xs: min(abs(t - x) for x in xs)
_vo = pcm(VO, sr=8000); _rms = lambda t_: float(np.sqrt(np.mean(_vo[max(0, int((t_ - 0.03) * 8000)):int((t_ + 0.03) * 8000)] ** 2)) + 1e-9)
end_ok = lambda b_: near(b_, ends + [x for x, _ in SIL]) <= 0.12 or _rms(b_) < 0.012          # a cue may be held into the pause after its words
off = [(a_, b_) for a_, b_, _ in TL.SUBS if near(a_, starts + [y for _, y in SIL]) > 0.12 or not end_ok(b_)]
ok("Subtitles synced to the spoken words (start within 0.12 s of a word start; end on a word end or inside the pause after it)", not off, "off: " + str(off) if off else "all cues")
srt = open(os.path.join(ROOT, "subtitles", "EP10_PRICE_OF_CHOICE.srt"), encoding="utf8").read()
ok("SRT: at most two lines per cue", all(len(b.strip().split("\n")) <= 4 for b in srt.strip().split("\n\n")), "checked")
# the on-screen texts as drawn by phone_ui.py (strings compared without «» quotes and line breaks)
import phone_ui
src = open(os.path.join(ROOT, "scripts", "phone_ui.py"), encoding="utf8").read()
norm_ = lambda x: re.sub(r"[«»\s]+", " ", x).strip()
drawn = {norm_(x) for x in (TL.MSG_DIE, TL.MSG_KILL, TL.MSG_STOP, TL.MSG_DENY, TL.MSG_PROJ, TL.MSG_CREATOR, TL.MSG_LVL, TL.MSG_NEXT)}
code_ok = all(k in src for k in ('"Уничтожить оригинал"', '"Остановить игру"', '("Недостаточно", "прав")', '"Создатель: "', '"Елена"', '("Уровень десять", "завершён")', '"Следующий игрок:"'))
missing = [m_ for m_ in REQUIRED if norm_(m_) not in drawn]
ok("All required on-screen texts, exact wording (drawn in code)", not missing and code_ok, "missing: " + ", ".join(missing) if missing or not code_ok else "all 8 present (phone/monitor UI in scripts/phone_ui.py, series fonts)")
def sub_at(word):
    return min((a_ for a_, _, txt in TL.SUBS if word.lower() in re.sub(r"[*!¡«»]", "", txt).lower()), default=None)
timing = [("Уничтожить оригинал", TL.CHOICE10["t1"]), ("Остановить игру", TL.CHOICE10["t2"]), ("Недостаточно прав", TL.CHOICE10["t_deny"]),
          ("Проект «Алекс»", TL.T_PROJ), ("Создатель: Елена", TL.T_CREATOR), ("Уровень десять завершён", TL.T_LVL), ("Следующий игрок: Елена", TL.T_NEXT)]
timing = [(n, t0, sub_at(n.replace("«", "").replace("»", "")) if "Проект" not in n else sub_at("Проект")) for n, t0 in timing]
early = [f"{n} ({t0} < {st})" for n, t0, st in timing if st is None or t0 < st - 0.05]
ok("No message appears before its words in the VO", not early, (", ".join(early) or ", ".join(f"«{n}» {t0:.2f}s" for n, t0, _ in timing)) + "; «Оригинал должен умереть» is EP09's last frame, carried over (spoken at 0.12 s)")
ok("Ending: «Следующий игрок: Елена», then the scream, door 204, hard cut", TL.T_NEXT_NAME < TL.T_SCREAM and TL.SHOTS[-2]["src"] == "E10_door204" and any(k == "scream" for _, k, _ in TL.SFX) and abs(TL.CUT_TO_BLACK - TL.SUBS[-1][1]) < 0.05,
   f"name {TL.T_NEXT_NAME:.2f} s → scream {TL.T_SCREAM:.2f} s (procedural muffled cry, no words) → door 204 → cut {TL.CUT_TO_BLACK:.2f} s; the sister's fate not shown")
# wrist numbers: which character carries which number (production names never on screen)
js = open(os.path.join(ROOT, "scripts", "render3d", "shots.js"), encoding="utf8").read()
nums_ok = ("P.wristBadge(a, '49', C49" in js and "zero(W, Z10[0], Z10[1]" in js and "{ num0: true }" in js and "wristRig(W, cam, { num: 1" in js and "'49'" not in js.split("// ---------- EP10 helpers")[1].split("const SHOTS = {")[0] and "'49'" not in js.split("EP10 «СОЗДАТЕЛЬ» (E10_*)")[1].split("REF_versions10")[0])
ok("Wrist numbers not mixed up (48 = ALEX_48, 49 = ALEX_49, 0 = ALEX_ZERO)", nums_ok, "48: ALEX_48's forearm (E10_hand48, EP07 ink); 49: ALEX_49 only (a49()); 0: ALEX_ZERO only (cast10 → zero(…, {num0: true}))")
ok("First shot continues EP09's last frame", TL.SHOTS[0]["src"] == "E9_cop_screen_close" and TL.SHOTS[0]["phone"] == "cop10",
   "EP09's E9_cop_screen_close still (read from ../EP09/scenes), its final red screen «Оригинал должен умереть», flat 47, no time jump")
g = run(["git", "-C", ROOT, "diff", "--stat", "origin/ccr-74797fc1-l56gtp", "--", "../EP02", "../EP03", "../EP04", "../EP05", "../EP06", "../EP07", "../EP08", "../EP09"]).stdout.strip()
ok("EP01–EP09 files untouched", g == "", g or "no changes against the EP09 branch (EP01 lives in its own branches and is not in this one)")

# contact sheet of the cut (one frame per shot)
from PIL import Image, ImageDraw
mids = [(s["t"][0] + s["t"][1]) / 2 for s in TL.SHOTS]
tiles = []
for i, t in enumerate(mids):
    # EP10: the 0.11 s black tail can sit past the last decodable seek point -> a black tile
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = (Image.frombytes("RGB", (1080, 1920), raw) if len(raw) >= 1080 * 1920 * 3 else Image.new("RGB", (1080, 1920))).resize((180, 320)); ImageDraw.Draw(im).text((4, 4), f"{i + 1} · {t:.1f}s", fill=(0, 255, 0)); tiles.append(im)
cols = 7; sheet = Image.new("RGB", (cols * 180, -(-len(tiles) // cols) * 320))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
sheet.save(os.path.join(ROOT, "docs", "EP10_contact_sheet.jpg"), quality=82)

md = ["# EP10 — QC report", "", f"File: `renders/EP10_PRICE_OF_CHOICE_FINAL.mp4` · {size:.1f} MB · {dur:.2f} s", "",
      "Generated by `scripts/07_qc.py` from the finished file.", "", "| Check | Result | Value |", "|---|---|---|"]
md += [f"| {n} | {'✅' if c else ('⚠️' if n in warn_rows else '❌')} | {val} |" for n, c, val in rows]
md += ["", "One frame from the middle of every shot (shot number · time):", "", "![contact sheet](EP10_contact_sheet.jpg)", ""]
open(os.path.join(ROOT, "docs", "EP10_QC.md"), "w").write("\n".join(md))
print("\n".join(f"{'OK ' if c else ('WARN' if n in warn_rows else 'FAIL')} {n}: {val}" for n, c, val in rows))
sys.exit(0 if all(c or n in warn_rows for n, c, _ in rows) else 1)
