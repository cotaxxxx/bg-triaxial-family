# Dig 実行手順と chat 監査入口

最初に PLAN.md、DERIVATION.md を読む。設計版。chat による束監査と Judge の別個の実行承認を要する。

## 入力と環境

ローカルの bg-triaxial-family の Git オブジェクトに、PROVENANCE.json の v2・v3・v4 が必要。作業ツリーは参照せず git show で固定版を読む。今回の束監査・Judge 実行承認は別々の40桁コミットを指定する。監査内容・署名者・許可予算と束の一致は Dig が実行指示で確認する。環境は Linux、Python 3.10+、C11、64-bit GMP、libmpfr-dev / libgmp-dev。設計対象は MPFR 4.2.2。

## 入力照合と人工試験

外側の .sha256 とアーカイブがある場所で次を使う。BG_REPO は対象リポジトリの絶対パス。

```sh
sha256sum -c PAPER_II_CORRESPONDENCE.tar.gz.sha256
tar -xzf PAPER_II_CORRESPONDENCE.tar.gz
cd paper_ii_correspondence
sha256sum -c SHA256SUMS.txt
python3 -B run.py preflight --repo "$BG_REPO"
```

preflight は積分を実行しない。人工テストは mpmath のある環境で `python3 -B smoke.py`。本計算・台帳検査の Python 依存は標準ライブラリのみ。

## 承認後の研究PC

NEW_RESULT は専用の結果ディレクトリ、AUDIT と APPROVAL は本件のコミット。下の例で MINUTES は当該呼び出しで許可された残り時間（1〜360分）。研究PCの通常の tmux 等で実行する。途中から同じビルド・同じ承認・同じ結果ディレクトリで再開できる。

```sh
bash build.sh
python3 -B run.py scan --repo "$BG_REPO" --out "$NEW_RESULT" --chat-audit "$AUDIT" --judge-approval "$APPROVAL" --workers 4 --minutes "$MINUTES"
python3 -B run.py isolate --repo "$BG_REPO" --out "$NEW_RESULT" --chat-audit "$AUDIT" --judge-approval "$APPROVAL" --workers 4 --minutes "$MINUTES"
python3 -B run.py verify --repo "$BG_REPO" --out "$NEW_RESULT" > "$NEW_RESULT/verification.log"
```

時間切れの scan/isolate は終了値2。各完成タスクを atomic rename で保存する。verify は入力と raw 包囲から有理数演算で判定・分割・収縮を再生する。独立実装による数値再積分は別工程。監査には identity.json、scan/、isolate/、verification.log、build/header.json、compiler.txt、build のハッシュ、実行時刻・終了コードを渡す。最終 JSON の receipt, reversed, unresolved, zero_brackets を読む。終了コードだけで全条件成立としない。

監査・承認が別のリポジトリに記録された場合は、それぞれのローカルパスを --audit-repo または --approval-repo で指定できる。Dig は結果登録前に結果を閉じてから次のハッシュ台帳を作る。isolate は未決がないときも出力用の空ディレクトリを作る。

    (cd "$NEW_RESULT" && find identity.json scan isolate verification.log -type f -print0 | sort -z | xargs -0 sha256sum > RESULT_SHA256SUMS.txt)
