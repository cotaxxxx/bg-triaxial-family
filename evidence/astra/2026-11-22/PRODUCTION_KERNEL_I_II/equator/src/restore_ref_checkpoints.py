"""Restore exact outer-latitude records from the committed index."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
from samples import ROOT
from run_intervals import atomic

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('case',help='for example H_36_80')
    a=ap.parse_args()
    base=ROOT/'results'/'checkpoints'
    index=json.loads((base/'INDEX.json').read_text())
    entry=index[a.case]
    work=ROOT/'results'/'ref_work';work.mkdir(exist_ok=True)
    with (work/(a.case+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=[]
        for row in entry['files']:
            raw=(base/row['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('checkpoint digest mismatch')
            data.append(raw)
        raw=b''.join(data);f=work/(a.case+'.jsonl')
        if len(raw.splitlines())!=entry['rows']:raise ValueError('checkpoint row count mismatch')
        if f.exists():
            local=f.read_bytes()
            if local.startswith(raw):return
            if not raw.startswith(local):raise ValueError('local checkpoint diverged')
        atomic(f,raw.decode())
if __name__=='__main__':main()
