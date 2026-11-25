"""Read Candidate B certificates using only the standard library and rational endpoints.

Elementary integral enclosures are inputs here. This script checks their use,
shape partitions and the graph/topology certificates, without a numerical kernel.
"""

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import re


F = Fraction
SPEC = Path(__file__).with_name("INPUTS.json")


class Invalid(ValueError):
    pass


def need(test, message):
    if not test:
        raise Invalid(message)


def q(x):
    keys = set(x)
    need(keys in ({"n","e"},{"n","d"}), "unrecognized rational encoding")
    need(isinstance(x["n"],str) and re.fullmatch(r"-?\d+",x["n"]), "invalid numerator")
    if "e" in x:
        need(type(x["e"]) is int, "dyadic exponent must be an integer")
        return int(x["n"])*F(2)**x["e"]
    need(isinstance(x["d"],str) and re.fullmatch(r"[1-9]\d*",x["d"]), "invalid denominator")
    return F(int(x["n"]),int(x["d"]))


def vec(encoded, size):
    need(len(encoded)==size,"wrong coordinate count")
    return tuple(q(x) for x in encoded)


def interval(encoded):
    lo,hi = vec(encoded,2)
    need(lo<=hi,"reversed interval")
    return lo,hi


def rect(encoded):
    a,b,c,d = vec(encoded,4)
    need(a<=b and c<=d,"reversed rectangle")
    return a,b,c,d


def clip(a,b):
    x = max(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),min(a[3],b[3])
    return x if x[0]<=x[1] and x[2]<=x[3] else None


def contains(outer,inner):
    return clip(outer,inner)==inner


def spans(a,axis):
    return a[2*axis],a[2*axis+1]


def replace_axis(box,axis,l,h):
    values = list(box)
    values[2*axis]=l
    values[2*axis+1]=h
    return tuple(values)


def corner(y,z):
    return y,y,z,z


def partition(box,axis,c):
    l,r = spans(box,axis)
    need(l<c<r,"cut must subdivide a nonempty interior")
    return replace_axis(box,axis,l,c),replace_axis(box,axis,c,r)


def plan_axis(box):
    return int(6*(box[1]-box[0]) < F(3,4)*(box[3]-box[2]))


def in_union(domain,rectangles):
    # Test the arrangement's open cells, their edges and vertices with exact probes.
    cuts = [{*spans(domain,i)} for i in range(2)]
    boxes = [x for r in rectangles if (x:=clip(domain,r)) is not None]
    if domain in boxes:
        return True
    for box in boxes:
        for i in range(2):
            cuts[i].update(spans(box,i))
    probes = []
    for coords in cuts:
        ordered = sorted(coords)
        probes.append(ordered + [(a+b)/2 for a,b in zip(ordered,ordered[1:])])
    return all(any(contains(b,corner(y,z)) for b in boxes) for y,z in product(*probes))


def strict(a):
    return 1 if a[0]>0 else -1 if a[1]<0 else 0


def intersect_intervals(a,b):
    x = max(a[0],b[0]),min(a[1],b[1])
    need(x[0]<=x[1],"empty intersection in proof")
    return x


def mul_range(a,b):
    values = [x*y for x,y in product(a,b)]
    return min(values),max(values)


def slope(dy,dz):
    need(strict(dz)!=0,"slope denominator contains zero")
    x = mul_range(dy,(F(1)/dz[1],F(1)/dz[0]))
    return -x[1],-x[0]


def difference(a,b):
    return a[0]-b[1],a[1]-b[0]


def spherical_pole():
    def atan_bounds(n):
        partial = sum(F((-1)**k,(2*k+1)*n**(2*k+1)) for k in range(64))
        return partial,partial+F(1,129*n**129)
    a,b = atan_bounds(5),atan_bounds(239)
    # Machin's identity and the alternating remainder, using rationals only.
    lo,hi = 16*a[0]-4*b[1],16*a[1]-4*b[0]
    return lo**2/32,hi**2/32


def rows(path,name):
    with (path/f"{name}.jsonl").open(encoding="utf-8") as data:
        seen = set()
        for line in data:
            need(line.endswith("\n"), f"torn line in {name}")
            item = json.loads(line)
            need(item["id"] not in seen, f"duplicate row in {name}")
            seen.add(item["id"])
            yield item


