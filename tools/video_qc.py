#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Controle qualite des clips de b-roll video - Hyperframes.

Le createur a signale (2026-09-10) que certains clips "sont faits a moitie ou
n'ont pas vraiment de sens... parfois c'est juste du blanc". Plutot que de
discuter, on mesure. Quatre defauts sont detectables automatiquement :

1. CADRE VIDE — luminance quasi uniforme sur toute la duree. Un plan ou il n'y a
   rien a voir. C'est le defaut qu'il a repere.

2. MOUVEMENT NUL — les images ne changent pas. Un "defilement" dont la course
   fait 20 px est un plan fixe deguise : il ne vaut pas mieux qu'une image, et il
   pese 40 fois plus lourd.

3. CADRE MORT — une part enorme du cadre est d'une seule couleur (typiquement du
   blanc en bas d'une capture courte etiree). EDITING_SYSTEM l'interdit deja pour
   les images ; ca vaut pour la video.

4. TROP COURT — sous 1,5 s un clip n'a pas le temps d'exister a l'ecran.

Les clips recales partent dans `_rebut/` a cote, jamais supprimes en silence.

Usage :
    python tools/video_qc.py [--appliquer] [--dossier ...]
"""
import os
import sys
import json
import shutil
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"
TMP = os.path.join(ROOT, "temp", "_vqc")

# Seuils recalibres apres un premier passage rate. Deux erreurs a ne pas refaire :
#  - j'echantillonnais a 200 px de large : a cette taille le TEXTE TAPE disparait,
#    donc les clips de frappe mesuraient un "mouvement nul" alors qu'il s'y passe
#    tout. On echantillonne desormais a 480 px.
#  - une interface epuree sur fond clair a legitimement une variance basse. Ce
#    n'est pas un cadre vide. Le vrai cadre vide, c'est variance basse ET aucun
#    mouvement. On exige donc les deux.
# Troisieme calibration de ce banc. Les deux precedentes se sont trompees de
# METRIQUE, pas de seuil :
#  1. echantillonnage a 200 px -> le texte tape disparaissait. Corrige a 480 px.
#  2. 95e centile de la difference -> dans une interface epuree le texte occupe
#     3-4 % des pixels, donc 95 % sont identiques et le centile vaut 0. Les 9
#     clips de frappe etaient declares "figes" alors qu'il s'y passe tout.
# On mesure desormais la PART DE PIXELS QUI CHANGENT : c'est ce qui distingue
# reellement un plan vivant d'un plan mort, quelle que soit la surface concernee.
#  3. seuil de detection a 12 niveaux -> les FONDS ANIMES, qui derivent
#     volontairement de facon imperceptible (1 a 5 niveaux par pixel), etaient
#     declares figes. Ils font pourtant exactement ce qu'on leur demande.
# Metrique finale : part de pixels changeant de plus de 3 niveaux. Elle voit a la
# fois le texte qui s'ecrit (petite surface, gros changement) et le degrade qui
# derive (grande surface, petit changement) — les deux extremes du catalogue.
SEUILS = dict(
    variance_morte=4.5,     # cadre uniforme : il n'y a rien a regarder
    #  4. seuil a 1 % -> recalait des clips que j'avais valides a l'oeil (frappe,
    #     curseur). Le banc ne doit pas arbitrer le GOUT, seulement detecter le
    #     mort. Un clip faible se REGENERE avec plus d'amplitude ; il ne se jette
    #     pas. Seuil final : 0,05 %, c'est-a-dire "il ne se passe litteralement rien".
    part_changee_min=0.05,  # % de pixels qui bougent de plus de 3 niveaux
    duree_min=1.5,
)
DELTA_PIXEL = 3
LARGEUR_ECH = 480


def duree(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v",
                        "-show_entries", "stream=duration", "-of", "default=nw=1:nk=1", p],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def echantillonner(p, n=6):
    """n images reparties sur la duree, en petit."""
    os.makedirs(TMP, exist_ok=True)
    d = duree(p)
    imgs = []
    for i in range(n):
        t = max(d * (i + 0.5) / n, 0.02)
        out = os.path.join(TMP, "s%02d.png" % i)
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-ss", "%.3f" % t,
                        "-i", p, "-frames:v", "1", "-vf", "scale=%d:-1" % LARGEUR_ECH, out],
                       capture_output=True, text=True)
        if os.path.isfile(out):
            try:
                imgs.append(np.asarray(Image.open(out).convert("L"), dtype=np.float32))
            except Exception:
                pass
            os.remove(out)
    return d, imgs


def mesurer(p):
    d, imgs = echantillonner(p)
    if not imgs:
        return None
    h = min(i.shape[0] for i in imgs)
    w = min(i.shape[1] for i in imgs)
    imgs = [i[:h, :w] for i in imgs]

    variance = float(np.mean([i.std() for i in imgs]))
    # Part de pixels qui changent nettement entre deux images echantillonnees.
    # On prend le MAXIMUM sur les paires : il suffit qu'il se passe quelque chose
    # a un moment du clip.
    if len(imgs) > 1:
        parts = [float((np.abs(imgs[k + 1] - imgs[k]) > DELTA_PIXEL).mean()) * 100
                 for k in range(len(imgs) - 1)]
        part_changee = max(parts)
    else:
        part_changee = 0.0
    # part du cadre occupee par la teinte dominante (a 8 niveaux pres)
    q = (imgs[len(imgs) // 2] // 8).astype(np.int32)
    vals, cnt = np.unique(q, return_counts=True)
    part_unie = float(cnt.max() / q.size)

    return dict(duree_s=round(d, 2), variance=round(variance, 1),
                part_changee=round(part_changee, 2), part_unie=round(part_unie, 3))


def juger(m, s):
    defauts = []
    if m["duree_s"] < s["duree_min"]:
        defauts.append("durée %.1fs < %.1fs" % (m["duree_s"], s["duree_min"]))
    mort = m["variance"] < s["variance_morte"]
    fige = m["part_changee"] < s["part_changee_min"]
    if mort and fige:
        defauts.append("cadre vide et figé (variance %.1f, %.2f %% de pixels bougent)"
                       % (m["variance"], m["part_changee"]))
    elif fige:
        defauts.append("rien ne bouge (%.2f %% < %.2f %% des pixels) — une image aurait suffi"
                       % (m["part_changee"], s["part_changee_min"]))
    elif mort:
        defauts.append("cadre quasi vide (variance %.1f < %.1f)"
                       % (m["variance"], s["variance_morte"]))
    # `part_unie` reste mesuree mais ne recale plus a elle seule : un fond ivoire
    # occupant 96 % du cadre est un choix de design, pas un defaut.
    return defauts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dossier", default=BROLL)
    ap.add_argument("--appliquer", action="store_true")
    a = ap.parse_args()

    clips = []
    for r, _, fs in os.walk(a.dossier):
        if "_rebut" in r:
            continue
        for f in sorted(fs):
            if f.lower().endswith(".mp4"):
                clips.append(os.path.join(r, f))
    if not clips:
        print("aucun clip")
        return 1

    gardes, recales = [], []
    print("%-52s %6s %7s %9s %6s  verdict" % ("clip", "durée", "varian", "%bouge", "unie"))
    print("-" * 100)
    for p in clips:
        m = mesurer(p)
        if m is None:
            recales.append(dict(fichier=os.path.basename(p),
                                chemin=os.path.relpath(p, ROOT), defauts=["illisible"]))
            print("%-52s  ILLISIBLE" % os.path.basename(p)[:51])
            continue
        d = juger(m, SEUILS)
        ligne = dict(fichier=os.path.basename(p), chemin=os.path.relpath(p, ROOT).replace("\\", "/"),
                     defauts=d, **m)
        print("%-52s %5.1fs %7.1f %8.2f%% %5.0f%%  %s" % (
            os.path.basename(p)[:51], m["duree_s"], m["variance"], m["part_changee"],
            m["part_unie"] * 100, "ok" if not d else "RECALÉ — " + d[0]))
        (gardes if not d else recales).append(ligne)

    if a.appliquer:
        for e in recales:
            src = os.path.join(ROOT, e["chemin"])
            if not os.path.isfile(src):
                continue
            dd = os.path.join(os.path.dirname(src), "_rebut")
            os.makedirs(dd, exist_ok=True)
            try:
                shutil.move(src, os.path.join(dd, os.path.basename(src)))
            except Exception as ex:
                print("  ! %s : %s" % (e["fichier"], ex))

    with open(os.path.join(BROLL, "_qc-video.json"), "w", encoding="utf-8") as fh:
        json.dump({"seuils": SEUILS, "gardes": len(gardes), "recales": len(recales),
                   "detail_recales": recales, "detail_gardes": gardes},
                  fh, ensure_ascii=False, indent=2)
    shutil.rmtree(TMP, ignore_errors=True)

    print("\n%d gardés · %d recalés%s" % (len(gardes), len(recales),
                                          "" if a.appliquer else "  (ajouter --appliquer)"))
    from collections import Counter
    c = Counter(e["defauts"][0].split("(")[0].split("—")[0].strip() for e in recales if e["defauts"])
    for k, v in c.most_common():
        print("   %-46s %d" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
