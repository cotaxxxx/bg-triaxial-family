import json,struct,hashlib
from pathlib import Path
from decimal import Decimal
b=Path('/home/daybreak/e4-pc-20261125');d=b/'bench'
def read(p):return json.loads(p.read_text())
def bits(v):return [struct.pack('>d',float(x)).hex() for x in v]
refs=[json.loads(l) for l in (b/'records/V60_REFERENCE_BENCH.jsonl').read_text().splitlines()]
assert len(refs)==2
reference={k:bits(refs[0][k]) for k in ('h33','w3')}
assert all(bits(r[k])==reference[k] for r in refs for k in reference)
cap=read(d/'capture.json')
assert len(cap['rows'])==8
receipt=read(b/'E4_PC_BUNDLE/BENCH_RECEIPT.template.json')
receipt.update(host=cap['host'],operator='Dig',cold_start=True,comparison_record='V60_ENDPOINT_COMPARISON.json; fixed c25ba7bc2b044356896e948f6201f8ade77eb06d chat_checks/bench_here.jsonl')
rows=[]; comparison=[]
for i,row in enumerate(cap['rows'],1):
    p=d/f'bench_{i}.log'
    assert row['worker']==i and row['exit_status']==0 and hashlib.sha256(p.read_bytes()).hexdigest()==row['log_sha256']
    lines=p.read_text().splitlines()
    assert len(lines)==1,lines
    r=json.loads(lines[0],parse_float=Decimal)
    measured={k:bits(r[k]) for k in reference}
    checks={k:measured[k]==reference[k] for k in reference}
    assert all(checks.values()),(i,measured,reference)
    assert r['sec']>0
    rows.append(dict(worker=i,v60_seconds=str(r['sec']),same_interval_bits=checks))
    comparison.append(dict(worker=i,seconds=str(r['sec']),maxrss_mb=str(r['maxrss_mb']),endpoints_binary64_hex=measured,checks=checks))
receipt['rows']=rows
(d/'V60_ENDPOINT_COMPARISON.json').write_text(json.dumps(dict(reference_binary64_hex=reference,reference_commit='c25ba7bc2b044356896e948f6201f8ade77eb06d',rows=comparison),indent=2)+'\n')
(d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Bench binary64 endpoints PASS 16/16')
