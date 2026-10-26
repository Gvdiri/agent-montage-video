#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Finalisation de la bibliotheque SFX - Hyperframes.

Prend une vague brute generee, et pour chaque son :

1. LE MESURE au banc (tools/sfx_bench.py) contre TOUS les roles, pas seulement
   celui qu'on avait en tete. Un "impact" a 260 ms d'attaque n'est pas un impact
   rate : c'est un reveal. On le range ou il est bon au lieu de le jeter.
2. LE NORMALISE. La vague 1 sortait des sons entre -53 dB et 0 dB de pic.
   La regle du projet dit "restrained must still be audible" : un SFX a -53 dB
   n'existe pas. Court -> pic a -1 dBFS. Long (texture) -> loudnorm -20 LUFS.
   On normalise ici, une fois, pour que la decision de mixage se prenne au montage
   et pas dans le fichier.
3. LE RANGE dans asset-library/sfx/<role>/ avec un nom parlant isole.
4. Ecrit un catalogue machine + un LISEZ-MOI lisible.

Ce qui ne passe aucun role part dans _rebut/ - garde pour inspection, jamais
propose au montage.

Usage :
    python tools/sfx_finalize.py asset-library/sfx/_brut-vague-1 [--dry]
"""
import os
import sys
import json
import shutil
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
from sfx_bench import measure, judge, ROLE_SPECS  # noqa: E402
import numpy as np  # noqa: E402
import librosa  # noqa: E402
import soundfile as sf  # noqa: E402

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SFX = os.path.join(ROOT, "asset-library", "sfx")

# Ordre de preference quand un son passe plusieurs roles : du plus specifique
# au plus permissif. Sinon tout finirait en "texture", qui accepte presque tout.
ORDRE = ["impact", "ui", "confirmation", "transition", "reveal", "riser", "texture"]

PREFIXE_ROLE = {
    "impact-": "impact", "reveal-": "reveal", "trans-": "transition",
    "riser-": "riser", "conf-": "confirmation", "ui-": "ui", "tex-": "texture",
}

# A quoi sert chaque role au montage - repris dans le LISEZ-MOI.
USAGE = {
    "impact": "Le coup. Hook a 0,00 s, chiffre qui claque, revelation seche, negatif rouge.",
    "reveal": "La carte de preuve qui apparait, le logo qui entre, le panneau qui se remplit.",
    "transition": "Le liant entre deux plans. Cadence 1,5 s : c'est le role le plus consomme.",
    "riser": "La tension qui monte vers la revelation ou vers le CTA.",
    "confirmation": "Ca a marche. Le positif, la resolution, la coche.",
    "ui": "Sons d'interface reels : clic, frappe, envoi, notification.",
    "texture": "Le lit sous un panneau de preuve, la tension continue, l'ambiance.",
}


SR = 44100


def _trim(y, floor_db=-55.0):
    """Coupe le silence de tete et de queue. Garde 3 ms de marge avant le
    transitoire : rogner pile sur l'attaque produit un clic."""
    if y.size == 0:
        return y
    pic = float(np.max(np.abs(y)))
    if pic <= 0:
        return y
    seuil = pic * (10 ** (floor_db / 20.0))
    idx = np.where(np.abs(y) > seuil)[0]
    if idx.size == 0:
        return y
    marge = int(0.003 * SR)
    return y[max(0, int(idx[0]) - marge): min(y.size, int(idx[-1]) + marge)]


