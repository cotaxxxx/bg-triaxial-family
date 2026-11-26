/* The included Candidate B code supplies J (jets), I (MPFR intervals),
 * azimuth(), bounded(), setup and adaptive Gauss integration. */
static J scale(J a, int n) { return jscale(a, integer(n)); }
static J product3(J a,J b,J c) { return jmul(jmul(a,b),c); }
static J fraction(J a,int n) { return jscale(a,recip(integer(n))); }

/* Four times the t^4 coefficient of E(t e_i); g[0] is gamma(0).
 * h is (1 - 2 U mu t + U t^2)^(-1/2). */
static J axial_quartic(J mu,J ratio,J gamma) {
    J h[5], g[5], powers[5], coeff[5];
    J a = jmul(ratio,mu);
    h[0] = constant(one);
    for (int k=1; k<=4; ++k) {
        J value = scale(jmul(a,h[k-1]),2*k-1);
        if (k>=2) value = jsub(value,scale(jmul(ratio,h[k-2]),k-1));
        h[k]=fraction(value,k);
        g[k]=jmul(gamma,jsub(h[k],jmul(mu,h[k-1])));
        powers[k]=constant(iz);
        coeff[k]=constant(iz);
    }
    powers[0]=constant(one);
    for (int j=1; j<=4; ++j) {
        for (int k=4; k>=0; --k) {
            J next=constant(iz);
            for (int l=1; l<=k; ++l)
                next=jplus(next,jmul(powers[k-l],g[l]));
            powers[k]=next;
        }
        J weight=jscale(fun_deriv(gamma,j),recip(fact[j]));
        for (int k=3; k<=4; ++k)
            coeff[k]=jplus(coeff[k],jmul(weight,powers[k]));
    }
    return scale(jsub(coeff[4],jmul(mu,coeff[3])),4);
}

static I extra_integrand(const Tree *tree,I u,I w,int angular) {
    layout(0,tree->derivative!=0,angular<0?0:4);
    /* 4 Az, 5 quartic y, 6 quartic x; 7..9 pole y, 10..12 pole x.
     * Per pole: radial Hessian, shear to other equatorial axis, shear to z. */
    int id=tree->quantity;
    int i = id==4 ? 2 : (id==5 || (id>=7 && id<=9)) ? 1 : 0;
    int j=(i+1)%3, k=(i+2)%3;
    J yy=variable(tree->y,tree->derivative==1,0);
    J zz=variable(tree->z,tree->derivative==2,0);
    J onej=constant(one);
    J ell[3]={onej,yy,zz}, h[3]={onej,jsq(yy),jsq(zz)};
    J h_inv[3]={onej,invroot(h[1],0),invroot(h[2],0)};
    J a=variable(u,0,angular==0), a2=jsq(a), rest=jsub(onej,a2);
    J c2=jsq(azimuth(w,1,angular==1)), s2=jsq(azimuth(w,0,angular==1));
    // Coordinates are evaluated at angle or latitude boxes; no division by a.
    J f;
    if (id<=6) {
        J s[3]; s[i]=a2; s[j]=jmul(rest,c2); s[k]=jmul(rest,s2);
        J d=bounded(sum3(jmul(h[0],s[0]),jmul(h[1],s[1]),jmul(h[2],s[2])),
                    tree->min_d,tree->max_d);
        J db=onej;
        for (int m=0;m<3;++m) for(int n=m+1;n<3;++n) {
            J gap=jsub(jdiv(ell[m],ell[n]),jdiv(ell[n],ell[m]));
            db=jplus(db,product3(s[m],s[n],jsq(gap)));
        }
        db.c[0].lo=max2(db.c[0].lo,one.lo);
        J gamma=invroot(invroot(db,1),0), ratio=jdiv(h[i],d);
        if (id==4) {
            J poly=sum3(scale(jsq(ratio),3),scale(ratio,-4),constant(integer(2)));
            f=jplus(product3(jsq(gamma),fun_deriv(gamma,2),jmul(s[i],jsq(jsub(ratio,onej)))),
                    product3(gamma,fun_deriv(gamma,1),jsub(jmul(s[i],poly),ratio)));
        } else f=axial_quartic(a,ratio,gamma);
    } else {
        J mu=jsub(onej,scale(a2,2));
        J d=bounded(jplus(jmul(a2,h[i]),jmul(rest,jplus(jmul(h[j],c2),jmul(h[k],s2)))),
                    tree->min_d,tree->max_d);
        J b=bounded(jplus(jmul(jsq(mu),h_inv[i]),
                         scale(product3(a2,rest,jplus(jmul(h_inv[j],c2),jmul(h_inv[k],s2))),4)),
                    tree->min_b,tree->max_b);
        J invp=invroot(invroot(jmul(d,b),1),0), gamma=jmul(a,invp);
        J fp=fun_deriv(gamma,1), fpp=fun_deriv(gamma,2);
        int mode=(id-7)%3;
        if (mode==0) {
            J kp=jneg(mu), ratio=jdiv(h[i],d), m=jmul(a,ratio);
            J ku=jmul(kp,invp), v=jsub(ku,jmul(gamma,m));
            J z=jsub(jmul(gamma,jsub(scale(jsq(m),3),ratio)),scale(jmul(ku,m),2));
            f=jplus(scale(product3(kp,fp,v),2),
                    jmul(a,jplus(jmul(fpp,jsq(v)),jmul(fp,z))));
        } else {
            int other=mode==1 ? 1-i : 2;
            J tang2=jmul(rest,other==j?c2:s2);
            J delta=jsub(h[other],h[i]);
            J eta=jneg(jmul(h_inv[i],h_inv[other]));
            J p=jdiv(a,d), t=scale(jdiv(product3(eta,a,mu),b),2);
            J v=jsub(t,p);
            J z=jplus(jdiv(jsub(a2,tang2),d),
                      jmul(eta,jdiv(jsub(jsq(mu),scale(jmul(a2,tang2),4)),b)));
            J weighted=jmul(delta,tang2), gfp=jmul(gamma,fp);
            J first=product3(jplus(jmul(jsq(gamma),fpp),gfp),weighted,jsq(v));
            J second=jmul(gfp,jsub(scale(jmul(weighted,jplus(jsq(p),jsq(t))),2),z));
            f=scale(product3(a,a2,jplus(first,second)),4);
        }
    }
    return times(at(&f,ix(0,np,nv)),fact[nv]);
}
