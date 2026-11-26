"""Freeze the run identity, execute the authorized pilot and then Candidate B."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import platform
import re
import resource
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from crossings import Crossings
from engine import (AngleTree, Budget, EDGES, Encloser, HERE, INPUTS, Inconsistent, JOURNALS,
                    Journal, Kernel, Q, QUANTITIES, Stop, edge_roots, pack, roots, unpack, unrational)
from shape import Family, Task

NS = 10**9
BUDGET = INPUTS["budget"]


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda:stream.read(1<<20),b""):
            result.update(data)
    return result.hexdigest()


def save(path,data):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(data,stream,indent=2,ensure_ascii=True)
        stream.write("\n")


def read_lines(path):
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.endswith("\n"):
                    raise Inconsistent(f"torn journal line in {path}")
                yield json.loads(line)


def preflight():
    manifest = json.loads((HERE/"MANIFEST.json").read_text())
    for file,expected in manifest["files"].items():
        if digest(HERE/file) != expected:
            raise Inconsistent(f"bundle SHA-256 mismatch in {file}")
    listed = dict((name,sha) for sha,name in
                  (line.split("  ",1) for line in (HERE/"SHA256SUMS.txt").read_text().splitlines()))
    if listed != {**manifest["files"],"MANIFEST.json":digest(HERE/"MANIFEST.json")}:
        raise Inconsistent("bundle SHA-256 list does not match MANIFEST")
    library = HERE/"build/candidate_kernel.so"
    build = json.loads((HERE/"build/BUILD.json").read_text())
    if build["library_sha256"]!=digest(library) or build["bundle_manifest_sha256"]!=digest(HERE/"MANIFEST.json"):
        raise Inconsistent("compiled library does not match build receipt")
    if (build["gmp_limb_bits"]!=64 or build["k1_sha256"]!=digest(HERE/"build/K1.log") or
        build["compile_log_sha256"]!=digest(HERE/"build/compile.log")):
        raise Inconsistent("K1 or compiler log does not match the receipt")
    kernel = Kernel(library)
    if (kernel.lib.cb_mpfr().decode(),kernel.lib.cb_gmp().decode()) != (build["mpfr"],build["gmp"]):
        raise Inconsistent("loaded library versions differ from the header probe")
    return manifest,build,library


def pilot(engine,f):
    cap = BUDGET["pilot_stage"]
    sphere = (Q(4,3),)*2 if f in ("Z1","Z2") else engine.kernel.sphere_reference()
    for i,entry in enumerate(INPUTS["pilot"]):
        box = tuple(map(Q,entry))
        for mode in range(3):
            with AngleTree(engine,f,mode,box,INPUTS["angular"]["precision"]) as tree:
                results = [tree.stage(n) for n in INPUTS["angular"]["stages"] if n<=cap]
            proof,interval = results[-1]
            includes = None if i or mode else interval[0]<=sphere[0]<=sphere[1]<=interval[1]
            record = dict(quantity=f,sample=i,derivative=mode,integral=proof,sphere_contains=includes)
            if includes is not None:
                record["reference"] = pack(sphere)
            engine.journal.row("events",record="pilot_integral",**record)
            if includes is False:
                raise Inconsistent(f"sphere containment failed for {f}")
    return "RECORDED"


def worker(phase,f,path,library,deadline,flag):
    started = time.monotonic_ns()
    cpu = time.process_time_ns()
    log = Journal(path,f"{phase}.{f}")
    cells = BUDGET["cells_other"]//len(QUANTITIES) if phase=="pilot" else BUDGET["cells_per_quantity"]
    budget = Budget(deadline,cells,lambda: bool(flag.value))
    family = None
    engine = None
    failure = None
    try:
        kernel = Kernel(library)
        kernel.watch(flag)
        engine = Encloser(kernel,log,budget,measure=phase=="pilot")
        if phase=="pilot":
            status = pilot(engine,f)
        else:
            family = Family(f,engine)
            status = family.run()
    except Stop as exc:
        status,failure = "STOPPED",str(exc)
        log.row("pending",quantity=f,phase=phase,reason=failure)
    except Exception:
        status,failure = "INCONSISTENT",traceback.format_exc()
        log.row("pending",quantity=f,phase=phase,reason="WORKER_EXCEPTION")
    if status=="INCONSISTENT":
        flag.value = 1
    log.row("events",record="worker_outcome",phase=phase,quantity=f,status=status,detail=failure,
            formula_calls=budget.cells,wall_ns=time.monotonic_ns()-started,
            cpu_ns=time.process_time_ns()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            reuse=engine.hits if engine else 0,shape_trials=family.examined if family else 0,
            chart_trials=len(family.tried) if family else 0)
    log.close()


def run_phase(context,phase,path,library,deadline,flag):
    submissions = []
    error = None
    try:
        # The coordinator computes Z1 itself. Three children give four processes total.
        for f in QUANTITIES[1:]:
            job = context.Process(target=worker,args=(phase,f,path/f,library,deadline,flag))
            job.start()
            submissions.append((f,job))
        worker(phase,QUANTITIES[0],path/QUANTITIES[0],library,deadline,flag)
        for _,job in submissions:
            job.join(max(0,(deadline-time.monotonic_ns())/NS))
    except Exception:
        error = traceback.format_exc()
        flag.value = 1
    finally:
        alive = [job for _,job in submissions if job.is_alive()]
        if alive:
            flag.value = 1
        for job in alive:
            job.terminate()
            job.join(2)
            if job.is_alive():
                job.kill()
                job.join()
    if error:
        save(path/"coordinator_error.json",dict(phase=phase,detail=error))
    return {f:job.exitcode for f,job in submissions}


def pilot_gate(path):
    stats = {f: [event for event in read_lines(path/f/"events.jsonl")]
             for f in QUANTITIES}
    counts = {}
    totals = 0
    samples = []
    for f,events in stats.items():
        for row in read_lines(path/f/"integrals.jsonl"):
            totals += row["formula_calls"]
            samples.extend(row.get("cell_ns",[]))
            key = (f,row["dimension"],row["target"],row["derivative"])
            counts.setdefault(key,[]).extend(row.get("cell_ns",[]))
    expected = {(i,d) for i in range(len(INPUTS["pilot"])) for d in range(3)}
    complete = True
    for f,events in stats.items():
        values = [e for e in events if e["record"]=="pilot_integral"]
        done = [e for e in events if e["record"]=="worker_outcome"]
        complete &= (len(values)==len(expected) and
                     {(r["sample"],r["derivative"]) for r in values}==expected and
                     len(done)==1 and done[0]["status"]=="RECORDED" and
                     [r["sphere_contains"] for r in values if not r["sample"] and not r["derivative"]]==[True])
    ordered = sorted(samples)
    p90 = ordered[(9*len(ordered)+9)//10-1] if ordered else None
    forecast_cells = BUDGET["cells_per_quantity"]+BUDGET["cells_other"]-totals
    estimate_ns = p90*forecast_cells if p90 is not None else None
    allowed = (complete and len(samples)==totals and estimate_ns is not None and
               estimate_ns<=NS*BUDGET["pilot_estimate_max_seconds"])
    by_kind = [dict(quantity=f,dimension=d,stage=n,derivative=k,cells=len(a),
                    median_ns=statistics.median(a),p90_ns=sorted(a)[(9*len(a)+9)//10-1])
               for (f,d,n,k),a in sorted(counts.items()) if a]
    return dict(allowed=bool(allowed),complete=bool(complete),formula_calls=totals,p90_ns=p90,
                forecast_cells=forecast_cells,estimate_ns=estimate_ns,
                estimate_seconds=estimate_ns/NS if estimate_ns is not None else None,by_kind=by_kind)


def run_intersections(path,library,deadline,flag,gate,main_folder):
    log = Journal(path,"compare")
    kernel = Kernel(library)
    kernel.watch(flag)
    budget = Budget(deadline,BUDGET["cells_other"]-gate["formula_calls"],lambda: bool(flag.value))
    engine = Encloser(kernel,log,budget)
    started = time.monotonic_ns()
    cpu = time.process_time_ns()
    reason = None
    try:
        charts = [r for f in QUANTITIES for r in read_lines(main_folder/f/"charts.jsonl")]
        status = Crossings(engine,charts).run()
    except Exception:
        status,reason = "INCONSISTENT",traceback.format_exc()
        log.row("pending",phase="intersections",reason="INTERSECTION_EXCEPTION")
    log.row("events",record="comparison_outcome",status=status,formula_calls=budget.cells,detail=reason,
            wall_ns=time.monotonic_ns()-started,cpu_ns=time.process_time_ns()-cpu,
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    log.close()
    return status


def merge(output,folders):
    result = {}
    problems = []
    for name in JOURNALS:
        with (output/f"{name}.jsonl").open("x",encoding="utf-8") as dest:
            result[name] = 0
            for folder in folders:
                try:
                    for line in read_lines(folder/f"{name}.jsonl"):
                        dest.write(json.dumps(line,separators=(",",":"))+"\n")
                        result[name] += 1
                except (Inconsistent,ValueError,OSError) as exc:
                    problems.append(str(exc))
    if problems:
        with (output/"events.jsonl").open("a",encoding="utf-8") as stream:
            stream.write(json.dumps(dict(id="finalize.corrupt",record="finalization",
                                         status="INCONSISTENT",detail=problems))+"\n")
        result["events"] += 1
    return result,problems


def recover_pending(output,started):
    """Reconstruct unvisited geometry after even a forcibly stopped child."""
    if not started:
        return 0
    from collections import defaultdict

    found = defaultdict(dict)
    for name in ("boxes","edges"):
        for row in read_lines(output/f"{name}.jsonl"):
            if row["record"]=="node":
                found[row["quantity"]][row["node"]] = row
    old = {(row.get("quantity"),row.get("node")) for row in read_lines(output/"pending.jsonl")}
    made = 0
    with (output/"pending.jsonl").open("a",encoding="utf-8") as pending:
        for f in QUANTITIES:
            tasks = [Task(n,n,b) for n,b in roots()]
            tasks += [Task(n,n,b,edge=e) for e in EDGES for n,b in edge_roots(e)]
            while tasks:
                task = tasks.pop()
                r = found[f].get(task.name)
                if r and r["status"]=="SPLIT":
                    tasks.extend(task.children(r["axis"],unrational(r["cut"])))
                elif r is None and (f,task.name) not in old:
                    made += 1
                    row = dict(id=f"finalize.pending.{made}",quantity=f,reason="UNEVALUATED",
                               phase="edges" if task.edge else "boxes",**task.fields())
                    pending.write(json.dumps(row,separators=(",",":"))+"\n")
    return made


def output_sha(output):
    files = sorted(x for x in output.rglob("*") if x.is_file())
    (output/"RESULT_SHA256SUMS.txt").write_text(
        "".join(f"{digest(path)}  {path.relative_to(output).as_posix()}\n" for path in files),
        encoding="ascii")


def summarize_journals(output):
    from collections import Counter
    shape = {f:Counter() for f in QUANTITIES}
    unresolved = {f:Counter() for f in QUANTITIES}
    signed = dict.fromkeys(QUANTITIES,Q(0))
    for r in read_lines(output/"boxes.jsonl"):
        f = r["quantity"]
        shape[f][r["status"]] += 1
        if r["status"]=="UNRESOLVED":
            unresolved[f][r["reason"]] += 1
        if r["status"] in ("SIGN_POS","SIGN_NEG"):
            y0,y1,z0,z1 = unpack(r["box"])
            signed[f] += (y1-y0)*(z1-z0)
    workers,visits,trace = [],dict.fromkeys(QUANTITIES,0),{}
    for r in read_lines(output/"events.jsonl"):
        if r["record"] in ("worker_outcome","comparison_outcome"):
            workers.append(r)
        if r["record"]=="root_visit":
            visits[r["quantity"]] += 1
        if r["record"]=="trace_budget":
            trace[r["quantity"]] = dict(status=r["status"],formula_calls=r["formula_calls"])
    return dict(counts=shape,signed_area={f:str(a) for f,a in signed.items()},workers=workers,
                root_visits=visits,trace=trace,unresolved_reasons=unresolved)


def run(args):
    static,build,library = preflight()
    output = args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    start = time.monotonic_ns()
    started_utc = datetime.now(timezone.utc).isoformat()
    limit = start+BUDGET["total_seconds"]*NS
    pilot_limit = min(limit,start+BUDGET["pilot_seconds"]*NS)
    ctx = mp.get_context("fork")
    flag = ctx.RawValue("i",0)
    parent_kernel = Kernel(library)
    parent_kernel.watch(flag)
    pilot_folder,main_folder,compare_folder = (output/"work"/p for p in ("pilot","main","compare"))
    pilot_return = run_phase(ctx,"pilot",pilot_folder,library,pilot_limit,flag)
    try:
        gate = pilot_gate(pilot_folder)
    except (ValueError,Inconsistent,OSError) as exc:
        gate = dict(allowed=False,complete=False,formula_calls=0,p90_ns=None,
                    forecast_cells=None,estimate_ns=None,
                    estimate_seconds=None,by_kind=[],receipt_error=str(exc))
    gate["child_exit"] = pilot_return
    proceeded = (gate["allowed"] and all(x==0 for x in pilot_return.values()) and
                 not flag.value and time.monotonic_ns()<limit)
    main_return = {}
    comparison = "NOT_RUN"
    if proceeded:
        main_return = run_phase(ctx,"main",main_folder,library,limit,flag)
        if not flag.value and time.monotonic_ns()<limit:
            comparison = run_intersections(compare_folder,library,limit,flag,gate,main_folder)
    elapsed = time.monotonic_ns()-start
    save(output/"PILOT.json",gate)
    shutil.copyfile(HERE/"INPUTS.json",output/"INPUTS.json")
    shutil.copyfile(HERE/"build/BUILD.json",output/"BUILD.json")
    folders = [*(pilot_folder/f for f in QUANTITIES),*(main_folder/f for f in QUANTITIES),compare_folder]
    rows,problems = merge(output,folders)
    if (pilot_folder/"coordinator_error.json").exists() or (main_folder/"coordinator_error.json").exists():
        problems.append("Coordinator failure (see work/*/coordinator_error.json)")
    try:
        rows["pending"] += recover_pending(output,proceeded)
    except (ValueError,Inconsistent,OSError) as exc:
        problems.append(str(exc))
    summary = dict(status="DIAGNOSTIC_ONLY",main_started=proceeded,child_exit=main_return,
                   operator_stop=bool(flag.value),deadline_reached=elapsed>=BUDGET["total_seconds"]*NS,
                   elapsed_ns=elapsed,rows=rows,comparison=comparison,finalization_errors=problems,
                   formula_calls=sum(r["formula_calls"] for r in read_lines(output/"integrals.jsonl")))
    if not problems:
        summary["journal_totals"] = summarize_journals(output)
    for name in ("build/K1.log","build/compile.log"):
        if (HERE/name).is_file():
            shutil.copyfile(HERE/name,output/Path(name).name)
    remaining = (limit-time.monotonic_ns())/NS
    if problems:
        inspection = dict(status="INVALID_LEDGER",detail=problems)
    elif remaining>0 and not flag.value:
        try:
            checked = subprocess.run([sys.executable,str(HERE/"verify_ledgers.py"),str(output),
                                      "--unsealed"],capture_output=True,text=True,timeout=remaining)
            inspection = json.loads(checked.stdout)
        except (subprocess.TimeoutExpired,ValueError) as exc:
            inspection = dict(status="INSPECTION_PENDING",detail=str(exc))
    else:
        inspection = dict(status="INSPECTION_PENDING",detail="execution deadline or operator stop")
    save(output/"LEDGER_INSPECTION.json",inspection)
    summary["inspection"] = inspection.get("status")
    summary["verified_conditions"] = {key:inspection.get(key) for key in ("quantities","intersections")}
    summary["elapsed_through_inspection_ns"] = time.monotonic_ns()-start
    save(output/"summary.json",summary)
    save(output/"MANIFEST.json",dict(bundle_commit=args.bundle_commit,judge_execution=args.judge_execution,
         source_bundle=static,bundle_manifest_sha256=digest(HERE/"MANIFEST.json"),
         command=sys.argv,build=build,os=platform.platform(),python=platform.python_version(),
         started_utc=started_utc,finished_utc=datetime.now(timezone.utc).isoformat(),
         processes=BUDGET["processes"]))
    output_sha(output)
    print(json.dumps(summary,indent=2))
    return 0 if inspection.get("status")!="INVALID_LEDGER" else 2


def sha_argument(value):
    if not re.fullmatch("[a-f0-9]{40}",value):
        raise argparse.ArgumentTypeError("give the full Git commit SHA")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-commit",type=sha_argument,required=True)
    parser.add_argument("--judge-execution",type=sha_argument,required=True)
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    static = json.loads((HERE/"MANIFEST.json").read_text())
    if args.judge_execution in {*static["commits"].values(),args.bundle_commit}:
        parser.error("supply the separate Judge execution approval commit")
    return run(args)


if __name__=="__main__":
    raise SystemExit(main())
