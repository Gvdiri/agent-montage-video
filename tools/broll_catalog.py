#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Catalogue de la bibliotheque b-roll - Hyperframes.

Scanne asset-library/broll/ et reecrit :
  - catalogue.json  : machine, une entree par fichier (dimensions, poids, origine)
  - 00-INDEX.md     : humain, la carte de la bibliotheque

Pourquoi un index genere et pas ecrit a la main : le createur a demande une vraie
structure "pour ne pas tout mettre en vrac", et note qu'un vrac "consomme plus de
tokens". Un index ecrit a la main devient faux des le premier ajout. Celui-ci se
regenere.

Usage :
    python tools/broll_catalog.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")
EXT = {".png", ".jpg", ".jpeg", ".mp4", ".webm", ".mov", ".gif", ".svg"}

# A quoi sert chaque categorie, et surtout QUAND s'en servir au montage.
CATEGORIES = {
    "01-ecrans-produits": (
        "Captures reelles de pages publiques de produits nommes.",
        "Quand la voix nomme un outil precis. C'est la seule categorie qui doit rester "
        "**reelle** : fabriquer l'ecran d'un produit nomme serait une affirmation factuelle, "
        "pas une illustration."),
    "02-ecrans-generiques": (
        "Interfaces generiques, sans marque : terminal, chat IA, tableau de bord, CRM, boite mail.",
        "Le fond de preuve par defaut. Reutilisable d'une video a l'autre. Ne nomme rien, "
        "donc n'affirme rien."),
    "03-mains-et-appareils": (
        "Mains qui scrollent, qui tapent, telephone tenu, souris.",
        "Le geste humain. A poser entre deux plans de preuve pour reposer l'oeil."),
    "04-lieux-et-bureaux": (
        "Bureaux, cafes, open spaces, interieurs.",
        "Le contexte. Sert d'etablissement ou de respiration."),
    "05-humain-au-travail": (
        "Quelqu'un devant un ecran, en reunion, en pause, debordé.",
        "Le miroir de l'audience. Sert surtout a incarner le probleme avant la solution."),
    "06-fonds-et-textures": (
        "Fonds, gradients, grains, grilles, voiles, balayages — generes a la charte.",
        "Sous un titre, derriere une carte, ou en surimpression. Le voile de couture du split "
        "et les voiles de lisibilite vivent ici : ils sont imposes par le standard de montage."),
    "07-objets-et-details": (
        "Clavier en macro, reflets d'ecran, objets de bureau, papier.",
        "Le detail qui donne de la matiere. Plan court, jamais porteur de sens seul."),
    "08-business-et-preuve": (
        "Courbes, notifications de vente, messages prives, factures.",
        "La preuve de resultat, et le mecanisme du CTA (mot-cle en commentaire -> message prive)."),
    "09-marques-et-logos": (
        "SVG officiels des produits cites.",
        "Regle permanente : tout nom de marque prononce porte son logo. Couleurs produit par defaut."),
    "10-motion-elements": (
        "Elements reutilisables a animer : curseurs, soulignements, fleches, compteurs.",
        "Le montage les anime ; la bibliotheque ne fournit que la forme."),
}

ORIGINES = [
    ("06-fonds-et-textures", "genere par `tools/generate-backgrounds.py` (procedural, a la charte)"),
    ("traitements", "variante produite par `tools/broll_treatments.py`"),
    ("02-ecrans-generiques", "construit en HTML puis rendu par `tools/generate-ui-screens.py`"),
    ("08-business-et-preuve", "construit en HTML puis rendu par `tools/generate-ui-screens.py`"),
]


def origine(rel):
    for cle, lib in ORIGINES:
        if cle in rel:
            return lib
    return "depose a la main"


def dims(p):
    if os.path.splitext(p)[1].lower() in {".png", ".jpg", ".jpeg", ".gif"}:
        try:
            with Image.open(p) as im:
                return im.size
        except Exception:
            return None
    return None


