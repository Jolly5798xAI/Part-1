"""Procedural sound design + music (EP04 config: timeline_ep04.py) (no third-party samples -> no rights issues).

The EP01–EP03 one-shots are re-synthesized in memory bit-identically (same generators, same RNG order; the files
already live in ../EP02/effects/sfx and ../EP03/effects/sfx). Only the NEW EP04 one-shots are written to effects/sfx/.

Writes:
  effects/sfx/<new>.wav      the 10 new EP04 one-shots
  audio/music_ep04.wav       the tension score (not stored in git)
  audio/mix_ep04.wav         VO (untouched, unaltered speed) + music + SFX + room tone, 48 kHz stereo (not stored in git)
"""
import os, sys, glob, subprocess, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep04 as TL

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


# ---- EP03 additions (appended after the EP01/EP02 set so those one-shots stay bit-identical)
def sfx_whoosh():  # fast body turn
    d = 0.6; t = t_(d)
    sweep = np.sin(np.pi * np.clip(t / 0.45, 0, 1)) ** 2
    n = hp(noise(d), 250)
    x = (lp(n, 900) * (1 - sweep) + lp(n, 3100) * sweep) * sweep
    return norm(x, .7)
def sfx_cloth():  # hoodie rustle
    d = 0.5; t = t_(d)
    x = hp(lp(noise(d), 4500), 1200) * env(len(t), .04, .3, 3) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 11 * t)))
    return norm(x, .45)
def sfx_wet_step():  # bare wet foot on laminate: soft slap + squelch
    d = 0.42; t = t_(d)
    slap = lp(noise(d), 1400) * env(len(t), .002, .04, 7) + np.sin(2 * np.pi * 95 * t) * env(len(t), .002, .05, 6) * .5
    squelch = lp(hp(noise(d), 600), 2600) * env(len(t), .03, .22, 4) * (0.5 + 0.5 * np.sin(2 * np.pi * (40 + 60 * t) * t)) * .55
    drip = np.sin(2 * np.pi * (1200 + 900 * np.exp(-np.maximum(0, t - .18) * 40)) * t) * np.exp(-np.maximum(0, t - .18) * 45) * (t > .18) * .25
    return norm(slap + squelch + drip, .55)
def sfx_step():  # socked foot on laminate
    d = 0.3; t = t_(d)
    x = lp(noise(d), 700) * env(len(t), .004, .06, 6) + np.sin(2 * np.pi * 80 * t) * env(len(t), .003, .07, 6) * .6
    return norm(x, .5)
def sfx_breath():  # held, shaky inhale through the nose
    d = 1.6; t = t_(d)
    shape = np.sin(np.pi * np.clip(t / 1.4, 0, 1)) ** 1.5 * (1 + 0.25 * np.sin(2 * np.pi * 7 * t))
    x = lp(hp(noise(d), 500), 2400) * shape
    return norm(x, .35)
def sfx_sting():  # dissonant hit for an apparition
    d = 2.8; t = t_(d)
    cl = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([233.1, 246.9, 349.2, 370.0, 493.9])) / 5
    x = cl * env(len(t), .005, 2.2, 3) + lp(noise(d), 400) * env(len(t), .002, .3, 4) * .6
    x += np.sin(2 * np.pi * (52 + 40 * np.exp(-t * 10)) * t) * env(len(t), .003, 1.2, 3) * .8
    return norm(x, .9)
def sfx_sting_soft():  # «tss» — a breathy hush, high and quiet
    d = 1.0; t = t_(d)
    x = hp(lp(noise(d), 9000), 3500) * np.sin(np.pi * np.clip(t / 0.8, 0, 1)) ** 2
    return norm(x, .3)
def sfx_knock_muffled():  # a fist on the far side of the padded door
    d = 0.5; t = t_(d)
    x = np.sin(2 * np.pi * 70 * t) * env(len(t), .003, .16, 5) + lp(noise(d), 500) * env(len(t), .001, .05, 6) * .7
    return norm(lp(x, 600), .9)
