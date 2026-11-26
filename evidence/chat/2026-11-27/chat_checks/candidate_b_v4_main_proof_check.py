"""chat: independent exact-rational check of the v4 main proof (Miranda + slope product) from the frozen v2/v3 ledgers.
usage: python3 -I this.py V2_RESULT_DIR V3_RESULT_DIR"""
import json,sys
from fractions import Fraction as F
V2,V3=sys.argv[1],sys.argv[2]
def r(v): return F(int(v['n']))*(F(2)**v['e'] if 'e' in v else F(1,int(v['d'])))
iv=lambda e:tuple(map(r,e['interval'])); bx=lambda b:tuple(map(r,b))
CH={c['id']:c for c in map(json.loads,open(V2+'/charts.jsonl'))}
E={e['id']:e for e in map(json.loads,open(V2+'/enclosures.jsonl'))}
LI={x['id']:x for x in map(json.loads,open(V3+'/work/local/proof/integrals.jsonl'))}
rows=[json.loads(l) for l in open(V3+'/work/local/proof/intersections.jsonl')]
t=[x for x in rows[2]['trials'] if x['box_index']==0 and x['target']==4096][0]
J=[[LI[i] for i in rr] for rr in t['jacobian']]; B=bx(J[0][0]['box'])
assert all(bx(x['box'])==B for rr in J for x in rr) and [(x['quantity'],x['derivative']) for rr in J for x in rr]==[('Z1',1),('Z1',2),('D2',1),('D2',2)]
Fy,Fz,Gy,Gz=iv(J[0][0]),iv(J[0][1]),iv(J[1][0]),iv(J[1][1])
X=(F(161,256),F(165,256),F(291,128),F(37,16))
assert B[0]<=X[0] and X[1]<=B[1] and B[2]<=X[2] and X[3]<=B[3] and Fy[0]>0 and Gz[1]<0
ab=lambda v:max(abs(v[0]),abs(v[1])); prod=ab(Fz)/Fy[0]*ab(Gy)/(-Gz[1]); assert prod<1
ok=True; zc=X[2]
for cid,z1 in (('main.Z1.charts.169',F(73,32)),('main.Z1.charts.171',F(147,64)),('main.Z1.charts.173',X[3])):
    c=CH[cid]; b=bx(c['box']); f0,f1=[iv(E[f]) for f in c['faces']]; fb=[bx(E[f]['box']) for f in c['faces']]
    ok&=c['cross']==0 and b[2]<=zc and z1<=b[3] and X[0]<=b[0] and b[1]<=X[1] and fb[0]==(b[0],b[0],b[2],b[3]) and fb[1]==(b[1],b[1],b[2],b[3])
    ok&= f0[1]+(X[0]-b[0])*Fy[0]<0 and f1[0]+(X[1]-b[1])*Fy[0]>0; zc=z1
yc=X[0]
for cid,y1 in (('main.D2.charts.99',F(41,64)),('main.D2.charts.96',X[1])):
    c=CH[cid]; b=bx(c['box']); f0,f1=[iv(E[f]) for f in c['faces']]; fb=[bx(E[f]['box']) for f in c['faces']]
    ok&=c['cross']==1 and b[0]<=yc and y1<=b[1] and X[2]<=b[2] and b[3]<=X[3] and fb[0]==(b[0],b[1],b[2],b[2]) and fb[1]==(b[0],b[1],b[3],b[3])
    ok&= f0[0]+(X[2]-b[2])*Gz[1]>0 and f1[1]+(X[3]-b[3])*Gz[1]<0; yc=y1
zs=[bx(c['box']) for c in CH.values() if c['quantity']=='Z1' and c['status']=='CHART']
ds=[bx(c['box']) for c in CH.values() if c['quantity']=='D2' and c['status']=='CHART']+[bx(rows[0]['common_chart']['box'])]
ov=[(max(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),min(a[3],b[3])) for a in zs for b in ds if max(a[0],b[0])<=min(a[1],b[1]) and max(a[2],b[2])<=min(a[3],b[3])]
inX=all(X[0]<=o[0] and o[1]<=X[1] and X[2]<=o[2] and o[3]<=X[3] for o in ov)
print(dict(faces_and_miranda=ok,slope_product=float(prod),product_lt_1=prod<1,supports=(len(zs),len(ds)),overlaps=len(ov),overlaps_in_X=inX))
