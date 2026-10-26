"""Recalage geometrique des raccords d'un cut talking-head.

1. Isole la zone du sujet par la VARIANCE TEMPORELLE (le mur est fixe, la tete bouge).
2. Mesure le deplacement A CHAQUE RACCORD, entre l'image mediane des K dernieres frames
   du plan et celle des K premieres du plan suivant (la mediane annule le mouvement
   de bouche, qui n'est pas un deplacement de la tete).
3. Resout un decalage constant par plan qui annule ces sauts, borne par regularisation.
4. VERIFIE la correction en simulation avant tout rendu.
"""
import json, subprocess, sys, os
import numpy as np

W, H = 270, 480
SCALE = 1080 / W

def frames(path):
    p = subprocess.run(['ffmpeg','-v','error','-i',path,'-vf',f'scale={W}:{H}',
                        '-pix_fmt','gray','-f','rawvideo','-'], capture_output=True)
    a = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(a)//(W*H)
    return a[:n*W*H].reshape(n,H,W).astype(np.float32)/255.

def shift(a, b):
    """deplacement du contenu de b par rapport a a, en pixels d'analyse"""
    win = np.hanning(a.shape[0])[:,None]*np.hanning(a.shape[1])[None,:]
    R = np.fft.rfft2(a*win)*np.conj(np.fft.rfft2(b*win))
    R /= np.abs(R)+1e-12
    c = np.fft.irfft2(R, s=a.shape)
    k = np.unravel_index(np.argmax(c), c.shape)
    out=[]
    for ax in range(2):
        i, n = k[ax], c.shape[ax]
        m = c[k]
        lo = c[(k[0]-1)%c.shape[0],k[1]] if ax==0 else c[k[0],(k[1]-1)%c.shape[1]]
        hi = c[(k[0]+1)%c.shape[0],k[1]] if ax==0 else c[k[0],(k[1]+1)%c.shape[1]]
        den = lo-2*m+hi
        v = i + (0.5*(lo-hi)/den if abs(den)>1e-9 else 0.)
        if v > n/2: v -= n
        out.append(v)
    # shift() renvoie -d ; on veut d = deplacement de b par rapport a a
    return np.array([-out[1], -out[0]])          # dx, dy

def subject_roi(f):
    v = f.var(axis=0)
    thr = np.percentile(v, 88)
    ys, xs = np.where(v > thr)
    y0,y1 = np.percentile(ys,[2,98]).astype(int)
    x0,x1 = np.percentile(xs,[2,98]).astype(int)
    # on garde le haut du sujet : tete et epaules, pas les mains
    y1 = y0 + int((y1-y0)*0.55)
    return slice(max(0,y0), y1), slice(max(0,x0), x1)

def main():
    vid, segf, outf = sys.argv[1], sys.argv[2], sys.argv[3]
    lam = float(sys.argv[4]) if len(sys.argv)>4 else 0.10
    K = 4
    segs = json.load(open(segf)); fps = 60.0
    cache = outf + '.frames.npy'
    f = np.load(cache) if os.path.exists(cache) else frames(vid)
    if not os.path.exists(cache): np.save(cache, f)
    print(f"{len(f)} frames · {len(f)/fps:.2f}s")

    roi = subject_roi(f)
    print(f"zone sujet : x {roi[1].start}-{roi[1].stop} · y {roi[0].start}-{roi[0].stop} (sur {W}x{H})")

    bounds, k = [], 0
    for s,e in segs:
        n = int(round((e-s)*fps)); bounds.append((k, k+n)); k += n
    bounds[-1] = (bounds[-1][0], min(bounds[-1][1], len(f)))

    def med(a, b):
        return np.median(f[a:b][:, roi[0], roi[1]], axis=0)

    n = len(bounds)
    s = []
    for j in range(n-1):
        a0,a1 = bounds[j]; b0,b1 = bounds[j+1]
        A = med(max(a0,a1-K), a1)
        B = med(b0, min(b1, b0+K))
        s.append(shift(A, B))
    s = np.array(s)

    A = np.zeros((n-1+n, n)); rhs = np.zeros((n-1+n, 2))
    for j in range(n-1):
        A[j, j+1] = 1.0; A[j, j] = -1.0
        rhs[j] = s[j]
    for j in range(n):
        A[n-1+j, j] = lam
    c, *_ = np.linalg.lstsq(A, rhs, rcond=None)
    c = c - (c.max(axis=0)+c.min(axis=0))/2

    # VERIFICATION EN SIMULATION : on decale reellement les frames et on remesure
    print(f"\n{'raccord':>8} {'avant':>9} {'apres (simule)':>16}")
    before, after = [], []
    ci = np.round(c).astype(int)
    for j in range(n-1):
        a0,a1 = bounds[j]; b0,b1 = bounds[j+1]
        A2 = med(max(a0,a1-K), a1); B2 = med(b0, min(b1, b0+K))
        d0 = np.hypot(*s[j])*SCALE
        As = np.roll(A2, (-ci[j][1], -ci[j][0]), axis=(0,1))
        Bs = np.roll(B2, (-ci[j+1][1], -ci[j+1][0]), axis=(0,1))
        d1 = np.hypot(*(s[j] - (c[j+1]-c[j])))*SCALE
        d1sim = np.hypot(*shift(As, Bs))*SCALE
        before.append(d0); after.append(d1)
        print(f"{j+1:>8} {d0:8.1f}px {d1:11.1f}px {d1sim:11.1f}px")
    print(f"\n  median  {np.median(before):5.1f} px  ->  {np.median(after):5.1f} px")
    print(f"  max     {max(before):5.1f} px  ->  {max(after):5.1f} px")
    off = c*SCALE
    mx,my = np.abs(off)[:,0].max(), np.abs(off)[:,1].max()
    print(f"  offsets max : dx {mx:.0f} px · dy {my:.0f} px")
    json.dump({'offsets': off.tolist()}, open(outf,'w'))

main()
