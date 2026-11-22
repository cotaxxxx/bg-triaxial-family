"""Render the measured report exclusively from archived records."""
import json
import sys
from pathlib import Path
root=Path(__file__).resolve().parent
d=Path(sys.argv[1])
def lines(path):return [json.loads(v) for v in path.read_text().splitlines()]
def mdtable(headers,rows):
    def row(xs):return '| '+' | '.join(map(str,xs))+' |'
    return '\n'.join([row(headers),row(['---']*len(headers)),*(row(r) for r in rows)])
comparison=json.loads((d/'comparison.json').read_text())
perf={v['name']:v for v in lines(d/'timings.jsonl')}
if set(perf)!={n+'_'+b for n in ('bench','tree0','tree1','N512') for b in ('python','c')}:
    raise ValueError('performance manifest')
sl=[lines(d/'perf'/f'bench_{s}.log') for s in ('python','c')]
rows=[]
def pair(label,t1,t2,r1=None,r2=None):
    rows.append([label,f'{t1:.2f}',f'{t2:.2f}',f'{t1/t2:.2f}×',
                 '—' if r1 is None else f'{r1/1024:.0f}', '—' if r2 is None else f'{r2/1024:.0f}'])
for i in (0,1):pair('V60 '+sl[0][i]['kind'],sl[0][i]['sec'],sl[1][i]['sec'])
for name,title in [('bench','V60 連続2箱'),('tree0','V61 W3・内部'),('tree1','V61 W3・軸面'),('N512','H33・N=NH=512')]:
    a,b=[perf[name+'_'+s] for s in ('python','c')]
    pair(title,a['sec'],b['sec'],a['rss_kib'],b['rss_kib'])
table=mdtable(['負荷','Python 秒','C版 秒','時間比','Python MiB','C版 MiB'],rows)
bx=lines(d/'perf/N512_python.log')[0]
import struct
def number(k):return struct.unpack('>d',bytes.fromhex(bx['outcome'][k]))[0]
br=lines(d/'branches_c.jsonl')
branch_table=mdtable(['入力','order','used','接触セル','lazy_skip','確認した分岐'],
    [[r['label'],*[r['outcome'].get('info',{}).get(k,'—') for k in ['order','used','contact_cells','lazy_skip']],
      ', '.join(k for k,v in r['observed'].items() if v) or '—'] for r in br])
trees=mdtable(['V61 木','葉数','評価数','leaf_sha256'],
              [[v['tree'],v['leaves'],v['evals'],'`'+v['leaf_sha256']+'`'] for v in comparison['B'] if v['backend']=='c'])
