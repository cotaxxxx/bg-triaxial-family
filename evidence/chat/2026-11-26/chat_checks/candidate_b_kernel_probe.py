import sys,ctypes
from fractions import Fraction as Q
sys.path.insert(0,sys.argv[1])
import engine as E
k=E.Kernel(sys.argv[2])
def val(q,deriv,y,z,target):
    lib=k.lib
    h=lib.cb_create(q,deriv,128,0,*(str(v).encode() for v in (y,y,z,z)))
    if not h: raise k.error()
    out=E.CResult(); m=lib.cb_extend(h,target,10**9,2**63,ctypes.byref(out))
    lo=int(out.lo)*Q(2)**out.lo_exp; hi=int(out.hi)*Q(2)**out.hi_exp; lib.cb_destroy(h)
    return m,float(lo),float(hi),out.calls
for target in (64,1024):
    for qi,name in enumerate(E.QUANTITIES):
        print(target,name,val(qi,0,Q(7,10),Q(8,5),target))
print('sphere',[val(qi,0,1,1,64)[1:3] for qi in range(4)])
for qi,name in enumerate(E.QUANTITIES[:1]):
    print('d/dy',name,val(qi,1,Q(7,10),Q(8,5),1024)[1:3],'d/dz',val(qi,2,Q(7,10),Q(8,5),1024)[1:3])
