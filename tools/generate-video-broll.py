#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B-roll VIDEO - Hyperframes.

Demande du createur : apres les images, du b-roll **video** — des extraits
realistes, des illustrations en mouvement.

Trois familles, toutes produites a partir de ce que la bibliotheque contient
deja. C'est le point cle : on ne va pas chercher des rushes ailleurs, on met en
mouvement les 258 sujets qu'on a. Un plan fixe de 2 s se voit ; le meme plan avec
une derive lente se regarde.

1. DERIVE (Ken Burns) — zoom et translation tres lents sur une photo ou une
   capture. C'est la technique la plus rentable du montage : elle transforme
   n'importe quelle image en plan vivant.

2. DEFILEMENT — une capture haute qui defile verticalement. Ca ne ressemble pas
   a un panoramique, ca ressemble a **quelqu'un qui scrolle une page**. C'est le
   plan le plus utile de la niche.

3. CURSEUR — un pointeur qui traverse le cadre et clique, en surimpression sur
   une capture. Donne l'impression d'un enregistrement d'ecran sans en faire un.

Sorties : MP4 60 fps (le projet est en 60), H.264 CRF 18, sans audio.

Usage :
    python tools/generate-video-broll.py [--only derive,defilement,curseur]
                                         [--max-par-famille 40]
