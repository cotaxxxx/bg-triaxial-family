"""Select the accepted zero-curve charts from the frozen Candidate B results."""

from v2_lock import HERE, read, sha256, verify_parent, verify_seal
from verify_v2 import F, contains, interval, need, rect, replace_axis, rows, spans, strict

CFG = read(HERE/"CONDITIONS.json")
FAMILIES = CFG["families"]
R = tuple(map(F,CFG["region"]))


def check_original(folder, version, count):
    name = "RESULT_SHA256SUMS.txt"
    expected = HERE/f"{version.upper()}_{name}"
    need((folder/name).read_bytes()==expected.read_bytes(), f"{version} checksum list differs")
    checked = verify_seal(folder,expected.read_text(encoding="ascii"))
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    need(len(checked)==count and actual==set(checked)|{name},f"{version} result file set differs")


def inherited(v2,v3,v4):
    verify_parent(v2)
    check_original(v3,"v3",99)
    check_original(v4,"v4",len((HERE/"V4_RESULT_SHA256SUMS.txt").read_text().splitlines()))
    report = read(v3/"LEDGER_INSPECTION.json")
    need(report["status"]=="PARTIAL" and not report["run_errors"] and
         set(report["quantities"])==set(FAMILIES) and
         all(x["arc_covered"] is True and x["open_leaves"]==0 for x in report["quantities"].values()),
         "the frozen v3 record lacks a complete cover")
    final = read(v4/"LEDGER_INSPECTION.json")
    m3 = read(v3/"MANIFEST.json")
    m4 = read(v4/"MANIFEST.json")
    need(m3["v2_result_commit"]==CFG["v2_result"] and
         m3["v2_result_checksum_sha256"]==sha256(HERE/"V2_RESULT_SHA256SUMS.txt") and
         m4["parent_results"]["v2_result"]==CFG["v2_result"] and
         m4["parent_results"]["v3_result"]==CFG["v3_result"],
         "result origins differ from the adopted chain")
    expected = {"Z1+Z2":"SHARED_ENDPOINT_ONLY","D1+D2":"SHARED_ENDPOINT_ONLY",
                "Z1+D1":"DISJOINT","Z2+D1":"DISJOINT","Z2+D2":"DISJOINT",
                "Z1+D2":"EXACTLY_ONE_INTERIOR"}
    need(final["status"]=="RELATION_RECORDED" and final["relations"]==expected,
         "v4 does not provide the adopted six relations")

    saved = {f:{} for f in FAMILIES}
    for r in rows(v2,"charts"):
        if r["status"]=="CHART":
            saved[r["quantity"]][r["id"]] = r
    charts = {}
    for f,group in saved.items():
        names = {r["transverse"] for r in group.values()}
        raw = {r["id"]:r for r in rows(v2/f"work/main/{f}","enclosures") if r["id"] in names}
        for ident,r in group.items():
            box,cross = rect(r["box"]),r["cross"]
            w = raw[r["transverse"]]
            need(cross in (0,1) and contains(R,box) and w["quantity"]==f
                 and w["derivative"]==cross+1 and contains(rect(w["box"]),box),
                 "old transverse derivative does not cover its chart")
            bound = interval(w["interval"])
            need(strict(bound)==r["direction"]!=0,"old chart direction is unresolved")
            charts[f,ident] = box,cross,bound,w["id"]
    local = v3/"work/local/proof"
    shared = {r["id"]:r for r in rows(local,"intersections") if r["record"]=="shared"}
    old = {r["id"]:r for r in rows(local,"integrals")}
    edges = list(rows(v2,"edges"))
    endpoints = {}
    for name,condition in CFG["shared"].items():
        r = shared[condition["id"]]
        f,g = condition["pair"]
        need(r["status"]=="ORDERED" and r["name"]==name and r["pair"]==[f,g] and
             strict(interval(r["difference"]))==-1,"sealed shared-curve orientation differs")
        win = rect(r["window"])
        roots = {}
        for family in (f,g):
            (root,) = [e for e in edges if e["record"]=="root_interval" and
                       e["edge"]=="y_max" and e["quantity"]==family]
            box = rect(root["box"])
            need(contains(win,box) and box[0]==box[1]==1,"shared endpoint is outside its window")
            roots[family] = (root["id"],box)
        lo = max(q[1][2] for q in roots.values())
        hi = min(q[1][3] for q in roots.values())
        need(lo<hi,"shared endpoint boxes do not intersect")
        endpoints[name] = dict(y="1",z=[str(lo),str(hi)],
                               edge_records=[q[0] for q in roots.values()],
                               difference=r["difference"],comparison=r["id"])
        support = r["common_chart"]
        if support:
            box = rect(support["box"])
            for family,ref in zip((f,g),support["transverse"],strict=True):
                w = old[ref]
                need(contains(R,box) and w["quantity"]==family and w["derivative"]==2 and
                     w["status"]=="COMPLETE" and rect(w["box"])==box,
                     "v3 common chart has the wrong transverse evidence")
                bound = interval(w["interval"])
                need(strict(bound)==support["direction"]==-1,"v3 common chart direction differs")
                charts[family,r["id"]] = box,1,bound,ref
    for f,expected in FAMILIES.items():
        count = sum(f==g for g,_ in charts)
        need(count==expected["charts"]==report["quantities"][f]["zero_supports"],
             "the exact chart population differs from the sealed report")
    return charts,endpoints
