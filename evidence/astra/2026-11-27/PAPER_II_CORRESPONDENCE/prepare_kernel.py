"""Generate the new compilation unit from the untouched Candidate B sources."""

from pathlib import Path
from shutil import copyfile
import sys


ROOT = Path(__file__).resolve().parent


def edit(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"expected one insertion point: {old!r}")
    return text.replace(old,new)


def prepare(destination):
    destination.mkdir(parents=True,exist_ok=True)
    source = ROOT/"src"
    candidate = (source/"candidate.c").read_text()
    hook = "static I integrand(const Tree *tree, I u, I w, int angular) {"
    candidate = edit(candidate,hook,'#include "new_integrands.h"\n\n'+hook+
                     "\n    if (tree->quantity >= AZ) return correspondence_integrand(tree,u,w,angular);")
    candidate = edit(candidate,"quantity > 3","quantity >= CORR_COUNT")
    jets = (source/"jets.h").read_text()
    jets = edit(jets,"coeff[9][98]","coeff[10][98]")
    jets = edit(jets,"j<=8&&j<=n","j<=9&&j<=n")
    (destination/"candidate.c").write_text(candidate)
    (destination/"jets.h").write_text(jets)
    for name in ("interval.h","new_integrands.h"):
        copyfile(source/name,destination/name)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]))
