# chat: E3 intersection check (exact rationals). Usage: python3 -I e3_compare.py ASTRA.jsonl V62_out_A.jsonl PUBLIC.jsonl SEALED.jsonl
import json,sys
from fractions import Fraction as F
A,V,P,S=[[json.loads(l) for l in open(p)] for p in sys.argv[1:5]]
assert len(A)==92 and len(V)==72 and len(P)==len(S)==20
val=lambda x:F(int(x[0]))*F(2)**x[1]
bad=0
for k,a in enumerate(A):
    alo,ahi=val(a['interval'][0]),val(a['interval'][1]); assert alo<=ahi and a['precision_bits']==128
    if k<72:
        v=V[k]; assert v['i']==k and v['group']=='A' and v['status']=='OK' and a['id']=='V62_%d'%k
        assert [F(x) for x in a['geometry']]==[F(x) for p in v['p'] for x in (p,p)]
        rlo,rhi=F(v['lo']),F(v['hi'])
    else:
        p,s=P[k-72],S[k-72]; assert a['id']==p['id']==s['id']
        assert [F(x) for x in a['geometry']]==[F(x) for b in p['box'] for x in b]
        rlo,rhi=F(float(s['lo'])),F(float(s['hi']))
    ok=max(alo,rlo)<=min(ahi,rhi); bad+=not ok
    print(a['id'],'INTERSECT' if ok else 'INCONSISTENT',float(alo),float(ahi),float(rlo),float(rhi))
print('RESULT',92-bad,'/92 intersect')
