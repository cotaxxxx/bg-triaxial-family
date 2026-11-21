"""Triaxial kernels of GeoEncloseReader 0.3.0 (chat, independent of Codex code), L = diag(1, s, s t).

Energy E(q) = < k arccos^2 g >,  k = 1 - q.xi,  D = |L(xi - q)|,  S = |L^{-1} xi|,  g = k/(D S),  u = L(xi - q)/D.
  centre_h(i):  h_i = E_ii(0) = < g [ P R_i (1 - R_i w_i) - Q w_i (1 - R_i)^2 ] >,  w = xi^2, d = sum A w, B = sum w/A,
                R_i = A_i/d, g = (d B)^{-1/2}    (chat's chord form at q = 0, V55 scout; octant symmetry).
  pole_b(i):    b_i = E_i(e_i) full gradient trace at the pole e_i,  E_i = < xi_i (g P - F) - L_i S u_i g^2 P >,
                chart xi = (1 - 2f^2) e_i + 2 f sqrt(1-f^2) (cos p e_j + sin p e_k), v = 2 f w, |w| = 1,
                g = f/(|Lw| S), measure (4/pi) f df dp on [0,1] x [0,pi/2].   No singular factor: |Lw| >= 1.
  disk_tau:     s = 1, q = r e1: tau = (T11 - T22)(r e1) = < k g P [ (m^2 - y^2)/D^2 - (mu^2 - y^2)/S^2 ] >,
                m = mu - r, xi = (mu, y, z); quarter-sphere symmetry, measure dmu dp / pi.
  disk_tau2:    d^2 tau/dr^2 by chat's own differentiation (V57 sec 3; checked against finite differences).
P, Q, F and the derivatives of P are positive series in h = (1 - g)/2 with explicit tails (h <= 1/2)."""
from math import factorial
from fractions import Fraction
import numpy as np
from mpmath import mp, mpf, cos, sin, pi as mpi
from .fiv import I, iv_frac, iv_mp_array, from_frac

NS = 60
_A = [Fraction(4**n*factorial(n)**2, factorial(2*n+1)) for n in range(NS+3)]


def _poly(coefs, h):
    """sum c_n h^n with nonnegative c_n and h >= 0 (Horner in interval arithmetic)."""
    acc = iv_frac(coefs[-1])
    for c in reversed(coefs[:-1]):
        acc = acc*h + iv_frac(c)
    return acc


def _tail(h, lead, ratio):
    """[0, lead * h^M/(1-ratio)] upper tail with lead >= 0, valid when consecutive-term ratio <= ratio < 1."""
    return I(np.zeros_like(lead.lo), (lead*(1.0/(1.0 - ratio))).hi)


def PQF(g, want=("P", "Q", "F")):
    g = g.clip(0.0, 1.0); h = (1 - g)*0.5; h = h.clip(0.0, 0.5); out = {}
    hp = [I.c(1.0), h]
    for _ in range(NS): hp.append(hp[-1]*h)    # hp[n] encloses h^n, n <= NS+1
    hM = hp[NS+1]
    aM = iv_frac(_A[NS+1])
    if "P" in want or "Q" in want:
        P = _poly([2*a for a in _A[:NS+1]], h) + _tail(h, 2*aM*hM, 0.5); out["P"] = P
    if "Q" in want:
        # Q = 2P + g P_g ;  P_g = -sum n a_n h^(n-1)  (dh/dg = -1/2, P = 2 sum a_n h^n)
        Pg = -(_poly([n*_A[n] for n in range(1, NS+1)], h) + _tail(h, (NS+1)*aM*hp[NS], 0.5*(NS+2)/(NS+1)))
        out["Pg"] = Pg; out["Q"] = 2*out["P"] + g*Pg
    if "F" in want:
        # arccos^2 g = 4 sum a_n h^(n+1)/(n+1)
        F = _poly([Fraction(0)] + [4*_A[n]/(n+1) for n in range(NS+1)], h) + _tail(h, 4*aM*hM*h*(1.0/(NS+2)), 0.5)
        out["F"] = F
    if "Pgg" in want:
        # P_gg = (1/2) sum n(n-1) a_n h^(n-2)
        Pgg = _poly([Fraction(n*(n-1), 2)*_A[n] for n in range(2, NS+1)], h) + \
            _tail(h, (NS+1)*NS*0.5*aM*hp[NS-1], 0.5*(NS+2)/NS)
        out["Pgg"] = Pgg
        if "Pg" not in out:
            out["Pg"] = -(_poly([n*_A[n] for n in range(1, NS+1)], h) + _tail(h, (NS+1)*aM*hp[NS], 0.5*(NS+2)/(NS+1)))
        if "P" not in out:
            out["P"] = _poly([2*a for a in _A[:NS+1]], h) + _tail(h, 2*aM*hM, 0.5)
    if "Pggg" in want:
        # P_ggg = -(1/4) sum n(n-1)(n-2) a_n h^(n-3)
        out["Pggg"] = -(_poly([Fraction(n*(n-1)*(n-2), 4)*_A[n] for n in range(3, NS+1)], h) +
                        _tail(h, (NS+1)*NS*(NS-1)*0.25*aM*hp[NS-2], 0.5*(NS+2)/(NS-1)))
    return out


