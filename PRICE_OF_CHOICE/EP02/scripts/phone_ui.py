"""Phone screen UI, drawn programmatically (never trust an image generator with Russian text).
draw_screen(state_elements, t) -> RGBA 720x1540 image of the phone screen at time t."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(ROOT, "effects", "fonts")
W, H = 720, 1540
_F = {}


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
            st, secs = data; sig.append(("timer", max(0, secs - int(t - st))))
        elif kind in ("push", "bubble", "bubble_red", "lock_text", "highlight") and age < 0.3: sig.append((kind, str(data), round(age, 2)))
        else: sig.append((kind, str(data)))
    # typing indicator disappears once the next bubble arrives
    return tuple(sig)


def draw_screen(elements, t):
    vis = visible(elements, t)
    kinds = [el[0] for _, el in vis]
    lock = "lock_glow" in kinds
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    # background
    for y in range(H):
        k = y / H
        c = (int(70 + 60 * k), int(8 + 6 * k), int(14 + 8 * k)) if lock else (int(12 + 6 * k), int(15 + 8 * k), int(22 + 12 * k))
        d.line([(0, y), (W, y)], fill=c + (255,))
    # status bar
    d.text((44, 26), "02:47", font=F("Rubik-Medium.ttf", 30), fill=(235, 235, 240))
    for i in range(4): d.rectangle([560 + i * 14, 50 - i * 6, 568 + i * 14, 56], fill=(235, 235, 240))
    d.rounded_rectangle([628, 30, 684, 56], 6, outline=(235, 235, 240), width=3); d.rectangle([634, 36, 652, 50], fill=(235, 235, 240))

    if lock:
        d.text((W // 2, 260), "02:48", font=F("Rubik-Medium.ttf", 150), fill=(255, 235, 235), anchor="mm")
        d.text((W // 2, 370), "пятница, 6 ноября", font=F("Rubik-Medium.ttf", 34), fill=(255, 200, 200), anchor="mm")
        for t0, (kind, data) in vis:
            if kind == "lock_text":
                a = ease((t - t0) / 0.2)
                # warning card
                card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
                cd.rounded_rectangle([40, 560, W - 40, 1060], 46, fill=(20, 4, 6, int(235 * a)), outline=(255, 60, 60, int(255 * a)), width=5)
                cd.text((W // 2, 640), "Номер скрыт", font=F("Rubik-Medium.ttf", 34), fill=(255, 140, 140, int(255 * a)), anchor="mm")
                lines = wrap(cd, data, F("Rubik-Bold.ttf", 92), W - 140)
                y = 820 - (len(lines) - 1) * 56
                for ln in lines:
                    cd.text((W // 2, y), ln, font=F("Rubik-Bold.ttf", 92), fill=(255, 255, 255, int(255 * a)), anchor="mm"); y += 112
                glow = card.filter(ImageFilter.GaussianBlur(14))
                im.alpha_composite(glow); im.alpha_composite(card)
        return im

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
    items = [(t0, el) for t0, el in vis if el[0] in ("bubble", "bubble_small", "bubble_red", "typing", "timer")]
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
        if kind == "timer":
            st, secs = data; rem = max(0, secs - int(t - st))
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
        ld.text((36 + bw - 20, y + dy + bh - 12), "02:47", font=F("Rubik-Medium.ttf", 22), fill=(150, 156, 175, int(255 * a)), anchor="rb")
        im.alpha_composite(layer)
        y += bh + 26
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
    import timeline_ep02 as TL
    out = os.path.join(ROOT, "renders", "ui_preview"); os.makedirs(out, exist_ok=True)
    for name, els in TL.PHONE.items():  # preview every phone state just after its last element appears
        draw_screen(els, max(t for t, _ in els) + 0.6).save(os.path.join(out, f"{name}.png"))
    print("wrote", len(TL.PHONE), "previews to", out)
