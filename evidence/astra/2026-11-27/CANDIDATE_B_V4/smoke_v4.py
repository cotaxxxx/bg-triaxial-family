"""Artificial exact tests for the v4 journal and rational checks."""

from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ancestors import PAIR, SPEC, X, project_faces
from engine import Journal, pack
from run_candidate_b_v4 import run_trials
from verify_v2 import rows, strict
from verify_v4 import BOXES, CENTRE, review_trials


def rejected(what):
    try:
        what()
    except ValueError:
        return
    raise AssertionError("edited certificate was accepted")


def check_faces():
    y0,y1,z0,z1 = X
    a,b = (3*y0+y1)/4,(y0+3*y1)/4
    connector = (z0+z1)/2
    p = [
        ("left-strip", (a,b,z0,connector), ("f.1","f.2"), [(-F(1,8),)*2,(F(1,8),)*2]),
        ("right-strip", (a,b,connector,z1), ("f.3","f.4"), [(-F(1,8),)*2,(F(1,8),)*2]),
    ]
    faces = project_faces(X,0,p,(F(1),F(2)),1)
    assert [strict(row[-1]) for row in faces]==[-1,1,-1,1]
    q = [("bottom-strip", (y0,y1,(3*z0+z1)/4,(z0+3*z1)/4), ("g.1","g.2"),
          [(F(1,8),)*2,(-F(1,8),)*2])]
    assert [strict(row[-1]) for row in project_faces(X,1,q,(-F(2),-F(1)),-1)]==[1,-1]
    rejected(lambda:project_faces(X,0,p[:1],(F(1),F(2)),1))


class Artificial:
    def __init__(self,path, *, contain=True):
        self.out = Journal(path,"v4.local")
        self.created = 0
        self.calls = 0
        delta = F(1,8192) if contain else F(1,256)
        self.root = CENTRE[0]+delta,CENTRE[1]-delta
        self.a = [(F(2),-F(1,2)),(-F(1,8),-F(1))]
        self.contain = contain

    @contextmanager
    def open(self, f, derivative, box):
        self.created += 1
        yield self.FakeTree(self,f,derivative,box,self.created)

    class FakeTree:
        def __init__(self,model,f,derivative,box,serial):
            self.model,self.f,self.d,self.b = model,f,derivative,box
            self.serial,self.calls = serial,0

        def stage(self,target):
            model = self.model
            row = model.a[PAIR.index(self.f)]
            if self.d == 0:
                value = sum(c*(u-v) for c,u,v in zip(row,CENTRE,model.root,strict=True))
                width = F(0)
            else:
                value = row[self.d-1]
                width = F(2) if target==256 else F(0)
            enclosure = value-width,value+width
            cumulative = 16+4*((target-16)//3)
            charge = cumulative-self.calls
            model.calls += charge
            self.calls = cumulative
            receipt = model.out.row(
                "integrals", tree=f"v4.local.tree.{self.serial}", quantity=self.f,
                derivative=self.d,box=pack(self.b),precision=128,target=target,cells=target,
                dimension=2,total_calls=cumulative,formula_calls=charge,trace=False,status="COMPLETE",
                interval=pack(enclosure),
            )
            return receipt["id"],enclosure


def check_trials(work):
    hit = work/"hit"
    test = Artificial(hit)
    state = run_trials(test.open,test.out.row)
    test.out.close()
    run = dict(status=state,elapsed_ns=1,formula_calls=test.calls)
    root, witness, attempts, charge = review_trials(hit,run,True)
    y,z = test.root
    assert root==(y,y,z,z) and charge==test.calls
    assert witness["box_index"]==0 and witness["stage"]==1024 and attempts[0]["failed"]
    k_rows = list(rows(hit,"intersections"))
    modified = deepcopy(k_rows)
    modified[1]["test"]["q"] = pack((F(1,8),))[0]
    file = hit/"intersections.jsonl"
    file.write_text("".join(json.dumps(r)+"\n" for r in modified))
    rejected(lambda:review_trials(hit,run,True))
    file.write_text("".join(json.dumps(r)+"\n" for r in k_rows))
    rejected(lambda:review_trials(hit,run,False))
    rejected(lambda:review_trials(hit,{**run,"formula_calls":0},True))

    miss = work/"miss"
    test = Artificial(miss,contain=False)
    state = run_trials(test.open,test.out.row)
    test.out.close()
    run = dict(status=state,elapsed_ns=1,formula_calls=test.calls)
    root, witness, attempts, charge = review_trials(miss,run,True)
    assert root is None and witness is None and len(attempts)==9
    assert test.created==2+4*len(BOXES) and charge==SPEC["krawczyk"]["max_formula_calls"]


def main():
    check_faces()
    print("Artificial faces: both orientations, full strips and rejection of a seam gap.")
    with TemporaryDirectory() as temp:
        check_trials(Path(temp))
    print("Artificial Krawczyk: first successful cap, centre reuse, norm tamper and gate rejection.")
    print("Artificial exhaustion: all 9 trials and the exact 76,384-panel cap.")


if __name__ == "__main__":
    main()
