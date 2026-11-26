"""Candidate B v3 residual covers and planned local comparisons."""

from collections import deque
from itertools import combinations, product

from engine import (
    AngleTree, INPUTS, Q, QUANTITIES, REGION, Inconsistent, Stop, add, covered,
    cut, divide, inside, midpoint, multiply, overlay, pack, point, replace,
    section, sign, split_axis, subtract, unpack,
)
from v2_lock import HERE, lines, read


V3 = read(HERE / "V3_INPUTS.json")
STAGES = V3["stages"]
BUDGET = V3["budget"]


def intervals(rows, mode="box"):
    return {r["id"]: unpack(r[mode]) for r in rows}


def old_geometry(folder):
    charts = {f: [] for f in QUANTITIES}
    for row in lines(folder / "charts.jsonl"):
        if row["status"] == "CHART":
            charts[row["quantity"]].append(row)
    opened = {f: {} for f in QUANTITIES}
    for filename, filter_row in (
        ("pending", lambda r: r.get("phase") == "boxes" and "box" in r),
        ("boxes", lambda r: r["status"] == "UNRESOLVED"),
    ):
        for row in lines(folder / f"{filename}.jsonl"):
            if filter_row(row):
                group = opened[row["quantity"]]
                data = (unpack(row["box"]), row["depth"])
                if group.setdefault(row["node"], data) != data:
                    raise Inconsistent("conflicting v2 open-node records")
    if {f: len(v) for f, v in opened.items()} != V3["v2_open"]:
        raise Inconsistent("unexpected v2 open-node population")
    return charts, opened


class Probe:
    """Use the original MPFR angle tree and journal every panel budget charge."""

    def __init__(self, kernel, journal, budget, *, measure=False):
        self.kernel = kernel
        self.journal = journal
        self.budget = budget
        self.measure = measure
        self.tree_serial = 0
        self.in_trace = False
        self.cache = {}

    def probe(self, f, box, mode, caps, accept):
        self.budget.guard()
        base = (f, box, mode)
        tree = None
        try:
            for n in caps:
                key = (*base, n)
                if key not in self.cache:
                    if tree is None:
                        tree = AngleTree(self,f,mode,box,INPUTS["angular"]["precision"])
                    self.cache[key] = tree.stage(n)
                result = self.cache[key]
                if accept(result[1]):
                    break
            return result
        finally:
            if tree is not None:
                tree.__exit__()

    def at(self, f, box, mode, cap):
        return self.probe(f, box, mode, [cap], lambda _: True)

    def signed(self, f, box, mode, caps, direction=None):
        return self.probe(
            f, box, mode, caps,
            lambda v: bool(sign(v)) if direction is None else sign(v) == direction,
        )


def padded(box, cross, amount):
    a, b = section(box, cross)
    lo, hi = section(REGION, cross)
    return replace(box, cross, max(lo, a - amount), min(hi, b + amount))


def substantial_overlap(a, b):
    return min(a[1], b[1]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[2], b[2])


def cover_ids(box, supports):
    touching = [(k, b) for k, b in supports.items() if overlay(box, b) is not None]
    if covered(box, [b for _, b in touching]):
        return [k for k, _ in touching]
    return []


def mean_value(mid, box, grads):
    answer = mid
    for axis, grad in enumerate(grads):
        if grad is not None:
            lo, hi = section(box, axis)
            half_width = (hi - lo) / 2
            answer = add(answer, multiply((-half_width, half_width), grad))
    return answer


