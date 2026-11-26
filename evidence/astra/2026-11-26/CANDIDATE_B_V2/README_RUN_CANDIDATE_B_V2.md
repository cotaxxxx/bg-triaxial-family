# 候補 B 第2版の実行用の束

2026-11-26 JST · DIAGNOSTIC_ONLY · chat の差分・コード監査待ち

対象は中間軸 $x=1$、短軸 $y$、長軸 $z$、$R=[1/4,1]\times[1,7]$。四量、区間算術の核、接続・交差の数学条件は第1版による。第2版で使う予算、先に角度を詰める基準、帯の追跡、初期箱の巡回は計画と入力に固定した。[第2版計画](PLAN_CANDIDATE_B_V2.md) · [差分一覧](DIFF_V1_TO_V2.md) · [入力](INPUTS.json)

## 1. 起動の条件と K1

以下は chat の監査と Judge の第2版の実行承認の後に、Dig が研究PCで行う手順。

1. `CANDIDATE_B_PC_BUNDLE_V2.tar.gz` を同名の `.sha256` と照合し、空の作業ディレクトリに展開する。展開先で `sha256sum -c SHA256SUMS.txt` を実行する。第2版の登録コミットと実行承認コミットを控える。
2. `bash build.sh` で K1 とビルドを行う。K1 は `libmpfr-dev` と `libgmp-dev` の状態・版、本物の MPFR ヘッダとライブラリの一致、GMP 64ビット limb を調べる。開発パッケージが欠ける場合は K1 のログと `apt-get -s install --no-install-recommends libmpfr-dev libgmp-dev` の変更予定を提出し、導入の個別承認を待つ。
3. 数値核は第1版と同じ入力ソースを、`-include mpfr.h -lmpfr -lgmp`、`-O2 -fno-fast-math -ffp-contract=off` でビルドする。Python 3.10 以降の標準ライブラリで制御する。`build/K1.log`、`build/compile.log`、`build/BUILD.json` を保全する。

## 2. パイロット、本走、停止

```sh
python3 -B run_candidate_b.py \
    --bundle-commit BUNDLE_GIT_SHA \
    --judge-execution JUDGE_EXECUTION_GIT_SHA \
    NEW_OUTPUT_DIRECTORY
```

- 同じ八箱、球の解析照合、30分上限でパイロットを行う。実測の90パーセンタイルで、最長並行ワーカーとその後の直列相の回数を時間に換算する。見積もりが19,800秒以下で、パイロットの条件と停止フラグ、全体期限を確認できた場合に本走へ進む。
- 本走は各量2,400万セル。各量のうち帯・接続は800万まで。パイロットと四量終了後の交差検査は共通800万セル。合計1億400万セル。親が Z1、三子プロセスが Z2、D1、D2 を担当する。角度の段階は同じ木を継続する。
- 起動から6時間で計算と実行内の台帳検査を打ち切る。外部から止める場合は親 PID への `SIGTERM` または `Ctrl+C` を使う。次の角度セルを始める前に共有停止フラグを読み、子を回収する。停止後は生の台帳、保留、締切の記録、SHA-256を保全する。出力ディレクトリは未使用のものを指定する。

## 3. 結果の照合

計画第1版の §7 に従う。量の台帳、角度木、実行台帳と共に `work/` のプロセス別原本、`PILOT.json`、ビルド記録、実行時 `MANIFEST.json`、`RESULT_SHA256SUMS.txt`、独立検査の出力を保存する。第2版の追加項目は中点幅とその上限、帯の入口・出口と由来、初期巡回の順、追跡のセル消費である。[第1版 §7](https://github.com/cotaxxxx/bg-triaxial-family/blob/f8c809f2e2cfdc32da04aba120e7e8fd1001de7e/evidence/astra/2026-11-26/CANDIDATE_B_PLAN/PLAN_CANDIDATE_B.md) · [第2版の台帳差分](DIFF_V1_TO_V2.md)

```sh
(cd NEW_OUTPUT_DIRECTORY && sha256sum -c RESULT_SHA256SUMS.txt)
python3 -B verify_ledgers.py NEW_OUTPUT_DIRECTORY
```

独立検査は標準ライブラリだけを読み込む。有理端点と参照IDを用いて被覆・符号・帯・接続・交差を検査し、素区間から計算方針の記録も再構成する。証拠の採否は結果台帳と核を監査した後の Judge の工程とする。

## 4. 事前登録時の確認

`python3 -B smoke_policy_v2.py` は少数の人工的な有理区間を返す模型で、中点ゲート、帯の由来、巡回順、比較の未確定処理を検査する。第2版の作業機での確認はこの人工入力と静的な核・設定の照合である。[確認記録](SMOKE_POLICY_V2.txt)
