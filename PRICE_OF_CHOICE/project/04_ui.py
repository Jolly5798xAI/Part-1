#!/usr/bin/env python3
"""Render the phone-interface inserts (final assets, exact Cyrillic) and the screen plates for compositing.

Outputs
  assets/ui/<SHOT>.mp4            full-frame UI shots, 1080x1920, 24 fps, exact frame count from the timeline
  assets/ui/screens/*.png         static screen contents (1080x2340) to composite onto the live-action phone shots
One visual language for the whole series: dark messenger, sender «Без номера», cold accent, red only for threats.
"""
import math, subprocess, pathlib, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, out_t, word_t, timeline
import shots as S

FONT_DIR = ROOT / "assets/fonts"
def F(name, size): return ImageFont.truetype(str(FONT_DIR / name), size)
REG, MED, SEMI, BOLD = "Inter-Regular.otf", "Inter-Medium.otf", "Inter-SemiBold.otf", "Inter-Bold.otf"
DISP, DISPB = "InterDisplay-SemiBold.otf", "InterDisplay-Bold.otf"

BG0, BG1 = (6, 8, 12), (13, 17, 24)
TXT, SUB, BUB = (233, 237, 243), (128, 138, 152), (27, 32, 42)
ACC, OK, RED = (143, 184, 255), (110, 205, 170), (232, 72, 77)
W, H = 1080, 1920

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def appear(t, t0, d=0.22): return ease((t - t0) / d) if t >= t0 else 0.0

def base(h=H, clock="02:47"):
    im = Image.new("RGB", (W, h), BG0)
    d = ImageDraw.Draw(im)
    for y in range(h):  # vertical gradient
        k = y / h
        d.line([(0, y), (W, y)], fill=tuple(int(BG0[i] + (BG1[i] - BG0[i]) * (1 - abs(k - 0.35) * 1.4)) for i in range(3)))
    d.text((70, 52), clock, font=F(SEMI, 40), fill=TXT)
    for i in range(4):  # signal bars
        bh = 12 + i * 7
        d.rounded_rectangle([W - 250 + i * 18, 88 - bh, W - 238 + i * 18, 88], 3, fill=TXT if i < 3 else SUB)
    d.rounded_rectangle([W - 150, 58, W - 80, 88], 7, outline=TXT, width=3)
    d.rounded_rectangle([W - 145, 63, W - 112, 83], 4, fill=TXT)  # low-ish battery
    d.rectangle([W - 78, 67, W - 73, 79], fill=TXT)
    return im

def header(d, y=150):
    d.text((60, y + 18), "‹", font=F(REG, 80), fill=ACC)
    d.ellipse([140, y + 10, 240, y + 110], fill=(42, 48, 59))
    d.text((190, y + 60), "?", font=F(SEMI, 56), fill=SUB, anchor="mm")
    d.text((268, y + 20), "Без номера", font=F(SEMI, 46), fill=TXT)
    d.text((268, y + 76), "номер скрыт", font=F(REG, 32), fill=SUB)
    d.line([(0, y + 145), (W, y + 145)], fill=(30, 35, 44), width=2)

def wrap(text, font, maxw):
    out, line = [], ""
    for w in text.split(" "):
        t = (line + " " + w).strip()
        if font.getlength(t) <= maxw: line = t
        else: out.append(line); line = w
    out.append(line)
    return out

LAST_BOX = []
FIRST_BOX = []

def bubble(im, y, text, a, color=TXT, border=None, font=None, stamp="02:47"):
    """incoming bubble at y, alpha a (0..1, slides up 30px). returns bottom y"""
    if a <= 0: return y
    font = font or F(MED, 54)
    lines = wrap(text, font, 800)
    lh = int(font.size * 1.28)
    bw = max(font.getlength(l) for l in lines) + 90
    bh = lh * len(lines) + 92
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    oy = int(30 * (1 - a))
    x0, y0 = 60, y + oy
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 40, fill=BUB + (int(255 * a),),
                        outline=(border + (int(255 * a),)) if border else None, width=4 if border else 0)
    for i, l in enumerate(lines):
        d.text((x0 + 45, y0 + 34 + i * lh), l, font=font, fill=color + (int(255 * a),))
    d.text((x0 + bw - 30, y0 + bh - 22), stamp, font=F(REG, 28), fill=SUB + (int(255 * a),), anchor="rb")
    im.paste(layer, (0, 0), layer)
    LAST_BOX[:] = [x0, y0, x0 + bw, y0 + bh]
    return y + bh + 26

def timer_card(im, y, remaining, total, a, label, danger=False, big=132):
    if a <= 0: return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    col = RED if danger else ACC
    al = int(255 * a)
    d.rounded_rectangle([60, y, W - 60, y + 260], 44, fill=(18, 22, 30, al), outline=(40, 46, 58, al), width=2)
    d.text((110, y + 34), label, font=F(MED, 36), fill=SUB + (al,))
    r = max(0, remaining)
    c = int(math.ceil(r - 1e-6)) if r > 0 else 0
    s = f"{c // 60:02d}:{c % 60:02d}"
    d.text((110, y + 84), s, font=F(DISPB, big), fill=col + (al,))
    cx, cy, rr = W - 200, y + 130, 84  # progress ring
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(40, 46, 58, al), width=14)
    frac = r / total
    d.arc([cx - rr, cy - rr, cx + rr, cy + rr], -90, -90 + 360 * frac, fill=col + (al,), width=14)
    im.paste(layer, (0, 0), layer)

