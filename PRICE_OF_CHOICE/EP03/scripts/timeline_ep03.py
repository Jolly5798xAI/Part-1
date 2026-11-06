"""EP03 «КТО ЗА МОЕЙ СПИНОЙ?» — editing timeline (single source of truth). Same format as EP02 (timeline_ep02_reference.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper small, word timestamps). Verified text: docs/EP03_transcript.txt.

EP03 opens where EP02 ended: the double whispering «Ты выбрал не того» at Alex's ear (EP02 shot E2_double_ear, same frames).

`python3 scripts/timeline_ep03.py` checks the timeline and writes timeline/ep03_timeline.json.
"""
import json, os

FPS = 30                 # locked for the series
VO_END = 102.77
CUT_TO_BLACK = 102.85
END = 105.30

# ---------------------------------------------------------------- shots
# src: still name (scenes/<src>.png, or ../EP02/illustrations/<src>.png for frames reused from EP02),
#      anim folder (scenes/<src>/), "LIPSYNC" (+ lips=<base>, shape picked from LIPSYNC by time) or "BLACK"
# cam: (cx, cy, zoom) start -> end, in source-normalised coords (0..1), zoom 1 = full frame
SHOTS = [
    # --- 1. «ТЫ ВЫБРАЛ НЕ ТОГО» (continues EP02's last shot)
    dict(t=(0.00, 1.25), src="LIPSYNC", lips="E2_double_ear", sub="top", cam=((.47, .43, 1.12), (.46, .43, 1.16))),
    dict(t=(1.25, 4.80), src="E2_double_behind", cam=((.47, .45, 1.15), (.4, .42, 1.42)), fx=["leakflicker"]),
    # --- 2. NOBODY BEHIND — WET PRINTS
    dict(t=(4.80, 6.25), src="E3_turn", anim=(0.0, 1.0), anim_start=4.86, anim_dur=0.95, cam=((.5, .42, 1.0), (.5, .4, 1.08)), fx=["shake_hits"]),
    dict(t=(6.25, 7.95), src="E3_hall_empty", cam=((.5, .5, 1.0), (.5, .47, 1.1))),
    dict(t=(7.95, 10.25), src="E3_prints_appear", anim=(0.0, 1.0), anim_start=8.0, anim_dur=2.1, cam=((.5, .55, 1.0), (.48, .6, 1.08))),
    dict(t=(10.25, 13.60), src="E3_prints_path", cam=((.42, .7, 1.25), (.55, .38, 1.15))),
    dict(t=(13.60, 17.35), src="E3_step_back", anim=(0.0, 1.0), anim_start=13.9, anim_dur=3.0, cam=((.5, .55, 1.0), (.5, .58, 1.06))),
    dict(t=(17.35, 20.45), src="E3_invisible", cam=((.5, .55, 1.0), (.42, .62, 1.22)), fx=["leakflicker"]),
    # --- 3. THE THIRD TASK
    dict(t=(20.45, 22.05), src="E3_pov_door", cam=((.5, .5, 1.0), (.5, .55, 1.15)), phone="task_pre", fx=["vibrate"]),
    dict(t=(22.05, 25.55), src="E3_pov_door", sub="bottom", cam=((.49, .63, 1.45), (.49, .63, 1.58)), phone="task"),
    dict(t=(25.55, 28.15), src="E3_pov_door", sub="bottom", cam=((.49, .64, 1.58), (.49, .64, 1.68)), phone="task"),
    # --- 4. THE MIRROR
    dict(t=(28.15, 30.40), src="E3_mirror_wide", cam=((.5, .45, 1.0), (.4, .4, 1.15))),
    dict(t=(30.40, 32.15), src="E3_mirror", cam=((.45, .42, 1.05), (.45, .42, 1.12))),
    dict(t=(32.15, 35.30), src="E3_mirror_dbl", cam=((.45, .42, 1.12), (.33, .36, 1.6))),
    dict(t=(35.30, 36.55), src="E3_look_back", cam=((.5, .4, 1.0), (.5, .4, 1.06)), fx=["shake_hits"]),
    dict(t=(36.55, 37.75), src="E3_behind_empty_m", cam=((.5, .6, 1.0), (.48, .65, 1.1))),
    dict(t=(37.75, 39.50), src="E3_mirror_dbl_close", cam=((.5, .4, 1.0), (.42, .38, 1.12))),
    dict(t=(39.50, 41.95), src="E3_mirror_shh", anim=(0.0, 1.0), anim_start=39.95, anim_dur=0.9, cam=((.42, .38, 1.1), (.36, .38, 1.3))),
    dict(t=(41.95, 44.10), src="E3_mirror_point", anim=(0.0, 1.0), anim_start=42.05, anim_dur=0.7, cam=((.45, .42, 1.1), (.6, .5, 1.2))),
    # --- 5. THE OFFICER OUTSIDE / THE LOCK
    dict(t=(44.10, 46.75), src="E3_door_outside", cam=((.5, .5, 1.0), (.5, .58, 1.18)), fx=["leakflicker", "shake_hits"]),
    dict(t=(46.75, 49.45), src="S13_door_bang", cam=((.5, .5, 1.1), (.5, .5, 1.16)), fx=["shake_hits", "leakflicker"]),
    dict(t=(49.45, 52.45), src="E3_lock_closed", cam=((.5, .5, 1.0), (.5, .5, 1.2))),
    # --- 6. TO THE BEDROOM
    dict(t=(52.45, 55.80), src="E3_prints_bedroom", cam=((.4, .75, 1.3), (.6, .5, 1.12))),
    dict(t=(55.80, 58.40), src="E3_approach", anim=(0.0, 1.0), cam=((.5, .5, 1.0), (.5, .52, 1.04))),
    dict(t=(58.40, 61.05), src="E3_beddoor_close", cam=((.5, .55, 1.0), (.55, .62, 1.15)), fx=["bedleak"]),
    dict(t=(61.05, 64.05), src="E3_pov_beddoor", cam=((.5, .5, 1.0), (.5, .55, 1.12)), phone="dark", fx=["bedleak"]),
    dict(t=(64.05, 66.55), src="E3_pov_beddoor", cam=((.5, .58, 1.2), (.5, .6, 1.3)), phone="bed_pre", fx=["vibrate"]),
    dict(t=(66.55, 70.05), src="E3_pov_beddoor", sub="bottom", cam=((.5, .63, 1.45), (.5, .63, 1.6)), phone="bed"),
    dict(t=(70.05, 72.10), src="E3_alex_face_bed", cam=((.5, .4, 1.0), (.45, .38, 1.1))),
    # --- 7. THE ORIGINAL
    dict(t=(72.10, 74.75), src="E3_beddoor_open", anim=(0.0, 1.0), anim_start=72.2, anim_dur=2.5, cam=((.5, .5, 1.0), (.55, .5, 1.1))),
    dict(t=(74.75, 77.05), src="E3_room_dark", cam=((.5, .5, 1.0), (.5, .45, 1.2)), fx=["dark"]),
    dict(t=(77.05, 80.30), src="E3_tied", cam=((.5, .55, 1.0), (.5, .35, 1.25))),
    dict(t=(80.30, 82.85), src="E3_tied_face", cam=((.5, .5, 1.0), (.5, .47, 1.25))),
    dict(t=(82.85, 85.75), src="LIPSYNC", lips="E3_tied_head", cam=((.5, .48, 1.05), (.5, .48, 1.12)), fx=["handshake"]),
    dict(t=(85.75, 88.30), src="E3_from_chair", cam=((.5, .5, 1.0), (.42, .48, 1.15))),
    # --- 8. THE LAST MESSAGE
    dict(t=(88.30, 91.95), src="E3_pov_room", cam=((.5, .5, 1.0), (.5, .55, 1.15)), phone="final_pre", fx=["vibrate"]),
    dict(t=(91.95, 95.65), src="E3_pov_room_close", sub="bottom", cam=((.5, .63, 1.45), (.5, .63, 1.58)), phone="final"),
    dict(t=(95.65, 97.85), src="E3_pov_room_close", sub="bottom", cam=((.5, .64, 1.6), (.5, .66, 1.85)), phone="final", fx=["redglow", "glitch", "handshake"]),
    # --- 9. HE CRIES WITH MY VOICE — CUT
    dict(t=(97.85, 100.45), src="E3_tied_face_tears", cam=((.5, .5, 1.05), (.5, .45, 1.3))),
    dict(t=(100.45, CUT_TO_BLACK), src="E3_tied_face_tears_eyes", cam=((.5, .45, 1.0), (.5, .43, 1.18))),
    dict(t=(CUT_TO_BLACK, END), src="BLACK", fx=["endcard"]),
]

