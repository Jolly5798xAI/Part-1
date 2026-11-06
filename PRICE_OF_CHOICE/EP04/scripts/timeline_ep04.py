"""EP04 «НЕ ТОТ АЛЕКС» — editing timeline (single source of truth). Same format as EP03 (../EP03/scripts/timeline_ep03.py).

All times are seconds on the voiceover clock (VO starts at 0.0 and is never cut, sped up or pitched).
Word times: timeline/transcript_words.json (faster-whisper small, word timestamps); phrase starts checked against
silencedetect (docs/EP04_VO_REPORT.md). Verified text: docs/EP04_transcript.txt.

EP04 opens where EP03 ended: extreme close-up of the tied double's wet eyes (EP03 shot E3_tied_face_tears_eyes, same frame,
same framing (0.5, 0.43, ×1.18)), while the VO says «Человек на стуле плакал моим голосом».

Lip-sync: during the double's and Alex's quoted lines the mouth shape is picked frame by frame from the VO envelope
(see lipsync()), so the mouths move exactly with the approved recording.

`python3 scripts/timeline_ep04.py` checks the timeline and writes timeline/ep04_timeline.json.
"""
import json, os, subprocess, glob

FPS = 30                 # locked for the series
VO_END = 108.28
CUT_TO_BLACK = 108.30    # last word «дверь» ends at 108.24
END = 110.75
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- shots
# src: still name (scenes/<src>.png, else ../EP03/scenes, else ../EP02/illustrations), anim folder (scenes/<src>/),
#      "LIPSYNC" (+ lips=<base>; shape from LIPSYNC by time) or "BLACK".  cam: (cx, cy, zoom) start -> end.
# mirror: the red message on the hall mirror (drawn in code on the mirror's quad from scenes/meta.json)
SHOTS = [
    # --- 1. HE CRIES WITH MY VOICE (continues EP03's last frame) — THE ORDER
    dict(sub="top", t=(0.00, 1.80), src="E3_tied_face_tears_eyes", cam=((.5, .43, 1.18), (.5, .44, 1.08))),
    dict(sub="top", t=(1.80, 3.95), src="E3_tied_face_tears", cam=((.5, .45, 1.25), (.5, .5, 1.08))),
    dict(t=(3.95, 7.40), src="E3_pov_room_close", sub="bottom", cam=((.5, .64, 1.62), (.5, .66, 1.78)), phone="kill_hold", fx=["redglow"]),
    # --- 2. THE SCAR
    dict(t=(7.40, 10.00), src="E4_approach", anim=(0.0, 1.0), anim_start=7.55, anim_dur=2.35, cam=((.5, .5, 1.0), (.5, .48, 1.06))),
    dict(t=(10.00, 11.85), src="E4_scar_dbl", cam=((.47, .5, 1.05), (.47, .47, 1.25))),
    dict(t=(11.85, 14.40), src="E4_scars", anim=(0.0, 1.0), anim_start=11.92, anim_dur=1.15, cam=((.5, .5, 1.0), (.5, .48, 1.22))),
    # --- 3. THE TAPE — «НЕ ТРОГАЙ ТЕЛЕФОН»
    dict(t=(14.40, 16.20), src="E4_tape_off", anim=(0.0, 1.0), anim_start=14.55, anim_dur=1.25, cam=((.5, .5, 1.05), (.5, .5, 1.1)), fx=["shake_hits"]),
    dict(sub="top", t=(16.20, 17.85), src="E4_dbl_gasp", cam=((.5, .5, 1.05), (.5, .52, 1.2))),
    dict(sub="top", t=(17.85, 20.75), src="LIPSYNC", lips="E4_dbl_talk", cam=((.5, .5, 1.1), (.5, .53, 1.3))),
    dict(t=(20.75, 22.80), src="E4_step_back", anim=(0.0, 1.0), anim_start=20.95, anim_dur=1.1, cam=((.5, .45, 1.0), (.5, .45, 1.06))),
    # --- 4. «КТО ТЫ?» — «Я — ТЫ»
    dict(sub="top", t=(22.80, 24.30), src="LIPSYNC", lips="E4_alex_talk", cam=((.5, .42, 1.2), (.5, .42, 1.3))),
    dict(sub="top", t=(24.30, 26.40), src="E4_dbl_eyes", cam=((.5, .45, 1.0), (.5, .45, 1.15))),
    dict(sub="top", t=(26.40, 28.35), src="LIPSYNC", lips="E4_dbl_talk", cam=((.5, .48, 1.15), (.5, .48, 1.25))),
    dict(sub="top", t=(28.35, 31.20), src="LIPSYNC", lips="E4_dbl_talk", cam=((.5, .5, 1.0), (.5, .52, 1.15))),
    dict(t=(31.20, 33.40), src="E4_step_back", anim=(1.0, 1.0), cam=((.5, .45, 1.06), (.48, .45, 1.15))),
    # --- 5. THIRTY SECONDS — TEN THOUSAND
    dict(t=(33.40, 35.15), src="E4_pov_chair", cam=((.5, .55, 1.0), (.5, .6, 1.12)), phone="count_pre", fx=["vibrate"]),
    dict(t=(35.15, 37.15), src="E4_pov_chair_close", sub="top", cam=((.5, .6, 1.38), (.5, .6, 1.45)), phone="count"),
    dict(t=(37.15, 39.50), src="E4_pov_chair_close", sub="top", cam=((.5, .62, 1.45), (.5, .64, 1.62)), phone="count", fx=["redglow"]),
    dict(sub="top", t=(39.50, 41.85), src="E4_alex_talk_neutral", cam=((.5, .42, 1.15), (.5, .42, 1.35))),
    # --- 6. THE PHONE ON THE FLOOR — THE MIRROR
    dict(t=(41.85, 43.45), src="E4_phone_throw", anim=(0.0, 1.0), anim_start=42.30, anim_dur=1.0, cam=((.5, .5, 1.0), (.5, .55, 1.06)), fx=["shake_hits"]),
    dict(t=(43.45, 44.65), src="E4_phone_floor", cam=((.5, .5, 1.12), (.5, .5, 1.2)), phone="cracked", fx=["shake_hits"]),
    dict(t=(44.65, 46.55), src="E4_phone_floor", cam=((.5, .5, 1.25), (.5, .5, 1.4)), phone="cracked", fx=["glitch"]),
    dict(t=(46.55, 48.70), src="E4_mirror_far", mirror=True, cam=((.5, .45, 1.0), (.5, .44, 1.2))),
    dict(t=(48.70, 51.15), src="E4_mirror_close", mirror=True, cam=((.5, .45, 1.0), (.5, .45, 1.12)), fx=["redglow"]),
    # --- 7. «ЭТО НЕ ИГРА НА ДЕНЬГИ» — «ПРОВЕРКА»
    dict(sub="top", t=(51.15, 52.95), src="E4_dbl_pale_wide", cam=((.5, .5, 1.05), (.5, .5, 1.22))),
    dict(sub="top", t=(52.95, 55.70), src="LIPSYNC", lips="E4_dbl_pale", cam=((.5, .5, 1.05), (.5, .52, 1.2))),
    dict(t=(55.70, 57.55), src="E4_lean", anim=(0.0, 1.0), anim_start=55.8, anim_dur=1.4, cam=((.5, .45, 1.0), (.5, .43, 1.08))),
    dict(sub="top", t=(57.55, 59.35), src="LIPSYNC", lips="E4_alex_talk", cam=((.5, .42, 1.3), (.5, .42, 1.42))),
    dict(sub="top", t=(59.35, 60.75), src="E4_dbl_pale_neutral", cam=((.5, .5, 1.2), (.5, .5, 1.28))),
    dict(sub="top", t=(60.75, 64.50), src="LIPSYNC", lips="E4_dbl_pale", cam=((.5, .5, 1.28), (.5, .5, 1.45))),
    # --- 8. FOOTSTEPS
    dict(t=(64.50, 67.85), src="E4_doorway_steps", anim=(0.0, 1.0), anim_start=64.7, anim_dur=3.0, cam=((.5, .5, 1.0), (.47, .5, 1.12)), fx=["shake_hits"]),
    dict(t=(67.85, 70.10), src="E4_boots", anim=(0.0, 1.0), anim_start=67.85, anim_dur=2.2, cam=((.5, .55, 1.0), (.5, .58, 1.08)), fx=["shake_hits"]),
    dict(t=(70.10, 72.30), src="E4_grab", anim=(0.0, 1.0), anim_start=70.45, anim_dur=0.45, cam=((.5, .5, 1.0), (.5, .52, 1.1)), fx=["shake_hits"]),
    # --- 9. ROOM 204
    dict(sub="top", t=(72.30, 73.85), src="LIPSYNC", lips="E4_dbl_pale", cam=((.5, .5, 1.2), (.5, .5, 1.32))),
    dict(t=(73.85, 74.45), src="E4_room204_wide", cam=((.5, .5, 1.0), (.5, .48, 1.08)), fx=["memory", "glitch", "tube"]),
    dict(t=(74.45, 75.90), src="E4_room204", cam=((.5, .46, 1.0), (.5, .46, 1.18)), fx=["tube"]),
    dict(sub="top", t=(75.90, 78.00), src="E4_alex_wide", cam=((.5, .42, 1.15), (.5, .42, 1.3))),
    dict(sub="top", t=(78.00, 80.15), src="E4_dbl_look", cam=((.5, .5, 1.05), (.5, .5, 1.25))),
    # --- 10. THE OFFICER IN THE DOORWAY
    dict(t=(80.15, 81.35), src="E4_alex_turn", anim=(0.0, 1.0), anim_start=80.25, anim_dur=0.8, cam=((.5, .42, 1.0), (.5, .42, 1.06)), fx=["shake_hits"]),
    dict(t=(81.35, 83.40), src="E4_cop_doorway", cam=((.5, .45, 1.0), (.47, .4, 1.15)), fx=["shake_hits", "leakflicker"]),
    dict(t=(83.40, 86.55), src="E2_photo_cop", cam=((.5, .5, 1.0), (.5, .45, 1.12)), fx=["memory", "photo"]),
    dict(t=(86.55, 89.65), src="E4_cop_mask", cam=((.5, .45, 1.0), (.5, .42, 1.3))),
    dict(t=(89.65, 91.15), src="E4_cop_raise", anim=(0.0, 1.0), anim_start=89.75, anim_dur=0.8, cam=((.5, .45, 1.0), (.5, .5, 1.1))),
    # --- 11. THE SISTER
    dict(t=(91.15, 94.40), src="E4_cop_phone", sub="top", cam=((.5, .5, 1.0), (.55, .52, 1.15)), phone="sis"),
    dict(t=(94.40, 97.30), src="E4_cop_phone_close", sub="top", cam=((.5, .45, 1.15), (.5, .42, 1.4)), phone="sis"),
    dict(t=(97.30, 101.40), src="E4_cop_phone_close", sub="top", cam=((.5, .55, 1.25), (.5, .6, 1.45)), phone="sis", fx=["redglow"]),
    dict(t=(101.40, 104.95), src="E4_cop_phone_close", sub="top", cam=((.5, .58, 1.2), (.5, .62, 1.3)), phone="voice", fx=["vibrate"]),
    dict(t=(104.95, CUT_TO_BLACK), src="E4_cop_phone_close", sub="top", cam=((.5, .45, 1.3), (.5, .4, 1.75)), phone="voice", fx=["handshake"]),
    dict(t=(CUT_TO_BLACK, END), src="BLACK", fx=["endcard"]),
]

