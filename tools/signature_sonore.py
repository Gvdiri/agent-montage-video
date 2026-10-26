# -*- coding: utf-8 -*-
"""Son d'ouverture EN TEST (17/10/2026) — la « signature originale » choisie par le createur parmi 3 versions d'ecoute.

⚠️ Ce n'est PAS une regle : le createur l'a dit, « c'est juste un test pour voir si ca colle avec mon style ». On le pose
seulement quand il sert la video (hook qui demande une ponctuation), et on le propose au createur ; jamais d'office.

Le son : grammaire du « Spider-Verse drop » (begaiement d'images, 3 notes, chute grave), melodie originale.
  Mi6 begaye x4 (eclats de 22 ms tous les 38 ms) -> Sol6 -> Do6 tenu hache en doubles croches -> chute Do3 -> Do2.
  Carre + scie legerement desaccordes, filtre a 4,5 kHz. 1,2 s ; 0 % d'energie entre 300 et 1000 Hz (le coeur de la
  voix) : il passe sous les premiers mots sans les masquer (voix >= +18 dB dans sa bande, mesure sur le #34).
  En do (comme Stranger Things) : a re-accorder si la musique d'une video est dans une tonalite qui frotte.
Pose : a 0,00 s, crete 9 dB sous la crete de la voix en bande telephone (300-3400 Hz).

  python tools/signature_sonore.py   -> asset-library/sfx/impact/impact_signature-test_01.wav (pic -1 dBFS)
  from signature_sonore import generer
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "audio-analysis-pkgs"))
import numpy as np
from scipy.signal import butter, sosfilt


def generer(sr=48000):
    def ton(f0, d, att=0.002, tau=0.09):
        t = np.arange(int(d * sr)) / sr
        w = 0.55 * np.sign(np.sin(2 * np.pi * f0 * t)) + 0.45 * (2 * ((f0 * 1.004 * t) % 1) - 1)
        e = np.exp(-t / tau); a = max(int(att * sr), 1); e[:a] *= np.linspace(0, 1, a)
        return w * e

    sig = np.zeros(int(1.2 * sr))

    def pose(x, at):
        i = int(at * sr); sig[i:i + len(x)] += x[:len(sig) - i]

    for k in range(4):                                    # Mi6 begaye
        pose(ton(1318.5, 0.022, tau=0.02), 0.038 * k)
    pose(ton(1568.0, 0.11, tau=0.06), 0.165)              # Sol6
    do = ton(1046.5, 0.34, tau=0.16)                       # Do6 tenu, hache en doubles croches
    gate = (np.floor(np.arange(len(do)) / sr / 0.042) % 2 == 0).astype(float)
    gate = np.convolve(gate, np.ones(int(sr * 0.002)) / int(sr * 0.002), "same")
    pose(do * (0.55 + 0.45 * gate), 0.29)
    t = np.arange(int(0.6 * sr)) / sr                      # chute Do3 -> Do2
    fq = 130.8 * (65.4 / 130.8) ** np.minimum(t / 0.18, 1)
    ph = 2 * np.pi * np.cumsum(fq) / sr
    drop = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * np.exp(-t / 0.22); drop[:int(sr * 0.002)] *= np.linspace(0, 1, int(sr * 0.002))
    pose(drop * 1.4, 0.56)
    sig = sosfilt(butter(4, 4500, btype="low", fs=sr, output="sos"), sig)
    sig = sosfilt(butter(2, 45, btype="high", fs=sr, output="sos"), sig)
    fo = int(0.12 * sr); sig[-fo:] *= np.linspace(1, 0, fo)
    return sig / np.abs(sig).max()


if __name__ == "__main__":
    import soundfile as sf
    out = os.path.abspath(os.path.join(HERE, "..", "asset-library", "sfx", "impact", "impact_signature-test_01.wav"))
    x = generer() * 10 ** (-1 / 20)                         # norme de la bibliotheque : pic -1 dBFS
    sf.write(out, x, 48000, subtype="PCM_16")
    print("%s : %.2f s" % (os.path.basename(out), len(x) / 48000))
