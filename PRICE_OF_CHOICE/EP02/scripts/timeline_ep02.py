"""EP02 — editing timeline (single source of truth). Same format as EP01 (timeline_ep01_reference.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper), word ends corrected with silencedetect
(docs/EP02_VO_REPORT.md). Verified text: docs/EP02_transcript.txt.

EP02 opens on EP01's last frame: S20_lock_turns, last frame, camera zoom 1.12, countdown 00:05.

`python3 scripts/timeline_ep02.py` writes timeline/ep02_timeline.json.
"""
import json, os

FPS = 30                 # locked for the series
VO_END = 95.16
CUT_TO_BLACK = 95.30
END = 97.50

# ---------------------------------------------------------------- shots
# src: still name (illustrations/<src>.png), anim folder (illustrations/<src>/), "LIPSYNC" (+ lips=<base>) or "BLACK"
# cam: (cx, cy, zoom) start -> end, in source-normalised coords (0..1), zoom 1 = full frame
SHOTS = [
    # --- 1. THE LOCK (continues EP01's last frame)
    dict(t=(0.00, 2.79), src="S20_lock_turns", anim=(1.0, 1.0), cam=((.5, .5, 1.12), (.5, .5, 1.22)), fx=["countdown", "shake_hits"]),
    # --- 2. THE STRUGGLE
    dict(t=(2.79, 5.10), src="E2_door_gap", anim=(0.0, 0.3), cam=((.5, .5, 1.0), (.48, .5, 1.06)), fx=["shake_hits"]),
    dict(t=(5.10, 8.40), src="E2_door_gap", anim=(0.3, 1.0), anim_start=5.10, anim_dur=2.7, cam=((.48, .5, 1.06), (.4, .5, 1.16)), fx=["shake_hits", "leakflicker"]),
    dict(t=(8.40, 9.30), src="E2_alex_brace", cam=((.5, .5, 1.0), (.5, .48, 1.05)), fx=["leakflicker"]),
    # --- 3. «НЕ СОПРОТИВЛЯЙСЯ»
    dict(t=(9.30, 11.55), src="S12_phone_rack", cam=((.5, .5, 1.0), (.55, .45, 1.22)), phone="rack_on", fx=["vibrate"]),
    dict(t=(11.55, 14.60), src="S12_phone_rack", cam=((.51, .49, 1.9), (.51, .49, 2.15)), phone="rack_msg"),
    dict(t=(14.60, 16.30), src="E2_alex_face", cam=((.5, .45, 1.0), (.5, .45, 1.08)), fx=["redglow"]),
    dict(t=(16.30, 18.30), src="E2_alex_brace_leg", cam=((.5, .5, 1.05), (.47, .5, 1.12)), fx=["shake_hits"]),
    dict(t=(18.30, 20.30), src="E2_gap", cam=((.5, .5, 1.0), (.55, .5, 1.12)), fx=["leakflicker"]),
    # --- 4. THE DOUBLE'S VOICE
    dict(t=(20.30, 23.55), src="LIPSYNC", lips="E2_gap_double", sub="top", cam=((.62, .45, 1.15), (.64, .42, 1.25))),
    dict(t=(23.55, 25.90), src="E2_gap_double_neutral", cam=((.64, .42, 1.25), (.7, .36, 1.75))),
    # --- 5. WATER / THE EMPTY GLASS
    dict(t=(25.90, 27.90), src="S13_door_bang", cam=((.5, .5, 1.1), (.5, .5, 1.14)), fx=["shake_hits", "freeze"]),
    dict(t=(27.90, 30.75), src="E2_water", anim=(0.0, 1.0), cam=((.5, .55, 1.0), (.5, .6, 1.12))),
    dict(t=(30.75, 33.70), src="E2_glass_empty", cam=((.5, .55, 1.0), (.47, .62, 1.3))),
    dict(t=(33.70, 36.90), src="S05_place_glass", cam=((.5, .45, 1.1), (.5, .55, 1.25)), fx=["freeze", "memory"]),
    # --- 6. TASK FAILED / BANK
    dict(t=(36.90, 39.30), src="S12_phone_rack", cam=((.5, .5, 1.0), (.55, .42, 1.25)), phone="fail_on", fx=["vibrate", "redglow"]),
    dict(t=(39.30, 42.95), src="S12_phone_rack", cam=((.51, .49, 1.9), (.51, .49, 2.2)), phone="fail", fx=["redglow", "glitch"]),
    dict(t=(42.95, 47.00), src="S06_phone_bank", cam=((.5, .5, 1.1), (.48, .47, 1.42)), phone="bank"),
    # --- 7. THE CHOICE
    dict(t=(47.00, 49.20), src="S03_phone_msg1", cam=((.5, .5, 1.0), (.5, .52, 1.2)), phone="chat3_pre", fx=["vibrate"]),
    dict(t=(49.20, 53.20), src="S03_phone_msg1", cam=((.47, .5, 1.5), (.47, .5, 1.68)), phone="chat3"),
    dict(t=(53.20, 55.00), src="S19_phone_final", cam=((.5, .62, 1.25), (.5, .62, 1.4)), phone="choice"),
    dict(t=(55.00, 56.78), src="S19_phone_final", sub="bottom", cam=((.36, .6, 2.0), (.36, .6, 2.25)), phone="choice"),
    dict(t=(56.78, 59.20), src="S19_phone_final", sub="bottom", cam=((.62, .58, 2.0), (.62, .58, 2.3)), phone="choice"),
    dict(t=(59.20, 61.30), src="S04_alex_phone_face", cam=((.5, .4, 1.25), (.5, .42, 1.1))),
    dict(t=(61.30, 64.10), src="S19_phone_final", sub="bottom", cam=((.5, .8, 1.6), (.5, .8, 1.8)), phone="choice", fx=["handshake"]),
    dict(t=(64.10, 66.25), src="S19_phone_final", cam=((.38, .62, 1.9), (.36, .62, 2.2)), phone="choice", fx=["handshake"]),
    # --- 8. THE SCREAM / SILENCE / KNOCKS
    dict(t=(66.25, 68.95), src="E2_entry_wide_shadows", cam=((.5, .5, 1.25), (.5, .5, 1.34)), fx=["shake_hits"]),
    dict(t=(68.95, 71.60), src="E2_entry_wide", cam=((.5, .5, 1.34), (.5, .5, 1.4))),
    dict(t=(71.60, 74.90), src="E2_door_low", cam=((.5, .45, 1.0), (.5, .42, 1.18)), fx=["leakflicker"]),
    # --- 9. THE PEEPHOLE AGAIN
    dict(t=(74.90, 76.60), src="S08_peephole_lean", cam=((.5, .45, 1.0), (.42, .4, 1.4)), fx=["iris_out"]),
    dict(t=(76.60, 78.40), src="E2_peep_empty", cam=((.5, .5, 1.2), (.5, .5, 1.28)), fx=["peephole", "iris_in", "tube"]),
    dict(t=(78.40, 82.00), src="E2_peep_phone", cam=((.5, .5, 1.0), (.52, .52, 1.35)), fx=["peephole", "tube"]),
    dict(t=(82.00, 83.70), src="E2_peep_phone_lit", cam=((.52, .52, 1.35), (.52, .52, 1.5)), phone="floor", fx=["peephole", "tube"]),
    dict(t=(83.70, 86.50), src="E2_peep_phone_lit", cam=((.52, .52, 2.0), (.52, .52, 2.4)), phone="floor", fx=["peephole", "tube"]),
    dict(t=(86.50, 89.45), src="E2_photo_back", cam=((.5, .5, 1.0), (.5, .48, 1.1)), fx=["photo"]),
    # --- 10. «ТЫ ВЫБРАЛ НЕ ТОГО»
    dict(t=(89.45, 92.70), src="E2_double_behind", cam=((.5, .5, 1.0), (.47, .45, 1.15)), fx=["leakflicker"]),
    dict(t=(92.70, CUT_TO_BLACK), src="LIPSYNC", lips="E2_double_ear", sub="top", cam=((.5, .45, 1.0), (.47, .43, 1.12))),
    dict(t=(CUT_TO_BLACK, END), src="BLACK", fx=["endcard"]),
]

