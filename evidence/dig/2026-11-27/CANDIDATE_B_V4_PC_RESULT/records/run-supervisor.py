"""Operational receipt, independent ledger inspection, and process checks; no changes to bundle."""
import datetime,json,os,pathlib,subprocess,time
b=pathlib.Path('/home/daybreak/candidate-b-v4-pc-20261127')
rec=b/'records';bundle=pathlib.Path((rec/'workdir.txt').read_text().strip());out=b/'RESULT'
v2='/home/daybreak/candidate-b-v2-pc-20261126/RESULT';v3='/home/daybreak/candidate-b-v3-pc-20261126/RESULT'
def stamp():return datetime.datetime.now().astimezone().isoformat()
def save(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2);f.write('\n')
assert not out.exists() and not (rec/'run-start.json').exists()
cmd=['python3','-B','run_candidate_b_v4.py','--bundle-commit','e7c039ee315162a9d3e001734128023bba3ac00f','--chat-audit','5c27aa720a0f8aa39323c0d8c351ac8a55df3a32','--judge-execution','cf375fb123ac1ec86adf5d6d32ef94ef532e65f8','--v2-result',v2,'--v3-result',v3,str(out)]
with (rec/'candidate-b-v4-run.log').open('xb') as log:
    before=time.monotonic();started=stamp()
    p=subprocess.Popen(cmd,cwd=bundle,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save(rec/'run-start.json',dict(started=started,pid=p.pid,process_group=p.pid,command=cmd,numerical_limit_seconds=300,max_formula_calls=76384,internal_inspection_limit_seconds=120))
    rc=p.wait()
    rows=subprocess.check_output(['ps','-eo','pid=,ppid=,pgid=,stat=,comm='],text=True)
    remaining=[r.strip() for r in rows.splitlines() if int(r.split(None,4)[2])==p.pid and not r.split(None,4)[3].startswith('Z')]
    save(rec/'run-end.json',dict(started=started,finished=stamp(),elapsed_seconds=time.monotonic()-before,exit_status=rc,remaining_process_group_members=remaining))
manifest=None;verify=None
if (out/'RESULT_SHA256SUMS.txt').is_file() and not remaining:
    with (rec/'manifest-postcheck.log').open('xb') as f:
        manifest=subprocess.run(['sha256sum','-c','RESULT_SHA256SUMS.txt'],cwd=out,stdout=f,stderr=subprocess.STDOUT).returncode
    if manifest==0:
        with (rec/'verify-v4.log').open('xb') as f:
            try:verify=subprocess.run(['python3','-I','-B','verify_v4.py',v2,v3,str(out)],cwd=bundle,stdout=f,stderr=subprocess.STDOUT,timeout=120).returncode
            except subprocess.TimeoutExpired:verify='DEADLINE'
save(rec/'postcheck-status.json',dict(manifest=manifest,verify_v4=verify))
