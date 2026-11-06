"""Render every illustration of EP02 from the shared 3D world (three.js + headless Chromium).
Writes illustrations/<SHOT>.png (stills, 1620x2880) and illustrations/<SHOT>/fNNNN.png (animated shots).
usage: python3 scripts/02_render_illustrations.py [SHOT_ID | PREFIX* ...]   (default: every shot in the library)"""
import json, subprocess, sys, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R3D = os.path.join(ROOT, "scripts", "render3d")
src = open(os.path.join(R3D, "shots.js"), encoding="utf8").read()
shots = re.findall(r"^\s{4}(\w+): \{ desc: (.*)$", src, re.M)
STILL, ANIM = (1620, 2880), (1296, 2304)
jobs = []
for sid, rest in shots:
    m = re.search(r"frames: (\d+)", rest); fr = int(m.group(1)) if m else 1
    w, h = ANIM if fr > 1 else STILL
    if sid.startswith("REF_"): w, h = 1080, 1920
    m = re.search(r"size: \[(\d+), (\d+)\]", rest)
    if m: w, h = int(m.group(1)), int(m.group(2))
    jobs.append({"id": sid, "shot": sid, "w": w, "h": h, "frames": fr})
# lip shapes of the double for the silent «Не верь телефону» (EP01)
for v in ["neutral", "ee", "oo", "open"]:
    jobs.append({"id": f"S16_double_face_{v}", "shot": "S16_double_face", "w": 1620, "h": 2880, "params": {"face": v}})
# EP02 variants of the same shot code
VARIANTS = [("E2_alex_brace_leg", "E2_alex_brace", {"leg": 1}), ("E2_entry_wide_shadows", "E2_entry_wide", {"shadows": 1}),
            ("E2_peep_phone_lit", "E2_peep_phone", {"lit": 1})]
for v in ["neutral", "ee", "oo", "open"]:  # lip shapes: the double speaks through the gap / whispers at the ear
    VARIANTS += [(f"E2_gap_double_{v}", "E2_gap", {"dbl": 1, "face": v}), (f"E2_double_ear_{v}", "E2_double_ear", {"face": v})]
for jid, shot, params in VARIANTS:
    jobs.append({"id": jid, "shot": shot, "w": STILL[0], "h": STILL[1], "params": params})
only = sys.argv[1:]
if only: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in only)]
os.makedirs(os.path.join(ROOT, "illustrations"), exist_ok=True)
jf = os.path.join(ROOT, "illustrations", "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), os.path.join(ROOT, "illustrations"), jf], check=True)
