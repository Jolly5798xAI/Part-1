"""Render the EP05 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
EP04 frames that EP05 reuses unchanged are read from ../EP04/scenes (not re-rendered, not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP05 job)
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

# EP05 «КОМНАТА 204» — animations (t 0 -> 1, or a parameter animated with pkey)
anim("E5_key_offer", "E5_key_offer", 16)
anim("E5_reach", "E5_reach", 16)
anim("E5_run_out", "E5_run_out", 20)
anim("E5_corridor_walk", "E5_corridor_walk", 24)
anim("E5_key_lock", "E5_key_lock", 16, pkey="k")
anim("E5_door204_open", "E5_door204_open", 20)
anim("E5_sister_behind", "E5_sister_behind", 16, pkey="k")
# stills
still("E5_alex_react", "E5_alex_react")
still("E5_key_tag", "E5_key_tag")
still("E5_doorway_cop", "E5_doorway")
still("E5_doorway_empty", "E5_doorway", empty=1)
still("E5_floor", "E5_floor")
still("E5_phone_task", "E5_phone_task")
still("E5_alex_key", "E5_alex_key")
still("E5_hall_voice", "E5_hall_voice")
still("E5_view_dark", "E5_view", mode="dark")
still("E5_view_stair", "E5_view", mode="stair")
still("E5_view_corridor", "E5_view", mode="corridor")
still("E5_corridor_far", "E5_corridor_far")
still("E5_door204", "E5_door204")
still("E5_door204_plate", "E5_door204_plate")
still("E5_door_listen", "E5_door_listen")
still("E5_door_gap", "E5_door_gap")
still("E5_alex_red", "E5_alex_red")
still("E5_room_dark", "E5_room")
still("E5_room_lit", "E5_room", on=1)
still("E5_phones_low", "E5_phones_low")
still("E5_phone_hero", "E5_phone_hero")
for m, tok in {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}.items():   # lip-sync set for the sister's line
    still(f"E5_sis_{m}", "E5_sis", face=("worried" + tok))
for ref in ("REF_key204", "REF_sister_mouths"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})
for ref in ("REF_corridor", "REF_room204"):
    jobs.append({"id": ref, "shot": ref, "w": 1080, "h": 1440, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
