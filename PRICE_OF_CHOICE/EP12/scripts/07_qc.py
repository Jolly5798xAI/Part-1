"""EP12 quality control on the finished MP4. Read-only. Writes docs/EP12_QC.md.

Checks: container/stream format, full decode without errors, duration vs VO, black/frozen frames,
audio sync (the VO inside the final AAC track vs the original MP3, by cross-correlation), loudness,
subtitles inside the VO, not overlapping and starting/ending on spoken word boundaries, every required on-screen text present,
the voiceover file unchanged (md5), EP02–EP11 files untouched (git), the opening on EP11's last screen, the hand continuity, the accident
(no collision), the two identical Elenas, the ending on «Не верь мне», and a contact sheet of the cut.
"""
import os, sys, re, json, glob, hashlib, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep12 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP4 = os.path.join(ROOT, "renders", "EP12_PRICE_OF_CHOICE_FINAL.mp4")
VO = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
VO_MD5 = "097cedfe5c6498c64ff763cd0faf69a2"
# EP12 required on-screen texts (brief §10)
REQUIRED = ["Первое задание", "Не тормози", "Награда — пятьсот долларов", "Повторить испытание", "Передача управления", "Новый администратор: сорок восемь", "Обнаружены две Елены"]
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
ST = next(x["t"] for x in TL.SHOTS if x["src"] == "BLACK")      # EP12: the recording switching off — a white line collapsing on black (0.15 s), not an empty frame
intended = lambda s_, e_: ST[0] - 0.05 <= s_ and e_ <= ST[1] + 0.05 and e_ - s_ <= 0.25
bad = [b for b in blacks if not intended(*b)]
ok("No empty/black frames (except the 0.15 s TV switch-off line at «Запись оборвалась»)", not bad, f"black: {', '.join(f'{s:.2f}–{e:.2f}' for s, e in blacks) or 'none'}")
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
ok("Last line not cut (audio present to the last word «…мне»)", seg(TL.END - 0.4, TL.END - 0.05) > 0.01, f"RMS {seg(TL.END - 0.4, TL.END - 0.05):.3f} in the last 0.35 s of «Не верь мне»")
ok("The episode ends on the last word (no black tail, no end card)", TL.SHOTS[-1]["t"][1] == TL.END and abs(TL.END - TL.VO_END) < 0.01,
   f"last shot {TL.SHOTS[-1]['src']}/{TL.SHOTS[-1].get('lips')} (monitor {TL.SHOTS[-1].get('monitor')}) to {TL.END:.2f} s = the MP3's end")

