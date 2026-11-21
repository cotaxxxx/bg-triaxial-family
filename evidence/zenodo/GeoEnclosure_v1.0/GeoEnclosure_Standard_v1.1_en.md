# GeoEnclosure Standard v1.1 (English translation)

2026-11-20. Drafted by chat (Claude, auditing AI). Methodology named by the Judge (the author). Revised after the review of v1.0 by Claude Code.

*This is a translation. The Japanese text `GeoEnclosure_Standard_v1.1_ja.md` is authoritative. On the roles (producer, auditor, Judge) and the run labels (V48, V57, …), see `README.md`.*

This standard sets the conditions under which a mathematical claim may be called "verified by interval computation" in the GeoEnclosure method. It was written from experience: it was used in the study of the stationary points of the volume-preserving spheroid and triaxial-ellipsoid families (runs V48–V59), where it caught real errors. The accompanying tool is GeoEncloseReader.

**Main changes from v1.0**
- Terms are separated. CONTRADICTED and INCONSISTENT are distinguished, and terms for the states of boxes and lemmas are added.
- The covering condition is now that the union contains the claimed region. Overlaps are allowed and recorded.
- "Do not choose the method from the values" is made precise. Adaptive refinement is allowed under rules fixed in advance.
- Adoption is split into two levels, each tied to a way of stating the result in a paper.
- New items: tracing back to the definition, a mandatory point check, a margin reserve, claims about roots, a claim–ledger table, the floating-point environment, differentiation at the boundary, publication and human responsibility, minimum sample sizes, and a conformance table.

---

## 0. Principles

A GeoEnclosure claim rests on four steps.

1. **A representation that fits the shape.** Before computing, rewrite the problem in a view where the integrand is bounded. Examples: the chord representation, a chart centred on a pole, the boundary trace.
2. **Enclose, then decide the sign.** Decide the sign of each box with an interval that contains the true value with certainty, rounding included, not with sampled values.
3. **Regenerate from scratch and check independently.** Confirm the same sign with formulas and code different from the producer's. How far this independent check went is stated by the level in §7.
4. **Close with analysis.** Connect the finitely many box results to a conclusion about the whole family by proofs: monotonicity, symmetry, bounds on derivatives.

**Numerical samples, plots and least-squares searches, however many, are diagnostics, not proofs.**

---

## 1. Terms

### 1.1 States of reports and boxes
| Term | Meaning |
|---|---|
| DIAGNOSTIC_ONLY / NOT_EVIDENCE | The default status of every report. It does not change until the Judge adopts the result |
| CONFIRMED | The audit verified, by intervals, the claimed sign on the whole box |
| NOT_REPRODUCED | The sign did not come out within the audit budget. **Not a counterexample** |
| CONTRADICTED | The audit interval lies entirely on the sign opposite to the claim. **A sign counterexample**; report it at once |
| INCONSISTENT | For the same quantity, the producer's interval and the audit interval do not meet. **One of the enclosures or formulas is wrong**; this is not necessarily a sign counterexample. Hold the whole ledger until the cause is found |
| EMPTY | The box does not meet the claimed region (e.g. it lies outside the closed ball). Record that it was discarded |
| OPEN | A box the producer left undecided. It does not support the claim. Count it as unfinished |

### 1.2 States of lemmas
| Term | Meaning |
|---|---|
| STATED | Only written down by the producer |
| HAND_CHECKED | The auditor followed the derivation by hand and recomputed the constants numerically |
| REDERIVED | The auditor derived it again independently (same conclusion, or constants on the safe side) |
| GAP | The derivation has a hole. State where the hole is |

### 1.3 Decision
Only the Judge decides "adoption". The levels are given in §7.

---

## 2. Computational standard (conditions for an enclosure to be correct)

### 2.1 Rounding and the floating-point environment
Build intervals that are certain to contain the true value, by one of the following methods. State in the report which method was used.
- **(a) Ball arithmetic:** balls from a library whose correctness is guaranteed, such as Arb.
- **(b) Round-to-nearest plus outward correction:** move the result of every operation one ulp outward. This correction also covers subnormal values.
- **(c) Directed rounding:** compute with the rounding mode fixed upward (or downward). Allowed only when all three of the following hold.
  - A test confirms that the mode is actually in effect at run time.
  - The lower and upper end of every operation are computed in the corresponding direction.
  - It has been confirmed that library functions do not ignore or reset the mode.