def residual(f, p, old_charts, opened, setup_rows):
    emit = p.journal.row
    supports = intervals(old_charts)
    for row in setup_rows:
        chart = row.get("common_chart")
        if chart and f in row["pair"]:
            supports[row["id"]] = unpack(chart["box"])
    left = {k: (b, d) for k, (b, d) in opened.items() if not cover_ids(b, supports)}
    extensions = 0
    try:
        for chart in old_charts:
            p.budget.guard()
            original = unpack(chart["box"])
            axis = chart["cross"]
            for amounts in V3["pads"][f]:
                shell = padded(original, axis, Q(amounts[axis]))
                if shell == original or not any(substantial_overlap(shell, b)
                                                for b, _ in left.values()):
                    continue
                ref, bounded = p.signed(f, shell, axis + 1, STAGES["extension"], chart["direction"])
                ok = sign(bounded) == chart["direction"]
                row = emit("charts", record="extension", quantity=f, parent=chart["id"],
                           box=pack(shell), derivative=ref, status="CHART" if ok else "OPEN")
                if ok:
                    supports[row["id"]] = shell
                    extensions += 1
                    left = {k: (b, d) for k, (b, d) in left.items()
                            if not (substantial_overlap(shell, b) and cover_ids(b, supports))}
                    break

        queue = deque((name, name, b, d)
                      for name, (b, d) in sorted(opened.items(), key=lambda x: (x[1][1], x[0])))
        visits = 0
        while queue:
            p.budget.guard()
            if visits == BUDGET["shape_visits_each"]:
                raise Stop("SHAPE_VISIT_LIMIT")
            visits += 1
            origin, name, box, depth = queue.popleft()
            fields = dict(record="residual", quantity=f, origin=origin, node=name,
                          box=pack(box), depth=depth)
            support = cover_ids(box, supports)
            if support:
                emit("boxes", **fields, status="COVERED", supports=support)
                continue
            caps = STAGES["short" if f.startswith("Z") else "direct_boundary"]
            ref, direct = p.signed(f, box, 0, caps)
            if sign(direct):
                emit("boxes", **fields, status="SIGN", evaluation=ref)
                continue
            fields.update(direct=ref)
            if f.startswith("D"):
                emit("boxes", **fields, status="OPEN", reason="NO_BOUNDARY_SPLIT")
                continue

            def narrow(value):
                lo, hi = value
                return hi - lo <= max(Q(1, 256), max(Q(0), lo, -hi) / 8)

            centre = point(midpoint(box[:2]), midpoint(box[2:]))
            mid_ref, mid = p.probe(f, centre, 0, STAGES["midpoint"], narrow)
            fields.update(midpoint=mid_ref)
            if not narrow(mid):
                emit("boxes", **fields, status="OPEN", reason="MIDPOINT_WIDTH")
                continue
            gradients = [p.at(f, box, mode, STAGES["mean_gradient"]) for mode in (1, 2)]
            mean = mean_value(mid, box, [v for _, v in gradients])
            if max(mean[0], direct[0]) > min(mean[1], direct[1]):
                raise Inconsistent("disjoint direct and mean-value enclosures")
            current = max(mean[0], direct[0]), min(mean[1], direct[1])
            fields.update(gradients=[r for r, _ in gradients], interval=pack(current))
            if sign(current):
                emit("boxes", **fields, status="MEAN_SIGN")
            elif depth == INPUTS["budget"]["shape_depth"]:
                emit("boxes", **fields, status="OPEN", reason="DEPTH_LIMIT")
            else:
                axis = split_axis(box)
                middle = midpoint(section(box, axis))
                children = [f"{name}/{i}" for i in (0, 1)]
                emit("boxes", **fields, status="SPLIT", axis=axis, children=children)
                queue.extend((origin, k, b, depth + 1)
                             for k, b in zip(children, cut(box, axis, middle)))
    except Stop as error:
        return "STOPPED", str(error), extensions
    return "RECORDED", None, extensions


def reconstructed(edge, eta, gradients):
    """Correlated image of (P, delta, B1, B2) into S, D, and F1, F2."""
    b1, b2 = gradients
    return (
        subtract(add(edge, edge), multiply(eta, add(b1, b2))),
        subtract(b2, b1),
        [subtract(edge, multiply(eta, b)) for b in gradients],
    )