def sfx_ring_muffled():  # a phone ringing + buzzing behind a closed door (2.8 s)
    d = 2.8; t = t_(d); x = np.zeros_like(t)
    notes = [(0.0, 1318.5), (0.14, 1568.0), (0.28, 1760.0), (0.9, 1318.5), (1.04, 1568.0), (1.18, 1760.0), (1.8, 1318.5), (1.94, 1568.0), (2.08, 1760.0)]
    for st, f in notes:
        n0 = int(st * SR); tt = t[: len(t) - n0]
        x[n0:] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * env(len(tt), .003, .2, 5)
    buzz = (np.sign(np.sin(2 * np.pi * 160 * t)) * 0.4) * lp(((t % 0.9) < 0.55).astype(float), 40)
    x = lp(x * 0.8 + buzz * 0.5, 900)  # through the door
    return norm(x, .55)
def sfx_mmph():  # muffled protest behind tape: «м-м-м!» in short bursts
    d = 1.6; t = t_(d)
    f0 = 210 + 60 * np.sin(2 * np.pi * 2.6 * t)
    src = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR))
    gate = lp(((t % 0.38) < 0.27).astype(float), 25)
    x = lp(hp(src, 120), 700) * gate * env(len(t), .03, 1.4, 1.5)
    return norm(x, .6)
def sfx_chair_creak():  # wooden chair rocking under someone tied to it
    d = 1.4; t = t_(d); x = np.zeros_like(t)
    for st in (0.0, 0.3, 0.62, 0.95):
        n0 = int(st * SR); L = int(.22 * SR); tt = np.arange(L) / SR
        f = 420 + 160 * np.sin(2 * np.pi * 3 * tt)
        x[n0:n0 + L] += lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (rng.random(L) > 0.4), 1800) * np.hanning(L) * .5
    return norm(x, .5)
def sfx_sob():  # crying through taped lips: nasal hum broken by sobs (4.8 s)
    d = 4.8; t = t_(d)
    sobs = np.zeros_like(t)
    for st, ln in ((0.0, .55), (0.7, .4), (1.2, .9), (2.3, .5), (2.95, 1.1), (4.2, .5)):
        i0, i1 = int(st * SR), int(min(d, st + ln) * SR); sobs[i0:i1] = np.hanning(i1 - i0) ** 0.7
    f0 = 260 + 70 * sobs + 25 * np.sin(2 * np.pi * 5.5 * t)  # quivering pitch
    src = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR))
    x = sum(lp(hp(src, fc * 0.7), fc * 1.3) * g for fc, g in ((300, 1.0), (900, .35)))
    x = lp(x, 1100) * sobs + lp(hp(noise(d), 400), 1600) * sobs * .12   # breath leaking through the nose
    return norm(x, .6)



# ---- EP04 additions (appended after the EP01–EP03 set so those one-shots stay bit-identical)
def sfx_tape_rip():  # duct tape ripped off skin: a fast tearing crackle
    d = 0.5; t = t_(d)
    rate = 900 * np.exp(-t * 4)
    ph = np.cumsum(rate) / SR; clicks = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
    x = lp(hp(noise(d), 1500), 7000) * env(len(t), .005, .22, 4) * .6 + lp(clicks, 5000) * 3 * env(len(t), .002, .25, 4)
    return norm(x, .75)
def sfx_gasp():  # sharp inhale through an open mouth
    d = 0.6; t = t_(d)
    shape = np.sin(np.pi * np.clip(t / 0.4, 0, 1)) ** 0.8
    x = lp(hp(noise(d), 700), 3800) * shape + lp(hp(noise(d), 300), 1200) * shape * .4
    return norm(x, .5)
def sfx_phone_drop():  # a phone smacks onto a laminate floor, small rattle
    d = 0.7; t = t_(d)
    x = lp(noise(d), 2500) * env(len(t), .0005, .02, 8) + np.sin(2 * np.pi * 160 * t) * env(len(t), .001, .06, 6) * .7
    n0 = int(.09 * SR); x[n0:] += (lp(noise(d), 3000) * env(len(t), .0005, .015, 8))[: len(x) - n0] * .4
    x += hp(noise(d), 3500) * env(len(t), .002, .1, 6) * .25
    return norm(x, .85)
