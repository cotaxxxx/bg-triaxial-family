# Dig 結果登録｜論文 II 対応条件の研究PC実行

2026-11-27 JST。証拠等級 DIAGNOSTIC_ONLY。結果受領票 CHECKS_RECORDED。採否は chat 結果監査後の Judge 裁定による。

- **旧版 3accf27 は使用していない。旧版は取り下げ扱いとし、実行したのは 04051b6（SHA-256 3e655bb2d907bf5c641fa9a38fd7256438f49cda636400331b7e5dab47fad8cf）だけである。**
- 固定束：branch codex/paper-ii-correspondence-20261127 @ 04051b610bd1ada9992e8912a3bdad4954ae929c。
- chat 束監査：c3042489ee3b4bb425d95d9ba0d257d683c3eba1（PASS）。Judge 実行承認：f9dd5c54d9e45a3d28c9c7e3d8318599a0ab3f9a。
- 固定原本20/20バイト一致、束内部19/19 SHA-256一致、preflight 614帯。基礎ソース6件はv3と一致。ビルド3/3 SHA-256一致。MPFR 4.2.2、GMP 6.3.0、64-bit limb。
- scan: 04:44:57.190557–04:46:03.151270 JST、65.960740833秒、1412件完了、EXPECTED 1110、UNRESOLVED 302。停止閾値706以下のためisolateへ進んだ。
- isolate: 04:46:03.164482–04:54:33.042411 JST、509.877950359秒、302件完了。scan/isolate合計壁時計575.852187811秒。4ワーカー、scan --minutes 59、isolate --minutes 357。
- verify: 終了コード0、CHECKS_RECORDED、1412/1412タスク、EXPECTED 1751葉、unresolved・zero_brackets・reversed 各0。独立数値再積分ではなく固定入力とraw区間からの台帳再生。
- RESULT/ は全1718原本（scan 1412、isolate 302、identity.json、verification.log、RESULT_SHA256SUMS.txt、空のrun.lock）をバイトそのまま保全。原本ハッシュ台帳1716件。records/ は全実行・照合ログ。build/ は生成ソース、バイナリ、ビルド記録、ハッシュ台帳を含む全10ファイル。bundle/ は固定入力の来歴・ハッシュ台帳とアーカイブのチェックサム。入力アーカイブ自体は研究PCに保全、固定コミットで取得可能。
- 研究PC原本：/home/daybreak/paper-ii-correspondence-pc-20261127/。再実行・数学的採否・計画変更なし。
