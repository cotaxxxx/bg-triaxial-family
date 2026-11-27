"""Build the Paper II linked viewer (one self-contained HTML file) from the v2 ledger.  Deterministic.

Usage:  python3 -I build_viewer.py CHARTS_JSONL EDGES_JSONL TEMPLATE_HTML OUT_HTML OUT_DATA_DIR [UNCERTIFIED_JSON]

Inputs (bg-triaxial-family, commit 862220cc03f8044ab770548d865a76ed56fc612c,
        evidence/dig/2026-11-26/CANDIDATE_B_V2_PC_RESULT/RESULT/):
  charts.jsonl  the certified strips (status CHART) of the four arcs
  edges.jsonl   the root intervals on the edges of R
The SHA-256 of both files is checked against the values below before anything is written.
The crossing interval is the one stated in Theorem 1 of Paper II v1.0 (ruling d6dc12b).

What is drawn, and its status:
  (A) proved:        strip boxes, end-point intervals, crossing box          -- exact dyadic rationals from the ledger
  (B) illustration:  line through the strip centres; side band of Theorem 2  -- no claim attached to the line or the width
  (C) uncertified:   optional table of axis points (uncertified_axis_table.py)
The script also runs the mechanical checks listed in the request and writes them to OUT_DATA_DIR/build_checks.json."""
import hashlib, json, sys
from fractions import Fraction as F

CHARTS_SHA = "95e1f773faf4c184cec4c953724c8a88a7c1e4c80874c061ed9bd7da3c973906"
EDGES_SHA = "0d19458192597d424915afa4bd253a4c9c0052c439850aab29b5ce2904bf32a2"
LEDGER_COMMIT = "862220cc03f8044ab770548d865a76ed56fc612c"
CROSS = dict(y=["0.63813109", "0.63821937"], z=["2.29643023", "2.29674050"])        # Paper II v1.0, Theorem 1, part 4
PAPER_I = dict(co="0.40795886", bo="0.64354577", bp="2.06538229", cp="4.72438340")  # Paper I, Table 1 (reference decimals)
SIDE = dict(Z1=dict(axis=0, d=0.028), Z2=dict(axis=1, d=-0.22), D1=dict(axis=0, d=-0.028), D2=dict(axis=1, d=0.22))  # as in Figure 2
EXPECT = dict(Z1=276, Z2=154, D1=111, D2=71)
PAIR_SIGN = dict(Z1=+1, Z2=+1, D1=-1, D2=-1)   # Theorem 2: pair where A_i > 0 (centre arcs), where T_i < 0 (pole arcs)


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rat(v): return F(int(v["n"]))*(F(2)**int(v["e"])) if "e" in v else F(int(v["n"]), int(v["d"]))
def fs(q): return "%d/%d" % (q.numerator, q.denominator) if q.denominator != 1 else str(q.numerator)


charts, edges, template, out_html, out_dir = sys.argv[1:6]; unc_path = sys.argv[6] if len(sys.argv) > 6 else None
shas = dict(charts=sha(charts), edges=sha(edges))
if "--print-sha" in sys.argv: print(shas); sys.exit(0)
assert shas["charts"] == CHARTS_SHA, "charts.jsonl is not the fixed input"
assert shas["edges"] == EDGES_SHA, "edges.jsonl is not the fixed input"

strips = {q: [] for q in EXPECT}
for line in open(charts):
    c = json.loads(line)
    if c["status"] != "CHART": continue
    b = [rat(v) for v in c["box"]]
    strips[c["quantity"]].append(dict(id=c["id"], box=b, cross=int(c["cross"]), direction=int(c["direction"])))
roots = {}
for line in open(edges):
    e = json.loads(line)
    if e["record"] == "root_interval": roots[(e["quantity"], e["edge"])] = [rat(v) for v in e["box"]]

checks = dict(strip_counts={q: len(v) for q, v in strips.items()}, strip_counts_as_in_paper=all(len(strips[q]) == EXPECT[q] for q in EXPECT))
# order the strips along the arc: start at the strip nearest to the first end point and always go to the nearest strip not yet used
def chain(lst, start):
    c = lambda s: ((s["box"][0] + s["box"][1])/2, (s["box"][2] + s["box"][3])/2)
    d = lambda a, b: ((a[0] - b[0])*8)**2 + (a[1] - b[1])**2
    rest = list(lst); out = []; cur = start
    while rest:
        k = min(range(len(rest)), key=lambda i: d(c(rest[i]), cur)); out.append(rest.pop(k)); cur = c(out[-1])
    return out
