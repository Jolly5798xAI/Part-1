#!/usr/bin/env python3
"""Stage E (audio): voiceover edit + original synthesized sound design + score + final mix.

Everything except the voiceover is synthesised here from scratch (numpy/scipy) — no third-party or
copyrighted samples. Cue times come from timeline/EP01_timeline.json.

Outputs (48 kHz):
  audio/stems/vo.flac       voiceover with the atmospheric pauses inserted (speech untouched)
  audio/stems/sfx.flac      all sound effects + room tone
  audio/stems/music.flac    dark-ambient score (ducked under the voice)
  audio/EP01_final_mix.wav  final mix, loudness-normalised to -14 LUFS / -1.5 dBTP
"""
import subprocess, json, pathlib, sys
import numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, timeline
import shots as S

SR = 48000
rng = np.random.default_rng(204)
TL = timeline()
DUR = TL["duration"]
N = int(round(DUR * SR))
CUT = TL["hard_cut_to_black"]

def db(x): return 10 ** (x / 20)
def t_(n): return np.arange(n) / SR
def env_ad(n, a, d):  # attack (s) / exponential decay time-constant (s)
    t = t_(n); return np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / d)
def bp(x, lo, hi, o=2): return signal.sosfilt(signal.butter(o, [lo, hi], "band", fs=SR, output="sos"), x)
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "high", fs=SR, output="sos"), x)
def noise(n): return rng.standard_normal(n)
def norm(x, peak=1.0): m = np.max(np.abs(x)) + 1e-9; return x / m * peak
def brown(n):
    b = np.cumsum(noise(n)); b = hp(b, 20); return norm(b)

def room_ir(sec=0.45, damp=6000):
    n = int(sec * SR); ir = noise(n) * np.exp(-t_(n) / (sec / 6)); ir = lp(ir, damp); ir[0] = 3.0
    return ir / np.sum(np.abs(ir)) * 8
IR_ROOM = room_ir()
IR_HALL = room_ir(1.1, 3500)  # stairwell (behind the door)
def verb(x, ir=IR_ROOM, wet=0.25): return x + wet * signal.fftconvolve(x, ir)[: len(x)]

# ------------------------------------------------------------------ effects
def fx_knock():
    n = int(0.35 * SR); t = t_(n)
    body = np.sin(2 * np.pi * 95 * t) * env_ad(n, 0.002, 0.045) + 0.6 * np.sin(2 * np.pi * 180 * t) * env_ad(n, 0.001, 0.03)
    click = bp(noise(n), 600, 3000) * env_ad(n, 0.0005, 0.006)
    metal = 0.15 * np.sin(2 * np.pi * 410 * t) * env_ad(n, 0.001, 0.12)  # steel door ring
    return verb(norm(body + 0.5 * click + metal) * 0.9)

def fx_door_blow():
    n = int(0.9 * SR); t = t_(n)
    thud = np.sin(2 * np.pi * (60 + 40 * np.exp(-t / 0.02)) * t) * env_ad(n, 0.002, 0.09)
    crack = bp(noise(n), 300, 5000) * env_ad(n, 0.0008, 0.02)
    ring = sum(a * np.sin(2 * np.pi * f * t) * env_ad(n, 0.001, d) for f, a, d in [(212, .25, .25), (377, .18, .2), (633, .1, .15), (1210, .05, .1)])
    rattle = bp(noise(n), 2000, 6000) * env_ad(n, 0.01, 0.06) * (1 + np.sign(np.sin(2 * np.pi * 38 * t))) * 0.2
    return verb(norm(thud + 0.6 * crack + ring + rattle), wet=0.35)

def fx_handle_rattle():
    n = int(0.45 * SR); y = np.zeros(n)
    for k in range(7):
        p = int((0.02 + k * 0.05 + rng.uniform(0, .02)) * SR); m = int(0.06 * SR)
        if p + m < n: y[p:p + m] += bp(noise(m), 1800, 7000) * env_ad(m, 0.0005, 0.008) * rng.uniform(.4, 1)
    tt = t_(n); y += 0.3 * np.sin(2 * np.pi * 900 * tt) * env_ad(n, 0.001, 0.08)
    return verb(norm(y))

def fx_phone_vibrate(wood=False):
    n = int(1.15 * SR); t = t_(n)
    gate = ((t % 0.55) < 0.38).astype(float); gate = lp(gate, 60)
    buzz = signal.sawtooth(2 * np.pi * 172 * t) * 0.6 + np.sin(2 * np.pi * 344 * t) * 0.3
    y = buzz * gate
    if wood:
        y = y + 0.8 * bp(noise(n), 150, 900) * gate * (0.5 + 0.5 * np.sin(2 * np.pi * 172 * t)) + 0.6 * lp(buzz * gate, 400)
    else:
        y = lp(y, 1500)
    return verb(norm(y), wet=0.12)

