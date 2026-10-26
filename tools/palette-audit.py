# -*- coding: utf-8 -*-
"""Audit de palette : un montage respecte-t-il brand-visual-system.md ?

Classe chaque pixel dans la palette canonique et sort la repartition, plus la
part de pixels SATURES HORS PALETTE (hors carnation) — c'est cette derniere qui
trahit une derive comme celle de la v3.

  python tools/palette-audit.py <video.mp4> [<video2.mp4> ...]
"""
import subprocess, sys
import numpy as np

W, H = 160, 284
PAL = {                      # palette canonique
    "graphite":  (0x07, 0x10, 0x17),
    "ivoire":    (0xF3, 0xF1, 0xEA),
    "acier":     (0x8D, 0x9A, 0xA1),
    "signal":    (0x22, 0xB9, 0xF2),
    "ice":       (0x8E, 0xDD, 0xF7),
    "mineral":   (0xF4, 0xF7, 0xF3),
    "cyan":      (0x25, 0xB9, 0xEE),
}


def frames(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vf', 'scale=%d:%d' % (W, H),
                        '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'], capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.uint8)
    n = len(a) // (W * H * 3)
    return a[:n * W * H * 3].reshape(n, H, W, 3).astype(np.float32)


def audit(path):
    f = frames(path)
    px = f.reshape(-1, 3)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    mx, mn = px.max(axis=1), px.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)

    # la carnation : chaud, rouge dominant, moyennement sature
    peau = (r > g + 12) & (g > b + 6) & (mx > 60) & (sat > .12) & (sat < .62)
    # la famille bleue de la marque (signal / ice / cyan)
    bleu = (b > r + 25) & (b > 90) & (sat > .22)
    # neutres : graphite / acier / ivoire — faible saturation
    neutre = sat <= .16
    graphite = neutre & (mx < 70)
    acier = neutre & (mx >= 70) & (mx < 190)
    ivoire = neutre & (mx >= 190)
    hors = ~(peau | bleu | neutre)

    tot = len(px)
    return {"graphite": graphite.sum() / tot * 100, "acier": acier.sum() / tot * 100,
            "ivoire": ivoire.sum() / tot * 100, "bleu": bleu.sum() / tot * 100,
            "carnation": peau.sum() / tot * 100, "HORS PALETTE": hors.sum() / tot * 100}


rows = [(p.split("\\")[-1].split("/")[-1], audit(p)) for p in sys.argv[1:]]
keys = ["graphite", "acier", "ivoire", "bleu", "carnation", "HORS PALETTE"]
print("%-26s %s" % ("", "".join("%12s" % k for k in keys)))
for name, d in rows:
    print("%-26s %s" % (name[:26], "".join("%11.2f%%" % d[k] for k in keys)))
print("\ncharte : graphite ~55 %% · ivoire ~30 %% · acier ~10 %% · bleu 3-5 %% max")
print("la carnation est le contrepoids humain assume ; HORS PALETTE doit tendre vers 0")
