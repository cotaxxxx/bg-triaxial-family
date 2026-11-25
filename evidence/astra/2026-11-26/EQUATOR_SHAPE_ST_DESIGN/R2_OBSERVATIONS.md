# E4 R2 台帳における形状方向の幅

2026-11-26 JST · DIAGNOSTIC_ONLY · 既存台帳の集計

固定コミット 981adf59bca9af50e70d57d4096d63b8aa1523d6 の E4 結果原本から、八組の `cases/<ID>/r2.jsonl` を読んだ。八ファイルの SHA-256 は原本の一覧と一致した。[固定結果ディレクトリ](https://github.com/cotaxxxx/bg-triaxial-family/tree/981adf59bca9af50e70d57d4096d63b8aa1523d6/evidence/dig/2026-11-26/E4_PC_RESULT/E4_RESULT) · [原本の SHA-256](https://github.com/cotaxxxx/bg-triaxial-family/blob/981adf59bca9af50e70d57d4096d63b8aa1523d6/evidence/dig/2026-11-26/E4_PC_RESULT/E4_RESULT/RESULT_SHA256SUMS.txt)

## 集計の範囲

- 1,779 行のうち `evaluation=COMPLETE` かつ `R2.status=MEASURED` の 1,771 行を集計した。各組の計算時間打ち切り時の未完行 1 行、計 8 行には値を補わなかった。
- 主集計はそのうち `panels=2048` かつ `decision=SPLIT` の 345 行である。各行は最終段階で得た包囲が零を含み、その次にパラメータ箱を二分割した親箱を表す。八組とも内部箱だった。異なる角度段階を同じ箱について重ねて数えていない。
- $w_s,w_t,w_{q_1},w_{q_2},w_a$ は `R2.parameter_widths`、$w_0$ は中心値の `R2.angle_width`。比率は $R=(w_s+w_t)/(w_s+w_t+w_{q_1}+w_{q_2}+w_a+w_0)$。分子、分母を各行から求めたうえで中央値をとる。幅の列は個別の中央値である。

| 組 ID | 完了行 | 最終段階の分割箱 | $w_s$ | $w_t$ | $w_{q_1}$ | $w_{q_2}$ | $w_a$ | $w_0$ | $R$ の中央値 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| (0,0,27,7,0) | 254 | 56 | 2.109 | 1.978 | 0.06387 | 0.04587 | 0.1284 | 0.00009937 | 92.52% |
| (1,3,27,7,0) | 250 | 52 | 5.624 | 3.188 | 0.08010 | 0.1192 | 0.9398 | 0.001106 | 82.98% |
| (2,5,0,23,0) | 202 | 37 | 2.568 | 1.337 | 0.03420 | 0.07790 | 1.287 | 0.004032 | 81.42% |
| (2,5,27,7,0) | 258 | 53 | 2.406 | 1.465 | 0.03817 | 0.06830 | 1.328 | 0.005501 | 81.59% |
| (3,7,0,23,0) | 203 | 36 | 1.272 | 0.6733 | 0.02090 | 0.09049 | 0.8559 | 0.008406 | 67.02% |
| (3,7,4,15,0) | 202 | 37 | 1.299 | 0.7293 | 0.02274 | 0.09223 | 0.8779 | 0.006542 | 67.74% |
| (3,7,10,0,0) | 202 | 37 | 1.322 | 0.7505 | 0.02408 | 0.09134 | 0.8952 | 0.005705 | 67.84% |
| (3,7,27,7,0) | 200 | 37 | 1.347 | 0.7726 | 0.02412 | 0.08709 | 0.9244 | 0.01148 | 67.58% |
| 全体 | 1771 | 345 |  |  |  |  |  |  | **75.71%** |

345 箱すべてで、六つの幅の最大値に $w_s$ または $w_t$ が達した。$R$ の最小は 65.17%。両形状方向の導関数区間が零を含むのは 345 箱すべてであり、全完了行を同じように数えると 1,771 / 1,771 行だった。

## 再集計の手順

台帳の二進有理数 `[m,e]` は $m2^e$。下端と上端の符号は指数に依存しないため、導関数の零包含は仮数の整数比較で決まる。幅と比率は二進有理数から求め、上表では末尾を丸めた。集計の中心部分を以下に示す。`rows` は原本の各行を JSON として読んだものとする。

```python
from fractions import Fraction

def dyadic(pair):
    mantissa, exponent = pair
    return int(mantissa) * Fraction(2) ** exponent

def contains_zero(name, row):
    lower, upper = row["integrals"][name]["interval"]
    return int(lower[0]) <= 0 <= int(upper[0])

complete = [
    row for row in rows
    if row["evaluation"] == "COMPLETE" and row["R2"]["status"] == "MEASURED"
]
splits = [
    row for row in complete
    if row["panels"] == 2048 and row["decision"] == "SPLIT"
]
share = []
for row in splits:
    ledger = row["R2"]
    assert ledger["axis_order"] == ["s", "t", "q1", "q2", "a"]
    shape_and_position = list(map(dyadic, ledger["parameter_widths"]))
    widths = shape_and_position + [dyadic(ledger["angle_width"])]
    share.append(sum(widths[:2]) / sum(widths))
    assert max(widths[:2]) == max(widths)
    assert contains_zero("I_s", row) and contains_zero("I_t", row)
```

これらは交差前の中心式で使った幅である。$w_0$ は中心値の角度積分の幅であり、各導関数積分の求積誤差は別に評価する必要がある。形状方向の幅の比率が大きいという観察から、真の勾配の単調性、新設計の曲率包囲の幅、最終的な符号判定数は決まらない。
