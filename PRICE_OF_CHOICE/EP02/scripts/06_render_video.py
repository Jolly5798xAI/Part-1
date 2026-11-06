"""Assemble an episode (EP02 config: timeline_ep02.py): illustrations + camera moves + phone UI + FX + subtitles + mixed audio -> MP4.

usage: python3 scripts/06_render_video.py [--preview START END] [--stills t1,t2,...] [--out FILE]
  default output: renders/EP02_PRICE_OF_CHOICE_FINAL.mp4 (1080x1920, 30 fps, H.264 + AAC)
"""
import os, sys, json, math, re, argparse, subprocess, functools
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep02 as TL
import phone_ui
phone_ui.CLOCK = getattr(TL, "PHONE_CLOCK", phone_ui.CLOCK)
phone_ui.LOCK_CLOCK = getattr(TL, "PHONE_CLOCK", phone_ui.LOCK_CLOCK)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ILL = os.path.join(ROOT, "illustrations")
OW, OH, FPS = 1080, 1920, TL.FPS
META = json.load(open(os.path.join(ILL, "meta.json")))
FONT_SUB = os.path.join(ROOT, "effects", "fonts", "PTSerif-Bold.ttf")
FONT_UI = os.path.join(ROOT, "effects", "fonts", "Rubik-Bold.ttf")


# ------------------------------------------------------------------ helpers
def ease_io(x): x = min(1, max(0, x)); return 0.5 - 0.5 * math.cos(math.pi * x)
def lerp(a, b, k): return a + (b - a) * k


def shot_at(t):
    for i, s in enumerate(TL.SHOTS):
        if s["t"][0] <= t < s["t"][1]: return i, s
    return len(TL.SHOTS) - 1, TL.SHOTS[-1]


@functools.lru_cache(maxsize=48)
def load(path):
    return Image.open(path).convert("RGB")


def anim_frames(name):
    d = os.path.join(ILL, name)
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".png"))


def perspective_coeffs(dst_quad, src_quad):
    """coeffs mapping output(dst) points -> input(src) points for Image.transform PERSPECTIVE"""
    A, B = [], []
    for (x, y), (u, v) in zip(dst_quad, src_quad):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


# ------------------------------------------------------------------ source (illustration + phone UI)
_src_cache = {}


