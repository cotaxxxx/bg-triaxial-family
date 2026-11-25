/* Fixed-precision endpoints use the MPFR 4.x ABI on 64-bit GMP limbs.
 * Each call constructs MPFR views over caller-owned two-limb significands. */
#pragma once
#include <gmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>
#if __has_include(<mpfr.h>)
#include <mpfr.h>
#else
typedef long mpfr_prec_t;
typedef long mpfr_exp_t;
typedef enum {MPFR_RNDN=0,MPFR_RNDZ,MPFR_RNDU,MPFR_RNDD,MPFR_RNDA} mpfr_rnd_t;
typedef struct {mpfr_prec_t _mpfr_prec;int _mpfr_sign;mpfr_exp_t _mpfr_exp;mp_limb_t *_mpfr_d;} __mpfr_struct;
typedef __mpfr_struct *mpfr_ptr;
typedef const __mpfr_struct *mpfr_srcptr;
#define DECL2(n) extern int mpfr_##n(mpfr_ptr,mpfr_srcptr,mpfr_srcptr,mpfr_rnd_t)
DECL2(add);DECL2(sub);DECL2(mul);DECL2(div);
#define DECL1(n) extern int mpfr_##n(mpfr_ptr,mpfr_srcptr,mpfr_rnd_t)
DECL1(sqrt);DECL1(sin);DECL1(cos);DECL1(neg);DECL1(abs);
extern int mpfr_const_pi(mpfr_ptr,mpfr_rnd_t);
extern int mpfr_set_si(mpfr_ptr,long,mpfr_rnd_t);
extern int mpfr_set_q(mpfr_ptr,mpq_srcptr,mpfr_rnd_t);
extern int mpfr_cmp(mpfr_srcptr,mpfr_srcptr);
extern int mpfr_cmp_si(mpfr_srcptr,long);
extern int mpfr_zero_p(mpfr_srcptr);
extern int mpfr_number_p(mpfr_srcptr);
extern mpfr_exp_t mpfr_get_z_2exp(mpz_ptr,mpfr_srcptr);
extern double mpfr_get_d(mpfr_srcptr,mpfr_rnd_t);
extern const char *mpfr_get_version(void);
#endif
_Static_assert(GMP_NUMB_BITS==64,"requires 64-bit GMP limbs");
typedef struct {long exp;int sign;mp_limb_t limb[2];} Num;
typedef struct {Num lo,hi;} I;
enum {DOWN=MPFR_RNDD,UP=MPFR_RNDU};
static inline __mpfr_struct view(const Num *x){return (__mpfr_struct){128,x->sign,x->exp,(mp_limb_t*)x->limb};}
static inline Num finish(Num *out,__mpfr_struct dst){out->exp=dst._mpfr_exp;out->sign=dst._mpfr_sign;return *out;}
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
static inline I recip(I x){if(sgn(x.lo)<=0&&sgn(x.hi)>=0){fputs("zero denominator\n",stderr);exit(2);}return (I){rn_div(one.lo,x.hi,DOWN),rn_div(one.hi,x.lo,UP)};}
static inline I quotient(I x,I y){return times(x,recip(y));}
static inline I root(I a){assert(sgn(a.lo)>=0);return (I){rn_sqrt(a.lo,DOWN),rn_sqrt(a.hi,UP)};}
static inline int iszero(I x){return sgn(x.lo)==0&&sgn(x.hi)==0;}
static inline Num mag(I x){return max2(rn_abs(x.lo,UP),rn_abs(x.hi,UP));}
static inline Num width(I x){return rn_sub(x.hi,x.lo,UP);}
static inline I meet(I a,I b){
 I v={max2(a.lo,b.lo),min2(a.hi,b.hi)};
 if(!numfinite(v.lo)||!numfinite(v.hi)||cmp(v.lo,v.hi)>0){fputs("INCONSISTENT: invalid interval intersection\n",stderr);exit(3);}return v;
}
static inline I valueq(const char*s){mpq_t q;mpq_init(q);if(mpq_set_str(q,s,10)!=0)exit(2);mpq_canonicalize(q);I v={rational(q,DOWN),rational(q,UP)};mpq_clear(q);return v;}
static inline void printnum(Num x){mpz_t m;mpz_init(m);__mpfr_struct z=view(&x);if(!numfinite(x))exit(2);if(mpfr_zero_p(&z)){printf("[\"0\",0]");}else{long e=mpfr_get_z_2exp(m,&z);gmp_printf("[\"%Zd\",%ld]",m,e);}mpz_clear(m);}
static inline void printi(I x){putchar('[');printnum(x.lo);putchar(',');printnum(x.hi);putchar(']');}
extern int mpfr_sinpi(mpfr_ptr,mpfr_srcptr,mpfr_rnd_t);
extern int mpfr_cospi(mpfr_ptr,mpfr_srcptr,mpfr_rnd_t);
extern int mpfr_set_d(mpfr_ptr,double,mpfr_rnd_t);
UNARY(sinpi) UNARY(cospi)
static inline I dyadic(double x){Num out={0};__mpfr_struct z=view(&out);mpfr_set_d(&z,x,MPFR_RNDN);return pt(finish(&out,z));}
