"""Operational receipt and process-group checks outside the frozen v3 bundle."""
import datetime,json,os,pathlib,signal,subprocess,sys,time
b=pathlib.Path('/home/daybreak/candidate-b-v3-pc-20261126')
rec=b/'records';bundle=pathlib.Path((rec/'workdir.txt').read_text().strip());out=b/'RESULT'
v2=pathlib.Path('/home/daybreak/candidate-b-v2-pc-20261126/RESULT')
jacobi=pathlib.Path('/home/daybreak/maclaurin-jacobi-pc-20261126/records/run-end.json')
j=json.loads(jacobi.read_text())
assert j['exit_status']==0 and j['finished']=='2026-11-26T18:15:40.143981+09:00'
assert (rec/'jacobi-run-end.json').read_bytes()==jacobi.read_bytes()
def stamp():return datetime.datetime.now().astimezone().isoformat()
def save(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2);f.write('\n')
def members(g):
    rows=subprocess.check_output(['ps','-eo','pid=,ppid=,pgid=,stat=,comm='],text=True)
    return [r.strip() for r in rows.splitlines() if int(r.split(None,4)[2])==g and not r.split(None,4)[3].startswith('Z')]
assert not out.exists() and not (rec/'run-start.json').exists()
cmd=['timeout','--signal=TERM','--kill-after=8s','21592s','python3','-B','run_candidate_b_v3.py','--bundle-commit','cdd885b5ff0fa31408f08a97c382f230f24bab04','--judge-execution','6ebfd9dba7e6c4741b12508904aa5181e86edb57','--v2-result',str(v2),'--jacobi-ended-at',j['finished'],'--jacobi-end-record',str(jacobi),str(out)]
with (rec/'candidate-b-v3-run.log').open('xb') as log:
    before=time.monotonic();started=stamp();limit=before+21600
    p=subprocess.Popen(cmd,cwd=bundle,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save(rec/'run-start.json',dict(started=started,timeout_pid=p.pid,process_group=p.pid,limit_seconds=21600,seal_reserve_seconds=600,pilot_limit_seconds=1800,bundle_audit='e76ac9fe9bbe9e60cd9671b9593155196b86cdbe',command=cmd))
    rc=p.wait()
    remaining=members(p.pid);cleanup=[]
    if remaining:
        cleanup.append('TERM to remaining process group after timeout exit')
        os.killpg(p.pid,signal.SIGTERM)
        for _ in range(8):
            time.sleep(.25);remaining=members(p.pid)
            if not remaining:break
    if remaining:
        cleanup.append('KILL to remaining process group after timeout exit')
        os.killpg(p.pid,signal.SIGKILL)
        for _ in range(8):
            time.sleep(.25);remaining=members(p.pid)
            if not remaining:break
    save(rec/'run-end.json',dict(started=started,finished=stamp(),elapsed_seconds=time.monotonic()-before,exit_status=rc,outer_timeout=rc in (124,137),remaining_process_group_members=remaining,cleanup=cleanup,operational_status='RUNNER_FINISHED' if rc==0 and not remaining and not cleanup else 'STOPPED_OR_PARTIAL'))
# The post-run verifier reads ledgers; it never reruns the numerical kernel.
manifest=None;verify=None
if (out/'RESULT_SHA256SUMS.txt').is_file():
    with (rec/'manifest-postcheck.log').open('xb') as f:
        manifest=subprocess.run(['sha256sum','-c','RESULT_SHA256SUMS.txt'],cwd=out,stdout=f,stderr=subprocess.STDOUT).returncode
    if manifest==0 and not remaining:
        seconds=limit-time.monotonic()
        if seconds>0:
            with (rec/'verify-v3.log').open('xb') as f:
                try:verify=subprocess.run(['python3','-I','-B','verify_v3.py',str(v2),str(out)],cwd=bundle,stdout=f,stderr=subprocess.STDOUT,timeout=seconds).returncode
                except subprocess.TimeoutExpired:verify='DEADLINE'
        else:
            (rec/'verify-v3.log').write_text('INSPECTION_PENDING: external time limit reached; original in-run ledger inspection retained.\n')
else:
    (rec/'verify-v3.log').write_text('INSPECTION_PENDING: result seal absent; raw journals retained.\n')
save(rec/'postcheck-status.json',dict(manifest=manifest,verify_v3=verify))