def source_image(shot, t):
    src = shot["src"]
    if src == "BLACK": return None, None
    if src == "LIPSYNC":
        v = "neutral"
        for tt, vv in TL.LIPSYNC:
            if t >= tt: v = vv
        name = f"{shot.get('lips', 'S16_double_face')}_{v}"; return load(os.path.join(ILL, name + ".png")), name
    if "anim" in shot:
        fr = anim_frames(src)
        a0, a1 = shot["t"]
        st = shot.get("anim_start", a0); du = shot.get("anim_dur", a1 - st)
        k = min(1, max(0, (t - st) / du))
        f0, f1 = shot["anim"]
        idx = int(round(lerp(f0, f1, k) * (len(fr) - 1)))
        return load(fr[idx]), src
    img = load(os.path.join(ILL, src + ".png"))
    if "phone" in shot and src in META and "screen" in META[src]:
        els = TL.PHONE[shot["phone"]]
        key = (src, shot["phone"], phone_ui.signature(els, t))
        if key not in _src_cache:
            if len(_src_cache) > 12: _src_cache.clear()
            ui = phone_ui.draw_screen(els, t)
            quad = META[src]["screen"]
            # draw on a 2x canvas then downsample for crisp text
            coeffs = perspective_coeffs(quad, [(0, 0), (ui.width, 0), (ui.width, ui.height), (0, ui.height)])
            warped = ui.transform(img.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
            base = img.convert("RGBA")
            glow = warped.resize((img.width // 8, img.height // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)).resize(img.size, Image.BILINEAR)
            g = Image.new("RGBA", img.size, (0, 0, 0, 0)); g.paste(glow, (0, 0))
            gl = np.asarray(glow.convert("RGB"), np.float32) * (np.asarray(glow.split()[3], np.float32)[..., None] / 255) * 0.55
            out = np.clip(np.asarray(base.convert("RGB"), np.float32) + gl, 0, 255).astype(np.uint8)
            out = Image.fromarray(out).convert("RGBA"); out.alpha_composite(warped)
            _src_cache[key] = out.convert("RGB")
        return _src_cache[key], src
    return img, src


# ------------------------------------------------------------------ camera + shake
def rnd(seed):
    r = np.random.default_rng(seed); return r


def shake_offset(shot, t):
    dx = dy = 0.0; dz = 0.0
    fx = shot.get("fx", [])
    if "shake_hits" in fx:
        for h in TL.HITS:
            if shot["t"][0] - 0.05 <= h <= t:
                a = 34 * math.exp(-(t - h) * 10)
                dx += a * math.sin((t - h) * 95 + h * 7); dy += a * 0.8 * math.cos((t - h) * 83 + h * 3); dz += 0.02 * math.exp(-(t - h) * 12)
    if "vibrate" in fx:
        for t0, kind, _ in TL.SFX:
            if kind == "vibrate" and t0 <= t <= t0 + 0.95 and ((t - t0) % 0.48) < 0.32:
                dx += 5 * math.sin(t * 410); dy += 4 * math.cos(t * 370)
    if "handshake" in fx:
        dx += 4 * math.sin(t * 13.1) + 2 * math.sin(t * 29.7); dy += 3 * math.cos(t * 11.3)
    return dx, dy, dz


def camera(img, shot, t):
    (cx0, cy0, z0), (cx1, cy1, z1) = shot["cam"]
    k = ease_io((t - shot["t"][0]) / (shot["t"][1] - shot["t"][0]))
    cx, cy, z = lerp(cx0, cx1, k), lerp(cy0, cy1, k), lerp(z0, z1, k)
    dx, dy, dz = shake_offset(shot, t); z *= 1 + dz
    W, H = img.size
    cw, ch = W / z, H / z
    x0 = min(max(cx * W - cw / 2, 0), W - cw); y0 = min(max(cy * H - ch / 2, 0), H - ch)
    sx = cw / OW
    x0 -= dx * sx; y0 -= dy * sx
    return img.transform((OW, OH), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)


# ------------------------------------------------------------------ peephole lens
def _peephole_mesh():
    R = 760.0; cx, cy = OW / 2, OH / 2; k = 0.42
    def f(x, y):
        dx, dy = (x - cx) / R, (y - cy) / R; r = math.hypot(dx, dy)
        s = (1 + k * r * r) / (1 + k) * 0.94 + 0.06 * 1
        return cx + dx * s * R, cy + dy * s * R
    mesh = []; gx, gy = 18, 32
    for j in range(gy):
        for i in range(gx):
            x0, x1 = OW * i / gx, OW * (i + 1) / gx; y0, y1 = OH * j / gy, OH * (j + 1) / gy
            q = [*f(x0, y0), *f(x0, y1), *f(x1, y1), *f(x1, y0)]
            mesh.append(((int(x0), int(y0), int(math.ceil(x1)), int(math.ceil(y1))), q))
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    r = np.hypot(xx - cx, yy - cy)
    mask = np.clip((R * 0.93 - r) / 40, 0, 1)
    rim = np.exp(-((r - R * 0.93) / 14) ** 2) * 0.35  # faint brass rim
    shade = (1 - 0.55 * (r / R) ** 3).clip(0, 1)
    return mesh, (mask * shade)[..., None].astype(np.float32), rim[..., None].astype(np.float32), r


@functools.lru_cache(maxsize=1)
def peephole_data(): return _peephole_mesh()


def peephole(frame, iris=1.0):
    mesh, mask, rim, r = peephole_data()
    w = frame.transform((OW, OH), Image.MESH, mesh, Image.BILINEAR)
    a = np.asarray(w, np.float32) * mask + rim * np.array([200, 160, 90], np.float32)
    if iris < 1:
        a *= np.clip((iris * 760 - r) / 30, 0, 1)[..., None]
    return a


# ------------------------------------------------------------------ grade / texture
@functools.lru_cache(maxsize=1)
def grade_luts():
    x = np.arange(256) / 255.0
    s = x + 0.12 * np.sin(2 * np.pi * x) * x * (1 - x) * 2  # gentle S-curve
    r = np.clip(s * 1.02 + 0.01, 0, 1); g = np.clip(s * 1.0 + 0.008, 0, 1); b = np.clip(s * 0.96 + 0.035 * (1 - x), 0, 1)
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    v = 1 - 0.42 * (((xx - OW / 2) / (OW * 0.75)) ** 2 + ((yy - OH / 2) / (OH * 0.72)) ** 2)
    rg = np.random.default_rng(5)
    grain = [rg.normal(0, 1, (OH // 2, OW // 2)).astype(np.float32) for _ in range(6)]
    return (r * 255).astype(np.uint8), (g * 255).astype(np.uint8), (b * 255).astype(np.uint8), np.clip(v, 0.35, 1)[..., None].astype(np.float32), grain


def finish(a, t, fi, extra_gain=1.0, desat=0.0):
    lr, lg, lb, vig, grain = grade_luts()
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # haze/bloom (the reference has a soft, slightly hazy look)
    small = im.resize((OW // 6, OH // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((OW, OH), Image.BILINEAR)
    im = ImageChops.screen(im, Image.blend(Image.new("RGB", im.size), small, 0.22))
    im = ImageEnhance.Color(im).enhance(0.9 - desat)
    r, g, b = im.split(); im = Image.merge("RGB", (r.point(lr.tolist()), g.point(lg.tolist()), b.point(lb.tolist())))
    a = np.asarray(im, np.float32) * vig * extra_gain
    gr = grain[fi % len(grain)]
    a += np.kron(gr, np.ones((2, 2), np.float32))[..., None] * 5.0
    return a


# ------------------------------------------------------------------ text
_txt_cache = {}


def tokens(text):
    """split marked text into words with colour, keeping punctuation glued to its word"""
    mode = None
    words = []
    buf = ""; bmodes = []
    for ch in text:
        if ch == "*": mode = None if mode == "y" else "y"; continue
        if ch == "!": mode = None if mode == "r" else "r"; continue
        buf += ch; bmodes.append(mode)
    # group into words; a word's colour = colour of its first letter
    w = ""; wm = None
    for ch, m in zip(buf, bmodes):
        if ch == " ":
            if w: words.append((w, wm)); w = ""; wm = None
        else:
            if not w or (wm is None and ch.isalnum()): wm = m if (ch.isalnum() or wm is None) else wm
            w += ch
    if w: words.append((w, wm))
    return words


COL = {None: (255, 255, 255), "y": (255, 214, 72), "r": (255, 72, 64)}


def sub_image(text, size=68, maxw=880):
    key = (text, size)
    if key in _txt_cache: return _txt_cache[key]
    font = ImageFont.truetype(FONT_SUB, size)
    words = tokens(text)
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    sp = d.textlength(" ", font=font)
    lines = [[]]; lw = 0
    for w, m in words:
        ww = d.textlength(w, font=font)
        if lines[-1] and lw + sp + ww > maxw: lines.append([]); lw = 0
        lines[-1].append((w, m, ww)); lw += (sp if len(lines[-1]) > 1 else 0) + ww
    if len(lines) > 2 and size > 50: return sub_image(text, size - 6, maxw)
    if len(lines) == 2:  # balance two lines
        allw = [x for l in lines for x in l]; best = None
        for c in range(1, len(allw)):
            a = sum(x[2] for x in allw[:c]) + sp * (c - 1); b = sum(x[2] for x in allw[c:]) + sp * (len(allw) - c - 1)
            if a <= maxw and b <= maxw and (best is None or abs(a - b) < best[0]): best = (abs(a - b), c)
        if best: lines = [allw[:best[1]], allw[best[1]:]]
    lh = int(size * 1.22); pad = 30
    Wt = int(maxw + 2 * pad); Ht = lh * len(lines) + 2 * pad
    layer = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    shadow = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0)); sd = ImageDraw.Draw(shadow)
    y = pad
    for line in lines:
        tw = sum(x[2] for x in line) + sp * (len(line) - 1); x = (Wt - tw) / 2
        for w, m, ww in line:
            sd.text((x + 3, y + 5), w, font=font, fill=(0, 0, 0, 230), stroke_width=6, stroke_fill=(0, 0, 0, 230))
            ld.text((x, y), w, font=font, fill=COL[m] + (255,), stroke_width=4, stroke_fill=(10, 10, 12, 255))
            x += ww + sp
        y += lh
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    shadow.alpha_composite(layer)
    _txt_cache[key] = shadow
    return shadow


def subtitle_zone(shot):
    if shot.get("sub") == "bottom": return 1330  # EP02: phone shots where the top of the screen carries text
    if "phone" in shot or shot.get("sub") == "top": return 330  # phone fills the middle/bottom -> top
    return 1330


def draw_subs(frame, t, shot):
    for a, b, text in TL.SUBS:
        if a <= t < b:
            special = text.startswith("«!Не верь") or text in getattr(TL, "BIG_SUBS", ())
            img = sub_image(text, 84 if special else 66)
            age = t - a; k = min(1, age / 0.12)
            sc = 0.9 + 0.1 * k
            im2 = img.resize((int(img.width * sc), int(img.height * sc)), Image.BILINEAR) if sc < 1 else img
            if k < 1:
                al = im2.split()[3].point(lambda v: int(v * k)); im2 = im2.copy(); im2.putalpha(al)
            cy = subtitle_zone(shot)
            x = int(500 - im2.width / 2); y = int(cy - im2.height / 2)  # centred slightly left of the TikTok side rail
            frame.alpha_composite(im2, (max(0, x), y))
            break


def draw_countdown(frame, t):
    # TL.COUNTDOWN = (show_from, start, seconds) or None  (EP01 used (68.58, 69.96, 10))
    if not getattr(TL, "COUNTDOWN", None): return
    _, st, secs = TL.COUNTDOWN[:3]
    until = TL.COUNTDOWN[3] if len(TL.COUNTDOWN) > 3 else TL.CUT_TO_BLACK
    if t < st or t >= until: return
    rem = max(0, secs - int(t - st))
    d = ImageDraw.Draw(frame)
    f = ImageFont.truetype(FONT_UI, 92)
    txt = f"00:{rem:02d}"
    pulse = 1.0 - ((t - st) % 1.0)
    col = (255, int(60 + 80 * (1 - pulse)), int(60 + 80 * (1 - pulse)), 255)
    d.rounded_rectangle([330, 150, 670, 290], 30, fill=(20, 0, 0, 170), outline=(255, 70, 70, 255), width=4)
    d.text((500, 220), txt, font=f, fill=col, anchor="mm")


def draw_endcard(frame, t):
    k = min(1, max(0, (t - (TL.CUT_TO_BLACK + 0.35)) / 0.5))
    if k <= 0: return
    d = ImageDraw.Draw(frame)
    f1 = ImageFont.truetype(FONT_SUB, 96); f2 = ImageFont.truetype(os.path.join(ROOT, "effects", "fonts", "Rubik-Medium.ttf"), 40)
    d.text((OW // 2, 880), "ЦЕНА ВЫБОРА", font=f1, fill=(235, 30, 36, int(255 * k)), anchor="mm")
    line2, line3 = getattr(TL, "ENDCARD", ("Серия 1 · «Стакан воды»", "Продолжение следует"))
    d.text((OW // 2, 990), line2, font=f2, fill=(220, 220, 225, int(230 * k)), anchor="mm")
    d.text((OW // 2, 1060), line3, font=f2, fill=(160, 160, 168, int(230 * k)), anchor="mm")


def dust(frame, t, shot):
    rg = np.random.default_rng(int(shot["t"][0] * 100))
    d = ImageDraw.Draw(frame)
    for i in range(70):
        h = TL.HITS[rg.integers(len(TL.HITS))]
        x0 = rg.uniform(0, OW); y0 = rg.uniform(0, OH * 0.5); sp = rg.uniform(120, 380)
        age = t - shot["t"][0] - rg.uniform(0, 0.6)
        if age < 0: continue
        y = y0 + sp * age; x = x0 + 20 * math.sin(age * 3 + i)
        a = int(140 * max(0, 1 - age / 1.6)); r = rg.uniform(1.5, 4)
        if a > 0: d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 210, 190, a))


# ------------------------------------------------------------------ frame
def render_frame(fi):
    t = fi / FPS
    si, shot = shot_at(t)
    fx = shot.get("fx", [])
    img, name = source_image(shot, t)
    if img is None:
        a = np.zeros((OH, OW, 3), np.float32)
    else:
        fr = camera(img, shot, t)
        if "peephole" in fx:
            iris = 1.0
            if "iris_in" in fx: iris = ease_io((t - shot["t"][0]) / 0.35)
            a = peephole(fr, iris)
        else:
            a = np.asarray(fr, np.float32)
        gain = 1.0
        rg = np.random.default_rng(fi * 7 + 1)
        if "tube" in fx and rg.random() < 0.06: gain *= rg.uniform(0.62, 0.85)
        if "leakflicker" in fx: gain *= 1 + 0.03 * math.sin(t * 37) * math.sin(t * 7)
        if "redglow" in fx:
            p = 0.5 + 0.5 * math.sin(t * 9)
            a = a * np.array([1.0 + 0.25 * p, 0.85, 0.85], np.float32)
        if "glitch" in fx and (t - shot["t"][0]) < 0.6 and rg.random() < 0.55:
            sh = int(rg.integers(8, 26)); a = a.copy(); a[..., 0] = np.roll(a[..., 0], sh, axis=1); a[..., 2] = np.roll(a[..., 2], -sh, axis=1)
            y0 = int(rg.integers(0, OH - 200)); hh = int(rg.integers(30, 160)); a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], int(rg.integers(-60, 60)), axis=1)
        if "memory" in fx:  # EP02: soft, hazy flashback insert
            bl = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), np.float32)
            a = a * 0.55 + bl * 0.45 + 10
        if "photo" in fx: gain *= 1.12  # EP02: flash-lit phone photo
        if "iris_out" in fx:
            k = (t - (shot["t"][1] - 0.3)) / 0.3
            if k > 0: gain *= 1 - ease_io(k)
        if "shake_hits" in fx:
            for h in TL.HITS:
                if shot["t"][0] <= h <= t: gain *= 1 + 0.18 * math.exp(-(t - h) * 18)
        a = finish(a, t, fi, gain, desat=0.25 if "freeze" in fx else 0.0)
    # global flashes
    for ft, col in TL.FLASHES:
        if ft <= t < ft + 0.2:
            k = 1 - (t - ft) / 0.2
            c = np.array([255, 255, 255] if col == "white" else [255, 30, 30], np.float32)
            a = a * (1 - 0.6 * k) + c * 0.6 * k
    # hard cut to black at the end of the lock shot
    frame = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    if "dust" in fx: dust(frame, t, shot)
    if "countdown" in fx or (getattr(TL, "COUNTDOWN", None) and len(TL.COUNTDOWN) == 3 and TL.COUNTDOWN[0] <= t < TL.CUT_TO_BLACK and "phone" not in shot): draw_countdown(frame, t)
    if "endcard" in fx: draw_endcard(frame, t)
    draw_subs(frame, t, shot)
    return frame.convert("RGB").tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs=2, type=float)
    ap.add_argument("--stills", type=str)
    ap.add_argument("--out", type=str, default=os.path.join(ROOT, "renders", "EP02_PRICE_OF_CHOICE_FINAL.mp4"))
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "renders"), exist_ok=True)
    if args.stills:
        for s in args.stills.split(","):
            t = float(s); Image.frombytes("RGB", (OW, OH), render_frame(int(round(t * FPS)))).save(os.path.join(ROOT, "renders", f"still_{t:06.2f}.png"))
        return
    a, b = (args.preview if args.preview else (0, TL.END))
    frames = range(int(round(a * FPS)), int(round(b * FPS)))
    mix = os.path.join(ROOT, "audio", "mix_ep02.wav")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
           "-ss", f"{a}", "-t", f"{b - a}", "-i", mix,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "14M", "-bufsize", "28M", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", args.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(args.workers) as pool:
        for i, buf in enumerate(pool.imap(render_frame, frames, chunksize=6)):
            p.stdin.write(buf)
            if i % 150 == 0: print(f"  frame {i}/{len(frames)}", flush=True)
    p.stdin.close(); p.wait()
    print("wrote", args.out)


if __name__ == "__main__":
    main()
