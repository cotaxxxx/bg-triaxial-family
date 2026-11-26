"""Compare certified graphs and account for every overlapping pair of primary charts."""

from itertools import combinations

from engine import (INPUTS, QUANTITIES, REGION, Stop, covered, cut, divide,
                    midpoint, overlay, pack, point, replace,
                    section, sign, split_axis, subtract, unpack, Q)


def face_sample(chart, index):
    z = unpack(chart["box"])[2+index]
    return z,chart["faces"][index]


def seam(a,b,y):
    left = max((face_sample(c,0) for c in (a,b)),key=lambda x:x[0])
    right = min((face_sample(c,1) for c in (a,b)),key=lambda x:x[0])
    if left[0] >= right[0]:
        return None
    return dict(y=pack((y,))[0],z=pack((left[0],right[0])),
                evaluation=[left[1],right[1]])


class Crossings:
    def __init__(self, engine, rows):
        self.e = engine
        self.emit = engine.journal.row
        self.budget = engine.budget
        self.primary = {f:[r for r in rows if r["quantity"]==f and r["status"]=="CHART"]
                        for f in QUANTITIES}
        self.directions = {r["id"]:r["direction"] for r in rows if r["status"]=="CHART"}

    def atlas_chart(self,f,span,z_bounds,previous):
        for chart in self.primary[f]:
            if chart["cross"] != 1:
                continue
            a,b,c,d = unpack(chart["box"])
            if not (a <= span[0] < span[1] <= b and z_bounds[0] <= c < d <= z_bounds[1]):
                continue
            if previous and not self.can_join(previous,chart,span[0]):
                continue
            return chart
        return None

    def can_join(self,a,b,y):
        if self.directions[a["id"]] != self.directions[b["id"]]:
            return None
        return seam(a,b,y)

    def slopes(self, charts, span):
        ids,values = [],[]
        for chart in charts:
            box = replace(unpack(chart["box"]),0,*span)
            f = chart["quantity"]
            dy,iv_y = self.e.value(f,box,1,policy="trace")
            dz,iv_z = self.e.value(f,box,2,policy="trace")
            if not sign(iv_z):
                # Transverse derivative is already strict on the containing chart.
                dz,iv_z = self.e.value(f,unpack(chart["box"]),2,policy="trace")
            if not sign(iv_z):
                return None
            d = divide(iv_y,iv_z)
            ids.append([dy,dz])
            values.append((-d[1],-d[0]))
        return ids,subtract(*values)

    def sample(self, charts, y):
        proofs,intervals = [],[]
        for chart in charts:
            lo,hi = unpack(chart["box"])[2:]
            left,right = chart["faces"]
            direction = self.directions[chart["id"]]
            f = chart["quantity"]
            # Enclose a single root by an opposing-sign bracket in the chart.
            while hi-lo > Q(1,4096):
                middle = (lo+hi)/2
                before = (lo,hi)
                for x in (middle,(lo+middle)/2,(middle+hi)/2):
                    if not lo < x < hi:
                        continue
                    ident,value = self.e.value(f,point(y,x),policy="trace")
                    s = sign(value)
                    if s == -direction:
                        lo,left = x,ident
                    if s == direction:
                        hi,right = x,ident
                    if x == middle and s:
                        break
                if (lo,hi) == before:
                    break
            proofs.append(dict(chart=chart["id"],z=pack((lo,hi)),evaluation=[left,right]))
            intervals.append((lo,hi))
        return dict(y=pack((y,))[0],roots=proofs,order=sign(subtract(*intervals)))

    def compare(self, pair, mode):
        if mode == "INTERIOR":
            window = tuple(map(Q,INPUTS["interior_crossing"]["window"]))
            y_range,z_bounds = window[:2],window[2:]
        else:
            y_range = tuple(map(Q,INPUTS["shared_end"]["y"]))
            z_bounds = section(REGION,1)
        cuts = {x for f in pair for c in self.primary[f] if c["cross"]==1
                for x in section(unpack(c["box"]),0) if y_range[0] < x < y_range[1]}
        points = sorted(set(y_range)|cuts)
        pending = [(lo,hi,0) for lo,hi in reversed(list(zip(points,points[1:])))]
        pieces = []
        joins = []
        selected = []
        previous = [None,None]
        while pending:
            self.budget.guard()
            lo,hi,depth = pending.pop()
            span = (lo,hi)
            charts = [self.atlas_chart(f,span,z_bounds,p) for f,p in zip(pair,previous)]
            result = self.slopes(charts,span) if all(charts) else None
            if not result or not sign(result[1]):
                if depth == INPUTS["budget"]["shape_depth"]:
                    return self.unresolved(pair,mode,"AUXILIARY_GRAPH_OR_SLOPE")
                mid = (lo+hi)/2
                pending.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
                continue
            refs,difference = result
            if pieces and sign(unpack(pieces[0]["difference"])) != sign(difference):
                return self.unresolved(pair,mode,"SLOPE_SIGN_CHANGES")
            if pieces:
                common = [self.can_join(a,b,lo) for a,b in zip(previous,charts)]
                if not all(common):
                    return self.unresolved(pair,mode,"UNJOINED_GRAPHS")
                joins.append(common)
            row = dict(y=pack(span),charts=[c["id"] for c in charts],gradient=refs,
                       difference=pack(difference))
            pieces.append(row)
            selected.append((span,charts))
            previous = charts
        result = dict(record="comparison",pair=list(pair),mode=mode,y=pack(y_range),pieces=pieces,
                      joins=joins)
        if mode == "SHARED":
            # Same-type quantities agree at y=1 by the rotational identity.
            common = self.can_join(*previous,y_range[1])
            if not common:
                return self.unresolved(pair,mode,"SHARED_ROOT_NOT_LINKED")
            result.update(endpoint=common,status="SHARED_ONLY")
        else:
            lo,hi = y_range
            left = self.sample(selected[0][1],lo)
            right = self.sample(selected[-1][1],hi)
            target_sign = sign(unpack(pieces[0]["difference"]))
            if left["order"] != -target_sign or right["order"] != target_sign:
                return self.unresolved(pair,mode,"END_ORDER")
            samples = [left,right]
            while hi-lo > Q(1,4096):
                self.budget.guard()
                mid = midpoint((lo,hi))
                charts = next(c for (a,b),c in selected if a<=mid<=b)
                proof = self.sample(charts,mid)
                samples.append(proof)
                if proof["order"] == -target_sign:
                    lo = mid
                elif proof["order"] == target_sign:
                    hi = mid
                else:
                    break
            bands = []
            for (a,b),charts in selected:
                if a <= hi and b >= lo:
                    common = overlay(unpack(charts[0]["box"]),unpack(charts[1]["box"]))
                    if common:
                        bands.append(common)
            if not bands:
                return self.unresolved(pair,mode,"GEOMETRY_CONTRADICTION")
            result.update(samples=samples,cross_box=pack((lo,hi,min(b[2] for b in bands),
                                                           max(b[3] for b in bands))),
                          status="UNIQUE_TRANSVERSE")
        comparison = self.emit("intersections",**result)
        footprint = []
        for span,charts in selected:
            common = overlay(unpack(charts[0]["box"]),unpack(charts[1]["box"]))
            if common:
                footprint.append((*span,*common[2:]))
        return comparison["id"],footprint

    def unresolved(self,pair,mode,reason):
        self.emit("intersections",record="comparison",pair=list(pair),mode=mode,reason=reason,
                  status="UNRESOLVED")
        return None,[]

    def account(self,pair,left,right,comparison,footprint):
        root = overlay(unpack(left["box"]),unpack(right["box"]))
        pending = [("",root,0)]
        nodes = []
        while pending:
            self.budget.guard()
            name,b,depth = pending.pop()
            row = dict(path=name,box=pack(b))
            if comparison and covered(b,footprint):
                row.update(status="REGION",comparison=comparison)
            else:
                evaluations = []
                for f in pair:
                    proof,i = self.e.value(f,b,policy="shape")
                    evaluations.append(proof)
                    if sign(i):
                        row.update(status="SIGN",evaluation=proof)
                        break
                else:
                    axis = split_axis(b)
                    a,z = section(b,axis)
                    ready = all(proof in self.e.split_ready for proof in evaluations)
                    if depth < INPUTS["budget"]["shape_depth"] and a<z and ready:
                        middle = midpoint((a,z))
                        row.update(status="SPLIT",axis=axis,evaluations=evaluations)
                        children = cut(b,axis,middle)
                        pending.extend([(name+str(k),children[k],depth+1) for k in (1,0)])
                    else:
                        row.update(status="UNRESOLVED",evaluations=evaluations,
                                   reason="DEPTH_OR_POINT" if ready else "MIDPOINT_ANGLE_LIMIT")
            nodes.append(row)
        self.emit("intersections",record="overlap",pair=list(pair),charts=[left["id"],right["id"]],
                  nodes=nodes,status="UNRESOLVED" if any(r["status"]=="UNRESOLVED" for r in nodes)
                  else "ACCOUNTED")

    def run(self):
        current = None
        try:
            for pair in combinations(QUANTITIES,2):
                self.budget.guard()
                current = list(pair)
                mode = None
                if set(pair)==set(INPUTS["interior_crossing"]["pair"]):
                    mode = "INTERIOR"
                if list(pair) in INPUTS["shared_end"]["pairs"]:
                    mode = "SHARED"
                comparison,footprint = self.compare(pair,mode) if mode else (None,[])
                for a in self.primary[pair[0]]:
                    for b in self.primary[pair[1]]:
                        self.budget.guard()
                        if overlay(unpack(a["box"]),unpack(b["box"])) is not None:
                            self.account(pair,a,b,comparison,footprint)
                self.emit("intersections",record="pair_progress",pair=list(pair),status="VISITED")
        except Stop as problem:
            self.emit("pending",phase="intersections",pair=current,reason=str(problem))
            return "STOPPED"
        return "RECORDED"
