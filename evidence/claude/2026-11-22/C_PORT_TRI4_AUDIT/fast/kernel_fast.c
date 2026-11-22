/* kernel_fast.c -- drop-in replacement for Astra's kernel.c (same exported symbols and ABI:
 * nearest_mode, test_adjacent, apply, horner), written branch-free so that the compiler can
 * vectorise the element loops.  Every arithmetic operation, comparison and selection is the same
 * IEEE binary64 operation in the same order as in kernel.c / fiv.py; only the control flow differs.
 *   - no FMA (-ffp-contract=off), no fast-math, round-to-nearest;
 *   - nextafter toward +/-infinity by integer arithmetic on the encoding, with the special values
 *     (zeros, infinities, NaN) selected by masks;
 *   - NaN propagates through min/max exactly as numpy's np.min/np.max/np.maximum do.
 * Claude Code, 2026-11-22.  DIAGNOSTIC_ONLY. */
#include <fenv.h>
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

_Static_assert(FLT_RADIX==2 && DBL_MANT_DIG==53 && DBL_MAX_EXP==1024 && sizeof(double)==8, "binary64 required");
int nearest_mode(void) { return fegetround()==FE_TONEAREST && FLT_EVAL_METHOD==0; }

#define ABSMASK UINT64_C(0x7fffffffffffffff)
#define INFBITS UINT64_C(0x7ff0000000000000)

static inline uint64_t tobits(double x) { uint64_t b; memcpy(&b, &x, 8); return b; }
static inline double frombits(uint64_t b) { double x; memcpy(&x, &b, 8); return x; }

/* nextafter(x, +inf) */
static inline double upf(double x) {
    uint64_t b = tobits(x), mag = b & ABSMASK, neg = b >> 63;
    uint64_t r = neg ? b - 1 : b + 1;                 /* finite non-zero, and -inf -> -DBL_MAX */
    r = (mag == 0) ? UINT64_C(1) : r;                 /* +0 and -0 -> smallest positive subnormal */
    r = (b == INFBITS) ? b : r;                       /* +inf stays */
    r = (mag > INFBITS) ? b : r;                      /* NaN stays */
    return frombits(r);
}
/* nextafter(x, -inf) */
static inline double dnf(double x) {
    uint64_t b = tobits(x), mag = b & ABSMASK, neg = b >> 63;
    uint64_t r = neg ? b + 1 : b - 1;                 /* finite non-zero, and +inf -> DBL_MAX */
    r = (mag == 0) ? UINT64_C(0x8000000000000001) : r;
    r = (b == (INFBITS | UINT64_C(0x8000000000000000))) ? b : r;   /* -inf stays */
    r = (mag > INFBITS) ? b : r;
    return frombits(r);
}
double test_adjacent(double x, int up) { return up ? upf(x) : dnf(x); }

/* product enclosure; NaN in any of the four products gives (NaN, NaN), as np.min/np.max do */
#define MUL(alo, ahi, blo, bhi, rlo, rhi) do {                                        \
        double p_ = (alo)*(blo), q_ = (alo)*(bhi), r_ = (ahi)*(blo), s_ = (ahi)*(bhi); \
        double l_ = p_ < q_ ? p_ : q_, h_ = p_ > q_ ? p_ : q_;                         \
        l_ = l_ < r_ ? l_ : r_; h_ = h_ > r_ ? h_ : r_;                                \
        l_ = l_ < s_ ? l_ : s_; h_ = h_ > s_ ? h_ : s_;                                \
        int nan_ = (p_ != p_) | (q_ != q_) | (r_ != r_) | (s_ != s_);                  \
        (rlo) = nan_ ? NAN : dnf(l_); (rhi) = nan_ ? NAN : upf(h_);                    \
    } while (0)

enum operation {ADD, SUB, MUL_, DIV, SQ, SQRT, NEG};
#define BLK 1024

