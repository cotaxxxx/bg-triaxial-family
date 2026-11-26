#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sha256sum -c SHA256SUMS.txt
python3 -B prepare_kernel.py build/src
flags=(-O2 -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror=implicit-function-declaration -Werror=incompatible-pointer-types -Werror=int-conversion -fno-fast-math -ffp-contract=off)
cc "${flags[@]}" build/src/build_probe.c -o build/probe -lmpfr -lgmp
build/probe > build/header.json
python3 -c 'import json; h=json.load(open("build/header.json")); assert h["mpfr"]=="4.2.2" and h["gmp_limb_bits"]==64,h'
cc "${flags[@]}" -fPIC -shared build/src/candidate.c -o build/kernel.tmp.so -lmpfr -lgmp
mv build/kernel.tmp.so build/kernel.so
cc --version > build/compiler.txt
sha256sum build/kernel.so build/header.json build/compiler.txt > build/SHA256SUMS.txt
