"""Run the eight fixed E4 cases once, after the audit and Judge's execution approval."""

import argparse
import multiprocessing as mp
import os
import platform
import re
import resource
import shutil
import signal
import sys
import time
from fractions import Fraction
from pathlib import Path

from bench_e4 import WORKERS, make_budget, validate_receipt
from check_e4 import replay_partition
from e4_kernel import BoxEvaluation, Clock, EvaluationStopped, read_interval
from e4_support import (
    E1_E3_AUDIT, KERNEL_SOURCE_SHA, MAX_DEPTH, PLAN_SHA, ROOT, SOURCE_COMMIT, STAGES,
    box_json, fixed_cases, json_line, norm_bounds_squared, read_box, read_json, read_jsonl,
    sha256, split_axis, split_box, timestamp, verify_manifest, write_json, write_manifest,
)
from run_intervals import encode

STATUSES = {"COVERED", "BUDGET", "UNRESOLVED", "NONPOSITIVE", "INCONSISTENT", "PARTIAL"}


class Memory:
    def __init__(self):
        self.children = set()
        self.sampled_sum_kib = 0

    def sample(self):
        total = 0
        for pid in (os.getpid(), *self.children):
            try:
                with open(f"/proc/{pid}/status", encoding="ascii") as stream:
                    for line in stream:
                        if line.startswith("VmRSS:"):
                            total += int(line.split()[1])
                            break
            except (FileNotFoundError, ProcessLookupError):
                continue
        self.sampled_sum_kib = max(self.sampled_sum_kib, total)


def log(stream, row):
    stream.write(json_line(row))
    stream.flush()


def write_rows(path, rows):
    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            log(stream, row)


def usage():
    self_use = resource.getrusage(resource.RUSAGE_SELF)
    child_use = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_sec = sum(entry.ru_utime + entry.ru_stime for entry in (self_use, child_use))
    return cpu_sec, max(self_use.ru_maxrss, child_use.ru_maxrss)


def collect_calls(counts, records):
    for record in records.values():
        if "same_as" in record:
            continue
        for counter in ("panel_calls", "gauss_nodes", "integrand_calls"):
            counts[counter] += record["new_" + counter]


