/* Rectangular truncated Taylor algebra in (a, one shape/position derivative,
 * one angular derivative). The table contains only componentwise valid pairs. */
#pragma once
#include "interval.h"
#define NJ 10
typedef struct {I c[NJ];uint64_t mask;} J;
static int na,np,nv,sz;
static int ix(int a,int p,int v){return a+(na+1)*(p+(np+1)*v);}
static int pairs[NJ][NJ],npair[NJ]; static uint64_t target[NJ];
static void layout(int a,int p,int v){
 na=a;np=p;nv=v;sz=(a+1)*(p+1)*(v+1);if (sz>NJ) fail("Taylor layout too large");
 for(int z=0;z<=v;z++)for(int y=0;y<=p;y++)for(int x=0;x<=a;x++){
  int i=ix(x,y,z);npair[i]=0;target[i]=UINT64_C(1)<<i;
  for(int k=0;k<=z;k++)for(int j=0;j<=y;j++)for(int h=0;h<=x;h++)pairs[i][npair[i]++]=ix(h,j,k);
 }
}
static J constant(I a){J o={.mask=1};o.c[0]=a;return o;}
static void entry(J *j,int i,I v){j->c[i]=v;j->mask|=target[i];}
static I at(const J *j,int i){return j->mask&target[i]?j->c[i]:iz;}
static J jplus(J x,J y){J o=x;uint64_t m=y.mask;while(m){int i=__builtin_ctzll(m);m&=m-1;entry(&o,i,x.mask&target[i]?plus(x.c[i],y.c[i]):y.c[i]);}return o;}
static J jneg(J x){uint64_t m=x.mask;while(m){int i=__builtin_ctzll(m);m&=m-1;x.c[i]=neg(x.c[i]);}return x;}
static J jsub(J x,J y){return jplus(x,jneg(y));}
static J jscale(J x,I b){uint64_t m=x.mask;while(m){int i=__builtin_ctzll(m);m&=m-1;x.c[i]=times(x.c[i],b);}return x;}
static J jmul(J x,J y){
 if(x.mask==1)return jscale(y,x.c[0]);
 if(y.mask==1)return jscale(x,y.c[0]);
 J o={.mask=0};for(int i=0;i<sz;i++){
  int have=0;I accum=iz;
  for(int h=0;h<npair[i];h++){int j=pairs[i][h],k=i-j;
   if((x.mask&target[j])&&(y.mask&target[k])){I v=times(x.c[j],y.c[k]);accum=have?plus(accum,v):v;have=1;}}
  if(have)entry(&o,i,accum);
 }return o;
}
static J jsq(J x){J o=jmul(x,x);o.c[0]=square(x.c[0]);return o;}
static J invroot(J x,int sqrtmode){
 J o=constant(sqrtmode?root(x.c[0]):recip(x.c[0]));
 I scale=sqrtmode?recip(plus(o.c[0],o.c[0])):neg(o.c[0]);
 for(int i=1;i<sz;i++){
  int any=0;I t=iz;
  for(int h=1;h<npair[i]-(sqrtmode?1:0);h++){
   int j=pairs[i][h],k=i-j;J *lhs=sqrtmode?&o:&x;
   if((lhs->mask&target[j])&&(o.mask&target[k])){I term=times(lhs->c[j],o.c[k]);t=any?plus(t,term):term;any=1;}
  }
  if(sqrtmode){if(any||(x.mask&target[i]))entry(&o,i,times(minus(at(&x,i),t),scale));}
  else if(any)entry(&o,i,times(t,scale));
 }
 return o;
}
static J jdiv(J x,J y){return jmul(x,invroot(y,0));}
static I fact[9],coeff[9][98],pifact[5],halfints[15];
static void tables(void){
 iz=integer(0);one=integer(1);pii=(I){circle(DOWN),circle(UP)};
 fact[0]=one;pifact[0]=one;
 for(int i=1;i<=8;i++){fact[i]=times(fact[i-1],integer(i));if(i<=4)pifact[i]=quotient(times(pifact[i-1],pii),integer(i));}
 for(int i=-5;i<=9;i++)halfints[i+5]=dyadic(i*0.5);
 // c_n * binom(n,j), the Taylor coefficient, including its factorial already.
 I c=integer(2);
 for(int n=1;n<=97;n++){
  I b=one;
  for(int j=0;j<=8&&j<=n;j++){coeff[j][n]=times(c,b);b=quotient(times(b,integer(n-j)),integer(j+1));}
  c=quotient(times(c,integer(n*n)),integer((n+1)*(2*n+1)));
 }
}
static I trig(I x,int cosine){
 Num lo=cosine?rn_cospi(x.lo,DOWN):rn_sinpi(x.lo,DOWN);
 Num hi=cosine?rn_cospi(x.lo,UP):rn_sinpi(x.lo,UP);
 lo=min2(lo,cosine?rn_cospi(x.hi,DOWN):rn_sinpi(x.hi,DOWN));
 hi=max2(hi,cosine?rn_cospi(x.hi,UP):rn_sinpi(x.hi,UP));
 for(int i=-2;i<=4;i++)if((((i+8)%2)==(cosine?0:1))&&cmp(x.lo,halfints[5+i].lo)<=0&&cmp(x.hi,halfints[5+i].hi)>=0){
  int pos=cosine?((i+8)%4==0):((i+8)%4==1);
  if(pos)hi=one.hi;else lo=num(-1);
 }
 return (I){lo,hi};
}
static J angle(I x,int cosine,int active){
 I tr[4];tr[0]=trig(x,0);tr[1]=trig(x,1);tr[2]=neg(tr[0]);tr[3]=neg(tr[1]);
 J o=constant(tr[cosine]);
 if(active)for(int j=1;j<=nv;j++)entry(&o,ix(0,0,j),times(tr[(cosine+j)%4],pifact[j]));
 return o;
}
static J fun_deriv(J g, int derivative){
 I y=minus(one,meet(g.c[0],(I){iz.lo,one.hi}));
 int ndeg=na+np+nv;
 I d[9];
 for(int j=0;j<=ndeg;j++){
  int order=derivative+j;
  int end=order?order:1;
  // Positive series: evaluate the lower endpoint without the nonnegative tail.
  // Initialize the upper Horner recurrence with the rigorous n>=97 tail.
  Num l=coeff[order][96].lo;
  Num h=rn_add(coeff[order][96].hi,rn_mul(rn_mul(coeff[order][97].hi,num(5),UP),rn_mul(y.hi,dyadic(.5).hi,UP),UP),UP);
  for(int n=95;n>=end;n--){l=rn_add(coeff[order][n].lo,rn_mul(y.lo,l,DOWN),DOWN);h=rn_add(coeff[order][n].hi,rn_mul(y.hi,h,UP),UP);}
  if(!order){l=rn_mul(l,y.lo,DOWN);h=rn_mul(h,y.hi,UP);}
  d[j]=(I){l,h};
  for (int k=j+1;k<=order;++k) d[j]=times(d[j],integer(k));
  if(order%2)d[j]=neg(d[j]);
 }
 J delta=g;delta.mask&=~UINT64_C(1);
 J result=constant(d[ndeg]);
 for(int j=ndeg-1;j>=0;j--)result=jplus(jmul(result,delta),constant(d[j]));
 return result;
}
