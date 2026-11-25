# E4 固定入力と同梱原本

2026-11-25、DIAGNOSTIC_ONLY。8組のキーと順番は試験計画 §5。層 I、`equator`、`H33` の三つのラベル、形タイル、位置セル、五つの有理端点対を照合した。

| 同梱ファイル | 原本 |
|---|---|
| `PLAN_TESTS_EQUATOR.md`、`DERIVATION.md`、`BUILD_EQUATOR.md` | `66afe3ad4c0d76442370df49174077f601733c6c`、`equator/` の同名ファイル |
| `README_RUN_E4_HISTORY.md` | 同コミットの `equator/README_RUN_E4.md` |
| `src/kernel.c`、`src/interval.h`、`src/jets.h`、`src/run_intervals.py`、`src/samples.py` | 同コミットの `equator/src/` の同名ファイル |
| `inputs/samples_v60.json` | `c25ba7bc2b044356896e948f6201f8ade77eb06d`、`calibration/V60/input/unpacked/v60/samples_v60.json` |
| `inputs/E4_CASES.json` | 計画 §5 の順で選んだ8行。V61の葉数・評価回数と照合用IDを付記 |

計画のSHA-256は `7f628c6e83ae68c8067dcd57d70f64ba2e0b7293035ca301c209d50f153a705d`。核ソースのSHA-256は `6cae72fdd9c1a30e4a759a49b3814d098941fa80056fd40001e6c24220d6fed3`。元のV60入力のGit blobは `74c6e9ee30bb8dc63d363878d3f685e1589420cc`、SHA-256は `6cd544a58266c61cd9e080bd151622724efcb1d2ef860c03de042568f77a372b`。有理座標を浮動小数点に変換せず、`--check-inputs` で各行と形・位置タイルの有理端点を照合する。

参照した範囲は承認、固定計画・導出・手順、この核と関連するAstraの固定ソース、V60の入力幾何と運用文書、監査・登録のGitメタデータである。ReaderとC移植、監査側の実装、独立検算の枝・参照値の閲覧は0件と自己申告する。
