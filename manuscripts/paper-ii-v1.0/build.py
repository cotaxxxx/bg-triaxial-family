"""Build Paper II v1.0 (markdown master and PDF) from the Claude Docs export v0.9."""
import re,subprocess,sys
src=open('../../evidence/chat/2026-11-27/CHAT_DRAFT_PAPER_II_v0_10_EN.md').read()
s=src
# strip the export's title block (title, date line, draft line)
i=s.index('## Abstract'); s=s[i:]
s=s.replace('\\_','_').replace('\\[','[').replace('\\]',']').replace('\\*','*').replace('&#91;','[').replace('\\<','<').replace('\\>','>')
s=re.sub(r'```latex\n(.*?)\n```',lambda m:'$$\n'+m.group(1)+'\n$$',s,flags=re.S)
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a,s.count(a)); s=s.replace(a,b)
n=s.count('(y*, z*)'); assert n>=4,n; s=s.replace('(y*, z*)','$(y_*, z_*)$')
old='F_y\\in[0.7337,\\,2.0574],\\quad F_z\\in[-0.3106,\\,-0.1393],\\quad G_y\\in[-0.2678,\\,0.1208],\\quad G_z\\in[-0.2338,\\,-0.1595].'
assert s.count(old)==1; s=s.replace(old,'\\begin{aligned}F_y&\\in[0.7337,\\,2.0574],&\\quad F_z&\\in[-0.3106,\\,-0.1393],\\\\ G_y&\\in[-0.2678,\\,0.1208],&\\quad G_z&\\in[-0.2338,\\,-0.1595].\\end{aligned}')
old='(1-2U\\mu t+Ut^2)^{-1/2}=\\sum_{n\\ge0}\\eta_n t^n,\\qquad n\\,\\eta_n=(2n-1)U\\mu\\,\\eta_{n-1}-(n-1)U\\,\\eta_{n-2},\\quad \\eta_0=1 .'
assert s.count(old)==1; s=s.replace(old,'\\begin{gathered}(1-2U\\mu t+Ut^2)^{-1/2}=\\sum_{n\\ge0}\\eta_n t^n,\\\\ n\\,\\eta_n=(2n-1)U\\mu\\,\\eta_{n-1}-(n-1)U\\,\\eta_{n-2},\\qquad \\eta_0=1 .\\end{gathered}')
rep('[Figure 1, file paper2_fig1_map.] **Figure 1.**','![](paper2_fig1_map.pdf){width=78%}\n\n**Figure 1.**')
rep('[Figure 2, file paper2_fig2_sides.] **Figure 2.**','![](paper2_fig2_sides.pdf){width=78%}\n\n**Figure 2.**')
full={'f8c809f':'f8c809f2e2cfdc32da04aba120e7e8fd1001de7e','bb50c85':'bb50c85c1bff93e3e04b54c5cbd218dcb3768a96','cdd885b':'cdd885b5ff0fa31408f08a97c382f230f24bab04','e7c039e':'e7c039ee315162a9d3e001734128023bba3ac00f','e5456d8':'e5456d8ca3966330f39ae0490ca1637d703c09c6','862220c':'862220cc03f8044ab770548d865a76ed56fc612c','7c6cd7e':'7c6cd7ecb21d7d4465e2140c5465412e4f3a4720'}
a=s.index('## Data and code availability'); b=s.index('## References'); blk=s[a:b]
for k,v in full.items():
    assert blk.count(k)==1,k; blk=blk.replace(k,v)
assert blk.count('adoption of Theorem 1 at 2d2576e, of Theorem 2 at 8f9fe35')==1
blk=blk.replace('adoption of Theorem 1 at 2d2576e, of Theorem 2 at 8f9fe35','adoption of Theorem 1 at 2d2576ee43f07a3cb94df28d63051f52649e3c81 (with the correction of one end point at d6dc12b24a3a1b7575350cdd8bed7e24494eaa89), of Theorem 2 at 8f9fe35af8675f3e043d7849ba2ab065efcf6634; the external audits, the reviews and the responses to them are in the same branch')
m=re.search(r'\[A reproduction archive.*?\]',blk,flags=re.S); assert m
blk=blk.replace(m.group(0),'A reproduction archive (the four bundles with their code and plans, the result ledgers, the checkers, the independent audit scripts and the figure script, with SHA-256 sums and instructions) is attached to the Zenodo record of this paper.')
s=s[:a]+blk+s[b:]
rep('it read the ledgers and did not recompute any interval.','it read the ledgers and did not recompute any interval. It also built the interactive viewer, which Claude audited against the ledger and the text of this paper.')
rep('adopted by the author\'s rulings 2d2576e (Theorem 1) and 8f9fe35 (Theorem 2) after the audits.','adopted by the author\'s rulings 2d2576e (Theorem 1; one end point corrected in d6dc12b) and 8f9fe35 (Theorem 2) after the audits.')
rep('Each plan, audit, approval and ruling is a dated commit in the public repositories. No AI system is an author.','Each plan, audit, approval and ruling is a dated commit in the public repositories. No AI system is an author. The author read the complete manuscript in a Japanese translation of this text and approved it on 27 November 2026.')
s=s.replace('- Repository of this paper: <https://github.com/cotaxxxx/bg-triaxial-family>\n  -','- Repository of this paper: <https://github.com/cotaxxxx/bg-triaxial-family>\n\n  -') if False else s

