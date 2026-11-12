"""EP11 quality control on the finished MP4. Read-only. Writes docs/EP11_QC.md.

Checks: container/stream format, full decode without errors, duration vs VO, black/frozen frames,
audio sync (the VO inside the final AAC track vs the original MP3, by cross-correlation), loudness,
subtitles inside the VO, not overlapping and starting/ending on spoken word boundaries, every required on-screen text present,
the voiceover file unchanged (md5), EP02–EP10 files untouched (git), the opening on EP10's last screen, the wrist numbers, the ending
(the last frame is «Оригинал проснулся» on the turned screen) and a contact sheet of the cut.
"""
import os, sys, re, json, glob, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep11 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP4 = os.path.join(ROOT, "renders", "EP11_PRICE_OF_CHOICE_FINAL.mp4")
VO = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
VO_MD5 = "5974a54f41fada113993a12605b97d1a"
# EP11 required on-screen texts (brief §10)
REQUIRED = ["Следующий игрок: Елена", "Выберите, кого сохранить", "Создателя или игрока", "Нулевой уровень активирован", "Удаление всех копий", "Подключение к оригиналу установлено", "Оригинал проснулся"]
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
intended = lambda s_, e_: False                                   # EP11: no black at all (the file ends on the last word)
bad = [b for b in blacks if not intended(*b)]
ok("No black frames", not bad, f"black: {', '.join(f'{s:.2f}–{e:.2f}' for s, e in blacks) or 'none'}")
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
ok("Last line not cut (audio present to the last word «…проснулся»)", seg(TL.END - 0.4, TL.END - 0.05) > 0.01, f"RMS {seg(TL.END - 0.4, TL.END - 0.05):.3f} in the last 0.35 s of «проснулся»")
ok("The episode ends on the last word (no black tail, no end card)", TL.SHOTS[-1]["t"][1] == TL.END and TL.SHOTS[-1].get("monitor") == "face11" and abs(TL.END - TL.VO_END) < 0.01,
   f"last shot {TL.SHOTS[-1]['src']} (monitor face11) to {TL.END:.2f} s = the MP3's end")

