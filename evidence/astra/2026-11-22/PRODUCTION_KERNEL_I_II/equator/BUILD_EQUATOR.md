# 改訂角度核　研究 PC の区間側手順

2026-11-23、DIAGNOSTIC_ONLY。以下は Dig 用の事前登録。実行には改訂計画の commit、chat の差分監査、条件固定と実行許可を要する。E4 は別途 Judge の明示承認を要する。旧版の手順全文は b9b0483 の同名ファイルに残る。

1. Dig は監査を通った commit の equator ディレクトリを新規の作業先に置き、既存の参照計算・既存の結果とは別にする。新しい束の SHA-256、内部マニフェスト、ソース・計画・入力の固定 commit を照合する。入力は `c157cc661dab02ddd2b8936868f9ecad74a9e25f` の `evidence/chat/2026-11-22/E3_INPUT_EQUATOR/E3_BOXES_PUBLIC.jsonl` を `inputs/E3_BOXES_PUBLIC.jsonl` に置く。幾何の SHA-256 は計画 §4。研究 PC 上の参照ジョブとは重ねない。
2. 64-bit GMP limb、正規 MPFR ヘッダと同一環境のライブラリを使う。ビルドと実行は equator ディレクトリを作業場所とする。コンパイラ・GMP・MPFR・Python・CPU・OS・ビルドフラグ・各 SHA-256・開始終了時刻・実行ログを保存する。以下は区間側だけを扱う。

```sh
sha256sum -c SHA256SUMS.txt
gcc -O2 -std=gnu17 -Wall -Wextra -Wno-enum-conversion -fno-fast-math \
  -Werror=implicit-function-declaration -Werror=incompatible-pointer-types \
  -Werror=int-conversion -include mpfr.h src/kernel.c -o kernel -lmpfr -lgmp
ldd ./kernel
sha256sum ./kernel
python3 src/samples.py
python3 src/run_intervals.py --workers 6
```

3. E1、E2 区間72点、Hₐₐ 8点、E2c 8点と4箱、E3 92件で共通する積分は一度だけ計算する。各積分内の順序は並列数に依存しない。改訂の出力は `results/revision_20261123/<kernel SHA-256>/` 以下。キャッシュはさらに `integrals/` 以下にあり、命令・段階・秒数と核の SHA を記録する。必須積分が欠けている場合、集計は PARTIAL として停止する。実行終了後、完全な集計原本とキャッシュのマニフェスト・SHA-256 を採取し、Dig が新しい結果として登録する。旧結果を置換しない。
4. E2 の独立参照は既存の指示 5220d70 の88組×2精度を使う。新たに参照を起動しない。元の参照 gate を改訂結果として流用しない。新しい区間と既存参照原本の照合・E3 の公開値との非盲検照合は計画 §§3–4 に従って chat が行う。E4 の8組・予算・個別承認は計画 §5 に従う。
