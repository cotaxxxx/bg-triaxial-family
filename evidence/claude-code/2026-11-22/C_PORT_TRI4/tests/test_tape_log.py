"""Check of the run log (outside the fixed plan).  (1) normal enclosures: no fallback line.  (2) the recorder is made to
refuse `clip` (a stand-in for 'an operation the recorder does not know'), the tape cache is emptied, and the same
boxes are enclosed again: every integrand call must go back to Python, the log must name box, kind, N, NH, grade and
the reason, and the bounds and enclose.last must equal those of (1) bit for bit.
Usage: test_tape_log.py LOG.jsonl out.json      (C-port tree and src/ on PYTHONPATH)"""
import json, struct, sys
from fractions import Fraction as F
import tape_log
tape_log.install(sys.argv[1])
from geoenclosereader import tri4, _tape
hx = lambda x: struct.pack(">d", float(x)).hex()
boxes = [("E3", [(F(3, 2), F(25, 16)), (F(2), F(33, 16)), (F(1, 8), F(5, 32)), (F(1, 4), F(9, 32)), (F(1, 4), F(9, 32))], 32, 0, None, False),
         ("H33", [(F(5, 2), F(41, 16)), (F(4), F(65, 16)), (F(1, 8), F(5, 32)), (F(1, 4), F(9, 32)), (F(0), F(1, 32))], 32, 3, 32, True),
         ("T12", [(F(3, 2), F(25, 16)), (F(2), F(33, 16)), (F(27, 32), F(7, 8)), (F(7, 32), F(1, 4)), (F(3, 8), F(13, 32))], 32, 0, None, False)]


def run():
    r = []
    for b in boxes:
        e = tri4.enclose(*b); r.append((hx(e.lo), hx(e.hi), json.dumps(tri4.enclose.last, sort_keys=True, default=str)))
    return r


a = run(); t1 = dict(tape_log.totals, reasons=dict(tape_log.totals["reasons"]))
def no_clip(self, lo, hi): raise _tape.Unsupported("test: clip refused")
keep = _tape.TI.clip; _tape.TI.clip = no_clip; _tape._cache.clear()
b = run(); _tape.TI.clip = keep; _tape._cache.clear(); t2 = dict(tape_log.totals, reasons=dict(tape_log.totals["reasons"]))
lines = [json.loads(l) for l in open(sys.argv[1])]; fb = [l for l in lines if l["event"] == "fallback"]
res = dict(normal=dict(enclosures=t1["enclosures"], c_kernel_calls=t1["c_kernel_calls"], fallback_calls=t1["fallback_calls"]),
           forced=dict(enclosures=t2["enclosures"] - t1["enclosures"], c_kernel_calls=t2["c_kernel_calls"] - t1["c_kernel_calls"],
                       fallback_calls=t2["fallback_calls"] - t1["fallback_calls"], reasons=t2["reasons"]),
           fallback_lines=len(fb), lines_name_box_kind_N_NH_grade=all(all(k in l for k in ("box", "kind", "N", "NH", "grade", "reasons")) for l in fb),
           same_bounds_and_last=a == b)
json.dump(res, open(sys.argv[2], "w"), indent=1); print(res)
