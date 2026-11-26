"""Read-only extraction from the registered original journals, not a numerical rerun."""
from fractions import Fraction
from pathlib import Path
from collections import Counter
import csv,json
here=Path(__file__).resolve().parent
p=here.parent/'RESULT'
def rows(n):
    with (p/n).open() as f:
        yield from map(json.loads,f)
def rational(x):
    if 'e' in x:return Fraction(int(x['n']))*Fraction(2)**int(x['e'])
    return Fraction(int(x['n']),int(x['d']))
def coords(r):return tuple(map(rational,r['box']))
quantities=('Z1','Z2','D1','D2')
expected={'Z1':(5487,0),'Z2':(1120,0),'D1':(0,1445),'D2':(0,622)}
box_nodes={(r['quantity'],r['node']):r for r in rows('boxes.jsonl') if r.get('record')=='node'}
pending=list(rows('pending.jsonl'))
noncoordinate=[r for r in pending if not ('box' in r and 'node' in r and r.get('phase')=='boxes')]
assert len(noncoordinate)==3
inspection=json.loads((p/'LEDGER_INSPECTION.json').read_text())
summary={}
for q in quantities:
    found=[r for r in pending if r.get('phase')=='boxes' and r.get('quantity')==q and 'node' in r and 'box' in r]
    assert len({r['node'] for r in found})==len(found)
    counts=Counter()
    values=[]
    for r in found:
        k=(q,r['node']);b=box_nodes.get(k)
        if r['reason']=='CELL_BUDGET':
            assert b is None
            status='PENDING'
        elif r['reason']=='DEPTH_LIMIT':
            assert b and b['status']=='UNRESOLVED' and b['reason']=='DEPTH_LIMIT' and coords(b)==coords(r) and b['depth']==r['depth']==18
            status='UNRESOLVED'
        else:raise AssertionError(r)
        y0,y1,z0,z1=coords(r)
        assert Fraction(1,4)<=y0<y1<=1 and 1<=z0<z1<=7
        counts[status]+=1
        values.append((y0,z0,y1,z1,r['node'],[q,status,r['reason'],r['root'],r['node'],r['depth'],str(y0),str(y1),str(z0),str(z1),r['id'],b['id'] if b else '']))
    assert (counts['PENDING'],counts['UNRESOLVED'])==expected[q]
    assert counts['PENDING']+counts['UNRESOLVED']==inspection['quantities'][q]['open']
    assert {r['node'] for r in found if r['reason']=='DEPTH_LIMIT'}=={n for (f,n),b in box_nodes.items() if f==q and b['status']=='UNRESOLVED' and b['reason']=='DEPTH_LIMIT'}
    with (here/(q+'_open_boxes.csv')).open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['quantity','status','reason','root','node','depth','y_min','y_max','z_min','z_max','pending_id','box_id'])
        w.writerows(v[-1] for v in sorted(values))
    summary[q]={'PENDING':counts['PENDING'],'UNRESOLVED_DEPTH_LIMIT':counts['UNRESOLVED'],'total':len(found)}
(here/'noncoordinate_pending.json').write_text(json.dumps(noncoordinate,indent=2)+'\n')
(here/'COUNTS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
print('noncoordinate pending rows:',len(noncoordinate))
