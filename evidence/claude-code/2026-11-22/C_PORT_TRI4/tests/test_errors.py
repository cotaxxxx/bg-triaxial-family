"""Extra check, outside the fixed plan: whole-array error conditions.  The interior kernel is called with the point q
ON the sphere (so D2 reaches 0 on some cells: sqrt of a negative number), and with s = [-1, 1] or t = [-1, 1]
(division by an interval containing 0),
once through the C kernel and once through the original Python function; exception type and text are compared,
or all output arrays bit for bit if no exception is raised.  Usage: test_errors.py out.json   (C-port tree on PYTHONPATH)"""
import json, sys
from fractions import Fraction as F
import numpy as np
from geoenclosereader import tri4, _tape
from geoenclosereader.fiv import I, iv_frac
from geoenclosereader.dual import D

G = tri4._grid(16, 0, None); shp = G["C1"].lo.shape; z = I(np.zeros(shp)); rows = []


def run(f, form, pt):
    cen = [x if isinstance(x, I) else iv_frac(x) for x in pt]
    if form == "I": r = f(G["s1"], G["c1"], G["s2"], G["c2"], *cen); return [r]
    if form == "I-cells": r = f(G["S1"], G["C1"], G["S2"], G["C2"], *cen); return [r]
    sa = D(G["S1"], [G["C1"], z]); ca = D(G["C1"], [-G["S1"], z]); sb = D(G["S2"], [z, G["C2"]]); cb = D(G["C2"], [z, -G["S2"]])
    r = f(sa, ca, sb, cb, *[D.const(x, 2) for x in cen]); return [r.v] + list(r.g)


for kind in ("E3", "T12", "H33"):
    for q in ((F(0), F(0), F(1)), (F(1), F(0), F(0)), (F(3, 5), F(4, 5), F(0)), (F(0), F(0), F(-1)), (F(1, 4), F(1, 4), F(1, 2))):
        for form, st in [(fm, (F(3, 2), F(2))) for fm in ("I", "I-cells", "D")] + ([("I", (iv_frac(-1, 1), F(2))), ("D", (F(3, 2), iv_frac(-1, 1)))] if q[2] == F(1, 2) else []):
            res = []
            for mode in (True, False):
                _tape.enabled = mode; c0 = _tape.stats["tape_calls"]
                try: X = run(tri4._make(kind), form, st + q); res.append(("ok", [x.lo.tobytes() + x.hi.tobytes() for x in X], _tape.stats["tape_calls"] - c0))
                except Exception as e: res.append((type(e).__name__ + ": " + str(e), None, _tape.stats["tape_calls"] - c0))
            _tape.enabled = True
            rows.append(dict(kind=kind, q=[str(x) for x in q], form=form, zero_in_st=any(isinstance(x, I) for x in st), c=res[0][0], python=res[1][0], kernel_calls=res[0][2], identical=res[0][:2] == res[1][:2]))
bad = sum(not r["identical"] for r in rows); import collections
json.dump(dict(simd=_tape._lib.tape_simd(), checks=len(rows), not_identical=bad, outcomes=dict(collections.Counter(r["python"] for r in rows)), fallbacks=_tape.stats["fallback_calls"], rows=rows), open(sys.argv[1], "w"), indent=1)
print("simd", _tape._lib.tape_simd(), "checks", len(rows), "not identical", bad, dict(collections.Counter(r["python"] for r in rows)), "fallbacks", _tape.stats["fallback_calls"])
