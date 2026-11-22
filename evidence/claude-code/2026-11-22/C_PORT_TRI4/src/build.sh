#!/bin/sh
# Build the C kernel and install it into a COPY of the pure-Python Reader 0.6.0 tree (GER2).
# Usage: build.sh /path/to/original/GER2 /path/to/new/tree [extra compiler flags]
# The original tree is only read.  The new tree is the original plus: geoenclosereader/_tape.py,
# geoenclosereader/libtape.so, and two lines appended to geoenclosereader/__init__.py.
# Fixed flags (PLAN_C_PORT.md): -O2, no contraction (no FMA), no fast-math, AVX2 for the hand-written loops.
# Without -mavx2 the same source compiles to the scalar path with the same results (pass NOAVX2=1).
set -e
here=$(cd "$(dirname "$0")" && pwd); src=$1; dst=$2; shift 2
CC=${CC:-gcc}; SIMD=${NOAVX2:+}; [ -z "${NOAVX2:-}" ] && SIMD=-mavx2
rm -rf "$dst"; mkdir -p "$dst"; cp -r "$src"/. "$dst"/; find "$dst" -name __pycache__ -prune -exec rm -rf {} +
FLAGS="-std=c11 -O2 -ffp-contract=off -fno-fast-math $SIMD -fPIC -shared $*"
$CC $FLAGS "$here/tape_kernel.c" -lm -o "$dst/geoenclosereader/libtape.so"
cp "$here/_tape.py" "$dst/geoenclosereader/_tape.py"
printf '\nfrom ._tape import install as _install_tape\n_install_tape()\n' >> "$dst/geoenclosereader/__init__.py"
{ $CC --version | head -1; echo "flags: $FLAGS"; if objdump -d "$dst/geoenclosereader/libtape.so" | grep -q -E "vfm|vfnm"; then echo "FMA instructions: PRESENT (must not happen)"; exit 3; else echo "FMA instructions: none"; fi; } | tee "$dst/BUILD_INFO.txt"