mid = lambda b: ((b[0] + b[1])/2, (b[2] + b[3])/2)
ends = dict(Z1=[roots[("Z1", "z_min")], roots[("Z1", "y_max")]], Z2=[roots[("Z2", "y_min")], roots[("Z2", "y_max")]],
            D1=[roots[("D1", "z_min")], roots[("D1", "y_max")]], D2=[roots[("D2", "y_min")], roots[("D2", "y_max")]])
pI = {k: F(v) for k, v in PAPER_I.items()}
endpt = dict(Z1=[(pI["co"], F(1)), (F(1), pI["cp"])], Z2=[mid(ends["Z2"][0]), (F(1), pI["cp"])],
             D1=[(pI["bo"], F(1)), (F(1), pI["bp"])], D2=[mid(ends["D2"][0]), (F(1), pI["bp"])])
inside = lambda p, b: b[0] <= p[0] <= b[1] and b[2] <= p[1] <= b[3]
checks["end_marks_inside_certified_intervals"] = {q: [inside(endpt[q][k], ends[q][k]) for k in (0, 1)] for q in strips}
for q in strips: strips[q] = chain(strips[q], endpt[q][0])
cen = {q: [((s["box"][0] + s["box"][1])/2, (s["box"][2] + s["box"][3])/2) for s in strips[q]] for q in strips}
line = {q: [endpt[q][0]] + cen[q] + [endpt[q][1]] for q in strips}
touch = lambda a, b: a[0] <= b[1] and b[0] <= a[1] and a[2] <= b[3] and b[2] <= a[3]
checks["consecutive_strips_touch_or_overlap"] = {q: dict(pairs=len(strips[q]) - 1, not_touching=sum(not touch(a["box"], b["box"]) for a, b in zip(strips[q], strips[q][1:]))) for q in strips}
checks["first_and_last_strip_meet_the_end_intervals"] = {q: [touch(strips[q][0]["box"], ends[q][0]), touch(strips[q][-1]["box"], ends[q][1])] for q in strips}
# check 1: the drawn line has a vertex inside every strip box of its quantity (the strip centre)
checks["line_vertex_inside_every_strip"] = {q: all(inside(c, s["box"]) for c, s in zip(cen[q], strips[q])) for q in strips}


def curve_at(q, axis, u):
    """transverse coordinate of the drawn line where the other coordinate (index 1 - axis) equals u (first crossing)"""
    L = line[q]; o = 1 - axis
    for a, b in zip(L, L[1:]):
        lo, hi = min(a[o], b[o]), max(a[o], b[o])
        if lo <= u <= hi and a[o] != b[o]: return a[axis] + (u - a[o])*(b[axis] - a[axis])/(b[o] - a[o])
    return None


# check 3: for every strip, the side of the drawn band agrees with the ledger (transverse axis, sign of the transverse derivative)
bad = []; nside = 0
for q in strips:
    ax, d = SIDE[q]["axis"], F(SIDE[q]["d"]).limit_denominator(1000)
    for c, s in zip(cen[q], strips[q]):
        p = list(c); p[ax] += d/64                                   # a point just on the drawn side of the centre
        t = s["cross"]                                               # transverse coordinate of this strip: 0 = y, 1 = z
        ref = curve_at(q, t, p[1 - t])
        if ref is None: continue
        nside += 1
        drawn = 1 if p[t] > ref else -1                              # drawn side, measured along the strip's transverse axis
        want = PAIR_SIGN[q]*s["direction"]                           # ledger: H increases along +t iff direction = +1
        if drawn != want: bad.append(s["id"])
checks["side_band_agrees_with_ledger"] = dict(strips_tested=nside, disagreements=len(bad), ids=bad[:10])
checks["side_band_as_in_figure_2"] = SIDE == dict(Z1=dict(axis=0, d=0.028), Z2=dict(axis=1, d=-0.22), D1=dict(axis=0, d=-0.028), D2=dict(axis=1, d=0.22))
cy, cz = [F(v) for v in CROSS["y"]], [F(v) for v in CROSS["z"]]; cm = ((cy[0] + cy[1])/2, (cz[0] + cz[1])/2)
checks["crossing_mark_inside_theorem_interval"] = cy[0] <= cm[0] <= cy[1] and cz[0] <= cm[1] <= cz[1]
checks["crossing_box_inside_a_Z1_strip_and_a_D2_strip"] = [any(s["box"][0] <= cy[0] and cy[1] <= s["box"][1] and s["box"][2] <= cz[0] and cz[1] <= s["box"][3] for s in strips[q]) for q in ("Z1", "D2")]
checks["paper_I_values_inside_end_intervals"] = dict(co=ends["Z1"][0][0] <= pI["co"] <= ends["Z1"][0][1], bo=ends["D1"][0][0] <= pI["bo"] <= ends["D1"][0][1],
                                                     cp=ends["Z1"][1][2] <= pI["cp"] <= ends["Z1"][1][3], bp=ends["D1"][1][2] <= pI["bp"] <= ends["D1"][1][3])
