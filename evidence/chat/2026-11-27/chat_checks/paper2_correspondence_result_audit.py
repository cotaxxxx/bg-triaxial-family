"""chat: independent re-read of the Paper II correspondence result (exact rationals, no producer code).
usage: python3 -I this.py SUPPORT.jsonl V2_RESULT_DIR V3_RESULT_DIR RESULT_DIR"""
import json,sys,collections as C
from fractions import Fraction as F
SUP,V2,V3,R=sys.argv[1:5]
def r(v): return F(int(v['n']))*(F(2)**v['e'] if 'e' in v else F(1,int(v['d'])))
TARGETS={'Z1':('Az','By'),'Z2':('Az','Bx'),'D1':('Ny','Jyx','Jyz'),'D2':('Nx','Jxy','Jxz')}
EXPECTED={'Az':1,'By':-1,'Bx':-1,'Ny':-1,'Nx':-1,'Jyx':1,'Jxy':1,'Jyz':1,'Jxz':1}
E2={e['id']:e for e in map(json.loads,open(V2+'/enclosures.jsonl'))}
L3={x['id']:x for x in map(json.loads,open(V3+'/work/local/proof/integrals.jsonl'))}
sh=[json.loads(l) for l in open(V3+'/work/local/proof/intersections.jsonl')][0]
bpT={L3[t]['quantity']:tuple(map(r,L3[t]['interval'])) for t in sh['common_chart']['transverse']}
def sg(v): return 1 if v[0]>0 else -1 if v[1]<0 else 0
def key(n,d,box,st): return '|'.join([n,str(d),*map(str,box),str(st)])
def mul(x,y):
    v=[a*b for a in x for b in y]; return min(v),max(v)
tot=C.Counter(); worst={}
for line in open(SUP):
    band=json.loads(line); q=band['q']; c=band['cross']; b=1-c; box0=tuple(map(F,band['box']))
    if band['id'].startswith('bp.'): Ht=bpT[q]
    else:
        e=E2[band['df']]; Ht=tuple(map(r,e['interval'])); assert e['derivative']==c+1 and tuple(map(r,e['box']))==box0
    assert sg(Ht)==band['direction']!=0
    for name in TARGETS[q]:
        fn=band['id']+'_'+name+'.json'; sc=json.load(open(f'{R}/scan/{fn}'))
        assert (sc['chart'],sc['q'],sc['name'],sc['phase'])==(band['id'],q,name,'scan')
        data=sc
        if any(x['status']!='EXPECTED' for x in sc['leaves']):
            data=json.load(open(f'{R}/isolate/{fn}')); assert (data['chart'],data['name'],data['phase'])==(band['id'],name,'isolate'); tot['isolated']+=1
        raw={k:tuple(map(F,v)) for k,v in data['raw'].items()}
        cover=F(0)
        for leaf in data['leaves']:
            tot['leaves']+=1; assert leaf['status']=='EXPECTED' and leaf['sign']==EXPECTED[name],(fn,leaf)
            def contract(cur):
                # independent replay of the transverse interval-Newton contraction (keeps the certified graph)
                for _ in range(3):
                    old=cur[2*c:2*c+2]; m=(old[0]+old[1])/2; pt=list(cur); pt[2*c]=pt[2*c+1]=m
                    h=raw[key(q,0,tuple(pt),1024)]; quo=mul(h,(1/Ht[1],1/Ht[0])); new=(max(old[0],m-quo[1]),min(old[1],m-quo[0]))
                    assert new[0]<=new[1],(fn,'graph lost'); nb=list(cur); nb[2*c],nb[2*c+1]=new; cur=tuple(nb)
                    if new[1]-new[0]>=(old[1]-old[0])*F(3,4): break
                return cur
            def signed_direct(cur):
                for st in (64,256):
                    g=raw.get(key(name,0,cur,st))
                    if g is not None and sg(g): return g
                return None
            cur=box0
            for ch in leaf['path']:
                # every ancestor was undecided: it was contracted, then its base was halved
                assert signed_direct(cur) is None
                cur=contract(cur); assert sg(raw[key(name,0,cur,1024)])==0
                lo,hi=cur[2*b:2*b+2]; m=(lo+hi)/2; nb=list(cur); nb[2*b],nb[2*b+1]=(lo,m) if ch=='0' else (m,hi); cur=tuple(nb)
            cover+=F(1,2**len(leaf['path']))
            lb=tuple(map(F,leaf['box']))
            g=signed_direct(cur)
            if g is not None:
                assert lb==cur; tot['direct']+=1
            else:
                cur=contract(cur); assert lb==cur,(fn,leaf['path'],'contracted box mismatch')
                g=raw[key(name,0,lb,1024)]; tot['contracted']+=1
            assert box0[2*c]<=lb[2*c] and lb[2*c+1]<=box0[2*c+1] and box0[2*b]<=lb[2*b] and lb[2*b+1]<=box0[2*b+1]
            assert sg(g)==EXPECTED[name],(fn,leaf['path'],g)
            margin=min(abs(g[0]),abs(g[1])); k=(q,name)
            if k not in worst or margin<worst[k][0]: worst[k]=(margin,band['id'],leaf['path'],[float(x) for x in lb],(float(g[0]),float(g[1])))
        assert cover==1,(fn,'base not tiled'); tot['tasks']+=1
print(dict(tot))
for k,v in sorted(worst.items()): print(k,'smallest |G| bound %.4g'%float(v[0]),v[1],'path',repr(v[2]),'box',['%.5f'%x for x in v[3]],'G in [%.5f, %.5f]'%v[4])
