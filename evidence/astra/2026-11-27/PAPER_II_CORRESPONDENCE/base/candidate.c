/* Candidate B, equations (1) and (6) of the frozen derivation.
 * The interval and jet headers adapt Astra's equator arithmetic.
 * One process calls this library serially. */
#include "jets.h"
#include <inttypes.h>
#include <limits.h>
#include <signal.h>
#include <time.h>

enum { MAX_LEAVES = 4096, MAX_PANELS = 2*MAX_LEAVES-16, MAX_DEPTH = 30 };
typedef struct {
    double a[2], b[2];
    unsigned root, depth;
    uint64_t path;
    I value;
    Num priority;
} Cell;

typedef struct {
    I y, z, min_d, max_d, min_b, max_b;
    int quantity, derivative, bits, dim, symmetry_axis;
    unsigned count, calls;
    int measure;
    uint64_t cell_ns[MAX_PANELS];
    Cell *leaves;
} Tree;

typedef struct {
    uint64_t calls;
    unsigned leaves;
    int dim;
    char lo[128], hi[128];
    long lo_exp, hi_exp;
} Result;

static I gl[2];
static int initialized_bits;
static volatile sig_atomic_t *stop_flag;

static void on_stop_signal(int signal_number) {
    (void)signal_number;
    if (stop_flag) *stop_flag = 1;
}

int cb_watch_stop(volatile sig_atomic_t *flag) {
    _Static_assert(sizeof(sig_atomic_t)==sizeof(int),"incompatible shared stop flag");
    stop_flag = flag;
    struct sigaction action = {0};
    action.sa_handler = on_stop_signal;
    if (sigemptyset(&action.sa_mask) != 0 || sigaction(SIGTERM,&action,NULL) != 0 ||
        sigaction(SIGINT,&action,NULL) != 0) return -1;
    return 0;
}

static void init(int bits) {
    precision = bits;
    if (initialized_bits == bits) return;
    tables();
    gl[1] = recip(root(integer(3)));
    gl[0] = neg(gl[1]);
    initialized_bits = bits;
}

static uint64_t nanos(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) fail("CLOCK_MONOTONIC");
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

static int stopped(uint64_t deadline) {
    return (stop_flag && *stop_flag) || (deadline && nanos() >= deadline);
}

static J bounded(J j, I lo, I hi) {
    j.c[0] = meet(j.c[0], (I){lo.lo, hi.hi});
    return j;
}

static J variable(I x, int axis_match, int angular_match) {
    J out = constant(x);
    if (np && axis_match) entry(&out, ix(0,1,0), one);
    if (nv && angular_match) entry(&out, ix(0,0,1), one);
    return out;
}

/* In angle(), the independent variable is phi/pi. Here phi/pi = w/2. */
static J azimuth(I w, int cosine, int derivative) {
    I half = dyadic(.5);
    J j = angle(times(w, half), cosine, derivative);
    if (derivative) {
        I power = half;
        for (int k = 1; k <= nv; ++k) {
            int row = ix(0,0,k);
            j.c[row] = times(j.c[row], power);
            power = times(power, half);
        }
    }
    return j;
}

static J sum3(J a, J b, J c) {
    return jplus(jplus(a,b),c);
}

