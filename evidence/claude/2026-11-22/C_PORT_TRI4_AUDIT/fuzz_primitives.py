"""Extra check (outside the fixed plan): bitwise fuzz of the native interval primitives against the pure-numpy
reference fiv.I, on random bit patterns and special values.  Usage: fuzz_primitives.py <ref GER2> <native GER2> <out.json>
DIAGNOSTIC_ONLY."""
import importlib.util, json, math, struct, sys
import numpy as np
ref_root, nat_root, outp = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("ref_fiv", ref_root + "/geoenclosereader/fiv.py"); ref_fiv = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref_fiv)
sys.path.insert(0, nat_root)
from geoenclosereader import fiv as nat_fiv, tri as nat_tri
spec = importlib.util.spec_from_file_location("ref_tri_poly", ref_root + "/geoenclosereader/fiv.py")
RI, NI = ref_fiv.I, nat_fiv.I
assert RI.__mul__ is not NI.__mul__
rng = np.random.default_rng(20261122)
SPECIAL = np.array([0.0, -0.0, 5e-324, -5e-324, 2.2250738585072014e-308, -2.2250738585072014e-308, 1.0, -1.0, 1 + 2**-52, 0.5, 1e-200, -1e-200,
                    1e200, -1e200, 1.7976931348623157e308, -1.7976931348623157e308, np.inf, -np.inf, np.nan, 3.0, 1/3, -1/3, 2**-1074*3])


def sample(n, mode):
    if mode == "bits":
        x = rng.integers(0, 2**64, size=n, dtype=np.uint64).view(np.float64)
    elif mode == "moderate":
        x = rng.standard_normal(n)*10.0**rng.integers(-8, 9, size=n)
    elif mode == "unit":
        x = rng.random(n)*rng.choice([1.0, -1.0, 1e-3, 1e-12], size=n)
    else:
        x = rng.choice(SPECIAL, size=n)
    return x


def interval(n, mode):
    a, b = sample(n, mode), sample(n, mode)
    lo, hi = np.fmin(a, b), np.fmax(a, b)            # NaN stays only if both are NaN
    nanmask = rng.random(n) < (0.02 if mode in ("special", "bits") else 0.0)
    lo = np.where(nanmask, np.nan, lo)
    return lo, hi


def same(x, y):
    x = np.asarray(x, np.float64); y = np.asarray(y, np.float64)
    if x.shape != y.shape: return False, None
    xb, yb = x.view(np.uint64), y.view(np.uint64)
    ok = (xb == yb) | (np.isnan(x) & np.isnan(y))
    return bool(ok.all()), (None if ok.all() else int(np.argmin(ok)))


res = {}; fails = []
def run(name, f, n_arrays, need_two=True, filt=None):
    cnt = 0; exc = 0
    for mode in ("moderate", "unit", "special", "bits"):
        for rep in range(n_arrays):
            n = int(rng.choice([1, 7, 64, 1000]))
            al, ah = interval(n, mode); bl, bh = interval(n, mode)
            if filt: al, ah, bl, bh = filt(al, ah, bl, bh)
            outs = []
            for I in (RI, NI):
                try:
                    with np.errstate(all="ignore"):
                        r = f(I(al.copy(), ah.copy()), I(bl.copy(), bh.copy()))
                    outs.append(("ok", r.lo, r.hi))
                except Exception as e:
                    outs.append(("exc", type(e).__name__, str(e)))
            cnt += 1
            if outs[0][0] != outs[1][0]:
                fails.append(dict(op=name, mode=mode, ref=str(outs[0][:2]), nat=str(outs[1][:2]))); continue
            if outs[0][0] == "exc":
                exc += 1
                if outs[0][1:] != outs[1][1:]: fails.append(dict(op=name, mode=mode, ref=outs[0][1:], nat=outs[1][1:]))
                continue
            for k in (1, 2):
                ok, i = same(outs[0][k], outs[1][k])
                if not ok:
                    fails.append(dict(op=name, mode=mode, end="lo" if k == 1 else "hi", a=[float(al.flat[i % al.size]), float(ah.flat[i % ah.size])],
                                      b=[float(bl.flat[i % bl.size]), float(bh.flat[i % bh.size])], ref=float(np.ravel(outs[0][k])[i]), nat=float(np.ravel(outs[1][k])[i])))
    res[name] = dict(arrays=cnt, both_raised=exc)

