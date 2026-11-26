"""chat audit of Candidate B v2 result ledgers (read-only, exact rationals)."""
import json,sys,collections as C
from fractions import Fraction as F
R=sys.argv[1]
def L(f): return [json.loads(l) for l in open(f'{R}/{f}')]
def r(v): return F(int(v['n']))*(F(2)**v['e'] if 'e' in v else F(1,int(v['d'])))
def bx(b): return tuple(r(v) for v in b)
E={e['id']:e for e in L('enclosures.jsonl')}
def iv(eid): return tuple(r(v) for v in E[eid]['interval'])
def sg(eid):
    lo,hi=iv(eid); return 1 if lo>0 else -1 if hi<0 else 0
area=lambda b:(b[1]-b[0])*(b[3]-b[2])
B=L('boxes.jsonl'); P=[p for p in L('pending.jsonl') if 'box' in p]
CH={c['id']:c for c in L('charts.jsonl')}; LK=L('links.jsonl')
REG=(F(1,4),F(1),F(1),F(7)); RA=area(REG)
out={}
for q in ('Z1','Z2','D1','D2'):
    o=C.Counter(); bq=[x for x in B if x['quantity']==q]; nodes={x['node']:x for x in bq}
    # 1 signs
    for x in bq:
        if x['status'] in('SIGN_POS','SIGN_NEG'):
            s=sg(x['evaluation']); o['sign_bad']+= s!=(1 if x['status']=='SIGN_POS' else -1)
            o['sign_box_mismatch']+= bx(E[x['evaluation']]['box'])!=bx(x['box'])
    # 2 tree partition
    for x in bq:
        if x['status']=='SPLIT':
            pb=bx(x['box']); ch=x['children']; ca=0
            for c in ch:
                cb=None
                if c in nodes: cb=bx(nodes[c]['box'])
                else:
                    m=[p for p in P if p['quantity']==q and p['node']==c]
                    if m: cb=bx(m[0]['box'])
                if cb is None: o['child_missing']+=1; continue
                o['child_outside']+= not(pb[0]<=cb[0] and cb[1]<=pb[1] and pb[2]<=cb[2] and cb[3]<=pb[3])
                ca+=area(cb)
            o['split_area_bad']+= ca!=area(pb)
    roots=[x for x in bq if x['parent'] is None]
    proots=[p for p in P if p['quantity']==q and p['parent'] is None]
    o['root_area_ok']=int(sum(area(bx(x['box'])) for x in roots)+sum(area(bx(p['box'])) for p in proots)==RA)
    leaves=[x for x in bq if x['status']!='SPLIT']; pend=[p for p in P if p['quantity']==q]
    la=sum(area(bx(x['box'])) for x in leaves)+sum(area(bx(p['box'])) for p in pend)
    o['leaf_area_equals_region']=int(la==RA)
    st=C.Counter(x['status'] for x in leaves)
    o.update({'n_'+k:v for k,v in st.items()}); o['n_pending']=len(pend)
    sa=sum(area(bx(x['box'])) for x in leaves if x['status'] in('SIGN_POS','SIGN_NEG'))
    ca=sum(area(bx(x['box'])) for x in leaves if x['status']=='IN_CHART_UNION')
    ua=sum(area(bx(x['box'])) for x in leaves if x['status']=='UNRESOLVED')+sum(area(bx(p['box'])) for p in pend)
    o['sign_frac']=round(float(sa/RA),5); o['chart_frac']=round(float(ca/RA),5); o['open_frac']=round(float(ua/RA),5)
    # 3 charts
    cq=[c for c in CH.values() if c['quantity']==q and c['status']=='CHART']
    for c in cq:
        b=bx(c['box']); k=c['cross']; f0,f1=c['faces']
        s0,s1=sg(f0),sg(f1); o['chart_face_bad']+= not(s0*s1==-1)
        b0,b1=bx(E[f0]['box']),bx(E[f1]['box'])
        lo,hi=(2*k,2*k+1)
        o['chart_face_geom_bad']+= not(b0[lo]==b0[hi]==b[lo] and b1[lo]==b1[hi]==b[hi] and b0[2-2*k:4-2*k]==b[2-2*k:4-2*k]==b1[2-2*k:4-2*k])
        t=c['transverse']; o['chart_transverse_bad']+= not(sg(t)!=0 and bx(E[t]['box'])==b and E[t]['derivative']==k+1)
    # 4 IN_CHART_UNION boxes within union bounding of listed charts (each box must lie inside some listed chart, or union)
    for x in leaves:
        if x['status']=='IN_CHART_UNION':
            b=bx(x['box']); cs=[bx(CH[c]['box']) for c in x['charts']]
            if any(CH[c]['status']!='CHART' for c in x['charts']): o['union_uses_rejected']+=1
            # exact containment by union: check area of b covered by union via grid of breakpoints
            ys=sorted({b[0],b[1]}|{v for c in cs for v in (c[0],c[1]) if b[0]<v<b[1]})
            zs=sorted({b[2],b[3]}|{v for c in cs for v in (c[2],c[3]) if b[2]<v<b[3]})
            ok=all(any(c[0]<=y0 and y1<=c[1] and c[2]<=z0 and z1<=c[3] for c in cs) for y0,y1 in zip(ys,ys[1:]) for z0,z1 in zip(zs,zs[1:]))
            o['union_not_covered']+= not ok
    lq=[l for l in LK if l['quantity']==q]
    o['links']=C.Counter(l['status'] for l in lq)
    out[q]=dict(o)
for q,o in out.items(): print(q,json.dumps({k:(dict(v) if isinstance(v,C.Counter) else v) for k,v in o.items()},default=str))
print('intersections:')
for x in L('intersections.jsonl'): print(' ',x['pair'],x['status'],x.get('mode',''),x.get('reason',''))
