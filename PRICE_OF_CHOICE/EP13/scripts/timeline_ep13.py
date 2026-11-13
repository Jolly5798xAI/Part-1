"""EP13 «ПОСЛЕДНЯЯ КОПИЯ» — editing timeline (single source of truth). Same format as EP12 (../EP12/scripts/timeline_ep12.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
The approved MP3 is 116.61 s (speech 0.16 – 116.30 s): 26.6 s over the 75–90 s target — reported before editing, not altered.
Phrase times: timeline/transcript_words.json (Whisper small via sherpa-onnx, cut at the VO's own pauses ≥ 0.09 s, silencedetect −36 dB);
verified text: docs/EP13_transcript.txt.

EP13 opens the second EP12 ended: room 204, cold light after the handover, ELENA_1 standing beside ALEX_48, the side monitor's live feed
of flat 47 with ELENA_0 at the kitchen table, both mouthing «Не верь мне» (EP12's last frame E12_two, reused unchanged) — same place, no
recap, no time jump. The hidden recording is the accident night from EP12 (same road, car, rain, cast) from angles EP12 never showed; it
never shows a collision. The room turns red with the system's warning and stays red to the end. The episode ends dead on «…моё лицо»:
every screen in room 204 (the turned computer, the side monitor, the table of phones) shows ALEX_48's own face — hard cut.

Production names (never shown): ALEX_48 (hand whole since EP12; «48» on the inner left wrist until «СОЗДАТЕЛЬ»), ALEX_ORIGINAL_CONSCIOUSNESS
(the face on the turned screen — phone_ui; in the recording a plain ALEX figure on the back seat; never ALEX_ZERO), ELENA_1 (room 204, «1»,
cold white-cyan), ELENA_0 (flat 47 on the feed, «0», red). Both Elenas: the same model, no differences except the number and the place.

`python3 scripts/timeline_ep13.py` checks the timeline and writes timeline/ep13_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30
VO_END = 116.61
END = 116.61             # the video ends with the MP3 (last word ends 116.30) — no black tail, no end card
CUT_TO_BLACK = END
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- key moments (VO clock, phrase starts from transcript_words.json)
T_BOTH = 2.77                          # «Не верь мне» — both Elenas at once
T_RAISE1 = 8.9                         # «Елена рядом со мной подняла руку»
T_ONE = 11.82                          # «…светился номер один»
T_FEED_RAISE0, T_FEED_RAISE1 = 14.55, 15.35   # ELENA_0's hand comes up on the feed
T_ZERO = 16.06                         # «появился ноль»
T_GRAB = 23.6                          # «…схватила меня»
T_PANEL = 28.68                        # «Я открыл панель администратора»
T_HIDDEN = 30.62                       # «На экране появилась скрытая запись»
T_PLAY = 31.9                          # the hidden recording starts playing on the screen
T_ROAD = 32.85                         # full frame: the recording
T_TASKPH = 34.17                       # «Телефон с заданием»
T_BACK = 35.67                         # «И ещё один человек на заднем сиденье»
T_LIGHT = 37.65                        # his phone lights his face
T_REAL = 41.50                         # «…настоящий Алекс»
T_CMDON = 45.75                        # «Отключить тормоза» appears on the second phone
T_TOGGLE = 46.55                       # his thumb flips it
T_FREEZE = 47.35                       # «Я замер»
T_SMILE = 50.12                        # «Оригинал на мониторе улыбнулся»
T_WARN = 59.29                         # «Вдруг система выдала предупреждение» — the room goes red
T_LAST = 61.72                         # «Обнаружена последняя копия»
T_N48 = 63.87                          # «Номер сорок восемь»
T_CHOICE = 72.28                       # «На экране появился новый выбор»
T_OPT1, T_OPT2 = 74.39, 75.79          # «Удалить все копии» · «Сохранить последнюю»
T_PRICE_LBL = 77.49                    # «Под вторым вариантом загорелась надпись»
T_PRICE = 79.76                        # «Цена — жизнь Елены»
T_PULL = 81.95                         # «Я дёрнул руку»
T_VOICE = 85.17                        # «Тогда система заговорила голосом оригинала»
T_COUNT = 89.41                        # «На мониторе начался отсчёт»
TICKS = [(91.33, 10), (92.43, 9), (93.63, 8), (95.15, 7), (96.65, 6), (98.15, 5), (99.65, 4), (101.15, 3), (102.65, 2), (104.15, 1)]
T_HUD = 94.75                          # the count continues as a small timer over the room shots (holds on 00:01, blinking)
T_POINT = 100.5                        # «Она указала на моё запястье»
T_VANISH = 102.55                      # «Номер сорок восемь исчез»
T_WORD0 = 104.32                       # «Вместо него появилось слово:» — the letters burn in
T_WORD = 106.33                        # «Создатель» — the word locks, flash
T_SYS = 107.57                         # «И система произнесла:»
T_MSG1, T_MSG2 = 109.29, 110.90        # «Для остановки игры» · «удалите её создателя»
T_FACES = 113.36                       # «Все экраны…» — every screen shows ALEX_48's face
T_ERASE = T_VANISH

# ---------------------------------------------------------------- shots
# src: still (scenes/<src>.png, else ../EP12/scenes …), anim folder, "LIPSYNC" (+ lips=<base>) or "BLACK".
# monitor=<state>: phone_ui.draw_monitor on the still's screen quad.  phone=<state>: phone_ui.draw_screen on the still's phone quad.
# screens=<state>: the same phone state on every phone quad (+ the side monitor in E13_all).  wrist=1: «СОЗДАТЕЛЬ» on the forearm quad.
CAM_IN = ((.5, .4, 1.14), (.5, .4, 1.2))       # EP12's last move ended at (.5, .4, 1.14) — EP13's first frame continues it
SHOTS = [
    # --- 1. «ОБЕ ЕЛЕНЫ ОДНОВРЕМЕННО СКАЗАЛИ: «НЕ ВЕРЬ МНЕ»» (EP12's last frame) — WHICH ONE IS REAL?
    dict(t=(0.00, 2.70), src="E12_two_neutral", monitor="live13", sub="top", cam=CAM_IN),
    dict(t=(2.70, 3.75), src="LIPSYNC", lips="E12_two", monitor="live13", sub="top", cam=((.5, .4, 1.2), (.5, .4, 1.26)), fx=["shake_hits"]),
    dict(t=(3.75, 6.85), src="E13_look", anim=(0.0, 1.0), anim_start=4.45, anim_dur=2.3, sub="top", cam=((.5, .45, 1.0), (.5, .43, 1.1))),
    dict(t=(6.85, 8.65), src="LIPSYNC", lips="E13_a48", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["handshake"]),
    # --- 2. ELENA_1 RAISES HER HAND: «1» — ON THE FEED, ELENA_0: «0» — «Я НАСТОЯЩАЯ… А ТА, ЧТО РЯДОМ, СОЗДАНА СИСТЕМОЙ»
    dict(t=(8.65, 10.86), src="E13_raise1", anim=(0.0, 0.79), anim_start=9.2, anim_dur=1.5, sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.06))),   # frames ≤ k 0.8: the «1» is not lit yet
    dict(t=(10.86, 13.20), src="E13_wrist1", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.16)), fx=["shake_hits"]),
    dict(t=(13.20, 16.00), src="E13_side", monitor="live13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    dict(t=(16.00, 17.45), src="E13_flat0", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["live", "shake_hits"]),
    dict(t=(17.45, 19.70), src="E13_side", monitor="live13", sub="bottom", cam=((.5, .5, 1.12), (.5, .5, 1.2))),
    dict(t=(19.70, 22.30), src="E13_side_ots", monitor="live13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    # --- 3. HE STEPS BACK — SHE GRABS HIM — «ОНА ВРЁТ. ПРОВЕРЬ ЗАПИСЬ АВАРИИ» — THE ADMIN PANEL — THE HIDDEN RECORDING
    dict(t=(22.30, 23.40), src="E13_back", anim=(0.0, 1.0), anim_start=22.45, anim_dur=0.8, sub="top", cam=((.5, .45, 1.0), (.5, .45, 1.05)), fx=["handshake"]),
    dict(t=(23.40, 25.95), src="E13_grab", anim=(0.0, 1.0), anim_start=T_GRAB, anim_dur=1.0, sub="top", cam=((.5, .45, 1.0), (.5, .44, 1.1)), fx=["shake_hits"]),
    dict(t=(25.95, 28.45), src="LIPSYNC", lips="E13_e1", sub="bottom", cam=((.5, .42, 1.04), (.5, .42, 1.16))),
    dict(t=(28.45, 29.75), src="E13_reach", anim=(0.0, 1.0), anim_start=28.6, anim_dur=0.9, sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.05))),
    dict(t=(29.75, 32.85), src="E13_mon_close", monitor="panel13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.12))),
    # --- 4. THE RECORDING: THE NIGHT ROAD — THE PHONE WITH THE TASK — SOMEONE ON THE BACK SEAT — THE REAL ALEX — «ОТКЛЮЧИТЬ ТОРМОЗА»
    dict(t=(32.85, 34.10), src="E13_road", anim=(0.0, 1.0), sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["rec", "rain"]),
    dict(t=(34.10, 35.55), src="E13_dash", phone="task13", sub="bottom", cam=((.5, .5, 1.0), (.5, .52, 1.12)), fx=["rec", "drive"]),
    dict(t=(35.55, 39.60), src="E13_reveal", anim=(0.0, 1.0), anim_start=35.7, anim_dur=3.7, sub="bottom", cam=((.5, .45, 1.0), (.5, .42, 1.1)), fx=["rec", "drive"]),
    dict(t=(39.60, 42.35), src="E13_orig_smirk", sub="bottom", cam=((.5, .42, 1.0), (.5, .4, 1.16)), fx=["rec", "drive", "shake_hits"]),
    dict(t=(42.35, 44.00), src="E13_phone2", phone="brakes13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["rec", "drive"]),
    dict(t=(44.00, 47.25), src="E13_phone2_close", phone="brakes13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["rec", "drive", "shake_hits"]),
    # --- 5. «Я ЗАМЕР» — «ТЫ САМ УСТРОИЛ АВАРИЮ?» — THE ORIGINAL SMILES: «МНЕ НУЖЕН БЫЛ ИДЕАЛЬНЫЙ ВЫБОР» — «ОН ПРОВЕРЯЛ, КТО ПОЖЕРТВУЕТ СОБОЙ»
    dict(t=(47.25, 48.20), src="E13_a48_neutral", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.08)), fx=["shake_hits"]),
    dict(t=(48.20, 50.00), src="LIPSYNC", lips="E13_a48", sub="bottom", cam=((.5, .42, 1.08), (.5, .42, 1.18)), fx=["handshake"]),
    dict(t=(50.00, 52.05), src="E13_mon_close", monitor="face13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    dict(t=(52.05, 54.25), src="E13_mon", monitor="face13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.12))),
    dict(t=(54.25, 56.50), src="E13_e1_neutral", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1))),
    dict(t=(56.50, 59.25), src="LIPSYNC", lips="E13_e1", sub="bottom", cam=((.5, .42, 1.1), (.5, .42, 1.22))),
    # --- 6. THE WARNING (the room goes red): «ОБНАРУЖЕНА ПОСЛЕДНЯЯ КОПИЯ» «НОМЕР СОРОК ВОСЕМЬ» — «А ТЫ КТО?» — «ТА, КОТОРАЯ ПЫТАЛАСЬ ТЕБЯ ОСТАНОВИТЬ»
    dict(t=(59.25, 61.60), src="E13_monr", monitor="warn13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["shake_hits", "redglow"]),
    dict(t=(61.60, 63.80), src="E13_monr_close", monitor="warn13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08))),
    dict(t=(63.80, 65.50), src="E13_tabler", monitor="warn13", screens="warnp13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["shake_hits"]),
    dict(t=(65.50, 67.15), src="E13_e1r_neutral", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.1)), fx=["redglow"]),
    dict(t=(67.15, 68.20), src="LIPSYNC", lips="E13_a48r", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.14)), fx=["redglow"]),
    dict(t=(68.20, 69.70), src="E13_e1r_down", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.14)), fx=["redglow"]),
    dict(t=(69.70, 72.10), src="LIPSYNC", lips="E13_e1r", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.14)), fx=["redglow"]),
    # --- 7. THE CHOICE: «УДАЛИТЬ ВСЕ КОПИИ» / «СОХРАНИТЬ ПОСЛЕДНЮЮ» — «ЦЕНА — ЖИЗНЬ ЕЛЕНЫ» — HE PULLS HIS HAND BACK — «НЕТ»
    dict(t=(72.10, 74.30), src="E13_monr", monitor="choice13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08))),
    dict(t=(74.30, 77.30), src="E13_monr_close", monitor="choice13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08))),
    dict(t=(77.30, 79.65), src="E13_monr_close", monitor="choice13", sub="bottom", cam=((.5, .5, 1.02), (.5, .54, 1.08))),
    dict(t=(79.65, 80.95), src="E13_monr_close", monitor="choice13", sub="bottom", cam=((.5, .55, 1.08), (.5, .56, 1.14)), fx=["shake_hits"]),
    dict(t=(80.95, 81.80), src="E13_e1r_neutral", sub="bottom", cam=((.5, .42, 1.12), (.5, .42, 1.18)), fx=["redglow"]),
    dict(t=(81.80, 83.10), src="E13_pull", anim=(0.0, 1.0), anim_start=T_PULL, anim_dur=0.6, sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.04)), fx=["handshake"]),
    dict(t=(83.10, 85.00), src="LIPSYNC", lips="E13_a48r", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["redglow", "handshake"]),
    # --- 8. THE SYSTEM, IN THE ORIGINAL'S VOICE: «ВЫБОР УЖЕ СДЕЛАН» — THE COUNTDOWN: 10, 9, 8
    dict(t=(85.00, 87.75), src="E13_monr_close", monitor="voice13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    dict(t=(87.75, 89.30), src="E13_monr", monitor="voice13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["shake_hits"]),
    dict(t=(89.30, 91.25), src="E13_monr_close", monitor="count13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.06))),
    dict(t=(91.25, 92.38), src="E13_monr_close", monitor="count13", sub="bottom", cam=((.5, .5, 1.1), (.5, .5, 1.16)), fx=["shake_hits"]),
    dict(t=(92.38, 93.58), src="E13_tabler", monitor="count13", screens="countp13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["shake_hits"]),
    dict(t=(93.58, 94.75), src="E13_monr", monitor="count13", sub="top", cam=((.5, .5, 1.04), (.5, .5, 1.14)), fx=["shake_hits"]),
    # --- 9. «АЛЕКС. ЕСТЬ ТРЕТИЙ ВАРИАНТ» — «КАКОЙ?» — SHE POINTS AT HIS WRIST — «48» VANISHES — «СОЗДАТЕЛЬ»
    dict(t=(94.75, 97.30), src="E13_e1r_neutral", sub="bottom", cam=((.5, .42, 1.0), (.5, .42, 1.12)), fx=["redglow", "hud"]),
    dict(t=(97.30, 99.45), src="LIPSYNC", lips="E13_e1r", sub="bottom", cam=((.5, .42, 1.06), (.5, .42, 1.18)), fx=["redglow", "hud"]),
    dict(t=(99.45, 100.35), src="LIPSYNC", lips="E13_a48r", sub="bottom", cam=((.5, .42, 1.08), (.5, .42, 1.14)), fx=["redglow", "hud"]),
    dict(t=(100.35, 102.45), src="E13_point", anim=(0.0, 1.0), anim_start=T_POINT, anim_dur=1.5, sub="top", cam=((.5, .45, 1.0), (.5, .47, 1.1)), fx=["hud"]),
    dict(t=(102.45, 104.25), src="E13_arm", anim=(1.0, 0.0), anim_start=T_VANISH, anim_dur=1.4, wrist=1, sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.06)), fx=["hud", "glitch"]),
    dict(t=(104.25, 106.28), src="E13_arm", anim=(0.0, 0.0), wrist=1, sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.04)), fx=["hud"]),
    dict(t=(106.28, 107.50), src="E13_arm", anim=(0.0, 0.0), wrist=1, sub="top", cam=((.5, .5, 1.04), (.5, .5, 1.08)), fx=["hud", "shake_hits"]),
    # --- 10. «ДЛЯ ОСТАНОВКИ ИГРЫ УДАЛИТЕ ЕЁ СОЗДАТЕЛЯ» — EVERY SCREEN: ALEX_48'S FACE — HARD CUT
    dict(t=(107.50, 109.20), src="E13_monr", monitor="msg13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["hud"]),
    dict(t=(109.20, 111.95), src="E13_monr_close", monitor="msg13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.12)), fx=["hud", "shake_hits"]),
    dict(t=(111.95, 113.30), src="E13_a48r_neutral", sub="bottom", cam=((.5, .42, 1.04), (.5, .42, 1.14)), fx=["redglow", "hud"]),
    dict(t=(113.30, 114.35), src="E13_monr_close", monitor="self13", sub="bottom", cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["shake_hits"]),
    dict(t=(114.35, 115.45), src="E13_tabler", monitor="self13", screens="selfp13", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.1))),
    dict(t=(115.45, END), src="E13_all", monitor="self13", screens="selfp13", sub="top", cam=((.5, .5, 1.0), (.5, .46, 1.16)), fx=["shake_hits"]),
]

# ---------------------------------------------------------------- lip-sync windows (3D stills) + the original's face (UI) + the feed (UI)
LIPW = [(2.77, 3.60), (6.98, 8.53), (26.08, 26.73), (26.90, 28.07), (48.32, 49.84), (56.63, 57.45), (57.56, 58.77), (67.31, 68.00),
        (69.82, 71.78), (83.17, 83.56), (83.72, 84.82), (97.43, 97.84), (97.98, 99.10), (99.59, 100.10)]
LIPW_UI = [(52.14, 54.03), (87.90, 89.14)]               # the original's face speaks (his line; the system in his voice)
LIPW_FEED = [(2.77, 3.60), (17.61, 18.64), (19.83, 20.70), (20.86, 21.94)]   # ELENA_0 on the feed


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


LIP_WINDOWS = sorted(set(LIPW + LIPW_UI + LIPW_FEED))


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


def tick_at(t):
    """the countdown number at t (None before «Десять»); holds on 1 after the last tick"""
    n = None
    for tt, v in TICKS:
        if t >= tt: n = v
    return n


# ---------------------------------------------------------------- screens (text drawn in code, series fonts)
PHONE_CLOCK = "23:48"            # the accident night (EP12's dashboard phone)
MSG_BRAKES = "Отключить тормоза"
MSG_LAST, MSG_N48 = "Обнаружена последняя копия", "Номер сорок восемь"
MSG_OPT1, MSG_OPT2, MSG_PRICE = "Удалить все копии", "Сохранить последнюю", "Цена — жизнь Елены"
MSG_WORD = "СОЗДАТЕЛЬ"
MSG_STOP1, MSG_STOP2 = "Для остановки игры", "удалите её создателя"
MSG_LIVE, MSG_FLAT = "Прямой эфир", "Квартира 47"
MSG_ADMIN, MSG_HIDDEN = "Администратор: 48", "Скрытая запись"
# the dashboard phone shows EP12's three task cards (already on screen: the hidden recording is the same night, a few seconds later)
TASK13 = dict(clock=PHONE_CLOCK, date="воскресенье, 5 ноября", t_on=-10, t1=-9, t2=-8, t3=-7, m1="Первое задание", m2="Не тормози", m3="Награда — пятьсот долларов")
PHONE = {"task13": [(0, ("task12", TASK13))], "brakes13": [(0, ("ui13", "brakes13"))], "warnp13": [(0, ("ui13", "warnp13"))],
         "countp13": [(0, ("ui13", "countp13"))], "selfp13": [(0, ("ui13", "selfp13"))]}
SCREENS_ON = {}
SCREENS_WIDE = {"selfp13": "self13"}   # the side monitor among the phone quads (E13_all) shows the monitor picture
SCREEN_TINT = {}
REC_STAMP = None

HITS = [0.1, T_BOTH, T_ONE, T_ZERO, T_GRAB, T_REAL, T_CMDON, T_TOGGLE, T_FREEZE, T_WARN, T_N48, T_PRICE, 88.0] + [t for t, _ in TICKS[:3]] + \
       [T_VANISH, T_WORD, T_MSG2, T_FACES, 115.45]
BLACKOUT = None
FLASHES = [(T_HIDDEN, "cold"), (T_ROAD, "white"), (T_REAL, "cold"), (T_TOGGLE, "red"), (T_WARN, "red"), (T_PRICE, "red"), (T_WORD, "white"), (T_FACES, "white")]
COUNTDOWN = None
ENDCARD = None
BIG_SUBS = ()

# ---------------------------------------------------------------- subtitles (*word* = yellow, !word! = red, ¡ = a literal "!")
SUBS = [
    (0.16, 2.60, "Обе Елены *одновременно* сказали:"),
    (2.77, 3.95, "«!Не верь мне!»."),
    (4.57, 6.85, "Я смотрел то на сестру, то на монитор."),
    (6.98, 8.60, "«Которая из вас *настоящая?*»"),
    (8.72, 10.70, "Елена рядом со мной *подняла руку*."),
    (10.84, 13.70, "На запястье светился *номер один*."),
    (13.81, 15.95, "На экране у *второй Елены*"),
    (16.06, 17.45, "появился !ноль!."),
    (17.61, 19.70, "«Я *настоящая*», — сказала она, —"),
    (19.83, 22.30, "«а та, что рядом, !создана системой!»."),
    (22.46, 23.35, "Я отступил."),
    (23.46, 25.95, "Но Елена с номером один *схватила меня*."),
    (26.08, 28.40, "«!Она врёт!. Проверь *запись аварии*»."),
    (28.68, 30.50, "Я открыл *панель администратора*."),
    (30.62, 32.80, "На экране появилась *скрытая запись*."),
    (32.96, 34.05, "*Ночная дорога*."),
    (34.17, 35.55, "Телефон с заданием."),
    (35.67, 39.40, "И ещё один человек на *заднем сиденье*."),
    (39.74, 42.30, "Это был… !настоящий Алекс!."),
    (42.45, 43.95, "Он держал *второй телефон*."),
    (44.04, 45.65, "На нём светилась команда:"),
    (45.75, 47.20, "«!Отключить тормоза!»."),
    (47.35, 48.15, "Я *замер*."),
    (48.32, 49.95, "«Ты сам *устроил аварию?*»"),
    (50.12, 52.00, "Оригинал на мониторе *улыбнулся*."),
    (52.14, 54.20, "«Мне нужен был !идеальный выбор!»."),
    (54.38, 56.45, "Елена с номером один прошептала:"),
    (56.63, 59.15, "«Он проверял, кто *пожертвует собой*»."),
    (59.29, 61.60, "Вдруг система выдала *предупреждение*:"),
    (61.72, 63.75, "«!Обнаружена последняя копия!."),
    (63.87, 65.45, "Номер *сорок восемь*»."),
    (65.63, 67.15, "Я посмотрел на сестру."),
    (67.31, 68.15, "«А ты *кто?*»"),
    (68.31, 69.65, "Она опустила глаза."),
    (69.82, 72.05, "«Та, которая *пыталась тебя остановить*»."),
    (72.28, 74.25, "На экране появился *новый выбор*:"),
    (74.39, 75.70, "«*Удалить все копии*»."),
    (75.79, 77.35, "«*Сохранить последнюю*»."),
    (77.49, 79.60, "Под вторым вариантом загорелась надпись:"),
    (79.76, 81.75, "«Цена — !жизнь Елены!»."),
    (81.89, 83.10, "Я *дёрнул руку*."),
    (83.17, 84.95, "«!Нет!. Я *не буду выбирать*»."),
    (85.17, 87.75, "Тогда система заговорила *голосом оригинала*:"),
    (87.90, 89.30, "«!Выбор уже сделан!»."),
    (89.41, 91.20, "На мониторе начался *отсчёт*."),
    (91.33, 92.35, "«!Десять!»."),
    (92.43, 93.55, "«!Девять!»."),
    (93.63, 94.70, "«!Восемь!»."),
    (94.82, 97.30, "Елена с номером один посмотрела на меня."),
    (97.43, 99.45, "«Алекс. Есть *третий вариант*»."),
    (99.59, 100.35, "«*Какой?*»"),
    (100.48, 102.45, "Она указала на *моё запястье*."),
    (102.55, 104.25, "Номер *сорок восемь* исчез."),
    (104.32, 106.25, "Вместо него появилось слово:"),
    (106.33, 107.45, "«!Создатель!»."),
    (107.57, 109.20, "И система произнесла:"),
    (109.29, 110.80, "«Для остановки игры"),
    (110.90, 113.20, "!удалите её создателя!»."),
    (113.36, 114.30, "*Все экраны*"),
    (114.35, END, "одновременно показали !моё лицо!."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.05, "sting_soft", 0.5), (T_BOTH - 0.02, "attempt_hit", 0.6), (T_BOTH + 0.02, "voice_static", 0.5), (4.5, "breath", 0.5), (5.6, "whoosh", 0.35)]
    + [(T_RAISE1 + 0.2, "cloth", 0.8), (10.25, "num_chime", 0.9), (T_ONE, "sting", 0.5), (13.25, "phone_on", 0.5), (T_FEED_RAISE0, "cloth", 0.4)]
    + [(T_ZERO - 0.25, "zero_on", 0.8), (T_ZERO, "num_chime", 0.7), (17.6, "voice_static", 0.5), (19.8, "voice_static", 0.5), (20.9, "sting_soft", 0.4)]
    + [(22.5, "step", 0.9), (22.9, "step", 0.7), (T_GRAB - 0.1, "whoosh", 0.8), (T_GRAB + 0.35, "cloth", 1.0), (T_GRAB + 0.4, "gasp", 0.5), (26.1, "breath", 0.4)]
    + [(T_PANEL + 0.2, "tap", 0.9), (T_PANEL + 0.25, "panel_open", 1.0), (T_HIDDEN, "type_lock", 0.6), (T_PLAY - 0.1, "button_press", 0.6), (T_PLAY, "rec_start", 0.8)]
    + [(T_ROAD - 0.05, "car_pass", 0.8), (T_TASKPH, "vibrate", 0.6), (T_TASKPH + 0.4, "notify_bad", 0.5), (34.9, "wiper", 0.5), (36.4, "wiper", 0.4)]
    + [(T_BACK, "sting_soft", 0.5), (T_BACK + 0.4, "heartbeat", 0.8), (T_LIGHT, "phone_on", 0.8), (38.6, "heartbeat", 0.9), (39.7, "breath", 0.5)]
    + [(T_REAL - 0.25, "sub_drop", 1.0), (T_REAL, "sting", 0.8), (42.5, "vibrate", 0.7), (44.1, "heartbeat", 0.8), (T_CMDON - 0.02, "brake_off", 0.9)]
    + [(T_TOGGLE, "tap", 1.0), (T_TOGGLE + 0.02, "brake_off", 1.0), (T_TOGGLE + 0.05, "glitch", 0.5), (T_FREEZE, "static_cut", 0.7), (T_FREEZE + 0.05, "heartbeat", 1.0)]
    + [(48.3, "breath", 0.4), (T_SMILE, "voice_static", 0.5), (T_SMILE + 0.1, "glitch", 0.4), (52.1, "voice_static", 0.6), (54.1, "boom_tail", 0.4), (54.4, "whisper", 0.6)]
    + [(T_WARN - 0.05, "copy_alarm", 1.0), (T_WARN, "sting", 0.7), (T_LAST, "type_lock", 0.7), (T_N48 - 0.02, "attempt_hit", 0.9), (T_N48 + 0.05, "phones_buzz", 0.8)]
    + [(65.6, "whoosh", 0.5), (67.2, "breath", 0.4), (68.3, "sting_soft", 0.4), (69.8, "boom_tail", 0.3)]
    + [(T_CHOICE, "choice_on", 1.0), (T_OPT1, "type_lock", 0.7), (T_OPT2, "type_lock", 0.7), (T_PRICE_LBL + 1.0, "glitch", 0.4), (T_PRICE - 0.02, "final_hit", 0.7), (T_PRICE, "heartbeat", 0.9)]
    + [(T_PULL, "whoosh", 0.9), (T_PULL + 0.1, "cloth", 0.9), (83.2, "breath", 0.5)]
    + [(T_VOICE, "glitch", 0.6), (T_VOICE + 0.05, "voice_static", 0.7), (87.85, "voice_static", 0.8), (88.0, "sub_drop", 0.45), (T_COUNT, "delete_alarm", 0.6)]
    + [(t, "count_tick", 1.0 if i < 3 else 0.55) for i, (t, _) in enumerate(TICKS)]
    + [(94.8, "heartbeat", 0.7), (97.4, "breath", 0.4), (99.6, "sting_soft", 0.5), (T_POINT, "whoosh", 0.6), (T_POINT + 0.6, "cloth", 0.7)]
    + [(T_VANISH - 0.05, "dissolve", 1.0), (T_VANISH + 0.1, "number_burn", 0.6), (T_WORD0, "word_burn", 1.0), (T_WORD - 0.03, "attempt_hit", 1.0), (T_WORD, "sting", 0.8)]
    + [(T_SYS, "voice_static", 0.6), (T_MSG1, "type_lock", 0.7), (T_MSG2, "type_lock", 0.8), (T_MSG2 + 0.05, "copy_alarm", 0.6), (112.0, "heartbeat", 1.0)]
    + [(T_FACES - 0.05, "screens_on", 1.0), (T_FACES, "faces_swarm", 0.8), (114.35, "phones_chorus", 0.6), (115.45, "final_cut", 1.0)]
)
HUM = []
CORRIDOR = []
MONHUM = [(0, 32.85), (47.25, END)]   # room 204: the computer's electrical drone
FLAT = []
RAIN = [(32.85, 47.25)]               # the hidden recording: rain + the engine inside the car
ENGINE = [(33.0, 47.0)]
# music: low tension under the two Elenas, lifts on the numbers, a pulse under the recording, a deep hit on the original, held under the
# confession, alarm on the warning, high under the choice, a ticking climb through the countdown, peaks at «СОЗДАТЕЛЬ», riser to the cut
MUSIC = [(0, .55), (2.7, .7), (4.0, .45), (8.6, .5), (11.8, .6), (13.2, .5), (16.0, .65), (17.5, .5), (22.3, .6), (23.5, .75), (26.0, .55),
         (28.6, .6), (30.6, .7), (32.9, .55), (35.6, .65), (37.6, .75), (41.5, .95), (42.4, .7), (45.7, .85), (47.3, .4), (50.1, .55), (52.1, .6),
         (54.3, .45), (59.3, .85), (61.7, .8), (63.9, .9), (65.5, .55), (69.8, .5), (72.3, .7), (77.5, .75), (79.8, .9), (81.9, .7), (85.2, .75),
         (88.0, .85), (89.4, .8), (91.3, .9), (94.8, .7), (97.4, .65), (100.4, .75), (102.5, .85), (106.3, 1.0), (107.5, .8), (110.9, .9),
         (113.4, 1.0), (END, 1.0)]
MUSIC_TAIL = False
BELLS = [(0.1, 932.3), (T_ONE, 987.8), (T_ZERO, 740.0), (T_HIDDEN, 880.0), (T_REAL, 659.3), (T_N48, 932.3), (T_CHOICE, 784.0), (T_WORD, 987.8), (T_FACES, 932.3)]
RISER = (110.9, END)


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
        assert s.get("screens") in (None, *PHONE), s
        assert s["t"][1] - s["t"][0] <= 4.5, ("shot too long", s["t"])
    lip = [s["t"] for s in SHOTS if s["src"] == "LIPSYNC"]
    for a, b in LIPW:
        assert all(any(x <= f / FPS < y for x, y in lip) for f in range(int(a * FPS), int(b * FPS))), ("lip window not covered", a, b)
    face = [s["t"] for s in SHOTS if s.get("monitor") in ("face13", "voice13")]
    for a, b in LIPW_UI:
        assert all(any(x <= f / FPS < y for x, y in face) for f in range(int(a * FPS), int(b * FPS))), ("screen-face lip window not on the screen", a, b)
    # no on-screen message before its words (phrase starts from timeline/transcript_words.json)
    w = json.load(open(os.path.join(ROOT, "timeline", "transcript_words.json")))
    start = {p["text"]: p["start"] for p in w}
    assert T_CMDON >= -0.01 + start["«Отключить"] and T_LAST >= -0.01 + start["«Обнаружена последняя копия."] and T_N48 >= -0.01 + start["Номер сорок восемь»."]
    assert T_OPT1 >= -0.01 + start["«Удалить все копии»."] and T_OPT2 >= -0.01 + start["«Сохранить последнюю»."] and T_PRICE >= -0.01 + start["«Цена —"]
    assert T_WORD0 >= -0.01 + start["Вместо него появилось слово:"] and T_MSG1 >= -0.01 + start["«Для остановки игры"] and T_MSG2 >= -0.01 + start["удалите её создателя»."]
    assert T_ONE >= -0.01 + start["светился номер один."] - 1.1 and T_ZERO >= -0.01 + start["появился ноль."] and T_FACES >= -0.01 + start["Все экраны"]
    assert TICKS[0][0] >= -0.01 + start["«Десять»."] and TICKS[1][0] >= -0.01 + start["«Девять»."] and TICKS[2][0] >= -0.01 + start["«Восемь»."]
    assert T_HIDDEN >= -0.01 + start["На экране появилась скрытая запись."] and T_SMILE >= -0.01 + start["Оригинал на мониторе улыбнулся."]
    # the first frame is EP12's last frame (both Elenas); the last frame: every screen with ALEX_48's face
    assert SHOTS[0]["src"] == "E12_two_neutral" and SHOTS[-1]["src"] == "E13_all" and SHOTS[-1].get("monitor") == "self13"
    # «48» stays on his wrist until it vanishes; «СОЗДАТЕЛЬ» never before its words
    for s in SHOTS:
        if s.get("wrist"): assert s["t"][0] >= T_VANISH - 0.2, s


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, flashes=FLASHES, subtitles=SUBS, sfx=SFX, monhum=MONHUM, rain=RAIN, engine=ENGINE, music=MUSIC, ticks=TICKS)
    with open(os.path.join(ROOT, "timeline", "ep13_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
