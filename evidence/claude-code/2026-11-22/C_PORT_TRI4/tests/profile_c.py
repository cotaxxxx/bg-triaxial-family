"""Work 4, last item: with the C kernel, where does a warm enclosure spend its time?  Cumulative times of the C replay
(_tape._run), I.fsum and tri4._mv_cells under cProfile; the rest is Python (assembly, dual/jet wrappers on outputs,
numpy on whole arrays).  Usage: profile_c.py cases.json ids out.json     (C-port tree on PYTHONPATH)"""
import cProfile, json, pstats, sys, time
from fractions import Fraction as F
from geoenclosereader import tri4
cases = {c["id"]: c for c in json.load(open(sys.argv[1]))}; out = []
for i in map(int, sys.argv[2].split(",")):
    c = cases[i]; box = [(F(a), F(b)) for a, b in c["box"]]; a = (c["kind"], box, c["N"], c["grade"], c["NH"], c["lazy"])
    tri4.enclose(*a); t0 = time.perf_counter(); tri4.enclose(*a); plain = time.perf_counter() - t0
    pr = cProfile.Profile(); pr.enable(); tri4.enclose(*a); pr.disable(); st = pstats.Stats(pr)
    cum = lambda f, n: sum(ct for (fn, ln, name), (cc, nc, tt, ct, callers) in st.stats.items() if fn.endswith(f) and name == n)
    tot = sum(tt for (cc, nc, tt, ct, callers) in st.stats.values())
    k, fs, mv = cum("_tape.py", "_run"), cum("fiv.py", "fsum"), cum("tri4.py", "_mv_cells")
    out.append(dict(id=i, kind=c["kind"], N=c["N"], grade=c["grade"], order=tri4.enclose.last["order"], warm_s=round(plain, 3), profiled_total_s=round(tot, 3),
                    c_kernel_s=round(k, 3), fsum_s=round(fs, 3), mv_cells_s=round(mv, 3), other_python_s=round(tot - k - fs - mv, 3)))
    print(out[-1], flush=True)
json.dump(out, open(sys.argv[3], "w"), indent=1)
