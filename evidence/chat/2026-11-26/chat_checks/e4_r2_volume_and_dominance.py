import json,sys,os
from fractions import Fraction as F
v=lambda x:F(int(x[0]))*F(2)**x[1]
root=sys.argv[1]
def vol(b): 
    p=F(1)
    for lo,hi in b: p*=F(hi)-F(lo)
    return p
for c in sorted(os.listdir(root)):
    d=f'{root}/{c}'; inp=json.load(open(f'{d}/input.json'))
    rb=inp.get('box') or inp.get('root',{}).get('box')
    rows=[json.loads(l) for l in open(f'{d}/r2.jsonl')]
    leaves=[json.loads(l) for l in open(f'{d}/leaves.jsonl')]; pend=[json.loads(l) for l in open(f'{d}/pending.jsonl')]
    if rb is None: rb=rows[0]['box']
    V=vol(rb); vl=sum(vol(x['box']) for x in leaves); vp=sum(vol(x['box']) for x in pend)
    # final-stage rows of boxes that were split (undecided at last stage)
    dom={'angle':0}; dom.update({a:0 for a in 's t q1 q2 a'.split()})
    ratios=[]
    for r in rows:
        R=r.get('R2',{})
        if R.get('status')!='MEASURED' or r.get('decision') not in ('SPLIT',): continue
        aw=v(R['angle_width']); pw=[v(x) for x in R['parameter_widths']]
        m=max(pw); k=['s','t','q1','q2','a'][pw.index(m)]
        if aw>=m: dom['angle']+=1
        else: dom[k]+=1
        ratios.append(float(aw/m) if m else float('inf'))
    decs={}
    for r in rows: decs[r.get('decision')]=decs.get(r.get('decision'),0)+1
    ratios.sort()
    print(f"{c:12s} leaves {float(vl/V):.4f} pending {float(vp/V):.4f} sum {float((vl+vp)/V):.4f} | split rows dominant: {dom} | angle/maxparam median {ratios[len(ratios)//2] if ratios else None:.3g} | decisions {decs}")
