"""Render the EP07 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
EP06/EP05 frames that EP07 reuses unchanged are read from ../EP06/scenes, ../EP05/scenes (not re-rendered, not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP07 job)
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
def anim(jid, shot, frames, pkey=None, **params):
    j = {"id": jid, "shot": shot, "w": ANIM[0], "h": ANIM[1], "frames": frames, "params": params}
    if pkey: j["pkey"] = pkey
    jobs.append(j)

# EP07 «ТОТ, КОГО СТЁРЛИ» — animations (t 0 -> 1, or a parameter animated with pkey)
anim("E7_reach", "E7_reach", 14, pkey="k")
jobs.append({"id": "E7_throw", "shot": "E7_throw", "w": ANIM[0], "h": ANIM[1], "frames": 20, "params": {}, "fm": True})   # the phone moves: per-frame screen quads
anim("E7_sis_vanish", "E7_sis_vanish", 18, pkey="k")
anim("E7_punch", "E7_punch", 16)
anim("E7_step_back", "E7_step_back", 16)
anim("E7_wrist", "E7_wrist", 16, pkey="num")
anim("E7_wrist_rub", "E7_wrist_rub", 16, pkey="rub")
anim("E7_wrist_clear", "E7_wrist_clear", 16, pkey="clear")
anim("E7_shatter", "E7_shatter", 18, pkey="k")
anim("E7_press", "E7_press", 12, pkey="press")
anim("E7_lean", "E7_feed", 14, pkey="lean", face="worried")
anim("E7_hand_vanish", "E7_hand_vanish", 16, pkey="k")
# stills
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
for m, tok in LIPS.items():
    still(f"E7_sisc_{m}", "E7_sisc", face="cold" + tok)                      # «Выбирай себя, Алекс. Ты всё равно вернёшься»
    still(f"E7_oldc_{m}", "E7_oldc", face="old_worried" + tok)               # «Она уже стёрла тебя. Сорок шесть раз»
    still(f"E7_alexd_{m}", "E7_alexd", face="wide_worried" + tok, crack=1, back=1)   # «Тогда почему я ещё здесь?»
    still(f"E7_feedm_{m}", "E7_feed", face="worried" + tok, lean=1)  # «Алекс… если ты меня слышишь, найди настоящего себя»
still("E7_phone_pov", "E7_phone_pov")
still("E7_floor_phone", "E7_floor_phone")
still("E7_room_dark", "E7_room_dark")
still("E7_mirror_front", "E7_mirror_front")
still("E7_alex_dark", "E7_alexd", face="wide_worried", crack=0, back=1)
still("E7_old_point", "E7_oldc", point=1)
still("E7_wrist_wires", "E7_wrist_clear", clear=1, close=1)
still("E7_realize", "E7_realize")
still("E7_wide_copy", "E7_wide_copy")
still("E7_reveal", "E7_reveal")
still("E7_monitor_sis", "E7_monitor_sis")
still("E7_feed", "E7_feed", face="cold")
still("E7_alex_shout", "E7_alexd", face="wide_worried_open", shatter=1, back=1)
still("E7_wall", "E7_wall")
still("E7_wall_red", "E7_wall", red=1)
still("E7_mon", "E7_mon")
still("E7_mon_red", "E7_mon", red=1)
for ref in ("REF_monitor_room", "REF_operator_room", "REF_arm48"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
