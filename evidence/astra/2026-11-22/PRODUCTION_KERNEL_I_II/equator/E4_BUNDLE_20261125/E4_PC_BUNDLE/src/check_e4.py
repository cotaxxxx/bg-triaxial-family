"""Check a saved E4 binary partition with exact rationals, without running the kernel."""

import argparse
import json
from pathlib import Path
from fractions import Fraction

from e4_kernel import read_interval
from e4_support import (
    MAX_DEPTH, STAGES, box_json, fixed_cases, norm_bounds_squared, read_box, read_json,
    read_jsonl, sha256, split_axis, split_box, verify_manifest,
)


def replay_partition(root, events):
    frontier = [((), root)]
    accepted = []
    for row in events:
        if not frontier:
            raise ValueError("extra event after root partition is exhausted")
        path, box = frontier.pop()
        if (row["path"] != list(path) or read_box(row["box"]) != box
                or row["depth"] != len(path) or len(path) > MAX_DEPTH):
            raise ValueError(f"wrong DFS path, depth or box at {path}")
        if row["decision"] == "LEAF":
            if row["panels"] not in STAGES or read_interval(row["interval"])[0] <= 0:
                raise ValueError(f"nonpositive or invalid leaf at {path}")
            accepted.append(row)
        elif row["decision"] == "SPLIT":
            before_contact = row["reason"] == "POSITION_BEFORE_CONTACT"
            if before_contact:
                low, high = norm_bounds_squared(box)
                if low >= Fraction(1, 4) or high < 1:
                    raise ValueError(f"invalid pre-contact split at {path}")
            else:
                if row["reason"] != "UNDECIDED" or row["panels"] != STAGES[-1]:
                    raise ValueError(f"invalid split stage at {path}")
                lower, upper = read_interval(row["interval"])
                if not lower <= 0 < upper:
                    raise ValueError(f"split of a decided enclosure at {path}")
            axis = split_axis(box, root, position_only=before_contact)
            if axis is None or row["axis"] != axis or len(path) == MAX_DEPTH:
                raise ValueError(f"invalid split axis or depth at {path}")
            lower, upper = split_box(box, axis)
            frontier.extend(((path + (1,), upper), (path + (0,), lower)))
        elif row["decision"] != "EMPTY" or norm_bounds_squared(box)[0] <= 1:
            raise ValueError(f"invalid terminal event at {path}")
    pending = [
        {"path": list(path), "depth": len(path), "box": box_json(box)}
        for path, box in reversed(frontier) if norm_bounds_squared(box)[0] <= 1
    ]
    return accepted, pending


def check_case(case_directory, expected):
    summary = read_json(case_directory / "summary.json")
    if summary["id"] != expected["id"] or summary["root"] != expected["box"]:
        raise ValueError("saved case key or geometry differs from fixed input")
    root = read_box(expected["box"])
    events = read_jsonl(case_directory / "partition.jsonl")
    leaves, pending = replay_partition(root, events)
    if leaves != read_jsonl(case_directory / "leaves.jsonl"):
        raise ValueError("leaf log does not match the partition")
    if pending != read_jsonl(case_directory / "pending.jsonl"):
        raise ValueError("pending log does not match the partition")
    if summary["leaf_sha256"] != sha256(case_directory / "leaves.jsonl"):
        raise ValueError("leaf contents differ from the saved leaf checksum")
    if summary["complete"] != (summary["status"] == "COVERED"):
        raise ValueError("completion flag disagrees with the status")
    if summary["complete"] and (pending or not leaves):
        raise ValueError("a completed case has pending geometry or no positive leaves")

    measurements = read_jsonl(case_directory / "r2.jsonl")
    complete = [row for row in measurements if row["evaluation"] == "COMPLETE"]
    partial = [row for row in measurements if row["evaluation"] == "MISSING_PARTIAL"]
    if len(complete) + len(partial) != len(measurements):
        raise ValueError("unexpected stage measurement state")
    if (len(complete), len(partial), len(leaves), len(pending)) != (
            summary["evaluations"], summary["partial_evaluations"], summary["leaves"],
            summary["pending_boxes"]):
        raise ValueError("measurement or partition counts differ")
    completed_leaves = {
        (tuple(row["path"]), row["panels"]): row for row in complete
        if row["decision"] == "LEAF"
    }
    if len(completed_leaves) != len(leaves):
        raise ValueError("leaf measurement count differs")
    for leaf in leaves:
        record = completed_leaves[(tuple(leaf["path"]), leaf["panels"])]
        if record["interval"] != leaf["interval"] or record["box"] != leaf["box"]:
            raise ValueError("leaf measurement does not match the partition")
    return {"id": expected["id"], "status": summary["status"],
            "leaves": len(leaves), "pending": len(pending)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    verify_manifest(args.output, "RESULT_SHA256SUMS.txt")
    summary = read_json(args.output / "SUMMARY.json")
    if summary["workers_without_summary"]:
        raise SystemExit("PARTIAL: worker summaries are missing; inspect raw journals")
    for case in fixed_cases():
        print(json.dumps(check_case(args.output / "cases" / case["id"], case)))


if __name__ == "__main__":
    main()
