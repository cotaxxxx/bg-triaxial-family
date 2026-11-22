"""_tape.py -- record the interval operations of the unchanged Reader 0.6.0 integrands and replay them in C.

How it works
  * `install()` replaces `tri4._make` and `tri3._make` by wrappers.  A wrapper, when called with the usual
    I / D / J arguments on a grid, looks up (or records) a *tape* for the call signature and runs it in
    `libtape.so` (tape_kernel.c), cell block by cell block.
  * Recording runs the ORIGINAL Python function once on symbolic intervals (class TI, a subclass of fiv.I).
    Each fiv.I operation (+, -, *, /, neg, sq, sqrt, clip and the three direct constructions the integrands
    use) appends one instruction.  The order of operations, the conversion of Python numbers, the None slots
    of the jets and the exact-zero arrays are therefore whatever the original code does: nothing is rewritten.
  * Whole-array conditions of fiv.py (division by an interval containing 0, sqrt of a negative) are evaluated
    over all cells by the kernel; the wrapper raises the same exception for the first instruction, in program
    order, that fails -- the point where fiv.py would have raised.
  * Anything not recognised while recording (an unexpected numpy call, a data-dependent branch) aborts the
    recording, and the call falls back to the original Python function.  Fallbacks are counted in `stats`.
Claude Code, 2026-11-22.  DIAGNOSTIC_ONLY."""
import ctypes as ct
from pathlib import Path
import numpy as np
from . import fiv, dual, jet, tri, tri2, tri3, tri4
from .fiv import I as RI
from .dual import D
from .jet import J

_lib = ct.CDLL(str(Path(__file__).resolve().with_name("libtape.so")))
if not _lib.tape_nearest_mode(): raise RuntimeError("binary64 round-to-nearest required")
OP = dict(ADD=0, SUB=1, NEG=2, MUL=3, DIV=4, SQ=5, SQRT=6, CLIP=7, TAILHI=8, MSEL=9, ZERO=10)
K_IN, K_CONST, K_TMP, K_OUT = 0, 1, 2, 3
stats = dict(tape_calls=0, fallback_calls=0, recorded=0, unsupported={})
enabled = True


class Unsupported(Exception):
    pass


class _Rec:
    """one recording: nodes are ('in', k) | ('const', k) | ('op', k)"""
    def __init__(self):
        self.instr = []          # (opcode, a, b, p1, p2, aux)
        self.full = []           # per node: does it have the grid shape (True) or is it 0-d (False)
        self.kind = []           # per node: 'in' | 'const' | 'op'
        self.payload = []        # in: input index; const: (lo, hi); op: instruction index
        self.masks = []

    def node(self, kind, payload, full):
        self.kind.append(kind); self.payload.append(payload); self.full.append(bool(full)); return len(self.kind) - 1

    def const(self, lo, hi):
        return self.node("const", (float(lo), float(hi)), False)

    def emit(self, opname, a, b=None, p1=0.0, p2=0.0, aux=0, full=None):
        f = (self.full[a] or (b is not None and self.full[b])) if full is None else full
        self.instr.append((OP[opname], a, -1 if b is None else b, float(p1), float(p2), int(aux)))
        return self.node("op", len(self.instr) - 1, f)


_rec = None                      # the active recording


class _TF:
    """one endpoint array of a symbolic interval; only the numpy calls the integrands make are understood"""
    __slots__ = ("n", "end")
    def __init__(self, n, end): self.n = n; self.end = end
    def __array_function__(self, func, types, args, kwargs):
        if func is np.zeros_like and len(args) == 1 and not kwargs: return _TFZero(self.n)
        if func is np.where and len(args) == 3 and args[1] is self and isinstance(args[2], float) and isinstance(args[0], np.ndarray):
            return _TFSel(args[0], self, args[2])
        raise Unsupported("numpy." + getattr(func, "__name__", "?"))
    def __array_ufunc__(self, *a, **k): raise Unsupported("ufunc on endpoint")
    def __array__(self, *a, **k): raise Unsupported("endpoint converted to an array")
    def __bool__(self): raise Unsupported("truth value of an endpoint")
    def _no(self, *a, **k): raise Unsupported("arithmetic on an endpoint")
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __neg__ = _no
    __lt__ = __le__ = __gt__ = __ge__ = __eq__ = __ne__ = _no
    __hash__ = None


