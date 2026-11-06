"""Procedural sound design + music (EP02 config: timeline_ep02.py) (no third-party samples -> no rights issues).

Writes:
  effects/sfx/*.wav          every synthesized one-shot (for reuse in later episodes)
  audio/music_ep02.wav       the tension score
  audio/mix_ep02.wav         VO (untouched, unaltered speed) + music + SFX + room tone, 48 kHz stereo
"""
import os, sys, glob, subprocess, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep02 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
rng = np.random.default_rng(1)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def t_(d): return np.arange(int(d * SR)) / SR
def env(n, a, d, curve=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) * curve / max(d, 1e-4))
    return e
def lp(x, fc):  # 2nd-order Butterworth low-pass
    from scipy.signal import butter, lfilter
    b, a = butter(2, min(fc, SR * 0.45) / (SR / 2)); return lfilter(b, a, x)
def hp(x, fc): return x - lp(x, fc)
def noise(d): return rng.standard_normal(int(d * SR))
def norm(x, peak=0.9): return x / (np.max(np.abs(x)) + 1e-9) * peak


# ------------------------------------------------------------------ one-shots
def sfx_knock():
    d = 0.35; t = t_(d)
    body = np.sin(2 * np.pi * 95 * t) * env(len(t), .002, .12, 5) + 0.5 * np.sin(2 * np.pi * 180 * t) * env(len(t), .001, .06, 6)
    click = lp(noise(d), 2500) * env(len(t), .0005, .02, 8)
    return norm(lp(body + 0.6 * click, 1800), .9)
def sfx_bang():
    d = 0.9; t = t_(d)
    sub = np.sin(2 * np.pi * (60 + 30 * np.exp(-t * 20)) * t) * env(len(t), .002, .35, 4)
    wood = lp(noise(d), 900) * env(len(t), .001, .12, 5)
    rattle = hp(noise(d), 2500) * env(len(t), .01, .25, 6) * 0.25 * (1 + np.sin(2 * np.pi * 31 * t))
    return norm(sub + 0.9 * wood + rattle, .95)
def sfx_hit():
    d = 2.6; t = t_(d)
    sub = np.sin(2 * np.pi * (45 + 60 * np.exp(-t * 12)) * t) * env(len(t), .003, 1.6, 3)
    air = lp(noise(d), 600) * env(len(t), .001, .5, 4) * 0.5
    metal = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([311, 467, 733])) * env(len(t), .002, 1.4, 4) * 0.08
    return norm(sub + air + metal, .95)
def sfx_boom_tail():
    d = 3.5; t = t_(d)
    x = np.sin(2 * np.pi * (38 + 25 * np.exp(-t * 6)) * t) * env(len(t), .005, 3.0, 2.5) + lp(noise(d), 300) * env(len(t), .01, 2.0, 3) * .4
    return norm(x, .9)
def sfx_vibrate():
    d = 0.95; t = t_(d)
    gate = ((t % 0.48) < 0.32).astype(float)
    gate = lp(gate, 60)
    buzz = np.sign(np.sin(2 * np.pi * 165 * t)) * 0.5 + np.sin(2 * np.pi * 330 * t) * 0.3
    return norm(lp(buzz, 700) * gate * (1 + 0.3 * np.sin(2 * np.pi * 9 * t)), .7)
def sfx_notify():
    d = 0.7; t = t_(d); x = np.zeros_like(t)
    for f, st in [(1318.5, 0.0), (1760.0, 0.09)]:
        n0 = int(st * SR); tt = t[: len(t) - n0]
        x[n0:] += np.sin(2 * np.pi * f * tt) * env(len(tt), .003, .35, 5) + 0.3 * np.sin(2 * np.pi * 2 * f * tt) * env(len(tt), .003, .15, 6)
    return norm(x, .6)
