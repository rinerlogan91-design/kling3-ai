#!/usr/bin/env python3
"""Vidéo « TU TRANCHES ? — Le mariage » (1080x1920, ~1 min).

La voix off vient de narration/ (Kokoro, skill canvas-video) :
    uv run --with kokoro-onnx --with soundfile <skill>/scripts/narrate.py video/mariage/narration
puis :
    python3 make_video.py   ->  tu_tranches_mariage.mp4
Dépendances : Pillow, numpy, opencv-python-headless, ffmpeg.
"""
import json
import math
import os
import subprocess
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
NARR = os.path.join(HERE, "narration")
OUT = os.path.join(HERE, "tu_tranches_mariage.mp4")
TIMING = json.loads(open(os.path.join(NARR, "timing.js"), encoding="utf-8").read()
                    .split("window.VIDEO_TIMING = ", 1)[1].rstrip().rstrip(";"))["fr"]
VOICE = os.path.join(NARR, "audio", "fr.m4a")
W, H, FPS, SR = 1080, 1920, 30, 44100
DUR = TIMING["duration"] + 1.0
SS = 1.35                      # sur-résolution des images sources
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RED, GREEN, WHITE, INK = (215, 25, 25), (25, 160, 45), (255, 255, 255), (15, 15, 15)

SC = {s["id"]: s for s in TIMING["scenes"]}
CUE = {s["id"]: [(s["start"] + c["s"], s["start"] + c["e"], c["text"]) for c in s["cues"]]
       for s in TIMING["scenes"]}
T0 = {k: v["start"] for k, v in SC.items()}
T1 = {k: v["start"] + v["d"] for k, v in SC.items()}
T1["choix"] = DUR


def c(scene, i, k=0):
    """Début (k=0) ou fin (k=1) de la phrase i d'une scène."""
    return CUE[scene][i][k]


_fonts = {}


def font(size):
    size = max(8, int(size))
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(BOLD, size)
    return _fonts[size]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def back(t):
    """Easing avec léger dépassement (effet « pop »)."""
    t = max(0.0, min(1.0, t))
    s = 1.9
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


# --------------------------------------------------------------------------
# Scènes : image, caméra (clés : temps, zoom, cx, cy), personnages animés
# Coordonnées des personnages dans l'image d'origine 941x1672.
# --------------------------------------------------------------------------
def keys_choc():
    return [(0.0, 1.30, .50, .45), (0.7, 1.0, .50, .50), (2.3, 1.12, .50, .42),
            (c("choc", 1), 1.12, .50, .42), (c("choc", 1) + .35, 1.65, .63, .38),
            (c("choc", 2) - .05, 1.75, .63, .38), (c("choc", 2) + .2, 2.3, .62, .36),
            (6.6, 2.4, .62, .36), (7.0, 1.9, .22, .32), (8.4, 1.95, .22, .32), (9.3, 1.05, .50, .50)]


def keys_pression():
    t = T0["pression"]
    return [(t, 1.75, .17, .72), (t + 2.3, 1.75, .83, .72), (c("pression", 1), 1.35, .50, .74),
            (c("pression", 1) + 2.0, 1.25, .50, .62), (c("pression", 2), 1.25, .45, .45),
            (c("pression", 2) + .35, 2.1, .21, .31), (c("pression", 2) + 2.4, 2.15, .21, .31),
            (c("pression", 2) + 2.8, 2.15, .55, .31), (T1["pression"] - .9, 2.25, .55, .30),
            (T1["pression"], 1.5, .50, .40)]


def keys_doute():
    t = T0["doute"]
    return [(t, 1.0, .50, .48), (c("doute", 0) + 1.2, 1.45, .68, .40), (c("doute", 1), 1.6, .68, .40),
            (c("doute", 2), 1.35, .62, .45), (c("doute", 2) + .25, 1.85, .69, .39),
            (c("doute", 3), 1.85, .69, .40), (c("doute", 3) + .6, 1.9, .45, .66),
            (T1["doute"], 2.45, .45, .66)]