exception_count=comparison['A_exceptions']+sum('exception' in r['outcome'] for r in br)
trial_count=comparison['A_total']+len(br)
errs=comparison['errors']
verdict='合格' if not errs else '不合格'
ratio=perf['N512_c']['rss_kib']/perf['N512_python']['rss_kib']
print(f"""# 三軸 Reader 0.6.0 の C 移植 · 旧指示書 v1.2 の診断記録

**DIAGNOSTIC_ONLY。固定試験の技術判定は{verdict}。** Judge の指定により、この成果物は旧 v1.2 の診断記録として保存する。現行の担当分離はコミット db9208b4934fefd11399d4c7cb88c79bc4d1f674 に記録されている。

## 固定試験の結果

|試験|検査内容|結果|
|---|---|---|
|A|8組 × 3位置 × 2格子の48件、chat 箱の6件、分岐7件の計61件。さらに旧計画の幾何深さ12件と球に届かないW3の2件も保持|全{trial_count}件を比較（包囲{trial_count-exception_count}件、同一例外の試験{exception_count}件）|
|B|V61の2本の木。Python、C版双方を記録済みの木と比較|下表に葉列のハッシュと評価数を掲載|
|C|同じビルド環境で Reader の自己試験6本を完走|{sum(v=='FAILURES 0' for v in comparison['C'].values())}/6本で FAILURES 0|

機械判定の差異記録は {len(errs)} 件。全入力・両実装の端点・幅・terms・used・診断値は results12/ 内の JSONL に残した。省略された幅は欠落のまま比較した。例外に enclose.last を転記すると直前の評価を誤記するので、例外型と文面を比較した。試験例の分類と各結果は comparison.json にもある。

{trees}

### 分岐の確認

{branch_table}

coarse は動く変数があり、細格子の接触セルが0個で、粗格子の D² 下端条件により order=1 となった場合を表す。p0 は有理数で求めた箱中心と記録された展開点が異なる場合である。上記に加え、接触 H33・分母0・球の外の3例と、人為的に空の共通部分を渡す1例で例外を比較した。人為例はエラー処理の単体試験である。丸め方向20,018件、fsum 2,030件、NaN・混合符号など配列8件の結果は同じフォルダにある。自己試験の examples は独立した有理数入門例で、tri4 を直接呼ぶ検査は他の自己試験が担当する。

## 速度とメモリ

{table}

同一のクラウド作業機（AMD EPYC 9V74、x86-64、GCC 14.2.0）で1スレッド、各負荷・各版1回ずつの逐次測定。個別の V60 箱は正本ベンチの呼び出し内で計時した。ほかは新しいプロセスの起動・読込みを含む実時間と wait4 のピーク RSS である。N=NH=512 のピーク RSS は C 版で Python の {ratio:.1%}。chat 箱の端点は [{number('lo'):.15g}, {number('hi'):.15g}]。V60 の2箱には個別 RSS を割り当てていない。研究PCの16並列および全域の費用はこの試験で測定していない。

## 実装と再現

固定入力は PLAN_C_PORT.md、深さの修正は PLAN_C_PORT_V2.md、現行範囲・追加分岐・§7の判定は PLAN_V12.md、球内に届く深さ12の追加2件は PLAN_V12_INBALL.md にある。自動再現は `bash reproduce.sh /path/to/bg-triaxial-family /path/to/new-run`。CPython・Cython・NumPy・mpmath・ビルドフラグは BUILD.md に記載した。入力 bundle の SHA-256 を確認してから実行する。再現先では結果を results/ に書き出す。

Reader の tri4.py、tri3.py、tri2.py は正本とバイト一致する。分数とスカラーのべき、一次・二次の組立て、terms、共通部分、例外、enclose.last を Python で保持した。Cython は元の格子被積分関数、平均値セル、dual/jet の式を C に変換する。ctypes 経由の区間演算・Horner・CPython の総和が端点を計算する。32,768セルごとに二階ジェットの一時配列を再利用し、各セルの結果を元の順に並べてから全体を一度だけ合計する。セルの並列化は行っていない。

CPython v3.12.14 の math_fsum と補助関数を含む連続 5,718 バイトの SHA-256 は `9dccff927dd43beef171bbb9b3436b56383c63b1bd50d8a0eb77c557342a363e`。原典コミットとライセンスは BUILD.md と CPYTHON_LICENSE.txt にある。V61 の研究PC記録は Ryzen 9 9900X、Ubuntu の Linux 7.0.0-38-generic、CPython 3.11.16 のビルドコンパイラ GCC 15.2.0 を示す。当該PCで本移植をビルド・実行した実績は今回の測定には含まれない。

## 独立照合と採否

この旧版の実装と技術試験は Astra/Codex が担当した。旧 v1.2 §6 は本計算の約1%を同じ Reader の Python 版で包み直し、差異があれば該当組を使わない設計である。その同式照合と、別式による独立検証は異なる。今回の結果について chat の独立再現と Judge による数理的な採否は未実施である。

現行の裁定では、監査用 Reader の C 移植は Claude Code の v1.3 が担当する。Astra の本計算核 v2.0 は、Reader の実装を読んでいない別セッションに分け、別の表示・別のコードから開発する。今回のセッションでは旧 v1.2 のために Reader の実装を読んだ。この成果物は v2.0 の入力や独立核へ引き継ぐコードには含めない。
""")
if errs: print(json.dumps(errs,indent=2))