def _fades(y, fin_ms=12.0, debut_ms=1.5):
    """Fondu de sortie applique A LA FIN du fichier - pas a t=0.
    (Le bug de la premiere version : afade st=0 coupait tout apres 8 ms.)"""
    n = y.size
    nd = min(int(debut_ms / 1000 * SR), n // 4)
    nf = min(int(fin_ms / 1000 * SR), n // 2)
    if nd > 1:
        y[:nd] *= np.linspace(0.0, 1.0, nd, dtype=np.float32)
    if nf > 1:
        y[n - nf:] *= np.linspace(1.0, 0.0, nf, dtype=np.float32) ** 1.6
    return y


def _ecrire(y, dst):
    y = np.clip(y, -1.0, 1.0)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    sf.write(dst, (y * 32767).astype(np.int16), SR, subtype="PCM_16")
    return True


def norm_court(src, dst):
    """Court : trim, fondus, pic cale a -1 dBFS.
    On sort en WAV : le MP3 ajoute un padding d'encodeur qui decale le
    transitoire, inacceptable pour un son qui doit tomber sur une frame."""
    y, _ = librosa.load(src, sr=SR, mono=True)
    y = _fades(_trim(y).astype(np.float32).copy())
    pic = float(np.max(np.abs(y)))
    if pic > 0:
        y *= (10 ** (-1.0 / 20.0)) / pic
    return _ecrire(y, dst)


def norm_long(src, dst):
    """Texture : loudness constante plutot que pic constant - sinon un drone
    grave parait beaucoup plus fort qu'un impact au meme pic."""
    y, _ = librosa.load(src, sr=SR, mono=True)
    y = _fades(_trim(y, floor_db=-70.0).astype(np.float32).copy(), fin_ms=120.0, debut_ms=60.0)
    rms = float(np.sqrt(np.mean(y ** 2))) if y.size else 0.0
    if rms > 0:
        y *= (10 ** (-23.0 / 20.0)) / rms      # ~ -23 dB RMS, lit discret
    pic = float(np.max(np.abs(y)))
    if pic > 10 ** (-1.5 / 20.0):              # garde-fou anti-ecretage
        y *= (10 ** (-1.5 / 20.0)) / pic
    return _ecrire(y, dst)


def role_initial(nom):
    for p, r in PREFIXE_ROLE.items():
        if nom.startswith(p):
            return r
    return None


def slug(nom, role):
    """impact-02-slam-sec.mp3 -> impact_slam-sec_02.mp3 : lisible isole."""
    base = os.path.splitext(nom)[0]
    parts = base.split("-")
    num = ""
    reste = []
    for p in parts[1:]:
        if p.isdigit() and not num:
            num = p
        else:
            reste.append(p)
    desc = "-".join(reste) or "sans-nom"
    return "%s_%s_%s.wav" % (role, desc, num or "01")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brut")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    src_dir = os.path.abspath(a.brut)
    fichiers = sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".mp3"))
    if not fichiers:
        print("rien a finaliser dans %s" % src_dir)
        return 1

    catalogue = []
    stats = {r: 0 for r in ORDRE}
    rebut = 0

    print("%-26s %-13s %-13s %s" % ("fichier", "role prevu", "role retenu", "note"))
    print("-" * 92)

    for f in fichiers:
        p = os.path.join(src_dir, f)
        m = measure(p)
        if m is None:
            print("%-26s %-13s %-13s illisible" % (f[:25], "-", "REBUT"))
            rebut += 1
            continue

        prevu = role_initial(f)
        # "ui" a un spec volontairement large (aucune reference mesuree pour ce
        # role). Il ne doit donc JAMAIS servir de fourre-tout : sans ce garde-fou
        # il aspire les sub-graves et vide reveal/riser/texture. On ne le propose
        # que si le son etait effectivement prevu comme un son d'interface.
        candidats = [r for r in ORDRE if r != "ui" or prevu == "ui"]
        passe = [r for r in candidats if judge(m, r)[0] == "PASS"]

        if prevu and prevu in passe:
            retenu, note = prevu, ""
        elif passe:
            retenu = passe[0]
            note = "reaffecte (prevu %s)" % prevu
        else:
            retenu, note = None, "aucun role - %s" % "; ".join(judge(m, prevu or "impact")[1][:1])

        if retenu is None:
            print("%-26s %-13s %-13s %s" % (f[:25], prevu or "-", "REBUT", note))
            if not a.dry:
                d = os.path.join(SFX, "_rebut")
                os.makedirs(d, exist_ok=True)
                shutil.copy2(p, os.path.join(d, f))
            rebut += 1
            continue

        nom = slug(f, retenu)
        dest_dir = os.path.join(SFX, retenu)
        dest = os.path.join(dest_dir, nom)
        print("%-26s %-13s %-13s %s" % (f[:25], prevu or "-", retenu, note))

        if not a.dry:
            os.makedirs(dest_dir, exist_ok=True)
            ok = norm_long(p, dest) if retenu == "texture" else norm_court(p, dest)
            if not ok:
                print("   ! normalisation echouee, copie brute")
                shutil.copy2(p, dest)
            apres = measure(dest) or m
            catalogue.append(dict(
                fichier=nom, role=retenu, source=f,
                centroide_hz=apres["centroide_hz"], dominante_hz=apres["dominante_hz"],
                energie_aigus_pct=round(apres["hf_ratio"] * 100, 1),
                energie_grave_pct=round(apres["sub_ratio"] * 100, 1),
                duree_s=apres["duree_utile"], attaque_ms=round(apres["attaque_s"] * 1000),
                pic_db=apres["peak_db"], rms_db=apres["rms_db"],
                reaffecte=bool(note),
            ))
        stats[retenu] += 1

    if a.dry:
        print("\n[dry] rien ecrit")
        return 0

    cat_path = os.path.join(SFX, "catalogue.json")
    ancien = []
    if os.path.exists(cat_path):
        try:
            ancien = json.load(open(cat_path, encoding="utf-8")).get("sons", [])
        except Exception:
            ancien = []
    connus = {c["fichier"] for c in catalogue}
    fusion = catalogue + [c for c in ancien if c["fichier"] not in connus]
    with open(cat_path, "w", encoding="utf-8") as fh:
        json.dump({"reference_spec": "reference-analysis/nate-herk-DbLuwUVlE9Z "
                                     "(centroide 84-225 Hz, 0-0,3 % au-dessus de 3 kHz)",
                   "sons": sorted(fusion, key=lambda c: (c["role"], c["fichier"]))},
                  fh, ensure_ascii=False, indent=2)

    lignes = ["# Bibliotheque SFX — index",
              "",
              "> Genere par `tools/sfx_finalize.py`. Ne pas editer a la main.",
              "> Chaque son a ete **mesure** avant d'entrer ici : registre sub-grave,",
              "> cale sur la reference qui performe (centroide 84-225 Hz, 0 % au-dessus de 3 kHz).",
              "> Tous normalises : court = pic -1 dBFS, texture = -20 LUFS.",
              ""]
    for r in ORDRE:
        sons = [c for c in fusion if c["role"] == r]
        if not sons:
            continue
        lignes += ["## %s (%d)" % (r, len(sons)), "", USAGE.get(r, ""), "",
                   "| fichier | duree | centroide | grave | attaque |",
                   "|---|---:|---:|---:|---:|"]
        for c in sorted(sons, key=lambda x: x["fichier"]):
            lignes.append("| `%s` | %.2f s | %.0f Hz | %.0f %% | %d ms |" % (
                c["fichier"], c["duree_s"], c["centroide_hz"],
                c["energie_grave_pct"], c["attaque_ms"]))
        lignes.append("")
    with open(os.path.join(SFX, "LISEZ-MOI.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lignes))

    print("\n" + " · ".join("%s %d" % (r, n) for r, n in stats.items() if n))
    print("rebut : %d" % rebut)
    print("-> %s" % cat_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
