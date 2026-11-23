# 改訂角度核　研究 PC の区間側手順

2026-11-23、DIAGNOSTIC_ONLY。以下は Dig 用の事前登録。実行には改訂計画の commit、chat の差分監査、条件固定と実行許可を要する。E4 は別途 Judge の明示承認を要する。旧版の手順全文は b9b0483 の同名ファイルに残る。

差分監査の K1〜K3 を以下の手順に反映する。[chat 差分監査 §4（`049ce42`）](https://github.com/cotaxxxx/bg-triaxial-family/blob/049ce4281b5be59a22b4e05c430c4367c42de242/evidence/chat/2026-11-23/CHAT_AUDIT_EQUATOR_REVISION_2ad94b7.md#4-研究-pc-で流す前の条件)

## K2　開始順

Dig は、E2 の独立参照の計算が終了し、88 組（各 80 桁と 110 桁）の結果原本、実行記録、SHA-256 が GitHub に登録されたことを登録 commit で確認する。参照が実行中、未完、未登録の間は、以下の区間側 E1〜E3 を開始しない。E2 の参照 gate の扱いは試験計画 §§3–4 に従う。[E2 参照の実行指示（`5220d70`）](https://github.com/cotaxxxx/bg-triaxial-family/blob/5220d70c05201fa251f3ee8a48195243c014e1ad/evidence/chat/2026-11-23/DIG_RUN_E2_REFERENCE_PC_v2.md)

## K1　MPFR・GMP の開発用パッケージ

開始条件の確認後、Dig は研究 PC（Debian/Ubuntu 系）で次の確認を行い、出力を環境台帳に保存する。

```bash
dpkg-query -W -f='${binary:Package}\t${db:Status-Status}\t${Version}\n' libmpfr-dev libgmp-dev
gcc --version
```

両パッケージの状態が `installed` で、版を取得できることを確認する。欠けている場合は出力と `apt-get -s install --no-install-recommends libmpfr-dev libgmp-dev` が示す変更予定を報告し、ビルドと区間計算を止める。Judge が導入を個別に承認した後、Dig が次を実行し、上の確認を繰り返す。

```bash
sudo apt-get install --no-install-recommends libmpfr-dev libgmp-dev
```

APT が承認範囲外の変更を求めた場合は中断する。導入ができない場合も停止し、Judge に報告する。

両パッケージを確認したら、C コンパイラが正規の開発用ヘッダを読めることと GMP limb が 64 ビットであることを次で確認する。失敗時はエラーを保存して停止する。自作の ABI 宣言でのビルドは認めない。

```bash
printf '#include <gmp.h>\n#include <mpfr.h>\n#if GMP_LIMB_BITS != 64\n#error Expected 64-bit GMP limb\n#endif\n' |
  gcc -E -x c - >/dev/null
```

## 入力とビルド

1. Dig は監査を通った commit の equator ディレクトリを新規の作業先に置き、既存の参照計算・既存の結果とは別にする。新しい束の SHA-256、内部マニフェスト、ソース・計画・入力の固定 commit を照合する。入力は `c157cc661dab02ddd2b8936868f9ecad74a9e25f` の `evidence/chat/2026-11-22/E3_INPUT_EQUATOR/E3_BOXES_PUBLIC.jsonl` を `inputs/E3_BOXES_PUBLIC.jsonl` に置く。幾何の SHA-256 は計画 §4。研究 PC 上の参照ジョブとは重ねない。
2. 64-bit GMP limb、正規 MPFR ヘッダと同一環境のライブラリを使う。ビルドと実行は equator ディレクトリを作業場所とする。コンパイラ・GMP・MPFR・Python・CPU・OS・ビルドフラグ・各 SHA-256・開始終了時刻・実行ログを保存する。以下は区間側だけを扱う。

```bash
(
  set -e
  sha256sum -c SHA256SUMS.txt
  gcc -O2 -std=gnu17 -Wall -Wextra -Wno-enum-conversion -fno-fast-math \
    -Werror=implicit-function-declaration -Werror=incompatible-pointer-types \
    -Werror=int-conversion -include mpfr.h src/kernel.c -o kernel -lmpfr -lgmp
  ldd ./kernel
  sha256sum ./kernel
  python3 src/samples.py
)
```

ビルドや入力照合が失敗した場合、または `ldd` に未解決の共有ライブラリがある場合は、出力を保存し、実行に進まない。

## K3　区間側 E1〜E3 の所要時間と停止条件

旧核の 311 積分は、128・512・2,048 面までの 1 積分の実測が中央値 10.79 秒、最大 33.09 秒で、並行した個別の経過秒の合計は 3,559.75 秒だった。旧実行と同じ 6 並列、研究 PC の各ワーカーが旧作業機と同程度の速度と仮定し、全積分に内部パネルの評価回数比 5 を掛けると、`3,559.75 × 5 ÷ 6 ≈ 2,966 秒`（約 49 分 26 秒）となる。接触では回数比は 1。**運用上の目安は約 50 分**とする。研究 PC での実測前の換算値であり、機種差、並列効率、準備や集計の時間で増減する。[旧核の集計](https://github.com/cotaxxxx/bg-triaxial-family/blob/049ce4281b5be59a22b4e05c430c4367c42de242/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/results/INTERVAL_RUN_SUMMARY.json) · [旧実行の環境](https://github.com/cotaxxxx/bg-triaxial-family/blob/f01879d/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/results/ENVIRONMENT.json)

区間側は一度だけ実行する。開始から **6,000 秒（100 分）** で終了していなければ、そのジョブに TERM を送り、30 秒後も実行中なら KILL を送る。Dig は停止後にそのジョブの子プロセスも終了したことを確認する。

```bash
(
  set -C
  {
    printf 'started_at=%s\n' "$(date -Is)"
    run_status=0
    timeout --verbose --signal=TERM --kill-after=30s 6000s \
      python3 src/run_intervals.py --workers 6 || run_status=$?
    printf 'finished_at=%s\nexit_status=%s\n' "$(date -Is)" "$run_status"
    exit "$run_status"
  } > interval-run.log 2>&1
)
```

締切による停止（通常は終了コード 124、KILL の場合は 137）や実行障害は PARTIAL として扱う。確定済みの積分キャッシュとログをそのまま保全し、開始・停止時刻、経過秒、終了コード、完了件数（全 311 件中）と失敗箇所を chat と Judge に報告する。再実行は Judge の判断を待つ。

この時間の目安と停止条件は区間側 E1〜E3 に適用する。E4 の予算と開始条件は試験計画 §5 に従う。

## 出力の保全と照合

1. E1、E2 区間72点、Hₐₐ 8点、E2c 8点と4箱、E3 92件で共通する積分は一度だけ計算する。各積分内の順序は並列数に依存しない。改訂の出力は `results/revision_20261123/<kernel SHA-256>/` 以下。キャッシュはさらに `integrals/` 以下にあり、命令・段階・秒数と核の SHA を記録する。必須積分が欠けている場合、集計は PARTIAL として停止する。実行終了後、完全な集計原本とキャッシュのマニフェスト・SHA-256 を採取し、Dig が新しい結果として登録する。旧結果を置換しない。
2. E2 の独立参照は既存の指示 5220d70 の88組×2精度を使う。新たに参照を起動しない。元の参照 gate を改訂結果として流用しない。新しい区間と既存参照原本の照合・E3 の公開値との非盲検照合は計画 §§3–4 に従って chat が行う。E4 の8組・予算・個別承認は計画 §5 に従う。
