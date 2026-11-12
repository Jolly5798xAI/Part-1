"""Assemble an episode (EP11 config: timeline_ep11.py): illustrations + camera moves + phone UI + FX + subtitles + mixed audio -> MP4.

usage: python3 scripts/06_render_video.py [--preview START END] [--stills t1,t2,...] [--out FILE]
  default output: renders/EP11_PRICE_OF_CHOICE_FINAL.mp4 (1080x1920, 30 fps, H.264 + AAC)
"""
import os, sys, json, math, re, argparse, subprocess, functools
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline_ep11 as TL
import phone_ui
phone_ui.CLOCK = getattr(TL, "PHONE_CLOCK", phone_ui.CLOCK)
phone_ui.LOCK_CLOCK = getattr(TL, "PHONE_CLOCK", phone_ui.LOCK_CLOCK)
phone_ui.VIDEO_LIP = TL.lip_at                                                 # EP06: Alex's mouth on the recording

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ILL = os.path.join(ROOT, "scenes")                                            # EP11 renders
ILL_EP10 = os.path.join(os.path.dirname(ROOT), "EP10", "scenes")             # EP10 frames reused unchanged (read-only): E10_pov_end
ILL_EP09 = os.path.join(os.path.dirname(ROOT), "EP09", "scenes")             # EP09 frames reused unchanged (read-only): E9_cop_screen_close
ILL_EP08 = os.path.join(os.path.dirname(ROOT), "EP08", "scenes")             # EP08 frames reused unchanged (read-only): E8_rec_knife
ILL_EP07 = os.path.join(os.path.dirname(ROOT), "EP07", "scenes")             # EP07 frames reused unchanged (read-only): E7_mon, E7_feedm_*
ILL_EP06 = os.path.join(os.path.dirname(ROOT), "EP06", "scenes")             # EP06 frames reused unchanged (read-only)
ILL_EP05 = os.path.join(os.path.dirname(ROOT), "EP05", "scenes")             # EP05 frames reused unchanged (read-only)
ILL_EP04 = os.path.join(os.path.dirname(ROOT), "EP04", "scenes")             # EP04 frames reused unchanged (read-only)
ILL_EP03 = os.path.join(os.path.dirname(ROOT), "EP03", "scenes")             # EP03 frames reused unchanged (read-only)
ILL_EP02 = os.path.join(os.path.dirname(ROOT), "EP02", "illustrations")      # EP01/EP02 frames reused unchanged (read-only)
FONTS = os.path.join(os.path.dirname(ROOT), "EP02", "effects", "fonts")      # shared series fonts (read-only)
OW, OH, FPS = 1080, 1920, TL.FPS
META = json.load(open(os.path.join(ILL_EP02, "meta.json"))); META.update(json.load(open(os.path.join(ILL_EP03, "meta.json"))))
META.update(json.load(open(os.path.join(ILL_EP04, "meta.json"))))
META.update(json.load(open(os.path.join(ILL_EP05, "meta.json"))))
META.update(json.load(open(os.path.join(ILL_EP06, "meta.json"))))
META.update(json.load(open(os.path.join(ILL_EP07, "meta.json"))))
META.update(json.load(open(os.path.join(ILL_EP08, "meta.json"))))
META.update(json.load(open(os.path.join(ILL_EP09, "meta.json"))))
META.update(json.load(open(os.path.join(ILL_EP10, "meta.json"))))
META.update(json.load(open(os.path.join(ILL, "meta.json"))))
FONT_SUB = os.path.join(FONTS, "PTSerif-Bold.ttf")
FONT_UI = os.path.join(FONTS, "Rubik-Bold.ttf")


