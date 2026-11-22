# 指示書の版（2026-11-22）

| ファイル | 宛先 | 状態 |
|---|---|---|
| `ASTRA_INSTRUCTION_C_PORT_TRI4_20261122.md`（v1.2） | Astra | **置き換え済み**。Judge 判定（2026-11-22）で仕事を分けた |
| `CLAUDE_CODE_INSTRUCTION_C_PORT_TRI4_v1_3_20261122.md`（v1.3） | Claude Code | 有効。監査の核（Reader の tri4）を C に移す。1 ビット一致 |
| `ASTRA_INSTRUCTION_PRODUCTION_KERNEL_v2_0_20261122.md`（v2.0） | Astra | 有効。層 I・II の本計算の核を、Reader とは別の式で書く |

体制（Judge 判定、2026-11-22）：作る＝Dig（ChatGPT ＋ Astra 6.2）、監査＝Claude（chat）＋ Claude Code、証明の査読＝Fable 5.2（Anthropic。Claude と同じ会社なので、会社まで違う外部ではない）、判定＝Judge。

## 役割の確認（Judge、2026-11-22 夕）

Judge 判定「chat は監査」。chat は作る側の仕事（本計算の核や包み方の設計、Reader で層 I・II を流し切る計画）をしない。

- 赤道の包み方の書き換え（偶関数性、動く座標など）は、作る側の Astra が v2.0 の核の中で行う。V62・V62-B・V63-A の診断は、その材料として参照する。
- Reader 0.7（テープ方式、格子の使い回し）は、Claude Code が監査の道具として速くする。chat は 1 ビット一致を再現して検収する。
- V60〜V63 は、監査の道具（Reader）の速さと限界を測った診断として閉じる。Reader 0.7 で V63-A の設定を流し直すことがあっても、目的は「監査で包み直せる葉の数」を測ることに限る。
- chat の仕事：計画を流す前に監査する、結果を検収する、本計算の台帳から種つきで葉を抜き取って Reader で包み直す、報告する。
