"""Candidate B shape, boundary, chart and connection searches."""

from collections import deque
from dataclasses import dataclass
from itertools import combinations, product

from engine import (EDGES, INPUTS, REGION, WIDTH, Inconsistent, Stop, covered,
                    cut, edge_box, edge_roots, extensions, inside, midpoint,
                    overlay, pack, point, replace, section, sign, spread_roots,
                    split_axis, unpack, Q)
from trace_bands import Trace


def signed_pair(lo,hi,gradient):
    return sign(lo) != 0 and sign(hi) == -sign(lo) and sign(gradient) == sign(hi)


def point_at(axis, x, other):
    return point(x,other) if axis == 0 else point(other,x)


def chart_faces(box, cross):
    return [replace(box,cross,v,v) for v in section(box,cross)]


@dataclass(frozen=True)
class Task:
    name: str
    root: str
    box: tuple
    depth: int = 0
    parent: str | None = None
    edge: str | None = None

    def fields(self):
        fields = dict(node=self.name,root=self.root,parent=self.parent,depth=self.depth,
                      box=pack(self.box))
        if self.edge:
            fields["edge"] = self.edge
        return fields

    def children(self,axis,middle):
        boxes = cut(self.box,axis,middle)
        return [Task(f"{self.name}/{i}",self.root,b,self.depth+1,self.name,self.edge)
                for i,b in enumerate(boxes)]


