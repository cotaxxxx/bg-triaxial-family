# V60 実行手順（研究 PC、一回だけ）

依頼：この束を一度だけ流し、できた結果のファイルを一つ返してください。ファイルの中身は変えないでください。途中で止まったときも、`out/` をそのまま返してください。

所要時間：1〜2 時間（自己試験に約 10 分、本番は 16 本を並べて流します）。メモリは約 16 GB 使います。

## 1. 準備（Python 3.11 以上と、numpy、mpmath）

```bash
PYBASE=/home/daybreak/.pyenv/versions/3.11.16/bin/python3.11
$PYBASE -m venv ~/v60env
~/v60env/bin/pip install numpy mpmath
```

## 2. 展開と実行

```bash
mkdir -p ~/v60 && cd ~/v60
tar xzf /path/to/V60_PC_BUNDLE.tar.gz
cd V60_PC_BUNDLE
sha256sum -c MANIFEST.sha256          # すべて OK になることを確かめる
PY=~/v60env/bin/python bash run_all.sh
```

`run_all.sh` は次の順に進みます：入力の照合 → 環境の記録 → 自己試験 4 本 → 速度の基準測定（16 本を同時に） → 96 組 → 梱包。

## 3. 返すもの

`V60_PC_BUNDLE/V60_RESULT_*.tar.gz` を一つ返してください。

途中で止まった場合は `out/` をまとめて返してください：

```bash
tar czf V60_PARTIAL.tar.gz out
```

## 4. してほしくないこと

- ファイルの書き換え、並列数の変更、途中からの再開。
- 結果の解釈。解釈は chat が行います。
