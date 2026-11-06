#!/usr/bin/env python3
"""Stage B: align the approved transcript to the real speech timing.

Input : timeline/asr_raw.json   (GigaAM-v2 char timestamps + Whisper-turbo text, made by 00_transcribe.py)
        docs/EP01_transcript.txt (verified transcript, one phrase per line)
Output: timeline/EP01_words.json (every transcript word with start/end in seconds)

Words are matched to the GigaAM words by normalised spelling (difflib).
A word that GigaAM missed gets its time by interpolating between its neighbours.
"""
import json, re, difflib, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
asr = json.load(open(ROOT / "timeline/asr_raw.json"))

# --- GigaAM words with times (char-level timestamps -> word start/end)
gw = []
for seg in asr:
    cur, t0, tl = "", None, None
    for ch, ts in seg["tokens"]:
        if ch.strip() == "":
            if cur:
                gw.append((cur, t0, tl + 0.06))
            cur, t0 = "", None
            continue
        if t0 is None:
            t0 = ts
        cur += ch
        tl = ts
    if cur:
        gw.append((cur, t0, tl + 0.06))
    # last word of a phrase ends where the phrase's speech ends
    if gw:
        w, a, b = gw[-1]
        gw[-1] = (w, a, max(b, min(seg["end"] - 0.05, b + 0.35)))


def norm(w):
    w = w.lower().replace("ё", "е")
    w = re.sub(r"[^a-zа-я0-9]", "", w)
    return {"500": "пятьсот", "60": "шестьдесят", "10": "десять"}.get(w, w)


lines = [l.strip() for l in open(ROOT / "docs/EP01_transcript.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
words = []
for li, line in enumerate(lines):
    for tok in line.split():
        if tok in ("—", "-"):
            continue  # dashes are punctuation, attach nothing
        words.append({"line": li + 1, "text": tok, "key": norm(tok)})

# split hyphenated compounds the ASR writes as two words ("кто-то" -> "кто то")
gnorm = [norm(w) for w, _, _ in gw]
tkeys = []
for i, w in enumerate(words):
    for part in w["key"].split():
        tkeys.append((i, part))
sm = difflib.SequenceMatcher(a=[k for _, k in tkeys], b=gnorm, autojunk=False)
starts, ends = {}, {}
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag in ("equal", "replace") and (i2 - i1) == (j2 - j1):
        for k in range(i2 - i1):
            wi = tkeys[i1 + k][0]
            starts.setdefault(wi, gw[j1 + k][1])
            ends[wi] = gw[j1 + k][2]
    elif tag == "replace":  # unequal block: spread proportionally
        a, b = gw[j1][1], gw[j2 - 1][2]
        n = i2 - i1
        for k in range(n):
            wi = tkeys[i1 + k][0]
            starts.setdefault(wi, a + (b - a) * k / n)
            ends[wi] = a + (b - a) * (k + 1) / n

# hyphenated words: "кто-то" key is "ктото" -> try matching against joined ASR pairs
for i, w in enumerate(words):
    if i in starts:
        continue
    # interpolate from neighbours
    prev = max([j for j in starts if j < i], default=None)
    nxt = min([j for j in starts if j > i], default=None)
    a = ends[prev] if prev is not None else 0.0
    b = starts[nxt] if nxt is not None else a + 0.4
    # group consecutive missing words
    run = [j for j in range(prev + 1 if prev is not None else 0, nxt if nxt is not None else len(words)) if j not in starts]
    k = run.index(i)
    starts[i] = a + (b - a) * k / len(run)
    ends[i] = a + (b - a) * (k + 1) / len(run)
    w["interpolated"] = True

for i, w in enumerate(words):
    w["start"] = round(starts[i], 3)
    w["end"] = round(max(ends[i], starts[i] + 0.12), 3)
    w["index"] = i
    del w["key"]

json.dump({"source": "audio/ElevenLabs_2026-11-06T01_50_20_Artem Lebedev - Captivating and Engaging_eleven_v3.mp3",
           "duration": 74.919, "words": words}, open(ROOT / "timeline/EP01_words.json", "w"), ensure_ascii=False, indent=1)
for w in words:
    print(f'{w["index"]:3d} {w["start"]:6.2f}-{w["end"]:6.2f} {w["text"]}{" (interp)" if w.get("interpolated") else ""}')
