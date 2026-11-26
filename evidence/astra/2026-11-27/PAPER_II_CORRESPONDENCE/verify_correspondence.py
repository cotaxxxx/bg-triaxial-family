"""Replay the local sign and exception journal with rational endpoints only."""

import argparse
from collections import Counter,defaultdict,deque
import json
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from inheritance import CFG, FAMILIES, R, inherited
from proof_rules import graph_test,krawczyk
from v2_lock import HERE,read,sha256,verify_seal
from verify_v2 import F,contains,interval,need,partition,rect,replace_axis,rows,spans,strict


class Tape:
    def __init__(self,folder):
        self.raw = {}
        live = {}
        self.calls = 0
        stages = set(CFG["stages"])|set(CFG["exception_stages"])
        for i,r in enumerate(rows(folder,"integrals"),1):
            f,b,d,n = r["quantity"],rect(r["box"]),r["derivative"],r["target"]
            ident = r["id"]
            need(ident==f"correspondence.integrals.{i}" and contains(R,b) and
                 r["precision"]==CFG["precision"] and r["trace"] is False and
                 f in CFG["native_ids"] and d in (0,1,2) and n in stages,
                 "raw enclosure input is outside the plan")
            arg = f,b,d
            old,last,total,continued = live.get(r["tree"],(arg,0,0,True))
            limit = 16+4*((n-16)//3)
            charge,passed = r["formula_calls"],r["status"]=="COMPLETE"
            need(r["tree"].startswith("correspondence.tree.") and arg==old and continued and
                 last<n and type(charge) is int and charge>=0 and total+charge==r["total_calls"]<=limit,
                 "angle-tree stages or charges do not agree")
            live[r["tree"]] = arg,n,r["total_calls"],passed
            self.calls += charge
            if passed:
                need(r["dimension"]==2 and r["cells"]==n and r["total_calls"]==limit,
                     "complete integral has missing panels")
                self.raw[ident] = (arg,n,interval(r["interval"]))
            else:
                need(r["status"] in ("PENDING","INCONSISTENT") and "interval" not in r,
                     "unfinished integral cannot provide an enclosure")
        need(self.calls<=CFG["max_formula_calls"],"planned cell budget exceeded")

    def use(self,ref,f,b,derivative,caps):
        arg,stage,value = self.raw[ref]
        need(arg==(f,b,derivative) and stage in caps,"reference has the wrong box, quantity or stage")
        return value


def check_exception(tape,record,group,box,cross,transverse):
    f,_,p,_ = group
    base = 1-cross
    points = [(a+b)/2 for a,b in (spans(box,0),spans(box,1))]
    pt = (points[0],points[0],points[1],points[1])
    status,location = "OPEN",None
    tried = []
    for r,n in zip(record,CFG["exception_stages"]):
        need(status=="OPEN" and r["target"]==n,"unplanned or unnecessary exception trial")
        along = tape.use(r["along"],f,box,base+1,[n])
        qp = [tape.use(ref,p,box,k,[n]) for ref,k in zip(r["q_derivatives"],(1,2),strict=True)]
        ends = [tape.use(ref,p,replace_axis(box,base,x,x),0,[n])
                for ref,x in zip(r["ends"],spans(box,base),strict=True)]
        status,slope = graph_test(cross,transverse,along,*qp,ends)
        need(interval(r["arc_derivative"])==slope,"difference along the certified graph is incorrect")
        if status=="OPEN":
            grad = [along,along]
            grad[cross] = transverse
            vals = [tape.use(ref,g,pt,0,[n]) for ref,g in zip(r["points"],(f,p),strict=True)]
            test = krawczyk(box,vals,[grad,qp])
            need(r["krawczyk"]==test,"Krawczyk matrix, image or contraction differs")
            if test and test["strict"]:
                status,location = "KRAW_ZERO",test["K"]
        else:
            need("points" not in r and "krawczyk" not in r,"unplanned root solve after graph test")
            if status=="GRAPH_ZERO":
                location = list(map(str,box))
        need(r["status"]==status,"incorrect exception classification")
        tried.append(r["id"])
    need(len(tried)==len(record) and (status!="OPEN" or len(tried)==len(CFG["exception_stages"])),
         "exception record stopped before its prescribed terminal test")
    return status,location


def exercise(charts,folder,run):
    local = folder/"work"
    tape = Tape(local)
    need(tape.calls==run["formula_calls"],"summary panel count differs from the raw journal")
    attempts = defaultdict(list)
    for r in rows(local,"intersections"):
        attempts[r["family"],r["chart"],r["quantity"],r["node"]].append(r)
    roots = [(f,ident,p,"",b) for (f,ident),(b,_,_,_) in sorted(charts.items())
             for p in FAMILIES[f]["channels"]]
    queue = deque(roots)
    counts = {f:Counter() for f in FAMILIES}
    exceptions = []
    opposite = []
    opened = []
    for r in rows(local,"boxes"):
        need(bool(queue),"more records than the planned cover")
        f,ident,p,node,box = queue.popleft()
        key = (f,ident,p,node)
        _,cross,transverse,old = charts[f,ident]
        need(key==(r["family"],r["chart"],r["quantity"],r["node"]) and
             rect(r["box"])==box and r["transverse"]==old,"shape partition or inherited reference differs")
        ref = r["enclosure"]
        s = strict(tape.use(ref,p,box,0,CFG["stages"]))
        outcome = r["status"]
        n = tape.raw[ref][1]
        if s:
            need(outcome==("POS" if s>0 else "NEG"),"sign leaf is not strictly enclosed")
        else:
            need(n==CFG["stages"][-1],"sign policy stopped before the final stage")
            if len(node)<CFG["max_base_depth"]:
                need(outcome=="CUT","shape refinement is missing its base bisection")
                base = 1-cross
                a,b = spans(box,base)
                queue.extend((f,ident,p,node+str(k),piece) for k,piece in
                             enumerate(partition(box,base,(a+b)/2)))
            else:
                checked,location = check_exception(tape,attempts.pop(key),key,box,cross,transverse)
                need(checked==outcome and location==r["location"],"terminal witness differs")
                if outcome in ("KRAW_ZERO","GRAPH_ZERO"):
                    exceptions.append(dict(family=f,chart=ident,quantity=p,node=node,
                                           method=outcome,location=location))
                if outcome=="OPEN":
                    opened.append(dict(family=f,chart=ident,quantity=p,node=node,
                                       box=list(map(str,box)),status="OPEN"))
                s = {"GRAPH_POS":1,"GRAPH_NEG":-1}.get(outcome,0)
        if s and s!=CFG["expected_sign"][p]:
            opposite.append(dict(family=f,chart=ident,quantity=p,node=node,box=list(map(str,box)),sign=s))
        counts[f][outcome] += 1
    if run["status"]=="RECORDED":
        need(not queue and not attempts,"completed run has missing or detached shape records")
    else:
        need(run["status"] in ("STOPPED","INCONSISTENT") and len(attempts)<=1,
             "interrupted run contains detached local trials")
        need(not attempts or next(iter(attempts)) in {x[:4] for x in queue},
             "interrupted local trials do not belong to a pending shape node")
    for f,ident,p,node,box in queue:
        counts[f]["PENDING"] += 1
        opened.append(dict(family=f,chart=ident,quantity=p,node=node,
                           box=list(map(str,box)),status="PENDING"))
    return dict(
        status="CONDITIONS_RECORDED" if not opened and run["status"]=="RECORDED" else "PARTIAL",
        diagnostic_only=True, counts={f:dict(v) for f,v in counts.items()},
        formula_calls=tape.calls, exact_chart_tasks=len(roots),
        possible_repeated_events=exceptions, open_boxes=opened,
        signs_different_from_prior=opposite, run_status=run["status"],
    )


def read_result(v2,v3,v4,out):
    charts,ends = inherited(v2,v3,v4)
    need(read(out/"SHARED_ENDPOINTS.json")==ends,"shared endpoint record differs")
    identity = read(out/"MANIFEST.json")
    need(identity["grade"]=="DIAGNOSTIC_ONLY" and identity["bundle"]==read(HERE/"MANIFEST.json") and
         all(identity[k]==CFG[k+"_result"] for k in ("v2","v3","v4")) and
         identity["adoption"]==CFG["adoption"] and
         (out/"CONDITIONS.json").read_bytes()==(HERE/"CONDITIONS.json").read_bytes(),
         "the solved inputs do not match the frozen sources")
    commits = [identity[k] for k in ("bundle_commit","chat_audit","judge_execution")]
    need(len(set(commits))==3 and all(re.fullmatch("[a-f0-9]{40}",x) for x in commits),
         "separate bundle, audit and approval references are required")
    build = read(out/"BUILD.json")
    need(build==identity["build"] and build["gmp_limb_bits"]==64 and
         build["manifest_sha256"]==sha256(HERE/"MANIFEST.json") and
         build["generated_sha256"]==identity["bundle"]["generated_sources"] and
         build["compile_log_sha256"]==sha256(out/"compile.log") and
         build["k1_sha256"]==sha256(out/"K1.log"),"build receipt differs")
    result = exercise(charts,out,read(out/"RUN.json"))
    result["endpoint_degeneracies"] = ends
    return result


def verify_result_hashes(folder):
    name = "RESULT_SHA256SUMS.txt"
    hashes = verify_seal(folder,(folder/name).read_text())
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    need(actual==set(hashes)|{name},"result has missing or unhashed files")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--unsealed",action="store_true")
    for field in ("v2","v3","v4","output"):
        p.add_argument(field,type=Path)
    a = p.parse_args()
    try:
        if not a.unsealed:
            verify_result_hashes(a.output)
        result = read_result(a.v2,a.v3,a.v4,a.output)
        if not a.unsealed:
            saved = read(a.output/"LEDGER_INSPECTION.json")
            need(saved["status"]=="INSPECTION_PENDING" or result==saved,
                 "sealed inspection differs from rational replay")
    except (OSError,ValueError,TypeError,KeyError,IndexError,ArithmeticError) as error:
        result = dict(status="INVALID_LEDGER",detail=str(error))
    print(json.dumps(result,indent=2))
    return 2 if result["status"]=="INVALID_LEDGER" else 0


if __name__=="__main__":
    raise SystemExit(main())
