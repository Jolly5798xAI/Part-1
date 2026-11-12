"""Render the EP11 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
Frames EP10 reuses unchanged (E9_cop_screen_close, E8_feedc_*, EP01's S05_place_glass / S06_phone_bank) are read from ../EP09, ../EP08, ../EP02 (not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP11 job)
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

# EP11 «НУЛЕВОЙ УРОВЕНЬ» — animations (t 0 -> 1, or a parameter animated with pkey)
anim("E11_run", "E11_run", 18)
anim("E11_grab", "E11_grab", 16)
anim("E11_break", "E11_break", 18, pkey="k")
anim("E11_nod", "E11_nod", 12, pkey="k")
anim("E11_point", "E11_point", 14, pkey="k")
anim("E11_hand", "E11_hand", 14, pkey="k")
anim("E11_cop_dust", "E11_cop_dust", 20, pkey="k")
anim("E11_a49_dust", "E11_a49_dust", 20, pkey="k")
anim("E11_lunge", "E11_lunge", 14, pkey="k")
anim("E11_turn", "E11_turn", 24, pkey="turn", fm=True)
# stills (lip-sync sets: neutral / open / ee / oo picked frame by frame from the VO envelope)
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
def lipface(base, tok): return (base + tok) if base else (tok[1:] or "neutral")
for m, tok in LIPS.items():
    still(f"E11_cop_{m}", "E11_cop", face=lipface("old_worried", tok))            # «Не входи. Там начинается нулевой уровень»
    still(f"E11_sis_{m}", "E11_sis", face=lipface("worried", tok))                # «Алекс. Я не создавала эту игру» … «…версии тебя»
    still(f"E11_sisc_{m}", "E11_sis", face=lipface("worried", tok), close=1)      # the same, closer
    still(f"E11_sisr_{m}", "E11_sis", face=lipface("worried", tok), red=1, close=1)   # «Не трогай его!» «Потому что это не компьютер»
    still(f"E11_a48_{m}", "E11_a48", face=lipface("wide_worried", tok))           # «Но на экране было твоё имя» «Значит, настоящий Алекс…»
    still(f"E11_a48r_{m}", "E11_a48", face=lipface("wide_worried", tok), red=1)   # «Почему?»
still("E11_door204", "E11_door204")
still("E11_room", "E11_room")
still("E11_room_close", "E11_room", close=1)
still("E11_cuffs", "E11_cuffs")
still("E11_mon", "E11_mon")
still("E11_mon_close", "E11_mon", close=1)
still("E11_mon_red", "E11_mon", red=1)
still("E11_mon_red_close", "E11_mon", red=1, close=1)
still("E11_sis_look", "E11_sis", face="worried", head=-0.14)
still("E11_side", "E11_side")
still("E11_side_close", "E11_side", close=1)
still("E11_hosp", "E11_hosp")
still("E11_hosp_close", "E11_hosp", close=1)
still("E11_wide_red", "E11_wide")
still("E11_face", "E11_face")
still("E11_face_close", "E11_face", close=1)
still("E11_sis_fear", "E11_sis_fear")
still("E11_a48_lit", "E11_a48", face="wide_worried_open", lit=1, red=1, noCop=1)
jobs.append({"id": "E11_hosp_feed", "shot": "E11_hosp", "w": 1600, "h": 980, "params": {}})   # the side monitor's recording (16:10)
for ref in ("REF_versions11", "REF_room204_ep11", "REF_hospital"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
