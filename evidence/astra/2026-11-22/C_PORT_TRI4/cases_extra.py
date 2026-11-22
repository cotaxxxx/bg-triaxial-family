import json
from cases_run import HERE,F,run
for i,row in enumerate(json.loads((HERE/'cases_v2_extra.json').read_text())):
    box = [[F(x) for x in p] for p in row['box']]
    for j,n in enumerate((64,256)):
        print(json.dumps(run(54+2*i+j,('C12',box,n,0,max(16,n//2)))),flush=True)
