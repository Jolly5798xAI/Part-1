#!/usr/bin/env python3
"""Russian subtitles synced to the real word timings (output timeline, i.e. after the atmospheric pauses).

Outputs
  subtitles/EP01_ru.srt   plain SRT (upload to TikTok / any editor)
  subtitles/EP01_ru.ass   styled version burned into the video (safe zone for TikTok UI, key words highlighted)
Groups: 2–5 words, broken at punctuation, max ~24 characters, one line.
"""
import pathlib, sys, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, WORDS, out_t, timeline

TL = timeline()
CUT = TL["hard_cut_to_black"]
MAXC, MAXW = 24, 5
# key words: red = threat, ice-blue = money / system
RED = {"выломать", "стук", "газа", "стене", "погибнешь", "бить", "замолчал", "лицо", "окровавленную", "ладонь", "снаружи", "Двойник"}
ICE = {"500", "долларов", "тысячи", "две", "60", "10", "секунд", "минуты", "три"}
PHRASE_RED = ["Не верь телефону", "моё лицо", "лицом к стене", "Открой дверь"]

# words a group must not END on (they belong to the next word)
CLITIC = {"у", "в", "к", "с", "за", "на", "от", "и", "а", "но", "что", "как", "моё", "мою", "моего", "три", "две", "500", "60", "10",
          "это", "не", "«не", "уже", "был", "без", "ещё", "один", "кто-то", "через", "мне", "я", "он", "тут", "в"}

def split_line(ws):
    """optimal split of one transcript line into groups of 1..MAXW words (DP over break costs)"""
    n = len(ws)
    best = [0.0] + [1e9] * n
    back = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - MAXW), j):
            g = ws[i:j]
            txt = " ".join(w["text"] for w in g)
            c = 0.0
            if len(txt) > MAXC + 4: continue
            if len(txt) > MAXC: c += 3
            last = g[-1]["text"].lower().strip("«»:,.!?")
            if j < n and last in CLITIC: c += 20
            if j < n and not re.search(r"[,:—]$", g[-1]["text"]): c += 1.5
            if len(g) == 1 and n > 1: c += 4
            c += abs(len(txt) - 18) * 0.08     # prefer balanced ~18-char groups
            if best[i] + c < best[j]: best[j], back[j] = best[i] + c, i
    out, j = [], n
    while j > 0: out.append(ws[back[j]:j]); j = back[j]
    return out[::-1]

def groups():
    lines = {}
    for w in WORDS: lines.setdefault(w["line"], []).append(w)
    out = []
    for k in sorted(lines): out += split_line(lines[k])
    return out

def clean(t):
    t = re.sub(r"[.,]$", "", t)         # TikTok style: no trailing period/comma
    t = re.sub(r"\.(?=»)", "", t)
    return t

def fmt_srt(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
def fmt_ass(t):
    cs = int(round(t * 100)); return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"

def style_words(text):
    s = text
    for ph in PHRASE_RED:
        if ph in s:
            return s.replace(ph, r"{\c&H4F4AFF&}" + ph + r"{\c&HFFFFFF&}")
    toks = []
    for tok in s.split(" "):
        core = tok.strip("«»:,.—")
        if core in RED: toks.append(r"{\c&H4F4AFF&}" + tok + r"{\c&HFFFFFF&}")
        elif core in ICE: toks.append(r"{\c&HFFD39C&}" + tok + r"{\c&HFFFFFF&}")
        else: toks.append(tok)
    return " ".join(toks)

def main():
    gs = groups()
    # re-insert the dash that the transcript has between «Откроешь — погибнешь»
    cues = []
    for k, g in enumerate(gs):
        a = out_t(g[0]["start"]) - 0.04
        nxt = out_t(gs[k + 1][0]["start"]) - 0.04 if k + 1 < len(gs) else CUT
        b = min(nxt, out_t(g[-1]["end"]) + 0.45, CUT)
        text = " ".join(x["text"] for x in g).replace("«Откроешь погибнешь».", "«Откроешь — погибнешь»").replace("Время 60", "Время — 60")
        cues.append((max(0, a), b, clean(text)))
    # sanity: every transcript word appears exactly once, in order
    joined = " ".join(c[2] for c in cues)
    norm = lambda s: re.sub(r"[^\wё ]", "", s.lower()).split()
    assert norm(joined) == norm(" ".join(w["text"] for w in WORDS)), "subtitle words differ from transcript"
    d = ROOT / "subtitles"; d.mkdir(exist_ok=True)
    with open(d / "EP01_ru.srt", "w", encoding="utf-8") as f:
        for i, (a, b, t) in enumerate(cues, 1):
            f.write(f"{i}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{t}\n\n")
    head = f"""[Script Info]
Title: ЦЕНА ВЫБОРА — EP01
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,5,2,2,110,170,500,204

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(d / "EP01_ru.ass", "w", encoding="utf-8") as f:
        f.write(head)
        for a, b, t in cues:
            f.write(f"Dialogue: 0,{fmt_ass(a)},{fmt_ass(b)},Sub,,0,0,0,,{{\\fad(50,0)\\fscx94\\fscy94\\t(0,90,\\fscx100\\fscy100)}}{style_words(t)}\n")
    for a, b, t in cues:
        print(f"{a:6.2f}-{b:6.2f} {t}")
    print(len(cues), "cues")

if __name__ == "__main__":
    main()
