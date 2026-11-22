"""Run and retain independent 80/110-digit reference results; log failures explicitly."""
import argparse, concurrent.futures as cf, json, os, subprocess, sys
from fractions import Fraction as F
from samples import ROOT,HAA
from run_intervals import atomic,unpack
OUT=ROOT/'results'
def keys():
    return [('H',i) for i in range(72)]+[('Haa',i) for i in HAA]+[('contact',i) for i in range(8)]
def path(k,i,d):return OUT/f'reference_{k}_{i}_{d}.json'
def run(key):
    k,i,d=key;p=path(k,i,d)
    if p.exists() and p.stat().st_size:
        obj=json.loads(p.read_text());assert (obj['kind'],obj['id'],obj['dps'])==(k,i,d);return
    cmd=[sys.executable,str(ROOT/'src/reference.py'),k,str(i),str(d)]
    process=subprocess.run(cmd,capture_output=True,text=True)
    if process.returncode:
        atomic(p.with_suffix('.error'),process.stderr);raise RuntimeError('reference failed '+str(key))
    row=json.loads(process.stdout);assert (row['kind'],row['id'],row['dps'])==(k,i,d)
    atomic(p,process.stdout)
def aggregate():
    data={}
    for f in ('H_stages.jsonl','Haa_stages.jsonl','E2c_stages.jsonl'):
        p=OUT/f
        if p.exists():
            for l in p.read_text().splitlines():
                r=json.loads(l);data[r['id']]=unpack(r['stages'][-1]['interval'])
    rows=[]
    for k,i in keys():
        ps=[path(k,i,d) for d in (80,110)]
        if any(not p.exists() or not p.stat().st_size for p in ps):continue
        aa,bb=[json.loads(p.read_text()) for p in ps]
        a,b=F(aa['value']),F(bb['value']);diff=abs(a-b)
        key={'H':'V62_','Haa':'Haa_','contact':'E2c_point_'}[k]+str(i)
        interval=data.get(key)
        status='AWAITING_ENCLOSURE'
        if diff>=F(1,10**55):status='REFERENCE_UNRESOLVED'
        elif interval:
            status='PASS' if interval[0]<=b<=interval[1] else 'FAIL'
            if k=='contact':
                parent=data.get('E2c_box_'+str(i//2))
                if parent is None:status='AWAITING_PARENT'
                elif not parent[0]<=b<=parent[1]:status='FAIL'
        rows.append(dict(kind=k,id=i,status=status,value80=aa['value'],value110=bb['value'],
                   abs_difference=str(diff),seconds=[aa['seconds'],bb['seconds']],calls=[aa['quadrature_calls'],bb['quadrature_calls']]))
    if rows:atomic(OUT/'reference_comparisons.jsonl',''.join(json.dumps(r)+'\n' for r in rows))
    print(json.dumps({'pairs':len(rows),'of':88,'statuses':{x:sum(r['status']==x for r in rows) for x in {r['status'] for r in rows}}}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--skip-active-first',action='store_true');ap.add_argument('--aggregate',action='store_true')
    args=ap.parse_args()
    if not args.aggregate:
        queue=[(k,i,d) for k,i in keys() for d in (80,110) if not(args.skip_active_first and k=='H' and i==0)]
        with cf.ThreadPoolExecutor(args.workers) as pool:
            for _ in pool.map(run,queue):aggregate()
    aggregate()
