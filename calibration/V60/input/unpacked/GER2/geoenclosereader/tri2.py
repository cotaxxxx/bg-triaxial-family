"""Second-order triaxial enclosures (GeoEncloseReader 0.3.0, chat). Same integrands as tri.py, smooth charts:
  centre  octant (th, ph) in [0, pi/2]^2,  weight sin th / (pi/2);
  pole    xi = cos(2b) e_i + sin(2b)(cos p e_j + sin p e_k)  [f = sin b], weight (4/pi) sin b cos b, (b, p) in [0, pi/2]^2;
  disk    s = 1, q = r e1, (th, ph) in [0, pi] x [0, pi/2], weight sin th / pi.
Enclosure of a mean over a shape (or (t, r)) box Bx with centre c:
  value(c)  = sum_cells [ f(c, x_c) m0 + gm . m1  +/- gr . M1 ],  (gm, gr) = mid/rad of grad_x f(c, X_cell)
  value(Bx) = value(c) + sum_k [sum_cells grad_pk f(Bx, X_cell) m0] [-rad_k, rad_k]
with m0 = int w, m1 = int (x - x_c) w, M1 = int |x - x_c| w per cell (mpmath, outward). Mean value theorem on each cell
(convex) and on the box."""
import numpy as np
from fractions import Fraction
from mpmath import mp, mpf, cos, sin, pi as mpi, quad
from .fiv import I, iv_frac, iv_mp_array
from .dual import D, chain
from .tri import PQF

mp.dps = 40


def _cell_moments(N, lo, hi, wkind, ends=None):
    """Per 1-D cell: endpoints, centre, and m0, m1, M1 of the 1-D weight (product weights are separable).
    ends: optional explicit increasing endpoint list (mp numbers) replacing the uniform grid (0.4.0)."""
    e = ends if ends is not None else [mpf(lo) + (mpf(hi) - mpf(lo))*j/N for j in range(N+1)]
    N = len(e) - 1; c = [(e[j] + e[j+1])/2 for j in range(N)]
    if wkind == "sin":   w = sin
    elif wkind == "one": w = lambda x: mpf(1)
    elif wkind == "sincos": w = lambda x: sin(x)*cos(x)
    m0 = [quad(w, [e[j], e[j+1]]) for j in range(N)]
    m1 = [quad(lambda x: (x - c[j])*w(x), [e[j], e[j+1]]) for j in range(N)]
    M1 = [quad(lambda x: abs(x - c[j])*w(x), [e[j], c[j], e[j+1]]) for j in range(N)]
    return e, c, m0, m1, M1


def _trig_cells(e, c):
    n = len(c); j = np.arange(n)
    ce = iv_mp_array([cos(x) for x in e]); se = iv_mp_array([sin(x) for x in e])
    cosX = I(np.minimum(ce.lo[j], ce.lo[j+1]), np.maximum(ce.hi[j], ce.hi[j+1]))
    sinX = I(np.minimum(se.lo[j], se.lo[j+1]), np.maximum(se.hi[j], se.hi[j+1]))
    # cos/sin are monotone on a cell unless it contains an extremum (k pi/2); widen to the extremum then
    for a in range(n):
        for k in range(-1, 5):
            x = k*mpi/2
            if e[a] < x < e[a+1]:
                val = float(cos(x)); sval = float(sin(x))
                cosX.lo[a] = min(cosX.lo[a], val); cosX.hi[a] = max(cosX.hi[a], val)
                sinX.lo[a] = min(sinX.lo[a], sval); sinX.hi[a] = max(sinX.hi[a], sval)
    return cosX, sinX, iv_mp_array([cos(x) for x in c]), iv_mp_array([sin(x) for x in c])


_grid = {}


def _grid2(key, N1, a1, b1, w1, N2, a2, b2, w2, scale, ends1=None):
    if key in _grid: return _grid[key]
    e1, c1, m01, m11, M11 = _cell_moments(N1, a1, b1, w1, ends1); e2, c2, m02, m12, M12 = _cell_moments(N2, a2, b2, w2)
    N1 = len(e1) - 1
    C1, S1, c1c, s1c = _trig_cells(e1, c1); C2, S2, c2c, s2c = _trig_cells(e2, c2)
    J1, J2 = np.meshgrid(np.arange(N1), np.arange(N2), indexing="ij")
    tk = lambda x, idx: I(x.lo[idx], x.hi[idx])
    sc = mpf(scale)
    m0 = iv_mp_array([m01[a]*m02[b]*sc for a in range(N1) for b in range(N2)])
    m1a = iv_mp_array([m11[a]*m02[b]*sc for a in range(N1) for b in range(N2)])
    m1b = iv_mp_array([m01[a]*m12[b]*sc for a in range(N1) for b in range(N2)])
    M1a = iv_mp_array([M11[a]*m02[b]*sc for a in range(N1) for b in range(N2)])
    M1b = iv_mp_array([m01[a]*M12[b]*sc for a in range(N1) for b in range(N2)])
    rs = lambda x: I(x.lo.reshape(N1, N2), x.hi.reshape(N1, N2))
    G = dict(C1=tk(C1, J1), S1=tk(S1, J1), C2=tk(C2, J2), S2=tk(S2, J2), c1=tk(c1c, J1), s1=tk(s1c, J1), c2=tk(c2c, J2), s2=tk(s2c, J2),
             m0=rs(m0), m1=[rs(m1a), rs(m1b)], M1=[rs(M1a), rs(M1b)])
    _grid[key] = G; return G