def keys_ultimatum():
    t = T0["ultimatum"]
    q_end = c("ultimatum", 2, 1)
    return [(t, 1.0, .50, .45), (c("ultimatum", 0, 1), 1.15, .50, .42),
            (c("ultimatum", 1), 1.15, .50, .42), (c("ultimatum", 1) + .3, 2.0, .43, .37),
            (q_end, 2.25, .43, .37), (q_end + .25, 2.3, .73, .33), (c("ultimatum", 3), 2.75, .73, .33),
            (c("ultimatum", 3) + .5, 1.0, .50, .45), (T1["ultimatum"], 1.05, .50, .45)]


def keys_choix():
    t = T0["choix"]
    return [(t, 1.0, .50, .45), (c("choix", 0), 1.0, .50, .45), (c("choix", 0) + .35, 1.85, .26, .47),
            (c("choix", 1) - .05, 1.95, .26, .47), (c("choix", 1) + .3, 1.85, .76, .47),
            (c("choix", 2) - .05, 1.95, .76, .47), (c("choix", 2) + .4, 1.0, .50, .50),
            (DUR, 1.08, .50, .55)]


# actor : centre (x, y), rayon, type, début, fin, amplitude
def actors_for(sid):
    t0, t1 = T0[sid], T1[sid]
    if sid == "choc":
        return [((200, 560), 230, "bob", t0, t1, 14, 2.4),            # le marié sautille de joie
                ((390, 610), 120, "bob", c("choc", 2), t1, 8, 3.0),   # le prêtre sursaute
                ((600, 600), 260, "tremble", c("choc", 1), t1, 5, 0),  # la mariée commence à trembler
                ((600, 560), 200, "pop", c("choc", 2), c("choc", 2) + .6, .18, 0)]
    if sid == "pression":
        g = [(70, 860), (150, 1020), (110, 1210), (90, 1410), (800, 850), (780, 1010), (790, 1200), (850, 1420)]
        out = [((x, y), 120, "jump", t0 + .25 * i, t0 + .25 * i + .7, 22, 0) for i, (x, y) in enumerate(g)]
        out += [((x, y), 120, "sway", t0 + 2, t1, 5, 0.9 + .15 * i) for i, (x, y) in enumerate(g)]
        out += [((200, 650), 220, "bob", t0, t1, 7, 1.6),
                ((510, 620), 240, "tremble", t0, t1, 4, 0),
                ((510, 470), 160, "pop", c("pression", 2) + 2.6, c("pression", 2) + 3.2, .15, 0)]
        return out
    if sid == "doute":
        return [((230, 700), 280, "bob", t0, t1, 10, 2.0),
                ((660, 760), 330, "tremble", t0, t1, 4, 0),
                ((660, 700), 300, "tremble", c("doute", 2), c("doute", 2, 1) + .3, 9, 0),
                ((660, 650), 230, "pop", c("doute", 2), c("doute", 2) + .6, .16, 0),
                ((440, 1110), 190, "tremble", c("doute", 3), t1, 7, 0)]
    if sid == "ultimatum":
        q0, q1 = c("ultimatum", 2), c("ultimatum", 2, 1)
        return [((190, 640), 230, "bob", t0, t1, 10, 2.2),
                ((400, 560), 150, "talk", q0, q1, 7, 0),
                ((400, 560), 150, "pop", c("ultimatum", 1) + .2, c("ultimatum", 1) + .8, .14, 0),
                ((700, 620), 260, "tremble", t0, t1, 4, 0),
                ((700, 560), 220, "tremble", q1, c("ultimatum", 3) + .5, 9, 0)]
    if sid == "choix":
        return [((110, 760), 150, "bob", t0, t1, 10, 2.4), ((330, 760), 150, "bob", t0, t1, 10, 2.4),
                ((800, 800), 170, "tremble", t0, t1, 6, 0), ((550, 820), 140, "tremble", t0, t1, 4, 0),
                ((760, 640), 210, "jump", c("choix", 1), c("choix", 1) + 3, 10, 0)]
    return []


SCENES = [
    dict(id="choc", img="1_choc.png", keys=keys_choc()),
    dict(id="pression", img="2_pression.png", keys=keys_pression()),
    dict(id="doute", img="3_doute.png", keys=keys_doute()),
    dict(id="ultimatum", img="4_ultimatum.png", keys=keys_ultimatum()),
    dict(id="choix", img="5_choix.png", keys=keys_choix()),
]
for s in SCENES:
    s["t0"], s["t1"], s["actors"] = T0[s["id"]], T1[s["id"]], actors_for(s["id"])
