# 候補 B 実行用の束

2026-11-26 JST · DIAGNOSTIC_ONLY · chat コード監査待ち

形の範囲は $R=[1/4,1]\times[1,7]$。中間軸 $x=1$、短軸 $y$、長軸 $z$ とする。Z1 と D1 を短軸、Z2 と D2 を中間軸に対応させる。箱、境界で照合する有理端点、八つのパイロット箱、予算は `INPUTS.json` に固定した。計画と導出は登録済みの版を参照する。[承認書 a17d23e](https://github.com/cotaxxxx/bg-triaxial-family/blob/a17d23e9d001a7716ae8cbb663eb377b58c23152/evidence/chat/2026-11-26/ASTRA_SCOPE_CANDIDATE_B_BUNDLE_20261126.md) · [計画と導出 f8c809f](https://github.com/cotaxxxx/bg-triaxial-family/tree/f8c809f2e2cfdc32da04aba120e7e8fd1001de7e/evidence/astra/2026-11-26/CANDIDATE_B_PLAN) · [計画監査 6349d6d](https://github.com/cotaxxxx/bg-triaxial-family/blob/6349d6dcb944ec15e48d66bb1e9302305b44d9d7/evidence/chat/2026-11-26/CHAT_AUDIT_CANDIDATE_B_PLAN_f8c809f.md)

回転辺での $a_c,h_c,B_o,h_b$ と閾値の引用は第一論文 v1.0 による。本文に使う狭い区間は引用値とし、候補 B の計算では計画の広い端点での符号と辺の根の全数を照合する。[第一論文 v1.0](https://doi.org/10.5281/zenodo.24495446)

## 1. 束の照合と K1

以下は chat の束の監査と Judge の別の実行承認の後、Dig が研究 PC で行う手順。承認コミットと束の登録コミットを確認して記録する。

1. 届いた `CANDIDATE_B_PC_BUNDLE.tar.gz` を同名の `.sha256` と照合する。空の作業ディレクトリに展開し、展開先に移って `sha256sum -c SHA256SUMS.txt` を実行する。`MANIFEST.json` には入力・コードの SHA-256 と、計画・承認・監査の固定コミットが入っている。
2. `bash build.sh` を行う。K1 は `dpkg-query` で `libmpfr-dev` と `libgmp-dev` の状態と版を調べる。開発用パッケージが欠けていれば、K1 のログと `apt-get -s install --no-install-recommends libmpfr-dev libgmp-dev` の変更予定を報告して止める。実際の導入は Judge の別承認を受けてから行い、K1 を繰り返す。
3. 正式な `mpfr.h` を `-include mpfr.h` で強制し、`-lmpfr -lgmp` でリンクする。実ヘッダとリンク先の版、GMP の 64 ビット limb、MPFR 4.2 以上を検査する。ビルドは `-O2 -fno-fast-math -ffp-contract=off`。Python 3.10 以降の標準ライブラリを使う。`build/K1.log`、`build/compile.log`、`build/BUILD.json` を保全する。

## 2. パイロット、本走と停止

研究 PC のシェルで、監査を受けた束と実行承認の完全なコミット SHA を記録してから一回だけ起動する。`tmux` などで端末を保全し、空の出力先を指定する。下の大文字は実際の Git SHA と出力パスに置き換える。

```sh
python3 -B run_candidate_b.py \
    --bundle-commit BUNDLE_GIT_SHA \
    --judge-execution JUDGE_EXECUTION_GIT_SHA \
    NEW_OUTPUT_DIRECTORY
```

- 先に P0〜P7 で四量の値と二つの一次形微分を 64、256 セルまで求める。パイロットの開始から 30 分で打ち切る。球で解析値の包含を要する。測定した各セルの時間から 90 パーセンタイルを計算し、300 万セルを実効 3 コア相当で流す見積もりが 5 時間以下の場合だけ、同じ起動の中で本走に進む。
- 最大四プロセスで、親が Z1、三つの子が Z2・D1・D2 を担当する。各量の上限は 90 万セル公式評価。パイロットと交差・組立の予算を合わせて 40 万とし、全量合計 400 万を超えない。本走は計画の 64、256、1,024 段階と境界の追加評価を用いる。セル数は取り除いた親も含む。独立した台帳検査は計算の子をすべて回収してから行う。
- 全体の計算と台帳検査の上限は起動から 6 時間。外部からの停止は起動した親 PID へ `SIGTERM` または `Ctrl+C`。共有された停止フラグを角度セルの開始前にも確認し、評価中はそのセルを抜けてから停止する。未完成の角度段階は有効区間として出さない。角度木の内部と形の木の両方で、部分評価による箱の除外を防ぐ。
- 停止後は全子プロセスの終了を確認し、台帳・未処理の形箱、次に行うべき段階、実行時の SHA-256 を整理する。停止後の保全には数学計算を含めない。出力先に既存のディレクトリがあれば起動時に止める。

## 3. 算術と監査の対応

| ファイル | 監査箇所 |
|---|---|
| `src/interval.h`、`src/jets.h` | 既存の Astra 角度核の区間端点、Taylor 係数、級数の剰余。128・256 ビットと $F'$、$F''$ の合成に対応。データ束の `MANIFEST.json` に元ファイルの Git blob を記録 |
| `src/candidate.c` | 中心の式 (1) と (3)、極点の式 (5)–(6)、二節点と符号付き四階剰余 (7)。形微分は Taylor の一次係数。回転辺での一次元化は辺に沿う微分まで |
| `engine.py` | 段階の継続、直接と平均値の交差、有理端点の外向き丸め、式を再構成できる参照 ID |
| `shape.py` | 四辺と全形箱。符号、三条件を満たす帯、共通線分による帯・端点の接続 |
| `crossings.py` | 六組の比較。必要なら同じ三条件を満たす比較用補助帯を作り、傾き差、端点での順序、両者の根の重なりを照合。補助帯の回数は量ごとの帯上限に含める |
| `verify_ledgers.py` | 計算モジュールの import なし。量と座標の対応、有理端点での平均値式、初期箱と子の被覆、符号、帯の三条件、共通線分、傾き差と二分、全重なりの処理を再判定 |

二進有理端点は `{"n":"整数","e":指数}` の $n2^e$。非二進有理端点は `{"n":"整数","d":"正整数"}` の $n/d$。形箱の順は $y$ 下端・上端、$z$ 下端・上端で、正方形の積分変数は中心が $(\mu,w)$、極点が $(r,w)$。絶対値を使う有効端点は MPFR から二進有理数で出す。区間式と証明ステップの合成は整数比の演算でも再現できる。

## 4. 受け渡す結果

`boxes.jsonl`、`edges.jsonl`、`charts.jsonl`、`links.jsonl`、`intersections.jsonl`、`pending.jsonl`、`summary.json` に計画 §7 の内容を残す。`integrals.jsonl` は数値核が返した素区間、`enclosures.jsonl` はそれらへの参照・各段階と交差、`events.jsonl` はパイロットと実行の記録。`PILOT.json`、ビルド記録、実行時の `MANIFEST.json` と `RESULT_SHA256SUMS.txt` を合わせて保存する。`work/` はプロセス別の原台帳であり、出力のハッシュ対象である。実行時の `MANIFEST.json` は事前登録のものと区別し、両コミット、時計、CPU、コンパイラ、MPFR/GMP、コマンドを記録する。

```sh
(cd NEW_OUTPUT_DIRECTORY && sha256sum -c RESULT_SHA256SUMS.txt)
python3 -B verify_ledgers.py NEW_OUTPUT_DIRECTORY
```

`verify_ledgers.py` は数値核を再計算せず、素区間を使った証明の成立条件を点検する。見落とした箱、未照合の接続や交差、未確定の端点が残れば、量ごとにその状態を返す。数学的採否は台帳とコードの監査を経た Judge の裁定による。

## 5. 事前登録時の確認

作業機での確認は小さな人工台帳と球の解析値の包含に限る。`smoke_candidate_b.py` は研究 PC 用ランナーの入口を呼ばず、人工の二直線と有理端点の破損検査、それに球での 16→64 セルの回帰だけを行う。記録は [SMOKE_CHECKS.txt](SMOKE_CHECKS.txt)。
