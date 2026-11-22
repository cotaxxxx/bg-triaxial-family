/* Reader 0.6 binary64 primitives. All grid and polynomial coefficients
   arrive as binary64 endpoints. No trigonometric library calls. */
#include <fenv.h>
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(FLT_RADIX==2 && DBL_MANT_DIG==53 && DBL_MAX_EXP==1024 && sizeof(double)==8,
               "binary64 required");
int nearest_mode(void) { return fegetround()==FE_TONEAREST && FLT_EVAL_METHOD==0; }

/* nextafter(x,+/-infinity) for IEEE binary64, including signed zero and
   subnormals. The library reference is exported for bitwise unit testing. */
static inline double adjacent(double x, int up) {
    uint64_t bits;
    memcpy(&bits,&x,sizeof bits);
    const uint64_t mag = bits & UINT64_C(0x7fffffffffffffff);
    if (mag==0) bits = up ? 1 : UINT64_C(0x8000000000000001);
    else if (mag >= UINT64_C(0x7ff0000000000000)) return nextafter(x,up ? INFINITY : -INFINITY);
    else if ((bits>>63) == (unsigned)up) --bits;
    else ++bits;
    memcpy(&x,&bits,sizeof x);
    return x;
}
double test_adjacent(double x,int up) { return adjacent(x,up); }
static inline double dn(double x) { return adjacent(x,0); }
static inline double up(double x) { return adjacent(x,1); }
typedef struct {double lo,hi;} interval;
static inline interval mul(interval a,interval b) {
    double p=a.lo*b.lo, q=a.lo*b.hi, r=a.hi*b.lo, s=a.hi*b.hi;
    double l=p<q?p:q, h=p>q?p:q;
    l=l<r?l:r; h=h>r?h:r;
    l=l<s?l:s; h=h>s?h:s;
    if (!isfinite(p)||!isfinite(q)||!isfinite(r)||!isfinite(s)) {
        if(isnan(p)||isnan(q)||isnan(r)||isnan(s)) return (interval){NAN,NAN};
    }
    return (interval){dn(l),up(h)};
}
enum operation {ADD,SUB,MUL,DIV,SQ,SQRT,NEG};
int apply(int op,size_t n,const double *al,const double *ah,size_t sa,
          const double *bl,const double *bh,size_t sb,double *ol,double *oh) {
    int positive=1,negative=1;
    if (op==DIV) {
        for(size_t i=0;i<n;i++) { positive &= bl[i*sb]>0; negative &= bh[i*sb]<0; }
        if(!positive && !negative) return 1;
    }
    if (op==SQRT) {
        for(size_t i=0;i<n;i++) if(al[i*sa]<0) return 2;
    }
    for (size_t i=0;i<n;i++) {
        interval a={al[i*sa],ah[i*sa]}, b={bl[i*sb],bh[i*sb]}, v;
        switch(op) {
        case ADD: v=(interval){dn(a.lo+b.lo),up(a.hi+b.hi)}; break;
        case SUB: v=(interval){dn(a.lo-b.hi),up(a.hi-b.lo)}; break;
        case MUL: v=mul(a,b); break;
        case DIV:
            v=mul(a,(interval){dn(1./b.hi),up(1./b.lo)}); break;
        case SQ: {
            double l=a.lo*a.lo,h=a.hi*a.hi;
            double m=a.lo>=0?l:(a.hi<=0?h:0.);
            v=(interval){m>0?dn(m):0.,up((isnan(l)||isnan(h))?NAN:(l>h?l:h))};break;
        }
        case SQRT:
            {double l=dn(sqrt(a.lo)); v=(interval){isnan(l)?l:(l>0?l:0.),up(sqrt(a.hi))};}break;
        case NEG: v=(interval){-a.hi,-a.lo}; break;
        default: return 3;
        }
        ol[i]=v.lo;oh[i]=v.hi;
    }
    return op==DIV && negative && !positive ? -1 : 0;
}
void horner(size_t n,const double *hl,const double *hh,size_t m,
            const double *cl,const double *ch,double *ol,double *oh) {
    for(size_t i=0;i<n;i++) {
        interval h={hl[i],hh[i]}, a={cl[m-1],ch[m-1]};
        for(size_t j=m-1;j>0;j--) {
            a=mul(a,h);
            a=(interval){dn(a.lo+cl[j-1]),up(a.hi+ch[j-1])};
        }
        ol[i]=a.lo;oh[i]=a.hi;
    }
}
