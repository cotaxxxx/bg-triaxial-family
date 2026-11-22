"""Generate the fixed A population from the ordered, normalized V61 records."""
import json
import random
import sys
from fractions import Fraction as F
from pathlib import Path

def select(path):
    rng = random.Random(20261124)
    rows = sorted((json.loads(line) for line in Path(path).read_text().splitlines()),
                  key=lambda r: (r['layer'], r['kind'], r['tile'], r['cell'], r['stratum']))
    assert len(rows) == 39
    indices = []
    for kind in ('H33', 'W3', 'C12'):
        indices.extend(rng.sample([i for i, r in enumerate(rows) if r['kind'] == kind], 2))
    indices.extend(rng.sample([i for i in range(39) if i not in indices], 2))
    cases = []
    for i in indices:
        r = rows[i]
        box = [[F(x) for x in pair] for pair in r['box']]
        for depth in range(13):
            if depth in (0, 6, 12):
                cases.append(dict(kind=r['kind'], layer=r['layer'], tile=r['tile'], cell=r['cell'],
                                  depth=depth, box=[[str(x) for x in p] for p in box]))
            if depth < 12:
                j = depth % 5
                lo, hi = box[j]
                box[j] = ((lo, (lo+hi)/2), ((lo+hi)/2, hi))[rng.randrange(2)]
    return cases

if __name__ == '__main__':
    print(json.dumps(select(sys.argv[1]), indent=2))
