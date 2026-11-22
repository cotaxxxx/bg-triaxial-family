/* Verbatim excerpts from CPython v3.12.14 Modules/mathmodule.c, see CPYTHON_LICENSE.txt. */
#include <Python.h>
#include <math.h>
#include <assert.h>
#include <string.h>
#define ASSIGN_DOUBLE(target_var, obj, error_label)        \
    if (PyFloat_CheckExact(obj)) {                         \
        target_var = PyFloat_AS_DOUBLE(obj);               \
    }                                                      \
    else if (PyLong_CheckExact(obj)) {                     \
        target_var = PyLong_AsDouble(obj);                 \
        if (target_var == -1.0 && PyErr_Occurred()) {      \
            goto error_label;                              \
        }                                                  \
    }                                                      \
    else {                                                 \
        target_var = PyFloat_AsDouble(obj);                \
        if (target_var == -1.0 && PyErr_Occurred()) {      \
            goto error_label;                              \
        }                                                  \
    }

#define NUM_PARTIALS  32  /* initial partials array size, on stack */

/* Extend the partials array p[] by doubling its size. */
static int                          /* non-zero on error */
_fsum_realloc(double **p_ptr, Py_ssize_t  n,
             double  *ps,    Py_ssize_t *m_ptr)
{
    void *v = NULL;
    Py_ssize_t m = *m_ptr;

    m += m;  /* double */
    if (n < m && (size_t)m < ((size_t)PY_SSIZE_T_MAX / sizeof(double))) {
        double *p = *p_ptr;
        if (p == ps) {
            v = PyMem_Malloc(sizeof(double) * m);
            if (v != NULL)
                memcpy(v, ps, sizeof(double) * n);
        }
        else
            v = PyMem_Realloc(p, sizeof(double) * m);
    }
    if (v == NULL) {        /* size overflow or no memory */
        PyErr_SetString(PyExc_MemoryError, "math.fsum partials");
        return 1;
    }
    *p_ptr = (double*) v;
    *m_ptr = m;
    return 0;
}

/* Full precision summation of a sequence of floats.

   def msum(iterable):
       partials = []  # sorted, non-overlapping partial sums
       for x in iterable:
           i = 0
           for y in partials:
               if abs(x) < abs(y):
                   x, y = y, x
               hi = x + y
               lo = y - (hi - x)
               if lo:
                   partials[i] = lo
                   i += 1
               x = hi
           partials[i:] = [x]
       return sum_exact(partials)

   Rounded x+y stored in hi with the roundoff stored in lo.  Together hi+lo
   are exactly equal to x+y.  The inner loop applies hi/lo summation to each
   partial so that the list of partial sums remains exact.

   Sum_exact() adds the partial sums exactly and correctly rounds the final
   result (using the round-half-to-even rule).  The items in partials remain
   non-zero, non-special, non-overlapping and strictly increasing in
   magnitude, but possibly not all having the same sign.

   Depends on IEEE 754 arithmetic guarantees and half-even rounding.
*/

/*[clinic input]
math.fsum

    seq: object
    /

Return an accurate floating-point sum of values in the iterable seq.

Assumes IEEE-754 floating-point arithmetic.
[clinic start generated code]*/

static PyObject *
math_fsum(PyObject *module, PyObject *seq)
/*[clinic end generated code: output=ba5c672b87fe34fc input=4506244ded6057dc]*/
{
    PyObject *item, *iter, *sum = NULL;
    Py_ssize_t i, j, n = 0, m = NUM_PARTIALS;
    double x, y, t, ps[NUM_PARTIALS], *p = ps;
    double xsave, special_sum = 0.0, inf_sum = 0.0;
    double hi, yr, lo = 0.0;

    iter = PyObject_GetIter(seq);
    if (iter == NULL)
        return NULL;

    for(;;) {           /* for x in iterable */
        assert(0 <= n && n <= m);
        assert((m == NUM_PARTIALS && p == ps) ||
               (m >  NUM_PARTIALS && p != NULL));

        item = PyIter_Next(iter);
        if (item == NULL) {
            if (PyErr_Occurred())
                goto _fsum_error;
            break;
        }
        ASSIGN_DOUBLE(x, item, error_with_item);
        Py_DECREF(item);

        xsave = x;
        for (i = j = 0; j < n; j++) {       /* for y in partials */
            y = p[j];
            if (fabs(x) < fabs(y)) {
                t = x; x = y; y = t;
            }
            hi = x + y;
            yr = hi - x;
            lo = y - yr;
            if (lo != 0.0)
                p[i++] = lo;
            x = hi;
        }

        n = i;                              /* ps[i:] = [x] */
        if (x != 0.0) {
            if (! Py_IS_FINITE(x)) {
                /* a nonfinite x could arise either as
                   a result of intermediate overflow, or
                   as a result of a nan or inf in the
                   summands */
                if (Py_IS_FINITE(xsave)) {
                    PyErr_SetString(PyExc_OverflowError,
                          "intermediate overflow in fsum");
                    goto _fsum_error;
                }
                if (Py_IS_INFINITY(xsave))
                    inf_sum += xsave;
                special_sum += xsave;
                /* reset partials */
                n = 0;
            }
            else if (n >= m && _fsum_realloc(&p, n, ps, &m))
                goto _fsum_error;
            else
                p[n++] = x;
        }
    }

    if (special_sum != 0.0) {
        if (Py_IS_NAN(inf_sum))
            PyErr_SetString(PyExc_ValueError,
                            "-inf + inf in fsum");
        else
            sum = PyFloat_FromDouble(special_sum);
        goto _fsum_error;
    }

    hi = 0.0;
    if (n > 0) {
        hi = p[--n];
        /* sum_exact(ps, hi) from the top, stop when the sum becomes
           inexact. */
        while (n > 0) {
            x = hi;
            y = p[--n];
            assert(fabs(y) < fabs(x));
            hi = x + y;
            yr = hi - x;
            lo = y - yr;
            if (lo != 0.0)
                break;
        }
        /* Make half-even rounding work across multiple partials.
           Needed so that sum([1e-16, 1, 1e16]) will round-up the last
           digit to two instead of down to zero (the 1e-16 makes the 1
           slightly closer to two).  With a potential 1 ULP rounding
           error fixed-up, math.fsum() can guarantee commutativity. */
        if (n > 0 && ((lo < 0.0 && p[n-1] < 0.0) ||
                      (lo > 0.0 && p[n-1] > 0.0))) {
            y = lo * 2.0;
            x = hi + y;
            yr = x - hi;
            if (y == yr)
                hi = x;
        }
    }
    sum = PyFloat_FromDouble(hi);

  _fsum_error:
    Py_DECREF(iter);
    if (p != ps)
        PyMem_Free(p);
    return sum;

  error_with_item:
    Py_DECREF(item);
    goto _fsum_error;
}

#undef NUM_PARTIALS
/* ctypes.PyDLL keeps the GIL and propagates Python exceptions. */
int sum_iterable(PyObject *values, double *out) {
    PyObject *result=math_fsum(NULL,values);
    if (!result) return -1;
    *out=PyFloat_AS_DOUBLE(result);
    Py_DECREF(result);
    return 0;
}
