"""Run and retain independent 80/110-digit reference results; log failures explicitly."""
import argparse, concurrent.futures as cf, json, os, subprocess, sys
from fractions import Fraction as F
from decimal import Decimal
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
    rows=[];early_failures=[]
    for k,i in keys():
        ps=[path(k,i,d) for d in (80,110)]
        for d,p in zip((80,110),ps):
            if p.with_suffix('.error').exists():
                early_failures.append({'kind':k,'id':i,'dps':d,'status':'REFERENCE_EXECUTION_ERROR'})
            elif p.exists() and p.stat().st_size and json.loads(p.read_text()).get('status')=='REFERENCE_UNRESOLVED':
                early_failures.append({'kind':k,'id':i,'dps':d,'status':'REFERENCE_UNRESOLVED'})
        if any(not p.exists() or not p.stat().st_size for p in ps):continue
        aa,bb=[json.loads(p.read_text()) for p in ps]
        if any(x.get('status')=='REFERENCE_UNRESOLVED' for x in (aa,bb)):
            rows.append(dict(kind=k,id=i,status='REFERENCE_UNRESOLVED',value80=aa['value'],
                             value110=bb['value'],seconds=[aa['seconds'],bb['seconds']]))
            continue
        def original(obj):
            if 'mpf_binary' in obj:
                n,e=obj['mpf_binary'];return F(int(n))*F(2)**e,F(0)
            # Older already-running jobs retained dps decimal digits. One
            # decimal ulp bounds the unknown rounding to that displayed value.
            dec=Decimal(obj['value'])
            return F(dec),F(10)**(dec.adjusted()-obj['dps']+1)
        (a,ea),(b,eb)=original(aa),original(bb);diff=abs(a-b)
        diff_bound=diff+ea+eb
        key={'H':'V62_','Haa':'Haa_','contact':'E2c_point_'}[k]+str(i)
        interval=data.get(key)
        status='AWAITING_ENCLOSURE'
        if diff_bound>=F(1,10**55):status='REFERENCE_UNRESOLVED'
        elif interval:
            status='PASS' if interval[0]<=b-eb and b+eb<=interval[1] else 'FAIL'
            if k=='contact':
                parent=data.get('E2c_box_'+str(i//2))
                if parent is None:status='AWAITING_PARENT'
                elif not(parent[0]<=b-eb and b+eb<=parent[1]):status='FAIL'
        rows.append(dict(kind=k,id=i,status=status,value80=aa['value'],value110=bb['value'],
                   abs_difference=str(diff),abs_difference_upper=str(diff_bound),seconds=[aa['seconds'],bb['seconds']],calls=[aa['quadrature_calls'],bb['quadrature_calls']]))
    if rows:atomic(OUT/'reference_comparisons.jsonl',''.join(json.dumps(r)+'\n' for r in rows))
    bad=[{'kind':r['kind'],'id':r['id'],'status':r['status']} for r in rows if r['status'] in ('REFERENCE_UNRESOLVED','FAIL')]
    gate='STOP_REPORT' if bad or early_failures else 'PASS' if len(rows)==88 and all(r['status']=='PASS' for r in rows) else 'PENDING'
    summary={'pairs':len(rows),'of':88,'statuses':{x:sum(r['status']==x for r in rows) for x in {r['status'] for r in rows}},
             'reference_gate':gate,'blockers':early_failures+bad}
    atomic(OUT/'E2_REFERENCE_GATE.json',json.dumps(summary)+'\n')
    print(json.dumps(summary),flush=True)
    return gate
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=6);ap.add_argument('--kind',choices=['H','contact','Haa']);ap.add_argument('--min-id',type=int,default=0);ap.add_argument('--max-id',type=int,default=71)
    ap.add_argument('--require-pass',action='store_true');ap.add_argument('--skip-active-first',action='store_true');ap.add_argument('--aggregate',action='store_true')
    args=ap.parse_args()
    if not args.aggregate:
        queue=[(k,i,d) for k,i in keys() for d in (80,110) if (not args.kind or k==args.kind) and args.min_id<=i<=args.max_id and not(args.skip_active_first and k=='H' and i==0)]
        with cf.ThreadPoolExecutor(args.workers) as pool:
            for _ in pool.map(run,queue):aggregate()
    gate=aggregate()
    if gate=='STOP_REPORT' or (args.require_pass and gate!='PASS'):sys.exit(4)
