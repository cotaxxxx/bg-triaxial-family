"""chat: independent end-to-end check of the nine new Paper-II coefficients.
Computes E(q) = sphere mean of k*arccos(g)^2 directly from the definition (numpy, float64) and
differentiates by finite differences in the position q. No producer formula is used.
usage: python3 this.py y z  -> prints Az,By,Bx (centre) and Ny,Hyx,Hyz,Nx,Hxy,Hxz,J.. (pole, extrapolated d->0)"""
import sys,json
import numpy as np
y,z=map(float,sys.argv[1:3]); ell=np.array([1.0,y,z]); h=ell**2
def gl(a,b,n):
    x,w=np.polynomial.legendre.leggauss(n); return (b-a)/2*x+(a+b)/2,(b-a)/2*w
def f_of(k,D2,B):
    g=np.clip(k/np.sqrt(D2*B),-1,1); return k*np.arccos(g)**2
# ---- centre: full sphere, Gauss-Legendre in mu, trapezoid in phi
MU,WM=gl(-1,1,240); PH=np.arange(480)*2*np.pi/480
m,p=np.meshgrid(MU,PH,indexing='ij'); s=np.sqrt(1-m*m)
def E_axis_centered(q,axis=2):
    # polar axis = 'axis' ; xi components
    xi=[None]*3; a=axis; b=(a+1)%3; c=(a+2)%3
    xi[a]=m; xi[b]=s*np.cos(p); xi[c]=s*np.sin(p)
    k=1-sum(q[l]*xi[l] for l in range(3)); D2=sum(h[l]*(xi[l]-q[l])**2 for l in range(3)); B=sum(xi[l]**2/h[l] for l in range(3))
    return (f_of(k,D2,B).mean(axis=1)*WM).sum()/2
def fd(fun,order,hh):
    # 9-point central stencils
    c2=np.array([-1/560,8/315,-1/5,8/5,-205/72,8/5,-1/5,8/315,-1/560]); c4=np.array([7/240,-2/5,169/60,-122/15,91/8,-122/15,169/60,-2/5,7/240])
    v=np.array([fun(j*hh) for j in range(-4,5)]); return (c2@v)/hh**2 if order==2 else (c4@v)/hh**4
def axis_fun(i):
    def g(t):
        q=[0,0,0]; q[i]=t; return E_axis_centered(q,axis=i)
    return g
res={'Az':fd(axis_fun(2),2,0.06),'By':fd(axis_fun(1),4,0.08)/6,'Bx':fd(axis_fun(0),4,0.08)/6,
     'Ay(Z1)':fd(axis_fun(1),2,0.06),'Ax(Z2)':fd(axis_fun(0),2,0.06)}
# ---- pole: q=(1-d)e_i, composite GL in r (mu=1-2r^2) with geometric panels, trapezoid in phi
def pole_E(q,i,d):
    edges=[0.0]+[min(1.0,d*2**j/4) for j in range(0,40) if d*2**j/4<1.0]+[1.0]
    tot=0.0; PHI=np.arange(256)*2*np.pi/256; b=(i+1)%3; c=(i+2)%3
    for lo,hi in zip(edges,edges[1:]):
        r,w=gl(lo,hi,24); rr,pp=np.meshgrid(r,PHI,indexing='ij'); mu=1-2*rr*rr; sn=2*rr*np.sqrt(1-rr*rr)
        xi=[None]*3; xi[i]=mu; xi[b]=sn*np.cos(pp); xi[c]=sn*np.sin(pp)
        k=1-sum(q[l]*xi[l] for l in range(3)); D2=sum(h[l]*(xi[l]-q[l])**2 for l in range(3)); B=sum(xi[l]**2/h[l] for l in range(3))
        tot+=((f_of(k,D2,B).mean(axis=1))*2*r*w).sum()
    return tot
def pole_quantities(i,d):
    s_=d/3; c1=np.array([1/12,-2/3,0,2/3,-1/12]); c2=np.array([-1/12,4/3,-5/2,4/3,-1/12])
    def line(dirn):
        vals=[]
        for j in range(-2,3):
            q=[0.0,0.0,0.0]; q[i]=1-d; q[dirn]+=j*s_; vals.append(pole_E(q,i,d))
        return np.array(vals)
    vi=line(i); out={'T':(c1@vi)/s_,'N':(c2@vi)/s_**2}
    for j in range(3):
        if j!=i: out['H%d'%j]=(c2@line(j))/s_**2
    return out
def extrap(i):
    ds=[0.04,0.02,0.01,0.005]; Q=[pole_quantities(i,d) for d in ds]; out={}
    for key in Q[0]:
        v=[q[key] for q in Q]; r1=[2*v[n+1]-v[n] for n in range(3)]; out[key]=(v[-1],r1[-1])
    return out
for i,nm in ((1,'y'),(0,'x')):
    e=extrap(i); T=e['T'][1]; res['T'+nm]=T; res['N'+nm]=e['N'][1]; res['N'+nm+'_raw_d=.005']=e['N'][0]
    for j in range(3):
        if j!=i:
            res['J'+nm+'xyz'[j]]=(e['H%d'%j][1]-T)/(h[j]-h[i]); res['H'+nm+'xyz'[j]]=e['H%d'%j][1]
print(json.dumps(res,indent=1))