class _TFZero:
    __slots__ = ("like",)
    def __init__(self, like): self.like = like


class _TFSel:
    __slots__ = ("mask", "src", "val")
    def __init__(self, mask, src, val): self.mask = mask; self.src = src; self.val = val


class TI(RI):
    """symbolic interval: a node of the active recording"""
    __slots__ = ("n",)

    def __init__(self, lo, hi=None):
        r = _rec
        if isinstance(lo, _TFZero) and hi is None:                       # I(np.zeros_like(x.lo))
            self.n = r.emit("ZERO", lo.like)
        elif isinstance(lo, _TFZero) and isinstance(hi, _TF) and hi.end == "hi":     # tri._tail
            if r.full[lo.like] != r.full[hi.n]: raise Unsupported("tail shapes")
            self.n = r.emit("TAILHI", hi.n)
        elif isinstance(lo, _TFSel) and isinstance(hi, _TFSel) and lo.mask is hi.mask and lo.src.n == hi.src.n \
                and lo.src.end == "lo" and hi.src.end == "hi" and lo.val == hi.val:   # tri3 contact masking
            for k, m in enumerate(r.masks):
                if m is lo.mask: break
            else:
                r.masks.append(lo.mask); k = len(r.masks) - 1
            self.n = r.emit("MSEL", lo.src.n, p1=lo.val, aux=k, full=True)
        else:
            a = np.asarray(lo, dtype=np.float64); b = a if hi is None else np.asarray(hi, dtype=np.float64)
            if a.size != 1 or b.size != 1: raise Unsupported("array constant inside the integrand")
            self.n = r.const(a.reshape(()), b.reshape(()))

    @classmethod
    def _of(cls, n):
        o = object.__new__(cls); o.n = n; return o

    lo = property(lambda self: _TF(self.n, "lo"))
    hi = property(lambda self: _TF(self.n, "hi"))

    @staticmethod
    def c(x):
        if isinstance(x, TI): return x
        if isinstance(x, RI):
            if x.lo.size != 1 or x.hi.size != 1: raise Unsupported("concrete array interval inside the integrand")
            return TI._of(_rec.const(x.lo.reshape(()), x.hi.reshape(())))
        if isinstance(x, (int, float, np.floating, np.integer)) and not isinstance(x, bool):
            v = np.asarray(x, dtype=np.float64); return TI._of(_rec.const(v, v))
        raise Unsupported("operand of type " + type(x).__name__)

    def __add__(a, b): return TI._of(_rec.emit("ADD", a.n, TI.c(b).n))
    __radd__ = __add__
    def __neg__(a): return TI._of(_rec.emit("NEG", a.n))
    def __sub__(a, b): return TI._of(_rec.emit("SUB", a.n, TI.c(b).n))
    def __rsub__(a, b): return TI._of(_rec.emit("SUB", TI.c(b).n, a.n))
    def __mul__(a, b): return TI._of(_rec.emit("MUL", a.n, TI.c(b).n))
    __rmul__ = __mul__
    def __truediv__(a, b): return TI._of(_rec.emit("DIV", a.n, TI.c(b).n))
    def __rtruediv__(a, b): return TI._of(_rec.emit("DIV", TI.c(b).n, a.n))
    def sq(a): return TI._of(_rec.emit("SQ", a.n))
    def sqrt(a): return TI._of(_rec.emit("SQRT", a.n))
    def clip(a, lo, hi): return TI._of(_rec.emit("CLIP", a.n, p1=lo, p2=hi))
    def hull(a, b): raise Unsupported("hull")
    def fsum(a): raise Unsupported("fsum")
    @staticmethod
    def where(mask, a, b): raise Unsupported("I.where")
    def __repr__(self): return "TI(%d)" % self.n