def still(name):
    for d in (ILL, ILL_EP10, ILL_EP09, ILL_EP08, ILL_EP07, ILL_EP06, ILL_EP05, ILL_EP04, ILL_EP03, ILL_EP02):
        p = os.path.join(d, name + ".png")
        if os.path.exists(p): return p
    raise FileNotFoundError(name)


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
        name = f"{shot.get('lips', 'S16_double_face')}_{v}"; return load(still(name)), name
    if "anim" in shot:
        fr = anim_frames(src)
        a0, a1 = shot["t"]
        st = shot.get("anim_start", a0); du = shot.get("anim_dur", a1 - st)
        k = min(1, max(0, (t - st) / du))
        f0, f1 = shot["anim"]
        idx = int(round(lerp(f0, f1, k) * (len(fr) - 1)))
        img = load(fr[idx])
        if "screens" in shot: img = screens_overlay(img, src, shot["screens"], t)
        if "monitor" in shot and src in META:                                 # EP11: a monitor UI on a turning screen (per-frame quads)
            fm = META[src].get("fm"); m = (fm[idx] if fm and idx < len(fm) else META[src]).get("screen")
            if m:
                area = 0.5 * sum(m[i][0] * m[(i + 1) % 4][1] - m[(i + 1) % 4][0] * m[i][1] for i in range(4))
                if area > 400:                                                # only once the screen faces the camera (front side, clockwise in image space)
                    key = (src, idx, "mon", shot["monitor"], round(t * 15))
                    if key not in _src_cache:
                        if len(_src_cache) > 12: _src_cache.clear()
                        _src_cache[key] = warp_ui(img, m, META[src]["w"], phone_ui.draw_monitor(shot["monitor"], t, 0), glow=0.45)
                    img = _src_cache[key]
        if "phone" in shot and src in META:                                   # EP07: phone UI on animated shots (per-frame quad if stored)
            fm = META[src].get("fm"); m = (fm[idx] if fm and idx < len(fm) else META[src])
            if m.get("screen"): img = phone_on(img, m["screen"], m.get("w", META[src]["w"]), shot["phone"], t, (src, idx))
        return img, src
    img = load(still(src))
    if "screens" in shot:
        key = (src, "screens", shot["screens"], phone_ui.signature(TL.PHONE[shot["screens"]], t))
        if key not in _src_cache:
            if len(_src_cache) > 12: _src_cache.clear()
            _src_cache[key] = screens_overlay(img, src, shot["screens"], t)
        img = _src_cache[key]
    if shot.get("mirror"): return mirror_text(img, src, t), src
    if shot.get("mtext"): return mirror_text7(img, src, shot["mtext"], t), src            # EP07
    if shot.get("monitors"): return monitors_overlay(img, src, shot["monitors"], t), src  # EP07
    if shot.get("monitor"):                                                               # EP07
        key = (src, "mon", shot["monitor"], round(t * 15))
        if key not in _src_cache:
            if len(_src_cache) > 12: _src_cache.clear()
            _src_cache[key] = warp_ui(img, META[src]["screen"], META[src]["w"], phone_ui.draw_monitor(shot["monitor"], t, 0, bool(shot.get("mcrack"))), glow=0.45)
        return _src_cache[key], src
    if "phone" in shot and src in META and "screen" in META[src]:
        els = TL.PHONE[shot["phone"]]
        key = (src, shot["phone"], shot.get("screens"), phone_ui.signature(els, t))
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


