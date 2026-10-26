#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Traitements de presentation pour n'importe quelle capture - Hyperframes.

Releve sur les references InsiderForce (Da5fhPriu3n, DcJUMc8AjDv, DcOemduleSH,
analysees le 2026-09-10) : leurs captures ne sont JAMAIS posees a plat. Elles
sont systematiquement traitees - coins arrondis, ombre portee profonde, legere
rotation, parfois empilees en pile de cartes. C'est ce traitement qui fait la
valeur percue, pas la capture elle-meme.

D'ou le choix d'en faire un OUTIL et pas des PNG figes : applique a nos 25 ecrans
generes, il produit des dizaines de variantes ; et il marchera aussi sur les
captures reelles qu'on fera plus tard. Un PNG fige ne sert qu'une fois.

Tous les rendus sortent en PNG avec ALPHA : la carte flotte, le montage
choisit le fond derriere.

Usage :
    python tools/broll_treatments.py <image|dossier> [...] [--out DOSSIER]
                                     [--traitements carte,incline,pile,...]
"""
import os
import sys
import math
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

_faits = []


# ---------------------------------------------------------------------- outils
def coins_arrondis(im, rayon):
    im = im.convert("RGBA")
    masque = Image.new("L", im.size, 0)
    ImageDraw.Draw(masque).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1],
                                             radius=rayon, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), masque)
    return out


def ombre(im, flou=34, dy=26, dx=0, opacite=104, etal=6):
    """Ombre portee douce et profonde, comme sur les cartes de la reference."""
    marge = flou * 3 + max(abs(dx), abs(dy)) + etal + 10
    toile = Image.new("RGBA", (im.size[0] + marge * 2, im.size[1] + marge * 2),
                      (0, 0, 0, 0))
    alpha = im.split()[-1]
    if etal:
        alpha = alpha.filter(ImageFilter.MaxFilter(etal * 2 + 1))
    forme = Image.new("RGBA", im.size, (6, 12, 20, opacite))
    forme.putalpha(Image.eval(alpha, lambda v: int(v * opacite / 255)))
    toile.paste(forme, (marge + dx, marge + dy), forme)
    toile = toile.filter(ImageFilter.GaussianBlur(flou))
    toile.paste(im, (marge, marge), im)
    return toile


def incliner(im, angle_x=0.0, angle_y=16.0, echelle=1.0):
    """Perspective simple : on rapproche deux coins pour simuler une rotation.
    angle_y > 0 = le bord droit s'eloigne."""
    w, h = im.size
    ky = math.tan(math.radians(min(abs(angle_y), 42))) * 0.5
    kx = math.tan(math.radians(min(abs(angle_x), 42))) * 0.5
    dh = h * ky
    dw = w * kx
    if angle_y >= 0:
        cible = [(0, 0), (w, dh), (w, h - dh), (0, h)]
    else:
        cible = [(0, dh), (w, 0), (w, h), (0, h - dh)]
    if angle_x:
        cible = [(cible[0][0] + dw, cible[0][1]), (cible[1][0] - dw, cible[1][1]),
                 (cible[2][0] - dw, cible[2][1]), (cible[3][0] + dw, cible[3][1])]
    coef = _coef_perspective(cible, [(0, 0), (w, 0), (w, h), (0, h)])
    out = im.transform((w, h), Image.PERSPECTIVE, coef, Image.BICUBIC)
    if echelle != 1.0:
        out = out.resize((int(w * echelle), int(h * echelle)), Image.LANCZOS)
    return out


def _coef_perspective(src, dst):
    m = []
    for (x, y), (u, v) in zip(src, dst):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        m.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A = np.matrix(m, dtype=float)
    B = np.array(dst, dtype=float).reshape(8)
    return np.array(np.dot(np.linalg.inv(A.T * A) * A.T, B)).reshape(8)


def rogner_alpha(im, marge=0):
    bb = im.split()[-1].getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    return im.crop((max(x0 - marge, 0), max(y0 - marge, 0),
                    min(x1 + marge, im.size[0]), min(y1 + marge, im.size[1])))


def limiter(im, cote_max=1800):
    w, h = im.size
    if max(w, h) <= cote_max:
        return im
    f = cote_max / max(w, h)
    return im.resize((int(w * f), int(h * f)), Image.LANCZOS)


def sortir(im, out_dir, nom, desc):
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, nom)
    limiter(rogner_alpha(im)).save(p, optimize=True)
    _faits.append(dict(fichier=nom, dossier=os.path.relpath(out_dir, ROOT).replace("\\", "/"),
                       description=desc))
    print("  %-56s %s" % (nom, desc))


# ----------------------------------------------------------------- traitements
def t_carte(im, base, out):
    sortir(ombre(coins_arrondis(im, 20)), out, "%s_carte.png" % base,
           "carte flottante : coins arrondis + ombre profonde, fond transparent")


