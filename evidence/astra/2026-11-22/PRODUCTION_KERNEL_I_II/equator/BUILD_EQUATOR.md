# 独立核のビルドと E1–E3 の実行

計画 276fc34、差分監査 b81df96。DIAGNOSTIC_ONLY。作業ディレクトリはこの文書のある equator/。E4 の運用は別工程。

1. 公開幾何 JSONL を inputs/E3_BOXES_PUBLIC.jsonl に置く。python src/samples.py は入力 SHA-256、全 ID、順位、厳密な有理数での親包含を照合する。
2. 64-bit GMP limb の Linux で次を実行する。MPFR と GMP をリンクし、全区間端点を MPFR 128-bit で外向きに計算する。本実行は GCC 14.2.0、MPFR の soname 6、mpmath 1.3.0。MPFR ヘッダが提供される環境ではそのヘッダを優先する。
3. 角度二分木は緯度・方位を π 単位で表す。二節点の積分と四階剰余を直接包囲と交差させる。角度微分のスケーリングと面積に π を含めている。計算の履歴は異なるパラメータ箱、各式の各積分で独立。各組の内部は一スレッドで処理する。
4. 組み合わせの最後は Python の有理算術で演算し、各積・和を128ビットの下向き／上向き二進値に変換する。記録の端点 [m,e] は正確な整数 m×2ᵉ。C 核のハッシュの異なる中間積分を混用しない。E3 は全92行がそろって初めて出力する。
5. E2 の固定球面の参照は別の数値実装。i と精度ごとに完了値と秒数を保存し、80桁と110桁の差・包囲への包含を照合する。E2c は親箱への包含も照合する。参照値は証明用の区間に使わない。

```sh
gcc -O2 -std=gnu17 -Wall -Wextra -Wno-enum-conversion -fno-fast-math src/kernel.c -o kernel -l:libmpfr.so.6 -lgmp
python src/samples.py
python src/run_intervals.py --workers 6
python src/run_references.py --workers 6
python src/run_intervals.py --aggregate
python src/run_references.py --aggregate
```

長時間ジョブ中は --aggregate で揃った実測だけを集計できる。results/integrals/ のキャッシュは入力、実行ファイル SHA、各段階、時刻を照合できる。正式な結果の原本はそれぞれの集計 JSONL。Reader の封印値の照合は chat が行う。
