#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Index et planches-contact de la banque de logos - Hyperframes.

Produit :
  - LISEZ-MOI.md          : mode d'emploi + inventaire par secteur
  - _planches/<secteur>.jpg : planche-contact visuelle, pour choisir a l'oeil

Pourquoi des planches et pas 720 PNG : le pipeline consomme du SVG (il se
redimensionne sans perte et se recolore). Les PNG ne serviraient qu'a regarder —
autant une planche par secteur.

Usage :
    python tools/logos_index.py
"""
import os
import sys
import json
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "asset-library", "broll", "09-marques-et-logos")
PLANCHES = os.path.join(OUT, "_planches")
TMP = os.path.join(ROOT, "temp", "_logo-planches")

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
    if os.path.isfile(c):
        CHROME = c
        break


def planche(secteur, fichiers):
    """Rend tous les SVG d'un secteur en une grille, via une seule page Chrome."""
    if CHROME is None or not fichiers:
        return None
    cols = 8
    cell = 150
    lignes = (len(fichiers) + cols - 1) // cols
    cases = []
    for p in fichiers:
        try:
            svg = open(p, encoding="utf-8").read()
        except Exception:
            continue
        svg = svg.replace("<svg ", "<svg width='62' height='62' ", 1)
        nom = os.path.basename(p).replace("logo_", "").replace("_couleur.svg", "")
        cases.append("<div class='c'>%s<div class='n'>%s</div></div>" % (svg, nom[:18]))
    html = ("<!doctype html><meta charset='utf-8'><style>"
            "*{margin:0;padding:0;box-sizing:border-box}"
            "body{background:#FFF;font-family:'Segoe UI',sans-serif;"
            "display:grid;grid-template-columns:repeat(%d,%dpx)}"
            ".c{height:%dpx;display:flex;flex-direction:column;align-items:center;"
            "justify-content:center;gap:9px;border:1px solid #F0F0F0}"
            ".n{font-size:10.5px;color:#8A8A8A;text-align:center;line-height:1.2;"
            "max-width:130px;word-break:break-word}"
            "</style>%s" % (cols, cell, cell, "".join(cases)))
    os.makedirs(TMP, exist_ok=True)
    hp = os.path.join(TMP, "%s.html" % secteur)
    with open(hp, "w", encoding="utf-8") as fh:
        fh.write(html)
    os.makedirs(PLANCHES, exist_ok=True)
    png = os.path.join(PLANCHES, "%s.png" % secteur)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--screenshot=%s" % png,
                    "--window-size=%d,%d" % (cols * cell, lignes * cell),
                    "--virtual-time-budget=2500", "file:///%s" % hp.replace("\\", "/")],
                   capture_output=True, text=True, timeout=180)
    if os.path.isfile(png):
        jpg = png.replace(".png", ".jpg")
        Image.open(png).convert("RGB").save(jpg, quality=84, optimize=True)
        os.remove(png)
        return os.path.basename(jpg)
    return None


# Pertinence par secteur. Retour du createur (2026-09-10) : certains logos "ne
# serviront vraiment jamais". Plutot que de les supprimer — un logo manquant bloque
# un montage, un logo inutilise ne coute rien — on les signale, et on garde.
PERIPHERIQUES = {
    "17-secteurs-clients": "périphérique — utile seulement si la vidéo cite le secteur d'un client "
                           "(livraison, commerce, transport). L'automobile, la mode et la restauration "
                           "n'ont à peu près aucune chance de servir.",
    "19-jeux-divertissement": "périphérique — hors niche, sauf Discord et Twitch (communauté). "
                              "Gardé au cas où, à ne pas parcourir en cherchant un outil.",
    "16-education-medias": "mixte — les plateformes d'apprentissage et les médias tech servent ; "
                           "le streaming grand public, non.",
}


