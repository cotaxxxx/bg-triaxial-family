"""Schedule identical integrals once; aggregate using exact fractions and 128-bit outward rounding."""
import argparse, concurrent.futures as cf, hashlib, json, os, subprocess, tempfile, time
from fractions import Fraction as F
from pathlib import Path
from samples import ROOT, points, contacts, e1, public_boxes, HAA, deg, middle
OUT=ROOT/'results'
MAXSTAGES=(128,512,2048)
def rounded(x,up):
    if not x:return F(0)
    e=x.numerator.bit_length()-x.denominator.bit_length()
    if abs(x)<F(2)**e:e-=1
    unit=F(2)**(e-127); a=x/unit
    return (-(-a.numerator//a.denominator) if up else a.numerator//a.denominator)*unit
def ri(a,b):return (rounded(a,False),rounded(b,True))
def add(A,B):return ri(A[0]+B[0],A[1]+B[1])
def mul(A,B):
    a=[x*y for x in A for y in B];return ri(min(a),max(a))
def intersect(*iv):
    a,b=max(q[0] for q in iv),min(q[1] for q in iv)
    if a>b:raise RuntimeError(f'INCONSISTENT: {a} > {b}')
    return a,b
def encode(x):
    if not x:return ['0',0]
    n=x.numerator;ex=1-x.denominator.bit_length()
    while n%2==0:n//=2;ex+=1
    return [str(n),ex]
def ivjson(iv):return [encode(x) for x in iv]
def unpack(ab):return tuple(F(int(n))*F(2)**e for n,e in ab)
def idigest(obj):return hashlib.sha256(json.dumps(obj,separators=(',',':')).encode()).hexdigest()
def atomic(path,s):
    with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,prefix=path.name+'.',delete=False) as tmp:
        tmp.write(s);name=tmp.name
    os.replace(name,path)
def arr(b):return [str(v) for ab in b for v in ab]
def tasks():
    jobs={};cases=[]
    def req(b,order,side=-1,mode=0):
        args=[str(mode),str(order),str(side)]+arr(b);k=idigest(args)
        jobs[k]=args;return k
    def hcase(id,b):
        mid=[deg(middle(x)) for x in b];base=b[:4]+[deg(0)];tube=b[:4]+[(F(0),b[4][1])]
        return dict(id=id,kind='H',box=b,D=req(b,2),center=req(mid,2),base=req(base,2),four=req(tube,4) if b[4][1] else None,
                    gradients=[req(b,2,i) if i<4 else req(b,3) for i in range(5) if b[i][1]>b[i][0]],
                    grad_axes=[i for i in range(5) if b[i][1]>b[i][0]])
    for label,b in [('center',[deg(middle(x)) for x in e1()]),('box',e1())]:
        tube=b[:4]+[(F(0),b[4][1])]
        cases.append(dict(id='E1_'+label,kind='E1',box=b,D=req(b,3),four=req(tube,4)))
    for i,b in enumerate(points()):cases.append(hcase('V62_'+str(i),b))
    for id,b in public_boxes():cases.append(hcase(id,b))
    for i in HAA:cases.append(dict(id='Haa_'+str(i),kind='Haa',box=points()[i],D=req(points()[i],4)))
    for i,(pts,b) in enumerate(contacts()):
        for n,pt in enumerate(pts):cases.append(dict(id='E2c_point_'+str(2*i+n),kind='contact_point',box=pt,D=req(pt,2,mode=1)))
        cases.append(dict(id='E2c_box_'+str(i),kind='contact_box',box=b,D=req(b,2,mode=2)))
    return jobs,cases
def combine(c,stage,outcomes):
    def val(k):return unpack(outcomes[k][stage]['interval'])
    b=c['box'];d=val(c['D']);kind=c['kind'];raw={'direct':d}
    if kind=='H':
        C=val(c['center'])
        for i,k in zip(c['grad_axes'],c['gradients']):
            lo,hi=b[i];m=middle(b[i]);C=add(C,mul(ri(lo-m,hi-m),val(k)))
        a=b[4];term=(F(0),F(0)) if not c['four'] else mul(ri(a[0]**2/2,a[1]**2/2),val(c['four']))
        raw.update(center=C,even=add(val(c['base']),term))
    if kind=='E1':raw['even']=mul(ri(*b[4]),val(c['four']))
    return raw,intersect(*raw.values())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=6);ap.add_argument('--aggregate',action='store_true')
    args=ap.parse_args()
    jobs,cases=tasks();kernel=ROOT/'kernel';binhash=hashlib.sha256(kernel.read_bytes()).hexdigest()
    cache=OUT/'integrals'/binhash;cache.mkdir(parents=True,exist_ok=True)
    atomic(cache/'jobs.json',json.dumps(jobs,sort_keys=True)+'\n')
    def run(k):
        path=cache/(k+'.json')
        if path.exists():return
        before=time.monotonic();cmd=[str(kernel)]+jobs[k]
        p=subprocess.run(cmd,capture_output=True,text=True)
        if p.returncode:
            raise RuntimeError(f'{k}: {cmd} {p.returncode} {p.stderr}')
        rows=[json.loads(s) for s in p.stdout.splitlines()]
        if [row['panels'] for row in rows]!=list(MAXSTAGES):raise RuntimeError('missing stages')
        atomic(path,json.dumps(dict(args=jobs[k],seconds=time.monotonic()-before,stages=rows))+'\n')
    if not args.aggregate:
        with cf.ThreadPoolExecutor(args.workers) as pool:
            for _ in pool.map(run,jobs):pass
    result={k:json.loads((cache/(k+'.json')).read_text())['stages'] for k in jobs if (cache/(k+'.json')).exists()}
    rows=[]
    for c in cases:
        cumulative=None;stages=[]
        try:
            for i,L in enumerate(MAXSTAGES):
                data,iv=combine(c,i,result);cumulative=iv if cumulative is None else intersect(cumulative,iv)
                row=dict(panels=L,components={k:ivjson(v) for k,v in data.items()},interval=ivjson(cumulative),width=ivjson(ri(cumulative[1]-cumulative[0],cumulative[1]-cumulative[0]))[1])
                if c['kind'].startswith('contact'):row['contact_data']=result[c['D']][i]
                stages.append(row)
        except KeyError:continue
        rows.append(dict(id=c['id'],kind=c['kind'],box=arr(c['box']),stages=stages,precision_bits=128))
    for name,subset in [('E1',[r for r in rows if r['kind']=='E1']),('E2c',[r for r in rows if r['kind'].startswith('contact')]),('Haa',[r for r in rows if r['kind']=='Haa']),('H',[r for r in rows if r['kind']=='H'])]:
        if subset:atomic(OUT/(name+'_stages.jsonl'),''.join(json.dumps(r,separators=(',',':'))+'\n' for r in subset))
    H=[r for r in rows if r['kind']=='H']
    if len(H)==92:
        f=OUT/'E3_ASTRA_ENDPOINTS.jsonl'
        public_hash='183bc5412593c223e5b799a8f08b6aec24077e2bbd5860bb02843c2353b04a80'
        lines=[]
        for r in H:
            lines.append(json.dumps({'id':r['id'],'geometry':r['box'],'interval':r['stages'][-1]['interval'],
                      'precision_bits':128,'input_sha256':public_hash if ',' in r['id'] else idigest(r['box']),
                      'status':'ENCLOSED_PENDING_CHAT'},separators=(',',':')))
        atomic(f,'\n'.join(lines)+'\n')
    print(json.dumps(dict(completed=len(result),planned=len(jobs),finished_cases=len(rows),total_cases=len(cases),kernel_sha256=binhash)))
if __name__=='__main__':main()
