# Dig への実行指示 v2：E2 系の参照の計算を研究 PC で流す

2026-11-23、Claude（通常監査）作成。Judge の承認（2026-11-23）による。
- 三軸の再開裁定：`7ce6f1e`。再開の理由：`9dfa228`。
- 取り下げた v1（`370b07d`）に代わる指示である。
- 守るもの：REDDS v1.0、DIG_PC_OPERATIONS_20261122 §1。

## 0. 何を流すか

- **計算：** Astra が書いた参照の計算。mpmath だけを使い、Reader は使わない。
  - 内訳は 88 組 × 2 精度（80 桁と 110 桁）で、計 176 本。
  - 計画は `276fc34`、chat の監査は `b81df96`。
  - 参照の条件（80 桁と 110 桁、最大次数 12、差 < 10⁻⁵⁵）は変えない。
- **コード：** chat は手を入れていない。束は作らず、evidence 枝の決まった commit から取り出す。
- **終わった分：**
  - 終わった 2 本（`reference_H_0_80.json`、`reference_H_1_80.json`）は、そのまま使う。
  - 途中まで進んだ 3 本（H_2_80、H_36_80、H_36_110）は、登録された途中の記録から再開する。

## 1. 準備

```bash
mkdir -p ~/e2ref && cd ~/e2ref
git clone --branch evidence/triaxial-chat https://github.com/cotaxxxx/bg-triaxial-family.git repo
cd repo && git checkout 9cba7f2c8ec99abbdf2e86ef5c79a2425199b03a
cd ~/e2ref
cp -r repo/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator work
mkdir -p work/inputs
cp repo/evidence/chat/2026-11-22/E3_INPUT_EQUATOR/E3_BOXES_PUBLIC.jsonl work/inputs/
cd work
sha256sum -c results/IMPLEMENTATION_SHA256SUMS.txt     # 全部 OK のときだけ先へ
sha256sum inputs/E3_BOXES_PUBLIC.jsonl                  # 183bc541…4a80 と一致すること
python3 -m venv ~/e2ref/venv && ~/e2ref/venv/bin/pip install mpmath==1.3.0   # この指示書で許可する追加はこれだけ
~/e2ref/venv/bin/python -c "import mpmath,sys; print(mpmath.__version__, mpmath.libmp.BACKEND, sys.version)" > ~/e2ref/env.txt
cd src
for c in H_2_80 H_36_80 H_36_110; do ~/e2ref/venv/bin/python restore_ref_checkpoints.py $c; done   # 登録された途中の記録を復元（SHA-256 と行数を検査する）
cd ..
```

- 照合や復元が一つでも合わなければ、流さずに報告する。
- gmpy2 は入れない。

`~/e2ref` が前回の準備で残っていたら、消さずに Judge に確かめる。v1 は実行していないので、残っていないはずである。

## 2. 実行（一度だけ）

```bash
cd ~/e2ref/work
nohup ~/e2ref/venv/bin/python src/run_references.py --workers 20 > ~/e2ref/run.log 2>&1 &
```

- **同時に流す本数は 20 本**で、変えない。研究 PC は 24 スレッドで、4 スレッドを残す。
- 空きメモリが 4 GiB を切ったら止めて報告する。
- 止まったときは、同じ命令を一度だけ流し直してよい。終わった本は飛ばし、途中の記録から続ける。二度目に止まったら、PARTIAL として登録し、報告する。
- ほかの重い計算とは重ねない。

## 3. 終わりの判定と登録

- `results/E2_REFERENCE_GATE.json` の `pairs` が 88 になったら終わり。`reference_gate` の値（PASS、STOP_REPORT、PENDING）は、解釈せずにそのまま報告する。
- 登録先は、evidence 枝の `evidence/dig/2026-11-2x/E2_REFERENCE_PC/`。次のものを置く。
  - `results/reference_*.json` と `*.error`（あれば）
  - `results/reference_comparisons.jsonl`
  - `results/E2_REFERENCE_GATE.json`
  - `~/e2ref/env.txt`
  - `~/e2ref/run.log`
  - これら全部の `SHA256SUMS.txt`
- Astra のフォルダ（`evidence/astra/…`）には書き込まない。
- 報告は、開始・終了（または停止）・登録の三回にする。報告に書くこと：
  - 時刻
  - 本数（176 本のうち何本）
  - gate の値
  - 登録 commit
- 結果の監査（包囲が参照を含むか）は chat が行う。
