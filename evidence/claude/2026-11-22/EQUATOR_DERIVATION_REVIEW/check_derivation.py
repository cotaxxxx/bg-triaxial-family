"""Numerical spot checks for the review of DERIVATION.md (equator band, commit f7716a0).  float64 / mpmath,
non-validated, DIAGNOSTIC_ONLY.  Written from DERIVATION.md and the original definition only.
(1) items 2-5: the transformed integral equals the original one; a-derivatives at fixed (lambda, phi) versus fixed xi.
(2) items 8-10: series coefficients, F'(1), F''(1), M1, M2, the ratio bound 32/57 and the tail bound (5/2) T.
(3) items 14-16: the two-node rule constant 1/4320.
(4) items 20-22: |gamma'| <= l/D, |gamma''| <= 3 l^2/D^2, |d_a^2 (k F)| <= C0/d0 at random points (finite differences)."""
import json, math, sys
import numpy as np
import mpmath as mp
out = {}

# ---------- (1)
NL, NPH = 2000, 1000
lam = -np.pi/2 + (np.arange(NL) + 0.5)*np.pi/NL; ph = (np.arange(NPH) + 0.5)*2*np.pi/NPH
LAM, PH = np.meshgrid(lam, ph, indexing="ij"); V = np.sin(LAM); C = np.cos(LAM)


def kF(xi, q, l):
    v = xi - q[:, None, None]; k = 1 - (q[:, None, None]*xi).sum(0)
    D = np.sqrt(((l[:, None, None]*v)**2).sum(0)); b = np.sqrt(((xi/l[:, None, None])**2).sum(0))
    return k*np.arccos(np.clip(k/(D*b), -1, 1))**2


def G_fixed_xi(q, l):                      # lambda = latitude of xi itself; density cos(lambda)/(4 pi) * (pi * 2 pi) for the mean
    xi = np.stack([C*np.cos(PH), C*np.sin(PH), V]); return kF(xi, q, l)*C*np.pi/2


def G_moebius(q, l):                       # items 2-5
    a = q[2]; U = 1 + a*V; A = 1 - a*a; z = (V + a)/U; r = np.sqrt(A)*C/U
    xi = np.stack([r*np.cos(PH), r*np.sin(PH), z]); return kF(xi, q, l)*(A*C/U**2)*np.pi/2


def dn(G, q, l, n, h):
    e = np.array([0, 0, h]); f = lambda m: G(q + m*e, l)
    return {0: lambda: f(0), 2: lambda: (f(1) - 2*f(0) + f(-1))/h**2, 3: lambda: (f(2) - 2*f(1) + 2*f(-1) - f(-2))/(2*h**3),
            4: lambda: (f(2) - 4*f(1) + 6*f(0) - 4*f(-1) + f(-2))/h**4}[n]()


rows = []
for s, t in ((2.68, 5.45), (2.0, 3.0)):
    l = np.array([1.0, s, s*t]); q = np.array([0.85, 0.22, 1/64])
    for n, h in ((0, 0), (2, 2e-3), (3, 2e-3), (4, 4e-3)):
        r = dict(L3=s*t, n=n)
        for name, G in (("fixed_xi", G_fixed_xi), ("moebius", G_moebius)):
            d = dn(G, q, l, n, h); r[name] = dict(integral=float(d.mean()), mean_abs=float(np.abs(d).mean()), max_abs=float(np.abs(d).max()))
        rows.append(r); print("L3=%5.2f n=%d fixed xi: int %+.5e mean|.| %.3e max %.2e | moebius: int %+.5e mean|.| %.3e max %.2e" % (
            s*t, n, r["fixed_xi"]["integral"], r["fixed_xi"]["mean_abs"], r["fixed_xi"]["max_abs"], r["moebius"]["integral"], r["moebius"]["mean_abs"], r["moebius"]["max_abs"]), flush=True)
out["transform"] = rows

