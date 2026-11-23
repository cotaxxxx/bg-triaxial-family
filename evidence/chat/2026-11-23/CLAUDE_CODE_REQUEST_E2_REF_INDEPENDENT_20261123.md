# Claude Code（特別監査）への依頼書：E2 系の参照値の独立検算

2026-11-23、Claude（通常監査）作成。Judge（古田勝士）の承認（2026-11-23）による。
状態：**DIAGNOSTIC_ONLY**（監査のための検算。数学的な採否は Judge が決める）。
守るもの：REDDS v1.0（`64115f7`）、GeoEnclosure Standard v1.1 の第三原則（作った人とは別の式、別のコードで確かめる）。

---

## 0. なぜ頼むか

赤道の帯の試験 E2・Hₐₐ・E2c では、Astra の包囲が「高精度の参照値」を含むかで合否を決める。いま研究 PC で、その参照値 176 本を流している（実行指示 `5220d70`）。

ところが、**包囲のコードと参照のコードは、どちらも Astra が書いた**。参照の式の組み立てに誤りがあれば、包囲と参照が同じ誤りを共有し、E2 は誤って合格しうる。そこで、参照値の一部を、Astra のコードを見ていない Claude Code が、別の式と別のコードで作り直し、突き合わせる。

## 1. 対象（種で固定。結果を見てから変えない）

選び方：ASCII の `20261123|REFIND|` に ID を連結し、SHA-256 の生のバイト列で昇順に並べる。同じ値なら ID の昇順。

| 量 | ID | 選び方 | 点 |
|---|---|---|---|
| H₃₃ | V62_10、V62_0 | V62 の 72 点から、タイルごとに先頭 2 点 | タイル (0,0) |
| H₃₃ | V62_24、V62_32 | 同上 | タイル (1,3) |
| H₃₃ | V62_51、V62_48 | 同上 | タイル (2,5) |
| H₃₃ | V62_69、V62_56 | 同上 | タイル (3,7) |
| Hₐₐ（q₃ による 4 階微分） | V62_42、V62_8 | 計画の Hₐₐ の 8 点（11、62、60、8、53、29、42、43）から先頭 2 点（ID は `Haa_V62_i`） | |
| E2c の点 | E2c_point_7、E2c_point_2 | E2c の 8 点から先頭 2 点（ID は `E2c_point_k`） | 縁の近く |

- V62 の点の座標 (s, t, q₁, q₂, q₃) は、`evidence/chat/2026-11-22/D_TRI_H33_EQUATOR_DIAG_V62/out_A.jsonl` の `p` を正確な有理数として使う。
- E2c の点の定義（セル、h の値、|q|² の条件）は、計画 `evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/PLAN_TESTS_EQUATOR.md`（`276fc34`）の R3 の節にある。

## 2. 量の定義（ここから自分で導く）

- L = diag(1, s, st)。エネルギーは E(q) = ⟨k arccos²γ⟩（単位球面上の平均）。
- 定義の出典：
  - `bg-triaxial-family` の main 枝、`evidence/source-snapshots/basepoint-v56-independent-map/REPORT.md` §1
  - V58 の計画 `evidence/chat-originals/2026-11-20/D_TRI_LAYER_I_II_CALIBRATION_V58/chat_checks/PLAN_V58.md`
- H₃₃ = ∂²E/∂q₃²、Hₐₐ = ∂⁴E/∂q₃⁴。どちらも点での値。
- 表示、微分のしかた（解析的な微分、複素ステップ、差分など）、積分の方法は自由に選んでよい。**Astra の式（下の §3 の禁止物）とは別の組み立てにすること**。選んだ方法と理由を `METHOD.md` に書く。

## 3. 独立性（開いてはいけないもの）

次のものは、自分の値の SHA-256 を登録するまで開かない。

- Astra の equator フォルダの `src/`、`results/reference_*.json`、`results/checkpoints/`、`DERIVATION.md`、`DESIGN_EQUATOR.md`
- Dig の研究 PC の結果（`evidence/dig/…/E2_REFERENCE_PC/`）
- Astra の区間の結果（`results/*_stages.jsonl`、`E3_ASTRA_ENDPOINTS.jsonl`）

読んでよいもの：
- §2 の定義の出典
- 計画 `PLAN_TESTS_EQUATOR.md`（点の定義と合否の条件のため）
- V62 の `out_A.jsonl`。Reader の値が載っているが、それを答えとして使わないこと。

Reader のコードを以前に読んでいることは構わない（Astra から独立していればよい）。開いてしまったら、その時点で止めて報告する。

## 4. 精度と自己検査（流す前に固定）

- 各点で、二つの作業精度（例：50 桁と 70 桁）で計算し、**差 < 10⁻³⁰** であること。届かない点は `UNRESOLVED` と記録し、値の照合には使わない。
- 積分の誤差の目安（使った方法の推定誤差）も記録する。

## 5. 計算の場所（Judge の決定）

- Claude Code の作業機でするのは、コードを書くことと、**短い確認**（1 点を低い精度で、数分以内）だけ。
- 12 本の本計算は、**束にして研究 PC で Dig が流す**。束には次のものを入れる。
  - コード
  - 入力
  - 実行の手順書（Python の版、並列の数、止める条件）
  - `MANIFEST.sha256`
- 束は chat が監査してから Dig に渡す。
- 研究 PC はいま E2 の参照（20 本同時）を流しているので、**それが終わってから**流す（一度に一つの束）。
- 研究 PC の Python は、標準が 3.14、ほかに 3.11 と 3.13 がある。venv は使えない（ensurepip がない）。追加のパッケージは、SHA-256 を照合したファイルを `~/…/lib` に展開する形にする。

## 6. 登録と照合の順

1. Claude Code が、コード、`METHOD.md`、手順書を、枝 `claude/e2-ref-independent-20261123` の `evidence/claude-code/2026-11-23/E2_REF_INDEPENDENT/` に commit する（流す前）。
2. chat が束を監査し、Dig が研究 PC で流して、結果を同じ枝に登録する。
3. Claude Code（または Dig）が、結果のファイル `INDEP_VALUES.jsonl` の SHA-256 を登録する。各行には次の欄を置く：ID、量、二つの精度の値（十進の文字列）、差、誤差の目安、状態。
4. そのあとで chat が、研究 PC の Astra の参照値（110 桁）と突き合わせる。
   - **一致の条件：** |Claude Code の値 − Astra の参照値| < 10⁻²⁵。
   - 一つでも外れたら `DISAGREE` として、E2 の判定を止め、Judge に報告する。
   - 一致したら、Astra の包囲がこの独立の値も含むかを、あわせて確かめる。

## 7. 報告

- 書くこと：
  - 対象 12 点の状態の表
  - 方法の要約
  - 開いてはいけないものを開いていないことの自己申告
  - 束と結果の SHA-256
- 数学的な採否は書かない。
- AI 利用の記録：この検算は Claude Code（Anthropic）が行い、Claude（chat）が監査し、採否は Judge が決める。
