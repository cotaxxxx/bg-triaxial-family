"""Small rational fixtures for the v3 planning and replay code."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from engine import Journal, Q, QUANTITIES, pack, unpack
from method_v3 import boundary_setup, interior_setup, residual
from verify_v3 import (
    audit_extensions, audit_residual, check_interior, check_shared, review_pairs,
)
from v2_lock import lines
from run_candidate_b_v3 import execution_record


class Toy:
    def __init__(self,path,prefix,equations):
        self.journal = Journal(path,prefix)
        self.equations = equations
        self.budget = SimpleNamespace(guard=lambda: None)
        self.values = {}

    def at(self,f,box,mode,cap):
        a,b,c = self.equations[f]
        y0,y1,z0,z1 = box
        values = [a*y+b*z+c for y in (y0,y1) for z in (z0,z1)]
        v = (min(values),max(values)) if not mode else ((a,b)[mode-1],)*2
        key = str(len(self.values))
        self.values[key] = f,box,mode,cap,v
        return key,v

    def probe(self,f,box,mode,caps,accept):
        for cap in caps:
            key,v = self.at(f,box,mode,cap)
            if accept(v):
                break
        return key,v

    def signed(self,f,box,mode,caps,direction=None):
        return self.probe(f,box,mode,caps,lambda v: (1 if v[0]>0 else -1 if v[1]<0 else 0)
                          in ((-1,1) if direction is None else (direction,)))

    def get(self,ref,phase,f,box,mode,caps):
        g,r,d,n,v = self.values[ref]
        assert (g,r,d)==(f,box,mode) and n in caps
        return v


def expect_rejection(operation):
    try:
        operation()
    except ValueError:
        return
    raise AssertionError("modified proof was accepted")


def paired(path):
    toy = Toy(path/"paired","toy.shared",{
        "D1":(Q(1,3),Q(-1),Q(33,16)-Q(1,3)),
        "D2":(Q(-1,4),Q(-1),Q(33,16)+Q(1,4)),
        "Z1":(Q(1,2),Q(-1),Q(151,32)-Q(1,2)),
        "Z2":(Q(-1,2),Q(-1),Q(151,32)+Q(1,2)),
    })
    boundary_setup(toy)
    toy.journal.close()
    ref = {
        (f,"y_max"):[(f,(Q(1),Q(1),z-Q(1,256),z+Q(1,256)))]
        for f,z in (("D1",Q(33,16)),("D2",Q(33,16)),("Z1",Q(151,32)),("Z2",Q(151,32)))
    }
    parent = SimpleNamespace(roots=ref,edge_links={"Z1","Z2","D1","D2"})
    results = list(lines(path/"paired/intersections.jsonl"))
    for r in results:
        _, area, belt = check_shared(r,toy,parent)
        assert len(area)==1
        if r["name"]=="bp":
            assert belt is not None and unpack(r["difference"])==(-Q(7,12),)*2
            bad = deepcopy(r)
            bad["common_chart"]["faces"][0]["sum"] = pack((Q(0),Q(0)))
            expect_rejection(lambda: check_shared(bad,toy,parent))
    print("Artificial shared roots: factored D, both reconstructed face signs, and tamper check.")


def cross(path):
    y,z = Q(81,128),Q(73,32)
    model = {"Z1":(Q(5),Q(-1),z-5*y),"D2":(Q(0),Q(-1),z)}
    toy = Toy(path/"cross","toy.cross",model)
    interior_setup(toy)
    toy.journal.close()
    row, = lines(path/"cross/intersections.jsonl")
    pair,footprint,image = check_interior(row,toy)
    assert pair==("Z1","D2") and footprint and image==(y,y,z,z)
    changed = deepcopy(row)
    changed["trials"][0]["test"]["norm"] = pack((Q(1,2),))[0]
    expect_rejection(lambda: check_interior(changed,toy))
    print("Artificial crossing: eight graph seams, strict Krawczyk image and tamper check.")


def covers(path):
    destination = path/"work/main"
    c = Q(63,64),Q(127,128),Q(33,16),Q(67,32)
    prior = {"id":"old.chart","quantity":"D1","cross":1,"direction":-1,"box":pack(c)}
    leaf = (*c[:2],Q(131,64),Q(33,16))
    opened = {"old.leaf":(leaf,18)}
    toy = Toy(destination/"D1","toy.extension",{"D1":(Q(0),Q(-1),Q(133,64))})
    assert residual("D1",toy,[prior],opened,[])[0]=="RECORDED"
    toy.journal.close()
    support = {prior["id"]:unpack(prior["box"])}
    audit_extensions(path,toy,SimpleNamespace(charts={prior["id"]:prior}),"D1",support)
    assert audit_residual(path,toy,"D1",opened,support)=={"COVERED":1}

    toy = Toy(destination/"Z2","toy.cheap",{"Z2":(Q(0),Q(0),Q(2))})
    assert residual("Z2",toy,[],opened,[])[0]=="RECORDED"
    toy.journal.close()
    assert len(toy.values)==1 and next(iter(toy.values.values()))[3]==16
    assert audit_residual(path,toy,"Z2",opened,{})=={"SIGN":1}

    assert {p["status"] for p in review_pairs(path,None,False,{},{}).values()}=={"DEFERRED_COVER"}
    log = Journal(path/"work/compare/proof","toy.premature")
    log.row("intersections",record="gate",status="COVER_RECORDED")
    log.close()
    expect_rejection(lambda: review_pairs(path,None,False,{},{}))
    print("Artificial residuals: chart widening at depth 18, Z2 early sign at 16 cells, and global gate.")


def false_completion(path):
    shared = path/"finished"
    log = Journal(shared/"work/compare/proof","toy.finished")
    log.row("intersections",record="gate",status="COVER_RECORDED")
    log.row("intersections",record="pair_done",pair=["Z1","D1"])
    log.close()
    support = {f:{} for f in QUANTITIES}
    assert review_pairs(shared,None,True,{},support)["Z1+D1"]["status"]=="DISJOINT"
    rectangle = (Q(1,2),Q(9,16),Q(3,2),Q(7,4))
    support["Z1"]["left"] = support["D1"]["right"] = rectangle
    expect_rejection(lambda: review_pairs(shared,None,True,{},support))
    fake = SimpleNamespace(jacobi_ended_at="2026-11-26T18:13:59+09:00",
                           jacobi_end_record="artificial",bundle_commit="a"*40,
                           judge_execution="b"*40)
    expect_rejection(lambda: execution_record(fake))
    print("Artificial receipts: omitted overlap and premature Jacobi timestamp rejected.")


def main():
    with TemporaryDirectory() as work:
        path = Path(work)
        paired(path)
        cross(path)
        covers(path)
        false_completion(path)


if __name__ == "__main__":
    main()
