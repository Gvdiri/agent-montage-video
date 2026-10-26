# -*- coding: utf-8 -*-
"""Mesure independante voix / lit (x0,80) sur les fichiers ecrits, par seconde parlee.

  python tools/mesure-lit.py videos/<atelier> [gain_lit_db ...]   (PYTHONPATH=tools/audio-analysis-pkgs)

Cible depuis le 01/10 : bande parole (300-3400) mediane ~16 dB, soit ~14 LU. 8 LU = trop fort ; 14,6 LU
avec carve profond (31 dB en bande parole) = inaudible. Le carve allege fait la difference.
"""
import os, re, subprocess, sys
import numpy as np

SR = 48000


def lire(path, af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def lufs_court(sig):
    """Sonie court terme (3 s) toutes les 0,1 s via ebur128 — K-weighting officiel."""
    raw = sig.astype(np.float32).tobytes()
    p = subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", "ebur128=framelog=verbose", "-f", "null", "-"],
                       input=raw, capture_output=True)
    e = p.stderr.decode("utf-8", "ignore")
    M = [float(x) for x in re.findall(r"M:\s*(-?[\d.]+|-inf)", e)[:-1] if x != "-inf"]
    I = float(re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", e)[-1])
    return I, np.array(re.findall(r"M:\s*(-?[\d.inf]+)", e))


def lufs_int(sig):
    raw = sig.astype(np.float32).tobytes()
    e = subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", "ebur128", "-f", "null", "-"], input=raw, capture_output=True).stderr.decode()
    return float(re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", e)[-1])


def par_seconde(v, b, ref_v):
    n = min(len(v), len(b)) // SR
    out = []
    for k in range(n):
        vs, bs = v[k * SR:(k + 1) * SR], b[k * SR:(k + 1) * SR]
        if 10 * np.log10(np.mean(ref_v[k * SR:(k + 1) * SR] ** 2) + 1e-12) > PAROLE - 10:
            out.append(10 * np.log10(np.mean(vs ** 2) + 1e-12) - 10 * np.log10(np.mean(bs ** 2) + 1e-12))
    return np.array(out)


at = sys.argv[1]
gains = [float(g) for g in sys.argv[2:]] or [0.0]
pub = os.path.join(at, "public")
V = os.path.join(pub, "voice.wav")
B = os.path.join(pub, "music-bed.mp3")
bandes = {"plein": None, "tel(hp150)": "highpass=f=150:p=2,highpass=f=150:p=2",
          "parole(300-3400)": "highpass=f=300,highpass=f=300,lowpass=f=3400,lowpass=f=3400"}
voix = lire(V)
PAROLE = 10 * np.log10(np.mean(voix[np.abs(voix) > 0.01] ** 2))
print("==", os.path.basename(at.rstrip("/\\")))
iv = lufs_int(voix)
for g in gains:
    k = 0.80 * 10 ** (g / 20)
    lit = lire(B) * k
    il = lufs_int(lit)
    lig = ["lit %+.1f dB | LUFS voix %.1f  lit %.1f  ecart %.1f LU" % (g, iv, il, iv - il)]
    for nom, af in bandes.items():
        v = lire(V, af) if af else voix
        b = lire(B, af) * k if af else lit
        d = par_seconde(v, b, voix)
        lig.append("%s med %.1f (min %.1f)" % (nom, np.median(d), d.min()))
    print("   " + " | ".join(lig))
