"""Strict manifest and field comparison. Retain stdout for both sides, including discrepancies."""
import argparse
import json
from pathlib import Path
import sys
p=argparse.ArgumentParser()
p.add_argument('results',type=Path)
p.add_argument('references',type=Path)
a=p.parse_args();d=a.results
load=lambda path:[json.loads(s) for s in path.read_text().splitlines()]
left=load(d/'A_python.jsonl');right=load(d/'A_c.jsonl')
left += load(d/'A_extra_python.jsonl');right += load(d/'A_extra_c.jsonl')
inball_ref=load(d/'inball_python.jsonl');inball_c=load(d/'inball_c.jsonl')
left+=inball_ref;right+=inball_c
if [r['index'] for r in left]!=list(range(68)) or [r['index'] for r in right]!=list(range(68)):
    raise ValueError('missing, duplicate, or reordered fixed cases')
omit={'sec','rss_kib'}
from validate_extra import validate
branches,errors=validate(d)
if any("exception" in r["outcome"] for r in inball_ref+inball_c):errors.append(dict(test="nonempty depth",python=inball_ref,c=inball_c))
for x,y in zip(left,right):
    if any(x.get(k)!=y.get(k) for k in (x.keys()|y.keys())-omit):
        errors.append(dict(test='A',python=x,c=y))
ep=load(d/'errors_python.jsonl');ec=load(d/'errors_c.jsonl')
if ep!=ec or len(ep)!=4: errors.append(dict(test='error dispatch',python=ep,c=ec))
rows=[]
for i in range(2):
    src=load(a.references/f'lazy_{i}.jsonl')[0]
    for backend in ['python','c']:
        v=load(d/'perf'/f'tree{i}_{backend}.jsonl')
        check=['leaves','evals','leaf_sha256','status']
        ok=len(v)==1 and all(v[0][k]==src[k] for k in check) and src['status']=='COVERED'
        rows.append(dict(tree=i,backend=backend,**{k:v[0][k] for k in check},equal=ok))
        if not ok:errors.append(dict(test='B',expected=src,actual=v))
tests={}
for name in ['tri','tri2','tri3','tri4','lazy','examples']:
    tests[name]=(d/'selftest'/f'selftest_{name}.log').read_text().splitlines()[-1]
    if tests[name]!='FAILURES 0':errors.append(dict(test='C',name=name,last=tests[name]))
primitives=json.loads((d/'primitives.json').read_text())
if primitives!=dict(nextafter=20018,fsum=2030,mismatches=0):errors.append(dict(test='primitives',actual=primitives))
for backend in ['c','python']:
    vals=load(d/'perf'/f'N512_{backend}.log')
    if len(vals)!=1 or vals[0]['outcome']!=left[53]['outcome']:errors.append(dict(test='memory',backend=backend))
x=load(d/'perf/bench_python.log');y=load(d/'perf/bench_c.log')
for i in (0,1):
    if any(x[i][k]!=y[i][k] for k in ('kind','lo','hi')):errors.append(dict(test='bench',python=x[i],c=y[i]))
print(json.dumps(dict(A_total=len(left),A_exceptions=sum('exception' in r['outcome'] for r in left),
                      error_probes=ep,branch_cases=7,branches=branches,B=rows,C=tests,primitives=primitives,errors=errors),indent=2))
sys.exit(bool(errors))
