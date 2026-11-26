"""Local chart decisions. Bounds and all geometric operations are rational."""
from fractions import Fraction as Q
from frozen import signed,need

NAMES=('Z1','Z2','D1','D2','Az','By','Bx','Ny','Jyx','Jyz','Nx','Jxy','Jxz')
TARGETS={'Z1':('Az','By'),'Z2':('Az','Bx'),'D1':('Ny','Jyx','Jyz'),'D2':('Nx','Jxy','Jxz')}
EXPECTED={'Az':1,'By':-1,'Bx':-1,'Ny':-1,'Nx':-1,'Jyx':1,'Jxy':1,'Jyz':1,'Jxz':1}
DEPTH=10
GOAL=Q(1,4096)
def span(box,j):
    return box[2*j:2*j+2]
def setspan(box,j,interval):
    return box[:2*j]+tuple(interval)+box[2*j+2:]
def sub(x,y):
    return x[0]-y[1],x[1]-y[0]
def mul(x,y):
    v=[a*b for a in x for b in y]
    return min(v),max(v)
def div(x,y):
    need(signed(y),'zero divisor')
    return mul(x,(1/y[1],1/y[0]))
def mid(x):
    return (x[0]+x[1])/2
def meet(x,y):
    z=max(x[0],y[0]),min(x[1],y[1])
    need(z[0]<=z[1],'certified graph disappeared')
    return z

def classify(band,transverse,name,evaluate,deep=True):
    curve=band['q']
    c=band['cross']
    b=1-c
    rootbox=tuple(map(Q,band['box']))
    leaves=[]
    def contract(box):
        for _ in range(3):
            old=span(box,c)
            m=mid(old)
            h=evaluate(curve,0,setspan(box,c,(m,m)),1024)
            new=meet(old,sub((m,m),div(h,transverse)))
            box=setspan(box,c,new)
            if new[1]-new[0]>=(old[1]-old[0])*Q(3,4):
                break
        return box
    def base_face(box,side):
        point=span(box,b)[side]
        return contract(setspan(box,b,(point,point)))
    def leaf(box,path,outcome,**data):
        leaves.append(dict(path=path,box=list(map(str,box)),status=outcome,**data))
    def visit(box,path):
        g=evaluate(name,0,box,64)
        if not signed(g):
            g=evaluate(name,0,box,256)
        if not signed(g) and not deep:
            leaf(box,path,"UNRESOLVED")
            return
        if not signed(g):
            box=contract(box)
            g=evaluate(name,0,box,1024)
        sign=signed(g)
        if sign:
            leaf(box,path,'EXPECTED' if sign==EXPECTED[name] else 'REVERSED',sign=sign)
            return
        # Only an unresolved coefficient requests extra along-curve information.
        if len(path)>=3:
            gb=evaluate(name,1+b,box,1024)
            gc=evaluate(name,1+c,box,1024)
            hb=evaluate(curve,1+b,box,1024)
            slope=sub(gb,mul(gc,div(hb,transverse)))
            if signed(slope):
                faces=[signed(evaluate(name,0,base_face(box,j),1024)) for j in (0,1)]
                if faces[0]==faces[1]!=0:
                    leaf(box,path,'EXPECTED' if faces[0]==EXPECTED[name] else 'REVERSED',sign=faces[0])
                    return
                if faces[0]*faces[1]==-1:
                    need(faces==[-signed(slope),signed(slope)],'endpoint order inconsistent')
                    # Keep the certified parent even if the zero is exactly on
                    # a new midpoint. Only the published root box is contracted.
                    domain=box
                    for _ in range(DEPTH):
                        old=span(box,b)
                        m=mid(old)
                        at_mid=contract(setspan(box,b,(m,m)))
                        g_mid=evaluate(name,0,at_mid,1024)
                        new=meet(old,sub((m,m),div(g_mid,slope)))
                        box=contract(setspan(box,b,new))
                        if (max(span(box,j)[1]-span(box,j)[0] for j in (0,1))<=GOAL
                                or new[1]-new[0]>=(old[1]-old[0])*Q(3,4)):
                            break
                    leaf(box,path,'UNIQUE_ZERO',domain=list(map(str,domain)),
                         face_signs=faces,slope=list(map(str,slope)))
                    return
        if len(path)==DEPTH:
            faces=[signed(evaluate(name,0,base_face(box,j),1024)) for j in (0,1)]
            if faces[0]*faces[1]==-1:
                leaf(box,path,'ZERO_EXISTS',face_signs=faces)
            else:
                leaf(box,path,'UNRESOLVED')
            return
        lo,hi=span(box,b)
        m=(lo+hi)/2
        for side,part in enumerate(((lo,m),(m,hi))):
            visit(setspan(box,b,part),path+str(side))
    visit(rootbox,'')
    return leaves
