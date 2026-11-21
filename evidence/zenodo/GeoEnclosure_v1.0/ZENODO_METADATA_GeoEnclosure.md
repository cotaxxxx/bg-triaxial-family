# Zenodo 登録の入力値：GeoEnclosure（研究ノート v1.0 ＋ 基準 v1.1 ＋ GeoEncloseReader 0.6.0）

Judge 判定（2026-11-21）：研究ノート、基準、道具を、一つの GeoEnclosure の登録にまとめる。第一論文は別の登録にする（`ZENODO_METADATA_Paper_I_v0.4.md`）。

この紙はアップロードしません。前の紙 `ZENODO_METADATA_GeoEnclosure_v1.1.md` は、この紙で置き換えます。★は、決めていただく点です。

## 1. ファイル（9 個をアップロード）

- `README.md`
- `GeoEnclosure_Note_v1_0_JA.md`（主文書）
- `GeoEnclosure_Standard_v1.1_ja.md`
- `GeoEnclosure_Standard_v1.1_en.md`
- `GeoEnclosure_Standard_v1.1_explained_ja.md`
- `GeoEncloseReader-0.6.0.zip`
- `check_n3_cover.py`
- `rerun_186_rules.py`
- `SHA256SUMS.txt`

Zenodo の画面で、主文書（default preview）に `GeoEnclosure_Note_v1_0_JA.md` を選んでください。

## 2. 基本の欄

| 欄 | 入れる値 |
|---|---|
| Resource type | **Publication → Working paper**（なければ Publication → Technical note） |
| Title | GeoEnclosure: a methodology of interval enclosure and sign determination based on problem structure (research note v1.0, Standard v1.1, GeoEncloseReader 0.6.0) |
| Additional titles | GeoEnclosure：構造に基づく区間包囲と符号判定の方法論（Translated title, Japanese） |
| Publication date | 公開する日 |
| Creators | Furuta, Katsushi（Person）。ORCID：0009-0005-3129-8043。所属：DAYBREAK |
| Description | §3 の英文をそのまま貼る |
| Version | 1.0 |
| Languages | Japanese、English |
| Licenses | ★ CC BY 4.0（文書）と MIT（コード） |
| Keywords | GeoEnclosure; interval analysis; verified numerical computation; computer-assisted proof; sign determination; parameter space; verification cost; computational design |
| Related works | Is supplemented by：https://github.com/cotaxxxx/GeoEnclosure（Software）。Is supplemented by：https://github.com/cotaxxxx/bg-spheroid-family/tree/1ec3ec11992ce97b1c468733f00e55d59006e632/manuscripts/2026-11-21/GeoEnclosure_Note_v1_0（Other）。References：第一論文の DOI（Publication / Preprint）。第一論文を先に出したときはここで入れ、後に出したときは Edit で足す |

## 3. Description（英文。このまま貼る）

In computer-assisted proofs, once a candidate solution or a proof strategy has been found, guaranteeing that it is correct can require checking a large parameter region and a great deal of computation. Now that AI makes candidates and strategies easier to obtain, this verification cost tends to limit the pace of research as a whole.

This record organises one research methodology for the problem of verification cost, called GeoEnclosure. Its basic idea is to work backwards from the desired conclusion and, according to the structure of the problem, to choose again which quantity to verify and in which representation. Its basic operations are summarised in three steps: *Decide what to measure. Enclose values. Read signs.*

The research note uses an elementary two-variable example and the records of a study of volume-preserving spheroids. It shows that the same region yields different mathematical information depending on the quantity decided. In particular, on a box that actually contains a zero, the sign of that quantity cannot be decided however finely the box is subdivided. A different kind of decision, transversality at the zero, is then needed in principle. The note confirms this concretely on the records of 186 boxes. Using the sign of H alone excludes roots in 56 boxes. Adding the radial curvature and a tangential fourth derivative gives the crossing direction in the remaining 130 boxes. The two check scripts recompute these counts from the public archive.

GeoEnclosure does not claim a new theory of interval analysis. It is a working procedure and a set of verification conditions for combining existing interval arithmetic, analytic estimates, sign decisions and independent checks according to the goal. The record contains three parts:
- the research note (Japanese), which presents the ideas, the verification conditions, the scope and the limits;
- the GeoEnclosure Standard v1.1 (Japanese original, English translation, plain-language explanation), with two adoption levels: A1, a sampled independent audit; A2, a full independent recomputation;
- GeoEncloseReader 0.6.0, the audit tool, including examples for students that use only the Python standard library.

AI agents took part as producers (ChatGPT and Codex, OpenAI) and as auditor (Claude, Anthropic), and Claude Code (Anthropic) took part in revision and checking. The author made every adoption decision and is responsible for the content. Not peer reviewed.

## 4. 公開の前に必ずすること

1. **研究ノートの補足資料 A.4：記入済み**（2026-11-21、確認範囲 G01〜G18。ブランチの commit `1ec3ec1`）。
2. **AI 利用の開示に Codex を加えるかを確かめてください。** ノートは第一論文の台帳と計算核に依拠しています。それを作ったのが Codex なら、ノートの開示にも名前を入れます。上の説明文は、すでに Codex を含めています。
3. ★ **ライセンスを決めてください。**
4. **Save draft で画面を確かめてから Publish してください。** DOI は取り消せません。
