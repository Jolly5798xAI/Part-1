"""EP01 «Стакан воды» — editing timeline (single source of truth).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never altered).
They were taken from word-level timestamps in timeline/transcript_words.json
(faster-whisper) and checked against silencedetect pauses.

`python3 scripts/timeline_ep01.py` writes timeline/ep01_timeline.json for reference.
"""
import json, os

FPS = 30
VO_END = 74.92
CUT_TO_BLACK = 75.05
END = 77.2

# ---------------------------------------------------------------- shots
# src: still name (illustrations/<src>.png) or anim folder (illustrations/<src>/)
# cam: (cx, cy, zoom) start -> end, in source-normalised coords (0..1), zoom 1 = full frame
# anim: (t_start, t_end) -> frame range mapping for animated sources ("rev" plays backwards)
# fx: list of effect tags handled by the renderer
SHOTS = [
    # --- HOOK
    dict(t=(0.00, 1.70), src="S01_glass_hook", cam=((.5, .55, 1.0), (.47, .62, 1.18)), fx=["leakflicker"]),
    dict(t=(1.70, 2.78), src="S01_glass_hook", cam=((.46, .70, 1.65), (.46, .72, 1.85))),
    dict(t=(2.78, 3.80), src="S07_entry_wide", cam=((.5, .5, 1.05), (.45, .52, 1.2))),
    dict(t=(3.80, 4.46), src="S13_door_bang", cam=((.5, .5, 1.1), (.5, .5, 1.15)), fx=["shake_hits"]),
    dict(t=(4.46, 5.70), src="S02_door_inside", cam=((.5, .45, 1.0), (.5, .45, 1.12)), fx=["shake_hits"]),
    dict(t=(5.70, 5.92), src="BLACK"),
    # --- THE FIRST MESSAGE
    dict(t=(5.92, 9.70), src="S03_phone_msg1", cam=((.5, .5, 1.0), (.5, .52, 1.22)), phone="msg1", fx=["vibrate"]),
    dict(t=(9.70, 11.78), src="S03_phone_msg1", cam=((.5, .5, 1.55), (.5, .5, 1.7)), phone="msg1", fx=["timer60"]),
    dict(t=(11.78, 13.45), src="S04_alex_phone_face", cam=((.5, .4, 1.25), (.5, .42, 1.08))),
    dict(t=(13.45, 15.88), src="S03_phone_msg1", cam=((.5, .47, 1.9), (.5, .47, 2.05)), phone="msg1_hl"),
    dict(t=(15.88, 17.32), src="S05_place_glass", cam=((.5, .45, 1.1), (.5, .55, 1.25))),
    # --- MONEY + TASK 2
    dict(t=(17.32, 20.42), src="S06_phone_bank", cam=((.5, .5, 1.1), (.5, .48, 1.28)), phone="bank", fx=["vibrate"]),
    dict(t=(20.42, 25.02), src="S06_phone_bank", cam=((.5, .45, 1.45), (.5, .5, 1.2)), phone="task2"),
    # --- KNOCK / POLICE
    dict(t=(25.02, 26.88), src="S07_entry_wide", cam=((.5, .5, 1.25), (.5, .5, 1.32)), fx=["shake_hits"]),
    dict(t=(26.88, 29.20), src="S02_door_inside", cam=((.5, .5, 1.0), (.5, .42, 1.25)), fx=["leakflicker", "shake_hits"]),
    dict(t=(29.20, 32.62), src="S13_door_bang", cam=((.55, .5, 1.0), (.4, .45, 1.2)), fx=["shake_hits"]),
    dict(t=(32.62, 34.10), src="S08_peephole_lean", cam=((.5, .45, 1.0), (.42, .4, 1.45)), fx=["iris_out"]),
    # --- THROUGH THE PEEPHOLE
    dict(t=(34.10, 36.80), src="S09_peephole_wide", cam=((.36, .5, 1.25), (.36, .48, 1.35)), fx=["peephole", "iris_in", "tube"]),
    dict(t=(36.80, 38.52), src="S09_peephole_wide", cam=((.36, .48, 1.35), (.66, .5, 1.55)), fx=["peephole", "tube"]),
    dict(t=(38.52, 39.66), src="S10_peephole_man", cam=((.5, .5, 1.0), (.5, .46, 1.18)), fx=["peephole", "tube"]),
    # --- THE LOCK / WARNING
    dict(t=(39.66, 41.16), src="S11_hand_lock", anim=(0.0, 1.0), cam=((.5, .5, 1.0), (.5, .5, 1.08))),
    dict(t=(41.16, 42.92), src="S12_phone_rack", cam=((.5, .5, 1.0), (.55, .4, 1.25)), phone="warn_on", fx=["vibrate", "redglow"]),
    dict(t=(42.92, 44.84), src="S12_phone_rack", cam=((.5, .49, 1.55), (.5, .49, 1.72)), phone="warn", fx=["redglow", "glitch"]),
    dict(t=(44.84, 45.96), src="S11_hand_lock", anim=(1.0, 0.0), cam=((.5, .5, 1.08), (.5, .5, 1.0))),
    dict(t=(45.96, 48.00), src="S13_door_bang", cam=((.45, .5, 1.15), (.45, .5, 1.3)), fx=["shake_hits", "dust"]),
    # --- THE QUESTION
    dict(t=(48.00, 50.88), src="S14_peephole_cop", cam=((.5, .5, 1.0), (.5, .47, 1.15)), fx=["peephole", "tube"]),
    dict(t=(50.88, 52.06), src="S14_peephole_cop", cam=((.5, .45, 1.35), (.5, .45, 1.38)), fx=["peephole", "tube", "freeze"]),
    # --- THE DOUBLE
    dict(t=(52.06, 54.80), src="S15_head_turn", anim=(0.0, 1.0), cam=((.5, .5, 1.0), (.5, .48, 1.08)), fx=["peephole", "tube"]),
    dict(t=(54.80, 55.90), src="S16_double_face_neutral", cam=((.5, .5, 1.0), (.5, .48, 1.08)), fx=["peephole", "tube"]),
    dict(t=(55.90, 57.52), src="S16_double_face_neutral", cam=((.5, .47, 1.18), (.5, .47, 1.26)), fx=["peephole", "tube", "flash"]),
    dict(t=(57.52, 58.96), src="S17_alex_steps_back", cam=((.5, .42, 1.3), (.5, .45, 1.0))),
    dict(t=(58.96, 62.04), src="S18_bloody_palm", anim=(0.0, 1.0), anim_start=59.30, anim_dur=0.5, cam=((.5, .5, 1.0), (.5, .5, 1.15)), fx=["peephole", "tube"]),
    dict(t=(62.04, 64.72), sub="top", src="S16_double_face_neutral", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["peephole", "tube"]),
    dict(t=(64.72, 66.36), src="LIPSYNC", sub="top", cam=((.5, .52, 1.12), (.5, .53, 1.2)), fx=["peephole", "tube"]),
    # --- FINAL MESSAGE
    dict(t=(66.36, 68.58), src="S19_phone_final", cam=((.5, .5, 1.0), (.5, .5, 1.15)), phone="final_pre", fx=["vibrate"]),
    dict(t=(68.58, 71.40), src="S19_phone_final", cam=((.5, .47, 1.45), (.5, .47, 1.65)), phone="final", fx=["handshake"]),
    dict(t=(71.40, CUT_TO_BLACK), src="S20_lock_turns", anim=(0.0, 1.0), cam=((.5, .5, 1.0), (.5, .5, 1.12)), fx=["countdown"]),
    dict(t=(CUT_TO_BLACK, END), src="BLACK", fx=["endcard"]),
]

