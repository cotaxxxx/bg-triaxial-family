# Judge 実行承認：候補B v4（e7c039e）

- 承認者：Judge（古田勝士）。AskUserQuestion ボタン「承認する（推奨）」。記録は chat（Claude）。承認時刻はこのコミットの時刻を正とする。
- 束：evidence/astra/2026-11-27/CANDIDATE_B_V4 @ e7c039ee315162a9d3e001734128023bba3ac00f、SHA-256 32f9a7b8dc1047f139c819545eafcfb17b5efdae01cb376262e94f9b726c580e
- chat 監査：CHAT_AUDIT_CANDIDATE_B_V4_BUNDLE_e7c039e.md（5c27aa7）PASS

## 条件
1. Dig が研究PCで README_RUN_CANDIDATE_B_V4.md どおりに 1 回実行。評価前に v2 原本（862220c）・v3 原本（7c6cd7e）・束・ビルドの SHA-256 を照合。
2. 新規評価は Krawczyk 小箱のみ（最大 76,384 セル、300 秒）。
3. パッケージ不足なら停止して報告。
4. 結果一式を evidence/dig/ に登録し、chat 監査を受ける。採否は Judge。
