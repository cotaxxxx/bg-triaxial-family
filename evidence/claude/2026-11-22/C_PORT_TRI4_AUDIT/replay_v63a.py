"""Replay of the V63-A subdivision rule (copied from v63a/run_v63a.py of the production bundle) with two changes:
the time budget is replaced by a cap on the number of enclosures per sample, and the grid is built just before each
enclosure so that grid time and enclosure time are measured separately.  Every enclosure is recorded.
Usage: replay_v63a.py samples.json KMAX part nparts out.jsonl      (Reader chosen by PYTHONPATH)"""
import json, math, struct, sys, time
from fractions import Fraction as F
import numpy as np
from geoenclosereader import tri4, tri2

S = json.load(open(sys.argv[1])); KMAX = int(sys.argv[2]); part, nparts = int(sys.argv[3]), int(sys.argv[4])
out = open(sys.argv[5], "a"); MAXDEPTH = 24


def hx(x): return struct.pack(">d", float(x)).hex()


def norm(o):
    if isinstance(o, dict): return {str(k): norm(v) for k, v in sorted(o.items(), key=lambda kv: str(kv[0]))}
    if isinstance(o, (list, tuple)): return [norm(v) for v in o]
    if isinstance(o, (bool, np.bool_)): return bool(o)
    if isinstance(o, (int, np.integer)): return int(o)
    if isinstance(o, (float, np.floating)): return "f:" + hx(o)
    return str(o)


def grade(kind, box):
    L3 = float(box[0][1]*box[1][1])
    if kind == 'H33': return max(0, min(4, round(math.log2(L3))))
    if kind == 'W3': return max(0, min(2, round(math.log2(L3)/2)))
    return 0


def outside(box): return sum(b[0]**2 for b in box[2:]) > 1


def ev(idx, kind, box, N):
    global nev
    if len(tri2._grid) > 4: tri2._grid.clear()
    g = grade(kind, box); n0 = len(tri2._grid)
    t0 = time.perf_counter(); tri4._grid(N, g, box); t1 = time.perf_counter()
    fresh = len(tri2._grid) > n0
    e = {'W3': tri4.W3, 'H33': tri4.H33, 'C12': tri4.C12}[kind](box, N, g, N, True); t2 = time.perf_counter()
    rec = dict(id=idx*1000 + nev, sample=idx, n=nev, kind=kind, box=[[str(a), str(b)] for a, b in box], N=N, grade=g,
               lo=hx(e.lo), hi=hx(e.hi), last=norm(tri4.enclose.last), grid_fresh=fresh, seconds=dict(grid=t1 - t0, enclose=t2 - t1))
    out.write(json.dumps(rec, sort_keys=True) + "\n"); out.flush(); nev += 1
    return e


for idx, smp in enumerate(S):
    if idx % nparts != part: continue
    kind = smp['kind']; box0 = [tuple(F(x) for x in pr) for pr in smp['box']]; nev = 0
    L3 = float(box0[0][1]*box0[1][1]); N0 = 64 if L3 <= 4 else (128 if L3 <= 10 else 256)
    queue = [(box0, 0, N0)]; leaves = skipped = 0; status = 'COVERED'
    while queue:
        if nev >= KMAX: status = 'KMAX'; break
        box, dep, N = queue.pop()
        if outside(box): skipped += 1; continue
        try:
            e = ev(idx, kind, box, N)
        except ValueError as ex:
            status = ('INCONSISTENT: ' if 'INCONSISTENT' in str(ex) else 'KERNEL_LIMIT: ') + str(ex); break
        L = tri4.enclose.last
        if e.lo > 0: leaves += 1; continue
        if e.hi < 0 and L['contact_cells'] == 0: status = 'NEGATIVE'; break
        terms = L['terms']; aw = L['angular_width']
        jbest = max(terms, key=lambda j: terms[j]) if terms else None
        if jbest is not None and terms[jbest] >= aw and N < 512:
            e2 = ev(idx, kind, box, 2*N); L2 = tri4.enclose.last
            if e2.lo > 0: leaves += 1; continue
            t2 = L2['terms'].get(jbest, float('inf'))
            if t2 <= 0.5*terms[jbest]: queue.append((box, dep, 2*N)); continue
        if jbest is not None and terms[jbest] >= aw and dep < MAXDEPTH:
            lo, hi = box[jbest]; m = (lo + hi)/2
            for half in ((lo, m), (m, hi)):
                nb = list(box); nb[jbest] = half; queue.append((nb, dep + 1, N))
        elif N < 512: queue.append((box, dep, 2*N))
        elif jbest is not None and dep < MAXDEPTH:
            lo, hi = box[jbest]; m = (lo + hi)/2
            for half in ((lo, m), (m, hi)):
                nb = list(box); nb[jbest] = half; queue.append((nb, dep + 1, N))
        else: status = 'UNRESOLVED'; break
    out.write(json.dumps(dict(id=idx*1000 + 999, sample=idx, end=True, status=status, enclosures=nev, leaves=leaves, skipped=skipped,
                              remaining=len(queue)), sort_keys=True) + "\n"); out.flush()
