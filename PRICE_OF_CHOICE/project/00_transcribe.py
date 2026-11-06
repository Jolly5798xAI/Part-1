#!/usr/bin/env python3
"""Stage B (step 1): speech recognition of the approved voiceover -> timeline/asr_raw.json.

Two independent offline models (sherpa-onnx, CPU), downloaded from the k2-fsa/sherpa-onnx GitHub releases:
  - GigaAM v2 Russian transducer  (character timestamps)   sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19
  - Whisper large-v3-turbo         (cross-check of the text) sherpa-onnx-whisper-turbo
Models are NOT stored in the repo (~1.2 GB). Usage:

  WORK=/some/scratch/dir; mkdir -p $WORK/models && cd $WORK/models
  for m in sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19 sherpa-onnx-whisper-turbo; do
    curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/$m.tar.bz2 | tar xj; done
  ffmpeg -i "../audio/<voiceover>.mp3" -ar 16000 -ac 1 $WORK/vo16k.wav
  pip install sherpa-onnx soundfile
  python3 project/00_transcribe.py $WORK && cp $WORK/asr.json timeline/asr_raw.json

The verified transcript lives in docs/EP01_transcript.txt; 01_align.py maps it onto these timestamps.
"""
import sys, json, numpy as np, soundfile as sf, sherpa_onnx
S=sys.argv[1]; M=S+'/models/'
x,sr=sf.read(S+'/vo16k.wav',dtype='float32')
# energy-based phrase segmentation
hop=160; win=400
fr=np.array([np.sqrt(np.mean(x[i:i+win]**2)+1e-12) for i in range(0,len(x)-win,hop)])
db=20*np.log10(fr); thr=np.percentile(db,95)-38
voiced=db>thr
# find silences >= 0.25s
segs=[];inside=False;start=0;sil=0
minsil=int(0.25*sr/hop)
for i,v in enumerate(voiced):
    if v:
        if not inside: inside=True;start=i
        sil=0;last=i
    elif inside:
        sil+=1
        if sil>=minsil: segs.append((start,last));inside=False
if inside: segs.append((start,last))
segs=[(max(0,s*hop/sr-0.08),min(len(x)/sr,e*hop/sr+win/sr+0.08)) for s,e in segs if (e-s)*hop/sr>0.12]
g=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M+'sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19/encoder.int8.onnx',decoder=M+'sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19/decoder.onnx',joiner=M+'sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19/joiner.onnx',tokens=M+'sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19/tokens.txt',model_type='nemo_transducer',num_threads=4)
w=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+'sherpa-onnx-whisper-turbo/turbo-encoder.int8.onnx',decoder=M+'sherpa-onnx-whisper-turbo/turbo-decoder.int8.onnx',tokens=M+'sherpa-onnx-whisper-turbo/turbo-tokens.txt',language='ru',task='transcribe',num_threads=4)
out=[]
for a,b in segs:
    chunk=x[int(a*sr):int(b*sr)]
    r=[]
    for rec in (g,w):
        st=rec.create_stream(); st.accept_waveform(sr,chunk); rec.decode_stream(st); r.append(st.result)
    toks=[(t,round(a+ts,3)) for t,ts in zip(r[0].tokens,r[0].timestamps)]
    out.append(dict(start=round(a,3),end=round(b,3),giga=r[0].text,whisper=r[1].text.strip(),tokens=toks))
    print(f"{a:6.2f}-{b:6.2f} | G: {r[0].text}\n              | W: {r[1].text.strip()}")
json.dump(out,open(S+'/asr.json','w'),ensure_ascii=False,indent=1)
