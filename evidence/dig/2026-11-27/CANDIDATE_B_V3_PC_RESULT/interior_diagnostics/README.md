# Z1 intersect D2: extraction of v3 run records

DIAGNOSTIC_ONLY. No numerical integration or mathematical adoption. Exact source is RESULT/work/local/proof/intersections.jsonl (v3.local.proof.intersections.3) and integrals.jsonl, with the frozen V3_INPUTS.json and method_v3.py auxiliary(), krawczyk(), interior_setup().

The auxiliary routine returns None at the first failed band's final angular stage. Only piece 1, Z1, was evaluated (256, 1024, 4096; four records per stage). The remaining quantities/pieces, slope difference and endpoint ordering were not evaluated. NOT_EVALUATED is not a negative sign or a failed numerical test. All eight planned piece coordinates are retained. The exact intervals and IDs of actual evaluations are in AUXILIARY_8_PIECES.json. CSV is a readable index.

KRAWCZYK_9_TRIALS.json preserves all nine trials, input box, exact image K and norm q, references and original integral rows; strict inclusion in each coordinate and q<1 are evaluated by exact rational comparisons of stored values. CSV contains exact endpoints and flags. Approximate q is for reading only. Auxiliary support was unavailable; the combined support test was not reached because all strict flags were false. The extraction script does not import the kernel or run the runner. These are record-level checks, not independent mathematical audit.