# data availability as a table (40-digit identifiers do not fit in a nested list)
a=s.index('## Data and code availability'); b=s.index('## References')
F=full
avail="""## Data and code availability

All material is public and pinned by commit. Repository of this paper: <https://github.com/cotaxxxx/bg-triaxial-family>

| Item | Commit |
|:-----------------------|:---------------------------------------------|
| Derivation of the four integrands | `%s` |
| Bundle v2 | `%s` |
| Bundle v3 | `%s` |
| Bundle v4 | `%s` |
| Bundle C (correspondence) | `04051b610bd1ada9992e8912a3bdad4954ae929c` |
| Result v1 | `%s` |
| Result v2 | `%s` |
| Result v3 | `%s` |
| Result v4 | `f58ca0c871bc075c89f09aa1df5a2e4ec4b702b7` |
| Result C | `5959680d898dee1289c4023e059dd7e5b84847cf` |
| Adoption of Theorem 1 | `2d2576ee43f07a3cb94df28d63051f52649e3c81` |
| Correction of one end point | `d6dc12b24a3a1b7575350cdd8bed7e24494eaa89` |
| Adoption of Theorem 2 | `8f9fe35af8675f3e043d7849ba2ab065efcf6634` |
| Interactive viewer | `202744a3074910df1b9e0bf9759144f24493ba56` |

Bundle C is on the branch codex/paper-ii-correspondence-20261127 and the viewer on the branch claude/paper-ii-viewer-20261127; they are not reachable from the other branches. The audits, the rulings, the external audits, the reviews and the responses to them are on the branch evidence/triaxial-chat.

Record of the method as a worked example: <https://github.com/cotaxxxx/GeoEnclosure>, directory examples/triaxial-four-curves. Process records: <https://github.com/cotaxxxx/experimental-mathematics-ai-collaboration>

A reproduction archive (the four bundles with their code and plans, the result ledgers, the checkers, the independent audit scripts, the figure script and the sources of the viewer, with SHA-256 sums and instructions) is attached to the Zenodo record of this paper (doi:10.5281/zenodo.24581453).

**Interactive viewer.** The Zenodo record also contains a linked viewer of the map: one self-contained HTML file with no network access, in English and Japanese. Choosing a shape on the map of Figure 1 shows the corresponding ellipsoid and, when the shape lies in a certified strip, the local event of Theorem 2. The viewer is built from the ledger of run v2 by a script in the archive. It is an illustration and not part of any proof. It can also display uncertified floating-point positions of stationary points on the axes; this layer is off by default and is labelled as not proved here.

"""%(F['f8c809f'],F['bb50c85'],F['cdd885b'],F['e7c039e'],F['e5456d8'],F['862220c'],F['7c6cd7e'])
s=s[:a]+avail+s[b:]
# inline symbols with subscripts -> TeX math (outside display math and the availability section)
G={'ℓ':r'\ell','ξ':r'\xi','η':r'\eta','∂':r'\partial'}
def conv(t):
    t=re.sub(r'∂²_(\{[^}]+\}|[A-Za-z]+)',lambda m:'\x00P'+m.group(1).strip('{}').replace('_','\x01')+'\x00',t)
    def f(m):
        base=G.get(m.group(1),m.group(1)); sub=m.group(2).strip('{}').replace('−','-'); star='^{\\ast}' if m.group(3) else ''
        return '$'+base+'_{'+sub+'}'+star+'$'
    t=re.sub(r'(?<![\w$\\])([A-Za-zℓξη∂])_(\{[^}]+\}|[A-Za-z0-9]+)(\*?)',f,t)
    return re.sub('\x00P([^\x00]*)\x00',lambda m:'$\\partial^2_{'+m.group(1).replace('\x01','_')+'}$',t)
a=s.index('## Data and code availability'); b=s.index('## References')
parts=re.split(r'(\$\$.*?\$\$)',s[:a],flags=re.S); pre=''.join(p if p.startswith('$$') else conv(p) for p in parts)
parts=re.split(r'(\$\$.*?\$\$)',s[b:],flags=re.S); post=''.join(p if p.startswith('$$') else conv(p) for p in parts)
s=pre+s[a:b]+post
s=s.replace('$\\partial^2_{q_j}$','$\\partial^2_{q_j}$')

