#!/bin/bash
# Driver for PLAN_C_PORT.md (tests A-E, work 1, work 4) on one machine.  Written after the plan was fixed; it only executes it.
# Usage: run_all.sh GER2_ORIG V57_DIR V61_BUNDLE_DIR REP_JSON MPMATH_DIR WORKDIR
set -u
T=$(cd "$(dirname "$0")" && pwd); SRC=$T/../src; GER=$1; V57=$2; V61=$3; REP=$4; MP=$5; W=$6
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
mkdir -p $W && cd $W && rm -rf py c c_scalar *.jsonl *.json st_* && mkdir py && cp -r $GER py/GER2 && find py -name __pycache__ -prune -exec rm -rf {} +
sh $SRC/build.sh $GER $W/c/GER2 > build_c.log 2>&1 || { echo BUILD FAILED; exit 2; }
NOAVX2=1 sh $SRC/build.sh $GER $W/c_scalar/GER2 > build_c_scalar.log 2>&1 || { echo BUILD FAILED; exit 2; }
PP() { echo "$W/$1/GER2:$MP"; }
A12=$(python3 -c "import json;print(','.join(str(c['id']) for c in json.load(open('$T/cases_A.json')) if c['group']!='A2'))")
A2=3000,3001,3002,3003,3004; A4=$(python3 -c "print(','.join(str(i) for i in range(4000,4018)))")
log() { echo "[$(date -u +%T)] $*" | tee -a run_all.log; }
log "phase 1: tests A, D, E, C, profile"
( PYTHONPATH=$(PP c) python3 $T/run_cases.py $T/cases_A.json c_A.jsonl $A12
  PYTHONPATH=$(PP c) python3 $T/run_cases.py $T/cases_A.json c_A2.jsonl $A2
  PYTHONPATH=$(PP c) python3 $T/run_cases.py $T/cases_A3_audit.json c_A3.jsonl
  PYTHONPATH=$(PP c) python3 $T/run_cases.py $T/cases_A3_audit_supp1.json c_A3s.jsonl
  PYTHONPATH=$(PP c_scalar) python3 $T/run_cases.py $T/cases_A3_audit.json cs_A3.jsonl
  PYTHONPATH=$(PP c_scalar) python3 $T/run_cases.py $T/cases_A3_audit_supp1.json cs_A3s.jsonl
  PYTHONPATH=$(PP c_scalar) python3 $T/run_cases.py $T/cases_A.json cs_A4.jsonl $A4
  PYTHONPATH=$(PP c) python3 $T/test_blocks.py blocks_avx2.json > blocks_avx2.log 2>&1
  PYTHONPATH=$(PP c_scalar) python3 $T/test_blocks.py blocks_scalar.json > blocks_scalar.log 2>&1
  V57=$V57 EXTRA=$MP sh $T/selftests.sh $W/c/GER2 $W/st_c ) > p1.log 2>&1 &
( PYTHONPATH=$(PP py) python3 $T/run_cases.py $T/cases_A.json py_A.jsonl $A12 ) > p2.log 2>&1 &
( PYTHONPATH=$(PP py) python3 $T/run_cases.py $T/cases_A.json py_A2.jsonl $A2 ) > p3.log 2>&1 &
( PYTHONPATH=$(PP py) python3 $T/run_cases.py $T/cases_A3_audit.json py_A3.jsonl
  PYTHONPATH=$(PP py) python3 $T/run_cases.py $T/cases_A3_audit_supp1.json py_A3s.jsonl
  V57=$V57 EXTRA=$MP sh $T/selftests.sh $W/py/GER2 $W/st_py
  PYTHONPATH=$(PP py) python3 $T/profile_ref.py $T/cases_A.json 2009,2011,2018,2020,2036,2038 profile.json ) > p4.log 2>&1 &
wait
log "phase 2: test B (4 processes)"
for k in py c; do for i in 0 1; do
  PYTHONPATH=$MP python3 $V61/v61/run_v61.py $W/$k/GER2 $REP $i 2 $W/tree_${k}_$i.jsonl 20000 > tree_${k}_$i.log 2>&1 &
done; done; wait
log "phase 3: bench (alone, 3 times each)"
for r in 1 2 3; do for k in py c; do PYTHONPATH=$MP python3 $V61/v60/bench_v60.py $W/$k/GER2 >> bench_$k.jsonl 2>> bench.err; done; done
log "done"
