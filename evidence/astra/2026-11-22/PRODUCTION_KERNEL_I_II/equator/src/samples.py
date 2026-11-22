"""Exact public input geometry. No comparison endpoints are loaded."""
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TILES = [(0,0), (1,3), (2,5), (3,7)]
HAA = [11,62,60,8,53,29,42,43]
CONTACT = [(30,9,1473752885,2268194787), (18,26,389648170,1103898352),
           (31,3,2361926102,3259023912), (30,8,2449788317,3255197840)]
def tile(i,j):
    return [(1+F(11*i,20),1+F(11*(i+1),20)),(1+F(5*j,8),1+F(5*(j+1),8))]
def deg(v): return (F(v),F(v))
def middle(ab): return sum(ab)/2
def points():
    return [[deg(middle(p)) for p in tile(i,j)] + [deg(x),deg(y),deg(a)]
            for i,j in TILES for a in (0,F(1,32)) for x in (F(27,32),F(55,64),F(7,8))
            for y in (F(7,32),F(15,64),F(1,4))]
def contacts():
    out=[]
    for (i,j),(k,l,h0,h1) in zip(TILES,CONTACT):
        shape=tile(i,j)
        pts=[]
        for h,a in ((h0,0),(h1,F(1,64))):
            u=F(h,2**32)
            pts.append([deg(middle(v)) for v in shape]+[deg((k+u)/32),deg((l+u)/32),deg(a)])
        box=shape+[(F(k,32),F(k+1,32)),(F(l,32),F(l+1,32)),(F(0),F(1,32))]
        out.append((pts,box))
    return out
def e1():
    return [(F(b),F(b)+F(d)) for b,d in [('53/20','11/160'),('43/8','5/32'),
           ('27/32','1/64'),('7/32','1/128'),('0','1/1024')]]
def public_boxes():
    raw=(ROOT/'inputs/E3_BOXES_PUBLIC.jsonl').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='183bc5412593c223e5b799a8f08b6aec24077e2bbd5860bb02843c2353b04a80'
    groups=[(0,0,27,7,218),(1,3,27,7,33),(2,5,0,23,40),(2,5,27,7,30),
            (3,7,0,23,48),(3,7,4,15,45),(3,7,10,0,32),(3,7,27,7,28)]
    population=[f'{i},{j},{k},{l},0,{h}' for i,j,k,l,n in groups for h in range(1,n+1)]
    ids=sorted(population,key=lambda x:(hashlib.sha256(('20261126|'+x).encode()).digest(),x))[:20]
    rows=[json.loads(x) for x in raw.splitlines()]
    assert len(population)==474 and [r['id'] for r in rows]==ids
    out=[]
    for n,r in enumerate(rows,1):
        assert set(r)=={'id','rank','box','N'} and r['rank']==n
        i,j,k,l,_,h=map(int,r['id'].split(','))
        root=tile(i,j)+[(F(k,32),F(k+1,32)),(F(l,32),F(l+1,32)),(F(0),F(1,32))]
        box=[(F(a),F(b)) for a,b in r['box']]
        assert len(box)==5 and all(a<=c<=d<=b for (a,b),(c,d) in zip(root,box))
        out.append((r['id'],box))
    return out
if __name__=='__main__':
    print(json.dumps({'public_boxes':len(public_boxes()),'V62_points':len(points()),
                      'contact_boxes':len(contacts()),'Haa_ids':HAA}))
