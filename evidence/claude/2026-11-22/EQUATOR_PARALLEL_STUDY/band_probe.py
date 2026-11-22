"""Non-validated numerical probe (float64, finite differences; DIAGNOSTIC_ONLY, not an enclosure).
Question: how much do the q3-derivatives of the integrand of E = <k arccos^2(gamma)> cancel under the integral,
(a) in the usual coordinates (xi on the sphere fixed while q moves), and
(b) in chord coordinates (omega = direction from q to xi fixed while q moves; xi = q + r*omega,
    r = -q.omega + sqrt((q.omega)^2 + 1 - |q|^2), sphere measure = r^2/(omega.xi) d omega)?
For n = 2 (the integrand of H33) and n = 3, 4 (its first and second q3-derivatives) the script prints the integral,
the mean absolute value and the maximum of the n-th q3-derivative of the integrand in both coordinate systems.
Written from the formulas only (k = 1 - q.xi, D = |L(xi - q)|, B = |L^-1 xi|^2, gamma = k/(D sqrt B), L = diag(1, s, s t)).
Usage: band_probe.py out.json [NZ NPHI]"""
import json, sys
import numpy as np

NZ = int(sys.argv[2]) if len(sys.argv) > 2 else 4000; NP = int(sys.argv[3]) if len(sys.argv) > 3 else 2000     # band_variation.py passes the same arguments
z = -1 + (np.arange(NZ) + 0.5)*2/NZ; ph = (np.arange(NP) + 0.5)*2*np.pi/NP
Z, PH = np.meshgrid(z, ph, indexing="ij"); RHO = np.sqrt(1 - Z*Z); X = np.stack([RHO*np.cos(PH), RHO*np.sin(PH), Z])   # unit vectors, equal weights


def f_xi(xi, q, l):
    v = xi - q[:, None, None]; k = 1 - (q[:, None, None]*xi).sum(0)
    D = np.sqrt(((l[:, None, None]*v)**2).sum(0)); S = np.sqrt(((xi/l[:, None, None])**2).sum(0))
    g = np.clip(k/(D*S), -1.0, 1.0); return k*np.arccos(g)**2


def F_usual(q, l): return f_xi(X, q, l)


def F_chord(q, l):
    qw = (q[:, None, None]*X).sum(0); c = np.sqrt(qw*qw + 1 - (q*q).sum()); r = -qw + c
    xi = q[:, None, None] + r*X; return f_xi(xi, q, l)*r*r/c            # omega.xi = c


def deriv(F, q, l, n, h):
    e = np.array([0.0, 0.0, h]); f = lambda m: F(q + m*e, l)
    if n == 0: return f(0)
    if n == 2: return (f(1) - 2*f(0) + f(-1))/h**2
    if n == 3: return (f(2) - 2*f(1) + 2*f(-1) - f(-2))/(2*h**3)
    if n == 4: return (f(2) - 4*f(1) + 6*f(0) - 4*f(-1) + f(-2))/h**4


def main():
    out = []
    for s, t in ((2.68, 5.45), (1.3, 1.3), (2.0, 3.0)):
        l = np.array([1.0, s, s*t])
        for q3 in (0.0, 1/64, 1/32):
            q = np.array([0.85, 0.22, q3])
            for n, h in ((0, 0.0), (2, 2e-3), (3, 2e-3), (4, 4e-3)):
                row = dict(s=s, t=t, L3=s*t, q=[float(x) for x in q], n=n, h=h)
                for name, F in (("usual", F_usual), ("chord", F_chord)):
                    d = deriv(F, q, l, n, h); row[name] = dict(integral=float(d.mean()), mean_abs=float(np.abs(d).mean()), max_abs=float(np.abs(d).max()))
                row["cancellation_usual"] = row["usual"]["mean_abs"]/max(abs(row["usual"]["integral"]), 1e-300)
                row["cancellation_chord"] = row["chord"]["mean_abs"]/max(abs(row["chord"]["integral"]), 1e-300)
                out.append(row)
                print("L3=%5.2f q3=%.5f n=%d | usual: int %+.5e  mean|.| %.4e  max %.3e | chord: int %+.5e  mean|.| %.4e  max %.3e" % (
                    s*t, q3, n, row["usual"]["integral"], row["usual"]["mean_abs"], row["usual"]["max_abs"],
                    row["chord"]["integral"], row["chord"]["mean_abs"], row["chord"]["max_abs"]), flush=True)
    json.dump(dict(NZ=NZ, NPHI=NP, rows=out), open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
