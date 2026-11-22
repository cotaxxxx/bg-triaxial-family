"""Run the fixed cases with whichever Reader is first on PYTHONPATH.  Output: one JSON line per case."""
import json, resource, struct, sys, time
from fractions import Fraction as F
import numpy as np
from geoenclosereader import tri4
try:
    from geoenclosereader import _tape                     # present only in the C-port tree
except ImportError:
    _tape = None


def hx(x):
    return struct.pack(">d", float(x)).hex()


def norm(o):
    if isinstance(o, dict): return {str(k): norm(v) for k, v in sorted(o.items(), key=lambda kv: str(kv[0]))}
    if isinstance(o, (list, tuple)): return [norm(v) for v in o]
    if isinstance(o, (bool, np.bool_)): return bool(o)
    if isinstance(o, (int, np.integer)): return int(o)
    if isinstance(o, (float, np.floating)): return "f:" + hx(o)
    return str(o)


cases = json.load(open(sys.argv[1]))
only = set(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else None
with open(sys.argv[2], "a") as out:
    for c in cases:
        if only is not None and c["id"] not in only: continue
        box = [(F(a), F(b)) for a, b in c["box"]]
        t0 = time.perf_counter(); rec = dict(id=c["id"]); k0 = dict(_tape.stats) if _tape else None
        try:
            if c["wrap"]:
                fn = {"E3": tri4.W3, "T12": tri4.C12, "H33": tri4.H33}[c["kind"]]
                r = fn(box, c["N"], c["grade"], c["NH"], c["lazy"])
            else:
                r = tri4.enclose(c["kind"], box, c["N"], c["grade"], c["NH"], c["lazy"])
            rec.update(status="ok", lo=hx(r.lo), hi=hx(r.hi), last=norm(tri4.enclose.last))
        except Exception as e:
            rec.update(status="exception", type=type(e).__name__, msg=str(e))
        rec["seconds"] = time.perf_counter() - t0
        if _tape: rec["kernel"] = dict(simd=_tape._lib.tape_simd(), c_calls=_tape.stats["tape_calls"] - k0["tape_calls"], python_fallbacks=_tape.stats["fallback_calls"] - k0["fallback_calls"])
        rec["maxrss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 1)
        pass; rec["maxrss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, 1)
        out.write(json.dumps(rec, sort_keys=True) + "\n"); out.flush()