def tone(fs, n, d, a=0.002):
    t = t_(n); return sum(amp * np.sin(2 * np.pi * f * t) for f, amp in fs) * env_ad(n, a, d)

def fx_notify_ding():
    n = int(0.9 * SR); y = tone([(1318.5, 1), (2637, .2)], n, 0.18)
    m = int(0.12 * SR); y[m:] += tone([(1760, .8), (3520, .15)], n - m, 0.25)
    return verb(norm(y) * 0.8, wet=0.3)

def fx_money_chime():
    n = int(1.2 * SR); y = np.zeros(n)
    for k, f in enumerate([987.8, 1318.5, 1975.5]):
        m = int(k * 0.07 * SR); y[m:] += tone([(f, 1), (f * 2.01, .12)], n - m, 0.35)
    return verb(norm(y) * 0.8, wet=0.35)

def fx_timer_start():
    n = int(0.25 * SR); return norm(tone([(880, 1), (1760, .3)], n, 0.05)) * 0.6

def fx_tick():
    n = int(0.12 * SR); y = bp(noise(n), 2500, 7000) * env_ad(n, 0.0003, 0.004) + 0.5 * tone([(3200, 1)], n, 0.01)
    return verb(norm(y), wet=0.4)

def fx_ui_tick_soft():
    n = int(0.1 * SR); return norm(tone([(2200, 1)], n, 0.012)) * 0.5

def fx_cloth_rustle(sec=0.6):
    n = int(sec * SR); e = lp(np.abs(noise(n)), 8) ; e = e / e.max() * np.hanning(n)
    return norm(bp(noise(n), 800, 6000) * e)

def fx_breath(sec=1.3, sharp=False):
    n = int(sec * SR); t = t_(n)
    e = np.sin(np.pi * np.clip(t / (sec * (0.35 if sharp else 0.45)), 0, 1)) ** 2
    e2 = np.sin(np.pi * np.clip((t - sec * 0.5) / (sec * 0.5), 0, 1)) ** 2 * (0 if sharp else 0.7)
    y = bp(noise(n), 400, 2500) * e + bp(noise(n), 300, 1800) * e2
    return verb(norm(y), wet=0.15)

def fx_water_shiver():
    n = int(0.8 * SR); t = t_(n)
    y = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * env_ad(n, 0.01, 0.2) * rng.uniform(.3, 1) for f in rng.uniform(1200, 4200, 8))
    y *= (1 + 0.5 * np.sin(2 * np.pi * 11 * t))
    return verb(norm(y) * 0.5, wet=0.3)

def fx_glass_set():
    n = int(1.0 * SR); t = t_(n)
    thump = lp(noise(n), 400) * env_ad(n, 0.001, 0.015)
    ring = sum(a * np.sin(2 * np.pi * f * t) * env_ad(n, 0.0005, d) for f, a, d in [(2310, 1, .25), (3770, .5, .18), (5420, .3, .1), (6950, .15, .07)])
    return verb(norm(0.6 * thump + 0.25 * ring), wet=0.25)

def fx_glass_rattle():
    n = int(0.7 * SR); y = np.zeros(n)
    for k in range(6):
        p = int(k * 0.1 * SR + rng.uniform(0, 0.03) * SR); g = fx_glass_set()[: int(0.2 * SR)] * rng.uniform(.3, .8)
        y[p:p + len(g)] += g[: n - p]
    return norm(y)

def fx_footstep_sock():
    n = int(0.3 * SR); return verb(norm(lp(noise(n), 500) * env_ad(n, 0.01, 0.04) + 0.3 * bp(noise(n), 1500, 4000) * env_ad(n, 0.02, 0.03)))

def fx_footstep_corridor():
    n = int(0.5 * SR); y = lp(noise(n), 1500) * env_ad(n, 0.002, 0.03) + 0.4 * bp(noise(n), 2000, 5000) * env_ad(n, 0.001, 0.01)
    return verb(lp(norm(y), 1200), IR_HALL, 0.5)

def fx_peephole_cover():
    n = int(0.3 * SR); return verb(norm(bp(noise(n), 1500, 6000) * env_ad(n, 0.001, 0.01) + 0.4 * tone([(2700, 1)], n, 0.04)))