def sfx_notify_bad():
    d = 0.9; t = t_(d); x = np.zeros_like(t)
    for f, st in [(880, 0.0), (830.6, 0.12), (622.3, 0.24)]:
        n0 = int(st * SR); tt = t[: len(t) - n0]
        x[n0:] += np.sin(2 * np.pi * f * tt) * env(len(tt), .003, .4, 4)
    return norm(x, .6)
def sfx_coin():
    d = 0.9; t = t_(d); x = np.zeros_like(t)
    for f, st in [(1568, 0.0), (2093, 0.07), (2637, 0.14)]:
        n0 = int(st * SR); tt = t[: len(t) - n0]
        x[n0:] += np.sin(2 * np.pi * f * tt) * env(len(tt), .002, .5, 5)
    return norm(x, .55)
def sfx_alarm():
    d = 1.4; t = t_(d)
    x = np.sign(np.sin(2 * np.pi * 740 * t)) * ((t % 0.2) < 0.12) * env(len(t), .01, 1.2, 2)
    return norm(lp(x, 2500), .4)
def sfx_tick(hard=False):
    d = 0.12; t = t_(d)
    x = hp(noise(d), 3000) * env(len(t), .0003, .015, 8) + np.sin(2 * np.pi * (2200 if hard else 3200) * t) * env(len(t), .0005, .03, 8) * 0.5
    if hard: x += np.sin(2 * np.pi * 120 * t) * env(len(t), .001, .06, 5)
    return norm(x, .8 if hard else .5)
def sfx_glass():
    d = 1.2; t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t + p) * env(len(t), .001, dd, 4) * a for f, dd, a, p in
            [(2780, .9, .5, 0), (4110, .6, .35, 1), (5630, .4, .2, 2), (1210, .2, .4, 0)])
    x += lp(noise(d), 1500) * env(len(t), .0005, .02, 8) * .6
    return norm(x, .6)
def sfx_peep():
    d = 0.5; t = t_(d)
    x = lp(noise(d), 1200) * env(len(t), .05, .3, 4) * .6 + np.sin(2 * np.pi * 70 * t) * env(len(t), .005, .1, 5) * .5
    return norm(x, .5)
def sfx_tube_on():
    d = 0.9; t = t_(d)
    flick = (rng.random(len(t) // 1200 + 1) > 0.45).repeat(1200)[: len(t)].astype(float)
    x = (np.sin(2 * np.pi * 100 * t) + .5 * np.sin(2 * np.pi * 200 * t)) * lp(flick, 200) * .6 + hp(noise(d), 4000) * flick * 0.1
    return norm(x, .5)
def sfx_creak():
    d = 2.5; t = t_(d); x = np.zeros_like(t)
    # granular crackle: tiny clicks with a slowly rising rate = vertebrae / cartilage
    rate = 15 + 60 * (t / d)
    phase = np.cumsum(rate) / SR
    idx = np.where(np.diff(np.floor(phase)) > 0)[0]
    for i in idx:
        L = int(SR * .012)
        if i + L < len(x): x[i:i + L] += lp(noise(.012), 1800 + rng.random() * 2000)[:L] * np.hanning(L) * (0.4 + rng.random())
    x += np.sin(2 * np.pi * (180 + 40 * np.sin(2 * np.pi * .7 * t)) * t) * env(len(t), .4, 2.0, 2) * 0.12
    return norm(x, .7)
def sfx_slap():
    d = 0.6; t = t_(d)
    x = lp(noise(d), 2200) * env(len(t), .001, .05, 7) + np.sin(2 * np.pi * 140 * t) * env(len(t), .001, .08, 6) * .6
    x += lp(noise(d), 600) * env(len(t), .03, .35, 4) * .15  # wet smear
    return norm(x, .8)
def sfx_whisper():
    d = 1.2; t = t_(d)
    syll = np.zeros_like(t)
    for s, e in [(0, .14), (.14, .4), (.4, .55), (.55, .72), (.72, .88), (.88, 1.1)]:
        i0, i1 = int(s * SR), int(e * SR); syll[i0:i1] = np.hanning(i1 - i0)
    x = hp(lp(noise(d), 5000), 1200) * syll
    return norm(x, .35)
def sfx_lock_click():
    d = 0.35; t = t_(d)
    x = hp(noise(d), 2000) * env(len(t), .0003, .01, 8) + sum(np.sin(2 * np.pi * f * t) * env(len(t), .0005, .12, 6) * a for f, a in [(2400, .4), (3900, .25), (900, .3)])
    return norm(x, .8)
def sfx_lock_turn():
    d = 0.6; t = t_(d)
    grind = hp(noise(d), 1500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * t))) * env(len(t), .05, .4, 3) * 0.5
    return norm(grind + 0.6 * np.concatenate([np.zeros(int(.45 * SR)), sfx_lock_click()])[:len(t)], .85)
