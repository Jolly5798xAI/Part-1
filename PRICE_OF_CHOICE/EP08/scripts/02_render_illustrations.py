"""Render the EP08 frames from the shared 3D world (three.js + headless Chromium).
Writes scenes/<ID>.png (stills, 1620x2880) and scenes/<ID>/fNNNN.png (animated shots) + scenes/meta.json.
EP07 frames that EP08 reuses unchanged (E7_mon, E7_feedm_*) are read from ../EP07/scenes (not re-rendered, not copied).

usage: python3 scripts/02_render_illustrations.py [ID | PREFIX* ...] [--scale 0.25]   (default: every EP08 job)
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

# EP08 «ЗАВТРАШНИЙ ДЕНЬ» — animations (t 0 -> 1, or a parameter animated with pkey)
anim("E8_hand", "E8_hand", 14, pkey="k")
anim("E8_feed_shake", "E8_feed_shake", 16)
anim("E8_rec_two", "E8_rec", 16, pkey="k", view="two")
anim("E8_rec_plead", "E8_rec", 14, pkey="k", view="plead")
anim("E8_punch_mon", "E8_punch_mon", 16)
anim("E8_quake", "E8_quake", 18, pkey="k")
anim("E8_run", "E8_run", 18)
anim("E8_portal", "E8_portal", 18, pkey="k")
anim("E8_door", "E8_door", 14, pkey="ajar")
anim("E8_step_in", "E8_step_in", 18)
anim("E8_flat_in", "E8_flat_in", 22)
anim("E8_glass", "E8_glass", 18, pkey="k")
anim("E8_turn", "E8_turn", 18)
anim("E8_hand_flat", "E8_hand_flat", 14, pkey="k")
anim("E8_lock", "E8_lock", 30, pkey="turn")
# stills
LIPS = {"neutral": "", "open": "_open", "ee": "_ee", "oo": "_oo"}
for m, tok in LIPS.items():
    still(f"E8_alexm_{m}", "E8_alexm", face="wide_worried" + tok)                 # «Что будет завтра?» / «Но я же Алекс»
    still(f"E8_alexc_{m}", "E8_alexm", face="wide_worried" + tok, close=1)        # «Это неправда»
    still(f"E8_feedc_{m}", "E7_feed", face="cold" + tok, close=1)                  # «Ты убьёшь…» / «Ты его последняя копия» / «Тогда измени будущее»
    still(f"E8_orig_{m}", "E8_orig", face="neutral" + tok)                         # «Ты пришёл раньше»
    still(f"E8_origp_{m}", "E8_orig", face="neutral" + tok, point=1)               # «Прячься. Сейчас появится первый»
still("E8_feed", "E7_feed", face="cold", close=1)
still("E8_feed_shout", "E7_feed", face="worried_open", lean=1)
still("E8_mon_feed", "E8_mon", feed="sis")
still("E8_mon_rec", "E8_mon", feed="rec", rec="wide")
still("E8_mon_crack", "E8_mon", feed="rec", rec="plead", crack=1)
still("E8_mon_del", "E8_mon", feed="ui", crack=1, red=1, k=0.6)
still("E8_wall", "E8_wall", k=0.55)
still("E8_rec_flat", "E8_rec", view="wide", empty=1)
still("E8_rec_door", "E8_rec", view="door")
still("E8_rec_knife", "E8_rec", view="knife")
still("E8_phone", "E8_phone")
still("E8_phone_close", "E8_phone", close=1)
still("E8_alex_hall", "E8_alex_hall")
still("E8_kitchen", "E8_kitchen")
still("E8_orig_look", "E8_orig", face="neutral_down", down=1)
still("E8_orig_point", "E8_orig_point")
still("E8_hide", "E8_hide")
for ref in ("REF_kitchen", "REF_versions"):
    jobs.append({"id": ref, "shot": ref, "w": 1600, "h": 1100, "params": {}})

if args: jobs = [j for j in jobs if any(j["id"] == o or (o.endswith("*") and j["id"].startswith(o[:-1])) for o in args)]
for j in jobs:
    j["w"] = int(j["w"] * scale) // 2 * 2; j["h"] = int(j["h"] * scale) // 2 * 2
os.makedirs(OUT, exist_ok=True)
jf = os.path.join(OUT, "_jobs.json"); json.dump(jobs, open(jf, "w"), indent=1)
subprocess.run(["node", os.path.join(R3D, "render.js"), OUT, jf], check=True)
