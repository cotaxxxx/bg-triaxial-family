/* tape_kernel.c -- blocked interpreter for a recorded sequence of outward-rounded interval operations.
 *
 * The sequence ("tape") is recorded by running the unchanged Python integrand of Reader 0.6.0 on symbolic
 * intervals (tape.py).  Every instruction is one fiv.I operation; the interpreter performs, for every grid
 * cell, exactly the IEEE binary64 operations fiv.py performs (round-to-nearest, then one ulp outward by
 * nextafter), in the recorded order.  Cells are processed in blocks of BLK so that all temporaries stay
 * in cache.  No FMA, no fast-math, no libm except sqrt (correctly rounded by IEEE 754).
 *
 * Two code paths compute the same binary64 results:
 *   - scalar C (always compiled; used for the last 1-3 cells of a block and when AVX2 is not enabled);
 *   - AVX2 intrinsics, four cells at a time (compiled when __AVX2__ is defined, i.e. with -mavx2).  Only
 *     IEEE add/sub/mul/div/sqrt, MINPD/MAXPD (= the C expressions a<b?a:b and a>b?a:b), ordered/unordered
 *     compares and integer operations on the encodings are used.  No FMA intrinsic appears in this file.
 * The loops are written out by hand so that the speed does not depend on the optimisation level (-O2).
 * Claude Code, 2026-11-22.  DIAGNOSTIC_ONLY. */
#define _POSIX_C_SOURCE 200112L
#include <fenv.h>
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(FLT_RADIX==2 && DBL_MANT_DIG==53 && DBL_MAX_EXP==1024 && sizeof(double)==8, "binary64 required");
int tape_nearest_mode(void) { return fegetround()==FE_TONEAREST && FLT_EVAL_METHOD==0; }

#define ABSMASK UINT64_C(0x7fffffffffffffff)
#define INFBITS UINT64_C(0x7ff0000000000000)
#define BLK 128
#define AI static inline __attribute__((always_inline))

AI uint64_t tobits(double x) { uint64_t b; memcpy(&b, &x, 8); return b; }
AI double frombits(uint64_t b) { double x; memcpy(&x, &b, 8); return x; }
/* nextafter toward +inf / -inf by integer arithmetic on the encoding; selections are written with masks so
   that the element loops contain no control flow.  Special values: zeros go to the smallest subnormal of the
   right sign, the infinity in the direction of travel and NaN are returned unchanged. */
AI uint64_t selu(uint64_t m, uint64_t a, uint64_t b) { return (a & m) | (b & ~m); }      /* m ? a : b, m all-ones or 0 */
AI double upf(double x) {
    uint64_t b = tobits(x), mag = b & ABSMASK;
    uint64_t neg = (uint64_t)0 - (b >> 63);
    uint64_t r = selu(neg, b - 1, b + 1);
    r = selu((uint64_t)0 - (uint64_t)(mag == 0), UINT64_C(1), r);
    r = selu((uint64_t)0 - (uint64_t)((b == INFBITS) | (mag > INFBITS)), b, r);
    return frombits(r);
}
AI double dnf(double x) {
    uint64_t b = tobits(x), mag = b & ABSMASK;
    uint64_t neg = (uint64_t)0 - (b >> 63);
    uint64_t r = selu(neg, b + 1, b - 1);
    r = selu((uint64_t)0 - (uint64_t)(mag == 0), UINT64_C(0x8000000000000001), r);
    r = selu((uint64_t)0 - (uint64_t)((b == (INFBITS | UINT64_C(0x8000000000000000))) | (mag > INFBITS)), b, r);
    return frombits(r);
}
AI double seld(int c, double a, double b) {                                                /* c ? a : b on the encodings */
    return frombits(selu((uint64_t)0 - (uint64_t)(c != 0), tobits(a), tobits(b)));
}
double tape_adjacent(double x, int up) { return up ? upf(x) : dnf(x); }

