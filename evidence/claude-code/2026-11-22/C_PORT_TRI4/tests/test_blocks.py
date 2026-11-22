"""Kernel check on grids whose cell count is not a multiple of the block (128) or of the vector width (4), so that
the scalar tail loops and short blocks are exercised: every integrand call form used by tri4.enclose is evaluated
by the C kernel and by the original Python function (same process, _tape.enabled switched) and every output array
is compared bit for bit.  Usage: test_blocks.py out.json      (C-port tree on PYTHONPATH)"""
import json, sys
from fractions import Fraction as F
import numpy as np
from geoenclosereader import tri3, tri4, _tape
from geoenclosereader.fiv import I, iv_frac
from geoenclosereader.dual import D
from geoenclosereader.jet import J

box = [(F(3, 2), F(25, 16)), (F(2), F(33, 16)), (F(1, 8), F(5, 32)), (F(1, 4), F(9, 32)), (F(1, 4), F(9, 32))]
p0 = [(a + b)/2 for a, b in box]; cen = [iv_frac(x) for x in p0]; full = [iv_frac(a, b) for a, b in box]
G0 = tri4._grid(16, 0, box)


def leaves(x):
    if isinstance(x, J): return [x.v] + [g for g in x.g if g is not None] + [h for h in x.h.values() if h is not None]
    if isinstance(x, D): return [x.v] + list(x.g)
    return [x]


def calls(f, G, shp, act, jets):
    z = I(np.zeros(shp)); one = I(np.ones(shp)); n = len(act); out = []
    out.append(f(G["s1"], G["c1"], G["s2"], G["c2"], *cen))
    sa = D(G["S1"], [G["C1"], z]); ca = D(G["C1"], [-G["S1"], z]); sb = D(G["S2"], [z, G["C2"]]); cb = D(G["C2"], [z, -G["S2"]])
    out.append(f(sa, ca, sb, cb, *[D.const(x, 2) for x in cen]))
    pars = [D(I(np.full(shp, full[j].lo), np.full(shp, full[j].hi)), [one if j == act[i] else z for i in range(n)]) if j in act
            else D.const(I(np.full(shp, full[j].lo), np.full(shp, full[j].hi)), n) for j in range(5)]
    out.append(f(D.const(G["S1"], n), D.const(G["C1"], n), D.const(G["S2"], n), D.const(G["C2"], n), *pars))
    if not jets: return [l for o in out for l in leaves(o)]      # the masked tri3 kernel is only called with I and D
    pd = [D(cen[j], [one if j == act[i] else z for i in range(n)]) if j in act else D.const(cen[j], n) for j in range(5)]
    out.append(f(*[D.const(G[k], n) for k in ("s1", "c1", "s2", "c2")], *pd))
    nv = 2 + n; prs = [(a, 2 + i) for a in (0, 1) for i in range(n)]
    Ja = lambda val, slot, dv: J(val, [dv if q == slot else None for q in range(nv)], {p: None for p in prs}, prs)
    jp = [J.var(cen[j], 2 + act.index(j), nv, prs, one) if j in act else J.const(cen[j], nv, prs) for j in range(5)]
    out.append(f(Ja(G["S1"], 0, G["C1"]), Ja(G["C1"], 0, -G["S1"]), Ja(G["S2"], 1, G["C2"]), Ja(G["C2"], 1, -G["S2"]), *jp))
    prC = [(i, k) for i in range(n) for k in range(i, n)]
    jq = [J.var(I(np.full(shp, full[j].lo), np.full(shp, full[j].hi)), act.index(j), n, prC, one) if j in act
          else J.const(I(np.full(shp, full[j].lo), np.full(shp, full[j].hi)), n, prC) for j in range(5)]
    out.append(f(*[J.const(G[k], n, prC) for k in ("S1", "C1", "S2", "C2")], *jq))
    return [l for o in out for l in leaves(o)]


res = []; nbad = 0
for shape in ((1, 1), (1, 3), (3, 5), (5, 7), (9, 15), (11, 13), (16, 31), (16, 32)):
    a, b = shape; cut = lambda x: I(np.ascontiguousarray(x.lo[:a, :b]).copy(), np.ascontiguousarray(x.hi[:a, :b]).copy())
    G = {k: cut(G0[k]) for k in ("S1", "C1", "S2", "C2", "s1", "c1", "s2", "c2")}
    for kind in ("E3", "T12", "H33"):
        for maker, mk, jets in (("tri4", lambda: tri4._make(kind), True), ("tri3+mask", lambda: tri3._make(kind, safe_mask=np.arange(a*b).reshape(shape) % 3 != 1), False)):
            for act in ([0, 1, 2, 3, 4], [1, 4]):
                _tape.enabled = True; c0 = _tape.stats["tape_calls"]; X = calls(mk(), G, shape, act, jets); used = _tape.stats["tape_calls"] - c0
                _tape.enabled = False; Y = calls(mk(), G, shape, act, jets); _tape.enabled = True
                same = len(X) == len(Y) and all(x.lo.shape == y.lo.shape and x.lo.tobytes() == y.lo.tobytes() and x.hi.tobytes() == y.hi.tobytes() for x, y in zip(X, Y))
                nbad += not same
                res.append(dict(shape=shape, cells=a*b, kind=kind, maker=maker, act=act, arrays=len(X), kernel_calls=used, identical=bool(same)))
json.dump(dict(simd=_tape._lib.tape_simd(), checks=len(res), not_identical=nbad, fallbacks=_tape.stats["fallback_calls"], fallback_reasons=_tape.stats["unsupported"], rows=res), open(sys.argv[1], "w"), indent=1)
print("simd", _tape._lib.tape_simd(), "checks", len(res), "not identical", nbad, "fallbacks", _tape.stats["fallback_calls"], "arrays", sum(r["arrays"] for r in res))
