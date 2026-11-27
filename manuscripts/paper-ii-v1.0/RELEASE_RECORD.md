# 論文 II v1.0 公開版の記録（第 3 版・最終、2026-11-27 JST、chat）

第 1 版（コミット `69ff74e`）の PDF と zip は、ビューアの同時掲載と題名の変更により公開版ではなくなった。以下が現在の候補。

## Zenodo に入れる 3 ファイル（最終版、DOI 10.5281/zenodo.24581453）

| ファイル | 大きさ（バイト） | SHA-256 | MD5 |
|---|---:|---|---|
| `Paper_II_v1_0_EN.pdf`（22 ページ） | 263,881 | `bcc997e68b647c218873f894c5df9252a97f517edc450a94bf9c60eab460e244` | `6110e8977a53c445106c5a4c64dd9e1a` |
| `Paper_II_v1_0_reproduction.zip`（2,429 ファイル） | 56,961,041 | `e6650c446b846e23ad4a66b326d3267cfb14f3ee916bf99188feb49732be1dc8` | `62767e41a563d238f4630f622e09f1ef` |
| `paper2_viewer.html` | 107,949 | `99c0e05050787840dabec16f845a2717e900a5a21c9837bbe17ad8e18bf1b4c8` | `663e472a9db51d7a3c175b5316f7a3b3` |

- PDF はこのディレクトリ（コミット `dfee5342efa9cabb0fdde52651dacd23d84b75b7`）。zip の中の PDF・ビューアは上と同一。
- ビューアは Claude Code の `b79b8e4b2efecd1327baa2d674e970f889d385a8`（chat 監査 3 回、すべて PASS）。
- zip は repo に置かない。`SHA256SUMS.txt`（2,428 行）で照合できる。
- これより前の候補（第 1 版 `69ff74e`、第 2 版 `46c17ca`、DOI 入り PDF の最初の版 `ae8d73b`）のハッシュは公開版のものではない。
- 相互参照：ビューアの埋め込みデータは論文のソース `ae8d73b` を指す。公開版の PDF はその一つ後のコミットで組んだもので、違いは「データとコード」の表のビューアのコミット番号の一行だけ。

## v0.10（査読・監査済みの草稿）からの追加

題名（裁定 `83aa382`、`c775274`）、著者の承認の一文、訂正裁定 d6dc12b の併記、「データとコード」の表、ビューアの段落と AI 開示の一文、付録 B。「発見的な方法論」の一文（裁定 `83e76d0`）は v0.10 に入っている。

## Zenodo の入力案

- Resource type：Publication / Preprint（論文 I と同じにする）
- Title：A Map of the Angle Energy on Triaxial Ellipsoids: Four Threshold Curves of Stationary Points, with Reproduction Code and an Interactive Viewer
- Creator：Furuta, Katsushi／Affiliation：DAYBREAK／ORCID：0009-0005-3129-8043
- Version：v1.0／Language：English
- Keywords：angle energy; triaxial ellipsoid; stationary points; bifurcation; computer-assisted proof; interval arithmetic; GeoEnclosure; reproducibility; interactive viewer
- Related works：論文 I `10.5281/zenodo.24495446`（論文 I と同じ関係の種類）／GeoEnclosure `10.5281/zenodo.24421364`（References）／https://github.com/cotaxxxx/bg-triaxial-family（Is supplemented by）
- Description（英）：PDF の Abstract の三段落＋「Files: the paper (PDF), a reproduction archive (zip), and an interactive viewer (one self-contained HTML file; open it in a browser).」
- Description（日）：PDF の付録 B。
- License：文書 CC BY 4.0、コード MIT（GeoEnclosure の登録と同じ書き方）。
- Files：上の 3 つ。PDF をプレビューに。ファイル名に "-1" が付いていないこと。

## 確認表の状況

| 項目 | 状況 |
|---|---|
| 定理の文面と裁定、数値と台帳 | 済（Astra・Claude Code・Muse、訂正 d6dc12b） |
| 文献 [3]〜[9] | 済。[1][2] は **Judge が投稿時に DOI ページで題名を確認** |
| 目次（16 項目）、欠け字 0、はみ出し 0、未定義参照 0、フォント埋め込み | 済（組み直し後に再確認） |
| コミット番号（表の 14 個） | 済（`git rev-parse`） |
| zip の展開と、Python だけの再確認の例 | 済（組み直し後に再実行、`faces_and_miranda: True`） |
| ビューア | 済（監査 2 回）。Safari・Firefox・実機は未確認 |
| v1.0 の PDF を査読者が見たか | **見ていない**（見たのは v0.1〜v0.6 の本文）。v0.6 以後の本文の変更は、§8 の二文、要旨の一文、AI 開示、題名、ビューアの段落 |
| Zenodo 入力、公開前の SHA-256 の再照合 | **Judge の作業** |
