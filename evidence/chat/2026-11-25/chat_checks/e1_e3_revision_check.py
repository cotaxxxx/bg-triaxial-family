import json,sys
from fractions import Fraction as F
from decimal import Decimal
O,N,R=sys.argv[1:4]
v=lambda x:F(int(x[0]))*F(2)**x[1]
def load(d,f): return {r['id']:r for r in map(json.loads,open(f'{d}/{f}_stages.jsonl'))}
nest_bad=0;n=0;ratios=[];idsets={}
for f in ('E1','H','Haa','E2c'):
    o,nw=load(O,f),load(N,f); assert set(o)==set(nw),f; idsets[f]=len(nw)
    for i in nw:
        assert o[i]['box']==nw[i]['box']
        for so,sn in zip(o[i]['stages'],nw[i]['stages']):
            assert so['panels']==sn['panels']; n+=1
            (a,b),(c,d)=[(v(s['interval'][0]),v(s['interval'][1])) for s in (so,sn)]
            if not(a<=c and d<=b): nest_bad+=1
        so,sn=o[i]['stages'][-1],nw[i]['stages'][-1]
        wo=v(so['interval'][1])-v(so['interval'][0]); wn=v(sn['interval'][1])-v(sn['interval'][0])
        ratios.append((float(wn/wo) if wo else 1.0,f,i))
ratios.sort(); print("largest ratios",[(round(r,4),f,i) for r,f,i in ratios[-6:]]); print("ids",idsets,'stage rows',n,'nesting violations',nest_bad)
rs=sorted(r for r,_,_ in ratios); print('final width ratio new/old: min %.4f median %.4f max %.4f'%(rs[0],rs[len(rs)//2],rs[-1]))
# E2 containment
fin={}
for f in ('H','Haa','E2c'):
    for i,r in load(N,f).items(): s=r['stages'][-1]['interval']; fin[i]=(v(s[0]),v(s[1]))
def val(o):
    if 'mpf_binary' in o: a,e=o['mpf_binary']; return F(int(a))*F(2)**e,F(0)
    d=Decimal(o['value']); return F(d),F(10)**(d.adjusted()-o['dps']+1)
HAA=[11,62,60,8,53,29,42,43]; ok=0; marg=[]
for k,i in [('H',i) for i in range(72)]+[('Haa',i) for i in HAA]+[('contact',i) for i in range(8)]:
    b,eb=val(json.load(open(f'{R}/reference_{k}_{i}_110.json')))
    key={'H':'V62_','Haa':'Haa_','contact':'E2c_point_'}[k]+str(i); lo,hi=fin[key]
    g= lo<=b-eb and b+eb<=hi
    if k=='contact': plo,phi=fin['E2c_box_'+str(i//2)]; g=g and plo<=b-eb and b+eb<=phi
    ok+=g; marg.append((float(min(b-lo,hi-b)/(hi-lo)),key))
marg.sort(); print('E2 references inside revised final intervals:',ok,'/ 88; smallest relative margin',[(round(m,3),k) for m,k in marg[:3]])
# signs on the 92 E3 endpoints
for tag,f in (('old',f'{O}/E3.jsonl'),('new',f'{N}/E3_ASTRA_ENDPOINTS.jsonl')):
    A=[json.loads(l) for l in open(f)]; pos=[a['id'] for a in A if v(a['interval'][0])>0]; neg=[a['id'] for a in A if v(a['interval'][1])<0]
    pts=sum(1 for a in A[:72] if v(a['interval'][0])>0); bx=sum(1 for a in A[72:] if v(a['interval'][0])>0)
    W=sorted(float(v(a['interval'][1])-v(a['interval'][0])) for a in A[:72])
    print(tag,'positive: points',pts,'/72, boxes',bx,'/20; negative',len(neg),'; point width median %.3g max %.3g'%(W[36],W[-1]))
