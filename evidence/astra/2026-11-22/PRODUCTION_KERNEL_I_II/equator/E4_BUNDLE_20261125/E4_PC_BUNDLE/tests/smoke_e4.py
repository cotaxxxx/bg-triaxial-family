"""Small invented inputs only. This program never calls the E4 entry point."""

import argparse
import json
import select
import subprocess
import sys
import tempfile
import time
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bench_e4 import capture, make_budget, validate_receipt
from check_e4 import check_case, replay_partition
from e4_kernel import BoxEvaluation, Clock, EvaluationStopped, StagedIntegral, read_interval, width
from e4_support import STAGES, box_json, read_json, read_jsonl, write_json
from run_intervals import arr, combine, ivjson
from run_e4 import run_case
from samples import deg


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


class Synthetic:
    def __init__(self, _kernel, _io, box, _pid):
        self.box = box
        self.contact = False
        self.active = None
        self.records = {}

    def advance(self, panels, _previous, clock):
        self.records = {}
        low, high = self.box[0]
        if low == 8:
            clock.end_ns = time.monotonic_ns()
            clock.poll()
        if low == 9:
            raise EvaluationStopped("INCONSISTENT", "synthetic disjoint intervals")
        if low == 10:
            raise OSError("synthetic process failure")
        if low == 11:
            interval = (F(-1), F(0))
        elif low == 12 or high - low > F(1, 2) or (low > 7 and panels == 128):
            interval = (F(-1), F(1))
        else:
            interval = (F(1), F(2))
        return interval, {"interval": ivjson(interval), "R2": {"status": "SYNTHETIC"}}

    def close(self):
        return None


def test_partitions(directory):
    budget = {"wall_budget_seconds": "3", "ratio": "1"}
    for seed, top, goal in [(7, 8, "COVERED"), (8, 8, "BUDGET"), (9, 9, "INCONSISTENT"),
                            (10, 10, "PARTIAL"), (11, 11, "NONPOSITIVE"), (12, 12, "UNRESOLVED")]:
        box = ((F(seed), F(top)), deg(1), deg(0), deg(0), deg(0))
        case = {"id": f"synthetic-{seed}", "box": box_json(box)}
        output = directory / case["id"]
        summary = run_case(case, output, directory, budget, lambda: False, evaluator=Synthetic)
        expect(summary["status"] == goal, summary)
        check_case(output, case)
        if goal == "COVERED":
            expect(summary["leaves"] == 2 and summary["evaluations"] == 6, summary)
            events = read_jsonl(output / "partition.jsonl")
            expect([r["path"] for r in events] == [[], [0], [1]], events)
            expect([r["panels"] for r in events] == [2048, 128, 512], events)
            bad_events = [dict(events[0], axis=1), *events[1:]]
            try:
                replay_partition(box, bad_events)
            except ValueError:
                pass
            else:
                raise AssertionError("checker accepted the wrong partition axis")
        if goal in {"BUDGET", "INCONSISTENT", "PARTIAL"}:
            rows = read_jsonl(output / "r2.jsonl")
            expect(summary["pending_boxes"] == 1 and summary["evaluations"] == 0, summary)
            expect(len(rows) == 1 and rows[0]["evaluation"] == "MISSING_PARTIAL"
                   and rows[0]["interval"] is None, rows)
    print("synthetic DFS, exact cover and six terminal states checked")


def test_bench(directory):
    output = directory / "synthetic-bench"
    capture(output, [sys.executable, "-c", "print('synthetic receipt only')"], directory)
    capture_data = read_json(output / "capture.json")
    write_json(output / "receipt.json", {
        "host": capture_data["host"], "workers": 8, "operator": "synthetic",
        "cold_start": True, "evaluations": ["h33", "w3"], "comparison_record": "synthetic",
        "rows": [{"worker": i, "v60_seconds": str(40 + i),
                  "same_interval_bits": {"h33": True, "w3": True}} for i in range(1, 9)],
    })
    budget = make_budget(validate_receipt(output))
    expect(budget["median_seconds"] == "89/2", budget)
    expect(F(budget["wall_budget_seconds"]) == 14400 * F("44.5") / F("45.1"), budget)
    print("synthetic eight-process timing receipts and exact median conversion checked")


def test_c_stage_io(kernel, stage_io):
    point = (deg(1), deg(1), deg(F(1, 9)), deg(F(1, 8)), deg(0))
    args = ["0", "2", "-1", *arr(point)]
    plain = subprocess.run([str(kernel), *args], text=True, capture_output=True, timeout=30, check=True)
    baseline = [json.loads(line) for line in plain.stdout.splitlines()]
    expect([row["panels"] for row in baseline] == list(STAGES), baseline)
    clock = Clock(time.monotonic_ns(), 30 * 10**9, lambda: False, lambda: None)
    staged = StagedIntegral(kernel, stage_io, args)
    try:
        for expected in baseline:
            row = staged.advance(expected["panels"], clock)
            expect({field: row[field] for field in expected} == expected, row)
            if row["panels"] < STAGES[-1]:
                ready, _, _ = select.select([staged.process.stdout], [], [], 0.05)
                expect(not ready and staged.process.poll() is None, "stage pipe failed to pause")
    finally:
        staged.close()
    staged = StagedIntegral(kernel, stage_io, args)
    try:
        staged.advance(STAGES[0], clock)
    finally:
        staged.close()
    expect(staged.process.returncode == 0 and staged.stage == 1, "early stage shutdown failed")
    print("synthetic C point: all stage rows equal plain kernel, exact pause and early exit checked")


def test_c_assembly(kernel, stage_io):
    box = (deg(1), deg(1), (F(1, 9), F(1, 9) + F(1, 256)), deg(F(1, 8)), (F(0), F(1, 512)))
    clock = Clock(time.monotonic_ns(), 25 * 10**9, lambda: False, lambda: None)
    work = BoxEvaluation(kernel, stage_io, box, lambda _pid: None)
    try:
        result, rec = work.advance(128, None, clock)
        outcomes = {}
        for name, stage in work.records.items():
            outcomes[name] = [work.records[stage["same_as"]] if "same_as" in stage else stage]
        spec = {"box": box, "kind": "H", "D": "D", "center": "I0", "base": "base", "four": "Haa",
                "grad_axes": [2, 4], "gradients": ["I_q1", "I_a"]}
        components, expected = combine(spec, 0, outcomes)
        expect(result == expected and rec["components"] == {
            name: ivjson(iv) for name, iv in components.items()
        }, rec)
        expect(rec["R2"]["angle_width"] == width(read_interval(outcomes["I0"][0]["interval"])), rec)
        expect(rec["R2"]["omitted_zero_width_axes"] == ["s", "t", "q2"], rec)
        for name in ("I0", "I_q1", "I_a"):
            expect({"coarse_2R_sum", "composite_2R_sum", "width"} <= outcomes[name][0].keys(), name)
    finally:
        work.close()
    print("synthetic C box: unchanged E1–E3 assembly and R2 remainder fields checked")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", type=Path)
    parser.add_argument("--stage-io", type=Path)
    args = parser.parse_args()
    if bool(args.kernel) != bool(args.stage_io):
        parser.error("supply both --kernel and --stage-io for the optional small C smoke")
    with tempfile.TemporaryDirectory(prefix="astra-e4-smoke-") as temp:
        directory = Path(temp)
        test_partitions(directory)
        test_bench(directory)
    if args.kernel:
        test_c_stage_io(args.kernel.resolve(), args.stage_io.resolve())
        test_c_assembly(args.kernel.resolve(), args.stage_io.resolve())


if __name__ == "__main__":
    main()
