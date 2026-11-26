"""Read the two fixed result seals and reconstruct the local v4 geometry."""

from itertools import product

from v2_lock import HERE, read, sha256, verify_parent, verify_seal
from verify_v2 import (
    F, clip, contains, interval, mul_range, need, rect, replace_axis, rows, slope, spans, strict,
)


SPEC = read(HERE / "V4_INPUTS.json")
PAIR = tuple(SPEC["pair"])
X = tuple(map(F, SPEC["X"]))
DOMAIN = tuple(map(F, SPEC["region"]))
LOCAL = "work/local/proof"


def verify_v3_seal(folder):
    checksum = HERE / "V3_RESULT_SHA256SUMS.txt"
    original = folder / "RESULT_SHA256SUMS.txt"
    need(original.read_bytes() == checksum.read_bytes(), "v3 checksum list differs from 7c6cd7e")
    files = verify_seal(folder, checksum.read_text(encoding="ascii"))
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    need(len(files) == 99 and actual == set(files) | {original.name},
         "v3 original file set differs from the frozen result")


def receipt(v3):
    manifest = read(v3 / "MANIFEST.json")
    need(manifest["bundle_commit"] == SPEC["v3_bundle"]
         and manifest["v2_result_commit"] == SPEC["v2_result"]
         and manifest["v2_result_checksum_sha256"] == sha256(HERE / "V2_RESULT_SHA256SUMS.txt"),
         "v3 does not inherit the fixed v2 result")
    report = read(v3 / "LEDGER_INSPECTION.json")
    quantities = report["quantities"]
    need(report["status"] == "PARTIAL" and report["diagnostic_only"] is True
         and not report["run_errors"] and set(quantities) == {"Z1","Z2","D1","D2"}
         and all(r["arc_covered"] is True and r["open_leaves"] == 0 for r in quantities.values()),
         "v3 has no sealed complete cover of all four curves")
    relations = report["intersections"]
    saved = SPEC["v3_preserved_relations"]
    need(set(relations) == {*saved, "Z1+D2"}
         and all(relations[label]["status"] == status for label,status in saved.items())
         and relations["Z1+D2"] == dict(status="UNRESOLVED", overlaps=4, accounted=0),
         "v3 does not have the expected five relations and one unresolved pair")
    return report


def frozen_overlap(v3, supports):
    """Enumerate every closed overlap of the original zero supports."""
    f,g = PAIR
    observed = {}
    for (i,a),(j,b) in product(supports[f].items(),supports[g].items()):
        intersection = clip(a,b)
        if intersection is not None:
            observed[i,j] = intersection
    fixed = {tuple(r["supports"]): tuple(map(F,r["box"])) for r in SPEC["overlaps"]}
    need(len(fixed) == 4 and observed == fixed, "complete zero supports yield a different overlap set")
    checked = set()
    expected = {r["record"]:r for r in SPEC["overlaps"]}
    compare = v3 / "work/compare/proof"
    phase = list(rows(compare,"intersections"))
    need(phase[0]["record"] == "gate" and phase[0]["status"] == "COVER_RECORDED",
         "v3 intersection phase did not start with the full-cover gate")
    need(sum(r["record"] == "pair_done" and tuple(r["pair"]) == PAIR for r in phase) == 1,
         "v3 did not enumerate this pair to completion")
    for r in phase:
        if r["record"] != "overlap" or tuple(r["pair"]) != PAIR:
            continue
        spec = expected[r["id"]]
        (tile,) = r["tiles"]
        b = observed[tuple(r["supports"])]
        need(r["supports"] == spec["supports"] and rect(tile["box"]) == b
             and tile["status"] == "OPEN" and contains(X,b),
             "v3 overlap is not one of the four fixed rectangles inside X")
        checked.add(r["id"])
    need(checked == set(expected), "some v3 overlap rows are absent")


def v3_gradient(v3, local):
    planned = SPEC["v3_jacobian"]
    result = next(r for r in local if r["id"] == planned["reference"])
    need(result["record"] == "interior" and tuple(result["pair"]) == PAIR,
         "v3 derivative source is from a different pair")
    (attempt,) = [
        r for r in result["trials"]
        if (r["box_index"],r["target"]) == (planned["box_index"],planned["stage"])
    ]
    need(attempt["jacobian"] == planned["integrals"], "v3 Jacobian references differ")
    raw = {row["id"]: row for row in rows(v3/LOCAL,"integrals")}
    b = tuple(map(F,planned["box"]))
    need(contains(DOMAIN,b) and contains(b,X), "v3 Jacobian box does not enclose X")
    jacobian = []
    for f, ids in zip(PAIR,planned["integrals"],strict=True):
        line = []
        for mode, ident in enumerate(ids,1):
            r = raw[ident]
            need((r["quantity"],r["derivative"],r["precision"],r["target"],r["cells"],
                  r["dimension"],r["status"],rect(r["box"])) ==
                 (f,mode,planned["precision"],planned["stage"],planned["stage"],2,"COMPLETE",b),
                 "v3 Jacobian record is not a complete bound on its planned box")
            line.append(interval(r["interval"]))
        need(len(line) == 2, "v3 Jacobian does not have two columns")
        jacobian.append(line)
    return jacobian


