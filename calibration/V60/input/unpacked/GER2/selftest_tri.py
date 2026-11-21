"""Self-tests of the 0.3.0 triaxial kernels: series vs mpmath, kernels vs chat's non-interval quadrature."""
import sys, time
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '.')
import numpy as np
from fractions import Fraction as Fr
from mpmath import mp, mpf, acos, asin
from geoenclosereader.fiv import I
from geoenclosereader import tri
sys.path.insert(0, sys.argv[2] if len(sys.argv) > 2 else '../v57')
import chat_v57_numeric_lib as num
mp.dps = 30; bad = 0
def chk(name, enc, val):
    global bad; ok = enc.lo <= val <= enc.hi; bad += not ok
    print(f"{'OK ' if ok else 'BAD'} {name}: [{float(enc.lo):.12g}, {float(enc.hi):.12g}] width {float(enc.hi-enc.lo):.2e}  ref {val:.12g}")
for gv in ("0", "0.05", "0.3", "0.77", "0.999", "1"):
    g = mpf(gv); a = acos(g); P = 2 if g == 1 else 2*a/mp.sqrt(1 - g*g)
    dP = mp.diff(lambda x: 2*acos(x)/mp.sqrt(1 - x*x), g) if g < 1 else mpf(-2)/3
    ddP = mp.diff(lambda x: 2*acos(x)/mp.sqrt(1 - x*x), g, 2) if g < 1 else mpf(8)/15
    o = tri.PQF(I(float(g)), ("P", "Q", "F", "Pgg"))
    chk(f"P({gv})", o["P"], float(P)); chk(f"Q({gv})", o["Q"], float(2*P + g*dP)); chk(f"F({gv})", o["F"], float(a*a))
    chk(f"Pg({gv})", o["Pg"], float(dP)); chk(f"Pgg({gv})", o["Pgg"], float(ddP))
GO = num.octant(384); GP = num.polegrid(384, 384)
for (s, t) in ((1, 1), (1.25, 2.5), (1.566968518621, 2.296585954219), (3.2, 6), (2.4512275558, 1)):
    S, T = Fr(s), Fr(t); t0 = time.time()
    for i in (1, 2, 3):
        chk(f"h{i}({s},{t}) N=128", tri.centre_h(i, S, S, T, T, 128), num.hi(i, s, t, GO))
    for i in (1, 2, 3):
        chk(f"b{i}({s},{t}) N=128", tri.pole_b(i, S, S, T, T, 128, 128), num.bi(i, s, t, GP))
    print("   time", round(time.time() - t0, 2))
for (t, r) in ((4.3, 0.38), (4.4, 0.19), (2.5, 0.9)):
    chk(f"tau({t},{r})", tri.disk_tau(Fr(t), Fr(t), Fr(r), Fr(r), 256, 128), num.tau(t, r))
    chk(f"tau''({t},{r})", tri.disk_tau2(Fr(t), Fr(t), Fr(r), Fr(r), 256, 128), num.tau2(t, r))
print("FAILURES", bad)
