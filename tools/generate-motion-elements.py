#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Elements graphiques reutilisables - Hyperframes.

Releve sur les references InsiderForce (2026-09-10) : leur b-roll signature n'est
pas de la video, ce sont des FORMES PLATES enormes qui entrent par le bord du
cadre - mains, curseurs, marque-pages - plus une boite noire de surlignage sur
la phrase cle et des lignes de liaison a pastilles. C'est bon marche, c'est
reconnaissable, et c'est entierement reproductible en vectoriel.

Ici on produit les memes objets, mais a NOTRE charte : graphite, ivoire, acier,
bleu signal en ponctuation, et un rouge sobre reserve au negatif (le code couleur
semantique de la doctrine de retention).

Sortie : PNG avec alpha. Le montage les anime ; la bibliotheque ne fournit que la
forme - c'est ce qui les rend reutilisables.

Usage :
    python tools/generate-motion-elements.py [--only surlignage,curseurs,...]
"""
import os
import sys
import json
import shutil
import argparse
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "asset-library", "broll", "10-motion-elements")
TMP = os.path.join(ROOT, "temp", "_motion-svg")

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
          os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")]:
    if os.path.isfile(c):
        CHROME = c
        break

# charte
GRAPHITE = "#071017"
IVOIRE = "#F3F1EA"
ACIER = "#8D9AA1"
SIGNAL = "#22B9F2"
ROUGE = "#C8362B"      # rouge sobre : le negatif, jamais decoratif
VERT = "#137333"

_faits = []


def rendre(sous, nom, svg, w, h, desc):
    os.makedirs(TMP, exist_ok=True)
    hp = os.path.join(TMP, nom.replace(".png", ".html"))
    with open(hp, "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><html><head><meta charset='utf-8'><style>"
                 "*{margin:0;padding:0}html,body{width:%dpx;height:%dpx;background:transparent}"
                 "</style></head><body>%s</body></html>" % (w, h, svg))
    d = os.path.join(OUT, sous)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, nom)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000",
                    "--force-device-scale-factor=1", "--screenshot=%s" % out,
                    "--window-size=%d,%d" % (w, h), "--virtual-time-budget=1200",
                    "file:///%s" % hp.replace("\\", "/")],
                   capture_output=True, text=True, timeout=90)
    if not os.path.isfile(out):
        print("  ! echec %s" % nom)
        return
    _faits.append(dict(sous_categorie=sous, fichier=nom, description=desc))
    print("  %-52s %s" % (nom, desc))


def svg(w, h, corps, vb=None):
    """vb = viewBox explicite, pour dessiner une fois et sortir a plusieurs tailles."""
    x0, y0, x1, y1 = vb if vb else (0, 0, w, h)
    return ("<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d' "
            "viewBox='%g %g %g %g'>%s</svg>" % (w, h, x0, y0, x1, y1, corps))


# ------------------------------------------------------------------ SURLIGNAGE
def bloc_surlignage():
    """La boite pleine posee sous une phrase cle - device central de la reference."""
    print("\n[surlignages-traits]")
    s = "soulignements-traits"
    for nom, coul, txtc, desc in [
        ("surlignage_boite-graphite", GRAPHITE, IVOIRE, "boite pleine graphite - la phrase cle, texte ivoire par-dessus"),
        ("surlignage_boite-signal", SIGNAL, GRAPHITE, "boite pleine bleu signal - la preuve, le positif"),
        ("surlignage_boite-rouge", ROUGE, IVOIRE, "boite pleine rouge sobre - le negatif, ce qui est barre"),
        ("surlignage_boite-ivoire", IVOIRE, GRAPHITE, "boite pleine ivoire - phrase cle sur fond sombre"),
    ]:
        for i, (w, h) in enumerate([(900, 150), (1300, 150), (620, 150)], 1):
            rendre(s, "%s_%02d.png" % (nom, i),
                   svg(w, h, "<rect x='0' y='0' width='%d' height='%d' rx='14' fill='%s'/>" % (w, h, coul)),
                   w, h, "%s (%dx%d)" % (desc, w, h))

    # Traits de soulignement : la regle de charte dit 3-4 px sous un mot reste ivoire
    for nom, coul, ep, desc in [
        ("trait_signal-fin", SIGNAL, 5, "trait fin bleu signal - souligne un mot sans le remplir"),
        ("trait_signal-epais", SIGNAL, 11, "trait epais bleu signal - un mot decisif"),
        ("trait_ivoire", IVOIRE, 6, "trait ivoire - sur fond sombre"),
        ("trait_rouge", ROUGE, 7, "trait rouge sobre - marque le negatif"),
    ]:
        rendre(s, "%s.png" % nom,
               svg(900, 40, "<rect x='0' y='%d' width='900' height='%d' rx='%d' fill='%s'/>"
                   % (20 - ep // 2, ep, ep // 2, coul)),
               900, 40, desc)

    # Trait "trace a la main" : moins mecanique, plus editorial
    for nom, coul in [("trait_brosse-signal", SIGNAL), ("trait_brosse-ivoire", IVOIRE)]:
        rendre(s, "%s.png" % nom,
               svg(900, 60, "<path d='M14 40 C 200 22, 380 46, 560 30 S 830 24, 886 34' "
                            "stroke='%s' stroke-width='12' fill='none' stroke-linecap='round'/>" % coul),
               900, 60, "trait de brosse irregulier - soulignement editorial, moins mecanique")

    # Barre : le mot raye du negatif
    rendre(s, "barre_rature-rouge.png",
           svg(900, 40, "<path d='M10 22 L 890 18' stroke='%s' stroke-width='9' "
                        "stroke-linecap='round'/>" % ROUGE),
           900, 40, "rature - le mot barre de la paire negatif/positif")


# -------------------------------------------------------------------- CURSEURS
def bloc_curseurs():
    print("\n[curseurs-pointeurs]")
    s = "curseurs-pointeurs"
    fleche = ("<path d='M8 4 L8 78 L26 61 L38 88 L54 80 L42 54 L66 52 Z' "
              "fill='%s' stroke='%s' stroke-width='5' stroke-linejoin='round'/>")
    for nom, f, st, desc in [
        ("curseur_graphite", GRAPHITE, IVOIRE, "pointeur classique, graphite cercle d'ivoire"),
        ("curseur_ivoire", IVOIRE, GRAPHITE, "pointeur ivoire - sur fond sombre"),
        ("curseur_signal", SIGNAL, IVOIRE, "pointeur bleu signal - marque un clic decisif"),
    ]:
        for taille, sfx, note in [(1, "_01", ""),
                                  (3, "_geant_02", " — version geante, entre par le bord du cadre")]:
            rendre(s, "%s%s.png" % (nom, sfx),
                   svg(int(80 * taille), int(100 * taille), fleche % (f, st), vb=(0, 0, 80, 100)),
                   int(80 * taille), int(100 * taille), desc + note)

    # Main ouverte - l'element signature de la reference (leur main orange), a notre charte
    main = ("<g fill='%s' stroke='%s' stroke-width='6' stroke-linejoin='round'>"
            "<path d='M92 176 L92 74 a15 15 0 0 1 30 0 L122 132 L122 44 a15 15 0 0 1 30 0 "
            "L152 132 L152 56 a15 15 0 0 1 30 0 L182 136 L182 82 a15 15 0 0 1 30 0 L212 190 "
            "a62 62 0 0 1 -62 62 L128 252 a44 44 0 0 1 -36 -20 L52 168 a16 16 0 0 1 26 -18 Z'/></g>")
    for nom, f, st, desc in [
        ("main_ouverte-graphite", GRAPHITE, IVOIRE, "main ouverte, graphite - entre par le bord du cadre, tres grande"),
        ("main_ouverte-ivoire", IVOIRE, GRAPHITE, "main ouverte, ivoire - sur fond sombre"),
    ]:
        rendre(s, "%s.png" % nom, svg(280, 300, main % (f, st)), 280, 300, desc)

    # Clic : ondes concentriques
    rendre(s, "clic_ondes-signal.png",
           svg(240, 240, "".join("<circle cx='120' cy='120' r='%d' fill='none' stroke='%s' "
                                 "stroke-width='%d' opacity='%.2f'/>" % (r, SIGNAL, w, o)
                                 for r, w, o in [(28, 0, 0), (34, 8, .95), (62, 6, .55), (94, 4, .28)])
               + "<circle cx='120' cy='120' r='18' fill='%s'/>" % SIGNAL),
           240, 240, "ondes de clic - marque le point d'action")


# ------------------------------------------------------------------- LIAISONS
def bloc_liaisons():
    """Lignes a pastilles : le device schematique de Da5fhPriu3n."""
    print("\n[fleches-annotations]")
    s = "fleches-annotations"
    for nom, coul in [("liaison_coude-graphite", GRAPHITE), ("liaison_coude-signal", SIGNAL)]:
        rendre(s, "%s.png" % nom,
               svg(620, 340, "<path d='M24 24 L24 200 L596 200 L596 316' stroke='%s' stroke-width='7' "
                             "fill='none' stroke-linejoin='round'/>"
                             "<circle cx='24' cy='24' r='16' fill='%s'/>"
                             "<circle cx='596' cy='316' r='16' fill='%s'/>" % (coul, coul, coul)),
               620, 340, "ligne de liaison coudee a pastilles - relie deux elements du cadre")
    for nom, coul in [("liaison_droite-graphite", GRAPHITE), ("liaison_droite-signal", SIGNAL)]:
        rendre(s, "%s.png" % nom,
               svg(680, 60, "<path d='M22 30 L658 30' stroke='%s' stroke-width='7' stroke-linecap='round'/>"
                            "<circle cx='22' cy='30' r='15' fill='%s'/>"
                            "<circle cx='658' cy='30' r='15' fill='%s'/>" % (coul, coul, coul)),
               680, 60, "ligne de liaison droite a pastilles")

    # Fleches
    for nom, coul, d, desc in [
        ("fleche_courbe-droite", GRAPHITE, "M30 40 C 180 30, 340 70, 430 180",
         "fleche courbe vers la droite - designe un element"),
        ("fleche_courbe-gauche", GRAPHITE, "M450 40 C 300 30, 140 70, 50 180",
         "fleche courbe vers la gauche"),
        ("fleche_courbe-signal", SIGNAL, "M30 40 C 180 30, 340 70, 430 180",
         "fleche courbe bleu signal"),
    ]:
        pointe = "M430 180 l -34 -22 M430 180 l 6 -40" if "droite" in nom or "signal" in nom else "M50 180 l 34 -22 M50 180 l -6 -40"
        rendre(s, "%s.png" % nom,
               svg(500, 230, "<path d='%s' stroke='%s' stroke-width='9' fill='none' "
                             "stroke-linecap='round'/><path d='%s' stroke='%s' stroke-width='9' "
                             "fill='none' stroke-linecap='round'/>" % (d, coul, pointe, coul)),
               500, 230, desc)

    # Entourage manuscrit
    for nom, coul in [("entourage_signal", SIGNAL), ("entourage_rouge", ROUGE)]:
        rendre(s, "%s.png" % nom,
               svg(720, 260, "<path d='M360 22 C 120 22, 26 84, 26 130 C 26 182, 150 236, 372 236 "
                             "C 596 236, 694 178, 694 128 C 694 78, 580 26, 344 26' "
                             "stroke='%s' stroke-width='10' fill='none' stroke-linecap='round'/>" % coul),
               720, 260, "entourage trace a la main - isole un mot ou un chiffre")

    # Crochets
    for nom, coul in [("crochets_graphite", GRAPHITE), ("crochets_ivoire", IVOIRE)]:
        rendre(s, "%s.png" % nom,
               svg(760, 200, "<path d='M64 16 L20 16 L20 184 L64 184' stroke='%s' stroke-width='9' "
                             "fill='none' stroke-linecap='round'/>"
                             "<path d='M696 16 L740 16 L740 184 L696 184' stroke='%s' stroke-width='9' "
                             "fill='none' stroke-linecap='round'/>" % (coul, coul)),
               760, 200, "crochets d'encadrement - enserre un bloc de texte")


# --------------------------------------------------------------------- BADGES
def bloc_badges():
    """Badges numerotes : la doctrine demande #1 #2 #3 dans le panneau de preuve."""
    print("\n[compteurs-chiffres]")
    s = "compteurs-chiffres"
    police = ("font-family='Sora, Segoe UI, sans-serif' font-weight='700' "
              "text-anchor='middle' dominant-baseline='central'")
    for i in range(1, 6):
        for nom, fond, txt, desc in [
            ("badge_plein-graphite", GRAPHITE, IVOIRE, "badge numerote plein graphite"),
            ("badge_plein-signal", SIGNAL, GRAPHITE, "badge numerote plein bleu signal"),
        ]:
            rendre(s, "%s_%02d.png" % (nom, i),
                   svg(180, 180, "<circle cx='90' cy='90' r='86' fill='%s'/>"
                                 "<text x='90' y='94' %s font-size='84' fill='%s'>%d</text>"
                                 % (fond, police, txt, i)),
                   180, 180, "%s — %d" % (desc, i))
        rendre(s, "badge_contour-ivoire_%02d.png" % i,
               svg(180, 180, "<circle cx='90' cy='90' r='80' fill='none' stroke='%s' stroke-width='8'/>"
                             "<text x='90' y='94' %s font-size='80' fill='%s'>%d</text>"
                             % (IVOIRE, police, IVOIRE, i)),
               180, 180, "badge numerote en contour ivoire — %d" % i)