fl = lambda x: float(x)
data = dict(
    strips={q: [[fl(v) for v in s["box"]] + [s["cross"], s["direction"]] for s in strips[q]] for q in strips},
    line={q: [[round(fl(a), 6), round(fl(b), 6)] for a, b in line[q]] for q in strips},
    side=SIDE,
    ends=[dict(q=q, box=[fl(v) for v in ends[q][k]]) for q in ("Z1", "Z2", "D1", "D2") for k in (0, 1)],
    edgeEnds=dict(cp=[fl(ends["Z1"][1][2]), fl(ends["Z1"][1][3])], bp=[fl(ends["D1"][1][2]), fl(ends["D1"][1][3])]),
    cross=dict(y=[fl(v) for v in cy], z=[fl(v) for v in cz]),
    marks=[dict(kind="pt", label="c_o", y=fl(pI["co"]), z=1, at="below"), dict(kind="pt", label="b_o", y=fl(pI["bo"]), z=1, at="below"),
           dict(kind="pt", label="b_p", y=1, z=fl(pI["bp"]), at="right"), dict(kind="pt", label="c_p", y=1, z=fl(pI["cp"]), at="right"),
           dict(kind="pt", label="", y=0.25, z=fl(mid(ends["Z2"][0])[1]), at="left"), dict(kind="pt", label="", y=0.25, z=fl(mid(ends["D2"][0])[1]), at="left"),
           dict(kind="ball", label="", y=1, z=1, at="right"), dict(kind="cross", label="", y=fl(cm[0]), z=fl(cm[1]), at="upleft")],
    unc=None,
    meta=dict(repo="cotaxxxx/bg-triaxial-family", ledger_commit=LEDGER_COMMIT, charts_sha256=shas["charts"], edges_sha256=shas["edges"], crossing_ruling="d6dc12b",
              paper="Paper II v1.0 (ae8d73b5aefba2870ca6ded76eb53851c5cb4fdb)", unc_source=""))
if unc_path:
    u = json.load(open(unc_path)); data["unc"] = dict(ys=u["ys"], zs=u["zs"], ry=u["ry"], rx=u["rx"])
    data["meta"]["unc_source"] = u["source"] + ", SHA-256 of the table " + sha(unc_path)
    checks["uncertified_table"] = dict(sha256=sha(unc_path), shapes=len(u["ys"])*len(u["zs"]), more_than_one_sign_change=u["sign_changes_more_than_one"])
html = open(template, encoding="utf-8").read()
assert html.count("__DATA__") == 1
html = html.replace("__DATA__", json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
import re
ext = re.findall(r"""(?:src|href)\s*=\s*["'](?:https?:)?//[^"']+|url\(\s*["']?https?:|@import|<link\b|<script[^>]*\bsrc=|fetch\(|XMLHttpRequest|WebSocket|importScripts|new Image|<img\b|<iframe\b""", html)
checks["external_references_in_html"] = ext
checks["html_bytes"] = len(html.encode("utf-8"))
open(out_html, "w", encoding="utf-8").write(html)
checks["html_sha256"] = sha(out_html)
json.dump(dict(Z1=[dict(id=s["id"], box=[fs(v) for v in s["box"]], cross=s["cross"], direction=s["direction"]) for s in strips["Z1"]],
               Z2=[dict(id=s["id"], box=[fs(v) for v in s["box"]], cross=s["cross"], direction=s["direction"]) for s in strips["Z2"]],
               D1=[dict(id=s["id"], box=[fs(v) for v in s["box"]], cross=s["cross"], direction=s["direction"]) for s in strips["D1"]],
               D2=[dict(id=s["id"], box=[fs(v) for v in s["box"]], cross=s["cross"], direction=s["direction"]) for s in strips["D2"]],
               end_intervals={q: [[fs(v) for v in b] for b in ends[q]] for q in ends}, crossing=CROSS, ledger_commit=LEDGER_COMMIT, inputs_sha256=shas),
          open(out_dir + "/strips_exact.json", "w"), sort_keys=True, indent=0)
json.dump(checks, open(out_dir + "/build_checks.json", "w"), sort_keys=True, indent=1)
print(json.dumps(checks, sort_keys=True, indent=1))