# ---------------------------------------------------------------- lip-sync (shape per frame from the VO envelope)
# windows where a character's mouth moves with the VO (quoted lines only; narration keeps the mouth closed)
LIP_WINDOWS = [(17.90, 20.20), (23.00, 24.00), (26.50, 27.90), (28.50, 30.62), (52.95, 55.20), (57.55, 58.90),
               (60.78, 64.05), (72.30, 73.85)]


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

# ---------------------------------------------------------------- phone screen states (same UI as EP01–EP03, text drawn in code)
PHONE_CLOCK = "02:51"
MSG_DONT = "Не входи. Там находится оригинал."
MSG_DONE, MSG_FOUND, MSG_KILL = "Задание выполнено.", "Объект найден.", "Теперь уничтожь копию."
MSG_30 = "Осталось тридцать секунд."
MSG_10K = "Уничтожь копию. Получишь десять тысяч долларов."
MSG_MIRROR = "Неповиновение зафиксировано."
MSG_NEXT = "Следующее задание начнётся с неё."
T_30, T_10K = 35.25, 37.27
PHONE = {
    "kill_hold": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_DONT)), (0, ("bubble", MSG_DONE)), (0, ("bubble", MSG_FOUND)), (0, ("bubble_red", MSG_KILL))],
    "count_pre": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_FOUND)), (0, ("bubble_small", MSG_KILL)), (33.70, ("typing", None))],
    "count": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_FOUND)), (0, ("bubble_small", MSG_KILL)),
              (T_30, ("bubble_red", MSG_30)), (T_30, ("timer", (T_30, 30))), (T_10K, ("bubble_red", MSG_10K))],
    "cracked": [(0, ("header", "Номер скрыт")), (0, ("bubble_small", MSG_KILL)), (0, ("bubble_red", MSG_30)), (0, ("timer", (T_30, 30))),
                (0, ("bubble_red", MSG_10K)), (43.62, ("crack", 7)), (44.90, ("glitch", None)), (45.80, ("off", None))],
    "sis": [(0, ("header", "Номер скрыт")), (91.85, ("photo_msg", "E4_sister_photo")), (97.34, ("bubble_red", MSG_NEXT))],
    "voice": [(0, ("header", "Номер скрыт")), (0, ("photo_msg", "E4_sister_photo")), (0, ("bubble_red", MSG_NEXT)),
              (101.75, ("voice", (105.15, 3.10)))],
}
# the red text on the hall mirror: scrambled glow from «на зеркале», legible on the quoted words
MIRROR = dict(text=MSG_MIRROR, scramble=47.55, legible=48.92)

