# Judge 実行承認：論文 II 対応条件（04051b6）

- 承認者：Judge（古田勝士）。AskUserQuestion ボタン「承認する（推奨）」。記録は chat（Claude）。承認時刻はこのコミットの時刻を正とする。
- 束：branch codex/paper-ii-correspondence-20261127 @ 04051b610bd1ada9992e8912a3bdad4954ae929c、evidence/astra/2026-11-27/PAPER_II_CORRESPONDENCE
- 束 SHA-256：3e655bb2d907bf5c641fa9a38fd7256438f49cda636400331b7e5dab47fad8cf
- chat 監査：c3042489ee3b4bb425d95d9ba0d257d683c3eba1（PASS）

## 許可する実行と予算
1. `preflight` → `build.sh` → `scan`（--minutes 60 以内）→ `isolate` → `verify`。scan と isolate の合計は壁時計 6 時間以内（isolate の --minutes は 360 から scan の実測を引いた値以下）。4 プロセス。
2. scan の結果で UNRESOLVED が全 1,412 件の半数を超えた場合は、isolate に進まず停止して報告する。
3. 実行するのは上の SHA-256 の束のみ。evidence/triaxial-chat の 3accf27 にある同名ディレクトリの旧版は使わない。
4. パッケージ不足なら停止して報告（導入は別承認）。
5. 結果一式を登録し、chat 監査を受ける。採否は Judge。