# --------------------------------------------------------------------- SYMBOLES
def bloc_symboles():
    print("\n[transitions]")
    s = "transitions"
    rendre(s, "symbole_coche-verte.png",
           svg(200, 200, "<circle cx='100' cy='100' r='94' fill='%s'/>"
                         "<path d='M56 104 L86 134 L146 68' stroke='#FFF' stroke-width='16' "
                         "fill='none' stroke-linecap='round' stroke-linejoin='round'/>" % VERT),
           200, 200, "coche pleine - ca a marche")
    rendre(s, "symbole_croix-rouge.png",
           svg(200, 200, "<circle cx='100' cy='100' r='94' fill='%s'/>"
                         "<path d='M66 66 L134 134 M134 66 L66 134' stroke='#FFF' stroke-width='16' "
                         "stroke-linecap='round'/>" % ROUGE),
           200, 200, "croix pleine - le negatif, ce qui ne marche pas")
    rendre(s, "symbole_coche-contour-verte.png",
           svg(200, 200, "<path d='M46 104 L86 144 L156 58' stroke='%s' stroke-width='18' "
                         "fill='none' stroke-linecap='round' stroke-linejoin='round'/>" % VERT),
           200, 200, "coche seule, sans pastille - plus discrete")
    for nom, coul, desc in [("etoile_signal", SIGNAL, "etoile a quatre branches - marqueur de liste"),
                            ("etoile_ivoire", IVOIRE, "meme etoile, ivoire")]:
        rendre(s, "%s.png" % nom,
               svg(160, 160, "<path d='M80 8 C 88 56, 104 72, 152 80 C 104 88, 88 104, 80 152 "
                             "C 72 104, 56 88, 8 80 C 56 72, 72 56, 80 8 Z' fill='%s'/>" % coul),
               160, 160, desc)
    # Bandes de transition pleine largeur
    for nom, coul, desc in [
        ("bande_balayage-graphite", GRAPHITE, "bande pleine graphite - balaie le cadre en transition"),
        ("bande_balayage-ivoire", IVOIRE, "bande pleine ivoire"),
        ("bande_balayage-signal", SIGNAL, "bande pleine bleu signal"),
    ]:
        rendre(s, "%s.png" % nom, svg(1080, 1920, "<rect width='1080' height='1920' fill='%s'/>" % coul),
               1080, 1920, desc)


BLOCS = {"surlignage": bloc_surlignage, "curseurs": bloc_curseurs,
         "liaisons": bloc_liaisons, "badges": bloc_badges, "symboles": bloc_symboles}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    if CHROME is None:
        print("Chrome introuvable")
        return 1
    for n in ([x.strip() for x in a.only.split(",")] if a.only else list(BLOCS)):
        if n not in BLOCS:
            print("bloc inconnu : %s" % n)
            return 1
        BLOCS[n]()
    with open(os.path.join(OUT, "_manifeste.json"), "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/generate-motion-elements.py",
                   "releve_sur": "references InsiderForce 2026-09-10",
                   "elements": _faits}, fh, ensure_ascii=False, indent=2)
    shutil.rmtree(TMP, ignore_errors=True)
    print("\n%d elements produits" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
