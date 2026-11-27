# chat 監査：ビューアの修正版（Claude Code、`202744a`）

2026-11-27 JST。対象：`202744a3074910df1b9e0bf9759144f24493ba56` の `viewer/paper2_viewer.html`（SHA-256 `c97bbb970c543fd3641f203e469b154e34c0cb2e671e4f64d00841b77bfbe42a`、107,950 バイト）。依頼書 `c775274`（5 点）。前回の監査 `ccd8929`。

判定：**PASS。採用の条件を満たす。**

| 依頼 | 確認 | 結果 |
|---|---|---|
| 1「横断的に」 | 差分と、ブラウザで Z₁ の帯に形を置いたときの文（英・日） | "crosses the arc transversally"／「この弧を横断的に横切るとき」 |
| 2 既定で非表示 | 開いた直後の状態（パソコンの幅・携帯の幅）：チェックなし、出来事の欄に「Uncertified」の行なし、凡例 C と注記は非表示。チェックを入れると出て、外すと消える | 成立 |
| 2 追加：絵の中の注記 | チェックを入れた画面の写し | 3D の描画面の左上に "Uncertified numerics — not proved in Paper II" の枠つき文字 |
| 3 README | 差分 | 記載あり |
| 4・5 フッターと題名 | ブラウザで読む | 新しい題名（英・日）。DOI は「公開後に記入」のまま |
| ほかを変えていないこと | `template.html` の差分は上の点だけ。ページ内の帯 612 本を台帳と再照合、交点の箱を再照合 | 一致 |
| 外部への通信 | オフラインで開く | 要求 0 件、エラー 0 件、横スクロールなし |

写しとスクリプト：`viewer_audit/`（`audit3.js`、`chat_desktop_default.png`、`chat_desktop_unc_on.png`、`chat_phone_default.png`）。

確認していないこと：Safari・Firefox・実機。ビルドの再実行。
