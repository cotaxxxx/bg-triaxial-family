"""UNCERTIFIED NUMERICS (double precision, no error bounds) -- optional layer of the Paper II viewer.

For a grid of shapes (y, z) in R = [1/4, 1] x [1, 7] this script locates, on the short axis (y) and on the middle
axis (x), the zero of the first derivative of the energy along the axis, if there is one strictly inside.
It uses the author-independent quadrature code of the first triaxial map (Claude Code, 2026-11-20):
  repository cotaxxxx/basepoint-geometry, branch ccr-1e5ce365-5ksfyr, commit f3170e6,
  diagnostics/triaxial_map_20261120/code/{triax.py, libtriax.so built from triax_kernel.c}
The energy is evaluated in the reference ball; with semi-axes proportional to (1/y, 1, z) -> (1, 1/y, z/y),
axis 1 of that code is the short axis (paper: y) and axis 2 the middle axis (paper: x).
kappa_i(r) = E_i(r e_i)/r (kappa_i(0) = E_ii(0)) is sampled at NR points of [0, RMAX] and a sign change is located
by linear interpolation.  Nothing here is part of any proof.

Usage: python3 uncertified_axis_table.py TRIAX_CODE_DIR OUT.json"""
import json, sys
sys.path.insert(0, sys.argv[1])
import numpy as np
import triax

NY, NZ, NR, RMAX = 46, 61, 96, 0.9995
ys = [0.25 + i/60 for i in range(NY)]; zs = [1 + j/10 for j in range(NZ)]
r = np.linspace(0, RMAX, NR)


def root(k):
    s = np.sign(k); ch = np.nonzero(s[:-1]*s[1:] < 0)[0]
    if len(ch) == 0: return None, 0
    i = ch[0]; return float(r[i] - k[i]*(r[i+1] - r[i])/(k[i+1] - k[i])), len(ch)


ry = [[None]*NZ for _ in range(NY)]; rx = [[None]*NZ for _ in range(NY)]; multi = 0; sg = {}
for a, y in enumerate(ys):
    for b, z in enumerate(zs):
        l = np.array([1.0, 1/y, z/y])
        for ax, tab in ((0, ry), (1, rx)):
            q = np.zeros((NR, 3)); q[:, ax] = r; o = triax.ev(l, q)
            k = np.where(r > 0, o[:, 1 + ax]/np.where(r > 0, r, 1), o[:, 4 + ax])
            v, n = root(k); multi += n > 1
            tab[a][b] = None if v is None else round(v, 4)
    print(a, flush=True)
json.dump(dict(note="UNCERTIFIED NUMERICS: double precision, no error bounds, not part of any proof", ys=[round(v, 6) for v in ys], zs=[round(v, 6) for v in zs],
               r_max=RMAX, n_r=NR, nodes=[96, 96], sign_changes_more_than_one=multi, ry=ry, rx=rx,
               source="cotaxxxx/basepoint-geometry@f3170e6 diagnostics/triaxial_map_20261120/code"), open(sys.argv[2], "w"), separators=(",", ":"))