static I integrand(const Tree *tree, I u, I w, int angular) {
    layout(0, tree->derivative != 0, angular < 0 ? 0 : 4);
    int i = tree->quantity % 2 == 0 ? 1 : 0;
    int m = (i + 1) % 3, n = (i + 2) % 3;
    J yy = variable(tree->y, tree->derivative == 1, 0);
    J zz = variable(tree->z, tree->derivative == 2, 0);
    J lengths[3] = {constant(one), yy, zz};
    J squares[3] = {constant(one), jsq(yy), jsq(zz)};
    J inverse[3] = {constant(one), invroot(squares[1],0), invroot(squares[2],0)};
    J a = variable(u, 0, angular == 0), a2 = jsq(a);
    J rest = jsub(constant(one), a2);
    J f;
    if (tree->quantity < 2) {
        J s[3];
        if (tree->dim == 1) {
            int j = tree->symmetry_axis;
            s[j] = a2;
            s[(j+1)%3] = s[(j+2)%3] = jscale(rest, dyadic(.5));
        } else {
            s[i] = a2;
            s[m] = jmul(rest, jsq(azimuth(w,1,angular == 1)));
            s[n] = jmul(rest, jsq(azimuth(w,0,angular == 1)));
        }
        J d = sum3(s[0], jmul(s[1],squares[1]), jmul(s[2],squares[2]));
        d = bounded(d, tree->min_d, tree->max_d);
        /* Equation (3) gives a dependency-free floor for dB. */
        J db = constant(one);
        for (int j = 0; j < 3; ++j) for (int k = j+1; k < 3; ++k) {
            J difference = jsub(jdiv(lengths[j], lengths[k]), jdiv(lengths[k], lengths[j]));
            db = jplus(db, jmul(jmul(s[j],s[k]), jsq(difference)));
        }
        db.c[0].lo = max2(db.c[0].lo, one.lo);
        J gamma = invroot(invroot(db,1),0);
        J ratio = jdiv(squares[i],d), ratio2 = jsq(ratio);
        J quadratic = sum3(jscale(ratio2,integer(3)), jscale(ratio,integer(-4)),
                           constant(integer(2)));
        J first = jmul(jmul(jsq(gamma), fun_deriv(gamma,2)),
                       jmul(s[i],jsq(jsub(ratio,constant(one)))));
        J second = jmul(jmul(gamma,fun_deriv(gamma,1)),
                        jsub(jmul(s[i],quadratic),ratio));
        f = jplus(first,second);
    } else {
        J mu = jsub(constant(one), jscale(a2,integer(2)));
        J transverse_d, transverse_b;
        if (tree->dim == 1) {
            transverse_d = squares[m];
            transverse_b = inverse[m];
        } else {
            J c2 = jsq(azimuth(w,1,angular == 1));
            J s2 = jsq(azimuth(w,0,angular == 1));
            transverse_d = jplus(jmul(squares[m],c2),jmul(squares[n],s2));
            transverse_b = jplus(jmul(inverse[m],c2),jmul(inverse[n],s2));
        }
        J d = jplus(jmul(rest,transverse_d),jmul(a2,squares[i]));
        J b = jplus(jmul(jsq(mu),inverse[i]),
                   jscale(jmul(jmul(a2,rest),transverse_b),integer(4)));
        d = bounded(d, tree->min_d, tree->max_d);
        b = bounded(b, tree->min_b, tree->max_b);
        J gamma = jdiv(a,invroot(jmul(d,b),1));
        J gamma_fp = jmul(gamma,fun_deriv(gamma,1));
        J first = jmul(mu,jplus(fun_deriv(gamma,0), gamma_fp));
        J second = jmul(jdiv(jmul(squares[i],a2),d),gamma_fp);
        f = jscale(jmul(a,jneg(jplus(first,second))),integer(2));
    }
    return times(at(&f,ix(0,np,nv)),fact[nv]);
}

static I span(double a, double b) {
    return (I){dyadic(a).lo,dyadic(b).hi};
}

static I node(double a, double b, unsigned k) {
    I lo = dyadic(a), hi = dyadic(b), half = dyadic(.5);
    return plus(times(plus(lo,hi),half), times(times(minus(hi,lo),half),gl[k]));
}

static void evaluate(Tree *tree, Cell *cell) {
    uint64_t start = tree->measure ? nanos() : 0;
    I u = span(cell->a[0],cell->b[0]), w = span(cell->a[1],cell->b[1]);
    I du = minus(dyadic(cell->b[0]),dyadic(cell->a[0]));
    I dw = tree->dim == 2 ? minus(dyadic(cell->b[1]),dyadic(cell->a[1])) : one;
    I area = times(du,dw);
    I natural = times(area,integrand(tree,u,w,-1));
    I error = times(square(square(du)),integrand(tree,u,w,0));
    if (tree->dim == 2)
        error = plus(error,times(square(square(dw)),integrand(tree,u,w,1)));
    I sum = iz;
    for (unsigned i = 0; i < 2; ++i)
        for (unsigned j = 0; j < (tree->dim == 2 ? 2U : 1U); ++j)
            sum = plus(sum,integrand(tree,node(cell->a[0],cell->b[0],i),
                                    tree->dim == 2 ? node(cell->a[1],cell->b[1],j) : w,-1));
    I gauss = times(times(area,dyadic(tree->dim == 2 ? .25 : .5)),sum);
    I remainder = quotient(times(area,error),integer(4320));
    cell->value = meet(natural,plus(gauss,remainder));
    cell->priority = width(cell->value);
    if (tree->calls >= MAX_PANELS) fail("cell evaluation counter overflow");
    if (tree->measure) tree->cell_ns[tree->calls] = nanos()-start;
    ++tree->calls;
}