def banner(im, y, title, line1, line2, a):
    if a <= 0: return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    al = int(255 * a); oy = int(-40 * (1 - a))
    d.rounded_rectangle([40, y + oy, W - 40, y + oy + 230], 44, fill=(30, 35, 45, int(235 * a)))
    d.rounded_rectangle([75, y + oy + 40, 165, y + oy + 130], 24, fill=OK + (al,))
    d.text((120, y + oy + 85), "$", font=F(BOLD, 58), fill=(10, 30, 22, al), anchor="mm")
    d.text((195, y + oy + 40), title, font=F(SEMI, 34), fill=SUB + (al,))
    d.text((W - 80, y + oy + 40), "сейчас", font=F(REG, 30), fill=SUB + (al,), anchor="ra")
    d.text((195, y + oy + 88), line1, font=F(SEMI, 48), fill=TXT + (al,))
    d.text((195, y + oy + 152), line2, font=F(REG, 36), fill=SUB + (al,))
    im.paste(layer, (0, 0), layer)

# ------------------------------------------------------------------ timing anchors (output seconds)
T = dict(
    t1_post=word_t("Поставь"), t1_time=word_t("Время"), t1_timer=word_t("60"),
    name=word_t("имя", after=14.0), t2_reward=word_t("Следующее"), t2_text=word_t("Не", after=23.0),
    t2_timer=word_t("три", after=24.0), warn=word_t("Откроешь"), open=word_t("Открой", after=68.0),
    left=word_t("Осталось"), ten=word_t("10", after=70.0),
)
TIMER1_START, TIMER2_START, TIMER3_START = T["t1_timer"], T["t2_timer"], T["ten"]