def fx_corridor_hum():
    n = int(2.0 * SR); t = t_(n); y = (np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t) + 0.15 * bp(noise(n), 6000, 9000))
    return y * np.minimum(1, np.minimum(t / 0.2, (2.0 - t) / 0.5)) * 0.5

def fx_lock_touch():
    n = int(0.3 * SR); return verb(norm(tone([(3100, 1), (4850, .5), (7200, .2)], n, 0.03, 0.0005) + 0.3 * bp(noise(n), 3000, 8000) * env_ad(n, .0003, .004)))

def fx_low_boom():
    n = int(3.0 * SR); t = t_(n)
    y = np.sin(2 * np.pi * (34 + 30 * np.exp(-t / 0.15)) * t) * env_ad(n, 0.01, 0.9) + 0.3 * lp(noise(n), 200) * env_ad(n, 0.005, 0.4)
    rev = np.flip(bp(noise(int(0.6 * SR)), 300, 3000) * np.linspace(0, 1, int(0.6 * SR)) ** 3)  # pre-swell is placed before (see place)
    return norm(y)

def fx_tinnitus():
    n = int(2.2 * SR); t = t_(n); return np.sin(2 * np.pi * 6200 * t) * np.sin(np.pi * t / 2.2) ** 2

def fx_whoosh_short():
    n = int(0.45 * SR); e = np.sin(np.pi * t_(n) / 0.45) ** 3
    sweep = np.concatenate([bp(noise(n), 300 + 1000 * k, 1200 + 2500 * k)[int(k * n / 6): int((k + 1) * n / 6)] for k in np.linspace(0, 1, 6)])
    return norm(sweep[:n] * e[: len(sweep[:n])])

def fx_palm_slap_wet():
    n = int(0.6 * SR); t = t_(n)
    slap = bp(noise(n), 400, 4000) * env_ad(n, 0.0008, 0.02) + 0.5 * np.sin(2 * np.pi * 140 * t) * env_ad(n, 0.001, 0.04)
    wet = bp(noise(n), 1000, 5000) * env_ad(n, 0.01, 0.12) * (np.abs(lp(noise(n), 40)) > 0.03) * 0.35
    return lp(norm(slap + wet), 3500)  # heard through the door

def fx_smear():
    n = int(1.6 * SR); e = np.sin(np.pi * t_(n) / 1.6) ** 2
    return lp(norm(bp(noise(n), 500, 3000) * e * (0.6 + 0.4 * np.abs(lp(noise(n), 15)) / 0.1).clip(0, 2)), 3000)

def fx_key_insert():
    n = int(0.65 * SR); y = np.zeros(n)
    for k in range(5):  # key teeth passing the pins
        p = int((0.05 + k * 0.09) * SR); m = int(0.05 * SR)
        y[p:p + m] += (bp(noise(m), 2500, 9000) * env_ad(m, 0.0003, 0.006) + tone([(4200 + 300 * k, .6)], m, 0.01, 0.0003))
    m = int(0.5 * SR); y[: m] += 0.25 * bp(noise(m), 3000, 8000) * np.hanning(m)  # scrape
    return verb(norm(y), wet=0.2)

def fx_lock_pins():
    n = int(0.75 * SR); y = np.zeros(n)
    for k in range(6):
        p = int((0.04 + k * 0.11 + rng.uniform(0, .02)) * SR); m = int(0.08 * SR)
        y[p:p + m] += tone([(2600 + 180 * k, 1), (5300, .4)], m, 0.012, 0.0003) + 0.6 * bp(noise(m), 3000, 9000) * env_ad(m, .0003, .004)
    return verb(norm(y), wet=0.2)

def fx_lock_turn():
    n = int(1.2 * SR); t = t_(n); y = np.zeros(n)
    grind = bp(noise(n), 700, 4000) * np.clip(t / 0.15, 0, 1) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
    y += 0.5 * grind
    for p in (0.25, 0.55, 0.78):  # ratchet clicks of the bolt
        m = int(0.15 * SR); q = int(p * SR)
        y[q:q + m] += 1.4 * (tone([(1650, 1), (3100, .6), (5200, .3)], m, 0.02, 0.0004) + bp(noise(m), 1500, 7000) * env_ad(m, .0004, .006))
    return verb(norm(y), wet=0.2)

def fx_reveal_sting():
    n = int(4.0 * SR); t = t_(n)
    sub = np.sin(2 * np.pi * 41.2 * t) * env_ad(n, 0.02, 1.6)
    clus = sum(np.sin(2 * np.pi * f * t) for f in (220, 233.1, 311.1, 329.6)) * env_ad(n, 0.6, 1.5) * 0.25
    return norm(sub + lp(clus, 2500))