def boundary_setup(p):
    emit = p.journal.row
    for name, cfg in V3["shared"].items():
        f, g = cfg["pair"]
        window = tuple(map(Q, cfg["window"]))
        for n in STAGES["local"]:
            dy = [p.at(q, window, 1, n) for q in (f, g)]
            diff = subtract(dy[1][1], dy[0][1])
            if sign(diff):
                break
        data = dict(record="shared", name=name, pair=[f, g], window=pack(window),
                    derivatives=[r for r, _ in dy], difference=pack(diff),
                    status="ORDERED" if sign(diff) else "OPEN", common_chart=None)
        if sign(diff) and cfg["common_chart"]:
            b = tuple(map(Q, cfg["common_chart"]))
            eta = Q(0), 1 - b[0]
            for n in STAGES["local"]:
                faces = []
                okay = True
                for z, target in zip(b[2:], (1, -1)):
                    edge = p.at(g, point(Q(1), z), 0, n)
                    slopes = [p.at(q, (b[0], Q(1), z, z), 1, n) for q in (f, g)]
                    s, d, values = reconstructed(edge[1], eta, [v for _, v in slopes])
                    faces.append(dict(edge=edge[0], derivatives=[r for r, _ in slopes],
                                      sum=pack(s), difference=pack(d),
                                      values=[pack(v) for v in values]))
                    okay &= all(sign(v) == target for v in values)
                transverse = [p.at(q, b, 2, n) for q in (f, g)]
                if okay and all(sign(v) == -1 for _, v in transverse):
                    data["common_chart"] = dict(box=pack(b), faces=faces,
                                                transverse=[r for r, _ in transverse],
                                                direction=-1)
                    break
        emit("intersections", **data)


def negative(interval):
    return -interval[1], -interval[0]


def auxiliary(p):
    cfg = V3["interior"]
    lo, hi, _, _ = map(Q, cfg["window"])
    n = cfg["graph_y_parts"]
    dy = (hi - lo) / n
    pieces = []
    for k in range(n):
        span = (lo + k * dy, lo + (k + 1) * dy)
        graphs = []
        for f in cfg["pair"]:
            box = (*span, *map(Q, cfg["graph_z"][f][k]))
            y0,y1,z0,z1 = box
            for cap in STAGES["local"]:
                lp, left = p.at(f, (y0,y1,z0,z0), 0, cap)
                rp, right = p.at(f, (y0,y1,z1,z1), 0, cap)
                yp, y_grad = p.at(f, box, 1, cap)
                zp, z_grad = p.at(f, box, 2, cap)
                if sign(left) == 1 and sign(right) == sign(z_grad) == -1:
                    break
            else:
                return None
            if pieces:
                earlier = unpack(pieces[-1]["graphs"][len(graphs)]["box"])
                if max(z0, earlier[2]) >= min(z1, earlier[3]):
                    return None
            graphs.append(dict(box=pack(box), faces=[lp,rp], gradient=[yp,zp],
                               slope=pack(negative(divide(y_grad,z_grad)))))
        diff = subtract(*[unpack(g["slope"]) for g in graphs])
        if sign(diff) != 1:
            return None
        pieces.append(dict(graphs=graphs, difference=pack(diff)))
    order = []
    for y, z, targets, piece in zip(
        (lo,hi), map(Q,cfg["test_z"]), ((-1,1),(1,-1)), (pieces[0],pieces[-1])
    ):
        if not all(inside(point(y,z),unpack(g["box"])) for g in piece["graphs"]):
            return None
        evidence = [p.signed(f,point(y,z),0,STAGES["local"],t)
                    for f,t in zip(cfg["pair"], targets)]
        if [sign(v) for _,v in evidence] != list(targets):
            return None
        order.append([r for r,_ in evidence])
    return dict(pieces=pieces, order=order)


def krawczyk(box, values, jacobian):
    m = midpoint(box[:2]), midpoint(box[2:])
    j = [[midpoint(entry) for entry in row] for row in jacobian]
    det = j[0][0]*j[1][1] - j[0][1]*j[1][0]
    if not det:
        return None
    c = [[j[1][1]/det,-j[0][1]/det], [-j[1][0]/det,j[0][0]/det]]
    image = []
    norm = Q(0)
    for i in range(2):
        ans = m[i],m[i]
        for k in range(2):
            ans = subtract(ans,multiply((c[i][k],)*2, values[k]))
        row_norm = Q(0)
        for k in range(2):
            factor = Q(int(i==k)),Q(int(i==k))
            for l in range(2):
                factor = subtract(factor,multiply((c[i][l],)*2,jacobian[l][k]))
            row_norm += max(map(abs,factor))
            radius = (box[2*k+1]-box[2*k])/2
            ans = add(ans,multiply(factor,(-radius,radius)))
        image.extend(ans)
        norm = max(norm,row_norm)
    success = norm < 1 and all(a<c0<=c1<b
                               for a,b,c0,c1 in zip(box[::2],box[1::2],image[::2],image[1::2]))
    return dict(c=[pack(row) for row in c], image=pack(image), norm=pack((norm,))[0], strict=success)