def sfx_glass_crack():  # the screen glass cracking: a sharp tick and a spreading crackle
    d = 0.9; t = t_(d); x = np.zeros_like(t)
    x += hp(noise(d), 3000) * env(len(t), .0003, .01, 8)
    for i in range(26):
        st = 0.01 + (i / 26) ** 1.6 * 0.6; n0 = int(st * SR); L = int(.008 * SR)
        x[n0:n0 + L] += hp(noise(.008), 2500 + rng.random() * 4000)[:L] * np.hanning(L) * (1 - i / 30)
    x += sum(np.sin(2 * np.pi * f * t) * env(len(t), .0005, .15, 6) * .15 for f in (3100, 4870))
    return norm(x, .7)
def sfx_glitch():  # a dying screen: digital stutter
    d = 0.8; t = t_(d)
    gate = (rng.random(len(t) // 600 + 1) > 0.5).repeat(600)[: len(t)].astype(float)
    x = (np.sign(np.sin(2 * np.pi * 1200 * t)) * .3 + hp(noise(d), 2000) * .5) * gate * env(len(t), .01, .7, 2)
    return norm(lp(x, 6000), .45)
def sfx_power_down():  # a falling electronic whine and click
    d = 0.7; t = t_(d)
    f = 1800 * np.exp(-t * 6) + 80
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), .005, .5, 3) * .5 + hp(noise(d), 3000) * env(len(t), .0005, .01, 8)
    return norm(x, .45)
def sfx_shimmer():  # the message forming on the mirror: glassy, rising, detuned
    d = 2.2; t = t_(d)
    x = sum(np.sin(2 * np.pi * f * (1 + 0.02 * t) * t + i) for i, f in enumerate([1480, 1567, 2217, 2349])) / 4
    x = x * np.clip(t / 1.2, 0, 1) ** 2 * env(len(t), 1.3, .8, 3) + hp(noise(d), 6000) * np.clip(t / 1.4, 0, 1) * .08
    return norm(x, .4)
def sfx_heavy_step():  # a boot on laminate behind a wall: low thud, slight creak
    d = 0.6; t = t_(d)
    x = np.sin(2 * np.pi * (55 + 30 * np.exp(-t * 25)) * t) * env(len(t), .003, .2, 5) + lp(noise(d), 400) * env(len(t), .001, .06, 6) * .8
    x += lp(hp(noise(d), 500), 1500) * env(len(t), .05, .25, 4) * .15
    return norm(lp(x, 900), .9)
def sfx_phone_on():  # a phone screen waking: soft click and a short tone
    d = 0.6; t = t_(d)
    x = hp(noise(d), 2500) * env(len(t), .0003, .008, 8) * .6 + np.sin(2 * np.pi * 660 * t) * env(len(t), .01, .25, 5) * .3
    return norm(x, .5)
def sfx_voice_static():  # a phone speaker on: faint crackle under the line (the VO itself is untouched)
    d = 3.3; t = t_(d)
    crack = (rng.random(len(t)) > 0.9985).astype(float)
    x = lp(hp(noise(d), 1800), 4000) * .12 + lp(crack, 3000) * 2.5
    x *= np.clip(t / 0.15, 0, 1) * np.clip((d - t) / 0.3, 0, 1)
    return norm(x, .25)


SFX_FUNCS = dict(knock=sfx_knock, bang=sfx_bang, hit=sfx_hit, boom_tail=sfx_boom_tail, vibrate=sfx_vibrate, notify=sfx_notify,
                 notify_bad=sfx_notify_bad, coin=sfx_coin, alarm=sfx_alarm, tick=lambda: sfx_tick(False), tick_hard=lambda: sfx_tick(True),
                 glass=sfx_glass, peep=sfx_peep, tube_on=sfx_tube_on, creak=sfx_creak, slap=sfx_slap, whisper=sfx_whisper,
                 lock_click=sfx_lock_click, lock_turn=sfx_lock_turn, lock_clack=sfx_lock_clack,
                 door_creak=sfx_door_creak, water=sfx_water, scream=sfx_scream, tap=sfx_tap,
                 whoosh=sfx_whoosh, cloth=sfx_cloth, wet_step=sfx_wet_step, step=sfx_step, breath=sfx_breath, sting=sfx_sting,
                 sting_soft=sfx_sting_soft, knock_muffled=sfx_knock_muffled, ring_muffled=sfx_ring_muffled, mmph=sfx_mmph,
                 chair_creak=sfx_chair_creak, sob=sfx_sob,
                 tape_rip=sfx_tape_rip, gasp=sfx_gasp, phone_drop=sfx_phone_drop, glass_crack=sfx_glass_crack, glitch=sfx_glitch,
                 power_down=sfx_power_down, shimmer=sfx_shimmer, heavy_step=sfx_heavy_step, phone_on=sfx_phone_on, voice_static=sfx_voice_static)
