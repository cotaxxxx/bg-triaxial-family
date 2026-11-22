import argparse
import json
import math
import os
import resource
import struct
import time
from fractions import Fraction as F
from pathlib import Path
from geoenclosereader import tri2, tri4

HERE = Path(__file__).resolve().parent
def jobs():
    rows = json.loads((HERE/'cases.json').read_text())
    for i, row in enumerate(rows):
        box = [[F(x) for x in pair] for pair in row['box']]
        kind = row['kind']
        log = math.log2(float(box[0][1]*box[1][1]))
        grade = min(4,max(0,round(log))) if kind == 'H33' else min(2,max(0,round(log/2))) if kind == 'W3' else 0
        for n in (64,256):
            yield kind,box,n,grade,max(16,n//2)
    box = [(F(a),F(a)+F(w)) for a,w in [('53/20','11/160'),('43/8','5/32'),('27/32','1/64'),('7/32','1/128'),('0','1/1024')]]
    for n in (256,512):
        for nh in (128,256,512):
            yield 'H33',box,n,4,nh

def encode(x):
    if isinstance(x,float):
        return struct.pack('>d',x).hex()
    if isinstance(x,dict):
        return {str(k):encode(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):
        return [encode(v) for v in x]
    return x

def run(index, job):
    k,b,n,g,nh=job
    t=time.monotonic()
    try:
        e=getattr(tri4,k)(b,n,g,nh,False)
        outcome=encode(dict(lo=float(e.lo),hi=float(e.hi),info=tri4.enclose.last))
    except ValueError as ex:
        outcome={'exception':type(ex).__name__,'message':str(ex)}
    return dict(index=index,kind=k,box=[[str(x) for x in p] for p in b],N=n,NH=nh,grade=g,outcome=outcome,
                sec=time.monotonic()-t,rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

if __name__=='__main__':
    import sys
    for i, job in enumerate(jobs()):
        if len(sys.argv)>1 and i not in map(int,sys.argv[1:]): continue
        if len(tri2._grid)>4:tri2._grid.clear()
        print(json.dumps(run(i,job)),flush=True)
