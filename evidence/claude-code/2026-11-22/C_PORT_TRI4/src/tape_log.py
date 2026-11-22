"""tape_log.py -- optional run log for the C-port tree (Issue #1, point 3).  It does not touch the computation.

    import tape_log; tape_log.install("out/tape_log.jsonl")        # after geoenclosereader is importable

or, without editing a runner:   python3 run_with_log.py LOG READER_DIR SCRIPT [script arguments...]

What is written (JSON lines, appended):
  * one line  {"event": "fallback", ...}  for every tri4.enclose call during which at least one integrand call went
    back to the original Python function: kind, box, N, NH, grade, lazy, number of C-kernel calls, number of
    fallbacks, and the reasons with their counts.  The enclosure itself is still computed -- by the original
    Python function -- so a fallback is a loss of speed, not a change of value or of a sign decision.
  * one line  {"event": "summary", ...}  at exit: enclosures, exceptions, C-kernel calls, recordings, fallbacks in
    total and by reason, enclosures with a fallback, fallbacks that happened outside tri4.enclose, kernel build.
tri4.enclose is replaced by a pass-through wrapper; `tri4.enclose.last` keeps working because the Reader assigns it
through the module-level name.  Claude Code, 2026-11-22.  DIAGNOSTIC_ONLY."""
import atexit, inspect, json

totals = None


def install(path):
    global totals
    from geoenclosereader import tri4, _tape
    orig = tri4.enclose; sig = inspect.signature(orig); out = open(path, "a")
    totals = dict(enclosures=0, exceptions=0, c_kernel_calls=0, fallback_calls=0, enclosures_with_fallback=0, reasons={})
    base = dict(c=_tape.stats["tape_calls"], f=_tape.stats["fallback_calls"])

    def enclose(*a, **k):
        s = _tape.stats; c0, f0, r0 = s["tape_calls"], s["fallback_calls"], dict(s["unsupported"]); ok = False
        try:
            r = orig(*a, **k); ok = True; return r
        finally:
            dc, df = s["tape_calls"] - c0, s["fallback_calls"] - f0
            totals["enclosures"] += 1; totals["exceptions"] += not ok; totals["c_kernel_calls"] += dc; totals["fallback_calls"] += df
            if df:
                b = sig.bind(*a, **k); b.apply_defaults(); p = b.arguments
                rs = {key: v - r0.get(key, 0) for key, v in s["unsupported"].items() if v != r0.get(key, 0)}
                for key, v in rs.items(): totals["reasons"][key] = totals["reasons"].get(key, 0) + v
                totals["enclosures_with_fallback"] += 1
                out.write(json.dumps(dict(event="fallback", kind=p["kind"], box=[[str(x), str(y)] for x, y in p["box"]], N=p["N"], NH=p["NH"],
                                          grade=p["grade"], lazy=p["lazy"], raised_exception=not ok, c_kernel_calls=dc, fallback_calls=df, reasons=rs)) + "\n"); out.flush()
    tri4.enclose = enclose

    def summary():
        s = _tape.stats
        out.write(json.dumps(dict(event="summary", **totals, recordings=s["recorded"], all_c_kernel_calls=s["tape_calls"] - base["c"],
                                  all_fallback_calls=s["fallback_calls"] - base["f"], all_reasons=dict(s["unsupported"]),
                                  fallbacks_outside_enclose=s["fallback_calls"] - base["f"] - totals["fallback_calls"],
                                  kernel_simd=_tape._lib.tape_simd(), tape_enabled=bool(_tape.enabled))) + "\n"); out.flush()
    atexit.register(summary)
