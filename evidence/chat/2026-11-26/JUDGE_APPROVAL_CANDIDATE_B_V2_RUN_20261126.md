# Judge 承認：候補 B 第 2 版の研究 PC での実行（2026-11-26）

記録：Claude（通常監査）。Judge（古田勝士）が承認した。承認の時刻は、この記録の commit の時刻を正とする。

- 束：commit `bb50c85c1bff93e3e04b54c5cbd218dcb3768a96` の `evidence/astra/2026-11-26/CANDIDATE_B_V2/CANDIDATE_B_PC_BUNDLE_V2.tar.gz`（隣の `.sha256` と照合する）。
- 束の監査：`4ffdc9dcd9a676b45830863b4fea543d18540f45`（PASS）。
- 実行者：Dig（研究 PC）。手順書 `README_RUN_CANDIDATE_B_V2.md` に従う。`--bundle-commit` には束の登録 commit、`--judge-execution` にはこの承認の記録の commit の、完全な SHA を入れる。

## 条件

1. K1 は承認済みのパッケージ（`03fc846`）で満たすはず。足りなければ止めて報告する。
2. パイロット（30 分）の後、見積もりが 19,800 秒以下のときだけ本走へ（ランナーの自動判定）。全体は 6 時間で停止し、子のプロセスまで止まったことを確かめる。
3. 束、計画、核を変えない。同じ出力先で再実行しない。第 1 版の結果を上書きしない。ほかの計算を重ねない。等級は DIAGNOSTIC_ONLY。
4. 結果は、台帳、`PILOT.json`、ビルドの記録、実行時の `MANIFEST.json`、`RESULT_SHA256SUMS.txt`、`verify_ledgers.py` の出力を含めて登録する。
5. 報告は、開始、終了または停止、登録の三回だけ。