def t_incline_droite(im, base, out):
    sortir(ombre(incliner(coins_arrondis(im, 20), angle_y=17), flou=40, dy=30),
           out, "%s_incline-droite.png" % base,
           "carte inclinee vers la droite - donne du relief sans 3D")


def t_incline_gauche(im, base, out):
    sortir(ombre(incliner(coins_arrondis(im, 20), angle_y=-17), flou=40, dy=30),
           out, "%s_incline-gauche.png" % base, "carte inclinee vers la gauche")


def t_pile(im, base, out):
    """Pile de cartes decalees - device repere sur Da5fhPriu3n."""
    c = coins_arrondis(im, 20)
    w, h = c.size
    dec = int(min(w, h) * 0.035)
    toile = Image.new("RGBA", (w + dec * 3, h + dec * 3), (0, 0, 0, 0))
    for i, opac in enumerate([70, 130, 255]):
        couche = c.copy()
        if opac < 255:
            a = couche.split()[-1].point(lambda v: int(v * opac / 255))
            couche.putalpha(a)
            blanc = Image.new("RGBA", couche.size, (255, 255, 255, 0))
            blanc.paste(couche, (0, 0), couche)
            couche = blanc
        off = dec * (2 - i)
        toile.alpha_composite(couche, (off, off))
    sortir(ombre(toile, flou=38, dy=28), out, "%s_pile.png" % base,
           "pile de trois cartes decalees - suggere une serie, un catalogue")


def t_navigateur(im, base, out):
    """Cadre de navigateur autour de la capture."""
    w, h = im.size
    barre = max(int(h * 0.052), 34)
    r = 18
    toile = Image.new("RGBA", (w, h + barre), (255, 255, 255, 255))
    d = ImageDraw.Draw(toile)
    d.rectangle([0, 0, w, barre], fill=(240, 241, 243, 255))
    d.line([(0, barre), (w, barre)], fill=(225, 227, 230, 255), width=2)
    cy = barre // 2
    for i, c in enumerate([(243, 92, 78), (245, 190, 79), (95, 196, 84)]):
        cx = 20 + i * 22
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=c + (255,))
    d.rounded_rectangle([96, cy - 12, w - 20, cy + 12], radius=7,
                        fill=(255, 255, 255, 255), outline=(225, 227, 230, 255))
    toile.paste(im.convert("RGBA"), (0, barre))
    sortir(ombre(coins_arrondis(toile, r), flou=36, dy=26), out,
           "%s_navigateur.png" % base, "capture encadree dans une fenetre de navigateur")


def t_telephone(im, base, out):
    """Capture inseree dans une coque de telephone."""
    src = im.convert("RGBA")
    ecran_w, ecran_h = 760, 1520
    src = src.resize((ecran_w, int(src.size[1] * ecran_w / src.size[0])), Image.LANCZOS)
    if src.size[1] < ecran_h:
        fond = Image.new("RGBA", (ecran_w, ecran_h), (255, 255, 255, 255))
        fond.paste(src, (0, 0))
        src = fond
    else:
        src = src.crop((0, 0, ecran_w, ecran_h))
    bord = 26
    toile = Image.new("RGBA", (ecran_w + bord * 2, ecran_h + bord * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(toile)
    d.rounded_rectangle([0, 0, toile.size[0] - 1, toile.size[1] - 1], radius=76,
                        fill=(16, 20, 26, 255))
    toile.paste(coins_arrondis(src, 54), (bord, bord), coins_arrondis(src, 54))
    d = ImageDraw.Draw(toile)
    cx = toile.size[0] // 2
    d.rounded_rectangle([cx - 62, bord + 16, cx + 62, bord + 42], radius=13,
                        fill=(16, 20, 26, 255))
    sortir(ombre(toile, flou=44, dy=32), out, "%s_telephone.png" % base,
           "capture inseree dans une coque de telephone")


def _reflet(carte, hauteur=0.30, opacite=70):
    """Reflet au sol, attenue vers le bas. C'est ce qui fait lire le plan comme
    posé sur une surface, donc comme un volume et non comme un aplat."""
    w, h = carte.size
    hr = int(h * hauteur)
    r = carte.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, w, hr))
    a = r.split()[-1]
    grad = Image.linear_gradient("L").resize((w, hr))          # 0 en haut -> 255 en bas
    grad = grad.point(lambda v: int((255 - v) * opacite / 255))
    r.putalpha(Image.composite(grad, Image.new("L", (w, hr), 0), a))
    toile = Image.new("RGBA", (w, h + hr + 14), (0, 0, 0, 0))
    toile.alpha_composite(carte, (0, 0))
    toile.alpha_composite(r, (0, h + 14))
    return toile


