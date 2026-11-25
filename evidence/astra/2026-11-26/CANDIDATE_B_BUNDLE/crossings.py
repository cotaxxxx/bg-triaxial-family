"""Compare certified graphs and account for every overlapping pair of primary charts."""

from itertools import combinations

from engine import (INPUTS, QUANTITIES, REGION, WIDTH, Stop, covered, cut, divide,
                    interval_width, midpoint, overlay, pack, point, replace,
                    section, sign, split_axis, subtract, unpack, Q)
from shape import chart_faces, signed_pair


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
    def __init__(self, engine, rows, attempted):
        self.e = engine
        self.emit = engine.journal.row
        self.budget = engine.budget
        self.primary = {f:[r for r in rows if r["quantity"]==f and r["status"]=="CHART"]
                        for f in QUANTITIES}
        self.tries = {f:max(attempted.get(f,0),sum(r["quantity"]==f for r in rows))
                      for f in QUANTITIES}
        self.auxiliary = {f:[] for f in QUANTITIES}
        self.directions = {r["id"]:r["direction"] for r in rows if r["status"]=="CHART"}

    def bracket(self, f, span, bounds):
        """Find a narrow transverse gate on the whole y slab."""
        if self.tries[f] >= INPUTS["budget"]["chart_trials_per_quantity"]:
            return None
        self.tries[f] += 1
        lo,hi = bounds
        left,a = self.e.value(f,(*span,lo,lo))
        right,b = self.e.value(f,(*span,hi,hi))
        direction = sign(b)
        if not direction or sign(a) != -direction:
            self.emit("charts",record="comparison_trial",quantity=f,box=pack((*span,lo,hi)),
                      cross=1,status="REJECTED",reason="FACES",faces=[left,right])
            return None
        original = (*span,lo,hi)
        while hi-lo > WIDTH[1]:
            mid = (lo+hi)/2
            before = (lo,hi)
            for x in (mid,(lo+mid)/2,(mid+hi)/2):
                if not lo < x < hi:
                    continue
                ident,val = self.e.value(f,(*span,x,x))
                if sign(val) == -direction:
                    lo,left,a = x,ident,val
                if sign(val) == direction:
                    hi,right,b = x,ident,val
                if x == mid and sign(val):
                    break
            if (lo,hi) == before:
                self.emit("charts",record="comparison_trial",quantity=f,box=pack(original),
                          cross=1,status="REJECTED",reason="WIDE_GATE",faces=[left,right])
                return None
        box = (*span,lo,hi)
        derivative,di = self.e.value(f,box,2)
        ok = signed_pair(a,b,di)
        row = self.emit("charts",record="comparison_chart" if ok else "comparison_trial",
                        quantity=f,box=pack(box),source_box=pack(original),cross=1,base=0,
                        faces=[left,right],transverse=derivative,width=pack((hi-lo,))[0],
                        direction=direction if ok else 0,status="CHART" if ok else "REJECTED")
        if ok:
            self.auxiliary[f].append(row)
            self.directions[row["id"]] = direction
            return row
        return None

    def atlas_chart(self,f,span,z_bounds,previous):
        for chart in self.primary[f]+self.auxiliary[f]:
            if chart["cross"] != 1:
                continue
            a,b,c,d = unpack(chart["box"])
            if not (a <= span[0] < span[1] <= b and z_bounds[0] <= c < d <= z_bounds[1]):
                continue
            if previous and not self.can_join(previous,chart,span[0]):
                continue
            return chart
        chart = self.bracket(f,span,z_bounds)
        if chart and (not previous or self.can_join(previous,chart,span[0])):
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
            dy,iv_y = self.e.value(f,box,1)
            dz,iv_z = self.e.value(f,box,2)
            if not sign(iv_z):
                # Transverse derivative is already strict on the containing chart.
                dz,iv_z = self.e.value(f,unpack(chart["box"]),2)
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
                    ident,value = self.e.value(f,point(y,x))
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
                for f in pair:
                    proof,i = self.e.value(f,b,shortcut=True)
                    if sign(i):
                        row.update(status="SIGN",evaluation=proof)
                        break
                else:
                    axis = split_axis(b)
                    a,z = section(b,axis)
                    if depth < INPUTS["budget"]["shape_depth"] and a<z:
                        middle = midpoint((a,z))
                        row.update(status="SPLIT",axis=axis)
                        children = cut(b,axis,middle)
                        pending.extend([(name+str(k),children[k],depth+1) for k in (1,0)])
                    else:
                        row["status"] = "UNRESOLVED"
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
