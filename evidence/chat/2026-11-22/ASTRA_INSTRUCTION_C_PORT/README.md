# 指示書の版（2026-11-22）

| ファイル | 宛先 | 状態 |
|---|---|---|
| `ASTRA_INSTRUCTION_C_PORT_TRI4_20261122.md`（v1.2） | Astra | **置き換え済み**。Judge 判定（2026-11-22）で仕事を分けた |
| `CLAUDE_CODE_INSTRUCTION_C_PORT_TRI4_v1_3_20261122.md`（v1.3） | Claude Code | 有効。監査の核（Reader の tri4）を C に移す。1 ビット一致 |
| `ASTRA_INSTRUCTION_PRODUCTION_KERNEL_v2_0_20261122.md`（v2.0） | Astra | 有効。層 I・II の本計算の核を、Reader とは別の式で書く |

体制：作る＝Dig（ChatGPT ＋ Astra）、監査＝Claude（chat）＋ Claude Code、外部監査＝Muse（範囲は未定）、判定＝Judge。
