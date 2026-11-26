"""Build the extended translation unit from the byte-frozen v3 sources."""
from pathlib import Path

def replace_once(s, a, b):
    if s.count(a) != 1:
        raise ValueError(f"unexpected base source around {a!r}")
    return s.replace(a, b)

def generate(out):
    out=Path(out)
    out.mkdir(parents=True, exist_ok=True)
    base=Path(__file__).resolve().parent / "base"
    c=(base/"candidate.c").read_text()
    marker="static I integrand(const Tree *tree, I u, I w, int angular) {"
    c=replace_once(c, marker, '#include "quantities.inc"\n'+marker+
                   '\n    if (tree->quantity >= 4) return extra_integrand(tree,u,w,angular);')
    c=replace_once(c,"quantity > 3","quantity > 12")
    jets=(base/"jets.h").read_text()
    for a,b in [("coeff[9][98]","coeff[10][98]"),("j<=8&&j<=n","j<=9&&j<=n")]:
        jets=replace_once(jets,a,b)
    (out/"candidate.c").write_text(c)
    (out/"jets.h").write_text(jets)
    for source in [base/"interval.h",base/"build_probe.c",base.parent/"quantities.inc"]:
        (out/source.name).write_bytes(source.read_bytes())

if __name__=="__main__":
    import sys
    generate(sys.argv[1])
