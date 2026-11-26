"""Evaluate the local coefficients on the adopted zero-curve chart boxes."""

import argparse
from collections import deque
from ctypes import c_int
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import subprocess
import sys
import time
import traceback

from engine import AngleTree, Budget, Inconsistent, Journal, Kernel, Stop, cut, midpoint, pack, replace, section, sign
from inheritance import CFG, FAMILIES, inherited
from proof_rules import graph_test, krawczyk
from v2_lock import HERE, read, seal, sha256, verify_seal


NS = 10**9


def save(path,data):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(data,stream,indent=2)
        stream.write("\n")


class LocalTree(AngleTree):
    def __init__(self,engine,quantity,derivative,box,bits):
        self.e = engine
        self.f,self.d,self.box,self.bits = quantity,derivative,box,bits
        self.calls = 0
        engine.tree_serial += 1
        self.tree_id = f"{engine.journal.prefix}.tree.{engine.tree_serial}"
        self.handle = engine.kernel.lib.cb_create(
            CFG["native_ids"].index(quantity),derivative,bits,0,
            *(str(x).encode("ascii") for x in box),
        )
        if not self.handle:
            raise engine.kernel.error()


class Native:
    def __init__(self,kernel,journal,budget):
        self.kernel,self.journal,self.budget = kernel,journal,budget
        self.measure = self.in_trace = False
        self.tree_serial = 0

    def one(self,f,b,d,target):
        with LocalTree(self,f,d,b,CFG["precision"]) as tree:
            return tree.stage(target)

    def sign(self,f,b):
        with LocalTree(self,f,0,b,CFG["precision"]) as tree:
            for target in CFG["stages"]:
                proof,value = tree.stage(target)
                if sign(value):
                    break
        return proof,value


def exceptional(p,f,q,b,cross,transverse,emit):
    base = 1-cross
    m = tuple(midpoint(section(b,k)) for k in (0,1))
    pt = (m[0],m[0],m[1],m[1])
    for n in CFG["exception_stages"]:
        a,along = p.one(f,b,base+1,n)
        q_refs,dq = zip(*(p.one(q,b,d,n) for d in (1,2)),strict=True)
        e_refs,ends = zip(*(p.one(q,replace(b,base,x,x),0,n)
                            for x in section(b,base)),strict=True)
        state,hprime = graph_test(cross,transverse,along,*dq,ends)
        fields = dict(target=n,along=a,q_derivatives=list(q_refs),ends=list(e_refs),
                      arc_derivative=pack(hprime))
        if state!="OPEN":
            emit(status=state,**fields)
            return state,b if state=="GRAPH_ZERO" else None
        rs,values = zip(*(p.one(g,pt,0,n) for g in (f,q)),strict=True)
        gradient_f = [along,along]
        gradient_f[cross] = transverse
        check = krawczyk(b,values,[gradient_f,dq])
        fields.update(points=list(rs),krawczyk=check)
        if check and check["strict"]:
            emit(status="KRAW_ZERO",**fields)
            return "KRAW_ZERO",check["K"]
        emit(status="OPEN",**fields)
    return "OPEN",None


def cover(p,charts):
    emit = p.journal.row
    roots = [(f,i,q,"",b,0) for (f,i),(b,_,_,_) in sorted(charts.items())
             for q in FAMILIES[f]["channels"]]
    queue = deque(roots)
    while queue:
        p.budget.guard()
        f,i,q,node,b,depth = queue.popleft()
        _,cross,transverse,old = charts[f,i]
        ref,value = p.sign(q,b)
        fields = dict(family=f,chart=i,quantity=q,node=node,box=pack(b),
                      enclosure=ref,transverse=old)
        if sign(value):
            emit("boxes",status="POS" if sign(value)>0 else "NEG",**fields)
        elif depth<CFG["max_base_depth"]:
            base = 1-cross
            children = cut(b,base,midpoint(section(b,base)))
            emit("boxes",status="CUT",**fields)
            for k,child in enumerate(children):
                queue.append((f,i,q,node+str(k),child,depth+1))
        else:
            def attempt(**data):
                emit("intersections",family=f,chart=i,quantity=q,node=node,**data)
            state,location = exceptional(p,f,q,b,cross,transverse,attempt)
            emit("boxes",status=state,location=None if location is None else
                 list(map(str,location)),**fields)


