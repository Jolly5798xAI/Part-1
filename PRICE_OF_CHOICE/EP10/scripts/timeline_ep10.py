"""EP10 «СОЗДАТЕЛЬ» — editing timeline (single source of truth). Same format as EP09 (../EP09/scripts/timeline_ep09.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
The approved MP3 is 121.81 s (speech 0.12 – 121.73 s): 31.8 s over the 75–90 s target — reported, not altered.
Phrase times: timeline/transcript_words.json (Whisper small via sherpa-onnx, cut at the VO's own pauses ≥ 0.09 s, silencedetect −36 dB);
verified text: docs/EP10_transcript.txt.

EP10 opens on EP09's last frame (E9_cop_screen_close: the officer's phone, red, «Оригинал должен умереть»), the same second — flat 47,
the front door open, no recap, no time jump, no change of location. It ends on «…из-за двери комнаты двести четыре»: door 204 under its
red lamp, hard cut to black. Nothing after it; what happened to the sister is not shown.

Production names (never shown): ALEX_48 (hero, «48», left hand being deleted), ALEX_49 (cyan «49»), ALEX_ZERO (red «0»),
ALEX_OLD_POLICE (the officer: old Alex), SISTER (Елена — named for the first time in EP10's voiceover; never named in EP01–EP09).

Lip-sync: ALEX_48, ALEX_ZERO, the officer (calm, then afraid) and the sister (EP08's close feed stills; EP10's room-204 webcam stills)
pick their mouth shape frame by frame from the VO envelope. The narrator voices every line (no second voice).

`python3 scripts/timeline_ep10.py` checks the timeline and writes timeline/ep10_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 121.81          # the approved MP3 is 121.809 s
CUT_TO_BLACK = 121.74    # hard cut on the last word «…двести четыре» (speech ends 121.73)
END = 121.81             # the video ends with the MP3 (black tail; no end card, no call to action)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- key moments (VO clock)
T_AIM = 4.9              # the phone settles on ALEX_ZERO («…с номером ноль»)
T_ON = 22.55             # «…все телефоны загорелись»
T_MANY = 25.3            # «…сотни лиц» — the grid has zoomed out to hundreds
T_TAP = 64.95            # «Я нажал «Остановить игру»»
T_RED = 66.45            # «…экран стал красным»
T_DENY = 67.53           # «Недостаточно прав»
T_SIS_ON = 73.3          # «Вдруг заговорила сестра»
T_TURN = 80.75           # «Алекс-ноль резко обернулся»
T_VIDEO = 82.75          # «На экранах появилось видео»
T_CAP = 84.29            # «Комната двести четыре»
T_PROJ, T_CREATOR, T_NAME = 91.05, 92.27, 93.35   # «Проект «Алекс»», «Создатель:», «Елена»
T_VANISH = 96.85         # «Он начал исчезать»
T_KNEES = 99.35          # the knees hit the floor
T_OFF = 109.25           # «Экран телефона погас»
T_LVL, T_NEXT, T_NEXT_NAME = 112.26, 114.34, 115.73   # «Уровень десять завершён», «Следующий игрок:», «Елена»
T_SCREAM = 119.05        # «…её крик»
T_ZERO_ON = 1e9          # (EP09 fx, unused)

# ---------------------------------------------------------------- shots
# src: still (scenes/<src>.png, else ../EP09/scenes, ../EP08/scenes, … ../EP02/illustrations), anim folder, "LIPSYNC" (+ lips=<base>) or "BLACK".
SHOTS = [
    # --- 1. «ОРИГИНАЛ ДОЛЖЕН УМЕРЕТЬ» (EP09's last frame) — THE PHONE ON ALEX_ZERO — HE DOES NOT MOVE
    dict(t=(0.00, 2.40), src="E9_cop_screen_close", phone="cop10", sub="top", cam=((.5, .52, 1.08), (.5, .52, 1.16)), fx=["handshake"]),
    dict(t=(2.40, 5.60), src="E10_cop_aim", anim=(0.0, 1.0), anim_start=2.6, anim_dur=T_AIM - 2.6, sub="bottom", cam=((.5, .46, 1.0), (.5, .45, 1.08))),
    dict(t=(5.60, 8.40), src="E10_zero_still", sub="bottom", cam=((.5, .42, 1.0), (.5, .41, 1.12)), fx=["redglow"]),
    # --- 2. «ПОЧЕМУ ИМЕННО ОН?» — «ПОТОМУ ЧТО ОН СОЗДАЛ НАС» — «Я СОЗДАЛ ИГРУ. НО НЕ ДЛЯ ЭТОГО»
    dict(t=(8.40, 11.10), src="LIPSYNC", lips="E10_a48", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1))),
    dict(t=(11.10, 15.40), src="LIPSYNC", lips="E10_cop", sub="bottom", cam=((.5, .4, 1.0), (.5, .39, 1.14))),
    dict(t=(15.40, 17.90), src="E10_zero_head", anim=(0.0, 1.0), anim_start=15.6, anim_dur=1.9, sub="bottom", cam=((.5, .42, 1.0), (.5, .41, 1.08)), fx=["redglow"]),
    dict(t=(17.90, 21.30), src="LIPSYNC", lips="E10_zero", sub="bottom", cam=((.5, .4, 1.06), (.5, .39, 1.2))),
    # --- 3. ALL THE PHONES LIGHT UP — HUNDREDS OF FACES — «ЧТО ЭТО ТАКОЕ?» — «ТЕ, КТО НЕ ПРОШЁЛ ИСПЫТАНИЯ» — THE HAND
    dict(t=(21.30, 23.55), src="E10_phones", screens="faces", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06)), fx=["tube"]),
    dict(t=(23.55, 26.10), src="E10_pov_zero", phone="faces", sub="top", cam=((.5, .56, 1.0), (.5, .58, 1.12))),
    dict(t=(26.10, 27.90), src="E10_pov_close", phone="faces", sub="top", cam=((.5, .56, 1.05), (.5, .56, 1.25)), fx=["glitch"]),
    dict(t=(27.90, 29.40), src="LIPSYNC", lips="E10_a48", sub="bottom", cam=((.5, .41, 1.08), (.5, .41, 1.16))),
    dict(t=(29.40, 32.75), src="LIPSYNC", lips="E10_cop", sub="bottom", cam=((.5, .39, 1.12), (.5, .38, 1.22))),
    dict(t=(32.75, 35.55), src="E10_hand48", anim=(0.0, 1.0), sub="bottom", cam=((.5, .45, 1.0), (.5, .43, 1.12)), fx=["glitch"]),
    # --- 4. «А ДЕНЬГИ? ЗАДАНИЯ? СТАКАН ВОДЫ?» — «МЫ ПРОВЕРЯЛИ…» — EP01: THE GLASS BY THE DOOR, THE 500 $
    dict(t=(35.55, 38.70), src="LIPSYNC", lips="E10_a48", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["handshake"]),
    dict(t=(38.70, 40.75), src="E10_zero_still", sub="bottom", cam=((.5, .41, 1.12), (.5, .41, 1.2)), fx=["redglow"]),
    dict(t=(40.75, 44.05), src="LIPSYNC", lips="E10_zero", sub="bottom", cam=((.5, .4, 1.0), (.5, .4, 1.12))),
    dict(t=(44.05, 46.40), src="LIPSYNC", lips="E10_zero", sub="bottom", cam=((.5, .38, 1.24), (.5, .38, 1.34)), fx=["redglow"]),
    dict(t=(46.40, 49.20), src="S05_place_glass", sub="bottom", cam=((.5, .55, 1.0), (.5, .58, 1.1)), fx=["memory"]),
    dict(t=(49.20, 51.65), src="S06_phone_bank", phone="bank10", sub="top", cam=((.5, .58, 1.0), (.5, .6, 1.08)), fx=["memory"]),
    dict(t=(51.65, 54.30), src="LIPSYNC", lips="E10_a48", sub="bottom", cam=((.5, .42, 1.04), (.5, .41, 1.14))),
    dict(t=(54.30, 56.70), src="LIPSYNC", lips="E10_zero", sub="bottom", cam=((.5, .4, 1.1), (.5, .4, 1.04))),
    # --- 5. THE PHONE HELD OUT — THE CHOICE — «ОСТАНОВИТЬ ИГРУ» — RED — «НЕДОСТАТОЧНО ПРАВ»
    dict(t=(56.70, 59.60), src="E10_cop_give", anim=(0.0, 1.0), anim_start=56.9, anim_dur=2.2, sub="bottom", cam=((.5, .46, 1.0), (.5, .45, 1.08))),
    dict(t=(59.60, 63.70), src="E10_pov_choice", phone="choice", sub="top", cam=((.5, .56, 1.0), (.5, .57, 1.08))),
    dict(t=(63.70, 64.80), src="E10_a48_look", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.12))),
    dict(t=(64.80, 67.45), src="E10_pov_choice", phone="choice", sub="top", cam=((.5, .57, 1.12), (.5, .56, 1.2)), fx=["shake_hits"]),
    dict(t=(67.45, 69.30), src="E10_pov_close", phone="choice", sub="top", cam=((.5, .56, 1.0), (.5, .56, 1.1)), fx=["shake_hits", "glitch"]),
    # --- 6. THE OFFICER, AFRAID — THE SISTER'S VOICE FROM EVERY PHONE — «ПОТОМУ ЧТО СОЗДАТЕЛЬ — НЕ ОН»
    dict(t=(69.30, 71.35), src="E10_copf_neutral", sub="bottom", cam=((.5, .4, 1.0), (.5, .39, 1.1)), fx=["handshake"]),
    dict(t=(71.35, 72.75), src="LIPSYNC", lips="E10_copf", sub="bottom", cam=((.5, .39, 1.1), (.5, .39, 1.16)), fx=["handshake"]),
    dict(t=(72.75, 75.40), src="E10_phones_b", screens="sis", sub="bottom", cam=((.5, .45, 1.06), (.5, .45, 1.0)), fx=["tube"]),
    dict(t=(75.40, 77.50), src="E10_pov_zero", phone="sis", sub="top", cam=((.5, .56, 1.0), (.5, .58, 1.12)), fx=["glitch"]),
    dict(t=(77.50, 80.45), src="LIPSYNC", lips="E8_feedc", sub="bottom", cam=((.5, .44, 1.0), (.5, .44, 1.1)), fx=["cctv", "glitch"]),
    # --- 7. ALEX_ZERO TURNS — THE VIDEO: ROOM 204 — THE SISTER AT THE COMPUTER — «ПРОЕКТ «АЛЕКС»» — «СОЗДАТЕЛЬ: ЕЛЕНА»
    dict(t=(80.45, 82.35), src="E10_zero_turn", anim=(0.0, 1.0), anim_start=80.6, anim_dur=0.6, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06)), fx=["shake_hits"]),
    dict(t=(82.35, 84.20), src="E10_pov_close", phone="video", sub="top", cam=((.5, .56, 1.0), (.5, .56, 1.08))),
    dict(t=(84.20, 87.70), src="E10_r204_wide", sub="bottom", cam=((.5, .45, 1.0), (.5, .42, 1.12)), fx=["cctv", "cap204"]),
    dict(t=(87.70, 89.40), src="E10_r204_wide", sub="bottom", cam=((.56, .4, 1.3), (.56, .38, 1.45)), fx=["cctv"]),
    dict(t=(89.40, 92.20), src="E10_r204_mon", monitor="proj10", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.1))),
    dict(t=(92.20, 94.60), src="E10_r204_mon_close", monitor="proj10", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["shake_hits"]),
    # --- 8. ALEX_ZERO STARTS TO DISAPPEAR — THE OFFICER ON HIS KNEES — THE SISTER INTO THE LENS: «ПОЗДРАВЛЯЮ, АЛЕКС»
    dict(t=(94.60, 96.65), src="E10_a48_look", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.06))),
    dict(t=(96.65, 98.40), src="E10_zero_vanish", anim=(0.0, 1.0), anim_start=96.8, anim_dur=1.6, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06)), fx=["glitch"]),
    dict(t=(98.40, 100.20), src="E10_cop_kneel", anim=(0.0, 1.0), anim_start=98.5, anim_dur=T_KNEES - 98.5, sub="bottom", cam=((.5, .45, 1.0), (.5, .46, 1.05)), fx=["shake_hits"]),
    dict(t=(100.20, 102.80), src="E10_sis_neutral", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["cctv"]),
    dict(t=(102.80, 105.40), src="LIPSYNC", lips="E10_sis", sub="bottom", cam=((.5, .42, 1.1), (.5, .42, 1.18)), fx=["cctv"]),
    dict(t=(105.40, 107.85), src="LIPSYNC", lips="E10_sis", sub="bottom", cam=((.5, .4, 1.28), (.5, .4, 1.38)), fx=["cctv"]),
    # --- 9. THE SCREEN DIES — «УРОВЕНЬ ДЕСЯТЬ ЗАВЕРШЁН» — «СЛЕДУЮЩИЙ ИГРОК: ЕЛЕНА» — HER SCREAM — DOOR 204 — CUT
    dict(t=(107.85, 110.70), src="E10_pov_end", phone="end", sub="top", cam=((.5, .56, 1.0), (.5, .56, 1.06))),
    dict(t=(110.70, 113.20), src="E10_pov_end", phone="end", sub="top", cam=((.5, .56, 1.06), (.5, .56, 1.14))),
    dict(t=(113.20, 116.90), src="E10_pov_end", phone="end", sub="top", cam=((.5, .56, 1.14), (.5, .56, 1.24)), fx=["shake_hits"]),
    dict(t=(116.90, 118.85), src="E10_a48_end", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1)), fx=["handshake"]),
    dict(t=(118.85, CUT_TO_BLACK), src="E10_door204", anim=(0.0, 1.0), anim_start=118.9, anim_dur=2.8, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["tube", "shake_hits"]),
    dict(t=(CUT_TO_BLACK, END), src="BLACK"),
]

# ---------------------------------------------------------------- lip-sync windows (ALEX_48 / officer / ALEX_ZERO / sister)
LIPW = [(9.78, 10.75), (12.80, 14.64), (18.05, 20.76), (28.05, 29.07), (29.59, 31.17), (35.70, 38.36), (40.88, 43.73), (44.18, 45.92),
        (51.91, 53.87), (54.64, 55.49), (71.43, 72.58), (77.60, 80.01), (103.09, 107.58)]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
LIP_WINDOWS = LIPW


def _envelope():
    """RMS of the VO per video frame (cached in timeline/vo_envelope.json so the build is reproducible)."""
    cache = os.path.join(ROOT, "timeline", "vo_envelope.json")
    if os.path.exists(cache): return json.load(open(cache))
    import numpy as np
    mp3 = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.float32); hop = 48000 // FPS
    env = [round(float(np.sqrt(np.mean(x[i:i + hop] ** 2))), 5) for i in range(0, len(x) - hop, hop)]
    json.dump(env, open(cache, "w"))
    return env


def lipsync():
    env = _envelope(); peak = sorted(env)[int(len(env) * 0.97)]
    out = []
    for a, b in LIP_WINDOWS:
        f0, f1 = int(a * FPS), int(b * FPS); prev = None
        for f in range(f0, f1, 2):                         # 15 shape changes per second at most
            e = max(env[f:f + 2]) / peak
            s = "neutral" if e < 0.08 else ("open" if e > 0.55 else ("ee" if (f // 2) % 2 else "oo") if e > 0.25 else ("oo" if (f // 2) % 3 == 0 else "ee"))
            if s != prev: out.append((round(f / FPS, 3), s)); prev = s
        out.append((round(b, 3), "neutral"))
    return out


LIPSYNC = lipsync()


def lip_at(t):
    v = "neutral"
    for tt, vv in LIPSYNC:
        if t >= tt: v = vv
    return v


# ---------------------------------------------------------------- screens (text drawn in code, series fonts)
PHONE_CLOCK = "02:56"            # a minute after EP09's phones (02:55)
MSG_FOUND, MSG_CHECK, MSG_DIE = "Создатель обнаружен", "Начать последнюю проверку", "Оригинал должен умереть"
MSG_KILL, MSG_STOP, MSG_DENY = "Уничтожить оригинал", "Остановить игру", "Недостаточно прав"
MSG_PROJ, MSG_CREATOR = "Проект «Алекс»", "Создатель: Елена"
MSG_LVL, MSG_NEXT = "Уровень десять завершён", "Следующий игрок: Елена"
COP10 = dict(clock=PHONE_CLOCK, t_on=-9, t1=-9, t2=-9, t3=-1, m1=MSG_FOUND, m2=MSG_CHECK, m3=MSG_DIE)   # EP09's final screen, already red
CHOICE10 = dict(t1=60.64, t2=62.15, t_tap=T_TAP, t_red=T_RED, t_deny=T_DENY)
END10 = dict(t_off=T_OFF, t1=T_LVL, t2=T_NEXT, t_name=T_NEXT_NAME)
PHONE = {"cop10": [(0, ("cop9", COP10))],
         "faces": [(0, ("faces10", dict(t_on=T_ON, t_many=T_MANY)))],
         "bank10": [(0, ("bank_app", (1e9, 500, 500, [("Зачисление", 500)])))],   # EP01's bank screen: +500 $
         "choice": [(0, ("choice10", CHOICE10))],
         "sis": [(0, ("sis10", dict(t_on=T_SIS_ON, lips=False)))],
         "video": [(0, ("video10", dict(t_on=T_VIDEO, t_cap=T_CAP)))],
         "end": [(0, ("end10", END10))]}
SCREENS_ON = {"faces": T_ON, "sis": T_SIS_ON}   # phones in the wide shots stay dark until these moments
SCREEN_TINT = {}
REC_STAMP = "ПТ 06.11"

HITS = [T_AIM, T_TAP, T_RED, T_DENY, T_TURN, T_NAME, T_KNEES, T_NEXT_NAME, T_SCREAM]
BLACKOUT = None
FLASHES = [(T_ON, "cold"), (T_DENY, "red"), (T_SIS_ON, "cold"), (T_VIDEO, "cold"), (T_NAME, "red"), (T_VANISH, "cold"), (T_NEXT_NAME, "red"), (T_SCREAM, "white")]
COUNTDOWN = None
ENDCARD = None
BIG_SUBS = ("«!Недостаточно прав!».", "«Следующий игрок: !Елена!».")

# ---------------------------------------------------------------- subtitles (*word* = yellow, !word! = red, ¡ = a literal "!")
# Only words that are in the voiceover; at most two lines each. Starts/ends from the phrase timings.
SUBS = [
    (0.12, 2.00, "«!Оригинал должен умереть!»."),
    (2.57, 5.50, "Полицейский направил телефон на Алекса с номером *ноль*."),
    (6.07, 7.60, "Тот даже *не пошевелился*."),
    (8.63, 9.62, "Я спросил:"),
    (9.78, 10.95, "«*Почему именно он?*»"),
    (11.26, 12.45, "Полицейский ответил:"),
    (12.80, 14.90, "«Потому что он !создал нас!»."),
    (15.59, 17.75, "Алекс-ноль медленно *поднял голову*."),
    (18.05, 19.55, "«Я *создал игру*."),
    (19.68, 21.10, "Но !не для этого!»."),
    (21.54, 23.55, "Вдруг *все телефоны* загорелись."),
    (23.64, 26.00, "На экранах появились !сотни лиц!."),
    (26.21, 27.70, "Каждое было *моим*."),
    (28.05, 29.30, "«*Что это такое?*»"),
    (29.59, 31.30, "«Те, кто !не прошёл испытания!», —"),
    (31.40, 32.75, "ответил полицейский."),
    (32.90, 35.50, "Я посмотрел на свою *исчезающую руку*."),
    (35.70, 38.60, "«А деньги? Задания? *Стакан воды?*»"),
    (39.07, 40.60, "Алекс-ноль произнёс:"),
    (40.88, 43.95, "«Мы проверяли, способен ли ты *отказаться*."),
    (44.18, 46.30, "Каждый раз ты выбирал !награду!»."),
    (46.70, 49.15, "Я вспомнил, как поставил *стакан у двери*"),
    (49.31, 51.60, "и как получил *пятьсот долларов*."),
    (51.91, 54.10, "«Но я *не знал*, что происходит»."),
    (54.64, 55.60, "«*Теперь знаешь*», —"),
    (55.74, 56.70, "ответил он."),
    (56.89, 58.70, "Полицейский протянул мне *телефон*."),
    (58.76, 60.50, "На экране было *два варианта*:"),
    (60.64, 62.00, "«!Уничтожить оригинал!»,"),
    (62.15, 63.60, "«*Остановить игру*»."),
    (63.98, 65.80, "Я нажал «*Остановить игру*»,"),
    (65.91, 67.35, "и экран стал !красным!."),
    (67.53, 69.20, "«!Недостаточно прав!»."),
    (69.35, 71.30, "Полицейский впервые *испугался*."),
    (71.43, 72.70, "«!Этого не должно быть¡!»"),
    (72.82, 74.38, "Вдруг заговорила *сестра*."),
    (74.45, 77.20, "Её голос раздался *из всех телефонов*."),
    (77.60, 80.30, "«Потому что создатель — !не он!»."),
    (80.60, 82.38, "Алекс-ноль резко *обернулся*."),
    (82.44, 84.15, "На экранах появилось *видео*."),
    (84.29, 85.78, "*Комната двести четыре*."),
    (85.86, 87.68, "За столом сидела *моя сестра*."),
    (87.77, 89.35, "Перед ней стоял компьютер."),
    (89.44, 90.95, "На мониторе было написано:"),
    (91.05, 92.15, "«*Проект „Алекс“*»."),
    (92.27, 94.40, "«Создатель: !Елена!»."),
    (94.77, 96.65, "Я посмотрел на Алекса-ноль."),
    (96.78, 98.30, "Он начал !исчезать!."),
    (98.47, 100.10, "Полицейский упал *на колени*,"),
    (100.19, 102.60, "а сестра посмотрела *прямо в камеру*."),
    (103.09, 104.65, "«*Поздравляю, Алекс¡*"),
    (104.80, 107.80, "Ты наконец дошёл до !последнего уровня!»."),
    (108.39, 109.88, "Экран телефона *погас*,"),
    (109.97, 112.05, "а затем появилась новая надпись:"),
    (112.26, 114.20, "«*Уровень десять завершён*»."),
    (114.34, 116.80, "«Следующий игрок: !Елена!»."),
    (117.16, 118.98, "И вдруг я услышал её !крик!"),
    (119.02, 121.73, "из-за двери *комнаты двести четыре*."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.05, "delete_alarm", 0.5), (0.3, "sting_soft", 0.4), (2.7, "cloth", 0.6), (3.6, "whoosh", 0.4), (T_AIM, "sting", 0.6), (T_AIM, "notify_bad", 0.5)]
    + [(6.2, "breath", 0.35), (8.5, "boom_tail", 0.3), (11.2, "heavy_step", 0.25), (14.65, "sting", 0.55), (15.7, "cloth", 0.4)]
    + [(17.6, "breath", 0.4), (20.8, "boom_tail", 0.45)]
    + [(T_ON - 0.05, "phones_chorus", 0.9), (T_ON, "faces_swarm", 1.0), (23.6, "glitch", 0.4), (24.6, "shimmer", 0.5), (26.2, "glitch", 0.5), (26.25, "sting", 0.5)]
    + [(29.55, "voice_static", 0.4), (32.9, "dissolve", 0.7), (33.6, "wires_hum", 0.5)]
    + [(38.8, "sting_soft", 0.45), (44.2, "boom_tail", 0.4)]
    + [(46.45, "shimmer", 0.45), (47.6, "glass", 0.55), (49.25, "coin", 0.6), (49.6, "notify", 0.45), (51.5, "shimmer", 0.35)]
    + [(54.5, "sting_soft", 0.4), (56.95, "heavy_step", 0.5), (57.6, "heavy_step", 0.45), (58.3, "cloth", 0.4)]
    + [(60.64, "notify_bad", 0.8), (62.15, "notify", 0.7), (T_TAP, "tap", 1.0), (T_TAP + 0.05, "button_press", 0.6)]
    + [(T_RED, "delete_alarm", 0.7), (T_RED, "sting", 0.6), (T_DENY, "denied", 1.0), (T_DENY + 0.02, "glitch", 0.7)]
    + [(69.4, "breath", 0.5), (70.2, "sting_soft", 0.4)]
    + [(T_SIS_ON - 0.1, "phones_chorus", 0.6), (T_SIS_ON, "voice_static", 1.0), (75.4, "glitch", 0.5), (77.5, "voice_static", 1.0), (77.55, "sting", 0.45)]
    + [(T_TURN - 0.1, "whoosh", 0.8), (T_VIDEO, "rec_start", 0.7), (T_VIDEO + 0.05, "glitch", 0.5), (T_CAP, "sting_soft", 0.5)]
    + [(89.5, "wires_hum", 0.4), (T_PROJ, "type_lock", 0.6), (T_CREATOR, "type_lock", 0.5), (T_NAME, "attempt_hit", 1.0), (T_NAME, "sting", 0.8)]
    + [(94.8, "breath", 0.4), (T_VANISH, "dissolve", 1.0), (97.3, "number_burn", 0.5)]
    + [(98.6, "whoosh", 0.5), (T_KNEES, "knee_thud", 1.0), (100.25, "voice_static", 0.5), (100.5, "sting_soft", 0.45)]
    + [(103.0, "voice_static", 0.7), (107.7, "boom_tail", 0.4)]
    + [(T_OFF, "crt_off", 0.9), (110.9, "glitch", 0.4), (T_LVL, "type_lock", 0.6), (T_LVL + 0.1, "notify_bad", 0.6)]
    + [(T_NEXT, "type_lock", 0.6), (T_NEXT_NAME, "next_player", 1.0), (T_NEXT_NAME, "attempt_hit", 0.8)]
    + [(117.2, "breath", 0.5), (T_SCREAM, "scream", 1.0), (T_SCREAM + 0.02, "sting", 0.7), (120.2, "door_creak", 0.35), (CUT_TO_BLACK, "final_hit", 1.0)]
)
HUM = []
CORRIDOR = [(118.85, CUT_TO_BLACK)]       # the hotel corridor's air under the last shot
MONHUM = []
FLAT = [(0.0, 84.2), (94.6, 100.2), (107.85, 118.85)]   # flat 47 at night: the fridge hum, a faint clock (not under room 204)
# music: picks up on EP09's cut, low under the dialogue, swells with the phones and the faces, pulls right back under «Мы проверяли»,
# climbs through the choice to the red screen, drops for the sister's voice, rises on the video and the name, sinks under
# «Поздравляю», climbs from the dead screen to «Елена», and stops dead on the cut after the scream
MUSIC = [(0, .6), (2.4, .45), (5.6, .35), (11.1, .4), (14.6, .55), (17.9, .4), (21.3, .55), (22.6, .85), (26.1, .75), (27.9, .45),
         (32.8, .55), (35.6, .4), (40.8, .35), (46.4, .3), (51.7, .4), (56.7, .55), (60.6, .65), (63.7, .75), (66.4, .9), (67.5, .97),
         (69.3, .45), (72.8, .5), (77.5, .4), (80.5, .65), (84.2, .7), (89.4, .75), (93.3, .95), (94.6, .5), (96.8, .75), (99.3, .85),
         (100.2, .35), (107.8, .45), (109.2, .3), (112.2, .6), (115.7, .95), (116.9, .55), (119.0, .9), (CUT_TO_BLACK, 1.0)]
MUSIC_TAIL = False                         # no end card: dead silence after the cut
BELLS = [(0.1, 880.0), (T_ON, 987.8), (T_PROJ, 784.0), (T_NAME, 932.3), (100.3, 880.0), (T_NEXT_NAME, 987.8)]
RISER = (110.7, CUT_TO_BLACK)


def check():
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    assert SHOTS[0]["t"][0] == 0 and SHOTS[-1]["t"][1] == END
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)
    assert SUBS[-1][1] <= CUT_TO_BLACK + 1e-9
    assert all(0 <= t < END for t, _, _ in SFX)
    for s in SHOTS:
        assert s.get("phone") in (None, *PHONE) and s.get("screens") in (None, *PHONE), s
        assert s["t"][1] - s["t"][0] <= 4.5, ("shot too long", s["t"])
    lip = [s["t"] for s in SHOTS if s["src"] == "LIPSYNC"]
    for a, b in LIPW:
        assert all(any(x <= f / FPS < y for x, y in lip) for f in range(int(a * FPS), int(b * FPS))), ("lip window not covered", a, b)
    # no on-screen message before its words
    assert CHOICE10["t1"] >= 60.64 and CHOICE10["t2"] >= 62.15 and CHOICE10["t_deny"] >= 67.53
    assert T_PROJ >= 91.05 and T_CREATOR >= 92.27 and T_NAME >= 93.35 and T_LVL >= 112.26 and T_NEXT >= 114.34 and T_NEXT_NAME >= 115.73


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, subtitles=SUBS, sfx=SFX, flat=FLAT, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep10_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