# lip shapes (src="LIPSYNC" picks <lips>_<shape>.png): the double through the gap (20.32–23.48) and at the ear (93.65–95.14)
LIPSYNC = [(20.30, "neutral"), (20.32, "open"), (20.50, "ee"), (20.76, "neutral"), (21.00, "oo"), (21.15, "open"), (21.30, "ee"),
           (21.46, "neutral"), (21.79, "open"), (21.98, "oo"), (22.10, "ee"), (22.24, "oo"), (22.42, "ee"), (22.62, "ee"),
           (22.80, "open"), (22.90, "oo"), (22.98, "oo"), (23.12, "ee"), (23.28, "oo"), (23.50, "neutral"),
           (92.70, "neutral"), (93.65, "oo"), (93.82, "open"), (94.02, "ee"), (94.24, "ee"), (94.50, "neutral"), (94.76, "oo"),
           (94.95, "open"), (95.14, "neutral")]

# ---------------------------------------------------------------- phone screen states (same UI as EP01, text drawn in code)
PHONE_CLOCK = "02:49"
MSG_EP01_WARN = "Откроешь — погибнешь."
MSG_EP01_OPEN = "Открой дверь. Осталось десять секунд."
MSG_CHOICE = "Хочешь вернуть деньги — выбери, кто останется за дверью."
PHONE = {
    "rack_on": [(9.40, ("lock_glow", None))],
    "rack_msg": [(0, ("lock_glow", None)), (11.62, ("lock_text", "Не сопротивляйся. Это проверка."))],
    "fail_on": [(37.70, ("lock_glow", None))],
    "fail": [(0, ("lock_glow", None)), (39.46, ("lock_text", "Задание провалено.")),
             (40.80, ("lock_text", "Задание провалено. Штраф — 2 000 $"))],
    "bank": [(0, ("bank_app", (45.80, 500, -1500, [("Зачисление", 500), ("Штраф", -2000)])))],
    "chat3_pre": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_EP01_WARN)), (0, ("bubble_small", MSG_EP01_OPEN)),
                  (47.70, ("typing", None))],
    "chat3": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_EP01_WARN)), (0, ("bubble_small", MSG_EP01_OPEN)),
              (49.36, ("bubble_red", MSG_CHOICE))],
    "choice": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_CHOICE)),
               (53.40, ("photos", ("E2_photo_cop", "E2_photo_dbl"))), (59.45, ("timer", (61.35, 10))), (65.10, ("select", 0))],
    "floor": [(82.12, ("photo_full", "E2_photo_back"))],
}

