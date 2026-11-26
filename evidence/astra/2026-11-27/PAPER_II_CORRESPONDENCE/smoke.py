"""Analytic sphere and artificial graph tests. No task from the shape bands is run."""

import argparse
from ctypes import c_int
from fractions import Fraction as F
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from engine import Budget, Journal, Kernel, pack
from inheritance import CFG
from proof_rules import krawczyk
from run_correspondence import Native,cover
from verify_correspondence import exercise
from verify_v2 import spherical_pole


def angular_algebra():
    # F(gamma)=gamma^2. Compare division of two rotated Taylor series
    # with the factored angular derivative before integration.
    t = F(3,5)
    w = (-t,F(12,25),F(16,25))
    mu = 1-2*t**2
    xi = (mu,2*t*w[1],2*t*w[2])
    axes = (F(9,16),F(1),F(4))
    reciprocal = tuple(1/a for a in axes)
    sigma = axes[1]-axes[0]

    def quadratic_form(diagonal,vector):
        x,y,z = vector
        components = ((x,-y,-x/2),(y,x,-y/2),(z,F(0),F(0)))
        return tuple(sum(axis*sum(v[j]*v[n-j] for j in range(n+1))
                         for axis,v in zip(diagonal,components,strict=True)) for n in range(3))

    d,B = quadratic_form(axes,w),quadratic_form(reciprocal,xi)
    P = tuple(sum(d[j]*B[n-j] for j in range(n+1)) for n in range(3))
    direct = 8*t**5*(P[1]**2-P[0]*P[2])/P[0]**3
    m = reciprocal[0]*reciprocal[1]
    a,b = 2*t/d[0],4*m*t*mu/B[0]
    U2, P2 = w[1]**2*(a*a+b*b),w[1]**2*(a+b)**2
    S2 = 2*(t*t-w[1]**2)/d[0]-2*m*(mu*mu-xi[1]**2)/B[0]
    factored = 4*t**5/P[0]*sigma*(-S2+sigma*(U2+P2))
    assert direct==factored
    print("Artificial angular coefficient: rotation of two rational forms agrees exactly.")


class Artificial:
    def __init__(self,folder):
        self.journal = Journal(folder,"correspondence")
        self.calls = 0
        self.serial = 0
        self.budget = Budget(time.monotonic_ns()+10**10,10**7,lambda:False)

    def one(self,f,b,d,n):
        self.serial += 1
        centre = F(161,256)
        if f=="AZ":
            v = (F(1),)*2
        elif f=="KY":
            v = (F(int(d==1)),)*2 if d else (b[0]-centre,b[1]-centre)
        else:
            v = (F(int(d==2)),)*2 if d else (b[2]-F(17,8),b[3]-F(17,8))
        cells = 16+4*((n-16)//3)
        self.calls += cells
        row = self.journal.row("integrals",tree=f"correspondence.tree.{self.serial}",
                               quantity=f,box=pack(b),derivative=d,target=n,precision=128,
                               trace=False,formula_calls=cells,total_calls=cells,dimension=2,cells=n,
                               interval=pack(v),status="COMPLETE")
        return row["id"],v

    def sign(self,f,b):
        return self.one(f,b,0,CFG["stages"][-1])


def artificial(path):
    b = tuple(map(F,["1/2","3/4","2","9/4"]))
    charts = {("Z1","artificial_chart"):(b,1,(F(1),F(1)),"artificial transverse")}
    test = Artificial(path/"work")
    cover(test,charts)
    test.journal.close()
    receipt = dict(status="RECORDED",formula_calls=test.calls)
    tested = exercise(charts,path,receipt)
    assert tested["status"]=="CONDITIONS_RECORDED" and tested["exact_chart_tasks"]==2
    event, = tested["possible_repeated_events"]
    box = list(map(F,event["location"]))
    assert event["method"]=="GRAPH_ZERO" and box[0]<F(161,256)<box[1]
    jac = [[(F(0),)*2,(F(1),)*2],[(F(1),)*2,(F(0),)*2]]
    c = (F(sum(b[:2]),2),F(sum(b[2:]),2))
    kr = krawczyk(b,[(F(0),)*2,(c[0]-F(161,256),)*2],jac)
    assert kr["strict"] and kr["q"]=="0"
    file = path/"work/boxes.jsonl"
    proof = file.read_text()
    corrupted = json.loads(proof.splitlines()[0])
    corrupted["box"][0] = pack((F(1,4),))[0]
    lines = [json.dumps(corrupted),*proof.splitlines()[1:]]
    file.write_text("\n".join(lines)+"\n")
    try:
        exercise(charts,path,receipt)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered cover was accepted")
    print("Artificial checks: full bisection, monotone graph zero, Krawczyk and tamper rejection.")


def native(path,library):
    kernel = Kernel(library.resolve())
    stop = c_int(0)
    kernel.watch(stop)
    journal = Journal(path/"native","sphere")
    p = Native(kernel,journal,Budget(time.monotonic_ns()+20*10**9,5000,lambda:False))
    box = (F(1),)*4
    pi = spherical_pole()  # exact-rational enclosure of pi^2/32
    radial = -6*pi[1]-F(1,2), -6*pi[0]-F(1,2)
    angular = F(9,2)*pi[0]-F(1,2), F(9,2)*pi[1]-F(1,2)
    tests = [("AZ",0,(F(4,3),)*2),("KY",0,(-F(16,3),)*2),("KX",0,(-F(16,3),)*2),
             ("MY",0,radial),("MX",0,radial),("CYX",0,angular),("CXY",0,angular),
             ("CYZ",0,angular),("CXZ",0,angular),("KY",1,(-F(416,105),)*2)]
    try:
        for f,d,reference in tests:
            _,v = p.one(f,box,d,64)
            assert v[0]<=reference[0]<=reference[1]<=v[1],(f,d,v,reference)
    finally:
        journal.close()
    print(f"Native MPFR analytic sphere: {len(tests)} inclusions, {p.budget.cells} panels, including F order 9.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library",type=Path)
    args = p.parse_args()
    angular_algebra()
    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        artificial(path)
        if args.library:
            native(path,args.library)


if __name__=="__main__":
    main()
