# Dig への実行指示：E2 系の参照の計算を研究 PC で流す

2026-11-22、chat（Claude、監査担当）。Judge の判定（`2a963ac`）による。DIG_PC_OPERATIONS_20261122 の §1 に従う。

## 0. 何を流すか

- Astra が書いた参照の計算（mpmath だけを使う。Reader は使わない）。
- 内訳は 88 組 × 2 精度（80 桁と 110 桁）で、計 176 本。
- 計画は `276fc34` で、chat の監査は `b81df96`。
- コードには chat が手を入れていない。
- 束は作らない。evidence 枝から、決まった commit のファイルをそのまま取り出す。

## 1. 準備

```bash
mkdir -p ~/e2ref && cd ~/e2ref
git clone --branch evidence/triaxial-chat https://github.com/cotaxxxx/bg-triaxial-family.git repo
cd repo && git checkout <この指示書の commit>
cd ~/e2ref
cp -r repo/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator work
mkdir -p work/inputs
cp repo/evidence/chat/2026-11-22/E3_INPUT_EQUATOR/E3_BOXES_PUBLIC.jsonl work/inputs/
cd work
sha256sum -c results/IMPLEMENTATION_SHA256SUMS.txt     # 全部 OK のときだけ先へ
sha256sum inputs/E3_BOXES_PUBLIC.jsonl                  # 183bc541…4a80 と一致すること
python3 -m venv ~/e2ref/venv && ~/e2ref/venv/bin/pip install mpmath==1.3.0   # この指示書で許可する追加はこれだけ
~/e2ref/venv/bin/python -c "import mpmath,sys; print(mpmath.__version__, mpmath.libmp.BACKEND, sys.version)" > ~/e2ref/env.txt
```

- 照合が一つでも合わなければ、流さずに報告する。
- gmpy2 は入れない（数値の結果は変わらないが、条件をそろえるため）。

## 2. 実行（一度だけ）

```bash
cd ~/e2ref/work
nohup ~/e2ref/venv/bin/python src/run_references.py --workers 20 > ~/e2ref/run.log 2>&1 &
```

- **同時に流す本数は 20 本**で、変えない。研究 PC は 24 スレッドで、4 スレッドを残す。
- 一本ごとに数 GB は使わない見込み。空きメモリが 4 GiB を切ったら止めて報告する。
- 終わった本は飛ばし、緯度ごとの途中の記録から再開する作りになっている。止まったときは同じ命令を一度だけ流し直してよい。二度目に止まったら、PARTIAL として登録し、報告する。
- E4 とは重ねない。E4 の束は、まだ存在しない。

## 3. 終わりの判定と登録

- 終わったら、`results/E2_REFERENCE_GATE.json` の `pairs` が 88 になる。`reference_gate` の値（PASS、STOP_REPORT、PENDING）は、解釈せずにそのまま報告する。
- 登録先は `evidence/dig/2026-11-2x/E2_REFERENCE_PC/`。次のものを置く。
  - `results/reference_*.json` と `*.error`（あれば）
  - `results/reference_comparisons.jsonl`
  - `results/E2_REFERENCE_GATE.json`
  - `~/e2ref/env.txt`
  - `~/e2ref/run.log`
  - これら全部の `SHA256SUMS.txt`
- Astra のフォルダ（`evidence/astra/…`）には書き込まない。
- 報告するのは、開始・終了（または停止）・登録の三回。
- 報告に書くこと：
  - 開始と終了の時刻
  - 本数（176 本のうち何本）
  - gate の値
  - 登録 commit
