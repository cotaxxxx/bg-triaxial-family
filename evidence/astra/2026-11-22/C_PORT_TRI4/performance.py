"""One fresh process per backend/workload, strictly serial. Linux RSS is KiB."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

root=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
for name in ['bundle','native','samples','out']: p.add_argument(name,type=Path)
a=p.parse_args()
bundle,native,samples,out=[v.resolve() for v in (a.bundle,a.native,a.samples,a.out)]
out.mkdir(parents=True,exist_ok=True)
for job in ['bench','tree0','tree1','N512']:
    for backend,reader in [('python',bundle/'GER2'),('c',native)]:
        name=f'{job}_{backend}'
        log=out/(name+'.log')
        if job=='bench':
            args=[root/'bench_box.py',bundle/'v60/bench_v60.py',reader]
        elif job=='N512':
            args=[root/'cases_run.py','53']
        else:
            args=[root/'run_tree.py',bundle,reader,samples,job[-1],out/(name+'.jsonl')]
        env=dict(os.environ,PYTHONPATH=str(reader),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        with log.open('x') as f:
            start=time.monotonic()
            proc=subprocess.Popen([sys.executable,*args],env=env,stdout=f)
            _,status,ru=os.wait4(proc.pid,0)
            proc.returncode=os.waitstatus_to_exitcode(status)
            print(json.dumps(dict(name=name,sec=time.monotonic()-start,rss_kib=ru.ru_maxrss,
                                  returncode=proc.returncode)),flush=True)
            if proc.returncode: raise SystemExit(proc.returncode)