def main():
    man = os.path.join(OUT, "_manifeste.json")
    logos = json.load(open(man, encoding="utf-8")).get("logos", []) if os.path.exists(man) else []
    par_slug = {l["slug"]: l for l in logos if l.get("slug")}

    secteurs = {}
    for r, _, fs in os.walk(OUT):
        if "_planches" in r or "_a-verifier" in r:
            continue    # la quarantaine n'est pas la bibliotheque
        sec = os.path.relpath(r, OUT).replace("\\", "/")
        if sec in (".",):
            continue
        # _couleur.svg = Simple Icons (monochrome) · _officiel.svg = Commons (vraies couleurs)
        svgs = sorted(os.path.join(r, f) for f in fs
                      if f.endswith("_couleur.svg") or f.endswith("_officiel.svg"))
        if svgs:
            secteurs[sec] = svgs

    total = sum(len(v) for v in secteurs.values())
    multi = sum(1 for l in logos if l.get("multicolore"))
    arch = sum(1 for l in logos if l.get("source_archive"))
    introuvables = json.load(open(man, encoding="utf-8")).get("introuvables", []) if os.path.exists(man) else []

    L = ["# Banque de logos produits",
         "",
         "> Générée par `tools/fetch-logos-massif.py`, indexée par `tools/logos_index.py`.",
         "> Source : tracés officiels Simple Icons, rendus à la **couleur officielle de la marque**.",
         "",
         "## Pourquoi cette banque existe",
         "",
         "Règle permanente du projet : **tout nom de marque prononcé porte son logo à l'écran**.",
         "Un logo se lit plus vite qu'un mot, il renforce l'autorité, et il professionnalise le plan.",
         "La référence du monteur fait exactement ça — elle affiche le logo de l'outil pendant",
         "qu'elle en parle, y compris ses propres outils de montage.",
         "",
         "Tailles planchers mesurées : **42 px** en tuile de grille, **36 px** en barre de titre de",
         "carte, **150 px** en plein cadre, à 0,96 d'opacité. Un logo trop petit ne fait pas le travail.",
         "",
         "## État",
         "",
         "| | |", "|---|---:|",
         "| Logos | **%d** |" % total,
         "| Secteurs | %d |" % len(secteurs),
         "| Marques absentes du catalogue courant, reprises d'une version archivée | %d |" % arch,
         "| Marques que je sais multicolores (colorimétrie approchée) | %d |" % multi,
         "| Demandées mais introuvables | %d |" % len(introuvables),
         "",
         "Chaque marque existe en **deux fichiers** :",
         "- `logo_<slug>_couleur.svg` — couleur officielle de la marque, **le défaut**",
         "- `logo_<slug>_ivoire.svg` — monochrome ivoire, pour une **liste de connecteurs**",
         "  (trois logos saturés côte à côte font un mur de logos) ou un fond sombre",
         "",
         "## ⚠️ Trois limites à connaître avant de poser un logo",
         "",
         "**1. Les tracés sont monochromes.** Pour une marque nativement monochrome (Anthropic,",
         "OpenAI, GitHub, Notion, Vercel…) c'est le logo exact. Pour une marque multicolore ou en",
         "dégradé (Figma, Google, Slack, Instagram…), **la forme est officielle mais pas la",
         "colorimétrie**. Le champ `multicolore` du manifeste marque celles que je sais être dans",
         "ce cas — son absence ne vaut pas vérification. Si la marque est le **sujet** du plan,",
         "aller chercher son lockup officiel sur sa page presse.",
         "",
         "**2. Certaines marques viennent d'une version archivée du catalogue.** Elles en ont été",
         "retirées pour raisons de marque déposée (OpenAI, LinkedIn, Amazon, Xbox, Disney, la",
         "plupart des médias). Les afficher pendant qu'on **parle d'elles** est un usage nominatif,",
         "éditorial — c'est le cas d'usage ici. Ne pas s'en servir pour suggérer un partenariat,",
         "une approbation ou une affiliation.",
         "",
         "**3. Ne jamais peindre un logo d'une couleur par défaut.** Une première version colorait",
         "en noir tout logo absent du CDN : LinkedIn, Amazon, Adobe et Canva se sont retrouvés en",
         "silhouette noire alors qu'ils sont bleu, orange, rouge et cyan. Un logo sans couleur",
         "officielle doit échouer bruyamment, pas être inventé.",
         "",
         "**4. Un dossier `_a-verifier/` existe.** Il contient les logos dont la correspondance",
         "n'est pas certaine : la recherche a trouvé un fichier au nom approchant, pas exact",
         "(« Chroma » ramenait *ChromaDex*, « Tally » ramenait *Tally Hall*, le groupe). Ils ne",
         "sont **pas** dans la bibliothèque et ne doivent pas être utilisés sans ouvrir le fichier.",
         "",
         "**5. Trois secteurs sont marqués ⚪ périphériques.** Ils sont gardés — un logo manquant",
         "bloque un montage en cours, un logo inutilisé ne coûte rien — mais ils ne sont pas à",
         "parcourir quand on cherche un outil de la niche.",
         "",
         "## Planches-contact",
         "",
         "Une image par secteur dans `_planches/` — pour choisir à l'œil sans ouvrir 720 fichiers.",
         ""]

    for sec in sorted(secteurs):
        fs = secteurs[sec]
        p = planche(sec, fs)
        noms = []
        for f in fs:
            b = os.path.basename(f)
            officiel = b.endswith("_officiel.svg")
            slug = b.replace("logo_", "").replace("_couleur.svg", "").replace("_officiel.svg", "")
            e = par_slug.get(slug, {})
            marque = ""
            if e.get("multicolore"):
                marque = " ⚠️"
            if e.get("source_archive"):
                marque += " 📦"
            if officiel:
                marque = " ⭐"   # Commons : vraies couleurs, pas une silhouette
            noms.append("`%s`%s" % (slug, marque))
        note_p = PERIPHERIQUES.get(sec)
        L += ["### %s — %d%s" % (sec, len(fs), "  ⚪" if note_p else ""), ""]
        if note_p:
            L += ["> ⚪ **%s**" % note_p, ""]
        if p:
            L += ["![%s](_planches/%s)" % (sec, p), ""]
        L += [" · ".join(noms), ""]
        print("  %-26s %3d logos%s" % (sec, len(fs), "  (planche ok)" if p else ""))

    L += ["---", "",
          "Légende : ⭐ logo officiel en vraies couleurs (Wikimedia Commons) · ⚠️ colorimétrie approchée "
          "(silhouette monochrome d'une marque multicolore) · 📦 repris d'une version archivée du catalogue",
          "",
          "## Introuvables — à sourcer à la main",
          "",
          "Ces marques ne sont dans aucune version du catalogue. Si l'une d'elles doit apparaître,",
          "récupérer son logo sur **sa propre page presse / brand kit**.",
          ""]
    if introuvables:
        L += [" · ".join("%s" % i["nom"] for i in introuvables), ""]

    with open(os.path.join(OUT, "LISEZ-MOI.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
    print("\n%d logos · %d secteurs · index ecrit" % (total, len(secteurs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
