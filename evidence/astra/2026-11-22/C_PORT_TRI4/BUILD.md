# Build and replay

Use x86-64 Linux, CPython 3.12 with development headers, NumPy 2.3.5, mpmath 1.3.0, Cython 3.1.6 and GCC. This run used CPython 3.12.14, GCC 14.2.0 and an AMD EPYC 9V74. Cython upstream tag 3.1.6 was at b40c676a7396e3b8ca25974bd5ca4b5cef7f9908. A local Cython source checkout can be placed on PYTHONPATH for build.py. The supplied inputs are assumed to be available in the repository's Git object database at the commit in PLAN_C_PORT.md.

From this folder:

```sh
bash reproduce.sh /path/to/bg-triaxial-family /path/to/new-run
```

To build just the accelerated Reader and import it:

```sh
python build.py /path/to/V63A_PC_BUNDLE/GER2 /path/to/new-build/GER2
PYTHONPATH=/path/to/new-build/GER2 python -c 'from geoenclosereader import tri4; print(tri4.__file__)'
```

The build checks the original Python sources against reader_hashes.json. It puts a ctypes library and three extension modules into a new Reader copy, and saves all three generated C translation units in its root. Arithmetic lives in kernel.c. Cython translates dual.py, jet.py and the original integrand and _mv_cells function bodies in _cells.py. The original tri4.py, tri3.py, tri2.py, their scalar powers and all enclose.last and intersection code run as Python. The grid and rational endpoints are produced by the original routines. Joins of consecutive 32,768-cell jet blocks copy values into original cell order; no block sums are combined. A negative divisor in a block or an exception triggers an unblocked native evaluation to preserve the original global error order. Kernels on small inputs and ordinary duals are evaluated on whole arrays. PQF coefficient construction and NumPy/ctypes dispatch retain Python dependencies. This is a single-threaded hybrid implementation. An application can import tri4 normally from the build directory.

Explicit compile flags: `-std=c11 -O2 -ffp-contract=off -fno-fast-math -msse2 -mfpmath=sse -fPIC -shared`. Finite nextafter toward infinity is implemented using adjacent binary64 encodings and special values use libm nextafter. The comparison to math.nextafter covers signed zero, subnormals, finite extremes, infinities and seeded bit patterns. Array reductions call the verbatim math_fsum source and supporting macro/reallocator copied from CPython v3.12.14 commit 2abcf904b8dac8c999d2b3aac76681abb333798a, Modules/mathmodule.c (see CPYTHON_LICENSE.txt). ctypes.PyDLL passes a contiguous vector memoryview as an iterator and preserves its exceptions. Reader moves the result one unit outward separately. No cell parallelism is enabled.

The runner exposes both grid policies through its command line. For example, with a new result file per run:

```sh
python run_tree.py /path/to/V63A_PC_BUNDLE /path/to/new-build/GER2 refs/rep.json 0 tree0.jsonl --nmax 256 --nh half
python run_tree.py /path/to/V63A_PC_BUNDLE /path/to/new-build/GER2 refs/rep.json 0 tree0-fine.jsonl --nmax 512 --nh full
```

For B the runner uses the V63-A traversal with the V61 grid limits. Its cache eviction threshold is four grids as in the supplied runner. Its exact decision tree is checked against the V61 archival results. Each invocation runs just the indicated sample. The two unit-less shape coordinates and three reference-ball coordinates in cases*.json are exact rational strings. For A, numeric output strings in outcome are 16 hexadecimal digits in big-endian IEEE binary64 encoding; integer, Boolean and rational-string metadata retain their original types. Compare archived and regenerated outcomes, not elapsed seconds.
