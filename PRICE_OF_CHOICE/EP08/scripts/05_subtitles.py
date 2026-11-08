"""Export the subtitle track (timeline_ep08.SUBS) to subtitles/EP08_PRICE_OF_CHOICE.srt"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep08 as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def plain(text): return re.sub(r"[*!]", "", text).replace("¡", "!")


def wrap2(text, maxc=30):
    words = text.split(); lines = [""]
    for w in words:
        if len(lines[-1]) + len(w) + 1 > maxc and lines[-1]: lines.append(w)
        else: lines[-1] = (lines[-1] + " " + w).strip()
    if len(lines) > 2:  # rebalance into two lines
        mid = len(text) // 2; cut = text.rfind(" ", 0, mid + 6)
        lines = [text[:cut].strip(), text[cut:].strip()]
    return "\n".join(lines)


def main():
    out = os.path.join(ROOT, "subtitles", "EP08_PRICE_OF_CHOICE.srt")
    with open(out, "w", encoding="utf8") as f:
        for i, (a, b, text) in enumerate(TL.SUBS, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{wrap2(plain(text))}\n\n")
    print("wrote", out, len(TL.SUBS), "cues")


if __name__ == "__main__":
    main()