def fx_music_pulse_hit():
    n = int(2.0 * SR); t = t_(n); return norm(np.sin(2 * np.pi * 46 * t) * env_ad(n, 0.005, 0.5))

FX = dict(knock=fx_knock, door_blow=fx_door_blow, handle_rattle=fx_handle_rattle, phone_vibrate=fx_phone_vibrate,
          phone_vibrate_wood=lambda: fx_phone_vibrate(True), notify_ding=fx_notify_ding, money_chime=fx_money_chime,
          timer_start=fx_timer_start, tick=fx_tick, ui_tick_soft=fx_ui_tick_soft, cloth_rustle=fx_cloth_rustle,
          breath=fx_breath, breath_in_sharp=lambda: fx_breath(0.7, True), water_shiver=fx_water_shiver, glass_set=fx_glass_set,
          glass_rattle=fx_glass_rattle, footstep_sock=fx_footstep_sock, footstep_corridor=fx_footstep_corridor,
          peephole_cover=fx_peephole_cover, corridor_hum=fx_corridor_hum, lock_touch=fx_lock_touch, low_boom=fx_low_boom,
          tinnitus=fx_tinnitus, whoosh_short=fx_whoosh_short, palm_slap_wet=fx_palm_slap_wet, smear=fx_smear,
          key_insert=fx_key_insert, lock_pins=fx_lock_pins, lock_turn=fx_lock_turn, reveal_sting=fx_reveal_sting,
          music_pulse_hit=fx_music_pulse_hit)
# Sounds that happen on the far side of the steel door get muffled.
BEHIND_DOOR = {"footstep_corridor", "palm_slap_wet", "smear"}
MUSIC_FX = {"reveal_sting", "music_pulse_hit", "low_boom", "tinnitus"}  # routed to the music stem
BASE_LEVEL = -12.0  # dBFS reference for gain_db 0

def place(buf, x, t, gain_db, pan=0.0):
    i = int(round(t * SR)); x = x[: max(0, len(buf) - i)]
    if len(x) == 0: return
    g = db(BASE_LEVEL + gain_db)
    buf[i:i + len(x), 0] += x * g * np.sqrt(0.5 * (1 - pan)) * 1.414
    buf[i:i + len(x), 1] += x * g * np.sqrt(0.5 * (1 + pan)) * 1.414

# ------------------------------------------------------------------ voiceover with pauses
def load_vo():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / TL["voiceover"]), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    vo = np.frombuffer(raw, np.float32).astype(np.float64)
    parts, last = [], 0
    for p in TL["atmospheric_pauses"]:
        i = int(round(p["source_t"] * SR)); parts += [vo[last:i], np.zeros(int(round(p["seconds"] * SR)))]; last = i
    parts.append(vo[last:])
    out = np.concatenate(parts)
    y = np.zeros(N); y[: min(N, len(out))] = out[:N]
    return y

def automation(points, n):
    """points: [(t, dB)] linear-in-dB interpolation"""
    ts = np.array([p[0] for p in points]); ds = np.array([p[1] for p in points])
    return db(np.interp(t_(n), ts, ds))

