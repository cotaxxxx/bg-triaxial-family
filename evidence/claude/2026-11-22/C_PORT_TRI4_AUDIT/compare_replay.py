"""Compare replay records of several backends field by field (seconds excluded); tabulate grid and enclosure time.
Usage: compare_replay.py out.json name1=file1 name2=file2 ..."""
import json, sys, collections
B = {}
for a in sys.argv[2:]:
    n, f = a.split("=", 1); B[n] = {r["id"]: r for r in map(json.loads, open(f))}
names = list(B); ref = names[0]; strip = lambda r: {k: v for k, v in r.items() if k != "seconds"}
ids = sorted(set().union(*[set(B[n]) for n in names])); bad = []
for i in ids:
    for n in names[1:]:
        if i not in B[ref] or i not in B[n]: bad.append((i, n, "missing")); continue
        if strip(B[ref][i]) != strip(B[n][i]): bad.append((i, n, dict(ref=strip(B[ref][i]), other=strip(B[n][i]))))
enc = [i for i in ids if i in B[ref] and not B[ref][i].get("end")]
tot = {n: dict(grid_s=round(sum(B[n][i]["seconds"]["grid"] for i in enc if i in B[n]), 2),
               enclose_s=round(sum(B[n][i]["seconds"]["enclose"] for i in enc if i in B[n]), 2)) for n in names}
for n in names: tot[n]["total_s"] = round(tot[n]["grid_s"] + tot[n]["enclose_s"], 2)
R = B[ref]; cov = collections.Counter()
for i in enc:
    r = R[i]; L = r["last"]; cov["N=%d" % r["N"]] += 1; cov["grade=%d" % r["grade"]] += 1; cov["kind_" + r["kind"]] += 1
    cov["grid_fresh"] += r["grid_fresh"]; cov["lazy_skip"] += bool(L["lazy_skip"]); cov["order=%s" % L["order"]] += 1
    cov["contact_cells>0"] += L["contact_cells"] > 0
rows = [dict(id=i, kind=R[i]["kind"], N=R[i]["N"], grade=R[i]["grade"], order=R[i]["last"]["order"], grid_fresh=R[i]["grid_fresh"],
             **{n + "_grid_s": round(B[n][i]["seconds"]["grid"], 2) for n in names if i in B[n]},
             **{n + "_enclose_s": round(B[n][i]["seconds"]["enclose"], 2) for n in names if i in B[n]}) for i in enc]
res = dict(backends=names, records=len(ids), enclosures=len(enc), different=len(bad), coverage=dict(sorted(cov.items())), totals=tot,
           ends=[strip(R[i]) for i in ids if i in R and R[i].get("end")], rows=rows, differences=bad)
json.dump(res, open(sys.argv[1], "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("rows", "differences", "ends")}, indent=1)); print("DIFFERENT:", [(b[0], b[1]) for b in bad])
