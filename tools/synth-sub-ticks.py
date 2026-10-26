# -*- coding: utf-8 -*-
"""Genere les ticks d'interface du registre verrouille.

Pourquoi generer plutot que piocher : la famille `ui/` de la bibliotheque vient
de l'ancienne generation « chrome » et sort entierement du registre (centroide
650 a 3 900 Hz, jusqu'a 81 %% d'energie au-dessus de 3 kHz). Les deux seuls sons
d'interface encore utilises dans le montage #23 mesuraient 266 Hz et 410 Hz de
centroide — et le premier revenait SEPT fois. C'est ce qui grattait l'oreille.

Cible, relevee sur les deux references Nate Herk et verrouillee le 2026-09-10 :
centroide 96-100 Hz, 92-97 %% de l'energie sous 200 Hz, moins de 0,12 %% au-dessus
de 3 kHz. Un tick dans ce registre ne « clique » pas, il se sent — c'est
exactement le vocabulaire autorise : sub, low, deep, chest, thud, felt.

  python tools/synth-sub-ticks.py
"""
import os, sys, wave, struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "audio-analysis-pkgs"))
import numpy as np

SR = 48000
OUT = os.path.join(HERE, "..", "asset-library", "sfx", "sub-tick-v2")
os.makedirs(OUT, exist_ok=True)


def write(path, x):
    x = x / max(np.abs(x).max(), 1e-9) * 0.89
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(v * 32767)) for v in x))


def tick(f0, dur, tau, h2=0.06, sweep=0.0):
    """Une sinusoide grave a attaque raide et decroissance courte.

    Pas de transitoire large bande : c'est l'ATTAQUE qui donne le percussif,
    pas un clic. Un clic ajouterait precisement l'energie haute qu'on evite.
    """
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = f0 * (1.0 - sweep * t / max(dur, 1e-9))
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t / tau)
    env[:int(SR * 0.0022)] *= np.linspace(0, 1, int(SR * 0.0022))   # attaque 2,2 ms
    x = np.sin(ph) * env + h2 * np.sin(2 * ph) * env ** 1.7
    return x


JOBS = [
    # nom                       f0    duree   tau    h2    sweep
    ("sub-tick_item_01.wav",    96,   0.090, 0.022, 0.06, 0.00),   # revelation d'un item
    ("sub-tick_item_02.wav",   104,   0.085, 0.020, 0.05, 0.06),   # variante, evite la repetition
    ("sub-tick_valide_01.wav", 118,   0.170, 0.055, 0.07, 0.38),   # selection / confirmation
]

FR = np.fft.rfftfreq(1024, 1. / SR)
print("cible : centroide 96-100 Hz · >=92 %% sous 200 Hz · <=0,12 %% au-dessus de 3 kHz\n")
print("%-26s %9s %11s %12s" % ("fichier", "centroide", "sous 200Hz", "au-dessus 3k"))
for name, f0, dur, tau, h2, sw in JOBS:
    x = tick(f0, dur, tau, h2, sw)
    p = os.path.join(OUT, name)
    write(p, x)
    n = 1024
    w = np.hanning(n)
    hop = n // 2
    acc = np.zeros(n // 2 + 1)
    for i in range(max((len(x) - n) // hop, 1)):
        acc += np.abs(np.fft.rfft(x[i * hop:i * hop + n] * w)) ** 2
    tot = max(acc.sum(), 1e-20)
    print("%-26s %7.0f Hz %9.1f %% %10.3f %%" % (
        name, (FR * acc).sum() / tot, 100 * acc[FR < 200].sum() / tot, 100 * acc[FR > 3000].sum() / tot))
print("\n->", os.path.normpath(OUT))
