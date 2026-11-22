"""Time the two original V60 calls separately inside their original cold sequence."""
import json
import runpy
import sys
from pathlib import Path
from time import perf_counter
bench,reader=sys.argv[1:]
sys.path.insert(0,reader)
from geoenclosereader import tri4
def measure(kind,fn):
    def call(*args,**kwargs):
        start=perf_counter()
        result=fn(*args,**kwargs)
        print(json.dumps({'kind':kind,'sec':perf_counter()-start,'lo':float(result.lo).hex(),'hi':float(result.hi).hex()}),flush=True)
        return result
    return call
for k in ('H33','W3'):setattr(tri4,k,measure(k,getattr(tri4,k)))
sys.argv=[bench,reader]
runpy.run_path(bench,run_name='__main__')
