# 三軸設計v2.0・v2.1の時系列確認｜停止前の既存案件

**記録日：2026年11月23日**  
**検証・記録：Dig（ChatGPT）**  
**確認対象：三軸楕円体研究の設計v2.0・v2.1と、2026年11月22日の中止裁定の前後関係**  
**性格：GitHub履歴の事実確認／研究計画・試験・数学的認証の裁定ではない**

## 1．確認した履歴

| 出来事 | JST | 根拠コミット |
|---|---|---|
| 設計指示v2.0・v2.1の修正・SHA一覧の固定 | **2026-11-22 17:44:38** | [`c25ba7bc2b044356896e948f6201f8ade77eb06d`](https://github.com/cotaxxxx/bg-triaxial-family/commit/c25ba7bc2b044356896e948f6201f8ade77eb06d) |
| 三軸研究のJudge中止裁定 | **2026-11-22 20:08:07** | [`686343fdf9349fd15cd5324457bd44aaa6af5dde`](https://github.com/cotaxxxx/bg-triaxial-family/commit/686343fdf9349fd15cd5324457bd44aaa6af5dde) |
| 三軸研究のJudge再開裁定 | **2026-11-23** | [`7ce6f1e7a4bbe6d599499eadff4de1e46327ef68`](https://github.com/cotaxxxx/bg-triaxial-family/commit/7ce6f1e7a4bbe6d599499eadff4de1e46327ef68) |

時刻はGitHubコミットの`committer.date`（UTC）を日本時間へ換算した値。厳密な設計作業の開始時刻ではなく、**GitHubに記録されたコミット時刻**を表す。

GitHub比較 `c25ba7b...686343f` は、設計側コミットが中止裁定コミットの**祖先（24コミット前）**であることを示す。したがって、設計v2.0・v2.1の当該版は停止前に存在していた。

## 2．`c25ba7b`で変更されたファイル

1. [`ASTRA_INSTRUCTION_PRODUCTION_KERNEL_v2_0_20261122.md`](https://github.com/cotaxxxx/bg-triaxial-family/blob/c25ba7bc2b044356896e948f6201f8ade77eb06d/evidence/chat/2026-11-22/ASTRA_INSTRUCTION_C_PORT/ASTRA_INSTRUCTION_PRODUCTION_KERNEL_v2_0_20261122.md)
2. [`ASTRA_DESIGN_EQUATOR_v2_1_20261122.md`](https://github.com/cotaxxxx/bg-triaxial-family/blob/c25ba7bc2b044356896e948f6201f8ade77eb06d/evidence/chat/2026-11-22/ASTRA_INSTRUCTION_C_PORT/ASTRA_DESIGN_EQUATOR_v2_1_20261122.md)
3. [`SHA256SUMS.txt`](https://github.com/cotaxxxx/bg-triaxial-family/blob/c25ba7bc2b044356896e948f6201f8ade77eb06d/evidence/chat/2026-11-22/ASTRA_INSTRUCTION_C_PORT/SHA256SUMS.txt)

当該コミットは、設計・実装側がReaderのコードおよび監査側のフォルダ・ブランチを開かないという独立性の制限を、`*.md`を含めて明示した変更として記録されている。

## 3．再開後の扱い

Judgeの再開後に、新しい設計セッションへ`c25ba7b`固定のv2.0とv2.1が渡されたとの報告を受領した。

設計セッションの担当者からは、改訂後v2.1 §0の確認・閲覧履歴点検で禁止対象閲覧0件との**自己申告**があった。監査側の追加参考数値は渡していないとの報告も受領しているが、**Digが当該設計セッションの全閲覧履歴を独立監査したという意味ではない**。

**整理：** 停止前から存在する設計指示を、再開後に引き継いだ案件であり、設計指示そのものを「再開後に新規に生まれた研究課題」とは数えない。

## 4．計画・実行の関門

- `PLAN_TESTS_EQUATOR.md`について、**新しい設計セッションによる改訂・登録・固定コミットは、当該報告の時点では未受領**。旧リポジトリに同名の資料が存在することを、新しい設計セッションの提出完了と扱わない。
- 新しい計画、設計、剰余導出の固定リンクが提出された後、Claude（通常監査）が計画と独立性条件を確認する。
- **試験の実行は通常監査とJudgeの個別実行承認が揃ってから**。この時系列記録は、Reader 0.7やC移植、既存の撤回済みE2/E4実行指示の再承認を意味しない。
- 新しい計算の結果や数学的証拠等級のPASS・CLOSEDは、この履歴確認から生じない。

## 5．結果

**記録上の判定：PRE-STOP DESIGN IDENTIFIED / HISTORY VERIFIED / TEST EXECUTION NOT AUTHORIZED**

Judge裁定、監査原本、既存コードや証拠等級は変更しない。
