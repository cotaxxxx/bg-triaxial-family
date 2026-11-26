"""Execute a frozen band scan, isolate unresolved cases, or replay a receipt."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from ctypes import byref
from fractions import Fraction as Q
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from frozen import HERE,PROV,digest,freeze,need
from method import classify,NAMES,TARGETS

sys.path.insert(0,str(HERE/'base'))
from engine import Kernel,CResult

def key(n,d,box,stage):
    return '|'.join([n,str(d),*map(str,box),str(stage)])

class Interrupted(Exception):
    pass

class Evaluator:
    def __init__(self,deadline):
        self.kernel=Kernel(HERE/'build/kernel.so')
        self.deadline=deadline
        self.raw={}
        self.calls=0

    def __call__(self,n,d,box,stage):
        k=key(n,d,box,stage)
        if k not in self.raw:
            if time.monotonic_ns()>=self.deadline:
                raise Interrupted()
            handle=self.kernel.lib.cb_create(NAMES.index(n),d,128,0,*(str(x).encode() for x in box))
            if not handle:
                raise self.kernel.error()
            try:
                out=CResult()
                status=self.kernel.lib.cb_extend(handle,stage,10000,self.deadline,byref(out))
                self.calls+=out.calls
                if status<0:
                    raise self.kernel.error()
                if status>0:
                    raise Interrupted()
                need(out.leaves==stage,'incomplete quadrature')
                pair=int(out.lo)*Q(2)**out.lo_exp,int(out.hi)*Q(2)**out.hi_exp
                need(pair[0]<=pair[1],'inverted enclosure')
                self.raw[k]=list(map(str,pair))
            finally:
                self.kernel.lib.cb_destroy(handle)
        return tuple(map(Q,self.raw[k]))

def write(path,v):
    tmp=path.with_suffix('.'+str(os.getpid())+'.tmp')
    tmp.write_text(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n')
    tmp.replace(path)

def evaluate_job(item):
    band,trans,name,phase,directory,deadline,stamp=item
    if time.monotonic_ns()>=deadline:
        return 'TIME'
    kernel=Evaluator(deadline)
    try:
        leaves=classify(band,trans,name,kernel,deep=phase=='isolate')
    except Interrupted:
        return 'TIME'
    receipt=dict(chart=band['id'],q=band['q'],name=name,phase=phase,
                 identity=stamp,raw=kernel.raw,leaves=leaves,panel_calls=kernel.calls)
    write(directory/(band['id']+'_'+name+'.json'),receipt)
    return 'DONE'

def replay(path,band,trans,name,phase,stamp):
    data=json.loads(path.read_text())
    need((data['identity'],data['chart'],data['q'],data['name'],data['phase'])==
         (stamp,band['id'],band['q'],name,phase),'receipt identity: '+str(path))
    used=set()
    def read(n,d,box,stage):
        k=key(n,d,box,stage)
        used.add(k)
        lo,hi=map(Q,data['raw'][k])
        need(lo<=hi,'invalid raw interval')
        return lo,hi
    leaves=classify(band,trans,name,read,deep=phase=='isolate')
    need(set(data['raw'])==used and data['leaves']==leaves,'replay mismatch: '+str(path))
    return leaves

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['scan','isolate','verify','preflight'])
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    ap.add_argument('--audit-repo',type=Path,help='repository holding the chat audit, default --repo')
    ap.add_argument('--approval-repo',type=Path,help='repository holding the Judge decision, default --repo')
    ap.add_argument('--judge-approval',help='full Git commit for this specific execution')
    ap.add_argument('--chat-audit',help='full Git commit of the bundle audit')
    ap.add_argument('--workers',type=int,default=4,choices=range(1,9))
    ap.add_argument('--minutes',type=int,default=360,choices=range(1,361))
    args=ap.parse_args()
    subprocess.run(['sha256sum','--quiet','-c','SHA256SUMS.txt'],cwd=HERE,check=True)
    bands=freeze(args.repo)
    print('verified input charts:',len(bands),file=sys.stderr,flush=True)
    if args.action=='preflight':
        return
    need(args.out is not None,'--out required')
    root=args.out.resolve()
    audit,approval=args.chat_audit,args.judge_approval
    stampfile=root/'identity.json'
    lock=None
    if args.action!='verify':
        import fcntl
        for h,source in ((audit,args.audit_repo or args.repo),(approval,args.approval_repo or args.repo)):
            need(h and len(h)==40 and all(c in '0123456789abcdef' for c in h),'full audit and approval commits required')
            subprocess.run(['git','-C',str(source),'cat-file','-e',h+'^{commit}'],check=True)
        need(audit!=approval and not {audit,approval}.intersection(v for v in PROV.values() if isinstance(v,str)),
             'distinct new audit and approval receipts required')
        subprocess.run(['sha256sum','--quiet','-c','build/SHA256SUMS.txt'],cwd=HERE,check=True)
        root.mkdir(parents=True,exist_ok=True)
        lock=(root/'run.lock').open('a')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        identity=dict(audit=audit,approval=approval,bundle=digest((HERE/'SHA256SUMS.txt').read_bytes()),
                      build=digest((HERE/'build/SHA256SUMS.txt').read_bytes()),header=json.loads((HERE/'build/header.json').read_text()),
                      compiler=(HERE/'build/compiler.txt').read_text().splitlines()[0],machine=platform.platform(),
                      provenance=PROV)
        if stampfile.exists():
            need(identity==json.loads(stampfile.read_text()),'resume identity mismatch')
        else:
            write(stampfile,identity)
    identity=json.loads(stampfile.read_text())
    need(identity['bundle']==digest((HERE/'SHA256SUMS.txt').read_bytes()) and identity['provenance']==PROV,'wrong package')
    stamp=digest(stampfile.read_bytes())
    deadline=time.monotonic_ns()+args.minutes*60*10**9
    jobs=[]
    missing=set()
    pending=set()
    unresolved=[]
    zeros=[]
    reversed_leaves=[]
    counts={}
    done=0
    total=0
    for phase in ('scan','isolate'):
        directory=root/phase
        if args.action==phase:
            directory.mkdir(exist_ok=True)
        for band,trans in bands:
            for name in TARGETS[band['q']]:
                filename=band['id']+'_'+name+'.json'
                if phase=='scan':
                    total+=1
                elif filename not in pending:
                    continue
                path=directory/filename
                if not path.is_file():
                    if phase==args.action:
                        jobs.append((band,trans,name,phase,directory,deadline,stamp))
                    if phase=='scan':
                        missing.add(filename)
                    continue
                leaves=replay(path,band,trans,name,phase,stamp)
                open_rows=[x for x in leaves if x['status'] in ('UNRESOLVED','ZERO_EXISTS')]
                if phase=='scan' and open_rows:
                    pending.add(filename)
                    continue
                done+=1
                for row in leaves:
                    status=row['status']
                    counts[status]=counts.get(status,0)+1
                    record=dict(chart=band['id'],coefficient=name,**row)
                    if status in ('UNRESOLVED','ZERO_EXISTS'):
                        unresolved.append(record)
                    if status=='UNIQUE_ZERO':
                        zeros.append(record)
                    if status=='REVERSED':
                        reversed_leaves.append(record)
        if phase=='scan' and args.action=='isolate':
            need(not missing,'finish scan phase before isolate')
    if args.action=='verify':
        report=dict(grade='DIAGNOSTIC_ONLY',receipt='CHECKS_RECORDED' if done==total and not unresolved else 'PARTIAL',
                    tasks=total,completed_tasks=done,missing_scan=len(missing),missing_or_pending=total-done,
                    leaves=counts,unresolved=unresolved,zero_brackets=zeros,reversed=reversed_leaves,
                    note='Per-chart brackets; overlapping witnesses are not distinct-zero counts.')
        print(json.dumps(report,indent=2))
        return
    print('remaining tasks in phase',len(jobs),flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        finished=sum(outcome=='DONE' for outcome in pool.map(evaluate_job,jobs,chunksize=1))
    print(json.dumps(dict(phase=args.action,completed_now=finished,remaining_in_phase=len(jobs)-finished)))
    if finished!=len(jobs):
        raise SystemExit(2)

if __name__=='__main__':
    main()
