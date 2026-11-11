"""Render the EP10 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
Frames EP10 reuses unchanged (E9_cop_screen_close, E8_feedc_*, EP01's S05_place_glass / S06_phone_bank) are read from ../EP09, ../EP08, ../EP02 (not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP10 job)
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

# EP10 «СОЗДАТЕЛЬ» — animations (t 0 -> 1, or a parameter animated with pkey)
anim("E10_cop_aim", "E10_cop_aim", 16)
anim("E10_zero_head", "E10_zero_head", 14, pkey="k")
anim("E10_hand48", "E10_hand48", 14, pkey="k")
anim("E10_cop_give", "E10_cop_give", 16)
anim("E10_press", "E10_press", 14, pkey="k")
anim("E10_zero_turn", "E10_zero_turn", 14, pkey="k")
anim("E10_zero_vanish", "E10_zero_vanish", 20, pkey="k")
anim("E10_cop_kneel", "E10_cop_kneel", 16, pkey="kneel")
anim("E10_door204", "E10_door204", 20, pkey="d")
# stills (lip-sync sets: neutral / open / ee / oo picked frame by frame from the VO envelope)
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
def lipface(base, tok): return (base + tok) if base else (tok[1:] or "neutral")
for m, tok in LIPS.items():
    still(f"E10_a48_{m}", "E10_a48", face=lipface("wide_worried", tok))           # «Почему именно он?» «Что это такое?» …
    still(f"E10_cop_{m}", "E10_cop", face=lipface("old", tok))                    # «Потому что он создал нас.» «Те, кто не прошёл испытания»
    still(f"E10_copf_{m}", "E10_cop", face=lipface("old_worried_wide", tok), copB=1)   # «Этого не должно быть!»
    still(f"E10_zero_{m}", "E10_zero", face=lipface("pale", tok))                 # «Я создал игру…» «Мы проверяли…» «Теперь знаешь»
    still(f"E10_sis_{m}", "E10_sis", face=lipface("cold", tok))                   # «Поздравляю, Алекс! Ты наконец дошёл до последнего уровня.»
still("E10_zero_still", "E10_zero", face="neutral", red=0.9)
still("E10_zero_say", "E10_zero", face="pale", red=0.55, copB=1, fov=30)
still("E10_a48_red", "E10_a48", face="wide_worried_open", copB=1, red=1)
still("E10_a48_look", "E10_a48", face="wide_worried", copB=1)
still("E10_phones", "E10_phones")
still("E10_phones_b", "E10_phones", copB=1)
still("E10_pov_zero", "E10_pov", look="zero")
still("E10_pov_choice", "E10_pov", look="copB", close=1)
still("E10_pov_close", "E10_pov", look="zero", close=1)
still("E10_pov_end", "E10_pov", look="copB", close=1, after=1)
still("E10_a48_end", "E10_a48", face="wide_worried_open", after=1)
still("E10_r204_wide", "E10_r204_wide")
still("E10_r204_mon", "E10_r204_mon")
still("E10_r204_mon_close", "E10_r204_mon", close=1)
for ref in ("REF_versions10", "REF_room204_desk"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
