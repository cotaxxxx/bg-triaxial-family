"""V60 samples: the same 96 combos as V59 (samples_v59.json), ordered by the V59/V59-B lower-bound seconds, largest first
(so that idx % P spreads the heavy combos over the P processes). No combo is added or dropped."""
import json
S = json.load(open('../v59/samples_v59.json')); M = json.load(open('../v59/merged_v59b.json'))
key = lambda r: (r['layer'], r['stratum'], r['kind'], tuple(r['tile']), tuple(r['cell']))
lb = {key(r): r['sec'] + (0 if r['status'] == 'COVERED' else r['remaining']*r['sec']/max(r['evals'], 1)) for r in M}
assert len(S) == 96 and all(key(s) in lb for s in S)
S2 = sorted(S, key=lambda s: (-lb[key(s)], json.dumps(s, sort_keys=True)))
json.dump(S2, open('samples_v60.json', 'w'), indent=0)
print(len(S2), 'first', S2[0]['stratum'], S2[0]['kind'], round(lb[key(S2[0])]), 'last', S2[-1]['stratum'], round(lb[key(S2[-1])]))