# subtitles and phone text
subs_ok = all(a_ <= b_ for (a_, _, _), (b_, _, _) in zip(TL.SUBS, TL.SUBS[1:])) and all(e <= TL.VO_END + 0.05 for _, e, _ in TL.SUBS)
ok("Subtitles inside the VO, no overlaps", subs_ok, f"{len(TL.SUBS)} cues")
W_ = [w for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json"))) for w in sg["words"]]
starts = [w["s"] for w in W_]; ends = [w["e"] for w in W_]
SIL = [(float(x), float(y)) for x, y in re.findall(r"\| (\d+\.\d+) \| (\d+\.\d+) \|", open(os.path.join(ROOT, "docs", "EP11_VO_REPORT.md")).read())]
near = lambda t, xs: min(abs(t - x) for x in xs)
_vo = pcm(VO, sr=8000); _rms = lambda t_: float(np.sqrt(np.mean(_vo[max(0, int((t_ - 0.03) * 8000)):int((t_ + 0.03) * 8000)] ** 2)) + 1e-9)
end_ok = lambda b_: near(b_, ends + [x for x, _ in SIL]) <= 0.12 or _rms(b_) < 0.012          # a cue may be held into the pause after its words
off = [(a_, b_) for a_, b_, _ in TL.SUBS if near(a_, starts + [y for _, y in SIL]) > 0.12 or not end_ok(b_)]
ok("Subtitles synced to the spoken words (start within 0.12 s of a word start; end on a word end or inside the pause after it)", not off, "off: " + str(off) if off else "all cues")
srt = open(os.path.join(ROOT, "subtitles", "EP11_PRICE_OF_CHOICE.srt"), encoding="utf8").read()
ok("SRT: at most two lines per cue", all(len(b.strip().split("\n")) <= 4 for b in srt.strip().split("\n\n")), "checked")
# the on-screen texts as drawn by phone_ui.py (strings compared without «» quotes and line breaks)
import phone_ui
src = open(os.path.join(ROOT, "scripts", "phone_ui.py"), encoding="utf8").read()
norm_ = lambda x: re.sub(r"[«»\s]+", " ", x).strip()
drawn = {norm_(x) for x in ("Следующий игрок: Елена", TL.MSG_TITLE, f"{TL.MSG_OPT1} {TL.MSG_OR} {TL.MSG_OPT2}", TL.MSG_ZERO, TL.MSG_DEL, TL.MSG_LINK, TL.MSG_WOKE)}
code_ok = all(k in src for k in ('"Следующий игрок:"', '"Елена"', '"Выберите,", "кого сохранить"', '"Создателя"', '"или"', '"игрока"', '"Нулевой уровень", "активирован"',
                                 '"Удаление"', '"всех копий"', '"Подключение", "к оригиналу установлено"', '"Оригинал"', '"проснулся"'))
missing = [m_ for m_ in REQUIRED if norm_(m_) not in drawn]
ok("All required on-screen texts, exact wording (drawn in code)", not missing and code_ok, "missing: " + ", ".join(missing) if missing or not code_ok else f"all {len(REQUIRED)} present (phone/monitor UI in scripts/phone_ui.py, series fonts)")
W0 = {sg["text"]: sg["start"] for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json")))}
def said(txt): return min((st for t_, st in W0.items() if txt.lower() in re.sub(r"[«»]", "", t_).lower()), default=None)
timing = [("Следующий игрок", TL.T_NEXT, said("Следующий игрок")), ("Елена (next player)", TL.T_NEXT_NAME, 1.91),
          ("Выберите, кого сохранить", TL.T_TITLE, said("Выберите, кого сохранить")), ("Создателя", TL.T_OPT1, said("Создателя")), ("или игрока", TL.T_OPT2, 23.48),
          ("красный экран", TL.T_RED, said("загорелся красным")), ("Нулевой уровень активирован", TL.T_ZERO, said("Нулевой уровень активирован")),
          ("Удаление всех копий", TL.T_DEL, said("Удаление всех копий")), ("лицо на экране", TL.T_FACE, said("появилось моё лицо")), ("глаза открылись", TL.T_EYES, said("глаза открылись")),
          ("Подключение к оригиналу установлено", TL.T_MSG1, said("Подключение к оригиналу")), ("Оригинал проснулся", TL.T_MSG2, said("Оригинал проснулся"))]
early = [f"{n} ({t0} < {st})" for n, t0, st in timing if st is None or t0 < st - 0.02]
ok("No message appears before its words in the VO", not early, ", ".join(early) or ", ".join(f"«{n}» {t0:.2f}s (said {st:.2f}s)" for n, t0, st in timing))
ok("Ending: the original wakes — «Подключение к оригиналу установлено», then «Оригинал проснулся» on the last frame", TL.T_MSG1 < TL.T_MSG2 < TL.END and TL.SHOTS[-1].get("monitor") == "face11",
   f"«{TL.MSG_LINK}» {TL.T_MSG1:.2f} s → «{TL.MSG_WOKE}» {TL.T_MSG2:.2f} s → file ends {TL.END:.2f} s; nothing of what the original does next")
js = open(os.path.join(ROOT, "scripts", "render3d", "shots.js"), encoding="utf8").read()
e11 = js.split("EP11 «НУЛЕВОЙ УРОВЕНЬ» (E11_*)")[1].split("REF_versions11")[0]
nums_ok = ("a49(W, B11[0], B11[1]" in e11 and "num0" not in e11 and "zero(" not in e11 and "wristRig(W, cam, { num: 1" in e11 and "'49'" not in e11)
ok("Wrist numbers not mixed up (48 = ALEX_48, 49 = ALEX_49; ALEX_ZERO and his 0 not on screen)", nums_ok, "48: ALEX_48's forearm (E11_hand, EP07 ink); 49: ALEX_49 only (a49(), E11_a49_dust); no «0» anywhere in EP11")
ok("First shot continues EP10's last screen", TL.SHOTS[0]["src"] == "E10_pov_end" and TL.SHOTS[0]["phone"] == "next11" and TL.SHOTS[1]["src"] == "E11_door204",
   "EP10's E10_pov_end still (read from ../EP10/scenes) with EP10's final screen, then door 204 under the red lamp (EP10's last shot) — no time jump")
g = run(["git", "-C", ROOT, "diff", "--stat", "origin/ccr-36be756c-nrqgjk", "--", "../EP02", "../EP03", "../EP04", "../EP05", "../EP06", "../EP07", "../EP08", "../EP09", "../EP10"]).stdout.strip()
ok("EP01–EP10 files untouched", g == "", g or "no changes against the EP10 branch (EP01 lives in its own branches and is not in this one)")

# contact sheet of the cut (one frame per shot)
from PIL import Image, ImageDraw
mids = [(s["t"][0] + s["t"][1]) / 2 for s in TL.SHOTS]
tiles = []
for i, t in enumerate(mids):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = (Image.frombytes("RGB", (1080, 1920), raw) if len(raw) >= 1080 * 1920 * 3 else Image.new("RGB", (1080, 1920))).resize((180, 320)); ImageDraw.Draw(im).text((4, 4), f"{i + 1} · {t:.1f}s", fill=(0, 255, 0)); tiles.append(im)
cols = 7; sheet = Image.new("RGB", (cols * 180, -(-len(tiles) // cols) * 320))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
sheet.save(os.path.join(ROOT, "docs", "EP11_contact_sheet.jpg"), quality=82)

md = ["# EP11 — QC report", "", f"File: `renders/EP11_PRICE_OF_CHOICE_FINAL.mp4` · {size:.1f} MB · {dur:.2f} s", "",
      "Generated by `scripts/07_qc.py` from the finished file.", "", "| Check | Result | Value |", "|---|---|---|"]
md += [f"| {n} | {'✅' if c else ('⚠️' if n in warn_rows else '❌')} | {val} |" for n, c, val in rows]
md += ["", "One frame from the middle of every shot (shot number · time):", "", "![contact sheet](EP11_contact_sheet.jpg)", ""]
open(os.path.join(ROOT, "docs", "EP11_QC.md"), "w").write("\n".join(md))
print("\n".join(f"{'OK ' if c else ('WARN' if n in warn_rows else 'FAIL')} {n}: {val}" for n, c, val in rows))
sys.exit(0 if all(c or n in warn_rows for n, c, _ in rows) else 1)
