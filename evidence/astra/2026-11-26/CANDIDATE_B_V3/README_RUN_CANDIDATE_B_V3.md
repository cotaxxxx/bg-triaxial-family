# 候補B v3｜研究PCでの実行手順

2026-11-26 JST · DIAGNOSTIC_ONLY · chat 監査前

判定条件と数値は [PLAN.md](PLAN.md) と [V3_INPUTS.json](V3_INPUTS.json)。chat の計画・コード監査、Judge の v3 実行承認、マクローリン–ヤコビ実例の終了確認を済ませた後、この手順を Dig が実施する。

## 1. 原本の照合とビルド

1. マクローリン–ヤコビ実例の終了時刻と Dig の終了記録を確認し、実例の子プロセスを含めて実行が終わったことを確認する。v3 登録コミットと Judge の v3 実行承認コミットをそれぞれ控える。
2. `CANDIDATE_B_PC_BUNDLE_V3.tar.gz` と同名の `.sha256` を照合し、新しいディレクトリへ展開する。展開先で `sha256sum -c SHA256SUMS.txt` を実行する。
3. `V2_RESULT` には `862220c` の研究PC上の v2 原本ディレクトリを指定する。v2 の実績で記録された場所は `/home/daybreak/candidate-b-v2-pc-20261126/RESULT`。原本の `RESULT_SHA256SUMS.txt` と束内の `V2_RESULT_SHA256SUMS.txt` の同一性を確認する。v3 ランナーでも原本の全ファイルを照合する。[v2 原本の登録記録](https://github.com/cotaxxxx/bg-triaxial-family/blob/862220cc03f8044ab770548d865a76ed56fc612c/evidence/dig/2026-11-26/CANDIDATE_B_V2_PC_RESULT/README.md)
4. `bash build.sh` で v2 と同じ K1 と実ヘッダによるビルドを行う。開発用パッケージが足りない場合は K1 ログと `apt-get -s install --no-install-recommends libmpfr-dev libgmp-dev` の予定を報告し、Judge の導入承認を待つ。MPFR ヘッダ・ライブラリの版、GMP の64ビット limb、コンパイラ、フラグを記録する。Python 3.10 以上の標準ライブラリを使う。

## 2. パイロット、本走、停止

マクローリン–ヤコビ実例の実際の終了時刻をオフセット付き ISO 形式で入れる。終了記録は参照可能なパスまたは固定コミットを指定する。手順1で確かめた事実を引数と実行台帳に記録する。空いている出力先を指定し、SSH 接続の離脱に備え `tmux` などの中で動かす。外側の6時間上限は GNU timeout で、数値評価の締切と保全の余裕はランナーで管理する。

```sh
bash build.sh
timeout --signal=TERM --kill-after=8s 21592s python3 -B run_candidate_b_v3.py \
    --bundle-commit V3_BUNDLE_GIT_SHA \
    --judge-execution V3_EXECUTION_GIT_SHA \
    --v2-result V2_RESULT \
    --jacobi-ended-at JACOBI_END_ISO_WITH_OFFSET \
    --jacobi-end-record JACOBI_END_RECORD \
    NEW_OUTPUT_DIRECTORY
```

本走は、パイロットの球の包囲、出力、壁時計の見積もりがそろったときだけ進む。局所の共有端点と交差、四量の並行処理、全域比較の順。全域の比較は全四曲線の被覆後に行い、被覆が残った場合は保留を記録する。停止する場合はランナーへの `SIGTERM` またはセッションの `Ctrl+C` を使い、終了後に子プロセスの有無を確認する。資源上限で残った葉は未決または未処理として台帳に残る。外側の強制終了で封が途中までの場合は、生の台帳と起動・停止ログを保全する。

## 3. 読み直しと報告

```sh
(cd NEW_OUTPUT_DIRECTORY && sha256sum -c RESULT_SHA256SUMS.txt)
python3 -I -B verify_v3.py V2_RESULT NEW_OUTPUT_DIRECTORY
```

局所の記録は `work/local/proof/intersections.jsonl`、残る形箱と帯は `work/main/<量>/`、全域比較は `work/compare/proof/intersections.jsonl`。各ワーカーの `integrals.jsonl` に、区間の端点、形箱、一次微分の方向、精度、角度段階、セル課金を保存する。保全するものは `work/` 全体、`PILOT.json`、`RUN.json`、`LEDGER_INSPECTION.json`、実行時 `MANIFEST.json`、ビルド/K1 受領書とログ、SHA-256。検査の出力と実行終了記録を付けて chat と Judge に渡す。

## 4. 事前登録時の確認

`python3 -B smoke_v3.py` は人工の一次関数で共有端点と帯、局所交差、Krawczykの真の包含、台帳の改変の拒否、全曲線の被覆前の保留を調べる。核とビルド手順は v2 とバイト一致を確認した。[確認記録](SMOKE_V3.txt)