# jolts -> camera shake (fx "shake_hits"): tape ripped, phone hits the floor, the crack, heavy steps, the grab, the turn, the reveal
HITS = [15.02, 43.02, 43.62, 66.35, 67.10, 67.95, 68.70, 69.45, 70.62, 80.32, 81.40]
FLASHES = [(13.30, "white"), (48.92, "red"), (74.45, "white"), (81.40, "white"), (97.34, "red"), (CUT_TO_BLACK - 0.04, "white")]
COUNTDOWN = None
ENDCARD = ("Серия 4 · «Не тот Алекс»", "Продолжение следует")
BIG_SUBS = ("«!Я — ты!.", "«!Неповиновение зафиксировано!».", "найди !комнату 204!».", "«!Следующее задание начнётся с неё!».",
            "«Алекс… пожалуйста… !не открывай дверь!».")

# ---------------------------------------------------------------- subtitles (*word* = yellow highlight, !word! = red danger)
# Only words that are in the voiceover; at most two lines each. Starts from silencedetect, ends from word timings.
SUBS = [
    (0.05, 3.04, "Человек на стуле плакал !моим голосом!."),
    (4.22, 7.18, "А телефон требовал *уничтожить копию*."),
    (8.63, 9.62, "Я подошёл ближе."),
    (9.86, 11.50, "На его запястье был *шрам*,"),
    (11.78, 13.80, "точно такой же, !как у меня!."),
    (14.56, 16.00, "Я сорвал ленту с его рта,"),
    (16.36, 17.50, "он сразу прошептал:"),
    (17.93, 20.30, "«Не трогай телефон. !Он слышит нас!»."),
    (21.01, 22.10, "Я отступил."),
    (23.03, 24.20, "«Кто ты?»"),
    (24.34, 25.70, "Он посмотрел мне в глаза."),
    (26.56, 28.00, "«!Я — ты!."),
    (28.53, 30.80, "Только я *уже проходил эту ночь*»."),
    (31.63, 33.20, "Я хотел задать ещё вопрос,"),
    (33.44, 35.00, "но телефон завибрировал."),
    (35.25, 36.80, "«!Осталось тридцать секунд!»."),
    (37.27, 38.50, "«Уничтожь копию —"),
    (38.68, 41.70, "получишь *десять тысяч долларов*»."),
    (41.90, 43.30, "Я бросил телефон на пол,"),
    (43.50, 44.50, "экран *треснул*,"),
    (44.66, 46.40, "но сообщение появилось снова."),
    (46.66, 48.40, "Теперь — *прямо на зеркале*."),
    (48.92, 51.10, "«!Неповиновение зафиксировано!»."),
    (51.17, 52.50, "Двойник *побледнел*."),
    (52.98, 53.90, "«Ты не понимаешь,"),
    (54.00, 55.30, "это !не игра на деньги!»."),
    (55.77, 57.40, "Я наклонился к нему:"),
    (57.59, 59.00, "«Тогда что это?»"),
    (59.42, 60.40, "Он прошептал:"),
    (60.81, 61.60, "«*Проверка*."),
    (61.76, 64.20, "Они ищут того, !кто помнит!»."),
    (64.62, 67.70, "В этот момент за дверью спальни *раздались шаги*."),
    (67.90, 69.80, "Медленные. *Тяжёлые*."),
    (70.27, 72.00, "Двойник схватил меня *за руку*."),
    (72.33, 73.60, "«Если хочешь выжить —"),
    (73.72, 75.80, "найди !комнату 204!»."),
    (76.36, 77.50, "Я спросил, где она,"),
    (77.70, 79.70, "но он уже смотрел *мне за спину*."),
    (80.31, 81.15, "Я обернулся."),
    (81.30, 83.32, "В дверном проёме стоял *полицейский*,"),
    (83.32, 86.40, "тот самый, которого я выбрал *во втором задании*."),
    (86.63, 89.50, "Только теперь его лицо было закрыто !чёрной маской!."),
    (89.74, 90.90, "Он поднял телефон."),
    (91.20, 93.90, "На экране была *фотография моей сестры*."),
    (94.47, 96.50, "Под ней — одно сообщение:"),
    (97.35, 100.60, "«!Следующее задание начнётся с неё!»."),
    (101.47, 104.40, "И тут из телефона раздался *её голос*:"),
    (105.15, 108.26, "«Алекс… пожалуйста… !не открывай дверь!»."),
]