TRANS = 0.32

# Secousses caméra (début, durée, amplitude en px source)
SHAKES = [(c("choc", 2), .6, 16), (c("doute", 2), 1.0, 14), (c("doute", 3), .5, 10),
          (c("ultimatum", 1), .35, 10), (c("ultimatum", 2, 1), .5, 12)]
# Coups de zoom accompagnés d'un « boom »
BOOMS = [c("choc", 1), c("choc", 2), c("pression", 2) + 2.6, c("doute", 2), c("doute", 3),
         c("ultimatum", 1), c("ultimatum", 2, 1), c("choix", 0), c("choix", 1)]


# ------------------------------- Images ------------------------------------
def load(name):
    im = Image.open(os.path.join(IMG, name)).convert("RGB")
    im = im.resize((int(im.width * SS), int(im.height * SS)), Image.LANCZOS)
    return np.ascontiguousarray(np.array(im))


def envelope(t, a, b, f=0.2):
    if t < a or t > b:
        return 0.0
    return min(1.0, (t - a) / f, (b - t) / f)


def animate_actors(src, actors, t):
    """Déforme localement l'image pour faire bouger les bonshommes."""
    live = []
    for (x, y), r, kind, a, b, amp, freq in actors:
        e = envelope(t, a, b)
        if e > 0:
            live.append(((x * SS, y * SS), r * SS, kind, a, b, amp * SS, freq, e))
    if not live:
        return src
    h, w = src.shape[:2]
    mx, my = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    for (cx, cy), r, kind, a, b, amp, freq, e in live:
        x0, x1 = int(max(0, cx - r)), int(min(w, cx + r))
        y0, y1 = int(max(0, cy - r)), int(min(h, cy + r))
        if x1 <= x0 or y1 <= y0:
            continue
        X, Y = mx[y0:y1, x0:x1], my[y0:y1, x0:x1]
        d2 = ((X - cx) ** 2 + (Y - cy) ** 2) / (r * r)
        m = np.clip(1 - d2, 0, 1) ** 2 * e
        dx = dy = 0.0
        mag = 0.0
        if kind == "bob":
            dy = -amp * abs(math.sin(math.pi * freq * t))
        elif kind == "tremble":
            dx = amp * math.sin(2 * math.pi * 11 * t + cx) + amp * .5 * math.sin(2 * math.pi * 17 * t)
            dy = amp * .5 * math.sin(2 * math.pi * 13 * t + cy)
        elif kind == "sway":
            dx = amp * math.sin(2 * math.pi * freq * t + cx * .01)
        elif kind == "jump":
            p = (t - a) / max(.01, b - a)
            dy = -amp * math.sin(math.pi * min(1, p * 2.2)) if p < 1 / 2.2 else 0
        elif kind == "talk":
            dy = -amp * abs(math.sin(2 * math.pi * 4.5 * t))
            mag = 0.04 * abs(math.sin(2 * math.pi * 4.5 * t))
        elif kind == "pop":
            p = (t - a) / max(.01, b - a)
            mag = amp * math.sin(math.pi * p)
        k = 1 - mag * m
        mx[y0:y1, x0:x1] = cx + (X - cx) * k - dx * m
        my[y0:y1, x0:x1] = cy + (Y - cy) * k - dy * m
    return cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def cam_at(sc, t):
    ks = sc["keys"]
    if t <= ks[0][0]:
        return ks[0][1:]
    for (ta, *va), (tb, *vb) in zip(ks, ks[1:]):
        if ta <= t <= tb:
            p = ease((t - ta) / max(1e-3, tb - ta))
            return tuple(u + (v - u) * p for u, v in zip(va, vb))
    return ks[-1][1:]


