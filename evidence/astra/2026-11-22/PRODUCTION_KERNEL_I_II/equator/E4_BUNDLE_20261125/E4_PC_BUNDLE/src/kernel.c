/* Independent equator quadrature, pre-registered angular revision at fixed precision. */
#include "jets.h"
#include <time.h>
typedef struct {
 I p[5], gap,bmin,frame[3][3],rho,delta,eta,cap;
 int contact,order,which;double lower,upper;
} Problem;
static I norm3(I v[3]){return root(plus(plus(square(v[0]),square(v[1])),square(v[2])));}
static I midpoint(I x){return times(plus(pt(x.lo),pt(x.hi)),dyadic(.5));}
static I crosscomp(I x[3],I y[3],int i){int j=(i+1)%3,k=(i+2)%3;return minus(times(x[j],y[k]),times(x[k],y[j]));}
static void prepare(Problem *p){
 I L=times(p->p[0],p->p[1]),rho=norm3(p->p+2);p->rho=rho;p->bmin=recip(pt(L.hi));
 if(!p->contact){p->gap=minus(one,pt(rho.hi));p->lower=-.5;p->upper=.5;if(sgn(p->gap.lo)<=0){fputs("interior domain failed\n",stderr);exit(4);}return;}
 assert(cmp(rho.lo,dyadic(.5).lo)>=0);
 I n[3],m[3],nstar[3],delta[3];
 for(int i=0;i<3;i++){m[i]=midpoint(p->p[2+i]);n[i]=quotient(p->p[2+i],rho);}
 I nr=norm3(m);
 for(int i=0;i<3;i++){p->frame[2][i]=nstar[i]=quotient(m[i],nr);delta[i]=minus(n[i],nstar[i]);}
 p->delta=norm3(delta);
 int id=0;for(int i=1;i<3;i++)if(cmp(mag(nstar[i]),mag(nstar[id]))<0)id=i;
 I e[3],perp[3];for(int i=0;i<3;i++){e[i]=integer(i==id);perp[i]=minus(e[i],times(nstar[i],nstar[id]));}
 I norm=norm3(perp);for(int i=0;i<3;i++)p->frame[0][i]=quotient(perp[i],norm);
 for(int i=0;i<3;i++)p->frame[1][i]=crosscomp(nstar,p->frame[0],i);
 int found=0;
 for(int k=24;k>=0;k--){double b=1./(1UL<<k);I eta=times(integer(2),trig(dyadic(b*.5),0));
   if(cmp(eta.lo,p->delta.hi)>0){found=1;p->lower=b;p->upper=1.;p->eta=eta;break;}}
 if(!found||p->lower>=1){fputs("contact: whole-sphere fallback\n",stderr);exit(4);}
 p->gap=times(root(pt(rho.lo)),minus(pt(p->eta.lo),pt(p->delta.hi)));
 // M_1, M_2 from the positive coefficient sums, y=1 in Derivation 10.
 I M[3];for(int j=1;j<=2;j++){I v=iz;for(int n=j;n<=96;n++)v=plus(v,coeff[j][n]);
    M[j]=times(fact[j],plus(v,times(dyadic(2.5),coeff[j][97])));}
 I C=plus(times(integer(2),times(M[1],L)),times(plus(M[2],times(integer(3),M[1])),square(L)));
 I r=plus(p->eta,p->delta);r.hi=min2(r.hi,num(2));
 p->cap=quotient(times(C,r),times(integer(2),root(pt(rho.lo))));
}
static J with_derivative(I x,int i){J j=constant(x);
 if(i==4&&na>0)entry(&j,ix(1,0,0),one);
 if(np&&i==pdir)entry(&j,ix(0,1,0),one);
 return j;
}
static I integrand(Problem *p,I u,I v,int angular){
 axis=angular;pdir=p->which;layout(p->order,pdir>=0,angular>=0?4:0);
 J S=with_derivative(p->p[0],0),T=with_derivative(p->p[1],1),L=jmul(S,T);
 J X=with_derivative(p->p[2],2),Y=with_derivative(p->p[3],3),a=with_derivative(p->p[4],4),U=constant(one);
 J su=angle(u,0,angular==0),cu=angle(u,1,angular==0),sv=angle(v,0,angular==1),cv=angle(v,1,angular==1),x[3],jac,vertical;
 if(!p->contact){
  J A=jsub(U,jsq(a)),inv=invroot(jplus(U,jmul(a,su)),0);
  J r=jmul(jmul(invroot(A,1),cu),inv);
  x[0]=jmul(r,cv);x[1]=jmul(r,sv);x[2]=jmul(jplus(su,a),inv);
  vertical=jmul(jmul(A,su),inv);jac=jmul(jmul(A,cu),jsq(inv));
 }else{
  J ec=jmul(su,cv),es=jmul(su,sv);for(int i=0;i<3;i++)x[i]=jplus(jplus(jscale(ec,p->frame[0][i]),jscale(es,p->frame[1][i])),jscale(cu,p->frame[2][i]));
  jac=su;vertical=jsub(x[2],a);
 }
 J k=jsub(U,jplus(jplus(jmul(X,x[0]),jmul(Y,x[1])),jmul(a,x[2])));
 J d2=jplus(jplus(jsq(jsub(x[0],X)),jsq(jmul(S,jsub(x[1],Y)))),jsq(jmul(L,vertical)));
 d2.c[0].lo=max2(d2.c[0].lo,square(pt(p->gap.lo)).lo);
 J b2=jplus(jplus(jsq(x[0]),jsq(jdiv(x[1],S))),jsq(jdiv(x[2],L)));
 b2.c[0].lo=max2(b2.c[0].lo,square(pt(p->bmin.lo)).lo);
 J gamma=jdiv(k,invroot(jmul(d2,b2),1));
 J value=jmul(jmul(jac,k),fun(gamma));
 I coef=at(&value,ix(na,np,nv));
 // u and v are angles in units of pi. Two Jacobian factors of pi
 // combine with 1/(4*pi), and jets are factorial-normalized.
 return times(times(times(coef,fact[na]),fact[nv]),times(pii,dyadic(.25)));
}
typedef struct {double x0,x1,y0,y1;int root;uint64_t path;int depth;I sum,legacy;Num wid, legacy_radius, micro_radius; int nx;} Cell;
static I span(double x,double y){return (I){dyadic(x).lo,dyadic(y).hi};}
static I gl[2];
static I node(double x,double y,int k){return plus(times(plus(dyadic(x),dyadic(y)),dyadic(.5)),times(times(minus(dyadic(y),dyadic(x)),dyadic(.5)),gl[k]));}
/* Positive Peano weights fix the sign of the normalized Gaussian error.
 * Preserve the original symmetric enclosure and its width for tree ordering. */
