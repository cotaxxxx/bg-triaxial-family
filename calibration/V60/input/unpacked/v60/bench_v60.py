"""V60 speed benchmark (fixed workload, cold grid cache). usage: bench_v60.py READER_DIR -> one JSON line."""
import sys, time, json, resource
sys.path.insert(0, sys.argv[1])
from fractions import Fraction as F
from geoenclosereader import tri4
t0 = time.time()
c = (F(117, 40), F(91, 16), F(1, 64), F(47, 64), F(1, 64)); r = F(1, 512)
e1 = tri4.H33([(x - r, x + r) for x in c], 256, 4)
c = (F(5, 2), F(4), F(1, 4), F(1, 8), F(1, 2)); r = F(1, 256)
e2 = tri4.W3([(x - r, x + r) for x in c], 128, 2)
print(json.dumps(dict(sec=round(time.time() - t0, 2), maxrss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 1),
                      h33=[float(e1.lo), float(e1.hi)], w3=[float(e2.lo), float(e2.hi)])), flush=True)