def camera(src, sc, t, extra_zoom=1.0):
    z, cx, cy = cam_at(sc, t)
    z *= extra_zoom
    sh, sw = src.shape[:2]
    cw, ch = sw / z, sh / z
    x = min(max(cx * sw - cw / 2, 0), sw - cw)
    y = min(max(cy * sh - ch / 2, 0), sh - ch)
    for s, d, amp in SHAKES:
        if s <= t <= s + d:
            k = amp * SS * (1 - (t - s) / d)
            x += k * math.sin(t * 83)
            y += k * math.cos(t * 71)
    sc_ = W / cw
    M = np.float32([[sc_, 0, -x * sc_], [0, sc_, -y * sc_]])
    out = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return out, (x, y, sc_)


def to_out(view, px, py):
    """Coordonnées image d'origine -> coordonnées écran."""
    x, y, s = view
    return (px * SS - x) * s, (py * SS - y) * s


# ------------------------------ Overlays -----------------------------------
HL = {"mariage": GREEN, "OUI": GREEN, "NON": RED, "plus": RED, "marier.": RED, "famille": GREEN,
      "amis": GREEN, "milliers": RED, "d'euros": RED, "immense": GREEN, "sourire.": GREEN,
      "même": RED, "chose.": RED, "l'aimes": RED, "trop": RED, "vite.": RED, "l'alliance,": RED,
      "doigt": RED, "monde": RED, "LA": RED, "question": RED, "secondes": RED, "A": GREEN, "B": RED,
      "commentaire,": GREEN, "pourquoi": GREEN, "époux": GREEN, "épouse": GREEN, "regarde.": RED}


def wrap(d, text, f, maxw):
    lines, cur = [], []
    for w_ in text.split():
        if d.textlength(" ".join(cur + [w_]), font=f) <= maxw or not cur:
            cur.append(w_)
        else:
            lines.append(cur)
            cur = [w_]
    return lines + ([cur] if cur else [])


CAPS = []
for s in SCENES:
    cues = CUE[s["id"]]
    for i, (a, e, text) in enumerate(cues):
        if s["id"] == "choix" and i == len(cues) - 1:
            continue                                    # « TU TRANCHES ! » = carton final
        end = cues[i + 1][0] if i + 1 < len(cues) else s["t1"] - .1
        if s["id"] == "choc" and i == 1:
            end = cues[2][1]                            # « …dire OUI… » reste avec la suite
        size = 74 if s["id"] == "ultimatum" and i == 2 else 62
        CAPS.append((a - .05, end - .05, text.replace(" :", " :").replace(" ?", " ?")
                     .replace(" !", " !").replace("« ", "« ").replace(" »", " »"),
                     e - a, size, s["id"] == "choc" and i == 2))


def draw_caption(d, t, a, b, text, speak, size, stack):
    if not a <= t <= b:
        return
    ain = (t - a) / .3
    al = int(255 * min(1, ain, (b - t) / .2))
    f = font(size * (0.85 + 0.15 * back(ain)))
    lines = wrap(d, text, f, W - 190)
    lh = int(f.size * 1.27)
    bh = lh * len(lines) + 56
    y0 = 120 + (330 if stack else 0)
    bw = max(d.textlength(" ".join(l), font=f) for l in lines) + 80
    x0 = (W - bw) / 2
    d.rounded_rectangle([x0 + 10, y0 + 12, x0 + bw + 10, y0 + bh + 12], 34, fill=(0, 0, 0, int(al * .55)))
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 34, fill=(255, 255, 255, int(al * .97)),
                        outline=(0, 0, 0, al), width=6)
    n = sum(len(l) for l in lines)
    shown = 1 + n * (t - a) / max(.4, speak * .85)
    k = 0
    for i, l in enumerate(lines):
        x = (W - d.textlength(" ".join(l), font=f)) / 2
        for w_ in l:
            if k < shown:
                col = HL.get(w_, HL.get(w_.strip(",.?!…«» "), INK))
                d.text((x, y0 + 28 + i * lh), w_, font=f, fill=col + (al,))
            k += 1
            x += d.textlength(w_ + " ", font=f)


