import json
from cases_run import HERE,F,run
from math import log2
for row in json.loads((HERE/'inball.json').read_text()):
    b=[[F(x) for x in p] for p in row['box']]
    grade=max(0,min(2,round(log2(float(b[0][1]*b[1][1]))/2)))
    for i,n in enumerate((64,256)):
        print(json.dumps(run(66+i,('W3',b,n,grade,n//2))),flush=True)
