# Astra への指示書：三軸の包囲の核（tri4）を C に移す

2026-11-22、chat（Claude、監査担当）作成。Judge（古田 勝士）の指示による。
宛先：ChatGPT（GPT-6.2 Astra、高）。Codex を使って作業してください。
状態：**DIAGNOSTIC_ONLY**。この作業の結果は、chat の検証と Judge の判定を経るまで、証拠として使いません。

---

## 0. なぜこの作業が要るのか

三軸楕円体の層 I・II の計算は、V61 までで 96 組中 87 組が完走しました。終わった組から見積もると、全域の費用は **Python で少なくとも 22.65 CPU 年**です。研究 PC の 16 コアで割っても 1 年半ほどかかり、このままでは終わりません。

費用の大半は、包囲の核（Reader 0.6.0 の `tri4`）を Python と numpy で動かしていることによります。**計算の中身を一切変えずに、核を C に移して速くする**のがこの作業の目的です。

赤道の H33 が終わらない件（包み方の問題）は、chat が別の系統（V63-A・V63-B）で扱っています。この作業では扱いません。

## 1. 守ること（最優先）

1. **計算の中身を変えない。** 式、格子、丸めの向き、分け方の規則、閾値は、Reader 0.6.0 と同じにする。C 版は「同じ計算を速く行うもの」であり、「よりよい計算」ではない。改善の案があれば、実装せずに別紙で提案する。
2. **結果は、Python 版と 1 ビットまで同じにする。** 包囲の両端の binary64 の値が、すべての試験で Python 版と一致すること。一致しないものが一つでもあれば、合格としない。
3. **計画と試験の組は、計算を流す前に固定する。** 結果を見てから、試験の組・合格の条件・規則を変えない。変えるときは新しい版の計画として書く。
4. **リポジトリ：** `cotaxxxx/bg-triaxial-family` の `evidence/triaxial-chat` 枝に置く。`main` には触らない。`cotaxxxx/bg-spheroid-family` の `main` と STATE にも触らない。
5. 研究 PC で流す計算は、一回ずつ、手順書どおりに行う。

## 2. 正本（ここから始める）

| もの | 場所 |
|---|---|
| Reader 0.6.0（`GER2/geoenclosereader/`） | `cotaxxxx/GeoEnclosure` の `reader/`（commit `1f84913`）。または下の束の中の `GER2/` |
| ランナー（V61 と同じ規則、N の上限と NH を引数に取れる形） | `bg-triaxial-family`、`evidence/triaxial-chat` 枝、`evidence/chat/2026-11-22/D_TRI_V63A_GRID/V63A_PC_BUNDLE.tar.gz` の中の `v63a/run_v63a.py`（元は `run_v61.py`） |
| 等価の基準になる記録 | `evidence/chat/2026-11-21/D_TRI_LAYER_I_II_COMPLETION_V61/chat_checks/repro/`（2 組の木。`leaf_sha256`、葉の数、評価回数） |
| V61 の結果（39 組） | 同じフォルダの `results/V61_RESULT_20261121_1645.tar.gz` |

Reader の丸めの設計（`fiv.py` の冒頭に書いてある）：
- 四則と sqrt は IEEE の正しい丸め（最近接）で計算し、端を `nextafter` で 1 ulp 外へ動かす。
- 三角関数や π は libm を使わず、mpmath（40 桁）か有理数から外向きに丸めた値を使う。
- 多数の項の和は `math.fsum`（正確な和を一度だけ丸める）で、そのあと 1 ulp 外へ動かす。

この設計なら、C でも 1 ビットまで同じ結果を出せます。

## 3. 作業の順番

### 作業 1：どこで時間を使っているかを測る（C を書く前に）

- Reader 0.6.0 の `tri4.H33`・`tri4.W3`・`tri4.C12` を、V61 の組から選んだ箱（下の §4 の試験の組）で profile する（`cProfile` など）。
- 時間の内訳を、格子の生成（mpmath）、配列の演算（numpy）、`fsum`、Python の制御、の四つに分けて表にする。
- **移す範囲は、この表で決める。** 格子の生成（mpmath）は、キャッシュされていて軽いなら Python に残してよい。その場合は、C へ渡す配列の形を決めておく。

### 作業 2：C で実装する

