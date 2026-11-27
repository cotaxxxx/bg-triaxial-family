# Claude Code への依頼：ビューアに DOI を入れる（最終ビルド）

2026-11-27 JST、chat。対象：`claude/paper-ii-viewer-20261127` @ `202744a`（chat 監査 PASS、`46c17ca`）。

Judge が Zenodo で DOI を予約した：**10.5281/zenodo.24581453**

変えるのは次の 2 点だけ。ほかは変えないでください。

1. フッターの「DOI: to be added on publication／DOI：公開後に記入」を `doi:10.5281/zenodo.24581453` に（英・日）。README も同じ。
2. `meta` とフッターにある論文の参照先コミット（いまは `69ff74e5…`）を、論文 v1.0 の最終版のソースのコミット `ae8d73b5aefba2870ca6ded76eb53851c5cb4fdb`（枝 `evidence/triaxial-chat`、`manuscripts/paper-ii-v1.0/`）に差し替える。

納品：同じ枝に新しいコミット、HTML の SHA-256、`build_checks.json` の再生成。報告は「変わったのはこの 2 点だけ」「外部への通信なし」と、既定の画面の写し 1 枚で足ります。

これが論文 II の公開前の最後の工程です。納品後、chat が差分を確かめ、zip を作り直し、Judge が PDF・zip・ビューアを Zenodo に投稿します。