def preflight(directory):
    manifest = read(HERE/"MANIFEST.json")
    hashes = verify_seal(HERE,(HERE/"SHA256SUMS.txt").read_text())
    if hashes!={**manifest["files"],"MANIFEST.json":sha256(HERE/"MANIFEST.json")}:
        raise Inconsistent("bundle checksum list disagrees with the manifest")
    build = read(directory/"BUILD.json")
    lib = directory/"correspondence_kernel.so"
    if (build["library_sha256"] != sha256(lib)
            or build["manifest_sha256"] != hashes["MANIFEST.json"]
            or build["compile_log_sha256"] != sha256(directory/"compile.log")
            or build["k1_sha256"] != sha256(directory/"K1.log")
            or build["generated_sha256"] != manifest["generated_sources"]
            or build["gmp_limb_bits"] != 64):
        raise Inconsistent("bundle build receipt differs")
    return manifest,build,lib


def inspect(ancestors,out):
    try:
        check = subprocess.run([sys.executable,"-I","-B",str(HERE/"verify_correspondence.py"),
                                "--unsealed",*map(str,ancestors),str(out)],
                               capture_output=True,text=True,timeout=CFG["inspection_seconds"])
        return json.loads(check.stdout)
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        return dict(status="INSPECTION_PENDING",detail=str(exc))


def run(args):
    ids = [args.bundle_commit,args.chat_audit,args.judge_execution]
    if len(set(ids))!=3:
        raise ValueError("bundle, audit and execution approval are separate commits")
    inputs = [p.resolve() for p in (args.v2,args.v3,args.v4)]
    out = args.output.resolve()
    if any(out.is_relative_to(p) or p.is_relative_to(out) for p in inputs):
        raise ValueError("the output must be outside all frozen result directories")
    manifest,build,lib = preflight(HERE/"build")
    charts,endpoints = inherited(*inputs)
    kernel = Kernel(lib)
    if (kernel.lib.cb_mpfr().decode(),kernel.lib.cb_gmp().decode()) != (build["mpfr"],build["gmp"]):
        raise Inconsistent("MPFR/GMP versions differ from the build receipt")
    stop = c_int(0)
    kernel.watch(stop)
    out.mkdir(parents=True,exist_ok=False)
    save(out/"MANIFEST.json",dict(grade="DIAGNOSTIC_ONLY",bundle=manifest,build=build,
         v2=CFG["v2_result"],v3=CFG["v3_result"],v4=CFG["v4_result"],adoption=CFG["adoption"],
         bundle_commit=ids[0],chat_audit=ids[1],judge_execution=ids[2],
         started_utc=datetime.now(timezone.utc).isoformat()))
    save(out/"SHARED_ENDPOINTS.json",endpoints)
    for name in ("BUILD.json","HEADER.json","compile.log","K1.log"):
        (out/name).write_bytes((HERE/"build"/name).read_bytes())
    (out/"CONDITIONS.json").write_bytes((HERE/"CONDITIONS.json").read_bytes())
    journal = Journal(out/"work","correspondence")
    start = time.monotonic_ns()
    budget = Budget(start+NS*CFG["evaluation_seconds"],CFG["max_formula_calls"],lambda: bool(stop.value))
    state,detail = "RECORDED",None
    try:
        cover(Native(kernel,journal,budget),charts)
    except Stop as exc:
        state,detail = "STOPPED",str(exc)
    except Exception:
        state,detail = "INCONSISTENT",traceback.format_exc()
    finally:
        journal.close()
    save(out/"RUN.json",dict(status=state,detail=detail,formula_calls=budget.cells,
                             elapsed_ns=time.monotonic_ns()-start,
                             finished_utc=datetime.now(timezone.utc).isoformat()))
    result = inspect(inputs,out) if not stop.value else dict(status="INSPECTION_PENDING",detail="operator stop")
    save(out/"LEDGER_INSPECTION.json",result)
    seal(out,"RESULT_SHA256SUMS.txt")
    print(json.dumps(result,indent=2))
    return 2 if state=="INCONSISTENT" or result["status"]=="INVALID_LEDGER" else 0


def commit(value):
    if not re.fullmatch(r"[0-9a-f]{40}",value):
        raise argparse.ArgumentTypeError("use the full 40-place Git SHA")
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("bundle-commit","chat-audit","judge-execution"):
        p.add_argument("--"+flag,type=commit,required=True)
    for flag in ("v2","v3","v4"):
        p.add_argument("--"+flag,type=Path,required=True)
    p.add_argument("output",type=Path)
    return run(p.parse_args())


if __name__=="__main__":
    raise SystemExit(main())
