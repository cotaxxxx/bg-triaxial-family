"""Exact arithmetic for the graph tests and local two-equation enclosures."""

from verify_v2 import F, difference, mul_range, slope, strict


def add(a,b):
    return a[0]+b[0],a[1]+b[1]


def hull_abs(b):
    return max(map(abs,b))


def graph_test(cross, transverse, along, q_y, q_z, ends):
    other = 1-cross
    derivative = (q_y,q_z)
    root_slope = slope(along,transverse)
    along_curve = add(derivative[other],mul_range(derivative[cross],root_slope))
    lower,upper = map(strict,ends)
    if strict(along_curve) and lower*upper == -1 and upper == strict(along_curve):
        receiver = "GRAPH_ZERO"
    elif strict(along_curve) and lower == upper != 0:
        receiver = "GRAPH_POS" if lower > 0 else "GRAPH_NEG"
    else:
        receiver = "OPEN"
    return receiver,along_curve


def krawczyk(box, values, jacobian):
    centres = [(box[k]+box[k+1])/2 for k in (0,2)]
    m = [[(x+y)/2 for x,y in row] for row in jacobian]
    a,b = m
    det = a[0]*b[1]-a[1]*b[0]
    if det == 0:
        return None
    c = [[b[1]/det,-a[1]/det],[-b[0]/det,a[0]/det]]
    endpoints = []
    row_norms = []
    for i, coefficients in enumerate(c):
        out = (centres[i],)*2
        for k in range(2):
            out = difference(out,mul_range((coefficients[k],)*2,values[k]))
        norm = F(0)
        for j in range(2):
            part = (F(int(i==j)),)*2
            for k in range(2):
                part = difference(part,mul_range((coefficients[k],)*2,jacobian[k][j]))
            norm += hull_abs(part)
            x = (box[2*j]-centres[j],box[2*j+1]-centres[j])
            out = add(out,mul_range(part,x))
        row_norms.append(norm)
        endpoints.extend(out)
    q = max(row_norms)
    inside = all(box[i]<endpoints[i]<=endpoints[i+1]<box[i+1] for i in (0,2))
    return dict(C=[list(map(str,row)) for row in c],K=list(map(str,endpoints)),
                q=str(q),inside=inside,strict=inside and q<1)