_PATCH = (dual, jet, tri, tri2, tri3, tri4)


def _leaves(obj, out):
    """template of an I / D / J object; real intervals are appended to `out`"""
    if obj is None: return None
    if isinstance(obj, RI): out.append(obj); return ("I", len(out) - 1)
    if isinstance(obj, D): return ("D", _leaves(obj.v, out), [_leaves(x, out) for x in obj.g])
    if isinstance(obj, J): return ("J", _leaves(obj.v, out), [_leaves(x, out) for x in obj.g],
                                   [(p, _leaves(obj.h[p], out)) for p in obj.pairs], tuple(obj.pairs))
    raise Unsupported("argument of type " + type(obj).__name__)


def _build(t, mk):
    if t is None: return None
    if t[0] == "I": return mk(t[1])
    if t[0] == "D": return D(_build(t[1], mk), [_build(x, mk) for x in t[2]])
    return J(_build(t[1], mk), [_build(x, mk) for x in t[2]], {p: _build(x, mk) for p, x in t[3]}, list(t[4]))


def _key(t):
    if t is None or t[0] == "I": return t
    if t[0] == "D": return ("D", _key(t[1]), tuple(_key(x) for x in t[2]))
    return ("J", _key(t[1]), tuple(_key(x) for x in t[2]), tuple((p, _key(x)) for p, x in t[3]), t[4])


class _Prog:
    pass


def _compile(rec, out_nodes):
    """liveness, slot allocation, and the C arrays of one recording"""
    n = len(rec.instr); node_of_instr = [None]*n
    for nd, (k, p) in enumerate(zip(rec.kind, rec.payload)):
        if k == "op": node_of_instr[p] = nd
    out_index = {}
    for nd in out_nodes:
        if rec.kind[nd] == "op" and nd not in out_index: out_index[nd] = len(out_index)
    last = {}
    for i, (_, a, b, _, _, _) in enumerate(rec.instr):
        for x in (a, b):
            if x >= 0 and rec.kind[x] == "op": last[x] = i
    consts = [rec.payload[nd] for nd in range(len(rec.kind)) if rec.kind[nd] == "const"]
    cidx = {}; k = 0
    for nd in range(len(rec.kind)):
        if rec.kind[nd] == "const": cidx[nd] = k; k += 1
    free = []; nslot = 0; slot = {}
    op = np.empty(n, np.int32); ra = np.empty(n, np.uint32); rb = np.zeros(n, np.uint32); rd = np.empty(n, np.uint32)
    p1 = np.empty(n); p2 = np.empty(n); aux = np.empty(n, np.int32)

    def ref(x):
        kd = rec.kind[x]
        if kd == "in": return (K_IN << 30) | rec.payload[x]
        if kd == "const": return (K_CONST << 30) | cidx[x]
        if x in out_index: return (K_OUT << 30) | out_index[x]
        return (K_TMP << 30) | slot[x]
    for i, (o, a, b, q1, q2, ax) in enumerate(rec.instr):
        nd = node_of_instr[i]
        op[i] = o; p1[i] = q1; p2[i] = q2; aux[i] = ax; ra[i] = ref(a)
        if b >= 0: rb[i] = ref(b)
        if nd in out_index: rd[i] = (K_OUT << 30) | out_index[nd]
        else:
            if free: s = free.pop()
            else: s = nslot; nslot += 1
            slot[nd] = s; rd[i] = (K_TMP << 30) | s
        for x in {a, b}:                                   # release operands after the destination is placed
            if x >= 0 and rec.kind[x] == "op" and x not in out_index and last.get(x) == i: free.append(slot[x])
        if nd not in out_index and nd not in last: free.append(slot[nd])        # never read (dead value)
    P = _Prog(); P.n = n; P.op, P.ra, P.rb, P.rd, P.p1, P.p2, P.aux = op, ra, rb, rd, p1, p2, aux
    P.c_lo = np.array([c[0] for c in consts] or [0.0]); P.c_hi = np.array([c[1] for c in consts] or [0.0]); P.nconst = len(consts)
    P.nslot = nslot; P.out_index = out_index; P.rec = rec; P.nmask = len(rec.masks)
    P.div_or_sqrt = [(i, o) for i, (o, *_r) in enumerate(rec.instr) if o in (OP["DIV"], OP["SQRT"])]
    return P


