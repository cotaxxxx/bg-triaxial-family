# Zenodo 登録の入力値：第一論文 v0.4（プレプリント）

この紙はアップロードしません。★は、決めていただく点です。

## 0. 出す順番（Judge 判定 2026-11-21：別の登録にし、DOI で相互リンクする）

1. **GeoEnclosure を先に公開する（DOI-A）。**
2. **第一論文を公開する（DOI-B）。** Related works に DOI-A を入れる。
3. **GeoEnclosure の登録を Edit する。** Related works に DOI-B を足す。DOI-A は変わらない。

## 1. ファイル（4 個をアップロード）

ファイルは `cotaxxxx/bg-spheroid-family`、commit `a5ab9b5016c8df9b7f94cbfd7cd0e82aeba8dd28`、`manuscripts/2026-11-20/Paper_I_v0_4/` にあります。SHA-256 は、同じ場所にある `Paper_I_v0_4.sha256` と一致することを確かめました。

| ファイル | SHA-256 の先頭 |
|---|---|
| `Paper_I_v0_4_Integrated_EN.pdf`（36 ページ） | `4ca119d6…` |
| `Paper_I_v0_4_Computational_Supplement_EN.pdf` | `2441b82e…` |
| `Paper_I_v0_4_Manuscript_and_Verification.zip` | `57ee540b…` |
| `Paper_I_v0_4.sha256` | — |

`Paper_I_v0_4_Review_Response_JA.md` は、内部の査読への回答なので外すことを勧めます。

## 2. 基本の欄

| 欄 | 入れる値 |
|---|---|
| Resource type | **Publication → Preprint** |
| Title | Counting stationary points and saddle circles of a cone-volume-weighted angle energy on spheroids |
| Publication date | 公開する日 |
| Creators | Furuta, Katsushi（Person）。ORCID：**0009-0005-3129-8043**（論文の表紙の値）。所属：DAYBREAK |
| Description | §3 の英文をそのまま貼る |
| Version | v0.4（Integrated research draft） |
| Language | English |
| Licenses | ★ CC BY 4.0 を案とする。Taylor & Francis は、投稿前の原稿を非営利のサーバーに置くことを認めている |
| Keywords | spheroid; stationary set; cone volume measure; radial Gauss map; Morse–Bott critical manifold; validated numerics |
| Related works | References：DOI-A（GeoEnclosure、Resource type：Publication / Standard）。Is supplemented by：https://github.com/cotaxxxx/bg-spheroid-family/tree/a5ab9b5016c8df9b7f94cbfd7cd0e82aeba8dd28/manuscripts/2026-11-20/Paper_I_v0_4（Resource type：Other） |

## 3. Description（英文。このまま貼る）

A numerical search finds an equatorial saddle circle in a prolate spheroid. How can one exclude a second circle, or an off-equatorial critical point? For the squared radial–normal angle averaged against cone volume, we reduce the full stationary-set diagram to six explicit computational assertions. In particular, rotation turns an entire critical orbit into a scalar root, and a fourth derivative in a tangential direction determines its radial crossing. An exploratory transverse-sign cover left 21,254 of 31,340 leaves undecided. Two representations of a tangential fourth derivative give a negative upper bound on all 731 equatorial boxes for aspect ratios from two to five. A second implementation encloses the same boxes with 1,043 terminal pieces. Strict radial monotonicity then reduces the existence of a saddle circle to two endpoint signs. Over the full volume-preserving family, analytic endpoint estimates and the six named inputs yield four transitions involving the centre, axial saddle pairs, an equatorial saddle circle and boundary gradient traces.

**Status of this version.** This is a proof-development manuscript, not a submission-ready certification claim. The analytic arguments are written out. The computational inputs are stated as Assertions C1–C6, and the classification theorem states its dependence on them explicitly. In the terms of the GeoEnclosure Standard v1.1 (DOI-A), the result is at adoption level A1: a sampled independent audit, giving a theorem with its computational propositions as assumptions. It is not at level A2, a full independent recomputation. Not peer reviewed.

## 4. 公開の前に直すこと・決めること

1. **AI 利用の開示（直すことを強く勧めます）。**
   - 今の PDF（33 ページ、「Use of AI tools.」の段落）には ChatGPT しか書かれていません。
   - 論文が引用している計算記録の多くは、Codex（OpenAI）が作ったものです（文献に `…_CODEX` のフォルダが並んでいます）。監査は Claude（Anthropic）が、台帳の点の照合は Claude Code（Anthropic）が行いました。
   - GeoEnclosure の登録では、これらを名前で書いています。同じ著者の二つの登録で開示がずれると、読む人に不信を与えます。Zenodo の DOI は取り消せないので、公開の前に一文を直してください。案は次のとおりです。

     > Use of AI tools. ChatGPT and Codex (OpenAI) assisted with exploratory derivations, numerical code, the producer computations cited in the source records, verification scripts, English drafting, revision and typesetting. Claude (Anthropic) performed the independent audits and drafted the GeoEnclosure Standard used to state the adoption levels; Claude Code (Anthropic) performed the ledger point checks. Final scientific review and approval of the manuscript and disclosure rest with the author.

2. ★ **「approval … pending」の一文。** 今の PDF は、著者の最終承認を「保留中」と書いています。
   - 承認してから出すなら、「pending」を消してください。
   - そのまま出すなら、「著者の承認前の草稿」として公開することになります。

3. ★ **ライセンス。** 文書は CC BY 4.0 を案にしています。

4. **文献のリンク先はすべて公開されています。** `bg-spheroid-family`、`bg-oblate-spheroid`、`basepoint-geometry` は、どれも公開リポジトリであることを確かめました。

5. **Experimental Mathematics への投稿：** 投稿するときは、送る原稿に Zenodo の DOI を書き、「プレプリントとして公開済み」と添えてください。
