#!/usr/bin/env python3
"""Génère la vidéo « TU TRANCHES ? » (1080x1920, 60 s) à partir des 5 images.

Usage : python3 make_video.py   ->  tu_tranches.mp4
La voix et le timing viennent de narration/ (Kokoro, skill canvas-video :\nuv run --with kokoro-onnx --with soundfile narrate.py video/narration).\nDépendances : Pillow, numpy, ffmpeg.
"""
import json
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
OUT = os.path.join(HERE, "tu_tranches.mp4")
NARR = os.path.join(HERE, "narration")
TIMING = json.loads(open(os.path.join(NARR, "timing.js"), encoding="utf-8").read()
                    .split("window.VIDEO_TIMING = ", 1)[1].rstrip().rstrip(";"))["fr"]
VOICE = os.path.join(NARR, "audio", "fr.m4a")
W, H, FPS = 1080, 1920, 30
DUR = TIMING["duration"]
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
# Image et mouvement de caméra de chaque scène (les temps viennent de la voix)
# cam = (zoom_début, zoom_fin, cx_début, cy_début, cx_fin, cy_fin)
# --------------------------------------------------------------------------
LOOK = {
    "accroche": dict(img="1_reflexion_salaire.png", cam=(1.30, 1.05, 0.70, 0.55, 0.50, 0.50), shake=0),
    "ami-vire": dict(img="2_ami_vire.png", cam=(1.0, 1.18, 0.50, 0.50, 0.38, 0.55), shake=0),
    "offre":    dict(img="3_offre_patron.png", cam=(1.0, 1.25, 0.50, 0.55, 0.55, 0.68), shake=0),
    "appel":    dict(img="4_appel_ami.png", cam=(1.0, 1.20, 0.50, 0.55, 0.62, 0.55), shake=1),
    "minuit":   dict(img="1_reflexion_salaire.png", cam=(1.05, 1.45, 0.50, 0.50, 0.68, 0.55), shake=0),
    "choix":    dict(img="5_tu_tranches.png", cam=(1.45, 1.0, 0.50, 0.17, 0.50, 0.50), shake=0),
}
SCENES, CUES = [], {}
for s in TIMING["scenes"]:
    SCENES.append(dict(LOOK[s["id"]], id=s["id"], t0=s["start"], t1=s["start"] + s["d"]))
    CUES[s["id"]] = [(s["start"] + c["s"], s["start"] + c["e"], c["text"]) for c in s["cues"]]
XFADE = 0.45

# Mots surlignés
HL = {"doubler": GREEN, "salaire": GREEN, "meilleur": RED, "ami.": RED, "ami": RED, "virer.": RED,
      "cinq": RED, "ans.": RED, "gratuitement": GREEN, "patron": RED, "deux": GREEN, "fois": GREEN,
      "élevé": GREEN, "changer": GREEN, "vie.": GREEN, "compter": RED, "toi.": RED, "»": RED,
      "A": GREEN, "acceptes.": GREEN, "B": RED, "refuses.": RED, "commentaire.": GREEN, "pourquoi.": GREEN}

# Sous-titres : chaque phrase reste affichée jusqu'à la suivante
CAPS = []
for sc in SCENES:
    cues = CUES[sc["id"]]
    for i, (s, e, text) in enumerate(cues):
        if sc["id"] == "minuit" and i == 1:
            continue  # le SMS à l'écran affiche déjà la phrase
        if sc["id"] == "choix" and i == len(cues) - 1:
            continue  # « Maintenant, tu tranches ! » = carton final
        end = cues[i + 1][0] if i + 1 < len(cues) else sc["t1"] - 0.1
        pos = "bottom" if sc["id"] == "choix" else "top"
        CAPS.append((s - 0.05, end - 0.05, text.replace(" :", "\u00a0:"), e - s, pos))

