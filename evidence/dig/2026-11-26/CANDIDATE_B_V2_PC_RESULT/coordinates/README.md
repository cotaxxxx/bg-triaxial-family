# Open shape boxes: exact coordinates
Source: original RESULT/pending.jsonl and RESULT/boxes.jsonl; counts checked against RESULT/LEDGER_INSPECTION.json.
One CSV per quantity. Each row is one unique shape box, with exact rational endpoints y_min,y_max,z_min,z_max, node/root/depth and source ledger IDs. PENDING is CELL_BUDGET (no completed box node); UNRESOLVED is DEPTH_LIMIT (matching depth-18 node). Rows are sorted by y_min,z_min,y_max,z_max,node. No numerical reevaluation, no interpretation.
Three pending records contain no box coordinates (two worker-level budget notices and one intersection notice); preserved separately in noncoordinate_pending.json. D1/D2 correspond to partial_1/partial_2.
