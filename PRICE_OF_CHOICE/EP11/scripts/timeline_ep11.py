"""EP11 «НУЛЕВОЙ УРОВЕНЬ» — editing timeline (single source of truth). Same format as EP10 (../EP10/scripts/timeline_ep10.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
The approved MP3 is 108.12 s (speech 0.13 – 108.12 s, no silent tail): 18.1 s over the 75–90 s target — reported, not altered.
Phrase times: timeline/transcript_words.json (Whisper small via sherpa-onnx, cut at the VO's own pauses ≥ 0.09 s, silencedetect −36 dB);
verified text: docs/EP11_transcript.txt.

EP11 opens the second EP10 ended: «Следующий игрок: Елена» on ALEX_48's phone (EP10's last phone frame, E10_pov_end, reused unchanged),
then door 204 under its red lamp at the end of the hotel corridor (EP10's very last shot) as her scream comes from behind it. No recap,
no time jump, no new location. It ends on «Оригинал проснулся» on the turned screen — the last frame of the file (the speech runs to the
end of the MP3, so there is no black tail).

Production names (never shown): ALEX_48, ALEX_49, ALEX_OLD_POLICE, SISTER (Елена), ALEX_ORIGINAL_CONSCIOUSNESS (only a face drawn on the
computer's screen — never a 3D figure, never identified with ALEX_ZERO, who is not on screen in EP11).

Lip-sync: the officer, the sister, ALEX_48 (3D stills) and the original's face on the screen (drawn by phone_ui.draw_face11) pick their
mouth shape frame by frame from the VO envelope. The narrator voices every line (no second voice, the voice is never processed).

`python3 scripts/timeline_ep11.py` checks the timeline and writes timeline/ep11_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 108.12          # the approved MP3 is 108.121 s
END = 108.12             # the video ends with the MP3 on the last word — no black tail, no end card, no call to action
CUT_TO_BLACK = END       # (no cut to black: the episode stops dead on «Оригинал проснулся»)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- key moments (VO clock)
T_NEXT, T_NEXT_NAME = 0.13, 1.91      # «Следующий игрок:» «Елена» (EP10's last screen, the name lands on the word)
T_SCREAM = 3.92                       # «…её крик»
T_GRAB = 8.45                         # the officer's hand closes on ALEX_48's shoulder («…схватил меня»)
T_DOOR = 14.15                        # door 204 bursts open («…и открыл дверь»)
T_TITLE, T_OPT1, T_OPT2 = 20.39, 22.42, 23.48   # «Выберите, кого сохранить» · «Создателя» · «или игрока»
T_REC = 37.45                         # the recording starts on the side monitor («Она указала на монитор»)
T_COPIES = 49.42                      # «…начала создавать новые версии тебя»: the recording breaks into copies of his face
T_RED = 62.05                         # «Вдруг экран загорелся красным» — the word «красным»
T_ZERO, T_DEL = 63.17, 65.75          # «Нулевой уровень активирован» · «Удаление всех копий»
T_DUST_COP, T_DUST_49 = 68.6, 72.4    # the officer / ALEX_49 falling apart
T_LUNGE = 75.6
T_TURN0, T_TURN1 = 84.34, 86.15       # «Экран медленно повернулся»
T_FACE = 86.42                        # «На нём появилось моё лицо» (eyes closed)
T_EYES = 91.35                        # «А потом глаза открылись»
T_MSG1 = 103.62                       # «Подключение к оригиналу установлено»
T_MSG2 = 106.89                       # «Оригинал проснулся»
T_ERASE = T_COPIES                    # (06_render_video 'glitch_late': the recording tears when the copies appear)

# ---------------------------------------------------------------- shots
# src: still (scenes/<src>.png, else ../EP10/scenes, … ../EP02/illustrations), anim folder, "LIPSYNC" (+ lips=<base>) or "BLACK".
# monitor=<state>: phone_ui.draw_monitor on the still's screen quad (per-frame quads on the animated E11_turn).
SHOTS = [
    # --- 1. «СЛЕДУЮЩИЙ ИГРОК: ЕЛЕНА» (EP10's last screen) — HER SCREAM BEHIND DOOR 204 — THE RUN — THE OFFICER CATCHES HIM
    dict(t=(0.00, 3.00), src="E10_pov_end", phone="next11", sub="top", cam=((.5, .56, 1.14), (.5, .56, 1.24)), fx=["handshake"]),
    dict(t=(3.00, 5.15), src="E11_door204", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["tube", "shake_hits"]),
    dict(t=(5.15, 7.70), src="E11_run", anim=(0.0, 1.0), anim_start=5.2, anim_dur=2.5, sub="bottom", cam=((.5, .48, 1.0), (.5, .48, 1.06)), fx=["handshake"]),
    dict(t=(7.70, 9.75), src="E11_grab", anim=(0.0, 1.0), anim_start=7.75, anim_dur=1.55, sub="bottom", cam=((.5, .46, 1.0), (.5, .46, 1.06)), fx=["shake_hits"]),
    # --- 2. «НЕ ВХОДИ. ТАМ НАЧИНАЕТСЯ НУЛЕВОЙ УРОВЕНЬ» — HE BREAKS FREE — THE DOOR
    dict(t=(9.75, 12.95), src="LIPSYNC", lips="E11_cop", sub="bottom", cam=((.5, .4, 1.0), (.5, .39, 1.14)), fx=["handshake"]),
    dict(t=(12.95, 15.00), src="E11_break", anim=(0.0, 1.0), anim_start=13.1, anim_dur=1.6, sub="bottom", cam=((.5, .46, 1.0), (.5, .45, 1.08)), fx=["shake_hits"]),
    # --- 3. THE SISTER, CHAINED — THE SCREEN IN FRONT OF HER — «ВЫБЕРИТЕ, КОГО СОХРАНИТЬ» — «СОЗДАТЕЛЯ ИЛИ ИГРОКА»
    dict(t=(15.00, 17.00), src="E11_room", sub="bottom", cam=((.5, .45, 1.0), (.5, .43, 1.12))),
    dict(t=(17.00, 18.40), src="E11_cuffs", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["glitch"]),
    dict(t=(18.40, 20.30), src="E11_mon", monitor="choice11", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.08))),
    dict(t=(20.30, 22.35), src="E11_mon_close", monitor="choice11", sub="top", cam=((.5, .48, 1.0), (.5, .48, 1.06))),
    dict(t=(22.35, 24.90), src="E11_mon_close", monitor="choice11", sub="top", cam=((.5, .48, 1.06), (.5, .48, 1.14)), fx=["shake_hits"]),
    # --- 4. «АЛЕКС. Я НЕ СОЗДАВАЛА ЭТУ ИГРУ» — «НО НА ЭКРАНЕ БЫЛО ТВОЁ ИМЯ» — «Я СОЗДАЛА ТОЛЬКО КОПИИ, ЧТОБЫ СПАСТИ ТЕБЯ»
    dict(t=(24.90, 26.95), src="E11_sis_look", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1))),
    dict(t=(26.95, 29.85), src="LIPSYNC", lips="E11_sis", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.16))),
    dict(t=(29.85, 32.60), src="LIPSYNC", lips="E11_a48", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["handshake"]),
    dict(t=(32.60, 36.40), src="LIPSYNC", lips="E11_sisc", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12))),
    # --- 5. SHE NODS AT THE MONITOR — THE HOSPITAL RECORDING — «ТЫ ПОПАЛ В АВАРИЮ ТРИ ГОДА НАЗАД» — THE COPIES
    dict(t=(36.40, 38.20), src="E11_point", anim=(0.0, 1.0), anim_start=36.55, anim_dur=1.3, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06))),
    dict(t=(38.20, 40.90), src="E11_side", monitor="hosp11", sub="bottom", cam=((.5, .45, 1.0), (.5, .46, 1.12))),
    dict(t=(40.90, 42.90), src="E11_hosp_close", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.1)), fx=["rec"]),
    dict(t=(42.90, 45.50), src="E11_hosp", sub="bottom", cam=((.5, .5, 1.0), (.5, .48, 1.12)), fx=["rec"]),
    dict(t=(45.50, 48.00), src="LIPSYNC", lips="E11_sisc", sub="bottom", cam=((.5, .42, 1.1), (.5, .42, 1.18))),
    dict(t=(48.00, 50.45), src="E11_side_close", monitor="hosp11", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["glitch_late"]),
    dict(t=(50.45, 52.70), src="LIPSYNC", lips="E11_sis", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1))),
    # --- 6. THE HAND — «ЗНАЧИТ, НАСТОЯЩИЙ АЛЕКС ВСЁ ЕЩЁ ЖИВ?» — SHE NODS
    dict(t=(52.70, 55.40), src="E11_hand", anim=(0.0, 1.0), anim_start=52.84, anim_dur=2.4, sub="bottom", cam=((.5, .45, 1.0), (.5, .43, 1.12)), fx=["glitch"]),
    dict(t=(55.40, 58.95), src="LIPSYNC", lips="E11_a48", sub="bottom", cam=((.5, .42, 1.08), (.5, .41, 1.2))),
    dict(t=(58.95, 60.90), src="E11_nod", anim=(0.0, 1.0), anim_start=59.6, anim_dur=0.95, sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.12))),
    # --- 7. THE SCREEN GOES RED — «НУЛЕВОЙ УРОВЕНЬ АКТИВИРОВАН» — «УДАЛЕНИЕ ВСЕХ КОПИЙ» — THE OFFICER AND ALEX_49 FALL APART
    dict(t=(60.90, 63.05), src="E11_mon", monitor="zero11", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.06)), fx=["shake_hits"]),
    dict(t=(63.05, 65.55), src="E11_mon_red", monitor="zero11", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.08)), fx=["redglow"]),
    dict(t=(65.55, 67.90), src="E11_mon_red_close", monitor="zero11", sub="top", cam=((.5, .48, 1.0), (.5, .48, 1.08)), fx=["shake_hits"]),
    dict(t=(67.90, 70.50), src="E11_cop_dust", anim=(0.0, 1.0), anim_start=68.1, anim_dur=2.3, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06)), fx=["glitch", "redglow"]),
    dict(t=(70.50, 74.90), src="E11_a49_dust", anim=(0.0, 1.0), anim_start=70.7, anim_dur=4.0, sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.16)), fx=["glitch"]),
    # --- 8. HE LUNGES FOR THE COMPUTER — «НЕ ТРОГАЙ ЕГО!» — «ПОЧЕМУ?» — «ПОТОМУ ЧТО ЭТО НЕ КОМПЬЮТЕР»
    dict(t=(74.90, 76.60), src="E11_lunge", anim=(0.0, 1.0), anim_start=75.15, anim_dur=1.1, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.08)), fx=["shake_hits"]),
    dict(t=(76.60, 79.60), src="LIPSYNC", lips="E11_sisr", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["redglow"]),
    dict(t=(79.60, 80.95), src="LIPSYNC", lips="E11_a48r", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.14)), fx=["handshake"]),
    dict(t=(80.95, 84.20), src="LIPSYNC", lips="E11_sisr", sub="bottom", cam=((.5, .42, 1.14), (.5, .42, 1.26)), fx=["redglow"]),
    # --- 9. THE SCREEN TURNS — HIS FACE, EYES CLOSED — THE EYES OPEN — «ЕЛЕНА, ОТОЙДИ ОТ НЕГО…»
    dict(t=(84.20, 86.30), src="E11_turn", anim=(0.0, 1.0), anim_start=T_TURN0, anim_dur=T_TURN1 - T_TURN0, monitor="face11", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.06))),
    dict(t=(86.30, 88.30), src="E11_face", monitor="face11", sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.08))),
    dict(t=(88.30, 90.70), src="E11_face_close", monitor="face11", sub="top", cam=((.5, .46, 1.0), (.5, .46, 1.1))),
    dict(t=(90.70, 92.40), src="E11_face_close", monitor="face11", sub="top", cam=((.5, .44, 1.18), (.5, .44, 1.3)), fx=["shake_hits"]),
    dict(t=(92.40, 95.60), src="E11_a48_lit", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.14)), fx=["handshake"]),
    dict(t=(95.60, 97.85), src="E11_face_close", monitor="face11", sub="top", cam=((.5, .46, 1.04), (.5, .46, 1.14))),
    dict(t=(97.85, 100.90), src="E11_face", monitor="face11", sub="top", cam=((.5, .45, 1.04), (.5, .45, 1.16))),
    # --- 10. THE SISTER, AFRAID — «ПОДКЛЮЧЕНИЕ К ОРИГИНАЛУ УСТАНОВЛЕНО» — «ОРИГИНАЛ ПРОСНУЛСЯ» — END ON THE LAST WORD
    dict(t=(100.90, 103.50), src="E11_sis_fear", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["redglow"]),
    dict(t=(103.50, 106.80), src="E11_face_close", monitor="face11", sub="top", cam=((.5, .46, 1.0), (.5, .46, 1.1))),
    dict(t=(106.80, END), src="E11_face_close", monitor="face11", sub="top", cam=((.5, .46, 1.12), (.5, .46, 1.2)), fx=["shake_hits"]),
]

# ---------------------------------------------------------------- lip-sync windows (3D stills) + the original's face on the screen (UI)
LIPW = [(9.82, 10.60), (10.87, 12.62), (27.05, 27.47), (27.89, 29.69), (30.29, 32.27), (33.09, 34.82), (35.07, 36.19), (45.60, 47.50),
        (50.47, 52.01), (55.99, 58.83), (78.28, 79.32), (79.89, 80.46), (81.31, 83.52)]
LIPW_UI = [(95.69, 97.50), (98.00, 100.83)]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
LIP_WINDOWS = sorted(LIPW + LIPW_UI)


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
PHONE_CLOCK = "02:57"            # a minute after EP10's phones (02:56)
MSG_TITLE, MSG_OPT1, MSG_OR, MSG_OPT2 = "Выберите, кого сохранить", "Создателя", "или", "игрока"
MSG_ZERO, MSG_DEL = "Нулевой уровень активирован", "Удаление всех копий"
MSG_LINK, MSG_WOKE = "Подключение к оригиналу установлено", "Оригинал проснулся"
NEXT11 = dict(t_off=-9, t1=-9, t2=T_NEXT, t_name=T_NEXT_NAME)          # EP10's last screen: «Уровень десять завершён» already there
PHONE = {"next11": [(0, ("end10", NEXT11))]}
SCREENS_ON = {}
SCREEN_TINT = {}
REC_STAMP = "06.11.2023"         # the hospital recording: three years before EP10's «ПТ 06.11»
HOSP_STAMP = REC_STAMP

HITS = [T_SCREAM, T_GRAB, T_DOOR, T_OPT2, T_RED, T_DEL, T_DUST_COP, T_LUNGE, T_EYES, T_MSG2]
BLACKOUT = None
FLASHES = [(T_SCREAM, "white"), (T_DOOR, "cold"), (T_REC, "cold"), (T_RED, "red"), (T_DEL, "red"), (T_FACE, "cold"), (T_EYES, "white"), (T_MSG2, "red")]
COUNTDOWN = None
ENDCARD = None
BIG_SUBS = ()

# ---------------------------------------------------------------- subtitles (*word* = yellow, !word! = red, ¡ = a literal "!")
# Only words that are in the voiceover; at most two lines each. Starts/ends from the phrase timings.
SUBS = [
    (0.13, 2.80, "«Следующий игрок: !Елена!»."),
    (3.06, 4.85, "И сразу её !крик!."),
    (5.23, 7.60, "Я бросился к двери *комнаты двести четыре*,"),
    (7.78, 9.65, "но полицейский *схватил меня*."),
    (9.82, 10.80, "«*Не входи*."),
    (10.87, 12.95, "Там начинается !нулевой уровень!»."),
    (13.19, 14.90, "Я вырвался и *открыл дверь*."),
    (15.04, 16.95, "За ней стояла *моя сестра*,"),
    (17.01, 18.38, "!прикованная к креслу!."),
    (18.43, 20.10, "Перед ней горел *экран*."),
    (20.39, 22.25, "«*Выберите, кого сохранить*»."),
    (22.42, 24.75, "«!Создателя! или *игрока*»."),
    (24.98, 26.80, "Елена посмотрела на меня."),
    (27.05, 27.80, "«*Алекс*."),
    (27.89, 30.05, "Я !не создавала! эту игру»."),
    (30.29, 32.50, "«Но на экране было *твоё имя*»."),
    (33.09, 34.98, "«Я создала *только копии*,"),
    (35.07, 36.55, "чтобы !спасти тебя!»."),
    (36.78, 38.15, "Она указала на *монитор*."),
    (38.27, 40.95, "На записи я лежал в *больничной палате*"),
    (41.04, 42.80, "!без сознания!."),
    (42.95, 45.35, "«Ты попал в аварию *три года назад*."),
    (45.60, 47.95, "Я пыталась вернуть *твою память*."),
    (48.13, 52.60, "Но программа начала создавать !новые версии тебя!»."),
    (52.84, 55.70, "Я посмотрел на свою *исчезающую руку*."),
    (55.99, 59.25, "«Значит, *настоящий Алекс* всё ещё жив?»"),
    (59.59, 60.90, "Елена *кивнула*."),
    (61.04, 63.00, "Вдруг экран загорелся !красным!."),
    (63.17, 65.50, "«!Нулевой уровень! активирован»."),
    (65.75, 67.80, "«!Удаление всех копий!»."),
    (68.01, 70.50, "Полицейский за моей спиной начал *рассыпаться*."),
    (70.56, 72.20, "Из коридора донёсся *крик*."),
    (72.32, 74.90, "Алекс-сорок девять тоже !исчезал!."),
    (75.12, 76.60, "Я бросился *к компьютеру*,"),
    (76.66, 78.15, "но Елена закричала:"),
    (78.28, 79.70, "«!Не трогай его¡!»"),
    (79.89, 81.05, "«*Почему?*»"),
    (81.31, 84.10, "«Потому что это !не компьютер!»."),
    (84.34, 86.30, "Экран медленно *повернулся*."),
    (86.42, 88.30, "На нём появилось *моё лицо*,"),
    (88.40, 90.55, "только с *закрытыми глазами*."),
    (90.75, 92.35, "А потом глаза !открылись!."),
    (92.48, 95.40, "Я услышал *собственный голос*:"),
    (95.69, 97.85, "«Елена, *отойди от него*."),
    (98.00, 101.30, "Эта копия уже !знает слишком много!»."),
    (101.66, 103.50, "На экране появилось сообщение:"),
    (103.62, 106.70, "«*Подключение к оригиналу установлено*»."),
    (106.89, END, "«!Оригинал проснулся!»."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.05, "sting_soft", 0.4), (T_NEXT_NAME, "next_player", 0.7), (2.95, "whoosh", 0.4), (T_SCREAM, "scream", 1.0), (T_SCREAM + 0.02, "sting", 0.6)]
    + [(5.25 + 0.31 * i, "step", 0.9) for i in range(8)] + [(5.3, "breath", 0.4), (7.75, "heavy_step", 0.6), (8.1, "heavy_step", 0.55)]
    + [(T_GRAB - 0.05, "cloth", 0.9), (T_GRAB, "hit", 0.5), (9.6, "breath", 0.5), (12.65, "boom_tail", 0.4)]
    + [(13.2, "cloth", 0.8), (13.5, "whoosh", 0.6), (13.95, "lock_clack", 0.7), (T_DOOR, "door_open", 1.0), (T_DOOR + 0.05, "sting", 0.5)]
    + [(15.1, "phones_buzz", 0.35), (17.05, "chain_rattle", 1.0), (18.5, "wires_hum", 0.45)]
    + [(T_TITLE, "type_lock", 0.6), (T_OPT1, "notify_bad", 0.6), (T_OPT2, "notify", 0.6), (T_OPT2 + 0.02, "attempt_hit", 0.5)]
    + [(25.0, "chain_rattle", 0.5), (26.6, "breath", 0.35), (32.4, "sting_soft", 0.4), (36.2, "boom_tail", 0.35)]
    + [(36.7, "chain_rattle", 0.7), (T_REC, "rec_start", 0.7)] + [(38.3 + 0.86 * i, "ecg_beep", 0.8) for i in range(8)]
    + [(42.9, "wires_hum", 0.3), (T_COPIES, "faces_swarm", 0.8), (T_COPIES, "glitch", 0.5)]
    + [(52.85, "dissolve", 0.7), (53.4, "number_burn", 0.4), (58.9, "sting_soft", 0.4), (59.9, "chain_rattle", 0.35)]
    + [(T_RED, "delete_alarm", 0.8), (T_RED, "sting", 0.7), (T_ZERO, "type_lock", 0.6), (T_ZERO + 0.05, "zero_on", 0.6)]
    + [(T_DEL, "type_lock", 0.6), (T_DEL + 0.05, "attempt_hit", 0.5), (66.6, "delete_alarm", 0.35)]
    + [(68.2, "dissolve", 1.0), (T_DUST_COP, "debris", 0.6), (69.6, "dissolve", 0.6)]
    + [(70.6, "scream", 0.55), (71.3, "dissolve", 0.8), (T_DUST_49, "dissolve", 0.9), (73.4, "debris", 0.45)]
    + [(75.15, "whoosh", 0.8), (75.2, "step", 0.9), (75.5, "step", 0.9), (T_LUNGE, "chain_rattle", 0.8), (78.3, "gasp", 0.5)]
    + [(80.6, "sting_soft", 0.4), (83.6, "boom_tail", 0.4)]
    + [(T_TURN0, "swivel", 1.0), (T_TURN0 + 0.2, "wires_hum", 0.6), (T_FACE, "glitch", 0.5), (T_FACE + 0.05, "shimmer", 0.5)]
    + [(T_EYES - 0.35, "eyes_open", 1.0), (T_EYES, "sting", 0.7), (92.6, "breath", 0.45)]
    + [(95.6, "voice_static", 0.7), (97.9, "voice_static", 0.6), (100.95, "chain_rattle", 0.6), (101.7, "notify_bad", 0.4)]
    + [(T_MSG1, "connect", 1.0), (T_MSG1 + 0.02, "type_lock", 0.5), (T_MSG2 - 0.02, "final_hit", 1.0), (T_MSG2, "attempt_hit", 0.8)]
)
HUM = []
CORRIDOR = [(3.0, 15.0), (70.5, 74.9)]          # the hotel corridor's air
MONHUM = [(15.0, 38.2), (45.5, 70.5), (74.9, END)]   # room 204: the computer's electrical drone
FLAT = []
# music: picks up on EP10's cut — fast under the run and the grab, holds under «Не входи», rises at the door; drops low under the
# sister's confession and the hospital, swells on the red screen and the deletion, rises with the turning screen and the face, a riser
# under the last two messages, hard stop on the final word (the file ends there)
MUSIC = [(0, .65), (3.0, .8), (5.1, .85), (7.7, .9), (9.7, .5), (12.9, .7), (14.2, .85), (15.0, .55), (18.4, .5), (20.3, .6),
         (22.4, .75), (24.9, .4), (32.6, .35), (36.4, .4), (38.2, .3), (45.5, .35), (49.4, .55), (52.7, .5), (55.4, .4), (58.9, .45),
         (61.0, .7), (62.1, .95), (65.6, .97), (67.9, .85), (70.5, .9), (74.9, .95), (76.6, .6), (81.0, .55), (84.2, .7), (86.4, .75),
         (90.7, .8), (91.4, .95), (92.4, .5), (95.6, .45), (100.9, .55), (103.5, .75), (106.8, .95), (END, 1.0)]
MUSIC_TAIL = False
BELLS = [(0.1, 987.8), (T_NEXT_NAME, 932.3), (15.0, 784.0), (T_REC, 880.0), (T_FACE, 740.0), (T_EYES, 987.8), (T_MSG1, 784.0)]
RISER = (101.0, END)


def check():
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    assert SHOTS[0]["t"][0] == 0 and SHOTS[-1]["t"][1] == END
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)
    assert SUBS[-1][1] <= END + 1e-9
    assert all(0 <= t < END for t, _, _ in SFX)
    for s in SHOTS:
        assert s.get("phone") in (None, *PHONE) and s.get("screens") in (None, *PHONE), s
        assert s["t"][1] - s["t"][0] <= 4.5, ("shot too long", s["t"])
    lip = [s["t"] for s in SHOTS if s["src"] == "LIPSYNC"]
    for a, b in LIPW:
        assert all(any(x <= f / FPS < y for x, y in lip) for f in range(int(a * FPS), int(b * FPS))), ("lip window not covered", a, b)
    face = [s["t"] for s in SHOTS if s.get("monitor") == "face11"]
    for a, b in LIPW_UI:
        assert all(any(x <= f / FPS < y for x, y in face) for f in range(int(a * FPS), int(b * FPS))), ("screen-face lip window not on the screen", a, b)
    # no on-screen message before its words (phrase starts from timeline/transcript_words.json)
    assert T_NEXT >= 0.13 and T_NEXT_NAME >= 1.91 and T_TITLE >= 20.39 and T_OPT1 >= 22.42 and T_OPT2 >= 23.48
    assert T_RED >= 61.04 and T_ZERO >= 63.17 and T_DEL >= 65.75 and T_FACE >= 86.42 and T_EYES >= 90.75 and T_MSG1 >= 103.62 and T_MSG2 >= 106.89
    assert SHOTS[-1].get("monitor") == "face11"                     # the last frame is the screen with «Оригинал проснулся»


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, subtitles=SUBS, sfx=SFX, corridor=CORRIDOR, monhum=MONHUM, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep11_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