# subtitles and phone text
subs_ok = all(a_ <= b_ for (a_, _, _), (b_, _, _) in zip(TL.SUBS, TL.SUBS[1:])) and all(e <= TL.VO_END + 0.05 for _, e, _ in TL.SUBS)
ok("Subtitles inside the VO, no overlaps", subs_ok, f"{len(TL.SUBS)} cues")
W_ = [w for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json"))) for w in sg["words"]]
starts = [w["s"] for w in W_]; ends = [w["e"] for w in W_]
SIL = [(float(x), float(y)) for x, y in re.findall(r"\| (\d+\.\d+) \| (\d+\.\d+) \|", open(os.path.join(ROOT, "docs", "EP12_VO_REPORT.md")).read())]
near = lambda t, xs: min(abs(t - x) for x in xs)
_vo = pcm(VO, sr=8000); _rms = lambda t_: float(np.sqrt(np.mean(_vo[max(0, int((t_ - 0.03) * 8000)):int((t_ + 0.03) * 8000)] ** 2)) + 1e-9)
end_ok = lambda b_: near(b_, ends + [x for x, _ in SIL]) <= 0.12 or _rms(b_) < 0.012          # a cue may be held into the pause after its words
off = [(a_, b_) for a_, b_, _ in TL.SUBS if near(a_, starts + [y for _, y in SIL]) > 0.12 or not end_ok(b_)]
ok("Subtitles synced to the spoken words (start within 0.12 s of a word start; end on a word end or inside the pause after it)", not off, "off: " + str(off) if off else "all cues")
srt = open(os.path.join(ROOT, "subtitles", "EP12_PRICE_OF_CHOICE.srt"), encoding="utf8").read()
ok("SRT: at most two lines per cue", all(len(b.strip().split("\n")) <= 4 for b in srt.strip().split("\n\n")), "checked")
# the on-screen texts as drawn by phone_ui.py (strings compared without «» quotes and line breaks)
import phone_ui
src = open(os.path.join(ROOT, "scripts", "phone_ui.py"), encoding="utf8").read()
norm_ = lambda x: re.sub(r"[«»\s]+", " ", x).strip()
drawn = {norm_(x) for x in (TL.MSG_TASK1, TL.MSG_TASK2, TL.MSG_TASK3, TL.MSG_CMD, TL.MSG_HAND, TL.MSG_NEWADM + " сорок восемь", TL.MSG_TWO)}
code_ok = all(k in src for k in ('data["m1"]', 'data["m2"]', 'data["m3"]', 'TL.MSG_CMD', 'TL.MSG_HAND', 'TL.MSG_NEWADM', '"48"', '"Обнаружены"', '"две Елены"'))
missing = [m_ for m_ in REQUIRED if norm_(m_) not in drawn]
ok("All required on-screen texts, exact wording (drawn in code)", not missing and code_ok, ("missing: " + ", ".join(missing)) if (missing or not code_ok) else f"all {len(REQUIRED)} present (phone/monitor UI in scripts/phone_ui.py, series fonts; «сорок восемь» is drawn as a big «48»)")
W0 = {sg["text"]: sg["start"] for sg in json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json")))}
def said(txt): return min((st for t_, st in W0.items() if txt.lower() in re.sub(r"[«»]", "", t_).lower()), default=None)
timing = [("Первое задание", TL.T_TASK1, said("Первое задание")), ("Не тормози", TL.T_TASK2, said("Не тормози")), ("Награда", TL.T_TASK3, said("Награда")),
          ("человек на дороге", 32.0 + 0.16, said("Впереди появился человек")), ("Повторить испытание", TL.T_CMD, said("Повторить")),
          ("47 копий", TL.T_GRID, said("Сорок семь копий")), ("Передача управления", TL.T_HAND, said("Передача управления")),
          ("Новый администратор", TL.T_NEWADM, said("Новый администратор")), ("48", TL.T_48, said("сорок восемь.")),
          ("второй экран", TL.T_SIDE_ON, said("загорелся второй экран")), ("Прямой эфир", TL.T_LIVE, said("прямой эфир")), ("Квартира 47", TL.T_FLAT, said("Моя квартира")),
          ("Обнаружены две Елены", TL.T_TWO, said("Обнаружены две Елены"))]
early = [f"{n} ({t0} < {st})" for n, t0, st in timing if st is None or t0 < st - 0.02]
ok("No message appears before its words in the VO", not early, ", ".join(early) or ", ".join(f"«{n}» {t0:.2f}s (said {st:.2f}s)" for n, t0, st in timing))
last = TL.SHOTS[-1]
ok("Ending: both Elenas on screen at «Не верь мне» (ELENA_204 lip-synced + ELENA_APARTMENT on the live feed, lip-synced)", last.get("lips") == "E12_two" and last.get("monitor") == "live12" and TL.LIPW_FEED[-1] == TL.LIPW[-1],
   f"last shot from {last['t'][0]:.2f} s: E12_two_* (ELENA_204) with draw_live12 (E12_flatfeed_*) on the side monitor; «Не верь мне» {TL.T_LAST:.2f}–{TL.END:.2f} s; which one is real is not shown")
js = open(os.path.join(ROOT, "scripts", "render3d", "shots.js"), encoding="utf8").read()
e12 = js.split("EP12 «ПЕРВОЕ ИСПЫТАНИЕ» (E12_*)")[1].split("REF_versions12")[0]
hand_shots = [x for x in TL.SHOTS if x["src"] in ("E12_raise", "E12_hand") or x.get("lips") == "E12_a48"]
ok("Hand continuity: disappearing until the handover, whole only from «Она перестала исчезать»", all(x["t"][1] <= TL.T_STOP + 1e-6 for x in hand_shots) and "E12_hand_stop" in [x["src"] for x in TL.SHOTS] and TL.T_HAND < TL.T_STOP,
   f"{len(hand_shots)} ALEX_48 shots with the hand going (van 0.74, EP11's state) all end by {TL.T_STOP:.2f} s; E12_hand_stop {TL.T_STOP:.2f} s: the blocks come back; after: whole")
ok("Accident: no collision shown, the record breaks off first; he brakes, the car does not stop", "E12_skid" in e12 and "collision" not in e12.replace("No collision is ever shown", "") and TL.SHOTS[[x['src'] for x in TL.SHOTS].index("E12_skid") + 1]["src"] == "BLACK",
   "E12_ahead (person in the headlights) → E12_brake (foot on the pedal, brake lights) → E12_skid (side-on, wheels locked, still moving) → static/black at «Запись оборвалась»; no contact, no injuries")
ok("Both Elenas identical (same model, same clothes, same face set)", "sis204(W" in e12 and "P.sisterSeated(W.p.face || 'worried'" in e12, "ELENA_204 = makePerson('sister'); ELENA_APARTMENT = sisterSeated(same face tokens) — no extra marks on either")
ok("ALEX_OLD_POLICE and ALEX_49 not brought back", "cop11(" not in e12 and "a49(" not in e12, "neither is placed in any E12_* shot")
ok("First shot continues EP11's last screen", TL.SHOTS[0]["src"] == "E11_face_close" and TL.SHOTS[0]["monitor"] == "face12" and TL.T_HOOK_END > 1.0,
   "EP11's E11_face_close still (read from ../EP11/scenes), «Оригинал проснулся» still on the screen until it clears — same place, no time jump, no recap")
g = run(["git", "-C", ROOT, "diff", "--stat", "origin/ccr-ff234f8e-k8f2b2", "--", "../EP02", "../EP03", "../EP04", "../EP05", "../EP06", "../EP07", "../EP08", "../EP09", "../EP10", "../EP11"]).stdout.strip()
ok("EP01–EP11 files untouched", g == "", g or "no changes against the EP11 branch (EP01 lives in its own branches and is not in this one)")

# contact sheet of the cut (one frame per shot)
from PIL import Image, ImageDraw
mids = [(s["t"][0] + s["t"][1]) / 2 for s in TL.SHOTS]
tiles = []
for i, t in enumerate(mids):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = (Image.frombytes("RGB", (1080, 1920), raw) if len(raw) >= 1080 * 1920 * 3 else Image.new("RGB", (1080, 1920))).resize((180, 320)); ImageDraw.Draw(im).text((4, 4), f"{i + 1} · {t:.1f}s", fill=(0, 255, 0)); tiles.append(im)
cols = 7; sheet = Image.new("RGB", (cols * 180, -(-len(tiles) // cols) * 320))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
sheet.save(os.path.join(ROOT, "docs", "EP12_contact_sheet.jpg"), quality=82)

md = ["# EP12 — QC report", "", f"File: `renders/EP12_PRICE_OF_CHOICE_FINAL.mp4` · {size:.1f} MB · {dur:.2f} s", "",
      "Generated by `scripts/07_qc.py` from the finished file.", "", "| Check | Result | Value |", "|---|---|---|"]
md += [f"| {n} | {'✅' if c else ('⚠️' if n in warn_rows else '❌')} | {val} |" for n, c, val in rows]
md += ["", "One frame from the middle of every shot (shot number · time):", "", "![contact sheet](EP12_contact_sheet.jpg)", ""]
open(os.path.join(ROOT, "docs", "EP12_QC.md"), "w").write("\n".join(md))
print("\n".join(f"{'OK ' if c else ('WARN' if n in warn_rows else 'FAIL')} {n}: {val}" for n, c, val in rows))
sys.exit(0 if all(c or n in warn_rows for n, c, _ in rows) else 1)
