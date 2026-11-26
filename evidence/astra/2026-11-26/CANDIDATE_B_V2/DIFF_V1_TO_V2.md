# 候補 B 第1版から第2版への差分一覧

2026-11-26 JST · DIAGNOSTIC_ONLY

比較元は第1版計画 `f8c809f` と実行束 `f70b83b`。第2版は新しいディレクトリに置く。[第1版の束](https://github.com/cotaxxxx/bg-triaxial-family/tree/f70b83b24fc62b7bbd7b3d70b24163ab8bf8f779/evidence/astra/2026-11-26/CANDIDATE_B_BUNDLE) · [承認範囲](https://github.com/cotaxxxx/bg-triaxial-family/blob/bae282ee6d3decbca00a48afbc9bab7df9ad5467/evidence/chat/2026-11-26/ASTRA_SCOPE_CANDIDATE_B_V2_20261126.md)

| 項目 | 第1版 | 第2版と確認箇所 |
|---|---|---|
| 回数と時間 | 400万セル。旧パイロットの外挿式 | 1億400万セルと6時間。各量2,400万セル、共通800万。各量の追跡は内数800万。見積もりは最長並行ワーカーと直列相の和。`INPUTS.json`、`run_candidate_b.py`、独立検査の `review_pilot` |
| 中点幅 | 形の項の幅を中点幅と比較して早期二分 | 中点の共通部分に $\max(1/256,d_m/8)$ の幅条件。4,096セルまで幅を詰め、未達は未確定。`engine.py`、`shape.py`、独立検査の `read_enclosures`・`tree`・`overlap_check` |
| 帯の候補 | 未確定箱を起点に幅を合わせて試行 | その実行で証明した辺の根を起点に、前の帯から反符号の入口・出口をつないで試行。`trace_bands.py`、`shape.py`、独立検査の `trace_condition` |
| 初期箱と分割の順 | 行順に深さ優先 | 初期箱を24のまとまりに巡回。帯を置いた後、未確定箱を幅優先。`engine.spread_roots`、`Family.run`、独立検査の `review_schedule` |
| 交差に使う帯 | 必要に応じ比較用帯を追加試行 | 追跡済みの帯を選ぶ。支持が足りない場合は未確定。`crossings.py` の `atlas_chart` と重なり分割の可否を変更 |
| 台帳の追加項目 | 第1版の区間と根・帯・接続・交差 | `integrals.trace`、`enclosures.policy/split_ready`、`stages.midpoint_interval/midpoint_limit/midpoint_ok`、`edges.direction`、`charts.continuation`、`root_visit`・`trace_budget`・`trace_probe`・`trace_end`。新しい判定は有理端点で再確認 |
| 作業機の確認 | 人工台帳と球の値 | 第2版の人工台帳と順序・停止の方針。数値核は第1版からバイト単位で同じ。`smoke_policy_v2.py` |

`src/candidate.c`、`src/interval.h`、`src/jets.h`、`src/build_probe.c`、`build.sh` は第1版と同一。四量の定義と計算核、$R$、辺の照合条件、帯の三条件は第1版を適用する。接続の線分証明、交差の傾き差・同じ辺の根・全重なりの照合、および全葉の被覆から弧を判断する論理を引き継いでいる。

計算モジュールを import しない独立検査には、角度上限と回数、90パーセンタイルを使った時間見積もりの再構成、幅ゲートと帯の由来、初期巡回と深さ順のチェックを追加した。ソースの具体的な差分は [POLICY_CODE_V1_TO_V2.patch](POLICY_CODE_V1_TO_V2.patch)。実測と方針の対応は [第2版計画](PLAN_CANDIDATE_B_V2.md)。
