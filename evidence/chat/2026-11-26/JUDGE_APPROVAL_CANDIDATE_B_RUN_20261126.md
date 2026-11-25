# Judge 承認：候補 B の研究 PC での実行（2026-11-26 08:20 JST）

記録：Claude（通常監査）。Judge（古田勝士）が承認した。

- 束：commit `f70b83b0` の `evidence/astra/2026-11-26/CANDIDATE_B_BUNDLE/CANDIDATE_B_PC_BUNDLE.tar.gz`（隣の `.sha256` と照合する）。
- 束の監査：`d59497bd7c11d160adad3d29d30055375d07fc16`（PASS）。
- 実行者：Dig（研究 PC）。手順書 `README_RUN_CANDIDATE_B.md` に従う。`--bundle-commit` には束の登録 commit の完全な SHA、`--judge-execution` にはこの承認の記録の完全な SHA を入れる。

## 条件

1. K1：研究 PC の開発用パッケージは承認済み（`03fc846`）。`build.sh` の検査で足りなければ止めて報告する。
2. パイロット（30 分）の後、見積もりが 5 時間以下のときだけ本走へ進む（ランナーの自動判定）。全体は 6 時間で停止し、子のプロセスまで止まったことを確かめる。
3. 束、計画、核を変えない。同じ出力先で再実行しない。ほかの計算を重ねない。等級は DIAGNOSTIC_ONLY。
4. 結果は、台帳、`PILOT.json`、ビルドの記録、実行時の `MANIFEST.json`、`RESULT_SHA256SUMS.txt`、`verify_ledgers.py` の出力を含めて登録する。
5. 報告は、開始、終了または停止、登録の三回だけ。

## 訂正（2026-11-26 08:05）

- 題の時刻「08:20 JST」は chat の書き誤り。承認と記録の時刻は commit `4247e0c` の時刻（2026-11-26 07:58:26 +0900）を正とする。中身は変えない。
