"""EP13 word timings without Hugging Face: Whisper *small* (sherpa-onnx int8 export, GitHub release k2-fsa/sherpa-onnx asr-models),
run on the VO cut at its own pauses (silencedetect -36 dB, >= 0.09 s). Word times inside a chunk are spread by letter count.

usage: python3 scripts/01_transcribe.py /path/to/sherpa-onnx-whisper-small   -> timeline/transcript_raw.json
The verified phrase text is then fixed by hand in docs/EP13_transcript.txt and timeline/transcript_words.json.
"""
import glob, json, os, re, subprocess, sys
import numpy as np
import sherpa_onnx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = sys.argv[1]
mp3 = sorted(glob.glob(os.path.join(ROOT, "audio", "ElevenLabs_*.mp3")))[0]
SR = 16000
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", mp3, "-af", "silencedetect=n=-36dB:d=0.09", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
dur = len(a) / SR
# speech chunks = gaps between silences
chunks, t = [], 0.0
for s, e in zip(ss, se + [dur] * (len(ss) - len(se))):
    if s - t > 0.15: chunks.append((t, s))
    t = e
if dur - t > 0.15: chunks.append((t, dur))
rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=f"{M}/small-encoder.int8.onnx", decoder=f"{M}/small-decoder.int8.onnx", tokens=f"{M}/small-tokens.txt",
    language="ru", task="transcribe", num_threads=4)
out = []
for s, e in chunks:
    st = rec.create_stream(); st.accept_waveform(SR, a[int(s * SR):int(e * SR)]); rec.decode_stream(st)
    text = st.result.text.strip()
    ws = text.split(); n = sum(len(w) for w in ws) or 1; c = s; words = []
    for w in ws:
        d = (e - s) * len(w) / n; words.append({"w": w, "s": round(c, 3), "e": round(c + d, 3)}); c += d
    out.append({"start": round(s, 3), "end": round(e, 3), "text": text, "words": words})
    print(f"{s:7.2f}-{e:7.2f}  {text}")
json.dump(out, open(os.path.join(ROOT, "timeline", "transcript_raw.json"), "w"), ensure_ascii=False, indent=1)
