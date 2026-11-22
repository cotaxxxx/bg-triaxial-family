import json
from collections import defaultdict
from time import perf_counter
from cases_run import jobs, tri4, tri2
from geoenclosereader.fiv import I

totals = defaultdict(float)
stack = []
def timed(fn, group):
    def call(*args, **kwargs):
        start=perf_counter()
        frame=[0.]
        stack.append(frame)
        try: return fn(*args,**kwargs)
        finally:
            elapsed=perf_counter()-start
            stack.pop()
            if stack: stack[-1][0]+=elapsed
            totals[group]+=elapsed-frame[0]
    return call
# Grid inclusive time: fiv occurs inside grid construction and belongs to grid.
def grid(fn):
    def call(*a,**kw):
        if stack: return fn(*a,**kw)
        old=dict(totals); t=perf_counter()
        try:return fn(*a,**kw)
        finally:
            dt=perf_counter()-t
            totals.clear();totals.update(old);totals['grid']+=dt
    return call
tri4._grid=grid(tri4._grid)
for name in ('__init__','__add__','__radd__','__neg__','__sub__','__rsub__','__mul__','__rmul__','__truediv__','__rtruediv__','sq','sqrt','clip','hull','fsum'):
    setattr(I,name,timed(getattr(I,name),'fsum' if name=='fsum' else 'array'))
seen=set()
for kind,box,n,g,h in jobs():
    if kind in seen: continue
    seen.add(kind)
    tri2._grid.clear()
    for temp in ['cold','warm']:
        totals.clear();t=perf_counter()
        try: getattr(tri4,kind)(box,n,g,h,False)
        except ValueError: pass
        dt=perf_counter()-t
        print(json.dumps(dict(kind=kind,cache=temp,elapsed=dt,**totals,control=dt-sum(totals.values()))),flush=True)
