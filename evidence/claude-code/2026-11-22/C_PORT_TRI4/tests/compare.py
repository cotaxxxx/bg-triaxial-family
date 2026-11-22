"""Compare the two result files field by field (seconds and peak memory excluded) and tabulate branch coverage.
Usage: compare.py cases.json[,cases2.json,...] python.jsonl c.jsonl out.json"""
import json, struct, sys, collections
cases = {c["id"]: c for f in sys.argv[1].split(",") for c in json.load(open(f))}
A = {r["id"]: r for r in map(json.loads, open(sys.argv[2]))}
B = {r["id"]: r for r in map(json.loads, open(sys.argv[3]))}
strip = lambda r: {k: v for k, v in r.items() if k not in ("seconds", "maxrss_mb", "kernel")}
ids = sorted(set(A) | set(B)); bad = []; cov = collections.Counter(); sp = collections.defaultdict(lambda: [0.0, 0.0])
for i in ids:
    if i not in A or i not in B: bad.append((i, "missing in one backend")); continue
    if strip(A[i]) != strip(B[i]): bad.append((i, dict(python=strip(A[i]), c=strip(B[i]))))
    c = cases[i]; a = A[i]; cov["kind_" + c["kind"]] += 1
    if c["grade"]: cov["grade_nonzero"] += 1
    if a["status"] == "exception": cov["exception_" + a["type"] + ": " + a["msg"]] += 1
    else:
        L = a["last"]; act = sum(1 for x, y in c["box"] if x != y)
        if L["contact_cells"] > 0: cov["contact_cells"] += 1
        if L["contact_cells"] == 0 and L["order"] == 1 and act: cov["order1_no_contact_active"] += 1
        if L["lazy_skip"]: cov["lazy_skip"] += 1
        if act == 0: cov["no_active_variable"] += 1
        if L["order"] == 2: cov["order2"] += 1
        from fractions import Fraction as F
        if [F(x) for x in L["p0"]] != [(F(x) + F(y))/2 for x, y in c["box"]]: cov["p0_displaced"] += 1
        if L["used"] == 2: cov["used_second_order"] += 1
        if L["used"] == 1 and L["order"] == 2 and not L["lazy_skip"]: cov["both_computed_first_tighter"] += 1
        if c["N"]*2*c["N"] > 32768 and L["order"] == 2 and not L["lazy_skip"]: cov["tiled_jets"] += 1
    key = (c["kind"], c["N"]); sp[key][0] += A[i]["seconds"]; sp[key][1] += B[i]["seconds"]
REQ = ["contact_cells", "order1_no_contact_active", "lazy_skip", "p0_displaced", "exception_ValueError: box does not meet the ball",
       "no_active_variable", "grade_nonzero", "kind_E3", "kind_T12", "kind_H33"]
kc = [B[i].get("kernel") for i in ids if i in B and B[i].get("kernel")]
res = dict(c_kernel_calls=sum(k["c_calls"] for k in kc), python_fallbacks=sum(k["python_fallbacks"] for k in kc), peak_mb=dict(python=max(r.get("maxrss_mb", 0) for r in A.values()), c=max(r.get("maxrss_mb", 0) for r in B.values())), required_branches={k: cov.get(k, 0) for k in REQ}, all_required_branches_seen=all(cov.get(k, 0) > 0 for k in REQ), cases=len(ids), identical=len(ids) - len(bad), different=len(bad), coverage=dict(sorted(cov.items())),
           speed={"%s N=%d" % k: dict(python_s=round(v[0], 3), c_s=round(v[1], 3), ratio=round(v[0]/v[1], 2) if v[1] else None) for k, v in sorted(sp.items())},
           total=dict(python_s=round(sum(v[0] for v in sp.values()), 1), c_s=round(sum(v[1] for v in sp.values()), 1)), differences=bad)
json.dump(res, open(sys.argv[4], "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "differences"}, indent=1)); print("DIFFERENT:", [b[0] for b in bad])