# lip shapes for the silent «Не верь телефону» (64.78–65.88)
LIPSYNC = [(64.72, "neutral"), (64.78, "ee"), (64.92, "ee"), (65.05, "neutral"), (65.18, "ee"), (65.36, "ee"),
           (65.50, "oo"), (65.66, "oo"), (65.80, "neutral")]

# ---------------------------------------------------------------- phone screen states
# Each state: list of (appear_time, element). Elements are drawn by the renderer.
ADDRESS = "Алекс. Лесная\u00a012, кв.\u00a047."
MSG1 = "Поставь полный стакан у входа. Время — шестьдесят секунд."
PHONE = {
    "msg1": [(5.92, ("header", "Номер скрыт")), (6.68, ("typing", None)), (7.94, ("bubble", ADDRESS + "\n" + MSG1))],
    "msg1_hl": [(0, ("header", "Номер скрыт")), (0, ("bubble", ADDRESS + "\n" + MSG1)), (14.46, ("highlight", ADDRESS))],
    "bank": [(0, ("header", "Номер скрыт")), (0, ("bubble", ADDRESS + "\n" + MSG1)), (18.72, ("push", ("БАНК", "Зачисление: +500\u00a0$")))],
    "task2": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG1)),
              (21.02, ("typing", None)), (22.02, ("bubble", "Следующее задание —\u00a02\u00a0000\u00a0$")),
              (23.12, ("bubble", "Не открывай дверь три минуты.")), (24.00, ("timer", (24.00, 180)))],
    "warn_on": [(41.25, ("lock_glow", None))],
    "warn": [(0, ("lock_glow", None)), (42.96, ("lock_text", "Откроешь — погибнешь."))],
    "final_pre": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", "Не открывай дверь три минуты.")), (0, ("bubble_small", "Откроешь — погибнешь.")), (66.98, ("typing", None))],
    "final": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", "Откроешь — погибнешь.")),
              (68.64, ("bubble_red", "Открой дверь. Осталось десять секунд.")), (69.96, ("timer", (69.96, 10)))],
}

