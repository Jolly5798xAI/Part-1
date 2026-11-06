"""Render the EP03 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
EP01/EP02 frames that EP03 reuses unchanged are read from ../EP02/illustrations (not re-rendered, not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every E3_* job)
"""
import json, subprocess, sys, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R3D = os.path.join(ROOT, "scripts", "render3d")
OUT = os.path.join(ROOT, "scenes")
src = open(os.path.join(R3D, "shots.js"), encoding="utf8").read()
shots = re.findall(r"^\s{4}(E3_\w+): \{ desc: (.*)$", src, re.M)
STILL, ANIM = (1620, 2880), (1296, 2304)
args = sys.argv[1:]
scale = 1.0
if "--scale" in args:
    i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]

jobs = []
for sid, rest in shots:
    m = re.search(r"frames: (\d+)", rest); fr = int(m.group(1)) if m else 1
    w, h = ANIM if fr > 1 else STILL
    jobs.append({"id": sid, "shot": sid, "w": w, "h": h, "frames": fr})

# EP03 variants of the same shot code (parameters are read in shots.js as W.p.*)
VARIANTS = [
    ("E3_hall_empty_prints", "E3_hall_empty", {"prints": 1}),
    ("E3_pov_room_close", "E3_pov_room", {"center": 1}),
    ("E3_mirror_wide_dbl", "E3_mirror_wide", {"dbl": 1}),
    ("E3_mirror_dbl", "E3_mirror", {"dbl": 1}),
    ("E3_mirror_dbl_close", "E3_mirror", {"dbl": 1, "fov": 26}),
    ("E3_behind_empty_m", "E3_behind_empty", {"m": 1}),
    ("E3_prints_bedroom_leak", "E3_prints_bedroom", {"leak": 1}),
    ("E3_beddoor_close_dim", "E3_beddoor_close", {"leak": 0.25}),
    ("E3_tied_face_eyes", "E3_tied_face", {"cam": "eyes", "face": "tape_worried_wide"}),
    ("E3_tied_face_tears", "E3_tied_face", {"face": "tape_worried_tears"}),
    ("E3_tied_face_tears_eyes", "E3_tied_face", {"cam": "eyes", "face": "tape_worried_tears"}),
]
# the double's gestures in the mirror, as short animations (k = 0 -> 1)
for pose in ("shh", "point"):
    jobs.append({"id": f"E3_mirror_{pose}", "shot": "E3_mirror", "w": ANIM[0], "h": ANIM[1], "frames": 16,
                 "params": {"dbl": 1, "fov": 26, "pose": pose}, "pkey": "k"})
# head shaking: three head angles, alternated by the editor like lip shapes
for name, ang in (("l", 0.42), ("c", 0.0), ("r", -0.42)):
    VARIANTS.append((f"E3_tied_head_{name}", "E3_tied_face", {"face": "tape_worried_wide", "head": ang}))
for jid, shot, params in VARIANTS:
    jobs.append({"id": jid, "shot": shot, "w": STILL[0], "h": STILL[1], "params": params})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
