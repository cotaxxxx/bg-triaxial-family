"""External operational deadline; no changes to frozen bundle or its output."""
import datetime,hashlib,json,os,pathlib,signal,subprocess,sys,time
b=pathlib.Path('/home/daybreak/candidate-b-pc-20261126')
rec=b/'records';bundle=pathlib.Path((rec/'workdir.txt').read_text().strip());out=b/'RESULT'
def stamp(): return datetime.datetime.now().astimezone().isoformat()
def save(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2);f.write('\n')
def members(g):
    rows=subprocess.check_output(['ps','-eo','pid=,ppid=,pgid=,stat=,comm='],text=True)
    return [r.strip() for r in rows.splitlines() if int(r.split(None,4)[2])==g and not r.split(None,4)[3].startswith('Z')]
assert not out.exists() and not (rec/'run-start.json').exists()
assert hashlib.sha256((bundle/'build/candidate_kernel.so').read_bytes()).hexdigest()==json.loads((bundle/'build/BUILD.json').read_text())['library_sha256']
cmd=[sys.executable,'-B','run_candidate_b.py','--bundle-commit','f70b83b24fc62b7bbd7b3d70b24163ab8bf8f779','--judge-execution','4247e0c1f995dcac4b17cb795d371c2d38754383',str(out)]
with (rec/'candidate-b-run.log').open('xb') as log:
    before=time.monotonic();started=stamp();limit=before+21600
    p=subprocess.Popen(cmd,cwd=bundle,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save(rec/'run-start.json',dict(started=started,parent_pid=p.pid,process_group=p.pid,limit_seconds=21600,pilot_limit_seconds=1800,bundle_audit='d59497bd7c11d160adad3d29d30055375d07fc16',command=cmd))
    expired=False;term=None;escalation=[]
    try:rc=p.wait(timeout=max(0,limit-time.monotonic()))
    except subprocess.TimeoutExpired:
        expired=True;term=stamp()
        p.terminate()
        try:rc=p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            escalation.append('parent still running after TERM; TERM to run process group')
            os.killpg(p.pid,signal.SIGTERM)
            try:rc=p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                escalation.append('KILL to run process group');os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
    remaining=members(p.pid)
    for _ in range(8):
        if not remaining:break
        time.sleep(.25);remaining=members(p.pid)
    if remaining:
        escalation.append('TERM to remaining run group after parent exit')
        os.killpg(p.pid,signal.SIGTERM)
        for _ in range(40):
            remaining=members(p.pid)
            if not remaining:break
            time.sleep(.25)
    if remaining:
        escalation.append('KILL to remaining run group')
        os.killpg(p.pid,signal.SIGKILL)
        for _ in range(40):
            remaining=members(p.pid)
            if not remaining:break
            time.sleep(.25)
    save(rec/'run-end.json',dict(started=started,finished=stamp(),elapsed_seconds=time.monotonic()-before,exit_status=rc,outer_timeout=expired,term_sent=term,escalation=escalation,remaining_process_group_members=remaining,operational_status='PARTIAL' if expired or remaining or rc or escalation else 'RUNNER_FINISHED'))
# Preserve output; only ledger inspection, never numerical integration or a second run.
if (out/'RESULT_SHA256SUMS.txt').is_file():
    with (rec/'manifest-postcheck.log').open('xb') as f:
        manifest=subprocess.run(['sha256sum','-c','RESULT_SHA256SUMS.txt'],cwd=out,stdout=f,stderr=subprocess.STDOUT).returncode
    check=None;remaining_seconds=limit-time.monotonic()
    if manifest==0 and remaining_seconds>0 and not remaining:
        with (rec/'verify-ledgers.log').open('xb') as f:
            try:
                check=subprocess.run([sys.executable,'-B','verify_ledgers.py',str(out)],cwd=bundle,stdout=f,stderr=subprocess.STDOUT,timeout=remaining_seconds).returncode
            except subprocess.TimeoutExpired:check='DEADLINE'
    else:
        (rec/'verify-ledgers.log').write_text('INSPECTION_PENDING: no time remaining, run process remains, or manifest check failed. Existing LEDGER_INSPECTION.json preserved.\n')
    save(rec/'postcheck-status.json',dict(manifest=manifest,verify_ledgers=check))
