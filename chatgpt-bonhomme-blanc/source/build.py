#!/usr/bin/env python3
"""Régénère le kit ChatGPT à partir du skill Claude (moteur, référence, exemples).

    python3 chatgpt-bonhomme-blanc/source/build.py

À relancer après toute modification de .claude/skills/bonhomme-blanc/.
"""
import json
import pathlib
import re
import shutil
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parent
SKILL = KIT.parent / ".claude" / "skills" / "bonhomme-blanc"
FILES = KIT / "fichiers-a-importer"


def main():
    FILES.mkdir(exist_ok=True)
    engine = (SKILL / "engine" / "engine.js").read_text(encoding="utf-8")
    template = (HERE / "studio.template.html").read_text(encoding="utf-8")
    assert "/*__ENGINE__*/" in template
    studio = template.replace("/*__ENGINE__*/", engine.replace("</script", "<\\/script"))
    (FILES / "bonhomme-blanc-studio.html").write_text(studio, encoding="utf-8")

    shutil.copy(SKILL / "reference" / "elements.md", FILES / "reference-elements.md")
    for name in ("demo", "mariage"):
        data = json.loads((SKILL / "examples" / f"{name}.json").read_text(encoding="utf-8"))
        (FILES / f"exemple-{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    block = engine[engine.index("const DRAW = {"):engine.index("function drawCover")]
    types = sorted(set(re.findall(r"^    (\w+)\(c,", block, re.M)))
    assert "text" in types and "timer" in types, types
    cv = (HERE / "construire_video.py").read_text(encoding="utf-8").replace("__TYPES__", repr(set(types)))
    (FILES / "construire_video.py").write_text(cv, encoding="utf-8")
    shutil.copy(HERE / "guide-style.md", FILES / "guide-style.md")

    # Exemple prêt à ouvrir, pour tester le Studio sans ChatGPT.
    demo = json.loads((SKILL / "examples" / "mariage.json").read_text(encoding="utf-8"))
    demo["title"] = "exemple-mariage"
    payload = json.dumps(demo, ensure_ascii=False).replace("</", "<\\/")
    test = studio.replace('<script id="scene-data" type="application/json">null</script>',
                          f'<script id="scene-data" type="application/json">{payload}</script>')
    (KIT / "tester-exemple-mariage.html").write_text(test, encoding="utf-8")

    zpath = KIT / "kit-chatgpt-bonhomme-blanc.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ["INSTALLATION.md", "instructions-gpt.txt", "tester-exemple-mariage.html"]:
            z.write(KIT / f, f)
        for f in sorted(FILES.iterdir()):
            z.write(f, f"fichiers-a-importer/{f.name}")
    print("Kit régénéré :", zpath)


if __name__ == "__main__":
    main()
