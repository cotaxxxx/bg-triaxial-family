"""A positive-volume depth-12 companion for any selected empty intersection."""
import json
from fractions import Fraction as F
from pathlib import Path
here=Path(__file__).resolve().parent
def select():
    rows=json.loads((here/'cases.json').read_text())
    for r in json.loads((here/'cases_v2_extra.json').read_text()): rows[r['source_index']]=r
    def box(r):return [[F(x) for x in p] for p in r['box']]
    def norm_lower(b):return sum(max(F(0),lo,-hi)**2 for lo,hi in b[2:])
    for i,r in enumerate(rows):
        if norm_lower(box(r))<=1:continue
        assert r['depth']==12
        b=box(rows[i-1])
        assert rows[i-1]['depth']==6 and norm_lower(b)<1 and all(lo>=0 for lo,hi in b[2:])
        axes=[j for j,(lo,hi) in enumerate(b) if lo<hi]
        for depth in range(6,12):
            j=axes[depth%len(axes)]
            lo,hi=b[j];b[j]=[lo,(lo+hi)/2]
        assert norm_lower(b)<1
        yield dict(r,source_index=i,box=[[str(x) for x in p] for p in b])
if __name__=='__main__':
    print(json.dumps(list(select()),indent=2))
