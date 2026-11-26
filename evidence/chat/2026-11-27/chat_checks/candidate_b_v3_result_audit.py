"""chat independent re-read of candidate-B v3 results (exact rationals; does not import producer code)."""
import json,sys,collections as C
from fractions import Fraction as F
V2,V3=sys.argv[1],sys.argv[2]
def r(v): return F(int(v['n']))*(F(2)**v['e'] if 'e' in v else F(1,int(v['d'])))
bx=lambda b:tuple(r(v) for v in b)
L=lambda p:[json.loads(l) for l in open(p)]
V2CH={c['id']:c for c in L(f'{V2}/charts.jsonl')}
V2E={e['id']:e for e in L(f'{V2}/enclosures.jsonl')}
def sg(lo,hi): return 1 if lo>0 else -1 if hi<0 else 0
DOM=(F(1,4),F(1),F(1),F(7))
PADS={'Z1':[('1/128','1/32'),('1/256','1/64')],'Z2':[('1/64','1/16'),('1/128','1/32'),('1/256','1/64')],'D1':[('1/128','1/32'),('1/256','1/64')],'D2':[('1/128','1/32'),('1/256','1/64')]}
v2boxes=L(f'{V2}/boxes.jsonl'); v2pend=[p for p in L(f'{V2}/pending.jsonl') if 'box' in p]
out={}
for q in ('Z1','Z2','D1','D2'):
    o=C.Counter(); base=f'{V3}/work/main/{q}'
    I={x['id']:x for x in L(f'{base}/integrals.jsonl')}
    sup={c['id']:bx(c['box']) for c in V2CH.values() if c['quantity']==q and c['status']=='CHART'}
    sh=L(f'{V3}/work/local/proof/intersections.jsonl')[0]
    if q in sh['pair'] and sh['common_chart']:
        cc=sh['common_chart']; fv=[[sg(r(a),r(b)) for a,b in f['values']] for f in cc['faces']]
        LI={x['id']:x for x in L(f'{V3}/work/local/proof/integrals.jsonl')}
        tv=[sg(*map(r,LI[t]['interval'])) for t in cc['transverse']]
        o['common_chart_ok']=int(fv==[[1,1],[-1,-1]] and tv==[-1,-1] and sg(*map(r,sh['difference']))!=0)
        sup[sh['id']]=bx(cc['box'])
    # v2 chart validity re-check (faces strict opposite, transverse strict = direction)
    for cid in [k for k in sup if k in V2CH]:
        c=V2CH[cid]; f0,f1=[sg(*map(r,V2E[f]['interval'])) for f in c['faces']]; t=sg(*map(r,V2E[c['transverse']]['interval']))
        o['v2chart_bad']+= not(f0*f1==-1 and t==c['direction']!=0)
    for c in L(f'{base}/charts.jsonl'):
        old=V2CH[c['parent']]; a=old['cross']; ob=bx(old['box']); nb=bx(c['box'])
        opts=[]
        for pad in PADS[q]:
            p=F(pad[a]); t=list(ob); t[2*a]=max(DOM[2*a],ob[2*a]-p); t[2*a+1]=min(DOM[2*a+1],ob[2*a+1]+p); opts.append(tuple(t))
        o['ext_unplanned']+= nb not in opts
        d=I[c['derivative']]; o['ext_deriv_box_or_axis_bad']+= not(bx(d['box'])==nb and d['derivative']==a+1)
        s=sg(*map(r,d['interval']))
        if c['status']=='CHART':
            o['ext_chart']+=1; o['ext_sign_bad']+= s!=old['direction']; sup[c['id']]=nb
        else: o['ext_open']+=1
    # covered leaves: inside union of their supports; equals set of v2 open leaves
    v2open={p['node']:bx(p['box']) for p in v2pend if p['quantity']==q}
    v2open.update({x['node']:bx(x['box']) for x in v2boxes if x['quantity']==q and x['status']=='UNRESOLVED'})
    seen=set()
    for b in L(f'{base}/boxes.jsonl'):
        if b['record']!='residual': continue
        if b['origin']==b['node']: seen.add(b['node'])
        if b['status']=='COVERED':
            box=bx(b['box']); cs=[sup[s] for s in b['supports'] if s in sup]; o['missing_support']+= len(cs)!=len(b['supports'])
            ys=sorted({box[0],box[1]}|{v for c in cs for v in c[:2] if box[0]<v<box[1]}); zs=sorted({box[2],box[3]}|{v for c in cs for v in c[2:] if box[2]<v<box[3]})
            ok=all(any(c[0]<=y0 and y1<=c[1] and c[2]<=z0 and z1<=c[3] for c in cs) for y0,y1 in zip(ys,ys[1:]) for z0,z1 in zip(zs,zs[1:]))
            o['covered']+=1; o['cover_gap']+= not ok
        else: o['status_'+b['status']]+=1
    o['v2_open']=len(v2open); o['v3_roots_match_v2_open']=int(seen==set(v2open))
    out[q]=dict(o)
for q,o in out.items(): print(q,o)