# shake / hit moments (screen jolts), used by fx "shake_hits"
HITS = [4.50, 4.80, 5.10, 5.38, 26.30, 26.52, 26.74, 27.55, 27.80, 29.45, 29.70, 29.95, 31.60, 31.85,
        46.30, 46.66, 47.00, 47.30, 47.60]
FLASHES = [(0.00, "white"), (4.50, "white"), (42.96, "red"), (55.92, "white"), (CUT_TO_BLACK - 0.04, "white")]

# ---------------------------------------------------------------- subtitles (text verified by ear-checked ASR,
# ASR slips fixed: «стакан входа» → «стакан у входа», «насчёт» → «на счёт», «одёрнул» → «отдёрнул», «приложил глазку» → «приложил к глазку»)
# *word* = highlight (yellow), !word! = danger (red)
SUBS = [
    (0.00, 1.56, "Мне заплатили *500 долларов*"),
    (1.56, 2.62, "за стакан воды."),
    (2.80, 3.92, "А через минуту кто-то"),
    (3.92, 5.62, "попытался !выломать! мою дверь."),
    (5.92, 7.76, "Всё началось с сообщения без номера:"),
    (7.94, 9.60, "«Поставь полный стакан у входа."),
    (9.80, 11.50, "Время — *60 секунд*»."),
    (11.84, 13.42, "Я решил, что это мошенники,"),
    (13.48, 15.82, "но в сообщении были *моё имя и адрес*."),
    (15.94, 17.22, "Я поставил стакан."),
    (17.38, 18.62, "Телефон завибрировал:"),
    (18.72, 20.32, "на счёт пришли *500 долларов*."),
    (20.48, 22.95, "Следующее задание стоило уже *2 тысячи*."),
    (23.12, 24.92, "«Не открывай дверь *3 минуты*»."),
    (25.08, 26.82, "В ту же секунду раздался *стук*."),
    (26.94, 29.14, "Мужчина за дверью представился полицейским."),
    (29.14, 31.18, "Он кричал, что в доме утечка газа"),
    (31.18, 32.58, "и нужно срочно выходить."),
    (32.68, 34.06, "Я посмотрел в глазок."),
    (34.16, 36.04, "Полицейский действительно был в форме,"),
    (36.18, 38.34, "но рядом с ним стоял ещё один человек —"),
    (38.52, 39.56, "*лицом к стене*."),
    (39.70, 40.98, "Я потянулся к замку —"),
    (41.18, 42.42, "телефон загорелся."),
    (42.96, 44.62, "«!Откроешь — погибнешь!»."),
    (44.90, 46.04, "Я отдёрнул руку."),
    (46.24, 47.86, "Снаружи начали !бить в дверь!."),
    (48.04, 50.86, "Я спросил полицейского, как зовут моего соседа."),
    (51.00, 51.94, "Он *замолчал*."),
    (52.10, 54.78, "А человек у стены медленно повернул голову."),
    (55.16, 57.12, "У него было !моё лицо!."),
    (57.48, 58.82, "Я отступил от двери."),
    (58.96, 61.92, "Двойник приложил к глазку окровавленную ладонь,"),
    (62.06, 64.30, "а затем беззвучно произнёс:"),
    (64.78, 66.10, "«!Не верь телефону!»."),
    (66.34, 68.48, "В этот момент пришло новое сообщение."),
    (68.64, 71.02, "«Открой дверь. Осталось *10 секунд*»."),
    (71.42, 72.56, "И тут я услышал,"),
    (72.60, 74.88, "как кто-то начал !открывать замок! снаружи."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.00, "hit", 0.8)]
    + [(t, "bang", 1.0) for t in (4.50, 4.80, 5.10, 5.38)]
    + [(6.00, "vibrate", 0.8), (7.94, "notify", 0.7)]
    + [(t, "tick", 0.5) for t in (10.38, 11.38)]
    + [(16.92, "glass", 0.9)]
    + [(17.82, "vibrate", 0.9), (18.72, "coin", 0.7), (22.02, "notify", 0.6), (23.12, "notify", 0.5)]
    + [(t, "knock", 1.0) for t in (26.30, 26.52, 26.74)]
    + [(t, "knock", 0.65) for t in (27.55, 27.80)]
    + [(t, "knock", 0.85) for t in (29.45, 29.70, 29.95, 31.60, 31.85)]
    + [(33.50, "peep", 0.6), (34.10, "tube_on", 0.5)]
    + [(41.22, "vibrate", 1.0), (42.96, "hit", 1.0), (42.96, "alarm", 0.5)]
    + [(t, "bang", 1.1) for t in (46.30, 46.66, 47.00, 47.30, 47.60)]
    + [(52.30, "creak", 0.9), (55.92, "hit", 1.0), (59.40, "slap", 0.9), (64.78, "whisper", 0.45)]
    + [(66.52, "vibrate", 1.0), (68.64, "notify_bad", 0.7)]
    + [(t, "tick_hard", 0.75) for t in (69.96, 70.96, 71.96, 72.96, 73.96)]
    + [(72.05, "lock_click", 0.9), (73.00, "lock_click", 1.0), (74.30, "lock_turn", 1.1), (74.98, "lock_clack", 1.3)]
    + [(75.05, "boom_tail", 0.9)]
)
# fluorescent hum windows (stairwell shots)
HUM = [(34.10, 39.66), (48.00, 66.36)]
# music intensity curve (time, level 0..1)
MUSIC = [(0, .55), (2.7, .5), (5.6, .15), (5.92, .3), (17.3, .35), (25.0, .5), (32.6, .6), (39.6, .7), (42.9, .85),
         (48.0, .55), (50.9, .12), (52.0, .1), (54.8, .6), (57.5, .65), (64.7, .4), (66.3, .75), (71.4, .95), (75.0, 1.0)]


def export():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC,
                phone=PHONE, hits=HITS, flashes=FLASHES, subtitles=SUBS, sfx=SFX, hum=HUM, music=MUSIC)
    with open(os.path.join(root, "timeline", "ep01_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events; runtime {END:.2f}s")
