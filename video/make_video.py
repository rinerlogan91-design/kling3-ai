#!/usr/bin/env python3
"""Génère la vidéo « TU TRANCHES ? » (1080x1920, 60 s) à partir des 5 images.

Usage : python3 make_video.py   ->  tu_tranches.mp4
Dépendances : Pillow, numpy, ffmpeg.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
OUT = os.path.join(HERE, "tu_tranches.mp4")
W, H, FPS, DUR = 1080, 1920, 30, 60.0
SR = 44100

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RED = (210, 20, 20)
GREEN = (20, 150, 40)


def font(size):
    return ImageFont.truetype(BOLD, size)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def load(name):
    im = Image.open(os.path.join(IMG, name)).convert("RGB")
    # légère sur-résolution pour que les zooms restent nets
    return im.resize((int(W * 1.35), int(H * 1.35)), Image.LANCZOS)


# --------------------------------------------------------------------------
# Scènes : (fichier, début, fin, mouvement caméra, position des sous-titres)
# mouvement : (zoom_début, zoom_fin, cx_début, cy_début, cx_fin, cy_fin)
#   cx/cy = centre du cadrage en fraction de l'image
# --------------------------------------------------------------------------
SCENES = [
    # 1. Accroche : il fixe l'écran « SALAIRE x2 » en pensant à son ami
    dict(img="1_reflexion_salaire.png", t0=0.0, t1=7.0,
         cam=(1.30, 1.05, 0.70, 0.55, 0.50, 0.50), shake=0),
    # 2. Le meilleur ami vient de se faire virer
    dict(img="2_ami_vire.png", t0=7.0, t1=19.0,
         cam=(1.0, 1.18, 0.50, 0.50, 0.38, 0.55), shake=0),
    # 3. Le patron propose le poste, salaire doublé
    dict(img="3_offre_patron.png", t0=19.0, t1=31.0,
         cam=(1.0, 1.25, 0.50, 0.55, 0.55, 0.68), shake=0),
    # 4. Une heure plus tard, l'ami appelle
    dict(img="4_appel_ami.png", t0=31.0, t1=41.0,
         cam=(1.0, 1.20, 0.50, 0.55, 0.62, 0.55), shake=1),
    # 5. Message du patron : jusqu'à minuit
    dict(img="1_reflexion_salaire.png", t0=41.0, t1=47.0,
         cam=(1.05, 1.45, 0.50, 0.50, 0.68, 0.55), shake=0),
    # 6. Le choix A ou B
    dict(img="5_tu_tranches.png", t0=47.0, t1=60.0,
         cam=(1.45, 1.0, 0.50, 0.17, 0.50, 0.50), shake=0),
]
XFADE = 0.45

# Sous-titres : (début, fin, texte, mots surlignés -> couleur, position)
CAPS = [
    (0.3, 6.8, "Tu peux doubler ton salaire demain…", {"doubler": GREEN, "salaire": GREEN}, "top"),
    (2.6, 6.8, "…mais tu dois prendre la place de ton meilleur ami.", {"meilleur": RED, "ami.": RED}, "top2"),

    (7.3, 10.2, "Ton meilleur ami vient de se faire virer.", {"virer.": RED}, "top"),
    (10.2, 12.9, "Vous travaillez ensemble depuis 5 ans.", {"5": RED, "ans.": RED}, "top"),
    (12.9, 15.9, "C'est lui qui t'a fait entrer dans l'entreprise.", {}, "top"),
    (15.9, 18.9, "Quand tu n'avais rien, il t'a hébergé gratuitement 3 mois.", {"gratuitement": GREEN}, "top"),

    (19.3, 22.4, "Aujourd'hui, ton patron t'appelle dans son bureau.", {"patron": RED}, "top"),
    (22.4, 25.6, "Il te propose son poste… avec un salaire x2.", {"x2.": GREEN, "salaire": GREEN}, "top"),
    (25.6, 30.9, "Rembourser tes dettes. Aider ta famille. Changer de vie.", {"Changer": GREEN, "de": GREEN, "vie.": GREEN}, "top"),

    (31.3, 34.4, "Une heure plus tard… ton meilleur ami t'appelle.", {"ami": RED}, "top"),
    (34.4, 40.9, "« Frère, je suis au fond du trou. Heureusement que je peux compter sur toi. »", {"compter": RED, "sur": RED, "toi.": RED}, "top"),

]


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textlength(test, font=fnt) <= maxw or not cur:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    return lines


def draw_caption(frame, t, start, end, text, hl, pos):
    if not (start <= t <= end):
        return
    a_in = ease((t - start) / 0.35)
    a_out = ease((end - t) / 0.25)
    alpha = min(a_in, a_out)
    fnt = font(62)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap(d, text, fnt, W - 200)
    lh = 78
    box_h = lh * len(lines) + 60
    y0 = {"top": 150, "top2": 150, "bottom": H - box_h - 170}[pos]
    if pos == "top2":
        y0 = 150 + 3 * lh + 70
    y0 += int((1 - a_in) * 40)  # glisse vers le haut en apparaissant
    box_w = max(d.textlength(" ".join(l), font=fnt) for l in lines) + 80
    x0 = (W - box_w) / 2
    d.rounded_rectangle([x0 + 10, y0 + 12, x0 + box_w + 10, y0 + box_h + 12], 34, fill=(0, 0, 0, 150))
    d.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], 34, fill=(255, 255, 255, 245),
                        outline=(0, 0, 0, 255), width=6)
    # mots révélés progressivement (effet « karaoké »)
    nwords = sum(len(l) for l in lines)
    shown = int(1 + (t - start) / 0.08)
    k = 0
    for i, l in enumerate(lines):
        lw = d.textlength(" ".join(l), font=fnt)
        x = (W - lw) / 2
        y = y0 + 30 + i * lh
        for w in l:
            col = hl.get(w, (15, 15, 15))
            if k < shown or k >= nwords:
                d.text((x, y), w, font=fnt, fill=col + (255,))
            k += 1
            x += d.textlength(w + " ", font=fnt)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(layer)


def camera(src, t, sc):
    z0, z1, cx0, cy0, cx1, cy1 = sc["cam"]
    p = ease((t - sc["t0"]) / (sc["t1"] - sc["t0"]))
    z = z0 + (z1 - z0) * p
    cx = cx0 + (cx1 - cx0) * p
    cy = cy0 + (cy1 - cy0) * p
    sw, sh = src.size
    cw, ch = sw / z / 1.0, sh / z / 1.0
    # le zoom 1.0 = image entière
    cw, ch = sw / z, sh / z
    x = min(max(cx * sw - cw / 2, 0), sw - cw)
    y = min(max(cy * sh - ch / 2, 0), sh - ch)
    if sc["shake"] and t - sc["t0"] < 4.5:  # le téléphone vibre
        amp = 14 * (1 - (t - sc["t0"]) / 4.5)
        x = min(max(x + amp * math.sin(t * 61), 0), sw - cw)
        y = min(max(y + amp * math.cos(t * 47), 0), sh - ch)
    return src.resize((W, H), Image.BILINEAR, box=(x, y, x + cw, y + ch))


def sms_bubble(frame, t):
    """Notification du patron (scène 5)."""
    s, e = 41.4, 46.9
    if not (s <= t <= e):
        return
    p = ease((t - s) / 0.4)
    a = min(p, ease((e - t) / 0.25))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = int(-380 + p * 520)
    d.rounded_rectangle([60, y, W - 60, y + 430], 40, fill=(245, 245, 245, 250), outline=(0, 0, 0, 255), width=6)
    d.rounded_rectangle([100, y + 35, 190, y + 125], 22, fill=GREEN + (255,))
    d.text((122, y + 45), "✉", font=font(56), fill=(255, 255, 255, 255))
    d.text((215, y + 40), "PATRON", font=font(50), fill=(15, 15, 15, 255))
    d.text((215, y + 95), "maintenant", font=font(30), fill=(110, 110, 110, 255))
    fnt = font(54)
    lines = wrap(d, "« Tu as jusqu'à minuit pour accepter. Sinon, le poste va à quelqu'un d'autre. »", fnt, W - 220)
    for i, l in enumerate(lines):
        txt = " ".join(l)
        col = RED if "minuit" in txt else (20, 20, 20)
        d.text((100, y + 160 + i * 66), txt, font=fnt, fill=col + (255,))
    # horloge qui tourne
    if t > 43:
        cx, cy, r = W // 2, H - 360, 130
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 240), outline=(0, 0, 0, 255), width=10)
        ang = (t - 43) * 2.4
        d.line([cx, cy, cx + 0.8 * r * math.sin(ang), cy - 0.8 * r * math.cos(ang)], fill=RED + (255,), width=10)
        d.line([cx, cy, cx, cy - 0.55 * r], fill=(0, 0, 0, 255), width=12)
        d.text((cx, cy + r + 50), "00:00", font=font(64), fill=RED + (255,), anchor="mm",
               stroke_width=5, stroke_fill=(255, 255, 255, 255))
    if a < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    frame.alpha_composite(layer)


def countdown(frame, t):
    """Compte à rebours 5..1 puis appel à commenter (scène 6)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if 51.2 <= t < 56.2:
        n = 5 - int(t - 51.2)
        f = (t - 51.2) % 1.0
        sc = 1.6 - 0.6 * ease(f / 0.25)
        a = int(255 * (1 - max(0, f - 0.75) / 0.25))
        r = int(170 * sc)
        cx, cy = W // 2, H // 2 + 60
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, int(a * 0.92)), outline=(255, 255, 255, a), width=10)
        d.arc([cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18], -90, -90 + 360 * (1 - f), fill=RED + (a,), width=14)
        d.text((cx, cy), str(n), font=font(int(190 * sc)), fill=(255, 255, 255, a), anchor="mm")
    if t >= 56.2:
        p = ease((t - 56.2) / 0.4)
        pulse = 1 + 0.04 * math.sin((t - 56.2) * 8)
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(215 * p)))
        f1 = font(int(150 * pulse))
        cy = H // 2 - 220
        wa = d.textlength("A", font=f1)
        wo = d.textlength(" ou ", font=f1)
        wb = d.textlength("B ?", font=f1)
        x = (W - wa - wo - wb) / 2
        al = int(255 * p)
        for txt, col in (("A", GREEN), (" ou ", (255, 255, 255)), ("B ?", RED)):
            d.text((x, cy), txt, font=f1, fill=col + (al,), stroke_width=6, stroke_fill=(0, 0, 0, al))
            x += d.textlength(txt, font=f1)
        f2 = font(58)
        for i, line in enumerate(["Écris ta lettre en commentaire", "et explique pourquoi !"]):
            d.text((W // 2, H // 2 + 60 + i * 80), line, font=f2, fill=(255, 255, 255, al), anchor="mm")
        f3 = font(int(96 * pulse))
        d.text((W // 2, H // 2 + 330), "TU TRANCHES ?", font=f3, fill=(255, 255, 255, al), anchor="mm",
               stroke_width=6, stroke_fill=RED + (al,))
    frame.alpha_composite(layer)


def flash_x2(frame, t):
    """Gros « x2 » qui claque quand on annonce le salaire doublé."""
    s, e = 22.6, 25.4
    if not (s <= t <= e):
        return
    f = t - s
    sc = 2.2 - 1.2 * ease(f / 0.3)
    a = int(255 * min(1, (e - t) / 0.3))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((W // 2, 760), "x2", font=font(int(200 * sc)), fill=GREEN + (a,), anchor="mm",
           stroke_width=10, stroke_fill=(255, 255, 255, a))
    frame.alpha_composite(layer)


def render_frame(t, images):
    active = [sc for sc in SCENES if sc["t0"] - XFADE <= t < sc["t1"] or (sc is SCENES[-1] and t >= sc["t0"])]
    base = None
    for sc in active:
        fr = camera(images[sc["img"]], t, sc)
        if base is None:
            base = fr
        else:
            a = ease((t - (sc["t0"] - XFADE)) / XFADE)
            base = Image.blend(base, fr, a)
    frame = base.convert("RGBA")
    # scène d'accroche : léger voile pour la lisibilité
    if t < 7:
        frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(60 * (1 - ease((t - 5) / 2))))))
    for c in CAPS:
        draw_caption(frame, t, *c)
    flash_x2(frame, t)
    sms_bubble(frame, t)
    countdown(frame, t)
    # fondu d'entrée
    if t < 0.4:
        frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - t / 0.4)))))
    return frame.convert("RGB")