# ---------- (2)
mp.mp.dps = 40
c = [mp.mpf(0), mp.mpf(2)]
for n in range(1, 400): c.append(c[n]*n*n/((n + 1)*(2*n + 1)))
F = lambda g: mp.acos(g)**2
chk = dict(series_at_y_half=float(abs(sum(c[n]*mp.mpf(1)/2**n for n in range(1, 400)) - F(mp.mpf(1)/2))),
           F1_at_1=float(-c[1]), F2_at_1=float(2*c[2]),
           M1=float(max(abs(mp.diff(F, g)) for g in [mp.mpf(i)/200 for i in range(0, 200)])), M1_at_0=float(abs(mp.diff(F, 0))),
           M2_at_0=float(abs(mp.diff(F, 0, 2))), M2_grid_max=float(max(abs(mp.diff(F, mp.mpf(i)/200, 2)) for i in range(0, 200))))
worst = 0; tail_ok = True
for j in range(0, 9):
    for n in range(64, 399): worst = max(worst, float(mp.mpf(n*n)/((2*n + 1)*(n + 1 - j))))
    T = c[97]*mp.ff(97, j); tail = sum(c[n]*mp.ff(n, j) for n in range(97, 399)); tail_ok &= bool(0 <= tail <= mp.mpf(5)/2*T)
chk.update(worst_ratio_n_ge_64_j_le_8=worst, bound_32_over_57=32/57, tail_within_5_over_2_T_at_y_1=tail_ok)
out["series"] = chk; print(chk)

# ---------- (3)
d = mp.mpf(1); x1, x2 = -d/(2*mp.sqrt(3)), d/(2*mp.sqrt(3)); f4 = lambda x: x**4
gl = dict(error_for_x4=float(mp.quad(f4, [-d/2, d/2])/d - (f4(x1) + f4(x2))/2), d4_times_24_over_4320=float(d**4*24/4320))
out["two_node_rule"] = gl; print(gl)

# ---------- (4)
rng = np.random.default_rng(20261122); bad = dict(g1=0, g2=0, kF2=0); worst = dict(g1=0.0, g2=0.0, kF2=0.0); N = 200000
M1, M2 = math.pi, 2.0
s = rng.uniform(1, 3.2, N); t = rng.uniform(1, 6, N); l3 = s*t
xi = rng.normal(size=(3, N)); xi /= np.linalg.norm(xi, axis=0)
qd = rng.normal(size=(3, N)); qd /= np.linalg.norm(qd, axis=0); rho = rng.uniform(0.5, 1.0, N)**0.25
near = rng.random(N) < 0.5; qd = np.where(near, xi + 0.2*rng.normal(size=(3, N)), qd); qd /= np.linalg.norm(qd, axis=0); q = qd*rho
L = np.stack([np.ones(N), s, l3])


def parts(q):
    v = xi - q; k = 1 - (q*xi).sum(0); D = np.sqrt(((L*v)**2).sum(0)); b = np.sqrt(((xi/L)**2).sum(0)); g = k/(D*b); return k, D, g


h = 1e-4; e3 = np.array([[0.0], [0.0], [1.0]])
k0, D0, g0 = parts(q); kp, Dp, gp = parts(q + h*e3); km, Dm, gm = parts(q - h*e3)
ok = (np.linalg.norm(q + h*e3, axis=0) < 1) & (D0 > 50*h*l3)           # finite differences meaningful
g1 = np.abs(gp - gm)/(2*h); g2 = np.abs(gp - 2*g0 + gm)/h**2
Fv = lambda g: np.arccos(np.clip(g, -1, 1))**2
kF2 = np.abs(kp*Fv(gp) - 2*k0*Fv(g0) + km*Fv(gm))/h**2
d0 = np.linalg.norm(xi - q, axis=0); C0 = 2*M1*l3 + (M2 + 3*M1)*l3**2
for name, lhs, rhs in (("g1", g1, l3/D0), ("g2", g2, 3*l3**2/D0**2), ("kF2", kF2, C0/d0)):
    ratio = (lhs/rhs)[ok]; worst[name] = float(ratio.max()); bad[name] = int((ratio > 1 + 1e-3).sum())
out["contact_bounds"] = dict(samples=int(ok.sum()), worst_ratio_lhs_over_bound=worst, violations=bad); print(out["contact_bounds"])
json.dump(out, open(sys.argv[1], "w"), indent=1)
