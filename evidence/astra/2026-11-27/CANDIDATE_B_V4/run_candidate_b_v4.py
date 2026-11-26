"""Record the approved Candidate B v4 local intersection calculation."""

import argparse
from contextlib import ExitStack
from ctypes import c_int
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

from ancestors import PAIR, SPEC, X, local_proof
from engine import AngleTree, Budget, Inconsistent, Journal, Kernel, Stop, add, inside, multiply, pack, subtract
from v2_lock import HERE, read, seal, sha256, verify_seal


K_SPEC = SPEC["krawczyk"]
NS = 10**9


def save(path, data):
    with path.open("x",encoding="utf-8") as target:
        json.dump(data,target,indent=2)
        target.write("\n")


def preflight():
    manifest_path = HERE/"MANIFEST.json"
    manifest = read(manifest_path)
    expected = verify_seal(HERE,(HERE/"SHA256SUMS.txt").read_text(encoding="ascii"))
    if expected != {**manifest["files"],"MANIFEST.json":sha256(manifest_path)}:
        raise Inconsistent("bundle manifest and checksum list differ")
    if any(expected.get(f) != digest for f,digest in manifest["fixed_sources"].items()):
        raise Inconsistent("fixed v2/v3 kernel or support source differs")
    build = read(HERE/"build/BUILD.json")
    library = HERE/"build/candidate_kernel.so"
    if (build["library_sha256"] != sha256(library)
            or build["bundle_manifest_sha256"] != expected["MANIFEST.json"]
            or build["k1_sha256"] != sha256(HERE/"build/K1.log")
            or build["compile_log_sha256"] != sha256(HERE/"build/compile.log")
            or build["gmp_limb_bits"] != 64):
        raise Inconsistent("the linked kernel or K1/build receipt does not match this bundle")
    return manifest,build,library


def contract(box, centre, value, jacobian):
    """Outward interval operations on exact rationals."""
    j = [[(a+b)/2 for a,b in row] for row in jacobian]
    determinant = j[0][0]*j[1][1] - j[0][1]*j[1][0]
    if determinant == 0:
        return None
    inverse = [[j[1][1]/determinant,-j[0][1]/determinant],
               [-j[1][0]/determinant,j[0][0]/determinant]]
    image = []
    norms = []
    for i, coefficients in enumerate(inverse):
        current = (centre[i],)*2
        for constant, interval in zip(coefficients,value,strict=True):
            current = subtract(current,multiply((constant,)*2,interval))
        norm = Fraction(0)
        for col in range(2):
            unit = Fraction(int(i == col))
            entry = (unit,unit)
            for k,constant in enumerate(coefficients):
                entry = subtract(entry,multiply((constant,)*2,jacobian[k][col]))
            norm += max(map(abs,entry))
            delta = box[2*col]-centre[col],box[2*col+1]-centre[col]
            current = add(current,multiply(entry,delta))
        image += list(current)
        norms.append(norm)
    strictly_inside = [box[k] < image[k] <= image[k+1] < box[k+1] for k in (0,2)]
    return dict(C=[pack(row) for row in inverse], K=pack(image),
                q=pack((max(norms),))[0], inside=strictly_inside, contraction=max(norms)<1)


def run_trials(make_tree, emit):
    centre = tuple(map(Fraction,K_SPEC["centre"]))
    at = (centre[0],centre[0],centre[1],centre[1])
    points = {}
    with ExitStack() as keep:
        values = [keep.enter_context(make_tree(f,0,at)) for f in PAIR]
        for i,args in enumerate(K_SPEC["boxes"]):
            box = tuple(map(Fraction,args))
            if not inside(box,X) or (box[0]+box[1],box[2]+box[3]) != tuple(2*x for x in centre):
                raise Inconsistent("fixed Krawczyk box has the wrong centre or leaves X")
            with ExitStack() as trial:
                derivatives = [[trial.enter_context(make_tree(f,d,box)) for d in (1,2)]
                               for f in PAIR]
                for target in K_SPEC["stages"]:
                    if target not in points:
                        points[target] = [tree.stage(target) for tree in values]
                    v = points[target]
                    j = [[tree.stage(target) for tree in row] for row in derivatives]
                    check = contract(box,centre,[iv for _,iv in v],[[iv for _,iv in row] for row in j])
                    if check is None:
                        failures = ["SINGULAR_MIDPOINT"]
                    else:
                        failures = [f"K_{axis}_NOT_STRICT" for axis,inside_ in
                                    zip(("Y","Z"),check["inside"],strict=True) if not inside_]
                        if not check["contraction"]:
                            failures.append("Q_NOT_LT_ONE")
                    emit("intersections", record="krawczyk", box_index=i, stage=target,
                         box=pack(box), values=[ident for ident,_ in v],
                         jacobian=[[ident for ident,_ in row] for row in j],
                         test=check, failed=failures)
                    if not failures:
                        return "RECORDED"
    return "RECORDED"