- 対象：`tri4.enclose`（一次の形、二次の形、lazy、二つの形の共通部分）と、それが呼ぶ `tri2` / `tri3` / `jet` / `dual` / `fiv` の計算。
- 丸め：四則と sqrt のあとに `nextafter` で外へ 1 ulp。**FMA を使わない**（`-ffp-contract=off`）、**`-ffast-math` を使わない**、`-O2` まで。x87 を使わない（x86-64 の SSE2）。
- 和：`math.fsum` と同じ値を返す正確な和（Shewchuk の部分和の方法など）。`fsum` の結果と 1 ビットまで同じであることを試験で示す。
- 三角関数・π：Python 側で作った値（mpmath から外向きに丸めた binary64）を配列で受け取る。C の libm の `sin`・`cos`・`acos` は使わない。
- 呼び出し：Python から ctypes か cffi で呼ぶ。ランナー（`run_v63a.py` の規則）は Python のままでよい。N の上限と NH を引数で選べるようにする（V61 の設定：上限 256、NH = max(16, N/2)。V63-A の設定：上限 512、NH = N）。
- 並列：まず一本で 1 ビット一致を示す。そのあと、セルの並列化をするなら、和の順序が結果を変えないこと（正確な和なので変わらないはず）を試験で示す。
- エラー：Python 版が `ValueError`（接触のセル）や `INCONSISTENT` を出す所では、C 版も同じ場所で同じ状態を返す。

### 作業 3：等価性の試験（計画を固定してから流す）

次の三つを、すべて満たすこと。

| 試験 | 合格の条件 |
|---|---|
| A. 単発の包囲 | §4 の試験の組のすべての箱と N について、包囲の両端、一次の幅、二次の幅、`used`、`terms` が Python 版と 1 ビットまで同じ |
| B. 木の一致 | V61 の 2 組（`chat_checks/repro/rep.json`）を V61 の設定で流し、`leaf_sha256`、葉の数、評価回数が Python 版の記録と同じ |
| C. 自己試験 | Reader 0.6.0 の自己試験 6 本（`selftest_tri`、`selftest_tri2`、`selftest_tri3`、`selftest_tri4`、`selftest_lazy`、`examples/selftest_examples`）が、C 版の核に差し替えても FAILURES 0 |

### 作業 4：速さを測る

- V60 の bench の箱（`v60/bench_v60.py` の h33 と w3）で、Python 版と C 版の秒数を同じ機械で測り、比を出す。
- V61 の 2 組の木を流した秒数も、両方で測る。
- メモリの最大値も記録する（N = 512 で Python 版は約 3.75 GB）。

## 4. 試験の組（作業 3 の前に固定すること）

- V61 の 39 組から、層 I の H33・W3、層 II の C12 を少なくとも 2 組ずつ含むように、種 20261124 で 8 組を選ぶ。各組で、根の箱と、深さ 6・12 の子の箱を一つずつ、N = 64・256 で包む。
- 加えて、chat の試験箱（`evidence/chat/2026-11-22/D_TRI_V63A_GRID/chat_checks/grid_test_box.md` の箱）を、N = 256・512、NH = 128・256・512 で包む。
- 選び方のスクリプトと、選ばれた組の一覧を、流す前に commit する。

## 5. 納めるもの

`evidence/triaxial-chat` 枝の `evidence/astra/2026-11-2x/C_PORT_TRI4/` に、次のものを置く。

1. `PLAN_C_PORT.md`：作業 3・4 の計画（流す前に commit）。
2. `PROFILE.md`：作業 1 の時間の内訳。
3. C のソースと、ビルドの手順（コンパイラの版、フラグ）。
4. 試験 A・B・C の出力と、合否の表。
5. 速さとメモリの表。
6. `SHA256SUMS.txt`。

報告は、合格・不合格をそのまま書く。不合格の箱があれば、その箱、N、Python 版と C 版の値を全部書く。**数学的な解釈と採否の判断はしない**（chat が検証し、Judge が決める）。

## 6. このあと

chat が、試験 A・B を独立に再現します。合格すれば、Judge の判定を経て、C 版で V63（赤道）と本計算を流す計画を chat が作ります。

AI 利用の記録：この作業は ChatGPT（OpenAI、GPT-6.2 Astra）が Codex（OpenAI）を用いて行い、Claude（Anthropic）が監査する。採否は著者が決める。