typedef struct {I legacy, signed_sum, dx4, dy4; Num radius;} Panel;
static Panel panel(Problem *p,double x0,double x1,double y0,double y1){
 I u=span(x0,x1),v=span(y0,y1);
 I d=minus(dyadic(x1),dyadic(x0)),e=minus(dyadic(y1),dyadic(y0)),area=times(d,e);
 I natural=times(area,integrand(p,u,v,-1));
 I fx=integrand(p,u,v,0),fy=integrand(p,u,v,1);
 I d4=square(square(d)),e4=square(square(e));
 I wx=times(d4,pt(mag(fx))),wy=times(e4,pt(mag(fy)));
 I radius=quotient(times(area,plus(wx,wy)),integer(4320));
 I q=iz;
 for(int j=0;j<2;j++)for(int k=0;k<2;k++)
  q=plus(q,integrand(p,node(x0,x1,j),node(y0,y1,k),-1));
 q=times(times(area,dyadic(.25)),q);
 I legacy=meet(natural,plus(q,(I){rn_neg(radius.hi,DOWN),radius.hi}));
 if(p->contact)return (Panel){legacy,legacy,wx,wy,radius.hi};
 I correction=quotient(times(area,plus(times(d4,fx),times(e4,fy))),integer(4320));
 return (Panel){legacy,meet(legacy,plus(q,correction)),wx,wy,radius.hi};
}

/* Work at dyadic cuts. If binary64 cannot represent a cut exactly, stop
 * before constructing a purported partition of that parent interval. */
static void cuts(double lo,double hi,int n,double out[5]){
 out[0]=lo;out[n]=hi;
 for(int step=n;step>1;step/=2)for(int j=0;j<n;j+=step){
  double mid=(out[j]+out[j+step])*.5;
  I exact=midpoint(span(out[j],out[j+step]));
  if(cmp(dyadic(mid).lo,exact.lo)||cmp(dyadic(mid).hi,exact.hi)){
   fputs("angular subdivision precision exhausted\n",stderr);exit(4);
  }
  out[j+step/2]=mid;
 }
}

