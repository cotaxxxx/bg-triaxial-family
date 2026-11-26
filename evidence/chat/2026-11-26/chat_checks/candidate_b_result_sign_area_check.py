import json,sys,collections as C
from fractions import Fraction as F
R=sys.argv[1]
L=lambda f:[json.loads(l) for l in open(f'{R}/{f}')]
EN={e['id']:e for e in L('enclosures.jsonl') if 'id' in e}
def r(v): return F(int(v['n']))*(F(2)**v['e'] if 'e' in v else F(1,int(v['d'])))
B=[x for x in L('boxes.jsonl') if 'quantity' in x]; P=[x for x in L('pending.jsonl') if 'quantity' in x]
area=lambda b:(r(b[1])-r(b[0]))*(r(b[3])-r(b[2]))
bad=0;res={}
for q in ('Z1','Z2','D1','D2'):
    s=[x for x in B if x['quantity']==q and x['status'] in('SIGN_POS','SIGN_NEG')]
    for x in s:
        lo,hi=[r(v) for v in EN[x['evaluation']]['interval']]
        ok=(lo>0) if x['status']=='SIGN_POS' else (hi<0)
        bad+= not ok
    sa=sum(area(x['box']) for x in s)
    leaf_area=sum(area(x['box']) for x in B if x['quantity']==q and x['status']!='SPLIT' and 'box' in x)+sum(area(x['box']) for x in P if x['quantity']==q and x.get('phase')=='boxes' and 'box' in x)
    res[q]=(len(s),str(sa),float(sa/F(9,2)),float(leaf_area/F(9,2)))
print('sign boxes with interval contradicting their sign:',bad)
for q,v in res.items(): print(q,'sign boxes',v[0],'signed area',v[1],'= %.4f of R'%v[2],'| leaves+pending area / R = %.4f'%v[3])
