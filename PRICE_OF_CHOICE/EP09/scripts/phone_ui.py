"""Phone screen UI, drawn programmatically (never trust an image generator with Russian text).
draw_screen(state_elements, t) -> RGBA 720x1540 image of the phone screen at time t."""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

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
        elif kind == "video":                                                             # EP06: the recording
            sig.append((kind, VIDEO_LIP(t), int(t * 2) % 2, int(t - data["start"]), int(t * 15) if age < 0.4 else -1,
                        round(min(max(t - data["cap_t"], -0.1), 0.3), 2), int(t * 4)))
        elif kind == "count": sig.append((kind,) + count_state(data, t))
        elif kind in ("count5", "count5full"): sig.append((kind, count5_rem(data, t), round(min(count5_age(data, t), 0.3), 1)))
        elif kind in ("attempt", "attempt_prev"): sig.append((kind, round(min(age, 1.0), 2) if age < 1.0 else 1, int(t * 3) % 2))
        elif kind == "lock8":                                                             # EP08: the date changes
            sig.append((kind, round(min(max(t - data["t_changed"], -0.1), 0.4), 2), round(min(max(t - data["t_tomorrow"], -0.1), 0.4), 2),
                        int(t * 15) if data["t_on"] + 0.6 <= t < data["t_flip"] + 0.25 else (0 if t < data["t_flip"] else 1), round(min(max(t - data["t_on"], -0.1), 0.3), 2)))
        elif kind == "task9":                                                             # EP09: ALEX_49's task, then the crack
            sig.append((kind, round(min(max(t - data["t_on"], -0.1), 0.3), 2), round(min(max(t - data["t1"], -0.1), 0.3), 2), round(min(max(t - data["t2"], -0.1), 0.3), 2),
                        int(t * 15) if t >= data["t_crack"] else -1))
        elif kind == "cop9":                                                              # EP09: the officer's phone
            sig.append((kind, round(min(max(t - data["t_on"], -0.1), 0.3), 2), round(min(max(t - data["t1"], -0.1), 0.3), 2), round(min(max(t - data["t2"], -0.1), 0.3), 2),
                        round(min(max(t - data["t3"], -0.1), 0.5), 2), int(t * 4) % 2 if t >= data["t3"] else 0))
        elif kind == "choice": sig.append((kind, round(min(age, 0.4), 2), round(min(max(t - data["t_right"], -0.1), 0.4), 2), int(t * 4) % 2))
        else: sig.append((kind, str(data)))
    # typing indicator disappears once the next bubble arrives
    return tuple(sig)


ILL = os.path.join(ROOT, "scenes")
_IMG = {}


def photo(name, size):
    k = (name, size)
    if k not in _IMG:
        path = os.path.join(ILL, name + ".png")
        for ep in ("EP06", "EP04"):   # EP07: EP06 portrait / EP04 photo, read-only
            if not os.path.exists(path): path = os.path.join(os.path.dirname(ROOT), ep, "scenes", name + ".png")
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
        if kind == "video": draw_video(im, data, t, t0); return im          # EP06
        if kind == "count": draw_count(im, data, t); return im              # EP06
        if kind == "lock8": draw_lock8(im, data, t); return im              # EP08
        if kind == "task9": draw_task9(im, data, t); return im              # EP09
        if kind == "cop9": draw_cop9(im, data, t); return im                # EP09
    for t0, (kind, data) in vis:
        if kind == "count5full": draw_count5full(im, data, t); return im    # EP07
        if kind == "photo_full": draw_photo_full(im, data, t - t0); return im

    y = 100
    for t0, (kind, data) in vis:
        if kind == "header":
            d.text((40, y + 40), "‹", font=F("Rubik-Medium.ttf", 64), fill=(120, 170, 255), anchor="lm")
            d.ellipse([90, y, 170, y + 80], fill=(70, 76, 90)); d.text((130, y + 40), "?", font=F("Rubik-Bold.ttf", 46), fill=(220, 220, 230), anchor="mm")
            d.text((190, y + 22), data, font=F("Rubik-Medium.ttf", 40), fill=(245, 245, 250), anchor="lm")
            d.text((190, y + 62), "был(а) только что", font=F("Rubik-Medium.ttf", 26), fill=(140, 150, 170), anchor="lm")
            y += 110; d.line([(0, y), (W, y)], fill=(40, 46, 60), width=2); y += 30
    if any(k in ("attempt", "attempt_prev") for _, (k, _) in vis):          # EP06: the attempt counter replaces the chat
        for t0, (kind, data) in vis:
            if kind == "attempt": draw_attempt(im, data, t - t0, t)
            if kind == "attempt_prev": draw_attempt_prev(im, data, t - t0, t)
        return im
    # chat items stacked
    hl = None
    for t0, (kind, data) in vis:
        if kind == "highlight": hl = (data, t - t0)
    typing_done = False
    sel = None
    for t0, (kind, data) in vis:
        if kind == "select": sel = (data, t - t0)
    items = [(t0, el) for t0, el in vis if el[0] in ("bubble", "bubble_small", "bubble_red", "typing", "timer", "photos", "photo_msg", "voice", "choice")]
    for idx, (t0, (kind, data)) in enumerate(items):
        if kind == "typing":
            later = any(k in ("bubble", "bubble_red", "choice") and tt > t0 for tt, (k, _) in items)
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
        if kind == "choice":
            y = draw_choice(im, data, y, t, t0); d = ImageDraw.Draw(im); continue
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
    for t0, (kind, data) in vis:  # EP07: the last five seconds under the choice
        if kind == "count5": draw_count5(im, data, t)
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



