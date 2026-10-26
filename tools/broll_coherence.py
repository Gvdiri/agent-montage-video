#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Coherence de la bibliotheque b-roll - Hyperframes.

Une bibliotheque qui se remplit par vagues accumule des orphelins. Trois cas
constates pendant la construction :

1. CLIP ORPHELIN — l'image source a ete ecartee a la revue visuelle, mais le clip
   video qui en derivait est reste. On a vu des clips fabriques a partir d'un
   cockpit de chasseur et d'une devanture de superette.

2. TRAITEMENT ORPHELIN — meme chose pour les variantes (carte, incline, 3d).

3. FICHIER VIDE — ffmpeg cree le fichier de sortie AVANT d'encoder : un echec
   laisse un .mp4 de quelques octets, que le test "le fichier existe" prend
   ensuite pour du travail deja fait.

Rien n'est supprime sans etre affiche. `--appliquer` pour agir.

Usage :
    python tools/broll_coherence.py [--appliquer]
"""
import os
import sys
import json
import argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")
TAILLE_MINI = 2048


def racine_source(nom):
    """« broll_x_zoom-avant.mp4 » -> « broll_x » ; « x_carte.png » -> « x »."""
    # En cascade : « capture_x_longue_defilement-bas » porte DEUX suffixes.
    # Ne retirer que le dernier laissait « capture_x_longue », introuvable parmi
    # les sources, donc signale a tort comme orphelin.
    base = os.path.splitext(nom)[0]
    SUFFIXES = ("_zoom-avant", "_zoom-arriere", "_derive-droite", "_derive-gauche",
                "_plongee", "_defilement-bas", "_defilement-haut", "_curseur",
                "_carte", "_incline-droite", "_incline-gauche", "_pile", "_flou",
                "_navigateur", "_telephone", "_3d-gauche", "_3d", "_longue")
    change = True
    while change:
        change = False
        for suf in SUFFIXES:
            if base.endswith(suf):
                base = base[: -len(suf)]
                change = True
                break
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--appliquer", action="store_true")
    a = ap.parse_args()

    # sources vivantes = toute image hors dossiers derives
    vivantes = set()
    derives = []
    vides = []
    for r, _, fs in os.walk(BROLL):
        rel = os.path.relpath(r, BROLL).replace("\\", "/").split("/")
        est_derive = any(x in rel for x in ("video", "traitements"))
        est_exclu = any(x in rel for x in ("_ecartes", "_a-verifier", "_planches", "_rebut"))
        for f in fs:
            ext = os.path.splitext(f)[1].lower()
            p = os.path.join(r, f)
            if ext in (".mp4", ".webm") and os.path.getsize(p) < TAILLE_MINI:
                vides.append(p)
                continue
            if est_exclu:
                continue
            if est_derive and ext in (".mp4", ".webm", ".png", ".jpg"):
                derives.append(p)
            elif ext in (".png", ".jpg", ".jpeg"):
                vivantes.add(racine_source(f))

    orphelins = []
    for p in derives:
        rac = racine_source(os.path.basename(p))
        # les clips et fonds fabriques de toutes pieces n'ont pas d'image source
        if rac.startswith(("frappe_", "fond-anime", "texture-animee", "grille-animee",
                           "poussiere-animee", "balayage-anime", "overlay_")):
            continue
        if rac not in vivantes:
            orphelins.append(p)

    print("Sources vivantes : %d" % len(vivantes))
    print("Dérivés          : %d" % len(derives))
    print()
    if vides:
        print("Fichiers vides (%d) :" % len(vides))
        for p in vides:
            print("   %s" % os.path.relpath(p, BROLL))
    if orphelins:
        print("\nDérivés orphelins — leur source a été écartée (%d) :" % len(orphelins))
        for p in orphelins:
            print("   %s" % os.path.relpath(p, BROLL))
    if not vides and not orphelins:
        print("Aucune incohérence.")

    if a.appliquer:
        n = 0
        for p in vides + orphelins:
            try:
                os.remove(p)
                n += 1
            except Exception as e:
                print("  ! %s : %s" % (os.path.basename(p), e))
        print("\n%d fichiers supprimés" % n)
    elif vides or orphelins:
        print("\n(ajouter --appliquer pour supprimer)")

    with open(os.path.join(BROLL, "_coherence.json"), "w", encoding="utf-8") as fh:
        json.dump({"sources_vivantes": len(vivantes), "derives": len(derives),
                   "vides": [os.path.relpath(p, BROLL).replace("\\", "/") for p in vides],
                   "orphelins": [os.path.relpath(p, BROLL).replace("\\", "/") for p in orphelins]},
                  fh, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