def sfx_lock_clack():
    d = 1.2; t = t_(d)
    x = sfx_lock_click()
    x = np.concatenate([x, np.zeros(len(t) - len(x))])
    x += np.sin(2 * np.pi * 85 * t) * env(len(t), .001, .25, 5) * .8 + hp(noise(d), 800) * env(len(t), .0005, .05, 7) * .5
    return norm(x, .95)


# ---- EP02 additions (appended after the EP01 set so the EP01 one-shots stay bit-identical)
def sfx_door_creak():  # door straining against the frame
    d = 2.2; t = t_(d)
    f = 70 + 25 * np.sin(2 * np.pi * 0.6 * t) + 15 * rng.standard_normal(len(t)).cumsum() / np.sqrt(len(t))
    stick = (np.sin(2 * np.pi * np.cumsum(f) / SR) > 0.6).astype(float)
    x = lp(hp(noise(d), 300), 1600) * lp(stick, 400) * env(len(t), .15, 1.6, 2)
    x += np.sin(2 * np.pi * np.cumsum(f * 2.1) / SR) * env(len(t), .2, 1.5, 2) * .25
    return norm(x, .7)
def sfx_water():  # slow trickle + drips
    d = 3.2; t = t_(d)
    x = lp(hp(noise(d), 900), 3500) * (0.25 + 0.15 * np.sin(2 * np.pi * 3.3 * t) ** 2) * np.minimum(1, t / 0.8)
    for st in (0.3, 0.9, 1.35, 2.0, 2.6):
        n0 = int(st * SR); tt = np.arange(int(.12 * SR)) / SR
        x[n0:n0 + len(tt)] += np.sin(2 * np.pi * (900 + 1400 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 45) * .8
    return norm(x * env(len(t), .3, 3.0, 1.2), .5)
def sfx_scream():  # short muffled cry behind a door (formant-filtered buzz, low-passed)
    d = 1.1; t = t_(d)
    f0 = 300 + 140 * np.sin(np.pi * np.minimum(1, t / 0.55)) - 120 * np.maximum(0, t - 0.55)
    src = np.sign(np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))) / SR))
    x = sum(lp(hp(src, fc * 0.8), fc * 1.2) * g for fc, g in ((800, 1.0), (1200, .6), (2600, .25)))
    x += hp(noise(d), 1500) * .15
    x = lp(x, 1400)  # through the door
    return norm(x * env(len(t), .03, .9, 2.2), .8)
def sfx_tap():  # finger on glass
    d = 0.15; t = t_(d)
    x = lp(noise(d), 3000) * env(len(t), .0005, .012, 8) + np.sin(2 * np.pi * 180 * t) * env(len(t), .001, .03, 6) * .5
    return norm(x, .6)


SFX_FUNCS = dict(knock=sfx_knock, bang=sfx_bang, hit=sfx_hit, boom_tail=sfx_boom_tail, vibrate=sfx_vibrate, notify=sfx_notify,
                 notify_bad=sfx_notify_bad, coin=sfx_coin, alarm=sfx_alarm, tick=lambda: sfx_tick(False), tick_hard=lambda: sfx_tick(True),
                 glass=sfx_glass, peep=sfx_peep, tube_on=sfx_tube_on, creak=sfx_creak, slap=sfx_slap, whisper=sfx_whisper,
                 lock_click=sfx_lock_click, lock_turn=sfx_lock_turn, lock_clack=sfx_lock_clack,
                 door_creak=sfx_door_creak, water=sfx_water, scream=sfx_scream, tap=sfx_tap)