def _angle_duals(G, n):
    """sin/cos of the two chart angles over the cells as duals with gradients w.r.t. (x1, x2) in slots 0, 1."""
    z = I(np.zeros_like(G["C1"].lo)); g = lambda a, b: [a, b] + [z]*(n - 2)
    return (D(G["S1"], g(G["C1"], z)), D(G["C1"], g(-G["S1"], z)), D(G["S2"], g(z, G["C2"])), D(G["C2"], g(z, -G["S2"])))


def _enclose(f, G, p0, p1):
    """f(sin1, cos1, sin2, cos2, pa, pb) -> integrand (works for I and D). p0, p1: Fractions (box endpoints)."""
    pc = [(a + b)/2 for a, b in zip(p0, p1)]; prad = [(b - a)/2 for a, b in zip(p0, p1)]
    # (i) centre value: f at cell centres + angular gradient over cells
    vc = f(G["s1"], G["c1"], G["s2"], G["c2"], iv_frac(pc[0]), iv_frac(pc[1]))
    s1, c1, s2, c2 = _angle_duals(G, 2)
    fd = f(s1, c1, s2, c2, D.const(iv_frac(pc[0]), 2), D.const(iv_frac(pc[1]), 2))
    tot = vc*G["m0"]
    for k in range(2):
        gk = fd.g[k]; gm = (gk.lo + gk.hi)*0.5; gr = np.maximum(gk.hi - gm, gm - gk.lo)
        gm_i = I(gm); gr_i = I(np.nextafter(gr, np.inf))
        tot = tot + gm_i*G["m1"][k] + I(-1.0, 1.0)*gr_i*G["M1"][k]
    val = tot.fsum(); _enclose.last = {"centre_width": float(val.hi - val.lo), "shape_width": 0.0}
    # (ii) parameter box: natural integral of the parameter gradient
    if any(r != 0 for r in prad):
        z = I(np.zeros_like(G["C1"].lo)); one = I(np.ones_like(G["C1"].lo))
        pa = D(iv_frac(p0[0], p1[0]), [one, z]); pb = D(iv_frac(p0[1], p1[1]), [z, one])
        fp = f(D.const(G["S1"], 2), D.const(G["C1"], 2), D.const(G["S2"], 2), D.const(G["C2"], 2), pa, pb)
        for k in range(2):
            if prad[k] == 0: continue
            dk = (fp.g[k]*G["m0"]).fsum(); term = dk*iv_frac(-prad[k], prad[k]); val = val + term
            _enclose.last["shape_width"] += float(term.hi - term.lo)
    return val


def _PQ_d(g):
    if isinstance(g, D):
        o = PQF(g.v, ("Pgg", "Q", "F")); P, Pg, Pgg, Q, F = o["P"], o["Pg"], o["Pgg"], o["Q"], o["F"]
        return chain(g, P, Pg), chain(g, Q, 3*Pg + g.v*Pgg), chain(g, F, -P)
    o = PQF(g, ("P", "Q", "F")); return o["P"], o["Q"], o["F"]


def _centre_f(i):
    def f(s1, c1, s2, c2, s, t):
        X = [s1*c2, s1*s2, c1]; w = [x.sq() for x in X]; A = [None, s.sq(), (s*t).sq()]
        d = w[0] + A[1]*w[1] + A[2]*w[2]; B = w[0] + w[1]/A[1] + w[2]/A[2]
        g = (1/(d*B).sqrt()).clip(0.0, 1.0); P, Q, _ = _PQ_d(g)
        R = (1/d) if i == 1 else A[i-1]/d; wi = w[i-1]
        return g*(P*R*(1 - R*wi) - Q*wi*(1 - R).sq())
    return f


def centre_h(i, s0, s1, t0, t1, N=64):
    G = _grid2(("oct", N), N, 0, mpi/2, "sin", N, 0, mpi/2, "one", 1/(mpi/2))
    return _enclose(_centre_f(i), G, (Fraction(s0), Fraction(t0)), (Fraction(s1), Fraction(t1)))


