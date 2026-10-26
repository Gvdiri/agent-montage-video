#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Banc de mesure SFX - Hyperframes.

Pourquoi ce fichier existe : la doctrine de retention (EDITING_SYSTEM.md, 2026-09-06)
a mesure le design sonore de la reference qui performe. Resultat : centroide spectral
315 Hz sur le hook, 219 Hz sur la revelation, 0 % d'energie au-dessus de 3 kHz.
Notre bibliotheque d'alors etait brillante -> mauvais registre.

On arrete de juger a l'oreille. Chaque SFX genere passe ici avant d'entrer dans la
bibliotheque. Ce qui sort du spec est jete, pas "ecoute une deuxieme fois".

Usage:
    python tools/sfx_bench.py <fichier|dossier> [...] [--role ROLE] [--json out.json]
"""
import sys
import os
import json
import argparse
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))

import numpy as np
import librosa

SR = 44100
AUDIO_EXT = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"}

# Spec par role. Cales sur les mesures de reference-analysis/nate-herk-DbLuwUVlE9Z.
# centroid_max : plafond de brillance. Au-dessus, le son cliquette au lieu de se ressentir.
# hf_ratio_max : part de l'energie au-dessus de 3 kHz. La reference est a 0 %.
# sub_ratio_min : part de l'energie sous 200 Hz. C'est ce qui fait le coup dans la poitrine.
ROLE_SPECS = {
    "impact": dict(centroid_max=450, hf_ratio_max=0.06, sub_ratio_min=0.35,
                   dur_min=0.25, dur_max=2.2, attack_max=0.06),
    "reveal": dict(centroid_max=700, hf_ratio_max=0.12, sub_ratio_min=0.20,
                   dur_min=0.6, dur_max=3.5, attack_max=1.2),
    "transition": dict(centroid_max=900, hf_ratio_max=0.20, sub_ratio_min=0.12,
                       dur_min=0.2, dur_max=1.6, attack_max=0.5),
    "riser": dict(centroid_max=1400, hf_ratio_max=0.30, sub_ratio_min=0.08,
                  dur_min=0.8, dur_max=4.0, attack_max=3.5),
    # ⚠️ UI : SEUL ROLE DONT LE SPEC N'EST PAS MESURE SUR UNE REFERENCE.
    # Les deux references analysees n'ont aucun son d'interface (0 % d'energie
    # au-dessus de 3 kHz sur toute leur timeline). Un clic de clavier est
    # brillant par nature : lui appliquer le spec sub-grave de la marque n'a
    # pas de sens. Ces bornes sont donc larges a dessein - elles n'attrapent
    # que le vrai dechet (le "clic" ElevenLabs a 9 444 Hz / 99,7 % d'aigus).
    # A REVOIR des qu'une reference avec du son d'interface aura ete mesuree.
    "ui": dict(centroid_max=5200, hf_ratio_max=0.88, sub_ratio_min=0.0,
               dur_min=0.02, dur_max=3.0, attack_max=2.0),
    "confirmation": dict(centroid_max=1200, hf_ratio_max=0.25, sub_ratio_min=0.10,
                         dur_min=0.2, dur_max=1.8, attack_max=0.25),
    "texture": dict(centroid_max=2500, hf_ratio_max=0.45, sub_ratio_min=0.0,
                    dur_min=0.3, dur_max=8.0, attack_max=8.0),
    # "libre" = on mesure sans juger (pour analyser une reference)
    "libre": None,
}


def db(x):
    return 20.0 * np.log10(max(float(x), 1e-12))


def measure(path):
    y, sr = librosa.load(path, sr=SR, mono=True)
    if y.size == 0:
        return None

    peak = float(np.max(np.abs(y)))
    if peak <= 0:
        return None
    # Bornes utiles : on ignore le silence de tete et de queue a -50 dB du pic.
    thr = peak * (10 ** (-50 / 20.0))
    loud = np.where(np.abs(y) > thr)[0]
    if loud.size == 0:
        return None
    i0, i1 = int(loud[0]), int(loud[-1])
    core = y[i0:i1 + 1]
    dur_utile = core.size / sr

    # Spectre moyen pondere par l'energie, sur la partie utile seulement.
    n_fft = 4096
    S = np.abs(librosa.stft(core, n_fft=n_fft, hop_length=n_fft // 4)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    spec = S.sum(axis=1)
    total = float(spec.sum()) or 1e-12

    centroid = float((freqs * spec).sum() / total)
    hf_ratio = float(spec[freqs > 3000].sum() / total)
    sub_ratio = float(spec[freqs < 200].sum() / total)
    lo_mid_ratio = float(spec[(freqs >= 200) & (freqs <= 1000)].sum() / total)
    dom = float(freqs[int(np.argmax(spec))])

    # Attaque : temps entre le debut utile et le pic
    peak_idx = int(np.argmax(np.abs(core)))
    attack = peak_idx / sr
    rms = float(np.sqrt(np.mean(core ** 2)))

    # Queue : duree apres le pic pour retomber a -30 dB du pic
    tail_thr = peak * (10 ** (-30 / 20.0))
    after = np.abs(core[peak_idx:])
    below = np.where(after < tail_thr)[0]
    tail = float(below[0] / sr) if below.size else float(after.size / sr)

    return dict(
        fichier=os.path.basename(path),
        chemin=path.replace("\\", "/"),
        duree_fichier=round(y.size / sr, 3),
        duree_utile=round(dur_utile, 3),
        centroide_hz=round(centroid, 1),
        dominante_hz=round(dom, 1),
        hf_ratio=round(hf_ratio, 4),
        sub_ratio=round(sub_ratio, 4),
        lo_mid_ratio=round(lo_mid_ratio, 4),
        attaque_s=round(attack, 4),
        queue_s=round(tail, 3),
        peak_db=round(db(peak), 2),
        rms_db=round(db(rms), 2),
    )


def judge(m, role):
    spec = ROLE_SPECS.get(role)
    if spec is None:
        return "-", []
    fails = []
    if m["centroide_hz"] > spec["centroid_max"]:
        fails.append("centroide %.0fHz > %dHz (trop brillant)" % (m["centroide_hz"], spec["centroid_max"]))
    if m["hf_ratio"] > spec["hf_ratio_max"]:
        fails.append("aigus %.1f%% > %.0f%%" % (m["hf_ratio"] * 100, spec["hf_ratio_max"] * 100))
    if m["sub_ratio"] < spec["sub_ratio_min"]:
        fails.append("grave %.1f%% < %.0f%%" % (m["sub_ratio"] * 100, spec["sub_ratio_min"] * 100))
    if not (spec["dur_min"] <= m["duree_utile"] <= spec["dur_max"]):
        fails.append("duree %.2fs hors [%s-%s]s" % (m["duree_utile"], spec["dur_min"], spec["dur_max"]))
    if m["attaque_s"] > spec["attack_max"]:
        fails.append("attaque %.0fms > %.0fms (mou)" % (m["attaque_s"] * 1000, spec["attack_max"] * 1000))
    return ("PASS" if not fails else "FAIL"), fails


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in sorted(files):
                    if os.path.splitext(f)[1].lower() in AUDIO_EXT:
                        out.append(os.path.join(root, f))
        elif os.path.splitext(p)[1].lower() in AUDIO_EXT:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--role", default="libre", choices=list(ROLE_SPECS.keys()))
    ap.add_argument("--json", default=None)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    files = collect(a.paths)
    if not files:
        print("aucun fichier audio trouve")
        return 1

    rows = []
    hdr = "%-38s %6s %7s %7s %6s %6s %7s %7s  verdict" % (
        "fichier", "dur", "centr", "dom", ">3k", "<200", "atk", "peak")
    if not a.quiet:
        print(hdr)
        print("-" * len(hdr))
    for f in files:
        m = measure(f)
        if m is None:
            print("%-38s (vide / illisible)" % os.path.basename(f))
            continue
        verdict, fails = judge(m, a.role)
        m["role"] = a.role
        m["verdict"] = verdict
        m["motifs"] = fails
        rows.append(m)
        if not a.quiet:
            print("%-38s %5.2fs %6.0fH %6.0fH %5.1f%% %5.1f%% %5.0fms %6.1f  %s" % (
                m["fichier"][:37], m["duree_utile"], m["centroide_hz"], m["dominante_hz"],
                m["hf_ratio"] * 100, m["sub_ratio"] * 100, m["attaque_s"] * 1000,
                m["peak_db"], verdict))
            for x in fails:
                print("%-38s   ! %s" % ("", x))

    if a.json:
        d = os.path.dirname(os.path.abspath(a.json))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
        if not a.quiet:
            print("\n-> %s" % a.json)

    if a.role != "libre":
        ok = sum(1 for r in rows if r["verdict"] == "PASS")
        print("\n%d/%d PASS (role: %s)" % (ok, len(rows), a.role))
    return 0


if __name__ == "__main__":
    sys.exit(main())