# ------------------------------------------------------------------ music
def curve(points, t):
    xs, ys = zip(*points); return np.interp(t, xs, ys)

def music(dur):
    t = np.arange(int(dur * SR)) / SR
    lvl = curve(TL.MUSIC, t)
    lvl = lp(lvl, 3)
    # 1) low drone: detuned saws on A1 + E2, filtered, cutoff follows intensity
    def saw(f): return 2 * ((t * f) % 1) - 1
    drone = sum(saw(f) for f in (55.0, 55.3, 82.4, 82.0)) / 4
    drone = lp(drone, 400) * 0.55 + lp(drone, 140) * 0.45
    # 2) dissonant high string cluster (A4/Bb4/E5) fades in with tension
    cl = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 5.1 * t + i)) for i, f in enumerate([440.0, 466.2, 659.3, 698.5]))
    cl = cl / 4 * np.clip((lvl - 0.45) / 0.5, 0, 1) ** 1.5
    # 3) heartbeat pulse, bpm rises with intensity
    bpm = 62 + 50 * lvl
    ph = np.cumsum(bpm / 60 / SR)
    beat = np.zeros_like(t)
    frac = ph % 1
    for off, amp in [(0, 1.0), (0.22, 0.6)]:
        tt = (frac - off) % 1
        beat += amp * np.sin(2 * np.pi * 48 * tt * 0.6) * np.exp(-tt * 28)
    beat *= np.clip((lvl - 0.3) / 0.4, 0, 1)
    # 4) glassy motif in the mysterious part (sparse bell notes)
    bell = np.zeros_like(t)
    for st, f in getattr(TL, "BELLS", [(6.2, 987.8), (8.9, 880.0), (12.0, 784.0), (15.4, 740.0), (19.6, 987.8), (23.2, 932.3)]):
        n0 = int(st * SR); n = int(2.5 * SR); tt = np.arange(n) / SR
        bell[n0:n0 + n] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 2.2)
    # 5) final riser 66.3 -> 75.0
    r0, r1 = getattr(TL, "RISER", (66.3, 75.0))
    rs = np.clip((t - r0) / (r1 - r0), 0, 1) * (t < r1 + 0.3)
    riser = hp(noise(dur), 500) * rs ** 2.2 * 0.35
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 900 * rs ** 2) / SR) * rs ** 2 * 0.15
    x = 0.42 * drone * (0.4 + 0.6 * lvl) + 0.22 * cl + 0.55 * beat + 0.16 * bell + riser + sweep
    # hard stop at the cut to black, then a long low tail for the end card
    x[int(TL.CUT_TO_BLACK * SR):] = 0
    tail = np.arange(len(x) - int(TL.CUT_TO_BLACK * SR)) / SR
    x[int(TL.CUT_TO_BLACK * SR):] = lp(sum(saw(f)[: len(tail)] for f in (55.0, 55.4)), 120) * np.exp(-tail * 0.9) * 0.25
    return x * lvl.clip(0.08, 1) / 0.6


def room_tone(dur):
    n = noise(dur); brown = np.cumsum(n); brown = hp(brown / (np.max(np.abs(brown)) + 1e-9), 30)
    t = np.arange(len(n)) / SR
    hum = 0.15 * np.sin(2 * np.pi * 50 * t) + 0.05 * np.sin(2 * np.pi * 100 * t)
    return norm(lp(brown, 500), 1) * 0.6 + hum

