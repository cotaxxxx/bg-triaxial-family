"""General-point triaxial enclosures, second order in the parameters (GeoEncloseReader 0.5.0, V60, chat).
Same integrands and chart as tri3 (0.4.0): E3, T12, H33 on the full sphere, weight sin th / (4 pi), p = (s, t, q1, q2, q3).

Second-order path (no contact cell on the fine grid, D^2 > 0 on every coarse cell x box):
  p0 = expansion point in box ∩ ball (the box centre when it lies in the closed ball, see _p0), delta = p - p0.
  Taylor with integral remainder along the segment p0 -> p (it stays in box ∩ ball: both are convex):
      E(p) = E(p0) + sum_j dE_j(p0) delta_j + int_0^1 (1 - u) delta^T Hess E(p0 + u delta) delta du
  (A)  E(p0):      angular mean value on the fine grid (as tri3 (i)), at the point p0.
  (B)  dE_j(p0):   angular mean value of d_j f on the fine grid:
                   sum_cells [ d_j f(x_c, p0) m0 + mid(d_a d_j f) m1_a +/- rad(d_a d_j f) M1_a ]  (jets, a = th, ph).
  (C)  Hess E(xi) for every xi in the box: sum_cells range(d_j d_k f over coarse cell x box) m0  (jets in p).
  E(box ∩ ball) ⊂ A + sum_j B_j delta_j + sum_j (1/2) C_jj [0, max delta_j^2] + sum_{j<k} C_jk delta_j delta_k.
  Differentiation under the integral is valid because the integrand is C^2 in (xi, p) where D > 0, and g stays in [0, 1]
  on the ball, so the clip to [0, 1] never changes a true value or derivative there.
First-order path (contact cells present, or a coarse cell meets D = 0): tri3's form with two corrections (0.5.0):
  the expansion point is p0 in the ball (0.4.0 used the box centre even when it lay outside the ball: erratum E3),
  and the parameter gradient is summed over the cells before multiplying by delta (valid; slightly tighter, V59-B D3).
"""
import numpy as np
from fractions import Fraction
from mpmath import pi as mpi
from .fiv import I, iv_frac
from .dual import D
from .jet import J
from .tri import PQF
from .tri2 import _grid2, _PQ_d
from . import tri3
from .tri3 import _common, _fallback, _graded, _th0


def _PQ_any(g):
    if isinstance(g, J):
        o = PQF(g.v, ("Pgg", "Pggg", "Q", "F")); P, Pg, Pgg, Pggg, Q, F = o["P"], o["Pg"], o["Pgg"], o["Pggg"], o["Q"], o["F"]
        return (g.chain(P, Pg, Pgg), g.chain(Q, 3*Pg + g.v*Pgg, 4*Pgg + g.v*Pggg), g.chain(F, -P, -Pg))
    return _PQ_d(g)


def _make(kind):
    """the tri3 integrands, written once for I, D and J arguments (no contact masking: callers exclude contact)."""
    def f(s1, c1, s2, c2, s, t, q1, q2, q3):
        xi, L, v, k, Lv, D2, S = _common(s1, c1, s2, c2, s, t, q1, q2, q3)
        Dn = D2.sqrt(); g = (k/(Dn*S)).clip(0.0, 1.0); P, Q, F = _PQ_any(g); u = [x/Dn for x in Lv]
        if kind == "E3":
            return xi[2]*(g*P - F) - L[2]*S*u[2]*g.sq()*P
        if kind == "T12":
            n1 = xi[0]/S; n2 = (xi[1]/s)/S
            return k*g*P*(u[0]*u[1] - n1*n2)
        if kind == "H33":
            b3 = L[2]*u[2]; z3 = xi[2] - g*S*b3
            return (P*(g*S).sq()*(L[2].sq() - b3.sq()) - Q*z3.sq())/(Dn*S)
    return f


def _in_ball(p): return p[2]**2 + p[3]**2 + p[4]**2 <= 1


def _p0(box):
    """expansion point: the centre if it is in the closed ball; otherwise the centre pulled toward the box point nearest
    the origin (z) by halving, z + (c - z)/2^k, k = 1..30; z itself as the last resort. Exact rationals."""
    c = [(a + b)/2 for a, b in box]
    if _in_ball(c): return c
    z = [a if j < 2 else (a if a > 0 else (b if b < 0 else Fraction(0))) for j, (a, b) in enumerate(box)]
    z[0], z[1] = c[0], c[1]
    if not _in_ball(z): raise ValueError("box does not meet the ball")
    for kk in range(1, 31):
        p = [zz + (cc - zz)/2**kk for zz, cc in zip(z, c)]
        if _in_ball(p): return p
    return z