# door impacts / jolts -> camera shake (fx "shake_hits")
HITS = [0.62, 2.30, 3.20, 5.15, 6.30, 7.55, 16.60, 25.92, 66.30]
FLASHES = [(40.80, "red"), (86.50, "white"), (CUT_TO_BLACK - 0.04, "white")]
COUNTDOWN = (0.0, -5.04, 10, 2.79)   # (show_from, start, seconds, show_until): EP01's 10-second timer, 00:05 at frame 0
ENDCARD = ("Серия 2", "Продолжение следует")
BIG_SUBS = ("«!Ты выбрал не того!».",)

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger)
SUBS = [
    (0.00, 2.48, "Замок начал !поворачиваться! снаружи."),
    (2.94, 5.00, "Я схватил ручку обеими руками,"),
    (5.16, 6.72, "но кто-то по ту сторону"),
    (6.72, 8.25, "двери оказался *сильнее*."),
    (9.32, 10.82, "Телефон завибрировал."),
    (11.58, 13.81, "«Не сопротивляйся, это *проверка*»."),
    (14.69, 16.09, "Какая ещё проверка?"),
    (16.40, 17.95, "Я упёрся ногой в дверь"),
    (17.95, 20.00, "и вдруг услышал *собственный голос*:"),
    (20.32, 21.50, "«Алекс, отойди."),
    (21.79, 23.48, "Я уже совершил эту ошибку»."),
    (24.43, 25.76, "Это говорил !мой двойник!."),
    (26.24, 27.80, "Ручка перестала двигаться,"),
    (27.94, 30.53, "потом из-под двери медленно потекла *вода*."),
    (31.10, 33.39, "Я посмотрел на стакан — он был *пуст*,"),
    (33.76, 35.10, "но я точно помнил,"),
    (35.16, 36.70, "что наполнил его до краёв."),
    (37.61, 38.92, "Телефон загорелся снова."),
    (39.46, 40.70, "«!Задание провалено!."),
    (40.80, 42.78, "Штраф — *2 000 долларов*»."),
    (43.45, 45.10, "На экране банковского приложения"),
    (45.10, 46.74, "баланс стал !отрицательным!,"),
    (47.02, 49.01, "а следом пришло новое сообщение:"),
    (49.37, 50.80, "«Хочешь вернуть деньги —"),
    (50.84, 52.70, "выбери, кто !останется за дверью!»."),
    (53.36, 54.90, "Появились две фотографии."),
    (55.10, 56.75, "На первой был *полицейский*,"),
    (56.82, 58.34, "на второй — *я сам*."),
    (59.36, 61.32, "Под фотографиями шёл обратный отсчёт:"),
    (61.70, 62.50, "«*10*…"),
    (62.50, 63.28, "«*10*… *9*…"),
    (63.28, 64.10, "«*10*… *9*… *8*…»"),
    (64.16, 66.22, "Я нажал на фотографию *полицейского*."),
    (67.00, 68.90, "За дверью раздался !короткий крик!,"),
    (69.18, 70.92, "потом наступила *тишина*."),
    (71.70, 72.70, "И кто-то осторожно"),
    (72.76, 74.07, "постучал *три раза*."),
    (74.93, 76.55, "Я снова посмотрел в глазок —"),
    (76.80, 77.92, "коридор был *пуст*."),
    (78.51, 79.95, "Только на полу лежал телефон,"),
    (80.28, 81.68, "точно такой же, *как мой*."),
    (82.03, 83.36, "Его экран загорелся."),
    (83.72, 86.19, "На нём появилась фотография моей квартиры,"),
    (86.52, 88.64, "сделанная !из-за моей спины!."),
    (89.51, 91.20, "А потом я услышал прямо возле уха"),
    (91.20, 92.61, "*собственный голос*:"),
    (93.65, 95.24, "«!Ты выбрал не того!»."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.62, "lock_clack", 1.0), (2.30, "lock_click", 0.8)]
    + [(3.20, "knock", 0.45), (5.15, "bang", 0.75), (6.30, "bang", 0.85), (7.55, "bang", 0.95), (5.20, "door_creak", 0.9)]
    + [(9.40, "vibrate", 1.0), (11.62, "notify_bad", 0.6)]
    + [(16.60, "bang", 0.7), (18.40, "door_creak", 0.45)]
    + [(25.92, "bang", 1.0), (25.95, "lock_click", 0.7)]
    + [(28.20, "water", 0.9), (30.85, "hit", 0.55), (34.55, "glass", 0.6)]
    + [(37.70, "vibrate", 1.0), (39.46, "notify_bad", 0.7), (40.80, "hit", 0.7), (40.80, "alarm", 0.3)]
    + [(45.80, "notify_bad", 0.55)]
    + [(47.10, "vibrate", 0.8), (49.36, "notify", 0.65), (53.40, "notify", 0.6)]
    + [(t, "tick_hard", 0.75) for t in (61.35, 62.35, 63.35, 64.35)]
    + [(65.10, "tap", 0.9), (66.28, "scream", 0.8)]
    + [(t, "knock", 0.5) for t in (74.15, 74.47, 74.79)]
    + [(75.60, "peep", 0.6), (76.62, "tube_on", 0.5)]
    + [(82.12, "notify", 0.35), (86.40, "hit", 0.55), (89.70, "creak", 0.35)]
    + [(CUT_TO_BLACK, "boom_tail", 0.9)]
)
HUM = [(76.60, 85.00)]       # fluorescent hum windows (peephole shots)
# music intensity curve (time, level 0..1): starts where EP01's riser ended, drops to near-silence for the voices
MUSIC = [(0, .9), (2.7, .8), (8.3, .55), (9.3, .35), (14.6, .4), (18.3, .12), (24.3, .2), (25.9, .45), (27.9, .3), (36.9, .45),
         (40.8, .8), (43.0, .55), (47.0, .5), (53.3, .6), (59.3, .7), (61.3, .85), (66.2, .9), (66.3, .05), (74.9, .05),
         (76.6, .35), (82.0, .45), (86.4, .55), (88.7, .5), (89.4, .1), (93.6, .15), (95.3, .15)]
BELLS = [(26.6, 987.8), (28.9, 880.0), (31.2, 784.0), (33.8, 740.0), (36.0, 698.5), (78.6, 987.8), (83.8, 932.3)]
RISER = (81.8, 85.2)


def check():
    missing = [k for k in ("VO_END", "CUT_TO_BLACK", "END") if globals()[k] is None]
    if missing or not SHOTS or not SUBS:
        raise SystemExit("timeline_ep02 is still a template: set " + ", ".join(missing + [k for k in ("SHOTS", "SUBS") if not globals()[k]]))
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)


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
