"""Fix the boxes of test A (run once, before any comparison).  Usage: select_cases.py samples_v61.json out.json
A1: 8 of the 39 V61 combos (seed 20261124; at least 2 each of layer I H33, layer I W3, layer II C12); for each the root
    box and one descendant at depth 6 and at depth 12 (seeded bisection path; a half lying outside the ball by the
    runner's test is not taken); N = 64 and 256 with lazy off, N = 64 also with lazy on; grade by the runner's rule,
    NH by the V61 rule (None = max(16, N/2)); called through the wrappers W3 / C12 / H33 as the runner does.
A2: chat's test box (grid_test_box.md), H33, grade 4, lazy off, (N, NH) in (256,128) (256,256) (512,128) (512,256) (512,512).
A4: boxes for the branch 'no contact cell on the fine grid, D2 <= 0 on a coarse cell, second-order form dropped':
    direction in the middle of a cell of the NH = 16 grid, |q| in {29/32, 15/16, 61/64}, N = 128, NH = 16, three kinds,
    lazy off and on.
(A3 = the 133 boxes of the earlier audit, files cases_A3_audit.json and cases_A3_audit_supp1.json, unchanged.)"""
import json, math, random, sys
from fractions import Fraction as F

SEED = 20261124
S = json.load(open(sys.argv[1])); assert len(S) == 39
KIND = {"W3": "E3", "C12": "T12", "H33": "H33"}


def grade(kind, box):
    L3 = float(box[0][1]*box[1][1])
    if kind == 'H33': return max(0, min(4, round(math.log2(L3))))
    if kind == 'W3': return max(0, min(2, round(math.log2(L3)/2)))
    return 0


def outside(box): return sum(b[0]**2 for b in box[2:]) > 1


rng = random.Random(SEED)
cls = {("I", "H33"): [], ("I", "W3"): [], ("II", "C12"): []}
for i, s in enumerate(S): cls[(s["layer"], s["kind"])].append(i)
chosen = []
for k in (("I", "H33"), ("I", "W3"), ("II", "C12")): chosen += rng.sample(cls[k], 2)
chosen += rng.sample([i for i in range(39) if i not in chosen], 2)
cases = []; cid = 2000
for i in chosen:
    s = S[i]; box = [(F(a), F(b)) for a, b in s["box"]]; path = random.Random(SEED*1000 + i); boxes = {0: list(box)}
    for dep in range(1, 13):
        while True:
            j = path.randrange(5); lo, hi = box[j]; m = (lo + hi)/2; halves = [(lo, m), (m, hi)]; path.shuffle(halves)
            ok = [h for h in halves if not outside(box[:j] + [h] + box[j+1:])]
            if ok: box = box[:j] + [ok[0]] + box[j+1:]; break
        if dep in (6, 12): boxes[dep] = list(box)
    for dep, b in boxes.items():
        for N, lazy in ((64, False), (64, True), (256, False)):
            cases.append(dict(id=cid, group="A1", sample=i, layer=s["layer"], stratum=s["stratum"], depth=dep, kind=KIND[s["kind"]], wrap=True,
                              box=[[str(x), str(y)] for x, y in b], N=N, grade=grade(s["kind"], b), NH=None, lazy=lazy)); cid += 1
cid = 3000
tb = [(F(53, 20), F(53, 20) + F(11, 160)), (F(43, 8), F(43, 8) + F(5, 32)), (F(27, 32), F(27, 32) + F(1, 64)), (F(7, 32), F(7, 32) + F(1, 128)), (F(0), F(1, 1024))]
for N, NH in ((256, 128), (256, 256), (512, 128), (512, 256), (512, 512)):
    cases.append(dict(id=cid, group="A2", kind="H33", wrap=True, box=[[str(x), str(y)] for x, y in tb], N=N, grade=4, NH=NH, lazy=False)); cid += 1
cid = 4000; d = (F(126, 256), F(153, 256), F(162, 256)); w = F(1, 512)
for kind in ("E3", "T12", "H33"):
    for r in (F(29, 32), F(15, 16), F(61, 64)):
        for lazy in (False, True):
            c = (F(3, 2), F(3, 2), r*d[0], r*d[1], r*d[2])
            cases.append(dict(id=cid, group="A4", kind=kind, wrap=False, box=[[str(x - w), str(x + w)] for x in c], N=128, grade=0, NH=16, lazy=lazy)); cid += 1
json.dump(cases, open(sys.argv[2], "w"), indent=1)
print(len(cases), "cases; chosen V61 combos:", chosen, [(S[i]["layer"], S[i]["kind"], S[i]["stratum"]) for i in chosen])
