"""Read-only derivation of comparison flags from recorded exact endpoints; no kernel calls."""
import json,csv
from pathlib import Path
from fractions import Fraction as Q
from decimal import Decimal, localcontext
P=Path(__file__).resolve().parent
R=P.parent/'RESULT'
def rows(path):
    return [json.loads(l) for l in path.read_text().splitlines()]
def q(x):
    if isinstance(x,dict):
        return Q(int(x['n']),int(x['d'])) if 'd' in x else Q(int(x['n']))*Q(2)**x['e']
    return Q(x)
def exact(x):
    return str(q(x))
def approx(x):
    with localcontext() as c:
        c.prec=12
        v=q(x);return str(Decimal(v.numerator)/Decimal(v.denominator))
def sign(v):
    a,b=map(q,v)
    return '+' if a>0 else '-' if b<0 else 'CONTAINS_ZERO'
def write(name,obj):
    with (P/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
cfg=json.loads((R/'V3_INPUTS.json').read_text())['interior']
local=R/'work/local/proof'
raw=next(r for r in rows(local/'intersections.jsonl') if r['record']=='interior')
ints=rows(local/'integrals.jsonl')
byid={r['id']:r for r in ints}
assert raw['pair']==['Z1','D2'] and raw['graphs'] is None and raw['chosen'] is None and len(raw['trials'])==9
lo,hi,*_=map(Q,cfg['window']);dy=(hi-lo)/cfg['graph_y_parts']
# Auxiliary exits immediately at first failed band. Match only the evaluations
# preceding first Krawczyk value, and only the exact planned box and stage.
start=next(i for i,r in enumerate(ints) if r['id']==raw['trials'][0]['values'][0])
aux=ints[:start]
def match(f,box,mode,cap):
    found=[r for r in aux if r['quantity']==f and tuple(map(q,r['box']))==tuple(box) and r['derivative']==mode and r['target']==cap]
    assert len(found)<=1
    return found[0] if found else None
pieces=[]
for k in range(cfg['graph_y_parts']):
    y0,y1=lo+k*dy,lo+(k+1)*dy
    piece={'piece':k+1,'y_span':[str(y0),str(y1)],'quantities':{},'slope_difference':'NOT_EVALUATED','endpoint_order':'NOT_EVALUATED'}
    for f in cfg['pair']:
        z0,z1=map(Q,cfg['graph_z'][f][k])
        b=(y0,y1,z0,z1)
        item={'box':[str(x) for x in b],'stages':[],'status':'NOT_EVALUATED'}
        for cap in (256,1024,4096):
            ev=[match(f,x,m,cap) for x,m in [((y0,y1,z0,z0),0),((y0,y1,z1,z1),0),(b,1),(b,2)]]
            if not any(ev):continue
            assert all(ev)
            # source interval endpoints unchanged; flags reproduce auxiliary gate only.
            s=[sign(r['interval']) for r in ev]
            checks={'lower_face_positive':s[0]=='+','upper_face_negative':s[1]=='-','transverse_z_negative':s[3]=='-'}
            item['stages'].append({'target':cap,'records':{n:r for n,r in zip(('lower_face','upper_face','y_derivative','z_derivative'),ev)},'signs':dict(zip(('lower_face','upper_face','y_derivative','z_derivative'),s)),'conditions':checks,'gate':all(checks.values())})
            item['status']='FACE_AND_TRANSVERSE_PASS' if all(checks.values()) else 'FACE_OR_TRANSVERSE_FAIL'
        piece['quantities'][f]=item
    piece['status']='STOPPED_AT_FIRST_FAILED_BAND' if k==0 else 'NOT_EVALUATED'
    pieces.append(piece)
assert len(pieces)==8
assert len(pieces[0]['quantities']['Z1']['stages'])==3
assert all(not s['gate'] for s in pieces[0]['quantities']['Z1']['stages'])
assert all(not a['stages'] for p in pieces for f,a in p['quantities'].items() if p['piece']!=1 or f!='Z1')
assert sum(4*len(a['stages']) for p in pieces for a in p['quantities'].values())==12
write('AUXILIARY_8_PIECES.json',{'source':raw['id'],'original_graphs':raw['graphs'],'scope':'Actual recorded evaluations only. auxiliary() returns None on first failed band. No slope difference or endpoint order was reached. NOT_EVALUATED is not FAIL.','pieces':pieces})
trials=[]
for i,t in enumerate(raw['trials'],1):
    b=list(map(Q,cfg['krawczyk_boxes'][t['box_index']]))
    test=t['test'];assert test is not None
    im=list(map(q,test['image']));norm=q(test['norm'])
    assert len(im)==4
    iy=b[0]<im[0]<=im[1]<b[1];iz=b[2]<im[2]<=im[3]<b[3];cq=norm<1
    assert test['strict']==(iy and iz and cq)
    reasons=[name for name,ok in [('q_less_than_1',cq),('strict_inclusion_y',iy),('strict_inclusion_z',iz)] if not ok]
    trials.append({'trial':i,'box_index':t['box_index'],'target':t['target'],'box':[str(v) for v in b],'image_K_exact':[str(v) for v in im],'q_exact':str(norm),'image_K_approx':[approx(v) for v in im],'q_approx':approx(norm),'conditions':{'q_less_than_1':cq,'strict_inclusion_y':iy,'strict_inclusion_z':iz,'strict':test['strict'],'auxiliary_support':'NOT_AVAILABLE_AND_NOT_REACHED'},'failed_conditions':reasons,'original_trial':t,'integral_records':[byid[id] for id in t['values']+[id for row in t['jacobian'] for id in row]]})
assert len(trials)==9 and all(not t['conditions']['strict'] for t in trials)
write('KRAWCZYK_9_TRIALS.json',{'source':raw['id'],'original_status':raw['status'],'chosen':raw['chosen'],'trials':trials})
with (P/'KRAWCZYK_9_TRIALS.csv').open('x',newline='') as f:
    w=csv.writer(f);w.writerow(['trial','box_index','target','y_lo','y_hi','z_lo','z_hi','K_y_lo','K_y_hi','K_z_lo','K_z_hi','q','q_approx','q_lt_1','K_y_strict','K_z_strict','failed_conditions','auxiliary_support'])
    for t in trials:
        c=t['conditions'];w.writerow([t['trial'],t['box_index'],t['target'],*t['box'],*t['image_K_exact'],t['q_exact'],t['q_approx'],c['q_less_than_1'],c['strict_inclusion_y'],c['strict_inclusion_z'],';'.join(t['failed_conditions']),c['auxiliary_support']])
with (P/'AUXILIARY_8_PIECES.csv').open('x',newline='') as f:
    w=csv.writer(f);w.writerow(['piece','quantity','y_lo','y_hi','z_lo','z_hi','target','status','lower_face_sign','upper_face_sign','dy_sign','dz_sign','lower_face_positive','upper_face_negative','transverse_negative','slope_difference','endpoint_order','evaluation_ids'])
    for p in pieces:
        for f0,a in p['quantities'].items():
            if not a['stages']:
                w.writerow([p['piece'],f0,*a['box'],'','NOT_EVALUATED',*(['NOT_EVALUATED']*9),''])
            for s in a['stages']:
                c=s['conditions'];w.writerow([p['piece'],f0,*a['box'],s['target'],'PASS' if s['gate'] else 'FAIL',*s['signs'].values(),*c.values(),'NOT_EVALUATED','NOT_EVALUATED',';'.join(r['id'] for r in s['records'].values())])
print('Auxiliary: 8 planned pieces, 1 quantity attempted at 3 stages, 12 original integral records, others NOT_EVALUATED')
for s in pieces[0]['quantities']['Z1']['stages']:
    print('AUX',s['target'],s['signs'],s['conditions'])
for t in trials:print('KRAWCZYK',t['trial'],t['target'],'q',t['q_approx'],'failed',t['failed_conditions'])