# ------------------------------- Audio -------------------------------------
def make_audio(path):
    n = int(SR * DUR)
    t = np.arange(n) / SR
    out = np.zeros(n)

    def env(s, e, fade=0.5):
        m = np.clip((t - s) / fade, 0, 1) * np.clip((e - t) / fade, 0, 1)
        return m

    # nappe grave et tendue (accord mineur), plus présente vers la fin
    for f, g in ((55, 0.10), (65.4, 0.06), (82.4, 0.06), (110, 0.04)):
        out += g * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)) * env(0, 60, 2)
    out *= 0.7 + 0.5 * (t / DUR)

    # « pulse » rythmique doux
    beat = (np.sin(2 * np.pi * 1.5 * t) > 0.97).astype(float)
    out += 0.05 * np.convolve(beat, np.exp(-np.arange(2000) / 300), "same") * np.sin(2 * np.pi * 220 * t)

    def add(sig, start):
        i = int(start * SR)
        out[i:i + len(sig)] += sig[: max(0, n - i)]

    def whoosh(d=0.5):
        k = np.arange(int(d * SR)) / SR
        noise = np.random.default_rng(1).standard_normal(len(k))
        noise = np.convolve(noise, np.ones(30) / 30, "same")
        return 0.25 * noise * np.sin(np.pi * k / d) ** 2

    for sc in SCENES[1:]:
        add(whoosh(), sc["t0"] - 0.35)

    def hit(f=60, d=0.8, g=0.5):
        k = np.arange(int(d * SR)) / SR
        return g * np.sin(2 * np.pi * f * k * (1 - 0.4 * k)) * np.exp(-k * 5)

    add(hit(), 7.0)     # « viré »
    add(hit(80, 0.6, 0.4), 22.6)  # x2
    add(hit(), 47.0)

    # pièces / caisse enregistreuse à la proposition
    for i in range(6):
        k = np.arange(int(0.12 * SR)) / SR
        add(0.12 * np.sin(2 * np.pi * (2400 + 300 * i) * k) * np.exp(-k * 35), 22.7 + i * 0.07)

    # sonnerie de téléphone
    for r in range(3):
        k = np.arange(int(0.9 * SR)) / SR
        ring = 0.12 * (np.sin(2 * np.pi * 440 * k) + np.sin(2 * np.pi * 480 * k)) * (np.sin(2 * np.pi * 20 * k) > 0)
        add(ring, 31.2 + r * 1.3)

    # battements de cœur pendant l'appel
    for b in np.arange(34.4, 40.8, 0.85):
        for dt, g in ((0, 0.55), (0.18, 0.4)):
            add(hit(45, 0.25, g), b + dt)

    # notification SMS
    for i, f in enumerate((1320, 1760)):
        k = np.arange(int(0.15 * SR)) / SR
        add(0.2 * np.sin(2 * np.pi * f * k) * np.exp(-k * 12), 41.4 + i * 0.13)

    # tic-tac de l'horloge
    for b in np.arange(43, 46.9, 0.5):
        k = np.arange(int(0.03 * SR)) / SR
        add(0.25 * np.sin(2 * np.pi * (2000 if int(b * 2) % 2 else 1500) * k) * np.exp(-k * 150), b)

    # compte à rebours
    for i in range(5):
        k = np.arange(int(0.25 * SR)) / SR
        add(0.3 * np.sin(2 * np.pi * 880 * k) * np.exp(-k * 14), 51.2 + i)
    k = np.arange(int(1.2 * SR)) / SR
    add(0.35 * (np.sin(2 * np.pi * 523 * k) + np.sin(2 * np.pi * 659 * k) + np.sin(2 * np.pi * 784 * k)) / 3
        * np.exp(-k * 2.5), 56.2)
    add(hit(55, 1.0, 0.5), 56.2)

    out *= np.clip(t / 0.5, 0, 1) * np.clip((DUR - t) / 1.0, 0, 1)
    out = np.tanh(out * 1.4) * 0.8
    pcm = (out * 32767).astype(np.int16)
    stereo = np.stack([pcm, pcm], axis=1).ravel()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


def main():
    wav = os.path.join(HERE, "_audio.wav")
    make_audio(wav)
    images = {sc["img"]: load(sc["img"]) for sc in SCENES}
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int(DUR * FPS)
    for i in range(total):
        p.stdin.write(render_frame(i / FPS, images).tobytes())
        if i % 150 == 0:
            print(f"{i}/{total}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
