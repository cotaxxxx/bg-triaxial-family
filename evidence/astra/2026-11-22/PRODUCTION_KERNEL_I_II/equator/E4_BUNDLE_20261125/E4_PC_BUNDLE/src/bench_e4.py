"""Collect eight operational V60 bench logs and compute the frozen E4 budget."""

import argparse
import concurrent.futures
import os
import platform
import subprocess
import threading
import time
from fractions import Fraction
from pathlib import Path

from e4_support import read_json, sha256, timestamp, write_json

WORKERS = 8
CALIBRATION_SECONDS = Fraction("45.1")
REFERENCE_BUDGET_SECONDS = 14_400
BENCH_CASES = ["h33", "w3"]


def capture(output, command, cwd):
    output.mkdir()
    start = threading.Barrier(WORKERS, timeout=60)

    def one(worker):
        log = output / f"bench_{worker}.log"
        with log.open("xb") as stream:
            start.wait()
            started = timestamp()
            before = time.monotonic_ns()
            try:
                status = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                        env=dict(os.environ, LC_ALL="C")).returncode
            except OSError as exc:
                stream.write(f"bench launch error: {exc}\n".encode())
                status = 127
            elapsed = time.monotonic_ns() - before
        return {"worker": worker, "log": log.name, "log_sha256": sha256(log),
                "started_utc": started, "ended_utc": timestamp(),
                "outer_wall_ns": elapsed, "exit_status": status}

    with concurrent.futures.ThreadPoolExecutor(WORKERS) as executor:
        rows = list(executor.map(one, range(1, WORKERS + 1)))
    write_json(output / "capture.json", {
        "host": platform.node(), "os": platform.platform(), "command": command, "cwd": str(cwd),
        "workers": WORKERS, "cpu_affinity": sorted(os.sched_getaffinity(0)), "rows": rows,
    })
    if any(row["exit_status"] != 0 for row in rows):
        raise ValueError("at least one reference bench invocation failed; logs preserved")


def fraction_seconds(value):
    if type(value) is not str:
        raise ValueError("benchmark times must be exact strings from the V60 timing record")
    seconds = Fraction(value)
    if seconds <= 0:
        raise ValueError("nonpositive benchmark elapsed time")
    return seconds


def validate_receipt(directory):
    receipt = read_json(directory / "receipt.json")
    capture_data = read_json(directory / "capture.json")
    if (receipt["host"] != platform.node() or receipt["host"] != capture_data["host"]
            or receipt["cold_start"] is not True or receipt["workers"] != WORKERS
            or capture_data["workers"] != WORKERS or receipt["evaluations"] != BENCH_CASES
            or capture_data["cpu_affinity"] != sorted(os.sched_getaffinity(0))
            or not receipt["comparison_record"].strip()
            or not receipt["operator"].strip()):
        raise ValueError("bench receipt has the wrong host, concurrency or comparison record")
    captures = capture_data["rows"]
    rows = receipt["rows"]
    expected_workers = list(range(1, WORKERS + 1))
    if ([row["worker"] for row in captures] != expected_workers
            or [row["worker"] for row in rows] != expected_workers):
        raise ValueError("expected eight distinct bench workers in order")
    elapsed = []
    for capture_row, row in zip(captures, rows):
        log = directory / f"bench_{row['worker']}.log"
        if (capture_row["exit_status"] != 0 or capture_row["log"] != log.name
                or capture_row["log_sha256"] != sha256(log)
                or row["same_interval_bits"] != {"h33": True, "w3": True}):
            raise ValueError(f"bench worker {row['worker']} failed the reference check")
        elapsed.append(fraction_seconds(row["v60_seconds"]))
    return elapsed


def make_budget(elapsed):
    if len(elapsed) != WORKERS or any(seconds <= 0 for seconds in elapsed):
        raise ValueError("need eight positive V60 timing values")
    ordered = sorted(elapsed)
    median = (ordered[3] + ordered[4]) / 2
    ratio = median / CALIBRATION_SECONDS
    return {
        "v60_seconds": list(map(str, elapsed)),
        "median_seconds": str(median), "baseline_seconds": "45.1",
        "ratio": str(ratio), "reference_budget_seconds": REFERENCE_BUDGET_SECONDS,
        "wall_budget_seconds": str(REFERENCE_BUDGET_SECONDS * ratio),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    cap = sub.add_parser("capture", help="Dig runs the separately approved reference command")
    cap.add_argument("output", type=Path)
    cap.add_argument("--cwd", required=True, type=Path)
    cap.add_argument("command", nargs="+")
    convert = sub.add_parser("budget")
    convert.add_argument("directory", type=Path)
    opts = parser.parse_args()
    if opts.operation == "capture":
        capture(opts.output, opts.command, opts.cwd)
    else:
        summary = make_budget(validate_receipt(opts.directory))
        output = opts.directory / "BUDGET.json"
        if output.exists():
            raise SystemExit(f"refusing to replace {output}")
        write_json(output, summary)
        print(f"per-case wall budget: {float(Fraction(summary['wall_budget_seconds'])):.3f} s")


if __name__ == "__main__":
    main()
