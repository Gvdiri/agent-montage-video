#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Synthetiseur de SFX - Hyperframes.

Pourquoi synthetiser plutot que generer par IA :

- La vague 1 ElevenLabs a donne 1 son UI utilisable sur 6. Un clic de souris
  sorti du modele mesurait 9 444 Hz de centroide avec 99,7 % d'energie au-dessus
  de 3 kHz : ce n'est pas un clic, c'est du souffle. Le modele est bon sur les
  nappes et les impacts, mauvais sur le mecanique court et sec.
- Un clic, une frappe, un 808 sont des objets simples : une enveloppe et un
  filtre. Les synthetiser donne un controle exact du spectre, donc ils passent
  le banc par construction au lieu de passer par hasard.
- Et c'est gratuit, illimite, deterministe : meme graine, meme fichier.

Sortie : asset-library/sfx/<role>/synth_*.wav, deja normalises.

Usage :
    python tools/synth_sfx.py [--only ui,impact,transition] [--list]
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
import numpy as np
import soundfile as sf
from scipy import signal as sg

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SFX = os.path.join(ROOT, "asset-library", "sfx")

_faits = []


# --------------------------------------------------------------------- briques
def t(dur):
    return np.arange(int(dur * SR), dtype=np.float32) / SR


def env_exp(n, attaque_ms=1.0, decay=0.12, courbe=3.0):
    """Enveloppe percussive : attaque quasi instantanee, decroissance exponentielle."""
    x = np.arange(n, dtype=np.float32) / SR
    a = int(max(attaque_ms, 0.05) / 1000 * SR)
    e = np.exp(-x / max(decay, 1e-4)) ** 1.0
    e = e ** (courbe / 3.0)
    if a > 1:
        e[:a] *= np.linspace(0, 1, a, dtype=np.float32)
    return e.astype(np.float32)


def bruit(n, graine):
    return np.random.default_rng(graine).standard_normal(n).astype(np.float32)


def passe_bande(x, f_lo, f_hi, ordre=4):
    lo = max(f_lo / (SR / 2), 1e-4)
    hi = min(f_hi / (SR / 2), 0.99)
    b, a = sg.butter(ordre, [lo, hi], btype="band")
    return sg.lfilter(b, a, x).astype(np.float32)


def passe_bas(x, f, ordre=4):
    b, a = sg.butter(ordre, min(f / (SR / 2), 0.99), btype="low")
    return sg.lfilter(b, a, x).astype(np.float32)


def sinus_glissant(dur, f0, f1, courbe=4.0):
    """Sinus dont la frequence chute exponentiellement : c'est LA recette du 808."""
    x = t(dur)
    k = np.exp(-x / (dur / courbe))
    f = f1 + (f0 - f1) * k
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase).astype(np.float32)


def resonance(dur, freq, decay, graine=0):
    """Corps resonant amorti - le "body" d'une touche de clavier."""
    x = t(dur)
    return (np.sin(2 * np.pi * freq * x) * np.exp(-x / decay)).astype(np.float32)


def ecrire(y, role, nom, desc):
    y = np.asarray(y, dtype=np.float32)
    n = y.size
    nf = min(int(0.012 * SR), n // 2)
    if nf > 1:
        y[n - nf:] *= np.linspace(1, 0, nf, dtype=np.float32) ** 1.6
    pic = float(np.max(np.abs(y)))
    if pic > 0:
        y = y * ((10 ** (-1.0 / 20.0)) / pic)
    d = os.path.join(SFX, role)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, nom)
    sf.write(p, (np.clip(y, -1, 1) * 32767).astype(np.int16), SR, subtype="PCM_16")
    _faits.append(dict(role=role, fichier=nom, description=desc))
    print("  %-11s %-38s %s" % (role, nom, desc))


