#!/bin/sh
# Rebuild the viewer from the fixed ledger commit.  Run from the repository root:  sh viewer/make_viewer.sh
# Needs: git (with the commit below available), python3.  The optional table is taken from viewer/data as committed.
set -e
C=862220cc03f8044ab770548d865a76ed56fc612c; R=evidence/dig/2026-11-26/CANDIDATE_B_V2_PC_RESULT/RESULT
T=$(mktemp -d); git show $C:$R/charts.jsonl > $T/charts.jsonl; git show $C:$R/edges.jsonl > $T/edges.jsonl
python3 -I viewer/build_viewer.py $T/charts.jsonl $T/edges.jsonl viewer/template.html viewer/paper2_viewer.html viewer/data viewer/data/uncertified_axis_points.json > /dev/null
sha256sum viewer/paper2_viewer.html; rm -rf $T
