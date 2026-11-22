import ctypes as ct
import itertools
import json
import math
import random
import struct
from geoenclosereader._native_port import lib,rawsum
bits=lambda x:struct.pack('>d',x).hex()
rng=random.Random(20261124)
lib.test_adjacent.argtypes=[ct.c_double,ct.c_int]
lib.test_adjacent.restype=ct.c_double
near=[0.,-0.,5e-324,-5e-324,math.inf,-math.inf,1.,-1.,float.fromhex('0x1.fffffffffffffp+1023')]
near += [struct.unpack('>d',rng.randbytes(8))[0] for _ in range(10000)]
for x in near:
    for side,d in enumerate((-math.inf,math.inf)):
        a,b=lib.test_adjacent(x,side),math.nextafter(x,d)
        assert (math.isnan(a) and math.isnan(b)) or bits(a)==bits(b)
tests=[[],[0.],[-0.],[math.inf,-math.inf],[1e308,1e308],[float('nan')]]
for seq in ([1e100,1.,-1e100],[1.,2**-53,2**-106],[1.,2**-53,-2**-106],[5e-324,-5e-324,5e-324]):
    tests.extend(itertools.permutations(seq))
for _ in range(2000):
    tests.append([math.ldexp(rng.uniform(-1,1),rng.randrange(-1074,1024)) for j in range(rng.randrange(1,151))])
def take(f,seq):
    try:return bits(f(seq))
    except (ValueError,OverflowError) as e:return [type(e).__name__,str(e)]
for seq in tests: assert take(rawsum,seq)==take(math.fsum,seq),seq
print(json.dumps(dict(nextafter=2*len(near),fsum=len(tests),mismatches=0)))
