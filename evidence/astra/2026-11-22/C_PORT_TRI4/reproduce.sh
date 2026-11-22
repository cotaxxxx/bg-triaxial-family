#!/usr/bin/env bash
# bash reproduce.sh /path/to/bg-triaxial-family /new/output
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$1" && pwd)
mkdir "$2"
work=$(cd "$2" && pwd)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
pin=558a490e9a39c3681495bb50127aeecb87e212cc
cd "$work"
for spec in \
  evidence/chat/2026-11-22/D_TRI_V63A_GRID/V63A_PC_BUNDLE.tar.gz \
  evidence/chat/2026-11-21/D_TRI_LAYER_I_II_COMPLETION_V61/results/V61_RESULT_20261121_1645.tar.gz; do
  git -C "$repo" show "$pin:$spec" > "${spec##*/}"
done
sha256sum -c - <<'SUM'
71bba593815ad696db657d5fa707c16f0697a5b5ea72d78cb83d4608730d7513  V63A_PC_BUNDLE.tar.gz
65b3257206649289c1a0e49402178d98f8d1843715aa7c4e33ea6a10fefd118e  V61_RESULT_20261121_1645.tar.gz
SUM
tar xzf V63A_PC_BUNDLE.tar.gz
tar xzf V61_RESULT_20261121_1645.tar.gz
bundle="$work/V63A_PC_BUNDLE"
ref="$bundle/GER2"
native="$work/build/GER2"
mkdir -p results/selftest results/perf
python "$here/select_cases.py" out/res_v61.jsonl > selection.json
cmp selection.json "$here/cases.json"
python "$here/select_v2.py" out/res_v61.jsonl > extra.json
cmp extra.json "$here/cases_v2_extra.json"
python "$here/branch_cases.py" > branches.json
cmp branches.json "$here/branch_cases.json"
python "$here/inball.py" > inball.json
cmp inball.json "$here/inball.json"
PYTHONPATH="$ref" python "$here/profile_ref.py" > results/profile.jsonl
python "$here/build.py" "$ref" "$native" > results/build.log 2>&1
PYTHONPATH="$native" python "$here/test_primitives.py" > results/primitives.json
for backend in python c; do
  reader=$ref
  if [[ $backend == c ]]; then reader=$native; fi
  PYTHONPATH="$reader" python "$here/cases_run.py" > "results/A_${backend}.jsonl"
  PYTHONPATH="$reader" python "$here/cases_extra.py" > "results/A_extra_${backend}.jsonl"
  PYTHONPATH="$reader" python "$here/run_inball.py" > "results/inball_${backend}.jsonl"
  PYTHONPATH="$reader" python "$here/run_branches.py" > "results/branches_${backend}.jsonl"
  PYTHONPATH="$reader" python "$here/test_array.py" > "results/array_${backend}.jsonl"
  PYTHONPATH="$reader" python "$here/test_errors.py" > "results/errors_${backend}.jsonl"
done
for f in selftest_{tri,tri2,tri3,tri4,lazy}.py examples/selftest_examples.py; do
  (cd "$native" && PYTHONPATH="$native:$bundle/v57" python -u "$f") > "results/selftest/$(basename "$f" .py).log" 2>&1
  tail -1 "results/selftest/$(basename "$f" .py).log" | grep -Fx 'FAILURES 0'
done
python "$here/performance.py" "$bundle" "$native" "$here/refs/rep.json" results/perf > results/timings.jsonl
python "$here/check_results.py" results "$here/refs" > results/comparison.json
cat results/comparison.json