def _angles(n, lo, hi):
    """Endpoints of n equal cells of [lo, hi] (mp numbers): cos/sin as outward intervals at each endpoint."""
    e = [mpf(lo) + (mpf(hi) - mpf(lo))*j/n for j in range(n+1)]
    return e, iv_mp_array([cos(x) for x in e]), iv_mp_array([sin(x) for x in e])


def _mono_hull(vals, a, b):
    """Hull of a monotone function on cell [a, b] given endpoint intervals vals[a], vals[b]."""
    return I(np.minimum(vals.lo[a], vals.lo[b]), np.maximum(vals.hi[a], vals.hi[b]))


def _octant(N):
    e, c, s = _angles(N, 0, mpi/2); j = np.arange(N)
    cth = _mono_hull(c, j, j+1); sth = _mono_hull(s, j, j+1)           # cos, sin on [0, pi/2] monotone
    meas_th = iv_mp_array([cos(e[k]) - cos(e[k+1]) for k in range(N)])   # int sin dth
    dph = iv_mp_array([(e[k+1] - e[k])/(mpi/2) for k in range(N)])
    T, Pp = np.meshgrid(j, j, indexing="ij")
    ct, st = I(cth.lo[T], cth.hi[T]), I(sth.lo[T], sth.hi[T]); cp, sp = I(cth.lo[Pp], cth.hi[Pp]), I(sth.lo[Pp], sth.hi[Pp])
    W = I(meas_th.lo[T], meas_th.hi[T])*I(dph.lo[Pp], dph.hi[Pp])
    return (st*cp, st*sp, ct), W


_cache = {}


def centre_h(i, s0, s1, t0, t1, N=128):
    """Enclosure of h_i over the shape box [s0,s1] x [t0,t1] (exact rationals), axis i in {1,2,3}."""
    key = ("oct", N)
    if key not in _cache: _cache[key] = _octant(N)
    X, W = _cache[key]; w = [x.sq() for x in X]
    s = iv_frac(s0, s1); t = iv_frac(t0, t1); A = [I.c(1.0), s.sq(), (s*t).sq()]
    d = w[0]*A[0] + w[1]*A[1] + w[2]*A[2]; B = w[0] + w[1]/A[1] + w[2]/A[2]
    g = (1/(d*B).sqrt()).clip(0.0, 1.0); pq = PQF(g, ("P", "Q"))
    R = A[i-1]/d; wi = w[i-1]
    f = g*(pq["P"]*R*(1 - R*wi) - pq["Q"]*wi*(1 - R).sq())
    return (f*W).fsum()


def _polechart(N, M):
    ef = [mpf(j)/N for j in range(N+1)]; f = iv_mp_array(ef); j = np.arange(N)
    fc = _mono_hull(f, j, j+1)
    cf = iv_mp_array([mp.sqrt(1 - x*x) for x in ef]); cfc = _mono_hull(cf, j, j+1)     # sqrt(1-f^2), decreasing
    mf = iv_mp_array([(ef[k+1]**2 - ef[k]**2)/2 for k in range(N)])                     # int f df
    e, c, s = _angles(M, 0, mpi/2); k = np.arange(M)
    cp = _mono_hull(c, k, k+1); sp = _mono_hull(s, k, k+1); dp = iv_mp_array([(e[m+1] - e[m])*4/mpi for m in range(M)])
    F_, Pp = np.meshgrid(j, k, indexing="ij")
    take = lambda x, idx: I(x.lo[idx], x.hi[idx])
    return take(fc, F_), take(cfc, F_), take(cp, Pp), take(sp, Pp), take(mf, F_)*take(dp, Pp)


