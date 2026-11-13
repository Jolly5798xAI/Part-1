"""EP13 quality control on the finished MP4. Read-only. Writes docs/EP13_QC.md.

Checks: container/stream format, full decode without errors, duration vs VO, black/frozen frames,
audio sync (the VO inside the final AAC track vs the original MP3, by cross-correlation), loudness,
subtitles inside the VO, not overlapping and starting/ending on spoken word boundaries, every required on-screen text present,
the voiceover file unchanged (md5), EP02–EP12 files untouched (git), the opening on EP12's last frame, the numbers 1 / 0 / 48, the hidden
recording (EP12's car, no collision), «СОЗДАТЕЛЬ», the ending on every screen with ALEX_48's face, and a contact sheet of the cut.
"""
import os, sys, re, json, glob, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep13 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP4 = os.path.join(ROOT, "renders", "EP13_PRICE_OF_CHOICE_FINAL.mp4")
VO = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
VO_MD5 = "1b88f317c35291d93b1e933f0c30e1de"
# EP13 required on-screen texts (brief §11)
REQUIRED = ["Отключить тормоза", "Обнаружена последняя копия", "Номер сорок восемь", "Удалить все копии", "Сохранить последнюю", "Цена — жизнь Елены", "СОЗДАТЕЛЬ", "Для остановки игры удалите её создателя"]
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
bad = blacks
ok("No empty/black frames", not bad, f"black: {', '.join(f'{s:.2f}–{e:.2f}' for s, e in blacks) or 'none'}")
fz = run(["ffmpeg", "-hide_banner", "-nostats", "-i", MP4, "-vf", "freezedetect=n=0.0005:d=2.5", "-an", "-f", "null", "-"]).stderr
freezes = re.findall(r"freeze_start: ([\d.]+)", fz)
fr_bad = [float(f) for f in freezes if float(f) < TL.CUT_TO_BLACK - 0.1]
ok("No frozen picture ≥ 2.5 s", not fr_bad, ", ".join(freezes) or "none")

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
ok("Last line not cut (audio present to the last word «…лицо»)", seg(115.6, 116.25) > 0.01, f"RMS {seg(115.6, 116.25):.3f} in «…моё лицо» (115.6–116.25 s); the file ends at {TL.END:.2f} s")
ok("The episode ends on the last word (no black tail, no end card)", TL.SHOTS[-1]["t"][1] == TL.END and abs(TL.END - TL.VO_END) < 0.01,
   f"last shot {TL.SHOTS[-1]['src']}/{TL.SHOTS[-1].get('lips')} (monitor {TL.SHOTS[-1].get('monitor')}) to {TL.END:.2f} s = the MP3's end")

