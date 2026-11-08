"""Render the EP06 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
EP05 frames that EP06 reuses unchanged are read from ../EP05/scenes (not re-rendered, not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP06 job)
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

# EP06 «ПЕРВАЯ ПОПЫТКА» — animations (t 0 -> 1, or a parameter animated with pkey)
anim("E6_turn", "E6_turn", 16)
anim("E6_step", "E6_step", 20)
anim("E6_grab", "E6_grab", 12, pkey="k")
anim("E6_run", "E6_run", 20)
anim("E6_mirror_form", "E6_exit", 16, pkey="k", mirror=1)
anim("E6_palm", "E6_old", 14, pkey="palm", face="old_worried")
anim("E6_turn_back", "E6_turn_back", 16)
# stills
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
for m, tok in LIPS.items():
    still(f"E6_sisf_{m}", "E6_sisf", face="worried" + tok)       # the sister's lines («Не подходи…», «Твоей», «Ты снова всё забудешь»)
    still(f"E6_rec_{m}", "E6_rec", face="worried" + tok)         # Alex on the recording
    still(f"E6_old_{m}", "E6_old", face="old_worried" + tok)     # the old Alex in the mirror («Не верь ей…»)
still("E6_point", "E6_point")
still("E6_alex", "E6_alex")
still("E6_alex_red", "E6_alex", red=1)
still("E6_show_wide", "E6_show_wide")
still("E6_show", "E6_show")
still("E6_show_cold", "E6_show", red=1, face="cold")
still("E6_phones_red", "E6_phones_low", red=1)
still("E6_room_red", "E6_room", red=1)
still("E6_exit_wall", "E6_exit")
still("E6_mirror_young", "E6_mirror")
still("E6_mirror_old", "E6_mirror", old=1)
still("E6_sis_cold", "E6_sis_cold")
still("E6_sis_phone", "E6_sis_cold", phone=1)
jobs.append({"id": "E6_alex_portrait", "shot": "E6_alex_portrait", "w": 1000, "h": 1250, "params": {}})
for ref in ("REF_old_alex", "REF_sister_cold"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})
jobs.append({"id": "REF_mirror204", "shot": "REF_mirror204", "w": 1080, "h": 1440, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
