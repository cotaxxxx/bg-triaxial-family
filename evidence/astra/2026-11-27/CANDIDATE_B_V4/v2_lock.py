"""Pin the research-PC v2 records used as the starting cover."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    with path.open(encoding="utf-8") as stream:
        for item in stream:
            if not item.endswith("\n"):
                raise ValueError(f"truncated ledger row in {path}")
            yield json.loads(item)


def seal(directory, name):
    path = directory / name
    members = sorted(p for p in directory.rglob("*") if p.is_file() and p != path)
    with path.open("x", encoding="ascii") as output:
        for member in members:
            output.write(f"{sha256(member)}  {member.relative_to(directory).as_posix()}\n")


def verify_seal(directory, text):
    expected = {}
    for line in text.splitlines():
        digest, name = line.split("  ", 1)
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid SHA-256 in file list")
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != name or name in expected:
            raise ValueError("invalid or repeated path in SHA-256 list")
        expected[name] = digest
    for name, digest in expected.items():
        if sha256(directory / name) != digest:
            raise ValueError(f"SHA-256 mismatch for {name}")
    return expected


def verify_parent(folder):
    checksum = HERE / "V2_RESULT_SHA256SUMS.txt"
    if (folder / "RESULT_SHA256SUMS.txt").read_bytes() != checksum.read_bytes():
        raise ValueError("v2 result checksum list differs from 862220c")
    check = verify_seal(folder, checksum.read_text(encoding="ascii"))
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    if set(check) | {"RESULT_SHA256SUMS.txt"} != actual:
        raise ValueError("the v2 result folder differs from the frozen file set")