# ------------------------------------------------------------------------- UI
def bloc_ui():
    print("\n[ui] — la categorie ou la generation IA a echoue (1/6)")

    def clic(nom, desc, f_lo, f_hi, decay, corps_hz, corps_amp, graine, dur=0.06):
        n = int(dur * SR)
        clack = passe_bande(bruit(n, graine), f_lo, f_hi) * env_exp(n, 0.3, decay, 3.4)
        body = resonance(dur, corps_hz, decay * 1.8) * corps_amp
        ecrire(clack * 0.85 + body, "ui", nom, desc)

    clic("synth_clic-souris_01.wav", "clic de souris sec, plastique, proche", 1800, 4200, 0.010, 220, 0.18, 1)
    clic("synth_clic-souris-grave_02.wav", "clic de souris plus mat, bouton plus lourd", 1200, 3000, 0.014, 160, 0.28, 2)
    clic("synth_touche-clavier_03.wav", "une frappe de clavier mecanique", 2200, 5000, 0.012, 190, 0.22, 3)
    clic("synth_touche-clavier-sourde_04.wav", "frappe amortie, clavier silencieux", 900, 2400, 0.016, 150, 0.34, 4)
    clic("synth_touche-entree_05.wav", "touche entree : le thock, plus de corps", 800, 2600, 0.022, 110, 0.55, 5, dur=0.10)
    clic("synth_tick-ui_06.wav", "tick d'interface minuscule, pour une liste qui defile", 2600, 6000, 0.005, 300, 0.10, 6, dur=0.035)

    # Toggle = deux clics rapproches
    n = int(0.14 * SR)
    y = np.zeros(n, dtype=np.float32)
    for off, amp, g in ((0, 1.0, 11), (int(0.045 * SR), 0.72, 12)):
        m = int(0.05 * SR)
        c = passe_bande(bruit(m, g), 1500, 3800) * env_exp(m, 0.3, 0.009, 3.4) * amp
        y[off:off + m] += c + resonance(0.05, 200, 0.014) * 0.2 * amp
    ecrire(y, "ui", "synth_interrupteur_07.wav", "interrupteur : deux clics, bascule d'etat")

    # Rafale de frappe - le son "je tape une commande"
    for nom, dur, nb, graine, desc in [
        ("synth_frappe-rafale-courte_08.wav", 0.9, 7, 21, "rafale de frappe courte, 7 touches"),
        ("synth_frappe-rafale-longue_09.wav", 2.4, 19, 22, "rafale de frappe longue, on tape une commande"),
    ]:
        rng = np.random.default_rng(graine)
        n = int(dur * SR)
        y = np.zeros(n + int(0.1 * SR), dtype=np.float32)
        pos = 0.02
        for i in range(nb):
            off = int(pos * SR)
            m = int(0.06 * SR)
            f0 = 1900 + rng.random() * 900
            c = passe_bande(bruit(m, int(rng.integers(0, 1 << 30))), f0, f0 + 2600)
            c = c * env_exp(m, 0.3, 0.010 + rng.random() * 0.004, 3.4)
            c = c + resonance(0.06, 170 + rng.random() * 60, 0.018) * 0.22
            amp = 0.72 + rng.random() * 0.28
            y[off:off + m] += c * amp
            pos += (dur - 0.08) / nb * (0.62 + rng.random() * 0.76)
            if pos * SR > n:
                break
        ecrire(y[:n], "ui", nom, desc)

    # Notification : deux tons courts, sobres
    for nom, f1, f2, desc in [
        ("synth_notification-double_10.wav", 720, 960, "notification sobre, deux tons montants"),
        ("synth_notification-simple_11.wav", 640, 640, "notification d'un seul ton, discrete"),
    ]:
        n = int(0.30 * SR)
        y = np.zeros(n, dtype=np.float32)
        for i, f in enumerate((f1, f2)):
            off = int(i * 0.085 * SR)
            m = int(0.16 * SR)
            seg = (np.sin(2 * np.pi * f * t(0.16)) * 0.7
                   + np.sin(2 * np.pi * f * 2 * t(0.16)) * 0.12)
            y[off:off + m] += seg * env_exp(m, 1.5, 0.045, 3.0)
        ecrire(y, "ui", nom, desc)

    # Molette : suite de micro-detentes
    rng = np.random.default_rng(33)
    dur = 0.55
    n = int(dur * SR)
    y = np.zeros(n, dtype=np.float32)
    for i in range(9):
        off = int((0.02 + i * 0.058) * SR)
        m = int(0.02 * SR)
        if off + m >= n:
            break
        y[off:off + m] += (passe_bande(bruit(m, int(rng.integers(0, 1 << 30))), 2400, 5200)
                           * env_exp(m, 0.2, 0.004, 3.6) * (0.7 + rng.random() * 0.3))
    ecrire(y, "ui", "synth_molette-scroll_12.wav", "molette de souris, neuf crans")


