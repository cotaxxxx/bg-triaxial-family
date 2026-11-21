"""Interval dual numbers (value + gradient, both outward-rounded intervals), for mean-value enclosures. 0.3.0."""
import numpy as np
from .fiv import I


class D:
    __slots__ = ("v", "g")
    __array_priority__ = 200

    def __init__(self, v, g):
        self.v = v; self.g = list(g)

    @staticmethod
    def const(x, n):
        x = x if isinstance(x, I) else I.c(x); z = I(np.zeros_like(x.lo)); return D(x, [z]*n)

    def _c(self, b):
        return b if isinstance(b, D) else D.const(b, len(self.g))

    def __add__(a, b): b = a._c(b); return D(a.v + b.v, [x + y for x, y in zip(a.g, b.g)])
    __radd__ = __add__
    def __neg__(a): return D(-a.v, [-x for x in a.g])
    def __sub__(a, b): b = a._c(b); return D(a.v - b.v, [x - y for x, y in zip(a.g, b.g)])
    def __rsub__(a, b): return a._c(b) - a
    def __mul__(a, b): b = a._c(b); return D(a.v*b.v, [a.v*y + b.v*x for x, y in zip(a.g, b.g)])
    __rmul__ = __mul__
    def __truediv__(a, b):
        b = a._c(b); q = a.v/b.v; return D(q, [(x - q*y)/b.v for x, y in zip(a.g, b.g)])
    def __rtruediv__(a, b): return a._c(b)/a
    def sq(a): return D(a.v.sq(), [2*a.v*x for x in a.g])
    def sqrt(a):
        r = a.v.sqrt(); return D(r, [x/(2*r) for x in a.g])
    def clip(a, lo, hi): return D(a.v.clip(lo, hi), a.g)


def chain(gd, val, dval):
    """phi(g) as a dual, given enclosures val = phi(G), dval = phi'(G) over the value interval G of g."""
    return D(val, [dval*x for x in gd.g])
