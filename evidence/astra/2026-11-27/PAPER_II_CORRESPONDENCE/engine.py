"""Exact shape geometry, proof journal and the MPFR calculation interface."""

from contextlib import ExitStack
from ctypes import (CDLL, POINTER, Structure, byref, c_char, c_char_p, c_int, c_long,
                    c_uint, c_uint64, c_void_p)
from fractions import Fraction as Q
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
INPUTS = json.loads((HERE / "INPUTS.json").read_text())
POLICY = INPUTS["policy"]
QUANTITIES = INPUTS["quantities"]
REGION = tuple(map(Q, INPUTS["region"]))
WIDTH = tuple(map(Q, INPUTS["transverse_width"]))
EDGES = {"y_min": (0, REGION[0]), "y_max": (0, REGION[1]),
         "z_min": (1, REGION[2]), "z_max": (1, REGION[3])}
JOURNALS = ("boxes", "edges", "charts", "links", "intersections", "pending",
            "enclosures", "integrals", "events")


class Stop(Exception):
    """A declared resource limit or operator stop."""


class Inconsistent(Exception):
    """A nonfinite interval, impossible intersection or operational failure."""


def rational(value):
    n, d = value.numerator, value.denominator
    if d & (d-1):
        return {"n": str(n), "d": str(d)}
    return {"n": str(n), "e": 1-d.bit_length()}


def unrational(x):
    n = int(x["n"])
    return Q(n, int(x["d"])) if "d" in x else n * Q(2)**x["e"]


def pack(box):
    return list(map(rational, box))


def unpack(data):
    return tuple(map(unrational, data))


def section(box, axis):
    return box[2*axis:2*axis+2]


def interval_width(i):
    return i[1]-i[0]


def replace(box, axis, lo, hi):
    start = 2*axis
    return box[:start] + (lo,hi) + box[start+2:]


def cut(box, axis, x):
    lo, hi = section(box, axis)
    if not lo < x < hi:
        raise Inconsistent("shape cut outside the parent interior")
    return replace(box,axis,lo,x), replace(box,axis,x,hi)


def midpoint(bounds):
    return Q(sum(bounds),2)


def point(y,z):
    return (y,y,z,z)


def inside(a,b):
    return b[0] <= a[0] <= a[1] <= b[1] and b[2] <= a[2] <= a[3] <= b[3]


def overlay(a,b):
    c = (max(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),min(a[3],b[3]))
    return c if c[0] <= c[1] and c[2] <= c[3] else None


def covered(target, supports):
    """Closed rectangle union containment, also for lines and points."""
    slabs = [b for a in supports if (b := overlay(target,a)) is not None]
    if target in slabs:
        return True
    cuts = sorted({target[0],target[1]} | {x for b in slabs for x in b[:2]})
    probes = list(zip(cuts,cuts[1:])) or [(target[0],target[1])]
    for a,b in probes:
        reached = target[2]
        found = False
        intervals = sorted((c,d) for lo,hi,c,d in slabs if lo <= a <= b <= hi)
        for lo,hi in intervals:
            if lo <= reached <= hi:
                reached,found = hi,True
            if lo > reached:
                break
        if not found or reached < target[3]:
            return False
    return True


def roots():
    ny,nz = INPUTS["shape_grid"]
    ay,by,az,bz = REGION
    dy,dz = (by-ay)/ny,(bz-az)/nz
    return [(f"B{i:02d}.{j:02d}",(ay+i*dy,ay+(i+1)*dy,az+j*dz,az+(j+1)*dz))
            for i in range(ny) for j in range(nz)]


def spread_roots():
    """Visit one root per macroblock before advancing its local offset."""
    ny,nz = INPUTS["shape_grid"]
    sy,sz = POLICY["root_block"]
    if ny%sy or nz%sz:
        raise Inconsistent("root blocks must tile the fixed initial grid")
    grid = roots()
    return [grid[i*nz+j] for di in range(sy) for dj in range(sz)
            for i in range(di,ny,sy) for j in range(dj,nz,sz)]


def edge_box(edge, lo, hi):
    axis, position = EDGES[edge]
    return replace(replace(REGION,axis,position,position),1-axis,lo,hi)


def edge_roots(edge):
    axis,_ = EDGES[edge]
    n = INPUTS["shape_grid"][1-axis]
    lo,hi = section(REGION,1-axis)
    width = (hi-lo)/n
    return [(f"E.{edge}.{j:02d}",edge_box(edge,lo+j*width,lo+(j+1)*width)) for j in range(n)]


def extensions(bounds, limits, axis):
    lo,hi = bounds
    w = hi-lo
    seen = set()
    for extra in (0,w/2,w):
        span = (max(limits[0],lo-extra),min(limits[1],hi+extra))
        if span not in seen and 0 < interval_width(span) <= WIDTH[axis]:
            seen.add(span)
            yield span


def split_axis(box):
    dy = interval_width(section(box,0))/Q(3,4)
    dz = interval_width(section(box,1))/6
    return int(dz > dy)


