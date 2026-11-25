import json,sys,os
from fractions import Fraction as F
from decimal import Decimal
R,S=sys.argv[1],sys.argv[2]
iv={}
for f in ('H','Haa','E2c'):
    for l in open(f'{S}/{f}_stages.jsonl'):
        r=json.loads(l); a,b=r['stages'][-1]['interval']; iv[r['id']]=(F(int(a[0]))*F(2)**a[1],F(int(b[0]))*F(2)**b[1])
def val(o):
    if 'mpf_binary' in o: n,e=o['mpf_binary']; return F(int(n))*F(2)**e,F(0),'bin'
    d=Decimal(o['value']); return F(d),F(10)**(d.adjusted()-o['dps']+1),'dec'
HAA=[11,62,60,8,53,29,42,43]
keys=[('H',i) for i in range(72)]+[('Haa',i) for i in HAA]+[('contact',i) for i in range(8)]
worst=F(0);npass=0;kinds={};margins=[]
for k,i in keys:
    o80,o110=[json.load(open(f'{R}/reference_{k}_{i}_{d}.json')) for d in (80,110)]
    assert (o80['kind'],o80['id'],o80['dps'])==(k,i,80) and (o110['kind'],o110['id'],o110['dps'])==(k,i,110)
    (a,ea,t1),(b,eb,t2)=val(o80),val(o110); kinds[(t1,t2)]=kinds.get((t1,t2),0)+1
    db=abs(a-b)+ea+eb; worst=max(worst,db)
    key={'H':'V62_','Haa':'Haa_','contact':'E2c_point_'}[k]+str(i)
    lo,hi=iv[key]; ok= db<F(1,10**55) and lo<=b-eb and b+eb<=hi
    if k=='contact':
        plo,phi=iv['E2c_box_'+str(i//2)]; ok=ok and plo<=b-eb and b+eb<=phi
    margins.append((float(min(b-lo,hi-b)/(hi-lo)),k,i))
    npass+=ok
print('pairs',len(keys),'pass',npass,'worst diff bound %.3e'%float(worst),'value encodings',kinds)
margins.sort(); print('smallest relative margins inside interval:',[(round(m,4),k,i) for m,k,i in margins[:5]])
for k,i in [('Haa',8),('Haa',42)]:
    o=json.load(open(f'{R}/reference_{k}_{i}_110.json')); print(k,i,o['value'][:40],'calls',o['quadrature_calls'],'s',round(o['seconds']))
