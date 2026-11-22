#!/bin/sh
# Build libtape.so and install the tape wrapper into a COPY of the pure-Python Reader 0.6.0 tree.
# Usage: build.sh /path/to/copy/of/GER2          (the original tree is not touched)
# -march=native was used for the measurements in AUDIT_REPORT.md (GCC 13.3.0, sapphirerapids, 256-bit vectors).
# Never add -ffast-math or allow contraction: the results must stay bit-identical to Python.
set -e
here=$(cd "$(dirname "$0")" && pwd); tree=$1
gcc -std=c11 -O3 -march=native -ffp-contract=off -fno-fast-math -fno-trapping-math -fno-math-errno -fPIC -shared \
    "$here/tape_kernel.c" -lm -o "$tree/geoenclosereader/libtape.so"
cp "$here/_tape.py" "$tree/geoenclosereader/_tape.py"
grep -q "_install_tape" "$tree/geoenclosereader/__init__.py" || printf '\nfrom ._tape import install as _install_tape\n_install_tape()\n' >> "$tree/geoenclosereader/__init__.py"
