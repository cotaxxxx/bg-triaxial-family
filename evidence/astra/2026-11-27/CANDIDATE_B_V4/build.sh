#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sha256sum -c SHA256SUMS.txt
mkdir -p build
rm -f build/BUILD.json
if ! (
    echo 'K1 package and header preflight'
    for package in libmpfr-dev libgmp-dev; do
        row=$(dpkg-query -W -f='${binary:Package}\t${db:Status-Status}\t${Version}\n' "$package") || exit 1
        printf '%s\n' "$row"
        [[ "$(cut -f 2 <<< "$row")" == installed && -n "$(cut -f 3 <<< "$row")" ]] || exit 1
    done
) >build/K1.log 2>&1; then
    cat build/K1.log >&2
    echo 'K1 requires installed libmpfr-dev and libgmp-dev. Record apt-get -s and await Judge.' >&2
    exit 2
fi
python3 -c 'import sys; assert sys.version_info >= (3, 10)'
compiler=${CC:-cc}
flags=(-O2 -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra
       -Werror=implicit-function-declaration -Werror=incompatible-pointer-types
       -Werror=int-conversion -fno-fast-math -ffp-contract=off -include mpfr.h)
(
    "$compiler" --version || exit 1
    set -x
    "$compiler" "${flags[@]}" src/build_probe.c -o build/header_probe -lmpfr -lgmp || exit 1
    ./build/header_probe > build/HEADER.json || exit 1
    "$compiler" "${flags[@]}" -fPIC -shared src/candidate.c -o build/candidate_kernel.so -lmpfr -lgmp || exit 1
    set +x
    ldd build/candidate_kernel.so || exit 1
) >build/compile.log 2>&1 || { cat build/compile.log >&2; exit 2; }
python3 -B - "$compiler" "${flags[@]}" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

with open("build/HEADER.json") as source:
    data = json.load(source)
cpu = platform.processor()
if Path("/proc/cpuinfo").is_file():
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            cpu = line.split(":", 1)[1].strip()
            break
data.update(compiler=subprocess.check_output([sys.argv[1], "--version"], text=True).splitlines()[0],
            switches=sys.argv[2:]+["-fPIC","-shared","-lmpfr","-lgmp"],
            library_sha256=hashlib.sha256(Path("build/candidate_kernel.so").read_bytes()).hexdigest(),
            bundle_manifest_sha256=hashlib.sha256(Path("MANIFEST.json").read_bytes()).hexdigest(),
            k1_sha256=hashlib.sha256(Path("build/K1.log").read_bytes()).hexdigest(),
            compile_log_sha256=hashlib.sha256(Path("build/compile.log").read_bytes()).hexdigest(),
            os=platform.platform(), cpu=cpu, logical_cpus=os.cpu_count(), python=platform.python_version())
Path("build/BUILD.json").write_text(json.dumps(data, indent=2)+"\n")
PY
cat build/BUILD.json