def sign(value):
    return 1 if value[0] > 0 else -1 if value[1] < 0 else 0


def midpoint_limit(value):
    low,high = value
    distance = max(Q(0),low,-high)
    return max(Q(POLICY["midpoint_absolute"]),Q(POLICY["midpoint_relative"])*distance)


def meet(a,b):
    result = (max(a[0],b[0]), min(a[1],b[1]))
    if result[0] > result[1]:
        raise Inconsistent("empty intersection of two full enclosures")
    return result


def add(a,b):
    return a[0]+b[0],a[1]+b[1]


def subtract(a,b):
    return a[0]-b[1],a[1]-b[0]


def multiply(a,b):
    products = [x*y for x in a for y in b]
    return min(products),max(products)


def divide(a,b):
    if not sign(b):
        raise Inconsistent("slope division by an interval containing zero")
    return multiply(a,(Q(1)/b[1],Q(1)/b[0]))


def outward(value, bits, upward):
    """Round the exact mean-value endpoint onto the binary MPFR lattice."""
    if not value:
        return Q(0)
    a = abs(value)
    power = a.numerator.bit_length()-a.denominator.bit_length()
    if a < Q(2)**power:
        power -= 1
    unit = Q(2)**(power-bits+1)
    scaled = value/unit
    n,d = scaled.numerator,scaled.denominator
    return (-((-n)//d) if upward else n//d)*unit


class Journal:
    def __init__(self, path, prefix):
        path.mkdir(parents=True,exist_ok=False)
        self.prefix = prefix
        self.streams = {kind: (path/f"{kind}.jsonl").open("x",encoding="utf-8",buffering=1)
                        for kind in JOURNALS}
        self.count = dict.fromkeys(JOURNALS,0)

    def row(self, kind, **fields):
        self.count[kind] += 1
        number = f"{self.prefix}.{kind}.{self.count[kind]}"
        row = dict(id=number,**fields)
        self.streams[kind].write(json.dumps(row,ensure_ascii=True,separators=(",",":"))+"\n")
        return row

    def close(self):
        for stream in self.streams.values():
            stream.close()


class Budget:
    def __init__(self, deadline, cells, stop_flag):
        self.deadline = deadline
        self.max_cells = cells
        self.stop_flag = stop_flag
        self.cells = 0

    def guard(self):
        if self.stop_flag():
            raise Stop("OPERATOR_STOP")
        if time.monotonic_ns() >= self.deadline:
            raise Stop("DEADLINE")

    def allowance(self):
        self.guard()
        if self.cells >= self.max_cells:
            raise Stop("CELL_BUDGET")
        return self.max_cells-self.cells


class CResult(Structure):
    _fields_ = [("calls",c_uint64),("leaves",c_uint),("dim",c_int),
                ("lo",c_char*128),("hi",c_char*128),("lo_exp",c_long),("hi_exp",c_long)]


class Kernel:
    def __init__(self, path):
        self.lib = CDLL(str(path))
        self.lib.cb_create.argtypes = [c_int]*4+[c_char_p]*4
        self.lib.cb_create.restype = c_void_p
        self.lib.cb_destroy.argtypes = [c_void_p]
        self.lib.cb_destroy.restype = None
        self.lib.cb_extend.argtypes = [c_void_p,c_uint,c_uint64,c_uint64,POINTER(CResult)]
        self.lib.cb_extend.restype = c_int
        self.lib.cb_cell_ns.argtypes = [c_void_p,c_uint]
        self.lib.cb_cell_ns.restype = c_uint64
        self.lib.cb_sphere_reference.argtypes = [c_void_p,POINTER(c_long),c_void_p,POINTER(c_long)]
        self.lib.cb_sphere_reference.restype = c_int
        self.lib.cb_watch_stop.argtypes = [POINTER(c_int)]
        self.lib.cb_watch_stop.restype = c_int
        for name in ("cb_error","cb_mpfr","cb_gmp"):
            getattr(self.lib,name).restype = c_char_p

    def error(self):
        s = self.lib.cb_error()
        return Inconsistent(s.decode() if s else "C interval failure")

    def watch(self, flag):
        if self.lib.cb_watch_stop(byref(flag)):
            raise Inconsistent("installing the shared stop handler")

    def sphere_reference(self):
        lo,hi = (c_char*128)(),(c_char*128)()
        a,b = c_long(),c_long()
        if self.lib.cb_sphere_reference(lo,byref(a),hi,byref(b)):
            raise self.error()
        return (int(lo.value)*Q(2)**a.value,int(hi.value)*Q(2)**b.value)


class AngleTree:
    def __init__(self, engine, quantity, derivative, box, bits):
        self.e = engine
        self.f,self.d,self.box,self.bits = quantity,derivative,box,bits
        self.calls = 0
        engine.tree_serial += 1
        self.tree_id = f"{engine.journal.prefix}.tree.{engine.tree_serial}"
        self.handle = engine.kernel.lib.cb_create(
            QUANTITIES.index(quantity),derivative,bits,int(engine.measure),
            *(str(x).encode("ascii") for x in box))
        if not self.handle:
            raise engine.kernel.error()

    def __enter__(self):
        return self

    def __exit__(self,*unused):
        self.e.kernel.lib.cb_destroy(self.handle)

    def stage(self, target):
        e = self.e
        allowance = e.budget.allowance()
        out = CResult()
        started = time.monotonic_ns()
        mode = e.kernel.lib.cb_extend(self.handle,target,allowance,e.budget.deadline,byref(out))
        if out.calls < self.calls or out.calls-self.calls > allowance:
            raise Inconsistent("kernel cell count contradicts allocation")
        raw = dict(tree=self.tree_id,quantity=self.f,derivative=self.d,box=pack(self.box),precision=self.bits,
                   target=target,cells=out.leaves,dimension=out.dim,total_calls=out.calls,
                   formula_calls=out.calls-self.calls,wall_ns=time.monotonic_ns()-started,
                   trace=e.in_trace)
        e.budget.cells += raw["formula_calls"]
        if e.measure:
            raw["cell_ns"] = [e.kernel.lib.cb_cell_ns(self.handle,k)
                              for k in range(self.calls,out.calls)]
        self.calls = out.calls
        if mode:
            e.journal.row("integrals",**raw,status="INCONSISTENT" if mode < 0 else "PENDING")
            if mode < 0:
                raise e.kernel.error()
            e.budget.guard()
            raise Stop("CELL_BUDGET")
        ends = (int(out.lo)*Q(2)**out.lo_exp,int(out.hi)*Q(2)**out.hi_exp)
        if ends[0] > ends[1]:
            raise Inconsistent("backwards kernel interval")
        row = e.journal.row("integrals",**raw,status="COMPLETE",interval=pack(ends))
        return row["id"], ends


class Encloser:
    def __init__(self, kernel, journal, budget, measure=False):
        self.kernel,self.journal,self.budget,self.measure = kernel,journal,budget,measure
        self.cache = {}
        self.hits = 0
        self.tree_serial = 0
        self.split_ready = set()
        self.in_trace = False

    def value(self, quantity, box, derivative=0, *, edge=False, policy="default"):
        self.budget.guard()
        if (policy not in ("default","shape","trace") or
                (edge and policy!="default") or (policy=="shape" and derivative)):
            raise Inconsistent("invalid enclosure scheduling policy")
        key = (quantity,box,derivative,edge,policy)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        cfg = INPUTS["angular"]
        caps = cfg["stages"] if policy=="default" else POLICY["stages"]
        stages = [(cfg["precision"],n) for n in caps]
        if edge:
            stages.append((cfg["edge_precision"],cfg["edge_stage"]))
        current = None
        centre = None
        ready = False
        steps = []
        started = time.monotonic_ns()
        start_calls = self.budget.cells
        m = [midpoint(section(box,i)) for i in range(2)]
        with ExitStack() as stack:
            handles = {}

            def evaluate(where, mode, bits, cap):
                code = (where,mode,bits)
                if code not in handles:
                    handles[code] = stack.enter_context(AngleTree(self,quantity,mode,where,bits))
                return handles[code].stage(cap)

            for bits,cap in stages:
                idx, direct = evaluate(box,derivative,bits,cap)
                step = dict(precision=bits,target=cap,direct=idx)
                current = direct if current is None else meet(current,direct)
                steps.append(step)
                if sign(current):
                    break
                if derivative == 0 and (box[0] < box[1] or box[2] < box[3]):
                    mid_id, mid = evaluate(point(*m),0,bits,cap)
                    step["midpoint"] = mid_id
                    if policy=="shape":
                        centre = mid if centre is None else meet(centre,mid)
                        limit = midpoint_limit(centre)
                        ready = interval_width(centre)<=limit
                        step.update(midpoint_interval=pack(centre),midpoint_limit=rational(limit),
                                    midpoint_ok=ready)
                        if not ready:
                            continue
                        mid = centre
                    mode_ids = []
                    mv = mid
                    for axis,center in enumerate(m):
                        lo,hi = section(box,axis)
                        if lo == hi:
                            mode_ids.append(None)
                            continue
                        ident, grad = evaluate(box,axis+1,bits,cap)
                        part = multiply((lo-center,hi-center),grad)
                        mode_ids.append(ident)
                        mv = add(mv,part)
                    mv = (outward(mv[0],bits,False),outward(mv[1],bits,True))
                    step["gradients"],step["mean"] = mode_ids,pack(mv)
                    current = meet(current,mv)
                if sign(current) or ready:
                    break
        row = self.journal.row("enclosures",quantity=quantity,box=pack(box),derivative=derivative,
                               edge_retry=edge,policy=policy,split_ready=ready,stages=steps,
                               interval=pack(current),wall_ns=time.monotonic_ns()-started,
                               formula_calls=self.budget.cells-start_calls)
        answer = (row["id"],current)
        if ready:
            self.split_ready.add(row["id"])
        self.cache[key] = answer
        return answer