def fluo_hum(dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * 100 * t) + .6 * np.sin(2 * np.pi * 200 * t) + .3 * np.sin(2 * np.pi * 300 * t) + .15 * hp(noise(dur), 6000)
    flick = lp((rng.random(len(t) // 2400 + 1) > 0.08).repeat(2400)[: len(t)].astype(float), 80)
    return x * flick


def db(x): return 10 ** (x / 20)


def main():
    os.makedirs(os.path.join(ROOT, "effects", "sfx"), exist_ok=True)
    vo_path = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", vo_path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    vo = np.frombuffer(pcm, np.float32).astype(np.float64)
    dur = TL.END
    N = int(dur * SR)
    mix = np.zeros((N, 2))
    # VO: untouched, starts at 0
    v = np.zeros(N); v[: min(N, len(vo))] = vo[:N]
    mix += np.stack([v, v], 1)
    stems = {}
    snap = lambda name: stems.__setitem__(name, mix.copy())
    snap('vo')

    # SFX
    cache = {}
    for name, fn in SFX_FUNCS.items():
        cache[name] = fn(); write_wav(os.path.join(ROOT, "effects", "sfx", f"{name}.wav"), cache[name])
    base_gain = dict(knock=-9, bang=-8, hit=-10, boom_tail=-10, vibrate=-17, notify=-17, notify_bad=-15, coin=-18, alarm=-22,
                     tick=-20, tick_hard=-15, glass=-17, peep=-18, tube_on=-22, creak=-14, slap=-14, whisper=-20,
                     lock_click=-12, lock_turn=-11, lock_clack=-8, door_creak=-13, water=-17, scream=-11, tap=-16)
    pans = dict(knock=0.0, bang=0.0, vibrate=0.15, scream=-0.1, water=0.05, glass=-0.1, lock_click=-0.2, lock_turn=-0.2, lock_clack=-0.15, creak=0.25)
    for t0, kind, g in TL.SFX:
        x = cache[kind] * db(base_gain[kind]) * g
        i0 = int(t0 * SR); i1 = min(N, i0 + len(x)); x = x[: i1 - i0]
        p = pans.get(kind, 0.0)
        mix[i0:i1, 0] += x * np.sqrt(0.5 * (1 - p)) * 1.414
        mix[i0:i1, 1] += x * np.sqrt(0.5 * (1 + p)) * 1.414

    snap('sfx')
    # music (with ducking under VO)
    m = music(dur); write_wav(os.path.join(ROOT, "audio", "music_ep02.wav"), norm(m, .8))
    vo_env = lp(np.abs(v), 6); duck = 1 - 0.45 * np.clip(vo_env / (np.percentile(vo_env, 95) + 1e-9), 0, 1)
    m = norm(m, 1) * db(-7) * duck
    wide = np.stack([m, np.roll(m, int(0.011 * SR))], 1)
    mix += wide

    snap('music')
    # beds
    rt = room_tone(dur) * db(-44); mix += np.stack([rt, np.roll(rt, 900)], 1)
    hum = fluo_hum(dur) * db(-36)
    hmask = np.zeros(N)
    for a, b in TL.HUM: hmask[int(a * SR): int(b * SR)] = 1
    hmask = lp(hmask, 8); mix += np.stack([hum * hmask] * 2, 1)
    snap('beds')
    if os.environ.get('STEMS'):
        prev = np.zeros_like(mix)
        for k in ['vo', 'sfx', 'music', 'beds']:
            write_wav(f'/tmp/claude-0/stem_{k}.wav', stems[k] - prev); prev = stems[k]
    # end: silence after the tail
    fade = np.ones(N); fe = int((dur - 0.6) * SR); fade[fe:] = np.linspace(1, 0, N - fe); mix *= fade[:, None]

    # safety limiter (soft clip) — VO peaks stay intact
    peak = np.max(np.abs(mix))
    if peak > 0.89: mix = mix / peak * 0.89  # linear gain only: VO dynamics untouched
    out = os.path.join(ROOT, "audio", "mix_ep02.wav"); write_wav(out, mix)
    print("mix written", out, f"{dur:.2f}s peak {peak:.2f}")


if __name__ == "__main__":
    main()