# --------------------------------------------------------------------- IMPACT
def bloc_impact():
    print("\n[impact] — attaque instantanee, ce qui manquait aux 3 impacts 'mous'")
    recettes = [
        ("synth_808-profond_01.wav", 0.90, 130, 34, 0.26, 0.0, "808 profond, chute 130->34 Hz"),
        ("synth_808-court_02.wav", 0.55, 150, 42, 0.15, 0.0, "808 court et sec, pour un chiffre"),
        ("synth_808-long_03.wav", 1.60, 110, 28, 0.45, 0.0, "808 long, queue qui roule - fin de sequence"),
        ("synth_coup-poitrine_04.wav", 0.75, 95, 45, 0.20, 0.22, "coup dans la poitrine, un peu de corps"),
        ("synth_coup-mat_05.wav", 0.42, 180, 60, 0.11, 0.30, "coup mat et serre, transitoire marque"),
        ("synth_coup-porte_06.wav", 0.70, 210, 55, 0.16, 0.45, "porte lourde qui claque, piece sourde"),
        ("synth_sub-drop_07.wav", 1.20, 90, 26, 0.35, 0.0, "sub drop pur, se ressent plus qu'il ne s'entend"),
    ]
    for nom, dur, f0, f1, decay, souffle, desc in recettes:
        n = int(dur * SR)
        y = sinus_glissant(dur, f0, f1) * env_exp(n, 0.15, decay, 3.0)
        if souffle > 0:
            y = y + passe_bas(bruit(n, hash(nom) % (1 << 30)), 320) * env_exp(n, 0.15, decay * 0.18, 3.6) * souffle
        y = np.tanh(y * 1.25) * 0.8      # saturation douce : donne du corps sans aigus
        ecrire(y, "impact", nom, desc)

    # Double coup - le "battement de coeur"
    dur = 1.30
    n = int(dur * SR)
    y = np.zeros(n, dtype=np.float32)
    for off_s, amp in ((0.0, 1.0), (0.235, 0.66)):
        seg = sinus_glissant(0.7, 120, 32) * env_exp(int(0.7 * SR), 0.15, 0.18, 3.0) * amp
        off = int(off_s * SR)
        y[off:off + seg.size] += seg[:max(0, n - off)]
    ecrire(np.tanh(y * 1.2) * 0.82, "impact", "synth_double-coup_08.wav", "deux coups : battement de coeur, tension")

    # Impact negatif : deux sub legerement desaccordes -> battement instable
    dur = 1.0
    n = int(dur * SR)
    a = sinus_glissant(dur, 105, 38)
    b = sinus_glissant(dur, 99, 35)
    ecrire(np.tanh((a * 0.6 + b * 0.55) * env_exp(n, 0.2, 0.24, 3.0) * 1.2) * 0.82,
           "impact", "synth_impact-negatif_09.wav", "sub desaccorde : malaise, reserve au negatif/rouge")


