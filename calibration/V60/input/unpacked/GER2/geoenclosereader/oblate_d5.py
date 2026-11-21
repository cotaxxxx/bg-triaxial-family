"""Adapter for the oblate D5 transverse cover (D-OB, Judge V18): boxes in (d = 1 - r, tau, lambda).

Meridian map (V17 §2):  a = (1 - tau^2)/(1 + tau^2),  b = 2 tau/(1 + tau^2),  reference point q = (r a, 0, r b)
(physical p = (r a, 0, r lambda b) in K_lambda = {x^2 + y^2 + z^2/lambda^2 <= 1}); |q| = r.
On [0, 1], a decreases and b increases in tau, so a polar box maps into the (rho, z) hull
  rho in [r0 a(tau1), r1 a(tau0)],  z in [r0 b(tau0), r1 b(tau1)].
Claim checked: H = E_rho/rho = E_yy > 0 (chord (3), i = y), on hull ∩ ball ⊇ the polar box.
"""
import gzip, json, random, time
from fractions import Fraction as Fr
from flint import fmpq
from . import kernels as K


def _q(x): x = Fr(x); return fmpq(x.numerator, x.denominator)
def a_(t): return (1 - t*t)/(1 + t*t)
def b_(t): return 2*t/(1 + t*t)


def hull(pb):
    r0, r1, t0, t1, l0, l1 = pb
    return (_q(l0), _q(l1), _q(r0*a_(t1)), _q(r1*a_(t0)), _q(r0*b_(t0)), _q(r1*b_(t1)))


def polar_from_record(box):
    d0, d1 = Fr(box["d"][0]), Fr(box["d"][1])
    return (1 - d1, 1 - d0, Fr(box["tau"][0]), Fr(box["tau"][1]), Fr(box["lam"][0]), Fr(box["lam"][1]))


def final_leaves(path):
    """Final (not superseded) records of a V4 / Plan B output JSONL (gz or plain): highest level per name and
    no d-children name_h0/name_h1 (the cover rule of chat_v4_run / chat_planb_run)."""
    op = gzip.open if path.endswith(".gz") else open; recs = {}
    with op(path, "rt") as f:
        for ln in f:
            r = json.loads(ln); recs[(r["box"]["name"], int(r["box"].get("level", 0)))] = r
    lev = {}
    for (n, l) in recs: lev[n] = max(lev.get(n, -1), l)
    return [r for (n, l), r in recs.items() if l == lev[n] and (n + "_h0") not in lev and (n + "_h1") not in lev]


def bisect_polar(pb):
    r0, r1, t0, t1, l0, l1 = pb
    sc = [l1 - l0, 4*(r1 - r0), 4*r1*(t1 - t0)]; i = sc.index(max(sc)); c = list(pb); e = list(pb)
    lo, hi = {0: (4, 5), 1: (0, 1), 2: (2, 3)}[i]; m = (pb[lo] + pb[hi])/2; c[hi] = m; e[lo] = m
    return [tuple(c), tuple(e)]


def verify_polar(name, pb, ladder=("v50", "fine"), depth=6):
    t0 = time.monotonic(); tried = []
    for grid in ladder:
        todo = [(pb, 0)]; vals = []; ok = True; ev = 0
        while todo:
            b, d = todo.pop(); v = K.chord_bound(hull(b), 'y', 'lower', grid); ev += 1
            if v > 0: vals.append(float(v))
            elif d < depth: todo += [(c, d + 1) for c in bisect_polar(b)]
            else: ok = False; vals.append(float(v)); break
        tried.append({"grid": grid, "confirmed": ok, "evals": ev, "min": min(vals) if vals else None})
        if ok: break
    return {"leaf": name, "quantity": "H=E_yy", "polar_box": [str(x) for x in pb], "confirmed": tried[-1]["confirmed"],
            "grid_used": tried[-1]["grid"], "attempts": tried, "seconds": round(time.monotonic() - t0, 1)}
