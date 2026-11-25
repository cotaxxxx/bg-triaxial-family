"""Exact input geometry and shared record formats for the E4 bundle."""

import hashlib
import json
import os
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from samples import tile

ROOT = Path(__file__).resolve().parent.parent
SOURCE_COMMIT = "66afe3ad4c0d76442370df49174077f601733c6c"
E1_E3_AUDIT = "1b7c758bcf529dab5867467d16987b60d5ba6558"
V60_SAMPLE_COMMIT = "c25ba7bc2b044356896e948f6201f8ade77eb06d"
V60_SAMPLE_SHA = "6cd544a58266c61cd9e080bd151622724efcb1d2ef860c03de042568f77a372b"
PLAN_SHA = "7f628c6e83ae68c8067dcd57d70f64ba2e0b7293035ca301c209d50f153a705d"
KERNEL_SOURCE_SHA = "6cae72fdd9c1a30e4a759a49b3814d098941fa80056fd40001e6c24220d6fed3"
MAX_DEPTH = 40
STAGES = (128, 512, 2048)
AXES = ("s", "t", "q1", "q2", "a")
CASES = (
    ((0, 0, 27, 7, 0), 311, 1160),
    ((1, 3, 27, 7, 0), 338, 700),
    ((2, 5, 0, 23, 0), 238, 480),
    ((2, 5, 27, 7, 0), 372, 751),
    ((3, 7, 0, 23, 0), 263, 531),
    ((3, 7, 4, 15, 0), 243, 489),
    ((3, 7, 10, 0, 0), 248, 496),
    ((3, 7, 27, 7, 0), 335, 686),
)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_line(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("x", encoding="utf-8") as stream:
        stream.write(json_line(value))
    os.replace(tmp, path)


def read_jsonl(path):
    with path.open(encoding="utf-8") as rows:
        return [json.loads(line) for line in rows]


def read_box(raw):
    if len(raw) != 5 or any(len(pair) != 2 for pair in raw):
        raise ValueError("a box requires five pairs of endpoints")
    if any(type(x) is not str for pair in raw for x in pair):
        raise ValueError("box endpoints must be exact rational strings")
    box = tuple(tuple(map(Fraction, pair)) for pair in raw)
    if any(lo > hi for lo, hi in box):
        raise ValueError("reversed box")
    return box


def box_json(box):
    return [[str(lo), str(hi)] for lo, hi in box]


def norm_bounds_squared(box):
    # Only for the nonnegative reference octant used by the equator plan.
    return tuple(sum(pair[side] ** 2 for pair in box[2:]) for side in (0, 1))


def source_cases(directory=ROOT):
    v60 = directory / "inputs/samples_v60.json"
    if sha256(v60) != V60_SAMPLE_SHA:
        raise ValueError("fixed V60 sample checksum differs")
    rows = read_json(v60)
    chosen = []
    for key, leaves, evaluations in CASES:
        i, j, k, l, m = key
        matches = [
            row for row in rows
            if (row["layer"], row["stratum"], row["kind"]) == ("I", "equator", "H33")
            and row["tile"] == [i, j] and row["cell"] == [k, l, m]
        ]
        if len(matches) != 1:
            raise ValueError(f"V60 has {len(matches)} matches for {key}")
        row = matches[0]
        box = read_box(row["box"])
        expected = tuple(tile(i, j)) + tuple(
            (Fraction(p, 32), Fraction(p + 1, 32)) for p in (k, l, m)
        )
        if box != expected or norm_bounds_squared(box)[1] >= 1:
            raise ValueError(f"invalid or non-interior V60 root {key}")
        chosen.append(dict(row, id=",".join(map(str, key)), v61_leaves=leaves,
                           v61_evaluations=evaluations))
    return chosen


def fixed_cases(directory=ROOT):
    cases = source_cases(directory)
    if read_json(directory / "inputs/E4_CASES.json") != cases:
        raise ValueError("E4 roots differ from the eight V60 samples in plan order")
    if sha256(directory / "PLAN_TESTS_EQUATOR.md") != PLAN_SHA:
        raise ValueError("frozen plan checksum differs")
    if sha256(directory / "src/kernel.c") != KERNEL_SOURCE_SHA:
        raise ValueError("frozen kernel source checksum differs")
    return cases


def split_box(box, axis):
    lo, hi = box[axis]
    if lo >= hi:
        raise ValueError("cannot bisect a zero-width coordinate")
    mid = (lo + hi) / 2
    return (box[:axis] + ((lo, mid),) + box[axis + 1:],
            box[:axis] + ((mid, hi),) + box[axis + 1:])


def split_axis(box, root, position_only=False):
    axes = [i for i in range(2 if position_only else 0, 5) if box[i][0] < box[i][1]]
    if not axes:
        return None
    # max() retains the first axis on a tie. The fractions do not round.
    return max(axes, key=lambda i: (box[i][1] - box[i][0]) / (root[i][1] - root[i][0]))


def verify_manifest(directory, name):
    for line in (directory / name).read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        path = directory / rel
        if sha256(path) != digest:
            raise ValueError(f"checksum differs: {rel}")


def write_manifest(directory, name):
    manifest = directory / name
    with manifest.open("x", encoding="utf-8") as stream:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path != manifest:
                stream.write(f"{sha256(path)}  {path.relative_to(directory).as_posix()}\n")
