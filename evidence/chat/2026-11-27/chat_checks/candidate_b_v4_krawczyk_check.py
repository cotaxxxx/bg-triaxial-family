"""chat: independent exact-rational Krawczyk recomputation from the v4 MPFR intervals (no producer code).
usage: python3 -I this.py V4_RESULT_DIR"""
import json,sys
from fractions import Fraction as F
R=sys.argv[1]
def r(v): return F(int(v['n']))*(F(2)**v['e'] if 'e' in v else F(1,int(v['d'])))
iv=lambda e:tuple(map(r,e['interval'])); bx=lambda b:tuple(map(r,b))
I={x['id']:x for x in map(json.loads,open(R+'/work/local/integrals.jsonl'))}
def mul(a,b):
    p=[a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1]]; return (min(p),max(p))
add=lambda a,b:(a[0]+b[0],a[1]+b[1]); sub=lambda a,b:(a[0]-b[1],a[1]-b[0])
X=(F(161,256),F(165,256),F(291,128),F(37,16))
for l in open(R+'/work/local/intersections.jsonl'):
    t=json.loads(l)
    vals=[I[i] for i in t['values']]; J=[[I[i] for i in rr] for rr in t['jacobian']]
    Y=bx(J[0][0]['box']); m=(( Y[0]+Y[1])/2,(Y[2]+Y[3])/2)
    assert all(bx(x['box'])==Y for rr in J for x in rr)
    assert [(x['quantity'],x['derivative']) for x in vals]==[('Z1',0),('D2',0)] and all(bx(x['box'])==(m[0],m[0],m[1],m[1]) for x in vals)
    assert [(x['quantity'],x['derivative']) for rr in J for x in rr]==[('Z1',1),('Z1',2),('D2',1),('D2',2)]
    assert len({x['cells'] for x in vals}|{x['cells'] for rr in J for x in rr})==1
    Jv=[[iv(x) for x in rr] for rr in J]; H=[iv(x) for x in vals]
    mid=[[(a+b)/2 for a,b in rr] for rr in Jv]; det=mid[0][0]*mid[1][1]-mid[0][1]*mid[1][0]; assert det!=0
    C=[[mid[1][1]/det,-mid[0][1]/det],[-mid[1][0]/det,mid[0][0]/det]]
    pt=lambda c:(c,c)
    M=[[sub(pt(F(int(i==j))),add(mul(pt(C[i][0]),Jv[0][j]),mul(pt(C[i][1]),Jv[1][j]))) for j in range(2)] for i in range(2)]
    d=[(Y[0]-m[0],Y[1]-m[0]),(Y[2]-m[1],Y[3]-m[1])]
    K=[add(sub(pt(m[i]),add(mul(pt(C[i][0]),H[0]),mul(pt(C[i][1]),H[1]))),add(mul(M[i][0],d[0]),mul(M[i][1],d[1]))) for i in range(2)]
    q=max(sum(max(abs(a),abs(b)) for a,b in row) for row in M)
    strict=[Y[0]<K[0][0] and K[0][1]<Y[1], Y[2]<K[1][0] and K[1][1]<Y[3]]
    inX=X[0]<=Y[0] and Y[1]<=X[1] and X[2]<=Y[2] and Y[3]<=X[3]
    print(dict(record=t['id'],cells=vals[0]['cells'],Y=[str(v) for v in Y],Y_in_X=inX,q=float(q),q_lt_1=q<1,K_strict=strict,
               K_y=[float(K[0][0]),float(K[0][1])],K_z=[float(K[1][0]),float(K[1][1])],ACCEPT=all(strict) and q<1 and inX))
