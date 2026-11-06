"""Render every illustration of EP01 from the shared 3D world (three.js + headless Chromium).
Writes illustrations/<SHOT>.png (stills, 1620x2880) and illustrations/<SHOT>/fNNNN.png (animated shots).
usage: python3 scripts/02_render_illustrations.py [SHOT_ID ...]"""
import json, subprocess, sys, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R3D = os.path.join(ROOT, "scripts", "render3d")
src = open(os.path.join(R3D, "shots.js"), encoding="utf8").read()
shots = re.findall(r"^\s{4}(\w+): \{ desc: (?:.*?frames: (\d+))?.*$", src, re.M)
STILL, ANIM = (1620, 2880), (1296, 2304)
jobs = []
for sid, fr in shots:
    fr = int(fr) if fr else 1
    w, h = ANIM if fr > 1 else STILL
    if sid.startswith("REF_"): w, h = 1080, 1920
    jobs.append({"id": sid, "shot": sid, "w": w, "h": h, "frames": fr})
# lip shapes of the double for the silent «Не верь телефону»
for v in ["neutral", "ee", "oo", "open"]:
    jobs.append({"id": f"S16_double_face_{v}", "shot": "S16_double_face", "w": 1620, "h": 2880, "params": {"face": v}})
only = sys.argv[1:]
if only: jobs = [j for j in jobs if any(j["id"].startswith(o) for o in only)]
os.makedirs(os.path.join(ROOT, "illustrations"), exist_ok=True)
jf = os.path.join(ROOT, "illustrations", "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), os.path.join(ROOT, "illustrations"), jf], check=True)