# lip / head shapes for src="LIPSYNC": the double's whisper (EP02 E2_double_ear_*), then the tied man shaking his head (E3_tied_head_*)
LIPSYNC = [(0.00, "neutral"), (0.18, "oo"), (0.30, "ee"), (0.46, "open"), (0.64, "ee"), (0.80, "oo"), (0.95, "open"), (1.12, "neutral"),
           (82.85, "c")]
_t, _i = 84.12, 0
while _t < 85.60:                       # «отчаянно замотал головой» 84.12–85.56: fast left/right shakes
    LIPSYNC.append((round(_t, 2), ("l", "c", "r", "c")[_i % 4])); _t += 0.09; _i += 1
LIPSYNC.append((85.62, "c"))

# ---------------------------------------------------------------- phone screen states (same UI as EP01/EP02, text drawn in code)
PHONE_CLOCK = "02:50"
MSG_EP02 = "Хочешь вернуть деньги — выбери, кто останется за дверью."
MSG_TASK = "Третье задание. Найди того, кто стоит за твоей спиной."
MSG_REWARD = "Награда — пять тысяч долларов."
MSG_DONT = "Не входи. Там находится оригинал."
MSG_DONE, MSG_FOUND, MSG_KILL = "Задание выполнено.", "Объект найден.", "Теперь уничтожь копию."
PHONE = {
    "task_pre": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_EP02)), (20.90, ("typing", None))],
    "task": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_EP02)), (22.16, ("bubble_red", MSG_TASK)), (25.72, ("bubble", MSG_REWARD))],
    "dark": [(0, ("off", None))],
    "bed_pre": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_TASK)), (0, ("bubble_small", MSG_REWARD)), (64.30, ("typing", None))],
    "bed": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_TASK)), (0, ("bubble_small", MSG_REWARD)), (66.70, ("bubble_red", MSG_DONT))],
    "final_pre": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_REWARD)), (0, ("bubble_small", MSG_DONT)), (89.00, ("typing", None))],
    "final": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_REWARD)), (0, ("bubble_small", MSG_DONT)),
              (92.08, ("bubble", MSG_DONE)), (93.56, ("bubble", MSG_FOUND)), (95.78, ("bubble_red", MSG_KILL))],
}

