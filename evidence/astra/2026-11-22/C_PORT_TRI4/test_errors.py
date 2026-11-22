import json
import numpy as np
from cases_run import F,jobs,tri4
def probe(name,fn,expected):
    try: fn()
    except ValueError as err:
        actual=str(err)
        print(json.dumps(dict(name=name,error=type(err).__name__,message=actual)),flush=True)
        if actual!=expected:raise
    else: raise AssertionError(name)
for k,p,message in [('H33',(1,1,1,0,0),'contact cell in an interior-only kernel'),
                    ('W3',(1,1,0,0,0),'division by interval containing 0'),
                    ('H33',(1,1,1,1,0),'box does not meet the ball')]:
    box=[(F(x),F(x)) for x in p]
    probe(k+str(p),lambda:getattr(tri4,k)(box,16,0,16,False),message)
class Crossing:
    def __init__(self):
        self.calls=[]
    def __getattr__(self,name):
        op=getattr(np,name)
        if name not in ('maximum','minimum'): return op
        def call(a,b):
            if np.ndim(a)==0 and np.ndim(b)==0:
                self.calls.append(name)
                return np.asarray(float(name=='maximum'))
            return op(a,b)
        return call
proxy=Crossing()
tri4.np=proxy
k,b,n,g,nh=next(jobs())
probe('injected_empty_intersection',lambda:getattr(tri4,k)(b,n,g,nh,False),
      'INCONSISTENT: first- and second-order enclosures do not meet')
assert proxy.calls==['maximum','minimum'],proxy.calls
