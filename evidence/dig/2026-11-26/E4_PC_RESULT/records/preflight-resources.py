import os,json,pathlib,subprocess
m=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))
cpu=sorted(os.sched_getaffinity(0))
# V60 plan estimates ~1 GB per worker; require 8 GiB plus 4 GiB headroom.
assert len(cpu)>=8 and m>=12*1024*1024,(cpu,m)
print(json.dumps(dict(cpu_affinity=cpu,available_kib=m,required_kib=12*1024*1024,estimated_bench_worker_kib=1024*1024)))
