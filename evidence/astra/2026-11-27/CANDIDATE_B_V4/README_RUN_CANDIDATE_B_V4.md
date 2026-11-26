# 候補B v4｜Dig の実行手順

2026-11-27 JST · DIAGNOSTIC_ONLY · chat 監査前

計画とコードが chat の監査を受け、Judge が v4 の実行を承認した後に、研究PCで実行する。評価するのは $Z_1\cap\partial_2$ の Krawczyk 小箱だけ。存在・一意性・他の五組の関係は、固定原本を使って読み直す。[計画](PLAN.md) · [導出](DERIVATION.md) · [固定入力](V4_INPUTS.json)

## 1. 配布物・原本・ビルド

1. `CANDIDATE_B_PC_BUNDLE_V4.tar.gz` と同名の `.sha256` を照合する。新しい作業ディレクトリに展開し、`sha256sum -c SHA256SUMS.txt` で内部のファイルを照合する。
2. `V2_RESULT` に `862220c` の v2 の `RESULT/`、`V3_RESULT` に `7c6cd7e` の v3 の `RESULT/` を指定する。束に入っている2つの `*_RESULT_SHA256SUMS.txt` と各原本の `RESULT_SHA256SUMS.txt` を照合する。ランナーでも v2 の98件と v3 の99件を照合する。原本への書き込みが発生しないよう、出力先はどちらの原本ディレクトリとも分離する。[v2 固定原本](https://github.com/cotaxxxx/bg-triaxial-family/tree/862220cc03f8044ab770548d865a76ed56fc612c/evidence/dig/2026-11-26/CANDIDATE_B_V2_PC_RESULT/RESULT) · [v3 固定原本](https://github.com/cotaxxxx/bg-triaxial-family/tree/7c6cd7ecb21d7d4465e2140c5465412e4f3a4720/evidence/dig/2026-11-27/CANDIDATE_B_V3_PC_RESULT/RESULT)
3. `bash build.sh` で v2/v3 と同じ K1 検査とビルドを行う。開発用パッケージ `libmpfr-dev` または `libgmp-dev` が不足する場合は、K1 ログと `apt-get -s install --no-install-recommends libmpfr-dev libgmp-dev` の予定を報告し、Judge の導入承認を待つ。実 MPFR ヘッダとリンク先の版、GMP の64ビット limb、コンパイラとフラグを記録する。Python は3.10以上。

## 2. 起動と停止

最初の3引数は束の登録、chat の束監査、Judge の実行承認の各コミットの40桁の SHA。残りは上記の原本と、存在していない出力ディレクトリに置き換える。SSH 切断に備え `tmux` などの中で実行する。

```sh
python3 -B run_candidate_b_v4.py \
    --bundle-commit V4_BUNDLE_GIT_SHA \
    --chat-audit V4_CHAT_AUDIT_GIT_SHA \
    --judge-execution V4_EXECUTION_GIT_SHA \
    --v2-result V2_RESULT \
    --v3-result V3_RESULT \
    NEW_OUTPUT_DIRECTORY
```

4件の重なり、面の包囲、全箱の横断微分、傾きの積を照合してから、固定した小箱と角度段階で Krawczyk を試す。数値評価は76,384セル、300秒まで。途中で止める場合は `Ctrl+C` またはランナーへの `SIGTERM`。核は新しいセルの開始前に停止フラグと締切を読む。終了・停止時には作成済み台帳と理由を保全し、未実行の試行を記録する。数値評価の後の原本の読み直しには120秒の別の制限がある。期限で読み直しが完了しなければ、封印データを保持して次の読み直し手順を用いる。

## 3. 検収用の台帳

```sh
(cd NEW_OUTPUT_DIRECTORY && sha256sum -c RESULT_SHA256SUMS.txt)
python3 -I -B verify_v4.py V2_RESULT V3_RESULT NEW_OUTPUT_DIRECTORY
```

| ファイル | 記録 |
|---|---|
| `PRIMARY.json` | 4件の座標、参照する帯と積分ID、運んだ面の区間、傾きの積と主証明の条件 |
| `work/local/integrals.jsonl` | MPFR の素区間、精度、角度木、セル使用数 |
| `work/local/intersections.jsonl` | 小箱、Krawczyk 像の両座標、$q$、不成立の条件 |
| `LEDGER_INSPECTION.json` | 再構成した六組の関係と実行した試行、未実行の試行 |
| `MANIFEST.json`、`RUN.json`、SHA-256 とビルド記録 | 実行の承認、原本、終了理由と時刻、封印 |

主証明の条件がそろえば `Z1+D2` は `EXACTLY_ONE_INTERIOR` と記録される。Krawczyk の補強まで得られた場合の状態は `RELATION_RECORDED`。それ以外は `PARTIAL` として何が未確定か提示する。肯定の判定は実際の数値と封印原本を chat が監査し、Judge が採否を決める。

## 4. 事前登録時の動作確認

`python3 -B smoke_v4.py` で人工区間による面の輸送、継ぎ目の欠落の拒否、Krawczyk の打ち切りと全9試行時の上限、台帳改変の検出を再現できる。[作業機の確認記録](SMOKE_V4.txt)
