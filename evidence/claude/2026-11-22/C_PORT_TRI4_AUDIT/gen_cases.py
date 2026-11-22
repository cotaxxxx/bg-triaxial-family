"""Independent case generator for the C-port audit (fixed before any run).  DIAGNOSTIC_ONLY."""
import json, random, sys
from fractions import Fraction as F
rng = random.Random("CLAUDE-CPORT-AUDIT-20261122")
KINDS = ["E3", "T12", "H33"]


def dy(x, den):                      # dyadic rational near x
    return F(round(x*den), den)


def shape_box(ws, wt):
    s0 = dy(rng.uniform(1, 3.2 - float(ws)), 64); t0 = dy(rng.uniform(1, 6 - float(wt)), 64)
    return [s0, s0 + ws], [t0, t0 + wt]


def qpoint(rmin, rmax):
    while True:
        v = [abs(rng.gauss(0, 1)) for _ in range(3)]
        n = sum(x*x for x in v)**0.5
        if n > 1e-6:
            r = rng.uniform(rmin, rmax); return [x/n*r for x in v]


def qbox(c, w, den=1024):
    return [[dy(x, den), dy(x, den) + wi] for x, wi in zip(c, w)]


cases = []
def add(group, kind, box, N, grade=0, NH=None, lazy=False, wrap=False):
    cases.append(dict(id=len(cases), group=group, kind=kind, N=N, grade=grade, NH=NH, lazy=lazy, wrap=wrap,
                      box=[[str(a), str(b)] for a, b in box]))


W = [F(1, 8), F(1, 32), F(1, 128)]; QW = [F(1, 16), F(1, 64), F(1, 256)]
# G1 interior generic
for i in range(36):
    sb, tb = shape_box(rng.choice(W), rng.choice(W)); c = qpoint(0.05, 0.8)
    add("G1", KINDS[i % 3], [sb, tb] + qbox(c, [rng.choice(QW) for _ in range(3)]), [16, 32, 64][(i//3) % 3],
        grade=[0, 2][(i//9) % 2], lazy=bool((i//18) % 2))
# G2 touching the sphere (contact cells)
for i in range(12):
    sb, tb = shape_box(rng.choice(W), rng.choice(W)); c = qpoint(0.93, 0.995)
    add("G2", KINDS[i % 3], [sb, tb] + qbox(c, [rng.choice(QW[:2]) for _ in range(3)]), [32, 64][i % 2], grade=[0, 2][(i//6) % 2], lazy=bool(i % 4 == 3))
# G3 box centre outside the ball, box still meets the ball
for i in range(9):
    sb, tb = shape_box(F(1, 32), F(1, 32)); c = qpoint(0.90, 0.97); w = [F(1, 4), F(1, 4), F(1, 4)]
    add("G3", KINDS[i % 3], [sb, tb] + qbox(c, w), [16, 32, 64][i % 3], lazy=bool(i % 2))
# G4 box does not meet the ball
for i in range(3):
    sb, tb = shape_box(F(1, 32), F(1, 32)); c = qpoint(1.2, 1.5)
    add("G4", KINDS[i], [sb, tb] + qbox(c, [F(1, 64)]*3), 32)
# G5 zero-width coordinates (0..4 active variables)
for i in range(12):
    sb, tb = shape_box(F(1, 32), F(1, 32)); c = qpoint(0.1, 0.7); b = [sb, tb] + qbox(c, [F(1, 64)]*3)
    nact = [0, 1, 2, 3, 4][i % 5] if i < 10 else [0, 1][i % 2]
    keep = set(rng.sample(range(5), nact))
    b = [bb if j in keep else [bb[0], bb[0]] for j, bb in enumerate(b)]
    add("G5", KINDS[i % 3], b, [16, 32][i % 2], lazy=bool(i % 3 == 1), grade=[0, 2][i % 2])
# G6 equator / axes
for i in range(9):
    sb, tb = shape_box(F(1, 32), F(1, 32)); r = dy(rng.uniform(0.1, 0.9), 256); z = F(0)
    if i % 3 == 0: q = [[r, r + F(1, 64)], [r/2, r/2 + F(1, 64)], [z, z]]              # on the equatorial plane
    elif i % 3 == 1: q = [[r, r + F(1, 64)], [z, z], [z, F(1, 64)]]                      # near the e1 axis, thin slab in q3
    else: q = [[z, F(1, 128)], [z, F(1, 128)], [r, r + F(1, 64)]]                        # around the e3 axis
    add("G6", ["H33", "E3", "T12"][i % 3] if i < 6 else KINDS[i % 3], [sb, tb] + q, [32, 64, 32][i % 3], lazy=bool(i % 2))
# G7 large grids (tiling above 32768 cells)
for i, N in enumerate([128, 160, 200, 256]*4):
    sb, tb = shape_box(F(1, 128), F(1, 128)); c = qpoint(0.1, 0.85)
    add("G7", KINDS[i % 3], [sb, tb] + qbox(c, [F(1, 256)]*3), N, NH=(None if (i//4) % 2 == 0 else N), lazy=bool((i//8) % 2), grade=[0, 2][(i//2) % 2])
# G8 wide boxes
for i in range(9):
    s0 = dy(rng.uniform(1, 2.5), 8); t0 = dy(rng.uniform(1, 5), 8); c = qpoint(0.0, 0.5)
    add("G8", KINDS[i % 3], [[s0, s0 + F(11, 20)], [t0, t0 + F(5, 8)]] + qbox(c, [F(1, 4), F(1, 4), F(1, 4)], 64), [16, 32, 64][i % 3], lazy=bool(i % 2))
# G9 wrappers W3 / C12 / H33 (boxes away from q_i = 0)
for i in range(9):
    sb, tb = shape_box(rng.choice(W), rng.choice(W)); c = [max(0.12, x) for x in qpoint(0.3, 0.75)]
    add("G9", KINDS[i % 3], [sb, tb] + qbox(c, [F(1, 64)]*3), [32, 64, 32][i % 3], wrap=True, lazy=bool(i % 2), grade=[0, 2][(i//3) % 2])
json.dump(cases, sys.stdout, indent=0)
