# Claude Code への依頼：ビューアの小修正（採用の条件）

2026-11-27 JST、chat。対象：`claude/paper-ii-viewer-20261127` @ `d39c4f7`。監査 `ccd8929`（PASS）、採用裁定は同日（`JUDGE_RULING_PAPER_II_VIEWER_ADOPTION.md`）。

直す点は次の 5 つだけ（2 に追加、5 を追加。2026-11-27 改訂）。ほかは変えないでください。

1. **「横断的に」を入れる（必須）。** `evZ`・`evD` の文。
   - 英語：`When the shape crosses it, …` → `When the shape crosses the arc transversally, …`
   - 日本語：`形がこの弧を横切るとき、` → `形がこの弧を横断的に横切るとき、`
2. **保証のない数値の層を既定で非表示にする（必須、Judge 裁定）。** チェックボックスは残し、初期状態を外す。外れているあいだは、3D の白抜きの印も、出来事の欄の「Uncertified: …」の行も出さない。凡例 C と注記は、チェックを入れたときにだけ出すか、「チェックを入れると表示」と分かる文にする。
   **追加（Muse の意見「画面の切り取りは説明文を連れて行かない」を受けて）：** チェックを入れて印を表示しているあいだは、3D の絵の**中**（描画面の隅）にも「Uncertified numerics — not proved in Paper II／保証のない数値（論文 II は未証明）」の文字を描く。絵だけが切り取られても、注記が一緒に付いていくようにするため。
3. **README に一行。** 左の辺 y = 1/4 の二つの印は端点の区間の中点に置いた説明用（B）で、証明済みなのは区間（A）であること。
4. **フッター。** DOI の欄は「公開後に記入」のままでよい。論文の参照先コミットを、組み直し後の番号に差し替えられるよう、`template.html` の該当箇所を README に書いておく（いまも 2 か所と報告済みなら、その場所を明記するだけでよい）。

5. **論文の題名（Judge 裁定、2026-11-27 08:46）。** フッターの論文の題名を新しい題名に直す：`A Map of the Angle Energy on Triaxial Ellipsoids: Four Threshold Curves of Stationary Points, with Reproduction Code and an Interactive Viewer`。日本語の表示を出す所があれば「三軸楕円体の角度エネルギー地図 ― 停留点が出入りする四本の境目（再現コード・ビューア付き）」。README も同じ。

納品：同じ枝に新しいコミット。HTML の新しい SHA-256、`build_checks.json` の再生成、既定の画面（チェックなし）とチェックを入れた画面の写しを各 1 枚。検査の表は、変わった所だけ報告してください。
