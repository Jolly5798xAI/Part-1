"""Phone screen UI, drawn programmatically (never trust an image generator with Russian text).
draw_screen(state_elements, t) -> RGBA 720x1540 image of the phone screen at time t."""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(os.path.dirname(ROOT), "EP02", "effects", "fonts")  # shared series fonts (not copied)
W, H = 720, 1540
_F = {}
CLOCK = "02:47"        # status-bar / message time (EP01 default); 06_render_video sets it from the timeline
LOCK_CLOCK = "02:48"   # big clock on the lock screen


def F(name, size):
    k = (name, size)
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(FD, name), size)
    return _F[k]


def wrap(draw, text, font, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split(" "):
            cand = (line + " " + w).strip()
            if draw.textlength(cand, font=font) <= maxw: line = cand
            else:
                if line: out.append(line)
                line = w
        out.append(line)
    return out


def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def visible(elements, t):
    return [(t0, el) for t0, el in elements if t >= t0]


def signature(elements, t):
    """Hashable description of what is on screen at t (for caching)."""
    sig = []
    for t0, (kind, data) in visible(elements, t):
        age = t - t0
        if kind == "typing": sig.append(("typing", int(t * 4) % 3))
        elif kind == "timer":
            st, secs = data; sig.append(("timer", min(secs, max(0, secs - int(t - st)))))
        elif kind in ("push", "bubble", "bubble_red", "lock_text", "highlight", "photos", "photo_full") and age < 0.3: sig.append((kind, str(data), round(age, 2)))
        elif kind == "glitch": sig.append(("glitch", int(t * 15)))                       # EP04: changes every 2 frames
        elif kind == "voice":
            tp, du = data; sig.append(("voice", round(age, 1) if age < 0.3 else 1, int(max(0, min(1, (t - tp) / du)) * 40)))
        elif kind == "photo_msg" and age < 0.4: sig.append((kind, data, round(age, 2)))
        elif kind == "bank_app": sig.append((kind, str(data), round(min(max(t - data[0], -0.1), 0.6), 2)))
        elif kind == "select" and age < 0.6: sig.append((kind, data, round(age, 2)))
        else: sig.append((kind, str(data)))
    # typing indicator disappears once the next bubble arrives
    return tuple(sig)


ILL = os.path.join(ROOT, "scenes")
_IMG = {}


def photo(name, size):
    k = (name, size)
    if k not in _IMG:
        path = os.path.join(ILL, name + ".png")
        if not os.path.exists(path): path = os.path.join(os.path.dirname(ROOT), "EP04", "scenes", name + ".png")   # EP05: EP04 photo, read-only
        im = Image.open(path).convert("RGB")
        tw, th = size; sc = max(tw / im.width, th / im.height)
        im = im.resize((int(im.width * sc + 0.5), int(im.height * sc + 0.5)), Image.LANCZOS)
        x0, y0 = (im.width - tw) // 2, (im.height - th) // 2
        _IMG[k] = im.crop((x0, y0, x0 + tw, y0 + th))
    return _IMG[k]


def draw_photos(im, names, y, age, sel):
    """two photos side by side (the choice); sel = (index, age_of_tap) draws the tap ripple + red frame"""
    a = ease(age / 0.25); pw, ph = 300, 400; gap = 40; x0 = (W - 2 * pw - gap) // 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for i, name in enumerate(names):
        x = x0 + i * (pw + gap); yy = y + int((1 - a) * 40)
        layer.paste(photo(name, (pw, ph)).convert("RGBA"), (x, yy))
        ld.rounded_rectangle([x - 2, yy - 2, x + pw + 2, yy + ph + 2], 18, outline=(70, 78, 96, 255), width=4)
        if sel and sel[0] == i:
            k = ease(sel[1] / 0.25)
            ld.rounded_rectangle([x - 8, yy - 8, x + pw + 8, yy + ph + 8], 22, outline=(255, 70, 70, int(255 * k)), width=10)
            if sel[1] < 0.6:  # tap ripple
                r = 30 + 160 * sel[1]; cx, cy = x + pw // 2, yy + ph // 2
                ld.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, int(200 * (1 - sel[1] / 0.6))), width=8)
    layer.putalpha(Image.eval(layer.split()[3], lambda v: int(v * a)))
    im.alpha_composite(layer)
    return y + ph + 50


