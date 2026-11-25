"""Operational deadline supervisor; the frozen bundle and result directory are unchanged."""
import datetime,hashlib,json,os,pathlib,signal,subprocess,sys,time
from fractions import Fraction as F
b=pathlib.Path('/home/daybreak/e4-pc-20261125');bundle=b/'E4_PC_BUNDLE';rec=b/'records';out=b/'E4_RESULT'
def stamp():return datetime.datetime.now().astimezone().isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def groups(g):
    rows=subprocess.check_output(['ps','-eo','pid=,ppid=,pgid=,stat=,args='],text=True)
    return [r.strip() for r in rows.splitlines() if int(r.split(None,4)[2])==g and not r.split(None,4)[3].startswith('Z')]
def save(path,o):
    with path.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
assert not out.exists()
assert not (rec/'run-start.json').exists()
assert 'E1 staged check PASS' in (rec/'e1-stage-check.log').read_text()
assert digest(bundle/'build/kernel')=='ec6b0f68af615bd7fc8561307c8a33ee898cafcfb325ea8399c2cfcfe64a33df'
assert digest(b/'E4_PC_BUNDLE_20261125.tar.gz')=='c7dacbaf477800f528dfb129f91a9f76b4736df10bced2036f172bdfb41e582b'
budget=json.loads((b/'bench/BUDGET.json').read_text())
B=F(budget['wall_budget_seconds']);limit=B+3600
subprocess.run([sys.executable,'-B',str(rec/'preflight-resources.py')],check=True,stdout=(rec/'resource-before-e4.json').open('x'))
cmd=[sys.executable,'-B','src/run_e4.py','--bench',str(b/'bench'),'--output',str(out),'--bundle-audit','57f08eb3499f8273dcb602a8d3f7b82f80ab5bb6','--judge-execution-approval','e4ee768238aa3436f38381698af21dad31199b77']
with (rec/'e4-run.log').open('xb') as log:
    before=time.monotonic();started=stamp()
    p=subprocess.Popen(cmd,cwd=bundle,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save(rec/'run-start.json',dict(started=started,parent_pid=p.pid,process_group=p.pid,wall_budget_seconds=str(B),outer_limit_seconds=str(limit),command=cmd))
    timeout=False; term=None;escalation=[]
    try:
        rc=p.wait(timeout=max(0,float(limit)-(time.monotonic()-before)))
    except subprocess.TimeoutExpired:
        timeout=True;term=stamp();p.terminate()
        # The parent handles TERM and signals its workers to save and exit.
        try:rc=p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            escalation.append('parent did not exit within 120s of TERM; TERM to this run process group')
            os.killpg(p.pid,signal.SIGTERM)
            try:rc=p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                escalation.append('KILL to this run process group after TERM grace')
                os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
    # Resource tracker and forkserver can exit just after the parent.
    for _ in range(40):
        remaining=groups(p.pid)
        if not remaining:break
        time.sleep(0.25)
    if remaining:
        escalation.append('remaining members after parent exit; TERM to this run process group')
        os.killpg(p.pid,signal.SIGTERM)
        for _ in range(40):
            remaining=groups(p.pid)
            if not remaining:break
            time.sleep(0.25)
    if remaining:
        escalation.append('remaining members after TERM; KILL to this run process group')
        os.killpg(p.pid,signal.SIGKILL)
        for _ in range(40):
            remaining=groups(p.pid)
            if not remaining:break
            time.sleep(0.25)
    result=dict(started=started,finished=stamp(),elapsed_seconds=time.monotonic()-before,exit_status=rc,outer_timeout=timeout,term_sent=term,escalation=escalation,remaining_process_group_members=remaining,operational_status='PARTIAL' if timeout or rc or remaining or escalation else 'RUNNER_FINISHED')
    save(rec/'run-end.json',result)
if (out/'RESULT_SHA256SUMS.txt').is_file():
    with (rec/'postcheck.log').open('xb') as f:
        check=subprocess.run([sys.executable,'-B','src/check_e4.py',str(out)],cwd=bundle,stdout=f,stderr=subprocess.STDOUT).returncode
        manifest=subprocess.run(['sha256sum','-c','RESULT_SHA256SUMS.txt'],cwd=out,stdout=f,stderr=subprocess.STDOUT).returncode
    save(rec/'postcheck-status.json',dict(check_e4=check,manifest=manifest))