def stamp(d, t, a, b, text, x, y, size, col, rot_free=True):
    """Gros texte qui claque (pop) puis disparaît."""
    if not a <= t <= b:
        return
    p = (t - a) / .35
    al = int(255 * min(1, p * 2, (b - t) / .25))
    f = font(size * (0.4 + 0.6 * back(p)))
    d.text((x, y), text, font=f, fill=col + (al,), anchor="mm", stroke_width=max(4, f.size // 14),
           stroke_fill=(255, 255, 255, al))


def heart(d, x, y, s, col):
    d.ellipse([x - s, y - s * .6, x, y + s * .4], fill=col)
    d.ellipse([x, y - s * .6, x + s, y + s * .4], fill=col)
    d.polygon([(x - s * .97, y), (x + s * .97, y), (x, y + s * 1.15)], fill=col)


def overlays(frame, t, sc, view):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sid = sc["id"]

    # --- CHOC : cœurs du marié, « !? » au-dessus de la mariée
    if sid == "choc":
        if t < c("choc", 2):
            for i in range(5):
                ph = (t * .55 + i / 5) % 1
                gx, gy = to_out(view, 140 + 60 * math.sin(i * 2.1 + t), 440 - ph * 260)
                heart(d, gx, gy, 26, (230, 40, 70, int(255 * math.sin(math.pi * ph))))
        if t >= c("choc", 2):
            bx, by = to_out(view, 690, 380)
            stamp(d, t, c("choc", 2) + .05, sc["t1"] - .3, "!?", bx, by, 170, RED)
        stamp(d, t, 0.0, 1.9, "IMAGINE…", W / 2, H - 330, 125, INK)

    # --- PRESSION : « ! » sur les invités, compteur d'euros
    if sid == "pression":
        g = [(70, 760), (150, 920), (110, 1110), (90, 1310), (800, 750), (780, 910), (790, 1100), (850, 1320)]
        for i, (x, y) in enumerate(g):
            a = sc["t0"] + .25 * i
            gx, gy = to_out(view, x, y)
            stamp(d, t, a, a + 1.6, "!", gx, gy, 110, RED)
        a = c("pression", 1) + .9
        if a <= t <= c("pression", 2) + .2:
            v = int(25000 * ease((t - a) / 1.4) / 100) * 100
            al = int(255 * min(1, (t - a) / .2, (c("pression", 2) + .2 - t) / .2))
            txt = f"-{v:,} €".replace(",", " ")
            f = font(120)
            tw = d.textlength(txt, font=f)
            d.rounded_rectangle([(W - tw) / 2 - 40, H - 520, (W + tw) / 2 + 40, H - 340], 40,
                                fill=(255, 255, 255, int(al * .95)), outline=RED + (al,), width=10)
            d.text((W / 2, H - 430), txt, font=f, fill=RED + (al,), anchor="mm")

    # --- DOUTE : « ? » qui tournent autour de la tête de la mariée
    if sid == "doute" and c("doute", 0) + .8 <= t <= c("doute", 3) + .5:
        al_g = min(1, (t - c("doute", 0) - .8) / .3, (c("doute", 3) + .5 - t) / .3)
        for i in range(4):
            ang = t * 2.2 + i * math.pi / 2
            qx, qy = to_out(view, 660 + 230 * math.cos(ang), 470 + 90 * math.sin(ang))
            f = font(90 + 20 * math.sin(t * 5 + i))
            d.text((qx, qy), "?", font=f, fill=RED + (int(255 * al_g),), anchor="mm",
                   stroke_width=6, stroke_fill=(255, 255, 255, int(255 * al_g)))

    # --- ULTIMATUM : « SILENCE… »
    if sid == "ultimatum":
        a, b = c("ultimatum", 2, 1) + .15, c("ultimatum", 3)
        if a <= t <= b:
            stamp(d, t, a, b, "SILENCE…", W / 2, H - 360, 130, INK)

    # --- CHOIX : cadres lumineux A / B, compte à rebours sur le chrono
    if sid == "choix":
        for i, (x0, x1, col) in enumerate(((15, 462, GREEN), (478, 928, RED))):
            a, b = c("choix", i), c("choix", i + 1) - .05
            if a <= t <= b:
                al = int(255 * min(1, (t - a) / .3, (b - t) / .3) * (.75 + .25 * math.sin(t * 9)))
                p0, p1 = to_out(view, x0, 325), to_out(view, x1, 1230)
                d.rounded_rectangle([p0[0], p0[1], p1[0], p1[1]], 40, outline=col + (al,), width=16)
        cs = c("choix", 2)
        step = (c("choix", 4) - cs) / 5
        if cs <= t < cs + 5 * step:
            n = 5 - int((t - cs) / step)
            f_ = ((t - cs) / step) % 1
            cx, cy = to_out(view, 472, 1462)
            r = 120 * view[2] / 1.0 * SS / 1.5
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))
            d.arc([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], -90, -90 + 360 * (1 - f_), fill=RED + (255,),
                  width=int(r * .14))
            d.text((cx, cy), str(n), font=font(r * 1.25 * (1.25 - .25 * ease(f_ / .25))), fill=INK + (255,),
                   anchor="mm")

    for cap in CAPS:
        draw_caption(d, t, *cap)

    # carton final
    tf = c("choix", 4)
    if t >= tf - .1:
        p = ease((t - tf + .1) / .35)
        al = int(255 * p)
        pulse = 1 + .05 * math.sin((t - tf) * 9)
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(215 * p)))
        f1 = font(160 * pulse)
        parts = (("A", GREEN), (" ou ", WHITE), ("B ?", RED))
        x = (W - sum(d.textlength(s_, font=f1) for s_, _ in parts)) / 2
        for s_, col in parts:
            d.text((x, H / 2 - 330), s_, font=f1, fill=col + (al,), stroke_width=7, stroke_fill=(0, 0, 0, al))
            x += d.textlength(s_, font=f1)
        for i, line in enumerate(["Écris ton choix en commentaire", "et explique pourquoi !"]):
            d.text((W / 2, H / 2 + 20 + i * 82), line, font=font(58), fill=WHITE + (al,), anchor="mm")
        f3 = font(100 * back(min(1, (t - tf) / .4)) * pulse)
        d.text((W / 2, H / 2 + 330), "TU TRANCHES !", font=f3, fill=WHITE + (al,), anchor="mm",
               stroke_width=8, stroke_fill=RED + (al,))
    frame.alpha_composite(layer)


