"""V62 diagnostic: guaranteed point enclosures of H33 in the equator cell (27,7,0) and one control cell.
usage: diag_v62.py READER_DIR part nparts out.jsonl      (PLAN_V62_DIAG.md)"""
import sys, json, time, math
sys.path.insert(0, sys.argv[1])
from fractions import Fraction as F
from geoenclosereader import tri4
part, nparts, out = int(sys.argv[2]), int(sys.argv[3]), open(sys.argv[4], 'a')
TILES = {(0, 0): ((F(1), F(31, 20)), (F(1), F(13, 8))), (1, 3): ((F(31, 20), F(21, 10)), (F(23, 8), F(7, 2))),
         (2, 5): ((F(21, 10), F(53, 20)), (F(33, 8), F(19, 4))), (3, 7): ((F(53, 20), F(16, 5)), (F(43, 8), F(6)))}
def grade(st): return max(0, min(4, round(math.log2(float(st[0][1]*st[1][1])))))
jobs = []
# A: cell (27,7,0), 3 x 3 x 2 points per tile, N = 512
for tile, st in sorted(TILES.items()):
    s, t = sum(st[0])/2, sum(st[1])/2
    for q3 in (F(0), F(1, 32)):
        for q1 in (F(27, 32), F(55, 64), F(7, 8)):
            for q2 in (F(7, 32), F(15, 64), F(1, 4)):
                jobs.append(('A', tile, (s, t, q1, q2, q3), 512, grade(st)))
# B: cell centre at q3 = 0, N = 1024, every tile
for tile, st in sorted(TILES.items()):
    jobs.append(('B', tile, (sum(st[0])/2, sum(st[1])/2, F(55, 64), F(15, 64), F(0)), 1024, grade(st)))
# C: control, a covered equator cell (10,0,0) of tile (1,3), centre, q3 = 0, N = 512
st = TILES[(1, 3)]; jobs.append(('C', (1, 3), (sum(st[0])/2, sum(st[1])/2, F(21, 64), F(1, 64), F(0)), 512, grade(st)))
for i, (grp, tile, p, N, g) in enumerate(jobs):
    if i % nparts != part: continue
    T = time.time()
    try:
        e = tri4.H33([(x, x) for x in p], N, g, None, False); lo, hi, st_ = float(e.lo), float(e.hi), 'OK'
    except ValueError as ex:
        lo = hi = None; st_ = 'KERNEL_LIMIT: ' + str(ex)
    out.write(json.dumps(dict(i=i, group=grp, tile=tile, p=[str(x) for x in p], N=N, grade=g, lo=lo, hi=hi,
                              status=st_, sec=round(time.time() - T, 1))) + '\n'); out.flush()