def main():
    vo = load_vo()
    ev = [(s["t"], s["effect"], s["gain_db"], seg["shot"]) for seg in TL["segments"] for s in seg["sfx"]]
    T = {e: t for t, e, g, _ in sorted(ev, reverse=True)}  # first occurrence of each effect
    silence_t, reveal_t = T["silence_cut"], T["reveal_sting"]
    knock_t = min(t for t, e, g, _ in ev if e == "knock")
    riser_t = min(t for t, e, g, sh in ev if sh == "S11_A")

    # ---------------- SFX stem
    sfx = np.zeros((N, 2))
    rt = lp(brown(N), 400) * 0.5 + 0.15 * bp(noise(N), 800, 3000) + 0.08 * np.sin(2 * np.pi * 50 * t_(N))  # room tone + fridge hum
    rt = rt * automation([(0, -52), (silence_t, -52), (silence_t + 0.1, -58), (reveal_t, -58), (reveal_t + 1, -52), (DUR, -52)], N)
    sfx += np.stack([rt, np.roll(rt, 480)], 1)
    music_fx = np.zeros((N, 2))
    for t, e, g, sh in ev:
        if e not in FX: continue
        x = FX[e]()
        if e in BEHIND_DOOR: x = lp(x, 2500)
        pan = {"phone_vibrate_wood": -0.25, "notify_ding": -0.2, "footstep_sock": rng.uniform(-.15, .15), "breath": 0.05}.get(e, 0.0)
        place(music_fx if e in MUSIC_FX else sfx, x, t, g, pan)

    # ---------------- music stem: dark ambient, original
    t = t_(N)
    drone = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.41 * t + 0.3 * np.sin(2 * np.pi * 0.07 * t))
             + 0.35 * np.sin(2 * np.pi * 110.3 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t)))
    tension = np.sin(2 * np.pi * 58.27 * t) * np.clip((t - knock_t) / 8, 0, 1)  # minor-second rub enters with the knocks
    air = lp(bp(noise(N), 300, 1200), 1500) * 0.4 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t))
    high = np.sin(2 * np.pi * 1864.7 * t) * 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.1 * t))
    high_env = automation([(0, -80), (36.6, -80), (37.6, -6), (40.0, -6), (41.0, -80), (silence_t + 0.9, -80), (silence_t + 2.0, 0), (reveal_t, 0), (reveal_t + 0.05, -80), (DUR, -80)], N)
    # heartbeat pulse, accelerating; stops at the silence, returns after the reveal
    pulse = np.zeros(N)
    def beats(t0, t1, bpm0, bpm1):
        tt = t0
        while tt < t1:
            k = (tt - t0) / max(t1 - t0, 1e-3); bpm = bpm0 + (bpm1 - bpm0) * k
            for off, amp in ((0, 1.0), (0.18, 0.6)):
                i = int((tt + off) * SR); m = int(0.25 * SR)
                if i + m < N: pulse[i:i + m] += amp * np.sin(2 * np.pi * 48 * t_(m)) * env_ad(m, 0.004, 0.06)
            tt += 60 / bpm
    beats(knock_t + 1.8, silence_t, 62, 92)
    beats(reveal_t + 3.2, CUT, 78, 118)
    # riser into the cliffhanger
    k = np.clip((t - riser_t) / (CUT - riser_t), 0, 1)
    riser = (np.sin(2 * np.pi * np.cumsum(110 + 110 * k ** 2) / SR) * 0.4 + bp(noise(N), 500, 4000) * 0.5) * (k ** 2.2) * (t < CUT)
    level = automation([(0, -25), (5, -27), (knock_t, -26), (36, -26), (46, -25), (silence_t, -25), (silence_t + 0.25, -60),
                        (silence_t + 0.9, -42), (reveal_t - 0.02, -42), (reveal_t, -27), (66, -26), (CUT - 0.01, -21), (CUT, -120), (DUR, -120)], N)
    music_mono = lp(drone + tension + air, 900) * level + high * high_env * db(-18) + pulse * db(-22) * (t < CUT) + riser * db(-24)
    music = np.stack([music_mono, music_mono], 1)
    music[:, 1] = np.roll(music_mono, 240)  # tiny Haas width
    music += music_fx
    # dip the score under the whispered «Не верь телефону» (the double's silent line)
    seg = next(x for x in TL["segments"] if x["shot"] == "S10_E")
    music *= automation([(0, 0), (seg["start"] - 0.4, 0), (seg["start"], -7), (seg["end"] - 0.2, -7), (seg["end"] + 0.2, 0), (DUR, 0)], N)[:, None]
    # ducking under the voice
    env = np.sqrt(signal.sosfilt(signal.butter(1, 6, fs=SR, output="sos"), vo ** 2).clip(0))
    env = np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1)
    duck = db(-11 * env)
    music *= duck[:, None]
    sfx_duck = db(-3 * env)
    sfx *= sfx_duck[:, None]
    # hard cut: everything after the cut is silence (black end card)
    cut_i = int(CUT * SR)
    for st in (sfx, music): st[cut_i:] = 0
    vo2 = np.stack([vo, vo], 1); vo2[cut_i:] = 0

    stems = ROOT / "audio/stems"; stems.mkdir(parents=True, exist_ok=True)
    sf.write(stems / "vo.flac", vo2, SR, subtype="PCM_24")
    sf.write(stems / "sfx.flac", np.clip(sfx, -1, 1), SR, subtype="PCM_24")
    sf.write(stems / "music.flac", np.clip(music, -1, 1), SR, subtype="PCM_24")
    mix = vo2 * 1.0 + sfx + music
    mix = np.clip(mix, -1, 1)
    pre = ROOT / "audio/stems/_premix.wav"; sf.write(pre, mix, SR, subtype="FLOAT")
    # two-pass EBU R128 normalisation to TikTok-friendly -14 LUFS, -1.5 dBTP
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", af, "-c:a", "pcm_s24le", str(ROOT / "audio/EP01_final_mix.wav")], check=True)
    pre.unlink()
    print("mix written; premix measured", js["input_i"], "LUFS")

if __name__ == "__main__":
    main()
