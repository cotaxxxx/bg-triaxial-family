"""Predeclared branch inputs for Judge instructions v1.2."""
from fractions import Fraction as F
def cases():
    specs=[
        ('contact','W3',(1,1,0,0,1),0,64,0,32,False),
        ('coarse','W3',(2,2,'1/2','1/2','1/4'),'1/256',64,0,4,False),
        ('lazy','W3',('3/2',2,'1/4','1/4','1/2'),'1/4096',64,0,32,True),
        ('p0','W3',('6/5',2,'19/32','19/32','9/16'),'1/64',64,0,32,False),
        ('outside','H33',(1,1,1,1,0),0,16,0,16,False),
        ('point','H33',(2,3,'1/8','1/4','1/2'),0,64,2,32,False),
        ('lazy-bench','W3',('5/2',4,'1/4','1/8','1/2'),'1/4096',128,2,64,True),
    ]
    for label,k,pt,r,n,g,nh,lazy in specs:
        b=[(F(x)-F(r),F(x)+F(r)) for x in pt]
        yield dict(label=label,kind=k,box=[[str(a),str(b)] for a,b in b],N=n,grade=g,NH=nh,lazy=lazy)
if __name__=='__main__':
    import json
    print(json.dumps(list(cases()),indent=2))
