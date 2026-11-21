"""Vectorized outward-rounded interval arithmetic on IEEE binary64 (numpy), new in 0.3.0.

Each +, -, *, /, sqrt in numpy is correctly rounded (round-to-nearest), so the exact result of the operation on
the float endpoints lies within one ulp of the computed value; every result endpoint is moved one ulp outward with
nextafter. Transcendental values (trig at cell endpoints, pi, series coefficients) are never taken from libm: they
come from mpmath at 40 digits or from exact rationals and are rounded outward with `from_mp` / `from_frac`.
Sums of many terms use math.fsum (exact sum, one rounding) on each endpoint array, then one ulp outward."""
import math
import numpy as np
from fractions import Fraction
from mpmath import mp, mpf
mp.dps = 40
NINF, PINF = -np.inf, np.inf
dn = lambda x: np.nextafter(x, NINF)
up = lambda x: np.nextafter(x, PINF)


class I:
    __slots__ = ("lo", "hi")
    __array_priority__ = 100

    def __init__(self, lo, hi=None):
        self.lo = np.asarray(lo, dtype=np.float64); self.hi = np.asarray(lo if hi is None else hi, dtype=np.float64)

    @staticmethod
    def c(x):
        return x if isinstance(x, I) else I(x, x)          # only for exactly representable floats

    def __add__(a, b): b = I.c(b); return I(dn(a.lo + b.lo), up(a.hi + b.hi))
    __radd__ = __add__
    def __neg__(a): return I(-a.hi, -a.lo)
    def __sub__(a, b): b = I.c(b); return I(dn(a.lo - b.hi), up(a.hi - b.lo))
    def __rsub__(a, b): return I.c(b) - a

    def __mul__(a, b):
        b = I.c(b); p = np.stack([a.lo*b.lo, a.lo*b.hi, a.hi*b.lo, a.hi*b.hi])
        return I(dn(p.min(0)), up(p.max(0)))
    __rmul__ = __mul__

    def __truediv__(a, b):
        b = I.c(b)
        if not (np.all(b.lo > 0) or np.all(b.hi < 0)): raise ValueError("division by interval containing 0")
        return a*I(dn(1.0/b.hi), up(1.0/b.lo))
    def __rtruediv__(a, b): return I.c(b)/a

    def sq(a):
        lo = np.where(a.lo >= 0, a.lo*a.lo, np.where(a.hi <= 0, a.hi*a.hi, 0.0))
        hi = np.maximum(a.lo*a.lo, a.hi*a.hi)
        return I(np.where(lo > 0, dn(lo), 0.0), up(hi))

    def sqrt(a):
        if np.any(a.lo < 0): raise ValueError("sqrt of negative")
        return I(np.maximum(dn(np.sqrt(a.lo)), 0.0), up(np.sqrt(a.hi)))

    def clip(a, lo, hi):
        """Intersect with [lo, hi]; valid only where the true value is known to lie in [lo, hi]."""
        return I(np.clip(a.lo, lo, hi), np.clip(a.hi, lo, hi))

    def hull(a, b): return I(np.minimum(a.lo, b.lo), np.maximum(a.hi, b.hi))
    def where(mask, a, b): return I(np.where(mask, a.lo, b.lo), np.where(mask, a.hi, b.hi))

    def fsum(a):
        return I(dn(math.fsum(a.lo.ravel().tolist())), up(math.fsum(a.hi.ravel().tolist())))

    def __repr__(self): return f"I({self.lo}, {self.hi})"


def from_mp(x):
    x = mpf(x); f = float(x)
    return dn(f), up(f)                      # float(x) is within half an ulp of x


def from_frac(q):
    q = Fraction(q); f = float(q)            # correctly rounded
    return (dn(f) if Fraction(f) > q else f), (up(f) if Fraction(f) < q else f)


def iv_frac(a, b=None):
    lo, _ = from_frac(a); _, hi = from_frac(a if b is None else b); return I(lo, hi)


def iv_mp_array(vals):
    lo = np.array([from_mp(v)[0] for v in vals]); hi = np.array([from_mp(v)[1] for v in vals]); return I(lo, hi)