# ------------------------------------------------------------------ EP05: the same message on every phone of the table in room 204
def screens_overlay(img, src, state, t):
    """draws the chat state on each screen quad in META[src]['screens'] (bbox-local warps, so 35 screens stay cheap)"""
    quads = META.get(src, {}).get("screens")
    if not quads: return img
    if t < getattr(TL, "SCREENS_ON", {}).get(state, -1): return img                # EP10: the phones stay dark until they light up
    ui = phone_ui.draw_screen(TL.PHONE[state], t).convert("RGB")
    tint = getattr(TL, "SCREEN_TINT", {}).get(state, (120, 150, 215))          # EP06: the countdown glows red
    ui = Image.blend(ImageEnhance.Brightness(ui).enhance(1.6), Image.new("RGB", ui.size, tint), 0.42).convert("RGBA")
    small = ui.resize((ui.width // 3, ui.height // 3), Image.LANCZOS)
    sx = img.width / META[src]["w"]; sy = img.height / META[src]["h"]
    base = img.convert("RGBA")
    for q in quads:
        qq = [(x * sx, y * sy) for x, y in q]
        x0 = max(0, int(min(x for x, _ in qq)) - 1); y0 = max(0, int(min(y for _, y in qq)) - 1)
        x1 = min(img.width, int(max(x for x, _ in qq)) + 2); y1 = min(img.height, int(max(y for _, y in qq)) + 2)
        if x1 - x0 < 3 or y1 - y0 < 3: continue
        loc = [(x - x0, y - y0) for x, y in qq]
        coeffs = perspective_coeffs(loc, [(0, 0), (small.width, 0), (small.width, small.height), (0, small.height)])
        base.alpha_composite(small.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, coeffs, Image.BICUBIC), (x0, y0))
    # every screen throws light: a soft cold halo round each quad (screen glow, like the 3D emissive screens)
    glow = Image.new("RGB", (img.width // 6, img.height // 6)); gd = ImageDraw.Draw(glow)
    gcol = (255, 90, 80) if state in getattr(TL, "SCREEN_TINT", {}) else (150, 185, 255)
    for q in quads: gd.polygon([(x * sx / 6, y * sy / 6) for x, y in q], fill=gcol)
    glow = glow.filter(ImageFilter.GaussianBlur(7)).resize(img.size, Image.BILINEAR)
    out = np.asarray(base.convert("RGB"), np.float32) + np.asarray(glow, np.float32) * 0.55
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def light_gain(t):
    """EP05 blackout: the flat's light flickers and dies, then comes back flickering (TL.BLACKOUT)"""
    b = getattr(TL, "BLACKOUT", None)
    if not b: return 1.0
    f0, off, on, steady = b
    rg = np.random.default_rng(int(t * 30) + 77)
    if f0 <= t < off: return 1.0 if rg.random() < 0.55 else rg.uniform(0.15, 0.5)
    if off <= t < on: return 0.0
    if on <= t < steady: return rg.uniform(0.25, 1.0) if rg.random() < 0.7 else 0.05
    return 1.0


# ------------------------------------------------------------------ EP04: the message on the hall mirror
GLYPHS = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЫЭЮЯ"


def mirror_layer(t):
    """RGBA text card (same red alert style as the phone), mapped later onto the mirror glass.
    Before MIRROR['legible'] the letters are scrambled and faint (the message is forming), then it locks into the text."""
    M_ = TL.MIRROR; Wt, Ht = 620, 1000
    card = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    f = ImageFont.truetype(FONT_UI, 70)
    words = M_["text"].split(" ")
    legible = t >= M_["legible"]
    rg = np.random.default_rng(int(t * 15))
    a = 1.0 if legible else 0.25 + 0.5 * min(1, (t - M_["scramble"]) / (M_["legible"] - M_["scramble"]))
    y = Ht // 2 - 70
    for w in words:
        txt = w if legible else "".join(GLYPHS[rg.integers(len(GLYPHS))] if ch.isalpha() and rg.random() < 0.7 else ch for ch in w)
        tw = d.textlength(txt, font=f)
        while tw > Wt * 0.74 and f.size > 30: f = ImageFont.truetype(FONT_UI, f.size - 4); tw = d.textlength(txt, font=f)
        d.text((Wt / 2, y), txt, font=f, fill=(255, 60, 52, int(255 * a)), anchor="mm"); y += 110
    if legible and t - M_["legible"] < 0.5 and rg.random() < 0.35: a *= 0.4          # a short flicker as it locks in
    glow = card.filter(ImageFilter.GaussianBlur(18))
    out = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0)); out.alpha_composite(glow); out.alpha_composite(glow); out.alpha_composite(card)
    return out


_mir_cache = {}


def mirror_text(img, src, t):
    M_ = TL.MIRROR
    if t < M_["scramble"] or "quad" not in META.get(src, {}): return img
    key = (src, int(t * 15) if t < M_["legible"] + 0.5 else -1)
    if key in _mir_cache: return _mir_cache[key]
    if len(_mir_cache) > 8: _mir_cache.clear()
    card = mirror_layer(t)
    q = META[src]["quad"]; sx = img.width / META[src]["w"]; sy = img.height / META[src]["h"]
    quad = [(x * sx, y * sy) for x, y in q]
    # the mirror plane's local +x points along the wall; quad order is TL, TR, BR, BL in the mesh's frame
    coeffs = perspective_coeffs(quad, [(0, 0), (card.width, 0), (card.width, card.height), (0, card.height)])
    warped = card.transform(img.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    base = np.asarray(img, np.float32); w = np.asarray(warped, np.float32)
    al = w[..., 3:4] / 255
    out = base * (1 - 0.85 * al) + w[..., :3] * al * 1.05
    big = warped.resize((img.width // 8, img.height // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10)).resize(img.size, Image.BILINEAR)
    out += np.asarray(big, np.float32)[..., :3] * (np.asarray(big, np.float32)[..., 3:4] / 255) * 0.5   # red spill round the glass
    res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); _mir_cache[key] = res
    return res


# ------------------------------------------------------------------ EP07: UI on a quad (phones in animated shots, monitors), the mirror text
def warp_ui(img, quad, src_w, ui, glow=0.55):
    sc = img.width / src_w
    quad = [(x * sc, y * sc) for x, y in quad]
    coeffs = perspective_coeffs(quad, [(0, 0), (ui.width, 0), (ui.width, ui.height), (0, ui.height)])
    warped = ui.transform(img.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    g = warped.resize((img.width // 8, img.height // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)).resize(img.size, Image.BILINEAR)
    gl = np.asarray(g.convert("RGB"), np.float32) * (np.asarray(g.split()[3], np.float32)[..., None] / 255) * glow
    out = Image.fromarray(np.clip(np.asarray(img.convert("RGB"), np.float32) + gl, 0, 255).astype(np.uint8)).convert("RGBA")
    out.alpha_composite(warped)
    return out.convert("RGB")


def phone_on(img, quad, src_w, state, t, ck):
    els = TL.PHONE[state]
    key = (ck, state, phone_ui.signature(els, t))
    if key not in _src_cache:
        if len(_src_cache) > 12: _src_cache.clear()
        _src_cache[key] = warp_ui(img, quad, src_w, phone_ui.draw_screen(els, t))
    return _src_cache[key]


def monitors_overlay(img, src, state, t):
    """EP07: the wall of monitors — each screen quad gets its own monitor UI (nothing before they go red: the 3D static shows)"""
    if t < TL.T_MON_RED: return img
    key = (src, "mons", state, int((t - TL.T_MON_RED) * 6))
    if key in _src_cache: return _src_cache[key]
    if len(_src_cache) > 12: _src_cache.clear()
    out = img
    for i, q in enumerate(META[src].get("screens", [])):
        ui = phone_ui.draw_monitor(state, t + (0.17 * i if state == "wall" and t - TL.T_MON_RED > 0.3 else 0), i).resize((400, 245), Image.LANCZOS)
        out = warp_ui(out, q, META[src]["w"], ui, glow=0.3)
    _src_cache[key] = out
    return out


def mirror_text7(img, src, M_, t):
    """EP07: «Выбор сделан» on mirror 204 — scrambled red letters crawl over the glass, then lock into the words (upper third)"""
    if t < M_["scramble"] or "quad" not in META.get(src, {}): return img
    legible = t >= M_["legible"]
    key = (src, "m7", int(t * 15) if t < M_["legible"] + 0.5 else -1)
    if key in _mir_cache: return _mir_cache[key]
    if len(_mir_cache) > 8: _mir_cache.clear()
    Wt, Ht = 620, 1340
    card = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    f = ImageFont.truetype(FONT_UI, 96)
    rg = np.random.default_rng(int(t * 15))
    a = 1.0 if legible else 0.25 + 0.55 * min(1, (t - M_["scramble"]) / (M_["legible"] - M_["scramble"]))
    if legible and t - M_["legible"] < 0.5 and rg.random() < 0.35: a *= 0.4
    y = 250
    for w in M_["text"].split(" "):
        txt = w if legible else "".join(GLYPHS[rg.integers(len(GLYPHS))] if ch.isalpha() and rg.random() < 0.7 else ch for ch in w)
        d.text((Wt / 2, y), txt, font=f, fill=(255, 60, 52, int(255 * a)), anchor="mm"); y += 130
    glow = card.filter(ImageFilter.GaussianBlur(18))
    lay = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0)); lay.alpha_composite(glow); lay.alpha_composite(glow); lay.alpha_composite(card)
    q = META[src]["quad"]; sx = img.width / META[src]["w"]; sy = img.height / META[src]["h"]
    quad = [(x * sx, y * sy) for x, y in q]
    coeffs = perspective_coeffs(quad, [(0, 0), (Wt, 0), (Wt, Ht), (0, Ht)])
    warped = lay.transform(img.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    base = np.asarray(img, np.float32); w = np.asarray(warped, np.float32); al = w[..., 3:4] / 255
    out = base * (1 - 0.85 * al) + w[..., :3] * al * 1.05
    big = warped.resize((img.width // 8, img.height // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10)).resize(img.size, Image.BILINEAR)
    out += np.asarray(big, np.float32)[..., :3] * (np.asarray(big, np.float32)[..., 3:4] / 255) * 0.5
    res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); _mir_cache[key] = res
    return res


@functools.lru_cache(maxsize=1)
def cctv_layer():
    """EP07: the sister's feed as Alex sees it — scanlines, a hard vignette, REC corner marks (time drawn per frame)"""
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for y in range(0, OH, 4): d.line([(0, y), (OW, y)], fill=(0, 0, 0, 60))
    for (x, y, dx, dy) in [(46, 150, 1, 1), (OW - 46, 150, -1, 1), (46, OH - 260, 1, -1), (OW - 46, OH - 260, -1, -1)]:
        d.line([(x, y), (x + 80 * dx, y)], fill=(255, 255, 255, 170), width=5); d.line([(x, y), (x, y + 80 * dy)], fill=(255, 255, 255, 170), width=5)
    return lay


def cctv(a, t, fi):
    g = a.mean(axis=2, keepdims=True); a = (a * 0.55 + g * 0.45) * np.array([0.88, 1.0, 1.08], np.float32)
    rg = np.random.default_rng(fi * 13 + 5)
    if rg.random() < 0.07:
        y0 = int(rg.integers(0, OH - 120)); h = int(rg.integers(20, 110)); a = a.copy(); a[y0:y0 + h] = np.roll(a[y0:y0 + h], int(rg.integers(-50, 50)), axis=1) * 1.2
    return a


@functools.lru_cache(maxsize=1)
def rec_layer():
    """EP08: flat 47's security camera — scanlines, corner marks (REC + tomorrow's timestamp drawn per frame)"""
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for y in range(0, OH, 3): d.line([(0, y), (OW, y)], fill=(0, 0, 0, 70))
    for (x, y, dx, dy) in [(46, 150, 1, 1), (OW - 46, 150, -1, 1), (46, OH - 260, 1, -1), (OW - 46, OH - 260, -1, -1)]:
        d.line([(x, y), (x + 80 * dx, y)], fill=(255, 255, 255, 170), width=5); d.line([(x, y), (x, y + 80 * dy)], fill=(255, 255, 255, 170), width=5)
    return lay


def draw_rec(frame, t):
    frame.alpha_composite(rec_layer())
    d = ImageDraw.Draw(frame)
    if int(t * 2) % 2 == 0: d.ellipse([80, 186, 116, 222], fill=(255, 40, 40, 255))
    d.text((132, 204), "REC", font=ImageFont.truetype(FONT_UI, 44), fill=(255, 255, 255, 235), anchor="lm")
    d.text((OW - 90, 204), f"{TL.REC_STAMP}  02:54:{int(t) % 60:02d}", font=ImageFont.truetype(os.path.join(FONTS, "Rubik-Medium.ttf"), 40), fill=(255, 255, 255, 220), anchor="rm")


def draw_cctv(frame, t):
    frame.alpha_composite(cctv_layer())
    d = ImageDraw.Draw(frame)
    if int(t * 2) % 2 == 0: d.ellipse([80, 186, 116, 222], fill=(255, 40, 40, 255))
    d.text((132, 204), "REC", font=ImageFont.truetype(FONT_UI, 44), fill=(255, 255, 255, 235), anchor="lm")
    sec = int(t) % 60
    d.text((OW - 90, 204), f"02:54:{sec:02d}", font=ImageFont.truetype(os.path.join(FONTS, "Rubik-Medium.ttf"), 40), fill=(255, 255, 255, 220), anchor="rm")


# ------------------------------------------------------------------ camera + shake
@functools.lru_cache(maxsize=1)
def crack_layer():
    """EP09: the cracked phone screen (phone_ui's crack, the same seed as ALEX_49's phone) stretched over the whole frame"""
    im = Image.new("RGBA", (phone_ui.W, phone_ui.H), (0, 0, 0, 0)); phone_ui.draw_crack(im, 909)
    return im.resize((OW, OH), Image.BILINEAR)


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
    if "handshake_late" in fx and t >= getattr(TL, "T_TOMORROW", 1e9):                 # EP07: the frame jolts on «Завтрашний день»
        a = 1 + 6 * math.exp(-(t - TL.T_TOMORROW) * 6)
        dx += a * (4 * math.sin(t * 13.1) + 2 * math.sin(t * 29.7)); dy += a * 3 * math.cos(t * 11.3)
    return dx, dy, dz


def camera(img, shot, t):
    (cx0, cy0, z0), (cx1, cy1, z1) = shot["cam"]
    k = ease_io((t - shot["t"][0]) / (shot["t"][1] - shot["t"][0]))
    cx, cy, z = lerp(cx0, cx1, k), lerp(cy0, cy1, k), lerp(z0, z1, k)
    dx, dy, dz = shake_offset(shot, t); z *= 1 + dz
    W, H = img.size
    cw, ch = W / z, H / z
    if abs(W / H - OW / OH) > 0.01: cw = min(W, H * OW / OH) / z; ch = cw * OH / OW   # EP04: non-9:16 sources are cropped, not stretched
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
        buf += "!" if ch == "¡" else ch; bmodes.append(mode)   # EP05: ¡ = a literal "!"
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
            special = text in getattr(TL, "BIG_SUBS", ())
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
    if t < TL.COUNTDOWN[0] or t >= until: return                           # EP08: 00:10 shown (frozen, blinking) from COUNTDOWN[0]
    frozen = TL.COUNTDOWN[4] if len(TL.COUNTDOWN) > 4 else None          # EP06: the count freezes at the last second
    tt = min(t, frozen) if frozen else t
    rem = secs if tt < st else max(0, secs - int(tt - st))
    if tt < st and int(t * 3) % 2: return
    if frozen and t >= frozen and int(t * 4) % 2: return
    d = ImageDraw.Draw(frame)
    f = ImageFont.truetype(FONT_UI, 92)
    txt = f"00:{rem:02d}"
    pulse = 1.0 - ((t - st) % 1.0) if t >= st else 1.0
    col = (255, int(60 + 80 * (1 - pulse)), int(60 + 80 * (1 - pulse)), 255)
    d.rounded_rectangle([330, 150, 670, 290], 30, fill=(20, 0, 0, 170), outline=(255, 70, 70, 255), width=4)
    d.text((500, 220), txt, font=f, fill=col, anchor="mm")


def draw_endcard(frame, t):
    k = min(1, max(0, (t - (TL.CUT_TO_BLACK + 0.35)) / 0.5))
    if k <= 0: return
    d = ImageDraw.Draw(frame)
    f1 = ImageFont.truetype(FONT_SUB, 96); f2 = ImageFont.truetype(os.path.join(FONTS, "Rubik-Medium.ttf"), 40)
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
        if "glitch_late" in fx and t >= getattr(TL, "T_ERASE", 1e9) and rg.random() < 0.45:   # EP07: the deletion tears the picture
            sh = int(rg.integers(8, 30)); a = a.copy(); a[..., 0] = np.roll(a[..., 0], sh, axis=1); a[..., 2] = np.roll(a[..., 2], -sh, axis=1)
        if "cctv" in fx or "rec" in fx: a = cctv(a, t, fi)
        if "redglow_late" in fx and t >= getattr(TL, "T_ZERO_ON", 1e9):                       # EP09: the «0» burning lights the frame red
            p = min(1, (t - TL.T_ZERO_ON) / 1.2) * (0.6 + 0.4 * math.sin(t * 9)); a = a * np.array([1.0 + 0.3 * p, 1 - 0.12 * p, 1 - 0.12 * p], np.float32)
        if "memory" in fx:  # EP02: soft, hazy flashback insert
            bl = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), np.float32)
            a = a * 0.55 + bl * 0.45 + 10
        if "photo" in fx: gain *= 1.12  # EP02: flash-lit phone photo
        if "bedleak" in fx:  # EP03: the phone ringing behind the bedroom door pulses the light under it
            gain *= 1 + 0.07 * max(0, math.sin(t * 2 * math.pi * 1.6))
        if "dark" in fx: gain *= 0.9
        gain *= light_gain(t)
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
            if col == "black": a = a * (1 - 0.9 * k); continue                           # EP07: the screens die — a dip to black
            c = np.array({"white": [255, 255, 255], "cold": [190, 215, 255]}.get(col, [255, 30, 30]), np.float32)
            a = a * (1 - 0.6 * k) + c * 0.6 * k
    # hard cut to black at the end of the lock shot
    frame = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    if "dust" in fx: dust(frame, t, shot)
    if "countdown" in fx or (getattr(TL, "COUNTDOWN", None) and len(TL.COUNTDOWN) >= 3 and TL.COUNTDOWN[0] <= t < TL.CUT_TO_BLACK and "phone" not in shot and not shot.get("nohud")): draw_countdown(frame, t)
    if "crackscreen" in fx: frame.alpha_composite(crack_layer())                       # EP09: seen through the cracked phone screen
    if "cctv" in fx: draw_cctv(frame, t)
    if "cap204" in fx:                                                                  # EP10: the recording's room caption
        d_ = ImageDraw.Draw(frame); a_ = min(1.0, max(0.0, (t - TL.T_CAP) / 0.2))
        if a_ > 0:
            d_.rounded_rectangle([70, 250, 520, 340], 18, fill=(0, 0, 0, int(150 * a_)))
            d_.text((295, 295), "КОМНАТА 204", font=ImageFont.truetype(FONT_UI, 56), fill=(255, 255, 255, int(240 * a_)), anchor="mm")
    if "rec" in fx: draw_rec(frame, t)
    if "endcard" in fx: draw_endcard(frame, t)
    draw_subs(frame, t, shot)
    return frame.convert("RGB").tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs=2, type=float)
    ap.add_argument("--stills", type=str)
    ap.add_argument("--out", type=str, default=os.path.join(ROOT, "renders", "EP11_PRICE_OF_CHOICE_FINAL.mp4"))
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "renders"), exist_ok=True)
    if args.stills:
        for s in args.stills.split(","):
            t = float(s); Image.frombytes("RGB", (OW, OH), render_frame(int(round(t * FPS)))).save(os.path.join(ROOT, "renders", f"still_{t:06.2f}.png"))
        return
    a, b = (args.preview if args.preview else (0, TL.END))
    frames = range(int(round(a * FPS)), int(round(b * FPS)))
    mix = os.path.join(ROOT, "audio", "mix_ep11.wav")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
           "-ss", f"{a}", "-t", f"{b - a}", "-i", mix,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "6M", "-bufsize", "12M", "-profile:v", "high", "-pix_fmt", "yuv420p",
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