static int order(const Cell *a, const Cell *b) {
    if (a->root != b->root) return a->root < b->root ? -1 : 1;
    uint64_t pa = a->path << (2*(MAX_DEPTH-a->depth));
    uint64_t pb = b->path << (2*(MAX_DEPTH-b->depth));
    if (pa == pb) return (int)a->depth - (int)b->depth;
    return pa < pb ? -1 : 1;
}

static int pointer_order(const void *a, const void *b) {
    return order(*(const Cell *const *)a,*(const Cell *const *)b);
}

static double middle(double a, double b) {
    double mid = (a+b)*.5;
    I expect = times(plus(dyadic(a),dyadic(b)),dyadic(.5));
    if (!(a < mid && mid < b) || cmp(dyadic(mid).lo,expect.lo) || cmp(dyadic(mid).hi,expect.hi))
        fail("angular midpoint representation exhausted");
    return mid;
}

static int split(Tree *tree, uint64_t deadline) {
    unsigned best = 0;
    for (unsigned j = 1; j < tree->count; ++j) {
        int c = cmp(tree->leaves[j].priority,tree->leaves[best].priority);
        if (c > 0 || (c == 0 && order(&tree->leaves[j],&tree->leaves[best]) < 0)) best = j;
    }
    Cell parent = tree->leaves[best], children[4];
    if (parent.depth == MAX_DEPTH) fail("angular path representation exhausted");
    double a[3] = {parent.a[0],middle(parent.a[0],parent.b[0]),parent.b[0]};
    double w[3] = {parent.a[1],0,parent.b[1]};
    if (tree->dim == 2) w[1] = middle(w[0],w[2]);
    unsigned n = tree->dim == 1 ? 2 : 4;
    for (unsigned k = 0; k < n; ++k) {
        unsigned i = tree->dim == 2 ? k/2 : k, j = k%2;
        children[k] = (Cell){.a={a[i],tree->dim == 2 ? w[j] : 0},
                             .b={a[i+1],tree->dim == 2 ? w[j+1] : 0},
                             .root=parent.root,.depth=parent.depth+1,.path=4*parent.path+k};
        if (stopped(deadline)) return 1;
        evaluate(tree,&children[k]);
    }
    tree->leaves[best] = children[0];
    for (unsigned k = 1; k < n; ++k) tree->leaves[tree->count++] = children[k];
    return 0;
}

static int exact_box(const char **args, int *y_one, int *z_one) {
    mpq_t q[4];
    int valid = 1;
    for (int j = 0; j < 4; ++j) {
        mpq_init(q[j]);
        if (!args[j] || mpq_set_str(q[j],args[j],10) != 0 || !mpz_sgn(mpq_denref(q[j]))) {
            valid = 0;
        } else {
            mpq_canonicalize(q[j]);
        }
    }
    if (valid) {
        valid = mpq_cmp_ui(q[0],1,4) >= 0 && mpq_cmp(q[0],q[1]) <= 0
             && mpq_cmp_ui(q[1],1,1) <= 0 && mpq_cmp_ui(q[2],1,1) >= 0
             && mpq_cmp(q[2],q[3]) <= 0 && mpq_cmp_ui(q[3],7,1) <= 0;
        *y_one = mpq_cmp_ui(q[0],1,1) == 0 && mpq_cmp_ui(q[1],1,1) == 0;
        *z_one = mpq_cmp_ui(q[2],1,1) == 0 && mpq_cmp_ui(q[3],1,1) == 0;
    }
    for (int j = 0; j < 4; ++j) mpq_clear(q[j]);
    return valid;
}

const char *cb_error(void) { return error_text; }
const char *cb_mpfr(void) { return mpfr_get_version(); }
const char *cb_gmp(void) { return gmp_version; }

