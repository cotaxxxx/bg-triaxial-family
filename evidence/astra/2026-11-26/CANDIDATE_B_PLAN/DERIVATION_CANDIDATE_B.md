# 候補 B｜中心曲率と極点トレースの導出

2026-11-26 JST · DIAGNOSTIC_ONLY · 計算前の事前登録

形は $x=1,\ 0<y\le1\le z$、参照球座標の順は $(q_x,q_y,q_z)$ とする。以下の恒等式と剰余は解析的な導出である。四つの積分の符号、零集合の位置、計算時間はこれからの検証対象である。[Judge の承認範囲](https://github.com/cotaxxxx/bg-triaxial-family/blob/5b4235423a5fef8e09bd6976a05eaf6ad6dfbfdf/evidence/chat/2026-11-26/ASTRA_SCOPE_CANDIDATE_B_PLAN_20261126.md) · [固定した形の記法](https://github.com/cotaxxxx/experimental-mathematics-ai-collaboration/blob/ad48e66afe1cc3a30c18d721cccbb6dae05414ec/docs/PAPER_II_SHAPE_MAP_CONVENTION_20261125.md)

## 1. 定義と軸の読み替え

1. $L=\operatorname{diag}(\ell_x,\ell_y,\ell_z)=\operatorname{diag}(1,y,z)$、物理点は $p=Lq$ とする。$\xi\in S^2$、$k=1-q\cdot\xi$、$D=|L(\xi-q)|$、$B=|L^{-T}\xi|^2$、$\gamma=k/(D\sqrt B)$、$F(\gamma)=\arccos^2\gamma$。$E(q)=\langle kF(\gamma)\rangle$、$\langle\cdot\rangle=(4\pi)^{-1}\int_{S^2}(\cdot)\,dS$。第一論文 (2.4)–(2.5) と同じ参照球表示である。実際、境界点 $L\xi$ の面積要素は $\det L\sqrt B\,dS$、弦の法線成分は $k/\sqrt B$、三倍の体積は $4\pi\det L$。したがって cone-volume の重みは $k\,dS/(4\pi)$ となる。[第一論文 v0.5.7 英語正本 §§2.2–3.1](https://github.com/cotaxxxx/bg-spheroid-family/blob/2009fda4c1393349408f354dd4a6fc518ab16806/manuscripts/2026-11-24/Paper_I_v0_5_7_audit_fixes/Paper_I_v0_5_7_Audit_Fixes_Integrated_EN.pdf)
2. V56 の軸は $(1,s,st)$、順に短軸・中間軸・長軸。全体の $1/s$ 倍と初めの二軸の交換で $(x,y,z)=(1,1/s,t)$、参照球では $(q_x,q_y,q_z)=(q_2^{\rm V56},q_1^{\rm V56},q_3^{\rm V56})$。相似変換で $\gamma,k$ は不変、軸の入れ替えは球面平均を保つ。体積 $4\pi/3$ に対応する物理座標は $p=(yz)^{-1/3}Lq$。物理量へ換算すると中心 Hessian の各対角成分には対応する半軸の逆二乗、極点の各勾配成分には逆半軸が掛かる。以下の台帳は参照球での値を用いる。[V56 固定報告 §§1.1–1.4](https://github.com/cotaxxxx/bg-triaxial-family/blob/67eb2afdd3ccc0bb976302dbb68548b256b3fc45/evidence/source-snapshots/basepoint-v56-independent-map/REPORT.md)
3. $A_i(y,z)=\partial_{q_iq_i} E(0)$、$T_i(y,z)=g_{\partial,i}(e_i)$ とする。$g_\partial$ は第一論文の定義2.1と同じ内側からの全勾配の連続トレース。鏡映により中心は停留点、Hessian は対角である。$e_i$ を固定する二つの鏡映により、$g_\partial(e_i)$ の他の二成分は零。従って $T_i=0$ と $g_\partial(e_i)=0$ は同値で、負の極 $-e_i$ の条件も同じである。

| 量の ID | 積分する量 | 対応する軸 | 零集合 |
|---|---|---|---|
| `Z1` | $A_y$ | V56 $e_1$、短軸 | $Z_1$ |
| `Z2` | $A_x$ | V56 $e_2$、中間軸 | $Z_2$ |
| `D1` | $T_y$ | V56 $e_1$、短軸 | $\partial_1$ |
| `D2` | $T_x$ | V56 $e_2$、中間軸 | $\partial_2$ |

一つの軸を単位長にし、残る半軸を $(u,v)$ とした主関数を $M_A(u,v)$、$M_T(u,v)$ と書く。どちらも $u,v$ の交換で不変である。$A_y,T_y$ の引数は $(1/y,z/y)$、$A_x,T_x$ の引数は $(y,z)$。以下の式では元の $\ell$ を使うので、台帳上で主関数の軸番号に読み替える必要はない。

## 2. 中心の曲率

4. $q=0$ で $S_j=\xi_j^2$、$d=\sum_j\ell_j^2 S_j=D(0)^2$、$B=\sum_j\ell_j^{-2}S_j$、$U_i=\ell_i^2/d$、$\gamma_0=(dB)^{-1/2}$ とする。$\xi$ を固定した $q_i$ 微分では $k_i=-\xi_i$、$(D^{-1})_i(0)=U_i\xi_i/D(0)$、$(D^{-1})_{ii}(0)=(3U_i^2 S_i-U_i)/D(0)$。$\gamma=kD^{-1}B^{-1/2}$ に積の微分を使うと

   $$
   \gamma_i(0)=\gamma_0(U_i-1)\xi_i,\qquad
   \gamma_{ii}(0)=\gamma_0\bigl((3U_i^2-2U_i)S_i-U_i\bigr).
   $$

   $\partial_{ii}(kF)=kF''\gamma_i^2+kF'\gamma_{ii}+2k_i F'\gamma_i$ より、中心の被積分関数は

   $$
   \mathcal A_i
   =\gamma_0^2 F''(\gamma_0)S_i(U_i-1)^2
    +\gamma_0 F'(\gamma_0)\bigl[S_i(3U_i^2-4U_i+2)-U_i\bigr]. \tag{1}
   $$

   $D(q)\ge y(1-|q|)$、$\sqrt B\ge1/z$。中心近傍で形を有限範囲に限定すればこれらは一様に正で、§4 の $F$ の正則性により二階微分と積分を交換できる。
5. マークした軸 $i$ と残りの $m,n$ に対し、$\xi_i=\mu$、$S_i=\mu^2$、$S_m=(1-\mu^2)\cos^2\phi$、$S_n=(1-\mu^2)\sin^2\phi$、$\phi=\pi w/2$ とする。面積は $d\mu\,d\phi$。式 (1) は各座標の二乗だけに依存するため、$\mu$ を半分、$\phi$ を一象限に縮めると

   $$
   A_i(y,z)=\int_0^1\!\!\int_0^1\mathcal A_i(\mu,w;y,z)\,d\mu\,dw. \tag{2}
   $$

   被積分関数には $\sqrt{1-\mu^2}$ が現れない。$d\ge y^2,\ B\ge z^{-2}$ に加え、積には

   $$
   dB=1+\sum_{j<k}S_jS_k\bigl(\ell_j/\ell_k-\ell_k/\ell_j\bigr)^2\ge1 \tag{3}
   $$

   が成り立つ。これは $dB$ を展開して $(\sum_j S_j)^2=1$ を引けば得られる。Taylor 形式の定数項の下界に使える。

## 3. 極点のトレース

6. 固定した $\xi$ で $D_i=-\ell_i^2(\xi_i-q_i)/D$。$\partial_i\gamma=-\xi_i/(D\sqrt B)+\gamma\ell_i^2(\xi_i-q_i)/D^2$ を使い、

   $$
   \partial_{q_i}(kF)=-\xi_i(F+\gamma F')
       +\frac{k\ell_i^2(\xi_i-q_i)}{D^2}\,\gamma F'. \tag{4}
   $$

   $0\le k\le|\xi-q|$、$|\xi_i-q_i|\le|\xi-q|$、$D\ge y|\xi-q|$。二項目の係数の絶対値は $z^2/y^2$ 以下。$F,F'$ は $[0,1]$ 上で有界である。よって形のコンパクトな範囲では一様な優関数があり、$q\to e_i$ を積分内に通せる。唯一起こり得る接触点 $\xi=e_i$ は面積零である。
7. $q=e_i$、$\mu=\xi_i=1-2r^2$、$0\le r\le1$ とする。$k=2r^2$、$\xi_i-1=-k$、$\phi=\pi w/2$。次の二つの正の量を使う。

   $$
   \begin{aligned}
   d_i(r,w) &= (1-r^2)(\ell_m^2\cos^2\phi+\ell_n^2\sin^2\phi)+r^2\ell_i^2,\\
   B_i(r,w) &= \mu^2/\ell_i^2
     +4r^2(1-r^2)(\ell_m^{-2}\cos^2\phi+\ell_n^{-2}\sin^2\phi).
   \end{aligned} \tag{5}
   $$

   $D^2=4r^2d_i$、$B=B_i$、$\gamma_i^*=r/\sqrt{d_i B_i}$。$\mu^2+4r^2(1-r^2)=1$ により $d_i\ge y^2,\ B_i\ge z^{-2}$。幾何から $0\le\gamma_i^*\le1$ であり、$r=0$ まで式で延長できる。式 (4) の二項目は $\xi_i-1=-k$ と $D^2$ を代入すると分母の $r^2$ が消える。従って

   $$
   \begin{aligned}
   \mathcal T_i(r,w)
       &= -\mu\bigl(F(\gamma_i^*)+\gamma_i^*F'(\gamma_i^*)\bigr)
          -\frac{\ell_i^2r^2}{d_i}\gamma_i^*F'(\gamma_i^*),\\
   T_i(y,z)&=\int_0^1\!\!\int_0^1 2r\,\mathcal T_i(r,w;y,z)\,dr\,dw.
   \end{aligned} \tag{6}
   $$

   $|d\mu|=4r\,dr$ と $\phi$ の一象限への縮約が $2r$ の起源である。$\mu$ の両半球を $r\in[0,1]$ に含む。接触 $r=0$ でも $d_i,B_i$ は正で、$2r\mathcal T_i$ と必要な角度・形微分を連続に評価できる。ここでの $T_i$ は第一論文の境界規約に従う全勾配の成分である。

## 4. 形微分、端点と求積の剰余

8. 形方向 $\sigma=y$ または $z$ の微分は (1)–(6) の固定領域表示に対して行う。方向 $\sigma$ に対応する半軸 $\ell_j=\sigma$ だけが変わるので、$\partial_\sigma\ell_j^2=2\sigma$、$\partial_\sigma\ell_j^{-2}=-2\sigma^{-3}$。$Q=dB$ または $d_iB_i$、$\gamma=k_*/\sqrt Q$（中心 $k_*=1$、極点 $k_*=r$）に対し $\gamma_\sigma=-\gamma Q_\sigma/(2Q)$。$U_{i,\sigma}=(\partial_\sigma\ell_i^2)/d-U_i d_\sigma/d$、極点の $\ell_i^2r^2/d_i$ も同じ商の微分で求める。これらと $(F^{(j)}(\gamma))_\sigma=F^{(j+1)}(\gamma)\gamma_\sigma$ で $\partial_y,\partial_z$ の両被積分関数を一意に定める。これらも有界な連続関数なので積分の微分と一致する。
9. $b=1-\gamma\in[0,1]$ とし、$F(\gamma)=\sum_{n\ge1}c_n b^n$、$c_1=2$、$c_{n+1}=c_n n^2/[(n+1)(2n+1)]$ を使う。$F=4(\arcsin\sqrt{b/2})^2$ より現行導出 §2 の係数式になる。$F^{(j)}=(-1)^j\sum_{n\ge\max(1,j)}c_n(n)_j b^{n-j}$。$j\le7$ なら $n\ge64$ の係数比は $n^2/[(2n+1)(n+1-j)]\le32/57<3/5$。$n=96$ までを計算し、符号を付ける前に $[0,(5/2)c_{97}(97)_j\,(\sup b)^{97-j}]$ を加える。定数項の $\gamma$ の区間と $[0,1]$ を交差してよい。合成の微分係数は連鎖律の区間で求める。中心には $F''$、極点には $F'$ が現れる。形一次・角度純四次までで必要な次数はそれぞれ $2+1+4=7$、$1+1+4=6$。[現行導出 §2](https://github.com/cotaxxxx/bg-triaxial-family/blob/5b4235423a5fef8e09bd6976a05eaf6ad6dfbfdf/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/DERIVATION.md)
10. 任意の対象被積分関数を $G$ とし、角度矩形の辺長を $d_1,d_2$、面積を $S=d_1d_2$ とする。各方向の二節点は中点 $\pm d_j/(2\sqrt3)$、重みは $1/2$。一次元で値と一次微分を節点で合わせる三次 Hermite 補間の剰余は $G^{(4)}(\zeta)(x-x_-)^2(x-x_+)^2/24$。正規化積分でこの非負の重みの平均は $d_j^4/4320$。求積は三次式まで正確で、二節点で補間との差は零。従って正規化積分 $A_j$ と二節点演算 $Q_j$ の差に $d_j^4[G^{(4)}]/4320$ を使える。二次元では $A_1A_2-Q_1Q_2=(A_1-Q_1)A_2+Q_1(A_2-Q_2)$。各平均の重みは非負、和は1なので、矩形の積分区間は

   $$
   S\,Q_1Q_2G+\frac{S}{4320}
      \bigl(d_1^4[\partial_1^4G]+d_2^4[\partial_2^4G]\bigr). \tag{7}
   $$

   角括弧は当該セルと形箱の全域の包囲。節点と係数を外向きに丸め、自然区間 $S[G]$ と交差させ、分割したセルの寄与を足す。$\partial_1,\partial_2$ はここでは積分変数の微分である。一次元の辺の簡約でも同じ剰余の導出を使う。[現行導出 §§3・5](https://github.com/cotaxxxx/bg-triaxial-family/blob/5b4235423a5fef8e09bd6976a05eaf6ad6dfbfdf/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/DERIVATION.md)

## 5. 回転辺と球の解析照合

- 扁平辺 $z=1$ では短軸 $y$ が対称軸で $\lambda=y$。第一論文の $(\rho,\zeta)$ の縦座標 $\zeta$ はこの短軸の参照球座標である。$A_y=a_c(\lambda)=\partial_\zeta^2 E_\lambda(0,0)$、$T_y=B_o(\lambda)=\partial_\zeta E_\lambda(0,1^-)$。$A_x$ は横方向の $h_c(\lambda)$、$T_x$ は赤道の半径方向トレース $h_b(\lambda)$ と同じ形である。
- 扁長辺 $y=1$ では長軸 $z$ が対称軸で $\lambda=z$。$x,y$ は同じ赤道の方向だから $A_x=A_y=h_c(\lambda)=\lim_{\rho\downarrow0}\partial_\rho E_\lambda(\rho,0)/\rho$。$T_x=T_y=h_b(\lambda)=\lim_{\rho\uparrow1}\partial_\rho E_\lambda(\rho,0)/\rho$。後者では分母は 1 に近づく。ここで $a_c(\lambda)$ は第一論文 v0.5.7 の軸方向の曲率関数で、閾値は $c_o,c_p$ と書く。[第一論文 §§2.2–3.1、表1](https://github.com/cotaxxxx/bg-spheroid-family/blob/2009fda4c1393349408f354dd4a6fc518ab16806/manuscripts/2026-11-24/Paper_I_v0_5_7_audit_fixes/Paper_I_v0_5_7_Audit_Fixes_Integrated_EN.pdf)
- 中心の式 (2) はどちらの回転辺でも一次元にできる。対称軸を緯度軸に取り $\mu=|\xi_{\rm sym}|$ とすると $d,B,U_i$ は $\mu$ の関数となる。式 (1) は $S_i$ に関してアフィンなので、$S_i$ を対称軸なら $\mu^2$、横方向なら $(1-\mu^2)/2$ として $\mu$ を積分する。極点の式 (6) が一次元になるのはマークした軸が対称軸のときで、今回の辺の照合では $z=1$ の $T_y$ が該当する。
- 球 $(y,z)=(1,1)$ では式 (1) は $2(1-S_i)$。従って $A_i=4/3$。式 (6) は $d_i=B_i=1,\ \gamma_i^*=r$ なので $T_i=\int_0^1 2r[-(1-2r^2)F(r)-(1-r^2)r F'(r)]\,dr$。第二項を部分積分すると $\int_0^1(2r-4r^3)F(r)\,dr$ となる。もう一度部分積分し $r=\cos\theta$ とおくと $2\int_0^{\pi/2}\theta\cos^2\theta\sin^2\theta\,d\theta=\pi^2/32$。球での回帰照合の基準にする。

## 6. 事前登録時の代数検査

人工例 $L=\operatorname{diag}(1,7/9,8/5)$、$\xi=(1/3,2/3,2/3)$、$F(\gamma)=\gamma^2$ を使い、式 (1) を各軸方向の $k^3/(D^2 B)$ の有理 Taylor 係数と照合した。極点では $r=3/5$、$\sqrt{1-r^2}=4/5$、$(\cos\phi,\sin\phi)=(3/5,4/5)$ を使い、式 (5)–(6) と変形前の式 (4) を三方向で照合した。すべて有理数で一致した。式 (7) の一次元の重みの積分も有理数で確認した。実際の角度エネルギーの四積分は今後の実計算で評価する。
