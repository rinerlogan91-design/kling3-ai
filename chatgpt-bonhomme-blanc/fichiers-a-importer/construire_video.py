"""Bonhomme blanc — fabrique la page vidéo à partir d'un scénario JSON.

Usage (dans l'outil Python de ChatGPT) :

    exec(open('/mnt/data/construire_video.py', encoding='utf-8').read())
    chemin = construire(scene)            # scene = dict Python du scénario
    # -> /mnt/data/<titre>.html : à donner à l'utilisateur en lien de téléchargement

La fonction vérifie le scénario, intègre les images de l'utilisateur et écrit une page
HTML autonome. L'utilisateur l'ouvre dans Chrome/Edge/Safari et clique « Exporter en MP4 ».
"""
import base64
import io
import json
import os
import re

TYPES = {'desk', 'arch', 'image', 'monitor', 'window', 'tiles', 'workstation', 'money', 'stairs', 'bubble', 'rings', 'trafficlight', 'crowd', 'text', 'counter', 'caption', 'spotlight', 'line', 'progress', 'card', 'chart', 'ground', 'icon', 'character', 'timer', 'shape'}  # remplacé à la construction du kit
POSES = {"stand", "cheer", "work", "point", "phone", "sit", "run", "fallen", "worry", "refuse", "give"}
ICONS = {"lock", "unlock", "warning", "check", "cross", "clock", "briefcase", "play", "dollar", "search",
         "battery", "people", "city", "arrow", "heart", "star", "bulb", "ring", "flower"}
MARKS = {"", "joy", "shock", "sweat", "scribble"}
ENTREES = {"fade", "pop", "slam", "up", "type", "none"}
EASES = {"linear", "in", "out", "inOut", "outBack", "inExpo", "outExpo"}
SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}


def _dossiers(extra=None):
    out = [d for d in [extra, "/mnt/data", os.getcwd(), os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None] if d]
    return list(dict.fromkeys(out))


def _trouver(nom, dossiers):
    if os.path.isabs(nom) and os.path.exists(nom):
        return nom
    for d in dossiers:
        p = os.path.join(d, nom)
        if os.path.exists(p):
            return p
    # correspondance approximative (ChatGPT renomme parfois les fichiers envoyés)
    base = os.path.splitext(os.path.basename(nom))[0].lower()
    for d in dossiers:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if base and base in f.lower() and os.path.splitext(f)[1].lower() in MIME:
                    return os.path.join(d, f)
    return None


def _image_data_url(chemin):
    ext = os.path.splitext(chemin)[1].lower()
    try:
        from PIL import Image  # réduit les grosses images pour garder une page légère
        im = Image.open(chemin)
        im.thumbnail((1600, 1600))
        buf = io.BytesIO()
        if im.mode in ("RGBA", "LA", "P"):
            im.save(buf, "PNG"); mime = "image/png"
        else:
            im.convert("RGB").save(buf, "JPEG", quality=86); mime = "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        with open(chemin, "rb") as f:
            return f"data:{MIME.get(ext, 'image/png')};base64," + base64.b64encode(f.read()).decode()


def _est_kf(v):
    return isinstance(v, list) and v and all(isinstance(i, list) and len(i) >= 2 and isinstance(i[0], (int, float)) for i in v)


