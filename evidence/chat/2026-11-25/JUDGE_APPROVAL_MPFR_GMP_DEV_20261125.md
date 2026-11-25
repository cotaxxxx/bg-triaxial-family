# Judge 承認：研究 PC への MPFR・GMP 開発用パッケージの導入（2026-11-25 20:22 JST）

記録：Claude（通常監査）。Judge（古田勝士）が承認した。

- 背景：改訂した核の E1〜E3（`f48fd33` の手順、K1）の確認で、`libmpfr-dev` と `libgmp-dev` が未導入だった。Dig は手順どおり停止し、`apt-get -s` の結果（新規 3 件：libgmp-dev 6.3.0、libgmpxx4ldbl 6.3.0、libmpfr-dev 4.2.2。更新 0、削除 0）を報告した。
- 承認する操作：`sudo apt-get install --no-install-recommends libmpfr-dev libgmp-dev`
- 条件：
  1. この 3 件以外は入れない。結果が `apt-get -s` と違えば、入れずに止めて報告する。
  2. `apt-get -s` の出力と、導入後の `dpkg -l` の該当行を、実行の記録に残す。
  3. `f48fd33` の K1 の検査（本物の `mpfr.h` でのビルド、GMP の limb が 64 ビット）を通してから E1〜E3 を流す。
  4. E1〜E3 は手順どおり（目安 約 50 分、100 分で停止）。E4 は流さない。
- E2 の監査：`fac1300`（PASS、K2 充足）。
