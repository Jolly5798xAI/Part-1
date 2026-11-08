"""EP08 «ЗАВТРАШНИЙ ДЕНЬ» — editing timeline (single source of truth). Same format as EP07 (../EP07/scripts/timeline_ep07.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper small, the same CTranslate2 int8 model as EP03–EP07, sha256 ca732cb1…ce73);
phrase starts/ends checked against silencedetect (docs/EP08_VO_REPORT.md). Verified text: docs/EP08_transcript.txt.

EP08 opens on EP07's last shot — the centre monitor in the monitor room with the address «Лесная, 12 · Квартира 47», the date
«суббота, 7 ноября» and the red stamp «ЗАВТРА» (EP07 still E7_mon, EP07's end framing (0.5, 0.5, ×1.2)) — the same second,
ALEX_48 still in the monitor room, his left hand still being deleted. No recap, no time jump at the start.

Production names (never shown): ALEX_48 = the hero (the «48» on his wrist, the left hand being deleted), ALEX_ORIGINAL = the Alex
at the kitchen table (no marks), ALEX_FIRST = the voice behind the front door at the end (never shown).

Lip-sync: ALEX_48 («Что будет завтра?», «Но я же Алекс», «Это неправда»), the sister on her feed («Ты убьёшь…», «Ты его последняя
копия», «Тогда измени будущее», «Не бери нож!») and ALEX_ORIGINAL («Ты пришёл раньше», «Прячься…») pick their mouth shape frame by
frame from the VO envelope. The narrator voices every line (no second voice). The last line is heard through the door: no mouth.

`python3 scripts/timeline_ep08.py` checks the timeline and writes timeline/ep08_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 91.64           # the approved MP3 is 91.638 s; the last word «воды» ends at ~90.97
CUT_TO_BLACK = 90.97     # hard cut on the last word of EP01's first line — nothing after it
END = 91.64              # the video ends with the MP3 (black after the cut; no end card, no call to action)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- key moments (VO clock)
T_REC = 22.45            # «Вдруг монитор показал…» — the sister's feed is replaced by the recording
T_PUNCH = 34.70          # «Я ударил по экрану» — the fist hits the monitor
T_RECOFF = 38.05         # «…резко выключила запись» — the screen dies
T_QUAKE = (41.75, 42.45, 43.05)       # «…пол подо мной затрясся» — jolts
T_MON_RED = 43.95        # «На стене загорелся таймер» — every monitor shows the timer
T_DEL = 45.50            # «Удаление через десять секунд» typed on the centre monitor
COUNT_START, T_ZERO = 47.98, 57.98    # 00:10 … 00:00 (the last second goes as he steps through)
T_PORTAL = 50.30         # room 204 starts coming apart behind the frame
T_STEP = 57.70           # «Я шагнул внутрь»
T_SHUT = 60.62           # the flat's front door shuts behind him
T_PHONE_ON, T_CHANGED, T_FLIP, T_TOMORROW8 = 61.40, 63.16, 63.30, 64.68   # the lock screen: «Дата изменена», the date flips, «Завтра наступило»
T_GLASS = 66.63          # the glass hits the kitchen floor
T_KEY_IN, T_KEY_1 = 82.62, 83.46      # the key enters the lock / the first jerk of the thumb-turn
T_VOICE = 88.06          # «Мне заплатили пятьсот долларов за стакан воды…» (ALEX_FIRST, behind the door)

# EP07's monitor screens, already fully shown when EP08 starts (the address screen of EP07 in its final state)
T_ADDR_SCREEN, T_STREET, T_FLAT, T_DATE, T_TOMORROW = -9.0, -8.0, -7.0, -6.0, -5.0
T_MSG1 = T_MSG2 = -1.0

# ---------------------------------------------------------------- shots
# src: still name (scenes/<src>.png, else ../EP07/scenes, ../EP06/scenes, …), anim folder (scenes/<src>/), "LIPSYNC" (+ lips=<base>) or "BLACK".
# cam: (cx, cy, zoom) start -> end. phone: state drawn on the scene's phone screen; monitor: state drawn on the centre monitor
# (+ mcrack: the crack drawn into the screen UI); monitors: state on every monitor of the wall; fx: see 06_render_video.py.
SHOTS = [
    # --- 1. THE ADDRESS, TOMORROW (EP07's last shot continues)
    dict(t=(0.00, 2.70), src="E7_mon", monitor="addr", sub="top", cam=((.5, .5, 1.2), (.5, .49, 1.3))),
    dict(t=(2.70, 5.10), src="E7_mon", monitor="addr", sub="bottom", cam=((.5, .62, 1.55), (.5, .63, 1.68)), fx=["handshake"]),
    dict(t=(5.10, 7.05), src="E8_hand", anim=(0.0, 1.0), anim_start=5.15, anim_dur=1.8, sub="bottom", cam=((.5, .45, 1.0), (.5, .43, 1.1)), fx=["glitch"]),
    dict(t=(7.05, 9.55), src="LIPSYNC", lips="E8_alexm", sub="bottom", cam=((.5, .42, 1.0), (.5, .41, 1.12))),
    # --- 2. «ТЫ УБЬЁШЬ НАСТОЯЩЕГО АЛЕКСА» — «ТЫ ЕГО ПОСЛЕДНЯЯ КОПИЯ»
    dict(t=(9.55, 11.70), src="E8_feed", sub="bottom", cam=((.5, .45, 1.0), (.5, .43, 1.16)), fx=["cctv"]),
    dict(t=(11.70, 14.40), src="LIPSYNC", lips="E8_feedc", sub="bottom", cam=((.5, .44, 1.1), (.5, .44, 1.26)), fx=["cctv", "redglow"]),
    dict(t=(14.40, 15.60), src="E8_alexc_neutral", sub="bottom", cam=((.5, .38, 1.0), (.5, .38, 1.03))),
    dict(t=(15.60, 17.40), src="LIPSYNC", lips="E8_alexm", sub="bottom", cam=((.5, .41, 1.18), (.5, .41, 1.28))),
    dict(t=(17.40, 19.30), src="E8_feed_shake", anim=(0.0, 1.0), anim_start=17.62, anim_dur=1.4, sub="bottom", cam=((.5, .44, 1.0), (.5, .44, 1.08)), fx=["cctv"]),
    dict(t=(19.30, 21.60), src="LIPSYNC", lips="E8_feedc", sub="bottom", cam=((.5, .42, 1.3), (.5, .42, 1.46)), fx=["cctv", "redglow"]),
    # --- 3. THE RECORDING OF TOMORROW: THE FLAT, THE KNIFE, THE OTHER ALEX
    dict(t=(21.60, T_REC), src="E8_mon_feed", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06))),
    dict(t=(T_REC, 23.90), src="E8_mon_rec", monitor="rec", sub="bottom", cam=((.5, .5, 1.06), (.5, .5, 1.2)), fx=["glitch"]),
    dict(t=(23.90, 26.35), src="E8_rec_flat", sub="bottom", cam=((.5, .5, 1.0), (.5, .52, 1.12)), fx=["rec"]),
    dict(t=(26.35, 28.45), src="E8_rec_door", sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.14)), fx=["rec"]),
    dict(t=(28.45, 29.70), src="E8_rec_knife", sub="top", cam=((.5, .55, 1.0), (.5, .56, 1.12)), fx=["rec"]),
    dict(t=(29.70, 32.05), src="E8_rec_two", anim=(0.0, 1.0), anim_start=29.75, anim_dur=1.9, sub="bottom", cam=((.5, .5, 1.0), (.5, .48, 1.08)), fx=["rec"]),
    dict(t=(32.05, 34.10), src="E8_rec_plead", anim=(0.0, 1.0), sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.12)), fx=["rec"]),
    # --- 4. THE FIST — «ЭТО НЕПРАВДА» — SHE SWITCHES IT OFF — «ТОГДА ИЗМЕНИ БУДУЩЕЕ»
    dict(t=(34.10, 35.60), src="E8_punch_mon", anim=(0.0, 1.0), anim_start=34.20, anim_dur=0.8, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.05)), fx=["shake_hits"]),
    dict(t=(35.60, 37.00), src="LIPSYNC", lips="E8_alexm", sub="bottom", cam=((.5, .4, 1.22), (.5, .4, 1.32)), fx=["handshake", "redglow"]),
    dict(t=(37.00, 39.20), src="E8_mon_crack", monitor="recoff", mcrack=True, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    dict(t=(39.20, 41.00), src="LIPSYNC", lips="E8_feedc", sub="bottom", cam=((.5, .43, 1.18), (.5, .43, 1.3)), fx=["cctv"]),
    # --- 5. THE ROOM IS DELETED — THE TIMER — «УДАЛЕНИЕ ЧЕРЕЗ ДЕСЯТЬ СЕКУНД»
    dict(t=(41.00, 43.50), src="E8_quake", anim=(0.0, 1.0), anim_start=41.35, anim_dur=2.1, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["shake_hits"]),
    dict(t=(43.50, 45.35), src="E8_wall", monitors="timer", nohud=True, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.12)), fx=["redglow"]),
    dict(t=(45.35, 47.80), src="E8_mon_del", monitor="del", mcrack=True, nohud=True, sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.12)), fx=["redglow"]),
    # --- 6. BACK TO THE MIRROR — THE DOOR OF FLAT 47 — «НЕ БЕРИ НОЖ!» — THROUGH
    dict(t=(47.80, 50.10), src="E8_run", anim=(0.0, 1.0), anim_start=47.95, anim_dur=2.0, sub="bottom", cam=((.5, .5, 1.0), (.5, .48, 1.06)), fx=["shake_hits", "glitch_late"]),
    dict(t=(50.10, 52.70), src="E8_portal", anim=(0.0, 1.0), anim_start=T_PORTAL, anim_dur=2.2, sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.1))),
    dict(t=(52.70, 54.70), src="E8_door", anim=(0.0, 1.0), anim_start=53.0, anim_dur=1.6, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.12))),
    dict(t=(54.70, 56.00), src="E8_feed_shout", sub="bottom", cam=((.5, .5, 1.04), (.5, .52, 1.14)), fx=["cctv", "glitch"]),
    dict(t=(56.00, 57.25), src="LIPSYNC", lips="E7_feedm", sub="bottom", cam=((.5, .5, 1.12), (.5, .5, 1.22)), fx=["cctv", "handshake"]),
    dict(t=(57.25, 58.75), src="E8_step_in", anim=(0.0, 1.0), anim_start=57.35, anim_dur=1.35, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.1)), fx=["shake_hits"]),
    # --- 7. FLAT 47 — «ДАТА ИЗМЕНЕНА» — «ЗАВТРА НАСТУПИЛО»
    dict(t=(58.75, 61.30), src="E8_flat_in", anim=(0.0, 1.0), anim_start=58.75, anim_dur=2.2, sub="bottom", cam=((.5, .48, 1.0), (.5, .47, 1.08))),
    dict(t=(61.30, 63.05), src="E8_phone", phone="lock8", sub="top", cam=((.5, .58, 1.0), (.5, .6, 1.08))),
    dict(t=(63.05, 64.60), src="E8_phone_close", phone="lock8", sub="top", cam=((.5, .6, 1.0), (.5, .61, 1.06)), fx=["handshake"]),
    dict(t=(64.60, 66.30), src="E8_phone_close", phone="lock8", sub="top", cam=((.5, .62, 1.12), (.5, .63, 1.22))),
    # --- 8. THE GLASS — HE TURNS — ALEX_ORIGINAL AT THE TABLE
    dict(t=(66.30, 68.40), src="E8_glass", anim=(0.0, 1.0), anim_start=66.25, anim_dur=0.9, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08))),
    dict(t=(68.40, 69.40), src="E8_alex_hall", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.05))),
    dict(t=(69.40, 71.10), src="E8_turn", anim=(0.0, 1.0), anim_start=69.50, anim_dur=1.5, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.06))),
    dict(t=(71.10, 73.35), src="E8_kitchen", sub="bottom", cam=((.5, .45, 1.0), (.5, .42, 1.18))),
    dict(t=(73.35, 74.75), src="E8_orig_look", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.08))),
    dict(t=(74.75, 76.20), src="E8_hand_flat", anim=(0.0, 1.0), sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.08)), fx=["glitch"]),
    dict(t=(76.20, 77.80), src="LIPSYNC", lips="E8_orig", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.08))),
    dict(t=(77.80, 79.55), src="E8_orig_point", sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.08))),
    dict(t=(79.55, 82.30), src="LIPSYNC", lips="E8_origp", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.18))),
    # --- 9. THE KEY — THE VOICE BEHIND THE DOOR — CUT
    dict(t=(82.30, 84.55), src="E8_lock", anim=(0.0, 0.3), anim_start=82.90, anim_dur=1.4, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06))),
    dict(t=(84.55, 87.60), src="E8_hide", sub="bottom", cam=((.5, .5, 1.0), (.5, .52, 1.16))),
    dict(t=(87.60, CUT_TO_BLACK), src="E8_lock", anim=(0.3, 1.0), anim_start=88.05, anim_dur=2.85, sub="bottom", cam=((.5, .5, 1.06), (.5, .5, 1.24))),
    dict(t=(CUT_TO_BLACK, END), src="BLACK"),
]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
LIP_WINDOWS = [(8.38, 9.34), (11.88, 14.18), (15.80, 17.12), (19.50, 21.18), (35.66, 36.46), (39.36, 40.62), (56.12, 56.80),
               (76.46, 77.40), (79.82, 81.98)]


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
PHONE_CLOCK = "02:54"            # the same minute as EP07's feed — but a day later
ADDR_STREET, ADDR_FLAT = "Лесная, 12", "Квартира 47"
# the date: EP01's lock screen set the story on «пятница, 6 ноября»; EP07's monitor showed «суббота, 7 ноября» + «ЗАВТРА».
# EP08 keeps exactly that: the phone flips from the old date to the new one. No real-world calendar date is used.
DATE_LABEL, DATE_OLD, DATE_TEXT, DATE_WORD = "Дата", "пятница, 6 ноября", "суббота, 7 ноября", "ЗАВТРА"
NUMBER = "48"
MSG_DELETE10 = ("Удаление через", "десять секунд")          # «Удаление через десять секунд» (two lines on the monitor)
MSG_CHANGED, MSG_TOMORROW = "Дата изменена", "Завтра наступило"
MSG_UNSTABLE, MSG_DELETE = "Экземпляр сорок восемь нестабилен", "Начать удаление"   # EP07 (not drawn in EP08)
REC_STAMP = "СБ 07.11"           # the recording's timestamp: Saturday 7 November, 02:54 (tomorrow)
LOCK8 = dict(clock=PHONE_CLOCK, old=DATE_OLD, new=DATE_TEXT, t_on=T_PHONE_ON, t_changed=T_CHANGED, t_flip=T_FLIP, t_tomorrow=T_TOMORROW8,
             changed=MSG_CHANGED, tomorrow=MSG_TOMORROW)
PHONE = {"lock8": [(0, ("lock8", LOCK8))]}
SCREEN_TINT = {}

# jolts -> camera shake (fx "shake_hits")
HITS = [T_PUNCH, *T_QUAKE, 48.55, 49.45, 57.95]
BLACKOUT = None
FLASHES = [(5.15, "cold"), (11.88, "red"), (T_REC, "cold"), (25.22, "red"), (28.95, "red"), (T_PUNCH, "white"), (T_RECOFF, "black"),
           (39.36, "red"), (41.75, "white"), (T_MON_RED, "red"), (T_DEL, "red"), (T_PORTAL + 0.9, "cold"), (56.12, "red"),
           (T_ZERO, "white"), (63.30, "cold"), (64.68, "red"), (T_GLASS, "white"), (71.20, "cold"), (79.82, "red")]
COUNTDOWN = (47.80, COUNT_START, 10, T_ZERO + 0.25)   # HUD timer: 00:10 from 47.80, counting from 47.98, gone after 00:00
ENDCARD = None
BIG_SUBS = ("!Завтрашний день!.", "«!Не бери нож¡!»", "«!Завтра наступило!».", "«!Это неправда!».")

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger, ¡ = a literal "!")
# Only words that are in the voiceover; at most two lines each. Starts/ends from the word timings and silencedetect.
SUBS = [
    (0.00, 2.38, "На экране стоял *мой адрес*."),
    (3.06, 4.44, "И !завтрашняя дата!."),
    (5.22, 6.92, "Левая рука продолжала !исчезать!."),
    (7.16, 9.34, "Я закричал сестре: «*Что будет завтра?*»"),
    (9.86, 11.40, "Она посмотрела *прямо в камеру*."),
    (11.88, 14.18, "«Ты !убьёшь настоящего Алекса!»."),
    (14.66, 15.42, "Я замер."),
    (15.80, 17.12, "«Но я же *Алекс*»."),
    (17.62, 18.94, "Она покачала головой."),
    (19.50, 21.18, "«Ты его !последняя копия!»."),
    (21.98, 23.68, "Вдруг монитор показал *запись*."),
    (24.02, 24.84, "*Моя квартира*."),
    (25.22, 25.96, "!Завтрашний день!."),
    (26.56, 28.28, "Я увидел *себя* у входной двери."),
    (28.56, 29.34, "В руке был !нож!."),
    (29.82, 31.78, "А напротив стоял *другой Алекс*."),
    (32.20, 33.64, "Он !умолял! меня остановиться."),
    (34.26, 35.46, "Я *ударил по экрану*."),
    (35.66, 36.46, "«!Это неправда!»."),
    (37.16, 38.88, "Сестра резко *выключила запись*."),
    (39.36, 40.62, "«Тогда !измени будущее!»."),
    (41.32, 43.32, "В этот момент пол подо мной *затрясся*."),
    (43.72, 45.16, "На стене загорелся *таймер*."),
    (45.50, 47.48, "«!Удаление через десять секунд!»."),
    (48.08, 49.98, "Я *бросился* к разбитому зеркалу."),
    (50.18, 52.46, "За ним больше не было *комнаты 204*."),
    (52.84, 54.46, "Там стояла *моя входная дверь*."),
    (54.88, 55.88, "Сестра закричала:"),
    (56.12, 56.80, "«!Не бери нож¡!»"),
    (57.38, 58.60, "Я *шагнул внутрь*."),
    (58.91, 60.96, "И оказался в *своей квартире*."),
    (61.52, 62.90, "На телефоне было написано:"),
    (63.16, 64.42, "«!Дата изменена!»."),
    (64.68, 66.16, "«!Завтра наступило!»."),
    (66.98, 69.12, "Из кухни донёсся звук *разбитого стакана*."),
    (69.46, 70.84, "Я *медленно* повернулся."),
    (71.20, 73.04, "За столом сидел !настоящий Алекс!."),
    (73.56, 75.88, "Он посмотрел на мою *исчезающую руку*."),
    (76.46, 77.40, "«Ты *пришёл раньше*»."),
    (78.20, 79.28, "Потом указал *на дверь*."),
    (79.82, 81.98, "«Прячься. Сейчас появится !первый!»."),
    (82.98, 84.34, "В замке *повернулся ключ*."),
    (84.76, 87.13, "Из-за двери раздался *мой голос*:"),
    (88.06, 90.97, "«Мне заплатили 500 долларов за *стакан воды*…»"),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
TICKS = [COUNT_START + i for i in range(10)]
SFX = (
    [(0.05, "sting_soft", 0.5), (2.75, "type_lock", 0.4), (5.15, "dissolve", 0.8), (5.20, "glitch", 0.4), (7.10, "breath", 0.5), (7.35, "gasp", 0.5)]
    + [(9.60, "voice_static", 1.0), (11.85, "sting", 0.7), (11.88, "voice_static", 1.0), (14.55, "boom_tail", 0.5), (15.75, "breath", 0.4)]
    + [(17.60, "voice_static", 0.8), (19.45, "voice_static", 1.0), (19.50, "sting", 0.5)]
    + [(T_REC - 0.05, "glitch", 0.6), (T_REC, "rec_start", 1.0), (25.22, "sting", 0.6), (26.40, "heavy_step", 0.35), (28.90, "sting", 0.8)]
    + [(29.90, "step", 0.6), (30.40, "step", 0.6), (30.95, "step", 0.5), (32.15, "gasp", 0.45), (33.0, "breath", 0.4)]
    + [(34.25, "whoosh", 0.6), (T_PUNCH, "mon_punch", 1.0), (T_PUNCH + 0.03, "glass_crack", 0.8), (35.60, "breath", 0.5)]
    + [(T_RECOFF, "crt_off", 1.0), (39.30, "voice_static", 0.9), (39.36, "sting", 0.5)]
    + [(41.30, "quake", 1.0), (41.75, "hit", 0.6), (42.45, "debris", 0.8), (43.05, "debris", 0.6), (43.05, "glitch", 0.5)]
    + [(T_MON_RED, "delete_alarm", 0.9), (T_MON_RED, "screens_on", 0.6), (T_DEL, "type_lock", 0.8), (T_DEL, "notify_bad", 0.6)]
    + [(t, "delete_tick", 0.9) for t in TICKS]
    + [(47.95, "debris", 0.9), (48.10, "step", 0.7), (48.45, "step", 0.7), (48.80, "step", 0.7), (49.15, "step", 0.6), (49.45, "debris", 0.7)]
    + [(T_PORTAL, "portal", 1.0), (T_PORTAL + 0.1, "dissolve", 0.7), (52.80, "door_open", 0.6), (54.85, "voice_static", 1.0), (56.05, "voice_static", 1.0)]
    + [(56.12, "sting", 0.7), (T_STEP, "whoosh", 0.8), (T_STEP + 0.05, "portal", 0.6), (T_ZERO, "final_hit", 0.9), (T_ZERO, "power_out", 0.6)]
    + [(59.20, "step", 0.6), (59.70, "step", 0.55), (T_SHUT, "door_shut", 1.0), (T_PHONE_ON, "phone_on", 0.7), (T_CHANGED, "notify_bad", 0.8)]
    + [(T_FLIP, "glitch", 0.5), (T_TOMORROW8, "notify_bad", 0.85), (T_TOMORROW8, "sting", 0.6)]
    + [(T_GLASS, "cup_shatter", 1.0), (68.45, "breath", 0.5), (69.60, "cloth", 0.5), (70.30, "step", 0.4), (71.20, "sting", 0.7)]
    + [(73.40, "chair_creak", 0.4), (74.80, "dissolve", 0.6), (78.25, "cloth", 0.5), (79.82, "sting_soft", 0.6)]
    + [(T_KEY_IN, "lock_insert", 1.0), (T_KEY_1, "lock_turn", 1.0), (84.55, "breath", 0.45), (85.40, "heavy_step", 0.45), (86.0, "heavy_step", 0.4)]
    + [(88.6, "lock_turn", 0.9), (89.75, "lock_turn", 1.0), (CUT_TO_BLACK - 0.04, "lock_clack", 1.0), (CUT_TO_BLACK, "final_hit", 1.0)]
)
HUM = []                                  # the phones of room 204 are dead since EP07
CORRIDOR = []
MONHUM = [(0.0, T_STEP + 0.6)]            # the monitor room's drone + fan whine — until he is through the door
FLAT = [(T_STEP + 0.6, CUT_TO_BLACK)]     # flat 47 at night: a fridge hum from the kitchen, a faint clock
# music intensity curve (time, level 0..1): picks up at EP07's end level, low under the sister, climbs on the recording,
# peaks at the deletion and the run, drops to almost nothing in the flat, rises again from the key to the last line, stops dead
MUSIC = [(0, .9), (2.6, .55), (7.0, .6), (9.5, .4), (11.8, .55), (14.4, .35), (17.4, .4), (19.4, .55), (21.6, .6), (24.0, .65), (28.5, .8),
         (32.0, .85), (34.7, .95), (36.6, .5), (38.0, .2), (39.3, .35), (41.3, .75), (43.9, .9), (47.8, .95), (52.7, .9), (54.7, .6),
         (56.1, .85), (T_ZERO, .95), (T_ZERO + 0.05, .1), (61.3, .2), (63.1, .4), (64.7, .55), (66.3, .3), (71.1, .5), (73.3, .35),
         (76.2, .3), (79.5, .45), (82.3, .55), (84.5, .6), (T_VOICE, .7), (CUT_TO_BLACK, .95)]
MUSIC_TAIL = False                         # no end card: dead silence after the cut
BELLS = [(0.1, 987.8), (11.9, 880.0), (25.2, 784.0), (39.4, 932.3), (63.2, 987.8), (71.2, 880.0), (79.8, 784.0)]
RISER = (84.6, CUT_TO_BLACK)


def check():
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    assert SHOTS[0]["t"][0] == 0 and SHOTS[-1]["t"][1] == END
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)
    assert SUBS[-1][1] <= CUT_TO_BLACK + 1e-9
    assert all(0 <= t < END for t, _, _ in SFX)
    for s in SHOTS:
        assert s.get("phone") in (None, *PHONE), s
        assert s["t"][1] - s["t"][0] <= 4.5, ("shot too long", s["t"])
    lip = [s["t"] for s in SHOTS if s["src"] == "LIPSYNC"]
    for a, b in LIP_WINDOWS:
        assert all(any(x <= f / FPS < y for x, y in lip) for f in range(int(a * FPS), int(b * FPS))), ("lip window not covered", a, b)


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, countdown=COUNTDOWN, subtitles=SUBS, sfx=SFX, monhum=MONHUM, flat=FLAT, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep08_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
