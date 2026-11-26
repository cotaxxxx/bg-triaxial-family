# 論文 II｜局所対応条件の実行用の束

2026-11-27 JST · DIAGNOSTIC_ONLY · chat 監査前

[PLAN](PLAN.md) と [DERIVATION](DERIVATION.md) を固定した後の束。chat が式、形の台帳とコードへ差分監査を行う。Judge の実行承認後に以下を Dig が研究PCで行う。

## 準備

1. `PAPER_II_CORRESPONDENCE_PC_BUNDLE.tar.gz` と同名の `.sha256` を照合し、新規のディレクトリに展開する。展開先で `sha256sum -c SHA256SUMS.txt` を実行する。
2. `V2_RESULT`、`V3_RESULT`、`V4_RESULT` に、それぞれ `862220c`、`7c6cd7e`、`f58ca0c` の研究PC上の `RESULT/` を指定する。ランナーと検査器は出発時に、それぞれの全ファイルを固定の SHA-256 と照合する。結果出力は別の新規ディレクトリとする。
3. `bash build.sh` で libmpfr-dev と libgmp-dev の導入状態、実ヘッダとライブラリの版、64ビット GMP limb を確認してビルドする。開発用パッケージが欠けた場合は K1 ログと `apt-get -s install --no-install-recommends libmpfr-dev libgmp-dev` の予定を報告し、Judge の導入承認を待つ。Python 3.10以上と、候補Bと同じコンパイラフラグを使う。

## 実行と検収

以下の最初の三つの SHA はそれぞれ別の40桁のコミット。中断には `SIGTERM` または `Ctrl+C` を用いる。単一プロセスの数値核が新しいセルの開始前に停止指示を読む。数値評価は7,200秒または240万セル。続く有理数の検査にも300秒の上限を設けた。

```sh
bash build.sh
python3 -B run_correspondence.py \
    --bundle-commit BUNDLE_SHA \
    --chat-audit CHAT_AUDIT_SHA \
    --judge-execution EXECUTION_APPROVAL_SHA \
    --v2 V2_RESULT --v3 V3_RESULT --v4 V4_RESULT \
    NEW_OUTPUT_DIRECTORY
```

| 台帳 | 内容 |
|---|---|
| `work/integrals.jsonl` | 核の区間端点、形箱、量・微分・段階、式の評価回数 |
| `work/boxes.jsonl` | 帯ID、継承した横断微分、子箱の形、符号と試行の結果 |
| `work/intersections.jsonl` | 未決箱での端の符号、弧上の微分、Krawczyk逆行列・像と縮小率 |
| `SHARED_ENDPOINTS.json` | 固定した $c_p,b_p$ の辺根箱と参照ID |
| `LEDGER_INSPECTION.json` | 読み直した符号、局所例外の位置、未決・未訪問の箱 |
| `RUN.json`、`MANIFEST.json`、`RESULT_SHA256SUMS.txt` | 実行条件、停止の理由、原本と生成物の照合 |

```sh
(cd NEW_OUTPUT_DIRECTORY && sha256sum -c RESULT_SHA256SUMS.txt)
python3 -I -B verify_correspondence.py V2_RESULT V3_RESULT V4_RESULT NEW_OUTPUT_DIRECTORY
```

実行・停止後は封印した結果全体と外側のログを保存する。数学的な採否は chat の結果監査後に Judge が行う。

## 事前確認

`python3 -B smoke.py` は人工の符号変化、Krawczyk と台帳の改変拒否を調べる。ビルド後に `--library build/correspondence_kernel.so` を加えると球の解析値10項目も照合する。[確認記録](SMOKE.txt) · [生成の差分](GENERATED_KERNEL.patch)