class Family:
    def __init__(self, quantity, engine):
        self.f = quantity
        self.e = engine
        self.budget = engine.budget
        self.emit = engine.journal.row
        self.chart_rows = []
        self.trace_links = []
        self.linked_pairs = set()
        self.edge_rows = {edge: [] for edge in EDGES}
        self.tried = set()
        self.examined = 0
        self.task_count = INPUTS["budget"]["boxes_per_quantity"]
        self.chart_count = INPUTS["budget"]["chart_trials_per_quantity"]
        edge_queue = [Task(n,n,b,edge=edge) for edge in EDGES for n,b in edge_roots(edge)]
        box_queue = [Task(n,n,b) for n,b in spread_roots()]
        self.queue = deque(edge_queue+box_queue)
        self.deferred = {}
        self.phase = "anchors"

    def next_trial(self):
        self.budget.guard()
        if self.examined >= self.task_count:
            raise Stop("SHAPE_BOX_BUDGET")
        self.examined += 1

    def prepare_edges(self):
        for edge,anchor in INPUTS["expected_edges"][self.f].items():
            if anchor is None:
                continue
            cfg = INPUTS["anchors"][anchor]
            bounds = tuple(map(Q,cfg["interval"]))
            paper = tuple(map(Q,cfg["paper"]))
            if not bounds[0] < paper[0] < paper[1] < bounds[1]:
                raise Inconsistent("Paper I interval is outside the frozen wide bracket")
            checks = []
            for x in bounds:
                self.next_trial()
                checks.append(self.e.value(self.f,edge_box(edge,x,x),edge=True))
            self.emit("edges",record="anchor",quantity=self.f,edge=edge,anchor=anchor,
                      endpoints=pack(bounds),paper=pack(paper),
                      evaluation=[a[0] for a in checks],
                      status="MATCH" if [sign(a[1]) for a in checks] == cfg["signs"]
                      else "UNRESOLVED")
        for y,z in product(section(REGION,0),section(REGION,1)):
            self.next_trial()
            where = point(y,z)
            proof,i = self.e.value(self.f,where,edge=True)
            self.emit("edges",record="corner",quantity=self.f,box=pack(where),
                      evaluation=proof,status="NONZERO" if sign(i) else "UNRESOLVED")

    def node(self, task, status, **fields):
        stream = "edges" if task.edge else "boxes"
        return self.emit(stream,record="node",quantity=self.f,status=status,**task.fields(),**fields)

    def subdivide(self, task, axis, status_proof, location=None, root_cut=None):
        depth_limit = INPUTS["budget"]["edge_depth" if task.edge else "shape_depth"]
        if task.depth >= depth_limit:
            self.node(task,"UNRESOLVED",evaluation=status_proof,reason="DEPTH_LIMIT")
            self.emit("pending",quantity=self.f,phase=self.phase,reason="DEPTH_LIMIT",**task.fields())
            return []
        # The only non-midpoint split is a certified root-bracket endpoint on an edge.
        location = midpoint(section(task.box,axis)) if location is None else location
        children = task.children(axis,location)
        self.node(task,"SPLIT",axis=axis,cut=pack((location,))[0],
                  children=[c.name for c in children],evaluation=status_proof,root_cut=root_cut)
        return children

    def edge_task(self, task):
        edge = task.edge
        axis = 1-EDGES[edge][0]
        known = self.edge_rows[edge]
        for root in known:
            b = unpack(root["box"])
            if inside(task.box,b):
                self.node(task,"IN_ROOT",root_interval=root["id"])
                return []
            lo,hi = section(task.box,axis)
            if overlay(task.box,b) is not None:
                for x in section(b,axis):
                    if lo < x < hi:
                        return self.subdivide(task,axis,None,x,root["id"])
        proof, value = self.e.value(self.f,task.box,edge=True)
        if sign(value):
            self.node(task,"SIGN_POS" if sign(value)>0 else "SIGN_NEG",evaluation=proof)
            return []
        for lo,hi in extensions(section(task.box,axis),section(REGION,axis),axis):
            box = edge_box(edge,lo,hi)
            if any(overlay(box,unpack(row["box"])) is not None for row in known):
                continue
            left,a = self.e.value(self.f,edge_box(edge,lo,lo),edge=True)
            right,b = self.e.value(self.f,edge_box(edge,hi,hi),edge=True)
            if sign(a) == 0 or sign(a) != -sign(b):
                continue
            tangent,grad = self.e.value(self.f,box,axis+1,edge=True)
            if not signed_pair(a,b,grad):
                continue
            root = self.emit("edges",record="root_interval",quantity=self.f,edge=edge,
                             box=pack(box),faces=[left,right],tangent=tangent,
                             direction=sign(b),status="ROOT")
            known.append(root)
            self.node(task,"IN_ROOT",root_interval=root["id"],evaluation=proof)
            return []
        return self.subdivide(task,axis,proof)

    def chart(self, box, cross, continuation):
        key = (box,cross)
        if key in self.tried:
            return None
        if len(self.tried) >= self.chart_count:
            raise Stop("CHART_TRIAL_BUDGET")
        self.tried.add(key)
        left,right = chart_faces(box,cross)
        l,a = self.e.value(self.f,left,policy="trace")
        r,b = self.e.value(self.f,right,policy="trace")
        gradient = None
        ok = False
        if sign(a) and sign(a) == -sign(b):
            gradient,d = self.e.value(self.f,box,cross+1,policy="trace")
            ok = signed_pair(a,b,d)
        row = self.emit("charts",record="chart",quantity=self.f,box=pack(box),
                        cross=cross,base=1-cross,faces=[l,r],transverse=gradient,
                        direction=sign(b) if ok else 0,
                        continuation=continuation,
                        width=pack((section(box,cross)[1]-section(box,cross)[0],))[0],
                        status="CHART" if ok else "REJECTED")
        if ok:
            self.chart_rows.append(row)
            return row
        return None

    def shape_task(self, task, evaluation):
        proof,i = evaluation
        if sign(i):
            self.node(task,"SIGN_POS" if sign(i)>0 else "SIGN_NEG",evaluation=proof)
            return []
        possible = [(row["id"],unpack(row["box"])) for row in self.chart_rows]
        single = next((name for name,b in possible if inside(task.box,b)),None)
        if single:
            self.node(task,"IN_CHART_UNION",evaluation=proof,charts=[single])
            return []
        relevant = [(name,b) for name,b in possible if overlay(task.box,b) is not None]
        if covered(task.box,[b for _,b in relevant]):
            self.node(task,"IN_CHART_UNION",evaluation=proof,charts=[name for name,_ in relevant])
            return []
        if proof not in self.e.split_ready:
            reason = "MIDPOINT_ANGLE_LIMIT"
            self.node(task,"UNRESOLVED",evaluation=proof,reason=reason)
            self.emit("pending",quantity=self.f,phase="boxes",reason=reason,**task.fields())
            return []
        return self.subdivide(task,split_axis(task.box),proof)

    def record_link(self, origin, chart, witness):
        overlap = overlay(unpack(origin["box"]),unpack(chart["box"]))
        if overlap is None:
            raise Inconsistent("trace link has no common rectangle")
        edge = origin["record"]=="root_interval"
        a,b = (chart["id"],origin["id"]) if edge else (origin["id"],chart["id"])
        key = frozenset((a,b))
        if key in self.linked_pairs:
            return
        self.linked_pairs.add(key)
        self.trace_links.append((a,b,edge))
        self.emit("links",record="edge_link" if edge else "chart_link",quantity=self.f,a=a,b=b,
                  overlap=pack(overlap),witness=witness,status="LINKED")

    def connect(self):
        ids = {row["id"]: row["id"] for row in self.chart_rows}

        def group(name):
            while ids[name] != name:
                name = ids[name]
            return name

        linked_edges = set()
        for a,b,edge in self.trace_links:
            if edge:
                linked_edges.add(b)
            else:
                ids[group(a)] = group(b)
        for a,b in combinations(self.chart_rows,2):
            self.budget.guard()
            if group(a["id"]) == group(b["id"]):
                continue
            overlap = overlay(unpack(a["box"]),unpack(b["box"]))
            if overlap is None:
                continue
            row = link_witness(self.e,self.f,overlap)
            self.emit("links",record="chart_link",quantity=self.f,a=a["id"],b=b["id"],
                      overlap=pack(overlap),witness=row,status="LINKED" if row else "UNRESOLVED")
            if row:
                ids[group(a["id"])] = group(b["id"])
        for roots_on_edge in self.edge_rows.values():
            for root in roots_on_edge:
                if root["id"] in linked_edges:
                    continue
                for chart in self.chart_rows:
                    self.budget.guard()
                    overlap = overlay(unpack(chart["box"]),unpack(root["box"]))
                    if overlap is None:
                        continue
                    row = link_witness(self.e,self.f,overlap,edge=True)
                    self.emit("links",record="edge_link",quantity=self.f,a=chart["id"],b=root["id"],
                              overlap=pack(overlap),witness=row,
                              status="LINKED" if row else "UNRESOLVED")
                    if row:
                        break
        self.emit("links",record="components",quantity=self.f,
                  groups={name:group(name) for name in ids},status="RECORDED")

    def run_trace(self):
        start = self.budget.cells
        total = self.budget.max_cells
        cap = INPUTS["budget"]["trace_cells_per_quantity"]
        self.budget.max_cells = min(total,start+cap)
        self.e.in_trace = True
        outcome = "RECORDED"
        try:
            Trace(self).run()
            self.connect()
        except Stop as exc:
            outcome = str(exc)
            if not (outcome=="CHART_TRIAL_BUDGET" or
                    (outcome=="CELL_BUDGET" and self.budget.max_cells<total)):
                raise
            self.emit("pending",quantity=self.f,phase="trace",reason=outcome)
        except Inconsistent:
            outcome = "INCONSISTENT"
            raise
        finally:
            self.e.in_trace = False
            self.budget.max_cells = total
            self.emit("events",record="trace_budget",quantity=self.f,formula_calls=self.budget.cells-start,
                      status=outcome)

    def run(self):
        try:
            self.prepare_edges()
            self.phase = "edges"
            while self.queue and self.queue[0].edge:
                task = self.queue[0]
                self.next_trial()
                children = self.edge_task(task)
                self.queue.popleft()
                self.queue.extendleft(reversed(children))
            self.phase = "sweep"
            waiting = deque()
            while self.queue:
                task = self.queue[0]
                self.next_trial()
                proof,i = self.e.value(self.f,task.box,policy="shape")
                self.emit("events",record="root_visit",quantity=self.f,node=task.name,
                          box=pack(task.box),evaluation=proof,status="VISITED")
                if sign(i):
                    self.node(task,"SIGN_POS" if sign(i)>0 else "SIGN_NEG",evaluation=proof)
                else:
                    self.deferred[task.name] = (task,(proof,i))
                    waiting.append(task)
                self.queue.popleft()
            self.queue = waiting
            self.phase = "trace"
            self.run_trace()
            self.phase = "boxes"
            while self.queue:
                task = self.queue[0]
                if task.name in self.deferred:
                    _,evaluation = self.deferred[task.name]
                else:
                    self.next_trial()
                    evaluation = self.e.value(self.f,task.box,policy="shape")
                children = self.shape_task(task,evaluation)
                self.queue.popleft()
                self.deferred.pop(task.name,None)
                self.queue.extend(children)
        except (Stop,Inconsistent) as problem:
            pending = {task.name:task for task in self.queue}
            pending.update({name:task for name,(task,_) in self.deferred.items()})
            for task in pending.values():
                self.emit("pending",quantity=self.f,phase="edges" if task.edge else "boxes",
                          reason=str(problem),**task.fields())
            self.emit("pending",quantity=self.f,phase=self.phase,reason=str(problem))
            return "INCONSISTENT" if isinstance(problem,Inconsistent) else "STOPPED"
        return "RECORDED"


def link_witness(engine, quantity, overlap, edge=False):
    """A signed line segment contained in both charts (or chart and edge root)."""
    tests = set()
    for subdivisions in (1,4):
        for axis in range(2):
            lo,hi = section(overlap,axis)
            a,b = section(overlap,1-axis)
            if not a < b:
                continue
            candidates = [midpoint((lo,hi)),lo,hi] if subdivisions == 1 else [
                lo+(hi-lo)/4, hi-(hi-lo)/4]
            for x in candidates:
                if (axis,x) in tests:
                    continue
                tests.add((axis,x))
                p,q = point_at(axis,x,a),point_at(axis,x,b)
                li,l = engine.value(quantity,p,edge=edge)
                ri,r = engine.value(quantity,q,edge=edge)
                if sign(l) and sign(l) == -sign(r):
                    return dict(points=[pack(p),pack(q)],evaluation=[li,ri])
    return None