def _grid(N, grade, box):
    th0 = _th0(box) if grade else None
    return _grid2(("sph", N, grade, None if th0 is None else float(th0)), N, 0, mpi, "sin", 2*N, 0, 2*mpi, "one", 1/(4*mpi),
                  ends1=_graded(N, grade, th0))


def _mv_cells(vc, gd, G):
    """per-cell angular mean value: vc m0 + mid(gd) . m1 +/- rad(gd) . M1"""
    cell = vc*G["m0"]
    for kk in range(2):
        gk = gd[kk]; gm = (gk.lo + gk.hi)*0.5; gr = np.maximum(gk.hi - gm, gm - gk.lo)
        cell = cell + I(gm)*G["m1"][kk] + I(-1.0, 1.0)*I(np.nextafter(gr, np.inf))*G["M1"][kk]
    return cell


def enclose(kind, box, N=32, grade=0, NH=None):
    """box: 5 pairs of Fractions (s, t, q1, q2, q3). Encloses the sphere mean of `kind` over box ∩ ball."""
    NH = NH if NH is not None else max(16, N//2)
    G = _grid(N, grade, box); shp = G["C1"].lo.shape
    lo = [Fraction(a) for a, b in box]; hi = [Fraction(b) for a, b in box]
    p0 = _p0(list(zip(lo, hi)))
    full = [iv_frac(a, b) for a, b in zip(lo, hi)]
    dl = [iv_frac(a - c, b - c) for a, b, c in zip(lo, hi, p0)]           # delta_j ranges (contain 0)
    mx = [max(abs(a - c), abs(b - c)) for a, b, c in zip(lo, hi, p0)]
    act = [j for j in range(5) if hi[j] != lo[j]]
    _, _, _, _, _, D2box, _ = _common(G["S1"], G["C1"], G["S2"], G["C2"], *full)
    thr = (4.0/N)**2; safe = D2box.lo > thr; ncontact = int((~safe).sum())
    f = _make(kind); m0 = G["m0"]; z = I(np.zeros(shp))
    cen = [iv_frac(x) for x in p0]
    order = 2
    if ncontact == 0 and act:
        GH = _grid(NH, grade, box)
        _, _, _, _, _, D2H, _ = _common(GH["S1"], GH["C1"], GH["S2"], GH["C2"], *full)
        if not np.all(D2H.lo > 0): order = 1
    else:
        order = 1
    # (A) value at p0 (fine grid, angular mean value); contact cells are replaced below (first-order path only)
    if ncontact:
        fA = tri3._make(kind, safe_mask=safe)
    else:
        fA = f
    vc = fA(G["s1"], G["c1"], G["s2"], G["c2"], *cen)
    sa = D(G["S1"], [G["C1"], z]); ca = D(G["C1"], [-G["S1"], z]); sb = D(G["S2"], [z, G["C2"]]); cb = D(G["C2"], [z, -G["S2"]])
    fd = fA(sa, ca, sb, cb, *[D.const(x, 2) for x in cen])
    cellA = _mv_cells(vc, fd.g, G)
    A = (I.where(safe, cellA, z) if ncontact else cellA).fsum()
    angular_width = float(A.hi - A.lo); info = {}
    out1, terms1, out2, terms2, aw2 = A, {}, None, {}, angular_width
    if act and order == 2:
        n = len(act)
        # (B1) d_j f at cell centres, p = p0
        one = I(np.ones(shp))
        pd = [D(cen[j], [one if j == act[i] else z for i in range(n)]) if j in act else D.const(cen[j], n) for j in range(5)]
        fB1 = f(*[D.const(G[k], n) for k in ("s1", "c1", "s2", "c2")], *pd)
        # (B2) d_a d_j f over the fine cells at p0 (jets: slots 0, 1 = angles, 2 + i = act[i])
        nv = 2 + n; prs = [(a, 2 + i) for a in (0, 1) for i in range(n)]
        Ja = lambda val, slot, dv: J(val, [dv if q == slot else None for q in range(nv)], {p: None for p in prs}, prs)
        js1 = Ja(G["S1"], 0, G["C1"]); jc1 = Ja(G["C1"], 0, -G["S1"]); js2 = Ja(G["S2"], 1, G["C2"]); jc2 = Ja(G["C2"], 1, -G["S2"])
        jp = [J.var(cen[j], 2 + act.index(j), nv, prs, one) if j in act else J.const(cen[j], nv, prs) for j in range(5)]
        fB2 = f(js1, jc1, js2, jc2, *jp)
        Bj = {}
        for i, j in enumerate(act):
            gd = [fB2.h[(0, 2 + i)], fB2.h[(1, 2 + i)]]
            gd = [z if x is None else x for x in gd]
            Bj[j] = _mv_cells(fB1.g[i], gd, G).fsum()
        # (C) Hessian over coarse cells x box
        shH = GH["C1"].lo.shape; oneH = I(np.ones(shH))
        prC = [(i, k) for i in range(n) for k in range(i, n)]
        jq = [J.var(I(np.full(shH, full[j].lo), np.full(shH, full[j].hi)), act.index(j), n, prC, oneH) if j in act
              else J.const(I(np.full(shH, full[j].lo), np.full(shH, full[j].hi)), n, prC) for j in range(5)]
        fC = f(*[J.const(GH[k], n, prC) for k in ("S1", "C1", "S2", "C2")], *jq)
        C = {}
        for pr in prC:
            hv = fC.h[pr]; C[pr] = I(0.0, 0.0) if hv is None else (hv*GH["m0"]).fsum()
        # assemble
        for i, j in enumerate(act):
            tB = Bj[j]*dl[j]; out2 = tB if out2 is None else out2 + tB
            mid = abs(float(Bj[j].lo + Bj[j].hi))*0.5
            aw2 += float(Bj[j].hi - Bj[j].lo)*float(mx[j])
            terms2[j] = terms2.get(j, 0.0) + 2*mid*float(mx[j])
        for (i, k) in prC:
            j1, j2 = act[i], act[k]
            if i == k: tC = C[(i, k)]*iv_frac(0, mx[j1]**2)*0.5
            else: tC = C[(i, k)]*(dl[j1]*dl[j2])
            out2 = out2 + tC; w = float(tC.hi - tC.lo)
            terms2[j1] = terms2.get(j1, 0.0) + (w if i == k else 0.5*w)
            if i != k: terms2[j2] = terms2.get(j2, 0.0) + 0.5*w
        info = dict(B={j: (float(Bj[j].lo), float(Bj[j].hi)) for j in act}, C={str((act[i], act[k])): (float(C[(i, k)].lo), float(C[(i, k)].hi)) for (i, k) in prC})
        out2 = A + out2
    if act:
        n = len(act); one = I(np.ones(shp))
        if ncontact:
            fp_f = tri3._make(kind, safe_mask=safe)
        else:
            fp_f = f
        pars = [D(I(np.full(shp, full[j].lo), np.full(shp, full[j].hi)), [one if j == act[i] else z for i in range(n)]) if j in act
                else D.const(I(np.full(shp, full[j].lo), np.full(shp, full[j].hi)), n) for j in range(5)]
        fp = fp_f(D.const(G["S1"], n), D.const(G["C1"], n), D.const(G["S2"], n), D.const(G["C2"], n), *pars)
        for i, j in enumerate(act):
            gsum = (I.where(safe, fp.g[i]*m0, z) if ncontact else fp.g[i]*m0).fsum()
            tw = gsum*dl[j]; out1 = out1 + tw; terms1[j] = float(tw.hi - tw.lo)
    if ncontact:
        fb = (_fallback(kind, full[0], full[1], shp)*m0)
        out1 = out1 + I.where(safe, z, fb).fsum()
    # both are valid enclosures of the same mean: keep the intersection (an empty one would be an INCONSISTENT kernel)
    if out2 is None:
        out, terms, used = out1, terms1, 1
    else:
        lo_, hi_ = np.maximum(out1.lo, out2.lo), np.minimum(out1.hi, out2.hi)
        if lo_ > hi_: raise ValueError("INCONSISTENT: first- and second-order enclosures do not meet")
        out = I(lo_, hi_)
        w1, w2 = float(out1.hi - out1.lo), float(out2.hi - out2.lo)
        if w2 <= w1: terms, used, angular_width = terms2, 2, aw2
        else: terms, used = terms1, 1
        info["width1"], info["width2"] = w1, w2
    enclose.last = {"order": order, "used": used, "contact_cells": ncontact, "terms": terms, "angular_width": angular_width,
                    "total_width": float(out.hi - out.lo), "p0": [str(x) for x in p0], **info}
    return out


def W3(box, N=32, grade=0, NH=None):
    q3 = box[4]; return enclose("E3", box, N, grade, NH)/iv_frac(q3[0], q3[1])


def C12(box, N=32, grade=0, NH=None):
    return enclose("T12", box, N, grade, NH)/(iv_frac(box[2][0], box[2][1])*iv_frac(box[3][0], box[3][1]))


def H33(box, N=32, grade=0, NH=None):
    return enclose("H33", box, N, grade, NH)
