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
        elif kind == "task12":                                                            # EP12: the first task on the dashboard phone
            sig.append((kind,) + tuple(round(min(max(t - data[k], -0.1), 0.3), 2) for k in ("t_on", "t1", "t2", "t3")) + (int(t * 8) % 2 if data["t_on"] - 0.6 <= t < data["t1"] else 0,))
        elif kind == "ui13": sig.append((kind, data, int(t * 15)))                     # EP13
        elif kind in ("faces10", "choice10", "sis10", "video10", "end10"):  # EP10: animated full screens, 15 updates/s
            sig.append((kind, int(t * 15), VIDEO_LIP(t) if kind == "sis10" and data.get("lips") else 0))
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
        for ep in ("EP12", "EP11", "EP10", "EP06", "EP04"):   # EP07: EP06 portrait / EP04 photo, read-only (EP12: EP11/EP10 renders too)
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
        if kind == "task12": draw_task12(im, data, t); return im            # EP12
        if kind == "ui13": globals()["draw_" + data](im, t); return im      # EP13: full-screen phone states
        if kind == "cop9": draw_cop9(im, data, t); return im                # EP09
        if kind == "faces10": draw_faces10(im, data, t); return im          # EP10
        if kind == "choice10": draw_choice10(im, data, t); return im        # EP10
        if kind == "sis10": draw_sis10(im, data, t); return im              # EP10
        if kind == "video10": draw_video10(im, data, t); return im          # EP10
        if kind == "end10": draw_end10(im, data, t); return im              # EP10
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
    import timeline_ep13 as TL
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
    import timeline_ep13 as TL
    show, st, secs = TL.COUNTDOWN[:3]
    return secs if t < st else max(0, secs - int(t - st))


def draw_monitor(state, t, idx=0, crack=False):
    """EP08 states: 'rec' (REC overlay over the live recording, transparent), 'recoff' (the same, then the screen dies), 'timer' (one of
    the wall monitors: the deletion timer), 'del' («Удаление через десять секунд» + the timer). Anything else: EP07's draw_monitor7."""
    import timeline_ep13 as TL
    if state == "proj10": return draw_proj10(t)                         # EP10
    if state in ("choice11", "zero11", "hosp11", "face11"): return globals()["draw_" + state](t)   # EP11
    if state in ("face12", "admin12", "retry12", "live12"): return globals()["draw_" + state](t)   # EP12
    if state in M13: return globals()["draw_" + state](t)                                    # EP13
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

# ---------------------------------------------------------------- EP10 additions «СОЗДАТЕЛЬ»
# Alex's face in the series' own 16x16 pixel map (scene.js FACE_ALEX + faceVariant tokens), drawn flat for the screens
_FACE_ALEX = ['HHHHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHHH', 'HHsHHHHsHHHHHsHH', 'ssssssssssssssss', 'ssbbbssssssbbbss',
              'ssssssssssssssss', 'ssswessssssewsss', 'ssswessssssewsss', 'ssssssssssssssss', 'sssssssnnsssssss', 'ssssssssssssssss',
              'ssssssMMMMssssss', 'sssstttttttsssss', 'ssssstttttssssss', 'ssssssssssssssss']
_FPAL = {'H': (59, 42, 32), 's': (217, 162, 126), 'd': (192, 136, 102), 't': (201, 147, 114), 'w': (242, 239, 230), 'e': (27, 27, 32),
         'b': (46, 32, 24), 'n': (192, 136, 102), 'M': (122, 63, 53), 'O': (58, 22, 18)}
_FACES = {}


def _alex_face(v, px):
    """Alex's face at px pixels per cell, variant v: 0 neutral, 1 worried, 2 wide eyes, 3 eyes down, 4 open mouth (the failed copies)"""
    k = (v, px)
    if k in _FACES: return _FACES[k]
    f = list(_FACE_ALEX)
    if v == 1: f[5] = 'sssbbssssssbbsss'; f[4] = 'ssbsssssssssbsss'
    if v == 2: f[4] = 'ssbbbssssssbbbss'; f[5] = 'ssssssssssssssss'; f[6] = 'ssswwsssssswwsss'
    if v == 3: f[7] = 'ssswwsssssswwsss'; f[8] = 'ssseesssssseesss'
    if v == 4: f[12] = 'ssssssMOOMssssss'; f[13] = 'sssstMOOMttsssss'
    im = Image.new("RGB", (16, 16)); im.putdata([_FPAL[c] for row in f for c in row])
    _FACES[k] = im.resize((16 * px, 16 * px), Image.NEAREST)
    return _FACES[k]


def draw_faces10(im, data, t):
    """«На экранах появились сотни лиц. Каждое было моим.» Dark until t_on; then a grid of Alex's face that zooms out from a few big
    faces to hundreds (t_on -> t_many), each tile flickering, some tiles dead (static) — the copies that failed"""
    import random
    d = ImageDraw.Draw(im); d.rectangle([0, 0, W, H], fill=(4, 6, 9, 255))
    if t < data["t_on"]: return
    k = ease((t - data["t_on"]) / max(0.1, data["t_many"] - data["t_on"]))
    cols = int(round(3 + 11 * k)); cell = W / cols; rows = int(H / cell) + 1
    px = max(1, int(cell * 0.86 / 16))
    r = random.Random(1048)
    tick = int(t * 6)
    for j in range(rows):
        for i in range(cols):
            rr = random.Random(j * 131 + i * 17 + 7); v = rr.randrange(5)
            x0, y0 = int(i * cell), int(j * cell)
            if rr.random() < 0.06 and (tick + i + j) % 3 == 0:            # a dead tile: static
                for _ in range(10): xx = x0 + r.randrange(max(1, int(cell))); yy = y0 + r.randrange(max(1, int(cell))); d.rectangle([xx, yy, xx + 3, yy + 3], fill=(90, 120, 150, 255))
                continue
            f = _alex_face(v, px); ox = x0 + (int(cell) - f.width) // 2; oy = y0 + (int(cell) - f.height) // 2
            im.paste(f, (ox, oy))
            if (rr.random() < 0.18) and ((tick + i * 3 + j) % 4 == 0): d.rectangle([x0, y0, x0 + int(cell) - 2, y0 + int(cell) - 2], fill=(10, 14, 20, 140))
    if t - data["t_on"] < 0.25:                                          # the screen wakes: a white flash
        a = int(255 * (1 - (t - data["t_on"]) / 0.25)); lay = Image.new("RGBA", (W, H), (230, 240, 255, a)); im.alpha_composite(lay)


