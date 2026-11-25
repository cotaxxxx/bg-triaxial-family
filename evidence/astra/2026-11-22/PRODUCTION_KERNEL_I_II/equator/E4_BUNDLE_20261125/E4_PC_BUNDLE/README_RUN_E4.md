# E4 研究PC用手順

2026-11-25。DIAGNOSTIC_ONLY。対象は `PLAN_TESTS_EQUATOR.md` §5 の赤道帯の8組。束の作成承認は `66afe3ad4c0d76442370df49174077f601733c6c`、改訂核の E1〜E3 の監査は `1b7c758bcf529dab5867467d16987b60d5ba6558`。固定した計画・導出・旧手順の写しを同梱した。

## 1　開始条件

Dig は、同じ SHA-256 の束に対する chat の監査と、Judge の E4 実行承認の両方を確認し、各コミット SHA を記録する。研究PCを単独稼働にし、既存の計算の終了、8ワーカー分のCPUと利用可能メモリを確かめる。8本同時が運用条件に合わなければ、開始せずに報告する。較正とE4を順に各一度だけ実施する。

束と隣接する SHA-256 ファイルを同じ場所に置く。新しい作業ディレクトリで展開し、どちらかの照合が失敗したら停止する。

```bash
sha256sum -c E4_PC_BUNDLE_20261125.tar.gz.sha256
tar -xzf E4_PC_BUNDLE_20261125.tar.gz
cd E4_PC_BUNDLE
sha256sum -c MANIFEST.sha256
python3 -B src/run_e4.py --check-inputs
bash build.sh
```

`build.sh` は `libmpfr-dev`、`libgmp-dev`、正規のヘッダ、64ビットのGMP limbを確認する。不足時は変更予定を報告して停止し、Judge が導入を承認した場合に限り `BUILD_EQUATOR.md` の K1 に従う。コンパイル、リンク、実行ファイルの SHA-256 のいずれかに異常があれば停止する。環境・フラグ・リンクされたライブラリ・MPFR/GMPのヘッダと実行時の版は `build/ENVIRONMENT.txt` に残る。

## 2　V60による時間換算

Dig は運用側が管理する固定済みの V60 参照 bench を、コールド開始で8本同時に一度測る。各本は同じ h33、w3 の二評価を行う。各起動の出力を `bench_1.log` から `bench_8.log` に保存する。コマンドと作業場所は Dig が確認した V60 のものを使う。この束の収集器は、同じコマンドを8個の新しいプロセスで起動し、各ログのSHA-256と終了状態を記録する。

```bash
python3 -B src/bench_e4.py capture --cwd "$E4_V60_WORKDIR" "$E4_BENCH_DIR" -- \
  "$E4_V60_PYTHON" -B "$E4_V60_WORKDIR/bench_v60.py"
```

