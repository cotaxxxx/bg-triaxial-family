"""Work 1: where the pure-Python Reader 0.6.0 spends its time.  For each chosen case of test A: (1) the grids are
built with an empty cache and timed; (2) the enclosure is then run under cProfile with the grids cached.
Exclusive times are grouped:  array = methods of fiv.I except fsum, plus tri4._mv_cells (numpy array arithmetic);
fsum = I.fsum (math.fsum and the list conversion);  control = everything else (dual/jet/tri bookkeeping, Fractions,
dictionary work, tri4.enclose itself).  Usage: profile_ref.py cases.json ids out.json   (pure-Python tree on PYTHONPATH)"""
import cProfile, json, pstats, sys, time
from fractions import Fraction as F
from geoenclosereader import tri2, tri4
cases = {c["id"]: c for c in json.load(open(sys.argv[1]))}; out = []
for i in map(int, sys.argv[2].split(",")):
    c = cases[i]; box = [(F(a), F(b)) for a, b in c["box"]]; NH = c["NH"] if c["NH"] is not None else max(16, c["N"]//2)
    tri2._grid.clear(); t0 = time.perf_counter(); tri4._grid(c["N"], c["grade"], box); tri4._grid(NH, c["grade"], box); tg = time.perf_counter() - t0
    t0 = time.perf_counter(); tri4.enclose(c["kind"], box, c["N"], c["grade"], c["NH"], c["lazy"]); plain = time.perf_counter() - t0
    pr = cProfile.Profile(); pr.enable(); tri4.enclose(c["kind"], box, c["N"], c["grade"], c["NH"], c["lazy"]); pr.disable()
    st = pstats.Stats(pr); tot = arr = fs = 0.0
    for (fn, ln, name), (cc, nc, tt, ct, callers) in st.stats.items():
        tot += tt
        if fn.endswith("fiv.py") and name == "fsum": fs += ct
    for (fn, ln, name), (cc, nc, tt, ct, callers) in st.stats.items():
        if fn.endswith("fiv.py") and name != "fsum": arr += tt
        elif fn.endswith("tri4.py") and name == "_mv_cells": arr += tt
        elif fn == "~" and "numpy" in name: arr += tt          # numpy functions called by name (where, minimum, nextafter, ...)
    # numpy functions called from inside fsum are part of fsum, not of array: remove the double count
    fs_inner = sum(tt for (fn, ln, name), (cc, nc, tt, ct, callers) in st.stats.items()
                   if any(k[0].endswith("fiv.py") and k[2] == "fsum" for k in callers) and fn == "~" and "numpy" in name)
    arr -= fs_inner
    out.append(dict(id=i, kind=c["kind"], N=c["N"], NH=NH, grade=c["grade"], lazy=c["lazy"], order=tri4.enclose.last["order"], used=tri4.enclose.last["used"],
                    grid_cold_s=round(tg, 3), enclose_warm_s=round(plain, 3), profiled_total_s=round(tot, 3), array_s=round(arr, 3), fsum_s=round(fs, 3),
                    control_s=round(tot - arr - fs, 3)))
    print(out[-1], flush=True)
json.dump(out, open(sys.argv[3], "w"), indent=1)
