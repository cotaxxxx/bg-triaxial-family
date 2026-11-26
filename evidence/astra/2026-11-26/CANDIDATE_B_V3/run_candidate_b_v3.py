"""Resume the frozen v2 cover after the Jacobi example and v3 approval."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import multiprocessing as mp
import re
import resource
import signal
import subprocess
import sys
import time
import traceback

from engine import Budget, INPUTS, Journal, Kernel, QUANTITIES, Q, Stop, pack
from method_v3 import (
    BUDGET, Probe, V3, boundary_setup, final_comparisons, interior_setup, old_geometry, residual,
)
from v2_lock import HERE, lines, read, seal, sha256, verify_parent, verify_seal

NS = 10**9


def save(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def bundle():
    specification = read(HERE / "MANIFEST.json")
    sums = (HERE / "SHA256SUMS.txt").read_text(encoding="ascii")
    check = verify_seal(HERE, sums)
    if check != {**specification["files"], "MANIFEST.json": sha256(HERE / "MANIFEST.json")}:
        raise ValueError("bundle manifest does not match its SHA-256 list")
    build = read(HERE / "build/BUILD.json")
    library = HERE / "build/candidate_kernel.so"
    if (build["library_sha256"] != sha256(library)
            or build["bundle_manifest_sha256"] != check["MANIFEST.json"]
            or build["k1_sha256"] != sha256(HERE / "build/K1.log")
            or build["compile_log_sha256"] != sha256(HERE / "build/compile.log")
            or build["gmp_limb_bits"] != 64):
        raise ValueError("build receipt differs from the library or build records")
    return specification, build, library


def execution_record(args):
    now = datetime.now(timezone.utc)
    end = datetime.fromisoformat(args.jacobi_ended_at)
    minimum = datetime.fromisoformat(V3["jacobi_not_before"])
    if end.tzinfo is None or not minimum <= end <= now or not args.jacobi_end_record.strip():
        raise ValueError("provide the end time and record of the finished Jacobi example")
    if args.bundle_commit == args.judge_execution:
        raise ValueError("v3 requires a separate Judge execution approval")
    return dict(
        grade="DIAGNOSTIC_ONLY", started_utc=now.isoformat(),
        bundle_commit=args.bundle_commit, execution_approval=args.judge_execution,
        v2_result_commit=V3["v2_result_commit"],
        v2_result_checksum_sha256=sha256(HERE / "V2_RESULT_SHA256SUMS.txt"),
        jacobi_bundle_commit=V3["jacobi_bundle_commit"], jacobi_ended_at=end.isoformat(),
        jacobi_end_record=args.jacobi_end_record,
    )


def inspect_pilot(p, f):
    sphere = (Q(4,3),)*2 if f.startswith("Z") else p.kernel.sphere_reference()
    for k, raw in enumerate(INPUTS["pilot"]):
        box = tuple(map(Q,raw))
        for mode in (0,1,2):
            ref,value = p.probe(f,box,mode,(64,256),lambda _: False)
            okay = None if k or mode else value[0] <= sphere[0] <= sphere[1] <= value[1]
            p.journal.row("events",record="pilot",quantity=f,sample=k,mode=mode,
                          evaluation=ref,sphere_contains=okay,
                          sphere=pack(sphere) if okay is not None else None)
            if okay is False:
                raise ValueError(f"sphere containment failed for {f}")
    return "RECORDED"


def job(phase, f, output, library, deadline, flag, cells, data):
    started = time.monotonic_ns()
    log = Journal(output,f"v3.{phase}.{f}")
    p = None
    status,message = "INCONSISTENT",None
    count = None
    try:
        k = Kernel(library)
        k.watch(flag)
        received = data["build"]
        if (k.lib.cb_mpfr().decode(),k.lib.cb_gmp().decode()) != (received["mpfr"],received["gmp"]):
            raise ValueError("linked MPFR/GMP versions differ from the build receipt")
        p = Probe(k,log,Budget(deadline,cells,lambda: bool(flag.value)),measure=phase=="pilot")
        if phase=="pilot":
            status = inspect_pilot(p,f)
        elif phase=="local":
            boundary_setup(p)
            interior_setup(p)
            status = "RECORDED"
        elif phase=="main":
            status,message,count = residual(f,p,data["charts"][f],data["opened"][f],data["setup"])
        elif phase=="compare":
            status = final_comparisons(p,data["main"],data["setup"],data["charts"],data["opened"])
    except Stop as error:
        status,message = "STOPPED",str(error)
    except Exception:
        status,message = "INCONSISTENT",traceback.format_exc()
        flag.value = 1
    finally:
        log.row("events",record="outcome",phase=phase,quantity=f,status=status,detail=message,
                calls=p.budget.cells if p else 0,extensions=count,wall_ns=time.monotonic_ns()-started,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        log.close()


def launch(context, phase, tasks, location, library, deadline, flag, data):
    processes = {}
    try:
        for f,cap in tasks.items():
            if flag.value or time.monotonic_ns() >= deadline:
                break
            child = context.Process(target=job,
                args=(phase,f,location/f,library,deadline,flag,cap,data))
            child.start()
            processes[f] = child
        while any(child.is_alive() for child in processes.values()):
            if flag.value or time.monotonic_ns() >= deadline:
                break
            for child in processes.values():
                child.join(0.05)
    finally:
        living = [child for child in processes.values() if child.is_alive()]
        for child in living:
            child.terminate()
        for child in living:
            child.join(2)
            if child.is_alive():
                child.kill()
                child.join()
    return {f:child.exitcode for f,child in processes.items()}


def review_pilot(path):
    complete = True
    timings = []
    for f in QUANTITIES:
        directory = path / f
        if not (directory/"events.jsonl").is_file():
            complete = False
            continue
        events = list(lines(directory/"events.jsonl"))
        tests = [row for row in events if row["record"]=="pilot"]
        outcomes = [row["status"] for row in events if row["record"]=="outcome"]
        complete &= (
            {(r["sample"],r["mode"]) for r in tests} ==
            {(k,m) for k in range(len(INPUTS["pilot"])) for m in (0,1,2)}
            and [r["sphere_contains"] for r in tests if not r["sample"] and not r["mode"]]==[True]
            and outcomes==["RECORDED"]
        )
        for row in lines(directory/"integrals.jsonl"):
            timings.extend(row.get("cell_ns",[]))
    ordered = sorted(timings)
    observed = ordered[(9*len(ordered)+9)//10-1] if ordered else None
    price = max(observed,BUDGET["previous_p90_ns"]) if observed is not None else None
    cells = max(BUDGET["main_cells"].values())+BUDGET["local_cells"]+BUDGET["intersection_cells"]
    estimate = price*cells if price else None
    return dict(complete=bool(complete),samples=len(ordered),p90_ns=observed,price_ns=price,
                forecast_cells=cells,forecast_ns=estimate)


def emit_verification(output, v2, remaining_seconds):
    if remaining_seconds <= 0:
        return {"status":"INSPECTION_PENDING","detail":"wall timer elapsed"}
    try:
        checked = subprocess.run(
            [sys.executable,"-I","-B",str(HERE/"verify_v3.py"),"--unsealed",str(v2),str(output)],
            timeout=remaining_seconds, capture_output=True, text=True,
        )
        return json.loads(checked.stdout)
    except subprocess.TimeoutExpired:
        return {"status":"INSPECTION_PENDING","detail":"ledger check deadline"}
    except (OSError,ValueError) as exc:
        return {"status":"INSPECTION_PENDING","detail":str(exc)}


def run(args):
    start = time.monotonic_ns()
    identity = execution_record(args)
    specification,build,library = bundle()
    old = args.v2_result.resolve()
    verify_parent(old)
    charts,opened = old_geometry(old)
    output = args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    identity.update(bundle=specification,build=build)
    save(output/"MANIFEST.json",identity)
    for f in ("BUILD.json","K1.log","compile.log","HEADER.json"):
        (output/f).write_bytes((HERE/"build"/f).read_bytes())
    (output/"V3_INPUTS.json").write_bytes((HERE/"V3_INPUTS.json").read_bytes())
    hard = start + BUDGET["total_seconds"]*NS
    deadline = hard - BUDGET["seal_reserve_seconds"]*NS
    context = mp.get_context("fork")
    flag = context.Value("i",0,lock=False)

    def request_stop(_signal,_frame):
        flag.value = 1

    signal.signal(signal.SIGTERM,request_stop)
    signal.signal(signal.SIGINT,request_stop)
    work = output/"work"
    data = dict(build=build,charts=charts,opened=opened,main=work/"main")
    exited = {}
    ran = False
    try:
        cap = {f:BUDGET["pilot_cells_each"] for f in QUANTITIES}
        pilot_deadline = min(deadline,start + BUDGET["pilot_seconds"]*NS)
        exited["pilot"] = launch(context,"pilot",cap,work/"pilot",library,pilot_deadline,flag,data)
        pilot = review_pilot(work/"pilot")
        pilot["available_ns"] = max(0,deadline-time.monotonic_ns())
        pilot["allowed"] = bool(
            pilot["complete"] and exited["pilot"]==dict.fromkeys(QUANTITIES,0)
            and not flag.value and time.monotonic_ns() < pilot_deadline
            and pilot["forecast_ns"] is not None and pilot["forecast_ns"] <= pilot["available_ns"]
        )
        save(output/"PILOT.json",pilot)
        if pilot["allowed"]:
            ran = True
            exited["local"] = launch(context,"local",{"proof":BUDGET["local_cells"]},
                                     work/"local",library,deadline,flag,data)
            if exited["local"]=={"proof":0} and not flag.value:
                data["setup"] = list(lines(work/"local/proof/intersections.jsonl"))
                exited["main"] = launch(context,"main",BUDGET["main_cells"],
                                       data["main"],library,deadline,flag,data)
                if exited["main"]==dict.fromkeys(QUANTITIES,0) and not flag.value:
                    exited["compare"] = launch(context,"compare",{"proof":BUDGET["intersection_cells"]},
                                               work/"compare",library,deadline,flag,data)
        summary = dict(status="DIAGNOSTIC_ONLY",main_authorized_by_pilot=ran,exits=exited,
                       stopped=bool(flag.value),evaluation_deadline=time.monotonic_ns()>=deadline)
    except Exception:
        summary = dict(status="DIAGNOSTIC_ONLY",main_authorized_by_pilot=ran,exits=exited,
                       stopped=True,operational_error=traceback.format_exc())
    save(output/"RUN.json",summary)
    available = max(0,(hard-time.monotonic_ns())/NS-120)
    review = emit_verification(output,old,available) if not flag.value else {
        "status":"INSPECTION_PENDING","detail":"operator stop or worker failure"}
    save(output/"LEDGER_INSPECTION.json",review)
    seal(output,"RESULT_SHA256SUMS.txt")
    print(json.dumps(review,indent=2))
    return 2 if review["status"]=="INVALID_LEDGER" else 0


def full_sha(value):
    if not re.fullmatch("[a-f0-9]{40}",value):
        raise argparse.ArgumentTypeError("use a full Git commit SHA")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-commit",required=True,type=full_sha)
    parser.add_argument("--judge-execution",required=True,type=full_sha)
    parser.add_argument("--v2-result",required=True,type=Path)
    parser.add_argument("--jacobi-ended-at",required=True)
    parser.add_argument("--jacobi-end-record",required=True)
    parser.add_argument("output",type=Path)
    return run(parser.parse_args())


if __name__=="__main__":
    raise SystemExit(main())