**Conditions on the environment (common to all three methods)**
- Forbid automatic contraction into fused multiply-add (e.g. `-ffp-contract=off`).
- Do not use x87 extended precision (compute in binary64, e.g. SSE2).
- Forbid `-ffast-math` and similar flags. Record the compiler, its version and the flags.
- Decimal literals and reading from strings cause rounding. Build constants by outward rounding from rationals, or include the error in the interval.
- Do not evaluate trigonometric functions, π or series coefficients at interval endpoints with an unguaranteed library. Round outward from high-precision values or exact rationals.
- Enclose sums of many terms including their rounding error.
- Compute from endpoints. Do not produce values below 0 or NaN from the square or the intersection of a wide interval.

### 2.2 Quadrature remainders
Enclose the remainder explicitly, by one of the following.
- **Range enclosure (first order):** the range of the integrand on the cell times the measure of the cell.
- **Mean-value form (second order):** the value at the cell centre times the measure, the midpoint of the gradient times the first moment, and the radius of the gradient times the moment of |x − x_c|.
- **Analytic remainder:** for spectral approximation and the like, prove an upper bound on the remainder and add it. That proof is subject to the hand check in §5.

**Never use a numerical quadrature value as an interval without a remainder.** Never use a truncated Taylor expansion as an exact formula (correction E2 of V51).

### 2.3 Singularities, contact, and derivatives at the boundary
- **Unbounded integrands:** multiply an a-priori bound by the measure of the cell. Write the derivation of the bound in the kernel's documentation. Do not assign arbitrary point values.
- **Differentiation under the integral sign:** justify it, e.g. by dominated convergence. Show that the derivative of the integrand is uniformly bounded by an integrable function.
- **Boundary traces:** show that the extension from the inside is continuous (e.g. the integral over a cap around the contact point is uniformly O(η)). Then define the boundary value as the inner trace. Do not assume that second derivatives exist at the boundary (the arguments of V51 and V54).

### 2.4 Valid ranges
- Clip an interval only to a range known to contain the true value (e.g. γ ∈ [0, 1]). State the reason.
- When a box extends beyond the domain, state the claimed region explicitly (e.g. the intersection of the box with the closed ball). Also show that the mean-value segments stay inside that region.

### 2.5 Series
Use series of positive terms and enclose the tail by an explicit upper bound. State the bound on the ratio of terms.

---

## 3. Procedural standard

- **Fix the plan before running.** Record the plan, the way of sampling, the rules for refinement and decision, and the hashes of the code before the run.
- **Adaptation is allowed; the rules are fixed.** The following are allowed if the rules were fixed in advance, because an interval enclosure is correct however the boxes are chosen:
  - splitting undecided boxes;
  - refining the angular grid;
  - taking the first decision that passes.
- **Forbidden:**
  - changing the **scope of the claim** after seeing the results;
  - changing **how the audit samples** after seeing the results;
  - changing the **pass/fail thresholds** after seeing the results.
- **A change is a new plan.** If the method changes during a run, keep it as a revision (e.g. V55-A, V58-E) and do not delete the original record.
- **Diagnostic questions are binary.**
- **Keep every record.** Keep undecided rows and failed outputs too.
- **Set a budget.** Write the CPU seconds per box and in total into the plan.

---

## 4. Ledger standard

- **Box endpoints:** write them as integers or rationals, with the denominator stated (e.g. 2⁻²⁰, 5242880).
- **Values:** the lower and upper end of the interval, with the unit stated (e.g. 2⁻³⁶).
- **Covering:** verify in integers that **the union of the terminal boxes contains the claimed region**.
  - For a tree ledger, verify that each parent equals the union of its children.
  - For a ledger that is not a tree, verify that there are no holes, e.g. by a sweep.
  - The sum of areas (volumes) alone is not sufficient: with overlaps, holes can remain even when the sums agree.
  - **Overlaps are allowed**, but record whether there are any and how large they are.
