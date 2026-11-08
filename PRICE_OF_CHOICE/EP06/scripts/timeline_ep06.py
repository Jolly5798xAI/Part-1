"""EP06 «ПЕРВАЯ ПОПЫТКА» — editing timeline (single source of truth). Same format as EP05 (../EP05/scripts/timeline_ep05.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper small, word timestamps); phrase starts checked against
silencedetect (docs/EP06_VO_REPORT.md). Verified text: docs/EP06_transcript.txt.

EP06 opens on EP05's last shot — the sister's close-up behind Alex in room 204 (EP05 lip-sync stills E5_sis_*, EP05's end
framing (0.5, 0.44, ×1.25)) — while the approved VO repeats her question «Зачем ты снова запустил игру?». Same room, no time jump.

Lip-sync: the sister's lines, Alex's words on the recording (drawn inside the phone screen) and the old Alex's warning in the
mirror pick their mouth shape frame by frame from the VO envelope. The narrator voices every line (no second voice).

`python3 scripts/timeline_ep06.py` checks the timeline and writes timeline/ep06_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 85.89           # the approved MP3 is 85.89 s; the last word «себя» ends at 85.77
CUT_TO_BLACK = 85.95
END = 88.30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- shots
# src: still name (scenes/<src>.png, else ../EP05/scenes, ../EP04/scenes, ../EP03/scenes, ../EP02/illustrations), anim folder
#      (scenes/<src>/), "LIPSYNC" (+ lips=<base>; shape from LIPSYNC by time) or "BLACK".  cam: (cx, cy, zoom) start -> end.
# phone: state drawn on the scene's phone screen; screens: state drawn on EVERY phone of the table in room 204.
T_DOOR = 58.30           # «…дверь комнаты исчезла» — the door is gone (hard cut + flash)
T_OLD = 62.88            # «…только гораздо старше» — the reflection is the old Alex
SHOTS = [
    # --- 1. THE QUESTION (EP05's last shot continues: her close-up, EP05's end framing)
    dict(t=(0.00, 2.30), src="LIPSYNC", lips="E5_sis", sub="top", cam=((.5, .44, 1.25), (.5, .44, 1.36)), fx=["handshake"]),
    dict(t=(2.30, 3.50), src="E6_turn", anim=(0.0, 1.0), anim_start=2.30, anim_dur=1.0, cam=((.5, .45, 1.0), (.5, .43, 1.08)), screens="creator"),
    dict(t=(3.50, 5.95), src="E6_sisf_neutral", cam=((.5, .45, 1.0), (.5, .43, 1.16))),
    dict(t=(5.95, 7.80), src="E4_sister_photo", cam=((.5, .5, 1.0), (.5, .46, 1.15)), fx=["memory"]),
    # --- 2. «НЕ ПОДХОДИ. СНАЧАЛА ПОСМОТРИ»
    dict(t=(7.80, 10.50), src="E6_step", anim=(0.0, 1.0), anim_start=7.98, anim_dur=2.2, cam=((.5, .45, 1.0), (.47, .45, 1.08))),
    dict(t=(10.50, 12.70), src="LIPSYNC", lips="E6_sisf", sub="top", cam=((.5, .44, 1.08), (.5, .43, 1.22))),
    dict(t=(12.70, 14.45), src="E6_point", cam=((.5, .45, 1.0), (.47, .45, 1.1))),
    # --- 3. THE RECORDING (the same table, the same room)
    dict(t=(14.45, 16.60), src="E5_room_lit", cam=((.5, .55, 1.05), (.5, .58, 1.2)), screens="creator"),
    dict(t=(16.60, 20.70), src="E5_phone_hero", sub="top", cam=((.5, .52, 1.0), (.5, .54, 1.22)), phone="rec", screens="creator"),
    dict(t=(20.70, 24.95), src="E5_phone_hero", sub="top", cam=((.5, .54, 1.3), (.5, .55, 1.48)), phone="rec", screens="creator", fx=["tube"]),
    dict(t=(24.95, 26.75), src="E6_alex", cam=((.5, .42, 1.0), (.5, .42, 1.12))),
    dict(t=(26.75, 28.70), src="E6_show_wide", cam=((.5, .48, 1.0), (.47, .52, 1.1)), phone="attempt"),
    # --- 4. ATTEMPT 47
    dict(t=(28.70, 32.45), src="E6_show", sub="top", cam=((.72, .6, 1.4), (.76, .52, 1.75)), phone="attempt"),
    dict(t=(32.45, 36.00), src="E6_show", sub="top", cam=((.76, .58, 1.7), (.76, .66, 1.75)), phone="attempt", fx=["redglow"]),
    dict(t=(36.00, 38.15), src="E6_alex", cam=((.5, .42, 1.1), (.5, .42, 1.25))),
    dict(t=(38.15, 40.25), src="E6_sisf_neutral", cam=((.5, .44, 1.05), (.5, .43, 1.38))),
    dict(t=(40.25, 41.45), src="LIPSYNC", lips="E6_sisf", sub="top", cam=((.5, .43, 1.45), (.5, .43, 1.55))),
    # --- 5. THE PHONES SHAKE — THE COUNTDOWN
    dict(t=(41.45, 44.00), src="E5_phones_low", cam=((.5, .5, 1.0), (.5, .5, 1.1)), screens="buzz", fx=["vibrate"]),
    dict(t=(44.00, 46.30), src="E6_room_red", cam=((.5, .55, 1.05), (.5, .58, 1.18)), screens="count", fx=["redglow"]),
    dict(t=(46.30, 47.40), src="E5_phone_hero", sub="top", cam=((.5, .54, 1.3), (.5, .54, 1.42)), phone="count", screens="count"),
    dict(t=(47.40, 48.30), src="E6_phones_red", cam=((.5, .5, 1.05), (.5, .5, 1.12)), screens="count"),
    dict(t=(48.30, 49.50), src="E6_room_red", cam=((.5, .58, 1.2), (.5, .6, 1.3)), screens="count"),
    dict(t=(49.50, 51.65), src="E6_alex_red", cam=((.5, .42, 1.0), (.5, .42, 1.14)), fx=["redglow"]),
    dict(t=(51.65, 53.70), src="E6_grab", anim=(0.0, 1.0), anim_start=51.80, anim_dur=0.7, cam=((.5, .45, 1.0), (.48, .45, 1.08)), screens="count", fx=["handshake"]),
    dict(t=(53.70, 55.55), src="LIPSYNC", lips="E6_sisf", sub="bottom", cam=((.5, .40, 1.2), (.5, .40, 1.32)), fx=["redglow"]),
    # --- 6. THE DOOR IS GONE — THE MIRROR
    dict(t=(55.55, T_DOOR), src="E6_run", anim=(0.0, 1.0), anim_start=55.65, anim_dur=2.3, cam=((.5, .45, 1.0), (.5, .43, 1.12)), screens="count", fx=["handshake"]),
    dict(t=(T_DOOR, 59.15), src="E6_exit_wall", cam=((.5, .43, 1.12), (.5, .43, 1.16)), screens="count", fx=["glitch"]),
    dict(t=(59.15, 60.95), src="E6_mirror_form", anim=(0.0, 1.0), anim_start=59.20, anim_dur=1.55, cam=((.5, .43, 1.16), (.5, .42, 1.24)), screens="count"),
    dict(t=(60.95, T_OLD), src="E6_mirror_young", cam=((.5, .42, 1.0), (.47, .4, 1.14)), screens="count"),
    dict(t=(T_OLD, 64.65), src="E6_mirror_old", cam=((.47, .4, 1.14), (.45, .38, 1.3)), screens="count", fx=["glitch"]),
    dict(t=(64.65, 67.50), src="E6_palm", anim=(0.0, 1.0), anim_start=64.90, anim_dur=1.42, cam=((.5, .42, 1.0), (.5, .42, 1.08)), screens="count"),
    dict(t=(67.50, 69.35), src="LIPSYNC", lips="E6_old", sub="bottom", cam=((.5, .42, 1.1), (.5, .42, 1.2)), fx=["tube"]),
    dict(t=(69.35, 72.10), src="LIPSYNC", lips="E6_old", sub="bottom", cam=((.52, .38, 1.35), (.52, .37, 1.5)), fx=["tube"]),
    # --- 7. SHE NO LONGER SMILES — THE LAST TASK
    dict(t=(72.10, 73.75), src="E6_turn_back", anim=(0.0, 1.0), anim_start=72.12, anim_dur=1.5, cam=((.5, .45, 1.0), (.5, .44, 1.06)), screens="count"),
    dict(t=(73.75, 75.45), src="E6_sis_cold", cam=((.5, .44, 1.05), (.5, .43, 1.25)), fx=["redglow"]),
    dict(t=(75.45, 78.00), src="E6_sis_phone", cam=((.4, .55, 1.08), (.35, .58, 1.2)), phone="final"),
    dict(t=(78.00, 81.55), src="E6_show_cold", sub="top", cam=((.72, .62, 1.4), (.76, .58, 1.65)), phone="final"),
    dict(t=(81.55, 83.75), src="E6_show_cold", sub="top", cam=((.76, .6, 1.65), (.76, .64, 1.72)), phone="final"),
    dict(t=(83.75, CUT_TO_BLACK), src="E6_show_cold", sub="top", cam=((.76, .68, 1.72), (.76, .7, 1.85)), phone="final", fx=["handshake", "redglow"]),
    dict(t=(CUT_TO_BLACK, END), src="BLACK", fx=["endcard"]),
]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
# the sister: the question, «Не подходи. Сначала посмотри», «Твоей», «Ты снова всё забудешь»; Alex on the recording;
# the old Alex in the mirror: «Не верь ей, она не твоя сестра»
LIP_WINDOWS = [(0.00, 2.22), (10.62, 12.53), (20.74, 24.49), (40.37, 40.90), (53.82, 55.17), (68.16, 71.32)]


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


# ---------------------------------------------------------------- phone screen states (same UI as EP01–EP05, text drawn in code)
PHONE_CLOCK = "02:53"                                   # EP05: 02:52
MSG_CREATOR = "С возвращением, создатель."              # EP05 — still on every screen when EP06 opens
MSG_REC = "Если я снова сюда вернусь, не позволяйте мне вспомнить."
MSG_ATTEMPT = "Попытка номер сорок семь."
MSG_PREV = "Предыдущие сорок шесть завершились смертью."
MSG_LAST = "Последнее задание."
MSG_CHOOSE = "Выбери, кого стереть."
MSG_CHOICE = "Сестру или себя."
ATTEMPT_N = 47
T_REC, T_REC_CAP = 16.60, 20.74                          # the recording starts playing / Alex says the line
T_SHOW, T_ATTEMPT, T_PREV = 26.88, 29.96, 32.48
T_BUZZ, T_COUNT = 41.54, 44.64
COUNT = (46.50, 10, 55.60)                               # «Десять» at 46.50, one per second; frozen at «00:01» when Alex runs
T_FINAL_ON, T_LAST, T_CHOOSE, T_SIS, T_SELF = 78.66, 80.22, 81.66, 83.92, 85.07
PHONE = {
    # every phone in room 204 as EP05 left them
    "creator": [(0, ("header", "Номер скрыт")), (0, ("bubble_red", MSG_CREATOR))],
    # one phone plays a recording: Alex at this very table (lip-sync from the VO, his line as a caption at T_REC_CAP)
    "rec": [(0, ("header", "Номер скрыт")), (0, ("bubble_red", MSG_CREATOR)), (T_REC, ("video", {"src": "E6_rec", "start": T_REC, "cap": MSG_REC, "cap_t": T_REC_CAP}))],
    # the second phone the sister shows: «typing…», then the attempt counter on «Попытка…», the 46 crossed-out attempts on «Предыдущие…»
    "attempt": [(0, ("header", "Номер скрыт")), (T_SHOW, ("typing", None)), (T_ATTEMPT, ("attempt", MSG_ATTEMPT)), (T_PREV, ("attempt_prev", MSG_PREV))],
    # every phone vibrates and glitches on «завибрировали», the countdown lands on «появился обратный отсчёт»
    "buzz": [(0, ("header", "Номер скрыт")), (0, ("bubble_red", MSG_CREATOR)), (T_BUZZ, ("glitch", None))],
    "count": [(0, ("header", "Номер скрыт")), (0, ("bubble_red", MSG_CREATOR)), (T_BUZZ, ("glitch", None)), (T_COUNT, ("count", COUNT))],
    # the same phone in her hand: the last task, then the choice — her photo «СЕСТРУ» on «Сестру», his «СЕБЯ» on «…или себя»
    "final": [(0, ("header", "Номер скрыт")), (T_FINAL_ON, ("typing", None)), (T_LAST, ("bubble_red", MSG_LAST)), (T_CHOOSE, ("bubble_red", MSG_CHOOSE)),
              (T_SIS, ("choice", {"text": MSG_CHOICE, "left": ("E4_sister_photo", "СЕСТРУ"), "right": ("E6_alex_portrait", "СЕБЯ"), "t_right": T_SELF}))],
}
SCREEN_TINT = {"count": (215, 70, 60)}                  # the countdown throws red light (default: cold blue, as in EP05)

# jolts -> camera shake (fx "shake_hits"); none needed in EP06 (the vibration uses fx "vibrate" + the "vibrate" sfx)
HITS = [T_DOOR]
BLACKOUT = None
FLASHES = [(T_ATTEMPT, "red"), (40.37, "red"), (T_DOOR, "white"), (T_OLD, "cold"), (T_SIS, "red"), (T_SELF, "red"), (CUT_TO_BLACK - 0.04, "white")]
# countdown card at the top of non-phone shots: (show_from, start, seconds, until, frozen_at)
COUNTDOWN = (T_COUNT, COUNT[0], COUNT[1], T_DOOR, COUNT[2])
ENDCARD = ("Серия 6 · «Первая попытка»", "Продолжение следует")
BIG_SUBS = ("«!Твоей!».", "!Она не твоя сестра!».", "«!Сестру… или себя!».", "«!Попытка номер 47!».")

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger, ¡ = a literal "!")
# Only words that are in the voiceover; at most two lines each. Starts from silencedetect, ends from word timings.
SUBS = [
    (0.02, 2.22, "«!Зачем ты снова запустил игру?!»"),
    (2.30, 3.22, "Я *обернулся*."),
    (3.62, 5.90, "Передо мной стояла *сестра*, та самая,"),
    (5.98, 7.62, "что !исчезла три года назад!."),
    (8.00, 10.28, "Я бросился к ней, но она *отступила*."),
    (10.62, 12.52, "«!Не подходи!. Сначала *посмотри*»."),
    (12.86, 14.22, "Она указала на *телефоны*."),
    (14.56, 16.55, "На одном из экранов шла *запись*."),
    (17.16, 20.22, "Я сидел *за этим же столом* и говорил в камеру:"),
    (20.74, 22.38, "«!Если я снова сюда вернусь,!"),
    (22.70, 24.48, "!не позволяйте мне вспомнить!»."),
    (25.18, 26.66, "Я не понимал, что происходит."),
    (26.88, 28.42, "Сестра показала *второй экран*."),
    (28.76, 29.94, "На нём было написано:"),
    (29.96, 32.08, "«!Попытка номер 47!»."),
    (32.48, 35.62, "Предыдущие *46* !завершились смертью!."),
    (36.36, 38.18, "Я спросил: «*Чьей смертью?*»"),
    (38.40, 39.90, "Сестра посмотрела на меня."),
    (40.36, 41.40, "«!Твоей!»."),
    (41.58, 43.80, "В этот момент все телефоны *завибрировали*,"),
    (44.02, 46.12, "на экранах появился !обратный отсчёт!."),
    (46.42, 47.30, "!Десять!."),
    (47.42, 48.22, "!Девять!."),
    (48.30, 49.30, "!Восемь!."),
    (49.58, 51.40, "Что будет, когда *время закончится*?"),
    (51.80, 53.44, "Сестра *схватила меня за руку*."),
    (53.82, 55.40, "«Ты снова !всё забудешь!»."),
    (55.80, 57.10, "Я попытался *выбежать*,"),
    (57.28, 58.95, "но дверь комнаты !исчезла!."),
    (59.16, 60.90, "Вместо неё появилось *зеркало*."),
    (61.10, 62.62, "В отражении стоял *Алекс*,"),
    (62.88, 64.50, "только !гораздо старше!."),
    (64.74, 67.58, "Он приложил *ладонь к стеклу* и произнёс:"),
    (68.16, 69.30, "«!Не верь ей!."),
    (69.40, 71.80, "!Она не твоя сестра!»."),
    (72.21, 73.56, "Я *медленно* повернулся."),
    (73.88, 75.30, "Сестра больше !не улыбалась!."),
    (75.56, 77.74, "В её руке был *тот самый телефон*."),
    (78.12, 79.84, "На экране появилось сообщение:"),
    (80.26, 81.46, "«!Последнее задание!."),
    (81.70, 83.36, "Выбери, *кого стереть*."),
    (83.90, 85.88, "«!Сестру… или себя!»."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
TICKS = [COUNT[0] + i for i in range(10)]                 # 46.5 … 55.5: one tick per second until the count freezes
SFX = (
    [(2.30, "whoosh", 0.7), (2.40, "cloth", 0.5), (3.55, "sting_soft", 0.6), (5.95, "sting_soft", 0.5)]
    + [(t, "step", 0.6) for t in (8.05, 8.45)] + [(t, "step", 0.35) for t in (9.40, 9.80)] + [(10.40, "breath", 0.5), (12.90, "cloth", 0.4)]
    + [(14.50, "sting_soft", 0.5), (T_REC, "rec_start", 0.9), (T_REC_CAP, "sting_soft", 0.6), (24.60, "sting", 0.6)]
    + [(26.90, "cloth", 0.5), (27.40, "phone_on", 0.7), (T_ATTEMPT, "attempt_hit", 1.0), (T_ATTEMPT, "notify_bad", 0.6), (T_PREV, "x_marks", 0.9)]
    + [(38.30, "breath", 0.5), (40.37, "sting", 0.9), (40.37, "boom_tail", 0.5)]
    + [(T_BUZZ, "phones_buzz", 1.0)] + [(t, "vibrate", 0.8) for t in (T_BUZZ, 42.50, 43.45)] + [(T_COUNT, "glitch", 0.7), (T_COUNT, "sting", 0.6)]
    + [(t, "tick_hard", 0.9) for t in TICKS]
    + [(51.80, "cloth", 0.8), (51.85, "gasp", 0.6), (53.75, "breath", 0.5), (55.62, "whoosh", 0.7)]
    + [(t, "step", 0.75) for t in (55.85, 56.15, 56.45, 56.75, 57.05, 57.35, 57.65, 57.95)]
    + [(T_DOOR, "door_vanish", 1.0), (T_DOOR, "glitch", 0.8), (59.20, "mirror_form", 0.9), (59.25, "shimmer", 0.6), (60.80, "glass_ring", 0.6)]
    + [(T_OLD, "sting", 0.8), (T_OLD, "glitch", 0.6), (66.32, "glass_ring", 1.0), (66.32, "hit", 0.25), (68.12, "sting_soft", 0.6)]
    + [(72.15, "cloth", 0.4), (73.88, "sting_soft", 0.7), (75.60, "cloth", 0.4), (T_FINAL_ON, "phone_on", 0.7)]
    + [(T_LAST, "notify_bad", 0.75), (T_LAST, "sting", 0.5), (T_CHOOSE, "notify_bad", 0.7), (T_SIS, "final_hit", 0.8), (T_SELF, "final_hit", 1.0)]
    + [(CUT_TO_BLACK, "boom_tail", 0.9), (CUT_TO_BLACK, "sting", 0.6)]
)
HUM = [(0.0, CUT_TO_BLACK)]           # the phones' electric hum, the whole episode (room 204)
CORRIDOR = [(0.0, T_DOOR)]            # the corridor's air through the open door — it stops dead when the door vanishes
# music intensity curve (time, level 0..1): picks up at EP05's end level; drops for the recording, «Твоей», the frozen count
# and the old Alex's words; rises to the last task; hard stop at the cut
MUSIC = [(0, .25), (2.3, .4), (7.8, .5), (10.5, .4), (14.4, .35), (16.6, .25), (24.9, .45), (29.9, .7), (35.9, .45), (40.3, .2), (41.4, .7),
         (44.6, .8), (46.4, .85), (55.6, .9), (55.65, .15), (58.3, .6), (60.9, .45), (62.9, .7), (64.6, .4), (67.5, .25), (72.1, .45), (73.8, .55),
         (78.0, .65), (80.2, .75), (83.9, .9), (CUT_TO_BLACK, .9)]
BELLS = [(3.55, 880.0), (16.62, 987.8), (29.98, 784.0), (40.4, 932.3), (59.2, 987.8), (62.9, 880.0), (83.95, 987.8)]
RISER = (75.4, 83.9)


def check():
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    assert SHOTS[0]["t"][0] == 0 and SHOTS[-1]["t"][1] == END
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)
    assert SUBS[-1][1] <= VO_END + 0.05
    assert all(0 <= t < END for t, _, _ in SFX)
    for s in SHOTS:
        assert s.get("phone") in (None, *PHONE) and s.get("screens") in (None, *PHONE), s
    for a, b in LIP_WINDOWS:
        if (a, b) == (T_REC_CAP, 24.49): continue                      # drawn inside the phone screen (shots with phone="rec")
        lip = [s["t"] for s in SHOTS if s["src"] == "LIPSYNC"]
        assert all(any(x <= f / FPS < y for x, y in lip) for f in range(int(a * FPS), int(b * FPS))), ("lip window not covered", a, b)


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, countdown=COUNTDOWN, subtitles=SUBS, sfx=SFX, hum=HUM, corridor=CORRIDOR, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep06_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
