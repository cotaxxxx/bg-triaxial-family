# tri4 C port · archived v1.2 diagnostic

Judge 指定による旧 v1.2 の診断記録。Reader 0.6.0 の Python 実装と、同じ式を使った Astra/Codex の C 移植との比較である。

- 実測・照合・適用範囲は [REPORT.md](REPORT.md)。
- 再現方法は [BUILD.md](BUILD.md) と [reproduce.sh](reproduce.sh)。
- 事前固定は [PLAN_C_PORT.md](PLAN_C_PORT.md)、[深さの修正](PLAN_C_PORT_V2.md)、[v1.2の追加条件](PLAN_V12.md)、[球と交わる子箱](PLAN_V12_INBALL.md) の順。
- 生の数値と判定は [results12](results12/)、内容の検査には [SHA256SUMS.txt](SHA256SUMS.txt) を使う。
- 現行の役割は [Judge 裁定の版一覧](https://github.com/cotaxxxx/bg-triaxial-family/blob/db9208b4934fefd11399d4c7cb88c79bc4d1f674/evidence/chat/2026-11-22/ASTRA_INSTRUCTION_C_PORT/README.md) による。Claude Code が監査用 Reader v1.3、Astra は別セッションで独立の本計算核 v2.0 を担当する。
