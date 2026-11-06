#!/usr/bin/env python3
"""Stage E/G: assemble the episode from timeline/EP01_timeline.json.

Per shot, the first source found is used:
  1. scenes/<SHOT>.mp4 | .mov       generated video clip  (trimmed / held to the exact frame count)
  2. scenes/<SHOT>.png | .jpg       generated still        (animated with the camera move from the timeline — a camera move, not "video")
  3. assets/ui/<SHOT>.mp4           phone UI insert (04_ui.py)
  4. --animatic only: a labelled storyboard card (renders/_cards/)

  python3 project/06_build.py              -> renders/EP01_PRICE_OF_CHOICE_FINAL.mp4  (refuses if any live shot is missing)
  python3 project/06_build.py --animatic   -> renders/EP01_ANIMATIC_PREVIEW.mp4       (cards for missing shots, watermarked)

All shots get the same grade + grain; peephole shots get the circular fisheye mask. Subtitles (ASS) are burned in,
audio is audio/EP01_final_mix.wav. Output: 1080x1920, 24 fps, H.264 High, yuv420p, AAC 48 kHz, faststart.
"""
import subprocess, pathlib, sys, json, shutil, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, timeline
import shots as S

ANIMATIC = "--animatic" in sys.argv
TL = timeline()
W, H, FPS = TL["width"], TL["height"], TL["fps"]
WORK = ROOT / "renders/_work"; CARDS = ROOT / "renders/_cards"; OVL = ROOT / "assets/overlays"
FONT = str(ROOT / "assets/fonts/Inter-SemiBold.otf")
PEEPHOLE = {"S05_E", "S06_A", "S08_B", "S09_A", "S09_B", "S10_B", "S10_C", "S10_D", "S10_E"}
GRADE = ("eq=contrast=1.05:saturation=0.82:gamma=0.97,"
         "colorbalance=rs=-0.03:bs=0.06:rm=-0.02:bm=0.03:rh=-0.01:bh=0.01,"
         "curves=all='0/0.035 0.5/0.47 1/0.96'")
GRAIN_LIVE = "noise=alls=7:allf=t+u"
GRAIN_UI = "noise=alls=3:allf=t+u"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("ffmpeg failed:\n" + " ".join(map(str, cmd)) + "\n" + r.stderr[-2000:])

def peephole_mask():
    OVL.mkdir(parents=True, exist_ok=True)
    p = OVL / "peephole_mask.png"
    if p.exists(): return p
    m = Image.new("L", (W, H), 255); d = ImageDraw.Draw(m)
    r = 500; cx, cy = W // 2, int(H * 0.42)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    m = m.filter(ImageFilter.GaussianBlur(28))
    rgba = Image.new("RGBA", (W, H), (3, 4, 6, 255)); rgba.putalpha(m)
    rgba.save(p); return p

def find_source(seg):
    for rel in [seg["source"]] + seg["source_alternatives"] + ([seg["source"].replace(".mp4", ".mov")] if seg["kind"] == "live" else []):
        if (ROOT / rel).exists(): return ROOT / rel
    return None

