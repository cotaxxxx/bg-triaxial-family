#!/bin/bash
set -euo pipefail
base=/home/daybreak/e4-pc-20261125
cd "$base"
# Wait only for the already-launched E1 preflight, not for other computation.
while ps -p 1896289 -o stat= | grep -qv '^Z' && ps -p 1896463 -o stat= | grep -q '[RS]'; do sleep 1; done
grep -Fxq 'E1 staged check PASS: 4 raw integrals x 3, 2 aggregate rows x 3' records/e1-stage-check.log
cmp records/E1_original.jsonl records/E1_staged.jsonl || {
 python3 -B -c 'import json; from pathlib import Path; a,b=[list(map(json.loads,Path(x).read_text().splitlines())) for x in ("records/E1_original.jsonl","records/E1_staged.jsonl")]; assert a==b'
}
python3 -B records/preflight-resources.py > records/resource-before-bench.json
test ! -e bench
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
v60=/home/daybreak/v60/V60_PC_BUNDLE
cd E4_PC_BUNDLE
python3 -B src/bench_e4.py capture --cwd "$v60" "$base/bench" -- \
 /home/daybreak/v60env/bin/python -I -B "$v60/v60/bench_v60.py" "$v60/GER2"
cd "$base"
python3 -B records/make-receipt.py
cd E4_PC_BUNDLE
python3 -B src/bench_e4.py budget "$base/bench"