# jolts -> camera shake (fx "shake_hits"): the whip turn, the look back, the officer's knocks
HITS = [4.95, 35.42, 44.30, 44.62, 44.94, 46.70]
FLASHES = [(32.30, "white"), (81.24, "white"), (95.78, "red"), (CUT_TO_BLACK - 0.04, "white")]
COUNTDOWN = None
ENDCARD = ("Серия 3 · «Кто за моей спиной?»", "Продолжение следует")
BIG_SUBS = ("«!Ты выбрал не того!».", "«!Теперь уничтожь копию!».")

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger)
# Only words that are in the voiceover; at most two lines each.
SUBS = [
    (0.00, 1.18, "«!Ты выбрал не того!»."),
    (2.12, 4.56, "Эти слова прозвучали прямо у *моего уха*."),
    (4.92, 6.16, "Я резко обернулся,"),
    (6.38, 7.72, "за спиной *никого* не было,"),
    (7.98, 10.14, "но на полу появились !мокрые следы!."),
    (10.36, 13.22, "Они вели от входной двери *прямо ко мне*."),
    (13.98, 15.28, "Я сделал шаг назад,"),
    (15.62, 17.16, "следы *тоже сдвинулись*."),
    (17.50, 20.14, "Будто кто-то !невидимый! повторял мои движения."),
    (20.58, 21.64, "Телефон завибрировал."),
    (22.16, 23.40, "«Третье задание —"),
    (23.46, 25.40, "найди того, кто стоит *за твоей спиной*»."),
    (25.72, 27.68, "«Награда — *пять тысяч долларов*»."),
    (28.23, 30.22, "Я посмотрел в зеркало в прихожей,"),
    (30.48, 31.88, "в отражении стоял я,"),
    (32.22, 34.66, "а позади меня — !ещё один Алекс!."),
    (35.42, 37.26, "Я обернулся — *никого*."),
    (37.82, 39.24, "Снова посмотрел в зеркало."),
    (39.60, 41.44, "Двойник поднял *палец к губам*"),
    (41.44, 43.48, "и указал на *входную дверь*."),
    (44.24, 46.26, "Снаружи послышался голос полицейского:"),
    (46.84, 49.40, "«Алекс, открой. !Он уже внутри!»."),
    (49.64, 51.26, "Я посмотрел на дверной замок,"),
    (51.54, 52.38, "он был *закрыт*,"),
    (52.52, 55.58, "но мокрые следы теперь вели *к моей спальне*."),
    (56.02, 58.16, "Я медленно подошёл к двери комнаты,"),
    (58.46, 60.80, "изнутри раздался *звук моего телефона*,"),
    (61.12, 63.50, "хотя настоящий телефон был *у меня в руке*."),
    (64.14, 66.12, "На экране появилось новое сообщение:"),
    (66.70, 69.50, "«Не входи. Там находится !оригинал!»."),
    (70.32, 71.74, "Я не понял, что это значит,"),
    (72.22, 74.50, "пока дверь спальни не приоткрылась."),
    (74.80, 76.56, "В темноте сидел *человек*."),
    (77.20, 80.02, "Он был привязан к стулу с заклеенным ртом,"),
    (80.40, 82.46, "и у него было !моё лицо!."),
    (82.96, 85.56, "Он увидел меня и отчаянно замотал головой,"),
    (85.80, 88.02, "потом посмотрел на телефон в моей руке."),
    (88.46, 91.10, "На экране появилось *последнее сообщение*:"),
    (92.08, 93.40, "«Задание выполнено."),
    (93.56, 95.06, "Объект *найден*»."),
    (95.78, 97.28, "«!Теперь уничтожь копию!»."),
    (97.94, 100.40, "И в этот момент человек на стуле"),
    (100.40, 102.74, "начал плакать !моим голосом!."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
PRINT_TIMES = [round(8.0 + 2.1 * i / 8.2, 2) for i in range(8)]   # one wet step per print appearing (E3_prints_appear)
SFX = (
    [(1.30, "breath", 0.6), (4.92, "whoosh", 0.9), (4.95, "cloth", 0.8), (4.97, "hit", 0.35)]
    + [(t, "wet_step", 0.55 + 0.05 * i) for i, t in enumerate(PRINT_TIMES)]
    + [(14.30, "cloth", 0.45), (14.62, "step", 0.6), (15.62, "wet_step", 0.8), (15.98, "wet_step", 0.85), (17.45, "breath", 0.7)]
    + [(20.60, "vibrate", 1.0), (22.16, "notify_bad", 0.7), (25.72, "notify", 0.6), (25.80, "coin", 0.5)]
    + [(28.25, "step", 0.4), (28.65, "step", 0.4), (32.30, "sting", 1.0), (35.40, "whoosh", 0.8), (35.42, "cloth", 0.7), (36.60, "hit", 0.4)]
    + [(39.98, "sting_soft", 0.7), (42.08, "cloth", 0.4)]
    + [(t, "knock_muffled", 0.9) for t in (44.30, 44.62, 44.94)] + [(46.70, "knock_muffled", 1.0)]
    + [(49.62, "lock_click", 0.35)]
    + [(t, "step", 0.35) for t in (56.30, 56.95, 57.60)] + [(58.45, "ring_muffled", 1.0)]
    + [(64.20, "vibrate", 0.9), (66.70, "notify_bad", 0.7)]
    + [(72.30, "door_creak", 0.8), (73.10, "creak", 0.45), (74.80, "hit", 0.45)]
    + [(81.24, "sting", 0.9), (84.10, "mmph", 0.8), (84.20, "chair_creak", 0.7)]
    + [(88.50, "vibrate", 0.9), (92.08, "notify", 0.55), (93.56, "notify", 0.55), (95.78, "notify_bad", 0.8), (95.78, "hit", 0.45), (95.80, "alarm", 0.2)]
    + [(98.00, "sob", 0.75)]
    + [(CUT_TO_BLACK, "boom_tail", 0.9), (CUT_TO_BLACK, "sting", 0.6)]
)
HUM = []                 # no stairwell shots in EP03
# music intensity curve (time, level 0..1): starts near EP02's level under the whisper; drops out for the «shh» and the cut
MUSIC = [(0, .15), (1.2, .3), (4.9, .6), (6.3, .25), (8.0, .4), (13.6, .45), (17.4, .3), (20.5, .45), (28.2, .35), (32.2, .7),
         (35.3, .55), (37.8, .4), (39.5, .12), (44.1, .3), (49.5, .35), (52.5, .45), (55.8, .5), (58.4, .3), (64.1, .45),
         (66.6, .55), (70.0, .4), (72.1, .55), (74.8, .65), (80.3, .75), (82.9, .8), (88.3, .7), (91.9, .8), (95.7, .85),
         (97.8, .5), (100.4, .4), (102.8, .4)]
BELLS = [(6.4, 987.8), (10.4, 880.0), (28.3, 784.0), (37.9, 740.0), (52.6, 698.5), (74.9, 987.8), (80.4, 932.3)]
RISER = (88.3, 95.7)


def check():
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    assert SHOTS[0]["t"][0] == 0 and SHOTS[-1]["t"][1] == END
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)
    assert SUBS[-1][1] <= VO_END + 0.05
    assert all(0 <= t < END for t, _, _ in SFX)


def export():
    check()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC,
                phone=PHONE, hits=HITS, flashes=FLASHES, countdown=COUNTDOWN, subtitles=SUBS, sfx=SFX, hum=HUM, music=MUSIC)
    with open(os.path.join(root, "timeline", "ep03_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events; runtime {END:.2f}s")
