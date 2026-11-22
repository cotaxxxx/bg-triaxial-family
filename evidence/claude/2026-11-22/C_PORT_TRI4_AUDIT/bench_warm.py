"""Speed with a warm grid cache (reference only): each case is evaluated twice in one process; the second
call is timed.  Usage: bench_warm.py cases.json ids out.json   (Reader chosen by PYTHONPATH)"""
import json, sys, time
from fractions import Fraction as F
from geoenclosereader import tri4
cases = {c["id"]: c for c in json.load(open(sys.argv[1]))}; out = []
for i in map(int, sys.argv[2].split(",")):
    c = cases[i]; box = [(F(a), F(b)) for a, b in c["box"]]; ts = []
    for rep in range(3):
        t0 = time.perf_counter(); r = tri4.enclose(c["kind"], box, c["N"], c["grade"], c["NH"], c["lazy"]); ts.append(time.perf_counter() - t0)
    out.append(dict(id=i, kind=c["kind"], N=c["N"], NH=c["NH"], lazy=c["lazy"], order=tri4.enclose.last["order"], lazy_skip=tri4.enclose.last["lazy_skip"],
                    cold_s=ts[0], warm_s=min(ts[1:])))
json.dump(out, open(sys.argv[3], "w"), indent=1)