def pole_b(i, s0, s1, t0, t1, N=128, M=128):
    """Enclosure of b_i = E_i(e_i) over the shape box (full gradient trace at the pole e_i)."""
    key = ("pole", N, M)
    if key not in _cache: _cache[key] = _polechart(N, M)
    f, cf, cp, sp, W = _cache[key]
    s = iv_frac(s0, s1); t = iv_frac(t0, t1); L = [I.c(1.0), s, s*t]
    j, k = [a for a in (0, 1, 2) if a != i-1]
    Li, Lj, Lk = L[i-1], L[j], L[k]
    # w = (-f) e_i + cf (cp e_j + sp e_k);  xi = (1 - 2 f^2) e_i + 2 f cf (cp e_j + sp e_k)
    xi_i = 1 - 2*f.sq(); r = 2*f*cf; xi_j = r*cp; xi_k = r*sp
    nLw = ((Li*f).sq() + (Lj*cf*cp).sq() + (Lk*cf*sp).sq()).sqrt()
    S = (xi_i.sq()/Li.sq() + xi_j.sq()/Lj.sq() + xi_k.sq()/Lk.sq()).sqrt()
    g = (f/(nLw*S)).clip(0.0, 1.0); pq = PQF(g, ("P", "F"))
    # - L_i S u_i g^2 P with u_i = L_i (-f)/|Lw|
    integrand = xi_i*(g*pq["P"] - pq["F"]) + Li.sq()*S*f*g.sq()*pq["P"]/nLw
    return (integrand*W).fsum()


def _quarter(N, M):
    em = [-1 + mpf(2)*j/N for j in range(N+1)]; mu = iv_mp_array(em); j = np.arange(N)
    muc = _mono_hull(mu, j, j+1)
    sq1 = iv_mp_array([mp.sqrt(1 - x*x) for x in em])
    # sqrt(1 - mu^2) on a cell: max at mu=0 if inside
    lo = np.minimum(sq1.lo[j], sq1.lo[j+1]); hi = np.maximum(sq1.hi[j], sq1.hi[j+1])
    inside0 = (np.array([float(em[a]) for a in j]) < 0) & (np.array([float(em[a+1]) for a in j]) > 0)
    hi = np.where(inside0, 1.0, hi); s1c = I(lo, hi)
    dmu = iv_mp_array([em[a+1] - em[a] for a in range(N)])
    e, c, s = _angles(M, 0, mpi/2); k = np.arange(M)
    cp = _mono_hull(c, k, k+1); sp = _mono_hull(s, k, k+1); dp = iv_mp_array([(e[m+1] - e[m])/mpi for m in range(M)])
    MU, Pp = np.meshgrid(j, k, indexing="ij"); take = lambda x, idx: I(x.lo[idx], x.hi[idx])
    return take(muc, MU), take(s1c, MU), take(cp, Pp), take(sp, Pp), take(dmu, MU)*take(dp, Pp)


def _disk_parts(t0, t1, r0, r1, N, M):
    key = ("quarter", N, M)
    if key not in _cache: _cache[key] = _quarter(N, M)
    mu, s1, cp, sp, W = _cache[key]
    t = iv_frac(t0, t1); r = iv_frac(r0, r1)
    y = s1*cp; z = s1*sp; Y = y.sq(); Z = z.sq(); m = mu - r
    d = m.sq() + Y + t.sq()*Z; B = mu.sq() + Y + Z/t.sq()
    if np.any(d.lo <= 0): raise ValueError("contact cell: radius box must stay below 1 for disk kernels")
    k = 1 - r*mu; H = 1/(d*B).sqrt(); g = (k*H).clip(0.0, 1.0)
    return dict(mu=mu, Y=Y, Z=Z, m=m, d=d, B=B, k=k, H=H, g=g, t=t, r=r, W=W)


def disk_tau(t0, t1, r0, r1, N=256, M=128):
    p = _disk_parts(t0, t1, r0, r1, N, M); P = PQF(p["g"], ("P",))["P"]
    V = (p["m"].sq() - p["Y"])/p["d"]; Wn = (p["mu"].sq() - p["Y"])/p["B"]
    return (p["k"]*p["g"]*P*(V - Wn)*p["W"]).fsum()


def disk_tau2(t0, t1, r0, r1, N=256, M=128):
    p = _disk_parts(t0, t1, r0, r1, N, M); mu, m, d, k, H, g, Y, Z, t = (p[x] for x in ("mu", "m", "d", "k", "H", "g", "Y", "Z", "t"))
    pq = PQF(g, ("Pgg",)); P, Pg, Pgg = pq["P"], pq["Pg"], pq["Pgg"]
    md = m/d
    g1 = H*(k*md - mu)                                   # dg/dr
    g2 = H*(k*(3*m.sq()/d - 1)/d - 2*mu*md)              # d2g/dr2
    P0 = 2*Y + t.sq()*Z
    V = (m.sq() - Y)/d; V1 = -2*m*P0/d.sq(); V2 = 2*P0*(1 - 4*m.sq()/d)/d.sq()
    Wn = (mu.sq() - Y)/p["B"]
    G = P + g*Pg                                         # d(gP)/dg
    A0 = k*g*P; A1 = -mu*g*P + k*G*g1
    A2 = -2*mu*G*g1 + k*((2*Pg + g*Pgg)*g1.sq() + G*g2)
    return ((A2*(V - Wn) + 2*A1*V1 + A0*V2)*p["W"]).fsum()