NEW_EP03 = {"whoosh", "cloth", "wet_step", "step", "breath", "sting", "sting_soft", "knock_muffled", "ring_muffled", "mmph", "chair_creak", "sob"}
NEW_EP04 = {"tape_rip", "gasp", "phone_drop", "glass_crack", "glitch", "power_down", "shimmer", "heavy_step", "phone_on", "voice_static"}


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
        cache[name] = fn()
        if name in NEW_EP04: write_wav(os.path.join(ROOT, "effects", "sfx", f"{name}.wav"), cache[name])
    base_gain = dict(knock=-9, bang=-8, hit=-10, boom_tail=-10, vibrate=-17, notify=-17, notify_bad=-15, coin=-18, alarm=-22,
                     tick=-20, tick_hard=-15, glass=-17, peep=-18, tube_on=-22, creak=-14, slap=-14, whisper=-20,
                     lock_click=-12, lock_turn=-11, lock_clack=-8, door_creak=-13, water=-17, scream=-11, tap=-16,
                     whoosh=-14, cloth=-20, wet_step=-15, step=-20, breath=-22, sting=-11, sting_soft=-24, knock_muffled=-10,
                     ring_muffled=-16, mmph=-15, chair_creak=-18, sob=-17,
                     tape_rip=-13, gasp=-19, phone_drop=-10, glass_crack=-12, glitch=-20, power_down=-19, shimmer=-20, heavy_step=-9,
                     phone_on=-19, voice_static=-30)
    pans = dict(knock=0.0, bang=0.0, vibrate=0.15, scream=-0.1, water=0.05, glass=-0.1, lock_click=-0.2, lock_turn=-0.2, lock_clack=-0.15, creak=0.25,
                ring_muffled=0.35, wet_step=-0.15, breath=0.1, mmph=0.2, sob=0.15, chair_creak=0.25, heavy_step=-0.3, phone_drop=0.1)
    for t0, kind, g in TL.SFX:
        x = cache[kind] * db(base_gain[kind]) * g
        i0 = int(t0 * SR); i1 = min(N, i0 + len(x)); x = x[: i1 - i0]
        p = pans.get(kind, 0.0)
        mix[i0:i1, 0] += x * np.sqrt(0.5 * (1 - p)) * 1.414
        mix[i0:i1, 1] += x * np.sqrt(0.5 * (1 + p)) * 1.414

    snap('sfx')
    # music (with ducking under VO)
    m = music(dur); write_wav(os.path.join(ROOT, "audio", "music_ep04.wav"), norm(m, .8))
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
            write_wav(os.path.join(ROOT, 'audio', f'stem_{k}.wav'), stems[k] - prev); prev = stems[k]
    # end: silence after the tail
    fade = np.ones(N); fe = int((dur - 0.6) * SR); fade[fe:] = np.linspace(1, 0, N - fe); mix *= fade[:, None]

    # safety limiter (soft clip) — VO peaks stay intact
    peak = np.max(np.abs(mix))
    print("peak at", round(int(np.argmax(np.max(np.abs(mix), 1))) / SR, 2), "s")
    if peak > 0.89: mix = mix / peak * 0.89  # linear gain only: VO dynamics untouched
    out = os.path.join(ROOT, "audio", "mix_ep04.wav"); write_wav(out, mix)
    print("mix written", out, f"{dur:.2f}s peak {peak:.2f}")


if __name__ == "__main__":
    main()
