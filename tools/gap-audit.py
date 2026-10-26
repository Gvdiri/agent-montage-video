"""Audit des blancs d'un cut : compare les blancs AUX RACCORDS aux blancs NATURELS.

Mesure sur une enveloppe RMS 5 ms, seuil relatif au niveau de parole du rush
(et non un seuil absolu : c'est ce qui avait faussé la première passe).

  python tools/gap-audit.py <audio.wav> [--joins t1,t2,...] [--drop 26]
"""
import sys, wave, json, argparse
import numpy as np

HOP = 0.005

def envelope(path, hop=HOP):
    w = wave.open(path, 'rb')
    n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
    x = np.frombuffer(w.readframes(n), dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float64)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    x /= float(2 ** (8 * sw - 1))
    h = int(sr * hop)
    m = len(x) // h
    rms = np.sqrt((x[:m * h].reshape(m, h) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(rms), hop, len(x) / sr

def gaps(db, hop, thr, minlen=0.030):
    quiet = db < thr
    out, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) * hop >= minlen:
                out.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument('audio')
    p.add_argument('--joins', default='')
    p.add_argument('--drop', type=float, default=26.0,
                   help='seuil = niveau de parole - DROP dB')
    a = p.parse_args()

    db, hop, dur = envelope(a.audio)
    speech = np.percentile(db[db > db.max() - 40], 75)
    thr = speech - a.drop
    g = gaps(db, hop, thr)
    joins = [float(t) for t in a.joins.split(',') if t.strip()]

    jg, ng = [], []
    for s, e in g:
        if s < 0.05 or e > dur - 0.05:
            continue
        hit = next((t for t in joins if s - 0.05 < t < e + 0.05), None)
        (jg if hit is not None else ng).append((s, e, e - s, hit))

    print(f"niveau de parole {speech:.1f} dB · seuil {thr:.1f} dB · durée {dur:.2f}s")
    print(f"\nBLANCS AUX RACCORDS ({len(jg)}/{len(joins)})")
    for s, e, d, t in jg:
        print(f"  raccord @{t:6.2f}s   {d*1000:5.0f} ms")
    if ng:
        nd = sorted(x[2] for x in ng)
        print(f"\nBLANCS NATURELS ({len(ng)}) : median {np.median(nd)*1000:.0f} ms"
              f" · p25 {np.percentile(nd,25)*1000:.0f} · p75 {np.percentile(nd,75)*1000:.0f}")
    if jg:
        jd = sorted(x[2] for x in jg)
        print(f"RACCORDS : median {np.median(jd)*1000:.0f} ms"
              f" · min {jd[0]*1000:.0f} · max {jd[-1]*1000:.0f}")
        if ng:
            print(f"\n=> ecart raccord/naturel : x{np.median(jd)/np.median(nd):.2f}"
                  f"   (x1.0 = indetectable)")
            miss = [t for t in joins if not any(x[3] == t for x in jg)]
            if miss:
                print(f"   {len(miss)} raccord(s) sans blanc detectable : {miss}")

if __name__ == '__main__':
    main()