def _pole_f(i):
    def f(sb, cb, sp, cp, s, t):
        L = [None, s, s*t]; one = 1.0
        Li = L[i-1]; jk = [a for a in (0, 1, 2) if a != i-1]; Lj, Lk = L[jk[0]], L[jk[1]]
        # f = sin b, sqrt(1-f^2) = cos b; xi_i = 1 - 2 f^2, transverse radius 2 f cos b
        fq = sb; cf = cb; xi_i = 1 - 2*fq.sq(); rr = 2*fq*cf; xj = rr*cp; xk = rr*sp
        sqL = lambda Lx, x: x if Lx is None else Lx*x
        sqd = lambda Lx, x: x if Lx is None else x/Lx
        nLw = (sqL(Li, fq).sq() + sqL(Lj, cf*cp).sq() + sqL(Lk, cf*sp).sq()).sqrt()
        S = (sqd(Li, xi_i).sq() + sqd(Lj, xj).sq() + sqd(Lk, xk).sq()).sqrt()
        g = (fq/(nLw*S)).clip(0.0, 1.0); P, _, F = _PQ_d(g)
        Li2S = S if Li is None else Li.sq()*S
        return xi_i*(g*P - F) + Li2S*fq*g.sq()*P/nLw
    return f


def pole_b(i, s0, s1, t0, t1, N=64):
    G = _grid2(("pole", N), N, 0, mpi/2, "sincos", N, 0, mpi/2, "one", 4/mpi)
    return _enclose(_pole_f(i), G, (Fraction(s0), Fraction(t0)), (Fraction(s1), Fraction(t1)))


def _tau_f(s1, c1, s2, c2, t, r):
    mu = c1; y = s1*c2; z = s1*s2; Y = y.sq(); Z = z.sq(); m = mu - r
    d = m.sq() + Y + t.sq()*Z; B = mu.sq() + Y + Z/t.sq(); k = 1 - r*mu
    g = (k/(d*B).sqrt()).clip(0.0, 1.0); P, _, _ = _PQ_d(g)
    return k*g*P*((m.sq() - Y)/d - (mu.sq() - Y)/B)


def disk_tau(t0, t1, r0, r1, N=128):
    G = _grid2(("disk", N), 2*N, 0, mpi, "sin", N, 0, mpi/2, "one", 1/mpi)
    return _enclose(_tau_f, G, (Fraction(t0), Fraction(r0)), (Fraction(t1), Fraction(r1)))


def _tau2_f(s1, c1, s2, c2, t, r):
    """d^2/dr^2 of the tau integrand (chat's differentiation, V57 sec 3)."""
    mu = c1; y = s1*c2; z = s1*s2; Y = y.sq(); Z = z.sq(); m = mu - r
    d = m.sq() + Y + t.sq()*Z; B = mu.sq() + Y + Z/t.sq(); k = 1 - r*mu; H = 1/(d*B).sqrt()
    g = (k*H).clip(0.0, 1.0)
    if isinstance(g, D):
        o = PQF(g.v, ("Pgg", "Pggg")); P = chain(g, o["P"], o["Pg"]); Pg = chain(g, o["Pg"], o["Pgg"]); Pgg = chain(g, o["Pgg"], o["Pggg"])
    else:
        o = PQF(g, ("Pgg",)); P, Pg, Pgg = o["P"], o["Pg"], o["Pgg"]
    md = m/d
    g1 = H*(k*md - mu); g2 = H*(k*(3*m.sq()/d - 1)/d - 2*mu*md)
    P0 = 2*Y + t.sq()*Z
    V = (m.sq() - Y)/d; V1 = -2*m*P0/d.sq(); V2 = 2*P0*(1 - 4*m.sq()/d)/d.sq(); Wn = (mu.sq() - Y)/B
    G = P + g*Pg; A0 = k*g*P; A1 = -mu*g*P + k*G*g1; A2 = -2*mu*G*g1 + k*((2*Pg + g*Pgg)*g1.sq() + G*g2)
    return A2*(V - Wn) + 2*A1*V1 + A0*V2


def disk_tau2(t0, t1, r0, r1, N=128):
    G = _grid2(("disk", N), 2*N, 0, mpi, "sin", N, 0, mpi/2, "one", 1/mpi)
    return _enclose(_tau2_f, G, (Fraction(t0), Fraction(r0)), (Fraction(t1), Fraction(r1)))


def param_grad(f_kind, i, p0, p1, N=64):
    """Natural enclosure of the parameter gradient of the mean over the box (for derivative-sign ledgers)."""
    if f_kind == "centre":
        G = _grid2(("oct", N), N, 0, mpi/2, "sin", N, 0, mpi/2, "one", 1/(mpi/2)); f = _centre_f(i)
    else:
        G = _grid2(("pole", N), N, 0, mpi/2, "sincos", N, 0, mpi/2, "one", 4/mpi); f = _pole_f(i)
    z = I(np.zeros_like(G["C1"].lo)); one = I(np.ones_like(G["C1"].lo))
    pa = D(iv_frac(p0[0], p1[0]), [one, z]); pb = D(iv_frac(p0[1], p1[1]), [z, one])
    fp = f(D.const(G["S1"], 2), D.const(G["C1"], 2), D.const(G["S2"], 2), D.const(G["C2"], 2), pa, pb)
    return [(fp.g[k]*G["m0"]).fsum() for k in range(2)]