_cache = {}
_dp = ct.POINTER(ct.c_double); _u8p = ct.POINTER(ct.c_uint8)


def _wrap(module, name):
    original = getattr(module, name)

    def make(kind, *margs, **mkw):
        safe_mask = mkw.get("safe_mask", margs[0] if margs else None) if module is tri3 else None
        f_orig = original(kind, *margs, **mkw)

        def f(*args):
            if not enabled: return f_orig(*args)
            try:
                leaves = []; templ = [_leaves(a, leaves) for a in args]
                shapes = {x.lo.shape for x in leaves if x.lo.size != 1}
                if len(shapes) != 1 or any(x.lo.shape != x.hi.shape for x in leaves): raise Unsupported("argument shapes")
                shape = shapes.pop()
                # distinct input intervals (the same arrays may occupy several slots, e.g. the zero gradient)
                ids = {}; uniq = []; which = []
                for x in leaves:
                    kk = (id(x.lo), id(x.hi))
                    if kk not in ids: ids[kk] = len(uniq); uniq.append(x)
                    which.append(ids[kk])
                fullflag = tuple(x.lo.size != 1 for x in uniq)
                key = (module.__name__, name, kind, safe_mask is not None, tuple(_key(t) for t in templ), tuple(which), fullflag)
                P = _cache.get(key)
                if P is None:
                    P = _record(f_orig, templ, which, fullflag, safe_mask); _cache[key] = P; stats["recorded"] += 1
                if isinstance(P, Unsupported): raise P
            except Unsupported as e:
                stats["fallback_calls"] += 1; stats["unsupported"][str(e)] = stats["unsupported"].get(str(e), 0) + 1
                return f_orig(*args)
            stats["tape_calls"] += 1
            return _run(P, uniq, shape, safe_mask)
        return f
    setattr(module, name, make)


def _record(f_orig, templ, which, fullflag, safe_mask):
    global _rec
    rec = _Rec(); _rec = rec
    saved = [m.I for m in _PATCH]
    try:
        innodes = [rec.node("in", k, fl) for k, fl in enumerate(fullflag)]
        sym = [_build(t, lambda j: TI._of(innodes[which[j]])) for t in templ]
        for m in _PATCH: m.I = TI
        try:
            res = f_orig(*sym)
        except Unsupported as e:
            return e
        outs = []; otempl = _leaves_sym(res, outs)
        if any(m is not safe_mask for m in rec.masks): return Unsupported("unknown mask")
        P = _compile(rec, outs); P.otempl = otempl; P.outs = outs
        rec.masks = [None]*len(rec.masks)           # do not keep the recording-time mask array alive
        return P
    finally:
        for m, s in zip(_PATCH, saved): m.I = s
        _rec = None


def _leaves_sym(obj, out):
    if obj is None: return None
    if isinstance(obj, TI): out.append(obj.n); return ("I", len(out) - 1)
    if isinstance(obj, RI): raise Unsupported("concrete interval returned")
    if isinstance(obj, D): return ("D", _leaves_sym(obj.v, out), [_leaves_sym(x, out) for x in obj.g])
    if isinstance(obj, J): return ("J", _leaves_sym(obj.v, out), [_leaves_sym(x, out) for x in obj.g],
                                   [(p, _leaves_sym(obj.h[p], out)) for p in obj.pairs], tuple(obj.pairs))
    raise Unsupported("result of type " + type(obj).__name__)


