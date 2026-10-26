#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tri mesure des photos de banque - Hyperframes.

Meme principe que le banc SFX : on ne juge pas a l'oeil, on mesure.

Constat sur la premiere moisson Openverse (62 images CC0) : environ 40 % lisaient
"stock des annees 2010" — dominante jaune, bokeh violet, materiel vintage. La charte
l'interdit explicitement ("no generic AI aesthetic", "could this be mistaken for a
generic template?"), et l'identite est le **metal neutre** : graphite, ivoire, acier.

Ce qui est mesurable dans "ca fait daté" :

- **SATURATION** — l'identite est neutre. Une image tres saturee ne s'y fond pas et
  ne s'etalonne pas sans devenir grise et sale.
- **DOMINANTE** — un ecart fort entre canaux (jaune, magenta, vert) trahit une photo
  non etalonnee ou une lumiere artificielle datee.
- **NETTETE** — variance du laplacien. Le bokeh mou est le tic visuel du stock ancien.
- **DEFINITION** — deja filtree au telechargement, revalidee ici.

Les images ecartees ne sont pas supprimees : elles partent dans `_ecartes/` avec le
motif. C'est un tri, pas une censure — l'oeil humain garde le dernier mot.

Usage :
    python tools/broll_triage.py [dossier] [--appliquer] [--seuils sat=0.42,cast=0.13,net=80]
"""
import os
import sys
import json
import shutil
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEFAUT = os.path.join(ROOT, "asset-library", "broll")

# larg=940 : la carte de preuve du standard de split fait 972 px de large. Une image
# de 1024 px est donc DEJA a la bonne taille pour son usage principal. Le seuil de
# 1100 px de la premiere version etait cale sur le mauvais usage (plein cadre) et
# ecartait 57 images sur 62 pour une raison qui n'en etait pas une.
SEUILS = dict(sat=0.42, cast=0.13, net=80.0, larg=940)
PLEIN_CADRE = 1600      # au-dela, utilisable aussi en fond plein 1080x1920


def mesurer(p):
    im = Image.open(p).convert("RGB")
    larg, haut = im.size
    petit = im.copy()
    petit.thumbnail((520, 520), Image.LANCZOS)
    a = np.asarray(petit, dtype=np.float32) / 255.0

    mx = a.max(axis=2)
    mn = a.min(axis=2)
    sat = float(np.mean((mx - mn) / np.maximum(mx, 1e-6)))

    moy = a.reshape(-1, 3).mean(axis=0)
    cast = float(np.max(np.abs(moy - moy.mean())))

    g = np.asarray(petit.convert("L"), dtype=np.float32)
    # laplacien 3x3 par differences finies
    lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    net = float(lap.var())

    return dict(largeur=larg, hauteur=haut, saturation=round(sat, 4),
                dominante=round(cast, 4), nettete=round(net, 1),
                plein_cadre=bool(larg >= PLEIN_CADRE))


def juger(m, s):
    motifs = []
    if m["saturation"] > s["sat"]:
        motifs.append("saturation %.2f > %.2f (hors identite neutre)" % (m["saturation"], s["sat"]))
    if m["dominante"] > s["cast"]:
        motifs.append("dominante colorée %.3f > %.3f" % (m["dominante"], s["cast"]))
    if m["nettete"] < s["net"]:
        motifs.append("netteté %.0f < %.0f (mou / bokeh)" % (m["nettete"], s["net"]))
    if m["largeur"] < s["larg"]:
        motifs.append("largeur %d < %d px (sous la carte de preuve)" % (m["largeur"], s["larg"]))
    return motifs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier", nargs="?", default=DEFAUT)
    ap.add_argument("--appliquer", action="store_true", help="deplacer les ecartees dans _ecartes/")
    ap.add_argument("--seuils", default=None)
    a = ap.parse_args()

    s = dict(SEUILS)
    if a.seuils:
        for kv in a.seuils.split(","):
            k, v = kv.split("=")
            s[k.strip()] = float(v)

    fichiers = []
    for r, dnames, fs in os.walk(a.dossier):
        # `_planches` contient les planches-contact de logos : ce sont des index,
        # pas des photos a juger.
        if "_ecartes" in r or "_planches" in r:
            continue
        for f in sorted(fs):
            if f.lower().endswith((".jpg", ".jpeg")):
                fichiers.append(os.path.join(r, f))
    if not fichiers:
        print("aucune photo trouvee dans %s" % a.dossier)
        return 1

    gardes, ecartes = [], []
    print("%-48s %5s %6s %7s %6s  verdict" % ("fichier", "sat", "domin", "nettete", "plein"))
    print("-" * 92)
    for p in fichiers:
        try:
            m = mesurer(p)
        except Exception as e:
            print("  ! %s : %s" % (os.path.basename(p), e))
            continue
        motifs = juger(m, s)
        ligne = dict(fichier=os.path.basename(p),
                     chemin=os.path.relpath(p, ROOT).replace("\\", "/"), **m, motifs=motifs)
        print("%-48s %5.2f %6.3f %7.0f %6s  %s" % (
            os.path.basename(p)[:47], m["saturation"], m["dominante"], m["nettete"],
            "oui" if m["plein_cadre"] else "-",
            "garde" if not motifs else "ECARTE - " + motifs[0]))
        (gardes if not motifs else ecartes).append(ligne)

    if a.appliquer:
        for e in ecartes:
            src = os.path.join(ROOT, e["chemin"])
            d = os.path.join(os.path.dirname(src), "_ecartes")
            os.makedirs(d, exist_ok=True)
            try:
                shutil.move(src, os.path.join(d, os.path.basename(src)))
            except Exception as ex:
                print("  ! deplacement %s : %s" % (e["fichier"], ex))

    rapport = os.path.join(DEFAUT, "_triage.json")
    with open(rapport, "w", encoding="utf-8") as fh:
        json.dump({"seuils": s, "gardes": len(gardes), "ecartes": len(ecartes),
                   "detail_ecartes": ecartes, "detail_gardes": gardes},
                  fh, ensure_ascii=False, indent=2)

    print("\n%d gardées · %d écartées%s" % (len(gardes), len(ecartes),
                                            "" if a.appliquer else "  (ajouter --appliquer pour les déplacer)"))
    print("-> %s" % rapport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