def project_faces(box, axis, source, transverse, direction):
    """Transport strict signs from whole inherited chart faces to the faces of box."""
    side = spans(box,axis)
    base = spans(box,1-axis)
    edge = base[0]
    transported = []
    for chart, bounds, refs, values in source:
        lo,hi = spans(bounds,axis)
        a,b = spans(bounds,1-axis)
        part = max(a,base[0]),min(b,base[1])
        need(side[0] <= lo < hi <= side[1] and edge == part[0] < part[1] <= base[1],
             "fixed chart strips do not tile the faces of X")
        for k,(x,c,iv,ident) in enumerate(zip(side,(lo,hi),values,refs,strict=True)):
            expected = direction if k else -direction
            need(strict(iv) == expected, "inherited chart face has a wrong sign")
            change = mul_range((x-c,x-c),transverse)
            value = iv[0]+change[0],iv[1]+change[1]
            transported.append((chart,k,part,ident,value))
        edge = part[1]
    need(edge == base[1], "fixed chart strips leave an uncovered face interval")
    return transported


def local_proof(v2,v3):
    need(all(a<c<d<b for a,b,c,d in zip(DOMAIN[::2],DOMAIN[1::2],X[::2],X[1::2])),
         "X must lie in the interior of R")
    verify_parent(v2)
    verify_v3_seal(v3)
    report = receipt(v3)
    local = list(rows(v3/LOCAL,"intersections"))
    original = {f:{} for f in PAIR}
    for r in rows(v2,"charts"):
        if r["quantity"] in original and r["status"] == "CHART":
            original[r["quantity"]][r["id"]] = r
    supports = {f:{ident:rect(r["box"]) for ident,r in original[f].items()} for f in PAIR}
    for r in local:
        if r["record"] == "shared" and r["common_chart"] is not None:
            need(r["status"] == "ORDERED", "unexpected state of a v3 shared chart")
            for f in PAIR:
                if f in r["pair"]:
                    supports[f][r["id"]] = rect(r["common_chart"]["box"])
    need(all(len(supports[f]) == report["quantities"][f]["zero_supports"] for f in PAIR),
         "number of complete zero supports differs from v3")
    frozen_overlap(v3,supports)
    j = v3_gradient(v3,local)

    directions = (1,-1)
    derivatives = all(strict(j[i][i]) == directions[i] for i in range(2))
    pieces = []
    for i,f in enumerate(PAIR):
        charts = [original[f][ident] for ident in SPEC["faces"][f]]
        refs = {ident for r in charts for ident in r["faces"]}
        face_rows = {r["id"]:r for r in rows(v2/f"work/main/{f}","enclosures") if r["id"] in refs}
        source = []
        for r in charts:
            b = rect(r["box"])
            need(r["cross"] == i and r["direction"] == directions[i],
                 "inherited chart has the wrong graph coordinate or direction")
            values = []
            for c, ident in zip(spans(b,i),r["faces"],strict=True):
                entry = face_rows[ident]
                need(entry["quantity"] == f and entry["derivative"] == 0
                     and contains(rect(entry["box"]),replace_axis(b,i,c,c)),
                     "inherited enclosure does not bound the entire original face")
                values.append(interval(entry["interval"]))
            source.append((r["id"],b,r["faces"],values))
        if derivatives:
            pieces += [(f,*p) for p in project_faces(X,i,source,j[i][i],directions[i])]

    face_values = {}
    for f,_,side,_,_,value in pieces:
        old = face_values.get((f,side),value)
        face_values[f,side] = min(old[0],value[0]),max(old[1],value[1])
    miranda = derivatives and [strict(face_values[f,k]) for f in PAIR for k in (0,1)] == [-1,1,1,-1]
    slopes = [slope(j[0][1],j[0][0]),slope(j[1][0],j[1][1])] if derivatives else []
    bound = max(map(abs,mul_range(*slopes))) if slopes else None
    return {
        "box": [str(x) for x in X],
        "parent_jacobian": SPEC["v3_jacobian"],
        "jacobian_bounds": [[[str(x) for x in iv] for iv in row] for row in j],
        "face_pieces": [
            dict(quantity=f,chart=chart,side=side,span=list(map(str,span)),
                 enclosure=ref,interval=list(map(str,value)))
            for f,chart,side,span,ref,value in pieces
        ],
        "face_hulls": {f: [list(map(str,face_values[f,k])) for k in (0,1)]
                       for f in PAIR if (f,0) in face_values},
        "diagonals_strict": derivatives,
        "poincare_miranda": miranda,
        "slopes": [list(map(str,iv)) for iv in slopes],
        "slope_product_bound": None if bound is None else str(bound),
        "slope_contraction": bound is not None and bound < 1,
        "all_four_overlaps_inside_X": True,
        "overlaps": SPEC["overlaps"],
        "v3_preserved_relations": SPEC["v3_preserved_relations"],
    }