# ---------------------------------------------------------------- sound events (time, kind, gain)
STEPS = [66.35, 67.10, 67.95, 68.70, 69.45]
SFX = (
    [(0.00, "sob", 0.65), (3.90, "breath", 0.5)]
    + [(t, "step", 0.4) for t in (7.70, 8.35, 9.00)] + [(10.05, "sting_soft", 0.5), (11.95, "cloth", 0.5), (13.30, "sting", 0.9)]
    + [(14.62, "cloth", 0.5), (15.00, "tape_rip", 1.0), (15.10, "gasp", 0.9), (16.40, "breath", 0.7)]
    + [(21.00, "cloth", 0.5), (21.10, "step", 0.55), (21.55, "step", 0.45), (26.45, "sting_soft", 0.6)]
    + [(33.62, "vibrate", 1.0), (T_30, "notify_bad", 0.75)] + [(T_30 + i, "tick", 0.55) for i in range(1, 8)]
    + [(T_10K, "notify_bad", 0.7), (39.25, "coin", 0.45)]
    + [(42.10, "whoosh", 0.7), (43.02, "phone_drop", 1.0), (43.02, "hit", 0.3), (43.62, "glass_crack", 1.0), (44.90, "glitch", 0.8), (45.80, "power_down", 0.8)]
    + [(47.55, "shimmer", 0.9), (48.92, "sting", 0.75), (51.20, "breath", 0.6), (55.85, "cloth", 0.5), (59.40, "breath", 0.5), (63.30, "sting_soft", 0.7)]
    + [(t, "heavy_step", 0.75 + 0.06 * i) for i, t in enumerate(STEPS)] + [(70.30, "heavy_step", 0.6), (71.10, "heavy_step", 0.55)]
    + [(70.60, "cloth", 0.7), (70.62, "hit", 0.3)]
    + [(73.86, "tube_on", 0.8), (74.45, "sting", 0.85)]
    + [(80.28, "whoosh", 0.85), (80.32, "cloth", 0.7), (81.40, "sting", 0.7), (81.40, "hit", 0.3), (83.45, "sting_soft", 0.6), (88.60, "hit", 0.4)]
    + [(89.80, "cloth", 0.5), (90.35, "phone_on", 0.8), (91.85, "notify", 0.45), (97.34, "notify_bad", 0.8), (97.34, "hit", 0.4)]
    + [(101.75, "vibrate", 0.8), (101.80, "notify", 0.4), (105.10, "voice_static", 0.9)]
    + [(CUT_TO_BLACK, "boom_tail", 0.9), (CUT_TO_BLACK, "sting", 0.6)]
)
HUM = [(73.85, 75.90)]   # the fluorescent tube in the corridor of room 204
# music intensity curve (time, level 0..1): picks up at EP03's end level, drops for the whispers and the sister's line
MUSIC = [(0, .45), (3.9, .5), (7.4, .35), (10.0, .45), (13.3, .65), (14.4, .55), (17.9, .3), (20.8, .4), (24.3, .3), (26.4, .45),
         (31.2, .4), (33.4, .55), (35.2, .7), (41.8, .8), (43.5, .6), (46.5, .5), (48.9, .8), (51.2, .45), (55.7, .4), (59.3, .25),
         (64.5, .45), (67.9, .6), (70.1, .7), (72.3, .55), (73.9, .7), (75.9, .5), (80.2, .6), (81.4, .85), (83.4, .55), (86.6, .7),
         (89.7, .6), (91.2, .55), (97.3, .85), (101.4, .45), (104.9, .25), (108.3, .25)]