def run_case(case, destination, build, budget, stopped, ready=None, evaluator=BoxEvaluation):
    root = read_box(case["box"])
    destination.mkdir()
    write_json(destination / "input.json", case)
    memory = Memory()
    counts = dict(panel_calls=0, gauss_nodes=0, integrand_calls=0)
    complete = partial = deepest = 0
    boxes_evaluated = set()
    status, reason = "PARTIAL", "worker interrupted"
    todo = [((), root)]
    skew = Fraction(budget["ratio"])
    budget_ns = int(Fraction(budget["wall_budget_seconds"]) * 1_000_000_000)
    start_cpu, _ = usage()
    stop_node = None
    stop_panels = None
    with (destination / "partition.jsonl").open("x", encoding="utf-8") as partitions, (
            destination / "r2.jsonl").open("x", encoding="utf-8") as measurements:
        if ready is not None:
            ready.wait()
        started = timestamp()
        before = time.monotonic_ns()
        clock = Clock(before, budget_ns, stopped, memory.sample)

        def bisect(node, box, axis, why, **extra):
            lower, upper = split_box(box, axis)
            log(partitions, dict(node, decision="SPLIT", axis=axis, reason=why, **extra))
            path = tuple(node["path"])
            todo.extend(((path + (1,), upper), (path + (0,), lower)))

        try:
            while todo:
                path, box = todo.pop()
                deepest = max(deepest, len(path))
                node = {"case_id": case["id"], "path": list(path), "depth": len(path),
                        "box": box_json(box)}
                stop_node = node
                stop_panels = None
                clock.poll()
                low, high = norm_bounds_squared(box)
                if low > 1:
                    log(partitions, dict(node, decision="EMPTY"))
                    continue
                if high >= 1 and low < Fraction(1, 4):
                    axis = split_axis(box, root, position_only=True)
                    if axis is None or len(path) == MAX_DEPTH:
                        raise EvaluationStopped("UNRESOLVED", "contact geometry needs a position split")
                    bisect(node, box, axis, "POSITION_BEFORE_CONTACT")
                    continue
                work = evaluator(build / "kernel", build / "stage_io.so", box, memory.children.add)
                previous = None
                try:
                    for panels in STAGES:
                        stop_panels = panels
                        clock.poll()
                        boxes_evaluated.add(path)
                        stage_started = time.monotonic_ns()
                        try:
                            interval, data = work.advance(panels, previous, clock)
                        except (EvaluationStopped, ValueError, OSError, KeyError, TypeError) as err:
                            partial += 1
                            collect_calls(counts, work.records)
                            log(measurements, dict(
                                node, panels=panels, evaluation="MISSING_PARTIAL",
                                decision="DEADLINE" if getattr(err, "state", None) == "BUDGET" else "STOP",
                                R2={"status": "MISSING_PARTIAL"}, error=str(err),
                                integrals_completed_before_stop=work.records,
                                interrupted_integral=work.active, contact=work.contact,
                                interval=None, wall_ns=time.monotonic_ns() - stage_started,
                            ))
                            raise
                        complete += 1
                        collect_calls(counts, work.records)
                        previous = interval
                        axis = None
                        if interval[0] > 0:
                            decision = "LEAF"
                        elif interval[1] <= 0:
                            decision = "NONPOSITIVE"
                        elif panels != STAGES[-1]:
                            decision = "NEXT_STAGE"
                        else:
                            axis = split_axis(box, root)
                            decision = "SPLIT" if len(path) < MAX_DEPTH and axis is not None else "UNRESOLVED"
                        log(measurements, dict(data, **node, panels=panels, evaluation="COMPLETE",
                                               decision=decision, wall_ns=time.monotonic_ns() - stage_started))
                        if decision == "LEAF":
                            log(partitions, dict(node, decision=decision, panels=panels,
                                                 interval=data["interval"]))
                            break
                        if decision == "SPLIT":
                            bisect(node, box, axis, "UNDECIDED", panels=panels,
                                   interval=data["interval"])
                            break
                        if decision == "NONPOSITIVE":
                            raise EvaluationStopped(decision, "enclosure upper endpoint <= 0")
                        if decision == "UNRESOLVED":
                            raise EvaluationStopped(decision, "maximum depth or no nonzero coordinate")
                finally:
                    work.close()
                    memory.children.clear()
            status, reason = "COVERED", "DFS exhausted"
        except EvaluationStopped as exc:
            status, reason = exc.state, exc.detail
        except (ValueError, OSError, KeyError, TypeError) as exc:
            status, reason = "PARTIAL", str(exc)
        stopped_ns = time.monotonic_ns()
        computation_ended = timestamp()

    events = read_jsonl(destination / "partition.jsonl")
    leaves, pending = replay_partition(root, events)
    if status == "COVERED" and (pending or not leaves):
        status, reason = "PARTIAL", "positive exact coverage not verified"
    write_rows(destination / "leaves.jsonl", leaves)
    write_rows(destination / "pending.jsonl", pending)
    min_lower = min((read_interval(leaf["interval"])[0] for leaf in leaves), default=None)
    cpu_sec, peak_process_rss = usage()
    saved_ns = time.monotonic_ns()
    wall_ns = stopped_ns - before
    summary = dict(
        id=case["id"], root=case["box"], status=status, reason=reason, complete=status == "COVERED",
        leaves=len(leaves), pending_boxes=len(pending), evaluations=complete,
        partial_evaluations=partial, distinct_evaluated_boxes=len(boxes_evaluated),
        stop_node=stop_node if status != "COVERED" else None,
        stop_panels=stop_panels if status != "COVERED" else None,
        max_depth=deepest, min_leaf_lo=None if min_lower is None else encode(min_lower),
        observed_completed_panel_calls=counts["panel_calls"],
        observed_completed_gauss_nodes=counts["gauss_nodes"],
        observed_completed_integrand_calls=counts["integrand_calls"],
        unobserved_midstage_work=bool(partial),
        wall_ns=wall_ns, wall_seconds=wall_ns / 1e9, equivalent_seconds=float(Fraction(wall_ns, 10**9) / skew),
        cpu_seconds=cpu_sec - start_cpu, wall_budget_seconds=budget["wall_budget_seconds"],
        deadline_excess_ns=max(0, stopped_ns - clock.end_ns), save_ns=saved_ns - stopped_ns,
        elapsed_after_deadline_at_save_ns=max(0, saved_ns - clock.end_ns),
        max_single_process_rss_kib=peak_process_rss, max_sampled_case_rss_sum_kib=memory.sampled_sum_kib,
        started_utc=started, compute_ended_utc=computation_ended, saved_utc=timestamp(),
        leaf_sha256=sha256(destination / "leaves.jsonl"),
        v61_leaves=case.get("v61_leaves"), v61_evaluations=case.get("v61_evaluations"),
    )
    write_json(destination / "summary.json", summary)
    return summary


