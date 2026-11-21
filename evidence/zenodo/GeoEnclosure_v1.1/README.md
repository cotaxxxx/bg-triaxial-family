# GeoEnclosure Standard v1.1 and GeoEncloseReader 0.5.0

Author: Katsushi Furuta (古田 勝士), independent researcher.

## What this is

**GeoEnclosure** is a methodology for computer-assisted proofs about shapes. A quantity computed on a shape (Geo) is enclosed (Enclosure) in an interval that is certain to contain the true value, rounding included. The structure is then decided by signs on finitely many boxes, and closed by analysis.

This record contains two things:
- **The GeoEnclosure Standard v1.1:** the conditions under which a claim may be called "verified by interval computation". It covers rounding and the floating-point environment, quadrature remainders, singularities, plans fixed before running, ledgers and coverings, independent audit, claims about roots, two adoption levels (A1 sampled audit, A2 full independent recomputation) tied to how a theorem is stated, and how results are reported.
- **GeoEncloseReader 0.5.0:** the audit tool that implements the standard's independent re-enclosure.

The standard was written from use, not in advance. It was applied to the stationary points of the energy E(q) = ⟨k arccos²γ⟩ over volume-preserving spheroids and triaxial ellipsoids, and each rule in it corresponds to an error that was actually caught (Appendix A of the standard).

## What is not new

GeoEnclosure introduces no new numerical technique. It is an assembly of established ones, written down as rules and checks for one research programme:
- outward-rounded interval arithmetic and ball arithmetic;
- mean-value forms and Taylor forms with explicit remainders;
- Krawczyk's existence and uniqueness test;
- adaptive bisection;
- the separation of producer and independent checker.

What the record adds is the specific combination: an order of audit steps, sampling rules, adoption levels tied to how theorems are stated, and a log of the errors that motivated each rule. It also provides a tool that implements the combination. Standard references for the techniques:

- R. E. Moore, R. B. Kearfott, M. J. Cloud, *Introduction to Interval Analysis*, SIAM, 2009.
- W. Tucker, *Validated Numerics: A Short Introduction to Rigorous Computations*, Princeton University Press, 2011.
- S. M. Rump, Verification methods: Rigorous results using floating-point arithmetic, *Acta Numerica* 19 (2010), 287–449.
- F. Johansson, Arb: efficient arbitrary-precision midpoint-radius interval arithmetic, *IEEE Transactions on Computers* 66 (2017), 1281–1292.
- R. Krawczyk, Newton-Algorithmen zur Bestimmung von Nullstellen mit Fehlerschranken, *Computing* 4 (1969), 187–201.

## Files

| File | Content |
|---|---|
| `GeoEnclosure_Standard_v1.1_ja.md` | The standard, Japanese. **Authoritative text**, byte-identical to the adopted original |
| `GeoEnclosure_Standard_v1.1_en.md` | English translation |
| `GeoEnclosure_Standard_v1.1_explained_ja.md` | Plain-language explanation for readers outside the project (Japanese) |
| `GeoEncloseReader-0.5.0.zip` | The audit tool: source, self-tests, reference quadrature |
| `SHA256SUMS.txt` | SHA-256 of every file above |

## Roles in the text

The standard separates three roles. This separation is the core of the method.

| Name in the text | Role | Who |
|---|---|---|
| producer (作った人) | computes, and writes ledgers and reports | AI agents, mainly Codex (OpenAI) |
| auditor; "chat" (確かめる人) | checks with different formulas, different code and an independent kernel; drafted the standard; builds GeoEncloseReader | Claude (Anthropic) in claude.ai |
| Judge (判定する人) | decides whether a result is adopted, and takes responsibility | the author |

Claude Code (Anthropic) reviewed v1.0 of the standard. The labels V48, V57, … are the numbers of the audit runs in the underlying study.

**Use of AI.** The text of the standard and the code of GeoEncloseReader were drafted by an AI (Claude) under the author's direction. The author named the method, made every adoption decision, and is responsible for the content. No claim in this record is a mathematical theorem by itself. The standard explains how such claims are to be checked and stated.

## Status

- The standard v1.1 was adopted by the Judge on 2026-11-20.
- GeoEncloseReader is research software. All of its outputs are DIAGNOSTIC_ONLY until adopted.
- Version 0.5.0 adds an enclosure that is second order in the parameters, and corrects error E3 of 0.4.0.

## Provenance

The adopted originals and every audit record are kept, unchanged, in the GitHub repository `cotaxxxx/bg-triaxial-family`:
- branch `evidence/triaxial-chat`, commit `e3a466199150b2a7c62096f900acc0d3fab2ecba`;
- folder `evidence/chat-originals/`, with subfolders `2026-11-20/GEOENCLOSURE_STANDARD/` for the standard and `2026-11-21/D_TRI_LAYER_I_II_READER05_V60/` for Reader 0.5.0.

## Licence

- Documents: CC BY 4.0.
- Code: MIT.

## 日本語の概要

GeoEnclosure は、形についての計算機援用証明の方法論です。形の上で計算した量を、丸めまで含めて真の値を必ず含む区間で包み、有限個の箱の符号で構造を決め、解析で閉じます。

この登録物には、二つを収めています。
- **GeoEnclosure 基準 v1.1：** 「区間計算で確かめた」と言ってよい条件です。日本語が正本で、英訳を付けています。
- **GeoEncloseReader 0.5.0：** 基準のうち、独立に包み直す部分を担う監査の道具です。

新しい数値の技法は含みません。既にある技法の組み合わせです：外向き丸めの区間演算と球の演算、剰余を明示した平均値形式とテイラー形式、Krawczyk の判定、適応的な二分、作る人と確かめる人の分離。この登録物が加えるのは、その組み合わせ方です。具体的には、監査の順序、抜き取りの規則、定理の書き方と結び付けた採用の水準、そして各規則のもとになった誤りの記録と、それを実装した道具です。

基準の本文と道具のコードは、著者の指示のもとで AI（Claude）が起草しました。方法の命名、採用の判断、内容の責任は著者にあります。