def vignette_mask():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return np.clip((d - .55) / .7, 0, 1) ** 1.6


VIG = vignette_mask()


def frustration(t):
    """Intensité du voile rouge qui bat comme un cœur pendant les hésitations."""
    k = 0.0
    if T0["doute"] <= t <= T1["doute"]:
        k = .55
    a, b = c("ultimatum", 2, 1), c("ultimatum", 3) + .3
    if a <= t <= b:
        k = .9
    if k == 0:
        return 0.0
    beat = (t * 1.15) % 1
    return k * (.45 + .55 * math.exp(-beat * 7))


def render_frame(t, images):
    cur = max((s for s in SCENES if s["t0"] <= t), key=lambda s: s["t0"])
    src = animate_actors(images[cur["img"]], cur["actors"], t)
    rgb, view = camera(src, cur, t)
    # transition : coup de zoom + flash blanc
    nxt = [s for s in SCENES if 0 < s["t0"] - t <= TRANS]
    if nxt:
        n = nxt[0]
        p = 1 - (n["t0"] - t) / TRANS
        rgb, view = camera(src, cur, t, 1 + .35 * ease(p))
        if p > .5:
            rgb2, view = camera(animate_actors(images[n["img"]], n["actors"], n["t0"]), n, n["t0"], 1.25 - .25 * p)
            rgb = cv2.addWeighted(rgb, 1 - ease((p - .5) * 2), rgb2, ease((p - .5) * 2), 0)
    since = t - cur["t0"]
    if 0 < cur["t0"] and since < TRANS:
        rgb, view = camera(src, cur, t, 1 + .2 * (1 - ease(since / TRANS)))
    fr = frustration(t)
    if fr > 0:
        m = (VIG * fr)[..., None]
        rgb = (rgb * (1 - m) + np.array([170, 0, 0], np.float32) * m).astype(np.uint8)
    flash = 0.0
    for s in SCENES[1:]:
        flash = max(flash, 1 - abs(t - s["t0"]) / .12)
    if flash > 0:
        rgb = cv2.addWeighted(rgb, 1 - .7 * flash, np.full_like(rgb, 255), .7 * flash, 0)
    frame = Image.fromarray(rgb).convert("RGBA")
    overlays(frame, t, cur, view)
    if t < .25:
        frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - t / .25)))))
    return frame.convert("RGB")