"""
import os
import sys
import json
import math
import shutil
import random
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FPS = 60

_faits = []


def ff(args, label):
    r = subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + args,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  ! %s : %s" % (label, (r.stderr or "").strip()[:160]))
        return False
    return True


def note(chemin, famille, desc, source):
    _faits.append(dict(fichier=os.path.basename(chemin),
                       dossier=os.path.relpath(os.path.dirname(chemin), BROLL).replace("\\", "/"),
                       famille=famille, description=desc, source=os.path.basename(source)))
    print("  %-52s %s" % (os.path.basename(chemin)[:51], desc))


def _exclu(r):
    """Dossiers a ignorer — teste sur le chemin RELATIF a la bibliotheque.

    Piege : le projet vit dans « ma-video », donc tout chemin ABSOLU contient
    « video ». Filtrer sur le chemin absolu excluait la totalite des dossiers et
    ne produisait aucun clip, sans la moindre erreur.
    """
    rel = os.path.relpath(r, BROLL).replace("\\", "/").lower()
    return any(x in rel.split("/") for x in ("_ecartes", "traitements", "video", "_planches"))


def sortie(src, suffixe):
    d = os.path.join(os.path.dirname(src), "video")
    os.makedirs(d, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    return os.path.join(d, "%s_%s.mp4" % (base, suffixe))


# ------------------------------------------------------------------- DERIVE
def derive(src, sortie_path, dur, z0, z1, dx, dy, cadre):
    """zoompan sur l'image agrandie. On travaille en 2x pour que le zoom ne
    ramollisse pas l'image."""
    W, H = cadre
    n = int(dur * FPS)
    z = "%.5f+(%.5f-%.5f)*on/%d" % (z0, z1, z0, n)
    x = "iw/2-(iw/zoom/2)+(%.1f*on/%d)" % (dx, n)
    y = "ih/2-(ih/zoom/2)+(%.1f*on/%d)" % (dy, n)
    # Recadrage vertical : on part du HAUT de l'image, pas du centre.
    # Une capture large (1600x1000) recadree en 9:16 par le centre tombait sur la
    # bande vide du milieu de page — d'ou des clips a variance 0 alors que
    # l'image source etait bonne.
    haut = "0" if H > W else "(ih-oh)/2"
    vf = ("scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d:(iw-ow)/2:%s,"
          "scale=%d:%d,zoompan=z='%s':x='%s':y='%s':d=%d:s=%dx%d:fps=%d,"
          "format=yuv420p" % (W, H, W, H, haut, W * 2, H * 2, z, x, y, n, W, H, FPS))
    return ff(["-loop", "1", "-i", src, "-vf", vf, "-t", "%.3f" % dur,
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-an", sortie_path], os.path.basename(sortie_path))


def bloc_derive(maxi):
    """Une derive lente par image. Direction tiree au sort mais deterministe :
    deux appels donnent le meme fichier."""
    print("\n[derive — Ken Burns]")
    sources = []
    for cat in ("03-mains-et-appareils", "04-lieux-et-bureaux", "05-humain-au-travail",
                "07-objets-et-details", "01-ecrans-produits"):
        d = os.path.join(BROLL, cat)
        for r, _, fs in os.walk(d):
            if _exclu(r):
                continue
            for f in sorted(fs):
                if f.lower().endswith((".jpg", ".png")):
                    sources.append(os.path.join(r, f))
    random.Random(11).shuffle(sources)
    sources = sources[:maxi]

    mouvements = [
        ("zoom-avant", 1.00, 1.13, 0, 0, "zoom avant lent — on entre dans l'image"),
        ("zoom-arriere", 1.13, 1.00, 0, 0, "zoom arriere lent — on decouvre le contexte"),
        ("derive-droite", 1.06, 1.10, 190, 0, "derive vers la droite"),
        ("derive-gauche", 1.06, 1.10, -190, 0, "derive vers la gauche"),
        ("plongee", 1.04, 1.12, 0, 150, "descente lente dans le cadre"),
    ]
    rng = random.Random(23)
    for i, src in enumerate(sources):
        nom, z0, z1, dx, dy, desc = mouvements[i % len(mouvements)]
        # 9:16 pour les plans pleins, sinon on garde du 16:9 pour une carte
        cadre = (1080, 1920) if i % 3 else (1920, 1080)
        dur = rng.choice([5.0, 6.0, 7.0])
        out = sortie(src, nom)
        if os.path.exists(out) and os.path.getsize(out) > 2048:
            continue
        if derive(src, out, dur, z0, z1, dx, dy, cadre):
            note(out, "derive", "%s · %.0fs · %dx%d" % (desc, dur, cadre[0], cadre[1]), src)


# --------------------------------------------------------------- DEFILEMENT
def bloc_defilement(maxi):
    """Capture haute qui defile : ca lit comme quelqu'un qui scrolle."""
    print("\n[defilement — quelqu'un qui scrolle]")
    sources = []
    for cat in ("01-ecrans-produits", "02-ecrans-generiques"):
        d = os.path.join(BROLL, cat)
        for r, _, fs in os.walk(d):
            if _exclu(r):
                continue
            for f in sorted(fs):
                if not f.lower().endswith(".png"):
                    continue
                p = os.path.join(r, f)
                try:
                    with Image.open(p) as im:
                        w, h = im.size
                except Exception:
                    continue
                # il faut de la matiere a faire defiler
                if h >= w * 0.85:
                    sources.append((p, w, h))
    sources = sources[:maxi]
    print("  %d source(s) hautes retenues" % len(sources))

    for p, w, h in sources:
        W, H = 1080, 1920
        ech = W / float(w)
        h2 = int(h * ech)
        if h2 <= H + 60:
            continue
        course = h2 - H
        dur = max(4.0, min(9.0, course / 190.0))
        n = int(dur * FPS)
        for sens, nom, desc in ((1, "defilement-bas", "on scrolle vers le bas"),
                                (-1, "defilement-haut", "on remonte la page")):
            out = sortie(p, nom)
            if os.path.exists(out) and os.path.getsize(out) > 2048:
                continue
            dep = 0 if sens > 0 else course
            # ease-in-out : un scroll humain n'est pas lineaire
            # crop expose 'n' (numero de frame) ; 'on' n'existe que dans zoompan
            y = r"(%d)+(%d)*(0.5-0.5*cos(PI*min(n/%d\,1)))" % (dep, sens * course, n)
            vf = ("scale=%d:-1,crop=%d:%d:0:'%s',format=yuv420p" % (W, W, H, y))
            if ff(["-loop", "1", "-i", p, "-vf", vf, "-t", "%.3f" % dur,
                   "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                   "-pix_fmt", "yuv420p", "-an", out], os.path.basename(out)):
                note(out, "defilement", "%s · %.1fs" % (desc, dur), p)


# ------------------------------------------------------------------ CURSEUR
def bloc_curseur(maxi):
    """Pointeur qui traverse et clique. Donne le sentiment d'un enregistrement
    d'ecran sans avoir a en faire un."""
    print("\n[curseur — interaction simulee]")
    cur = None
    for r, _, fs in os.walk(os.path.join(BROLL, "10-motion-elements")):
        for f in fs:
            if f == "curseur_graphite_01.png":
                cur = os.path.join(r, f)
    if cur is None:
        print("  ! curseur introuvable — lancer generate-motion-elements.py")
        return

    sources = []
    d = os.path.join(BROLL, "02-ecrans-generiques")
    for r, _, fs in os.walk(d):
        if _exclu(r):
            continue
        for f in sorted(fs):
            if f.lower().endswith(".png"):
                sources.append(os.path.join(r, f))
    sources = sources[:maxi]
    print("  %d source(s), curseur=%s" % (len(sources), os.path.basename(cur) if cur else None))

    for i, p in enumerate(sources):
        out = sortie(p, "curseur")
        if os.path.exists(out) and os.path.getsize(out) > 2048:
            continue
        dur = 4.0
        try:
            with Image.open(p) as im:
                w, h = im.size
        except Exception:
            continue
        W = 1600
        H = int(1600 * h / float(w)) // 2 * 2      # H.264 exige une hauteur paire
        # trajet : coin bas-droit -> une cible dans le tiers haut, puis arret
        x0, y0 = int(W * 0.82), int(H * 0.86)
        x1, y1 = int(W * (0.30 + 0.22 * (i % 3))), int(H * 0.34)
        t = "min(t/2.2,1)"
        e = "(0.5-0.5*cos(PI*%s))" % t
        xe = "%d+(%d)*%s" % (x0, x1 - x0, e)
        ye = "%d+(%d)*%s" % (y0, y1 - y0, e)
        # Un pointeur de 54 px sur un cadre de 1600 px ne fait bouger que 0,3 %
        # des pixels : le plan parait fige. On ajoute une legere poussee avant
        # pour que le cadre entier vive.
        nf = int(dur * FPS)
        vf = ("[0:v]scale=%d:%d,zoompan=z='1.0+0.05*on/%d':x='iw/2-(iw/zoom/2)':"
              "y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d[bg];[1:v]scale=54:-1[c];"
              "[bg][c]overlay=x='%s':y='%s',format=yuv420p"
              % (W, H, nf, nf, W, H, FPS, xe, ye))
        if ff(["-loop", "1", "-i", p, "-loop", "1", "-i", cur,
               "-filter_complex", vf, "-t", "%.3f" % dur, "-r", str(FPS),
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-an", out], os.path.basename(out)):
            note(out, "curseur", "le pointeur rejoint une cible et s'arrete · %.0fs" % dur, p)


BLOCS = {"derive": bloc_derive, "defilement": bloc_defilement, "curseur": bloc_curseur}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--max-par-famille", type=int, default=40)
    a = ap.parse_args()
    for n in ([x.strip() for x in a.only.split(",")] if a.only else list(BLOCS)):
        if n not in BLOCS:
            print("bloc inconnu : %s" % n)
            return 1
        BLOCS[n](a.max_par_famille)
    man = os.path.join(BROLL, "_manifeste-video.json")
    ancien = json.load(open(man, encoding="utf-8")).get("clips", []) if os.path.exists(man) else []
    connus = {f["fichier"] for f in _faits}
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/generate-video-broll.py",
                   "principe": "mettre en mouvement les sujets deja en bibliotheque",
                   "clips": _faits + [x for x in ancien if x["fichier"] not in connus]},
                  fh, ensure_ascii=False, indent=2)
    print("\n%d clips produits" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