static unsigned long panel_calls;
static void cell_eval(Problem *p,Cell *c){
 Panel coarse=panel(p,c->x0,c->x1,c->y0,c->y1);
 panel_calls++;
 c->legacy=coarse.legacy;c->wid=width(coarse.legacy);
 c->legacy_radius=coarse.radius;
 if(p->contact){c->sum=coarse.legacy;c->micro_radius=coarse.radius;c->nx=0;return;}

 /* Minimize wx/nx^4 + wy/ny^4 at nx*ny=4. The equivalent
  * thresholds are 16 wx vs wy and wx vs 16 wy; ties favor 2x2. */
 Num wx=coarse.dx4.hi,wy=coarse.dy4.hi;
 int nx=2;
 if(cmp(wx,rn_mul(num(16),wy,UP))>0)nx=4;
 if(cmp(wy,rn_mul(num(16),wx,UP))>0)nx=1;
 int ny=4/nx;
 double x[5],y[5];cuts(c->x0,c->x1,nx,x);cuts(c->y0,c->y1,ny,y);
 I composite=iz;
 Num remainder=num(0);
 for(int i=0;i<nx;i++)for(int j=0;j<ny;j++){
  Panel child=panel(p,x[i],x[i+1],y[j],y[j+1]);
  panel_calls++;
  composite=plus(composite,child.signed_sum);
  remainder=rn_add(remainder,child.radius,UP);
 }
 c->sum=meet(coarse.signed_sum,composite);
 c->micro_radius=remainder;c->nx=nx;
}
static int cellkey(const void *a,const void *b){
 const Cell *c=a,*d=b;if(c->root!=d->root)return c->root<d->root?-1:1;
 uint64_t x=c->path<<(2*(30-c->depth)),y=d->path<<(2*(30-d->depth));
 if(x==y)return c->depth-d->depth;
 return x<y?-1:1;
}
static Cell active[2048],sorted[2048];
static void solve(Problem *p){
 prepare(p);
 int q=0;for(int i=0;i<4;i++)for(int j=0;j<8;j++){
  active[q]=(Cell){.x0=p->lower+(p->upper-p->lower)*i/4,.x1=p->lower+(p->upper-p->lower)*(i+1)/4,.y0=j*.25,.y1=(j+1)*.25,.root=q};
  cell_eval(p,&active[q++]);
 }
 while(1){
  if(q==128||q==512||q==2048){
   memcpy(sorted,active,sizeof(Cell)*q);qsort(sorted,q,sizeof(Cell),cellkey);I sum=iz,legacy_sum=iz;
   Num base_r=num(0),micro_r=num(0);int grids[5]={0};
   for(int j=0;j<q;j++){
    sum=plus(sum,sorted[j].sum);legacy_sum=plus(legacy_sum,sorted[j].legacy);
    base_r=rn_add(base_r,sorted[j].legacy_radius,UP);
    micro_r=rn_add(micro_r,sorted[j].micro_radius,UP);
    grids[sorted[j].nx]++;
   }
   if(cmp(sum.lo,legacy_sum.lo)<0||cmp(sum.hi,legacy_sum.hi)>0){
    fputs("INCONSISTENT: revised outer interval exceeds legacy interval\n",stderr);exit(3);
   }
   printf("{\"panels\":%d,\"outer\":",q);printi(sum);
   printf(",\"legacy_outer\":");printi(legacy_sum);
   printf(",\"panel_calls\":%lu,\"grids\":{\"contact\":%d,\"1x4\":%d,\"2x2\":%d,\"4x1\":%d}",panel_calls,grids[0],grids[1],grids[2],grids[4]);
   printf(",\"coarse_2R_sum\":");printnum(rn_mul(num(2),base_r,UP));
   printf(",\"composite_2R_sum\":");printnum(rn_mul(num(2),micro_r,UP));
   if(p->contact){printf(",\"rho\":");printi(p->rho);printf(",\"eta\":");printi(p->eta);printf(",\"delta\":");printi(p->delta);printf(",\"cap\":");printi(p->cap);sum=plus(sum,(I){rn_neg(p->cap.hi,DOWN),p->cap.hi});}
   printf(",\"interval\":");printi(sum);printf("}\n");fflush(stdout);if(q==2048)return;
  }
  int best=0;for(int i=1;i<q;i++){int k=cmp(active[i].wid,active[best].wid);if(k>0||(k==0&&cellkey(active+i,active+best)<0))best=i;}
  Cell par=active[best];if(par.depth>=30){fputs("panel representation exhausted\n",stderr);exit(4);}
  double x[3]={par.x0,(par.x0+par.x1)*.5,par.x1},y[3]={par.y0,(par.y0+par.y1)*.5,par.y1};
  if(cmp(dyadic(x[1]).lo,midpoint(span(x[0],x[2])).lo)||cmp(dyadic(y[1]).lo,midpoint(span(y[0],y[2])).lo)){fputs("angular midpoint precision exhausted\n",stderr);exit(4);}
  for(int k=0;k<4;k++){
   Cell *child=&active[k?q++:best];*child=(Cell){.root=par.root,.path=4*par.path+(unsigned)k,.depth=par.depth+1,.x0=x[k/2],.x1=x[1+k/2],.y0=y[k%2],.y1=y[1+k%2]};
   cell_eval(p,child);
  }
 }
}
int main(int argc,char**argv){
 if(argc!=14){fprintf(stderr,"usage: kernel contact(0/1/2=auto) a_order other_axis(-1..3) ten-rational-endpoints\n");return 2;}
 tables();gl[1]=recip(root(integer(3)));gl[0]=neg(gl[1]);
 Problem p={.contact=atoi(argv[1]),.order=atoi(argv[2]),.which=atoi(argv[3])};
 if(p.order<2||p.order>4||p.which< -1||p.which>3)return 2;
 for(int i=0;i<5;i++){I l=valueq(argv[4+2*i]),h=valueq(argv[5+2*i]);p.p[i]=(I){l.lo,h.hi};if(cmp(l.lo,h.hi)>0)return 2;}
 if(p.contact==2)p.contact=cmp(norm3(p.p+2).hi,one.lo)>=0;
 solve(&p);return 0;
}