posb = lambda al, ah, bl, bh: (al, ah, np.abs(bl) + 1e-300, np.abs(bl) + np.abs(bh) + 1e-300)
nonneg = lambda al, ah, bl, bh: (np.abs(al), np.abs(al) + np.abs(ah), bl, bh)
run("add", lambda a, b: a + b, 300); run("sub", lambda a, b: a - b, 300); run("mul", lambda a, b: a*b, 300)
run("div_any", lambda a, b: a/b, 200); run("div_positive", lambda a, b: a/b, 200, filt=posb)
run("div_negative", lambda a, b: a/(-b), 100, filt=posb)
run("sq", lambda a, b: a.sq(), 300); run("sqrt_any", lambda a, b: a.sqrt(), 150); run("sqrt_nonneg", lambda a, b: a.sqrt(), 200, filt=nonneg)
run("neg", lambda a, b: -a, 100); run("scalar_mul", lambda a, b: 2*a, 100); run("scalar_add", lambda a, b: a + 0.5, 100)
run("rsub", lambda a, b: 1 - a, 100); run("rdiv_positive", lambda a, b: 1.0/b, 100, filt=posb)
run("broadcast_mul", lambda a, b: a*type(a)(b.lo.ravel()[:1], b.hi.ravel()[:1]), 100)
# fsum against math.fsum
fs = 0
for rep in range(400):
    n = int(rng.choice([1, 2, 10, 1000, 20000])); mode = ["moderate", "unit", "cancel", "tiny"][rep % 4]
    if mode == "cancel":
        x = rng.standard_normal(n)*10.0**rng.integers(-30, 31, size=n); x = np.concatenate([x, -x, rng.standard_normal(3)*1e-20]); rng.shuffle(x)
    elif mode == "tiny":
        x = rng.standard_normal(n)*1e-310
    else:
        x = sample(n, mode)
    a = RI(x.copy(), x.copy()).fsum(); b = NI(x.copy(), x.copy()).fsum(); fs += 1
    if struct.pack(">dd", float(a.lo), float(a.hi)) != struct.pack(">dd", float(b.lo), float(b.hi)):
        fails.append(dict(op="fsum", mode=mode, n=int(x.size), ref=[float(a.lo), float(a.hi)], nat=[float(b.lo), float(b.hi)]))
res["fsum"] = dict(arrays=fs)
# Horner _poly: reference algorithm with the reference I  vs  native tri._poly
from fractions import Fraction
def ref_poly(coefs, h):
    acc = ref_fiv.iv_frac(coefs[-1])
    for c in reversed(coefs[:-1]): acc = acc*h + ref_fiv.iv_frac(c)
    return acc
pc = 0
for rep in range(200):
    m = int(rng.integers(1, 62)); coefs = [Fraction(int(rng.integers(0, 10**6)), int(rng.integers(1, 10**6))) for _ in range(m)]
    n = int(rng.choice([1, 50, 2000])); lo = rng.random(n)*0.5; hi = np.minimum(lo + rng.random(n)*10.0**rng.integers(-16, -1), 0.5)
    a = ref_poly(coefs, RI(lo.copy(), hi.copy())); b = nat_tri._poly(coefs, NI(lo.copy(), hi.copy())); pc += 1
    for x, y, e in ((a.lo, b.lo, "lo"), (a.hi, b.hi, "hi")):
        ok, i = same(np.broadcast_to(x, np.shape(y)) if np.shape(x) != np.shape(y) else x, y)
        if not ok: fails.append(dict(op="poly", end=e, m=m, n=n))
res["poly"] = dict(arrays=pc)
json.dump(dict(summary=res, failures=fails[:200], n_failures=len(fails)), open(outp, "w"), indent=1)
print(json.dumps(res)); print("failures:", len(fails)); [print(f) for f in fails[:10]]
