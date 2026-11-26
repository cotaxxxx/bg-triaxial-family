# 論文 II v1.0 公開候補の記録（2026-11-27 JST、chat）

## ファイルとハッシュ

| ファイル | 大きさ | SHA-256 | MD5 |
|---|---:|---|---|
| `Paper_II_v1_0_EN.pdf`（21 ページ） | 約 250 KB | `2d8b95bdc0603c76e3e5195fc53009b49625e6a3d50fead0b1d07199d42042f3` | `b1236c6df61264840184188dc8e1c40d` |
| `Paper_II_v1_0_reproduction.zip`（2,384 ファイル） | 53,008,476 バイト | `df0fcbb768e018cafca40df2831bf1f377017eb9d73a343da6027e57a5c196d1` | `a76201654cca8c8a28f0d341796a7959` |

PDF はこのディレクトリにある。zip は大きいので repo には置かず、Judge に直接渡した。zip の中身はすべて、README に書いた固定コミットからの写しで、`SHA256SUMS.txt`（2,383 行）で照合できる。zip の中の PDF は上の PDF と同一。

## Zenodo の入力案

- Resource type：Publication / Preprint（論文 I と同じにする）
- Title：A Map of the Angle Energy on Triaxial Ellipsoids: Four Threshold Curves of Stationary Points, with Reproduction Code
- Creator：Furuta, Katsushi／Affiliation：DAYBREAK／ORCID：0009-0005-3129-8043
- DOI：「No, I need one」
- Version：v1.0／Publication date：公開日／Language：English
- Keywords：angle energy; triaxial ellipsoid; stationary points; bifurcation; computer-assisted proof; interval arithmetic; GeoEnclosure; reproducibility
- Related works：
  - Continues / Is supplement to … 論文 I `10.5281/zenodo.24495446`（論文 I と同じ関係の種類を選ぶ）
  - References … GeoEnclosure `10.5281/zenodo.24421364`
  - Is supplemented by … https://github.com/cotaxxxx/bg-triaxial-family
- Description（英）：PDF の Abstract の三段落。
- Description（日）：PDF の付録 B の題名と三段落。
- Files：上の PDF と zip の二つ。PDF をプレビューに。ファイル名に "-1" が付いていないこと。

## 公開前の確認表（PAPER_II_RELEASE_CHECKLIST）の状況

| 項目 | 状況 |
|---|---|
| A 定理の文面が裁定と一致 | 済（2d2576e＋訂正 d6dc12b、8f9fe35）。Astra・Claude Code・Muse が確認 |
| A 数値・区間が台帳と一致 | 済（Claude Code が全件、chat が交点・D・ヤコビアンを有理数で引き直し） |
| A 範囲・前提の書き方が要旨・序論・結論で同じ | 済（Muse の監査 2 回） |
| B 文献 [3][4][5][6][7][9] | 済（[3][4][5][9] は Claude Code、[6][7] は chat が原典・書誌ページで確認） |
| B 文献 [1][2]（自著の DOI ページ） | **未**。chat と Claude Code の環境から Zenodo が開けない。Judge が投稿時に二つの DOI を開いて題名を確認 |
| C 目次のページ番号 | 済（16 項目を PDF の実ページと機械的に照合） |
| C 参照切れ・はみ出し・欠け字 | 済（LaTeX のログで欠け字 0、はみ出し 0、未定義参照 0） |
| C フォント埋め込み | 済（pdffonts で全フォント埋め込み）。日本語は付録 B のみ |
| C リンクは 40 桁固定 | 済（「データとコード」の表）。§6・§7 の本文中の短い番号 04051b6、2d2576e、d6dc12b、8f9fe35 は表の 40 桁と対応 |
| D コミット番号が実物と一致 | 済（Claude Code が 14 個、chat が表の 13 個を `git rev-parse` で確認） |
| D zip の中身一覧と SHA-256・MD5 | 済（上の表） |
| D 等級と採用裁定の関係 | 済（§7 末尾） |
| D AI 開示 | 済（各担当の実際の範囲で記載） |
| D 著者の通読・承認の文 | 済（実際の通読のあとに確定、本ディレクトリの PDF に記載） |
| E Zenodo 入力 | **Judge の作業**。公開ボタンの前に PDF の SHA-256 をもう一度照合（公開後は変えられない） |
| F 公開後（DOI を README・STATE・実例一覧へ） | 公開後に chat と Dig |

## 体裁について（正直な注記）

PDF は Markdown から pandoc と XeLaTeX で組んだ。本文は DejaVu Serif、数式は Computer Modern で、添字つきの記号だけを数式として組んでいるため、本文中の記号は立体と斜体が混じる。読むのに支障はないが、学術誌の組版の水準ではない。
