# 論文 II v1.0 公開候補の記録（第 2 版、2026-11-27 JST、chat）

第 1 版（コミット `69ff74e`）の PDF と zip は、ビューアの同時掲載と題名の変更により公開版ではなくなった。以下が現在の候補。

## Zenodo に入れる 3 ファイル

| ファイル | 大きさ（バイト） | SHA-256 | MD5 |
|---|---:|---|---|
| `Paper_II_v1_0_EN.pdf`（22 ページ） | 263,850 | `d44bf9c806506060c6d4f7b3f97a35d340696698ce85070b81e3a71e77852b12` | `3a84cd3aac20deb8c0fb6a6eb38b81bf` |
| `Paper_II_v1_0_reproduction.zip`（2,421 ファイル） | 56,317,019 | `8ac659039ae998638d55537d1214b98ecedabe7f32537e1099d4dd00f637d383` | `10f9bafdce19b1a1a0676c702e7fea3c` |
| `paper2_viewer.html` | 107,950 | `c97bbb970c543fd3641f203e469b154e34c0cb2e671e4f64d00841b77bfbe42a` | `b2bdcc234627ff55741fb3656b6ba751` |

- PDF はこのディレクトリ（コミット `3f290f2ef712cb20452b6f494120d3ea03250e99`）。zip の中の PDF・ビューアは上と同一。
- zip は大きいので repo に置かない。中身は README の固定コミットからの写しで、`SHA256SUMS.txt`（2,420 行）で照合できる。
- ビューアは Claude Code の `202744a`（chat 監査 PASS）。

**DOI について：** ビューアのフッターは「DOI：公開後に記入」のまま。PDF にも自分の DOI は入っていない。Zenodo の下書きで DOI を予約してから入れ直すかどうかは Judge の判断（入れ直すと 3 つともハッシュが変わる）。

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
