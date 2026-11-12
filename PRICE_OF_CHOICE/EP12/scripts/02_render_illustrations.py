"""Render the EP12 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
Frames EP10 reuses unchanged (E9_cop_screen_close, E8_feedc_*, EP01's S05_place_glass / S06_phone_bank) are read from ../EP09, ../EP08, ../EP02 (not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP12 job)
"""
import json, subprocess, sys, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R3D = os.path.join(ROOT, "scripts", "render3d")
OUT = os.path.join(ROOT, "scenes")
src = open(os.path.join(R3D, "shots.js"), encoding="utf8").read()
STILL, ANIM = (1620, 2880), (1296, 2304)
args = sys.argv[1:]
scale = 1.0
if "--scale" in args:
    i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]

jobs = []
def still(jid, shot, **params): jobs.append({"id": jid, "shot": shot, "w": STILL[0], "h": STILL[1], "params": params})
def anim(jid, shot, frames, pkey=None, fm=False, **params):
    j = {"id": jid, "shot": shot, "w": ANIM[0], "h": ANIM[1], "frames": frames, "params": params}
    if pkey: j["pkey"] = pkey
    if fm: j["fm"] = True
    jobs.append(j)

# EP12 «ПЕРВОЕ ИСПЫТАНИЕ» — animations (t 0 -> 1, or a parameter animated with pkey). Rain: `seed` changes per frame via t.
anim("E12_step", "E12_step", 16, pkey="k")
anim("E12_hand", "E12_hand", 14, pkey="k")
anim("E12_hand_stop", "E12_hand_stop", 20, pkey="k")
anim("E12_raise", "E12_raise", 14, pkey="k")
anim("E12_cuffs", "E12_cuffs", 14, pkey="k")
anim("E12_fall", "E12_fall", 16, pkey="k")
anim("E12_turn", "E12_turn", 14, pkey="k")
anim("E12_road", "E12_road", 22, pkey="seed")
anim("E12_wiper", "E12_wiper", 20, pkey="seed")
anim("E12_ahead", "E12_ahead", 18, pkey="d")
anim("E12_brake", "E12_brake", 12, pkey="k")
anim("E12_skid", "E12_skid", 20, pkey="seed")
# stills (lip-sync sets: neutral / open / ee / oo picked frame by frame from the VO envelope)
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
def lipface(base, tok): return (base + tok) if base else (tok[1:] or "neutral")
for m, tok in LIPS.items():
    still(f"E12_a48_{m}", "E12_a48", face=lipface("wide_worried", tok))                       # «Почему?» «Кто отправил…» «Ты запускала…» «Значит…»
    still(f"E12_sist_{m}", "E12_sis", face=lipface("worried", tok), tears=1, close=1, head=0.06)   # «Я пыталась найти версию…»
    still(f"E12_two_{m}", "E12_two", face=lipface("worried", tok))                            # «Не верь мне» (ELENA_204)
    jobs.append({"id": f"E12_flatfeed_{m}", "shot": "E12_flat", "w": 1600, "h": 980, "params": {"face": lipface("worried", tok)}})   # ELENA_APARTMENT on the side monitor
still("E12_sis_down", "E12_sis", face="worried", head=0.26)
still("E12_sis_cry", "E12_sis", face="worried", head=0.22, tears=1)
still("E12_side", "E12_side")
still("E12_side_close", "E12_side", close=1)
still("E12_beside", "E12_beside")
still("E12_flat", "E12_flat", wide=1)
still("E12_flat_close", "E12_flat")
still("E12_rec_wide", "E12_rec_wide")
still("E12_rec_mon", "E12_rec_mon")
still("E12_rec_mon_close", "E12_rec_mon", close=1)
still("E12_cabin_alex", "E12_cabin", who="alex")
still("E12_cabin_sis", "E12_cabin", who="sis")
still("E12_cabin", "E12_cabin")
still("E12_phone", "E12_phone")
still("E12_phone_close", "E12_phone", close=1)
jobs.append({"id": "E12_rec_feed", "shot": "E12_rec_wide", "w": 1600, "h": 980, "params": {}})   # the second recording on the main screen (16:10)
for ref in ("REF_versions12", "REF_car12"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