def interior_setup(p):
    cfg = V3["interior"]
    emit = p.journal.row
    graphs = auxiliary(p)
    footprint = [] if graphs is None else [
        overlay(*[unpack(g["box"]) for g in part["graphs"]]) for part in graphs["pieces"]
    ]
    footprint = [b for b in footprint if b is not None]
    trials = []
    chosen = None
    for k, trial in enumerate(cfg["krawczyk_boxes"]):
        box = tuple(map(Q,trial))
        centre = point(midpoint(box[:2]),midpoint(box[2:]))
        for cap in STAGES["local"]:
            v = [p.at(f,centre,0,cap) for f in cfg["pair"]]
            j = [[p.at(f,box,d,cap) for d in (1,2)] for f in cfg["pair"]]
            test = krawczyk(box,[a for _,a in v],[[a for _,a in row] for row in j])
            trials.append(dict(box_index=k,target=cap,values=[r for r,_ in v],
                               jacobian=[[r for r,_ in row] for row in j],test=test))
            if test and test["strict"] and covered(unpack(test["image"]),footprint):
                chosen = len(trials)-1
                break
        if chosen is not None:
            break
    emit("intersections",record="interior",pair=cfg["pair"],graphs=graphs,trials=trials,
         chosen=chosen,status="LOCAL_UNIQUE" if chosen is not None else "OPEN")


def patch_tiles(box, patches):
    cut_boxes = [c for b in patches if (c := overlay(b,box)) is not None]
    ends = [sorted(set(section(box,i)) | {x for b in cut_boxes for x in section(b,i)})
            for i in (0,1)]
    axes = [list(zip(e,e[1:])) or [(e[0],e[0])] for e in ends]
    return [(*y,*z) for y,z in product(*axes)]


def zero_supports(f, inherited, setup):
    # A widened chart contains exactly the zeros of its inherited chart.
    cards = intervals(inherited)
    for row in setup:
        chart = row.get("common_chart")
        if chart and f in row["pair"]:
            cards[row["id"]] = unpack(chart["box"])
    return cards


def covered_all(main, opened):
    for f in QUANTITIES:
        index = {r["node"]: r for r in lines(main / f / "boxes.jsonl")}
        queue = list(opened[f])
        while queue:
            row = index.get(queue.pop())
            if row is None or row["status"] == "OPEN":
                return False
            if row["status"] == "SPLIT":
                queue.extend(row["children"])
    return True


def final_comparisons(p, main, setup, inherited, opened):
    emit = p.journal.row
    if not covered_all(main,opened):
        emit("intersections",record="gate",status="DEFERRED_COVER")
        return "DEFERRED_COVER"
    emit("intersections",record="gate",status="COVER_RECORDED")
    supports = {f: zero_supports(f,inherited[f],setup) for f in QUANTITIES}
    claims = {}
    for r in setup:
        pair = tuple(r["pair"])
        if r["record"] == "shared" and r["status"] == "ORDERED":
            claims[pair] = [unpack(r["window"])]
        if r["record"] == "interior" and r["status"] == "LOCAL_UNIQUE":
            claims[pair] = [b for piece in r["graphs"]["pieces"]
                            if (b := overlay(*[unpack(g["box"]) for g in piece["graphs"]])) is not None]
    for f,g in combinations(QUANTITIES,2):
        patches = claims.get((f,g),[])
        for (i,a),(j,b) in product(supports[f].items(),supports[g].items()):
            p.budget.guard()
            box = overlay(a,b)
            if box is None:
                continue
            ledger = []
            for cell in patch_tiles(box,patches):
                part = dict(box=pack(cell))
                if covered(cell,patches):
                    part.update(status="LOCAL")
                else:
                    for h in (f,g):
                        ref, value = p.signed(h,cell,0,STAGES["cross_exclusion"])
                        if sign(value):
                            part.update(status="SIGN",quantity=h,evaluation=ref)
                            break
                    else:
                        part.update(status="OPEN")
                ledger.append(part)
            emit("intersections",record="overlap",pair=[f,g],supports=[i,j],tiles=ledger)
        emit("intersections",record="pair_done",pair=[f,g])
    return "RECORDED"
