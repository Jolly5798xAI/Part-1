"""Render the EP04 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
EP03 frames that EP04 reuses unchanged are read from ../EP03/scenes (not re-rendered, not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP04 job)
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

# animations (t 0 -> 1, or a parameter animated with pkey)
anim("E4_approach", "E4_approach", 30)
anim("E4_scars", "E4_scars", 20, pkey="k")
anim("E4_tape_off", "E4_tape_off", 16)
anim("E4_step_back", "E4_step_back", 20)
anim("E4_phone_throw", "E4_phone_throw", 16)
anim("E4_lean", "E4_lean", 16)
anim("E4_doorway_steps", "E4_doorway_steps", 24)
anim("E4_boots", "E4_boots", 24)
anim("E4_grab", "E4_grab", 12, pkey="k")
anim("E4_alex_turn", "E4_alex_turn", 16)
anim("E4_cop_raise", "E4_cop_raise", 16)
# stills
still("E4_scar_dbl", "E4_scars", k=0)
MOUTHS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
for m, tok in MOUTHS.items():                       # lip-sync sets (shape picked by the editor from the VO envelope)
    still(f"E4_dbl_talk_{m}", "E4_dbl", face="worried_redmark_tears" + tok)
    still(f"E4_dbl_pale_{m}", "E4_dbl", face="worried_redmark_pale" + tok)
    still(f"E4_alex_talk_{m}", "E4_alex", face="worried" + tok)
still("E4_dbl_gasp", "E4_dbl", face="wide_worried_redmark_tears_open")
still("E4_dbl_eyes", "E4_dbl", face="worried_redmark_tears", cam="eyes")
still("E4_dbl_pale_wide", "E4_dbl", face="wide_worried_redmark_pale")
still("E4_dbl_look", "E4_dbl", face="worried_redmark_pale_side", head=0.12)
still("E4_alex_wide", "E4_alex", face="wide_worried")
still("E4_pov_chair", "E4_pov_chair")
still("E4_pov_chair_close", "E4_pov_chair", center=1)
still("E4_phone_floor", "E4_phone_floor")
still("E4_mirror_far", "E4_mirror_far")
still("E4_mirror_close", "E4_mirror_close")
still("E4_room204", "E4_room204")
still("E4_room204_wide", "E4_room204", wide=1)
still("E4_cop_doorway", "E4_cop_doorway")
still("E4_cop_mask", "E4_cop_doorway", cam="mask")
still("E4_cop_phone", "E4_cop_phone")
still("E4_cop_phone_close", "E4_cop_phone", close=1)
still("E4_sister_photo", "E4_sister_photo")
for ref in ("REF_sister", "REF_masked_cop"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