def main():
    assets = []
    for r, _, fs in os.walk(BROLL):
        # Ne sont pas des assets : le tri ecarte, la quarantaine des logos douteux,
        # et les planches-contact (ce sont des index, pas du b-roll).
        rel_r = os.path.relpath(r, BROLL).replace("\\", "/")
        if any(x in rel_r.split("/") for x in ("_ecartes", "_a-verifier", "_planches")):
            continue
        for f in sorted(fs):
            if os.path.splitext(f)[1].lower() not in EXT:
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, BROLL).replace("\\", "/")
            d = dims(p)
            assets.append(dict(
                fichier=f, chemin=rel,
                categorie=rel.split("/")[0],
                sous_categorie=rel.split("/")[1] if rel.count("/") >= 2 else "",
                largeur=d[0] if d else None, hauteur=d[1] if d else None,
                octets=os.path.getsize(p), origine=origine(rel),
                # Un clip video est DERIVE d'une image deja comptee (derive, defilement,
                # curseur) : le compter comme un sujet nouveau gonflerait artificiellement
                # la couverture de la bibliotheque.
                variante=("traitements" in rel or "/video/" in rel
                          or rel.endswith("_ivoire.svg")),   # meme logo, autre teinte
                anime=rel.endswith((".mp4", ".webm")),
            ))

    with open(os.path.join(BROLL, "catalogue.json"), "w", encoding="utf-8") as fh:
        json.dump({"total": len(assets),
                   "sujets_distincts": len([a for a in assets if not a["variante"]]),
                   "assets": assets}, fh, ensure_ascii=False, indent=2)

    distincts = [a for a in assets if not a["variante"]]
    variantes = [a for a in assets if a["variante"]]

    L = ["# Bibliotheque B-roll — index",
         "",
         "> Genere par `tools/broll_catalog.py`. **Ne pas editer a la main.**",
         "> `catalogue.json` porte le detail machine (dimensions, poids, origine).",
         "",
         "## Etat",
         "",
         "| | |",
         "|---|---:|",
         "| Fichiers | **%d** |" % len(assets),
         "| Sujets visuels distincts | **%d** |" % len(distincts),
         "| Variantes de presentation | %d |" % len(variantes),
         "| dont clips video derives | %d |" % len([a for a in variantes if a.get("anime")]),
         "",
         "Les variantes sont des traitements du meme sujet — carte flottante, inclinaison,",
         "pile, flou, **et les clips video** (derive, defilement, curseur), qui mettent en",
         "mouvement une image deja comptee. Elles servent : on prend l'inclinee sur une",
         "video et la pile sur une autre pour ne pas se repeter. Mais",
         "autre pour ne pas se repeter. Mais **ce ne sont pas des sujets nouveaux** — a ne pas",
         "compter comme tels quand on evalue la couverture de la bibliotheque.",
         "",
         "## Nommage",
         "",
         "`<type>_<description-parlante>_<nn>.<ext>` — lisible isole, sans son dossier.",
         "Les variantes ajoutent le traitement en suffixe : `..._incline-droite.png`.",
         "",
         "## Categories",
         ""]

    for cat in sorted(CATEGORIES):
        dedans = [a for a in assets if a["categorie"] == cat]
        quoi, quand = CATEGORIES[cat]
        d_ = len([a for a in dedans if not a["variante"]])
        etat = "**vide**" if not dedans else "%d fichiers · %d sujets" % (len(dedans), d_)
        L += ["### `%s` — %s" % (cat, etat), "", quoi, "", "*Quand :* %s" % quand, ""]
        if not dedans:
            L += ["> ⚠️ Categorie vide. Elle demande des images photo-realistes que la chaine",
                  "> actuelle ne sait pas produire (voir la note en bas).", ""]
            continue
        subs = sorted({a["sous_categorie"] for a in dedans if a["sous_categorie"]})
        for s in subs:
            ss = [a for a in dedans if a["sous_categorie"] == s and not a["variante"]]
            if not ss:
                continue
            L += ["<details><summary><b>%s</b> — %d</summary>" % (s, len(ss)), "",
                  "| fichier | taille |", "|---|---|"]
            for a in sorted(ss, key=lambda x: x["fichier"]):
                t = "%dx%d" % (a["largeur"], a["hauteur"]) if a["largeur"] else "video"
                L.append("| `%s` | %s |" % (a["fichier"], t))
            L += ["", "</details>", ""]

    L += ["---", "",
          "## Provenance et licences",
          "",
          "| Catégorie | Origine | Licence |",
          "|---|---|---|",
          "| `01` captures produits | Chrome headless sur pages publiques | capture factuelle |",
          "| `02` écrans génériques | construits en HTML, rendus par Chrome | à nous |",
          "| `03` `04` `05` `07` photos | Openverse, filtre **CC0 uniquement** | domaine public, usage commercial libre, aucune attribution exigée |",
          "| `06` fonds et textures | procédural, à la charte | à nous |",
          "| `09` logos | `cdn.simpleicons.org` — tracé officiel + couleur de marque | voir `09-marques-et-logos/LISEZ-MOI.md` |",
          "| `10` éléments graphiques | vectoriel, à la charte | à nous |",
          "",
          "## Deux pièges à connaître",
          "",
          "**Les photos de banque ne sont pas à la charte.** Elles sont brutes : les étalonner",
          "avant usage (graphite/ivoire dominants, peau chaude préservée). `tools/broll_triage.py`",
          "a déjà écarté les plus datées sur mesure (saturation, dominante colorée, netteté) —",
          "elles sont dans les dossiers `_ecartes/`, pas supprimées. **L'œil garde le dernier mot.**",
          "",
          "**Les logos `simplifié` ne sont pas la vraie colorimétrie de la marque.** Simple Icons",
          "ne fournit qu'un tracé monochrome. Pour une marque multicolore (Figma, Google, Slack…),",
          "la forme est officielle mais pas les couleurs : bon pour une liste de connecteurs,",
          "à remplacer par le lockup officiel si la marque est le **sujet** du plan.",
          "",
          "## Comment on ajoute",
          "",
          "| Besoin | Outil |",
          "|---|---|",
          "| Un fond, une texture, un voile | `python tools/generate-backgrounds.py` |",
          "| Un écran d'interface générique | `python tools/generate-ui-screens.py` |",
          "| Une capture réelle de page produit | `python tools/capture-product-pages.py` |",
          "| Un logo produit | `python tools/fetch-logos.py` |",
          "| Des photos (mains, bureaux, personnes) | `python tools/fetch-stock-broll.py` puis `broll_triage.py --appliquer` |",
          "| Une forme graphique (curseur, flèche, badge) | `python tools/generate-motion-elements.py` |",
          "| Habiller une capture (carte, inclinaison, pile) | `python tools/broll_treatments.py <image>` |",
          "",
          "Après tout ajout : `python tools/broll_catalog.py` pour régénérer cet index.",
          ""]

    with open(os.path.join(BROLL, "00-INDEX.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    print("%d fichiers · %d sujets distincts · %d variantes"
          % (len(assets), len(distincts), len(variantes)))
    for cat in sorted(CATEGORIES):
        n = len([a for a in assets if a["categorie"] == cat])
        d_ = len([a for a in assets if a["categorie"] == cat and not a["variante"]])
        print("  %-24s %4d fichiers  %3d sujets%s" % (cat, n, d_, "   << VIDE" if n == 0 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