def draw_bank(im, d, data, t):
    """bank app: balance flips from `a` to `b` at t_change (data = (t_change, a, b, [(label, amount), ...]))"""
    t_change, a, b, ops = data
    d.rectangle([0, 0, W, H], fill=(244, 245, 248))
    d.rectangle([0, 0, W, 90], fill=(244, 245, 248))
    d.text((44, 26), "02:49", font=F("Rubik-Medium.ttf", 30), fill=(30, 32, 38))
    d.rounded_rectangle([40, 120, 120, 200], 22, fill=(32, 170, 90)); d.text((80, 160), "$", font=F("Rubik-Bold.ttf", 56), fill=(255, 255, 255), anchor="mm")
    d.text((145, 160), "БАНК", font=F("Rubik-Bold.ttf", 44), fill=(20, 22, 26), anchor="lm")
    d.rounded_rectangle([36, 240, W - 36, 560], 40, fill=(255, 255, 255))
    d.text((80, 300), "Баланс", font=F("Rubik-Medium.ttf", 36), fill=(110, 115, 125), anchor="lm")
    k = ease((t - t_change) / 0.35)
    val = a if t < t_change else b
    neg = val < 0
    txt = ("−" if neg else "") + f"{abs(val):,}".replace(",", "\u00a0") + ",00\u00a0$"
    col = (225, 40, 45) if neg else (20, 22, 26)
    shake = int(10 * (1 - k) * math.sin(t * 90)) if t >= t_change else 0
    d.text((80 + shake, 420), txt, font=F("Rubik-Bold.ttf", 100), fill=col, anchor="lm")
    if neg and k > 0: d.text((80, 515), "Недостаточно средств", font=F("Rubik-Medium.ttf", 30), fill=(225, 40, 45), anchor="lm")
    d.text((44, 640), "Операции", font=F("Rubik-Bold.ttf", 40), fill=(20, 22, 26), anchor="lm")
    y = 700
    for label, amount in ops:
        if amount < 0 and t < t_change: continue
        d.rounded_rectangle([36, y, W - 36, y + 130], 30, fill=(255, 255, 255))
        d.text((70, y + 45), label, font=F("Rubik-Medium.ttf", 34), fill=(30, 32, 38), anchor="lm")
        d.text((70, y + 92), "сегодня", font=F("Rubik-Medium.ttf", 26), fill=(140, 145, 155), anchor="lm")
        s_ = ("+" if amount > 0 else "−") + f"{abs(amount):,}".replace(",", "\u00a0") + "\u00a0$"
        d.text((W - 70, y + 65), s_, font=F("Rubik-Bold.ttf", 40), fill=(25, 150, 75) if amount > 0 else (225, 40, 45), anchor="rm")
        y += 150


def draw_photo_full(im, name, age):
    a = ease(age / 0.3)
    p = photo(name, (W, H)).convert("RGBA")
    p.putalpha(int(255 * a)); im.alpha_composite(p)


# ---------------------------------------------------------------- EP04 additions
def draw_crack(im, seed):
    """cracked glass: an impact point lower right, radial cracks with branches, a few shattered cells (seeded, so the
    same crack is drawn in every frame)"""
    import random
    r = random.Random(seed); layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    cx, cy = int(W * 0.68), int(H * 0.72)
    for i in range(14):
        a = i / 14 * 2 * math.pi + r.uniform(-0.2, 0.2); x, y = cx, cy; L = r.uniform(300, 1300)
        pts = [(x, y)]
        while math.hypot(x - cx, y - cy) < L:
            a += r.uniform(-0.35, 0.35); st = r.uniform(30, 90); x += math.cos(a) * st; y += math.sin(a) * st; pts.append((x, y))
            if r.random() < 0.18:  # branch
                bx, by, ba = x, y, a + r.choice((-1, 1)) * r.uniform(0.5, 1.1); bp = [(bx, by)]
                for _ in range(r.randint(2, 5)):
                    ba += r.uniform(-0.3, 0.3); bx += math.cos(ba) * 50; by += math.sin(ba) * 50; bp.append((bx, by))
                d.line(bp, fill=(10, 12, 16, 230), width=5); d.line(bp, fill=(225, 235, 245, 200), width=2)
        d.line(pts, fill=(10, 12, 16, 235), width=6); d.line(pts, fill=(235, 242, 250, 215), width=2)
    for k in range(5):  # rings round the impact
        rr = 40 + k * 38; d.arc([cx - rr, cy - rr, cx + rr, cy + rr], r.uniform(0, 360), r.uniform(0, 360) + r.uniform(60, 160), fill=(230, 238, 248, 170), width=2)
    d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(235, 240, 248, 120))
    for _ in range(9):  # dead pixel streaks / shattered cells
        x0 = r.randint(0, W - 40); y0 = r.randint(int(H * 0.5), H - 20)
        d.rectangle([x0, y0, x0 + r.randint(20, 120), y0 + r.randint(4, 14)], fill=(r.choice([255, 40]), r.choice([40, 255]), r.choice([255, 60]), 150))
    im.alpha_composite(layer)