#ifdef __AVX2__
#include <immintrin.h>
typedef __m256d vd; typedef __m256i vi;
int tape_simd(void) { return 4; }
#define VLOAD(p) _mm256_loadu_pd(p)
#define VSTORE(p, v) _mm256_storeu_pd((p), (v))
#define VSET(x) _mm256_set1_pd(x)
AI vi vsel(vi m, vi a, vi b) { return _mm256_blendv_epi8(b, a, m); }                       /* m ? a : b */
AI vd vseld(vd m, vd a, vd b) { return _mm256_blendv_pd(b, a, m); }                        /* m ? a : b */
AI vd vupf(vd x) {                                                                         /* = upf, lane by lane */
    const vi one = _mm256_set1_epi64x(1), inf = _mm256_set1_epi64x((long long)INFBITS), zero = _mm256_setzero_si256();
    vi b = _mm256_castpd_si256(x), mag = _mm256_and_si256(b, _mm256_set1_epi64x((long long)ABSMASK));
    vi neg = _mm256_cmpgt_epi64(zero, b);
    vi r = vsel(neg, _mm256_sub_epi64(b, one), _mm256_add_epi64(b, one));
    r = vsel(_mm256_cmpeq_epi64(mag, zero), one, r);
    r = vsel(_mm256_or_si256(_mm256_cmpeq_epi64(b, inf), _mm256_cmpgt_epi64(mag, inf)), b, r);
    return _mm256_castsi256_pd(r);
}
AI vd vdnf(vd x) {                                                                         /* = dnf, lane by lane */
    const vi one = _mm256_set1_epi64x(1), inf = _mm256_set1_epi64x((long long)INFBITS), zero = _mm256_setzero_si256();
    const vi ninf = _mm256_set1_epi64x((long long)(INFBITS | UINT64_C(0x8000000000000000)));
    const vi ntiny = _mm256_set1_epi64x((long long)UINT64_C(0x8000000000000001));
    vi b = _mm256_castpd_si256(x), mag = _mm256_and_si256(b, _mm256_set1_epi64x((long long)ABSMASK));
    vi neg = _mm256_cmpgt_epi64(zero, b);
    vi r = vsel(neg, _mm256_add_epi64(b, one), _mm256_sub_epi64(b, one));
    r = vsel(_mm256_cmpeq_epi64(mag, zero), ntiny, r);
    r = vsel(_mm256_or_si256(_mm256_cmpeq_epi64(b, ninf), _mm256_cmpgt_epi64(mag, inf)), b, r);
    return _mm256_castsi256_pd(r);
}
#define VMULI(alo, ahi, blo, bhi, rlo, rhi) do {                                                              \
        vd p_ = _mm256_mul_pd(alo, blo), q_ = _mm256_mul_pd(alo, bhi), r_ = _mm256_mul_pd(ahi, blo), s_ = _mm256_mul_pd(ahi, bhi); \
        vd l_ = _mm256_min_pd(p_, q_), h_ = _mm256_max_pd(p_, q_);                                             \
        l_ = _mm256_min_pd(l_, r_); h_ = _mm256_max_pd(h_, r_);                                                \
        l_ = _mm256_min_pd(l_, s_); h_ = _mm256_max_pd(h_, s_);                                                \
        vd nan_ = _mm256_or_pd(_mm256_or_pd(_mm256_cmp_pd(p_, p_, _CMP_UNORD_Q), _mm256_cmp_pd(q_, q_, _CMP_UNORD_Q)), \
                               _mm256_or_pd(_mm256_cmp_pd(r_, r_, _CMP_UNORD_Q), _mm256_cmp_pd(s_, s_, _CMP_UNORD_Q))); \
        (rlo) = vseld(nan_, VSET(NAN), vdnf(l_)); (rhi) = vseld(nan_, VSET(NAN), vupf(h_));                    \
    } while (0)
#else
int tape_simd(void) { return 1; }
#endif

#define MULI(alo, ahi, blo, bhi, rlo, rhi) do {                                       \
        double p_ = (alo)*(blo), q_ = (alo)*(bhi), r_ = (ahi)*(blo), s_ = (ahi)*(bhi); \
        double l_ = p_ < q_ ? p_ : q_, h_ = p_ > q_ ? p_ : q_;                         \
        l_ = l_ < r_ ? l_ : r_; h_ = h_ > r_ ? h_ : r_;                                \
        l_ = l_ < s_ ? l_ : s_; h_ = h_ > s_ ? h_ : s_;                                \
        int nan_ = (p_ != p_) | (q_ != q_) | (r_ != r_) | (s_ != s_);                  \
        (rlo) = seld(nan_, NAN, dnf(l_)); (rhi) = seld(nan_, NAN, upf(h_));            \
    } while (0)

