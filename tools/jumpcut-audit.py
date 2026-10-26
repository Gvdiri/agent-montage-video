"""Mesure la brutalite visuelle des raccords d'un cut talking-head.

Detecte les coupes, puis mesure a chaque coupe le DEPLACEMENT du sujet entre les
images qui l'encadrent (recherche exhaustive par correlation normalisee, robuste
aux changements de contenu), plus l'ecart d'image residuel apres recalage.

  python tools/jumpcut-audit.py <video.mp4> [--cuts t1,...] [--k 4]
"""
import argparse, subprocess, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seam_match import ncc_shift

W, H = 270, 480
SCALE = 1080 / W

def frames(path):
    p = subprocess.run(['ffmpeg','-v','error','-i',path,'-vf',f'scale={W}:{H}',
                        '-pix_fmt','gray','-f','rawvideo','-'], capture_output=True)
    a = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(a)//(W*H)
    return a[:n*W*H].reshape(n,H,W).astype(np.float32)/255.

def detect_cuts(f, fps):
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1,2))
    med = np.median(d); mad = np.median(np.abs(d-med))+1e-9
    z = (d-med)/mad
    keep, last = [], -99
    for i in np.where(z > 12)[0]:
        if i-last > int(fps*0.25): keep.append(i+1)
        last = i
    return keep

def subject_roi(f):
    v = f.var(axis=0); thr = np.percentile(v, 88)
    ys, xs = np.where(v > thr)
    y0,y1 = np.percentile(ys,[2,98]).astype(int)
    x0,x1 = np.percentile(xs,[2,98]).astype(int)
    return slice(max(0,y0), y0+int((y1-y0)*0.55)), slice(max(0,x0), x1)

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('--cuts', default=''); ap.add_argument('--fps', type=float, default=60.)
ap.add_argument('--k', type=int, default=4)
a = ap.parse_args()

f = frames(a.video)
cuts = ([int(round(float(t)*a.fps)) for t in a.cuts.split(',')] if a.cuts else detect_cuts(f, a.fps))
roi = subject_roi(f)
print(f"{len(f)} frames · {len(f)/a.fps:.2f}s · {len(cuts)} coupes")

K = a.k
print(f"\n{'#':>2} {'temps':>7} {'dx':>7} {'dy':>7} {'saut':>8} {'score':>6} {'ecart img':>10}")
mags, res = [], []
for i,k in enumerate(cuts,1):
    if k < K or k+K > len(f): continue
    A = np.median(f[k-K:k][:,roi[0],roi[1]], axis=0)
    B = np.median(f[k:k+K][:,roi[0],roi[1]], axis=0)
    d, sc = ncc_shift(A, B, rng=16)
    mag = np.hypot(*d)*SCALE
    ecart = float(np.abs(A-B).mean())
    mags.append(mag); res.append(ecart)
    print(f"{i:>2} {k/a.fps:7.2f} {d[0]*SCALE:+7.1f} {d[1]*SCALE:+7.1f} {mag:7.1f}px {sc:6.3f} {ecart:10.4f}")
if mags:
    print(f"\n  saut median {np.median(mags):5.1f} px · moyen {np.mean(mags):5.1f} px · max {max(mags):5.1f} px")
    print(f"  ecart d'image median {np.median(res):.4f}")
