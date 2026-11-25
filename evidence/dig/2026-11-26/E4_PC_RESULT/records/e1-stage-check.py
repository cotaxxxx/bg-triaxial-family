import json,sys,time,hashlib,subprocess
from pathlib import Path
base=Path('/home/daybreak/e4-pc-20261125')
bundle=base/'E4_PC_BUNDLE'
sys.path.insert(0,str(bundle/'src'))
from e4_kernel import Clock,StagedIntegral
from run_intervals import tasks,combine,intersect,ivjson,ri
from samples import public_boxes
from fractions import Fraction as F
# tasks() needs the public E3 geometry, not present in E4 bundle.
# E1 task definitions are reproduced exactly from the fixed tasks() E1 loop.
from samples import e1,deg,middle
from run_intervals import arr,idigest
jobs={};cases=[]
def req(b,order):
    args=['0',str(order),'-1']+arr(b);key=idigest(args);jobs[key]=args;return key
for label,b in [('center',[deg(middle(x)) for x in e1()]),('box',e1())]:
    tube=b[:4]+[(F(0),b[4][1])]
    cases.append(dict(id='E1_'+label,kind='E1',box=b,D=req(b,3),four=req(tube,4)))
repo='/home/daybreak/e2ref/repo'
ref='5f1a4c1f2ca80ce5954eb2492dc581fd2ecc50e9'
prefix='evidence/dig/2026-11-25/E1_E3_REVISION_PC/results/revision_20261123/ec6b0f68af615bd7fc8561307c8a33ee898cafcfb325ea8399c2cfcfe64a33df'
def original(k):return json.loads(subprocess.check_output(['git','-C',repo,'show',f'{ref}:{prefix}/integrals/{k}.json']))
oldjobs=json.loads(subprocess.check_output(['git','-C',repo,'show',f'{ref}:{prefix}/integrals/jobs.json']))
assert len(jobs)==4 and all(oldjobs[k]==a for k,a in jobs.items())
assert hashlib.sha256((bundle/'build/kernel').read_bytes()).hexdigest()==prefix.split('/')[-1]
outcomes={}
for k,args in jobs.items():
    orig=original(k)
    assert orig['args']==args
    clock=Clock(time.monotonic_ns(),180*10**9,lambda:False,lambda:None)
    staged=StagedIntegral(bundle/'build/kernel',bundle/'build/stage_io.so',args)
    try:
        got=[]
        for row in orig['stages']:
            value=staged.advance(row['panels'],clock)
            assert {field:value[field] for field in row}==row,(k,row['panels'])
            got.append(value)
        outcomes[k]=got
        print('raw stages match',k,flush=True)
    finally:
        staged.close()
rows=[]
for c in cases:
    cumulative=None;stages=[]
    for i,L in enumerate((128,512,2048)):
        data,iv=combine(c,i,outcomes)
        cumulative=iv if cumulative is None else intersect(cumulative,iv)
        stages.append(dict(panels=L,components={k:ivjson(v) for k,v in data.items()},interval=ivjson(cumulative),width=ivjson(ri(cumulative[1]-cumulative[0],cumulative[1]-cumulative[0]))[1]))
    rows.append(dict(id=c['id'],kind=c['kind'],box=arr(c['box']),stages=stages,precision_bits=128))
original_rows=[json.loads(l) for l in (base/'records/E1_original.jsonl').read_text().splitlines()]
assert rows==original_rows
(base/'records/E1_staged_integrals.json').write_text(json.dumps(outcomes,indent=2)+'\n')
(base/'records/E1_staged.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
print('E1 staged check PASS: 4 raw integrals x 3, 2 aggregate rows x 3',flush=True)