# ------------------------------- Audio -------------------------------------
def make_fx(path):
    n = int(SR * DUR)
    out = np.zeros(n)
    rng = np.random.default_rng(3)

    def add(sig, start, g=1.0):
        i = int(start * SR)
        if 0 <= i < n:
            out[i:i + len(sig)] += g * sig[: n - i]

    def tt(d):
        return np.arange(int(d * SR)) / SR

    def whoosh(d=.45):
        k = tt(d)
        nz = rng.standard_normal(len(k))
        sig = np.zeros_like(nz)
        for j in range(0, len(k), 512):                  # filtre passe-bas qui s'ouvre
            w_ = int(40 - 34 * j / len(k))
            sig[j:j + 512] = np.convolve(nz, np.ones(w_) / w_, "same")[j:j + 512]
        return sig * np.sin(np.pi * k / d) ** 2

    def boom(f=55, d=.7):
        k = tt(d)
        return np.sin(2 * np.pi * f * k * (1 - .35 * k)) * np.exp(-k * 6)

    def pop(f=900):
        k = tt(.09)
        return np.sin(2 * np.pi * f * k * (1 + 3 * k)) * np.exp(-k * 45)

    def thump(d=.18):
        k = tt(d)
        return np.sin(2 * np.pi * 48 * k) * np.exp(-k * 22)

    for s in SCENES[1:]:
        add(whoosh(), s["t0"] - .3, .22)
    for b in BOOMS:
        add(boom(), b, .32)
    add(pop(700), c("choc", 2) + .05, .3)
    for i in range(8):
        add(pop(800 + 60 * i), T0["pression"] + .25 * i, .18)
    for i in range(10):                                   # pièces qui tombent
        k = tt(.1)
        add(np.sin(2 * np.pi * (2300 + 140 * (i % 4)) * k) * np.exp(-k * 40), c("pression", 1) + .9 + i * .13, .1)
    # battements de cœur pendant les hésitations
    for b in np.arange(T0["doute"] + .2, T1["doute"], 1 / 1.15):
        add(thump(), b, .45)
        add(thump(), b + .2, .3)
    for b in np.arange(c("ultimatum", 2, 1), c("ultimatum", 3) + .3, 1 / 1.15):
        add(thump(), b, .6)
        add(thump(), b + .2, .42)
    # compte à rebours
    cs = c("choix", 2)
    step = (c("choix", 4) - cs) / 5
    for i in range(5):
        k = tt(.06)
        add(np.sin(2 * np.pi * 1600 * k) * np.exp(-k * 60), cs + i * step, .2)
    k = tt(1.4)
    add((np.sin(2 * np.pi * 523 * k) + np.sin(2 * np.pi * 659 * k) + np.sin(2 * np.pi * 784 * k)) / 3
        * np.exp(-k * 2.2), c("choix", 4), .3)
    add(boom(50, 1.0), c("choix", 4), .35)
    out *= np.clip((DUR - np.arange(n) / SR) / .8, 0, 1)
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w_:
        w_.setnchannels(1)
        w_.setsampwidth(2)
        w_.setframerate(SR)
        w_.writeframes(pcm.tobytes())


def main():
    wav = os.path.join(HERE, "_fx.wav")
    make_fx(wav)
    images = {s["img"]: load(s["img"]) for s in SCENES}
    # voix : plus de présence et de punch (égaliseur + compresseur)
    voice = ("[1:a]highpass=f=90,equalizer=f=3200:t=q:w=1.2:g=4,equalizer=f=180:t=q:w=1:g=2,"
             "acompressor=threshold=-20dB:ratio=3.5:attack=4:release=90:makeup=2,apad[v]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", VOICE, "-i", wav, "-filter_complex",
           voice + ";[v][2:a]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.95,"
           "aformat=channel_layouts=stereo[a]", "-map", "0:v", "-map", "[a]", "-t", f"{DUR:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int(DUR * FPS)
    for i in range(total):
        p.stdin.write(render_frame(i / FPS, images).tobytes())
        if i % 300 == 0:
            print(f"{i}/{total}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
