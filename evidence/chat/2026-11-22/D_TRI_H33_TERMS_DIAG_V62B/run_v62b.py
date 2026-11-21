"""V62-B instrumented copy of run_v61.py: identical rules; argv[7] = per-evaluation log (jsonl).
V61 runner: Reader 0.6 (tri4 with lazy=True: first-order form first, second order added only when undecided;
the tree, leaves and evals are those of V60 / Reader 0.5),
5-D adaptive cover of (shape tile x position cell) for layer I (W3/H33) and layer II (C12).
usage: run_v61.py READER_DIR samples.json part nparts out.jsonl BUDGET_SEC
Rules (PLAN_V61.md §3): as run_v60.py (PLAN_V60 §3) except: lazy=True; a progress trace every 300 s.
V60 rules: as V59-B run_v59b.py except: kernel tri4; MAXDEPTH 24; INCONSISTENT stops the combo;
grid cache cleared when it holds more than 16 grids (memory only, no effect on values); leaf hash and margins recorded."""
import sys, json, time, math, hashlib
sys.path.insert(0, sys.argv[1])
from fractions import Fraction as F
from geoenclosereader import tri4, tri2
S = json.load(open(sys.argv[2])); part, nparts = int(sys.argv[3]), int(sys.argv[4])
out = open(sys.argv[5], 'a'); BUDGET = float(sys.argv[6]); MAXDEPTH = 24
LOG = open(sys.argv[7], 'a')
def logev(box, dep, N, e, L, step):
    LOG.write(json.dumps(dict(step=step, dep=dep, N=N, w=[float(b - a) for a, b in box], lo=float(e.lo), hi=float(e.hi), used=L['used'], order=L['order'], aw=L['angular_width'], terms={str(k): v for k, v in L['terms'].items()}, w1=L.get('width1'), w2=L.get('width2'), tw=L['total_width'])) + "\n"); LOG.flush()


def grade(kind, box):
    L3 = float(box[0][1]*box[1][1])
    if kind == 'H33': return max(0, min(4, round(math.log2(L3))))
    if kind == 'W3': return max(0, min(2, round(math.log2(L3)/2)))
    return 0


def ev(kind, box, N):
    if len(tri2._grid) > 16: tri2._grid.clear()
    return {'W3': tri4.W3, 'H33': tri4.H33, 'C12': tri4.C12}[kind](box, N, grade(kind, box), None, True)


def outside(box): return sum(b[0]**2 for b in box[2:]) > 1


for idx, smp in enumerate(S):
    if idx % nparts != part: continue
    kind = smp['kind']; box0 = [tuple(F(x) for x in pr) for pr in smp['box']]; T0 = time.time()
    L3 = float(box0[0][1]*box0[1][1]); N0 = 64 if L3 <= 4 else (128 if L3 <= 10 else 256)
    queue = [(box0, 0, N0)]; leaves = evals = skipped = maxd = used2 = 0; status = 'COVERED'
    hsh = hashlib.sha256(); minlo = None; trace = []; tnext = 300.0; skips = 0
    while queue:
        el = time.time() - T0
        if el >= tnext: trace.append([round(el), evals, leaves, len(queue)]); tnext += 300.0
        if el > BUDGET: status = 'BUDGET'; break
        box, dep, N = queue.pop()
        if outside(box): skipped += 1; continue
        try:
            e = ev(kind, box, N); evals += 1; logev(box, dep, N, e, tri4.enclose.last, 'e')
        except ValueError as ex:
            status = ('INCONSISTENT: ' if 'INCONSISTENT' in str(ex) else 'KERNEL_LIMIT: ') + str(ex); break
        L = tri4.enclose.last; used2 += L['used'] == 2; skips += L.get('lazy_skip', False)
        if e.lo > 0:
            leaves += 1; maxd = max(maxd, dep); minlo = float(e.lo) if minlo is None else min(minlo, float(e.lo))
            hsh.update((repr([(str(a), str(b)) for a, b in box]) + f"|{N}\n").encode()); continue
        if e.hi < 0 and L['contact_cells'] == 0: status = 'NEGATIVE'; break
        terms = L['terms']; aw = L['angular_width']
        jbest = max(terms, key=lambda j: terms[j]) if terms else None
        if jbest is not None and terms[jbest] >= aw and N < 256:
            e2 = ev(kind, box, 2*N); evals += 1; L2 = tri4.enclose.last; logev(box, dep, 2*N, e2, L2, 'e2'); used2 += L2['used'] == 2; skips += L2.get('lazy_skip', False)
            if e2.lo > 0:
                leaves += 1; maxd = max(maxd, dep); minlo = float(e2.lo) if minlo is None else min(minlo, float(e2.lo))
                hsh.update((repr([(str(a), str(b)) for a, b in box]) + f"|{2*N}\n").encode()); continue
            t2 = L2['terms'].get(jbest, float('inf'))
            if t2 <= 0.5*terms[jbest]: queue.append((box, dep, 2*N)); continue
        if jbest is not None and terms[jbest] >= aw and dep < MAXDEPTH:
            lo, hi = box[jbest]; m = (lo + hi)/2
            for half in ((lo, m), (m, hi)):
                nb = list(box); nb[jbest] = half; queue.append((nb, dep + 1, N))
        elif N < 256: queue.append((box, dep, 2*N))
        elif jbest is not None and dep < MAXDEPTH:
            lo, hi = box[jbest]; m = (lo + hi)/2
            for half in ((lo, m), (m, hi)):
                nb = list(box); nb[jbest] = half; queue.append((nb, dep + 1, N))
        else: status = 'UNRESOLVED'; break
    rec = dict(smp, kernel='tri4/0.6.0 lazy', status=status, leaves=leaves, evals=evals, used2=used2, skipped=skipped, maxdepth=maxd,
               remaining=len(queue), sec=round(time.time() - T0, 1), budget=BUDGET, min_leaf_lo=minlo, leaf_sha256=hsh.hexdigest(), lazy_skips=skips, trace=trace)
    out.write(json.dumps(rec, default=str) + "\n"); out.flush(); print(json.dumps(rec, default=str), flush=True)