T_X2 = CUES["offre"][1][0] + 2.4                      # « …deux fois plus élevé… »
T_SMS = (CUES["minuit"][0][1] - 0.6, SCENES[4]["t1"] - 0.1)
T_COUNT = CUES["choix"][2][0]                          # « Tu as cinq secondes… »
T_FINAL = max(T_COUNT + 5, CUES["choix"][-1][0] - 0.3)


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


def draw_caption(frame, t, start, end, text, speak, pos):
    hl = HL
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
    y0 = {"top": 150, "bottom": H - box_h - 150}[pos]
    y0 += int((1 - a_in) * 40)  # glisse vers le haut en apparaissant
    box_w = max(d.textlength(" ".join(l), font=fnt) for l in lines) + 80
    x0 = (W - box_w) / 2
    d.rounded_rectangle([x0 + 10, y0 + 12, x0 + box_w + 10, y0 + box_h + 12], 34, fill=(0, 0, 0, 150))
    d.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], 34, fill=(255, 255, 255, 245),
                        outline=(0, 0, 0, 255), width=6)
    # mots révélés progressivement (effet « karaoké »)
    nwords = sum(len(l) for l in lines)
    shown = int(1 + nwords * (t - start) / max(0.5, speak * 0.9))
    k = 0
    for i, l in enumerate(lines):
        lw = d.textlength(" ".join(l), font=fnt)
        x = (W - lw) / 2
        y = y0 + 30 + i * lh
        for w in l:
            col = hl.get(w, hl.get(w.rstrip(",.?!…"), (15, 15, 15)))
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
    s, e = T_SMS
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
    if t > s + 1.2:
        cx, cy, r = W // 2, H - 360, 130
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 240), outline=(0, 0, 0, 255), width=10)
        ang = (t - s) * 2.4
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
    if T_COUNT <= t < T_COUNT + 5:
        n = 5 - int(t - T_COUNT)
        f = (t - T_COUNT) % 1.0
        sc = 1.6 - 0.6 * ease(f / 0.25)
        a = int(255 * (1 - max(0, f - 0.75) / 0.25))
        r = int(170 * sc)
        cx, cy = W // 2, H // 2 - 120
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, int(a * 0.92)), outline=(255, 255, 255, a), width=10)
        d.arc([cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18], -90, -90 + 360 * (1 - f), fill=RED + (a,), width=14)
        d.text((cx, cy), str(n), font=font(int(190 * sc)), fill=(255, 255, 255, a), anchor="mm")
    if t >= T_FINAL:
        p = ease((t - T_FINAL) / 0.4)
        pulse = 1 + 0.04 * math.sin((t - T_FINAL) * 8)
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
    s, e = T_X2, T_X2 + 2.6
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
    if t < SCENES[0]["t1"]:
        frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 50)))
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
def make_fx(path):
    """Bruitages discrets uniquement : souffle léger entre les scènes + notification du SMS."""
    n = int(SR * DUR)
    out = np.zeros(n)

    def add(sig, start):
        i = int(start * SR)
        out[i:i + len(sig)] += sig[: max(0, n - i)]

    d = 0.6
    k = np.arange(int(d * SR)) / SR
    noise = np.convolve(np.random.default_rng(1).standard_normal(len(k)), np.ones(60) / 60, "same")
    whoosh = 0.05 * noise * np.sin(np.pi * k / d) ** 2
    for sc in SCENES[1:]:
        add(whoosh, sc["t0"] - 0.4)
    for i, f in enumerate((1320, 1760)):
        k = np.arange(int(0.15 * SR)) / SR
        add(0.06 * np.sin(2 * np.pi * f * k) * np.exp(-k * 14), T_SMS[0] + 0.1 + i * 0.13)
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    wav = os.path.join(HERE, "_fx.wav")
    make_fx(wav)
    images = {sc["img"]: load(sc["img"]) for sc in SCENES}
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", VOICE, "-i", wav,
           "-filter_complex", "[1:a]volume=1.0[v];[2:a]volume=1.0[f];[v][f]amix=inputs=2:normalize=0,"
           "aformat=channel_layouts=stereo[a]", "-map", "0:v", "-map", "[a]",
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
