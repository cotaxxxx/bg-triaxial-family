"""Operational orchestration only. Frozen runner and numerical kernel are unmodified."""
import collections,datetime,hashlib,json,os,pathlib,signal,subprocess,time
b=pathlib.Path('/home/daybreak/paper-ii-correspondence-pc-20261127')
rec=b/'records';bundle=pathlib.Path((rec/'workdir.txt').read_text().strip());out=b/'RESULT'
repo='/home/daybreak/e2ref/repo'
audit='c3042489ee3b4bb425d95d9ba0d257d683c3eba1'
approval='f9dd5c54d9e45a3d28c9c7e3d8318599a0ab3f9a'
def stamp():return datetime.datetime.now().astimezone().isoformat()
def save(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2,ensure_ascii=False);f.write('\n')
def group_members(pgid):
    rows=subprocess.check_output(['ps','-eo','pid=,ppid=,pgid=,stat=,comm='],text=True)
    return [r.strip() for r in rows.splitlines() if int(r.split(None,4)[2])==pgid and not r.split(None,4)[3].startswith('Z')]
def phase(name,minutes,wall_limit):
    cmd=['python3','-B','run.py',name,'--repo',repo,'--out',str(out),'--chat-audit',audit,'--judge-approval',approval,'--workers','4','--minutes',str(minutes)]
    started=stamp();t0=time.monotonic();timed_out=False
    with (rec/(name+'.log')).open('xb') as log:
        p=subprocess.Popen(cmd,cwd=bundle,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        save(rec/(name+'-start.json'),dict(started=started,pid=p.pid,process_group=p.pid,command=cmd,wall_limit_seconds=wall_limit))
        try:rc=p.wait(timeout=max(0,wall_limit-(time.monotonic()-t0)))
        except subprocess.TimeoutExpired:
            timed_out=True
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:rc=p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
        remaining=group_members(p.pid)
        if remaining:
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            time.sleep(1)
            remaining=group_members(p.pid)
            if remaining:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                time.sleep(1)
                remaining=group_members(p.pid)
    result=dict(started=started,finished=stamp(),elapsed_seconds=time.monotonic()-t0,exit_status=rc,outer_timeout=timed_out,remaining_process_group_members=remaining)
    save(rec/(name+'-end.json'),result)
    return result
def scan_gate():
    supports=[json.loads(l) for l in (bundle/'SUPPORT.jsonl').read_text().splitlines()]
    targets={'Z1':('Az','By'),'Z2':('Az','Bx'),'D1':('Ny','Jyx','Jyz'),'D2':('Nx','Jxy','Jxz')}
    expected={s['id']+'_'+n+'.json':(s['id'],s['q'],n) for s in supports for n in targets[s['q']]}
    assert len(expected)==1412
    seen=set();counts=collections.Counter();by_quantity=collections.defaultdict(collections.Counter)
    stamp_hash=hashlib.sha256((out/'identity.json').read_bytes()).hexdigest()
    for f in (out/'scan').glob('*.json'):
        d=json.loads(f.read_text())
        assert f.name in expected and (d['chart'],d['q'],d['name'])==expected[f.name] and d['phase']=='scan' and d['identity']==stamp_hash
        assert len(d['leaves'])==1
        st=d['leaves'][0]['status'];assert st in ('EXPECTED','REVERSED','UNRESOLVED')
        seen.add(f.name);counts[st]+=1;by_quantity[d['q']+'/'+d['name']][st]+=1
    return dict(tasks=1412,completed=len(seen),missing=1412-len(seen),counts=dict(counts),by_quantity={k:dict(v) for k,v in by_quantity.items()},unresolved=counts['UNRESOLVED'],threshold=706,threshold_exceeded=counts['UNRESOLVED']>706)
assert not out.exists() and not (rec/'run-start.json').exists()
started=stamp();t0=time.monotonic();hard=t0+21600
save(rec/'run-start.json',dict(started=started,bundle_commit='04051b610bd1ada9992e8912a3bdad4954ae929c',bundle_sha256='3e655bb2d907bf5c641fa9a38fd7256438f49cda636400331b7e5dab47fad8cf',audit=audit,approval=approval,workers=4,scan_minutes=59,scan_wall_limit_seconds=3600,total_wall_limit_seconds=21600,unresolved_stop_threshold=706,withdrawn_old_bundle='3accf27'))
# Leave 60 seconds for scan initialization and worker shutdown within 60 minutes.
scan=phase('scan',59,3595)
gate=None;iso=None;reason=None
if scan['remaining_process_group_members']:
    reason='SCAN_PROCESS_GROUP_REMAINS'
elif not (out/'identity.json').is_file() or not (out/'scan').is_dir():
    reason='SCAN_OUTPUT_MISSING'
else:
    gate=scan_gate()
    gate['scan_exit_status']=scan['exit_status']
    remaining=hard-time.monotonic()
    minutes=min(360,int((remaining-60)//60))
    gate['isolate_minutes']=minutes
    if scan['exit_status']!=0 or gate['missing']:
        reason='SCAN_INCOMPLETE_OR_ERROR'
    elif gate['threshold_exceeded']:
        reason='UNRESOLVED_GT_706'
    elif minutes<1:
        reason='NO_REMAINING_BUDGET'
    else:
        reason='ISOLATE_AUTHORIZED'
    gate['decision']=reason
    save(rec/'scan-gate.json',gate)
    if reason=='ISOLATE_AUTHORIZED':
        iso=phase('isolate',minutes,max(0,hard-time.monotonic()-5))
        reason='ISOLATE_FINISHED' if iso['exit_status']==0 and not iso['remaining_process_group_members'] else 'ISOLATE_PARTIAL_OR_ERROR'
finish=stamp()
save(rec/'run-end.json',dict(started=started,finished=finish,elapsed_seconds=time.monotonic()-t0,reason=reason,scan=scan,isolate=iso))
# No further kernel evaluation after this point. Standalone verify replays sealed receipt data only.
if (out/'identity.json').is_file() and not scan['remaining_process_group_members'] and not (iso and iso['remaining_process_group_members']):
    (out/'scan').mkdir(exist_ok=True);(out/'isolate').mkdir(exist_ok=True)
    cmd=['python3','-B','run.py','verify','--repo',repo,'--out',str(out)]
    with (out/'verification.log').open('xb') as log,(rec/'verify-stderr.log').open('xb') as err:
        try:verify=subprocess.run(cmd,cwd=bundle,stdout=log,stderr=err,timeout=600).returncode
        except subprocess.TimeoutExpired:verify='DEADLINE'
    with (out/'RESULT_SHA256SUMS.txt').open('x') as f:
        for p in sorted([out/'identity.json',out/'verification.log',*list((out/'scan').rglob('*')),*list((out/'isolate').rglob('*'))],key=lambda p:os.fsencode(str(p.relative_to(out)))):
            if p.is_file():f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(out))+'\n')
    with (rec/'manifest-postcheck.log').open('xb') as f:
        manifest=subprocess.run(['sha256sum','-c','RESULT_SHA256SUMS.txt'],cwd=out,stdout=f,stderr=subprocess.STDOUT).returncode
    save(rec/'postcheck-status.json',dict(verify=verify,manifest=manifest))
else:
    save(rec/'postcheck-status.json',dict(verify=None,manifest=None,reason='unavailable identity or surviving processes'))
