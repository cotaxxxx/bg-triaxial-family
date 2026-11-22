"""Non-validated probe, continuation of band_probe.py (float64; DIAGNOSTIC_ONLY).
A cell-wise interval enclosure of an angular mean has width about  (mean of |angular gradient|) x (cell diameter).
This script measures the mean of |grad g| over the sphere for g = n-th q3-derivative of the integrand (n = 2, 3),
in the usual coordinates and in chord coordinates, and the width of the steep region (fraction of the sphere that
carries half of the total variation).  Usage: band_variation.py out.json"""
import json, sys
import numpy as np
import band_probe as bp          # the grid and the two integrands

out = []
dz = 2/bp.NZ; dph = 2*np.pi/bp.NP
for s_, t_ in ((2.68, 5.45), (2.0, 3.0)):
    l = np.array([1.0, s_, s_*t_]); q = np.array([0.85, 0.22, 1/64])
    for n, h in ((2, 2e-3), (3, 2e-3)):
        row = dict(s=s_, t=t_, L3=s_*t_, q=[float(x) for x in q], n=n)
        for name, F in (("usual", bp.F_usual), ("chord", bp.F_chord)):
            g = bp.deriv(F, q, l, n, h)
            gz = np.gradient(g, dz, axis=0)*bp.RHO; gp = (np.roll(g, -1, 1) - np.roll(g, 1, 1))/(2*dph)/bp.RHO
            v = np.sqrt(gz*gz + gp*gp); tv = float(v.mean()); vs = np.sort(v.ravel())[::-1]; c = np.cumsum(vs)
            half = float((np.searchsorted(c, 0.5*c[-1]) + 1)/vs.size)
            row[name] = dict(integral=float(g.mean()), mean_abs=float(np.abs(g).mean()), mean_abs_gradient=tv, fraction_of_sphere_with_half_the_variation=half,
                             predicted_width_N256=tv*np.pi/256, predicted_width_N512=tv*np.pi/512)
            print("L3=%5.2f n=%d %-5s int %+.4e mean|g| %.3e mean|grad g| %.3e half of variation on %.2e of the sphere; mean|grad| x pi/256 = %.3g, x pi/512 = %.3g" % (
                s_*t_, n, name, row[name]["integral"], row[name]["mean_abs"], tv, half, tv*np.pi/256, tv*np.pi/512), flush=True)
        row["ratio_usual_over_chord"] = row["usual"]["mean_abs_gradient"]/row["chord"]["mean_abs_gradient"]; out.append(row)
json.dump(dict(NZ=bp.NZ, NPHI=bp.NP, rows=out), open(sys.argv[1], "w"), indent=1)