Tree *cb_create(int quantity, int derivative, int bits, int measure,
                const char *y0, const char *y1, const char *z0, const char *z1) {
    if (setjmp(error_jump)) return NULL;
    int y_one = 0, z_one = 0;
    const char *args[] = {y0,y1,z0,z1};
    if (quantity < 0 || quantity > 3 || derivative < 0 || derivative > 2 ||
        (bits != 128 && bits != 256) || !exact_box(args,&y_one,&z_one))
        fail("invalid candidate B shape, quantity or precision");
    init(bits);
    I y = {valueq(y0).lo,valueq(y1).hi}, z = {valueq(z0).lo,valueq(z1).hi};
    I min_d = square(pt(y.lo)), max_d = square(pt(z.hi));
    I min_b = recip(max_d), max_b = recip(min_d);
    int symmetry = -1;
    if (quantity < 2 && y_one && derivative != 1) symmetry = 2;
    if ((quantity < 2 || quantity == 2) && z_one && derivative != 2) symmetry = 1;
    Tree *tree = calloc(1,sizeof *tree);
    if (!tree) fail("allocating angle tree");
    tree->leaves = calloc(MAX_LEAVES,sizeof *tree->leaves);
    if (!tree->leaves) { free(tree); fail("allocating angle leaves"); }
    tree->y=y; tree->z=z; tree->min_d=min_d; tree->max_d=max_d;
    tree->min_b=min_b; tree->max_b=max_b; tree->quantity=quantity; tree->derivative=derivative;
    tree->bits=bits; tree->dim=symmetry < 0 ? 2 : 1; tree->symmetry_axis=symmetry;
    tree->measure=measure;
    return tree;
}

void cb_destroy(Tree *tree) { if (tree) { free(tree->leaves); free(tree); } }
uint64_t cb_cell_ns(const Tree *tree, unsigned index) {
    return index < tree->calls ? tree->cell_ns[index] : 0;
}

/* Longjmp is confined to this API call. A failed tree is discarded by the caller.
 * A split starts only when the full replacement fits in the panel budget. */
int cb_extend(Tree *tree, unsigned target, uint64_t allowance, uint64_t deadline, Result *out) {
    if (setjmp(error_jump)) { out->calls=tree->calls; return -1; }
    init(tree->bits);
    unsigned growth = tree->dim == 1 ? 1 : 3;
    if (target < 16 || target > MAX_LEAVES || (target-16)%growth || target < tree->count)
        fail("invalid or decreasing angular stage");
    uint64_t initial = tree->calls;
    while (tree->count < target) {
        if (stopped(deadline)) goto interrupted;
        if (tree->count < 16) {
            if (tree->calls-initial >= allowance) goto interrupted;
            unsigned k = tree->count;
            unsigned i = tree->dim == 1 ? k : k/4, j = k%4;
            Cell *c = tree->leaves+k;
            double step = tree->dim == 1 ? .0625 : .25;
            c->a[0]=i*step; c->b[0]=(i+1)*step;
            c->a[1]=tree->dim == 2 ? j*.25 : 0;
            c->b[1]=tree->dim == 2 ? (j+1)*.25 : 0;
            c->root=k; evaluate(tree,c); ++tree->count;
        } else {
            if (allowance-(tree->calls-initial) < growth+1) goto interrupted;
            if (split(tree,deadline)) goto interrupted;
        }
    }
    const Cell *sorted[MAX_LEAVES];
    for (unsigned k = 0; k < tree->count; ++k) sorted[k] = tree->leaves+k;
    qsort(sorted,tree->count,sizeof *sorted,pointer_order);
    I sum = iz;
    for (unsigned k = 0; k < tree->count; ++k) sum = plus(sum,sorted[k]->value);
    encode(sum.lo,out->lo,&out->lo_exp);
    encode(sum.hi,out->hi,&out->hi_exp);
    out->calls=tree->calls; out->leaves=tree->count; out->dim=tree->dim;
    return 0;
interrupted:
    out->calls=tree->calls; out->leaves=tree->count; out->dim=tree->dim;
    return 1;
}

int cb_sphere_reference(char *lo, long *lo_exp, char *hi, long *hi_exp) {
    if (setjmp(error_jump)) return -1;
    init(128);
    I exact = quotient(square(pii),integer(32));
    encode(exact.lo,lo,lo_exp);
    encode(exact.hi,hi,hi_exp);
    return 0;
}
