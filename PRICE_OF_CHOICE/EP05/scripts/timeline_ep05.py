"""EP05 «КОМНАТА 204» — editing timeline (single source of truth). Same format as EP04 (../EP04/scripts/timeline_ep04.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper small, word timestamps); phrase starts checked against
silencedetect (docs/EP05_VO_REPORT.md). Verified text: docs/EP05_transcript.txt.

EP05 opens where EP04 ended: the officer's phone with the sister's photo and her voice message (EP04 frame
E4_cop_phone_close, EP04's end framing (0.5, 0.40, ×1.75)), while the approved VO says the tail of her line
«…не открывай дверь». No recap, no time jump.

Lip-sync: during the double's and the sister's quoted lines the mouth shape is picked frame by frame from the VO envelope.
Alex's own voice behind door 204 and the sister's cry from the hallway are heard off-screen (no visible mouth).

`python3 scripts/timeline_ep05.py` checks the timeline and writes timeline/ep05_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 86.13           # the approved MP3 is 86.126 s; the last word «игру» ends at 86.10
CUT_TO_BLACK = 86.13
END = 88.60
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- shots
# src: still name (scenes/<src>.png, else ../EP04/scenes, ../EP03/scenes, ../EP02/illustrations), anim folder (scenes/<src>/),
#      "LIPSYNC" (+ lips=<base>; shape from LIPSYNC by time) or "BLACK".  cam: (cx, cy, zoom) start -> end.
# phone: chat state drawn on the scene's phone screen; screens: state drawn on EVERY phone of the table in room 204.
SHOTS = [
    # --- 1. HER VOICE (continues EP04's last frame)
    dict(t=(0.00, 1.30), src="E4_cop_phone_close", sub="top", cam=((.5, .40, 1.75), (.5, .40, 1.86)), phone="voice_tail", fx=["handshake"]),
    dict(t=(1.30, 3.50), src="E5_alex_react", sub="top", cam=((.5, .44, 1.0), (.5, .42, 1.14))),
    dict(t=(3.50, 6.55), src="E4_sister_photo", cam=((.5, .5, 1.0), (.5, .46, 1.18)), fx=["memory"]),
    # --- 2. THE KEY
    dict(t=(6.55, 9.20), src="E5_key_offer", anim=(0.0, 1.0), anim_start=6.70, anim_dur=1.6, cam=((.5, .45, 1.0), (.48, .5, 1.08))),
    dict(t=(9.20, 12.20), src="E5_key_tag", cam=((.5, .5, 1.0), (.5, .54, 1.18))),
    dict(t=(12.20, 14.05), src="E5_reach", anim=(0.0, 1.0), anim_start=12.35, anim_dur=1.35, cam=((.5, .45, 1.0), (.5, .47, 1.06))),
    # --- 3. «НЕ ТРОГАЙ!»
    dict(t=(14.05, 16.15), src="E4_dbl_pale_wide", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.1)), fx=["shake_hits"]),
    dict(t=(16.15, 18.80), src="LIPSYNC", lips="E4_dbl_pale", sub="top", cam=((.5, .5, 1.0), (.5, .52, 1.1)), fx=["shake_hits"]),
    # --- 4. THE LIGHT GOES OUT — THE OFFICER IS GONE
    dict(t=(18.80, 20.30), src="E5_doorway_cop", cam=((.5, .45, 1.0), (.5, .45, 1.06))),
    dict(t=(20.30, 21.50), src="BLACK"),
    dict(t=(21.50, 23.80), src="E5_doorway_empty", cam=((.5, .45, 1.06), (.44, .44, 1.22))),
    dict(t=(23.80, 25.75), src="E5_floor", cam=((.5, .55, 1.0), (.5, .57, 1.14))),
    # --- 5. THE NEW TASK
    dict(t=(25.75, 26.05), src="E5_phone_task", sub="top", cam=((.5, .5, 1.05), (.5, .5, 1.06)), phone="dead"),
    dict(t=(26.05, 28.05), src="E5_phone_task", sub="top", cam=((.5, .5, 1.06), (.5, .5, 1.16)), phone="task", fx=["glitch"]),
    dict(t=(28.05, 30.20), src="E5_phone_task", sub="top", cam=((.5, .48, 1.18), (.5, .46, 1.32)), phone="task", fx=["redglow"]),
    dict(t=(30.20, 33.40), src="E5_phone_task", sub="top", cam=((.5, .5, 1.3), (.5, .55, 1.45)), phone="task", fx=["redglow"]),
    # --- 6. «ТВОЯ ПЕРВАЯ ОШИБКА»
    dict(t=(33.40, 36.65), src="E5_alex_key", cam=((.5, .42, 1.0), (.5, .42, 1.12))),
    dict(t=(36.65, 38.55), src="E4_dbl_pale_neutral", sub="top", cam=((.5, .42, 1.02), (.5, .40, 1.16))),
    dict(t=(38.55, 40.70), src="LIPSYNC", lips="E4_dbl_pale", sub="top", cam=((.5, .5, 1.0), (.5, .5, 1.12))),
    # --- 7. HER VOICE IN THE HALLWAY
    dict(t=(40.70, 43.70), src="E5_hall_voice", cam=((.5, .5, 1.0), (.48, .5, 1.15))),
    dict(t=(43.70, 45.60), src="E5_hall_voice", cam=((.48, .5, 1.15), (.45, .48, 1.4)), fx=["handshake"]),
    dict(t=(45.60, 47.00), src="E5_run_out", anim=(0.0, 1.0), anim_start=45.62, anim_dur=1.3, cam=((.5, .45, 1.0), (.5, .42, 1.05))),
    # --- 8. THE DOOR — THE CORRIDOR (same camera: darkness -> the stairwell as it should be -> the hotel corridor)
    dict(t=(47.00, 48.70), src="E5_view_dark", cam=((.5, .48, 1.0), (.5, .48, 1.08))),
    dict(t=(48.70, 50.10), src="E5_view_stair", cam=((.5, .48, 1.08), (.5, .48, 1.12)), fx=["memory"]),
    dict(t=(50.10, 52.60), src="E5_view_corridor", cam=((.5, .48, 1.12), (.5, .46, 1.3)), fx=["glitch"]),
    dict(t=(52.60, 54.75), src="E5_corridor_far", cam=((.5, .5, 1.0), (.5, .45, 1.2)), fx=["tube"]),
    dict(t=(54.75, 56.45), src="E5_door204", cam=((.5, .5, 1.0), (.5, .45, 1.12))),
    dict(t=(56.45, 58.10), src="E5_door204_plate", cam=((.5, .6, 1.0), (.5, .64, 1.12)), fx=["tube"]),
    # --- 9. MY OWN VOICE BEHIND THE DOOR
    dict(t=(58.10, 59.65), src="E5_corridor_walk", anim=(0.0, 1.0), anim_start=58.12, anim_dur=1.5, cam=((.5, .5, 1.0), (.5, .5, 1.05))),
    dict(t=(59.65, 62.65), src="E5_door_listen", cam=((.5, .45, 1.0), (.5, .42, 1.15))),
    dict(t=(62.65, 64.15), src="E5_door_gap", sub="top", cam=((.5, .6, 1.0), (.5, .62, 1.1))),
    dict(t=(64.15, 66.75), src="E5_alex_red", sub="top", cam=((.5, .42, 1.0), (.5, .42, 1.15)), fx=["tube"]),
    # --- 10. THE KEY — THE DOOR OPENS
    dict(t=(66.75, 68.05), src="E5_key_lock", anim=(0.0, 1.0), anim_start=66.85, anim_dur=0.95, cam=((.5, .5, 1.0), (.5, .5, 1.08)), fx=["shake_hits"]),
    dict(t=(68.05, 70.10), src="E5_door204_open", anim=(0.0, 1.0), anim_start=68.12, anim_dur=1.6, cam=((.5, .45, 1.0), (.5, .45, 1.06))),
    # --- 11. DOZENS OF PHONES
    dict(t=(70.10, 73.35), src="E5_room_dark", cam=((.5, .5, 1.0), (.5, .55, 1.12))),
    dict(t=(73.35, 75.40), src="E5_room_lit", cam=((.5, .55, 1.12), (.5, .56, 1.22)), screens="creator"),
    dict(t=(75.40, 77.95), src="E5_phones_low", cam=((.5, .5, 1.0), (.5, .5, 1.12)), screens="creator"),
    dict(t=(77.95, 81.05), src="E5_phone_hero", sub="bottom", cam=((.5, .5, 1.0), (.5, .44, 1.14)), phone="creator", screens="creator"),
    # --- 12. THE SISTER
    dict(t=(81.05, 83.75), src="E5_sister_behind", anim=(0.0, 1.0), anim_start=81.55, anim_dur=1.2, cam=((.5, .45, 1.0), (.52, .42, 1.1)), screens="creator"),
    dict(t=(83.75, CUT_TO_BLACK), src="LIPSYNC", lips="E5_sis", sub="top", cam=((.5, .45, 1.05), (.5, .44, 1.25)), fx=["handshake"]),
    dict(t=(CUT_TO_BLACK, END), src="BLACK", fx=["endcard"]),
]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
# quoted lines spoken on screen: the double (shouting, then the warning) and the sister's last line
LIP_WINDOWS = [(16.20, 18.74), (38.66, 40.06), (83.86, 86.10)]


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

# ---------------------------------------------------------------- phone screen states (same UI as EP01–EP04, text drawn in code)
PHONE_CLOCK = "02:52"                                   # EP04: 02:51
MSG_NEXT = "Следующее задание начнётся с неё."           # EP04
MSG_MIRROR = "Неповиновение зафиксировано."              # EP04 (the last thing the dead phone showed before the mirror)
MSG_FIND = "Найди комнату двести четыре."
MSG_REWARD = "Награда — сто тысяч долларов."
MSG_CREATOR = "С возвращением, создатель."
T_WAKE, T_FIND, T_REWARD, T_ON = 26.05, 28.12, 30.27, 73.35
PHONE = {
    # EP04's last frame: the voice message has played to the end
    "voice_tail": [(0, ("header", "Номер скрыт")), (0, ("photo_msg", "E4_sister_photo")), (0, ("bubble_red", MSG_NEXT)), (0, ("voice", (-3.10, 3.10)))],
    # Alex's phone, cracked and dead on the floor since EP04 — it wakes up under the cracks
    "dead": [(0, ("crack", 7)), (0, ("off", None))],
    "task": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_MIRROR)), (0, ("crack", 7)), (T_WAKE, ("typing", None)),
             (T_FIND, ("bubble_red", MSG_FIND)), (T_REWARD, ("bubble_red", MSG_REWARD))],
    # every phone in room 204 — all lit at once on «все экраны» (73.34)
    "creator": [(0, ("header", "Номер скрыт")), (T_ON, ("bubble_red", MSG_CREATOR))],
}

# jolts -> camera shake (fx "shake_hits"): the chair rocking as the double screams, the lock clacking open
HITS = [14.70, 15.40, 16.25, 67.62]
# the blackout: light flickers from BLACKOUT[0], dead at [1]; comes back flickering at [2], steady at [3]
BLACKOUT = (19.62, 20.15, 21.50, 22.05)
FLASHES = [(10.70, "white"), (56.50, "red"), (73.35, "cold"), (79.45, "red"), (CUT_TO_BLACK - 0.04, "white")]
COUNTDOWN = None
ENDCARD = ("Серия 5 · «Комната 204»", "Продолжение следует")
BIG_SUBS = ("«!Твоя первая ошибка!».", "«!С возвращением, создатель!».", "«Алекс… !зачем ты снова запустил игру?!»")

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger, ¡ = a literal "!")
# Only words that are in the voiceover; at most two lines each. Starts from silencedetect, ends from word timings.
SUBS = [
    (0.02, 1.15, "«…!не открывай дверь!»."),
    (1.62, 3.20, "Это был *голос моей сестры*."),
    (3.80, 5.58, "Но она !исчезла три года назад!."),
    (6.69, 9.08, "Полицейский в чёрной маске протянул мне *ключ*."),
    (9.32, 11.95, "На бирке было написано *204*."),
    (12.37, 13.80, "Я не успел его взять."),
    (14.10, 15.88, "Связанный двойник *закричал*."),
    (16.20, 16.95, "«!Не трогай¡!"),
    (17.10, 18.78, "Он хочет, чтобы ты *вспомнил*¡»"),
    (19.56, 20.62, "Свет *погас*."),
    (21.29, 23.56, "Когда он включился, полицейский !исчез!."),
    (23.86, 25.40, "Ключ лежал *у моих ног*."),
    (25.85, 27.80, "А телефон показывал новое задание."),
    (28.10, 30.02, "«!Найди комнату 204!."),
    (30.24, 32.72, "Награда — *сто тысяч долларов*»."),
    (33.52, 36.32, "Я спросил двойника, что находится в этой комнате."),
    (36.82, 37.95, "Он посмотрел на меня."),
    (38.75, 40.10, "«!Твоя первая ошибка!»."),
    (40.97, 43.62, "Вдруг из прихожей донёсся *голос сестры*:"),
    (43.86, 45.15, "«!Алекс, помоги мне¡!»"),
    (45.69, 46.95, "Я выбежал из спальни."),
    (47.08, 48.55, "Входная дверь была *открыта*."),
    (48.76, 50.30, "Но вместо подъезда за ней"),
    (50.38, 52.38, "оказался *гостиничный коридор*."),
    (52.72, 54.56, "В конце горела !красная лампа!."),
    (54.82, 57.52, "Под ней — дверь с номером *204*."),
    (58.15, 59.33, "Я подошёл ближе."),
    (59.70, 62.10, "Из комнаты раздался !мой собственный голос!:"),
    (62.77, 63.95, "«Не впускайте его."),
    (64.16, 65.66, "Он ещё !ничего не помнит!»."),
    (66.82, 67.75, "Я вставил ключ."),
    (68.16, 69.15, "Дверь *открылась*."),
    (70.17, 72.95, "Внутри стоял стол с *десятками телефонов*."),
    (73.20, 75.30, "Все экраны *одновременно загорелись*."),
    (75.44, 77.47, "На них было одно сообщение:"),
    (78.03, 80.15, "«!С возвращением, создатель!»."),
    (81.19, 83.55, "И тут *за моей спиной* сестра произнесла:"),
    (83.86, 86.12, "«Алекс… !зачем ты снова запустил игру?!»"),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
SFX = (
    [(0.00, "voice_static", 0.7), (1.40, "breath", 0.5), (3.60, "sting_soft", 0.5)]
    + [(6.75, "cloth", 0.5), (7.55, "key_jingle", 0.8), (8.70, "key_jingle", 0.45), (10.70, "sting", 0.8), (12.40, "cloth", 0.45)]
    + [(14.10, "chair_creak", 0.9), (14.70, "chair_creak", 0.8), (15.40, "hit", 0.25), (16.22, "chair_creak", 0.7)]
    + [(19.62, "flicker", 0.9), (20.12, "power_out", 1.0), (21.45, "power_on", 0.9), (22.95, "sting_soft", 0.6)]
    + [(26.05, "phone_on", 0.8), (T_FIND, "notify_bad", 0.75), (T_REWARD, "notify_bad", 0.7), (31.90, "coin", 0.4)]
    + [(33.50, "cloth", 0.4), (33.60, "key_jingle", 0.5), (38.66, "sting_soft", 0.7), (40.10, "hit", 0.3)]
    + [(41.00, "breath", 0.5), (45.66, "whoosh", 0.8)] + [(t, "step", 0.7) for t in (45.82, 46.12, 46.42, 46.72)]
    + [(47.10, "door_creak", 0.5), (48.76, "sting_soft", 0.6), (50.10, "glitch", 0.7), (50.12, "sting", 0.7), (56.50, "sting", 0.8)]
    + [(t, "step", 0.4) for t in (58.18, 58.62, 59.06, 59.50)]
    + [(59.75, "sting_soft", 0.6), (64.20, "breath", 0.5)]
    + [(66.90, "lock_insert", 1.0), (67.62, "lock_clack", 0.7), (68.15, "door_open", 1.0), (70.20, "sting_soft", 0.4)]
    + [(T_ON, "phones_chorus", 1.0), (T_ON + 0.01, "sting", 0.6), (79.45, "sting", 0.7)]
    + [(81.60, "cloth", 0.35), (82.20, "sting_soft", 0.8), (82.30, "breath", 0.6)]
    + [(CUT_TO_BLACK, "boom_tail", 0.9), (CUT_TO_BLACK, "sting", 0.6)]
)
HUM = [(52.60, 58.10), (64.15, 66.75)]   # the red lamp's buzz (close to the lamp)
CORRIDOR = [(50.10, 70.10)]              # the hotel corridor's air (ventilation, distant hum)
# music intensity curve (time, level 0..1): picks up at EP04's end level, drops in the blackout, the whispers and the last line
MUSIC = [(0, .25), (1.3, .35), (6.5, .45), (10.7, .65), (14.0, .7), (16.2, .8), (19.6, .85), (20.2, .08), (21.5, .45), (26.0, .55),
         (28.1, .7), (33.4, .45), (38.6, .6), (40.7, .35), (45.6, .7), (47.0, .45), (50.1, .65), (52.6, .55), (56.5, .7), (59.6, .45),
         (62.6, .3), (66.7, .6), (68.0, .7), (70.1, .45), (73.35, .85), (77.9, .75), (81.0, .4), (83.7, .25), (86.13, .25)]
BELLS = [(3.6, 880.0), (10.75, 987.8), (28.15, 784.0), (50.15, 932.3), (56.55, 987.8), (73.4, 880.0), (79.5, 987.8)]
RISER = (75.4, 81.0)


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


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE,
                hits=HITS, blackout=BLACKOUT, flashes=FLASHES, countdown=COUNTDOWN, subtitles=SUBS, sfx=SFX, hum=HUM,
                corridor=CORRIDOR, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep05_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
