"""Word-level transcription of the voiceover (faster-whisper). Output: timeline/transcript_words.json"""
import json, sys, glob, subprocess
import numpy as np
from faster_whisper import WhisperModel
mp3 = glob.glob("audio/ElevenLabs_*.mp3")[0]
model = WhisperModel(sys.argv[1] if len(sys.argv) > 1 else "medium", device="cpu", compute_type="int8")
pcm = subprocess.run(["ffmpeg","-v","error","-i",mp3,"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32)/32768
segs, info = model.transcribe(audio, language="ru", word_timestamps=True, beam_size=5)
out = []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                "words": [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}")
json.dump(out, open("timeline/transcript_words.json", "w"), ensure_ascii=False, indent=1)
