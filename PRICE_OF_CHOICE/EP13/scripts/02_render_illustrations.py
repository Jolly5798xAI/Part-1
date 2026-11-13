"""Render the EP13 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
Frames EP10 reuses unchanged (E9_cop_screen_close, E8_feedc_*, EP01's S05_place_glass / S06_phone_bank) are read from ../EP09, ../EP08, ../EP02 (not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP13 job)
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

# EP13 «ПОСЛЕДНЯЯ КОПИЯ» — animations (t 0 -> 1, or a parameter animated with pkey). Rain: `seed` changes per frame via t.
anim("E13_look", "E13_look", 18, pkey="k")
anim("E13_raise1", "E13_raise1", 16, pkey="k")
anim("E13_back", "E13_back", 14, pkey="k")
anim("E13_grab", "E13_grab", 14, pkey="k")
anim("E13_reach", "E13_reach", 14, pkey="k")
anim("E13_pull", "E13_reach", 14, pkey="k", pull=1, red=1)
anim("E13_point", "E13_point", 16, pkey="k")
anim("E13_arm", "E13_arm", 20, pkey="num")          # f0000 = num 0 ... f0019 = num 1 (the editor plays it backwards: the number vanishes)
anim("E13_road", "E13_road", 20, pkey="seed")
anim("E13_reveal", "E13_reveal", 20, pkey="k")
# stills (lip-sync sets: neutral / open / ee / oo picked frame by frame from the VO envelope)
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
def lipface(base, tok): return (base + tok) if base else (tok[1:] or "neutral")
for m, tok in LIPS.items():
    still(f"E13_a48_{m}", "E13_a48", face=lipface("wide_worried", tok))               # «Которая из вас настоящая?» «Ты сам устроил аварию?»
    still(f"E13_a48r_{m}", "E13_a48", face=lipface("wide_worried", tok), red=1)       # «А ты кто?» «Нет. Я не буду выбирать» «Какой?»
    still(f"E13_e1_{m}", "E13_e1", face=lipface("worried", tok))                      # «Она врёт…» «Он проверял…» «Та, которая…»
    still(f"E13_e1r_{m}", "E13_e1", face=lipface("worried", tok), red=1)              # «Алекс. Есть третий вариант»
    jobs.append({"id": f"E13_feed_{m}", "shot": "E13_flat", "w": 1600, "h": 980, "params": {"face": lipface("worried", tok)}})              # ELENA_0, hands on the table
    jobs.append({"id": f"E13_feedz_{m}", "shot": "E13_flat", "w": 1600, "h": 980, "params": {"face": lipface("worried", tok), "raise": 1, "zero": 1}})   # ELENA_0 shows the «0»
for z in (0.0, 0.5):
    jobs.append({"id": f"E13_feedr{int(z * 10)}", "shot": "E13_flat", "w": 1600, "h": 980, "params": {"face": "worried", "raise": 0.5 + z, "zero": 0}})   # the hand comes up
jobs.append({"id": "E13_recfeed", "shot": "E13_road", "w": 1600, "h": 980, "params": {"seed": 0.2}})   # the hidden recording on the screen (16:10)
jobs.append({"id": "E13_selfcam", "shot": "E13_selfcam", "w": 1600, "h": 980, "params": {}})
still("E13_e1r_down", "E13_e1", face="worried_down", head=0.22, red=1)
still("E13_wrist1", "E13_wrist1")
still("E13_flat0", "E13_flat", face="worried", zero=1, zoom=1, **{"raise": 1})        # full-frame live feed: the red «0» on ELENA_0's wrist
still("E13_side", "E13_side")
still("E13_side_ots", "E13_side", ots=1)
still("E13_mon", "E13_mon")
still("E13_mon_close", "E13_mon", close=1)
still("E13_monr", "E13_mon", red=1)
still("E13_monr_close", "E13_mon", close=1, red=1)
still("E13_table", "E13_table")
still("E13_tabler", "E13_table", red=1)
still("E13_all", "E13_all", red=1)
still("E13_dash", "E13_dash")
still("E13_orig", "E13_orig")
still("E13_orig_smirk", "E13_orig", face="smirk")
still("E13_phone2", "E13_phone2")
still("E13_phone2_close", "E13_phone2", close=1)
for ref in ("REF_versions13", "REF_car13"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