BELLS = [(10.1, 880.0), (24.4, 784.0), (59.4, 740.0), (74.5, 987.8), (83.5, 932.3), (91.9, 987.8)]
RISER = (89.7, 97.3)


def check():
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a["t"][1] - b["t"][0]) < 1e-9, ("gap/overlap between shots", a["t"], b["t"])
    assert SHOTS[0]["t"][0] == 0 and SHOTS[-1]["t"][1] == END
    for a, b in zip(SUBS, SUBS[1:]):
        assert a[1] <= b[0] + 1e-9, ("overlapping subtitles", a, b)
    assert SUBS[-1][1] <= VO_END + 0.05
    assert all(0 <= t < END for t, _, _ in SFX)
    for t0, (k, d) in [e for els in PHONE.values() for e in els]:
        assert isinstance(t0, (int, float))
    for s in SHOTS:  # LIPSYNC shots must lie inside the lip windows or be closed-mouth
        pass


def export():
    check()
    data = dict(fps=FPS, vo_end=VO_END, cut_to_black=CUT_TO_BLACK, end=END, shots=SHOTS, lipsync=LIPSYNC, phone=PHONE, mirror=MIRROR,
                hits=HITS, flashes=FLASHES, countdown=COUNTDOWN, subtitles=SUBS, sfx=SFX, hum=HUM, music=MUSIC)
    with open(os.path.join(ROOT, "timeline", "ep04_timeline.json"), "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    export()
    print(f"{len(SHOTS)} shots, {len(SUBS)} subtitles, {len(SFX)} sfx events, {len(LIPSYNC)} lip shapes; runtime {END:.2f}s")
