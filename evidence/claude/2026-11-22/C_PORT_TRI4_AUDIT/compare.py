"""Compare the two result files field by field (seconds excluded) and tabulate branch coverage."""
import json, struct, sys, collections
cases = {c["id"]: c for c in json.load(open(sys.argv[1]))}
A = {r["id"]: r for r in map(json.loads, open(sys.argv[2]))}
B = {r["id"]: r for r in map(json.loads, open(sys.argv[3]))}
strip = lambda r: {k: v for k, v in r.items() if k != "seconds"}
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
        from fractions import Fraction as F
        if [F(x) for x in L["p0"]] != [(F(x) + F(y))/2 for x, y in c["box"]]: cov["p0_displaced"] += 1
        if L["used"] == 2: cov["used_second_order"] += 1
        if L["used"] == 1 and L["order"] == 2 and not L["lazy_skip"]: cov["both_computed_first_tighter"] += 1
        if c["N"]*2*c["N"] > 32768 and L["order"] == 2 and not L["lazy_skip"]: cov["tiled_jets"] += 1
    key = (c["kind"], c["N"]); sp[key][0] += A[i]["seconds"]; sp[key][1] += B[i]["seconds"]
res = dict(cases=len(ids), identical=len(ids) - len(bad), different=len(bad), coverage=dict(sorted(cov.items())),
           speed={"%s N=%d" % k: dict(python_s=round(v[0], 3), c_s=round(v[1], 3), ratio=round(v[0]/v[1], 2) if v[1] else None) for k, v in sorted(sp.items())},
           total=dict(python_s=round(sum(v[0] for v in sp.values()), 1), c_s=round(sum(v[1] for v in sp.values()), 1)), differences=bad)
json.dump(res, open(sys.argv[4], "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "differences"}, indent=1)); print("DIFFERENT:", [b[0] for b in bad])
