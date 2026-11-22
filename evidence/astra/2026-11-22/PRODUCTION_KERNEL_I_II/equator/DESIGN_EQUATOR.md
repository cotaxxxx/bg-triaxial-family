# 赤道帯の独立な H₃₃ 包囲の設計

2026-11-22 ・ DIAGNOSTIC_ONLY ・ chat 監査待ち。これは実行前の設計である。

## 帯を固定する

a=q₃ とし、球面の緯度の変数 v を使って高さを z=(v+a)/(1+av) と置く。すると z−a=(1−a²)v/(1+av) である。物理的な弦の鉛直成分 st(z−a) が消える位置は、どの a でも v=0 になる。a 微分を何回とってもこの成分は v の因子を保つ。元の緯度を固定して微分したときの −st という並進項を積分する必要がなくなる。ヤコビアン、横方向の長さと面積密度は a とともに変化するので、すべて変換後のエネルギーに入れてから微分する。変換後も両極は固定される。

V62 の 72 点では下端は 1.15 を超えたが、V62-B の根では五変数のうち a の幅への寄与が約 49,132、深い所では五つの寄与が同程度だった。V63-A で格子を増やしても九組すべてが予算切れだった。そこで帯の位置を固定し、正負の項をセルの積分と球面の和の段階で合算した後に、パラメータ幅を掛ける。加えて H₃₃ の偶対称性に基づき四階微分の包囲とも交差をとる。長軸の効果が消えるのは帯の並進に限る。残る変動幅、速さ、符号は今回の成果に数えない。

## 被覆と境界

- 形は s の 4 区間 [1+11i/20,1+11(i+1)/20]、t の 8 区間 [1+5j/8,1+5(j+1)/8] の閉直積。i=0,…,3、j=0,…,7。q は第一八分体の 1/32 セルを閉球、0≤a≤1/32 と交差させる。いずれの形でも同じ式を使える。E4 は指定の八組だけを測る。
- 実装では整数のセル添字で非空の交差を列挙する。左下隅のノルム二乗が 1 より大きい場合だけ除く。上隅が 1 未満なら内部用の変換を使う。それ以外は閉球と交わる部分を接触用の包囲で評価する。V60 の層・区分ラベルを保存し、接触する赤道の縁を内部 770 セルの実績に混ぜない。軸の点、原点、共有面も覆う。q₁、q₂、a による除算はない。
- 有理数の中点での二分割は親を閉じた子二つで正確に覆う。COVERED は全葉で下端が厳密に正、未処理領域が空、かつ分割台帳が根と一致したときに限る。接触層で上界が粗くて決まらなければ未解決のまま残す。
- 赤道面に関する鏡映対称性、∂₃E(q₁,q₂,0)=0 と微積分の基本定理により、垂直線分が閉球内にあるとき W₃=∫₀¹ H₃₃(q₁,q₂,ua)du。ここでの包囲は層 I の赤道帯を対象とする。

## 実装・監査の境目

実装予定は C の区間演算と多変数 Taylor 係数である。角度の局所積分、パラメータの合成、接触用の別評価は DERIVATION.md、実行時の規則は PLAN_TESTS_EQUATOR.md に定めた。報告の主体は Dig / ChatGPT（OpenAI、Astra）と Codex、実装・数値の監査は Claude（chat）と Claude Code、導出の査読は Fable 5.2、採否は Judge。以下は担当セッションによるアクセス履歴の自己申告である。独立セッションは新規の空の作業場から開始した。参照は以下の個別文書・結果に限り、旧移植・監査枝を含む v2.1 §0 の禁止物を開いていない。

|根拠|版と位置|
|---|---|
|指示 v2.0、v2.1、研究 PC 運用|c25ba7bc2b044356896e948f6201f8ade77eb06d の evidence/chat/2026-11-22/ASTRA_INSTRUCTION_C_PORT/ 内の当該三指示|
|原定義・勾配の補題 0|main 67eb2afdd3ccc0bb976302dbb68548b256b3fc45、evidence/source-snapshots/basepoint-v56-independent-map/REPORT.md §1|
|形の分割|同 main の evidence/chat-originals/2026-11-20/D_TRI_LAYER_I_II_CALIBRATION_V58/chat_checks/PLAN_V58.md|
|V60 の較正区分と根|c25ba7b の calibration/V60/input/unpacked/v60/PLAN_V60.md、samples_v60.json|
|V61 の実測・葉数|同版 evidence/chat/2026-11-21/D_TRI_LAYER_I_II_COMPLETION_V61/ の PLAN_V61.md、CHAT_VERIFY_D_TRI_LAYER_I_II_COMPLETION_V61.md、chat_checks/budget_v61_out.txt|
|V62 の点|同版 evidence/chat/2026-11-22/D_TRI_H33_EQUATOR_DIAG_V62/ の PLAN_V62_DIAG.md、CHAT_RESULT_V62_DIAG.md、out_A.jsonl|
|幅と格子の診断|同版 evidence/chat/2026-11-22/ の D_TRI_H33_TERMS_DIAG_V62B/CHAT_RESULT_V62B.md、D_TRI_V63A_GRID/CHAT_VERIFY_V63A.md、D_TRI_V63A_GRID/chat_checks/grid_test_box.md|
