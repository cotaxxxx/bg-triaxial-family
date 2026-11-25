"""Use only artificial certificates and the separate spherical regression."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from crossings import Crossings
from engine import (AngleTree, Budget, Encloser, INPUTS, Journal, Kernel, Q,
                    Stop, pack, unpack, QUANTITIES)
from verify_ledgers import Invalid, Review, in_union, spherical_pole


class ArtificialIntervals:
    """Two crossing straight graphs, with exact synthetic interval images."""

    def __init__(self, journal, review):
        self.journal = journal
        self.review = review
        self.budget = Budget(time.monotonic_ns()+10**10,1000,lambda: False)

    def value(self, f, b, derivative=0, **options):
        slope = 2 if f=="Z1" else -2
        if derivative:
            value = (-slope,)*2 if derivative==1 else (1,1)
        else:
            a,c = sorted(slope*(y-Q(41,64))+Q(9,4) for y in b[:2])
            value = (b[2]-c,b[3]-a)
        number = str(len(self.review.proofs))
        self.review.proofs[number] = (f,b,derivative,value)
        return number,value


def rejects(test, data):
    try:
        test(data)
    except Invalid:
        return
    raise AssertionError("checker accepted an altered synthetic certificate")


def synthetic():
    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        journal = Journal(path/"synthetic","toy")
        spec = deepcopy(INPUTS)
        spec["shape_grid"] = [1,1]
        review = Review(path/"synthetic",spec)
        engine = ArtificialIntervals(journal,review)
        pair = ("Z1","D2")
        comparison,foot = Crossings(engine,[],{}).compare(pair,"INTERIOR")
        journal.close()
        review.read_charts()
        only = json.loads((path/"synthetic/intersections.jsonl").read_text())
        assert only["id"]==comparison and only["status"]=="UNIQUE_TRANSVERSE"
        assert review.comparison(only)==(pair,foot)
        assert unpack(only["cross_box"])[0] <= Q(41,64) <= unpack(only["cross_box"])[1]
        broken = deepcopy(only)
        broken["pieces"][0]["difference"] = pack((Q(0),Q(0)))
        rejects(review.comparison,broken)
        chart = next(iter(review.charts.values()))
        rejects(review.chart_condition,{**chart,"faces":chart["faces"][::-1]})
        a,b,c,d = Q(0),Q(1,2),Q(3,4),Q(1)
        assert in_union((a,d,a,d),[(a,b,a,d),(b,d,a,d)])
        assert not in_union((a,d,a,d),[(a,b,a,d),(c,d,a,d)])

        case = "Z1"
        node,geo = review.initial_rectangles()[0]
        lo,hi,y,z = geo
        m = (lo+hi)/2
        review.proofs["toy.sign"] = (case,geo,0,(1,2))
        review.proofs["toy.split"] = (case,geo,0,(-1,2))
        parent = dict(node=node,root=node,parent=None,depth=0,box=pack(geo),
                      status="SPLIT",axis=0,cut=pack((m,))[0],root_cut=None,
                      children=[node+"/0",node+"/1"],evaluation="toy.split")
        children = [
            dict(node=f"{node}/{j}",root=node,parent=node,depth=1,box=pack(box),
                 status="SIGN_POS",evaluation="toy.sign")
            for j,box in enumerate([(lo,m,y,z),(m,hi,y,z)])
        ]
        counts,area = review.tree(case,[parent,*children])
        assert counts=={"SPLIT":1,"SIGN_POS":2} and area==(hi-lo)*(z-y)
        assert review.tree(case,[parent,children[0]])[0]["PENDING"]==1
        broken = {**children[1],"box":pack((m+Q(1,8),hi,y,z))}
        rejects(lambda rows:review.tree(case,rows),[parent,children[0],broken])
        print("Synthetic crossing, strict derivative and face checks, union, split and pending: matched")


def synthetic_mean():
    with TemporaryDirectory() as tmp:
        path = Path(tmp)/"synthetic"
        journal = Journal(path,"main.Z1")
        box = (Q(1,2),Q(9,16),Q(2),Q(2))
        mid = (Q(17,32),Q(17,32),Q(2),Q(2))
        specs = [(box,0,(Q(-1),Q(1))),(mid,0,(Q(1,2),)*2),(box,1,(Q(0),Q(1)))]
        raw = []
        for j,(domain,derivative,value) in enumerate(specs):
            r = journal.row("integrals",tree=f"toy.{j}",quantity="Z1",derivative=derivative,
                            box=pack(domain),precision=128,target=64,cells=64,dimension=2,
                            total_calls=80,formula_calls=80,status="COMPLETE",interval=pack(value))
            raw.append(r["id"])
        value = (Q(15,32),Q(17,32))
        stage = dict(precision=128,target=64,direct=raw[0],midpoint=raw[1],
                     gradients=[raw[2],None],mean=pack(value))
        row = journal.row("enclosures",quantity="Z1",box=pack(box),derivative=0,edge_retry=False,
                          shape_shortcut=True,stages=[stage],interval=pack(value),formula_calls=240)
        journal.close()
        reader = Review(path,INPUTS)
        reader.read_integrals()
        reader.read_enclosures()
        assert reader.value(row["id"],"Z1",box)==value
        stage["mean"] = pack((Q(1,2),Q(17,32)))
        (path/"enclosures.jsonl").write_text(json.dumps(row)+"\n")
        rejects(lambda _:reader.read_enclosures(),None)
        print("Synthetic ledger mean-value reconstruction: valid bound read, narrowed bound rejected")


def sphere(library):
    kernel = Kernel(library)
    print(f"MPFR {kernel.lib.cb_mpfr().decode()} GMP {kernel.lib.cb_gmp().decode()}")
    known = spherical_pole()
    cut = kernel.sphere_reference()
    assert cut[0]<=known[0]<=known[1]<=cut[1]
    with TemporaryDirectory() as tmp:
        log = Journal(Path(tmp)/"sphere","sphere")
        deadline = time.monotonic_ns()+20_000_000_000
        circ = (Q(1),)*4
        engine = Encloser(kernel,log,Budget(deadline,1200,lambda: False))
        for bits in (128,256):
            for f in QUANTITIES:
                with AngleTree(engine,f,0,circ,bits) as handle:
                    handle.stage(16)
                    _,value = handle.stage(64)
                ref = (Q(4,3),)*2 if f[0]=="Z" else known
                assert value[0]<=ref[0]<=ref[1]<=value[1], (f,bits,value)
                print(f"Sphere {f} {bits} bits, 64 leaves: "
                      f"[{float(value[0]):.15g}, {float(value[1]):.15g}] contains analytic value")
        stopped = Encloser(kernel,log,Budget(deadline,1,lambda: False))
        with AngleTree(stopped,"Z1",0,circ,128) as handle:
            try:
                handle.stage(16)
            except Stop as why:
                assert str(why)=="CELL_BUDGET" and stopped.budget.cells==1
            else:
                raise AssertionError("one-cell limit should have stopped the integral")
        log.close()
        print("Sphere interrupted one-cell request: no usable interval emitted")


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library",type=Path,nargs="?")
    args = parser.parse_args()
    synthetic()
    synthetic_mean()
    if args.library:
        sphere(args.library.resolve())
