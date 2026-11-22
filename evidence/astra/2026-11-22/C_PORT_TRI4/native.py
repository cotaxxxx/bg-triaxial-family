"""ctypes adapter for binary64 array operations. Invoked once at import."""
import ctypes as ct
from functools import lru_cache
from pathlib import Path
import numpy as np

lib = ct.CDLL(str(Path(__file__).resolve().with_name('libtri4.so')))
ptr, size = ct.c_void_p, ct.c_size_t
lib.apply.argtypes = [ct.c_int, size, ptr, ptr, size, ptr, ptr, size, ptr, ptr]
lib.horner.argtypes = [size, ptr, ptr, size, ptr, ptr, ptr, ptr]
lib.horner.restype = None
pylib=ct.PyDLL(lib._name)
pylib.sum_iterable.argtypes=[ct.py_object,ct.POINTER(ct.c_double)]
negative_divisions=0
if not lib.nearest_mode(): raise RuntimeError("binary64 round-to-nearest required")

def contiguous(a):
    return a if a.flags.c_contiguous else np.ascontiguousarray(a)

def rawsum(a):
    a=contiguous(np.asarray(a,dtype=np.float64))
    out=ct.c_double()
    pylib.sum_iterable(memoryview(a.reshape(-1)),ct.byref(out))
    return out.value

def install():
    from geoenclosereader import fiv,tri
    I=fiv.I
    def op(code,a,b):
        b=I.c(b)
        values=[a.lo,a.hi,b.lo,b.hi]
        shape=np.broadcast_shapes(*(v.shape for v in values))
        # Stride zero for a scalar. Other broadcasts are materialized in C order.
        def data(v):
            return contiguous(v if v.size==1 or v.shape==shape else np.broadcast_to(v,shape))
        al,ah,bl,bh=map(data,values)
        if (al.size==1)!=(ah.size==1) or (bl.size==1)!=(bh.size==1):
            al,ah,bl,bh=[contiguous(np.broadcast_to(v,shape)) for v in values]
        lo=np.empty(shape);hi=np.empty_like(lo)
        status=lib.apply(code,lo.size,al.ctypes.data,ah.ctypes.data,int(al.size!=1),
                         bl.ctypes.data,bh.ctypes.data,int(bl.size!=1),lo.ctypes.data,hi.ctypes.data)
        global negative_divisions
        if status==-1:
            negative_divisions+=1
            status=0
        if status==1: raise ValueError('division by interval containing 0')
        if status==2: raise ValueError('sqrt of negative')
        if status: raise RuntimeError(status)
        return I(lo,hi)
    I.__add__=I.__radd__=lambda a,b:op(0,a,b)
    I.__sub__=lambda a,b:op(1,a,b)
    I.__mul__=I.__rmul__=lambda a,b:op(2,a,b)
    I.__truediv__=lambda a,b:op(3,a,b)
    I.sq=lambda a:op(4,a,a)
    I.sqrt=lambda a:op(5,a,a)
    I.__neg__=lambda a:op(6,a,a)
    I.fsum=lambda a:I(fiv.dn(rawsum(a.lo)),fiv.up(rawsum(a.hi)))
    @lru_cache(None)
    def coefficients(keys):
        vals=[fiv.iv_frac(v) for v in keys]
        return np.array([v.lo for v in vals]),np.array([v.hi for v in vals])
    def poly(coefs,h):
        cl,ch=coefficients(tuple(coefs))
        hl,hh=contiguous(h.lo),contiguous(h.hi)
        lo=np.empty_like(hl);hi=np.empty_like(hh)
        lib.horner(hl.size,hl.ctypes.data,hh.ctypes.data,len(cl),cl.ctypes.data,ch.ctypes.data,
                   lo.ctypes.data,hi.ctypes.data)
        return I(lo,hi)
    tri._poly=poly
