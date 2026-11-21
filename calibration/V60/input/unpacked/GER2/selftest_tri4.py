"""selftest for jet.py and tri4.py (GeoEncloseReader 0.5.0). Reference: v57/chat_v57_numeric_lib.general (Gauss, n=600).
1. jets: value/gradient/Hessian of a test function against mpmath derivatives (must lie inside the intervals).
2. point boxes: enclosure contains the reference value.
3. small boxes: reference values at 6 seeded random points of box ∩ ball lie inside the box enclosure.
Run from this folder: python3 selftest_tri4.py"""
import sys, time, random; sys.path.insert(0, '.'); sys.path.insert(0, '../v57')
import numpy as np
from fractions import Fraction as Fr
from mpmath import mp, mpf, diff, sqrt as msqrt
from geoenclosereader.fiv import I, iv_frac
from geoenclosereader.jet import J
from geoenclosereader import tri4
import chat_v57_numeric_lib as num
bad = 0
def ok(name, cond, msg=""):
    global bad; bad += not cond; print(("OK  " if cond else "BAD ") + name + " " + msg, flush=True)

# 1. jets: f(x, y, z) = sqrt(x^2 + 3 y) / (x + y z) at (0.7, 1.3, 0.4), all pairs
mp.dps = 30
pt = [Fr(7, 10), Fr(13, 10), Fr(2, 5)]; n = 3; prs = [(i, k) for i in range(3) for k in range(i, 3)]
X = [J.var(iv_frac(pt[i]), i, n, prs, I(1.0)) for i in range(3)]
F = (X[0].sq() + 3*X[1]).sqrt()/(X[0] + X[1]*X[2])
fm = lambda x, y, z: msqrt(x**2 + 3*y)/(x + y*z)
P = [mpf(p.numerator)/p.denominator for p in pt]
inside = lambda iv, v: float(iv.lo) <= float(v) <= float(iv.hi)
ok("jet value", inside(F.v, fm(*P)))
for i in range(3):
    o = [0]*3; o[i] = 1; ok(f"jet grad {i}", inside(F.g[i], diff(fm, P, tuple(o))))
for (i, k) in prs:
    o = [0]*3; o[i] += 1; o[k] += 1; ok(f"jet hess {i}{k}", inside(F.h[(i, k)], diff(fm, P, tuple(o))))
mp.dps = 40

def box_of(p, r):
    return [(Fr(x) - r, Fr(x) + r) if r else (Fr(x), Fr(x)) for x in p]

# 2. point boxes
for (s, t, q, kinds, N) in ((1.2, 1.5, (0.25, 0.25, 0.5), ("E3", "T12", "H33"), 64),
                            (2.5, 4, (0.25, 0.0, 0.5), ("E3", "H33"), 64),
                            (1.5, 2, (0.5, 0.5, 0.0), ("T12", "H33"), 64)):
    for kind in kinds:
        b = [(Fr(s), Fr(s)), (Fr(t), Fr(t))] + [(Fr(x), Fr(x)) for x in q]
        e = tri4.enclose(kind, b, N); ref = num.general(kind, s, t, q, 600)
        ok(f"point {kind} s={s} t={t} q={q}", float(e.lo) <= ref <= float(e.hi), f"[{float(e.lo):.8g}, {float(e.hi):.8g}] ref {ref:.8g}")

# 3. small boxes, seeded points
rng = random.Random(20261121)
cases = [  # (centre, half-width, kinds, N, grade, label)
    ((Fr(6, 5), Fr(3, 2), Fr(1, 4), Fr(1, 4), Fr(1, 2)), Fr(1, 128), ("E3", "T12", "H33"), 64, 0, "interior"),
    ((Fr(5, 2), Fr(4), Fr(1, 4), Fr(1, 8), Fr(1, 2)), Fr(1, 256), ("E3", "H33"), 128, 2, "elongated"),
    ((Fr(117, 40), Fr(91, 16), Fr(1, 64), Fr(47, 64), Fr(1, 64)), Fr(1, 512), ("H33",), 256, 4, "D1/8-like equator"),
    ((Fr(3, 2), Fr(2), Fr(1, 2), Fr(1, 2), Fr(1, 64)), Fr(1, 128), ("T12",), 64, 0, "layer II"),
    ((Fr(6, 5), Fr(3, 2), Fr(19, 32), Fr(19, 32), Fr(9, 16)), Fr(1, 64), ("E3",), 64, 0, "rim, centre outside ball"),
]
for (c, r, kinds, N, grade, label) in cases:
    b = box_of(c, r)
    for kind in kinds:
        t0 = time.time(); e = tri4.enclose(kind, b, N, grade); L = tri4.enclose.last
        pts = []
        while len(pts) < 6:
            p = [float(lo) + (float(hi) - float(lo))*rng.random() for lo, hi in b]
            if p[2]**2 + p[3]**2 + p[4]**2 <= 0.995: pts.append(p)
        refs = [num.general(kind, p[0], p[1], p[2:], 600) for p in pts]
        good = all(float(e.lo) <= v <= float(e.hi) for v in refs)
        ok(f"box {label} {kind} N={N}", good, f"[{float(e.lo):.6g}, {float(e.hi):.6g}] refs [{min(refs):.6g}, {max(refs):.6g}] "
           f"order {L['order']} used {L['used']} contact {L['contact_cells']} p0 {L['p0'][2:]} {time.time()-t0:.1f}s")
print("FAILURES", bad)
