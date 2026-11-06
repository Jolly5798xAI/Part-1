"""EP02 — editing timeline (single source of truth). TEMPLATE: fill in after the new voiceover is approved.

Same format as EP01 (see timeline_ep01_reference.py for a complete, working example).
All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Take them from timeline/transcript_words.json (scripts/01_transcribe.py).

`python3 scripts/timeline_ep02.py` writes timeline/ep02_timeline.json.
"""
import json, os

FPS = 30                 # locked for the series (EP01 final render: 30 fps)
VO_END = None            # <- duration of the new VO, from docs/EP02_VO_REPORT.md (scripts/00_check_vo.py)
CUT_TO_BLACK = None      # <- hard cut, usually VO_END + ~0.1
END = None               # <- CUT_TO_BLACK + ~2.15 s end card («ЦЕНА ВЫБОРА / Продолжение следует»)

# ---------------------------------------------------------------- shots
# dict(t=(start, end), src=<illustration name | "BLACK" | "LIPSYNC">, cam=((cx, cy, zoom), (cx, cy, zoom)),
#      anim=(0.0, 1.0) for animated sources, phone=<PHONE key>, sub="top", fx=[...])
# fx tags understood by 06_render_video.py: leakflicker, shake_hits, vibrate, redglow, glitch, peephole,
#      iris_in, iris_out, tube, freeze, dust, handshake, countdown, endcard  (white/red flashes come from FLASHES)
# EP01 angles from scripts/render3d/shots.js can be reused directly (same apartment / characters).
SHOTS = [
    # dict(t=(0.00, 1.80), src="S20_lock_turns", anim=(1.0, 1.0), cam=((.5, .5, 1.0), (.5, .5, 1.1))),  # e.g. pick up where EP01 ended
]

LIPSYNC = []             # [(time, "neutral" | "ee" | "oo" | "open"), ...] for src="LIPSYNC"

# ---------------------------------------------------------------- phone screen states
# Same UI language as EP01: hidden sender «Номер скрыт», typing dots, bubbles, bank push, timers. Text is never AI-generated.
# Elements: (appear_time, (kind, data)); kinds (phone_ui.py): header, typing, bubble, bubble_small, bubble_red,
#   highlight (str), push ((app, "title: amount")), timer ((start, seconds)), lock_glow, lock_text (str)
ADDRESS = "Алекс. Лесная 12, кв. 47."   # as shown in the rendered EP01 (CHECK: the other EP01 draft used «кв. 37»)
PHONE = {}

HITS = []                # door impacts -> camera shake
FLASHES = []             # [(time, "white" | "red"), ...]
COUNTDOWN = None         # (show_from, start, seconds) for the on-screen timer, or None

# ---------------------------------------------------------------- subtitles
# (start, end, text). Mark *important* words yellow and !danger! words red, 2–5 words per cue.
SUBS = []

# ---------------------------------------------------------------- sound
# (time, kind, gain); kinds = effects/sfx/*.wav names (knock, bang, hit, vibrate, notify, notify_bad, coin, glass, tick,
# tick_hard, tube_on, peep, creak, slap, whisper, alarm, lock_click, lock_turn, lock_clack, boom_tail)
SFX = []
HUM = []                 # fluorescent hum windows (stairwell shots)
MUSIC = [(0, .5)]        # music intensity curve (time, level 0..1)


def check():
    missing = [k for k in ("VO_END", "CUT_TO_BLACK", "END") if globals()[k] is None]
    if missing or not SHOTS or not SUBS:
        raise SystemExit("timeline_ep02 is still a template: set " + ", ".join(missing + [k for k in ("SHOTS", "SUBS") if not globals()[k]]))


def export():
    check()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC,
                phone=PHONE, hits=HITS, flashes=FLASHES, countdown=COUNTDOWN, subtitles=SUBS, sfx=SFX, hum=HUM, music=MUSIC)
    with open(os.path.join(root, "timeline", "ep02_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events; runtime {END:.2f}s")
