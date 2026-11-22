"""Exact-mpf checkpoints for completed inner integrals at fixed outer latitudes."""
import hashlib
import json
import os
from pathlib import Path
from mpmath import mp

def pack(x):
    sign,m,e,bc=x._mpf_;return [sign,str(m),e,bc]
def unpack(v):
    s,m,e,b=v;return mp.make_mpf((s,int(m),e,b))
class Latitudes:
    def __init__(self,path,geometry,order,dps,contact):
        path.parent.mkdir(parents=True,exist_ok=True)
        identity={'geometry':[[str(l),str(h)] for l,h in geometry],'order':order,'dps':dps,
                  'contact':contact,'maxdegree':12,'method':'pure_mpmath_1.3.0_fixed_xi_v1'}
        self.fingerprint=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        self.values={};self.path=path
        if path.exists():
            # A worker can be interrupted during the final write. Ignore only a
            # trailing incomplete record; elsewhere corrupt data are rejected.
            with path.open('rb+') as f:
                while True:
                    pos=f.tell();line=f.readline()
                    if not line:break
                    if not line.endswith(b'\n'):f.truncate(pos);break
                    row=json.loads(line)
                    if row['input_sha256']!=self.fingerprint:raise ValueError('mismatched checkpoint')
                    self.values[(row['prec'],tuple(row['lat']))]=row['value']
        self.out=path.open('a',buffering=1)
    def evaluate(self,latitude,fn):
        lat=pack(latitude);key=(mp.prec,tuple(lat))
        if key in self.values:return unpack(self.values[key])
        y=fn(latitude);value=pack(y)
        row={'input_sha256':self.fingerprint,'prec':key[0],'lat':lat,'value':value}
        self.out.write(json.dumps(row,separators=(',',':'))+'\n')
        self.values[key]=value
        return y