# ------------------------------------------------------------------ templates: f(t_out, t_local) -> Image
def tpl_bank_500(t, lt):
    im = base(); d = ImageDraw.Draw(im)
    d.text((W // 2, 420), "02:47", font=F(DISP, 230), fill=(200, 208, 220), anchor="mm")
    d.text((W // 2, 560), "пятница, 6 ноября", font=F(MED, 44), fill=SUB, anchor="mm")
    banner(im, 700, "БАНК", "Зачисление +500,00 $", "Счёт •• 4471", appear(lt, 0.04, 0.2))
    return im

def tpl_bank_500_full(t, lt):
    im = base(); d = ImageDraw.Draw(im)
    d.text((70, 170), "‹  Операции", font=F(MED, 42), fill=ACC)
    a = appear(lt, 0.25, 0.3)
    d.ellipse([W // 2 - 90, 330, W // 2 + 90, 510], fill=OK)
    d.text((W // 2, 420), "$", font=F(BOLD, 110), fill=(10, 30, 22), anchor="mm")
    d.text((W // 2, 590), "Зачисление", font=F(MED, 48), fill=SUB, anchor="mm")
    amt = 500 * ease((lt - 0.2) / 0.9) if lt > 0.2 else 0
    d.text((W // 2, 720), f"+{amt:,.2f} $".replace(",", " ").replace(".", ","), font=F(DISPB, 150), fill=TXT, anchor="mm")
    rows = [("Отправитель", "скрыт"), ("Назначение", "Задание 1 выполнено"), ("Счёт", "•• 4471"), ("Время", "02:48")]
    for i, (k, v) in enumerate(rows):
        al = appear(lt, 0.5 + i * 0.12)
        if al <= 0: continue
        y = 900 + i * 95
        d.text((90, y), k, font=F(REG, 40), fill=tuple(int(c * al) for c in SUB))
        d.text((W - 90, y), v, font=F(MED, 40), fill=tuple(int(c * al) for c in TXT), anchor="ra")
    return im

def chat(t, msgs, timer=None, clock="02:47", scroll=0):
    im = base(clock=clock); d = ImageDraw.Draw(im)
    header(d)
    y = 360 - scroll
    for text, t0, kw in msgs:
        y = bubble(im, y, text, appear(t, t0), **kw)
        if text == msgs[0][0]: FIRST_BOX[:] = LAST_BOX
    if timer:
        y0, start, total, label, danger = timer
        rem = total - max(0.0, t - start)
        timer_card(im, max(y + 10, y0), rem, total, appear(t, start - 0.05), label, danger)
    return im

def tpl_task1(t, lt):
    return chat(t, [("Алекс. ул.\u00a0Лесная,\u00a014, кв.\u00a037.", -99, {}),
                    ("Поставь полный стакан у\u00a0входа.", T["t1_post"] - 0.05, {}),
                    ("Время: 60 секунд.", T["t1_time"] - 0.05, {})],
                timer=(0, TIMER1_START, 60, "Осталось", False))

def tpl_name_address(t, lt):
    im = tpl_task1(t, lt)
    # highlight the first bubble (name + address) when «имя» is spoken
    a = appear(t, T["name"] - 0.1, 0.3)
    if a > 0:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x0, y0, x1, y1 = FIRST_BOX
        d.rounded_rectangle([x0 - 8, y0 - 8, x1 + 8, y1 + 8], 46, outline=ACC + (int(255 * a),), width=5)
        im.paste(layer, (0, 0), layer)
    return im

def tpl_task2_reward(t, lt):
    return chat(t, [("Задание 1 выполнено. +500\u00a0$", -99, {"color": OK, "stamp": "02:48"}),
                    ("Задание 2. Награда: 2\u00a0000\u00a0$", T["t2_reward"] + 0.15, {"stamp": "02:48"})], clock="02:48")

def tpl_task2(t, lt):
    return chat(t, [("Задание 1 выполнено. +500\u00a0$", -99, {"color": OK, "stamp": "02:48"}),
                    ("Задание 2. Награда: 2\u00a0000\u00a0$", -99, {"stamp": "02:48"}),
                    ("Не открывай дверь 3\u00a0минуты.", T["t2_text"] - 0.05, {"font": F(SEMI, 58), "stamp": "02:48"})],
                timer=(0, TIMER2_START, 180, "Не открывать", False), clock="02:48")

def tpl_warning(t, lt):
    return chat(t, [("Не открывай дверь 3\u00a0минуты.", -99, {"font": F(SEMI, 58), "stamp": "02:48"}),
                    ("ОТКРОЕШЬ — ПОГИБНЕШЬ.", T["warn"] - 0.08, {"color": RED, "border": RED, "font": F(BOLD, 64), "stamp": "02:49"})],
                timer=(0, TIMER2_START, 180, "Не открывать", True), clock="02:49", scroll=0)

def tpl_open_door(t, lt):
    return chat(t, [("ОТКРОЕШЬ — ПОГИБНЕШЬ.", -99, {"color": RED, "border": RED, "font": F(BOLD, 64), "stamp": "02:49"}),
                    ("Открой дверь.", T["open"] - 0.05, {"font": F(BOLD, 64), "stamp": "02:50"})],
                timer=(0, TIMER3_START, 10, "Осталось", True), clock="02:50")

TEMPLATES = dict(bank_500=tpl_bank_500, bank_500_full=tpl_bank_500_full, task1=tpl_task1, name_address=tpl_name_address,
                 task2_reward=tpl_task2_reward, task2=tpl_task2, warning=tpl_warning, open_door=tpl_open_door)
ZOOM = dict(bank_500=0.02, bank_500_full=0.02, task1=0.03, name_address=0.04, task2_reward=0.02, task2=0.05, warning=0.06, open_door=0.08)

def render_shot(seg):
    fn = TEMPLATES[seg["ui_template"]]
    out = ROOT / seg["source"]; out.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(S.FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    z = ZOOM.get(seg["ui_template"], 0.02)
    for i in range(seg["frames"]):
        t = (seg["frame_in"] + i) / S.FPS
        lt = i / S.FPS
        im = fn(t, lt)
        k = 1 + z * ease(lt / max(seg["duration"], 0.1))
        if k > 1.0005:
            cw, ch = W / k, H / k
            fy = 1250  # fixed point: content above grows upward, the subtitle zone below stays clear
            im = im.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, fy - fy / k, (W + cw) / 2, fy - fy / k + ch))
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    print("ui", seg["shot"], seg["frames"], "frames ->", seg["source"])

def screens():
    d = ROOT / "assets/ui/screens"; d.mkdir(parents=True, exist_ok=True)
    big = 1e9
    def save(name, im): im.save(d / name); print("screen", name)
    lock = base(); dr = ImageDraw.Draw(lock)
    dr.text((W // 2, 420), "02:47", font=F(DISP, 230), fill=(200, 208, 220), anchor="mm")
    banner(lock, 700, "Без номера", "Новое сообщение", "Нажмите, чтобы открыть", 1.0)
    save("screen_incoming.png", lock)
    save("screen_task1.png", chat(T["t1_timer"] + 1.5, [("Алекс. ул.\u00a0Лесная,\u00a014, кв.\u00a037.", -99, {}), ("Поставь полный стакан у\u00a0входа.", -99, {}), ("Время: 60 секунд.", -99, {})], timer=(0, T["t1_timer"], 60, "Осталось", False)))
    save("screen_bank.png", tpl_bank_500(0, 1.0))
    save("screen_warning.png", tpl_warning(T["warn"] + 1, 1))
    save("screen_open.png", tpl_open_door(T["open"] + 0.5, 1))

if __name__ == "__main__":
    tl = timeline()
    only = sys.argv[1:]
    for seg in tl["segments"]:
        if seg["kind"] == "ui" and (not only or seg["shot"] in only):
            render_shot(seg)
    if not only:
        screens()
