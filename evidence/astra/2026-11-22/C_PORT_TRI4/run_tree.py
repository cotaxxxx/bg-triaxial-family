"""Execute the pinned upstream DFS after making just the two grid settings arguments."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys
p=argparse.ArgumentParser()
p.add_argument('bundle',type=Path)
p.add_argument('reader',type=Path)
p.add_argument('samples',type=Path)
p.add_argument('index',type=int)
p.add_argument('output',type=Path)
p.add_argument('--nmax',type=int,choices=[256,512],default=256)
p.add_argument('--nh',choices=['half','full'],default='half')
a=p.parse_args()
if a.output.exists(): raise SystemExit('output already exists')
source=(a.bundle/'v63a/run_v63a.py').read_text()
for find,repl,count in [('N < 512',f'N < {a.nmax}',2),
                       ('grade(kind, box), N, True','grade(kind, box), '+('N' if a.nh=='full' else 'max(16,N//2)')+', True',1),
                       ('tri4/0.6.0 lazy Nmax512 NH=N',f'tri4/0.6.0 lazy Nmax{a.nmax} NH={a.nh}',1)]:
    if source.count(find)!=count: raise RuntimeError(find)
    source=source.replace(find,repl)
sys.argv=['run_v63a.py',str(a.reader.resolve()),str(a.samples.resolve()),str(a.index),
          str(len(json.loads(a.samples.read_text()))),str(a.output.resolve()),'20000']
exec(compile(source,'run_v63a.py','exec'),{'__name__':'__main__'})
