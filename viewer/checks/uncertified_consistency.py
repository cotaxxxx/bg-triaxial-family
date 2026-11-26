"""Consistency of the uncertified table with the certified arcs (illustration of the 'facing sides' remark; proves nothing).
For every grid shape the script reads from the drawn lines on which side of each arc the shape lies, predicts whether
Theorem 2's sides would put a pair on the axis if the pair persisted between its two arcs, and compares with the
uncertified table.  Shapes closer than TOL to a line (in z) are skipped.
Usage: python3 -I uncertified_consistency.py VIEWER_HTML OUT.json"""
import json, re, sys
html = open(sys.argv[1], encoding="utf-8").read()
D = json.loads(re.search(r"const DATA = (\{.*?\});\nconst COL", html, re.S).group(1)); U = D["unc"]; TOL = 0.06


def z_at(q, y):
    L = sorted(D["line"][q])
    if y < L[0][0] or y > L[-1][0]: return None
    for a, b in zip(L, L[1:]):
        if a[0] <= y <= b[0] and b[0] > a[0]: return a[1] + (y - a[0])*(b[1] - a[1])/(b[0] - a[0])
    return L[-1][1]


res = dict(tested=0, skipped_near_a_line=0, agree=0, disagree=[], pairs_in_table=dict(short=0, middle=0))
for i, y in enumerate(U["ys"]):
    zz = {q: z_at(q, y) for q in ("Z1", "Z2", "D1", "D2")}
    for j, z in enumerate(U["zs"]):
        if any(v is not None and abs(z - v) < TOL for v in zz.values()) or abs(y - 1) < 1e-9 and False: res["skipped_near_a_line"] += 1; continue
        short = zz["Z1"] is not None and z < zz["Z1"] and (zz["D1"] is None or z > zz["D1"])
        mid = zz["Z2"] is not None and zz["D2"] is not None and zz["D2"] < z < zz["Z2"]
        got = (U["ry"][i][j] is not None, U["rx"][i][j] is not None); res["tested"] += 1
        res["pairs_in_table"]["short"] += got[0]; res["pairs_in_table"]["middle"] += got[1]
        if got == (short, mid): res["agree"] += 1
        else: res["disagree"].append([y, z, got, [short, mid]])
res["disagree_count"] = len(res["disagree"]); res["disagree"] = res["disagree"][:12]
json.dump(res, open(sys.argv[2], "w"), indent=1); print({k: v for k, v in res.items() if k != "disagree"}, res["disagree"][:4])
