"""Numerical reference on the fixed unit sphere, independent of interval jets."""
import argparse
import fcntl
import json
import time
from functools import lru_cache
from pathlib import Path
from mpmath import mp
from samples import ROOT, points, contacts

def reference(box,order,dps,contact,progress=None,checkpoint=None):
    mp.dps=dps
    five=[mp.mpf(x.numerator)/x.denominator for x,_ in box]
    s,t,x,y,a=five
    ell=s*t
    calls=0
    @lru_cache(maxsize=None)
    def az(phi): return mp.cos(phi),mp.sin(phi)
    def latitude(lam):
        z,c=mp.sin(lam),mp.cos(lam)
        def longitude(phi):
            nonlocal calls
            calls+=1
            if progress and calls%65536==0:
                progress(calls)
            co,si=az(phi)
            X,Y=c*co,c*si
            n=(X,Y/s,z/ell)
            B=mp.sqrt(sum(v*v for v in n)); nu=[v/B for v in n]
            U,V=X-x,s*(Y-y)
            def arguments(q):
                W=ell*(z-q); D=mp.sqrt(U*U+V*V+W*W)
                k=1-x*X-y*Y-q*z
                v=(U/D,V/D,W/D)
                delta=sum((C-N)**2 for C,N in zip(v,nu))/2
                return k,D,v[2],delta
            def energy(q):
                k,D,u,delta=arguments(q)
                return k*4*mp.asin(mp.sqrt(delta/2))**2
            if order==4:
                return mp.diff(energy,a,4,addprec=100)*c
            k,D,u,delta=arguments(a)
            gamma=1-delta
            if delta==0:
                fp,fpp=-mp.mpf(2),mp.mpf(2)/3
            elif delta<mp.eps**mp.mpf('0.35'):
                # Positive series in delta, differentiated analytically.
                fp=fpp=mp.mpf(0); cn=mp.mpf(2)
                for n0 in range(1,12):
                    fp-=cn*n0*delta**(n0-1)
                    if n0>=2:fpp+=cn*n0*(n0-1)*delta**(n0-2)
                    cn*=mp.mpf(n0)**2/((n0+1)*(2*n0+1))
            else:
                sine=mp.sqrt(delta*(2-delta))
                alpha=2*mp.asin(mp.sqrt(delta/2))
                fp=-2*alpha/sine
                fpp=2*(1-alpha*gamma/sine)/(sine*sine)
            h=ell*u/D
            gp=-z/(D*B)+gamma*h
            gpp=2*gp*h+gamma*(h*h-ell*ell/(D*D))
            return c*(-2*z*fp*gp+k*(fpp*gp*gp+fp*gpp))
        return mp.quad(longitude, phis, method='tanh-sinh',maxdegree=12)
    lams=[-mp.pi/2,mp.asin(a),mp.pi/2]
    phis=[j*mp.pi/2 for j in range(5)]
    if contact:
        rho=mp.sqrt(x*x+y*y+a*a)
        lams=sorted(set(lams+[mp.asin(a/rho)]))
        phis=sorted(set(phis+[mp.atan2(y,x)]))
    callback=(lambda lam:checkpoint.evaluate(lam,latitude)) if checkpoint is not None else latitude
    value=mp.quad(callback,lams,method='tanh-sinh',maxdegree=12)/(4*mp.pi)
    return value,calls

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('kind',choices=['H','Haa','contact'])
    ap.add_argument('i',type=int); ap.add_argument('dps',type=int,choices=[80,110])
    args=ap.parse_args()
    box=contacts()[args.i//2][0][args.i%2] if args.kind=='contact' else points()[args.i]
    work=ROOT/'results'/'ref_work';work.mkdir(parents=True,exist_ok=True)
    lock=(work/f'{args.kind}_{args.i}_{args.dps}.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX)
    result_file=ROOT/'results'/f'reference_{args.kind}_{args.i}_{args.dps}.json'
    if result_file.exists() and result_file.stat().st_size:
        print(result_file.read_text().strip(),flush=True);return
    start=time.monotonic()
    def progress(calls):
        name=ROOT/'results'/f'progress_{args.kind}_{args.i}_{args.dps}.json'
        name.write_text(json.dumps({'evaluations':calls,'seconds':time.monotonic()-start})+'\n')
    from ref_checkpoint import Latitudes
    order=4 if args.kind=='Haa' else 2
    ck=Latitudes(ROOT/'results'/'ref_work'/f'{args.kind}_{args.i}_{args.dps}.jsonl',box,order,args.dps,args.kind=='contact')
    value,calls=reference(box,order,args.dps,args.kind=='contact',progress,ck)
    row={'id':args.i,'kind':args.kind,'dps':args.dps,'value':mp.nstr(value,args.dps),
         'mpf_binary':[str((-1 if value._mpf_[0] else 1)*value._mpf_[1]),value._mpf_[2]],
         'quadrature_calls':calls,'maxdegree':12,'seconds':time.monotonic()-start}
    from run_intervals import atomic
    atomic(result_file,json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)
if __name__=='__main__':main()
