"""Second-order interval jets (value, gradient, chosen Hessian entries), new in 0.5.0.

A jet carries enclosures of f, df/dx_i (i < n) and d2f/dx_i dx_j for the index pairs in `pairs` (i <= j).
Every pair set used here is closed under the rules below: the (i, j) entry of a product or of phi(a) needs only the
(i, j) entries and the i-th and j-th gradient entries of the arguments. Exact zeros are stored as None (sparsity).
Rules (outward intervals throughout):
  (ab)_ij  = a b_ij + b a_ij + a_i b_j + a_j b_i
  phi(a)_i = phi'(a) a_i,   phi(a)_ij = phi'(a) a_ij + phi''(a) a_i a_j
with phi', phi'' enclosed over the value interval of a (mean-value / Taylor remainder not needed: these are exact
derivative identities evaluated in interval arithmetic)."""
import numpy as np
from .fiv import I


def _add(x, y):
    if x is None: return y
    if y is None: return x
    return x + y


def _mul(x, y):
    if x is None or y is None: return None
    return x*y


def _neg(x): return None if x is None else -x


class J:
    __slots__ = ("v", "g", "h", "pairs")
    __array_priority__ = 300

    def __init__(self, v, g, h, pairs):
        self.v = v; self.g = g; self.h = h; self.pairs = pairs

    @staticmethod
    def const(x, n, pairs):
        x = x if isinstance(x, I) else I.c(x); return J(x, [None]*n, {p: None for p in pairs}, pairs)

    @staticmethod
    def var(x, i, n, pairs, one):
        g = [None]*n; g[i] = one; return J(x, g, {p: None for p in pairs}, pairs)

    def _c(self, b):
        return b if isinstance(b, J) else J.const(b, len(self.g), self.pairs)

    def __add__(a, b):
        b = a._c(b); return J(a.v + b.v, [_add(x, y) for x, y in zip(a.g, b.g)], {p: _add(a.h[p], b.h[p]) for p in a.pairs}, a.pairs)
    __radd__ = __add__

    def __neg__(a): return J(-a.v, [_neg(x) for x in a.g], {p: _neg(a.h[p]) for p in a.pairs}, a.pairs)
    def __sub__(a, b): return a + (-(a._c(b)))
    def __rsub__(a, b): return a._c(b) - a

    def __mul__(a, b):
        if not isinstance(b, J):                      # scalar / interval constant: linear
            b = b if isinstance(b, I) else I.c(b)
            return J(a.v*b, [_mul(x, b) for x in a.g], {p: _mul(a.h[p], b) for p in a.pairs}, a.pairs)
        g = [_add(_mul(a.v, y), _mul(b.v, x)) for x, y in zip(a.g, b.g)]
        h = {}
        for (i, j) in a.pairs:
            e = _add(_mul(a.v, b.h[(i, j)]), _mul(b.v, a.h[(i, j)]))
            if i == j: e = _add(e, _mul(_mul(a.g[i], b.g[i]), 2.0))
            else: e = _add(e, _add(_mul(a.g[i], b.g[j]), _mul(a.g[j], b.g[i])))
            h[(i, j)] = e
        return J(a.v*b.v, g, h, a.pairs)
    __rmul__ = __mul__

    def chain(a, val, d1, d2):
        g = [_mul(d1, x) for x in a.g]
        h = {(i, j): _add(_mul(d1, a.h[(i, j)]), _mul(d2, _mul(a.g[i], a.g[j]))) for (i, j) in a.pairs}
        return J(val, g, h, a.pairs)

    def inv(a):
        r = 1/a.v; return a.chain(r, -(r.sq()), 2*(r.sq()*r))

    def __truediv__(a, b):
        if not isinstance(b, J):
            b = b if isinstance(b, I) else I.c(b); return a*(1/b)
        return a*b.inv()

    def __rtruediv__(a, b): return a._c(b)/a

    def sq(a): return a.chain(a.v.sq(), 2*a.v, I.c(2.0))

    def sqrt(a):
        r = a.v.sqrt(); ir = 1/r; return a.chain(r, 0.5*ir, -0.25*(ir*ir.sq()))

    def clip(a, lo, hi):
        """valid only where the true value is known to lie in [lo, hi] (derivatives unchanged)."""
        return J(a.v.clip(lo, hi), a.g, a.h, a.pairs)