enum { OP_ADD, OP_SUB, OP_NEG, OP_MUL, OP_DIV, OP_SQ, OP_SQRT, OP_CLIP, OP_TAILHI, OP_MSEL, OP_ZERO };

/* one binary operation on m cells.  A scalar operand (stride 0) is read once before the loop.
   The AVX2 loop handles the cells four at a time; the scalar loop finishes (or does everything without AVX2). */
#ifdef __AVX2__
#define VEC_BODY(VXLO, VXHI, VYLO, VYHI)                                                                               \
    switch (op) {                                                                                                      \
    case OP_ADD: for (; i + 4 <= m; i += 4) { VSTORE(z0 + i, vdnf(_mm256_add_pd(VXLO, VYLO))); VSTORE(z1 + i, vupf(_mm256_add_pd(VXHI, VYHI))); } break; \
    case OP_SUB: for (; i + 4 <= m; i += 4) { VSTORE(z0 + i, vdnf(_mm256_sub_pd(VXLO, VYHI))); VSTORE(z1 + i, vupf(_mm256_sub_pd(VXHI, VYLO))); } break; \
    case OP_MUL: for (; i + 4 <= m; i += 4) { vd rl_, rh_; VMULI(VXLO, VXHI, VYLO, VYHI, rl_, rh_); VSTORE(z0 + i, rl_); VSTORE(z1 + i, rh_); } break;     \
    case OP_DIV: for (; i + 4 <= m; i += 4) {                                                                          \
            vd c0 = vdnf(_mm256_div_pd(VSET(1.0), VYHI)), c1 = vupf(_mm256_div_pd(VSET(1.0), VYLO)), rl_, rh_;         \
            VMULI(VXLO, VXHI, c0, c1, rl_, rh_); VSTORE(z0 + i, rl_); VSTORE(z1 + i, rh_); } break;                    \
    }
#else
#define VEC_BODY(VXLO, VXHI, VYLO, VYHI)
#endif
#define BIN_BODY(XLO, XHI, YLO, YHI, VXLO, VXHI, VYLO, VYHI)                                                           \
    size_t i = 0;                                                                                                      \
    VEC_BODY(VXLO, VXHI, VYLO, VYHI)                                                                                   \
    switch (op) {                                                                                                      \
    case OP_ADD: for (; i < m; i++) { z0[i] = dnf(XLO + YLO); z1[i] = upf(XHI + YHI); } break;                         \
    case OP_SUB: for (; i < m; i++) { z0[i] = dnf(XLO - YHI); z1[i] = upf(XHI - YLO); } break;                         \
    case OP_MUL: for (; i < m; i++) { MULI(XLO, XHI, YLO, YHI, z0[i], z1[i]); } break;                                 \
    case OP_DIV: for (; i < m; i++) {                                                                                  \
            double c0 = dnf(1.0/(YHI)), c1 = upf(1.0/(YLO));                                                           \
            MULI(XLO, XHI, c0, c1, z0[i], z1[i]); } break;                                                             \
    }
#ifdef __AVX2__
#define VCONST(n, x) const vd n = VSET(x);
#else
#define VCONST(n, x)
#endif
AI void bin_aa(int op, size_t m, const double *restrict x0, const double *restrict x1, const double *restrict y0,
               const double *restrict y1, double *restrict z0, double *restrict z1) {
    BIN_BODY(x0[i], x1[i], y0[i], y1[i], VLOAD(x0 + i), VLOAD(x1 + i), VLOAD(y0 + i), VLOAD(y1 + i)) }
AI void bin_as(int op, size_t m, const double *restrict x0, const double *restrict x1, const double b0, const double b1,
               double *restrict z0, double *restrict z1) {
    VCONST(vb0, b0) VCONST(vb1, b1) BIN_BODY(x0[i], x1[i], b0, b1, VLOAD(x0 + i), VLOAD(x1 + i), vb0, vb1) }
AI void bin_sa(int op, size_t m, const double a0, const double a1, const double *restrict y0, const double *restrict y1,
               double *restrict z0, double *restrict z1) {
    VCONST(va0, a0) VCONST(va1, a1) BIN_BODY(a0, a1, y0[i], y1[i], va0, va1, VLOAD(y0 + i), VLOAD(y1 + i)) }
