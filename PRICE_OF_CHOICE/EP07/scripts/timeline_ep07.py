"""EP07 «ТОТ, КОГО СТЁРЛИ» — editing timeline (single source of truth). Same format as EP06 (../EP06/scripts/timeline_ep06.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper small, the same CTranslate2 int8 model as EP03–EP06, sha256 ca732cb1…ce73);
phrase starts/ends checked against silencedetect (docs/EP07_VO_REPORT.md). Verified text: docs/EP07_transcript.txt.

EP07 opens on EP06's last shot — the phone in the sister's hand with the choice «Сестру или себя» (EP06 still E6_show_cold,
EP06's end framing (0.76, 0.70, ×1.85)) — while the approved VO repeats «Сестру… или себя…». Same room, same second, no recap.

Lip-sync: the sister's lines in room 204 («Выбирай себя…»), the old Alex in the mirror («Не нажимай!», «Она уже стёрла тебя…»),
Alex («Тогда почему я ещё здесь?») and the sister on the feed («Алекс… найди настоящего себя») pick their mouth shape frame by frame
from the VO envelope. The narrator voices every line (no second voice).

`python3 scripts/timeline_ep07.py` checks the timeline and writes timeline/ep07_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 101.15          # the approved MP3 is 101.146 s; the last word «день» ends at ~101.0
CUT_TO_BLACK = 101.15
END = 103.15
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- key moments (VO clock)
T_FIVE = 4.56            # «…пять секунд» — the timer reads 00:05
T_DROP = 20.29           # the phone hits the floor
T_ZERO = 22.66           # «…одна» ends — 00:00
T_OFF = 22.90            # «Все экраны погасли»
T_VANISH = 24.25         # «Сестра исчезла»
T_MTEXT, T_MTEXT_OK = 26.05, 27.57   # the letters crawl onto the glass / lock into «Выбор сделан» on the words
T_PUNCH = 32.60          # «…ударил по стеклу» — the fist hits, the glass cracks
T_48 = 45.78             # «Сорок восемь»
T_SHATTER = 60.12        # «…зеркало раскололось»
T_PRESS = 71.60          # «Она нажала кнопку»
T_MON_RED = 73.10        # «Все мониторы показали…» — every monitor goes red
T_MSG1, T_MSG2 = 75.20, 77.54        # «Экземпляр сорок восемь нестабилен» / «Начать удаление»
T_ERASE = 80.35          # «…как исчезает моя левая рука»
T_ADDR_SCREEN, T_STREET, T_FLAT = 89.62, 93.95, 95.74
T_DATE, T_TOMORROW = 98.86, 100.18

# ---------------------------------------------------------------- shots
# src: still name (scenes/<src>.png, else ../EP06/scenes, ../EP05/scenes, …), anim folder (scenes/<src>/), "LIPSYNC" (+ lips=<base>) or "BLACK".
# cam: (cx, cy, zoom) start -> end.  phone: state drawn on the scene's phone screen; screens: state on every phone of the table;
# monitor: state drawn on the one readable monitor (E7_mon*); monitors: state on every monitor of the wall (E7_wall*);
# mtext: the message on mirror 204 (E7_mirror_front).
MTEXT = dict(text="Выбор сделан", scramble=T_MTEXT, legible=T_MTEXT_OK)
SHOTS = [
    # --- 1. FIVE SECONDS (EP06's last shot continues: her phone, the choice)
    dict(t=(0.00, 1.68), src="E6_show_cold", sub="bottom", cam=((.76, .70, 1.85), (.75, .66, 1.98)), phone="hers", fx=["handshake", "redglow"]),
    dict(t=(1.68, 3.50), src="E6_sis_cold", cam=((.5, .44, 1.05), (.5, .43, 1.28)), fx=["redglow"]),
    dict(t=(3.50, 6.25), src="E7_phone_pov", sub="top", cam=((.5, .62, 1.0), (.5, .64, 1.16)), phone="mine"),
    dict(t=(6.25, 8.35), src="E7_sisc_neutral", cam=((.5, .45, 1.0), (.5, .44, 1.14)), fx=["redglow"]),
    dict(t=(8.35, 10.95), src="E7_reach", anim=(0.0, 1.0), anim_start=8.50, anim_dur=1.75, sub="top", cam=((.5, .62, 1.0), (.5, .63, 1.1)), phone="mine"),
    # --- 2. «ВЫБИРАЙ СЕБЯ» / «НЕ НАЖИМАЙ!»
    dict(t=(10.95, 12.70), src="LIPSYNC", lips="E7_sisc", sub="bottom", cam=((.5, .44, 1.0), (.5, .43, 1.08))),
    dict(t=(12.70, 14.95), src="LIPSYNC", lips="E7_sisc", sub="bottom", cam=((.5, .42, 1.1), (.5, .42, 1.18)), fx=["redglow"]),
    dict(t=(14.95, 17.35), src="E6_mirror_old", cam=((.47, .4, 1.1), (.45, .38, 1.3)), screens="table5", fx=["glitch"]),
    dict(t=(17.35, 19.05), src="LIPSYNC", lips="E6_old", sub="bottom", cam=((.5, .42, 1.12), (.5, .42, 1.3)), fx=["handshake", "tube"]),
    # --- 3. THE PHONE ON THE FLOOR — 3, 2, 1 — THE SCREENS DIE — SHE IS GONE
    dict(t=(19.05, 20.85), src="E7_throw", anim=(0.0, 1.0), anim_start=19.45, anim_dur=1.2, sub="top", cam=((.5, .5, 1.0), (.5, .52, 1.06)), phone="mine", fx=["shake_hits"]),
    dict(t=(20.85, T_ZERO + 0.04), src="E7_floor_phone", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.3)), phone="floor"),
    dict(t=(T_ZERO + 0.04, T_OFF), src="E6_room_red", cam=((.5, .58, 1.2), (.5, .58, 1.22)), screens="table5"),
    dict(t=(T_OFF, 24.15), src="E7_room_dark", cam=((.5, .56, 1.05), (.5, .57, 1.13))),
    dict(t=(24.15, 25.40), src="E7_sis_vanish", anim=(0.0, 1.0), anim_start=T_VANISH, anim_dur=0.95, cam=((.5, .48, 1.0), (.5, .47, 1.06))),
    # --- 4. «ВЫБОР СДЕЛАН»
    dict(t=(25.40, 27.55), src="E7_mirror_front", mtext=MTEXT, cam=((.5, .40, 1.0), (.48, .38, 1.12))),
    dict(t=(27.55, 29.55), src="E7_mirror_front", mtext=MTEXT, sub="bottom", cam=((.48, .35, 1.3), (.48, .34, 1.45))),
    dict(t=(29.55, 31.05), src="E7_alex_dark", cam=((.5, .44, 1.0), (.5, .43, 1.12))),
    # --- 5. THE FIST — THE CRACKS — «СОРОК ШЕСТЬ РАЗ»
    dict(t=(31.05, 33.25), src="E7_punch", anim=(0.0, 1.0), anim_start=31.62, anim_dur=1.36, sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.06)), fx=["shake_hits"]),
    dict(t=(33.25, 34.80), src="E7_oldc_neutral", cam=((.5, .42, 1.06), (.5, .42, 1.16))),
    dict(t=(34.80, 36.30), src="LIPSYNC", lips="E7_oldc", sub="bottom", cam=((.5, .42, 1.16), (.5, .42, 1.26)), fx=["tube"]),
    dict(t=(36.30, 38.45), src="LIPSYNC", lips="E7_oldc", sub="bottom", cam=((.52, .38, 1.36), (.52, .37, 1.52)), fx=["tube"]),
    dict(t=(38.45, 40.10), src="E7_step_back", anim=(0.0, 1.0), anim_start=38.95, anim_dur=0.9, cam=((.5, .45, 1.0), (.5, .44, 1.06))),
    dict(t=(40.10, 41.80), src="LIPSYNC", lips="E7_alexd", sub="bottom", cam=((.5, .44, 1.0), (.5, .43, 1.1))),
    # --- 6. 48 — THE CLEAR SKIN — THE WIRES
    dict(t=(41.80, 43.30), src="E7_old_point", cam=((.5, .42, 1.0), (.5, .44, 1.1))),
    dict(t=(43.30, T_48 - 0.08), src="E7_wrist", anim=(0.0, 1.0), anim_start=43.40, anim_dur=2.30, cam=((.5, .42, 1.0), (.53, .38, 1.15))),
    dict(t=(T_48 - 0.08, 47.25), src="E7_wrist", anim=(1.0, 1.0), cam=((.55, .32, 1.55), (.55, .32, 1.8)), sub="bottom", fx=["redglow"]),
    dict(t=(47.25, 49.10), src="E7_wrist_rub", anim=(0.0, 1.0), cam=((.5, .4, 1.1), (.5, .38, 1.18))),
    dict(t=(49.10, 51.85), src="E7_wrist_clear", anim=(0.0, 1.0), anim_start=49.35, anim_dur=2.2, cam=((.5, .42, 1.05), (.5, .42, 1.14))),
    dict(t=(51.85, 53.70), src="E7_wrist_wires", cam=((.5, .45, 1.0), (.5, .42, 1.18)), fx=["leakflicker"]),
    dict(t=(53.70, 56.35), src="E7_realize", cam=((.5, .42, 1.0), (.5, .41, 1.14))),
    dict(t=(56.35, 58.95), src="E7_wide_copy", cam=((.5, .5, 1.0), (.48, .48, 1.12))),
    # --- 7. THE MIRROR BURSTS — THE MONITOR ROOM — HER ON THE SCREEN
    dict(t=(58.95, 61.05), src="E7_shatter", anim=(0.0, 1.0), anim_start=T_SHATTER, anim_dur=0.9, cam=((.5, .45, 1.06), (.5, .45, 1.0)), fx=["shake_hits"]),
    dict(t=(61.05, 63.35), src="E7_reveal", cam=((.5, .45, 1.0), (.5, .44, 1.2))),
    dict(t=(63.35, 65.60), src="E7_monitor_sis", cam=((.5, .48, 1.0), (.5, .47, 1.15))),
    dict(t=(65.60, 69.35), src="E7_feed", cam=((.5, .45, 1.0), (.5, .42, 1.22)), fx=["cctv"]),
    dict(t=(69.35, 71.00), src="E7_alex_shout", cam=((.5, .44, 1.05), (.5, .44, 1.14)), fx=["handshake"]),
    dict(t=(71.00, 72.40), src="E7_press", anim=(0.0, 1.0), anim_start=71.10, anim_dur=0.62, cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["cctv"]),
    # --- 8. «ЭКЗЕМПЛЯР СОРОК ВОСЕМЬ НЕСТАБИЛЕН» — «НАЧАТЬ УДАЛЕНИЕ» — THE HAND
    dict(t=(72.40, 75.10), src="E7_wall", monitors="wall", cam=((.5, .5, 1.0), (.5, .5, 1.12))),
    dict(t=(75.10, 79.45), src="E7_mon_red", monitor="msg", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.12)), fx=["redglow"]),
    dict(t=(79.45, 82.15), src="E7_hand_vanish", anim=(0.0, 1.0), anim_start=T_ERASE, anim_dur=1.6, cam=((.5, .42, 1.0), (.5, .4, 1.1)), fx=["glitch_late"]),
    # --- 9. «НАЙДИ НАСТОЯЩЕГО СЕБЯ» — THE ADDRESS — TOMORROW
    dict(t=(82.15, 84.85), src="E7_lean", anim=(0.0, 1.0), anim_start=82.90, anim_dur=1.1, cam=((.5, .48, 1.0), (.5, .55, 1.05)), fx=["cctv"]),
    dict(t=(84.85, 86.90), src="LIPSYNC", lips="E7_feedm", sub="top", cam=((.5, .6, 1.0), (.5, .6, 1.08)), fx=["cctv"]),
    dict(t=(86.90, 89.55), src="LIPSYNC", lips="E7_feedm", sub="top", cam=((.5, .62, 1.12), (.5, .62, 1.22)), fx=["cctv"]),
    dict(t=(89.55, 93.90), src="E7_mon", monitor="addr", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    dict(t=(93.90, 97.70), src="E7_mon", monitor="addr", sub="bottom", cam=((.5, .48, 1.15), (.5, .47, 1.3))),
    dict(t=(97.70, CUT_TO_BLACK), src="E7_mon", monitor="addr", sub="top", cam=((.5, .5, 1.08), (.5, .5, 1.2)), fx=["handshake_late"]),
    dict(t=(CUT_TO_BLACK, END), src="BLACK", fx=["endcard"]),
]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
# sister «Выбирай себя, Алекс. / Ты всё равно вернёшься»; old Alex «Не нажимай!»; old Alex «Она уже стёрла тебя. / Сорок шесть раз»;
# Alex «Тогда почему я ещё здесь?»; the sister on the feed «Алекс, если ты меня слышишь, / найди настоящего себя»
LIP_WINDOWS = [(11.08, 12.23), (12.75, 14.11), (17.41, 18.44), (34.84, 36.13), (36.39, 38.32), (40.13, 41.64), (84.91, 86.82), (87.07, 88.97)]


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


# ---------------------------------------------------------------- phone screen states (same UI as EP01–EP06, text drawn in code)
PHONE_CLOCK = "02:53"                                   # EP06: 02:53 — the same minute
MSG_LAST = "Последнее задание."
MSG_CHOOSE = "Выбери, кого стереть."
MSG_CHOICE = "Сестру или себя."
MSG_DONE = "Выбор сделан"
MSG_UNSTABLE = "Экземпляр сорок восемь нестабилен"
MSG_DELETE = "Начать удаление"
ADDR_STREET, ADDR_FLAT = "Лесная, 12", "Квартира 47"
# the date: EP01's lock screen set the story on «пятница, 6 ноября» (it has been the same night since, 02:47 → 02:53),
# so the next day is Saturday the 7th. Shown as «ЗАВТРА» with that date under it (no real-world date is used).
DATE_LABEL, DATE_TEXT, DATE_WORD = "Дата", "суббота, 7 ноября", "ЗАВТРА"
NUMBER = "48"
# the last five seconds: 00:05 on «пять секунд», 04 while she reaches, then 3 / 2 / 1 on the words, 00:00 as «одна» ends
COUNT5 = [(3.58, 5), (11.08, 4), (20.90, 3), (21.48, 2), (22.15, 1), (T_ZERO, 0)]
CHOICE = {"text": MSG_CHOICE, "left": ("E4_sister_photo", "СЕСТРУ"), "right": ("E6_alex_portrait", "СЕБЯ"), "t_right": -9}
_CHAT = [(-9, ("header", "Номер скрыт")), (-9, ("bubble_red", MSG_LAST)), (-9, ("bubble_red", MSG_CHOOSE)), (-9, ("choice", CHOICE))]
PHONE = {
    # her phone exactly as EP06 left it (the last task + the choice), and from «пять секунд» the timer
    "hers": _CHAT + [(T_FIVE - 0.98, ("count5", COUNT5))],
    # Alex's own phone: the same task and choice, the timer counting the last five seconds
    "mine": _CHAT + [(3.58, ("count5", COUNT5))],
    # on the floor: the glass cracked by the fall
    "floor": _CHAT + [(3.58, ("count5", COUNT5)), (T_DROP, ("crack", 7))],
    # every phone on the table: the big timer
    "table5": [(0, ("count5full", COUNT5))],
}
SCREEN_TINT = {"table5": (215, 70, 60)}

# jolts -> camera shake (fx "shake_hits")
HITS = [T_DROP, T_PUNCH, T_SHATTER]
BLACKOUT = None
FLASHES = [(17.41, "red"), (T_ZERO, "white"), (T_OFF, "black"), (T_MTEXT_OK, "red"), (T_PUNCH, "white"), (T_48, "red"), (T_SHATTER, "white"),
           (T_PRESS, "red"), (T_MON_RED, "red"), (T_ERASE, "cold"), (T_STREET, "cold"), (T_TOMORROW, "red"), (CUT_TO_BLACK - 0.04, "white")]
COUNTDOWN = None
ENDCARD = ("Серия 7 · «Тот, кого стёрли»", "Продолжение следует")
BIG_SUBS = ("«!Не нажимай¡!»", "!Сорок восемь!.", "!46 раз!».", "«!Выбор сделан!».", "!Завтрашний день!.", "!Три, две, одна!.")

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger, ¡ = a literal "!")
# Only words that are in the voiceover; at most two lines each. Starts/ends from silencedetect and word timings.
SUBS = [
    (0.21, 0.88, "«!Сестру…!"),
    (1.68, 3.20, "!или себя…!»"),
    (3.58, 5.64, "На экране оставалось *пять секунд*."),
    (6.33, 7.59, "Я посмотрел на сестру."),
    (8.39, 10.28, "Она протянула руку к *моему телефону*."),
    (11.07, 12.23, "«*Выбирай себя*, Алекс."),
    (12.75, 14.11, "Ты всё равно !вернёшься!»."),
    (15.01, 17.24, "Но *старый Алекс* в зеркале закричал."),
    (17.41, 18.80, "«!Не нажимай¡!»"),
    (19.12, 20.49, "Я *бросил телефон* на пол."),
    (20.90, 22.70, "!Три, две, одна!."),
    (22.80, 23.93, "Все экраны *погасли*."),
    (24.15, 25.06, "Сестра !исчезла!."),
    (25.37, 27.26, "А в зеркале появилась *надпись*."),
    (27.57, 28.86, "«!Выбор сделан!»."),
    (29.59, 30.91, "Но я *ничего не выбирал*."),
    (31.11, 32.98, "Вдруг старый Алекс *ударил по стеклу*."),
    (33.24, 34.02, "Оно !треснуло!."),
    (34.84, 36.13, "«Она уже !стёрла тебя!."),
    (36.39, 38.32, "!46 раз!»."),
    (38.97, 39.78, "Я отступил."),
    (40.13, 41.64, "«Тогда почему *я ещё здесь*?»"),
    (41.85, 43.05, "Он показал на *мою руку*."),
    (43.32, 45.36, "На запястье медленно появлялся *номер*."),
    (45.73, 46.90, "!Сорок восемь!."),
    (47.30, 48.87, "Я попытался *стереть цифры*."),
    (49.12, 51.66, "Но кожа под пальцами стала !прозрачной!."),
    (51.88, 53.56, "Сквозь неё я увидел *провода*."),
    (54.57, 56.19, "Я был !не человеком!."),
    (56.53, 58.49, "Я был *очередной копией*."),
    (59.06, 60.83, "В этот момент зеркало !раскололось!."),
    (61.10, 63.14, "За ним оказалась *комната с мониторами*."),
    (63.39, 65.47, "На одном экране я увидел *свою сестру*."),
    (65.70, 67.19, "Она сидела перед компьютером"),
    (67.35, 68.80, "и смотрела *прямо на меня*."),
    (69.41, 70.75, "Я *закричал* её имя."),
    (71.06, 72.07, "Она !нажала кнопку!."),
    (72.45, 74.75, "Все мониторы показали *одно сообщение*."),
    (75.20, 77.32, "«!Экземпляр 48 нестабилен!»."),
    (77.54, 78.83, "«!Начать удаление!»."),
    (79.52, 81.94, "Я почувствовал, как !исчезает! моя левая рука."),
    (82.19, 84.22, "А потом сестра наклонилась *к микрофону*."),
    (84.91, 86.82, "«Алекс, если ты меня слышишь,"),
    (87.07, 88.97, "*найди настоящего себя*»."),
    (89.61, 93.04, "И экран показал *адрес моей квартиры*."),
    (93.95, 95.47, "*Лесная, 12*,"),
    (95.77, 97.30, "*квартира 47*."),
    (97.75, 99.30, "Но рядом была *дата*."),
    (100.05, 101.12, "!Завтрашний день!."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
TICKS = [3.58, 11.08, 20.90, 21.48, 22.15]
SFX = (
    [(0.05, "sting_soft", 0.5), (1.70, "sting_soft", 0.4), (3.55, "phone_on", 0.6)]
    + [(t, "tick_hard", 0.95) for t in TICKS] + [(T_ZERO, "final_hit", 0.9)]
    + [(6.30, "breath", 0.5), (8.45, "cloth", 0.5), (10.40, "breath", 0.4)]
    + [(15.00, "glass_ring", 0.6), (16.70, "sting", 0.7), (17.41, "glitch", 0.6), (17.41, "mirror_thump", 0.8)]
    + [(19.30, "whoosh", 0.8), (T_DROP, "phone_drop", 1.0), (T_DROP + 0.02, "glass_crack", 0.6)]
    + [(T_OFF, "screens_off", 1.0), (T_OFF, "power_out", 0.5)]
    + [(T_VANISH, "dissolve", 1.0), (T_VANISH + 0.05, "glitch", 0.5)]
    + [(T_MTEXT, "shimmer", 0.7), (T_MTEXT_OK, "sting", 0.8), (T_MTEXT_OK, "boom_tail", 0.5)]
    + [(29.60, "breath", 0.4), (31.70, "whoosh", 0.5), (T_PUNCH, "mirror_punch", 1.0), (T_PUNCH + 0.04, "glass_crack", 0.9), (33.30, "glass_ring", 0.4)]
    + [(36.39, "sting", 0.6), (38.98, "step", 0.6), (39.35, "step", 0.45)]
    + [(41.90, "sting_soft", 0.5), (43.40, "number_burn", 0.9), (T_48, "attempt_hit", 0.9)]
    + [(47.35, "cloth", 0.6), (47.95, "cloth", 0.5), (49.40, "shimmer", 0.5), (49.40, "glitch", 0.35), (51.90, "wires_hum", 0.9)]
    + [(54.60, "sting", 0.5), (56.55, "boom_tail", 0.5)]
    + [(T_SHATTER - 0.05, "glass_shatter", 1.0), (T_SHATTER, "hit", 0.5)]
    + [(61.12, "screens_on", 0.8), (63.40, "voice_static", 1.0), (65.75, "voice_static", 1.0), (69.40, "gasp", 0.6)]
    + [(T_PRESS, "button_press", 1.0), (T_MON_RED, "delete_alarm", 0.9), (T_MON_RED, "glitch", 0.5)]
    + [(T_MSG1, "notify_bad", 0.7), (T_MSG2, "notify_bad", 0.75), (T_MSG2, "sting", 0.6)]
    + [(T_ERASE, "dissolve", 1.0), (T_ERASE, "power_down", 0.4)]
    + [(82.95, "cloth", 0.4), (84.80, "voice_static", 1.0), (87.00, "voice_static", 0.8)]
    + [(T_ADDR_SCREEN, "phone_on", 0.6), (T_STREET, "type_lock", 0.9), (T_FLAT, "type_lock", 0.9), (T_DATE, "type_lock", 0.8)]
    + [(T_TOMORROW, "final_hit", 1.0), (T_TOMORROW, "sting", 0.6)]
    + [(CUT_TO_BLACK, "boom_tail", 0.9)]
)
HUM = [(0.0, T_OFF)]                    # the phones' electric hum in room 204 — it dies with the screens
CORRIDOR = []                           # the corridor is gone since EP06
MONHUM = [(T_SHATTER, CUT_TO_BLACK)]    # the monitor room's drone + fan whine, from the moment the mirror breaks
# music intensity curve (time, level 0..1): picks up at EP06's end level; drops into silence when the screens die, rises to the
# shatter, sits low under the feed, climbs to «Начать удаление», low under her plea, rises to the date and stops dead at the cut
MUSIC = [(0, .85), (3.5, .7), (10.9, .6), (14.9, .75), (17.4, .9), (20.8, .95), (T_OFF, .95), (T_OFF + 0.05, .12), (25.4, .3), (27.5, .55),
         (29.5, .35), (32.6, .7), (34.8, .4), (40.1, .45), (43.3, .55), (45.8, .75), (49.1, .6), (53.7, .4), (58.9, .65), (T_SHATTER, .9),
         (61.1, .45), (65.6, .3), (69.3, .55), (72.4, .7), (75.1, .8), (79.4, .9), (82.1, .35), (84.8, .2), (89.5, .45), (93.9, .55),
         (97.7, .7), (T_TOMORROW, .95), (CUT_TO_BLACK, .95)]
BELLS = [(0.1, 987.8), (15.0, 880.0), (27.6, 784.0), (45.8, 932.3), (61.1, 987.8), (75.2, 880.0), (93.95, 784.0)]
RISER = (93.9, 100.2)


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
        assert s["t"][1] - s["t"][0] <= 4.5, ("shot too long", s["t"])
    lip = [s["t"] for s in SHOTS if s["src"] == "LIPSYNC"]
    for a, b in LIP_WINDOWS:
        assert all(any(x <= f / FPS < y for x, y in lip) for f in range(int(a * FPS), int(b * FPS))), ("lip window not covered", a, b)


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, subtitles=SUBS, sfx=SFX, hum=HUM, monhum=MONHUM, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep07_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
