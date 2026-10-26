# -*- coding: utf-8 -*-
"""Garde-fou de mix : la musique et les SFX restent SOUS la voix, mesure a l'appui.

Pourquoi (2026-09-30) : le createur trouvait que le son d'arriere-plan « prend le
dessus » sur les #16 et #21. Mesure par fenetres de 1 s : le lit etait AU NIVEAU de
la voix sur l'intro et le CTA (ecart 0 dB, voire -6 dB), puis a -38/-51 dB au milieu
— un yo-yo. Cause : un contour dessine a la main (0 dB sur les plans « forts »,
-15 dB ailleurs) sans regarder le niveau reel de la voix, qui change d'un rush a
l'autre (-17,9 dB sur le #16, -21,2 dB sur le #21). Les SFX empiles (riser + impact
+ transition sur la meme coupe) montaient aussi 8 dB au-dessus de la voix.

Deux fonctions :
  asservir_lit(x, voix, sr, ecart_db)  -> le lit suit la voix a ecart constant ;
  plafonner_sfx(sfx, dossier, voix, dur) -> aucune fenetre de SFX ne passe la voix.
"""
import subprocess
import numpy as np


def charger(path, sr=48000, mono=True):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1" if mono else "2",
           "-ar", str(sr), "-f", "f32le", "pipe:1"]
    a = np.frombuffer(subprocess.run(cmd, check=True, capture_output=True).stdout,
                      dtype=np.float32).astype(np.float64)
    return a if mono else a.reshape(-1, 2)


def _rms_db(x, sr, fen):
    """RMS glissant (dB) sur une fenetre de `fen` secondes, un point par 10 ms."""
    hop = sr // 100
    n = max(1, int(fen * sr))
    c = np.concatenate([[0.0], np.cumsum(x * x)])
    centres = np.arange(0, len(x), hop)
    a = np.clip(centres - n // 2, 0, len(x))
    b = np.clip(centres + n // 2, 0, len(x))
    e = (c[b] - c[a]) / np.maximum(b - a, 1)
    return 10 * np.log10(e + 1e-12)


def niveau_parole(voix, sr=48000):
    """RMS de la voix sur les seules fenetres parlees (dB)."""
    v = _rms_db(voix, sr, 0.4)
    return float(10 * np.log10(np.mean(10 ** (v[v > v.max() - 30] / 10))))


def asservir_lit(x, voix, sr, ecart_db=10.0, volume_html=0.80, fondu_in=0.4, fondu_out=0.6):
    """Regle le lit (stereo, deja creuse/duck) pour qu'il reste `ecart_db` sous la voix.

    - le niveau de voix est sa moyenne sur 1,5 s, plancher a la parole -3 dB ;
    - le lit est mesure sur 2 s (un lit rythmique lu sur 0,3 s tombe entre les temps) ;
    - `volume_html` compense le data-volume de la balise <audio>.
    """
    n = len(x)
    mono = x.mean(axis=1)
    ref = niveau_parole(voix[:n], sr)
    # Niveau MOYEN de la voix sur 1,5 s (pas ses crêtes : viser les crêtes laissait
    # le lit à 2-5 dB de la voix au lieu de 10), plancher à la parole -3 dB pour
    # qu'un blanc entre deux phrases ne fasse pas plonger le lit.
    vh = np.maximum(_rms_db(voix[:n], sr, 1.5), ref - 3.0)
    b = _rms_db(mono, sr, 2.0)
    m = min(len(vh), len(b))
    g = (vh[:m] - ecart_db + 20 * np.log10(1.0 / volume_html)) - b[:m]
    g = np.clip(g, -24.0, 6.0)
    g = np.convolve(g, np.ones(31) / 31, mode="same")          # lissage 0,3 s
    t = np.arange(n) / float(sr)
    gd = np.interp(t, np.arange(m) / 100.0, g)
    gd += np.interp(t, [0, fondu_in], [-22.0, 0.0])            # fondu d'entree
    gd += np.interp(t, [t[-1] - fondu_out, t[-1]], [0.0, -30.0])  # fondu de sortie
    return x * (10 ** (gd / 20.0))[:, None], ref


def plafonner_sfx(sfx, dossier, voix, dur, sr=48000, marge_db=0.0, fen=0.5):
    """Baisse les SFX des fenetres ou leur somme passe au-dessus de la voix parlee.

    `sfx` = [(fichier, debut, duree, gain)] ; renvoie la meme liste, gains corriges.
    Chaque son recoit UNE correction : la plus forte exigee par les fenetres qu'il
    touche (un premier essai cumulait les corrections et enterrait les SFX a -30 dB).
    """
    import os
    ref = niveau_parole(voix, sr) - marge_db
    cache = {}
    sfx = [list(s) for s in sfx]
    n = int(dur * sr)
    w = int(fen * sr)
    for _ in range(2):
        somme = np.zeros(n)
        for f, t, d, g in sfx:
            if f not in cache:
                cache[f] = charger(os.path.join(dossier, f), sr)
            a = cache[f][:int(d * sr)] * g
            i = int(t * sr)
            j = min(n, i + len(a))
            somme[i:j] += a[:j - i]
        fac = [1.0] * len(sfx)
        for i in range(0, n, w):
            seg = somme[i:i + w]
            e = 10 * np.log10(np.mean(seg * seg) + 1e-12)
            if e <= ref:
                continue
            f_ = 10 ** (-(e - ref) / 20.0)
            t0, t1 = i / float(sr), (i + w) / float(sr)
            for k, s in enumerate(sfx):
                if s[1] < t1 and s[1] + s[2] > t0:
                    fac[k] = min(fac[k], f_)
        if all(f_ == 1.0 for f_ in fac):
            break
        for k, s in enumerate(sfx):
            s[3] = round(s[3] * fac[k], 3)
    return [tuple(s) for s in sfx]