int apply(int op, size_t n, const double *al, const double *ah, size_t sa,
          const double *bl, const double *bh, size_t sb, double *ol, double *oh) {
    int positive = 1, negative = 1;
    if (op == DIV) {
        for (size_t i = 0; i < n; i++) { positive &= bl[i*sb] > 0; negative &= bh[i*sb] < 0; }
        if (!positive && !negative) return 1;
    }
    if (op == SQRT) {
        int bad = 0;
        for (size_t i = 0; i < n; i++) bad |= al[i*sa] < 0;
        if (bad) return 2;
    }
    if (op < ADD || op > NEG) return 3;
    double A0[BLK], A1[BLK], B0[BLK], B1[BLK];
    for (size_t s = 0; s < n; s += BLK) {
        size_t m = n - s < BLK ? n - s : BLK;
        const double *x0, *x1, *y0, *y1;
        if (sa) { x0 = al + s; x1 = ah + s; } else { for (size_t i = 0; i < m; i++) { A0[i] = al[0]; A1[i] = ah[0]; } x0 = A0; x1 = A1; }
        if (sb) { y0 = bl + s; y1 = bh + s; } else { for (size_t i = 0; i < m; i++) { B0[i] = bl[0]; B1[i] = bh[0]; } y0 = B0; y1 = B1; }
        double *restrict z0 = ol + s, *restrict z1 = oh + s;
        switch (op) {
        case ADD: for (size_t i = 0; i < m; i++) { z0[i] = dnf(x0[i] + y0[i]); z1[i] = upf(x1[i] + y1[i]); } break;
        case SUB: for (size_t i = 0; i < m; i++) { z0[i] = dnf(x0[i] - y1[i]); z1[i] = upf(x1[i] - y0[i]); } break;
        case MUL_: for (size_t i = 0; i < m; i++) { MUL(x0[i], x1[i], y0[i], y1[i], z0[i], z1[i]); } break;
        case DIV: for (size_t i = 0; i < m; i++) {
                double c0 = dnf(1.0/y1[i]), c1 = upf(1.0/y0[i]);
                MUL(x0[i], x1[i], c0, c1, z0[i], z1[i]); } break;
        case SQ: for (size_t i = 0; i < m; i++) {
                double l = x0[i]*x0[i], h = x1[i]*x1[i];
                double mm = x0[i] >= 0 ? l : (x1[i] <= 0 ? h : 0.0);
                double mx = l > h ? l : h; mx = ((l != l) | (h != h)) ? NAN : mx;
                z0[i] = mm > 0 ? dnf(mm) : 0.0; z1[i] = upf(mx); } break;
        case SQRT: for (size_t i = 0; i < m; i++) {
                double l = dnf(sqrt(x0[i]));
                z0[i] = (l != l) ? l : (l > 0 ? l : 0.0); z1[i] = upf(sqrt(x1[i])); } break;
        case NEG: for (size_t i = 0; i < m; i++) { z0[i] = -x1[i]; z1[i] = -x0[i]; } break;
        }
    }
    return op == DIV && negative && !positive ? -1 : 0;
}

/* Horner with interval coefficients: for every cell, a = c[m-1]; for j = m-1..1: a = a*h + c[j-1].
   The cell loop is innermost within a block, so the same per-cell sequence of operations vectorises. */
void horner(size_t n, const double *hl, const double *hh, size_t m,
            const double *cl, const double *ch, double *ol, double *oh) {
    double a0[BLK], a1[BLK];
    for (size_t s = 0; s < n; s += BLK) {
        size_t k = n - s < BLK ? n - s : BLK;
        const double *restrict x0 = hl + s, *restrict x1 = hh + s;
        for (size_t i = 0; i < k; i++) { a0[i] = cl[m-1]; a1[i] = ch[m-1]; }
        for (size_t j = m - 1; j > 0; j--) {
            const double c0 = cl[j-1], c1 = ch[j-1];
            for (size_t i = 0; i < k; i++) {
                double t0, t1; MUL(a0[i], a1[i], x0[i], x1[i], t0, t1);
                a0[i] = dnf(t0 + c0); a1[i] = upf(t1 + c1);
            }
        }
        for (size_t i = 0; i < k; i++) { ol[s+i] = a0[i]; oh[s+i] = a1[i]; }
    }
}
