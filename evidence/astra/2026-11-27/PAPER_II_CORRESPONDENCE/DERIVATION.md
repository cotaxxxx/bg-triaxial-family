# 論文 II｜零曲線と軸上停留点の出入り

2026-11-27 JST · DIAGNOSTIC_ONLY · 条件付きの数学と計算の導出

形を $p=(y,z)$、$L=\operatorname{diag}(1,y,z)$、基点を参照球座標 $q$ とする。添字 $i=y,x$ はそれぞれ短軸・中間軸に対応する。$F(\gamma)=\arccos^2\gamma$、$E(q)=\langle kF(\gamma)\rangle$、$k=1-q\cdot\xi$、$D=|L(\xi-q)|$、$B=|L^{-T}\xi|^2$、$\gamma=k/(D\sqrt B)$。$A_i=E_{ii}(0)$、$T_i=\lim_{r\uparrow1}E_i(re_i)$ とする。符号と Morse 指数は正の相似尺度と座標の合同変換で保たれる。[候補Bの定義と求積剰余](https://github.com/cotaxxxx/bg-triaxial-family/blob/f8c809f2e2cfdc32da04aba120e7e8fd1001de7e/evidence/astra/2026-11-26/CANDIDATE_B_PLAN/DERIVATION_CANDIDATE_B.md)

## 1. 中心の定理

**定理 1.** $A_i(p_0)=0$ とする。ある形方向に $\partial_p A_i(p_0)\ne0$、$j\ne i$ の二つの $A_j(p_0)\ne0$、かつ $K_i(p_0)=E_{iiii}(0)\ne0$ と仮定する。十分小さい中心と形の近傍を取れば、中心以外の停留点は、$A_i(p)K_i(p_0)<0$ 側でちょうど $\pm r_i(p)e_i$ の一対であり、反対側と零曲線上には存在しない。$p\to p_0$ で

$
r_i^2=-6 A_i(p)/K_i(p_0)+o(|A_i(p)|).
$

対の Morse 指数は、二つの横固有値の負の数に $\mathbf 1_{K_i(p_0)<0}$ を足したもの。中心では $A_i$ の符号が変わる。形が $R$ の辺にある場合は、結論を $R$ に入る側に制限する。

**証明.** 各座標の鏡映により、軸上で横方向の勾配は零である。横方向の勾配を未知数 $q_j$ 二つで解く陰関数定理では、初期行列は対角で成分 $A_j$。解の一意性と軸上の解から、近傍の停留点は軸上に限る。固定した正の形の近傍と $|q|\le1/2$ では分母が下から離れ、$E$ は基点と形について解析的。$g_i(r,p)=E_i(re_i)$ は奇関数で、

$
g_i(r,p)=rU_i(r^2,p),
\qquad U_i(0,p)=A_i(p),\quad \partial_x U_i(0,p)=K_i(p)/6.
$

$U_i$ を $x=0$ の両側へ Taylor 級数で延長し、$U_i(x,p)=0$ を解く。単調な $\partial_xU_i$ で $x=0$ と根を結ぶ平均値式から、根の符号と上の展開を得る。物理根は $x=r^2>0$。根では $E_{ii}=2r_i^2\partial_xU_i$ であり、他の固有値は連続性と鏡映で上記の符号を保つ。

## 2. 軸端の定理

$M_i=\lim_{r\uparrow1}E_{ii}(re_i)$、$H_{ij}=\lim_{q\to e_i,\,|q|<1}E_{jj}(q)$（$j\ne i$）とする。

**定理 2.** $T_i(p_0)=0$、形を横切る方向に $\partial_p T_i(p_0)\ne0$、$M_i(p_0)\ne0$、二つの $H_{ij}(p_0)\ne0$ と仮定する。両極の十分小さい近傍では、$T_i(p)M_i(p_0)>0$ の側で内部停留点はちょうど一対、逆側で零個。$T_i=0$ では両極で全勾配のトレースが零になり、その極の近くの内部には停留点がない。根は

$
1-r_i(p)=T_i(p)/M_i(p_0)+o(|T_i(p)|).
$

内側の対の Morse 指数は $M_i,H_{ij},H_{ik}$ の負の数である。

**証明.** 任意の $j\ne i$ について、鏡映と $q_j=0$ から $q_j$ までの線分の積分で $E_j(q)=q_j\int_0^1 E_{jj}(q_i,tq_j,q_k)\,dt$。その線分は球内にあり、Hessian の連続トレースと $H_{ij}\ne0$ から符号を保つ。従って停留点は軸上。$g_i(r,p)$ は $r=1$ まで $C^1$ で、$g_i(1,p)=T_i(p)$、$\partial_r g_i(1,p)=M_i(p)$。この符号で半軸端の近傍は単調であり、左端の値は $p=p_0$ で $M_i$ と逆符号。中間値と平均値の定理から結論が従う。境界での横成分の零と内部 Hessian の対角化は鏡映による。球面制限の $j$ 方向二次微分は $H_{ij}-T_i$ で、トレース零の極で $H_{ij}$ に一致する。

**境界正則性.** 固定 $\xi$ で $v_j=\ell_j^2(\xi_j-q_j)/D^2$、$c=1/(D\sqrt B)$ とすると

$
\gamma_j=c(-\xi_j+kv_j),\qquad
\gamma_{jj}=c[-2\xi_jv_j+k(3v_j^2-\ell_j^2/D^2)].
$

コンパクトな正の形の範囲で $k=\xi\cdot(\xi-q)\le|\xi-q|$、$D\asymp|\xi-q|$。$F$ とその導関数は $[0,1]$ で有界で、$\partial_{jj}(kF)=-2\xi_jF'\gamma_j+kF''\gamma_j^2+kF'\gamma_{jj}$ は $C/|\xi-q|$ で抑えられる。混合微分も同じ次数で、形の一次微分で特異性の次数は増えない。$q=r\eta$ に対し $|\xi-q|^2=(1-r)^2+r|\xi-\eta|^2$。$r\ge1/2$ では接触点近くの半径 $\epsilon$ の球面キャップ積分は一様に $O(\epsilon)$。キャップ外では通常の連続極限を取れるので、Hessian と必要な形微分は境界まで連続に延びる。球面に沿う二階微分は $r<1$ の円弧で連鎖律を使い、この連続極限を取って得る。

## 3. 中心で測る量

$d=\sum\ell_j^2\xi_j^2$、$U=\ell_i^2/d$、$u=\xi_i$、$\gamma_0=1/\sqrt{dB}$。$(1-2Uur+Ur^2)^{-1/2}=\sum h_n r^n$ として

$
(h_0,h_1,h_2,h_3,h_4)=
\left(1,Uu,\frac{3U^2u^2-U}{2},
\frac{5U^3u^3-3U^2u}{2},
\frac{35U^4u^4-30U^3u^2+3U^2}{8}\right).
$

$\gamma=\gamma_0(1-ru)\sum h_nr^n$ より $a_n=\gamma_0(h_n-u h_{n-1})$。$K_i/24$ の被積分関数は

$
 F'(a_4-ua_3)+F''(a_1a_3+a_2^2/2-ua_1a_2)
 +F'''(a_1^2a_2/2-ua_1^3/6)+F''''a_1^4/24.
$

すべての $F^{(j)}$ は $\gamma_0$ で評価し、偶性で $u\in[0,1]$、方位を一象限にできる。コードはこの多項式の $24$ 倍を直接求める。$A_z$ は候補B式 (1) の添字を $z$ にする。

## 4. 極で測る量

候補Bの接触除去を用いる。$\xi_i=\mu=1-2t^2$、$w=(\xi-e_i)/(2t)$、$w_i=-t$、$w_j^2=(1-t^2)\cos^2\phi$ または同じ式の $\sin^2\phi$。$d=\sum\ell_j^2 w_j^2$、$dB$ は正、$L_0=1/\sqrt{dB}$、$k=2t^2$、$\gamma=tL_0$ とする。方位変数 $v\in[0,1]$ を $\phi=\pi v/2$ と取ると、正規化球面平均は $2t\,dt\,dv$ となる。

**軸端の傾き.** $\lambda=\ell_i^2/d,\ b=t^2\lambda$ として、§2 の対角 Hessian に代入し球面重み $2t$ を掛けると、$M_i$ の被積分関数は

$
L_0 F'(\gamma)(2\mu^2+4\mu b+3b^2-b)
+t L_0^2 F''(\gamma)(\mu+b)^2 .
$

これは $t=0$ でも連続で、割る量 $d,B$ は形の範囲で正である。

**横の曲率の因子を外す.** $\sigma=\ell_j^2-\ell_i^2$。球面で $e_i$ を $e_j$ へ向けて回す $R_\theta$ を使い、積分変数も $\xi=R_\theta\xi'$ と回す。すると $k$ は一定で、$d,B$ の行列は $R_\theta^T L^TL R_\theta,\ R_\theta^T(L^TL)^{-1}R_\theta$。$m=(\ell_i^2\ell_j^2)^{-1}$ と置いて $\theta=0$ で

$
d'=2\sigma w_iw_j,\quad d''=2\sigma(w_i^2-w_j^2),\quad
B'=-2\sigma m\xi_i\xi_j,\quad B''=-2\sigma m(\xi_i^2-\xi_j^2).
$

$a=2t/d$、$b=4mt\mu/B$、$U_2=w_j^2(a^2+b^2)$、$P^2=w_j^2(a+b)^2$、$S_2=2(t^2-w_j^2)/d-2m(\mu^2-4t^2 w_j^2)/B$ とする。ここで $d'/d=-\sigma a w_j$、$B'/B=-\sigma b w_j$。$\log\gamma$ の二階微分と連鎖律から

$
H_{ij}-T_i=\sigma C_{ij},\qquad
C_{ij}=\int_0^1\!\!\int_0^1 4t^3\left[
-\tfrac12\gamma F'S_2+
\sigma\left(\gamma F'(U_2/2+P^2/4)+\gamma^2F''P^2/4\right)
\right]dt\,dv.
$

ここで $C_{ij}$ は $\sigma=0$ でも右辺で定義し、一度も $\sigma$ で割らない。$T_i=0$ 上で $H_{ij}=\sigma C_{ij}$ である。赤道の組では $\sigma=\pm(1-y)(1+y)$ なので $b_p$ の角方向の退化は対称性から厳密。$j=z$ の $\sigma>0$ は軸長順と、候補Bの球・辺の零集合の情報から従う。$\partial_2$ は $z=1$ に達せず、$\partial_1$ は球を通らない。

**求積.** 式は既存の2点Gaussのセル積分と純四階剰余を用いる。$K_i$ の一次形微分と角度純四階を同時に取る場合の最大は $F^{(9)}$。旧正係数級数で $n\ge97,\ 0\le j\le9$ の係数の比は $n^2/[(2n+1)(n+1-j)]\le97/178<3/5$。従って旧と同じ97項目からの尾の倍率 $5/2$ を使える。MPFRは各演算を外向きに丸める。

## 5. 既知の退化、有効な条件、Claude Codeとの照合

- $Z_1,Z_2$ の他方の赤道中心固有値は $c_p$ 以外で零を持たない。v3の共有端点窓で $(A_y-A_x)/(1-y)<0$ が厳密なので、弧の連結性から $Z_1\setminus\{c_p\}$ で $A_x>0$、$Z_2\setminus\{c_p\}$ で $A_y<0$。$c_p$ では零固有値が二つある。
- $b_p$ では $T_y=T_x=0$ かつ赤道の横固有値が零。従って定理2の単純な孤立対の条件は成立しない。両共有端点での回転対称な辺の挙動は第一論文の回転族を参照する。$Z_1\cap\partial_2$ では中心と極が空間的に別なので、各局所定理をそれぞれ適用できる。[候補B採用裁定](https://github.com/cotaxxxx/bg-triaxial-family/blob/2d2576ee43f07a3cb94df28d63051f52649e3c81/evidence/chat/2026-11-27/JUDGE_RULING_CANDIDATE_B_ADOPTION.md) · [第一論文 v1.0](https://doi.org/10.5281/zenodo.24495446)

| Claude Code の条件（公開報告 命題3・4、層I–IV） | 今回の局所条件 |
|---|---|
| IV の形状横断 | 採用台帳の横断微分の厳密符号 |
| H3 の $W_3$ | 中心の $A_z$、極での長軸横成分の $H_{iz}=\sigma C_{iz}$ |
| H12 のせん断 $C_{12}^{\rm CC}$ | 中心のもう一方の固有値は採用弧と v3 の差から確定。極の本稿の $C_{ij}$ は $C_{12}^{\rm CC}(e_i)/(\ell_i\ell_j)$ |
| HB の軸方向の単調減少 | $\kappa_i(r)=E_i(re_i)/r=U_i(r^2)$ の端の量。$K_i=6\partial_x U_i(0)$、$M_i-T_i=2\partial_x U_i(1^-)$ |

最後の対応は $\partial_r(rU_i(r^2))=U_i+2r^2\partial_xU_i$ より従う。$0<r<1$ の狭義符号だけから端での非零は従わない。命題3のせん断恒等式を円弧方向に一度微分し極で評価すると、$H_{ij}-T_i=(\ell_j/\ell_i-\ell_i/\ell_j)C_{12}^{\rm CC}(e_i)$ になり、上表の尺度が一致する。11月27日の公開査読の「符号条件が必要」という指摘に対して、ここでは定理1・2とこの表で条件を明示する。命題4の全域の軸外排除・本数の仮定はこの局所検証の適用範囲と別である。[Claude Code の条件原本](https://github.com/cotaxxxx/bg-triaxial-family/blob/105a5c10fad8657ed654ff48abbffa2a10a59000/evidence/source-snapshots/claude-first-map/REPORT.md#L445) · [11月27日の査読記録](https://github.com/cotaxxxx/experimental-mathematics-ai-collaboration/blob/0854cd3e3de0fc5e2f87da2000cf1b39a14ff3a4/docs/PAPER_II_PRIOR_ART_SURVEY_NOTES_20261127.md)

## 6. 例外を局在する

既存帯で元の量を $P$、新しい検査量を $Q$ とする。横断方向 $v$ の $P_v$ が厳密符号を持ち、帯の両面で逆符号なので $P=0$ は $v=h(u)$（$u$ は帯に沿う変数）。子箱を $u$ だけで等分すれば、そのグラフの存在と一意性を継承できる。$Q$ が零を含む最終子箱で、両端断面の $Q$ と

$
\frac{d}{du}Q(u,h(u))=Q_u-Q_vP_u/P_v
$

を包む。単調で同符号なら零はなく、単調かつ厳密な符号反転なら、その子箱内に共通零が一つある。ここで $P_v$ は既存帯の区間を再利用する。

この判定が不十分なら、中心 $m$ の $[(P,Q)](m)$ と四つの微分の区間で $K=m-C[(P,Q)](m)+(I-C[J])(X-m)$ を求める。$C$ は区間ヤコビ行列の中点の有理逆行列。$K\subset\mathrm{int}\,X$、かつ $I-C[J]$ の最大行和上界 $q<1$ なら、縮小写像定理によりその箱内に共通零がただ一つ、像 $K$ に入る。複数の帯が同じ点を囲い得るので、台帳の局所証明の件数は零点の個数とみなさない。未確定は箱のまま残す。
