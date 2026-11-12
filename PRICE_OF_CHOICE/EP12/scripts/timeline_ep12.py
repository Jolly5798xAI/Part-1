"""EP12 «ПЕРВОЕ ИСПЫТАНИЕ» — editing timeline (single source of truth). Same format as EP11 (../EP11/scripts/timeline_ep11.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
The approved MP3 is 110.92 s (speech 0.15 – 110.92 s, no silent tail): 20.9 s over the 75–90 s target — reported, not altered.
Phrase times: timeline/transcript_words.json (Whisper small via sherpa-onnx, cut at the VO's own pauses ≥ 0.09 s, silencedetect −36 dB);
verified text: docs/EP12_transcript.txt.

EP12 opens the second EP11 ended: the computer in room 204 turned to ALEX_48, the original's face on it with «Оригинал проснулся» (EP11's
very last frame, E11_face_close, reused unchanged) — same place, same red light, no recap, no time jump. The accident is a recording the
system shows (REC look); it breaks off before anything happens to the person on the road. The episode ends dead on «Не верь мне»:
ELENA_204 beside ALEX_48 and ELENA_APARTMENT on the side monitor's live feed both mouth it (the narrator voices it — no second voice).

Production names (never shown): ALEX_48, ALEX_ORIGINAL_CONSCIOUSNESS (only the face on the turned screen, phone_ui.draw_face12 — never a 3D
figure, never ALEX_ZERO), ELENA_204, ELENA_APARTMENT (identical model). ALEX_OLD_POLICE and ALEX_49 were deleted in EP11 — not on screen.
ALEX_48's left hand keeps disappearing until the handover (T_STOP); from then on it is whole.

`python3 scripts/timeline_ep12.py` checks the timeline and writes timeline/ep12_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30
VO_END = 110.92
END = 110.92             # the video ends with the MP3 on the last word — no black tail, no end card
CUT_TO_BLACK = END
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- key moments (VO clock)
T_HOOK_END = 1.9                       # EP11's «Оригинал проснулся» clears off the screen
T_BLINK0, T_BLINK1 = 2.75, 3.3         # «…открыл глаза…»: the face blinks shut, then the eyes open on the words
T_FLASH = 17.3                         # «Экран вспыхнул»
T_ROAD = 18.28                         # «Передо мной появилась дорога»
T_VIB = 25.76                          # «Телефон завибрировал»
T_TASK1, T_TASK2, T_TASK3 = 27.20, 28.38, 29.60   # «Первое задание» · «Не тормози» · «Награда — пятьсот долларов»
T_PERSON = 32.16                       # «Впереди появился человек»
T_BRAKE = 34.2                         # «Я нажал на тормоз» — the foot hits the pedal on «нажал»
T_NOSTOP = 35.17                       # «Но машина не остановилась»
T_CUT = 37.64                          # «Запись оборвалась» — the recording dies (before anything happens to the person)
T_SMIRK0, T_SMIRK1 = 43.66, 46.0       # «Оригинальный Алекс усмехнулся»
T_REC2, T_REC2_END = 48.49, 50.45      # «На экране появилась новая запись» (on the turned screen, then full frame)
T_CMD = 53.83                          # «Повторить испытание» typed on the words
T_GRID, T_GRID_CYAN, T_GRID_END = 64.79, 66.45, 67.15   # «Сорок семь копий выбрали деньги» (47 red faces); «А ты нажал на тормоз»: back to the face
T_SCARED = 75.30                       # «Впервые оригинал выглядел испуганным»
T_RELEASE = 81.6                       # «Вдруг кресло Елены раскрылось» — the cuffs spring on «раскрылось»
T_FALL = 82.96                         # «Крепления упали на пол»
T_ADMIN = 84.44                        # «На мониторе появилось:»
T_HAND = 85.91                         # «Передача управления»
T_NEWADM, T_48 = 87.49, 88.92          # «Новый администратор:» · «сорок восемь»
T_RAISE = 90.29                        # «Я поднял руку»
T_STOP = 91.57                         # «Она перестала исчезать»
T_SIDE_ON = 93.6                       # «…загорелся второй экран»
T_LIVE = 94.99                         # «На нём был прямой эфир»
T_FLAT = 96.80                         # «Моя квартира»
T_TURN = 100.05                        # «Я обернулся»
T_TWO = 105.26                         # «Обнаружены две Елены»
T_LAST = 110.06                        # «Не верь мне»
T_ERASE = T_CUT

# ---------------------------------------------------------------- shots
# src: still (scenes/<src>.png, else ../EP11/scenes, ../EP10/scenes …), anim folder, "LIPSYNC" (+ lips=<base>) or "BLACK".
# monitor=<state>: phone_ui.draw_monitor on the still's screen quad (E11_face* quads are EP11's, the side monitor's are EP12's).
# phone=<state>: phone_ui.draw_screen on the still's phone quad.
SHOTS = [
    # --- 1. «ОРИГИНАЛ ПРОСНУЛСЯ» (EP11's last frame) — HE OPENS HIS EYES — «СОРОК ВОСЕМЬ. ТЫ ДОЛЖЕН ИСЧЕЗНУТЬ» — HE STEPS BACK
    dict(t=(0.00, 2.05), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.2), (.5, .46, 1.24)), fx=["shake_hits"]),
    dict(t=(2.05, 4.65), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.0), (.5, .44, 1.14))),
    dict(t=(4.65, 6.25), src="E11_face", monitor="face12", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.08)), fx=["redglow"]),
    dict(t=(6.25, 8.95), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.04), (.5, .46, 1.2)), fx=["shake_hits"]),
    dict(t=(8.95, 10.35), src="E12_step", anim=(0.0, 1.0), anim_start=9.3, anim_dur=0.95, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06)), fx=["handshake"]),
    dict(t=(10.35, 11.40), src="LIPSYNC", lips="E12_a48", sub="bottom", cam=((.5, .42, 1.04), (.5, .42, 1.12)), fx=["redglow"]),
    dict(t=(11.40, 14.05), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.0), (.5, .46, 1.16))),
    # --- 2. «НЕ СЛУШАЙ ЕГО!» — THE SCREEN FLASHES — THE ACCIDENT, AS A RECORDING
    dict(t=(14.05, 16.85), src="LIPSYNC", lips="E11_sisr", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["redglow", "shake_hits"]),
    dict(t=(16.85, 18.20), src="E11_face", monitor="face12", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.14))),
    dict(t=(18.20, 20.00), src="E12_road", anim=(0.0, 1.0), sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["rec", "rain"]),
    dict(t=(20.00, 21.45), src="E12_wiper", anim=(0.0, 1.0), sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.04)), fx=["rec", "rain"]),
    dict(t=(21.45, 22.80), src="E12_cabin_alex", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.08)), fx=["rec", "rain", "drive"]),
    dict(t=(22.80, 25.50), src="E12_cabin_sis", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.1)), fx=["rec", "rain", "drive"]),
    # --- 3. THE PHONE BUZZES — «ПЕРВОЕ ЗАДАНИЕ» «НЕ ТОРМОЗИ» «НАГРАДА — ПЯТЬСОТ ДОЛЛАРОВ»
    dict(t=(25.50, 27.10), src="E12_phone", phone="task12", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["rec", "vibrate", "drive"]),
    dict(t=(27.10, 29.50), src="E12_phone_close", phone="task12", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.05)), fx=["rec", "drive"]),
    dict(t=(29.50, 32.00), src="E12_phone_close", phone="task12", sub="top", cam=((.5, .54, 1.05), (.5, .58, 1.12)), fx=["rec", "drive"]),
    # --- 4. A PERSON IN THE ROAD — THE BRAKE — THE CAR DOES NOT STOP — THE RECORDING BREAKS OFF
    dict(t=(32.00, 33.85), src="E12_ahead", anim=(0.0, 1.0), sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["rec", "rain", "drive"]),
    dict(t=(33.85, 35.10), src="E12_brake", anim=(0.0, 1.0), anim_start=33.95, anim_dur=0.55, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["rec", "shake_hits"]),
    dict(t=(35.10, 37.55), src="E12_skid", anim=(0.0, 1.0), sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["rec", "rain", "handshake"]),
    dict(t=(37.55, 38.05), src="BLACK", sub="bottom", fx=["static"]),
    # --- 5. «КТО ОТПРАВИЛ СООБЩЕНИЕ?» — SHE SAYS NOTHING — THE ORIGINAL SMIRKS — «А ТЕПЕРЬ ПОКАЖИ ЕМУ ОСТАЛЬНОЕ»
    dict(t=(38.05, 40.60), src="E12_sis_down", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1)), fx=["redglow"]),
    dict(t=(40.60, 42.45), src="LIPSYNC", lips="E12_a48", sub="bottom", cam=((.5, .42, 1.08), (.5, .42, 1.18)), fx=["handshake"]),
    dict(t=(42.45, 43.55), src="E12_sis_down", sub="bottom", cam=((.5, .4, 1.14), (.5, .4, 1.2)), fx=["redglow"]),
    dict(t=(43.55, 45.95), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.0), (.5, .46, 1.12))),
    dict(t=(45.95, 48.35), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.12), (.5, .46, 1.22)), fx=["shake_hits"]),
    # --- 6. THE OTHER RECORDING — SHE TYPES «ПОВТОРИТЬ ИСПЫТАНИЕ» — «ТЫ ЗАПУСКАЛА ЕГО СНОВА?» — SHE CRIES
    dict(t=(48.35, 50.45), src="E11_face", monitor="face12", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.12))),
    dict(t=(50.45, 52.25), src="E12_rec_wide", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["rec"]),
    dict(t=(52.25, 53.75), src="E12_rec_mon", monitor="retry12", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["rec"]),
    dict(t=(53.75, 55.60), src="E12_rec_mon_close", monitor="retry12", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["rec"]),
    dict(t=(55.60, 57.45), src="LIPSYNC", lips="E12_a48", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["redglow", "handshake"]),
    dict(t=(57.45, 59.05), src="E12_sis_cry", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1)), fx=["redglow"]),
    dict(t=(59.05, 62.50), src="LIPSYNC", lips="E12_sist", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12))),
    # --- 7. «СОРОК СЕМЬ КОПИЙ ВЫБРАЛИ ДЕНЬГИ. А ТЫ НАЖАЛ НА ТОРМОЗ» — THE HAND — «ЗНАЧИТ, Я ПРОШЁЛ ИСПЫТАНИЕ?» — «ДА» — HE IS AFRAID
    dict(t=(62.50, 64.60), src="E11_face", monitor="face12", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.1))),
    dict(t=(64.60, 67.10), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.0), (.5, .46, 1.1))),
    dict(t=(67.10, 69.05), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.1), (.5, .46, 1.2)), fx=["shake_hits"]),
    dict(t=(69.05, 71.60), src="E12_hand", anim=(0.0, 1.0), anim_start=69.1, anim_dur=2.4, sub="bottom", cam=((.5, .45, 1.0), (.5, .43, 1.12)), fx=["glitch", "redglow"]),
    dict(t=(71.60, 74.20), src="LIPSYNC", lips="E12_a48", sub="bottom", cam=((.5, .42, 1.08), (.5, .41, 1.2))),
    dict(t=(74.20, 75.10), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.16), (.5, .46, 1.2))),
    dict(t=(75.10, 77.70), src="E11_face_close", monitor="face12", sub="top", cam=((.5, .46, 1.0), (.5, .46, 1.14)), fx=["shake_hits"]),
    dict(t=(77.70, 80.60), src="E11_face", monitor="face12", sub="top", cam=((.5, .45, 1.04), (.5, .45, 1.16)), fx=["handshake"]),
    # --- 8. THE CHAIR LETS HER GO — «ПЕРЕДАЧА УПРАВЛЕНИЯ» — «НОВЫЙ АДМИНИСТРАТОР: СОРОК ВОСЕМЬ» — THE HAND STOPS DISAPPEARING
    dict(t=(80.60, 82.85), src="E12_cuffs", anim=(0.0, 1.0), anim_start=81.2, anim_dur=1.3, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["redglow", "shake_hits"]),
    dict(t=(82.85, 84.35), src="E12_fall", anim=(0.0, 1.0), anim_start=82.9, anim_dur=1.1, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["redglow"]),
    dict(t=(84.35, 85.85), src="E11_face_close", monitor="admin12", sub="top", cam=((.5, .46, 1.0), (.5, .46, 1.06))),
    dict(t=(85.85, 87.40), src="E11_face_close", monitor="admin12", sub="top", cam=((.5, .46, 1.06), (.5, .46, 1.12))),
    dict(t=(87.40, 90.15), src="E11_face_close", monitor="admin12", sub="top", cam=((.5, .5, 1.1), (.5, .52, 1.24)), fx=["shake_hits"]),
    dict(t=(90.15, 91.50), src="E12_raise", anim=(0.0, 1.0), anim_start=90.3, anim_dur=0.9, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06))),
    dict(t=(91.50, 92.90), src="E12_hand_stop", anim=(0.0, 1.0), anim_start=91.55, anim_dur=1.25, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.08))),
    # --- 9. THE SECOND SCREEN — LIVE FROM FLAT 47 — ELENA AT THE TABLE — HE TURNS: ELENA IS STILL BESIDE HIM
    dict(t=(92.90, 94.90), src="E12_side", monitor="live12", sub="bottom", cam=((.5, .45, 1.0), (.5, .46, 1.1))),
    dict(t=(94.90, 96.70), src="E12_side_close", monitor="live12", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06))),
    dict(t=(96.70, 98.10), src="E12_side_close", monitor="live12", sub="bottom", cam=((.5, .5, 1.06), (.5, .5, 1.14))),
    dict(t=(98.10, 99.95), src="E12_flat_close", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.1)), fx=["live"]),
    dict(t=(99.95, 100.95), src="E12_turn", anim=(0.0, 1.0), anim_start=100.0, anim_dur=0.75, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.04)), fx=["handshake"]),
    dict(t=(100.95, 103.40), src="E12_beside", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["handshake"]),
    # --- 10. «ОБНАРУЖЕНЫ ДВЕ ЕЛЕНЫ» — BOTH SAY «НЕ ВЕРЬ МНЕ» — END ON THE LAST WORD
    dict(t=(103.40, 105.15), src="E12_side_close", monitor="live12", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.06))),
    dict(t=(105.15, 107.25), src="E12_side_close", monitor="live12", sub="top", cam=((.5, .5, 1.06), (.5, .5, 1.16)), fx=["shake_hits"]),
    dict(t=(107.25, 110.00), src="E12_two_neutral", monitor="live12", sub="top", cam=((.5, .42, 1.0), (.5, .4, 1.1))),
    dict(t=(110.00, END), src="LIPSYNC", lips="E12_two", monitor="live12", sub="top", cam=((.5, .4, 1.1), (.5, .4, 1.14)), fx=["shake_hits"]),
]

# ---------------------------------------------------------------- lip-sync windows (3D stills) + the original's face (UI) + the feed (UI)
LIPW = [(10.50, 11.13), (15.38, 16.46), (40.77, 42.02), (55.73, 57.04), (59.20, 62.13), (71.78, 72.35), (72.50, 73.77), (110.06, 110.92)]
LIPW_UI = [(6.39, 7.26), (7.51, 8.74), (11.64, 12.22), (12.31, 13.70), (46.09, 47.78), (67.21, 68.61), (74.44, 74.73), (77.86, 78.63), (78.77, 80.24)]
LIPW_FEED = [(110.06, 110.92)]          # ELENA_APARTMENT mouths «Не верь мне» on the feed at the same time as ELENA_204

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
LIP_WINDOWS = sorted(set(LIPW + LIPW_UI + LIPW_FEED))


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
PHONE_CLOCK = "23:48"            # the night of the accident (three years ago; the hospital recording in EP11 is 06.11.2023, 02:54)
MSG_TASK1, MSG_TASK2, MSG_TASK3 = "Первое задание", "Не тормози", "Награда — пятьсот долларов"
MSG_CMD = "Повторить испытание"
MSG_HAND, MSG_NEWADM = "Передача управления", "Новый администратор:"
MSG_LIVE, MSG_FLAT = "Прямой эфир", "Квартира 47"
MSG_TWO = "Обнаружены две Елены"
TASK12 = dict(clock=PHONE_CLOCK, date="воскресенье, 5 ноября", t_on=T_VIB, t1=T_TASK1, t2=T_TASK2, t3=T_TASK3, m1=MSG_TASK1, m2=MSG_TASK2, m3=MSG_TASK3)
PHONE = {"task12": [(0, ("task12", TASK12))]}
SCREENS_ON = {}
SCREEN_TINT = {}
REC_STAMP = None                 # the recordings show REC and a running time only (no date: when they were made is not said)

HITS = [0.1, T_BLINK1, 8.2, T_FLASH, T_BRAKE, T_CUT, 47.0, T_GRID, T_SCARED, T_RELEASE, T_48, T_STOP, T_TWO, T_LAST]
BLACKOUT = None
FLASHES = [(T_BLINK1, "cold"), (T_FLASH, "white"), (T_ROAD, "white"), (T_CUT, "white"), (T_REC2, "cold"), (T_RELEASE, "cold"), (T_48, "cold"), (T_SIDE_ON, "cold"), (T_TWO, "red")]
COUNTDOWN = None
ENDCARD = None
BIG_SUBS = ()

# ---------------------------------------------------------------- subtitles (*word* = yellow, !word! = red, ¡ = a literal "!")
SUBS = [
    (0.15, 1.95, "«!Оригинал проснулся!»."),
    (2.14, 4.55, "На экране открыл глаза *настоящий Алекс*."),
    (4.81, 6.15, "Он посмотрел на меня."),
    (6.39, 7.40, "«*Сорок восемь*."),
    (7.51, 8.90, "Ты должен !исчезнуть!»."),
    (9.39, 10.30, "Я отступил."),
    (10.50, 11.40, "«*Почему?*»"),
    (11.64, 13.95, "«Потому что ты *вспомнил аварию*»."),
    (14.18, 15.30, "Елена закричала:"),
    (15.38, 16.80, "«!Не слушай его¡!»"),
    (17.05, 18.15, "Экран *вспыхнул*."),
    (18.28, 19.95, "Передо мной появилась *дорога*."),
    (20.08, 21.40, "Ночь. *Дождь*."),
    (21.53, 22.75, "За рулём сидел *я*,"),
    (22.86, 25.45, "на пассажирском сиденье — *Елена*."),
    (25.76, 27.05, "Телефон *завибрировал*."),
    (27.20, 29.45, "«*Первое задание*». «!Не тормози!»."),
    (29.60, 31.95, "«Награда — *пятьсот долларов*»."),
    (32.16, 33.80, "Впереди появился !человек!."),
    (33.92, 35.05, "Я нажал *на тормоз*."),
    (35.17, 37.50, "Но машина !не остановилась!."),
    (37.64, 38.65, "Запись *оборвалась*."),
    (38.81, 40.50, "Я посмотрел на Елену."),
    (40.77, 42.40, "«Кто *отправил сообщение?*»"),
    (42.61, 43.50, "Она *молчала*."),
    (43.66, 45.90, "Оригинальный Алекс *усмехнулся*."),
    (46.09, 48.30, "«А теперь покажи ему *остальное*»."),
    (48.49, 50.40, "На экране появилась *новая запись*."),
    (50.52, 52.20, "Елена сидела за компьютером."),
    (52.31, 53.70, "Она вводила команду:"),
    (53.83, 55.55, "«!Повторить испытание!»."),
    (55.73, 57.40, "«Ты запускала его *снова?*»"),
    (57.60, 59.00, "Елена *заплакала*."),
    (59.20, 62.45, "«Я пыталась найти версию, которая *спасёт нас обоих*»."),
    (62.67, 64.55, "Оригинальный Алекс произнёс:"),
    (64.79, 67.05, "«!Сорок семь копий! выбрали деньги."),
    (67.21, 69.00, "А ты *нажал на тормоз*»."),
    (69.25, 71.55, "Я посмотрел на *исчезающую руку*."),
    (71.78, 74.15, "«Значит, я *прошёл испытание?*»"),
    (74.44, 75.05, "«*Да*»."),
    (75.30, 77.65, "Впервые оригинал выглядел !испуганным!."),
    (77.86, 80.55, "«И поэтому *система выбрала тебя*»."),
    (80.90, 82.80, "Вдруг кресло Елены *раскрылось*."),
    (82.96, 84.30, "Крепления упали на пол."),
    (84.44, 85.80, "На мониторе появилось:"),
    (85.91, 87.35, "«*Передача управления*»."),
    (87.49, 90.10, "«Новый администратор: *сорок восемь*»."),
    (90.29, 91.45, "Я поднял руку."),
    (91.57, 92.85, "Она *перестала исчезать*."),
    (92.97, 94.85, "Но затем загорелся *второй экран*."),
    (94.99, 96.65, "На нём был *прямой эфир*."),
    (96.80, 98.05, "*Моя квартира*."),
    (98.19, 99.90, "За столом сидела !Елена!."),
    (100.05, 100.95, "Я обернулся."),
    (101.01, 103.35, "Елена *всё ещё стояла* рядом со мной."),
    (103.50, 105.10, "На экране появилась надпись:"),
    (105.26, 107.20, "«!Обнаружены две Елены!»."),
    (107.37, 109.95, "А затем обе *одновременно* сказали:"),
    (110.06, END, "«!Не верь мне!»."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.05, "attempt_hit", 0.5), (0.1, "voice_static", 0.5), (1.6, "glitch", 0.4), (T_BLINK1 - 0.3, "eyes_open", 0.9), (T_BLINK1, "sting_soft", 0.5)]
    + [(6.3, "voice_static", 0.6), (8.2, "sting", 0.5), (9.35, "step", 0.9), (9.75, "step", 0.8), (11.55, "voice_static", 0.6), (13.8, "boom_tail", 0.4)]
    + [(14.2, "chain_rattle", 1.0), (15.4, "gasp", 0.4), (T_FLASH - 0.2, "rec_start", 0.8), (T_FLASH, "whoosh", 0.7), (T_FLASH + 0.02, "sting", 0.6)]
    + [(T_ROAD, "car_pass", 0.9), (20.0, "wiper", 0.7), (20.75, "wiper", 0.6), (21.5, "wiper", 0.5), (23.2, "wiper", 0.4), (24.6, "wiper", 0.4)]
    + [(T_VIB, "vibrate", 1.0), (T_VIB + 0.55, "vibrate", 0.9), (T_TASK1, "notify_bad", 0.8), (T_TASK2, "notify_bad", 0.9), (T_TASK3, "coin", 0.8), (T_TASK3 + 0.02, "notify", 0.5)]
    + [(T_PERSON, "sting", 0.8), (T_PERSON + 0.1, "heartbeat", 0.9), (33.0, "heartbeat", 1.0), (T_BRAKE - 0.08, "pedal_thud", 1.0), (T_BRAKE, "skid", 1.0)]
    + [(T_NOSTOP, "skid", 0.8), (36.4, "heartbeat", 0.9), (T_CUT - 0.05, "static_cut", 1.0), (T_CUT, "crt_off", 0.6)]
    + [(39.0, "chain_rattle", 0.4), (40.6, "breath", 0.4), (42.5, "sting_soft", 0.4), (43.7, "voice_static", 0.5), (45.95, "voice_static", 0.6), (47.0, "boom_tail", 0.4)]
    + [(T_REC2, "rec_start", 0.8), (T_REC2 + 0.02, "glitch", 0.5), (50.5, "rec_start", 0.4), (52.35, "typing", 0.9), (T_CMD, "typing", 1.0), (55.2, "button_press", 0.8)]
    + [(55.3, "attempt_hit", 0.5), (57.6, "sob", 0.8), (59.1, "breath", 0.4), (62.6, "voice_static", 0.5)]
    + [(T_GRID, "faces_swarm", 0.8), (T_GRID + 0.9, "x_marks", 0.6), (T_GRID_CYAN, "connect", 0.5), (69.1, "dissolve", 0.7), (69.6, "number_burn", 0.4)]
    + [(74.4, "voice_static", 0.5), (T_SCARED, "glitch", 0.6), (T_SCARED, "sting", 0.6), (77.8, "voice_static", 0.6), (80.3, "boom_tail", 0.4)]
    + [(T_RELEASE - 0.05, "cuff_open", 1.0), (T_RELEASE + 0.3, "chain_rattle", 0.8), (T_FALL + 0.35, "cuff_drop", 1.0), (T_FALL + 0.6, "chain_rattle", 0.6)]
    + [(T_ADMIN, "glitch", 0.6), (T_ADMIN + 0.05, "screens_on", 0.6), (T_HAND, "type_lock", 0.7), (T_HAND + 0.1, "admin", 1.0), (T_NEWADM, "type_lock", 0.6), (T_48, "attempt_hit", 0.8)]
    + [(T_RAISE, "cloth", 0.8), (T_RAISE + 0.2, "dissolve", 0.5), (T_STOP, "reassemble", 1.0), (T_STOP + 0.9, "sting_soft", 0.4)]
    + [(T_SIDE_ON - 0.1, "phone_on", 0.8), (T_SIDE_ON, "screens_on", 0.6), (T_LIVE, "rec_start", 0.5), (T_FLAT, "notify", 0.4), (98.2, "sting_soft", 0.4)]
    + [(T_TURN, "whoosh", 0.8), (101.0, "sting", 0.7), (103.5, "breath", 0.4), (T_TWO, "delete_alarm", 0.7), (T_TWO, "attempt_hit", 0.7), (107.4, "boom_tail", 0.4)]
    + [(T_LAST - 0.02, "final_hit", 1.0)]
)
HUM = []
CORRIDOR = []
MONHUM = [(0, 18.2), (38.7, 50.45), (55.6, 92.9 + 18.0)]   # room 204: the computer's electrical drone
FLAT = []
RAIN = [(18.2, 37.55)]                 # the accident recording: rain + the engine inside the car
ENGINE = [(20.0, 34.0)]
# music: holds tense under the original, swells on the flash, a pulse under the drive, peaks at the brake, cuts with the recording;
# low under the confession; rises with «сорок семь копий»; a held riser from the handover to the end, hard stop on the last word
MUSIC = [(0, .7), (2.0, .55), (6.3, .6), (8.9, .5), (11.4, .6), (14.0, .75), (17.3, .9), (18.3, .55), (25.5, .65), (27.2, .75), (29.6, .8),
         (32.0, .9), (34.2, 1.0), (37.6, .3), (38.7, .4), (43.5, .5), (48.4, .45), (53.8, .55), (55.6, .45), (57.5, .35), (62.5, .45),
         (64.8, .7), (67.2, .6), (69.0, .55), (71.6, .5), (75.3, .7), (77.7, .65), (80.6, .8), (84.4, .7), (87.4, .85), (89.0, .95),
         (90.2, .55), (92.9, .6), (98.1, .7), (100.0, .75), (103.4, .7), (105.3, .95), (107.3, .85), (END, 1.0)]
MUSIC_TAIL = False
BELLS = [(0.1, 987.8), (T_BLINK1, 932.3), (T_ROAD, 784.0), (T_REC2, 880.0), (T_GRID_CYAN, 740.0), (T_48, 987.8), (T_SIDE_ON, 784.0), (T_TWO, 932.3)]
RISER = (107.3, END)


def check():
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    assert SHOTS[0]["t"][0] == 0 and SHOTS[-1]["t"][1] == END
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)
    assert SUBS[-1][1] <= END + 1e-9
    assert all(0 <= t < END for t, _, _ in SFX)
    for s in SHOTS:
        assert s.get("phone") in (None, *PHONE), s
        assert s["t"][1] - s["t"][0] <= 4.5, ("shot too long", s["t"])
    lip = [s["t"] for s in SHOTS if s["src"] == "LIPSYNC"]
    for a, b in LIPW:
        assert all(any(x <= f / FPS < y for x, y in lip) for f in range(int(a * FPS), int(b * FPS))), ("lip window not covered", a, b)
    face = [s["t"] for s in SHOTS if s.get("monitor") == "face12"]
    for a, b in LIPW_UI:
        assert all(any(x <= f / FPS < y for x, y in face) for f in range(int(a * FPS), int(b * FPS))), ("screen-face lip window not on the screen", a, b)
    # no on-screen message before its words (phrase starts from timeline/transcript_words.json)
    assert T_TASK1 >= 27.20 and T_TASK2 >= 28.38 and T_TASK3 >= 29.60 and T_CMD >= 53.83 and T_HAND >= 85.91 and T_NEWADM >= 87.49
    assert T_48 >= 88.92 and T_TWO >= 105.26 and T_LIVE >= 94.99 and T_FLAT >= 96.80 and T_SIDE_ON >= 92.97 and T_BLINK1 >= 2.14
    # the hand: vanishing in every ALEX_48 shot before the handover, whole after (E12_turn renders him whole; E12_raise/E12_a48 vanish)
    for s in SHOTS:
        if s["src"] in ("E12_raise", "E12_hand") or s.get("lips") == "E12_a48": assert s["t"][1] <= T_STOP + 1e-9, s
        if s["src"] in ("E12_turn",): assert s["t"][0] >= T_STOP, s
    assert SHOTS[-1].get("lips") == "E12_two" and SHOTS[-1].get("monitor") == "live12"   # last frame: both Elenas


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, subtitles=SUBS, sfx=SFX, monhum=MONHUM, rain=RAIN, engine=ENGINE, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep12_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