def verifier(scene):
    """Renvoie (erreurs, avertissements). Les erreurs empêchent la construction."""
    err, warn = [], []
    if not isinstance(scene, dict) or not isinstance(scene.get("scenes"), list) or not scene["scenes"]:
        return ["Le scénario doit être un objet avec \"scenes\": [ ... ] non vide."], []
    W, H = SIZES.get(scene.get("format", "16:9"), (1920, 1080))
    W, H = scene.get("width", W), scene.get("height", H)
    images = scene.get("images", {}) or {}
    total = 0
    for si, sc in enumerate(scene["scenes"], 1):
        d = sc.get("duration")
        if not isinstance(d, (int, float)) or d <= 0:
            err.append(f"Scène {si} : \"duration\" manquante ou invalide."); d = 0
        total += d or 0
        if sc.get("transition", "cut") not in ("cut", "flash", "fade"):
            warn.append(f"Scène {si} : transition inconnue {sc.get('transition')!r} (cut, flash, fade).")
        for ei, e in enumerate(sc.get("elements", []), 1):
            ou = f"Scène {si}, élément {ei} ({e.get('type')})"
            if e.get("type") not in TYPES:
                err.append(f"{ou} : type inconnu. Types valides : {', '.join(sorted(TYPES))}."); continue
            for k, v in e.items():
                if isinstance(v, list) and v and isinstance(v[0], list) and not _est_kf(v) and k != "points":
                    err.append(f"{ou} : keyframes mal formées pour {k!r} (attendu [[t, valeur, \"ease\"], ...]).")
                if _est_kf(v) and k not in ("points",):
                    for item in v:
                        if len(item) > 2 and item[2] not in EASES:
                            warn.append(f"{ou} : ease inconnue {item[2]!r} pour {k!r}.")
                        if isinstance(item[0], (int, float)) and d and item[0] > d + 0.01:
                            warn.append(f"{ou} : keyframe à {item[0]} s au-delà de la durée de la scène ({d} s).")
            if e.get("in") and e["in"] not in ENTREES:
                warn.append(f"{ou} : animation d'entrée inconnue {e['in']!r}.")
            if isinstance(e.get("at"), (int, float)) and d and e["at"] >= d:
                warn.append(f"{ou} : apparaît à {e['at']} s mais la scène ne dure que {d} s (invisible).")
            pose = e.get("pose")
            for p in ([i[1] for i in pose] if _est_kf(pose) else [pose] if pose else []):
                if p not in POSES:
                    err.append(f"{ou} : pose inconnue {p!r}. Poses : {', '.join(sorted(POSES))}.")
            marks = e.get("marks")
            for m in ([i[1] for i in marks] if _est_kf(marks) else [marks] if marks is not None else []):
                if m not in MARKS:
                    warn.append(f"{ou} : marks inconnu {m!r} (joy, shock, sweat, scribble).")
            if e["type"] == "icon" and e.get("name") not in ICONS:
                warn.append(f"{ou} : icône inconnue {e.get('name')!r}. Icônes : {', '.join(sorted(ICONS))}.")
            if e.get("src") and e["src"] not in images:
                err.append(f"{ou} : image {e['src']!r} absente de \"images\".")
            # textes trop larges (estimation)
            if e["type"] in ("text", "caption") and isinstance(e.get("text"), str):
                size = e.get("size", 120 if e["type"] == "text" else 34)
                if isinstance(size, (int, float)):
                    sp = e.get("spacing", 0.05 if e["type"] == "text" else 0.2)
                    sp = sp if isinstance(sp, (int, float)) else 0.05
                    larg = max(len(l) for l in e["text"].split("\n")) * size * (0.68 + sp)
                    if larg > W * 0.9:
                        warn.append(f"{ou} : texte « {e['text'][:30]} » probablement trop large "
                                    f"(~{int(larg)} px pour {W} px). Réduis \"size\" ou coupe avec \\n.")
            for k, lim in (("x", W), ("y", H)):
                v = e.get(k)
                if isinstance(v, (int, float)) and not (-50 <= v <= lim + 50) and e["type"] not in ("ground", "money"):
                    warn.append(f"{ou} : {k}={v} hors de l'image ({W}×{H}).")
    if total > 180:
        warn.append(f"Vidéo longue ({total:.0f} s) : l'export prendra plusieurs minutes.")
    return err, warn


def construire(scene, nom=None, dossier="/mnt/data", studio=None):
    """Vérifie le scénario, intègre les images et écrit la page HTML. Renvoie le chemin."""
    if isinstance(scene, str):
        scene = json.loads(open(scene, encoding="utf-8").read() if os.path.exists(scene) else scene)
    scene = json.loads(json.dumps(scene))
    err, warn = verifier(scene)
    for w in warn:
        print("⚠", w)
    if err:
        for e in err:
            print("✖", e)
        raise ValueError(f"{len(err)} erreur(s) dans le scénario : corrige-les puis relance construire().")
    dossiers = _dossiers(dossier if os.path.isdir(dossier) else None)
    for k, v in list((scene.get("images") or {}).items()):
        if isinstance(v, str) and v.startswith("data:"):
            continue
        p = _trouver(v, dossiers)
        if not p:
            raise FileNotFoundError(f"Image {v!r} (clé {k!r}) introuvable dans {dossiers}.")
        scene["images"][k] = _image_data_url(p)
        print(f"✓ image {k!r} intégrée depuis {os.path.basename(p)}")
    studio = studio or _trouver("bonhomme-blanc-studio.html", dossiers)
    if not studio:
        raise FileNotFoundError("bonhomme-blanc-studio.html introuvable (fichier de connaissance du GPT).")
    html = open(studio, encoding="utf-8").read()
    marque = '<script id="scene-data" type="application/json">null</script>'
    if marque not in html:
        raise ValueError("Le fichier studio n'est pas le modèle vierge attendu.")
    titre = nom or scene.get("title") or "video-bonhomme-blanc"
    titre = re.sub(r"[^\w\-]+", "-", titre.lower()).strip("-") or "video-bonhomme-blanc"
    scene["title"] = titre
    payload = json.dumps(scene, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace(marque, f'<script id="scene-data" type="application/json">{payload}</script>')
    out_dir = dossier if os.path.isdir(dossier) else os.getcwd()
    chemin = os.path.join(out_dir, titre + ".html")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(html)
    duree = sum(s.get("duration", 0) for s in scene["scenes"])
    print(f"✓ Page créée : {chemin}  ({len(scene['scenes'])} scènes, {duree:.1f} s, {len(html) // 1024} Ko)")
    return chemin
