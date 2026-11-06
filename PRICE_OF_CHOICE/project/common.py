"""Shared helpers: time mapping and word lookup."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "project"))
import shots as S

def out_t(t, pause_before=False):
    """source-voiceover time -> output time. pause_before=True puts a pause starting exactly at t BEFORE t."""
    return round(t + sum(p for at, p in S.PAUSES if (at < t if pause_before else at <= t)), 3)

WORDS = json.load(open(ROOT / "timeline/EP01_words.json"))["words"]

def word_t(text, after=0.0, end=False):
    """output time of the first word starting with `text` (case/quote-insensitive) whose source start >= after"""
    for w in WORDS:
        if w["start"] >= after and w["text"].strip("«»:,.!?").lower().startswith(text.lower()):
            return out_t(w["end"] if end else w["start"])
    raise KeyError(text)

def timeline():
    return json.load(open(ROOT / "timeline/EP01_timeline.json"))