- **Provenance:** record the hash of every input ledger and compare it byte for byte with the stored original.
- **Transfer:** when moving the ledger of one edge inward, keep for each row the margin, the error formula and the remaining margin as unrounded fractions.

---

## 5. Audit standard (GeoEncloseReader)

The audit proceeds in this order.

1. **Receipt:**
   - Check the hashes.
   - Extract ZIP files into a separate directory and check for dangerous paths.
   - Run Python with `-I`, and run the producer's scripts only on copies.
2. **Tracing back to the definition (mandatory):** if the producer and the auditor both start from the formulas in the same instructions, an error in the instructions enters both. So confirm, with a different quadrature, that the kernel agrees with **the original geometric definition** (e.g. a numerical derivative of the energy E(q) = ⟨k arccos²γ⟩).
3. **Point check (mandatory first stage):** check every point claim in the ledger (node values etc.) for containing an independent value. It is cheap enough to run on all of them and finds errors in formulas and transcription (e.g. Claude Code's check: 158,551 points in 25 minutes). **A point check alone verifies neither the range of a box nor any classification.**
4. **Hand check:** follow every new analytic lemma and constant by hand. Recompute chains of constants numerically with the auditor's code. Give each lemma a state from §1.2.
5. **Independent kernel:** do not use the producer's code, kernels or coefficients. Derive the formulas yourself.
6. **Sampling:**
   - Divide into strata at least by quantity, kernel, representation, and presence of contact.
   - In each stratum choose **at least 2 boxes with the weakest margin**.
   - In each stratum choose **at least 4 random boxes from a fixed seed**. A wrong formula can also produce a large margin, so the random side is necessary too.
7. **Same-quantity check:** confirm that the auditor's enclosure at the box centre meets the producer's interval. If it does not, mark INCONSISTENT.
8. **Sign check:** confirm the claimed sign on the whole box with the auditor's own enclosure.
9. **Margin reserve:** with adaptive splitting, the margins of terminal boxes are tight (V57). This is not misconduct; it follows from the mechanism. But a small error in a kernel could break the sign. So, for the sampled weakest boxes, confirm that the margin under the audit enclosure is not smaller than the producer's margin. If it is smaller, split one level further and confirm that the margin grows.
10. **Recomputing covering and transfer:** run the checks of §4 on every row with the auditor's own code.

---

## 6. Claims about roots

A claim such as "there is exactly one zero" cannot be made from box signs alone. Show the following three separately.

1. **Existence:** show opposite signs at the ends, or show it by an inclusion such as Krawczyk's.
2. **Uniqueness:** show the sign of the derivative on the candidate set for zeros (e.g. the function always crosses zero downward).
3. **Location:** enclose it in an interval.

Treat **degenerate points** separately (degeneracy at the centre, a zero reaching the boundary, merging zeros). Show the number of zeros and their indices by local analysis (fourth-order terms, one-sided Hessians, etc.).

---

## 7. Adoption criteria and levels

### 7.1 Common conditions for adoption
1. The producer's checker passes (hashes, integer covering, signs, local inclusions).
2. The audit of §5 finds no CONTRADICTED and no INCONSISTENT.
3. Every new analytic lemma is HAND_CHECKED or better.
4. There is a **claim–ledger table**: the computational claims are written as propositions (C1, C2, …), and for each proposition the supporting ledger, kernel and checks are tabulated.
5. The scope of the claim and the unfinished parts are stated explicitly (§8).
6. The plan, ledgers, code and records are stored in the evidence archive.

### 7.2 Levels
| Level | Conditions | How to state it in a paper |
|---|---|---|
| **A1 adoption (sampled)** | 7.1 and an audit by sampling as in §5 | A theorem **with the computational propositions C1, C2, … stated explicitly as assumptions** ("Under C1–C6, …") |
| **A2 full independent recomputation** | 7.1 and every terminal box re-enclosed with an independent kernel and CONFIRMED | **An unconditional theorem** (as a computer-assisted proof) |

If a counterexample or an error is found after adoption, record it as a correction and review the adoption.

### 7.3 Publication and human responsibility
At the stage of writing a paper, add two more conditions.
- **Publication:** make the ledgers, code, plans and checkers a public object with a DOI.
- **Human confirmation:** the author personally performs the final check and takes responsibility for the scope and level of the claims.

---

## 8. Standard for stating results

- **State ranges in numbers.** E.g. "1 < s ≤ 1 + 2⁻³⁹", "log(st) ≤ 10⁻⁵".
- **Distinguish existence theorems from explicit results.** When the size of a neighbourhood has not been obtained, say so.
- **State the level (A1 or A2).**
- **Put the unfinished parts in the same table.**
- **Do not overstate.** Write "closed" only when §7 is satisfied on the whole claimed range.
- **Keep errors as corrections.** Number them (E1, E2, …) and do not delete the original text.

---

## 9. Leaving tools behind

Rather than the answer to one problem, leave tools for solving the next one.

- With each audit, add kernels and self-tests to GeoEncloseReader, raise its version, and store it.
- Write the tool's limits and the caveats found into the README (e.g. H₃₃ at the equator for elongated shapes).
- Measure computational costs and keep them. Estimates depend on the method, so state which method a number refers to (V58).

---

## Appendix A: main events that gave rise to this standard

| Event | Standard |
|---|---|
| V49–V50: squaring a wide ball gave negative values or NaN | 2.1 compute from endpoints |
| V51 E2: a truncated Taylor expansion was used as an exact formula | 2.2 state the remainder |
| Reconnaissance E1: a 96-point quadrature produced a false zero curve of h₃ | 0 samples are only diagnostics |
| Oblate case: "D-OB is closed" was an overstatement (corrected to the window [2/5, 33/50]) | 8 do not overstate |
| V55-A, V58-E: the method was changed during a run | 3 a change is a new plan |
| V57: the producer's (Codex's) terminal boxes were intervals split until the sign just came out | 5-6 weakest boxes, 5-9 margin reserve |
| V58: with second-order enclosures, the number of boxes needed fell to about 1/100 | 9 state costs per method |
| Review of v1.0: two meanings of CONTRADICTED, an excessive covering requirement, the handling of adaptation, the relation between adoption and proof | 1, 4, 3, 7.2 |

