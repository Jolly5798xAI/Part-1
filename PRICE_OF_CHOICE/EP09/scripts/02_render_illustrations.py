"""Render the EP09 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
EP07/EP08 frames that EP09 reuses unchanged (E8_feedc_*, E8_rec_knife) are read from ../EP08/scenes (not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP09 job)
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

# EP09 «ПЕРВЫЙ АЛЕКС» — animations (t 0 -> 1, or a parameter animated with pkey); fm=True stores the phone quad per frame
anim("E9_lock", "E8_lock", 30, pkey="turn")                 # EP08's lock close-up, re-rendered (the same shot, the same lock)
anim("E9_grab", "E9_grab", 18)
anim("E9_hide", "E9_hide", 18)
anim("E9_enter", "E9_enter", 22)
anim("E9_wrist49", "E9_wrist49", 16, pkey="g")
anim("E9_wrist48", "E9_wrist48", 14, pkey="k")
anim("E9_turn49", "E9_turn49", 18)
anim("E9_step_back", "E9_step_back", 14)
anim("E9_knife_grab", "E9_knife_grab", 16)
anim("E9_zero_knife", "E9_zero_knife", 18, pkey="k")
anim("E9_strike", "E9_strike", 22)
anim("E9_wrist0", "E9_wrist0", 16, pkey="g")
anim("E9_door_open", "E9_door_open", 18)
anim("E9_cop_phone", "E9_cop_phone", 16, pkey="lift", fm=True)
# stills
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
def lipface(base, tok): return (base + tok) if base else (tok[1:] or "neutral")
for m, tok in LIPS.items():
    still(f"E9_zero_{m}", "E9_zero", face=lipface("worried", tok))                  # «Прячься! Он не должен нас увидеть.»
    still(f"E9_a48w_{m}", "E9_a48w", face=lipface("wide_worried", tok))             # «Почему он следующий?»
    still(f"E9_zerow_{m}", "E9_zero", face=lipface("", tok), across=1)              # «…потому что тебя уже списали.»
    still(f"E9_zero0_{m}", "E9_zero_close", face=lipface("pale", tok), red=1)   # «Теперь ты понимаешь…»
still("E9_a48_hall", "E9_a48_hall")
still("E9_glass49", "E9_glass49")
still("E9_a48_peek", "E9_a48w", face="wide_worried", hall=1)
still("E9_a48_answer", "E9_a48w", face="wide_worried_open")
still("E9_two_wall", "E9_two_wall")
still("E9_vibrate", "E9_vibrate")
still("E9_phone49", "E9_phone49")
still("E9_knife_fist", "E9_knife_fist")
still("E9_phone_floor", "E9_phone_floor")
still("E9_three", "E9_three")
still("E9_zero_freeze", "E9_zero_close", face="neutral")
still("E9_zero_changed", "E9_zero_close", face="wide_pale")
still("E9_zero_look", "E9_zero_close", face="pale", red=1)
still("E9_cop_sil", "E9_cop_sil")
still("E9_mask", "E9_mask")
still("E9_cop_face", "E9_cop_face")
still("E9_cop_screen", "E9_cop_screen")
still("E9_cop_screen_close", "E9_cop_screen", close=1)
for ref in ("REF_versions9", "REF_wrists9"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
