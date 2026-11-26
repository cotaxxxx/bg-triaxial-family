"""Replay v2 and v3 ledgers using exact rational arithmetic, without the kernel."""

import argparse
from collections import Counter
from datetime import datetime
from itertools import combinations, product
import json
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_v2 import (
    F, Review, clip, contains, corner, difference, in_union, intersect_intervals, interval,
    mul_range, need, partition, plan_axis, q, rect, rows, slope, spans, spherical_pole, strict, vec,
)
from v2_lock import HERE, read, sha256, verify_parent, verify_seal


CFG2 = read(HERE/"INPUTS.json")
CFG = read(HERE/"V3_INPUTS.json")
BUDGET = CFG["budget"]
STAGES = CFG["stages"]
QUANTITIES = CFG2["quantities"]
DOMAIN = tuple(map(F,CFG2["region"]))


def rng_sum(parts):
    return tuple(sum(ends) for ends in zip(*parts))


def mul_point(value, bounds):
    a,b = (value*b for b in bounds)
    return min(a,b), max(a,b)


def derive_open(v2, parent):
    """Recover leaves by traversing each v2 partition, without reading its pending queue."""
    by = {f:{} for f in QUANTITIES}
    for r in rows(v2,"boxes"):
        by[r["quantity"]][r["node"]] = r
    answer = {}
    for f in QUANTITIES:
        tasks = [(node,b,0) for node,b in parent.initial_rectangles()]
        opened = {}
        while tasks:
            node,box,depth = tasks.pop()
            row = by[f].get(node)
            if row is None or row["status"]=="UNRESOLVED":
                opened[node] = box,depth
            elif row["status"]=="SPLIT":
                for child,tile in zip(row["children"],partition(box,row["axis"],q(row["cut"]))):
                    tasks.append((child,tile,depth+1))
        need(len(opened)==CFG["v2_open"][f],"v2 open leaf count differs")
        answer[f] = opened
    return answer


def journal_path(folder,phase,key):
    return folder/"work"/phase/key


def journal(folder,phase,key,name):
    directory = journal_path(folder,phase,key)
    return list(rows(directory,name)) if directory.is_dir() else []


