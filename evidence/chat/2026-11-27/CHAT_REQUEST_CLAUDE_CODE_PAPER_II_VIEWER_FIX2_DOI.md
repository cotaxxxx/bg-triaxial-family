# Claude Code への依頼：ビューアに DOI を入れる（最終ビルド）

2026-11-27 JST、chat。対象：`claude/paper-ii-viewer-20261127` @ `202744a`（chat 監査 PASS、`46c17ca`）。

Judge が Zenodo で DOI を予約した。**10.5281/zenodo.24581453**

変えるのは次の 2 点だけ。

1. フッターの「DOI: to be added on publication／DOI：公開後に記入」を `doi:10.5281/zenodo.24581453` に（英・日）。README も同じ。
2. `meta` とフッターの論文の参照先コミットを `e3e…`（下の値）に差し替える：論文 v1.0 の最終版のソースは枝 `evidence/triaxial-chat` のコミット **（chat がこのファイルと同じコミットで登録。下の「参照先」を見ること）**。

参照先：このファイルを含むコミットの番号を使ってください（`git log -1 --format=%H -- evidence/chat/2026-11-27/CHAT_REQUEST_CLAUDE_CODE_PAPER_II_VIEWER_FIX2_DOI.md`）。

納品：同じ枝に新しいコミット、HTML の SHA-256、`build_checks.json` の再生成。検査は「変わったのはこの 2 点だけ」「外部への通信なし」を報告。画面の写しは既定の 1 枚でよい。
