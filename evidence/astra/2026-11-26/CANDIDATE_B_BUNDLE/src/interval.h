/* Adapted from Astra equator src/interval.h. Real MPFR headers are mandatory. */
#pragma once
#include <gmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>
#include <mpfr.h>
#include <setjmp.h>
_Static_assert(GMP_NUMB_BITS == 64 && GMP_LIMB_BITS == 64, "requires 64-bit GMP limbs");
#if MPFR_VERSION < MPFR_VERSION_NUM(4,2,0)
#error Candidate B uses MPFR 4.2 or later (mpfr_sinpi and mpfr_cospi)
#endif
static mpfr_prec_t precision = 128;
static jmp_buf error_jump;
static const char *error_text;
static _Noreturn void fail(const char *message) { error_text=message; longjmp(error_jump,1); }
typedef struct {long exp;int sign;mp_limb_t limb[4];} Num;
typedef struct {Num lo,hi;} I;
#define DOWN MPFR_RNDD
#define UP MPFR_RNDU
static inline __mpfr_struct view(const Num *x){return (__mpfr_struct){precision,x->sign,x->exp,(mp_limb_t*)x->limb};}
static inline Num finish(Num *out,__mpfr_struct dst){
    if(!mpfr_number_p(&dst)) fail("nonfinite MPFR operation");
    out->exp=dst._mpfr_exp;out->sign=dst._mpfr_sign;return *out;
}
#define UNARY(name) static inline Num rn_##name(Num x,mpfr_rnd_t r){Num out={0};__mpfr_struct a=view(&x),z=view(&out);mpfr_##name(&z,&a,r);return finish(&out,z);}
UNARY(sqrt) UNARY(sin) UNARY(cos) UNARY(abs) UNARY(neg)
#define BINARY(name) static inline Num rn_##name(Num x,Num y,mpfr_rnd_t r){Num out={0};__mpfr_struct a=view(&x),b=view(&y),z=view(&out);mpfr_##name(&z,&a,&b,r);return finish(&out,z);}
BINARY(add) BINARY(sub) BINARY(mul) BINARY(div)
static inline Num num(long n){Num o={0};__mpfr_struct z=view(&o);mpfr_set_si(&z,n,DOWN);return finish(&o,z);}
static inline Num rational(mpq_t q,mpfr_rnd_t r){Num o={0};__mpfr_struct z=view(&o);mpfr_set_q(&z,q,r);return finish(&o,z);}
static inline Num circle(mpfr_rnd_t r){Num o={0};__mpfr_struct z=view(&o);mpfr_const_pi(&z,r);return finish(&o,z);}
static inline int cmp(Num x,Num y){__mpfr_struct a=view(&x),b=view(&y);return mpfr_cmp(&a,&b);}
static inline int sgn(Num x){__mpfr_struct v=view(&x);return mpfr_cmp_si(&v,0);}
static inline int numfinite(Num x){__mpfr_struct v=view(&x);return mpfr_number_p(&v);}
static inline Num min2(Num a,Num b){return cmp(a,b)<=0?a:b;}
static inline Num max2(Num a,Num b){return cmp(a,b)>=0?a:b;}
static I iz,one,pii;
static inline I pt(Num x){return (I){x,x};}
static inline I integer(long n){return pt(num(n));}
static inline I plus(I a,I b){return (I){rn_add(a.lo,b.lo,DOWN),rn_add(a.hi,b.hi,UP)};}
static inline I minus(I a,I b){return (I){rn_sub(a.lo,b.hi,DOWN),rn_sub(a.hi,b.lo,UP)};}
static inline I neg(I a){return (I){rn_neg(a.hi,DOWN),rn_neg(a.lo,UP)};}
static inline I times(I a,I b){
    int A=sgn(a.lo)>=0?1:sgn(a.hi)<=0?-1:0,B=sgn(b.lo)>=0?1:sgn(b.hi)<=0?-1:0;
    if(A>0&&B>0)return (I){rn_mul(a.lo,b.lo,DOWN),rn_mul(a.hi,b.hi,UP)};
    if(A>0&&B<0)return (I){rn_mul(a.hi,b.lo,DOWN),rn_mul(a.lo,b.hi,UP)};
    if(A<0&&B>0)return (I){rn_mul(a.lo,b.hi,DOWN),rn_mul(a.hi,b.lo,UP)};
    if(A<0&&B<0)return (I){rn_mul(a.hi,b.hi,DOWN),rn_mul(a.lo,b.lo,UP)};
    if(A==0&&B>0)return (I){rn_mul(a.lo,b.hi,DOWN),rn_mul(a.hi,b.hi,UP)};
    if(A==0&&B<0)return (I){rn_mul(a.hi,b.lo,DOWN),rn_mul(a.lo,b.lo,UP)};
    if(A>0&&B==0)return (I){rn_mul(a.hi,b.lo,DOWN),rn_mul(a.hi,b.hi,UP)};
    if(A<0&&B==0)return (I){rn_mul(a.lo,b.hi,DOWN),rn_mul(a.lo,b.lo,UP)};
    return (I){min2(rn_mul(a.lo,b.hi,DOWN),rn_mul(a.hi,b.lo,DOWN)),max2(rn_mul(a.lo,b.lo,UP),rn_mul(a.hi,b.hi,UP))};
}
static inline I square(I a){Num x=rn_abs(a.lo,UP),y=rn_abs(a.hi,UP),h=max2(x,y),l=min2(x,y);return (I){sgn(a.lo)<=0&&sgn(a.hi)>=0?iz.lo:rn_mul(l,l,DOWN),rn_mul(h,h,UP)};}
static inline I recip(I x){if(sgn(x.lo)<=0&&sgn(x.hi)>=0){fail("interval division by zero");}return (I){rn_div(one.lo,x.hi,DOWN),rn_div(one.hi,x.lo,UP)};}
static inline I quotient(I x,I y){return times(x,recip(y));}
static inline I root(I a){if (!numfinite(a.lo) || sgn(a.lo)<0) fail("invalid interval square root");return (I){rn_sqrt(a.lo,DOWN),rn_sqrt(a.hi,UP)};}
static inline int iszero(I x){return sgn(x.lo)==0&&sgn(x.hi)==0;}
static inline Num mag(I x){return max2(rn_abs(x.lo,UP),rn_abs(x.hi,UP));}
static inline Num width(I x){return rn_sub(x.hi,x.lo,UP);}
static inline I meet(I a,I b){
 I v={max2(a.lo,b.lo),min2(a.hi,b.hi)};
 if(!numfinite(v.lo)||!numfinite(v.hi)||cmp(v.lo,v.hi)>0){fail("invalid interval intersection");}return v;
}
static inline I valueq(const char*s){mpq_t q;mpq_init(q);if(mpq_set_str(q,s,10)!=0 || !mpz_sgn(mpq_denref(q))){mpq_clear(q);fail("invalid rational");}mpq_canonicalize(q);I v={rational(q,DOWN),rational(q,UP)};mpq_clear(q);return v;}
static inline void encode(Num x,char *output,long *exponent){
    if(!numfinite(x)) fail("nonfinite enclosure endpoint");
    __mpfr_struct z=view(&x);
    if(mpfr_zero_p(&z)){strcpy(output,"0");*exponent=0;return;}
    mpz_t m;mpz_init(m);
    *exponent=mpfr_get_z_2exp(m,&z);
    mpz_get_str(output,10,m);mpz_clear(m);
}
UNARY(sinpi) UNARY(cospi)
static inline I dyadic(double x){Num out={0};__mpfr_struct z=view(&out);mpfr_set_d(&z,x,MPFR_RNDN);return pt(finish(&out,z));}
