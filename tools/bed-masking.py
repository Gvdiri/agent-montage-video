# -*- coding: utf-8 -*-
"""Banc de masquage : quelle piste laisse le plus de place A CETTE voix.

Le choix du lit musical ne se fait pas a l'oreille sur 10 secondes : sous une voix
donnee, deux pistes qui « sonnent pareil » peuvent masquer du simple au double.
On mesure donc, fenetre par fenetre :

  speech_share : part de l'energie de la piste dans 300-3400 Hz (la bande de la voix)
  masking      : recouvrement spectral PONDERE par l'energie de la voix — une piste
                 peut avoir peu d'energie vocale globale et quand meme taper pile
                 dans les formants qui portent l'intelligibilite.

⚠ Regle de la maison : une metrique ne compte que si elle reproduit d'abord le
choix connu d'un actif valide. VOID 2:20-2:42 est le lit de la video Obsidian qui
a marche ; si ce banc ne le ressort pas en tete, c'est le banc qui est faux.

  python tools/bed-masking.py <voix.wav>
"""
import os, sys, json, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "audio-analysis-pkgs"))
sys.path.insert(0, os.path.join(HERE, "python-packages"))
import numpy as np

SR = 22050
LIB = os.path.join(HERE, "..", "asset-library", "music", "1-EN-USAGE")
TRACKS = ["01-SHENMUE", "02-BLANKA", "03-ONIZUKA"]  # le trio PNL, 2026-09-23
SPEECH = (300., 3400.)


def load(path, ss=None, dur=None):
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as fh:
        tmp = fh.name
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    cmd += ["-i", path]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "f32le", tmp]
    subprocess.run(cmd, check=True)
    a = np.fromfile(tmp, dtype=np.float32)
    os.unlink(tmp)
    return a.astype(np.float64)


def spectrum(x, n=2048):
    """Spectre moyen en puissance, fenetre de Hann, sauts de n/2."""
    if len(x) < n:
        return None
    w = np.hanning(n)
    hop = n // 2
    frames = 1 + (len(x) - n) // hop
    acc = np.zeros(n // 2 + 1)
    for i in range(frames):
        seg = x[i * hop:i * hop + n] * w
        acc += np.abs(np.fft.rfft(seg)) ** 2
    return acc / frames


FREQS = np.fft.rfftfreq(2048, 1. / SR)
BAND = (FREQS >= SPEECH[0]) & (FREQS <= SPEECH[1])


def measure(voice_spec, music):
    ms = spectrum(music)
    if ms is None:
        return None
    share = ms[BAND].sum() / max(ms.sum(), 1e-20)
    # Recouvrement pondere : la voix dit OU elle a besoin de place, la musique dit
    # combien elle en prend. On normalise par l'energie totale de chacune pour que
    # la mesure soit un rapport, pas un niveau (le niveau, c'est le mixage).
    v = voice_spec[BAND] / max(voice_spec[BAND].sum(), 1e-20)
    m = ms[BAND] / max(ms.sum(), 1e-20)
    masking = float((v * m).sum() * len(v))
    return share, masking


def main():
    voice = load(sys.argv[1])
    vs = spectrum(voice)
    an = json.load(open(os.path.join(LIB, "analyse-spectrale.json"), encoding="utf-8"))
    by_title = {t["title"]: t for t in an["tracks"]}

    rows = []
    for name in TRACKS:
        path = os.path.join(LIB, "complets", name + ".mp3")
        key = [k for k in by_title if name.split("-", 1)[1].replace("-", " ").lower() in k.lower()]
        wins = by_title[key[0]]["bestWindows"][:6] if key else []
        if not wins:
            wins = [{"startSec": s, "endSec": s + 22} for s in (30, 80, 130, 180)]
        for w in wins:
            mus = load(path, w["startSec"], w["endSec"] - w["startSec"])
            r = measure(vs, mus)
            if r:
                rows.append((name, w["startSec"], w["endSec"], r[0], r[1]))

    rows.sort(key=lambda r: r[4])
    print("%-12s %-14s %10s %10s" % ("piste", "fenetre", "bande voix", "masquage"))
    for n, s, e, sh, mk in rows:
        print("%-12s %-14s %9.2f%% %10.3f" % (n, "%.0f-%.0fs" % (s, e), sh * 100, mk))
    json.dump([{"track": n, "start": s, "end": e, "speech_share": sh, "masking": mk}
               for n, s, e, sh, mk in rows],
              open(os.path.join(HERE, "..", "temp", "bed-masking.json"), "w"), indent=1)


main()