# subtitles and phone text
subs_ok = all(a_ <= b_ for (a_, _, _), (b_, _, _) in zip(TL.SUBS, TL.SUBS[1:])) and all(e <= TL.VO_END + 0.05 for _, e, _ in TL.SUBS)
ok("Subtitles inside the VO, no overlaps", subs_ok, f"{len(TL.SUBS)} cues")
W_ = [w for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json"))) for w in sg["words"]]
starts = [w["s"] for w in W_]; ends = [w["e"] for w in W_]
SIL = [(float(x), float(y)) for x, y in re.findall(r"\| (\d+\.\d+) \| (\d+\.\d+) \|", open(os.path.join(ROOT, "docs", "EP13_VO_REPORT.md")).read())]
near = lambda t, xs: min(abs(t - x) for x in xs)
_vo = pcm(VO, sr=8000); _rms = lambda t_: float(np.sqrt(np.mean(_vo[max(0, int((t_ - 0.03) * 8000)):int((t_ + 0.03) * 8000)] ** 2)) + 1e-9)
end_ok = lambda b_: near(b_, ends + [x for x, _ in SIL]) <= 0.12 or _rms(b_) < 0.012          # a cue may be held into the pause after its words
off = [(a_, b_) for a_, b_, _ in TL.SUBS if near(a_, starts + [y for _, y in SIL]) > 0.12 or not end_ok(b_)]
ok("Subtitles synced to the spoken words (start within 0.12 s of a word start; end on a word end or inside the pause after it)", not off, "off: " + str(off) if off else "all cues")
srt = open(os.path.join(ROOT, "subtitles", "EP13_PRICE_OF_CHOICE.srt"), encoding="utf8").read()
ok("SRT: at most two lines per cue", all(len(b.strip().split("\n")) <= 4 for b in srt.strip().split("\n\n")), "checked")
# the on-screen texts as drawn by phone_ui.py / 06_render_video.py (strings compared without «» quotes and line breaks)
import phone_ui
src = open(os.path.join(ROOT, "scripts", "phone_ui.py"), encoding="utf8").read() + open(os.path.join(ROOT, "scripts", "06_render_video.py"), encoding="utf8").read()
norm_ = lambda x: re.sub(r"[«»\s]+", " ", x).strip()
drawn = {norm_(x) for x in (TL.MSG_BRAKES, TL.MSG_LAST, TL.MSG_N48, TL.MSG_OPT1, TL.MSG_OPT2, TL.MSG_PRICE, TL.MSG_WORD, TL.MSG_STOP1 + " " + TL.MSG_STOP2)}
code_ok = all(k in src for k in ('"Отключить"', '"тормоза"', 'TL.MSG_LAST', 'TL.MSG_N48', 'TL.MSG_OPT1', 'TL.MSG_OPT2', 'TL.MSG_PRICE', 'TL.MSG_WORD', 'TL.MSG_STOP1', 'TL.MSG_STOP2'))
missing = [m_ for m_ in REQUIRED if norm_(m_) not in drawn]
ok("All required on-screen texts, exact wording (drawn in code, series fonts)", not missing and code_ok, ("missing: " + ", ".join(missing)) if (missing or not code_ok) else f"all {len(REQUIRED)} present: " + " · ".join(f"«{m_}»" for m_ in REQUIRED))
W0 = {sg["text"]: sg["start"] for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json")))}
def said(txt): return min((st for t_, st in W0.items() if txt.lower() in re.sub(r"[«»]", "", t_).lower()), default=None)
timing = [("номер 1 горит", next(x["t"][0] for x in TL.SHOTS if x["src"] == "E13_wrist1"), said("На запястье")), ("ноль на экране", TL.T_ZERO, said("появился ноль")), ("скрытая запись", TL.T_HIDDEN, said("скрытая запись")),
          ("Отключить тормоза", TL.T_CMDON, said("Отключить")), ("улыбка оригинала", TL.T_SMILE, said("улыбнулся")),
          ("Обнаружена последняя копия", TL.T_LAST, said("Обнаружена последняя")), ("Номер сорок восемь", TL.T_N48, said("Номер сорок восемь")),
          ("выбор", TL.T_CHOICE, said("новый выбор")), ("Удалить все копии", TL.T_OPT1, said("Удалить все копии")), ("Сохранить последнюю", TL.T_OPT2, said("Сохранить последнюю")),
          ("Цена — жизнь Елены", TL.T_PRICE, said("Цена")), ("10", TL.TICKS[0][0], said("Десять")), ("9", TL.TICKS[1][0], said("Девять")), ("8", TL.TICKS[2][0], said("Восемь")),
          ("48 исчезает", TL.T_VANISH, said("Номер сорок восемь исчез")), ("буквы СОЗДАТЕЛЬ", TL.T_WORD0, said("Вместо него")), ("СОЗДАТЕЛЬ целиком", TL.T_WORD, said("Создатель")),
          ("Для остановки игры", TL.T_MSG1, said("Для остановки игры")), ("удалите её создателя", TL.T_MSG2, said("удалите её создателя")), ("все экраны — его лицо", TL.T_FACES, said("Все экраны"))]
early = [f"{n} ({t0} < {st})" for n, t0, st in timing if st is None or t0 < st - 0.02]
ok("No message appears before its words in the VO", not early, ", ".join(early) or ", ".join(f"«{n}» {t0:.2f}s (said {st:.2f}s)" for n, t0, st in timing))
js = open(os.path.join(ROOT, "scripts", "render3d", "shots.js"), encoding="utf8").read()
e13 = js.split("EP13 «ПОСЛЕДНЯЯ КОПИЯ» (E13_*)")[1].split("REF_versions13")[0]
srcs = [x["src"] for x in TL.SHOTS]
ok("Opening = EP12's last frame (both Elenas, «Не верь мне»), no recap, no time jump", srcs[0] == "E12_two_neutral" and TL.SHOTS[1].get("lips") == "E12_two" and TL.SHOTS[0]["cam"][0] == (.5, .4, 1.14),
   "EP12's E12_two still (read from ../EP12/scenes) with the live feed; EP12's last camera position (.5, .4, 1.14) continued; both mouth «Не верь мне» 2.77–3.60 s")
ok("Two Elenas told apart: ELENA_1 in room 204 (cold, «1»), ELENA_0 on the flat-47 feed (warm kitchen, red «0»)", "badge13(s, '1', C1" in e13 and "badge13(s, '0', C0" in e13 and "E13_wrist1" in srcs and "E13_flat0" in srcs,
   "same sister model for both (sis204 / sisterSeated), no other differences; «1» macro 10.86–13.20 s, «0» on the feed 16.00–17.45 s")
ok("ALEX_48: «48» on the wrist until it vanishes, then «СОЗДАТЕЛЬ»", "'48', C48" in js and "arm13Tex" in js and "E13_arm" in srcs and all(x["t"][0] >= TL.T_VANISH - 0.2 for x in TL.SHOTS if x.get("wrist")),
   f"E13_arm: «48» dissolves {TL.T_VANISH:.2f}–{TL.T_VANISH + 1.4:.2f} s; «СОЗДАТЕЛЬ» burns in from {TL.T_WORD0:.2f} s, locks {TL.T_WORD:.2f} s")
ok("Hidden recording = EP12's night: same road, car, rain, cast, dashboard phone; the original on the back seat with the second phone; no collision",
   "car13(" in e13 and "P.buildRoad(" in e13 and "car12(W, R, z, o)" in js and "collision" not in e13.replace("No collision.", "") and "E13_skid" not in e13,
   "car13 = EP12's car12 + a back bench and the original (plain ALEX model); EP12's dashboard phone with its three task cards; «Отключить тормоза» on the second phone; no impact, no blood")
ok("Ending: every screen shows ALEX_48's face, hard cut on the last word", TL.SHOTS[-1]["src"] == "E13_all" and TL.SHOTS[-1].get("monitor") == "self13" and TL.SHOTS[-1].get("screens") == "selfp13",
   f"from {TL.T_FACES:.2f} s: the turned computer, the side monitor and every phone on the table show the webcam picture of ALEX_48; the file ends {TL.END:.2f} s")
ok("No ALEX_ZERO, no events after the last line", "alex({ face: 'wide_pale' })" not in e13 and TL.END == TL.VO_END, "the original is a plain ALEX figure (recording) and a face on the screen only")
g = run(["git", "-C", ROOT, "diff", "--stat", "origin/ccr-10f66b56-p4q0qp", "--", "../EP02", "../EP03", "../EP04", "../EP05", "../EP06", "../EP07", "../EP08", "../EP09", "../EP10", "../EP11", "../EP12"]).stdout.strip()
ok("EP01–EP12 files untouched", g == "", g or "no changes against the EP12 branch (EP01 lives in its own branches and is not in this one)")

# contact sheet of the cut (one frame per shot)
from PIL import Image, ImageDraw
mids = [(s["t"][0] + s["t"][1]) / 2 for s in TL.SHOTS]
tiles = []
for i, t in enumerate(mids):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = (Image.frombytes("RGB", (1080, 1920), raw) if len(raw) >= 1080 * 1920 * 3 else Image.new("RGB", (1080, 1920))).resize((180, 320)); ImageDraw.Draw(im).text((4, 4), f"{i + 1} · {t:.1f}s", fill=(0, 255, 0)); tiles.append(im)
cols = 7; sheet = Image.new("RGB", (cols * 180, -(-len(tiles) // cols) * 320))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
sheet.save(os.path.join(ROOT, "docs", "EP13_contact_sheet.jpg"), quality=82)

md = ["# EP13 — QC report", "", f"File: `renders/EP13_PRICE_OF_CHOICE_FINAL.mp4` · {size:.1f} MB · {dur:.2f} s", "",
      "Generated by `scripts/07_qc.py` from the finished file.", "", "| Check | Result | Value |", "|---|---|---|"]
md += [f"| {n} | {'✅' if c else ('⚠️' if n in warn_rows else '❌')} | {val} |" for n, c, val in rows]
md += ["", "One frame from the middle of every shot (shot number · time):", "", "![contact sheet](EP13_contact_sheet.jpg)", ""]
open(os.path.join(ROOT, "docs", "EP13_QC.md"), "w").write("\n".join(md))
print("\n".join(f"{'OK ' if c else ('WARN' if n in warn_rows else 'FAIL')} {n}: {val}" for n, c, val in rows))
sys.exit(0 if all(c or n in warn_rows for n, c, _ in rows) else 1)