def _btn10(c, y, text, a, fill, edge, txt=(255, 255, 255), fs=58):
    c.rounded_rectangle([50, y, W - 50, y + 190], 44, fill=fill + (int(240 * a),), outline=edge + (int(255 * a),), width=6)
    c.text((W // 2, y + 95), text, font=F("Rubik-Bold.ttf", fs), fill=txt + (int(255 * a),), anchor="mm")


def draw_choice10(im, data, t):
    """the final choice on the officer's phone: «Уничтожить оригинал» (t1), «Остановить игру» (t2); the tap on «Остановить игру»
    (t_tap), the screen floods red (t_red), «Недостаточно прав» slams in (t_deny)"""
    red = t >= data["t_red"]
    d = _bg9(im, red=red)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    c.text((W // 2, 230), "Номер скрыт", font=F("Rubik-Medium.ttf", 36), fill=(255, 170, 170, 255), anchor="mm")
    if t >= data["t1"]:
        a = ease((t - data["t1"]) / 0.2); _btn10(c, 470 + int((1 - a) * 40), "Уничтожить оригинал", a, (70, 8, 12), (255, 70, 64), fs=46)
    if t >= data["t2"]:
        a = ease((t - data["t2"]) / 0.2)
        pressed = t >= data["t_tap"]
        _btn10(c, 760 + int((1 - a) * 40), "Остановить игру", a, (235, 238, 245) if pressed else (30, 36, 48), (255, 255, 255), (20, 22, 28) if pressed else (255, 255, 255))
        if pressed and t - data["t_tap"] < 0.5:                          # the tap ripple
            rr = int(40 + 500 * (t - data["t_tap"])); al = int(200 * (1 - (t - data["t_tap"]) / 0.5))
            c.ellipse([W // 2 - rr, 855 - rr, W // 2 + rr, 855 + rr], outline=(255, 255, 255, al), width=8)
    if red:
        a = ease((t - data["t_red"]) / 0.15); lay2 = Image.new("RGBA", (W, H), (200, 12, 16, int(170 * a))); lay.alpha_composite(lay2)
    if t >= data["t_deny"]:
        a = min(1.0, (t - data["t_deny"]) / 0.06); sc = 1.0 + 0.35 * max(0.0, 1 - (t - data["t_deny"]) / 0.12)
        lay = Image.new("RGBA", (W, H), (150, 6, 10, 255)); c = ImageDraw.Draw(lay)
        on = int(t * 4) % 2 == 0
        c.rounded_rectangle([34, 420, W - 34, 1180], 50, outline=(255, 235, 235, 255 if on else 150), width=8)
        c.text((W // 2, 520), "Ошибка", font=F("Rubik-Medium.ttf", 40), fill=(255, 200, 200, 255), anchor="mm")
        y = 720
        for ln in ("Недостаточно", "прав"):
            c.text((W // 2, y), ln, font=F("Rubik-Bold.ttf", 86), fill=(255, 255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(60, 0, 4, 255)); y += 150
        if sc > 1.001: lay = lay.resize((int(W * sc), int(H * sc)), Image.BILINEAR).crop((int(W * (sc - 1) / 2), int(H * (sc - 1) / 2), int(W * (sc - 1) / 2) + W, int(H * (sc - 1) / 2) + H))
        if t - data["t_deny"] < 0.5: draw_glitch(lay, t)
    glow = lay.filter(ImageFilter.GaussianBlur(14)); im.alpha_composite(glow); im.alpha_composite(lay)


_EP08 = os.path.join(os.path.dirname(ROOT), "EP08", "scenes")


def _feed_img(lip, size):
    k = ("feed", lip, size)
    if k not in _IMG:
        p = os.path.join(_EP08, f"E8_feedc_{lip}.png")
        im = Image.open(p).convert("RGB"); tw, th = size; sc = max(tw / im.width, th / im.height)
        im = im.resize((int(im.width * sc + 0.5), int(im.height * sc + 0.5)), Image.LANCZOS)
        x0, y0 = (im.width - tw) // 2, (im.height - th) // 2; _IMG[k] = im.crop((x0, y0, x0 + tw, y0 + th))
    return _IMG[k]


def _rec_marks(c, t, stamp=None):
    if int(t * 2) % 2 == 0: c.ellipse([60, 130, 92, 162], fill=(255, 40, 40, 255))
    c.text((106, 146), "REC", font=F("Rubik-Bold.ttf", 40), fill=(255, 255, 255, 240), anchor="lm")
    if stamp: c.text((W - 50, 146), stamp, font=F("Rubik-Medium.ttf", 34), fill=(255, 255, 255, 220), anchor="rm")


def draw_sis10(im, data, t):
    """the sister's live feed on every phone (EP08's close feed of her face; mouth from the VO envelope), scanlines, REC"""
    d = ImageDraw.Draw(im); d.rectangle([0, 0, W, H], fill=(3, 4, 6, 255))
    if t < data["t_on"]: return
    lip = VIDEO_LIP(t) if data.get("lips") else "neutral"
    f = _feed_img(lip, (W, H)).convert("RGBA")
    g = ImageEnhance.Color(f).enhance(0.6); im.alpha_composite(g)
    _scan(im, 60); c = ImageDraw.Draw(im); _rec_marks(c, t)
    if t - data["t_on"] < 0.4: draw_glitch(im, t)


def draw_video10(im, data, t):
    """«На экранах появилось видео»: the recording from room 204 on the phone (the E10_r204_wide render), REC, then «Комната 204»"""
    d = ImageDraw.Draw(im); d.rectangle([0, 0, W, H], fill=(3, 4, 6, 255))
    if t < data["t_on"]: return
    k = ("vid", W, H)
    if k not in _IMG: _IMG[k] = photo("E10_r204_wide", (W, H))
    f = ImageEnhance.Color(_IMG[k]).enhance(0.55).convert("RGBA"); im.alpha_composite(f)
    _scan(im, 60); c = ImageDraw.Draw(im); _rec_marks(c, t)
    if t >= data["t_cap"]:
        a = ease((t - data["t_cap"]) / 0.2)
        c.rounded_rectangle([50, H - 330, W - 50, H - 200], 30, fill=(0, 0, 0, int(170 * a)))
        c.text((W // 2, H - 265), "КОМНАТА 204", font=F("Rubik-Bold.ttf", 66), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    if t - data["t_on"] < 0.4: draw_glitch(im, t)


def draw_end10(im, data, t):
    """the phone dies (t_off: the picture collapses to a line, a dot, black), then on black: «Уровень десять завершён» (t1),
    «Следующий игрок:» (t2) and the name «Елена» (t_name), red"""
    d = ImageDraw.Draw(im); d.rectangle([0, 0, W, H], fill=(0, 0, 0, 255))
    if t < data["t_off"]:
        _bg9(im, red=True)
        c = ImageDraw.Draw(im); c.text((W // 2, H // 2), "Недостаточно прав", font=F("Rubik-Bold.ttf", 62), fill=(255, 255, 255, 255), anchor="mm")
        return
    a = t - data["t_off"]
    if a < 0.3:
        k = a / 0.3; hh = max(3, int(H * 0.5 * (1 - k) ** 3)); ww = int(W * (1 - k ** 2 * 0.95))
        d.rectangle([W // 2 - ww // 2, H // 2 - hh // 2, W // 2 + ww // 2, H // 2 + hh // 2], fill=(255, 225, 225, 255)); return
    if a < 0.6:
        rr = int(12 * (1 - (a - 0.3) / 0.3)) + 2; d.ellipse([W // 2 - rr, H // 2 - rr, W // 2 + rr, H // 2 + rr], fill=(255, 225, 225, 255)); return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    if t >= data["t1"]:
        al = ease((t - data["t1"]) / 0.25)
        for i, ln in enumerate(("Уровень десять", "завершён")):
            c.text((W // 2, 470 + i * 100), ln, font=F("Rubik-Bold.ttf", 78), fill=(235, 240, 255, int(255 * al)), anchor="mm")
    if t >= data["t2"]:
        al = ease((t - data["t2"]) / 0.25)
        c.line([(140, 690), (W - 140, 690)], fill=(255, 255, 255, int(90 * al)), width=3)
        c.text((W // 2, 820), "Следующий игрок:", font=F("Rubik-Bold.ttf", 66), fill=(255, 255, 255, int(255 * al)), anchor="mm")
    if t >= data["t_name"]:
        al = min(1.0, (t - data["t_name"]) / 0.08); sc = 1.0 + 0.3 * max(0.0, 1 - (t - data["t_name"]) / 0.15)
        f = F("Rubik-Bold.ttf", int(150 * sc))
        c.text((W // 2, 1010), "Елена", font=f, fill=(255, 60, 52, int(255 * al)), anchor="mm", stroke_width=5, stroke_fill=(50, 0, 3, int(255 * al)))
    glow = lay.filter(ImageFilter.GaussianBlur(16)); im.alpha_composite(glow); im.alpha_composite(lay)


def draw_proj10(t):
    """the sister's monitor in room 204: a dark project window — «Проект «Алекс»» typed in (TL.T_PROJ), then «Создатель:» (TL.T_CREATOR)
    and the name «Елена» in red (TL.T_NAME). Nothing else is written on it."""
    import timeline_ep13 as TL
    im, d = _mon_bg(False); cx = MW // 2
    d.rounded_rectangle([60, 60, MW - 60, MH - 60], 26, outline=(90, 170, 230, 255), width=6)
    d.rectangle([60, 60, MW - 60, 150], fill=(18, 40, 60, 255))
    for i, col in enumerate(((255, 90, 80), (255, 200, 80), (90, 220, 120))): d.ellipse([100 + i * 60, 88, 134 + i * 60, 122], fill=col + (255,))
    s1 = _typed(TL.MSG_PROJ, t, TL.T_PROJ, 22)
    fP, fC, fN = F("Rubik-Bold.ttf", 92), F("Rubik-Medium.ttf", 74), F("Rubik-Bold.ttf", 84)
    if s1: d.text((cx - d.textlength(TL.MSG_PROJ, font=fP) / 2, 400), s1, font=fP, fill=(235, 245, 255, 255), anchor="lm")
    wC, wN = d.textlength("Создатель: ", font=fC), d.textlength("Елена", font=fN); x0 = cx - (wC + wN) / 2
    if t >= TL.T_CREATOR: d.text((x0, 600), "Создатель: ", font=fC, fill=(170, 200, 230, 255), anchor="lm")
    if t >= TL.T_NAME:
        a = min(1.0, (t - TL.T_NAME) / 0.08)
        d.text((x0 + wC, 600), "Елена", font=fN, fill=(255, 70, 60, int(255 * a)), anchor="lm")
    if t < TL.T_CREATOR and int(t * 2.5) % 2 == 0:                     # the cursor
        xc = cx - d.textlength(TL.MSG_PROJ, font=fP) / 2 + (d.textlength(s1, font=fP) if s1 else 0) + 10
        d.rectangle([xc, 355, xc + 16, 445], fill=(235, 245, 255, 255))
    _scan(im, 30)
    return im



# ---------------------------------------------------------------- EP12 additions «НУЛЕВОЙ УРОВЕНЬ»
# Monitor states (MW x MH). Everything readable sits in the middle half of the width (the vertical frame sees the screen's centre).
def _TL():
    import timeline_ep13 as TL
    return TL


def _center_lines(d, lines, y0, font, fill, gap, stroke=0, sfill=(0, 0, 0, 255)):
    y = y0
    for ln in lines:
        d.text((MW // 2, y), ln, font=font, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sfill); y += gap


def draw_choice11(t):
    """the screen in front of the chained sister: idle glow (cold), then «Выберите, кого сохранить» typed in (T_TITLE), two choices:
    «Создателя» (T_OPT1) «или» «игрока» (T_OPT2). Nothing else is written on it."""
    TL = _TL(); im, d = _mon_bg(False); cx = MW // 2
    d.rounded_rectangle([330, 50, MW - 330, MH - 50], 30, outline=(90, 170, 230, 255), width=6)
    pulse = 0.5 + 0.5 * math.sin(t * 3.0)
    if t < TL.T_TITLE:                                                  # waiting: a slow pulsing ring, no text
        r = int(70 + 14 * pulse); d.ellipse([cx - r, MH // 2 - r, cx + r, MH // 2 + r], outline=(120, 190, 240, int(150 + 80 * pulse)), width=8)
        _scan(im, 30); return im
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    full = TL.MSG_TITLE; n = max(0, int((t - TL.T_TITLE) * 30)); typed = full[:n]
    l1, l2 = "Выберите,", "кого сохранить"
    f = F("Rubik-Bold.ttf", 78)
    c.text((cx, 180), typed[:len(l1)], font=f, fill=(235, 245, 255, 255), anchor="mm")
    if n > len(l1) + 1: c.text((cx, 275), typed[len(l1) + 1:], font=f, fill=(235, 245, 255, 255), anchor="mm")
    def btn(y, text, t0, red):
        a = ease((t - t0) / 0.2); fill = (70, 8, 12) if red else (16, 40, 62); edge = (255, 80, 70) if red else (120, 200, 255)
        c.rounded_rectangle([cx - 330, y + int((1 - a) * 30), cx + 330, y + 130 + int((1 - a) * 30)], 36, fill=fill + (int(235 * a),), outline=edge + (int(255 * a),), width=7)
        c.text((cx, y + 65 + int((1 - a) * 30)), text, font=F("Rubik-Bold.ttf", 68), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    if t >= TL.T_OPT1: btn(400, "Создателя", TL.T_OPT1, True)
    if t >= TL.T_OPT2:
        a = ease((t - TL.T_OPT2) / 0.2); c.text((cx, 595), "или", font=F("Rubik-Medium.ttf", 52), fill=(170, 200, 230, int(255 * a)), anchor="mm")
        btn(655, "игрока", TL.T_OPT2, False)
    glow = lay.filter(ImageFilter.GaussianBlur(10)); im.alpha_composite(glow); im.alpha_composite(lay)
    _scan(im, 30); return im


def draw_zero11(t):
    """the choice screen floods red (T_RED); «Нулевой уровень активирован» types in (T_ZERO); then «Удаление всех копий» (T_DEL) with a
    deletion bar filling."""
    TL = _TL()
    if t < TL.T_RED: return draw_choice11(t)
    im, d = _mon_bg(True); cx = MW // 2
    a = t - TL.T_RED
    if a < 0.25: im.alpha_composite(Image.new("RGBA", (MW, MH), (255, 40, 30, int(255 * (1 - a / 0.25)))))
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    on = int(t * 3) % 2 == 0
    c.rounded_rectangle([330, 50, MW - 330, MH - 50], 30, outline=(255, 90, 80, 255 if on else 140), width=8)
    f = F("Rubik-Bold.ttf", 84)
    if t >= TL.T_ZERO:
        n = max(0, int((t - TL.T_ZERO) * 28)); s1, s2 = "Нулевой уровень", "активирован"; typed = TL.MSG_ZERO[:n]
        c.text((cx, 190), typed[:len(s1)], font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(50, 0, 4, 255))
        if n > len(s1) + 1: c.text((cx, 295), typed[len(s1) + 1:], font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(50, 0, 4, 255))
    else:
        r = int(80 + 30 * abs(math.sin(t * 6))); c.ellipse([cx - r, MH // 2 - r - 60, cx + r, MH // 2 + r - 60], outline=(255, 220, 220, 220), width=10)
    if t >= TL.T_DEL:
        al = min(1.0, (t - TL.T_DEL) / 0.08); sc = 1.0 + 0.25 * max(0.0, 1 - (t - TL.T_DEL) / 0.15)
        fD = F("Rubik-Bold.ttf", int(72 * sc))
        c.text((cx, 480), "Удаление", font=fD, fill=(255, 70, 60, int(255 * al)), anchor="mm", stroke_width=5, stroke_fill=(40, 0, 3, 255))
        c.text((cx, 570), "всех копий", font=fD, fill=(255, 70, 60, int(255 * al)), anchor="mm", stroke_width=5, stroke_fill=(40, 0, 3, 255))
        k = min(1.0, (t - TL.T_DEL) / 9.0)
        c.rounded_rectangle([cx - 320, 690, cx + 320, 750], 14, outline=(255, 200, 200, 255), width=5)
        c.rectangle([cx - 310, 700, cx - 310 + int(620 * k), 740], fill=(255, 70, 60, 255))
        for i in range(int(k * 47)):                                     # a tick per deleted copy under the bar
            x = cx - 312 + i * 13.3; c.rectangle([x, 775, x + 7, 800], fill=(255, 210, 210, 230))
    glow = lay.filter(ImageFilter.GaussianBlur(12)); im.alpha_composite(glow); im.alpha_composite(lay)
    if a < 0.5: draw_glitch(im, t)
    _scan(im, 36); return im


def draw_hosp11(t):
    """the side monitor: black, then (T_REC) the hospital recording three years ago — the E11_hosp_feed render, desaturated, REC and the
    date; from T_COPIES the picture breaks up into copies of his face multiplying (the EP10 grid motif)."""
    TL = _TL()
    im = Image.new("RGBA", (MW, MH), (3, 4, 6, 255)); d = ImageDraw.Draw(im)
    if t < TL.T_REC:
        for i in range(260):
            r = (i * 7919 + int(t * 15) * 104729) % 100000; x = r % MW; y = (r // MW * 37 + i * 13) % MH
            d.rectangle([x, y, x + 5, y + 3], fill=(60, 80, 90, 255))
        return im
    k = ("hospfeed", MW, MH)
    if k not in _IMG: _IMG[k] = photo("E11_hosp_feed", (MW, MH))
    f = ImageEnhance.Color(_IMG[k]).enhance(0.45).convert("RGBA"); im.alpha_composite(f)
    if t >= TL.T_COPIES:                                                 # the copies: a grid of his face zooming out over the recording
        kk = ease((t - TL.T_COPIES) / 1.6); cols = int(round(2 + 14 * kk)); cell = MW / cols; rows = int(MH / cell) + 1
        px = max(1, int(cell * 0.86 / 16)); tick = int(t * 6)
        grid = Image.new("RGBA", (MW, MH), (4, 6, 9, int(255 * min(1.0, (t - TL.T_COPIES) / 0.3)))); g = ImageDraw.Draw(grid)
        for j in range(rows):
            for i in range(cols):
                v = (j * 131 + i * 17 + 7) % 5
                if (tick + i * 3 + j) % 11 == 0: continue
                fc = _alex_face(v, px); grid.paste(fc, (int(i * cell) + (int(cell) - fc.width) // 2, int(j * cell) + (int(cell) - fc.height) // 2))
        im.alpha_composite(grid)
    _scan(im, 50); c = ImageDraw.Draw(im); cx = MW // 2
    if int(t * 2) % 2 == 0: c.ellipse([cx - 360, 70, cx - 318, 112], fill=(255, 40, 40, 255))
    c.text((cx - 300, 91), "REC", font=F("Rubik-Bold.ttf", 54), fill=(255, 255, 255, 240), anchor="lm")
    c.text((cx + 370, 91), TL.HOSP_STAMP, font=F("Rubik-Medium.ttf", 50), fill=(255, 255, 255, 235), anchor="rm")
    if t - TL.T_REC < 0.35 or 0 <= t - TL.T_COPIES < 0.5: draw_glitch(im, t)
    return im


_FACE11 = {}


def _orig_face(eyes, mouth, px):
    """ALEX_ORIGINAL_CONSCIOUSNESS on the screen: Alex's own 16x16 face map (the series' FACE_ALEX), eyes 'closed' | 'half' | 'open',
    mouth 'neutral' | 'open' | 'ee' | 'oo' (lip-sync from the VO envelope), drawn cold and pale"""
    k = (eyes, mouth, px)
    if k in _FACE11: return _FACE11[k]
    f = list(_FACE_ALEX)
    if eyes == "closed": f[7] = 'ssssssssssssssss'; f[8] = 'sssbbssssssbbsss'
    if eyes == "half": f[7] = 'ssssssssssssssss'; f[8] = 'ssswessssssewsss'
    if mouth == "open": f[12] = 'ssssssMOOMssssss'; f[13] = 'sssstMOOMttsssss'
    if mouth == "ee": f[12] = 'sssssMOOOOMsssss'; f[13] = 'sssstttttttsssss'
    if mouth == "oo": f[12] = 'sssssssMMsssssss'; f[13] = 'sssstttOOttsssss'; f[14] = 'ssssstMMMtssssss'
    pal = dict(_FPAL); pal.update({'s': (214, 196, 188), 'd': (184, 164, 158), 't': (196, 176, 168), 'n': (184, 164, 158)})
    im = Image.new("RGB", (16, 16)); im.putdata([pal[c] for row in f for c in row])
    _FACE11[k] = im.resize((16 * px, 16 * px), Image.NEAREST)
    return _FACE11[k]


def draw_face11(t):
    """the computer, turned to ALEX_48: until T_FACE the red zero-level screen; then Alex's face, eyes closed (T_FACE); the eyes open
    (T_EYES); the mouth moves with the VO in the original's lines; «Подключение к оригиналу установлено» (T_MSG1), «Оригинал проснулся» (T_MSG2)"""
    TL = _TL()
    if t < TL.T_FACE: return draw_zero11(t)
    im = Image.new("RGBA", (MW, MH), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    for y in range(0, MH, 2):
        k = y / MH; d.line([(0, y), (MW, y)], fill=(int(8 + 10 * k), int(22 + 16 * k), int(30 + 20 * k), 255))
    a = t - TL.T_FACE
    eyes = "closed"
    if t >= TL.T_EYES: eyes = "half" if t - TL.T_EYES < 0.12 else "open"
    mouth = VIDEO_LIP(t) if any(x <= t < y for x, y in TL.LIPW_UI) else "neutral"
    px = 50; fc = _orig_face(eyes, mouth, px).convert("RGBA")
    fx, fy = (MW - fc.width) // 2, 60
    if a < 0.6:                                                          # the face assembles out of the static
        al = int(255 * ease(a / 0.6)); fc = fc.copy(); fc.putalpha(al)
    im.alpha_composite(fc, (fx, fy))
    if t >= TL.T_EYES and t - TL.T_EYES < 0.6:                            # the eyes open: a cold flare on them
        fl = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); fd = ImageDraw.Draw(fl); al = int(200 * (1 - (t - TL.T_EYES) / 0.6))
        for ex in (fx + 3 * px, fx + 11 * px): fd.rectangle([ex - 10, fy + 7 * px - 10, ex + 2 * px + 10, fy + 9 * px + 10], fill=(200, 245, 255, al))
        im.alpha_composite(fl.filter(ImageFilter.GaussianBlur(12)))
    # cold tint + scanlines
    im.alpha_composite(Image.new("RGBA", (MW, MH), (90, 200, 230, 28)))
    _scan(im, 46)
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay); cx = MW // 2
    if t >= TL.T_MSG1:
        band = 1.0 if t < TL.T_MSG2 else 0.0
        if band:
            c.rounded_rectangle([330, 560, MW - 330, 900], 30, fill=(4, 14, 20, 225), outline=(110, 220, 255, 255), width=6)
            n = max(0, int((t - TL.T_MSG1) * 26)); s1, s2 = "Подключение", "к оригиналу установлено"; typed = TL.MSG_LINK[:n]
            c.text((cx, 650), typed[:len(s1)], font=F("Rubik-Bold.ttf", 76), fill=(225, 250, 255, 255), anchor="mm")
            if n > len(s1) + 1:
                rest = typed[len(s1) + 1:]; r1, r2 = rest[:11], rest[12:]       # «к оригиналу» / «установлено»
                c.text((cx, 745), r1, font=F("Rubik-Bold.ttf", 66), fill=(225, 250, 255, 255), anchor="mm")
                if r2: c.text((cx, 830), r2, font=F("Rubik-Bold.ttf", 66), fill=(120, 230, 255, 255), anchor="mm")
    if t >= TL.T_MSG2:
        al = min(1.0, (t - TL.T_MSG2) / 0.06); sc = 1.0 + 0.3 * max(0.0, 1 - (t - TL.T_MSG2) / 0.15)
        c.rounded_rectangle([320, 560, MW - 320, 910], 30, fill=(40, 0, 4, int(235 * al)), outline=(255, 70, 60, int(255 * al)), width=8)
        fW = F("Rubik-Bold.ttf", int(96 * sc))
        c.text((cx, 670), "Оригинал", font=fW, fill=(255, 70, 60, int(255 * al)), anchor="mm", stroke_width=6, stroke_fill=(40, 0, 3, 255))
        c.text((cx, 800), "проснулся", font=fW, fill=(255, 70, 60, int(255 * al)), anchor="mm", stroke_width=6, stroke_fill=(40, 0, 3, 255))
    glow = lay.filter(ImageFilter.GaussianBlur(12)); im.alpha_composite(glow); im.alpha_composite(lay)
    if a < 0.4 or 0 <= t - TL.T_MSG2 < 0.25: draw_glitch(im, t)
    return im

# ---------------------------------------------------------------- EP12 additions «ПЕРВОЕ ИСПЫТАНИЕ»
def draw_task12(im, data, t):
    """the phone in the car's dash holder, three years ago: the lock screen (night, «воскресенье, 5 ноября»), it buzzes (t_on), then three cards
    one under another, each on its own words: «Первое задание» (t1), «Не тормози» (t2), «Награда — пятьсот долларов» (t3)"""
    d = _bg9(im)
    on = ease((t - data["t_on"] + 0.6) / 0.3)
    d.text((W // 2, 230), data["clock"], font=F("Rubik-Medium.ttf", 150), fill=(235, 240, 255, int(255 * on)), anchor="mm")
    d.text((W // 2, 340), data["date"], font=F("Rubik-Medium.ttf", 38), fill=(200, 215, 255, int(255 * on)), anchor="mm")
    if data["t_on"] - 0.6 <= t < data["t1"] and int(t * 8) % 2:                      # buzzing: the bell icon shakes
        d.text((W // 2 + 10, 470), "((  ))", font=F("Rubik-Bold.ttf", 60), fill=(255, 140, 140, 200), anchor="mm")
    _card9(im, 440, 250, data["m1"], data["t1"], t)
    _card9(im, 720, 250, data["m2"], data["t2"], t, big=True)
    _card9(im, 1000, 300, data["m3"], data["t3"], t, fill=(40, 26, 4), edge=(255, 196, 60))


def _face_variant(eyes, mouth, px, mood=None):
    """the original's face (EP11 _orig_face) + EP12 moods: 'smirk' (one corner of the mouth up), 'scared' (wide eyes, brows up, small open mouth)"""
    k = ("v12", eyes, mouth, px, mood)
    if k in _FACE11: return _FACE11[k]
    f = list(_FACE_ALEX)
    if eyes == "closed": f[7] = 'ssssssssssssssss'; f[8] = 'sssbbssssssbbsss'
    if eyes == "half": f[7] = 'ssssssssssssssss'; f[8] = 'ssswessssssewsss'
    if mood == "scared": f[5] = 'ssssssssssssssss'; f[4] = 'ssbbbssssssbbbss'; f[6] = 'sswwessssssewwss'; f[7] = 'sswwessssssewwss'; f[8] = 'sswwwssssssw wss'.replace(' ', 'w')
    if mouth == "open": f[12] = 'ssssssMOOMssssss'; f[13] = 'sssstMOOMttsssss'
    if mouth == "ee": f[12] = 'sssssMOOOOMsssss'; f[13] = 'sssstttttttsssss'
    if mouth == "oo": f[12] = 'sssssssMMsssssss'; f[13] = 'sssstttOOttsssss'; f[14] = 'ssssstMMMtssssss'
    if mood == "smirk" and mouth == "neutral": f[11] = 'sssssssssMMsssss'; f[12] = 'ssssssMMMMssssss'; f[13] = 'sssstttttttsssss'
    if mood == "scared" and mouth == "neutral": f[12] = 'sssssssMMsssssss'; f[13] = 'ssssssMOOMssssss'
    pal = dict(_FPAL); pal.update({'s': (214, 196, 188), 'd': (184, 164, 158), 't': (196, 176, 168), 'n': (184, 164, 158)})
    im = Image.new("RGB", (16, 16)); im.putdata([pal[c] for row in f for c in row])
    _FACE11[k] = im.resize((16 * px, 16 * px), Image.NEAREST)
    return _FACE11[k]


def _bg_face(red):
    im = Image.new("RGBA", (MW, MH), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    for y in range(0, MH, 2):
        k = y / MH; d.line([(0, y), (MW, y)], fill=((int(30 + 20 * k), int(8 + 6 * k), int(10 + 8 * k), 255) if red else (int(8 + 10 * k), int(22 + 16 * k), int(30 + 20 * k), 255)))
    return im, d


def draw_face12(t):
    """the computer turned to ALEX_48 (EP11's last screen): «Оригинал проснулся» still on it, then it clears; the original's face blinks and
    opens its eyes on «открыл глаза»; mouth from the VO in his lines; a smirk; the screen flashes white (T_FLASH) and becomes the recording;
    the second recording (T_REC2..); the grid of 47 copies (red) and one lit cyan; from T_SCARED his face is afraid."""
    TL = _TL()
    if t >= TL.T_FLASH and t < TL.T_FLASH + 0.6:                         # «Экран вспыхнул»: white-out
        k = (t - TL.T_FLASH) / 0.6; im = Image.new("RGBA", (MW, MH), (int(255 - 60 * k), int(255 - 40 * k), 255, 255)); _scan(im, 30); return im
    if TL.T_REC2 <= t < TL.T_REC2_END:                                   # the second recording plays on this screen
        im = Image.new("RGBA", (MW, MH), (3, 4, 6, 255)); kk = ("rec2", MW, MH)
        if kk not in _IMG: _IMG[kk] = photo("E12_rec_feed", (MW, MH))
        im.alpha_composite(ImageEnhance.Color(_IMG[kk]).enhance(0.5).convert("RGBA")); _scan(im, 50); c = ImageDraw.Draw(im); cx = MW // 2
        if int(t * 2) % 2 == 0: c.ellipse([cx - 360, 70, cx - 318, 112], fill=(255, 40, 40, 255))
        c.text((cx - 300, 91), "REC", font=F("Rubik-Bold.ttf", 54), fill=(255, 255, 255, 240), anchor="lm")
        if t - TL.T_REC2 < 0.35: draw_glitch(im, t)
        return im
    im, d = _bg_face(False)
    if TL.T_GRID <= t < TL.T_GRID_END:                                   # «Сорок семь копий выбрали деньги»: 47 red faces + one cyan (48)
        a = t - TL.T_GRID; cols, rows = 8, 6; cell = min(MW // cols, (MH - 40) // rows); px = max(1, int(cell * 0.82 / 16))
        x0 = (MW - cols * cell) // 2; y0 = (MH - rows * cell) // 2
        n_on = min(48, int(a * 40) + 1)
        for i in range(48):
            if i >= n_on: break
            j, ii = divmod(i, cols); fc = _alex_face((i * 7) % 5, px).convert("RGBA")
            tint = (255, 50, 40, 120) if i < 47 else (90, 230, 255, 120 if t >= TL.T_GRID_CYAN else 0)
            if i == 47 and t < TL.T_GRID_CYAN: tint = (255, 50, 40, 120)
            ov = Image.new("RGBA", fc.size, tint); fc.alpha_composite(ov)
            im.alpha_composite(fc, (x0 + ii * cell + (cell - fc.width) // 2, y0 + j * cell + (cell - fc.height) // 2))
            if i < 47 and a > 0.9:                                         # the money they chose: a red «$» stamped on each
                ImageDraw.Draw(im).text((x0 + ii * cell + cell // 2, y0 + j * cell + cell - 16), "$", font=F("Rubik-Bold.ttf", 34), fill=(255, 210, 90, 255), anchor="mm")
        if t >= TL.T_GRID_CYAN:
            j, ii = divmod(47, cols); x = x0 + ii * cell; y = y0 + j * cell
            ImageDraw.Draw(im).rectangle([x + 2, y + 2, x + cell - 2, y + cell - 2], outline=(110, 235, 255, 255), width=6)
        _scan(im, 46)
        if a < 0.3: draw_glitch(im, t)
        return im
    eyes = "open"
    if TL.T_BLINK0 <= t < TL.T_BLINK1: eyes = "closed"
    elif TL.T_BLINK1 <= t < TL.T_BLINK1 + 0.12: eyes = "half"
    mouth = VIDEO_LIP(t) if any(x <= t < y for x, y in TL.LIPW_UI) else "neutral"
    mood = "scared" if t >= TL.T_SCARED else ("smirk" if TL.T_SMIRK0 <= t < TL.T_SMIRK1 else None)
    px = 50; fc = _face_variant(eyes, mouth, px, mood).convert("RGBA")
    fx, fy = (MW - fc.width) // 2, 60
    if mood == "scared":                                                 # the picture trembles
        fx += int(6 * math.sin(t * 47)); fy += int(4 * math.sin(t * 31))
    im.alpha_composite(fc, (fx, fy))
    if TL.T_BLINK1 <= t < TL.T_BLINK1 + 0.6:                             # the eyes open again: a cold flare
        fl = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); fd = ImageDraw.Draw(fl); al = int(200 * (1 - (t - TL.T_BLINK1) / 0.6))
        for ex in (fx + 3 * px, fx + 11 * px): fd.rectangle([ex - 10, fy + 7 * px - 10, ex + 2 * px + 10, fy + 9 * px + 10], fill=(200, 245, 255, al))
        im.alpha_composite(fl.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(Image.new("RGBA", (MW, MH), (90, 200, 230, 28) if mood != "scared" else (230, 120, 110, 24)))
    _scan(im, 46)
    if t < TL.T_HOOK_END:                                                # EP11's last message still on the screen, fading out
        al = 1.0 if t < TL.T_HOOK_END - 0.4 else (TL.T_HOOK_END - t) / 0.4
        lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay); cx = MW // 2
        c.rounded_rectangle([320, 560, MW - 320, 910], 30, fill=(40, 0, 4, int(235 * al)), outline=(255, 70, 60, int(255 * al)), width=8)
        fW = F("Rubik-Bold.ttf", 96)
        c.text((cx, 670), "Оригинал", font=fW, fill=(255, 70, 60, int(255 * al)), anchor="mm", stroke_width=6, stroke_fill=(40, 0, 3, int(255 * al)))
        c.text((cx, 800), "проснулся", font=fW, fill=(255, 70, 60, int(255 * al)), anchor="mm", stroke_width=6, stroke_fill=(40, 0, 3, int(255 * al)))
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(12))); im.alpha_composite(lay)
    if 0 <= t - TL.T_SCARED < 0.3 or 0 <= t - TL.T_GRID_END < 0.25 or 0 <= t - TL.T_REC2_END < 0.25: draw_glitch(im, t)
    return im


def draw_admin12(t):
    """the handover: the face tears away (T_ADMIN), the screen goes cold; «Передача управления» typed in (T_HAND) with a transfer bar; then
    «Новый администратор:» (T_NEWADM) and a big cyan «48» stamped on (T_48)"""
    TL = _TL()
    if t < TL.T_ADMIN: return draw_face12(t)
    im, d = _bg_face(False); cx = MW // 2; a = t - TL.T_ADMIN
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    c.rounded_rectangle([300, 50, MW - 300, MH - 50], 30, outline=(110, 220, 255, 255), width=6)
    if t < TL.T_HAND:
        r = int(70 + 14 * math.sin(t * 6)); c.ellipse([cx - r, MH // 2 - r, cx + r, MH // 2 + r], outline=(140, 230, 255, 220), width=8)
    else:
        n = max(0, int((t - TL.T_HAND) * 28)); typed = TL.MSG_HAND[:n]; s1 = "Передача"
        f = F("Rubik-Bold.ttf", 74)
        c.text((cx, 170), typed[:len(s1)], font=f, fill=(230, 250, 255, 255), anchor="mm")
        if n > len(s1) + 1: c.text((cx, 270), typed[len(s1) + 1:], font=f, fill=(230, 250, 255, 255), anchor="mm")
        k = min(1.0, (t - TL.T_HAND) / 1.4)
        c.rounded_rectangle([cx - 320, 350, cx + 320, 395], 12, outline=(140, 230, 255, 255), width=4)
        c.rectangle([cx - 312, 358, cx - 312 + int(624 * k), 387], fill=(110, 230, 255, 255))
    if t >= TL.T_NEWADM:
        al = ease((t - TL.T_NEWADM) / 0.2)
        c.text((cx, 500), TL.MSG_NEWADM, font=F("Rubik-Bold.ttf", 54), fill=(200, 240, 255, int(255 * al)), anchor="mm")
    if t >= TL.T_48:
        al = min(1.0, (t - TL.T_48) / 0.06); sc = 1.0 + 0.35 * max(0.0, 1 - (t - TL.T_48) / 0.15)
        c.text((cx, 720), "48", font=F("Rubik-Bold.ttf", int(250 * sc)), fill=(120, 240, 255, int(255 * al)), anchor="mm", stroke_width=8, stroke_fill=(0, 30, 40, 255))
    glow = lay.filter(ImageFilter.GaussianBlur(12)); im.alpha_composite(glow); im.alpha_composite(lay)
    if a < 0.4 or 0 <= t - TL.T_48 < 0.2: draw_glitch(im, t)
    _scan(im, 36); return im


def draw_retry12(t):
    """the sister's monitor on the recording: a dark console; a blinking cursor while she types; «> Повторить испытание» typed in on the words
    (T_CMD); then the line flashes as it is entered (the run starts again: a circular arrow spinning)"""
    TL = _TL()
    im = Image.new("RGBA", (MW, MH), (6, 10, 14, 255)); d = ImageDraw.Draw(im)
    for i in range(7):
        y = 90 + i * 52; d.rectangle([120, y, 120 + 300 + (i * 173) % 700, y + 18], fill=(30, 60, 70, 255))   # earlier output, unreadable
    fC = F("Rubik-Bold.ttf", 80); y1, y2 = 470, 580; x0 = 470
    n = max(0, int((t - TL.T_CMD) * 15)) if t >= TL.T_CMD else 0
    typed = TL.MSG_CMD[:n]; w1 = "Повторить"
    l1, l2 = "> " + typed[:len(w1)], typed[len(w1) + 1:]
    d.text((x0, y1), l1, font=fC, fill=(150, 255, 200, 255), anchor="lm")
    if l2: d.text((x0 + d.textlength("> ", font=fC), y2), l2, font=fC, fill=(150, 255, 200, 255), anchor="lm")
    if n < len(TL.MSG_CMD) and int(t * 3) % 2 == 0:
        x = (x0 + d.textlength("> " + l2, font=fC) if l2 else x0 + d.textlength(l1, font=fC)) + 8; yy = y2 if l2 else y1
        d.rectangle([x, yy - 40, x + 36, yy + 40], fill=(150, 255, 200, 255))
    done = TL.T_CMD + len(TL.MSG_CMD) / 15
    if t >= done:
        k = min(1.0, (t - done) / 0.2)
        d.rectangle([x0 - 30, y1 - 60, MW - x0 + 60, y2 + 60], outline=(150, 255, 200, int(255 * k)), width=5)
        cx, cy, r = MW // 2, 760, 50; ang = (t - done) * 400
        d.arc([cx - r, cy - r, cx + r, cy + r], ang, ang + 290, fill=(150, 255, 200, 255), width=14)
    _scan(im, 50); return im


def draw_live12(t):
    """the side monitor: dark (static) until T_SIDE_ON; then the live feed of flat 47's kitchen — ELENA_APARTMENT at the table (her mouth from
    the VO in the last line); «● Прямой эфир» (T_LIVE), «Квартира 47» (T_FLAT); «Обнаружены две Елены» stamped over it in red (T_TWO)"""
    TL = _TL()
    im = Image.new("RGBA", (MW, MH), (3, 4, 6, 255)); d = ImageDraw.Draw(im)
    if t < TL.T_SIDE_ON:
        return im
    a = t - TL.T_SIDE_ON
    lip = VIDEO_LIP(t) if any(x <= t < y for x, y in TL.LIPW_FEED) else "neutral"
    kk = ("flatfeed", lip, MW, MH)
    if kk not in _IMG: _IMG[kk] = photo(f"E12_flatfeed_{lip}", (MW, MH))
    im.alpha_composite(ImageEnhance.Color(_IMG[kk]).enhance(0.75).convert("RGBA"))
    _scan(im, 50); c = ImageDraw.Draw(im); cx = MW // 2
    if t >= TL.T_LIVE:
        al = ease((t - TL.T_LIVE) / 0.2)
        if int(t * 2) % 2 == 0: c.ellipse([420, 72, 458, 110], fill=(255, 40, 40, int(255 * al)))
        c.text((474, 91), TL.MSG_LIVE, font=F("Rubik-Bold.ttf", 50), fill=(255, 255, 255, int(240 * al)), anchor="lm")
    if t >= TL.T_FLAT:
        al = ease((t - TL.T_FLAT) / 0.2)
        c.rounded_rectangle([cx - 190, 150, cx + 190, 222], 16, fill=(0, 0, 0, int(170 * al)))
        c.text((cx, 186), TL.MSG_FLAT, font=F("Rubik-Bold.ttf", 50), fill=(255, 255, 255, int(240 * al)), anchor="mm")
    if t >= TL.T_TWO:
        al = min(1.0, (t - TL.T_TWO) / 0.06); sc = 1.0 + 0.3 * max(0.0, 1 - (t - TL.T_TWO) / 0.15); on = int(t * 3) % 2 == 0
        lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); l = ImageDraw.Draw(lay)
        l.rounded_rectangle([210, MH - 330, MW - 210, MH - 90], 30, fill=(40, 0, 4, int(225 * al)), outline=(255, 70, 60, int(255 * al) if on else int(150 * al)), width=8)
        fW = F("Rubik-Bold.ttf", int(84 * sc))
        l.text((cx, MH - 255), "Обнаружены", font=fW, fill=(255, 80, 70, int(255 * al)), anchor="mm", stroke_width=5, stroke_fill=(40, 0, 3, 255))
        l.text((cx, MH - 160), "две Елены", font=fW, fill=(255, 80, 70, int(255 * al)), anchor="mm", stroke_width=5, stroke_fill=(40, 0, 3, 255))
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10))); im.alpha_composite(lay)
    if a < 0.4 or 0 <= t - TL.T_TWO < 0.2: draw_glitch(im, t)
    return im



# ---------------------------------------------------------------- EP13 additions «ПОСЛЕДНЯЯ КОПИЯ»
# Monitor states (MW x MH, drawn on the turned computer / the side monitor) and phone states (W x H, kind "ui13").
# Everything readable sits in the middle half of the monitor's width (the vertical frame sees the screen's centre).
M13 = ("live13", "panel13", "face13", "warn13", "choice13", "voice13", "count13", "msg13", "self13")
RED13, CYAN13 = (255, 70, 60), (120, 235, 255)


def _glitch13(im, t, n=10):
    import random
    r = random.Random(int(t * 15) + 13); a = im.copy(); w, h = im.size
    for _ in range(n):
        y0 = r.randint(0, h - 60); hh = r.randint(8, max(9, h // 12)); dx = r.randint(-w // 14, w // 14)
        im.paste(a.crop((0, y0, w, y0 + hh)), (dx, y0))
    im.alpha_composite(Image.new("RGBA", (w, h), (r.randint(0, 90), 0, r.randint(0, 60), r.randint(20, 70))))


def _glow_text(im, lay, blur=12):
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur))); im.alpha_composite(lay)


def _feed13(name, size):
    k = ("f13", name, size)
    if k not in _IMG: _IMG[k] = photo(name, size)
    return _IMG[k]


def draw_live13(t):
    """the side monitor: flat 47's live feed — ELENA_0 at the kitchen table (lip-synced in her lines and in «Не верь мне»); her hand comes
    up from T_FEED_RAISE0 and the red «0» is on her wrist from T_ZERO; «● Прямой эфир», «Квартира 47» (as in EP12)"""
    TL = _TL()
    lip = VIDEO_LIP(t) if any(x <= t < y for x, y in TL.LIPW_FEED) else "neutral"
    if t < TL.T_FEED_RAISE0: name = f"E13_feed_{lip}"
    elif t < TL.T_FEED_RAISE1: name = "E13_feedr0"
    elif t < TL.T_ZERO: name = "E13_feedr5"
    else: name = f"E13_feedz_{lip}"
    im = Image.new("RGBA", (MW, MH), (3, 4, 6, 255))
    im.alpha_composite(ImageEnhance.Color(_feed13(name, (MW, MH))).enhance(0.8).convert("RGBA"))
    _scan(im, 50); c = ImageDraw.Draw(im); cx = MW // 2
    if int(t * 2) % 2 == 0: c.ellipse([420, 72, 458, 110], fill=(255, 40, 40, 255))
    c.text((474, 91), TL.MSG_LIVE, font=F("Rubik-Bold.ttf", 50), fill=(255, 255, 255, 240), anchor="lm")
    c.rounded_rectangle([cx - 190, 150, cx + 190, 222], 16, fill=(0, 0, 0, 170))
    c.text((cx, 186), TL.MSG_FLAT, font=F("Rubik-Bold.ttf", 50), fill=(255, 255, 255, 240), anchor="mm")
    if 0 <= t - TL.T_ZERO < 0.25: _glitch13(im, t, 6)
    return im


def _row13(c, y, text, on, sel, fsz=56):
    c.rounded_rectangle([330, y - 46, MW - 330, y + 46], 18, fill=(60, 8, 10, 230) if sel else (10, 24, 32, 220),
                        outline=RED13 + (255,) if sel else (70, 140, 170, 200), width=5 if sel else 3)
    if text: c.text((MW // 2, y), text, font=F("Rubik-Bold.ttf", fsz), fill=(255, 235, 230, int(255 * on)) if sel else (200, 230, 240, int(255 * on)), anchor="mm")
    else: c.rectangle([MW // 2 - 170, y - 9, MW // 2 + 170, y + 9], fill=(60, 110, 130, 255))


def draw_panel13(t):
    """the admin panel: the screen wakes (T_PANEL + 0.2) — «Администратор: 48», three locked rows; «Скрытая запись» lights red (T_HIDDEN);
    it opens (T_PLAY): the recording of the night road plays in the frame (REC)"""
    TL = _TL(); im, d = _bg_face(False); cx = MW // 2; a = t - TL.T_PANEL - 0.2
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    if a < 0:
        r = int(70 + 14 * math.sin(t * 6)); c.ellipse([cx - r, MH // 2 - r, cx + r, MH // 2 + r], outline=(140, 230, 255, 220), width=8)
        _glow_text(im, lay); _scan(im, 36); return im
    if t < TL.T_PLAY:
        k = ease(a / 0.35); x0 = int(MW * (1 - k) * 0.3)
        c.rounded_rectangle([300 + x0, 50, MW - 300 + x0, MH - 50], 30, outline=CYAN13 + (255,), width=6)
        c.text((cx + x0, 140), TL.MSG_ADMIN, font=F("Rubik-Bold.ttf", 64), fill=(225, 250, 255, int(255 * k)), anchor="mm")
        for i, y in enumerate((300, 430, 560, 690)):
            if a < 0.25 + i * 0.12: continue
            hid = i == 2 and t >= TL.T_HIDDEN
            _row13(c, y, TL.MSG_HIDDEN if hid else "", 1.0, hid)
        _glow_text(im, lay)
        if t >= TL.T_HIDDEN and int(t * 4) % 2 == 0:
            ImageDraw.Draw(im).polygon([(MW // 2 + 250, 535), (MW // 2 + 250, 585), (MW // 2 + 290, 560)], fill=RED13 + (255,))
        if a < 0.3 or 0 <= t - TL.T_HIDDEN < 0.2: _glitch13(im, t, 6)
        _scan(im, 36); return im
    # the recording plays on the screen
    im = Image.new("RGBA", (MW, MH), (3, 4, 6, 255)); im.alpha_composite(ImageEnhance.Color(_feed13("E13_recfeed", (MW, MH))).enhance(0.55).convert("RGBA"))
    _scan(im, 50); c = ImageDraw.Draw(im)
    if int(t * 2) % 2 == 0: c.ellipse([cx - 360, 70, cx - 318, 112], fill=(255, 40, 40, 255))
    c.text((cx - 300, 91), "REC", font=F("Rubik-Bold.ttf", 54), fill=(255, 255, 255, 240), anchor="lm")
    c.text((cx + 340, 91), f"23:48:{12 + int(t - TL.T_PLAY):02d}", font=F("Rubik-Medium.ttf", 46), fill=(255, 255, 255, 230), anchor="rm")
    if t - TL.T_PLAY < 0.35: _glitch13(im, t)
    return im


def draw_face13(t):
    """the original's face on the turned screen: still, eyes on ALEX_48; the smile from T_SMILE; the mouth from the VO in his line"""
    TL = _TL(); im, d = _bg_face(False)
    mouth = VIDEO_LIP(t) if any(x <= t < y for x, y in TL.LIPW_UI) else "neutral"
    mood = "smirk" if t >= TL.T_SMILE else None
    px = 50; fc = _face_variant("open", mouth, px, mood).convert("RGBA"); fx, fy = (MW - fc.width) // 2, 60
    im.alpha_composite(fc, (fx, fy))
    im.alpha_composite(Image.new("RGBA", (MW, MH), (90, 200, 230, 28))); _scan(im, 46)
    if 0 <= t - TL.T_SMILE < 0.25: _glitch13(im, t, 5)
    return im


def _bg_red():
    im = Image.new("RGBA", (MW, MH), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    for y in range(0, MH, 2):
        k = y / MH; d.line([(0, y), (MW, y)], fill=(int(46 + 30 * k), int(4 + 4 * k), int(6 + 5 * k), 255))
    return im, d


def _typed13(text, t, t0, cps=28): return text[:max(0, int((t - t0) * cps))] if t >= t0 else ""


def draw_warn13(t):
    """the system's warning (the room goes red): a red alarm frame and a «!» (T_WARN); «Обнаружена / последняя копия» typed (T_LAST);
    «Номер сорок восемь» (T_N48) and a big «48» stamped under it"""
    TL = _TL()
    if t < TL.T_WARN: return draw_face13(t)
    im, d = _bg_red(); cx = MW // 2; on = int(t * 3) % 2 == 0
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    c.rounded_rectangle([300, 50, MW - 300, MH - 50], 30, outline=RED13 + ((255,) if on else (150,)), width=8)
    if t < TL.T_LAST:
        sc = 1.0 + 0.25 * max(0.0, 1 - (t - TL.T_WARN) / 0.2)
        c.polygon([(cx, 300 - int(150 * sc)), (cx - int(170 * sc), 300 + int(120 * sc)), (cx + int(170 * sc), 300 + int(120 * sc))], outline=RED13 + (255,), width=12)
        c.text((cx, 330), "!", font=F("Rubik-Bold.ttf", int(170 * sc)), fill=RED13 + (255,), anchor="mm")
    else:
        f = F("Rubik-Bold.ttf", 84); typed = _typed13(TL.MSG_LAST, t, TL.T_LAST, 30); w1 = "Обнаружена"
        c.text((cx, 160), typed[:len(w1)], font=f, fill=(255, 225, 220, 255), anchor="mm")
        if len(typed) > len(w1) + 1: c.text((cx, 265), typed[len(w1) + 1:], font=f, fill=(255, 225, 220, 255), anchor="mm")
    if t >= TL.T_N48:
        al = min(1.0, (t - TL.T_N48) / 0.08); sc = 1.0 + 0.35 * max(0.0, 1 - (t - TL.T_N48) / 0.15)
        c.text((cx, 400), TL.MSG_N48, font=F("Rubik-Bold.ttf", 60), fill=RED13 + (int(255 * al),), anchor="mm")
        c.text((cx, 640), "48", font=F("Rubik-Bold.ttf", int(240 * sc)), fill=RED13 + (int(255 * al),), anchor="mm", stroke_width=8, stroke_fill=(40, 0, 3, 255))
    _glow_text(im, lay)
    if 0 <= t - TL.T_WARN < 0.35 or 0 <= t - TL.T_N48 < 0.2: _glitch13(im, t)
    _scan(im, 36); return im


def _choice_layer(t, dim=1.0):
    TL = _TL(); cx = MW // 2
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    c.rounded_rectangle([300, 50, MW - 300, MH - 50], 30, outline=(255, 110, 100, int(200 * dim)), width=6)
    fB = F("Rubik-Bold.ttf", 54)
    if t >= TL.T_OPT1:
        a = ease((t - TL.T_OPT1) / 0.25)
        c.rounded_rectangle([cx - 400, 150, cx + 400, 300], 26, fill=(14, 30, 40, int(235 * a * dim)), outline=(140, 230, 255, int(255 * a * dim)), width=6)
        c.text((cx, 225), TL.MSG_OPT1, font=fB, fill=(225, 250, 255, int(255 * a * dim)), anchor="mm")
    if t >= TL.T_OPT2:
        a = ease((t - TL.T_OPT2) / 0.25)
        c.rounded_rectangle([cx - 400, 360, cx + 400, 510], 26, fill=(40, 6, 8, int(235 * a * dim)), outline=(255, 120, 110, int(255 * a * dim)), width=6)
        c.text((cx, 435), TL.MSG_OPT2, font=fB, fill=(255, 235, 230, int(255 * a * dim)), anchor="mm")
    if t >= TL.T_PRICE_LBL:                                  # «Под вторым вариантом загорелась надпись»: the strip under it lights
        on = 0.6 + 0.4 * (int(t * 3) % 2 == 0)
        c.rounded_rectangle([cx - 400, 545, cx + 400, 665], 22, fill=(70, 0, 4, int(200 * dim)), outline=RED13 + (int(255 * on * dim),), width=5)
        if t >= TL.T_PRICE:
            a = min(1.0, (t - TL.T_PRICE) / 0.08); sc = 1.0 + 0.3 * max(0.0, 1 - (t - TL.T_PRICE) / 0.15)
            c.text((cx, 605), TL.MSG_PRICE, font=F("Rubik-Bold.ttf", int(58 * sc)), fill=(255, 90, 80, int(255 * a * dim)), anchor="mm", stroke_width=4, stroke_fill=(40, 0, 3, 255))
    return lay


def draw_choice13(t):
    """the new choice: «Удалить все копии» (T_OPT1) / «Сохранить последнюю» (T_OPT2); the strip under the second lights (T_PRICE_LBL) and
    reads «Цена — жизнь Елены» (T_PRICE)"""
    TL = _TL(); im, d = _bg_red()
    _glow_text(im, _choice_layer(t))
    if 0 <= t - TL.T_CHOICE < 0.35 or 0 <= t - TL.T_PRICE < 0.2: _glitch13(im, t, 6)
    _scan(im, 36); return im


def _wave13(c, t, y, col, amp=90, w=760):
    TL = _TL(); env = TL._envelope(); f = int(t * TL.FPS); cx = MW // 2
    peak = sorted(env)[int(len(env) * 0.97)] or 1
    for i in range(38):
        e = env[max(0, min(len(env) - 1, f - 19 + i))] / peak; h = int(8 + amp * min(1.2, e) * (0.6 + 0.4 * math.sin(i * 1.7 + t * 9)))
        x = cx - w // 2 + i * (w // 38); c.rectangle([x, y - h, x + 12, y + h], fill=col)


def draw_voice13(t):
    """the system speaks in the original's voice (T_VOICE): the choice dims, his face comes up through it (red, ghosted) and speaks
    «Выбор уже сделан» (mouth from the VO); a voice waveform along the bottom"""
    TL = _TL(); im, d = _bg_red()
    if t < TL.T_VOICE: return draw_choice13(t)
    a = ease((t - TL.T_VOICE) / 0.5)
    _glow_text(im, _choice_layer(t, dim=1 - 0.75 * a))
    mouth = VIDEO_LIP(t) if any(x <= t < y for x, y in TL.LIPW_UI) else "neutral"
    fc = _face_variant("open", mouth, 50, "smirk").convert("RGBA")
    tint = Image.new("RGBA", fc.size, (255, 60, 50, 110)); fc.alpha_composite(tint); fc.putalpha(int(205 * a))
    im.alpha_composite(fc, ((MW - fc.width) // 2, 60))
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); _wave13(ImageDraw.Draw(lay), t, MH - 120, (255, 110, 100, int(230 * a)), amp=60)
    _glow_text(im, lay, 8)
    if 0 <= t - TL.T_VOICE < 0.4 or 0 <= t - 87.9 < 0.15: _glitch13(im, t)
    _scan(im, 40); return im


def draw_count13(t):
    """the countdown (T_COUNT): a red ring closes round the centre; from «Десять» the number on each spoken word (TICKS), the ring
    restarting each second"""
    TL = _TL(); im, d = _bg_red(); cx, cy = MW // 2, MH // 2 + 10
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    c.rounded_rectangle([300, 50, MW - 300, MH - 50], 30, outline=RED13 + (220,), width=6)
    n = TL.tick_at(t); r = 330
    if n is None:
        k = ease((t - TL.T_COUNT) / 1.2); c.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + int(360 * k), fill=RED13 + (255,), width=22)
    else:
        t0 = max(tt for tt, v in TL.TICKS if t >= tt); k = min(1.0, (t - t0) / 1.0)
        c.arc([cx - r, cy - r, cx + r, cy + r], -90 + int(360 * k), 270, fill=RED13 + (255,), width=22)
        sc = 1.0 + 0.3 * max(0.0, 1 - (t - t0) / 0.15)
        c.text((cx, cy), str(n), font=F("Rubik-Bold.ttf", int(380 * sc)), fill=(255, 90, 80, 255), anchor="mm", stroke_width=10, stroke_fill=(40, 0, 3, 255))
    _glow_text(im, lay, 14)
    if n is not None and t - max(tt for tt, v in TL.TICKS if t >= tt) < 0.12: _glitch13(im, t, 5)
    _scan(im, 36); return im


def draw_msg13(t):
    """the system speaks (T_SYS): a voice waveform; «Для остановки игры» (T_MSG1) / «удалите её создателя» (T_MSG2) typed in red;
    the timer, frozen on 00:01, blinks in the corner"""
    TL = _TL(); im, d = _bg_red(); cx = MW // 2
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    c.rounded_rectangle([300, 50, MW - 300, MH - 50], 30, outline=RED13 + (230,), width=6)
    _wave13(c, t, MH - 150, (255, 110, 100, 220), amp=50, w=700)
    c.text((cx, 220), _typed13(TL.MSG_STOP1, t, TL.T_MSG1, 24), font=F("Rubik-Bold.ttf", 76), fill=(255, 225, 220, 255), anchor="mm")
    l2 = _typed13(TL.MSG_STOP2, t, TL.T_MSG2, 22)
    if l2:
        w1 = "удалите её"; c.text((cx, 360), l2[:len(w1)], font=F("Rubik-Bold.ttf", 92), fill=(255, 80, 70, 255), anchor="mm", stroke_width=5, stroke_fill=(40, 0, 3, 255))
        if len(l2) > len(w1) + 1: c.text((cx, 480), l2[len(w1) + 1:], font=F("Rubik-Bold.ttf", 92), fill=(255, 80, 70, 255), anchor="mm", stroke_width=5, stroke_fill=(40, 0, 3, 255))
    if int(t * 3) % 2 == 0: c.text((MW - 340, 110), "00:01", font=F("Rubik-Bold.ttf", 54), fill=RED13 + (255,), anchor="rm")
    _glow_text(im, lay)
    if 0 <= t - TL.T_MSG2 < 0.2: _glitch13(im, t, 6)
    _scan(im, 36); return im


def draw_self13(t):
    """«Все экраны одновременно показали моё лицо»: ALEX_48 as the computer's camera sees him, red, live (from T_FACES)"""
    TL = _TL()
    if t < TL.T_FACES: return draw_msg13(t)
    im = Image.new("RGBA", (MW, MH), (3, 4, 6, 255))
    im.alpha_composite(ImageEnhance.Color(_feed13("E13_selfcam", (MW, MH))).enhance(0.85).convert("RGBA"))
    _scan(im, 46)
    if t - TL.T_FACES < 0.3: _glitch13(im, t)
    return im


# phone states (720 x 1540)
def draw_brakes13(im, t):
    """the original's second phone on the back seat: dark, a pulsing dot; the command card «Отключить тормоза» (T_CMDON) with a switch;
    his thumb flips it (T_TOGGLE): the switch goes red, a red brake warning icon lights"""
    TL = _TL(); d = ImageDraw.Draw(im)
    for y in range(H): k = y / H; d.line([(0, y), (W, y)], fill=(int(8 + 8 * k), int(10 + 8 * k), int(16 + 12 * k), 255))
    if t < TL.T_CMDON:
        r = int(26 + 8 * math.sin(t * 6)); d.ellipse([W // 2 - r, 700 - r, W // 2 + r, 700 + r], fill=(120, 170, 255, 200)); return
    a = ease((t - TL.T_CMDON) / 0.2); on = t >= TL.T_TOGGLE
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c = ImageDraw.Draw(lay)
    c.rounded_rectangle([40, 380, W - 40, 1150], 46, fill=(40, 6, 8, int(235 * a)) if on else (14, 22, 34, int(235 * a)), outline=(255, 70, 60, int(255 * a)) if on else (130, 180, 255, int(255 * a)), width=6)
    c.text((W // 2, 520), "Отключить", font=F("Rubik-Bold.ttf", 96), fill=(255, 240, 235, int(255 * a)), anchor="mm")
    c.text((W // 2, 640), "тормоза", font=F("Rubik-Bold.ttf", 96), fill=(255, 240, 235, int(255 * a)), anchor="mm")
    k = ease((t - TL.T_TOGGLE) / 0.15) if on else 0.0
    c.rounded_rectangle([W // 2 - 150, 760, W // 2 + 150, 900], 70, fill=(int(60 + 170 * k), int(70 - 40 * k), int(90 - 60 * k), int(255 * a)))
    kx = int(W // 2 - 80 + 160 * k); c.ellipse([kx - 58, 772, kx + 58, 888], fill=(245, 245, 250, int(255 * a)))
    if on:                                                  # the brake warning symbol: a circle with «!» between two arcs
        cx, cy = W // 2, 1030; c.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=(255, 70, 60, 255), width=10)
        c.text((cx, cy), "!", font=F("Rubik-Bold.ttf", 90), fill=(255, 70, 60, 255), anchor="mm")
        c.arc([cx - 95, cy - 95, cx + 95, cy + 95], 120, 240, fill=(255, 70, 60, 255), width=10); c.arc([cx - 95, cy - 95, cx + 95, cy + 95], -60, 60, fill=(255, 70, 60, 255), width=10)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10))); im.alpha_composite(lay)
    if 0 <= t - TL.T_TOGGLE < 0.2: draw_glitch(im, t)


def draw_warnp13(im, t):
    """every phone on the table: red alarm, a big «48» (with the warning line small under it)"""
    d = ImageDraw.Draw(im)
    for y in range(H): k = y / H; d.line([(0, y), (W, y)], fill=(int(90 + 60 * k), int(6 + 4 * k), int(10 + 6 * k), 255))
    on = int(t * 3) % 2 == 0
    d.rounded_rectangle([40, 300, W - 40, 1240], 50, outline=(255, 90, 80, 255 if on else 140), width=10)
    d.text((W // 2, 700), "48", font=F("Rubik-Bold.ttf", 360), fill=(255, 235, 230, 255), anchor="mm")
    d.text((W // 2, 1000), "последняя", font=F("Rubik-Bold.ttf", 74), fill=(255, 220, 215, 255), anchor="mm")
    d.text((W // 2, 1090), "копия", font=F("Rubik-Bold.ttf", 74), fill=(255, 220, 215, 255), anchor="mm")


def draw_countp13(im, t):
    TL = _TL(); d = ImageDraw.Draw(im)
    for y in range(H): k = y / H; d.line([(0, y), (W, y)], fill=(int(70 + 50 * k), int(4 + 4 * k), int(8 + 6 * k), 255))
    n = TL.tick_at(t)
    if n is not None: d.text((W // 2, H // 2), str(n), font=F("Rubik-Bold.ttf", 560), fill=(255, 225, 220, 255), anchor="mm")


def draw_selfp13(im, t):
    TL = _TL()
    if t < TL.T_FACES: draw_countp13(im, t); return
    k = ("selfp", W, H)
    if k not in _IMG:
        src = photo("E13_selfcam", (MW, MH)); cw = int(src.height * W / H); x0 = (src.width - cw) // 2
        _IMG[k] = src.crop((x0, 0, x0 + cw, src.height)).resize((W, H), Image.LANCZOS)
    im.alpha_composite(_IMG[k].convert("RGBA")); _scan(im, 40)

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import timeline_ep13 as TL
    CLOCK = LOCK_CLOCK = getattr(TL, "PHONE_CLOCK", CLOCK)
    out = os.path.join(ROOT, "renders", "ui_preview"); os.makedirs(out, exist_ok=True)
    for name, els in TL.PHONE.items():  # preview every phone state just after its last element appears
        draw_screen(els, max(t for t, _ in els) + 0.6).save(os.path.join(out, f"{name}.png"))
    print("wrote", len(TL.PHONE), "previews to", out)
