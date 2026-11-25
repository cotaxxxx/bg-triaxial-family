import ast,csv,hashlib,json,statistics,subprocess,sys
from pathlib import Path
from fractions import Fraction as F
base=Path('/home/daybreak/equator-revision-20261125')
work=base/'work'; out=base/'registration'; repo='/home/daybreak/e2ref/repo'
prefix='evidence/astra/2026-11-22/PRODUCTION_KERNEL_I_II/equator'
old='9cba7f2c8ec99abbdf2e86ef5c79a2425199b03a'
new='f48fd339fdb862883c475708c48ae76316f9fcb1'
def git(*a):return subprocess.check_output(['git','-C',repo,*a])
def sha(b):return hashlib.sha256(b).hexdigest()
def show(ref,p):return git('show',f'{ref}:{prefix}/{p}')
def unpack(x):return F(int(x[0]))*F(2)**x[1]
def iv(x):return tuple(map(unpack,x))
def funcs(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
def read(p):return json.loads(p.read_text())
old_runner=show(old,'src/run_intervals.py');new_runner=(work/'src/run_intervals.py').read_bytes()
assert funcs(old_runner)['tasks']==funcs(new_runner)['tasks']
assert (work/'src/samples.py').read_bytes()==show(old,'src/samples.py')
assert show(new,'src/kernel.c')==(work/'src/kernel.c').read_bytes()
binary=sha((work/'kernel').read_bytes())
assert binary=='ec6b0f68af615bd7fc8561307c8a33ee898cafcfb325ea8399c2cfcfe64a33df'
d=work/'results/revision_20261123'/binary
assert list(d.parent.iterdir())==[d]
assert binary in (base/'records/build.log').read_text() and binary in (work/'interval-run.log').read_text()
# Regenerate the job inventory from the frozen runner only; no numeric integration.
sys.path.insert(0,str(work/'src'))
from run_intervals import tasks
jobs,cases=tasks(); cache=d/'integrals'
assert read(cache/'jobs.json')==jobs
assert len(jobs)==311 and len(cases)==114
assert {f.stem for f in cache.glob('*.json') if f.name!='jobs.json'}==set(jobs)
assert len(list(cache.iterdir()))==312
# Old results copied at the frozen source commit must remain byte-identical.
oldpaths=git('ls-tree','-r','--name-only',new,prefix+'/results').decode().splitlines()
for p in oldpaths:
    rel=p[len(prefix)+1:]
    assert (work/rel).read_bytes()==git('show',new+':'+p),rel
# The original interval-result records also match the earlier old-kernel source.
for name in ['E1_stages.jsonl','H_stages.jsonl','Haa_stages.jsonl','E2c_stages.jsonl','E3_ASTRA_ENDPOINTS.jsonl','INTERVAL_RUN_SUMMARY.json','ENVIRONMENT.json']:
    assert (work/'results'/name).read_bytes()==show(old,'results/'+name),name
oldsum=read(work/'results/INTERVAL_RUN_SUMMARY.json')
assert oldsum['completed_unique_integrals']==311
# Original per-integral cache was not present in either pinned Git tree.
oldtree=git('ls-tree','-r','--name-only',old,prefix+'/results').decode().splitlines()
assert not any('/integrals/' in p for p in oldtree+oldpaths)
rows=[];seconds=[];tot_old=tot_new=0;contact_count=0
for k,args in sorted(jobs.items()):
    r=read(cache/(k+'.json'))
    assert sha(json.dumps(args,separators=(',',':')).encode())==k
    assert r['args']==args
    stages=r['stages']; assert [s['panels'] for s in stages]==[128,512,2048]
    sec=r['seconds'];assert isinstance(sec,(int,float)) and sec>0
    seconds.append(sec)
    contact=('cap' in stages[-1]);contact_count+=contact
    for s in stages:
        n=s['panels'];oc=32+4*((n-32)//3);nc=s['panel_calls']
        assert nc==oc*(1 if contact else 5)
        assert sum(s['grids'].values())==n
        assert s['grids']['contact']==(n if contact else 0)
        c=unpack(s['coarse_2R_sum']);m=unpack(s['composite_2R_sum'])
        assert c>=0 and m>=0
        lo,hi=iv(s['outer']);a,b=iv(s['legacy_outer']);assert a<=lo<=hi<=b
        if contact:assert c==m
        rows.append(dict(job_sha256=k,args_json=json.dumps(args,separators=(',',':')),route='contact' if contact else 'internal',stage_leaves=n,old_panel_calls_derived=oc,new_panel_calls_measured=nc,old_integrand_calls_derived=7*oc,new_integrand_calls_derived=7*nc,old_run_2R='NOT_RECORDED',new_coarse_2R_mantissa=s['coarse_2R_sum'][0],new_coarse_2R_exponent=s['coarse_2R_sum'][1],new_composite_2R_mantissa=s['composite_2R_sum'][0],new_composite_2R_exponent=s['composite_2R_sum'][1],new_whole_integral_seconds=sec if n==2048 else '',new_seconds_per_panel_formula=sec/nc if n==2048 else '',grid_contact=s['grids']['contact'],grid_1x4=s['grids']['1x4'],grid_2x2=s['grids']['2x2'],grid_4x1=s['grids']['4x1']))
        if n==2048:tot_old+=oc;tot_new+=nc
assert len(rows)==933
with (out/'INTEGRAL_EVALUATION_COMPARISON.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
counts={}
for name,expected in [('E1_stages.jsonl',2),('H_stages.jsonl',92),('Haa_stages.jsonl',8),('E2c_stages.jsonl',12),('E3_ASTRA_ENDPOINTS.jsonl',92)]:
    rr=[json.loads(l) for l in (d/name).read_text().splitlines()]
    assert len(rr)==expected and len({x['id'] for x in rr})==expected
    if name!='E3_ASTRA_ENDPOINTS.jsonl':assert all([s['panels'] for s in r['stages']]==[128,512,2048] for r in rr)
    else:assert all(r['status']=='ENCLOSED_PENDING_CHAT' for r in rr)
    counts[name]=len(rr)
oldtime=oldsum['wall_seconds_per_integral']['sum_over_simultaneous_jobs']
newtime=sum(seconds)
summary=dict(status='COMPLETE_PENDING_CHAT_AUDIT',grade='DIAGNOSTIC_ONLY',source_commit=new,old_source_commit=old,kernel_sha256=binary,kernel_c_sha256=sha((work/'src/kernel.c').read_bytes()),input_sha256=sha((work/'inputs/E3_BOXES_PUBLIC.jsonl').read_bytes()),old_result_files_byte_matched=len(oldpaths),old_task_definition_and_samples_identical=True,job_count=311,case_count=114,stage_rows_checked=933,internal_jobs=311-contact_count,contact_jobs=contact_count,old_panel_calls_derived=tot_old,new_panel_calls_measured=tot_new,old_integrand_calls_derived=7*tot_old,new_integrand_calls_derived=7*tot_new,old_sum_individual_seconds=oldtime,new_sum_individual_seconds=newtime,old_average_seconds_per_panel_derived=oldtime/tot_old,new_average_seconds_per_panel_derived=newtime/tot_new,old_average_seconds_per_integrand_call_derived=oldtime/(7*tot_old),new_average_seconds_per_integrand_call_derived=newtime/(7*tot_new),new_individual_seconds_min=min(seconds),new_individual_seconds_median=statistics.median(seconds),new_individual_seconds_max=max(seconds),new_elapsed_wall_seconds=723,estimate_seconds=oldtime*5/6,output_counts=counts,cache_args_stage_and_hash_mismatches=0,legacy_outer_containment_mismatches=0,old_per_integral_cache_in_pinned_sources=False,old_run_2R='NOT_RECORDED',E4='NOT_RUN')
(out/'REGISTRATION_CHECK.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
