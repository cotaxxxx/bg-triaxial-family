"""Bound temporary jet storage. Reductions and enclosure assembly stay in reference order."""
from . import tri3,tri4,_cells,_native_port
from .fiv import I
from .dual import D
from .jet import J
import numpy as np

CELLS=32768

def part(obj,sl):
    if isinstance(obj,I):
        def cut(x):return x if x.ndim==0 else x.reshape(-1)[sl]
        return I(cut(obj.lo),cut(obj.hi))
    if obj is None:return None
    if isinstance(obj,D):return D(part(obj.v,sl),[part(x,sl) for x in obj.g])
    if isinstance(obj,J):return J(part(obj.v,sl),[part(x,sl) for x in obj.g],
                                {p:part(x,sl) for p,x in obj.h.items()},obj.pairs)
    return obj

def fields(obj):
    if isinstance(obj,I): yield obj
    elif isinstance(obj,(D,J)):
        yield obj.v
        yield from (g for g in obj.g if g is not None)
        if isinstance(obj,J):yield from (h for h in obj.h.values() if h is not None)

def empty_like_result(obj,shape):
    if obj is None:return None
    if isinstance(obj,I):return I(np.empty(shape),np.empty(shape))
    g=[empty_like_result(x,shape) for x in obj.g]
    v=empty_like_result(obj.v,shape)
    if isinstance(obj,D):return D(v,g)
    return J(v,g,{p:empty_like_result(h,shape) for p,h in obj.h.items()},obj.pairs)

def make(kind,safe_mask=None):
    def kernel(mask):
        return _cells._make(kind) if mask is None else _cells._masked_make(kind,mask)
    whole=kernel(safe_mask)
    def evaluate(*args):
        # Small/scalar and non-jet calls retain a single global array pass.
        if not isinstance(args[0],J) or args[0].v.lo.size<=CELLS:return whole(*args)
        shape=args[0].v.lo.shape
        count=args[0].v.lo.size
        previous=_native_port.negative_divisions
        result=None
        for start in range(0,count,CELLS):
            sl=slice(start,min(start+CELLS,count))
            try:
                fragment=whole(*(part(a,sl) for a in args))
            except ValueError:
                # Full-array semantics determine the first exception.
                return whole(*args)
            if _native_port.negative_divisions!=previous:
                # A negative divisor on this tile might have a different
                # sign elsewhere. Reader requires uniform sign on all cells.
                return whole(*args)
            if result is None: result=empty_like_result(fragment,shape)
            for out,src in zip(fields(result),fields(fragment),strict=True):
                out.lo.reshape(-1)[sl]=src.lo
                out.hi.reshape(-1)[sl]=src.hi
        return result
    return evaluate

def install():
    tri4._make=make
    tri3._make=make
    tri4._mv_cells=_cells._mv_cells