def _tranche(carte, epaisseur=14, couleur=(206, 210, 216, 255)):
    """Epaisseur sur le cote : une carte sans tranche reste un rectangle plat."""
    w, h = carte.size
    toile = Image.new("RGBA", (w + epaisseur, h + epaisseur), (0, 0, 0, 0))
    for i in range(epaisseur, 0, -1):
        c = carte.copy()
        teinte = Image.new("RGBA", c.size, couleur)
        teinte.putalpha(c.split()[-1])
        toile.alpha_composite(teinte, (i, i))
    toile.alpha_composite(carte, (0, 0))
    return toile


def t_3d(im, base, out):
    """Perspective marquée + épaisseur + reflet. Le traitement le plus 'volume'
    du lot — demandé par le créateur le 2026-09-11."""
    c = incliner(coins_arrondis(im, 22), angle_y=26, angle_x=4)
    c = _tranche(c, epaisseur=16)
    c = _reflet(c)
    sortir(ombre(c, flou=46, dy=34, opacite=96), out, "%s_3d.png" % base,
           "volume 3D : perspective marquée, tranche visible, reflet au sol")


def t_3d_gauche(im, base, out):
    c = incliner(coins_arrondis(im, 22), angle_y=-26, angle_x=4)
    c = _tranche(c, epaisseur=16)
    c = _reflet(c)
    sortir(ombre(c, flou=46, dy=34, opacite=96), out, "%s_3d-gauche.png" % base,
           "volume 3D tourné vers la gauche")


def t_flou(im, base, out):
    """Version defocalisee - etat de transition, ou fond derriere un texte."""
    c = coins_arrondis(im, 20).filter(ImageFilter.GaussianBlur(14))
    sortir(ombre(c, flou=30, dy=20, opacite=80), out, "%s_flou.png" % base,
           "version floue - transition, ou fond derriere un titre")


TRAITEMENTS = {
    "carte": t_carte, "incline-droite": t_incline_droite, "incline-gauche": t_incline_gauche,
    "pile": t_pile, "navigateur": t_navigateur, "telephone": t_telephone, "flou": t_flou,
    "3d": t_3d, "3d-gauche": t_3d_gauche,
}

# Tous les ecrans n'appellent pas tous les traitements : un ecran deja au format
# telephone n'a pas besoin d'etre remis dans un telephone, et un ecran qui porte
# deja une barre de navigateur n'en recoit pas une seconde.
PAR_DEFAUT = ["carte", "incline-droite", "incline-gauche", "pile", "flou"]


def collecte(chemins):
    """Ne JAMAIS traiter un dossier `traitements/` : on habillerait des habillages.
    Constate le 2026-09-12 — un lot avait produit des `traitements/traitements/`
    pleins de variantes de variantes (`..._carte_incline-droite.png`)."""
    out = []
    for p in chemins:
        if os.path.isdir(p):
            for r, _, fs in os.walk(p):
                seg = os.path.relpath(r, p).replace("\\", "/").split("/")
                if any(x in seg for x in ("traitements", "video", "_ecartes", "_longues")):
                    continue
                for f in sorted(fs):
                    if f.lower().endswith(".png") and not f.startswith("_"):
                        out.append(os.path.join(r, f))
        elif p.lower().endswith((".png", ".jpg", ".jpeg")):
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--out", default=None)
    ap.add_argument("--traitements", default=None)
    a = ap.parse_args()

    noms = [x.strip() for x in a.traitements.split(",")] if a.traitements else PAR_DEFAUT
    for n in noms:
        if n not in TRAITEMENTS:
            print("traitement inconnu : %s (dispo : %s)" % (n, ", ".join(TRAITEMENTS)))
            return 1

    fichiers = collecte(a.sources)
    if not fichiers:
        print("aucune image trouvee")
        return 1
    print("%d image(s) · traitements : %s\n" % (len(fichiers), ", ".join(noms)))

    for f in fichiers:
        base = os.path.splitext(os.path.basename(f))[0]
        out = a.out or os.path.join(os.path.dirname(f), "traitements")
        try:
            im = Image.open(f).convert("RGBA")
        except Exception as e:
            print("  ! illisible %s : %s" % (base, e))
            continue
        # un ecran deja vertical n'a pas besoin de la coque telephone
        vertical = im.size[1] > im.size[0] * 1.4
        for n in noms:
            if n == "telephone" and vertical:
                continue
            try:
                TRAITEMENTS[n](im, base, out)
            except Exception as e:
                print("  ! %s sur %s : %s" % (n, base, e))

    man = os.path.join(ROOT, "asset-library", "broll", "_manifeste-traitements.json")
    os.makedirs(os.path.dirname(man), exist_ok=True)
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/broll_treatments.py",
                   "releve_sur": "references InsiderForce 2026-09-10",
                   "assets": _faits}, fh, ensure_ascii=False, indent=2)
    print("\n%d variantes produites" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
