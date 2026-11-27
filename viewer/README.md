# 論文 II の連動ビューア

論文：A Map of the Angle Energy on Triaxial Ellipsoids: Four Threshold Curves of Stationary Points, with Reproduction Code and an Interactive Viewer（三軸楕円体の角度エネルギー地図 ― 停留点が出入りする四本の境目（再現コード・ビューア付き））

2026-11-27 ／ Claude Code ／ 依頼：chat「Claude Code への依頼書：論文 II の連動ビューア（デモソフト）の完成」

`paper2_viewer.html` を開くと動く。1 つのファイルで完結し、外部の読み込みはない。大きさは約 107 KB。

**このビューアは説明用の道具であり、証明の一部ではない。**

## 画面

- 左：形の地図。座標は論文と同じ (y, z)、範囲は R = [1/4, 1] × [1, 7]。R の外は斜線で、「主張なし」と表示する。
- 右：半軸 (1, y, z) の楕円体。中心と、極 ±e_y、±e_x に印がある。ドラッグで回る。
- 地図をクリックかドラッグすると形が選べる。用意した道（扁平の辺、扁長の辺、交点を通る道、Z₂ と ∂₂ のあいだ）と、再生・停止、スライダーがある。
- 「拡大」で帯の箱が見える（4 倍ずつ、256 倍まで）。拡大中はクリックで形を選ぶ（ドラッグは等倍のときだけ）。
- 表示は英語（既定）と日本語を切り替えられる。用語は論文 II v1.0 と、その付録 B に合わせた。

## 何が証明済みで、何が説明用か

| 画面の区分 | 中身 | 出どころ |
|---|---|---|
| A　証明済み | 各弧が通る帯の箱（Z₁ 276、Z₂ 154、∂₁ 111、∂₂ 71 本）、辺の上の端点の区間 8 つ、交点の箱 | v2 の台帳の `charts.jsonl`（status = CHART）と `edges.jsonl`（root_interval）の、正確な二進有理数。交点の箱は論文 II v1.0 の定理 1 の区間（裁定 `d6dc12b`） |
| B　説明用 | 帯の中心を結んだ破線、対がある側を示す薄い帯 | 線は帯の中心を鎖の順につないだもの。薄い帯の向きは定理 2（中心は A_i > 0 の側、極は T_i < 0 の側）で、幅は論文の図 2 と同じ値。幅に意味はない |
| C　保証のない数値 | 3D 表示の白抜きの印（軸の上の停留点の位置） | `uncertified_axis_table.py`。倍精度、誤差評価なし。**既定では非表示**（Judge 裁定）。チェックを入れたときだけ、印、凡例 C、注記、出来事の欄の「Uncertified」の行が出る。表示しているあいだは、3D の絵の中にも「Uncertified numerics — not proved in Paper II／保証のない数値（論文 II は未証明）」と描く |

選んだ形が帯の箱の中にあるとき、右の面で、定理 2 のどの出来事の場所かを強調する（Z₁・Z₂ は中心とその軸、∂₁・∂₂ はその極、辺 y = 1 の c_p・b_p は赤道面の円、交点の箱は中心と極の両方）。文面は「この帯を弧が通る」「形が弧を横切るとき、対がちょうど一対、出入りする」までで、その形が弧の上にあるとは言わない。

左の辺 y = 1/4 の上の二つの印（Z₂ と ∂₂ の端）は、端点の区間の中点に置いた説明用（B）である。証明済みなのは区間（A。辺の上の太い線分）のほうである。辺 y = 1 と z = 1 の上の四つの印（c_o、b_o、b_p、c_p）は、論文 I の参考小数の位置に置いてあり、これも証明済みなのは区間である。

画面に出していないもの：R の外、領域ごとの停留点の個数、領域の塗り分け、対が二本の弧のあいだで存続すること、停留点の種類。

## 入力（固定）

- 帯と端点：`cotaxxxx/bg-triaxial-family`、commit `862220cc03f8044ab770548d865a76ed56fc612c`、`evidence/dig/2026-11-26/CANDIDATE_B_V2_PC_RESULT/RESULT/`
  - `charts.jsonl`　SHA-256 `95e1f773faf4c184cec4c953724c8a88a7c1e4c80874c061ed9bd7da3c973906`
  - `edges.jsonl`　SHA-256 `0d19458192597d424915afa4bd253a4c9c0052c439850aab29b5ce2904bf32a2`
- 交点の箱：論文 II v1.0（doi:10.5281/zenodo.24581453。ソースは commit `ae8d73b5aefba2870ca6ded76eb53851c5cb4fdb`）の定理 1 の 4。y* ∈ [0.63813109, 0.63821937]、z* ∈ [2.29643023, 2.29674050]。
- 論文 I の閾値の参考小数（印の位置）：c_o 0.40795886、b_o 0.64354577、b_p 2.06538229、c_p 4.72438340。
- 保証のない数値の表：`data/uncertified_axis_points.json`。計算に使ったのは、最初の三軸の地図の求積コード（`cotaxxxx/basepoint-geometry`、commit `f3170e6`、`diagnostics/triaxial_map_20261120/code`）。作る側のコードとは別の実装である。研究用 PC は使っていない（46 × 61 = 2,806 形、数分）。

ビルドは 2 つの入力の SHA-256 を照合してから書き出す。入力のコミットと SHA-256 は、画面の下にも出る。

論文の DOI と参照先（2026-11-27 に確定）：

- **DOI**：`doi:10.5281/zenodo.24581453`（Judge が Zenodo で予約したもの）。`template.html` の中の `foot1` の 2 か所（`T.en` の `foot1:` と `T.ja` の `foot1:`）に入れてあり、画面の下に出る。
- **論文の参照先コミット**：`ae8d73b5aefba2870ca6ded76eb53851c5cb4fdb`（枝 `evidence/triaxial-chat`、`manuscripts/paper-ii-v1.0/`。論文 v1.0 の最終版のソース）。`build_viewer.py` の `meta=dict(...)` の中の `paper=` の 1 か所で、HTML に埋め込まれるデータ（`DATA.meta.paper`）に入る。画面には出していない。
- 画面の下に出る入力のコミット（台帳の `862220c…`）は `build_viewer.py` の `LEDGER_COMMIT`、交点の裁定番号は同じ `meta` の `crossing_ruling` である。

## 作り直し方

```
sh viewer/make_viewer.sh          # リポジトリの根で。python3 -I、決定的
```

同じ入力からは、同じバイト列の HTML ができる（2 回ビルドして SHA-256 が一致することを確かめた）。

## ファイル

| ファイル | 中身 |
|---|---|
| `paper2_viewer.html` | 完成したビューア |
| `template.html` | 画面とスクリプトのひな形（データの差し込み口が 1 つ） |
| `build_viewer.py` | 台帳から HTML を作る。機械的な検査も行う |
| `uncertified_axis_table.py` | 保証のない数値の表を作る（任意の項目） |
| `data/strips_exact.json` | 抽出した帯と端点の区間（正確な有理数） |
| `data/uncertified_axis_points.json` | 保証のない数値の表 |
| `data/build_checks.json` | ビルドのときの検査の結果 |
| `checks/` | ブラウザでの検査、保証のない数値との突き合わせ、画面の写し |
| `CHECK_REPORT.md` | 検査の報告 |
| `LICENSE.md` | コードは MIT、文章は CC BY 4.0。第三者のコードは入っていない |