class Tape:
    def __init__(self,folder):
        self.raw = {}
        self.used = {}
        self.failures = []
        self.outcomes = {}
        self.timings = []
        caps = {f:BUDGET["pilot_cells_each"] for f in QUANTITIES}
        limits = {"pilot":caps,"local":{"proof":BUDGET["local_cells"]},
                  "main":BUDGET["main_cells"],"compare":{"proof":BUDGET["intersection_cells"]}}
        for phase,groups in limits.items():
            for key,cap in groups.items():
                self.read_tape(folder,phase,key,cap)

    def read_tape(self,folder,phase,key,cap):
        serial = 0
        prefix = f"v3.{phase}.{key}"
        total = 0
        trees = {}
        for r in journal(folder,phase,key,"integrals"):
            serial += 1
            ident = r["id"]
            f, box, kind, target = r["quantity"], rect(r["box"]),r["derivative"],r["target"]
            need(ident==f"{prefix}.integrals.{serial}" and f in QUANTITIES and
                 (key==f if phase in ("pilot","main") else key=="proof") and
                 contains(DOMAIN,box) and kind in (0,1,2) and r["trace"] is False and
                 r["precision"]==128 and target in (16,64,256,1024,4096),
                 "wrong native evaluation record")
            if phase=="pilot":
                need(target in (64,256) and box in [tuple(map(F,b)) for b in CFG2["pilot"]],
                     "unplanned native pilot input")
            if phase=="local":
                need(target in STAGES["local"],"local test used an unplanned stage")
            if phase=="compare":
                need(target in STAGES["cross_exclusion"],"exclusion used an unplanned stage")
            one_dim = ((f.startswith("Z") and box[0]==box[1]==1 and kind!=1) or
                       (f!="D2" and box[2]==box[3]==1 and kind!=2))
            dim = 1 if one_dim else 2
            max_calls = 16+(2 if dim==1 else 4)*((target-16)//(1 if dim==1 else 3))
            group = f,box,kind
            old, previous_target, earlier, complete = trees.get(r["tree"],(group,0,0,True))
            count = r["formula_calls"]
            need(r["tree"].startswith(prefix+".tree.") and old==group and
                 previous_target<target and complete and r["dimension"]==dim and
                 type(count) is int and count>=0 and earlier+count==r["total_calls"]<=max_calls,
                 "native tree continuation or panel count differs")
            total += count
            status = r["status"]
            trees[r["tree"]] = (group,target,r["total_calls"],status=="COMPLETE")
            if status=="COMPLETE":
                need(r["cells"]==target and r["total_calls"]==max_calls,"incomplete panel set")
                self.raw[ident] = phase,f,box,kind,target,interval(r["interval"])
            else:
                need(status in ("PENDING","INCONSISTENT") and "interval" not in r,
                     "unfinished integral has a purported endpoint")
                if status=="INCONSISTENT":
                    self.failures.append(ident)
            if phase=="pilot":
                sample = r["cell_ns"]
                need(len(sample)==count and all(type(x) is int and x>=0 for x in sample),
                     "invalid pilot timings")
                self.timings.extend(sample)
        need(total<=cap,"native panel budget exceeded")
        self.used[phase,key] = total
        outcomes = [r for r in journal(folder,phase,key,"events") if r["record"]=="outcome"]
        need(len(outcomes)<=1,"duplicate worker receipt")
        if outcomes:
            r = outcomes[0]
            need((r["phase"],r["quantity"],r["calls"])==(phase,key,total),
                 "worker receipt does not count its raw panels")
            self.outcomes[phase,key] = r["status"]
            if r["status"]=="INCONSISTENT":
                self.failures.append(r["id"])

    def get(self,ident,phase,f,box,kind,caps):
        scope, name, space, mode, target, result = self.raw[ident]
        need((scope,name,space,mode)==(phase,f,box,kind) and target in caps,
             f"wrong enclosure witness {ident}")
        return result


def check_pilot(folder,tape):
    complete = True
    for f in QUANTITIES:
        seen = set()
        for r in journal(folder,"pilot",f,"events"):
            if r["record"]!="pilot":
                continue
            k,d = r["sample"],r["mode"]
            need((k,d) not in seen and r["quantity"]==f and
                 0<=k<len(CFG2["pilot"]) and d in (0,1,2),"invalid pilot test")
            seen.add((k,d))
            box = tuple(map(F,CFG2["pilot"][k]))
            v = tape.get(r["evaluation"],"pilot",f,box,d,[256])
            if not k and not d:
                s = (F(4,3),)*2 if f.startswith("Z") else spherical_pole()
                need(r["sphere_contains"] is True and v[0]<=s[0]<=s[1]<=v[1],
                     "sphere is outside the pilot enclosure")
        complete &= len(seen)==3*len(CFG2["pilot"]) and tape.outcomes.get(("pilot",f))=="RECORDED"
    if not (folder/"PILOT.json").is_file():
        return False
    receipt = read(folder/"PILOT.json")
    sample = sorted(tape.timings)
    p90 = sample[(9*len(sample)+9)//10-1] if sample else None
    cells = max(BUDGET["main_cells"].values())+BUDGET["local_cells"]+BUDGET["intersection_cells"]
    price = max(p90,BUDGET["previous_p90_ns"]) if p90 is not None else None
    forecast = price*cells if price else None
    need(receipt["samples"]==len(sample) and receipt["p90_ns"]==p90
         and receipt["price_ns"]==price and receipt["forecast_cells"]==cells and
         receipt["forecast_ns"]==forecast and receipt["complete"]==bool(complete),
         "panel estimate or pilot timing record differs")
    if receipt["allowed"]:
        need(complete and forecast is not None and 0<forecast<=receipt["available_ns"]<=
             (BUDGET["total_seconds"]-BUDGET["seal_reserve_seconds"])*10**9,
             "main work was outside the pilot gate")
    return bool(receipt["allowed"])


def check_shared(row,tape,parent):
    cfg = CFG["shared"][row["name"]]
    pair = tuple(cfg["pair"])
    w = tuple(map(F,cfg["window"]))
    need(tuple(row["pair"])==pair and rect(row["window"])==w and w[1]==1,"wrong shared window")

    def local(ref,f,box,mode):
        return tape.get(ref,"local",f,box,mode,STAGES["local"])

    dy = [local(ref,f,w,1) for f,ref in zip(pair,row["derivatives"],strict=True)]
    diff = difference(dy[1],dy[0])
    ordered = bool(strict(diff))
    need(interval(row["difference"])==diff and row["status"]==("ORDERED" if ordered else "OPEN"),
         "factored difference does not have the recorded sign")
    edge = {}
    for f in pair:
        found = parent.roots[f,"y_max"]
        need(len(found)==1 and found[0][0] in parent.edge_links and contains(w,found[0][1]),
             "shared patch misses an inherited edge root")
        edge[f] = found[0][1]

    chart = row["common_chart"]
    if chart:
        b = rect(chart["box"])
        need(ordered and cfg["common_chart"] is not None and b==tuple(map(F,cfg["common_chart"])) and
             chart["direction"]==-1 and all(contains(b,x) for x in edge.values()),
             "paired chart has no complete shared anchor")
        delta = F(0),1-b[0]
        for mode,z,r in zip((1,-1),b[2:],chart["faces"],strict=True):
            p = local(r["edge"],pair[1],corner(F(1),z),0)
            bounds = [local(ref,f,(b[0],F(1),z,z),1)
                      for f,ref in zip(pair,r["derivatives"],strict=True)]
            s = difference(mul_point(2,p),mul_range(delta,rng_sum(bounds)))
            d = difference(bounds[1],bounds[0])
            values = [difference(p,mul_range(delta,v)) for v in bounds]
            need(interval(r["sum"])==s and interval(r["difference"])==d and
                 list(map(interval,r["values"]))==values and
                 all(strict(v)==mode for v in values),"paired face witness differs")
        need(all(strict(local(ref,f,b,2))==-1
                 for f,ref in zip(pair,chart["transverse"],strict=True)),
             "paired chart lacks strict transverse derivatives")
    return pair, [w] if ordered else [], rect(chart["box"]) if chart else None


def audit_graphs(data,tape):
    spec = CFG["interior"]
    f,g = spec["pair"]
    y0,y1,z0,z1 = map(F,spec["window"])
    parts = spec["graph_y_parts"]
    dy = (y1-y0)/parts
    need(len(data["pieces"])==parts,"auxiliary graphs omit a base span")
    previous = []
    footprint = []
    for k,row in enumerate(data["pieces"]):
        listed = row["graphs"]
        span = y0+k*dy,y0+(k+1)*dy
        support,derivatives = [],[]
        for h,chart in zip((f,g),listed,strict=True):
            b = (*span,*map(F,spec["graph_z"][h][k]))
            need(rect(chart["box"])==b and z0<=b[2]<b[3]<=z1,"wrong auxiliary graph box")
            for ref,z,expected in zip(chart["faces"],b[2:],(1,-1),strict=True):
                found = tape.get(ref,"local",h,(*span,z,z),0,STAGES["local"])
                need(strict(found)==expected,"auxiliary graph face is not signed")
            a,c = [tape.get(ref,"local",h,b,axis,STAGES["local"])
                   for axis,ref in enumerate(chart["gradient"],1)]
            need(strict(c)==-1,"auxiliary graph does not have a strict transverse sign")
            d = slope(a,c)
            need(interval(chart["slope"])==d,"v3 graph slope is inaccurate")
            if previous:
                old = previous[len(support)]
                need(max(old[2],b[2])<min(old[3],b[3]),"auxiliary seam is disjoint")
            support.append(b)
            derivatives.append(d)
        change = difference(*derivatives)
        need(interval(row["difference"])==change and strict(change)==1,
             "the two graph slopes are not strictly ordered")
        b = clip(*support)
        if b is not None:
            footprint.append(b)
        previous = support
    for y,z,values,piece,orientation in zip(
        (y0,y1),map(F,spec["test_z"]),data["order"],
        (data["pieces"][0],data["pieces"][-1]),((-1,1),(1,-1)),strict=True
    ):
        at = corner(y,z)
        for h,ref,chart,expected in zip((f,g),values,piece["graphs"],orientation,strict=True):
            need(contains(rect(chart["box"]),at) and
                 strict(tape.get(ref,"local",h,at,0,STAGES["local"]))==expected,
                 "the two auxiliary roots lack the recorded end ordering")
    return footprint


def audit_k(box,raw_value,raw_jac,data):
    centre = tuple((a+b)/2 for a,b in zip(box[::2],box[1::2]))
    # X minus its exact centre; both components are centred intervals.
    steps = tuple((box[2*k]-centre[k],box[2*k+1]-centre[k]) for k in range(2))
    mid = [[(a+b)/2 for a,b in row] for row in raw_jac]
    determinant = mid[0][0]*mid[1][1]-mid[1][0]*mid[0][1]
    if determinant==0:
        need(data is None,"claimed preconditioner for a singular midpoint")
        return None,False
    matrix = [vec(row,2) for row in data["c"]]
    need(len(matrix)==2 and all(sum(matrix[i][r]*mid[r][j] for r in range(2))==int(i==j)
                                for i,j in product(range(2),repeat=2)),
         "Krawczyk preconditioner is not the inverse of the midpoint matrix")
    error = [
        [difference((F(int(i==j)),)*2,
                    rng_sum([mul_point(matrix[i][k],raw_jac[k][j]) for k in range(2)]))
         for j in range(2)] for i in range(2)
    ]
    row_bounds = [
        rng_sum([(centre[i],)*2,
                 mul_point(-1,rng_sum([mul_point(c,v) for c,v in zip(matrix[i],raw_value)])),
                 *[mul_range(e,z) for e,z in zip(error[i],steps)]])
        for i in range(2)
    ]
    image = (*row_bounds[0],*row_bounds[1])
    norm = max(sum(max(abs(a),abs(b)) for a,b in line) for line in error)
    fits = norm<1 and all(box[i]<image[i]<=image[i+1]<box[i+1] for i in (0,2))
    need(rect(data["image"])==image and q(data["norm"])==norm and data["strict"]==fits,
         "Krawczyk image or contraction bound was not reconstructed")
    return image,fits


def check_interior(row,tape):
    spec = CFG["interior"]
    pair = tuple(spec["pair"])
    w = tuple(map(F,spec["window"]))
    need(tuple(row["pair"])==pair,"wrong interior crossing pair")
    footprint = audit_graphs(row["graphs"],tape) if row["graphs"] is not None else []
    schedule = list(product(range(len(spec["krawczyk_boxes"])),STAGES["local"]))
    picked = None
    local_box = None
    trials = row["trials"]
    for i,tr in enumerate(trials):
        k,cap = schedule[i]
        need((tr["box_index"],tr["target"])==(k,cap) and picked is None,
             "Krawczyk trial order differs")
        b = tuple(map(F,spec["krawczyk_boxes"][k]))
        need(contains(w,b),"Krawczyk box outside the approved window")
        centre = corner((b[0]+b[1])/2,(b[2]+b[3])/2)
        values = [tape.get(ref,"local",f,centre,0,[cap])
                  for f,ref in zip(pair,tr["values"],strict=True)]
        jac = [[tape.get(ref,"local",f,b,d,[cap]) for d,ref in enumerate(rr,1)]
               for f,rr in zip(pair,tr["jacobian"],strict=True)]
        need(all(len(rr)==2 for rr in jac),"Jacobian must be 2 by 2")
        image,good = audit_k(b,values,jac,tr["test"])
        if good and in_union(image,footprint):
            picked,local_box = i,image
    need(picked==row["chosen"] and ((picked is not None) or len(trials)==len(schedule)) and
         row["status"]==("LOCAL_UNIQUE" if picked is not None else "OPEN"),
         "local crossing decision differs from the predeclared trials")
    return pair,footprint if picked is not None else [],local_box


def review_local(folder,tape,parent):
    claims = {}
    supports = {f:{} for f in QUANTITIES}
    crossing = None
    for r in journal(folder,"local","proof","intersections"):
        if r["record"]=="shared":
            pair,area,chart = check_shared(r,tape,parent)
            if chart is not None:
                for f in pair:
                    supports[f][r["id"]] = chart
        else:
            need(r["record"]=="interior","unknown local proof record")
            pair,area,crossing = check_interior(r,tape)
        need(pair not in claims,"duplicate local proof")
        claims[pair] = area
    return claims,supports,crossing


def audit_extensions(folder,tape,parent,f,supports):
    prior = set()
    for r in journal(folder,"main",f,"charts"):
        old = parent.charts[r["parent"]]
        b = rect(r["box"])
        axis = old["cross"]
        start = rect(old["box"])
        a,h = spans(start,axis)
        lim = spans(DOMAIN,axis)
        options = []
        for amount in CFG["pads"][f]:
            p = F(amount[axis])
            ends = max(lim[0],a-p),min(lim[1],h+p)
            o = list(start)
            o[2*axis:2*axis+2] = ends
            options.append(tuple(o))
        need(r["record"]=="extension" and r["quantity"]==old["quantity"]==f and
             b!=start and b in options and r["parent"] not in prior,"unplanned chart extension")
        value = tape.get(r["derivative"],"main",f,b,axis+1,STAGES["extension"])
        fit = strict(value)==old["direction"]
        need(r["status"]==("CHART" if fit else "OPEN"),"extended chart lacks strict derivative")
        if fit:
            prior.add(r["parent"])
            supports[r["id"]] = b


def audit_residual(folder,tape,f,opened,supports):
    items = journal(folder,"main",f,"boxes")
    index = {r["node"]:r for r in items}
    need(len(index)==len(items)<=BUDGET["shape_visits_each"],"invalid residual node count")
    queue = [(name,name,b,depth) for name,(b,depth) in opened.items()]
    counts = Counter()
    while queue:
        origin,name,b,d = queue.pop()
        r = index.pop(name,None)
        if r is None:
            counts["PENDING"] += 1
            continue
        status = r["status"]
        counts[status] += 1
        need(r["record"]=="residual" and (r["quantity"],r["origin"],r["depth"])==(f,origin,d)
             and rect(r["box"])==b,"residual shape geometry differs")
        if status=="COVERED":
            need(in_union(b,[supports[key] for key in r["supports"]]),"chart cover leaves a gap")
            continue
        direct_caps = STAGES["short"] if f.startswith("Z") else STAGES["direct_boundary"]
        if status=="SIGN":
            need(strict(tape.get(r["evaluation"],"main",f,b,0,direct_caps))!=0,
                 "claimed sign does not separate from zero")
            continue
        direct = tape.get(r["direct"],"main",f,b,0,direct_caps[-1:])
        need(not strict(direct),"used a continuation after obtaining a cheap sign")
        if f.startswith("D"):
            need(status=="OPEN" and r["reason"]=="NO_BOUNDARY_SPLIT","boundary box was split again")
            continue
        m = corner((b[0]+b[1])/2,(b[2]+b[3])/2)
        lo,hi = tape.get(r["midpoint"],"main",f,m,0,STAGES["midpoint"])
        ready = hi-lo<=max(F(1,256),max(F(0),lo,-hi)/8)
        if not ready:
            need(status=="OPEN" and r["reason"]=="MIDPOINT_WIDTH" and
                 tape.raw[r["midpoint"]][4]==STAGES["midpoint"][-1],
                 "a wide midpoint cannot support further shape work")
            continue
        delta = [(b[j]-m[j],b[j+1]-m[j]) for j in (0,2)]
        grad = [tape.get(ref,"main",f,b,k,[STAGES["mean_gradient"]])
                for k,ref in enumerate(r["gradients"],1)]
        need(len(grad)==2,"mean value needs both derivatives")
        mv = rng_sum([(lo,hi),*[mul_range(u,v) for u,v in zip(delta,grad)]])
        value = intersect_intervals(direct,mv)
        need(interval(r["interval"])==value,"wrong mean-value intersection")
        if strict(value):
            need(status=="MEAN_SIGN","missed mean sign")
        elif d==CFG2["budget"]["shape_depth"]:
            need(status=="OPEN" and r["reason"]=="DEPTH_LIMIT","exceeded v2 depth")
        else:
            axis = plan_axis(b)
            children = [f"{name}/0",f"{name}/1"]
            need(status=="SPLIT" and r["axis"]==axis and r["children"]==children,
                 "unplanned residual split")
            a,h = spans(b,axis)
            queue.extend((origin,k,t,d+1) for k,t in zip(children,partition(b,axis,(a+h)/2)))
    need(not index,"orphan residual records")
    return dict(counts)


def review_pairs(folder,tape,closed,claims,supports):
    corpus = journal(folder,"compare","proof","intersections")
    pairs = list(combinations(QUANTITIES,2))
    result = {}
    if not closed:
        need(not corpus or (len(corpus)==1 and corpus[0]["record"]=="gate" and
                            corpus[0]["status"]=="DEFERRED_COVER"),
             "global intersection records preceded complete shape covers")
        return {"+".join(pair):{"status":"DEFERRED_COVER"} for pair in pairs}
    if not corpus:
        return {"+".join(pair):{"status":"PENDING"} for pair in pairs}
    need(corpus[0]["record"]=="gate" and corpus[0]["status"]=="COVER_RECORDED",
         "comparison lacks full-cover gate")
    finished = set()
    checked = {pair:{} for pair in pairs}
    for r in corpus[1:]:
        pair = tuple(r["pair"])
        need(pair in checked and pair not in finished,"unexpected pair after completion")
        if r["record"]=="pair_done":
            finished.add(pair)
            continue
        need(r["record"]=="overlap","unknown global comparison record")
        f,g = pair
        ids = tuple(r["supports"])
        b = clip(supports[f][ids[0]],supports[g][ids[1]])
        need(b is not None and ids not in checked[pair],"invalid or repeated chart overlap")
        patches = claims.get(pair,[])
        tiles = []
        unexplained = False
        for t in r["tiles"]:
            cell = rect(t["box"])
            need(contains(b,cell),"comparison tile outside the overlap")
            if t["status"]=="LOCAL":
                need(in_union(cell,patches),"comparison tile outside proved local footprint")
            elif t["status"]=="SIGN":
                h = t["quantity"]
                need(h in pair and strict(tape.get(t["evaluation"],"compare",h,cell,0,
                                                  STAGES["cross_exclusion"]))!=0,
                     "comparison exclusion is not strict")
            else:
                need(t["status"]=="OPEN","unknown comparison tile status")
                unexplained = True
            tiles.append(cell)
        need(in_union(b,tiles),"comparison tiles omit part of the overlap")
        checked[pair][ids] = not unexplained

    required = {
        tuple(s["pair"]):"SHARED_ENDPOINT_ONLY" for s in CFG["shared"].values()
    }
    required[tuple(CFG["interior"]["pair"])] = "EXACTLY_ONE_INTERIOR"
    for f,g in pairs:
        pair = f,g
        expected = {(i,j) for (i,a),(j,b) in product(supports[f].items(),supports[g].items())
                    if clip(a,b) is not None}
        found = checked[pair]
        if pair in finished:
            need(set(found)==expected,"final pair record omits actual overlaps")
        explained = sum(found.values())
        done = pair in finished and explained==len(expected) and (
            pair not in required or bool(claims.get(pair)))
        result["+".join(pair)] = dict(
            status=required.get(pair,"DISJOINT") if done else "UNRESOLVED",
            overlaps=len(expected),accounted=explained,
        )
    return result


def examine(old, folder):
    verify_parent(old)
    need((old/"INPUTS.json").read_bytes()==(HERE/"INPUTS.json").read_bytes(),
         "v2 input bytes differ")
    parent = Review(old,CFG2)
    inherited = parent.check()
    need(inherited["status"]=="PARTIAL" and not inherited["run_errors"],
         "v2 ancestry was not a coherent partial certificate")
    for r in inherited["quantities"].values():
        need(r["components"]==1 and r["expected_edge_counts"] and r["anchor_signs"]
             and r["all_corners_nonzero"] and r["linked_edge_roots"]==2 and
             all(not ({"PENDING","UNRESOLVED"} & set(entries)) for entries in r["edges"].values()),
             "inherited edge and connectedness proofs are incomplete")
    opened = derive_open(old,parent)
    tape = Tape(folder)
    eligible = check_pilot(folder,tape)
    need(eligible or not any(journal_path(folder,p,k).exists()
         for p,kk in (("local",["proof"]),("main",QUANTITIES),("compare",["proof"])) for k in kk),
         "work proceeded before the pilot gate")
    claims,paired,root = review_local(folder,tape,parent)
    supports = {}
    quantities = {}
    for f in QUANTITIES:
        core = {i:rect(parent.charts[i]["box"]) for i in parent.primary[f]}
        core.update(paired[f])
        atlas = core.copy()
        audit_extensions(folder,tape,parent,f,atlas)
        counts = audit_residual(folder,tape,f,opened[f],atlas)
        missing = counts.get("PENDING",0)+counts.get("OPEN",0)
        supports[f] = core
        quantities[f] = dict(v2_open=len(opened[f]),open_leaves=missing,decisions=counts,
                             cover_supports=len(atlas),zero_supports=len(core),arc_covered=missing==0)
    all_closed = eligible and not tape.failures and all(r["arc_covered"] for r in quantities.values())
    pairs = review_pairs(folder,tape,all_closed,claims,supports)
    done = all_closed and all(r["status"] in ("DISJOINT","EXACTLY_ONE_INTERIOR","SHARED_ENDPOINT_ONLY")
                              for r in pairs.values())
    return dict(
        status="CONDITIONS_CHECKED" if done else "PARTIAL",diagnostic_only=True,
        quantities=quantities,intersections=pairs,local_supported_pairs=[
            "+".join(pair) for pair,b in claims.items() if b
        ],interior_image=None if root is None else [str(x) for x in root],
        formula_calls={f"{phase}.{key}":value for (phase,key),value in tape.used.items()},
        run_errors=tape.failures,
    )


def identity(folder):
    result = read(folder/"MANIFEST.json")
    need((folder/"V3_INPUTS.json").read_bytes()==(HERE/"V3_INPUTS.json").read_bytes() and
         result["v2_result_commit"]==CFG["v2_result_commit"] and
         result["v2_result_checksum_sha256"]==sha256(HERE/"V2_RESULT_SHA256SUMS.txt") and
         result["jacobi_bundle_commit"]==CFG["jacobi_bundle_commit"],"execution inputs differ")
    need(all(re.fullmatch("[a-f0-9]{40}",result[k]) for k in ("bundle_commit","execution_approval"))
         and result["bundle_commit"]!=result["execution_approval"],"invalid registered approval IDs")
    start = datetime.fromisoformat(result["started_utc"])
    ended = datetime.fromisoformat(result["jacobi_ended_at"])
    need(start>=ended>=datetime.fromisoformat(CFG["jacobi_not_before"]) and
         result["jacobi_end_record"].strip(),"execution did not follow the Jacobi end record")
    build = read(folder/"BUILD.json")
    need(result["build"]==build and build["gmp_limb_bits"]==64 and
         build["k1_sha256"]==sha256(folder/"K1.log") and
         build["compile_log_sha256"]==sha256(folder/"compile.log"),"build receipt differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unsealed",action="store_true")
    parser.add_argument("v2",type=Path)
    parser.add_argument("run",type=Path)
    args = parser.parse_args()
    try:
        if not args.unsealed:
            name = "RESULT_SHA256SUMS.txt"
            found = verify_seal(args.run,(args.run/name).read_text(encoding="ascii"))
            actual = {p.relative_to(args.run).as_posix() for p in args.run.rglob("*") if p.is_file()}
            need(actual==set(found)|{name},"unexpected or unhashed result artifact")
        identity(args.run)
        result = examine(args.v2,args.run)
        receipt = args.run/"LEDGER_INSPECTION.json"
        if not args.unsealed and receipt.is_file():
            earlier = read(receipt)
            if earlier["status"]!="INSPECTION_PENDING":
                need(result==earlier,"sealed inspection differs from exact replay")
    except (OSError,ValueError,TypeError,IndexError,KeyError,ArithmeticError) as exc:
        result = dict(status="INVALID_LEDGER",detail=str(exc))
    print(json.dumps(result,indent=2))
    return 2 if result["status"]=="INVALID_LEDGER" else 0


if __name__=="__main__":
    raise SystemExit(main())
