/* Paper II only. The adopted Candidate B source files are preserved separately. */
enum {
    AZ = 4, KY, KX, MY, MX, CYX, CXY, CYZ, CXZ, CORR_COUNT
};

static J scaled(J j, long n) { return jscale(j, integer(n)); }
static J half(J j) { return jscale(j, dyadic(0.5)); }

static J centre_quantity(const Tree *tree, J u, J u2, J c2, J s2, const J lengths[3],
                         const J squares[3]) {
    const int i = tree->quantity == AZ ? 2 : tree->quantity == KY ? 1 : 0;
    const int m = (i+1)%3, n = (i+2)%3;
    const J rest = jsub(constant(one), u2);
    J s[3];
    s[i] = u2;
    s[m] = jmul(rest,c2);
    s[n] = jmul(rest,s2);
    J d = sum3(s[0],jmul(s[1],squares[1]),jmul(s[2],squares[2]));
    d = bounded(d,tree->min_d,tree->max_d);
    const J v = jdiv(squares[i],d);
    const J v2 = jsq(v);
    J db = constant(one);
    for (int j=0; j<3; ++j)
        for (int k=j+1; k<3; ++k) {
            const J a = jsub(jdiv(lengths[j],lengths[k]),jdiv(lengths[k],lengths[j]));
            db = jplus(db,jmul(jmul(s[j],s[k]),jsq(a)));
        }
    db.c[0].lo = max2(db.c[0].lo,one.lo);
    const J gamma = invroot(invroot(db,1),0);
    const J f1 = fun_deriv(gamma,1), f2 = fun_deriv(gamma,2);
    if (tree->quantity == AZ) {
        const J a = jmul(jmul(jsq(gamma),f2),jmul(u2,jsq(jsub(v,constant(one)))));
        const J b = jsub(jmul(u2,sum3(scaled(v2,3),scaled(v,-4),constant(integer(2)))),v);
        return jplus(a,jmul(jmul(gamma,f1),b));
    }

    const J vu = jmul(v,u), w = jsq(vu);
    const J h2 = half(jsub(scaled(w,3),v));
    const J h3 = half(jmul(vu,jsub(scaled(w,5),scaled(v,3))));
    const J h4 = jscale(sum3(scaled(v2,3),scaled(jmul(v,w),-30),scaled(jsq(w),35)),
                        dyadic(0.125));
    const J a1 = jmul(gamma,jsub(vu,u));
    const J a2 = jmul(gamma,jsub(h2,jmul(u,vu)));
    const J a3 = jmul(gamma,jsub(h3,jmul(u,h2)));
    const J a4 = jmul(gamma,jsub(h4,jmul(u,h3)));
    const J a12 = jsq(a1);
    const J k1 = jmul(f1,jsub(a4,jmul(u,a3)));
    const J k2 = jmul(f2,sum3(jmul(a1,a3),half(jsq(a2)),jneg(jmul(jmul(u,a1),a2))));
    const J p3 = jmul(jmul(a12,jsub(scaled(a2,3),jmul(u,a1))),fun_deriv(gamma,3));
    const J p4 = jmul(jsq(a12),fun_deriv(gamma,4));
    return sum3(scaled(jplus(k1,k2),24),scaled(p3,4),p4);
}

static J pole_quantity(const Tree *tree, J t, J t2, J c2, J s2, const J squares[3]) {
    const int f = tree->quantity;
    const int i = (f == MY || f == CYX || f == CYZ) ? 1 : 0;
    const int m = (i+1)%3, n = (i+2)%3;
    const J rest = jsub(constant(one),t2);
    const J mu = jsub(constant(one),scaled(t2,2));
    const J inverse[3] = {constant(one),invroot(squares[1],0),invroot(squares[2],0)};
    const J a = jmul(rest,c2), b = jmul(rest,s2);
    J d = sum3(jmul(a,squares[m]),jmul(b,squares[n]),jmul(t2,squares[i]));
    J B = sum3(jmul(jsq(mu),inverse[i]),scaled(jmul(jmul(t2,a),inverse[m]),4),
               scaled(jmul(jmul(t2,b),inverse[n]),4));
    d = bounded(d,tree->min_d,tree->max_d);
    B = bounded(B,tree->min_b,tree->max_b);
    const J L = invroot(invroot(jmul(d,B),1),0);
    const J gamma = jmul(t,L);
    const J f1 = fun_deriv(gamma,1), f2 = fun_deriv(gamma,2);

    if (f == MY || f == MX) {
        const J lambda = jdiv(squares[i],d);
        const J k = jmul(t2,lambda);
        const J p = sum3(scaled(jsq(mu),2),scaled(jmul(mu,k),4),jsub(scaled(jsq(k),3),k));
        const J n2 = jsq(jplus(mu,k));
        return jplus(jmul(jmul(L,f1),p),jmul(jmul(jmul(t,jsq(L)),f2),n2));
    }

    const int j = (f == CYX || f == CXY) ? 1-i : 2;
    const J w2 = j == m ? a : b;
    const J sigma = jsub(squares[j],squares[i]);
    const J reciprocal = jmul(inverse[i],inverse[j]);
    const J c = jdiv(scaled(t,2),d);
    const J e = jdiv(scaled(jmul(jmul(reciprocal,t),mu),4),B);
    const J p2 = jmul(w2,jsq(jplus(c,e)));
    const J j2 = jmul(w2,jplus(jsq(c),jsq(e)));
    const J S2 = scaled(jsub(jdiv(jsub(t2,w2),d),
                         jdiv(jmul(reciprocal,jsub(jsq(mu),scaled(jmul(t2,w2),4))),B)),2);
    const J gf = jmul(gamma,f1);
    const J term1 = jneg(half(jmul(gf,S2)));
    const J term2 = jmul(gf,jplus(half(j2),jscale(p2,dyadic(0.25))));
    const J term3 = jscale(jmul(jmul(jsq(gamma),f2),p2),dyadic(0.25));
    return scaled(jmul(jmul(t,t2),jplus(term1,jmul(sigma,jplus(term2,term3)))),4);
}

static I correspondence_integrand(const Tree *tree, I u, I w, int angular) {
    layout(0,tree->derivative != 0,angular < 0 ? 0 : 4);
    const J y = variable(tree->y,tree->derivative == 1,0);
    const J z = variable(tree->z,tree->derivative == 2,0);
    const J lengths[3] = {constant(one),y,z};
    const J squares[3] = {constant(one),jsq(y),jsq(z)};
    const J t = variable(u,0,angular == 0), t2 = jsq(t);
    const J c2 = jsq(azimuth(w,1,angular == 1));
    const J s2 = jsq(azimuth(w,0,angular == 1));
    const J g = tree->quantity <= KX ? centre_quantity(tree,t,t2,c2,s2,lengths,squares)
                                    : pole_quantity(tree,t,t2,c2,s2,squares);
    return times(at(&g,ix(0,np,nv)),fact[nv]);
}
