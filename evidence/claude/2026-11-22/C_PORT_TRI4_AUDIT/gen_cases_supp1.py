"""Supplementary cases (fixed before running): no contact on the fine grid, coarse-grid D^2 bound not positive."""
import json, random, sys
from fractions import Fraction as F
rng = random.Random("CLAUDE-CPORT-AUDIT-20261122-SUPP1")
dy = lambda x, den: F(round(x*den), den)
cases = []
for i in range(18):
    s0 = dy(rng.uniform(1, 3.1), 64); t0 = dy(rng.uniform(1, 5.9), 64)
    while True:
        v = [abs(rng.gauss(0, 1)) for _ in range(3)]; n = sum(x*x for x in v)**0.5
        if n > 1e-6: break
    r = rng.uniform(0.84, 0.93); q = [dy(x/n*r, 1024) for x in v]
    box = [[s0, s0 + F(1, 128)], [t0, t0 + F(1, 128)]] + [[x, x + F(1, 256)] for x in q]
    cases.append(dict(id=1000 + i, group="G10", kind=["E3", "T12", "H33"][i % 3], N=[32, 64][(i//3) % 2], grade=0, NH=None, lazy=False, wrap=False,
                      box=[[str(a), str(b)] for a, b in box]))
json.dump(cases, sys.stdout, indent=0)
