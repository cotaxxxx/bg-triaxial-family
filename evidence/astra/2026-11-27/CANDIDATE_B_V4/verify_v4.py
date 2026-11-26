"""Verify the local intersection and its inheritance from sealed rational endpoints."""

import argparse
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from ancestors import PAIR, SPEC, X, local_proof
from v2_lock import HERE, read, sha256, verify_seal
from verify_v2 import contains, difference, interval, mul_range, need, q, rect, rows, vec


CFG = SPEC["krawczyk"]
CENTRE = tuple(map(F,CFG["centre"]))
AT = (CENTRE[0],CENTRE[0],CENTRE[1],CENTRE[1])
BOXES = [tuple(map(F,v)) for v in CFG["boxes"]]
SCHEDULE = list(product(range(len(BOXES)),CFG["stages"]))


def mul_point(value,bounds):
    a,b = (value*t for t in bounds)
    return min(a,b),max(a,b)


def rng_sum(parts):
    return tuple(map(sum,zip(*parts)))


def read_native(path):
    tape = {}
    by_argument = {}
    raw_order = []
    trees = {}
    calls = 0
    for ordinal,row in enumerate(rows(path,"integrals"),1):
        f,b,d,n = row["quantity"],rect(row["box"]),row["derivative"],row["target"]
        need(f in PAIR and d in (0,1,2) and n in CFG["stages"]
             and row["precision"] == CFG["precision"] and row["trace"] is False,
             "unexpected local kernel argument")
        if b==AT and d==0:
            tree_id = 1+PAIR.index(f)
        else:
            need(b in BOXES and d in (1,2),"kernel evaluation outside a fixed Krawczyk box")
            tree_id = 3+4*BOXES.index(b)+2*PAIR.index(f)+d-1
        ident = f"v4.local.integrals.{ordinal}"
        need(row["tree"]==f"v4.local.tree.{tree_id}" and row["id"]==ident,
             "kernel row ID or tree receipt differs")
        last,target_total,finished = trees.get(tree_id,(0,0,True))
        status = row["status"]
        limit = 16+4*((n-16)//3)
        count = row["formula_calls"]
        need(status in ("COMPLETE","PENDING","INCONSISTENT") and finished and last<n
             and type(count) is int and 0<=count
             and target_total+count==row["total_calls"]<=limit,
             "native tree continuation or cell budget differs")
        if status=="COMPLETE":
            need(row["dimension"]==2 and row["cells"]==n and row["total_calls"]==limit,
                 "completed row must contain all panels of the prescribed stage")
            tape[ident] = interval(row["interval"])
            by_argument[f,b,d,n] = ident
        else:
            need("interval" not in row and
                 (row["dimension"]==2 or (status=="INCONSISTENT" and row["dimension"]==0)),
                 "unfinished tree cannot certify an endpoint")
        trees[tree_id] = n,row["total_calls"],status=="COMPLETE"
        calls += count
        raw_order.append((f,b,d,n,status))
    need(calls<=CFG["max_formula_calls"],"local total exceeded its fixed panel limit")
    return tape,by_argument,raw_order,calls


def check_krawczyk(box,value,jac,data):
    need(contains(X,box) and all(box[2*k]+box[2*k+1]==2*m for k,m in enumerate(CENTRE)),
         "candidate box is outside X or has the wrong centre")
    mid = [[(a+b)/2 for a,b in row] for row in jac]
    a,b = mid
    if a[0]*b[1] == a[1]*b[0]:
        need(data is None,"singular midpoint has a purported inverse")
        return ["SINGULAR_MIDPOINT"],None
    inverse = [vec(row,2) for row in data["C"]]
    need(len(inverse)==2 and all(
        sum(c*mid[k][j] for k,c in enumerate(inverse[i]))==int(i==j)
        for i,j in product(range(2),repeat=2)), "preconditioner is not the exact midpoint inverse")
    delta = [(box[k]-CENTRE[k//2],box[k+1]-CENTRE[k//2]) for k in (0,2)]
    error = [[difference((F(int(i==j)),)*2,
                         rng_sum([mul_point(c,jac[k][j]) for k,c in enumerate(row)]))
              for j in range(2)] for i,row in enumerate(inverse)]
    bounds = [rng_sum([(m,m),
                       *[mul_point(-c,v) for c,v in zip(row,value)],
                       *[mul_range(e,d) for e,d in zip(error_row,delta)]])
              for m,row,error_row in zip(CENTRE,inverse,error,strict=True)]
    image = (*bounds[0],*bounds[1])
    norm = max(sum(max(map(abs,e)) for e in error_row) for error_row in error)
    margins = [box[k]<image[k]<=image[k+1]<box[k+1] for k in (0,2)]
    need(rect(data["K"])==image and q(data["q"])==norm
         and data["inside"]==margins and data["contraction"] is (norm<1),
         "Krawczyk image, inclusion or contraction bound differs")
    failures = [f"K_{axis}_NOT_STRICT" for axis,good in zip(("Y","Z"),margins)
                if not good]
    if norm>=1:
        failures.append("Q_NOT_LT_ONE")
    return failures,image


def planned_raw(stop_at):
    scheduled = []
    completed_points = set()
    for i,cap in SCHEDULE[:stop_at]:
        if cap not in completed_points:
            scheduled += [(f,AT,0,cap) for f in PAIR]
            completed_points.add(cap)
        scheduled += [(f,BOXES[i],d,cap) for f in PAIR for d in (1,2)]
    return scheduled


def review_trials(path,run,primary):
    tape,by_argument,raw,calls = read_native(path)
    need(run["formula_calls"]==calls and type(run["elapsed_ns"]) is int and run["elapsed_ns"]>=0,
         "runner panel or time receipt differs")
    trial_rows = list(rows(path,"intersections"))
    status = run["status"]
    if not primary:
        need(status=="PRIMARY_UNRESOLVED" and not raw and not trial_rows,
             "native evaluations require the primary conditions")
        return None,None,[],calls
    need(status in ("RECORDED","STOPPED","INCONSISTENT") and len(trial_rows)<=len(SCHEDULE),
         "unexpected execution state or too many Krawczyk trials")
    root = None
    trial_audit = []

    def read_ref(ident,f,b,d,stage):
        need(by_argument[f,b,d,stage]==ident,"Krawczyk row references a different kernel input")
        return tape[ident]

    for k,row in enumerate(trial_rows):
        i,stage = SCHEDULE[k]
        b = BOXES[i]
        need(root is None and row["id"]==f"v4.local.intersections.{k+1}"
             and row["record"]=="krawczyk" and (row["box_index"],row["stage"])==(i,stage)
             and rect(row["box"])==b,"Krawczyk schedule differs from preregistration")
        value = [read_ref(ref,f,AT,0,stage) for f,ref in zip(PAIR,row["values"],strict=True)]
        jac = [[read_ref(ref,f,b,d,stage) for d,ref in zip((1,2),ids,strict=True)]
               for f,ids in zip(PAIR,row["jacobian"],strict=True)]
        failed,image = check_krawczyk(b,value,jac,row["test"])
        need(failed==row["failed"],"incorrect Krawczyk failure receipt")
        trial_audit.append(dict(record=row["id"],box_index=i,stage=stage,failed=failed))
        if not failed:
            root = image
    n = len(trial_rows)
    expected = planned_raw(n)
    actual = [entry[:4] for entry in raw]
    need(actual[:len(expected)]==expected
         and all(entry[-1]=="COMPLETE" for entry in raw[:len(expected)]),
         "completed trials omit or reorder their native calls")
    if status=="RECORDED":
        need(actual==expected and (root is not None or n==len(SCHEDULE)),
             "completed calculation has an extra call or ended early")
    else:
        upper = planned_raw(n+1)
        need(root is None and len(expected)<=len(actual)<=len(upper)
             and actual==upper[:len(actual)] and all(entry[-1]=="COMPLETE" for entry in raw[:-1]),
             "stopped run is not a prefix of the fixed schedule")
    return root,(trial_audit[-1] if root is not None else None),trial_audit,calls


def review_parent_and_run(v2,v3,folder):
    primary = local_proof(v2,v3)
    need(read(folder/"PRIMARY.json")==primary,"Poincare-Miranda or parent geometry receipt differs")
    main_ok = all(primary[k] for k in ("poincare_miranda","slope_contraction",
                                      "all_four_overlaps_inside_X"))
    run = read(folder/"RUN.json")
    root,witness,trial_audit,calls = review_trials(folder/"work/local",run,main_ok)
    relation = "EXACTLY_ONE_INTERIOR" if main_ok else "UNRESOLVED"
    status = "RELATION_RECORDED" if main_ok and root is not None else "PARTIAL"
    return {
        "status": status,
        "diagnostic_only": True,
        "region": SPEC["region"],
        "relations": {**primary["v3_preserved_relations"],"Z1+D2":relation},
        "X": primary["box"],
        "four_overlap_records": [row["record"] for row in primary["overlaps"]],
        "all_four_explained": main_ok,
        "primary_exists": primary["poincare_miranda"],
        "slope_product_bound": primary["slope_product_bound"],
        "krawczyk": {
            "accepted_trial": witness,
            "attempts": trial_audit,
            "unexecuted": [list(s) for s in SCHEDULE[len(trial_audit):]],
            "root_interval": None if root is None else list(map(str,root)),
        },
        "formula_calls": calls,
        "run_status": run["status"],
    }


def identity(folder):
    manifest = read(folder/"MANIFEST.json")
    local_manifest = HERE/"MANIFEST.json"
    need(manifest["status"]=="DIAGNOSTIC_ONLY"
         and manifest["bundle"]==read(local_manifest)
         and manifest["bundle_manifest_sha256"]==sha256(local_manifest)
         and (folder/"V4_INPUTS.json").read_bytes()==(HERE/"V4_INPUTS.json").read_bytes()
         and manifest["parent_results"]=={k:SPEC[k] for k in ("v2_result","v3_result","v3_audit")}
         and manifest["parent_seals"]=={v:sha256(HERE/f"{v.upper()}_RESULT_SHA256SUMS.txt")
                                       for v in ("v2","v3")},
         "result inputs differ from the fixed bundle or v2/v3 receipts")
    commits = [manifest[k] for k in ("bundle_commit","bundle_audit","judge_execution")]
    need(len(set(commits))==3 and all(re.fullmatch("[a-f0-9]{40}",v) for v in commits),
         "result is missing separate bundle, audit and Judge commit references")
    build = read(folder/"BUILD.json")
    need(build==manifest["build"] and build["gmp_limb_bits"]==64
         and build["bundle_manifest_sha256"]==manifest["bundle_manifest_sha256"]
         and build["k1_sha256"]==sha256(folder/"K1.log")
         and build["compile_log_sha256"]==sha256(folder/"compile.log"),
         "build receipt differs from frozen logs")


def verify_result_seal(folder):
    name = "RESULT_SHA256SUMS.txt"
    hashes = verify_seal(folder,(folder/name).read_text(encoding="ascii"))
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    need(actual==set(hashes)|{name},"result contains an unhashed file")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unsealed",action="store_true")
    parser.add_argument("v2",type=Path)
    parser.add_argument("v3",type=Path)
    parser.add_argument("result",type=Path)
    args = parser.parse_args()
    try:
        if not args.unsealed:
            verify_result_seal(args.result)
        identity(args.result)
        result = review_parent_and_run(args.v2,args.v3,args.result)
        if not args.unsealed:
            stored = read(args.result/"LEDGER_INSPECTION.json")
            if stored["status"]!="INSPECTION_PENDING":
                need(result==stored,"sealed inspection differs from the exact replay")
    except (OSError,ValueError,TypeError,ArithmeticError,IndexError,KeyError,StopIteration) as exc:
        result = {"status":"INVALID_LEDGER","reason":str(exc)}
    print(json.dumps(result,indent=2))
    return 2 if result["status"]=="INVALID_LEDGER" else 0


if __name__=="__main__":
    raise SystemExit(main())
