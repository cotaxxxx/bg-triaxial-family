#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sha256sum -c MANIFEST.sha256
python3 -B src/run_e4.py --check-inputs >/dev/null

if ! packages=$(dpkg-query -W -f='${binary:Package}\t${db:Status-Status}\t${Version}\n' libmpfr-dev libgmp-dev); then
  printf '%s\n' "$packages"
  printf '%s\n' 'Development package query failed. Stop and report per K1.' >&2
  exit 1
fi
printf '%s\n' "$packages"
if ! printf '%s\n' "$packages" | awk -F '\t' '
  $1 ~ /^lib(mpfr|gmp)-dev(:[^[:blank:]]+)?$/ && $2 == "installed" && $3 != "" { found++ }
  END { exit found != 2 }
'; then
  printf '%s\n' 'Missing MPFR/GMP development package. Stop and report per K1.' >&2
  exit 1
fi

mkdir build
exec > >(tee build/ENVIRONMENT.txt) 2>&1
printf 'build_started_utc=%s\n' "$(date -u +%FT%TZ)"
printf '%s\n' "$packages"
uname -a
cat /etc/os-release
lscpu
grep -E '^(MemTotal|MemAvailable):' /proc/meminfo
gcc --version
python3 --version
printf '#include <gmp.h>\n#include <mpfr.h>\n#if GMP_LIMB_BITS != 64\n#error Expected 64-bit GMP limb\n#endif\n' |
  gcc -E -x c - >/dev/null
kernel_flags=(-O2 -std=gnu17 -Wall -Wextra -Wno-enum-conversion -fno-fast-math
  -Werror=implicit-function-declaration -Werror=incompatible-pointer-types -Werror=int-conversion
  -include mpfr.h)
stage_flags=(-O2 -std=gnu17 -Wall -Wextra -Werror -fPIC -shared)
printf 'kernel compile flags: %s\n' "${kernel_flags[*]} src/kernel.c -o build/kernel -lmpfr -lgmp"
printf 'stage I/O compile flags: %s\n' "${stage_flags[*]} src/stage_io.c -o build/stage_io.so -ldl"
gcc "${kernel_flags[@]}" src/kernel.c -o build/kernel -lmpfr -lgmp
gcc "${stage_flags[@]}" src/stage_io.c -o build/stage_io.so -ldl
linked=$(ldd build/kernel)
printf '%s\n' "$linked"
if [[ "$linked" == *"not found"* ]]; then
  printf '%s\n' 'A kernel library could not be resolved.' >&2
  exit 1
fi
gcc -x c - -o build/versions -lmpfr -lgmp <<'E4_HEADER_PROBE'
#include <stdio.h>
#include <gmp.h>
#include <mpfr.h>
int main(void) {
    printf("MPFR header=%s runtime=%s\n", MPFR_VERSION_STRING, mpfr_get_version());
    printf("GMP header=%d.%d.%d runtime=%s limb_bits=%d\n",
           __GNU_MP_VERSION, __GNU_MP_VERSION_MINOR, __GNU_MP_VERSION_PATCHLEVEL,
           gmp_version, GMP_LIMB_BITS);
    return 0;
}
E4_HEADER_PROBE
build/versions
printf 'precision_bits=128 round_lower=RNDD round_upper=RNDU workers=8\n'
printf 'build_finished_utc=%s\n' "$(date -u +%FT%TZ)"
(
  cd build
  sha256sum kernel stage_io.so versions > BUILD.sha256
  cat BUILD.sha256
)
