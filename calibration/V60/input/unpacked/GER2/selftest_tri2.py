import sys, time
sys.path.insert(0, '.'); sys.path.insert(0, '../v57')
from fractions import Fraction as Fr
from geoenclosereader import tri2
import chat_v57_numeric_lib as num
bad = 0
def chk(name, enc, val):
    global bad; ok = enc.lo <= val <= enc.hi; bad += not ok
    print(f"{'OK ' if ok else 'BAD'} {name}: [{float(enc.lo):.12g}, {float(enc.hi):.12g}] width {float(enc.hi-enc.lo):.2e}  ref {val:.12g}", flush=True)
GO = num.octant(384); GP = num.polegrid(384, 384)
for N in (32, 64):
    for (s, t) in ((1, 1), (1.566968518621, 2.296585954219), (3.2, 6)):
        S, T = Fr(s), Fr(t); t0 = time.time()
        for i in (1, 2, 3): chk(f"N={N} h{i}({s},{t})", tri2.centre_h(i, S, S, T, T, N), num.hi(i, s, t, GO))
        for i in (1, 2, 3): chk(f"N={N} b{i}({s},{t})", tri2.pole_b(i, S, S, T, T, N), num.bi(i, s, t, GP))
        print("   time", round(time.time() - t0, 2), flush=True)
    for (t, r) in ((4.3, 0.38), (2.5, 0.9)): chk(f"N={N} tau({t},{r})", tri2.disk_tau(Fr(t), Fr(t), Fr(r), Fr(r), N), num.tau(t, r))
# a box: contains the point values at its corners and centre
b = (Fr(3), Fr(3) + Fr(1, 64), Fr(5), Fr(5) + Fr(1, 32))
enc = tri2.centre_h(1, *b, N=64)
for (s, t) in ((3, 5), (3 + 1/64, 5 + 1/32), (3 + 1/128, 5 + 1/64)): chk(f"box h1 contains ({s},{t})", enc, num.hi(1, s, t, GO))
print("FAILURES", bad)