def draw_glitch(im, t):
    import random
    r = random.Random(int(t * 15)); a = im.copy()
    for _ in range(10):
        y0 = r.randint(0, H - 80); h = r.randint(10, 90); dx = r.randint(-90, 90)
        band = a.crop((0, y0, W, y0 + h)); im.paste(band, (dx, y0))
    tint = Image.new("RGBA", (W, H), (r.randint(0, 80), 0, r.randint(0, 60), r.randint(20, 80))); im.alpha_composite(tint)


def draw_photo_msg(im, name, y, age):
    a = ease(age / 0.35); pw, ph = 560, 700
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    yy = y + int((1 - a) * 30)
    ld.rounded_rectangle([30, yy - 6, 36 + pw + 6, yy + ph + 6], 30, fill=(38, 44, 58, 255))
    p = photo(name, (pw, ph)).convert("RGBA"); m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw, ph], 26, fill=255)
    layer.paste(p, (36, yy), m)
    ld.text((36 + pw - 16, yy + ph - 14), CLOCK, font=F("Rubik-Medium.ttf", 24), fill=(235, 235, 240, 255), anchor="rb")
    layer.putalpha(Image.eval(layer.split()[3], lambda v: int(v * a)))
    im.alpha_composite(layer)
    return y + ph + 36


