"""Synthetic F(g)=g^2 only. No candidate-B shape-band run."""
from ctypes import CDLL, c_double, c_int
import os
from pathlib import Path
import subprocess
import tempfile
from method import classify
from fractions import Fraction as Q
from prepare_kernel import generate

def ledger_cases():
    band=dict(q='Z1',id='fixture',box=['0','1','0','1'],cross=1,direction=1)
    for root in (Q(2,5),None):
        def oracle(name,d,box,stage):
            x,X,t,T=box
            if name=='Z1':
                return (-Q(1,4),-Q(1,4)) if d==1 else (t-Q(1,4)-X/4,T-Q(1,4)-x/4)
            if root is None:
                return (Q(-2),Q(-1))
            if d:
                return (Q(1),Q(1)) if d==1 else (Q(0),Q(0))
            return (x-root,X-root)
        leaves=classify(band,(Q(1),Q(1)),'By',oracle)
        assert sum(Q(1,2**len(r['path'])) for r in leaves)==1
        if root is None:
            assert [x['status'] for x in leaves]==['EXPECTED']
        else:
            hits=[x for x in leaves if x['status']=='UNIQUE_ZERO']
            assert len(hits)==1 and all(x['status']!='UNRESOLVED' for x in leaves)
            y,Y,z,Z=map(Q,hits[0]['box'])
            assert y<=root<=Y and z<=Q(1,4)+root/4<=Z

def kernel_cases():
    # Test dependency only; production verifier and runner do not import mpmath.
    import mpmath as mp
    mp.mp.dps=54
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)
        generate(p)
        inc=p/'quantities.inc'
        substitute='''static J synthetic(J g,int n) {
            if(n==0)return jsq(g);
            if(n==1)return jscale(g,integer(2));
            return constant(integer(n==2?2:0));
        }
        '''
        inc.write_text(substitute+inc.read_text().replace('fun_deriv(','synthetic('))
        wrapper=r'''
#include "candidate.c"
int test_cell(int id,int d,int angular,double y,double z,double u,double w,double *out){
    if(setjmp(error_jump)) return -1;
    init(128);
    Tree t={0};t.quantity=id;t.derivative=d;t.y=dyadic(y);t.z=dyadic(z);
    t.min_d=square(t.y);t.max_d=square(t.z);t.min_b=recip(t.max_d);t.max_b=recip(t.min_d);
    I v=extra_integrand(&t,dyadic(u),dyadic(w),angular);
    __mpfr_struct a=view(&v.lo),b=view(&v.hi);
    out[0]=mpfr_get_d(&a,MPFR_RNDD);out[1]=mpfr_get_d(&b,MPFR_RNDU);return 0;
}
'''
        wrapper+="""
int ninth(double x,double *out){
    if(setjmp(error_jump)) return -1;
    init(128);layout(0,1,4);
    J v=constant(dyadic(x));entry(&v,ix(0,1,0),one);entry(&v,ix(0,0,1),one);
    J h=fun_deriv(v,4);I r=times(at(&h,ix(0,1,4)),fact[4]);
    __mpfr_struct a=view(&r.lo),b=view(&r.hi);
    out[0]=mpfr_get_d(&a,MPFR_RNDD);out[1]=mpfr_get_d(&b,MPFR_RNDU);return 0;
}
"""
        (p/'smoke.c').write_text(wrapper)
        subprocess.run([os.environ.get('CC','cc'),'-O2','-std=c11','-D_POSIX_C_SOURCE=200809L',
                        '-fPIC','-shared',str(p/'smoke.c'),'-o',str(p/'test.so'),'-lmpfr','-lgmp'],check=True)
        from ctypes import POINTER
        call=CDLL(str(p/'test.so')).test_cell
        call.argtypes=[c_int]*3+[c_double]*4+[POINTER(c_double)]
        def reference(id,y,z,u,w):
            i=2 if id==4 else 1 if id in (5,7,8,9) else 0
            j,k=(i+1)%3,(i+2)%3
            ang=mp.pi*w/2
            mu=u if id<=6 else 1-2*u*u
            xi=[0]*3
            xi[i]=mu
            xi[j]=mp.sqrt(1-mu*mu)*mp.cos(ang)
            xi[k]=mp.sqrt(1-mu*mu)*mp.sin(ang)
            h=[1,y*y,z*z]
            b=sum(xi[l]**2/h[l] for l in range(3))
            def energy(point):
                chord=sum(h[l]*(xi[l]-point[l])**2 for l in range(3))
                return (1-sum(point[l]*xi[l] for l in range(3)))**3/(chord*b)
            def axis(t):
                q=[0]*3;q[i]=t
                return energy(q)
            if id<=6:
                return mp.diff(axis,0,2) if id==4 else mp.diff(axis,0,4)/6
            mode=(id-7)%3
            if mode==0:
                return 2*u*mp.diff(axis,1,2)
            other=1-i if mode==1 else 2
            # Rotate BOTH the material surface variable and the evaluation point.
            # In the co-rotating frame only the metric changes.
            def rotated(theta):
                co,si=mp.cos(theta),mp.sin(theta)
                chord=list(xi);chord[i]-=1
                def rot(v,metric):
                    a=co*v[i]-si*v[other];t=si*v[i]+co*v[other]
                    l=3-i-other
                    return metric[i]*a*a+metric[other]*t*t+metric[l]*v[l]**2
                return (1-mu)**3/(rot(chord,h)*rot(xi,[1/v for v in h]))
            return 2*u*mp.diff(rotated,0,2)/(h[other]-h[i])
        args=list(map(mp.mpf,['0.75','1.5','0.375','0.5']))
        for id in range(4,13):
            for shape,ang_axis in ((0,-1),(1,-1),(2,-1),(0,0),(0,1),(1,0),(2,1)):
                degrees=(int(shape==1),int(shape==2),4*int(ang_axis==0),4*int(ang_axis==1))
                val=mp.diff(lambda *v:reference(id,*v),tuple(args),degrees)
                ends=(c_double*2)()
                assert call(id,shape,ang_axis,*map(float,args),ends)==0
                # The independent high-precision numerical differentiation is diagnostic.
                eps=mp.mpf('1e-38')*(1+abs(val))
                assert mp.mpf(ends[0])-eps<=val<=mp.mpf(ends[1])+eps,(id,degrees,val,list(ends))
        ninth=CDLL(str(p/'test.so')).ninth
        ninth.argtypes=[c_double,POINTER(c_double)]
        for x in (0,.25,.75,1):
            exact=(-mp.factorial(9)*2*mp.nprod(lambda k:k*k/((k+1)*(2*k+1)),[1,8])
                   if x==1 else mp.diff(lambda g:mp.acos(g)**2,mp.mpf(x),9))
            out=(c_double*2)()
            assert ninth(x,out)==0 and mp.mpf(out[0])<=exact<=mp.mpf(out[1]),(x,exact,list(out))
        for id in (8,11):
            out=(c_double*2)()
            assert call(id,0,-1,1,1.5,0.375,0.5,out)==0
            extrap=mp.limit(lambda y:reference(id,y,mp.mpf('1.5'),mp.mpf('.375'),mp.mpf('.5')),1)
            assert mp.mpf(out[0])-mp.mpf('1e-40')<=extrap<=mp.mpf(out[1])+mp.mpf('1e-40')
        print('63 synthetic integrand / derivative, 2 equal-axis and 4 ninth-derivative checks passed')

if __name__=='__main__':
    ledger_cases()
    kernel_cases()
    print('synthetic sign and failure-localization fixtures passed')
