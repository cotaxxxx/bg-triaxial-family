#include <gmp.h>
#include <mpfr.h>
#include <stdio.h>
#include <string.h>

_Static_assert(GMP_LIMB_BITS == 64 && GMP_NUMB_BITS == 64,"expected GMP 64-bit limbs");
#if MPFR_VERSION < MPFR_VERSION_NUM(4,2,0)
#error MPFR >= 4.2 required by the angle algebra
#endif

int main(void) {
    if (strcmp(MPFR_VERSION_STRING,mpfr_get_version()) || mp_bits_per_limb!=64) {
        fputs("compiled and loaded MPFR/GMP disagree\n",stderr);
        return 2;
    }
    printf("{\"mpfr\":\"%s\",\"gmp\":\"%s\",\"gmp_limb_bits\":%d}\n",
           mpfr_get_version(),gmp_version,mp_bits_per_limb);
    return 0;
}
