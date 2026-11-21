# Zenodo 登録の入力値：GeoEnclosure 基準 v1.1 ＋ GeoEncloseReader 0.5.0

この紙はアップロードしません。Zenodo の「New upload」の画面に、上から順に写すための値です。★は、決めていただく点です。

## 1. ファイル（6 個をアップロード）

- `README.md`
- `GeoEnclosure_Standard_v1.1_ja.md`
- `GeoEnclosure_Standard_v1.1_en.md`
- `GeoEnclosure_Standard_v1.1_explained_ja.md`
- `GeoEncloseReader-0.5.0.zip`
- `SHA256SUMS.txt`

## 2. 基本の欄

| 欄 | 入れる値 |
|---|---|
| Do you already have a DOI? | No（Zenodo に発行してもらう） |
| Resource type | **Publication → Standard**（なければ Publication → Technical note） |
| Title | GeoEnclosure Standard v1.1: conditions for interval-enclosure verification in computer-assisted proofs, with GeoEncloseReader 0.5.0 |
| Publication date | 2026-11-21 |
| Creators | Furuta, Katsushi（Person）。★ ORCID があれば入れる。所属は Independent researcher |
| Description | §3 の英文をそのまま貼る |
| Licenses | ★ Creative Commons Attribution 4.0 International（CC BY 4.0）と MIT License の二つ |
| Version | 1.1（道具は 0.5.0。題名と説明文に書いてある） |
| Languages | Japanese、English |
| Keywords | computer-assisted proof; interval arithmetic; verified computation; experimental mathematics; reproducibility; audit; ellipsoid; stationary points; GeoEnclosure |
| Related works | Is supplemented by：https://github.com/cotaxxxx/bg-triaxial-family（Resource type：Other） |

## 3. Description（英文。このまま貼る）

GeoEnclosure is a methodology for computer-assisted proofs about shapes. A quantity computed on a shape is enclosed in an interval that is certain to contain the true value, rounding included. The structure is then decided by signs on finitely many boxes, and the result is closed by analysis.

This record contains the GeoEnclosure Standard v1.1 and GeoEncloseReader 0.5.0, the audit tool that implements its independent re-enclosure. The standard sets the conditions under which a claim may be called "verified by interval computation". It covers:
- rounding and the floating-point environment;
- quadrature remainders and singularities;
- plans fixed before running, with adaptive refinement allowed only under pre-fixed rules;
- ledgers and coverings;
- independent audit, with tracing back to the original definition, full point checks, weakest-margin plus seeded random sampling, and a margin reserve;
- claims about roots;
- two adoption levels, tied to how a theorem is stated: A1, a sampled audit, gives a theorem with its computational propositions stated as assumptions; A2, a full independent recomputation, gives an unconditional theorem.

The standard was written from use. Each rule corresponds to an error actually caught while studying the stationary points of the energy E(q) = ⟨k arccos²γ⟩ over volume-preserving spheroids and triaxial ellipsoids.

The Japanese text is authoritative; an English translation and a plain-language explanation (Japanese) are included. The method separates three roles: producer, auditor and Judge. In this work the producers and the auditor were AI agents: Codex (OpenAI) produced, and Claude (Anthropic) audited, drafted the standard and wrote the tool. The author is the Judge, who named the method, made every adoption decision, and is responsible for the content. Provenance of every file is given in README.md.

## 4. 公開の前に確かめること（Zenodo の DOI は取り消せません）

- ★ **ライセンス：** 文書は CC BY 4.0、コードは MIT を案にしています。変えるときは、README.md の「Licence」の節も同じに直してください。直したら chat が SHA256SUMS を作り直します。
- ★ **名前の表記：** README と作者欄は「Katsushi Furuta（古田 勝士）」にしています。GitHub の表記に合わせました。
- ★ **公開の範囲：** 「Public」で公開すると、すぐに DOI が付いて誰でも読めます。先に「Save draft」で画面を確かめてから「Publish」を押すのが安全です。
- **Experimental Mathematics との関係：** この登録物は方法論の基準と道具です。論文の原稿ではありません。論文で引用するときは、この DOI を挙げます。投稿の前に、この雑誌の事前公開の規定を確かめてください。
