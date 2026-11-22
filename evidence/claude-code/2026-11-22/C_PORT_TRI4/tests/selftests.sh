#!/bin/sh
# run the six Reader self-tests with one Reader tree; stdout of each goes to $2/<name>.out.  V57 = directory of chat_v57_numeric_lib.py; EXTRA = extra PYTHONPATH (mpmath)
tree=$1; out=$2; mkdir -p "$out"; export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
cd "$tree"
for t in selftest_tri selftest_tri2 selftest_tri3 selftest_tri4 selftest_lazy examples/selftest_examples; do
  n=$(basename $t)
  ( PYTHONPATH="$tree:$V57${EXTRA:+:$EXTRA}" python3 $t.py > "$out/$n.out" 2> "$out/$n.err"; echo "exit $?" >> "$out/$n.out" )
done