## Appendix B: conformance table (results audited by chat in this session; V48–V53 will be organised in v1.2)

| Result | Analytic lemmas | Independent kernel | Weakest + random | Trace to definition | Full point check | Covering recomputed | Level |
|---|---|---|---|---|---|---|---|
| V54 oblate rim layer (λ ≤ 1/32) | HAND_CHECKED (all terms) | 6 points with mpmath and Reader 0.2.1 | points only (no finite cover) | E_ρ/ρ and E_zz compared with differences of the gradient trace | n/a | n/a | A1 (analytic result only) |
| V55 triaxial local theorem (near t = 3) | HAND_CHECKED; (1), (4), (6) rederived numerically | chat's Arb kernel | all 3 enclosure claims | (6) compared with the ε-derivative of E | not done | not done | A1 |
| V57 main rectangle, layer IV | 39 constants HAND_CHECKED; Appendix A3 is GAP (not followed in full) | Reader 0.3.0 | 30 boxes (weakest + random) | gradient trace (1) compared with differences of E (V55); centre h checked against sphere and rotational-family values | Claude Code checked the nodes | Krawczyk for the intersection recomputed | A1 |
| V57 explicit band | all constants HAND_CHECKED; (3) and (B) REDERIVED | Reader 0.3.0 | 4 disk boxes, 8 census items | formula for τ″ compared with differences of τ | not done | disk and transfer, all rows | A1 |
| V57 near-sphere | REDERIVED | — | — | formula compared with numerical derivatives to 14 digits | n/a | n/a | A1 (analytic only) |

What this table shows: **every result adopted so far is at level A1.** In a paper, such results are written as theorems with the computational propositions stated explicitly as assumptions. Raising them to A2 requires re-enclosing every terminal box with an independent kernel.
