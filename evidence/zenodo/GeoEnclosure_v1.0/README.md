# GeoEnclosure: research note v1.0, Standard v1.1 and GeoEncloseReader 0.6.0

Author: Katsushi Furuta (古田 勝士), DAYBREAK (independent research). ORCID 0009-0005-3129-8043.

## What this is

**GeoEnclosure** is a working method for computer-assisted proofs: *Decide what to measure. Enclose values. Read signs.* It works backwards from the conclusion one wants, chooses which quantity to enclose and in which representation, encloses it with guaranteed intervals, and reads what its sign allows one to conclude. Independent checking and analytic closure turn the finitely many box results into a mathematical claim.

This record holds the three parts of GeoEnclosure:

| Part | File | Role |
|---|---|---|
| Research note v1.0 (Japanese) | `GeoEnclosure_Note_v1_0_JA.md` | The method: definition, three operations, four principles, elementary examples, and a reproducible comparison on 186 boxes from a spheroid study. It also gives the limits of the method and a table of every claim with its evidence, checker and state |
| Standard v1.1 | `GeoEnclosure_Standard_v1.1_ja.md` (authoritative), `_en.md` (translation), `_explained_ja.md` (plain-language explanation) | The conditions under which a result may be called verified by interval computation, and two adoption levels: A1, a sampled independent audit; A2, a full independent recomputation |
| GeoEncloseReader 0.6.0 | `GeoEncloseReader-0.6.0.zip` | The audit tool: interval kernels, self-tests, reference quadrature, and examples for students (`GER2/examples/`, standard library only) |
| Check scripts | `check_n3_cover.py`, `rerun_186_rules.py` | They recompute the counts of §6 of the note from the public archive of the spheroid study, as described in the note's references |
| Checksums | `SHA256SUMS.txt` | SHA-256 of every file above |

## What is not new

GeoEnclosure introduces no new numerical technique. It assembles established ones:
- outward-rounded interval arithmetic and ball arithmetic;
- mean-value and Taylor forms with explicit remainders;
- interval Newton and Krawczyk tests;
- adaptive bisection, as in interval global optimisation;
- the separation of producer and independent checker.

What it adds is the explicit design step of choosing the quantity to be decided, and its verification conditions (note §1.2; Standard v1.1). The note's references give the standard literature (Moore; Moore–Kearfott–Cloud; Rump; Tucker; Hansen–Walster; Ratschek–Rokne; Gómez-Serrano; Oishi).

## Roles and use of AI

The standard separates three roles:
- **Producer:** AI agents: ChatGPT (OpenAI, GPT-6.2 Astra), using Codex (OpenAI) for the computations.
- **Auditor:** Claude (Anthropic, on claude.ai). It drafted the standard and wrote GeoEncloseReader.
- **Judge:** the author, who decides adoption and is responsible for the content.

The idea of the method came from the author's dialogue with Claude. Claude Code (Anthropic) reviewed v1.0 of the standard, revised the note to v1.0, and re-ran its checks from the public archive. The disclosure in the note gives the details. No AI decided any adoption.

## Status

- The research note is not peer reviewed. The author checked claims G01–G18 on 2026-11-21 (Appendix A.4).
- The standard v1.1 was adopted by the Judge on 2026-11-20.
- All outputs of GeoEncloseReader are DIAGNOSTIC_ONLY until adopted.

Version history of the tool:
- 0.5.0: second order in the parameters; corrects E3 of 0.4.0.
- 0.5.1: examples for students.
- 0.6.0: the `lazy` option. It gives the same tree of boxes and is faster.

## Provenance

| Item | Location |
|---|---|
| Research note and check scripts | `cotaxxxx/bg-spheroid-family`, branch `claude/geoenclosure-note-v1.0-20261121`, commit `1a4d1f03d261512428562376a03ec3f0328e6f86`, `manuscripts/2026-11-21/GeoEnclosure_Note_v1_0/`. The note is byte-identical to that file (sha256 `db152ea3…`), which records the author's final check (Appendix A.4: 2026-11-21, claims G01–G18) |
| Adopted originals of the standard | `cotaxxxx/bg-triaxial-family`, commit `67eb2afdd3ccc0bb976302dbb68548b256b3fc45`, `evidence/chat-originals/2026-11-20/GEOENCLOSURE_STANDARD/` |
| Tool | `cotaxxxx/GeoEnclosure` |

## Licence

- Documents: CC BY 4.0.
- Code: MIT.

## 日本語の概要

GeoEnclosure は、計算機援用証明の作業法です。標語は「何を測るか決める。値を包む。符号を読む。」です。この登録物には、次の三つを一つにまとめて収めています。

- **研究ノート v1.0：** 方法の説明
- **基準 v1.1：** 確かめたと言ってよい条件
- **GeoEncloseReader 0.6.0：** 監査の道具。学生向けの例題を含む

新しい数値の技法は含みません。既にある技法を組み合わせたものです。方法の着想は、著者と Claude との対話から生まれました。基準の本文と道具は、著者の指示のもとで Claude が起草しました。研究ノートは ChatGPT と Claude Code が改訂しました。方法の命名、採用の判断、内容の責任は著者にあります。