AI void bin_ss(int op, size_t m, const double a0, const double a1, const double b0, const double b1,
               double *restrict z0, double *restrict z1) {
    VCONST(va0, a0) VCONST(va1, a1) VCONST(vb0, b0) VCONST(vb1, b1) BIN_BODY(a0, a1, b0, b1, va0, va1, vb0, vb1) }

/* refs: kind in the top 2 bits (0 input, 1 constant, 2 temporary slot, 3 output), index below */
#define KIND(r) ((uint32_t)(r) >> 30)
#define IDX(r) ((uint32_t)(r) & 0x3fffffffu)

typedef struct { const double *lo, *hi; size_t stride; } src_t;

int tape_run(size_t ncell, int ninstr, const int32_t *op, const uint32_t *ra, const uint32_t *rb, const uint32_t *rd,
             const double *p1, const double *p2, const int32_t *aux,
             int nin, const double **in_lo, const double **in_hi, const uint8_t *in_full,
             int nconst, const double *c_lo, const double *c_hi,
             int nmask, const uint8_t **masks,
             int nslot, int nout, double **out_lo, double **out_hi,
             uint8_t *f_pos, uint8_t *f_neg, uint8_t *f_sqneg) {
    double *scr = NULL;
    if (posix_memalign((void **)&scr, 64, (size_t)(nslot > 0 ? nslot : 1)*2*BLK*sizeof(double))) return -1;
    for (int k = 0; k < ninstr; k++) { f_pos[k] = 1; f_neg[k] = 1; f_sqneg[k] = 0; }
    (void)nin; (void)nconst; (void)nmask; (void)nout;
    for (size_t s = 0; s < ncell; s += BLK) {
        size_t m = ncell - s < BLK ? ncell - s : BLK;
        for (int k = 0; k < ninstr; k++) {
            src_t A, B = {0, 0, 0};
#define RESOLVE(S, r) do { uint32_t kd = KIND(r), ix = IDX(r);                                                   \
                if (kd == 0) { size_t st = in_full[ix]; S.lo = in_lo[ix] + (st ? s : 0); S.hi = in_hi[ix] + (st ? s : 0); S.stride = st; } \
                else if (kd == 1) { S.lo = c_lo + ix; S.hi = c_hi + ix; S.stride = 0; }                           \
                else if (kd == 2) { S.lo = scr + (size_t)ix*2*BLK; S.hi = S.lo + BLK; S.stride = 1; }            \
                else { S.lo = out_lo[ix] + s; S.hi = out_hi[ix] + s; S.stride = 1; } } while (0)
            RESOLVE(A, ra[k]);
            double *z0, *z1;
            { uint32_t kd = KIND(rd[k]), ix = IDX(rd[k]);
              if (kd == 2) { z0 = scr + (size_t)ix*2*BLK; z1 = z0 + BLK; } else { z0 = out_lo[ix] + s; z1 = out_hi[ix] + s; } }
            int o = op[k];
            if (o == OP_ADD || o == OP_SUB || o == OP_MUL || o == OP_DIV) {
                RESOLVE(B, rb[k]);
                if (o == OP_DIV) {
                    int pos = 1, neg = 1; const size_t sb = B.stride;
                    for (size_t i = 0; i < m; i++) { pos &= B.lo[i*sb] > 0; neg &= B.hi[i*sb] < 0; }
                    f_pos[k] &= (uint8_t)pos; f_neg[k] &= (uint8_t)neg;
                }
                switch (o) {                      /* literal opcode at each call site: one specialised loop each */
#define CALL4(OPC) case OPC:                                                                            \
                    if (A.stride && B.stride) bin_aa(OPC, m, A.lo, A.hi, B.lo, B.hi, z0, z1);          \
                    else if (A.stride)        bin_as(OPC, m, A.lo, A.hi, B.lo[0], B.hi[0], z0, z1);    \
                    else if (B.stride)        bin_sa(OPC, m, A.lo[0], A.hi[0], B.lo, B.hi, z0, z1);    \
                    else                      bin_ss(OPC, m, A.lo[0], A.hi[0], B.lo[0], B.hi[0], z0, z1); \
                    break;
                CALL4(OP_ADD) CALL4(OP_SUB) CALL4(OP_MUL) CALL4(OP_DIV)
                }
                continue;
            }
            const double *restrict x0 = A.lo, *restrict x1 = A.hi; const size_t sa = A.stride;
            switch (o) {
            case OP_NEG: for (size_t i = 0; i < m; i++) { double a0 = x0[i*sa], a1 = x1[i*sa]; z0[i] = -a1; z1[i] = -a0; } break;
            case OP_SQ: { size_t i = 0;
#ifdef __AVX2__
                if (sa) for (; i + 4 <= m; i += 4) {
                    vd a0 = VLOAD(x0 + i), a1 = VLOAD(x1 + i), l = _mm256_mul_pd(a0, a0), h = _mm256_mul_pd(a1, a1), zr = _mm256_setzero_pd();
                    vd mm = vseld(_mm256_cmp_pd(a0, zr, _CMP_GE_OQ), l, vseld(_mm256_cmp_pd(a1, zr, _CMP_LE_OQ), h, zr));
                    vd mx = _mm256_max_pd(l, h);
                    mx = vseld(_mm256_or_pd(_mm256_cmp_pd(l, l, _CMP_UNORD_Q), _mm256_cmp_pd(h, h, _CMP_UNORD_Q)), VSET(NAN), mx);
                    VSTORE(z0 + i, vseld(_mm256_cmp_pd(mm, zr, _CMP_GT_OQ), vdnf(mm), zr)); VSTORE(z1 + i, vupf(mx)); }
#endif
                for (; i < m; i++) {
                    double a0 = x0[i*sa], a1 = x1[i*sa], l = a0*a0, h = a1*a1;
                    double mm = seld(a0 >= 0, l, seld(a1 <= 0, h, 0.0));
                    double mx = l > h ? l : h; mx = seld((l != l) | (h != h), NAN, mx);
                    z0[i] = seld(mm > 0, dnf(mm), 0.0); z1[i] = upf(mx); } } break;
            case OP_SQRT: { int bad = 0;
                for (size_t i = 0; i < m; i++) bad |= x0[i*sa] < 0;
                f_sqneg[k] |= (uint8_t)bad;
                size_t i = 0;
#ifdef __AVX2__
                if (sa) for (; i + 4 <= m; i += 4) {
                    vd l = vdnf(_mm256_sqrt_pd(VLOAD(x0 + i))), zr = _mm256_setzero_pd();
                    VSTORE(z0 + i, vseld(_mm256_cmp_pd(l, l, _CMP_UNORD_Q), l, vseld(_mm256_cmp_pd(l, zr, _CMP_GT_OQ), l, zr)));
                    VSTORE(z1 + i, vupf(_mm256_sqrt_pd(VLOAD(x1 + i)))); }
#endif
                for (; i < m; i++) {
                    double l = dnf(sqrt(x0[i*sa]));
                    z0[i] = seld(l != l, l, seld(l > 0, l, 0.0)); z1[i] = upf(sqrt(x1[i*sa])); } } break;
            case OP_CLIP: { const double lo = p1[k], hi = p2[k];        /* np.clip = minimum(maximum(x, lo), hi), NaN kept */
                for (size_t i = 0; i < m; i++) {
                    double a0 = x0[i*sa], a1 = x1[i*sa];
                    double u = a0 < lo ? lo : a0; u = u > hi ? hi : u;
                    double v = a1 < lo ? lo : a1; v = v > hi ? hi : v;
                    z0[i] = u; z1[i] = v; } } break;
            case OP_TAILHI: for (size_t i = 0; i < m; i++) { double a1 = x1[i*sa]; z0[i] = 0.0; z1[i] = a1; } break;
            case OP_ZERO: for (size_t i = 0; i < m; i++) { z0[i] = 0.0; z1[i] = 0.0; } break;
            case OP_MSEL: { const uint8_t *mk = masks[aux[k]] + s; const double val = p1[k];
                for (size_t i = 0; i < m; i++) { double a0 = x0[i*sa], a1 = x1[i*sa]; z0[i] = mk[i] ? a0 : val; z1[i] = mk[i] ? a1 : val; } } break;
            default: free(scr); return -2;
            }
        }
    }
    free(scr);
    return 0;
}
