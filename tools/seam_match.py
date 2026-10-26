"""Estimateur de deplacement robuste : recherche exhaustive par correlation normalisee.

La correlation de phase se trompe de pic quand le contenu change beaucoup entre deux
prises. Ici on balaie tous les decalages entiers d'une plage donnee et on garde le
meilleur au sens de la correlation croisee normalisee, puis on raffine au sous-pixel.
"""
import numpy as np

def ncc_shift(A, B, rng=16):
    """deplacement (dx,dy) du contenu de B par rapport a A, en px d'analyse"""
    m = rng
    Ac = A[m:-m, m:-m]
    Ac = Ac - Ac.mean()
    na = np.sqrt((Ac**2).sum()) + 1e-12
    best, score = (0, 0), -2.0
    grid = np.full((2*m+1, 2*m+1), -2.0)
    for dy in range(-m, m+1):
        for dx in range(-m, m+1):
            Bc = B[m+dy:B.shape[0]-m+dy, m+dx:B.shape[1]-m+dx]
            Bc = Bc - Bc.mean()
            s = float((Ac*Bc).sum()/(na*(np.sqrt((Bc**2).sum())+1e-12)))
            grid[dy+m, dx+m] = s
            if s > score: score, best = s, (dx, dy)
    dx, dy = best
    # raffinement sous-pixel par parabole sur chaque axe
    def refine(v, c):
        i = c + m
        if 0 < i < 2*m:
            lo, mi, hi = v[i-1], v[i], v[i+1]
            den = lo - 2*mi + hi
            if abs(den) > 1e-9:
                return c + 0.5*(lo-hi)/den
        return float(c)
    fdx = refine(grid[dy+m, :], dx)
    fdy = refine(grid[:, dx+m], dy)
    return np.array([fdx, fdy]), score