class Native:
    def __init__(self,kernel,journal,budget):
        self.kernel = kernel
        self.journal = journal
        self.budget = budget
        self.measure = False
        self.in_trace = False
        self.tree_serial = 0

    def tree(self,quantity,derivative,box):
        return AngleTree(self,quantity,derivative,box,K_SPEC["precision"])


def inspect(old2,old3,output):
    try:
        checked = subprocess.run(
            [sys.executable,"-I","-B",str(HERE/"verify_v4.py"),"--unsealed",
             str(old2),str(old3),str(output)],
            capture_output=True,text=True,timeout=120,
        )
        return json.loads(checked.stdout)
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        return dict(status="INSPECTION_PENDING",reason=str(exc))


def run(args):
    if len({args.bundle_commit,args.chat_audit,args.judge_execution}) != 3:
        raise ValueError("use distinct bundle, chat audit, and Judge execution commits")
    manifest,build,library = preflight()
    old2,old3 = args.v2_result.resolve(),args.v3_result.resolve()
    output = args.output.resolve()
    if any(output.is_relative_to(p) or p.is_relative_to(output) for p in (old2,old3)):
        raise ValueError("use a separate output directory outside the fixed result originals")
    gate = local_proof(old2,old3)
    kernel = Kernel(library)
    if (kernel.lib.cb_mpfr().decode(),kernel.lib.cb_gmp().decode()) != (build["mpfr"],build["gmp"]):
        raise Inconsistent("loaded MPFR/GMP differs from the build receipt")
    stop = c_int(0)
    kernel.watch(stop)
    output.mkdir(parents=True,exist_ok=False)
    save(output/"MANIFEST.json",dict(
        status="DIAGNOSTIC_ONLY", started_utc=datetime.now(timezone.utc).isoformat(),
        bundle_commit=args.bundle_commit, bundle_audit=args.chat_audit,
        judge_execution=args.judge_execution, bundle=manifest,
        bundle_manifest_sha256=sha256(HERE/"MANIFEST.json"), build=build,
        parent_results={key:SPEC[key] for key in ("v2_result","v3_result","v3_audit")},
        parent_seals={v:sha256(HERE/f"{v.upper()}_RESULT_SHA256SUMS.txt") for v in ("v2","v3")},
    ))
    for path in ("BUILD.json","HEADER.json","K1.log","compile.log"):
        (output/path).write_bytes((HERE/"build"/path).read_bytes())
    (output/"V4_INPUTS.json").write_bytes((HERE/"V4_INPUTS.json").read_bytes())
    save(output/"PRIMARY.json",gate)

    begin = time.monotonic_ns()
    journal = Journal(output/"work/local","v4.local")
    budget = Budget(begin+K_SPEC["seconds"]*NS,K_SPEC["max_formula_calls"],lambda: bool(stop.value))
    native = Native(kernel,journal,budget)
    status,detail = "INCONSISTENT",None
    try:
        if all(gate[k] for k in ("poincare_miranda","slope_contraction","all_four_overlaps_inside_X")):
            status = run_trials(native.tree,journal.row)
        else:
            status = "PRIMARY_UNRESOLVED"
    except Stop as exc:
        status,detail = "STOPPED",str(exc)
    except Exception:
        detail = traceback.format_exc()
    finally:
        journal.close()
    save(output/"RUN.json",dict(
        status=status, detail=detail, formula_calls=budget.cells,
        elapsed_ns=time.monotonic_ns()-begin, finished_utc=datetime.now(timezone.utc).isoformat(),
    ))
    result = inspect(old2,old3,output) if not stop.value else dict(
        status="INSPECTION_PENDING",reason="operator stop")
    save(output/"LEDGER_INSPECTION.json",result)
    seal(output,"RESULT_SHA256SUMS.txt")
    print(json.dumps(result,indent=2))
    return 2 if status=="INCONSISTENT" or result["status"]=="INVALID_LEDGER" else 0


def full_sha(value):
    if re.fullmatch(r"[0-9a-f]{40}",value) is None:
        raise argparse.ArgumentTypeError("use a full Git commit SHA")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-commit",required=True,type=full_sha)
    parser.add_argument("--chat-audit",required=True,type=full_sha)
    parser.add_argument("--judge-execution",required=True,type=full_sha)
    parser.add_argument("--v2-result",required=True,type=Path)
    parser.add_argument("--v3-result",required=True,type=Path)
    parser.add_argument("output",type=Path)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
