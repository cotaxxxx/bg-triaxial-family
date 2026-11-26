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
    echo 'K1 needs the real MPFR/GMP development headers. Record apt-get -s and await Judge.' >&2
    exit 2
fi
python3 -B prepare_kernel.py build/generated
compiler=${CC:-cc}
flags=(-O2 -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra
       -Werror=implicit-function-declaration -Werror=incompatible-pointer-types
       -Werror=int-conversion -fno-fast-math -ffp-contract=off -include mpfr.h)
(
    "$compiler" --version || exit 1
    set -x
    "$compiler" "${flags[@]}" src/build_probe.c -o build/header_probe -lmpfr -lgmp || exit 1
    ./build/header_probe >build/HEADER.json || exit 1
    "$compiler" "${flags[@]}" -fPIC -shared build/generated/candidate.c \
        -o build/correspondence_kernel.so -lmpfr -lgmp || exit 1
    set +x
    ldd build/correspondence_kernel.so || exit 1
) >build/compile.log 2>&1 || { cat build/compile.log >&2; exit 2; }

python3 -B - "$compiler" "${flags[@]}" <<'PY'
import os
import platform
import subprocess
import sys
from pathlib import Path
import json
from v2_lock import sha256

if sys.version_info < (3,10):
    raise SystemExit("Python 3.10 or later is required")
build = Path("build")
data = json.loads((build/"HEADER.json").read_text())
data.update(
    compiler=subprocess.check_output([sys.argv[1],"--version"],text=True).splitlines()[0],
    switches=sys.argv[2:]+["-fPIC","-shared","-lmpfr","-lgmp"],
    manifest_sha256=sha256(Path("MANIFEST.json")),
    library_sha256=sha256(build/"correspondence_kernel.so"),
    compile_log_sha256=sha256(build/"compile.log"), k1_sha256=sha256(build/"K1.log"),
    generated_sha256={f.name:sha256(f) for f in sorted((build/"generated").iterdir())},
    os=platform.platform(),cpu=platform.processor(),logical_cpus=os.cpu_count(),
    python=platform.python_version(),
)
(build/"BUILD.json").write_text(json.dumps(data,indent=2)+"\n")
PY
cat build/BUILD.json
