"""V61 extrapolation (PLAN_V61 §5). usage: budget_v61.py v61_out_dir v60_out_dir
For each of the 96 combos the final row is the V61 row (the 39 re-run combos) or else the V60 row (the 57 covered ones).
Seconds are converted to this container's seconds with each run's own r = median(bench)/45.1.
Reported per stratum: completed combos, mean evals (lower bound where unfinished), mean seconds (lower bound where
unfinished), and CPU-years = mean seconds x cells x 32 tiles."""
import sys, json, statistics, collections
D61, D60 = sys.argv[1], sys.argv[2]
r61 = statistics.median(json.loads(l)['sec'] for l in open(f'{D61}/bench.jsonl'))/45.1
r60 = statistics.median(json.loads(l)['sec'] for l in open(f'{D60}/bench.jsonl'))/45.1
key = lambda x: (x['layer'], x['stratum'], x['kind'], tuple(x['tile']), tuple(x['cell']))
V60 = {key(x): x for x in map(json.loads, open(f'{D60}/res_v60.jsonl'))}
V61 = {key(x): x for x in map(json.loads, open(f'{D61}/res_v61.jsonl'))}
assert len(V60) == 96 and len(V61) == 39 and all(k in V60 and V60[k]['status'] == 'BUDGET' for k in V61)
rows = []
for k, x in V60.items():
    y, r = (V61[k], r61) if k in V61 else (x, r60)
    done = y['status'] == 'COVERED'
    ev = y['evals'] + (0 if done else y['remaining'])
    sec = (y['sec'] + (0 if done else y['remaining']*y['sec']/max(y['evals'], 1)))/r
    rows.append(dict(k=k, src='V61' if k in V61 else 'V60', done=done, evals=ev, sec=sec, leaves=y['leaves'], status=y['status']))
st = json.load(open('../v59/strata_v59.json'))
cnt = {('I', s): v for s, v in st['counts_I'].items()}; cnt.update({('II', s): v for s, v in st['counts_II'].items()})
cnt[('I', 'rim')] -= 63
YEAR = 3.156e7; tot = collections.defaultdict(float)
print(f"r61 = {r61:.4f}, r60 = {r60:.4f}; V61 budget {next(iter(V61.values()))['budget']} s")
print("status (96 final rows):", dict(collections.Counter(r['status'].split(':')[0] for r in rows)))
print("layer stratum     n done  mean_evals  mean_sec(cont)  cells  CPU-years   [lower bound if done<n]")
for g in sorted(set((k[0], k[1]) for k in V60)):
    rs = [r for r in rows if (r['k'][0], r['k'][1]) == g]
    me = sum(r['evals'] for r in rs)/len(rs); ms = sum(r['sec'] for r in rs)/len(rs); y = ms*cnt[g]*32/YEAR; tot[g[0]] += y
    print(f"{g[0]:5} {g[1]:10} {len(rs):3} {sum(r['done'] for r in rs):4} {me:11.1f} {ms:15.1f} {cnt[g]:6} {y:10.2f}")
print("total CPU-years", {k: round(v, 2) for k, v in tot.items()}, round(sum(tot.values()), 2))
fin = [V61[k] for k in V61 if V61[k]['status'] == 'COVERED']
print(f"V61 completed {len(fin)}/39: evals median {statistics.median([x['evals'] for x in fin]) if fin else '-'}, "
      f"max {max([x['evals'] for x in fin]) if fin else '-'}; container-sec median {statistics.median([x['sec']/r61 for x in fin]) if fin else '-'}")
for k, x in sorted(V61.items(), key=lambda kv: (kv[1]['status'], kv[0])):
    print(' ', x['status'], k[1], k[2], list(k[3]), list(k[4]), 'leaves', x['leaves'], 'evals', x['evals'], 'remaining', x['remaining'],
          'sec', x['sec'], 'last trace', x['trace'][-1] if x['trace'] else None)
