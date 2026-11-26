"""Walk certified edge roots into the interior using signed transverse gates."""

from collections import deque
from dataclasses import dataclass, replace as updated

from engine import EDGES, POLICY, REGION, WIDTH, Q, Stop, inside, pack, point, section, sign, unpack


def station_point(base, u, v):
    return point(u,v) if base==0 else point(v,u)


def support(base, u, v):
    return (*u,*v) if base==0 else (*v,*u)


@dataclass(frozen=True)
class Frontier:
    origin: dict
    base: int
    u: Q
    advance: int
    bounds: tuple
    refs: tuple
    direction: int
    step: Q

    def gate(self):
        return testimony(self.base,self.u,self.bounds,self.refs)


def testimony(base, u, bounds, refs):
    return dict(points=[pack(station_point(base,u,v)) for v in bounds],evaluation=list(refs))


class Trace:
    def __init__(self, family):
        self.family = family
        self.e,self.f,self.emit = family.e,family.f,family.emit
        self.max_steps = tuple(map(Q,POLICY["trace_step"]))
        self.halvings = POLICY["trace_halvings"]
        self.gate_fraction = Q(POLICY["trace_gate_fraction"])

    def seed(self, edge, root):
        base,u = EDGES[edge]
        v = 1-base
        low,high = section(unpack(root["box"]),v)
        # Reuse the two edge point evaluations already certified by edge_task.
        advance = 1 if edge.endswith("_min") else -1
        return Frontier(root,base,u,advance,(low,high),tuple(root["faces"]),
                        root["direction"],self.max_steps[base])

    def tighten(self, front):
        low,high = front.bounds
        left,right = front.refs
        goal = WIDTH[1-front.base]*self.gate_fraction
        while high-low>goal:
            old = (low,high)
            mid = (low+high)/2
            for v in (mid,(low+mid)/2,(mid+high)/2):
                if not low<v<high:
                    continue
                proof,f = self.e.value(self.f,station_point(front.base,front.u,v),policy="trace")
                s = sign(f)
                if s==-front.direction:
                    low,left = v,proof
                elif s==front.direction:
                    high,right = v,proof
                if s and v==mid:
                    break
            if old==(low,high):
                break
        return updated(front,bounds=(low,high),refs=(left,right))

    def existing(self, front):
        gate = support(front.base,(front.u,)*2,front.bounds)
        for previous in self.family.chart_rows:
            if previous["id"]==front.origin["id"]:
                continue
            box = unpack(previous["box"])
            a,b = section(box,front.base)
            moves_ahead = front.u<b if front.advance>0 else a<front.u
            if moves_ahead and inside(gate,box):
                self.family.record_link(front.origin,previous,front.gate())
                return previous["id"]
        return None

    def advance(self, front):
        a,b = section(REGION,front.base)
        distance = b-front.u if front.advance>0 else front.u-a
        if not distance:
            return None,"DOMAIN_BOUNDARY"
        front = self.tighten(front)
        if self.existing(front):
            return None,"JOINED"
        cross = 1-front.base
        lo,hi = section(REGION,cross)
        width = WIDTH[cross]
        low = min(max(lo, sum(front.bounds)/2-width/2),hi-width)
        bounds = (low,low+width)
        first = min(front.step,distance)
        minimum = self.max_steps[front.base]/(2**self.halvings)
        for k in range(self.halvings+1):
            step = first/(2**k)
            if k and step<minimum:
                break
            far = front.u+front.advance*step
            refs = []
            for j,v in enumerate(bounds):
                proof,f = self.e.value(self.f,station_point(front.base,far,v),policy="trace")
                refs.append(proof)
                if sign(f)!=(-1 if j==0 else 1)*front.direction:
                    break
            else:
                footprint = support(front.base,tuple(sorted((front.u,far))),bounds)
                continuation = dict(origin=front.origin["id"],from_u=pack((front.u,))[0],
                                    to_u=pack((far,))[0],entry=front.gate(),
                                    exit=testimony(front.base,far,bounds,refs))
                row = self.family.chart(footprint,cross,continuation)
                if row:
                    self.family.record_link(front.origin,row,front.gate())
                    return Frontier(row,front.base,far,front.advance,bounds,tuple(refs),
                                    front.direction,min(2*step,self.max_steps[front.base])),"EXTENDED"
                continue
            self.emit("events",record="trace_probe",quantity=self.f,origin=front.origin["id"],
                      cross=cross,at=pack((far,))[0],bounds=pack(bounds),evaluations=refs,
                      status="NO_OPPOSITE_SIGNS")
        return None,"STEP_LIMIT"

    def run(self):
        fronts = deque(self.seed(e,r) for e,listed in self.family.edge_rows.items() for r in listed)
        current = None
        try:
            while fronts:
                current = fronts.popleft()
                self.e.budget.guard()
                moved,outcome = self.advance(current)
                if moved:
                    fronts.append(moved)
                else:
                    self.emit("events",record="trace_end",quantity=self.f,origin=current.origin["id"],
                              at=pack((current.u,))[0],status=outcome)
                    if outcome=="STEP_LIMIT":
                        self.emit("pending",quantity=self.f,phase="trace",origin=current.origin["id"],
                                  at=pack((current.u,))[0],reason=outcome)
                current = None
        except Stop as problem:
            if current is not None:
                fronts.appendleft(current)
            for front in fronts:
                self.emit("pending",quantity=self.f,phase="trace",origin=front.origin["id"],
                          at=pack((front.u,))[0],reason=str(problem))
            raise