class Review:
    def __init__(self, folder, cfg):
        self.folder,self.cfg = folder,cfg
        self.families = cfg["quantities"]
        self.domain = tuple(map(F,cfg["region"]))
        self.bands = tuple(map(F,cfg["transverse_width"]))
        self.edges = {"y_min":(0,self.domain[0]),"y_max":(0,self.domain[1]),
                      "z_min":(1,self.domain[2]),"z_max":(1,self.domain[3])}
        self.raw = {}
        self.proofs = {}
        self.charts = {}
        self.primary = defaultdict(list)
        self.roots = defaultdict(list)
        self.root_ids = {}
        self.links = defaultdict(list)
        self.edge_links = set()
        self.cells = Counter()
        self.anchors = {}
        self.corners = {}
        self.trials = Counter()
        self.failures = []

    def edge_box(self,side,lo,hi):
        axis,x = self.edges[side]
        return replace_axis(replace_axis(self.domain,axis,x,x),1-axis,lo,hi)

    def read_integrals(self):
        states = {}
        a = self.cfg["angular"]
        for r in rows(self.folder,"integrals"):
            f,kind,bits,cap = r["quantity"],r["derivative"],r["precision"],r["target"]
            b = rect(r["box"])
            phase = r["id"].split(".")[0]
            need(f in self.families and kind in (0,1,2) and contains(self.domain,b),
                 f"bad integral arguments at {r['id']}")
            need(phase in ("pilot","main","compare"),"unknown integral phase")
            need((bits==a["precision"] and cap in a["stages"]) or
                 (bits==a["edge_precision"] and cap==a["edge_stage"] and phase=="main"
                  and any(b==self.edge_box(side,*spans(b,1-axis))
                          for side,(axis,_) in self.edges.items())),
                 f"unplanned angle stage at {r['id']}")
            if phase=="pilot":
                need(cap<=self.cfg["budget"]["pilot_stage"] and
                     b in [tuple(map(F,x)) for x in self.cfg["pilot"]],"unplanned pilot argument")
            key = (phase,f,b,kind,bits)
            old,previous,last_target,last_status = states.get(r["tree"],(key,0,0,"COMPLETE"))
            count,cumulative = r["formula_calls"],r["total_calls"]
            need(key==old and cap>last_target and last_status=="COMPLETE" and
                 type(count) is int and 0<=count and cumulative==previous+count,
                 "inconsistent angular tree continuation or cell count")
            states[r["tree"]] = (key,cumulative,cap,r["status"])
            self.cells[(phase,f)] += count
            if r["status"]=="INCONSISTENT":
                self.failures.append(r["id"])
            if r["status"]=="COMPLETE":
                dim = 2
                if ((f in ("Z1","Z2") and b[0]==b[1]==1 and kind!=1) or
                    (f!="D2" and b[2]==b[3]==1 and kind!=2)):
                    dim = 1
                expected = 16 + (2 if dim==1 else 4)*(cap-16)//(1 if dim==1 else 3)
                need(r["dimension"]==dim and r["cells"]==cap and cumulative==expected,
                     "unplanned angular dimension or panel total")
                self.raw[r["id"]] = (f,b,kind,bits,cap,interval(r["interval"]),phase,count)
            else:
                need(r["status"] in ("PENDING","INCONSISTENT") and "interval" not in r,
                     "unfinished integral must have no usable interval")
        budget = self.cfg["budget"]
        need(sum(self.cells.values())<=budget["cells_total"],"total panel budget exceeded")
        for f in self.families:
            need(self.cells["main",f]<=budget["cells_per_quantity"],"quantity budget exceeded")
        need(sum(n for (phase,_),n in self.cells.items() if phase!="main")<=budget["cells_other"],
             "pilot and assembly budget exceeded")

    def read_enclosures(self):
        a = self.cfg["angular"]
        for row in rows(self.folder,"enclosures"):
            f,b,kind = row["quantity"],rect(row["box"]),row["derivative"]
            phase = row["id"].split(".")[0]
            planned = [(a["precision"],x) for x in a["stages"]]
            if row["edge_retry"]:
                planned.append((a["edge_precision"],a["edge_stage"]))
            seen_raw = set()
            count = 0

            def primitive(ident,where,mode,p,n):
                nonlocal count
                g,geo,code,precision,target,value,pp,calls = self.raw[ident]
                need((g,geo,code,precision,target,pp)==(f,where,mode,p,n,phase) and
                     ident not in seen_raw,"wrong primitive integral attached to enclosure")
                seen_raw.add(ident)
                count += calls
                return value

            accum = None
            finished = False
            m = ((b[0]+b[1])/2,(b[2]+b[3])/2)
            for i,step in enumerate(row["stages"]):
                p,n = step["precision"],step["target"]
                need(not finished and i<len(planned) and planned[i]==(p,n),
                     "unexpected enclosure stage")
                direct = primitive(step["direct"],b,kind,p,n)
                accum = direct if accum is None else intersect_intervals(accum,direct)
                need(("mean" in step)==(not strict(accum) and kind==0 and
                                         (b[0]<b[1] or b[2]<b[3])),
                     "mean-value stage does not follow the schedule")
                shortcut = False
                if "mean" in step:
                    centre = primitive(step["midpoint"],corner(*m),0,p,n)
                    exact_lo,exact_hi = centre
                    shape_width = F(0)
                    for axis in (0,1):
                        lo,hi = spans(b,axis)
                        ident = step["gradients"][axis]
                        if lo==hi:
                            need(ident is None,"a zero-width direction was given a term")
                            continue
                        derivative = primitive(ident,b,axis+1,p,n)
                        c,d = mul_range((lo-m[axis],hi-m[axis]),derivative)
                        exact_lo+=c; exact_hi+=d; shape_width+=d-c
                    enclosure = interval(step["mean"])
                    need(enclosure[0]<=exact_lo<=exact_hi<=enclosure[1],
                         "mean-value bounds omit an independently recomputed term")
                    accum = intersect_intervals(accum,enclosure)
                    shortcut = (row["shape_shortcut"] and not strict(accum) and
                                shape_width>2*(centre[1]-centre[0]))
                need(bool(step.get("shape_width_stop",False))==bool(shortcut),
                     "incorrect shape-width shortcut")
                finished = bool(strict(accum) or shortcut)
            need(accum is not None and (finished or len(row["stages"])==len(planned)) and
                 count==row["formula_calls"] and interval(row["interval"])==accum,
                 "enclosure does not equal its verified intersection")
            self.proofs[row["id"]] = (f,b,kind,accum)

    def value(self, ident, f, where, mode=0):
        g,b,d,i = self.proofs[ident]
        need(g==f and d==mode and contains(b,where), f"wrong enclosure for {ident}")
        return i

    def chart_condition(self,row):
        f,b,v = row["quantity"],rect(row["box"]),row["cross"]
        need(f in self.families and v in (0,1) and row["base"]==1-v and contains(self.domain,b),
             "invalid chart geometry")
        lo,hi = spans(b,v)
        a,z = spans(b,1-v)
        need(a<z and 0<hi-lo<=self.bands[v] and q(row["width"])==hi-lo,"chart width missed")
        left = self.value(row["faces"][0],f,replace_axis(b,v,lo,lo))
        right = self.value(row["faces"][1],f,replace_axis(b,v,hi,hi))
        transverse = self.value(row["transverse"],f,b,v+1)
        need(strict(left)==-strict(right)!=0 and strict(right)==strict(transverse)==row["direction"],
             "chart faces or transverse derivative do not have the required signs")
        return f,b

    def read_charts(self):
        for row in rows(self.folder,"charts"):
            self.trials[row["quantity"]] += 1
            if row["status"]!="CHART":
                need(row["status"]=="REJECTED","unknown chart state")
                continue
            f,b = self.chart_condition(row)
            need(row["record"] in ("chart","comparison_chart"),"unknown accepted chart type")
            self.charts[row["id"]] = row
            if row["record"]=="chart":
                self.primary[f].append(row["id"])
        need(all(n<=self.cfg["budget"]["chart_trials_per_quantity"] for n in self.trials.values()),
             "chart trial budget exceeded")

    def read_edges(self,record):
        f = record["quantity"]
        need(f in self.families,"invalid edge quantity")
        if record["record"]=="corner":
            p = rect(record["box"])
            need(p in [corner(y,z) for y,z in product(spans(self.domain,0),spans(self.domain,1))],
                 "invalid corner check")
            fits = bool(strict(self.value(record["evaluation"],f,p)))
            need((f,p) not in self.corners and record["status"]==("NONZERO" if fits else "UNRESOLVED"),
                 "incorrect corner record")
            self.corners[f,p] = fits
        elif record["record"]=="anchor":
            side,name = record["edge"],record["anchor"]
            expected = self.cfg["expected_edges"][f][side]
            spec = self.cfg["anchors"][name]
            x0,x1 = interval(record["endpoints"])
            l,h = interval(record["paper"])
            need(expected==name and spec["edge"]==side and (x0,x1)==tuple(map(F,spec["interval"])) and
                 (l,h)==tuple(map(F,spec["paper"])) and x0<l<h<x1 and (f,side) not in self.anchors,
                 "wrong Paper I bracket")
            signs = [strict(self.value(ident,f,self.edge_box(side,x,x)))
                     for ident,x in zip(record["evaluation"],(x0,x1))]
            fits = signs==spec["signs"]
            need(record["status"]==("MATCH" if fits else "UNRESOLVED"),"incorrect anchor state")
            self.anchors[f,side] = fits
        elif record["record"]=="root_interval":
            side = record["edge"]
            axis = 1-self.edges[side][0]
            b = rect(record["box"])
            lo,hi = spans(b,axis)
            need(0<hi-lo<=self.bands[axis] and b==self.edge_box(side,lo,hi) and contains(self.domain,b),
                 "incorrect edge root geometry")
            vals = [self.value(i,f,self.edge_box(side,x,x)) for i,x in zip(record["faces"],(lo,hi))]
            d = self.value(record["tangent"],f,b,axis+1)
            need(strict(vals[0])==-strict(vals[1])!=0 and strict(d)==strict(vals[1]) and
                 record["status"]=="ROOT","edge root lacks uniqueness or existence proof")
            need(all(clip(b,x[1]) is None for x in self.roots[f,side]),"edge root brackets overlap")
            self.roots[f,side].append((record["id"],b))
            self.root_ids[record["id"]] = (f,side,b)
        else:
            need(record["record"]=="node","unknown edge row type")

    def link(self,row):
        f = row["quantity"]
        if row["record"]=="components":
            return
        a,b = row["a"],row["b"]
        one = self.charts[a]
        need(one["quantity"]==f and one["record"]=="chart","link needs a primary chart")
        if row["record"]=="chart_link":
            other = self.charts[b]
            need(other["quantity"]==f and other["record"]=="chart" and a!=b,"invalid chart link")
            box = rect(other["box"])
        else:
            need(row["record"]=="edge_link" and self.root_ids[b][0]==f,"wrong edge link")
            box = self.root_ids[b][2]
        common = clip(rect(one["box"]),box)
        need(common is not None and rect(row["overlap"])==common,"link overlap is inaccurate")
        if row["status"]=="UNRESOLVED":
            need(row["witness"] is None,"unresolved link cannot have a witness")
            return
        need(row["status"]=="LINKED","unknown link status")
        points = [rect(b) for b in row["witness"]["points"]]
        need(len(points)==2 and all(p[0]==p[1] and p[2]==p[3] and contains(common,p)
                                     for p in points) and points[0]!=points[1] and
             (points[0][0]==points[1][0] or points[0][2]==points[1][2]),"link segment outside charts")
        signs = [strict(self.value(i,f,p)) for i,p in zip(row["witness"]["evaluation"],points)]
        need(len(signs)==2 and signs[0]==-signs[1]!=0,"link lacks opposite endpoint signs")
        if row["record"]=="chart_link":
            self.links[f].append((a,b))
        else:
            self.edge_links.add(b)

    def initial_rectangles(self,side=None):
        n = self.cfg["shape_grid"]
        points = []
        for axis in (0,1):
            lo,hi = spans(self.domain,axis)
            points.append([lo+(hi-lo)*F(i,n[axis]) for i in range(n[axis]+1)])
        if side:
            axis = 1-self.edges[side][0]
            return [(f"E.{side}.{i:02d}",self.edge_box(side,a,b))
                    for i,(a,b) in enumerate(zip(points[axis],points[axis][1:]))]
        return [(f"B{i:02d}.{j:02d}",(points[0][i],points[0][i+1],points[1][j],points[1][j+1]))
                for i in range(n[0]) for j in range(n[1])]

    def tree(self,f,node_rows,side=None):
        index = {r["node"]:r for r in node_rows}
        need(len(index)==len(node_rows),"duplicate shape node")
        pending = [(id,b,id,None,0) for id,b in self.initial_rectangles(side)]
        counts = Counter()
        signed_area = F(0)
        while pending:
            node,b,root,parent,depth = pending.pop()
            row = index.pop(node,None)
            if row is None:
                counts["PENDING"]+=1
                continue
            need(rect(row["box"])==b and (row["root"],row["parent"],row["depth"])==(root,parent,depth),
                 f"wrong parent or child geometry at {node}")
            state = row["status"]
            counts[state]+=1
            dmax = self.cfg["budget"]["edge_depth" if side else "shape_depth"]
            if state=="SPLIT":
                axis = row["axis"]
                need(axis==(1-self.edges[side][0] if side else plan_axis(b)) and depth<dmax,
                     "unplanned shape split axis or depth")
                location = q(row["cut"])
                if row["root_cut"]:
                    h,edge,box = self.root_ids[row["root_cut"]]
                    need((h,edge)==(f,side) and location in spans(box,axis),
                         "cut is not at a certified edge-root endpoint")
                else:
                    need(location==sum(spans(b,axis))/2 and
                         not strict(self.value(row["evaluation"],f,b)),"split wrongly motivated")
                children = [node+"/0",node+"/1"]
                need(row["children"]==children,"split children do not form a full binary partition")
                pending.extend((c,g,root,node,depth+1)
                               for c,g in zip(children,partition(b,axis,location)))
            elif state in ("SIGN_POS","SIGN_NEG"):
                actual = strict(self.value(row["evaluation"],f,b))
                need(actual==(1 if state=="SIGN_POS" else -1),"sign leaf has no strict certificate")
                signed_area += (b[1]-b[0])*(b[3]-b[2])
            elif state=="IN_CHART_UNION":
                need(not side,"shape chart attached to an edge leaf")
                ids = row["charts"]
                need(not strict(self.value(row["evaluation"],f,b)) and
                     set(ids)<=set(self.primary[f]) and
                     in_union(b,[rect(self.charts[c]["box"]) for c in ids]),"gap in chart-union leaf")
            elif state=="IN_ROOT":
                h,e,outer = self.root_ids[row["root_interval"]]
                need((h,e)==(f,side) and contains(outer,b),"edge leaf outside its bracket")
            else:
                need(state=="UNRESOLVED" and depth==dmax and row["reason"]=="DEPTH_LIMIT",
                     "unknown or premature unresolved shape leaf")
        need(not index,"orphan shape nodes")
        return dict(counts),signed_area

    def assemble_family(self,f,box_rows,edge_rows):
        a,area = self.tree(f,box_rows)
        e = {side:self.tree(f,[r for r in edge_rows if r["edge"]==side],side)[0]
             for side in self.edges}
        need(all(r["edge"] in self.edges for r in edge_rows),"unknown edge in tree")
        graphs = {chart: set() for chart in self.primary[f]}
        for i,j in self.links[f]:
            graphs[i].add(j)
            graphs[j].add(i)
        components = 0
        unseen = set(graphs)
        while unseen:
            components += 1
            wave = [unseen.pop()]
            while wave:
                next_vertices = graphs[wave.pop()] & unseen
                unseen -= next_vertices
                wave.extend(next_vertices)
        missing = sum(t.get(s,0) for t in [a,*e.values()] for s in ("UNRESOLVED","PENDING"))
        counts = {side:len(self.roots[f,side]) for side in self.edges}
        counts_fit = all(n==int(side in self.cfg["expected_edges"][f]) for side,n in counts.items())
        anchor_fit = all(self.anchors.get((f,side),False)
                         for side,name in self.cfg["expected_edges"][f].items() if name is not None)
        corners_fit = all(self.corners.get((f,corner(y,z)),False)
                          for y,z in product(spans(self.domain,0),spans(self.domain,1)))
        roots = [ident for side in self.edges for ident,_ in self.roots[f,side]]
        return dict(boxes=a,edges=e,roots=counts,components=components,open=missing,
                    signed_area=str(area),expected_edge_counts=counts_fit,anchor_signs=anchor_fit,
                    all_corners_nonzero=corners_fit,linked_edge_roots=len(self.edge_links&set(roots)),
                    arc_conditions=(missing==0 and components==1 and counts_fit and anchor_fit
                                    and corners_fit and len(roots)==2 and set(roots)<=self.edge_links))

    def graph_join(self,test,charts,y,alias=False):
        first,second = charts
        need(q(test["y"])==y,"wrong y coordinate for graph join")
        a,b = interval(test["z"])
        p,r = corner(y,a),corner(y,b)
        need(a<b and all(contains(rect(chart["box"]),p) and contains(rect(chart["box"]),r)
                        for chart in charts),"graph join bracket outside its supports")
        need((alias and y==1) or first["quantity"]==second["quantity"],"invalid shared endpoint")
        f = first["quantity"]
        ss = []
        for proof,x in zip(test["evaluation"],(p,r)):
            g = self.proofs[proof][0]
            need(g==f or (alias and g==second["quantity"]),"wrong proof in graph join")
            ss.append(strict(self.value(proof,g,x)))
        need(len(ss)==2 and ss[0]==-ss[1]!=0,"graph join lacks opposite signs")

    def root_order(self,sample,pair,pieces):
        y = q(sample["y"])
        chart_ids = [r["chart"] for r in sample["roots"]]
        need(len(chart_ids)==2 and any(a<=y<=b and charts==chart_ids for (a,b),charts in pieces),
             "root order sample outside the comparison atlas")
        z = []
        for f,proof in zip(pair,sample["roots"]):
            a,b = interval(proof["z"])
            chart_box = rect(self.charts[proof["chart"]]["box"])
            need(a<b and contains(chart_box,(y,y,a,b)),"root order bracket outside chart")
            left,right = proof["evaluation"]
            need(strict(self.value(left,f,corner(y,a)))==-strict(self.value(right,f,corner(y,b)))!=0,
                 "root order bracket lacks opposite signs")
            z.append((a,b))
        actual = strict(difference(*z))
        need(sample["order"]==actual,"wrong comparison of transverse root brackets")
        return y,actual

    def comparison(self,row):
        pair = tuple(row["pair"])
        iso = tuple(self.cfg["interior_crossing"]["pair"])
        shared = {tuple(x) for x in self.cfg["shared_end"]["pairs"]}
        if pair==iso:
            mode,target = "INTERIOR",tuple(map(F,self.cfg["interior_crossing"]["window"]))
        else:
            need(pair in shared,"unexpected comparison of graphs")
            mode,target = "SHARED",(*map(F,self.cfg["shared_end"]["y"]),*self.domain[2:])
        need(row["mode"]==mode,"wrong comparison mode")
        if row["status"]=="UNRESOLVED":
            return None
        need(interval(row["y"])==target[:2],"wrong comparison domain")
        position = target[0]
        direction = 0
        support = []
        previous = []
        pieces = []
        for j,piece in enumerate(row["pieces"]):
            a,b = interval(piece["y"])
            need(position==a<b<=target[1],"gap or overlap in comparison slabs")
            position=b
            charts = [self.charts[c] for c in piece["charts"]]
            need([c["quantity"] for c in charts]==list(pair),"comparison support has wrong quantity")
            need(len(piece["gradient"])==2 and all(len(x)==2 for x in piece["gradient"]),
                 "missing comparison gradients")
            values = []
            for c,f,refs in zip(charts,pair,piece["gradient"]):
                box = rect(c["box"])
                slice_box = (a,b,*box[2:])
                need(c["cross"]==1 and contains(box,slice_box) and contains(target,slice_box),
                     "comparison chart outside requested window")
                values.append(slope(self.value(refs[0],f,slice_box,1),
                                    self.value(refs[1],f,slice_box,2)))
            delta = difference(*values)
            need(interval(piece["difference"])==delta and strict(delta)!=0 and
                 (direction in (0,strict(delta))),"comparison slope lacks a uniform strict sign")
            direction = strict(delta)
            if j:
                joins = row["joins"][j-1]
                need(len(joins)==2,"comparison missing a join")
                for old,new,test in zip(previous,charts,joins):
                    self.graph_join(test,(old,new),a)
            common = clip(rect(charts[0]["box"]),rect(charts[1]["box"]))
            if common is not None:
                support.append((a,b,common[2],common[3]))
            pieces.append(((a,b),piece["charts"]))
            previous = charts
        need(position==target[1] and len(row["joins"])+1==len(pieces),"comparison atlas incomplete")
        if mode=="SHARED":
            need(row["status"]=="SHARED_ONLY","incorrect shared endpoint conclusion")
            self.graph_join(row["endpoint"],previous,target[1],alias=True)
        else:
            need(row["status"]=="UNIQUE_TRANSVERSE","incorrect interior comparison conclusion")
            evidence = [self.root_order(s,pair,pieces) for s in row["samples"]]
            need(evidence[:2]==[(target[0],-direction),(target[1],direction)],
                 "crossing lacks opposite orders at y endpoints")
            lo,hi = target[:2]
            for i,(y,order) in enumerate(evidence[2:]):
                need(y==(lo+hi)/2,"intersection refinement is not a bisection")
                if order==-direction:
                    lo=y
                elif order==direction:
                    hi=y
                else:
                    need(i==len(evidence)-3,"continued a bisection past an undecided sample")
            b = rect(row["cross_box"])
            need(b[:2]==(lo,hi) and contains(target,b),"wrong crossing location")
            options = [(q[2],q[3]) for q in support if lo<=q[1] and q[0]<=hi]
            need(bool(options) and all(b[2]<=a<=d<=b[3] for a,d in options),
                 "crossing enclosure omits part of the admissible atlas")
        return pair,support

    def overlap_check(self,row,claims):
        pair = tuple(row["pair"])
        i,j = row["charts"]
        need(i in self.primary[pair[0]] and j in self.primary[pair[1]],
             "overlap needs two primary charts of the stated pair")
        root = clip(rect(self.charts[i]["box"]),rect(self.charts[j]["box"]))
        need(root is not None,"overlap row for disjoint charts")
        nodes = {r["path"]:r for r in row["nodes"]}
        need(len(nodes)==len(row["nodes"]),"duplicate overlap leaf")
        pending = [("",root)]
        complete = True
        while pending:
            name,b = pending.pop()
            r = nodes.pop(name)
            need(rect(r["box"])==b,"wrong overlap subdivision")
            status = r["status"]
            if status=="SPLIT":
                axis = r["axis"]
                need(axis==plan_axis(b) and len(name)<self.cfg["budget"]["shape_depth"],
                     "unplanned overlap split")
                split = partition(b,axis,sum(spans(b,axis))/2)
                pending.extend((name+str(k),child) for k,child in enumerate(split))
            elif status=="REGION":
                owner,area = claims[r["comparison"]]
                need(owner==pair and in_union(b,area),"overlap not covered by certified graph comparison")
            elif status=="SIGN":
                proof = r["evaluation"]
                f = self.proofs[proof][0]
                need(f in pair and strict(self.value(proof,f,b)),"overlap lacks strict exclusion")
            else:
                need(status=="UNRESOLVED","unknown overlap leaf state")
                complete = False
        need(not nodes and row["status"]==("ACCOUNTED" if complete else "UNRESOLVED"),
             "overlap has orphan boxes or wrong conclusion")
        return pair,(i,j),complete

    def review_intersections(self):
        claims = {}
        owners = set()
        overlap_rows = []
        for r in rows(self.folder,"intersections"):
            if r["record"]=="comparison":
                checked = self.comparison(r)
                if checked:
                    pair,areas = checked
                    need(pair not in owners,"duplicate successful graph comparison")
                    claims[r["id"]] = (pair,areas)
                    owners.add(pair)
            elif r["record"]=="overlap":
                overlap_rows.append(r)
            else:
                need(r["record"]=="pair_progress","unknown intersection record")
        verified = defaultdict(set)
        seen = set()
        for r in overlap_rows:
            pair,key,ok = self.overlap_check(r,claims)
            need((pair,key) not in seen,"duplicate chart overlap")
            seen.add((pair,key))
            if ok:
                verified[pair].add(key)
        configured = {tuple(self.cfg["interior_crossing"]["pair"]),
                      *map(tuple,self.cfg["shared_end"]["pairs"])}
        result = {}
        for pair in combinations(self.families,2):
            a,b = pair
            covered = len(verified[pair])
            actual = sum(clip(rect(self.charts[i]["box"]),rect(self.charts[j]["box"])) is not None
                         for i,j in product(self.primary[a],self.primary[b]))
            result["+".join(pair)] = dict(overlaps=actual,accounted=covered,
                                             comparison_required=pair in configured,
                                             graph_comparison=pair in owners,
                                             conditions_met=covered==actual and
                                             (pair not in configured or pair in owners))
        return result

    def review_pilot(self):
        report = json.loads((self.folder/"PILOT.json").read_text())
        found = set()
        outcomes = {}
        spheres = set()
        for row in rows(self.folder,"events"):
            if row["record"]=="worker_outcome" and row["phase"]=="pilot":
                need(row["quantity"] not in outcomes,"duplicate pilot worker receipt")
                outcomes[row["quantity"]] = row["status"]
            if row["record"]!="pilot_integral":
                if row["status"]=="INCONSISTENT":
                    self.failures.append(row["id"])
                continue
            f,b,d,p,n,i,phase,_ = self.raw[row["integral"]]
            t = row["sample"]
            need(phase=="pilot" and f==row["quantity"] and d==row["derivative"] and
                 b==tuple(map(F,self.cfg["pilot"][t])) and n==self.cfg["budget"]["pilot_stage"] and
                 p==self.cfg["angular"]["precision"] and (f,t,d) not in found,"invalid pilot check")
            found.add((f,t,d))
            if t==d==0:
                ref = interval(row["reference"])
                if f in ("Z1","Z2"):
                    need(ref==(F(4,3),F(4,3)),"wrong spherical central reference")
                else:
                    lo,hi = spherical_pole()
                    need(ref[0]<=lo<=hi<=ref[1] and ref[1]-ref[0]<F(1,2**120),
                         "wrong spherical pole reference")
                ok = i[0]<=ref[0]<=ref[1]<=i[1]
                need(row["sphere_contains"]==ok,"wrong spherical containment result")
                if ok:
                    spheres.add(f)
        samples = [time for r in rows(self.folder,"integrals") if r["id"].startswith("pilot.")
                   for time in r.get("cell_ns",[])]
        count = sum(n for (phase,_),n in self.cells.items() if phase=="pilot")
        times = sorted(samples)
        p90 = times[(9*len(times)+9)//10-1] if times else None
        b = self.cfg["budget"]
        complete = (len(found)==len(self.families)*len(self.cfg["pilot"])*3 and
                    len(spheres)==len(self.families) and
                    all(outcomes.get(f)=="RECORDED" for f in self.families))
        allowed = (complete and count==len(samples) and p90 is not None and
                   p90*b["pilot_estimate_cells"]<=10**9*b["pilot_estimate_cores"]*
                   b["pilot_estimate_max_seconds"])
        need(report["formula_calls"]==count and report["p90_ns"]==p90 and
             report["complete"]==complete and report["allowed"]==allowed,"pilot gate differs from receipts")
        need(allowed or not any(n for (phase,_),n in self.cells.items() if phase!="pilot"),
             "main evaluation recorded without an eligible pilot")
        return bool(allowed)

    def check(self):
        self.read_integrals()
        self.read_enclosures()
        self.read_charts()
        edge_rows = defaultdict(list)
        box_rows = defaultdict(list)
        for r in rows(self.folder,"edges"):
            self.read_edges(r)
            if r["record"]=="node":
                edge_rows[r["quantity"]].append(r)
        for r in rows(self.folder,"boxes"):
            need(r["quantity"] in self.families and r["record"]=="node","unknown box row")
            box_rows[r["quantity"]].append(r)
        for r in rows(self.folder,"links"):
            self.link(r)
        families = {}
        for f in self.families:
            need(len(edge_rows[f])+len(box_rows[f]) <= self.cfg["budget"]["boxes_per_quantity"],
                 "shape attempt budget exceeded")
            families[f] = self.assemble_family(f,box_rows[f],edge_rows[f])
        pair = self.review_intersections()
        pilot = self.review_pilot()
        done = (pilot and not self.failures and all(x["arc_conditions"] for x in families.values())
                and all(x["conditions_met"] for x in pair.values()))
        return dict(status="CONDITIONS_CHECKED" if done else "PARTIAL",
                    diagnostic_only=True,quantities=families,intersections=pair,
                    pilot_eligible=pilot,run_errors=self.failures)


def verify_hashes(folder):
    seen = set()
    for line in (folder/"RESULT_SHA256SUMS.txt").read_text().splitlines():
        digest,name = line.split("  ",1)
        path = Path(name)
        need(re.fullmatch("[a-f0-9]{64}",digest) and not path.is_absolute() and
             ".." not in path.parts and name==path.as_posix() and name not in seen,
             "invalid result digest entry")
        seen.add(name)
        value = hashlib.sha256()
        with (folder/name).open("rb") as file:
            for data in iter(lambda:file.read(1<<20),b""):
                value.update(data)
        need(value.hexdigest()==digest,f"result digest mismatch for {name}")
    need({"INPUTS.json","PILOT.json","MANIFEST.json","summary.json","boxes.jsonl",
          "edges.jsonl","charts.jsonl","links.jsonl","intersections.jsonl","enclosures.jsonl",
          "integrals.jsonl","events.jsonl","pending.jsonl"}<=seen,"incomplete result digest list")
    actual = {x.relative_to(folder).as_posix() for x in folder.rglob("*") if x.is_file()}
    need(actual==seen|{"RESULT_SHA256SUMS.txt"},"unexpected or unhashed result file")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path)
    p.add_argument("--unsealed",action="store_true",help="verify while the runner seals its output")
    args = p.parse_args()
    try:
        if not args.unsealed:
            verify_hashes(args.run)
        need((args.run/"INPUTS.json").read_bytes()==SPEC.read_bytes(),"run inputs differ from bundle")
        cfg = json.loads(SPEC.read_bytes())
        result = Review(args.run,cfg).check()
    except (OSError,ValueError,KeyError,IndexError,TypeError,ZeroDivisionError) as exc:
        result = dict(status="INVALID_LEDGER",detail=str(exc))
    print(json.dumps(result,indent=2))
    return 2 if result["status"]=="INVALID_LEDGER" else 0


if __name__=="__main__":
    raise SystemExit(main())
