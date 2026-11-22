"""Probe (outside the fixed plans): how much of the grid time is spent on parts that do not depend on the box?
The phi direction of the sphere grid (2N uniform cells, weight 1) depends only on N.  This script memoises the two
pure helpers tri2._cell_moments (uniform case only) and tri2._trig_cells from OUTSIDE the Reader, builds graded grids
for several th0 with and without the memo, and compares every grid array bit for bit.
Usage: grid_memo_probe.py N out.json      (pure-Python Reader on PYTHONPATH)"""
import json, sys, time, hashlib
from fractions import Fraction as F
import numpy as np
from geoenclosereader import tri2, tri4

N = int(sys.argv[1]); grade = 4
boxes = [[(F(53, 20), F(16, 5)), (F(43, 8), F(6)), (F(27, 32), F(7, 8)), (F(7, 32), F(1, 4)), (F(a), F(b))]
         for a, b in ((F(0), F(1, 32)), (F(1, 64), F(1, 32)), (F(1, 32), F(1, 16)), (F(3, 16), F(1, 4)))]


def digest(G):
    h = hashlib.sha256()
    for k in ("C1", "S1", "C2", "S2", "c1", "s1", "c2", "s2", "m0"): h.update(G[k].lo.tobytes()); h.update(G[k].hi.tobytes())
    for k in ("m1", "M1"):
        for x in G[k]: h.update(x.lo.tobytes()); h.update(x.hi.tobytes())
    return h.hexdigest()


def run():
    out = []
    for b in boxes:
        tri2._grid.clear(); t0 = time.perf_counter(); G = tri4._grid(N, grade, b); out.append((time.perf_counter() - t0, digest(G)))
    return out


plain = run()
cm0, tc0 = tri2._cell_moments, tri2._trig_cells; memo_cm, memo_tc = {}, {}


def cm(N, lo, hi, wkind, ends=None):
    if ends is not None: return cm0(N, lo, hi, wkind, ends)
    k = (N, repr(lo), repr(hi), wkind)
    if k not in memo_cm: memo_cm[k] = cm0(N, lo, hi, wkind)
    return memo_cm[k]


def tc(e, c):
    k = (id(e), id(c))                         # only lists kept alive by memo_cm can repeat
    if not any(e is v[0] and c is v[1] for v in memo_cm.values()): return tc0(e, c)
    if k not in memo_tc: memo_tc[k] = tc0(e, c)
    r = memo_tc[k]; return tuple(type(x)(x.lo.copy(), x.hi.copy()) for x in r)


tri2._cell_moments, tri2._trig_cells = cm, tc
memo = run()
res = dict(N=N, grade=grade, plain_s=[round(t, 2) for t, _ in plain], memo_s=[round(t, 2) for t, _ in memo],
           identical=[a[1] == b[1] for a, b in zip(plain, memo)], digests=[a[1] for a in plain])
json.dump(res, open(sys.argv[2], "w"), indent=1); print(res)
