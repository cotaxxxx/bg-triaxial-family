# E4 実行用の束の事前登録　2026-11-25

**DIAGNOSTIC_ONLY。chat の束監査と Judge の E4 実行承認待ち。**

承認記録は `66afe3ad4c0d76442370df49174077f601733c6c` の ASTRA_SCOPE_E4_BUNDLE_20261125.md。前提となる改訂核 E1〜E3 の監査記録は `1b7c758bcf529dab5867467d16987b60d5ba6558`。

| 項目 | 固定したもの |
|---|---|
| [実行用の束](E4_PC_BUNDLE_20261125.tar.gz) | SHA-256 `c7dacbaf477800f528dfb129f91a9f76b4736df10bced2036f172bdfb41e582b` |
| [研究PC用手順](E4_PC_BUNDLE/README_RUN_E4.md) | 開始条件、正規ヘッダでのビルド、基準測定8本、時間換算、停止、結果の検査 |
| [入力8組](E4_PC_BUNDLE/inputs/E4_CASES.json) | 計画 §5 の順。元のV60入力との有理端点照合は [入力来歴](E4_PC_BUNDLE/INPUT_PROVENANCE.md) |
| [ランナー](E4_PC_BUNDLE/src/run_e4.py) | 分割台帳・R2・未処理箱・評価数・時刻・メモリ・SHA-256 |
| [同梱23ファイルのSHA-256](E4_PC_BUNDLE/MANIFEST.sha256) | 計画、核、導出、ランナー、入力、手順、人工確認記録 |

計画のSHA-256は `7f628c6e83ae68c8067dcd57d70f64ba2e0b7293035ca301c209d50f153a705d`。核ソースのSHA-256は `6cae72fdd9c1a30e4a759a49b3814d098941fa80056fd40001e6c24220d6fed3`。

各段階の判断を先に行うため、固定核の出力後に次段階の許可を待つI/O処理を別ファイルで同梱した。人工点で通常起動との三段階の一致と途中停止を確認した。人工小箱と人工の分割・締切・較正記録の確認範囲も記載した。 [人工確認の記録](E4_PC_BUNDLE/SMOKE_VALIDATION.md)

E4の8組と実際のV60較正は未開始。chat の監査対象はこの束のバイト列である。研究PCでの作業は Judge の実行承認に従う。
