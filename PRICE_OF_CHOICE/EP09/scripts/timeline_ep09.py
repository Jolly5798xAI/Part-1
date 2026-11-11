"""EP09 «ПЕРВЫЙ АЛЕКС» — editing timeline (single source of truth). Same format as EP08 (../EP08/scripts/timeline_ep08.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper small, the same CTranslate2 int8 model as EP03–EP08, sha256 ca732cb1…ce73);
phrase starts/ends checked against silencedetect (docs/EP09_VO_REPORT.md). Verified text: docs/EP09_transcript.txt.

EP09 opens the same second EP08 ended on: flat 47, the front door's lock close-up (EP08's E8_lock shot, re-rendered, the thumb-turn
fully turned, EP08's end framing ×1.24), his own voice behind the door. No recap, no time jump, no change of location.

Production names (never shown): ALEX_48 = the hero (the «48», the left hand being deleted), ALEX_49 = the new copy with the glass of
water (cyan «49» on his wrist), ALEX_ZERO = EP08's ALEX_ORIGINAL from the kitchen table (a red «0» burns on his wrist),
ALEX_OLD_POLICE = the officer, unmasked: old Alex.

Lip-sync: ALEX_ZERO («Прячься! Он не должен нас увидеть», «…потому что тебя уже списали», «Теперь ты понимаешь…»), ALEX_48 («Почему он
следующий?») and the sister («Алекс, не верь оригиналу!», EP08's close feed lip-sync stills, seen through the cracked screen) pick their
mouth shape frame by frame from the VO envelope. The narrator voices every line (no second voice).

`python3 scripts/timeline_ep09.py` checks the timeline and writes timeline/ep09_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 96.13           # the approved MP3 is 96.131 s; the last word «умереть» ends at ~96.02
CUT_TO_BLACK = 96.02     # hard cut on the last word of «Оригинал должен умереть» — nothing after it
END = 96.13              # the video ends with the MP3 (black after the cut; no end card, no call to action)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- key moments (VO clock)
T_GRAB = 6.30            # «…схватил меня за плечо»
T_CLICK = 12.58          # «замок щёлкнул» — the latch
T_49 = 23.36             # «…номер сорок девять» — the number fully lit
T_VIB = (35.30, 36.30, 37.00)          # the phone buzzes
T_TASK1, T_TASK2 = 37.96, 39.34       # «Задание выполнено», «Уничтожить предыдущую копию»
T_EYES = 44.60           # «…прямо в мою сторону» — ALEX_49 looks into the lens
T_KNIFE = 48.86          # «…нож»
T_STAB = 56.98           # the knife hits the phone («ударил ножом…»)
T_CRACK = 58.08          # «Экран раскололся»
T_SIS = 62.32            # «Алекс, не верь оригиналу!»
T_ZERO_ON, T_ZERO = 69.80, 71.14      # the «0» starts burning («загорелся») / fully lit on «ноль»
T_DOOR = 78.55           # «…входная дверь снова открылась»
T_REVEAL = 85.34         # «…был я» — his face
T_PHONE_UP = 87.50
T_MSG1, T_MSG2, T_MSG3 = 90.68, 92.10, 94.06   # «Создатель обнаружен», «Начать последнюю проверку», «Оригинал должен умереть»

# ---------------------------------------------------------------- shots
# src: still name (scenes/<src>.png, else ../EP08/scenes, ../EP07/scenes, …), anim folder (scenes/<src>/), "LIPSYNC" (+ lips=<base>) or "BLACK".
# cam: (cx, cy, zoom) start -> end. phone: state drawn on the scene's phone screen; fx: see 06_render_video.py.
SHOTS = [
    # --- 1. HIS OWN VOICE BEHIND THE DOOR (EP08's last shot continues) — THE GRAB — «ПРЯЧЬСЯ!»
    dict(t=(0.00, 2.15), src="E9_lock", anim=(1.0, 1.0), sub="bottom", cam=((.5, .5, 1.24), (.5, .5, 1.34))),
    dict(t=(2.15, 5.25), src="E9_a48_hall", sub="bottom", cam=((.5, .44, 1.0), (.5, .42, 1.12))),
    dict(t=(5.25, 7.75), src="E9_grab", anim=(0.0, 1.0), anim_start=5.35, anim_dur=1.95, sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.08)), fx=["shake_hits"]),
    dict(t=(7.75, 10.25), src="LIPSYNC", lips="E9_zero", sub="bottom", cam=((.5, .42, 1.0), (.5, .41, 1.1)), fx=["handshake"]),
    # --- 2. HIDING — THE LATCH — ALEX_49 WITH THE GLASS — «49»
    dict(t=(10.25, 12.45), src="E9_hide", anim=(0.0, 1.0), anim_start=10.35, anim_dur=1.9, sub="bottom", cam=((.5, .48, 1.0), (.5, .47, 1.06))),
    dict(t=(12.45, 16.55), src="E9_enter", anim=(0.0, 1.0), anim_start=12.75, anim_dur=3.7, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    dict(t=(16.55, 18.75), src="E9_glass49", sub="top", cam=((.5, .5, 1.0), (.5, .55, 1.12))),
    dict(t=(18.75, 21.15), src="E9_a48_peek", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.08))),
    dict(t=(21.15, 25.45), src="E9_wrist49", anim=(0.0, 1.0), anim_start=21.7, anim_dur=1.66, sub="top", cam=((.5, .55, 1.0), (.5, .58, 1.22))),
    dict(t=(25.45, 28.55), src="E9_wrist48", anim=(0.0, 1.0), sub="bottom", cam=((.5, .45, 1.0), (.5, .42, 1.12)), fx=["glitch"]),
    dict(t=(28.55, 30.55), src="LIPSYNC", lips="E9_a48w", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.08))),
    dict(t=(30.55, 32.45), src="E9_two_wall", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06))),
    dict(t=(32.45, 34.95), src="LIPSYNC", lips="E9_zerow", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1))),
    # --- 3. THE PHONE: «ЗАДАНИЕ ВЫПОЛНЕНО» — «УНИЧТОЖИТЬ ПРЕДЫДУЩУЮ КОПИЮ» — HE TURNS HIS HEAD
    dict(t=(34.95, 37.80), src="E9_vibrate", phone="task9", sub="bottom", cam=((.5, .45, 1.0), (.5, .46, 1.1)), fx=["vibrate"]),
    dict(t=(37.80, 41.80), src="E9_phone49", phone="task9", sub="top", cam=((.5, .58, 1.0), (.5, .6, 1.08))),
    dict(t=(41.80, 45.40), src="E9_turn49", anim=(0.0, 1.0), anim_start=42.05, anim_dur=2.6, sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.14))),
    # --- 4. THE KNIFE (EP08's recording) — «БУДУЩЕЕ НАЧИНАЛО СБЫВАТЬСЯ» — THE STRIKE: THE PHONE
    dict(t=(45.40, 46.50), src="E9_step_back", anim=(0.0, 1.0), sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.04))),
    dict(t=(46.50, 49.30), src="E9_knife_grab", anim=(0.0, 1.0), anim_start=47.55, anim_dur=1.45, sub="bottom", cam=((.5, .5, 1.0), (.5, .48, 1.08))),
    dict(t=(49.30, 50.70), src="E8_rec_knife", sub="top", cam=((.5, .55, 1.0), (.5, .56, 1.1)), fx=["rec", "glitch"]),
    dict(t=(50.70, 52.25), src="E9_knife_fist", sub="bottom", cam=((.5, .45, 1.0), (.5, .45, 1.1)), fx=["handshake"]),
    dict(t=(52.25, 55.45), src="E9_zero_knife", anim=(0.0, 1.0), anim_start=52.3, anim_dur=3.0, sub="bottom", cam=((.5, .45, 1.0), (.5, .44, 1.1)), fx=["redglow"]),
    dict(t=(55.45, 57.75), src="E9_strike", anim=(0.0, 1.0), anim_start=55.6, anim_dur=2.5, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["shake_hits"]),
    dict(t=(57.75, 59.35), src="E9_phone_floor", phone="task9", sub="top", cam=((.5, .55, 1.0), (.5, .56, 1.1)), fx=["shake_hits"]),
    # --- 5. THE SISTER THROUGH THE BROKEN SCREEN — THE «0»
    dict(t=(59.35, 62.15), src="E9_three", sub="bottom", cam=((.5, .45, 1.0), (.5, .46, 1.06)), fx=["tube"]),
    dict(t=(62.15, 64.65), src="LIPSYNC", lips="E8_feedc", sub="bottom", cam=((.5, .44, 1.0), (.5, .44, 1.1)), fx=["cctv", "crackscreen", "glitch"]),
    dict(t=(64.65, 66.25), src="E9_zero_freeze", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.04))),
    dict(t=(66.25, 67.75), src="E9_zero_changed", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.16)), fx=["glitch"]),
    dict(t=(67.75, 72.00), src="E9_wrist0", anim=(0.0, 1.0), anim_start=T_ZERO_ON, anim_dur=T_ZERO - T_ZERO_ON, sub="top", cam=((.5, .55, 1.0), (.5, .58, 1.2)), fx=["redglow_late"]),
    dict(t=(72.00, 73.65), src="E9_zero_look", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.06)), fx=["redglow"]),
    dict(t=(73.65, 76.90), src="LIPSYNC", lips="E9_zero0", sub="bottom", cam=((.5, .42, 1.04), (.5, .41, 1.18)), fx=["redglow"]),
    # --- 6. THE DOOR AGAIN — THE OFFICER, UNMASKED — OLD ALEX
    dict(t=(76.90, 78.45), src="E9_a48_answer", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.05))),
    dict(t=(78.45, 80.40), src="E9_door_open", anim=(0.0, 1.0), anim_start=78.6, anim_dur=1.7, sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08))),
    dict(t=(80.40, 83.20), src="E9_cop_sil", sub="bottom", cam=((.5, .45, 1.0), (.5, .4, 1.14))),
    dict(t=(83.20, 85.30), src="E9_mask", sub="top", cam=((.5, .5, 1.0), (.5, .52, 1.08))),
    dict(t=(85.30, 87.40), src="E9_cop_face", sub="bottom", cam=((.5, .45, 1.12), (.5, .44, 1.0)), fx=["shake_hits"]),
    # --- 7. HIS PHONE: «СОЗДАТЕЛЬ ОБНАРУЖЕН» — «НАЧАТЬ ПОСЛЕДНЮЮ ПРОВЕРКУ» — «ОРИГИНАЛ ДОЛЖЕН УМЕРЕТЬ» — CUT
    dict(t=(87.40, 89.45), src="E9_cop_phone", anim=(0.0, 1.0), anim_start=T_PHONE_UP, anim_dur=1.0, phone="cop9", sub="bottom", cam=((.5, .45, 1.0), (.5, .46, 1.06))),
    dict(t=(89.45, 92.05), src="E9_cop_screen", phone="cop9", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08))),
    dict(t=(92.05, 94.00), src="E9_cop_screen", phone="cop9", sub="top", cam=((.5, .52, 1.12), (.5, .52, 1.22)), fx=["handshake"]),
    dict(t=(94.00, CUT_TO_BLACK), src="E9_cop_screen_close", phone="cop9", sub="top", cam=((.5, .52, 1.0), (.5, .52, 1.08)), fx=["shake_hits"]),
    dict(t=(CUT_TO_BLACK, END), src="BLACK"),
]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
LIP_WINDOWS = [(7.82, 9.72), (28.62, 30.24), (32.60, 34.66), (62.32, 64.40), (73.70, 76.56)]


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
PHONE_CLOCK = "02:55"            # a minute after EP08's lock screen (02:54)
MSG_TASK1, MSG_TASK2 = "Задание выполнено", "Уничтожить предыдущую копию"
MSG_FOUND, MSG_CHECK, MSG_DIE = "Создатель обнаружен", "Начать последнюю проверку", "Оригинал должен умереть"
REC_STAMP = "СБ 07.11"           # EP08's recording stamp (the reused E8_rec_knife frame carries the same REC overlay)
TASK9 = dict(clock=PHONE_CLOCK, t_on=35.30, t1=T_TASK1, t2=T_TASK2, t_crack=T_CRACK, m1=MSG_TASK1, m2=MSG_TASK2)
COP9 = dict(clock=PHONE_CLOCK, t_on=88.00, t1=T_MSG1, t2=T_MSG2, t3=T_MSG3, m1=MSG_FOUND, m2=MSG_CHECK, m3=MSG_DIE)
PHONE = {"task9": [(0, ("task9", TASK9))], "cop9": [(0, ("cop9", COP9))]}
SCREEN_TINT = {}

HITS = [T_GRAB, T_STAB, T_CRACK, T_REVEAL, T_MSG3]           # camera jolts (fx "shake_hits")
BLACKOUT = None
FLASHES = [(T_GRAB, "cold"), (T_49, "cold"), (T_EYES, "red"), (T_KNIFE, "white"), (49.30, "cold"), (T_STAB, "white"), (T_SIS, "red"),
           (T_ZERO, "red"), (82.48, "cold"), (T_REVEAL, "white"), (T_MSG3, "red")]
COUNTDOWN = None
ENDCARD = None
BIG_SUBS = ("«!Оригинал должен умереть!».",)

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger, ¡ = a literal "!")
# Only words that are in the voiceover; at most two lines each. Starts/ends from the word timings and silencedetect.
SUBS = [
    (0.00, 1.70, "За дверью звучал *мой голос*,"),
    (2.18, 4.54, "тот самый, с которого !всё началось!."),
    (5.38, 7.60, "Настоящий Алекс схватил меня *за плечо*."),
    (7.82, 8.40, "«!Прячься¡!»"),
    (8.58, 9.72, "«Он не должен *нас увидеть*»."),
    (10.36, 12.26, "Я спрятался за *кухонной стеной*."),
    (12.58, 13.52, "Замок *щёлкнул*."),
    (13.86, 16.28, "В квартиру вошёл !ещё один я!."),
    (16.72, 18.30, "В руке он держал *стакан воды*."),
    (18.88, 20.96, "Но самое страшное было не это."),
    (21.20, 25.20, "На его запястье светился номер !сорок девять!."),
    (25.64, 28.55, "Я посмотрел на свою руку: *сорок восемь*."),
    (28.62, 30.24, "«*Почему он следующий?*»"),
    (30.82, 32.18, "Настоящий Алекс прошептал:"),
    (32.60, 34.66, "«Потому что тебя !уже списали!»."),
    (35.28, 37.56, "Вдруг телефон нового Алекса *завибрировал*."),
    (37.96, 39.02, "«!Задание выполнено!»."),
    (39.34, 41.48, "«!Уничтожить предыдущую копию!»."),
    (42.08, 45.18, "Он медленно повернул голову — *прямо в мою сторону*."),
    (45.48, 46.28, "Я *отступил*."),
    (46.52, 49.10, "Но настоящий Алекс схватил со стола !нож!."),
    (49.54, 51.96, "Тот самый, который я видел *на записи*."),
    (52.36, 55.00, "Я понял: !будущее начинало сбываться!."),
    (55.44, 57.86, "Но вместо меня он ударил ножом *по телефону*."),
    (58.08, 59.14, "Экран *раскололся*."),
    (59.50, 61.98, "Все трое одновременно услышали *голос сестры*."),
    (62.32, 64.40, "«Алекс, !не верь оригиналу¡!»"),
    (64.82, 65.88, "Настоящий Алекс *замер*."),
    (66.16, 67.26, "Его лицо *изменилось*."),
    (67.70, 71.62, "И вдруг на его запястье загорелся номер: !ноль!."),
    (71.96, 73.06, "Он посмотрел на меня."),
    (73.70, 76.56, "«Теперь ты понимаешь, почему я *не могу выйти отсюда*?»"),
    (77.22, 78.36, "Я хотел ответить,"),
    (78.46, 80.24, "но входная дверь *снова открылась*."),
    (80.42, 82.90, "На пороге стоял полицейский. !Без маски!."),
    (83.22, 85.58, "Под маской всё это время был *я*,"),
    (85.96, 87.18, "только !намного старше!."),
    (87.44, 88.30, "Он *поднял телефон*."),
    (88.74, 90.32, "На экране появилось сообщение:"),
    (90.68, 91.96, "«!Создатель обнаружен!»."),
    (92.10, 93.76, "«!Начать последнюю проверку!»."),
    (94.06, 96.02, "«!Оригинал должен умереть!»."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.05, "sting_soft", 0.4), (0.30, "breath", 0.5), (1.20, "heavy_step", 0.3), (2.00, "heavy_step", 0.28), (3.6, "boom_tail", 0.35)]
    + [(5.40, "whoosh", 0.6), (T_GRAB, "cloth", 0.8), (T_GRAB + 0.05, "gasp", 0.5), (7.80, "sting_soft", 0.5)]
    + [(10.40, "cloth", 0.5), (11.00, "step", 0.4), (11.90, "breath", 0.5)]
    + [(T_CLICK, "lock_clack", 1.0), (T_CLICK + 0.04, "lock_click", 0.8), (13.00, "door_creak", 0.7), (13.35, "door_open", 0.45)]
    + [(14.30, "step", 0.6), (14.90, "step", 0.6), (15.50, "step", 0.55), (16.10, "step", 0.5), (17.60, "glass", 0.35)]
    + [(21.65, "number_burn", 0.8), (22.24, "shimmer", 0.5), (T_49, "sting", 0.6)]
    + [(25.70, "dissolve", 0.6), (26.80, "wires_hum", 0.5), (28.50, "breath", 0.4), (30.80, "sting_soft", 0.5)]
    + [(t, "vibrate", 1.0) for t in T_VIB]
    + [(T_TASK1, "notify_bad", 0.8), (T_TASK2, "notify_bad", 0.9), (T_TASK2, "sting", 0.5)]
    + [(42.10, "cloth", 0.4), (43.30, "sting_soft", 0.5), (T_EYES, "sting", 0.8), (45.50, "step", 0.5), (45.60, "breath", 0.5)]
    + [(47.85, "knife_scrape", 1.0), (T_KNIFE, "sting", 0.7), (49.30, "rec_start", 0.8), (49.32, "glitch", 0.6), (50.70, "glitch", 0.4)]
    + [(52.40, "step", 0.5), (53.10, "step", 0.5), (53.30, "boom_tail", 0.4), (53.80, "step", 0.5)]
    + [(55.70, "whoosh", 0.9), (T_STAB, "knife_stab", 1.0), (T_STAB + 0.02, "glass_crack", 0.8), (57.40, "phone_drop", 1.0)]
    + [(T_CRACK, "glass_crack", 0.8), (T_CRACK + 0.04, "glitch", 0.7)]
    + [(59.40, "voice_static", 0.8), (60.60, "glitch", 0.4), (62.25, "voice_static", 1.0), (T_SIS, "sting", 0.5)]
    + [(64.80, "boom_tail", 0.5), (66.20, "glitch", 0.4), (66.30, "sting_soft", 0.5)]
    + [(T_ZERO_ON, "zero_on", 1.0), (T_ZERO, "attempt_hit", 0.7), (72.00, "breath", 0.4)]
    + [(77.20, "breath", 0.4), (T_DOOR, "door_creak", 0.9), (T_DOOR + 0.2, "door_open", 0.8)]
    + [(80.42, "heavy_step", 0.6), (81.10, "heavy_step", 0.5), (82.48, "sting", 0.6), (83.40, "cloth", 0.6)]
    + [(T_REVEAL, "attempt_hit", 1.0), (T_REVEAL, "sting", 0.7)]
    + [(87.50, "cloth", 0.5), (88.00, "phone_on", 0.8), (T_MSG1, "notify_bad", 0.9), (T_MSG2, "notify_bad", 0.9), (T_MSG2, "type_lock", 0.5)]
    + [(T_MSG3, "delete_alarm", 0.9), (T_MSG3, "sting", 0.9), (CUT_TO_BLACK, "final_hit", 1.0)]
)
HUM = []
CORRIDOR = []
MONHUM = []
FLAT = [(0.0, CUT_TO_BLACK)]              # flat 47 at night: the fridge hum from the kitchen, a faint clock
# music intensity curve (time, level 0..1): picks up low after EP08's hard cut, climbs on «49», drops to a whisper under the
# whispered lines, rises with the phone and the knife, peaks on the strike, pulls back for the sister and the «0», climbs from the
# door to the last message and stops dead on the cut
MUSIC = [(0, .45), (2.1, .4), (5.3, .65), (7.8, .55), (10.3, .45), (12.5, .55), (16.5, .5), (21.1, .6), (23.4, .8), (25.4, .55), (28.5, .3),
         (34.9, .45), (37.9, .7), (41.8, .75), (44.6, .85), (46.5, .7), (48.9, .85), (52.3, .9), (57.0, .97), (59.3, .45), (62.3, .55),
         (64.6, .3), (69.8, .6), (71.1, .85), (73.6, .4), (76.9, .45), (78.5, .7), (82.5, .75), (85.3, .9), (87.4, .6), (90.7, .75),
         (94.0, .95), (CUT_TO_BLACK, 1.0)]
MUSIC_TAIL = False                         # no end card: dead silence after the cut
BELLS = [(0.1, 880.0), (T_49, 987.8), (30.8, 784.0), (T_SIS, 932.3), (T_ZERO, 987.8), (T_REVEAL, 880.0)]
RISER = (87.4, CUT_TO_BLACK)


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
    # no on-screen message before its words
    assert TASK9["t1"] >= 37.96 and TASK9["t2"] >= 39.34 and COP9["t1"] >= 90.68 and COP9["t2"] >= 92.10 and COP9["t3"] >= 94.06


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, subtitles=SUBS, sfx=SFX, flat=FLAT, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep09_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