def card(seg):
    CARDS.mkdir(parents=True, exist_ok=True)
    p = CARDS / f"{seg['shot']}.png"
    im = Image.new("RGB", (W, H), (10, 13, 18)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = 1 - abs(y / H - 0.4) * 1.6
        d.line([(0, y), (W, y)], fill=(int(10 + 10 * k), int(13 + 13 * k), int(18 + 20 * k)))
    f = lambda s, n="Inter-SemiBold.otf": ImageFont.truetype(str(ROOT / "assets/fonts" / n), s)
    d.rounded_rectangle([70, 200, W - 70, 1130], 36, outline=(60, 72, 90), width=3)
    d.text((110, 240), "АНИМАТИК · кадр ещё не сгенерирован", font=f(34), fill=(232, 72, 77))
    d.text((110, 300), f"{seg['shot']}  ·  сцена {seg['scene']}", font=f(64, "InterDisplay-Bold.otf"), fill=(225, 230, 238))
    y = 410
    for line in textwrap.wrap(seg["visual"], 40):
        d.text((110, y), line, font=f(40, "Inter-Regular.otf"), fill=(200, 208, 220)); y += 54
    y += 20
    for line in textwrap.wrap("Камера: " + (seg["camera"] or ""), 48):
        d.text((110, y), line, font=f(32, "Inter-Regular.otf"), fill=(128, 138, 152)); y += 44
    d.text((110, 1070), f"{seg['duration']:.2f} с · prompts/EP01_prompts.md#{seg['shot'].lower()}", font=f(28, "Inter-Regular.otf"), fill=(110, 120, 135))
    im.save(p); return p

def zoom_for(camera):
    c = (camera or "").lower()
    if "pull" in c or "backwards" in c: return -0.06
    if "push" in c or "dolly" in c: return 0.06
    return 0.03

def build_shot(seg, src, is_card):
    out = WORK / f"{seg['shot']}.mp4"; n = seg["frames"]; dur = n / FPS
    post = [] if seg["kind"] == "ui" or is_card else [GRADE]
    post.append(GRAIN_UI if seg["kind"] == "ui" or is_card else GRAIN_LIVE)
    if not is_card and seg["kind"] == "live" and seg["shot"] in PEEPHOLE:
        mask = peephole_mask()
        flt = ("[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,tpad=stop_mode=clone:stop=-1,%s[v];"
               "[v][1:v]overlay=0:0,%s[o]") % (W, H, W, H, FPS, ",".join(post[:-1]) or "null", post[-1])
        ins = (["-loop", "1", "-i", str(src)] if src.suffix.lower() in (".png", ".jpg") else ["-i", str(src)]) + ["-loop", "1", "-i", str(mask)]
        run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", flt, "-map", "[o]", "-frames:v", str(n), *ENC, str(out)])
        return out
    if src.suffix.lower() in (".png", ".jpg"):
        z = zoom_for(seg["camera"]) if not is_card else 0.015
        z0, z1 = (1.0, 1.0 + z) if z >= 0 else (1.0 - z, 1.0)
        # per-frame scale from a 2x upscale keeps the move smooth (no zoompan jitter)
        zexpr = f"({z0}+({z1}-{z0})*t/{dur:.3f})"
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"scale=w='trunc({W}*{zexpr}/2)*2':h='trunc({H}*{zexpr}/2)*2':eval=frame,crop={W}:{H},fps={FPS}," + ",".join(post))
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(src), "-vf", vf, "-frames:v", str(n), *ENC, str(out)])
    else:
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},tpad=stop_mode=clone:stop=-1," + ",".join(post)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-frames:v", str(n), *ENC, str(out)])
    return out

def end_card():
    out = WORK / "END.mp4"; n = round(TL["end_card"]["end"] * FPS) - round(TL["end_card"]["start"] * FPS)
    t1, t2 = TL["end_card"]["text"]
    vf = (f"drawtext=fontfile='{ROOT/'assets/fonts/InterDisplay-Bold.otf'}':text='{t1}':fontsize=84:fontcolor=0xE6EAF0:x=(w-tw)/2:y=h*0.42:alpha='if(lt(t,0.35),0,min(1,(t-0.35)/0.3))',"
          f"drawtext=fontfile='{FONT}':text='{t2}':fontsize=40:fontcolor=0x8A94A3:x=(w-tw)/2:y=h*0.42+120:alpha='if(lt(t,0.5),0,min(1,(t-0.5)/0.3))'")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x030406:s={W}x{H}:r={FPS}", "-vf", vf, "-frames:v", str(n), *ENC, str(out)])
    return out

def main():
    WORK.mkdir(parents=True, exist_ok=True)
    plan, missing = [], []
    for seg in TL["segments"]:
        src = find_source(seg)
        if src is None:
            missing.append(seg["shot"])
            if ANIMATIC: plan.append((seg, card(seg), True))
        else:
            plan.append((seg, src, False))
    if missing and not ANIMATIC:
        print("Cannot build the FINAL video — generated visuals are missing for these shots:")
        for m in missing: print("  scenes/%s.mp4 (or .png/.jpg)" % m)
        print("Generate them with prompts/EP01_prompts.md, or run with --animatic for a timing preview.")
        sys.exit(2)
    parts = []
    for seg, src, is_card in plan:
        parts.append(build_shot(seg, src, is_card))
        print(f"  {seg['shot']:6s} {seg['frames']:4d}f  {'CARD' if is_card else src.relative_to(ROOT)}")
    parts.append(end_card())
    lst = WORK / "concat.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    picture = WORK / "picture.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(picture)])
    final = ROOT / ("renders/EP01_ANIMATIC_PREVIEW.mp4" if missing else "renders/EP01_PRICE_OF_CHOICE_FINAL.mp4")
    subs = ROOT / "subtitles/EP01_ru.ass"
    vf = f"ass='{subs}':fontsdir='{ROOT/'assets/fonts'}'"
    if missing:
        vf += (f",drawtext=fontfile='{FONT}':text='АНИМАТИК — НЕ ФИНАЛЬНОЕ ВИДЕО ({len(missing)} кадров не сгенерировано)':"
               f"fontsize=30:fontcolor=0xE8484D:x=(w-tw)/2:y=h-170:box=1:boxcolor=0x000000@0.55:boxborderw=12")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), "-i", str(ROOT / "audio/EP01_final_mix.wav"), "-vf", vf,
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", "-shortest", str(final)])
    print("written", final.relative_to(ROOT), "| missing live shots:", len(missing))

if __name__ == "__main__":
    main()
