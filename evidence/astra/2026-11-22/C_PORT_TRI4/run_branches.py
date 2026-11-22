import json
import time
from cases_run import HERE,F,encode,tri4
for row in json.loads((HERE/'branch_cases.json').read_text()):
    box=[[F(x) for x in pair] for pair in row['box']]
    try:
        e=getattr(tri4,row['kind'])(box,row['N'],row['grade'],row['NH'],row['lazy'])
        info=tri4.enclose.last
        obs=dict(contact=info['contact_cells']>0,
                 coarse=info['order']==1 and info['contact_cells']==0 and any(a!=b for a,b in box),
                 lazy=info['lazy_skip'],outside=False,point=all(a==b for a,b in box),
                 p0=any(F(z)!=(a+b)/2 for (a,b),z in zip(box,info['p0'])))
        outcome=encode(dict(lo=float(e.lo),hi=float(e.hi),info=info))
    except ValueError as err:
        obs=dict(outside=str(err)=='box does not meet the ball')
        outcome=dict(exception=type(err).__name__,message=str(err))
    print(json.dumps(dict(**row,observed=obs,outcome=outcome)),flush=True)
