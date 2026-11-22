"""Regenerate the selected V61 rows and RNG path, bisecting only positive-width axes."""
import json
from pathlib import Path
import sys
here=Path(__file__).resolve().parent
src=(here/'select_cases.py').read_text()
needle='j = depth % 5'
assert src.count(needle)==1
src=src.replace(needle, 'active = [k for k,(lo,hi) in enumerate(box) if lo < hi]\n                j = active[depth % len(active)]')
ns={'__name__':'selection'}
exec(compile(src,'selection_v2','exec'),ns)
rows=ns['select'](sys.argv[1])
old=json.loads((here/'cases.json').read_text())
changed=[dict(r,source_index=i) for i,r in enumerate(rows) if r!=old[i]]
assert len(changed)==6 and all(r['kind']=='C12' and r['depth'] in (6,12) for r in changed)
print(json.dumps(changed,indent=2))
