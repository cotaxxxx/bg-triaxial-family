"""Collect the outcome of PLAN_C_PORT.md from a work directory into results/SUMMARY.json (no judgement beyond the
plan's own conditions).  Usage: evaluate.py WORKDIR TESTS_DIR CHAT_REPRO_DIR out.json"""
import json, re, statistics, subprocess, sys
from pathlib import Path
W, T, R = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out = {}
rd = lambda f: [json.loads(l) for l in open(f)]


def cat(names, dst):
    with open(W/dst, "w") as o:
        for n in names: o.write(open(W/n).read())


# test A (228 cases) and test E (scalar build, 151 cases)
cat(["py_A.jsonl", "py_A2.jsonl", "py_A3.jsonl", "py_A3s.jsonl"], "A_python.jsonl"); cat(["c_A.jsonl", "c_A2.jsonl", "c_A3.jsonl", "c_A3s.jsonl"], "A_c.jsonl")
cs = ",".join(str(T/x) for x in ("cases_A.json", "cases_A3_audit.json", "cases_A3_audit_supp1.json"))
subprocess.run([sys.executable, str(T/"compare.py"), cs, str(W/"A_python.jsonl"), str(W/"A_c.jsonl"), str(W/"compare_A.json")], check=True, stdout=subprocess.DEVNULL)
a = json.load(open(W/"compare_A.json"))
out["A"] = dict(cases=a["cases"], identical=a["identical"], different=a["different"], required_branches=a["required_branches"],
                all_required_branches_seen=a["all_required_branches_seen"], c_kernel_calls=a["c_kernel_calls"], python_fallbacks=a["python_fallbacks"],
                coverage=a["coverage"], A1=a["identical"] == a["cases"] == 228, A2=a["all_required_branches_seen"], A3=a["python_fallbacks"] == 0)
ids4 = set(range(4000, 4018))
with open(W/"E_python.jsonl", "w") as o:
    for r in rd(W/"py_A3.jsonl") + rd(W/"py_A3s.jsonl") + [r for r in rd(W/"py_A.jsonl") if r["id"] in ids4]: o.write(json.dumps(r) + "\n")
cat(["cs_A3.jsonl", "cs_A3s.jsonl", "cs_A4.jsonl"], "E_c_scalar.jsonl")
subprocess.run([sys.executable, str(T/"compare.py"), cs, str(W/"E_python.jsonl"), str(W/"E_c_scalar.jsonl"), str(W/"compare_E.json")], check=True, stdout=subprocess.DEVNULL)
e = json.load(open(W/"compare_E.json")); simd = {r["kernel"]["simd"] for r in rd(W/"E_c_scalar.jsonl")}
out["E"] = dict(cases=e["cases"], identical=e["identical"], different=e["different"], python_fallbacks=e["python_fallbacks"], simd_width=sorted(simd), ok=e["identical"] == e["cases"] == 151 and simd == {1})
# test B
keys = ("leaf_sha256", "leaves", "evals"); more = ("status", "used2", "lazy_skips", "maxdepth", "min_leaf_lo", "skipped", "remaining")
B = []
for i in (0, 1):
    chat = rd(R/f"lazy_{i}.jsonl")[0]; py = rd(W/f"tree_py_{i}.jsonl")[0]; c = rd(W/f"tree_c_{i}.jsonl")[0]
    B.append(dict(tree=i, kind=c["kind"], cell=c["cell"], chat_record={k: chat[k] for k in keys}, python_here={k: py[k] for k in keys + more}, c_here={k: c[k] for k in keys + more},
                  c_equals_chat_record=all(c[k] == chat[k] for k in keys), c_equals_python_here=all(c[k] == py[k] for k in keys + more),
                  sec=dict(chat_record=chat["sec"], python_here=py["sec"], c_here=c["sec"])))
out["B"] = dict(trees=B, ok=all(b["c_equals_chat_record"] and b["c_equals_python_here"] for b in B))
# test C
names = ["selftest_tri", "selftest_tri2", "selftest_tri3", "selftest_tri4", "selftest_lazy", "selftest_examples"]; C = []
strip = lambda s: re.sub(r"\btime \d+(?:\.\d+)?|\d+\.\d+ ?s\b|\d+\.\d+ sec\w*|[0-9.]+ ?ms\b|\(\d+\.\d+s\)", "<t>", s)
for n in names:
    c = open(W/"st_c"/f"{n}.out").read(); p = open(W/"st_py"/f"{n}.out").read()
    C.append(dict(test=n, c_failures_0="FAILURES 0" in c and "exit 0" in c, python_failures_0="FAILURES 0" in p, same_output_apart_from_times=strip(c) == strip(p), identical_output=c == p))
out["C"] = dict(tests=C, ok=all(x["c_failures_0"] for x in C))
# test D
D = {}
for v in ("avx2", "scalar"):
    d = json.load(open(W/f"blocks_{v}.json")); D[v] = dict(simd=d["simd"], checks=d["checks"], not_identical=d["not_identical"], fallbacks=d["fallbacks"],
                                                             arrays=sum(r["arrays"] for r in d["rows"]), kernel_calls=sum(r["kernel_calls"] for r in d["rows"]))
out["D"] = dict(builds=D, ok=all(x["not_identical"] == 0 for x in D.values()) and D["avx2"]["simd"] == 4 and D["scalar"]["simd"] == 1)
out["overall_all_conditions_met"] = bool(out["A"]["A1"] and out["A"]["A2"] and out["A"]["A3"] and out["B"]["ok"] and out["C"]["ok"] and out["D"]["ok"] and out["E"]["ok"])
# speed and memory
bp, bc = rd(W/"bench_py.jsonl"), rd(W/"bench_c.jsonl")
out["bench_v60"] = dict(python_s=[r["sec"] for r in bp], c_s=[r["sec"] for r in bc], python_median_s=statistics.median(r["sec"] for r in bp), c_median_s=statistics.median(r["sec"] for r in bc),
                        python_maxrss_mb=max(r["maxrss_mb"] for r in bp), c_maxrss_mb=max(r["maxrss_mb"] for r in bc),
                        same_values=all(r["h33"] == bp[0]["h33"] and r["w3"] == bp[0]["w3"] for r in bp + bc))
pa, ca = {r["id"]: r for r in rd(W/"py_A2.jsonl")}, {r["id"]: r for r in rd(W/"c_A2.jsonl")}
cases = {c["id"]: c for c in json.load(open(T/"cases_A.json"))}
out["A2_chat_box"] = [dict(id=i, N=cases[i]["N"], NH=cases[i]["NH"], python_s=round(pa[i]["seconds"], 1), c_s=round(ca[i]["seconds"], 1), ratio=round(pa[i]["seconds"]/ca[i]["seconds"], 2),
                           python_maxrss_mb=pa[i]["maxrss_mb"], c_maxrss_mb=ca[i]["maxrss_mb"]) for i in sorted(pa)]
allp = {r["id"]: r for r in rd(W/"A_python.jsonl")}; allc = {r["id"]: r for r in rd(W/"A_c.jsonl")}
out["A_total_seconds"] = dict(python=round(sum(r["seconds"] for r in allp.values()), 1), c=round(sum(r["seconds"] for r in allc.values()), 1))
out["profile"] = json.load(open(W/"profile.json"))
json.dump(out, open(sys.argv[4], "w"), indent=1)
print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk in ("ok", "A1", "A2", "A3", "identical", "cases", "python_fallbacks", "python_median_s", "c_median_s")}) for k, v in out.items() if k != "profile"}, indent=1)[:3000])
