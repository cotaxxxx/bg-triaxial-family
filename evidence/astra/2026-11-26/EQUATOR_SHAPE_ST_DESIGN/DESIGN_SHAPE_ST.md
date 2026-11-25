# 赤道帯 H₃₃ の形状二方向の包囲設計

2026-11-26 JST · DIAGNOSTIC_ONLY · 事前登録・chat 差分監査待ち

Judge 裁定 900b3f7 §2 による設計である。対象は赤道帯の内部箱での $H=H_{33}=\partial_a^2 E$ と、形状変数 $s,t$ の幅に限る。現行方式の規則は Astra の現行導出・計画から取った。現行計画には旧 Reader の参考幅の記載がある。数値根拠は E4 の R2 台帳 981adf5 の Astra 区間に限る。[Judge 裁定](https://github.com/cotaxxxx/bg-triaxial-family/blob/900b3f700e257104fea5cad309667e2729edd151/evidence/chat/2026-11-26/JUDGE_RULING_AFTER_E4_20261126.md) · [R2 集計](R2_OBSERVATIONS.md)

## 1. 選んだ設計

位置を箱の有理中点に固定して $H$ を形状箱の四隅で包囲する。四隅の双線形補間に、$s,t$ の純二階微分による符号付きの剰余を加える。位置の箱幅は現行の一次の平均値形式で戻す。形状側の上下界はそれぞれ二変数の二次式としてまとめ、箱全体で極値を取る。

E4 で最終の 2,048 基本面まで評価して二分割に進んだ 345 箱すべてで、中心式の幅に対する最大寄与は $s$ または $t$ だった。二方向合計の比率は中央値 75.71%、最小 65.17%。同じ 345 箱の $I_s,I_t$ はともに零を含んだ。ここでの幅は現行の包囲で計上した幅である。真の勾配の符号や箱上の変動幅には別の評価が要る。[R2 集計](R2_OBSERVATIONS.md)

| 候補 | 今回の判断 |
|---|---|
| 形状方向の単調性を示して端へ寄せる | 現行の導関数区間で使える箱は集計した 345 箱にはなかった。別の式で符号を示せる可能性は残る。 |
| 形状中点での二次 Taylor 式 | 中点値、二つの中点勾配、三つの Hessian 成分で包める。混合項や一次項を独立な区間にすると、符号による相殺を失いやすい。 |
| 四隅の双線形補間と純二階剰余 | $st$ 型の変動を補間が厳密に再現する。剰余は形状幅の二乗で、混合微分と形状方向の単調性を仮定する必要がない。形状比の構造は純二階微分の包囲に使う。 |

四隅を採る理由は剰余の次数と、混合項を補間の中で保持できる点である。二階微分の評価が広い場合、包囲が縮まるかどうかは別途測定が必要になる。

## 2. 位置の変動を戻す

1. 形状箱を $S=[s_0,s_1]\times[t_0,t_1]$、位置箱を $X=X_1\times X_2\times X_a$ とし、$Q=(q_1,q_2,a)$、位置中点 $m=(m_1,m_2,m_a)$ とする。$h(s,t)=H(s,t,m)$、$d_s=s_1-s_0,\ d_t=t_1-t_0$ とする。以下は $s,t\ge1$、現行の $|a|\le 1/32$、かつ $\rho_*\ge\sup_{Q\in X}|Q|$ を $\rho_*<1$ と保証できる箱に適用する。
2. $J_i$ を $\partial_{Q_i}H$ の $S\times X$ 上の包囲とする。現行導出 §3 式19 と同様、角度積分を行ってから位置の変位を掛ける。各 $(s,t,Q)$ で固定した $s,t$ に対し、線分 $m+\tau(Q-m)$ は $X$ にある。微積分の基本定理より次式を得る。[現行導出 §3](https://github.com/cotaxxxx/bg-triaxial-family/blob/900b3f700e257104fea5cad309667e2729edd151/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/DERIVATION.md)

   $$
   H(s,t,Q)-h(s,t)
     =\sum_{i\in\{1,2,a\}}(Q_i-m_i)\int_0^1 \partial_{Q_i}H(s,t,m+\tau(Q-m))\,d\tau
     \ \in\ J_{\rm pos}:=\sum_i (X_i-m_i)J_i. \tag{1}
   $$

   幅が零の位置方向の項は厳密に零である。

## 3. 形状側の剰余と極値

3. $d_s,d_t>0$ なら $u=(s-s_0)/d_s,\ v=(t-t_0)/d_t$、$b_0(x)=1-x,\ b_1(x)=x$ とする。$C_{ij}=[c^-_{ij},c^+_{ij}]$ は $h(s_i,t_j)$ の包囲。$L_s,L_t$ をそれぞれ端点値からの一次補間とすると、$L_sL_t h=\sum_{i,j=0}^1 b_i(u)b_j(v)h(s_i,t_j)$。四つの重みは非負で和が 1 である。
4. 一変数区間 $[l,r]$ の内部 $x$ で、$c=(g(x)-Lg(x))/((x-l)(x-r))$ と置く。$g(y)-Lg(y)-c(y-l)(y-r)$ は $l,x,r$ で零。Rolle の定理を二回使うと $g''(\zeta)=2c$ となる $\zeta\in(l,r)$ がある。よって $g(x)-Lg(x)=-\tfrac12(x-l)(r-x)g''(\zeta)$。端では差が零である。
5. $K_s=[k_s^-,k_s^+]$ と $K_t=[k_t^-,k_t^+]$ は、それぞれ $S$ 全体での $h_{ss}$ と $h_{tt}$ の包囲とする。$I-L_sL_t=(I-L_s)+L_s(I-L_t)$。最初の項は $t$ を固定して手順4を適用する。第二項では $s=s_0,s_1$ の双方で手順4を適用し、$s$ の補間で足す。$L_s$ は非負の重みによる平均なので、第二項にも共通の $K_t$ が使える。よって各 $(u,v)$ について

   $$
   h-L_sL_t h \in -\omega_s(u)K_s-\omega_t(v)K_t,
   \quad \omega_s(u)=\tfrac12 d_s^2 u(1-u),\quad
   \omega_t(v)=\tfrac12 d_t^2 v(1-v). \tag{2}
   $$

   $\omega_s,\omega_t\ge0$ のため、下界は曲率区間の上端、上界はその下端を使う。曲率区間の上端が負なら、その方向の剰余によって補間の下界が上がる。
6. $Q_-(u,v)=\sum b_i(u)b_j(v)c^-_{ij}-\omega_s(u)k_s^+-\omega_t(v)k_t^+$、$Q_+(u,v)=\sum b_i(u)b_j(v)c^+_{ij}-\omega_s(u)k_s^--\omega_t(v)k_t^-$ と置く。手順3と式 (2) より $Q_-\le h\le Q_+$。式 (1) と合わせ、採用する形状・位置の包囲は

   $$
   I_{\rm shape,pos}=
     \left[\min_{[0,1]^2} Q_-,\ \max_{[0,1]^2} Q_+\right]+J_{\rm pos}. \tag{3}
   $$

   $d_s=0$ の場合は一致する四隅の $s$ 側の二対に同じ区間を使い、$u=0,\ \omega_s=0$ とする。これで $Q_\pm$ は $u$ に依存しない。$t$ も同様で、両幅が零なら角の一評価のみで形状側を包む。
7. 四隅の値を $z_{ij}$、剰余式で用いる曲率端点を $k_s,k_t$ としたとき、二次式の係数は以下となる。

   $$
   \begin{aligned}
   \alpha_s&=d_s^2 k_s/2, & \alpha_t&=d_t^2 k_t/2,\\
   Q(u,v)&=z_{00}+(z_{10}-z_{00}-\alpha_s)u+(z_{01}-z_{00}-\alpha_t)v\\
         &\quad+\alpha_s u^2+(z_{11}-z_{10}-z_{01}+z_{00})uv+\alpha_t v^2.
   \end{aligned} \tag{4}
   $$

8. $Q_-,Q_+$ それぞれで四隅、四辺上で一次導関数が零になる内点、正則な Hessian の場合は二本の一次方程式 $\nabla Q=0$ の解が箱の内点ならその点を評価する。辺の二次係数が零なら辺の端で足りる。Hessian が特異で内部に臨界点がある場合は、その点から零空間方向に境界まで動いても二次式の値は一定である。よって境界候補で足りる。有限な MPFR の端点をちょうどの二進有理数として受け取り、箱の有理端点とともに係数・行列式・候補点・候補値を有理数で計算する。極値を取った後、下端を下向き、上端を上向きに変換し、$J_{\rm pos}$ の加算も外向きに丸める。

簡単な事前指標も得られる。角の区間を $W_c=\max c^+_{ij}-\min c^-_{ij}$ とまとめ、$0\le\omega_\sigma\le d_\sigma^2/8$ を用いると、式 (3) の丸め前の幅は次を超えない。

$$
W_c+\sum_{\sigma\in\{s,t\}}\frac{d_\sigma^2}{8}\bigl(\max(0,k_\sigma^+)-\min(0,k_\sigma^-)\bigr)
    +\operatorname{diam}J_{\rm pos}. \tag{5}
$$

現行中心式の形状側の幅は丸め前に $\operatorname{diam}I_0+\sum_{\sigma\in\{s,t\}}d_\sigma\sup|I_\sigma|$。式 (5) は中心式を置き換える効果を測る指標に使える。直接式・偶関数式と交差した結果については、その交差後の幅も別に測る。

## 4. 純二階微分を形状比から導く

9. $L=\operatorname{diag}(1,s,st)$、$k=1-q\cdot\xi$、$D=|L(\xi-q)|$、$b=|L^{-1}\xi|$、$F(\gamma)=\arccos^2\gamma$、$\gamma=k/(Db)$。現行導出 §1 と同じ緯度経度の変換を使う。$q=Q$、$\xi$ とヤコビアン $J$ は $a$ に依存する。角度 $(\lambda,\phi)$ を固定したとき、$\xi,J,k$ は $s,t$ に依存しない。$G=Jk F(\gamma)/(4\pi)$ に対して $H=\int G_{aa}\,d\lambda\,d\phi$。[現行導出 §1](https://github.com/cotaxxxx/bg-triaxial-family/blob/900b3f700e257104fea5cad309667e2729edd151/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/DERIVATION.md)
10. $X_i^\xi=(\xi_i-q_i)^2,\ Y_j=\xi_j^2$、$w=(1,s^2,s^2t^2)$ とする。垂直成分 $\xi_3-a$ には現行導出 §1 式3の積の形を使える。平方積 $\mathcal P=D^2 b^2$ は次の九項の和である。

    $$
    \begin{aligned}
    \mathcal P&=\left(\sum_i w_iX_i^\xi\right)\left(\sum_j w_j^{-1}Y_j\right)
      =\sum_{i,j} Z_{ij},\\
    Z_{ij}&=X_i^\xi Y_j s^{\alpha_{ij}}t^{\beta_{ij}},\\
    \alpha_{ij}&=2(\mathbf 1_{i\ge2}-\mathbf 1_{j\ge2}),\qquad
    \beta_{ij}=2(\mathbf 1_{i=3}-\mathbf 1_{j=3}).
    \end{aligned} \tag{6}
    $$

    $Z_{ij}\ge0$。また $D\ge1-\rho_*$、$b\ge1/(s_1t_1)$ より $\mathcal P\ge(1-\rho_*)^2/(s_1t_1)^2>0$。分母の定数項にこの下界を使える。
11. $\sigma=s$ または $t$ を一つ固定する。その変数の指数 $-2,0,2$ ごとに式 (6) を $P_-,P_0,P_+$ にまとめる。各単項式を微分すれば次式を得る。

    $$
    \sigma \mathcal P_\sigma=2(P_+-P_-),\qquad
    \sigma^2 \mathcal P_{\sigma\sigma}=2P_++6P_-. \tag{7}
    $$

    $A_\sigma=\sigma\mathcal P_\sigma/\mathcal P$、$B_\sigma=\sigma^2\mathcal P_{\sigma\sigma}/\mathcal P$。非負の三群の和が $\mathcal P$ なので、$A_\sigma\in[-2,2]$、$B_\sigma\in[0,6]$。区間 Taylor 計算ではこの範囲と交差する対象は $A_\sigma,B_\sigma$ の定数項である。
12. $\gamma=k\mathcal P^{-1/2}$ を形状方向に二回微分する。$k$ は固定なので、$\gamma_\sigma=-\gamma A_\sigma/(2\sigma)$、$\gamma_{\sigma\sigma}=(\gamma/\sigma^2)T_\sigma$。ここで $T_\sigma=3A_\sigma^2/4-B_\sigma/2$。連鎖律 $\partial_{\sigma\sigma}F(\gamma)=F''(\gamma)\gamma_\sigma^2+F'(\gamma)\gamma_{\sigma\sigma}$ を代入すると

    $$
    G_{\sigma\sigma}=\frac{Jk}{4\pi\sigma^2}
      \left(\frac{\gamma^2}{4}F''(\gamma)A_\sigma^2
        +\gamma F'(\gamma)T_\sigma\right). \tag{8}
    $$

13. 式 (8) 全体を $a$ で二回微分し、その後に $Q=m$ を代入する。$J,k,\xi$ の $a$ 依存性も含む。手順1と10の正の下界、$1+a\sin\lambda>0$、$F$ の $\gamma=1$ での正則延長により、必要な導関数は箱と角度矩形の積の上で連続・有界である。微分の交換と積分下の微分が許されるので

    $$
    h_{\sigma\sigma}(s,t)=\left.\int\partial_a^2 G_{\sigma\sigma}(s,t,Q)\,d\lambda\,d\phi\right|_{Q=m}. \tag{9}
    $$

    $K_\sigma$ は式 (9) を $S\times\{m\}$ 上で角度積分して得る区間とする。角度を $\pi$ 単位にする場合は被積分関数と節点・剰余で現行の面積変換を使う。必要な $F^{(j)}$ は最大 $j=2+2+4=8$（式 (8) の $F''$、$a$ 二階、角度純四階）。この階数まで現行導出 §2 式9–10 の級数剰余が適用できる。平方根や逆数の幾何学的下界、$\gamma\in[0,1]$ は各 Taylor 展開の定数項の範囲評価に用いる。各微分係数は元の恒等式で包む。[現行導出 §2・§5](https://github.com/cotaxxxx/bg-triaxial-family/blob/900b3f700e257104fea5cad309667e2729edd151/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/DERIVATION.md)
14. 式 (8) の $T_\sigma$ の定数項には、同じ三群の比を使ってさらに幅を抑えられる。$x=(P_+-P_-)/\mathcal P$、$y=(P_++P_-)/\mathcal P$ とすると $|x|\le y\le1$、$A_\sigma=2x$、$B_\sigma=4y-2x$。よって $T_\sigma=3x^2+x-2y$。下界は $3x^2+x-2=3(x+1/6)^2-25/12$。上界は $3x^2+x-2|x|$ であり、$0\le x\le1$ では $3x^2-x\le2x\le2$、$-1\le x\le0$ では $3x(x+1)\le0$。従って $T_\sigma\in[-25/12,2]$ である。端を外向きに変換して定数項と交差させる。

## 5. 現行方式との接続と差分監査

- 内部箱では、四隅の $C_{ij}$、二つの $K_\sigma$、三つの位置微分 $J_i$ を、現行の角度積分の基本木規則、外向き丸め、符号付き剰余、方向別小矩形によってそれぞれ求める。基本木の選択は各被積分関数に対する現行規則を適用する。式 (3) は現行の中心式の位置項を引き継いだ代替式とし、同一箱での直接式・偶関数式および段階間の共通部分を取る。空交差は INCONSISTENT。必要な値が非有限なら現行計画の未完扱いに従う。接触経路には現行導出 §4 を使い、式 (9) の境界への延長は仮定しない。[現行導出](https://github.com/cotaxxxx/bg-triaxial-family/blob/900b3f700e257104fea5cad309667e2729edd151/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/DERIVATION.md) · [現行 E1–E4 計画](https://github.com/cotaxxxx/bg-triaxial-family/blob/900b3f700e257104fea5cad309667e2729edd151/evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator/PLAN_TESTS_EQUATOR.md)
- 非退化の内部箱を一段階まで評価すると、従来の 9 積分は形状・位置の中点値 1、形状勾配 2、位置勾配 3、直接・偶関数用 3。本案は四隅 4、形状曲率 2、位置勾配 3、直接・偶関数用 3 の計 12。旧・新を同じ箱で測る場合、共通の 6 を再利用できれば計 15。角度の四階微分を含む曲率積分の費用は一律でないため、この計数から時間比は出ない。
- 今後実装を別途承認された場合の比較に、同じ物理箱と角度段階での $C_{ij},K_s,K_t$、式 (5) の二方向の幅、式 (3) の幅、現行中心式と直接・偶関数との各交差後の幅、正の下端を得た箱数、角度評価回数と実時間を提案する。零幅方向、曲率符号の交差、特異 Hessian の極値も差分監査の対象とする。算出不能な行も残す。試験の対象と予算は実装を依頼された時点で事前に固定し、差分監査を経る。核を変える場合は Judge 裁定 §2 に従って E1〜E3 をやり直す。

本登録に含む確認は [人工入力での有理数検査](synthetic_shape_check.py) に限る。結果は [実行記録](SYNTHETIC_CHECK.txt)。ここで検査するのは式 (3)・(4) の極値評価と式 (6)–(8) の形状微分の代数である。実際の $H_{33}$ に対する包囲の幅や時間は未測定である。

同じディレクトリで以下を実行できる。人工入力はすべてスクリプトに固定している。

```sh
python3 -B synthetic_shape_check.py | diff -u SYNTHETIC_CHECK.txt -
sha256sum -c SHA256SUMS.txt
```