def run_worker(case, destination, build, budget, stopped, ready):
    summary = run_case(case, destination, build, budget, stopped, ready)
    print(json_line({key: summary[key] for key in ("id", "status", "leaves", "evaluations",
                                                   "pending_boxes", "compute_ended_utc")}),
          end="", flush=True)


def run_all(output, bench, audit_commit, judge_commit):
    cases = fixed_cases()
    verify_manifest(ROOT, "MANIFEST.sha256")
    build = ROOT / "build"
    verify_manifest(build, "BUILD.sha256")
    budget = make_budget(validate_receipt(bench))
    if read_json(bench / "BUDGET.json") != budget:
        raise ValueError("saved benchmark budget differs from the eight receipts")
    output.mkdir()
    shutil.copytree(bench, output / "bench")
    shutil.copyfile(build / "ENVIRONMENT.txt", output / "BUILD_ENVIRONMENT.txt")
    shutil.copyfile(build / "BUILD.sha256", output / "BUILD.sha256")
    shutil.copyfile(ROOT / "inputs/E4_CASES.json", output / "E4_CASES.json")
    (output / "cases").mkdir()
    write_json(output / "RUN.json", {
        "status": "DIAGNOSTIC_ONLY", "workers": WORKERS, "host": platform.node(),
        "cpu_affinity": sorted(os.sched_getaffinity(0)), "platform": platform.platform(),
        "python": sys.version, "started_utc": timestamp(), "build_scope_commit": SOURCE_COMMIT,
        "e1_e3_audit_commit": E1_E3_AUDIT, "bundle_audit_commit": audit_commit,
        "judge_execution_approval_commit": judge_commit, "plan_sha256": PLAN_SHA,
        "kernel_source_sha256": KERNEL_SOURCE_SHA, "kernel_sha256": sha256(build / "kernel"),
        "stage_io_sha256": sha256(build / "stage_io.so"),
        "bundle_manifest_sha256": sha256(ROOT / "MANIFEST.sha256"),
        "input_sha256": sha256(ROOT / "inputs/E4_CASES.json"), "budget": budget,
        "rounding": ["RNDD", "RNDU"], "precision_bits": 128,
    })

    stop = mp.Event()
    ready = mp.Barrier(WORKERS, timeout=60)

    def stop_all(*_):
        stop.set()

    signal.signal(signal.SIGTERM, stop_all)
    signal.signal(signal.SIGINT, stop_all)
    workers = []
    for case in cases:
        worker = mp.Process(
            target=run_worker,
            args=(case, output / "cases" / case["id"], build, budget, stop.is_set, ready),
        )
        worker.start()
        workers.append(worker)
    for worker in workers:
        worker.join()

    summaries = []
    missing = []
    for case, worker in zip(cases, workers):
        path = output / "cases" / case["id"] / "summary.json"
        if path.is_file():
            summary = read_json(path)
            if summary["status"] not in STATUSES:
                raise ValueError("unrecognized final worker state")
            summaries.append(summary)
        else:
            missing.append({"id": case["id"], "status": "PARTIAL", "exit_status": worker.exitcode})
    write_json(output / "SUMMARY.json", {
        "cases": summaries, "workers_without_summary": missing, "finished_utc": timestamp(),
    })
    write_manifest(output, "RESULT_SHA256SUMS.txt")
    adverse = {"PARTIAL", "INCONSISTENT", "NONPOSITIVE"}
    return int(bool(missing) or any(row["status"] in adverse for row in summaries))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-inputs", action="store_true")
    parser.add_argument("--bench", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bundle-audit")
    parser.add_argument("--judge-execution-approval")
    args = parser.parse_args()
    if args.check_inputs:
        print(json_line(fixed_cases()), end="")
        return 0
    commits = (args.bundle_audit, args.judge_execution_approval)
    if (args.output is None or args.bench is None
            or any(c is None or not re.fullmatch("[0-9a-f]{40}", c) for c in commits)
            or len(set(commits + (SOURCE_COMMIT, E1_E3_AUDIT))) != 4):
        parser.error("supply the bench directory, new output directory and the two new approval commits")
    return run_all(args.output.resolve(), args.bench.resolve(), *commits)


if __name__ == "__main__":
    raise SystemExit(main())