# ----------------------------------------------------------------- TRANSITION
def bloc_transition():
    print("\n[transition] — le role le plus consomme a 1,5 s de cadence")
    def whoosh(nom, dur, f_dep, f_arr, graine, desc, sens=1.0):
        n = int(dur * SR)
        x = np.arange(n, dtype=np.float32) / n
        src = bruit(n, graine)
        # filtre passe-bas balaye par blocs : moins couteux qu'un filtre variable
        out = np.zeros(n, dtype=np.float32)
        blocs = 48
        taille = n // blocs
        for i in range(blocs):
            s = i * taille
            e = n if i == blocs - 1 else (i + 1) * taille
            f = f_dep + (f_arr - f_dep) * (i / max(blocs - 1, 1))
            out[s:e] = passe_bas(src[s:e], max(f, 60), ordre=3)
        forme = np.sin(np.pi * x) ** (1.4 if sens > 0 else 0.8)
        ecrire(out * forme.astype(np.float32), "transition", nom, desc)

    whoosh("synth_whoosh-sub-descendant_01.wav", 0.80, 900, 120, 41, "whoosh sourd qui descend")
    whoosh("synth_whoosh-sub-montant_02.wav", 0.80, 120, 900, 42, "whoosh sourd qui monte")
    whoosh("synth_whoosh-court_03.wav", 0.45, 700, 160, 43, "whoosh tres court, coupe rapide")
    whoosh("synth_whoosh-large_04.wav", 1.20, 1100, 100, 44, "whoosh large, changement de sequence")
    whoosh("synth_balayage-sourd_05.wav", 0.65, 400, 180, 45, "balayage mat, changement de panneau")
    whoosh("synth_air-ferme_06.wav", 0.95, 600, 140, 46, "deplacement d'air en piece fermee")

    # Coupe seche : un thump minuscule, presque subliminal
    for nom, dur, f0, f1, desc in [
        ("synth_coupe-seche_07.wav", 0.22, 260, 90, "coupe seche, presque subliminale"),
        ("synth_coupe-douce_08.wav", 0.34, 200, 80, "coupe douce, liaison discrete"),
    ]:
        n = int(dur * SR)
        y = sinus_glissant(dur, f0, f1) * env_exp(n, 0.4, dur * 0.3, 3.2) * 0.9
        y += passe_bas(bruit(n, hash(nom) % (1 << 30)), 500) * env_exp(n, 0.4, dur * 0.16, 3.6) * 0.35
        ecrire(y, "transition", nom, desc)


# ---------------------------------------------------------------------- RISER
def bloc_riser():
    print("\n[riser]")
    for nom, dur, f0, f1, graine, desc in [
        ("synth_montee-sourde_01.wav", 2.0, 90, 700, 61, "montee sourde, filtre qui s'ouvre"),
        ("synth_montee-courte_02.wav", 1.2, 110, 520, 62, "montee courte avant une revelation"),
        ("synth_montee-longue_03.wav", 3.2, 70, 900, 63, "montee longue, tension qui s'installe"),
    ]:
        n = int(dur * SR)
        src = bruit(n, graine)
        out = np.zeros(n, dtype=np.float32)
        blocs = 64
        taille = n // blocs
        for i in range(blocs):
            s = i * taille
            e = n if i == blocs - 1 else (i + 1) * taille
            f = f0 + (f1 - f0) * ((i / max(blocs - 1, 1)) ** 1.7)
            out[s:e] = passe_bas(src[s:e], max(f, 60), ordre=3)
        forme = (np.arange(n, dtype=np.float32) / n) ** 1.5
        sub = sinus_glissant(dur, 45, 70) * forme * 0.5
        ecrire(out * forme * 0.85 + sub, "riser", nom, desc)


BLOCS = {"ui": bloc_ui, "impact": bloc_impact, "transition": bloc_transition, "riser": bloc_riser}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("\n".join(BLOCS))
        return 0
    for n in ([x.strip() for x in a.only.split(",")] if a.only else list(BLOCS)):
        if n not in BLOCS:
            print("bloc inconnu : %s" % n)
            return 1
        BLOCS[n]()
    with open(os.path.join(SFX, "_manifeste-synth.json"), "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/synth_sfx.py", "sons": _faits}, fh, ensure_ascii=False, indent=2)
    print("\n%d sons synthetises" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
