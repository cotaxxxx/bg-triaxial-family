"""Small artificial policy checks. No MPFR kernel or production runner is opened."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from unittest.mock import patch

from crossings import Crossings
from engine import Budget, Encloser, INPUTS, Journal, Q, pack, point, roots, spread_roots
from shape import Family, Task
from trace_bands import Trace
from verify_ledgers import Invalid, Review


class ToyTree:
    """Staged rational intervals with the same tree-accounting shape as MPFR."""

    def __init__(self,e,f,d,b,bits):
        self.e,self.f,self.d,self.b,self.bits = e,f,d,b,bits
        e.tree_serial += 1
        self.key = str(e.tree_serial)
        self.previous = 0

    def __enter__(self):
        return self

    def __exit__(self,*unused):
        return None

    def stage(self,cap):
        is_point = self.b[0]==self.b[1] and self.b[2]==self.b[3]
        reduced = (is_point and cap>=256 and self.e.synthetic_improvement)
        radius = Q(1,1024) if reduced else Q(1)
        value = (-radius,radius)
        cumulative = 16+4*(cap-16)//3
        used = cumulative-self.previous
        row = self.e.journal.row(
            "integrals",tree=self.key,quantity=self.f,derivative=self.d,box=pack(self.b),
            precision=self.bits,target=cap,cells=cap,dimension=2,total_calls=cumulative,
            formula_calls=used,status="COMPLETE",interval=pack(value),trace=False)
        self.previous = cumulative
        self.e.budget.cells += used
        return row["id"],value


def budget():
    return Budget(time.monotonic_ns()+3_000_000_000,200000,lambda: False)


def rejected(operation):
    try:
        operation()
    except (Invalid,KeyError):
        return
    raise AssertionError("checker accepted the deliberately corrupted receipt")


def midpoint_checks(tmp):
    ident,box = next((r,b) for r,b in roots() if r=="B04.04")
    for improves in (True,False):
        here = tmp/f"angle-{improves}"
        log = Journal(here,"main.Z1")
        e = Encloser(None,log,budget())
        e.synthetic_improvement = improves
        with patch("engine.AngleTree",ToyTree):
            evaluated = e.value("Z1",box,policy="shape")
        family = Family("Z1",e)
        children = family.shape_task(Task(ident,ident,box),evaluated)
        log.close()
        raw = json.loads((here/"enclosures.jsonl").read_text())
        shape_row = json.loads((here/"boxes.jsonl").read_text())
        targets = [s["target"] for s in raw["stages"]]
        assert targets==([64,256] if improves else [64,256,1024,4096])
        assert raw["split_ready"] is improves and bool(children) is improves
        assert "mean" not in raw["stages"][0]
        assert bool("mean" in raw["stages"][-1]) is improves
        assert shape_row["status"]==("SPLIT" if improves else "UNRESOLVED")
        reader = Review(here,INPUTS)
        reader.read_integrals()
        reader.read_enclosures()
        reader.tree("Z1",[shape_row])
        if improves:
            reader.split_ready.clear()
            rejected(lambda:reader.tree("Z1",[shape_row]))
        else:
            raw["split_ready"] = True
            (here/"enclosures.jsonl").write_text(json.dumps(raw)+"\n")
            rejected(reader.read_enclosures)
    print("Artificial midpoint: 64→256 before split; 4096 wide is unresolved; falsified gates rejected.")


class SignedToy:
    """Exact range of y - (1/2 + slope*(z-1)) on any artificial rectangle."""

    def __init__(self,log,reader,slope):
        self.journal,self.reader,self.slope = log,reader,slope
        self.budget = budget()
        self.split_ready = set()

    def value(self,f,b,d=0,**unused):
        y0,y1,z0,z1 = b
        l = y0-Q(1,2)-self.slope*(z1-1)
        h = y1-Q(1,2)-self.slope*(z0-1)
        value = (l,h) if not d else (Q(1),)*2 if d==1 else (-self.slope,)*2
        ref = str(len(self.reader.proofs))
        self.reader.proofs[ref] = (f,b,d,value)
        return ref,value


def trace_checks(tmp):
    for gentle in (True,False):
        here = tmp/f"trace-{gentle}"
        log = Journal(here,"main.Z1")
        reader = Review(here,INPUTS)
        e = SignedToy(log,reader,Q(1,128) if gentle else Q(10000))
        family = Family("Z1",e)
        a,b,u = Q(1,2)-Q(1,256),Q(1,2)+Q(1,256),Q(1)
        left = e.value("Z1",point(a,u))[0]
        right = e.value("Z1",point(b,u))[0]
        edge = (a,b,u,u)
        root = log.row("edges",record="root_interval",quantity="Z1",edge="z_min",
                       box=pack(edge),faces=[left,right],tangent=e.value("Z1",edge,1)[0],
                       status="ROOT",direction=1)
        reader.read_edges(root)
        trace = Trace(family)
        moved,outcome = trace.advance(trace.seed("z_min",root))
        if gentle:
            assert outcome=="EXTENDED" and moved is not None
            moved,second = trace.advance(moved)
            assert second=="EXTENDED" and moved is not None
        else:
            assert moved is None and outcome=="STEP_LIMIT" and not family.chart_rows
        log.close()
        reader.read_charts()
        if gentle:
            assert len(reader.charts)==2
            for line in (here/"links.jsonl").read_text().splitlines():
                reader.link(json.loads(line))
            assert root["id"] in reader.edge_links and len(reader.links["Z1"])==1
            corrupt = deepcopy(family.chart_rows[0])
            corrupt["continuation"]["exit"]["evaluation"].reverse()
            rejected(lambda:reader.trace_condition(corrupt))
    print("Artificial trace: edge → two linked charts; out-of-gate branch starts no chart.")


def schedule_checks(tmp):
    roots_in_order = spread_roots()
    assert len(roots_in_order)==len(dict(roots_in_order))==288
    blocks = set()
    for name,_ in roots_in_order[:24]:
        i,j = map(int,name[1:].split("."))
        blocks.add((i//3,j//4))
    assert len(blocks)==24
    here = tmp/"order"
    log = Journal(here,"main.Z1")
    reader = Review(here,INPUTS)
    for i,(name,geometry) in enumerate(roots_in_order[:24]):
        proof = str(i)
        reader.proofs[proof] = ("Z1",geometry,0,(Q(1),Q(2)))
        reader.enclosure_policy[proof] = "shape"
        log.row("events",record="root_visit",quantity="Z1",node=name,
                box=pack(geometry),evaluation=proof,status="VISITED")
    log.close()
    nodes = dict.fromkeys(INPUTS["quantities"],())
    assert reader.review_schedule(nodes)["Z1"]==24
    path = here/"events.jsonl"
    lines = path.read_text().splitlines()
    lines[0],lines[1] = lines[1],lines[0]
    path.write_text("\n".join(lines)+"\n")
    rejected(lambda:reader.review_schedule(nodes))
    print("Initial sweep: first 24 roots touch every macroblock; swapped visit order rejected.")

    here = tmp/"queue"
    log = Journal(here,"main.Z1")
    e = Encloser(None,log,budget())
    root_pair = roots_in_order[:2]
    root_ids = {box:name for name,box in root_pair}
    evaluated = []

    def evaluate(quantity,box,*,policy):
        assert quantity=="Z1" and policy=="shape"
        proof = f"toy-{len(evaluated)}"
        evaluated.append(box)
        if box in root_ids:
            e.split_ready.add(proof)
        return proof,(Q(-1),Q(1))

    with (patch("shape.spread_roots",return_value=root_pair),
          patch("shape.edge_roots",return_value=[]),
          patch.object(Family,"prepare_edges"),
          patch.object(e,"value",side_effect=evaluate)):
        assert Family("Z1",e).run()=="RECORDED"
    log.close()
    rows = [json.loads(s) for s in (here/"boxes.jsonl").read_text().splitlines()]
    assert [r["depth"] for r in rows]==[0,0,1,1,1,1]
    assert evaluated[:2]==[b for _,b in root_pair]
    assert [r["root"] for r in rows]==[root_pair[i][0] for i in (0,1,0,0,1,1)]
    print("Artificial scheduler: both initial visits precede any bisection; child queues stay breadth first.")


def comparison_checks(tmp):
    log = Journal(tmp/"comparison","compare")

    class NoProbes:
        journal = log
        budget = budget()

        def value(self,*args,**kwargs):
            raise AssertionError("comparison tried to build an unseeded chart")

    runner = Crossings(NoProbes(),[])
    assert runner.compare(("Z1","D2"),"INTERIOR")== (None,[])
    log.close()
    row = json.loads((tmp/"comparison/intersections.jsonl").read_text())
    assert row["status"]=="UNRESOLVED"
    print("Comparison without traced support records unresolved without new probes.")


def empty_receipt_checks(tmp):
    here = tmp/"empty"
    log = Journal(here,"main.Z1")
    log.close()
    report = dict(formula_calls=0,complete=False,allowed=False,p90_ns=None,
                  forecast_cells=32000000,estimate_ns=None)
    (here/"PILOT.json").write_text(json.dumps(report)+"\n")
    result = Review(here,INPUTS).check()
    assert result["status"]=="PARTIAL" and not result["pilot_eligible"]
    report["forecast_cells"] -= 1
    (here/"PILOT.json").write_text(json.dumps(report)+"\n")
    rejected(lambda:Review(here,INPUTS).check())
    print("Independent receipt audit: unstarted work stays partial; inconsistent forecast rejected.")


if __name__=="__main__":
    with TemporaryDirectory() as folder:
        work = Path(folder)
        midpoint_checks(work)
        trace_checks(work)
        schedule_checks(work)
        comparison_checks(work)
        empty_receipt_checks(work)