def _run(P, uniq, shape, safe_mask):
    rec = P.rec; ncell = int(np.prod(shape)); nin = len(uniq)
    keep = []
    def arr(a):
        a = np.ascontiguousarray(a, dtype=np.float64); keep.append(a); return a.ctypes.data_as(_dp)
    in_lo = (_dp*max(nin, 1))(*[arr(x.lo) for x in uniq]); in_hi = (_dp*max(nin, 1))(*[arr(x.hi) for x in uniq])
    in_full = np.array([x.lo.size != 1 for x in uniq] or [0], np.uint8)
    nout = len(P.out_index)
    olo = [np.empty(shape) for _ in range(nout)]; ohi = [np.empty(shape) for _ in range(nout)]
    out_lo = (_dp*max(nout, 1))(*[a.ctypes.data_as(_dp) for a in olo]); out_hi = (_dp*max(nout, 1))(*[a.ctypes.data_as(_dp) for a in ohi])
    masks = []
    for _ in range(P.nmask):                       # the only mask a recording may use is the caller's safe_mask
        m = safe_mask
        mm = np.ascontiguousarray(np.broadcast_to(m, shape), dtype=np.uint8); keep.append(mm); masks.append(mm.ctypes.data_as(_u8p))
    mk = (_u8p*max(len(masks), 1))(*masks)
    fp = np.empty(P.n, np.uint8); fn = np.empty(P.n, np.uint8); fs = np.empty(P.n, np.uint8)
    st = _lib.tape_run(ct.c_size_t(ncell), P.n, P.op.ctypes.data_as(ct.c_void_p), P.ra.ctypes.data_as(ct.c_void_p), P.rb.ctypes.data_as(ct.c_void_p),
                       P.rd.ctypes.data_as(ct.c_void_p), P.p1.ctypes.data_as(ct.c_void_p), P.p2.ctypes.data_as(ct.c_void_p), P.aux.ctypes.data_as(ct.c_void_p),
                       nin, in_lo, in_hi, in_full.ctypes.data_as(ct.c_void_p), P.nconst, P.c_lo.ctypes.data_as(ct.c_void_p), P.c_hi.ctypes.data_as(ct.c_void_p),
                       P.nmask, mk, P.nslot, nout, out_lo, out_hi, fp.ctypes.data_as(ct.c_void_p), fn.ctypes.data_as(ct.c_void_p), fs.ctypes.data_as(ct.c_void_p))
    if st: raise RuntimeError("tape_run status %d" % st)
    for i, o in P.div_or_sqrt:                      # the first failing whole-array condition, in program order
        if o == OP["DIV"] and not (fp[i] or fn[i]): raise ValueError("division by interval containing 0")
        if o == OP["SQRT"] and fs[i]: raise ValueError("sqrt of negative")

    def mk_out(j):
        nd = P.outs[j]; kd = rec.kind[nd]
        if kd == "in": return uniq[rec.payload[nd]]
        if kd == "const": lo, hi = rec.payload[nd]; return RI(np.asarray(lo), np.asarray(hi))
        k = P.out_index[nd]
        if rec.full[nd]: return RI(olo[k], ohi[k])
        return RI(np.asarray(olo[k].reshape(-1)[0]), np.asarray(ohi[k].reshape(-1)[0]))
    made = {}
    def once(j):
        nd = P.outs[j]
        if nd not in made: made[nd] = mk_out(j)
        return made[nd]
    res = [None]
    return _build(P.otempl, once)


def install():
    _wrap(tri4, "_make"); _wrap(tri3, "_make")