# ---------------------------------------------------------------- EP06 additions «ПЕРВАЯ ПОПЫТКА»
VIDEO_LIP = lambda t: "neutral"     # 06_render_video sets this: Alex's mouth shape on the recording, from the VO envelope


def draw_video(im, data, t, t0):
    """a recording playing full screen: Alex at the same table in room 204 (lip-synced still), recorded look,
    REC dot + timecode, player bar, and his line as a caption once he says it"""
    p = photo(f"{data['src']}_{VIDEO_LIP(t)}", (W, H)).copy()
    p = ImageEnhance.Contrast(ImageEnhance.Color(p).enhance(0.55), ).enhance(1.12)
    p = Image.blend(p, Image.new("RGB", p.size, (40, 60, 70)), 0.12)
    import random
    r = random.Random(int(t * 15))
    if t - t0 < 0.4 or r.random() < 0.08:                                    # tape wobble: a few displaced bands
        for _ in range(4 if t - t0 < 0.4 else 1):
            y0 = r.randint(0, H - 60); h = r.randint(8, 50); band = p.crop((0, y0, W, y0 + h)); p.paste(band, (r.randint(-40, 40), y0))
    im.paste(p, (0, 0))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for y in range(0, H, 4): ld.line([(0, y), (W, y)], fill=(0, 0, 0, 46))  # scanlines
    if int(t * 2) % 2 == 0: ld.ellipse([40, 112, 72, 144], fill=(255, 40, 40, 255))
    ld.text((86, 128), "REC", font=F("Rubik-Bold.ttf", 36), fill=(255, 255, 255, 235), anchor="lm")
    sec = max(0, int(t - data["start"])) + 11 * 60 + 38
    ld.text((W - 40, 128), f"00:{sec // 60:02d}:{sec % 60:02d}", font=F("Rubik-Medium.ttf", 32), fill=(255, 255, 255, 220), anchor="rm")
    for (x, y, dx, dy) in [(28, 96, 1, 1), (W - 28, 96, -1, 1), (28, H - 120, 1, -1), (W - 28, H - 120, -1, -1)]:   # camera frame corners
        ld.line([(x, y), (x + 50 * dx, y)], fill=(255, 255, 255, 170), width=4); ld.line([(x, y), (x, y + 50 * dy)], fill=(255, 255, 255, 170), width=4)
    prog = min(1.0, max(0.0, (t - data["start"]) / 9.0))
    ld.rectangle([40, H - 70, W - 40, H - 62], fill=(255, 255, 255, 90)); ld.rectangle([40, H - 70, 40 + (W - 80) * prog, H - 62], fill=(255, 50, 50, 255))
    if t >= data["cap_t"]:
        a = ease((t - data["cap_t"]) / 0.25); f = F("Rubik-Bold.ttf", 46)
        lines = wrap(ld, data["cap"], f, W - 120); lh = 58; bh = len(lines) * lh + 44; y0 = H - 260 - bh
        ld.rounded_rectangle([34, y0, W - 34, y0 + bh], 24, fill=(0, 0, 0, int(175 * a)))
        y = y0 + 22
        for ln in lines: ld.text((W // 2, y + lh // 2), ln, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm"); y += lh
    im.alpha_composite(lay)


def count_state(data, t):
    st, secs, freeze = data; tt = min(t, freeze)
    rem = secs if tt < st else max(0, secs - int(tt - st))
    frozen = t >= freeze
    return rem, (int(t * 4) % 2 if frozen else -1), (round(min((tt - st) % 1.0, 0.3), 1) if st <= tt and not frozen else -1)


def draw_count(im, data, t):
    """the countdown full screen: dark red, «ОСТАЛОСЬ», huge 00:SS, ten bars; frozen at the last second it blinks"""
    rem, blink, ph = count_state(data, t)
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(60 + 50 * k), int(4 + 4 * k), int(8 + 6 * k), 255))
    d.text((44, 26), CLOCK, font=F("Rubik-Medium.ttf", 30), fill=(255, 210, 210))
    d.text((W // 2, 470), "ОСТАЛОСЬ", font=F("Rubik-Medium.ttf", 46), fill=(255, 150, 150), anchor="mm")
    flash = ph >= 0 and ph < 0.15
    col = (255, 255, 255) if flash or blink == 1 else (255, 64, 56)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.text((W // 2, 720), f"00:{rem:02d}", font=F("Rubik-Bold.ttf", 214), fill=col + (255,), anchor="mm")
    for i in range(10):
        x = 70 + i * 60; on = i < rem
        cd.rounded_rectangle([x, 930, x + 40, 1010], 8, fill=(255, 60, 52, 255) if on else (70, 20, 22, 255))
    glow = card.filter(ImageFilter.GaussianBlur(16)); im.alpha_composite(glow); im.alpha_composite(card)


def draw_attempt(im, text, age, t):
    """the attempt counter: «ПОПЫТКА», a huge 47, the line «Попытка номер сорок семь.»"""
    import timeline_ep08 as _TL
    a = ease(age / 0.3); sc = 1.25 - 0.25 * a
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.text((W // 2, 300), "П О П Ы Т К А   №", font=F("Rubik-Medium.ttf", 40), fill=(255, 150, 150, int(255 * a)), anchor="mm")
    big = Image.new("RGBA", (W, 420), (0, 0, 0, 0)); bd = ImageDraw.Draw(big)
    bd.text((W // 2, 210), f"{_TL.ATTEMPT_N}", font=F("Rubik-Bold.ttf", 330), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    if sc != 1: big = big.resize((int(W * sc), int(420 * sc)), Image.BILINEAR)
    card.alpha_composite(big, ((W - big.width) // 2, 520 - big.height // 2))
    f = F("Rubik-Bold.ttf", 40); y = 770
    for ln in wrap(cd, text, f, W - 100):
        cd.text((W // 2, y), ln, font=f, fill=(255, 225, 225, int(255 * a)), anchor="mm"); y += 56
    glow = card.filter(ImageFilter.GaussianBlur(14)); im.alpha_composite(glow); im.alpha_composite(card)


def draw_attempt_prev(im, text, age, t):
    """46 dark-red cells crossed out one after another (the earlier attempts), the 47th lit and blinking, then the line"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    cs, gap, cols = 62, 12, 8; x0 = (W - (cols * cs + (cols - 1) * gap)) // 2; y0 = 880
    for i in range(48):
        x = x0 + (i % cols) * (cs + gap); y = y0 + (i // cols) * (cs + gap)
        if i < 46:
            k = ease((age - i * 0.018) / 0.12)
            if k <= 0: ld.rounded_rectangle([x, y, x + cs, y + cs], 10, outline=(90, 40, 44, 255), width=3); continue
            ld.rounded_rectangle([x, y, x + cs, y + cs], 10, fill=(90, 14, 18, int(255 * k)), outline=(255, 70, 64, int(255 * k)), width=3)
            ld.line([(x + 16, y + 16), (x + cs - 16, y + cs - 16)], fill=(255, 80, 70, int(255 * k)), width=6)
            ld.line([(x + cs - 16, y + 16), (x + 16, y + cs - 16)], fill=(255, 80, 70, int(255 * k)), width=6)
        elif i == 46:
            on = age > 46 * 0.018 and int(t * 3) % 2 == 0
            ld.rounded_rectangle([x, y, x + cs, y + cs], 10, fill=(255, 255, 255, 60 if on else 20), outline=(255, 255, 255, 255 if on else 140), width=4)
            ld.text((x + cs // 2, y + cs // 2), "47", font=F("Rubik-Bold.ttf", 28), fill=(255, 255, 255, 255), anchor="mm")
        else:
            ld.rounded_rectangle([x, y, x + cs, y + cs], 10, outline=(60, 30, 34, 255), width=2)
    a = ease((age - 0.5) / 0.3); f = F("Rubik-Bold.ttf", 42); y = 1350
    for ln in wrap(ld, text, f, W - 90):
        ld.text((W // 2, y), ln, font=f, fill=(255, 80, 72, int(255 * a)), anchor="mm"); y += 54
    im.alpha_composite(lay)


def draw_choice(im, data, y, t, t0):
    """the final choice: two cards — her photo «СЕСТРУ», his photo «СЕБЯ» — and the line «Сестру или себя.»"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    cw, ch, top = 292, 440, y + 6
    pulse = int(t * 4) % 2 == 0 and t >= data["t_right"]
    for side, (img, label) in ((0, data["left"]), (1, data["right"])):
        st = t0 if side == 0 else data["t_right"]
        if t < st: continue
        a = ease((t - st) / 0.3); x = 34 if side == 0 else W - 34 - cw; yy = top + int((1 - a) * 40)
        ld.rounded_rectangle([x, yy, x + cw, yy + ch], 30, fill=(34, 6, 9, int(245 * a)), outline=(255, 255, 255, int(255 * a)) if pulse else (255, 70, 64, int(255 * a)), width=5)
        ph = photo(img, (cw - 36, 300)).convert("RGBA"); m = Image.new("L", ph.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, ph.width, ph.height], 20, fill=int(255 * a))
        lay.paste(ph, (x + 18, yy + 18), m)
        ld.text((x + cw // 2, yy + ch - 58), label, font=F("Rubik-Bold.ttf", 54), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    if t >= data["t_right"]:
        a = ease((t - data["t_right"]) / 0.25)
        ld.text((W // 2, top + ch // 2), "или", font=F("Rubik-Medium.ttf", 34), fill=(255, 190, 190, int(255 * a)), anchor="mm")
    txt = data["text"] if t >= data["t_right"] else data["text"].split(" ")[0] + "…"
    ld.text((W // 2, top + ch + 70), txt, font=F("Rubik-Bold.ttf", 56), fill=(255, 90, 80, 255), anchor="mm")
    glow = lay.filter(ImageFilter.GaussianBlur(12)); im.alpha_composite(glow); im.alpha_composite(lay)
    return top + ch + 130


# ---------------------------------------------------------------- EP07 additions «ТОТ, КОГО СТЁРЛИ»
def count5_rem(data, t):
    rem = data[0][1]
    for tt, n in data:
        if t >= tt: rem = n
    return rem


def count5_age(data, t):
    a = 99.0
    for tt, n in data:
        if t >= tt: a = t - tt
    return a


def draw_count5(im, data, t):
    """the last five seconds under the choice: «ОСТАЛОСЬ» and a big red 00:0N that flashes white on every change"""
    rem, age = count5_rem(data, t), count5_age(data, t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([60, 1010, W - 60, 1380], 40, fill=(30, 3, 6, 235), outline=(255, 70, 64, 255), width=5)
    ld.text((W // 2, 1075), "ОСТАЛОСЬ", font=F("Rubik-Medium.ttf", 40), fill=(255, 150, 150, 255), anchor="mm")
    col = (255, 255, 255) if age < 0.15 else (255, 64, 56)
    sc = 1.0 + 0.25 * max(0.0, 1 - age / 0.2)
    ld.text((W // 2, 1235), f"00:{rem:02d}", font=F("Rubik-Bold.ttf", int(170 * sc)), fill=col + (255,), anchor="mm")
    glow = lay.filter(ImageFilter.GaussianBlur(14)); im.alpha_composite(glow); im.alpha_composite(lay)


def draw_count5full(im, data, t):
    """every phone on the table: the same five seconds, full screen (EP06's countdown look)"""
    rem, age = count5_rem(data, t), count5_age(data, t)
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(60 + 50 * k), int(4 + 4 * k), int(8 + 6 * k), 255))
    d.text((W // 2, 470), "ОСТАЛОСЬ", font=F("Rubik-Medium.ttf", 46), fill=(255, 150, 150), anchor="mm")
    col = (255, 255, 255) if age < 0.15 else (255, 64, 56)
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.text((W // 2, 720), f"00:{rem:02d}", font=F("Rubik-Bold.ttf", 214), fill=col + (255,), anchor="mm")
    for i in range(5):
        x = 100 + i * 110; cd.rounded_rectangle([x, 930, x + 80, 1010], 10, fill=(255, 60, 52, 255) if i < rem else (70, 20, 22, 255))
    glow = card.filter(ImageFilter.GaussianBlur(16)); im.alpha_composite(glow); im.alpha_composite(card)


# ---- the monitors behind the mirror (16:10 screens). Everything readable sits in the middle 50 % of the width,
# because the vertical frame only sees the centre of the big monitor.
MW, MH = 1600, 980


def _mon_bg(red):
    im = Image.new("RGBA", (MW, MH), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    for y in range(0, MH, 2):
        k = y / MH
        c = (int(70 + 40 * k), int(6 + 4 * k), int(10 + 6 * k)) if red else (int(6 + 6 * k), int(16 + 10 * k), int(24 + 14 * k))
        d.line([(0, y), (MW, y)], fill=c + (255,))
    return im, d


def _scan(im, alpha=40):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for y in range(0, im.height, 6): ld.line([(0, y), (im.width, y)], fill=(0, 0, 0, alpha))
    im.alpha_composite(lay)


def _typed(text, t, t0, cps=26):
    n = max(0, int((t - t0) * cps)); return text[:n]


def draw_monitor7(state, t, idx=0):
    """state 'wall' (one of the small monitors), 'msg' (the deletion message), 'addr' (the address + tomorrow)"""
    import timeline_ep09 as TL
    if state == "wall":
        red = t >= TL.T_MON_RED
        im, d = _mon_bg(red)
        if not red:
            import random; r = random.Random(idx * 31 + int(t * 8))
            for i in range(500): v = r.randint(0, 110); d.rectangle([r.randrange(0, MW, 8), r.randrange(0, MH, 8)] * 1 + [0, 0], fill=(v // 2, v, v))
        else:
            blink = int((t - TL.T_MON_RED) * 3) % 2 == 0
            cx, cy = MW // 2, MH // 2 - 60
            d.polygon([(cx, cy - 230), (cx + 260, cy + 200), (cx - 260, cy + 200)], outline=(255, 90, 80, 255) if blink else (255, 220, 220, 255), width=24)
            d.text((cx, cy + 40), "!", font=F("Rubik-Bold.ttf", 260), fill=(255, 90, 80, 255), anchor="mm")
            d.text((cx, cy + 330), f"№{TL.NUMBER}", font=F("Rubik-Bold.ttf", 150), fill=(255, 235, 235, 255), anchor="mm")
        _scan(im); return im
    if state == "msg":
        im, d = _mon_bg(True)
        cx = MW // 2
        d.text((cx, 210), f"№ {TL.NUMBER}", font=F("Rubik-Bold.ttf", 120), fill=(255, 225, 225, 255), anchor="mm")
        f = F("Rubik-Bold.ttf", 82); y = 380
        txt = _typed(TL.MSG_UNSTABLE, t, TL.T_MSG1, 18)
        for ln in wrap(d, txt, f, 760) if txt else []:
            d.text((cx, y), ln, font=f, fill=(255, 255, 255, 255), anchor="mm"); y += 100
        if t >= TL.T_MSG2:
            k = min(1.0, (t - TL.T_MSG2) / 0.25); on = int(t * 3) % 2 == 0
            d.rounded_rectangle([cx - 390, 640, cx + 390, 760], 26, fill=(255, 60, 52, int(255 * k)) if on else (150, 20, 20, int(255 * k)))
            d.text((cx, 700), TL.MSG_DELETE, font=F("Rubik-Bold.ttf", 66), fill=(255, 255, 255, int(255 * k)), anchor="mm")
            p = min(1.0, max(0.0, (t - TL.T_MSG2 - 0.4) / 5.0))
            d.rectangle([cx - 390, 800, cx + 390, 830], outline=(255, 120, 110, 255), width=4); d.rectangle([cx - 386, 804, cx - 386 + int(772 * p), 826], fill=(255, 235, 235, 255))
            d.text((cx, 880), f"{int(p * 100)} %", font=F("Rubik-Medium.ttf", 48), fill=(255, 190, 190, 255), anchor="mm")
        _scan(im); return im
    # addr
    im, d = _mon_bg(False)
    cx = MW // 2; cyan = (140, 230, 255, 255)
    if t < TL.T_STREET:                                     # the screen wakes up: a blinking cursor, nothing to read yet
        if int(t * 2.5) % 2 == 0: d.rectangle([cx - 30, MH // 2 - 60, cx + 30, MH // 2 + 60], fill=cyan)
        _scan(im); return im
    d.text((cx, 170), _typed(TL.ADDR_STREET, t, TL.T_STREET, 14), font=F("Rubik-Bold.ttf", 120), fill=(255, 255, 255, 255), anchor="mm")
    if t >= TL.T_FLAT: d.text((cx, 320), _typed(TL.ADDR_FLAT, t, TL.T_FLAT, 16), font=F("Rubik-Bold.ttf", 104), fill=(255, 255, 255, 255), anchor="mm")
    if t >= TL.T_DATE:
        k = min(1.0, (t - TL.T_DATE) / 0.25)
        d.line([(cx - 380, 440), (cx + 380, 440)], fill=(90, 150, 180, int(255 * k)), width=4)
        d.text((cx, 530), TL.DATE_TEXT, font=F("Rubik-Medium.ttf", 76), fill=(170, 220, 240, int(255 * k)), anchor="mm")
    if t >= TL.T_TOMORROW:
        k = min(1.0, (t - TL.T_TOMORROW) / 0.12); sc = 1.35 - 0.35 * k
        stamp = Image.new("RGBA", (800, 220), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
        sd.rounded_rectangle([10, 10, 790, 210], 30, outline=(255, 60, 52, 255), width=14)
        sd.text((400, 112), TL.DATE_WORD, font=F("Rubik-Bold.ttf", 150), fill=(255, 60, 52, 255), anchor="mm")
        stamp = stamp.rotate(-4, expand=True, resample=Image.BICUBIC)
        stamp = stamp.resize((int(stamp.width * sc), int(stamp.height * sc)), Image.BILINEAR)
        im.alpha_composite(stamp, (cx - stamp.width // 2, 760 - stamp.height // 2))
    _scan(im); return im



# ---------------------------------------------------------------- EP08 additions «ЗАВТРАШНИЙ ДЕНЬ»
def draw_lock8(im, data, t):
    """the lock screen after he comes through: 02:54, the date glitching from «пятница, 6 ноября» and flipping to «суббота, 7 ноября»,
    then two alert cards: «Дата изменена», «Завтра наступило» (EP01's lock-screen card style, cold screen instead of red)"""
    import random
    d = ImageDraw.Draw(im)
    for y in range(90, H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(10 + 16 * k), int(14 + 20 * k), int(28 + 34 * k), 255))
    on = ease((t - data["t_on"]) / 0.3)
    d.text((W // 2, 300), data["clock"], font=F("Rubik-Medium.ttf", 170), fill=(235, 240, 255, int(255 * on)), anchor="mm")
    flipped = t >= data["t_flip"]
    if not flipped and t >= data["t_on"] + 0.6:                          # the old date breaks up
        r = random.Random(int(t * 15)); txt = "".join(ch if (ch == " " or r.random() < 0.55) else r.choice("АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ0123456789") for ch in data["old"])
        dx = r.randint(-14, 14)
        d.text((W // 2 + dx, 425), txt, font=F("Rubik-Medium.ttf", 40), fill=(255, 120, 110, 255), anchor="mm")
    else:
        txt = data["new"] if flipped else data["old"]
        age = t - data["t_flip"]
        col = (255, 225, 120) if flipped and age < 0.8 else (200, 215, 255)
        d.text((W // 2, 425), txt, font=F("Rubik-Medium.ttf", 40), fill=col + (int(255 * on),), anchor="mm")
        if flipped and age < 0.25: d.rectangle([90, 400, W - 90, 450], outline=(255, 225, 120, int(255 * (1 - age / 0.25))), width=3)
    def card(y0, h, text, t0, big):
        a = ease((t - t0) / 0.2)
        if a <= 0: return
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(c); dy = int((1 - a) * 40)
        cd.rounded_rectangle([40, y0 + dy, W - 40, y0 + h + dy], 42, fill=(20, 4, 6, int(235 * a)), outline=(255, 60, 60, int(255 * a)), width=5)
        cd.text((W // 2, y0 + 58 + dy), "Номер скрыт", font=F("Rubik-Medium.ttf", 32), fill=(255, 140, 140, int(255 * a)), anchor="mm")
        fs = 74 if big else 62
        while cd.textlength(text, font=F("Rubik-Bold.ttf", fs)) > W - 140: fs -= 4
        cd.text((W // 2, y0 + h // 2 + 26 + dy), text, font=F("Rubik-Bold.ttf", fs), fill=(255, 255, 255, int(255 * a)), anchor="mm")
        glow = c.filter(ImageFilter.GaussianBlur(14)); im.alpha_composite(glow); im.alpha_composite(c)
    card(600, 250, data["changed"], data["t_changed"], False)
    card(900, 290, data["tomorrow"], data["t_tomorrow"], True)


def _mon_crack(im, seed=34):
    """the crack in the centre monitor drawn into the screen UI (same place as the 3D crack: the fist's hit at u .58, v .43)"""
    import random
    r = random.Random(seed); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = int(im.width * 0.582), int(im.height * 0.433)
    for i in range(12):
        a = i / 12 * 2 * math.pi + r.uniform(-0.2, 0.2); x, y = cx, cy; pts = [(x, y)]; L = r.uniform(250, 700)
        while math.hypot(x - cx, y - cy) < L:
            a += r.uniform(-0.25, 0.25); st = r.uniform(25, 60); x += math.cos(a) * st; y += math.sin(a) * st; pts.append((x, y))
        d.line(pts, fill=(5, 6, 8, 230), width=7); d.line(pts, fill=(200, 212, 220, 220), width=3)
    for k in range(4):
        rr = 50 + k * 60; d.arc([cx - rr, cy - rr, cx + rr, cy + rr], r.uniform(0, 360), r.uniform(0, 360) + r.uniform(60, 150), fill=(200, 212, 220, 180), width=3)
    d.ellipse([cx - 40, cy - 34, cx + 40, cy + 34], fill=(4, 5, 7, 255))
    im.alpha_composite(lay)


def _count_rem(t):
    import timeline_ep09 as TL
    show, st, secs = TL.COUNTDOWN[:3]
    return secs if t < st else max(0, secs - int(t - st))


def draw_monitor(state, t, idx=0, crack=False):
    """EP08 states: 'rec' (REC overlay over the live recording, transparent), 'recoff' (the same, then the screen dies), 'timer' (one of
    the wall monitors: the deletion timer), 'del' («Удаление через десять секунд» + the timer). Anything else: EP07's draw_monitor7."""
    import timeline_ep09 as TL
    if state in ("rec", "recoff"):
        off = state == "recoff" and t >= TL.T_RECOFF
        if off:
            im = Image.new("RGBA", (MW, MH), (2, 3, 4, 255)); d = ImageDraw.Draw(im); a = t - TL.T_RECOFF
            if a < 0.3:                                   # the picture collapses into a line, the line into a dot
                k = a / 0.3; hh = max(3, int(MH * 0.5 * (1 - k) ** 3)); ww = int(MW * (1 - k ** 2 * 0.95))
                d.rectangle([MW // 2 - ww // 2, MH // 2 - hh // 2, MW // 2 + ww // 2, MH // 2 + hh // 2], fill=(235, 245, 255, 255))
            elif a < 0.6: rr = int(14 * (1 - (a - 0.3) / 0.3)) + 2; d.ellipse([MW // 2 - rr, MH // 2 - rr, MW // 2 + rr, MH // 2 + rr], fill=(235, 245, 255, 255))
        else:
            im = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            cx = MW // 2
            if int(t * 2) % 2 == 0: d.ellipse([cx - 330, 90, cx - 290, 130], fill=(255, 40, 40, 255))
            d.text((cx - 270, 110), "REC", font=F("Rubik-Bold.ttf", 52), fill=(255, 255, 255, 240), anchor="lm")
            d.text((cx + 330, 110), f"{TL.REC_STAMP}  02:54:{int(t * 1.0) % 60:02d}", font=F("Rubik-Medium.ttf", 44), fill=(255, 255, 255, 230), anchor="rm")
            for (x, y, dx, dy) in [(cx - 380, 60, 1, 1), (cx + 380, 60, -1, 1), (cx - 380, MH - 60, 1, -1), (cx + 380, MH - 60, -1, -1)]:
                d.line([(x, y), (x + 70 * dx, y)], fill=(255, 255, 255, 190), width=6); d.line([(x, y), (x, y + 70 * dy)], fill=(255, 255, 255, 190), width=6)
        if crack: _mon_crack(im)
        return im
    if state == "timer":
        im, d = _mon_bg(True); rem = _count_rem(t); cx = MW // 2
        blink = t < TL.COUNTDOWN[1] and int(t * 3) % 2 == 1
        d.text((cx, 260), "УДАЛЕНИЕ", font=F("Rubik-Bold.ttf", 120), fill=(255, 225, 225, 255), anchor="mm")
        if not blink: d.text((cx, 600), f"00:{rem:02d}", font=F("Rubik-Bold.ttf", 330), fill=(255, 70, 60, 255), anchor="mm")
        _scan(im); return im
    if state == "del":                                    # the crack goes under the text, the text gets a dark outline: it must stay readable
        im, d = _mon_bg(True); cx = MW // 2
        _scan(im)
        if crack: _mon_crack(im)
        d = ImageDraw.Draw(im)
        n = max(0, int((t - TL.T_DEL) * 22)); l1, l2 = TL.MSG_DELETE10; s1 = l1[:n]; s2 = l2[:max(0, n - len(l1) - 1)]
        f = F("Rubik-Bold.ttf", 104)
        if s1: d.text((cx, 190), s1, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=8, stroke_fill=(30, 0, 2, 255))
        if s2: d.text((cx, 320), s2, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=8, stroke_fill=(30, 0, 2, 255))
        if t >= TL.T_DEL:
            rem = _count_rem(t); on = int(t * 3) % 2 == 0
            d.rounded_rectangle([cx - 330, 470, cx + 330, 830], 40, fill=(40, 4, 6, 255), outline=(255, 70, 60, 255) if on else (150, 30, 30, 255), width=10)
            d.text((cx, 650), f"00:{rem:02d}", font=F("Rubik-Bold.ttf", 250), fill=(255, 70, 60, 255), anchor="mm")
        return im
    return draw_monitor7(state, t, idx)



# ---------------------------------------------------------------- EP09 additions «ПЕРВЫЙ АЛЕКС»
def _card9(im, y0, h, text, t0, t, big=False, fill=(20, 4, 6), edge=(255, 60, 60), head="Номер скрыт"):
    """EP08's alert card (the series' «Номер скрыт» style), sliding up; long texts wrap to two lines"""
    a = ease((t - t0) / 0.2)
    if a <= 0: return
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(c); dy = int((1 - a) * 40)
    cd.rounded_rectangle([40, y0 + dy, W - 40, y0 + h + dy], 42, fill=fill + (int(235 * a),), outline=edge + (int(255 * a),), width=5)
    cd.text((W // 2, y0 + 56 + dy), head, font=F("Rubik-Medium.ttf", 32), fill=(255, 140, 140, int(255 * a)), anchor="mm")
    fs = 70 if big else 62
    while True:
        lines = wrap(cd, text, F("Rubik-Bold.ttf", fs), W - 130)
        if len(lines) <= 2 or fs <= 44: break
        fs -= 4
    lh = int(fs * 1.18); y = y0 + h // 2 + 26 + dy - (len(lines) - 1) * lh // 2
    for ln in lines:
        cd.text((W // 2, y), ln, font=F("Rubik-Bold.ttf", fs), fill=(255, 255, 255, int(255 * a)), anchor="mm"); y += lh
    glow = c.filter(ImageFilter.GaussianBlur(14)); im.alpha_composite(glow); im.alpha_composite(c)


def _bg9(im, red=False):
    d = ImageDraw.Draw(im)
    for y in range(90, H):
        k = y / H
        d.line([(0, y), (W, y)], fill=((int(60 + 50 * k), int(6 + 6 * k), int(10 + 8 * k), 255) if red else (int(10 + 16 * k), int(14 + 20 * k), int(28 + 34 * k), 255)))
    return d


def draw_task9(im, data, t):
    """ALEX_49's phone: it wakes (02:55), «Задание выполнено», then «Уничтожить предыдущую копию»; from t_crack the screen is
    cracked (the knife) and glitching — the cards stay readable through the crack"""
    d = _bg9(im)
    on = ease((t - data["t_on"]) / 0.3)
    d.text((W // 2, 250), data["clock"], font=F("Rubik-Medium.ttf", 150), fill=(235, 240, 255, int(255 * on)), anchor="mm")
    d.text((W // 2, 360), "суббота, 7 ноября", font=F("Rubik-Medium.ttf", 38), fill=(200, 215, 255, int(255 * on)), anchor="mm")
    _card9(im, 560, 250, data["m1"], data["t1"], t)
    _card9(im, 850, 330, data["m2"], data["t2"], t, big=True)
    if t >= data["t_crack"]:
        draw_crack(im, 909)
        draw_glitch(im, t)


def draw_cop9(im, data, t):
    """the officer's phone held out at them: «Создатель обнаружен», «Начать последнюю проверку», then the whole screen turns red:
    «Оригинал должен умереть» in large type (readable at a glance on a phone)"""
    final = t >= data["t3"]
    d = _bg9(im, red=final)
    on = ease((t - data["t_on"]) / 0.3)
    if not final:
        d.text((W // 2, 230), data["clock"], font=F("Rubik-Medium.ttf", 130), fill=(235, 240, 255, int(255 * on)), anchor="mm")
        _card9(im, 470, 290, data["m1"], data["t1"], t)
        _card9(im, 830, 330, data["m2"], data["t2"], t, big=True)
        return
    a = ease((t - data["t3"]) / 0.25); pulse = 0.85 + 0.15 * (int(t * 4) % 2)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(c)
    cd.rounded_rectangle([34, 300, W - 34, 1330], 50, outline=(255, 230, 230, int(255 * a * pulse)), width=8)
    cd.text((W // 2, 400), "Номер скрыт", font=F("Rubik-Medium.ttf", 36), fill=(255, 200, 200, int(255 * a)), anchor="mm")
    y = 640
    for ln in ("Оригинал", "должен", "умереть"):
        cd.text((W // 2, y), ln, font=F("Rubik-Bold.ttf", 116), fill=(255, 255, 255, int(255 * a)), anchor="mm", stroke_width=6, stroke_fill=(60, 0, 4, int(255 * a))); y += 175
    sc = 1.0 + 0.12 * (1 - a)
    if sc > 1.001: c = c.resize((int(W * sc), int(H * sc)), Image.BILINEAR).crop((int(W * (sc - 1) / 2), int(H * (sc - 1) / 2), int(W * (sc - 1) / 2) + W, int(H * (sc - 1) / 2) + H))
    glow = c.filter(ImageFilter.GaussianBlur(16)); im.alpha_composite(glow); im.alpha_composite(c)

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import timeline_ep09 as TL
    CLOCK = LOCK_CLOCK = getattr(TL, "PHONE_CLOCK", CLOCK)
    out = os.path.join(ROOT, "renders", "ui_preview"); os.makedirs(out, exist_ok=True)
    for name, els in TL.PHONE.items():  # preview every phone state just after its last element appears
        draw_screen(els, max(t for t, _ in els) + 0.6).save(os.path.join(out, f"{name}.png"))
    print("wrote", len(TL.PHONE), "previews to", out)