ja='''
## Appendix B. Title and abstract in Japanese

**三軸楕円体の角度エネルギー地図 ― 停留点が出入りする四本の境目（再現コード・ビューア付き）**

凸体とその内部の一点に対して、その点から境界の点を見る向きと、そこでの外向き法線とがなす角の二乗を、錐体積の重みで平均したものを角度エネルギーと呼ぶ。回転楕円体でのこのエネルギーの停留点は、この連作の第一論文（論文 I、doi:10.5281/zenodo.24495446）で、そこに述べた六つの計算主張を条件として分類した。そこには四つの閾値の形が現れた。本論文は、三本の軸がすべて違う楕円体を扱う。半軸を y ≤ 1 ≤ z と書き、形の長方形 R = [1/4, 1] × [1, 7] の上で、最長軸以外の二本の軸それぞれについて、中心でのエネルギーの二階微分と、その軸の端でのエネルギーの動径方向の微分という、四つの量を考える。

R の中で、四つの量それぞれの零集合は一本の弧である。四本の弧が出会うのは、辺 y = 1 の上の二つの扁長側の閾値の形と、内部のただ一点（横断的な交わり、y ≈ 0.6382、z ≈ 2.2966）だけである。回転楕円体の四つの閾値はこれらの弧の端点で、残る二つの端は辺 y = 1/4 の上にある。さらに、各弧は次の局所的な意味で境目である。形が弧を横切るとき、エネルギーの停留点がちょうど一対、中心を通って、または向かい合う一対の極を通って出入りし、どちら側に対があるかも決まる。二つの扁長側の閾値の形では、形が辺 y = 1 に沿って動くとき、対の代わりに一つの停留円が出入りする。

証明は計算機を使い、GeoEnclosure の方法論（doi:10.5281/zenodo.24421364）に従う。面積分を MPFR の区間演算で囲み、有理数の台帳に記録し、数値のコードとは独立の検査器で確かめる。第一の主張の証明に至る四回の実行（v1〜v4）を、数値の核を変えないまま、GeoEnclosure の一つの実例として記録する。この場合、証明は、精度を上げることによってではなく、確かめる命題を変えることによって閉じた。地図の各領域にある停留点の個数は、本論文では決めない。
'''
ja=ja.replace('## Appendix B. Title and abstract in Japanese\n','## Appendix B. Title and abstract in Japanese\n\n\\begingroup\\jafont\\XeTeXlinebreaklocale "ja"\\XeTeXlinebreakskip=0pt plus 1pt\n')+'\n\\endgroup\n'
s=s.rstrip()+'\n'+ja
head='''---
title: "A Map of the Angle Energy on Triaxial Ellipsoids: Four Threshold Curves of Stationary Points, with Reproduction Code and an Interactive Viewer"
author: "Katsushi Furuta (DAYBREAK) · ORCID 0009-0005-3129-8043"
date: "Version 1.0 · 27 November 2026 · doi:10.5281/zenodo.24581453"
---

'''
open('Paper_II_v1_0_EN.md','w').write(head+s)
open('header.tex','w').write(r'''\newfontfamily\jafont{Noto Serif CJK JP}
\usepackage{newunicodechar}\newunicodechar{ℓ}{\ensuremath{\ell}}\newunicodechar{∎}{\rule{0.55em}{0.55em}}
\usepackage{booktabs,longtable}\usepackage{xurl}\usepackage{fvextra}\renewcommand{\texttt}[1]{{\small\ttfamily #1}}
\setlength{\emergencystretch}{3em}
\usepackage{fancyhdr}\pagestyle{plain}
''')
cmd=['pandoc','Paper_II_v1_0_EN.md','-s','-o','Paper_II_v1_0_EN.tex','-H','header.tex','-V','geometry:a4paper,margin=25mm','-V','fontsize=11pt','-V','mainfont=DejaVu Serif','-V','monofont=DejaVu Sans Mono','-V','colorlinks=true','-V','linkcolor=black','-V','urlcolor=blue','--toc','--toc-depth=2','-f','markdown+pipe_tables+tex_math_dollars-auto_identifiers+implicit_figures']
r=subprocess.run(cmd,capture_output=True,text=True); import collections,re as _r; print(collections.Counter(_r.findall(r'There is no (\S+)',r.stderr)), r.stderr[-300:] if 'Error' in r.stderr else '')

for k in range(3):
    r=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error','Paper_II_v1_0_EN.tex'],capture_output=True,text=True)
    assert r.returncode==0,r.stdout[-2000:]
log=open('Paper_II_v1_0_EN.log',errors='replace').read()
print('missing:',log.count('Missing character'),'overfull:',re.findall(r'Overfull \\hbox \(([0-9.]+)pt',log),'undefined:',log.count('undefined'))