def draw_voice(im, d, data, y, t, t0):
    """voice message bubble: play button, 40 bars, progress in red while the VO plays"""
    tp, du = data; a = ease((t - t0) / 0.25); prog = max(0.0, min(1.0, (t - tp) / du))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    yy = y + int((1 - a) * 30); bw, bh = 600, 120
    ld.rounded_rectangle([36, yy, 36 + bw, yy + bh], 40, fill=(38, 44, 58, int(255 * a)))
    ld.ellipse([56, yy + 22, 132, yy + 98], fill=(255, 80, 80, int(255 * a)))
    if prog > 0 and prog < 1: ld.rectangle([82, yy + 44, 92, yy + 76], fill=(255, 255, 255, 255)); ld.rectangle([98, yy + 44, 108, yy + 76], fill=(255, 255, 255, 255))
    else: ld.polygon([(84, yy + 40), (84, yy + 80), (116, yy + 60)], fill=(255, 255, 255, int(255 * a)))
    import random
    r = random.Random(204)
    for i in range(40):
        hgt = 10 + int(r.random() ** 0.7 * 60); x = 156 + i * 11
        col = (255, 90, 90) if i / 40 < prog else (150, 156, 175)
        ld.rectangle([x, yy + 60 - hgt // 2, x + 6, yy + 60 + hgt // 2], fill=col + (int(255 * a),))
    ld.text((36 + bw - 20, yy + bh - 12), "0:0" + str(int(3 * prog) if prog > 0 else 3), font=F("Rubik-Medium.ttf", 22), fill=(150, 156, 175, int(255 * a)), anchor="rb")
    im.alpha_composite(layer)
    return y + bh + 26


def draw_screen(elements, t):
    vis = visible(elements, t)
    kinds = [el[0] for _, el in vis]
    lock = "lock_glow" in kinds
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    if "off" in kinds:  # EP03: screen asleep — black glass with a faint sheen
        for y in range(H): d.line([(0, y), (W, y)], fill=(6, 7, 10, 255))
        d.polygon([(0, 0), (W * 0.55, 0), (0, H * 0.35)], fill=(18, 20, 26, 255))
        for _, (k, dd) in vis:
            if k == "crack": draw_crack(im, dd)                # EP04: a dead, cracked screen
        return im
    # background
    for y in range(H):
        k = y / H
        c = (int(70 + 60 * k), int(8 + 6 * k), int(14 + 8 * k)) if lock else (int(12 + 6 * k), int(15 + 8 * k), int(22 + 12 * k))
        d.line([(0, y), (W, y)], fill=c + (255,))
    # status bar
    d.text((44, 26), CLOCK, font=F("Rubik-Medium.ttf", 30), fill=(235, 235, 240))
    for i in range(4): d.rectangle([560 + i * 14, 50 - i * 6, 568 + i * 14, 56], fill=(235, 235, 240))
    d.rounded_rectangle([628, 30, 684, 56], 6, outline=(235, 235, 240), width=3); d.rectangle([634, 36, 652, 50], fill=(235, 235, 240))

    if lock:
        d.text((W // 2, 260), LOCK_CLOCK, font=F("Rubik-Medium.ttf", 150), fill=(255, 235, 235), anchor="mm")
        d.text((W // 2, 370), "пятница, 6 ноября", font=F("Rubik-Medium.ttf", 34), fill=(255, 200, 200), anchor="mm")
        last = [i for i, (_, (k, _)) in enumerate(vis) if k == "lock_text"]
        for i, (t0, (kind, data)) in enumerate(vis):
            if kind == "lock_text" and i == last[-1]:
                a = ease((t - t0) / 0.2)
                # warning card
                card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
                cd.rounded_rectangle([40, 560, W - 40, 1060], 46, fill=(20, 4, 6, int(235 * a)), outline=(255, 60, 60, int(255 * a)), width=5)
                cd.text((W // 2, 640), "Номер скрыт", font=F("Rubik-Medium.ttf", 34), fill=(255, 140, 140, int(255 * a)), anchor="mm")
                fs = 92
                while True:  # EP02: longer cards shrink to fit (EP01 cards keep 92 px)
                    lines = wrap(cd, data, F("Rubik-Bold.ttf", fs), W - 140)
                    fits = len(lines) * fs * 1.22 <= 330 and max(cd.textlength(l, font=F("Rubik-Bold.ttf", fs)) for l in lines) <= W - 120
                    if fits or fs <= 50: break
                    fs -= 4
                lh = int(fs * 1.22)
                y = (820 if fs == 92 else 860) - (len(lines) - 1) * lh // 2
                for ln in lines:
                    cd.text((W // 2, y), ln, font=F("Rubik-Bold.ttf", fs), fill=(255, 255, 255, int(255 * a)), anchor="mm"); y += lh
                glow = card.filter(ImageFilter.GaussianBlur(14))
                im.alpha_composite(glow); im.alpha_composite(card)
        return im

    for t0, (kind, data) in vis:
        if kind == "bank_app": draw_bank(im, d, data, t); return im
        if kind == "photo_full": draw_photo_full(im, data, t - t0); return im

    y = 100
    for t0, (kind, data) in vis:
        if kind == "header":
            d.text((40, y + 40), "‹", font=F("Rubik-Medium.ttf", 64), fill=(120, 170, 255), anchor="lm")
            d.ellipse([90, y, 170, y + 80], fill=(70, 76, 90)); d.text((130, y + 40), "?", font=F("Rubik-Bold.ttf", 46), fill=(220, 220, 230), anchor="mm")
            d.text((190, y + 22), data, font=F("Rubik-Medium.ttf", 40), fill=(245, 245, 250), anchor="lm")
            d.text((190, y + 62), "был(а) только что", font=F("Rubik-Medium.ttf", 26), fill=(140, 150, 170), anchor="lm")
            y += 110; d.line([(0, y), (W, y)], fill=(40, 46, 60), width=2); y += 30
    # chat items stacked
    hl = None
    for t0, (kind, data) in vis:
        if kind == "highlight": hl = (data, t - t0)
    typing_done = False
    sel = None
    for t0, (kind, data) in vis:
        if kind == "select": sel = (data, t - t0)
    items = [(t0, el) for t0, el in vis if el[0] in ("bubble", "bubble_small", "bubble_red", "typing", "timer", "photos", "photo_msg", "voice")]
    for idx, (t0, (kind, data)) in enumerate(items):
        if kind == "typing":
            later = any(k in ("bubble", "bubble_red") and tt > t0 for tt, (k, _) in items)
            if later: continue
            d.rounded_rectangle([36, y, 200, y + 86], 40, fill=(38, 44, 58))
            ph = int(t * 4) % 3
            for i in range(3):
                c = 230 if i == ph else 120
                d.ellipse([70 + i * 38, y + 32, 92 + i * 38, y + 54], fill=(c, c, c + 10))
            y += 110; continue
        if kind == "photos":
            y = draw_photos(im, data, y, t - t0, sel); continue
        if kind == "photo_msg":
            y = draw_photo_msg(im, data, y, t - t0); d = ImageDraw.Draw(im); continue
        if kind == "voice":
            y = draw_voice(im, d, data, y, t, t0); continue
        if kind == "timer":
            st, secs = data; rem = min(secs, max(0, secs - int(t - st)))
            d.text((W // 2, y + 40), "осталось", font=F("Rubik-Medium.ttf", 32), fill=(255, 120, 120), anchor="mm")
            d.text((W // 2, y + 140), f"{rem // 60:02d}:{rem % 60:02d}", font=F("Rubik-Bold.ttf", 150), fill=(255, 70, 70), anchor="mm")
            y += 240; continue
        small = kind == "bubble_small"
        font = F("Rubik-Medium.ttf", 32 if small else 42); lh = 42 if small else 56
        a = 1.0 if small else ease((t - t0) / 0.18)
        lines = wrap(d, data, font, 560)
        bw = max(d.textlength(l, font=font) for l in lines) + 64
        bh = len(lines) * lh + 60
        fill = (74, 16, 22) if kind == "bubble_red" else ((30, 35, 46) if small else (38, 44, 58))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        dy = int((1 - a) * 30)
        ld.rounded_rectangle([36, y + dy, 36 + bw, y + dy + bh], 34, fill=fill + (int(255 * a),),
                             outline=(255, 80, 80, int(255 * a)) if kind == "bubble_red" else None, width=3)
        ty = y + dy + 26
        addr_lines = set()
        if hl and hl[0] in data:
            addr_lines = set(wrap(d, hl[0], font, 560))
        for ln in lines:
            if ln in addr_lines:
                k = ease(hl[1] / 0.35)
                tw = ld.textlength(ln, font=font)
                ld.rectangle([64, ty + 2, 64 + tw * k, ty + lh - 6], fill=(255, 210, 60, 110))
                ld.rectangle([64, ty + lh - 8, 64 + tw * k, ty + lh - 3], fill=(255, 70, 70, 255))
            col = (255, 225, 225) if kind == "bubble_red" else ((180, 186, 200) if small else (245, 246, 250))
            ld.text((68, ty), ln, font=font, fill=col + (int(255 * a),)); ty += lh
        ld.text((36 + bw - 20, y + dy + bh - 12), CLOCK, font=F("Rubik-Medium.ttf", 22), fill=(150, 156, 175, int(255 * a)), anchor="rb")
        im.alpha_composite(layer)
        y += bh + 26
    for t0, (kind, data) in vis:  # EP04: cracked glass and glitches sit on top of the whole screen
        if kind == "crack": draw_crack(im, data)
    if any(k == "glitch" for _, (k, _) in vis): draw_glitch(im, t)
    # push notification on top
    for t0, (kind, data) in vis:
        if kind == "push":
            a = ease((t - t0) / 0.25); oy = int(-200 * (1 - a))
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            ld.rounded_rectangle([24, 80 + oy, W - 24, 280 + oy], 36, fill=(242, 244, 247, 255))
            ld.rounded_rectangle([50, 112 + oy, 130, 192 + oy], 22, fill=(32, 170, 90))
            ld.text((90, 152 + oy), "$", font=F("Rubik-Bold.ttf", 56), fill=(255, 255, 255), anchor="mm")
            ld.text((150, 128 + oy), data[0] + "  ·  сейчас", font=F("Rubik-Medium.ttf", 28), fill=(110, 115, 125), anchor="lm")
            title, _, amount = data[1].partition(": ")
            ld.text((150, 180 + oy), title + ":", font=F("Rubik-Medium.ttf", 40), fill=(20, 22, 26), anchor="lm")
            ld.text((150, 236 + oy), amount, font=F("Rubik-Bold.ttf", 54), fill=(25, 150, 75), anchor="lm")
            im.alpha_composite(layer)
    return im


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import timeline_ep04 as TL
    CLOCK = LOCK_CLOCK = getattr(TL, "PHONE_CLOCK", CLOCK)
    out = os.path.join(ROOT, "renders", "ui_preview"); os.makedirs(out, exist_ok=True)
    for name, els in TL.PHONE.items():  # preview every phone state just after its last element appears
        draw_screen(els, max(t for t, _ in els) + 0.6).save(os.path.join(out, f"{name}.png"))
    print("wrote", len(TL.PHONE), "previews to", out)