Dig は `BENCH_RECEIPT.template.json` から `$E4_BENCH_DIR/receipt.json` を作る。8本それぞれについて V60 と同じ定義で計った二評価分の合計秒を `v60_seconds` に記録する。収集器の `outer_wall_ns` は起動と終了を含む運用記録である。h33、w3 の区間端点が既定の参照と binary64 のビットまで一致したこと、およびその照合記録を記入する。ログ、時刻、秒数または端点の照合が欠ける場合は Dig が停止し報告する。[V60の較正計画](https://github.com/cotaxxxx/bg-triaxial-family/blob/c25ba7bc2b044356896e948f6201f8ade77eb06d/calibration/V60/input/unpacked/v60/PLAN_V60.md)

```bash
python3 -B src/bench_e4.py budget "$E4_BENCH_DIR"
```

予算は各組につき研究PCの単調壁時計で **B = 14,400 × m / 45.1 秒**。m は8個の秒数を昇順に並べた中央2個の算術平均。換算係数と B は有理数で保存する。時間の目安は8本同時で各組 B までに加え、準備・較正・終了時の保存に要する時間である。たとえば m が45.1秒なら各組の上限は4時間。実際の m は当日の較正で決まる。

## 3　八組の一回実行

`E4_BUNDLE_AUDIT` と `E4_JUDGE_RUN_APPROVAL` は上で確認した二つの完全なコミット SHA。入力することで実行記録に両者を残す。出力ディレクトリは新規のパスを指定する。

```bash
python3 -B src/run_e4.py --bench "$E4_BENCH_DIR" --output "$E4_RESULT_DIR" \
  --bundle-audit "$E4_BUNDLE_AUDIT" \
  --judge-execution-approval "$E4_JUDGE_RUN_APPROVAL"
```

- 固定の8組を各1ワーカーに1組ずつ割り当て、揃ってから開始する。各組の時計を根評価の直前に開始する。128、512、2,048面の同一段階で全積分を組み立て、段階間の共通部分を取る。正下端で葉とし、上端が0以下ならその組の入力・区間を保存して `NONPOSITIVE` と報告する。
- 最終段階で符号未決の場合は、現在幅／根幅が最大の方向を厳密な中点で二分する。同率は `s,t,q1,q2,a` の順。下半分を先に処理する。深さ40で打ち切る非空の箱を残し、その組を `UNRESOLVED` とする。接触用の事前位置分割では位置3方向だけを比較する。指定8根は有理数のまま球の内部と確認する。
- Bに達した組では新しい評価を開始せず、実行中の積分を停止する。途中の段階は判定に使わず、該当箱と残る兄弟を未処理台帳に戻す。途中評価には `MISSING_PARTIAL` と記録する。子プロセスを回収し、締切からの経過と保存時間を別欄に残す。空の交差は `INCONSISTENT`、資源不足・不完全な出力・運用上の停止は `PARTIAL` として入力、ログと途中結果を保全する。必要な中断は Dig が実行親プロセスに TERM を送り、終了後に子プロセスの終了を確認する。
- すべての葉の下端が厳密に正で、厳密な二分割による被覆と未処理箱ゼロを検査した場合に `COVERED` とする。障害の記録を保持し、同じ出力先で再実行しない。

`stage_io.so` は固定の核が標準出力を `fflush` した直後に、次段階の許可を待つ。各組で一度に演算する核は一つとし、積分ごとの角度木を段階間で保持する。読み終えた子は終了を待って回収する。I/O待ちのライブラリは核のソース・コンパイルフラグ・区間演算から独立のファイルであり、実行ファイルと別にSHA-256を記録する。

## 4　結果の照合と登録

```bash
python3 -B src/check_e4.py "$E4_RESULT_DIR"
(cd "$E4_RESULT_DIR" && sha256sum -c RESULT_SHA256SUMS.txt)
```

組ごとの `r2.jsonl` に整数の二分割経路、深さ、段階、根・子の正確な端点、決定とその計数を置く。R2 の `parameter_widths` は `s,t,q1,q2,a` の順の5幅、`angle_width` は中心の積分幅。各 `I0`・`I_*` に積分幅、旧基本葉と小矩形側それぞれの上向きのΣ2R、自然区間だけのセルの有無を置く。これらは中心式の交差前に計測する。`intersection_width` に交差後の幅を置く。零幅で省いた方向は明記する。接触経路は `NOT_APPLICABLE` とし、球冠と外側の区間を別々に記録する。

`partition.jsonl` は二分割・端点・受理葉の台帳。`leaves.jsonl` と `pending.jsonl` はそこから厳密有理数で復元する。途中の評価番号、確定済みの積分とその評価回数は記録し、核が段階行を出す前に中断した回数は不明として扱う。各組の `summary.json` と全体の `SUMMARY.json` に完走、葉、評価、異なる箱、未処理箱、最大深さ、最小下端、核のパネル・求積点回数、CPU・壁時計・換算秒、最大RSS、葉台帳SHA-256を記録する。メモリは単一プロセスのOS高水位と、各組のプロセス合計RSSの標本最大を区別して記録する。後者には共有メモリの重複があり、連続時間での上界ではない。

Dig は開始・終了時刻、8組の状態、実行環境、較正原本、結果原本、SHA-256 を、実行承認で定める新しい保存先へ登録する。台帳検査に失敗した組・失われた集計があれば、元のログを保全して chat と Judge に報告する。チャット側が監査し、次工程への扱いは Judge が判断する。

## 5　人工入力での短い確認

`python3 -B tests/smoke_e4.py` は人工の時間記録と二分割を検査する。ビルド済み核での人工点・小箱の確認は `python3 -B tests/smoke_e4.py --kernel build/kernel --stage-io build/stage_io.so` とする。8組の実入力とV60の bench 入力は使用しない。
