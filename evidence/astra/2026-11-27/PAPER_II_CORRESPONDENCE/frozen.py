"""Resolve the adopted input from local Git objects. No network, no quadrature."""
from collections import Counter
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
PROV=json.loads((HERE/'PROVENANCE.json').read_text())
REG=('Z1','Z2','D1','D2')
PREFIX={'v2':'evidence/dig/2026-11-26/CANDIDATE_B_V2_PC_RESULT/RESULT/',
        'v3':'evidence/dig/2026-11-27/CANDIDATE_B_V3_PC_RESULT/RESULT/',
        'v4':'evidence/dig/2026-11-27/CANDIDATE_B_V4_PC_RESULT/RESULT/'}

def need(ok,message):
    if not ok:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def rational(v):
    return Q(int(v['n']),int(v['d'])) if 'd' in v else Q(int(v['n']))*Q(2)**v['e']

def iv(row):
    lower,upper=map(rational,row['interval'])
    need(lower<=upper,'reversed interval')
    return lower,upper

def signed(pair):
    return 1 if pair[0]>0 else -1 if pair[1]<0 else 0

def rows(repo,version,name,hashes):
    path=PREFIX[version]+name
    data=subprocess.check_output(['git','-C',str(repo),'show',PROV[version]+':'+path])
    need(digest(data)==hashes[version][name],'source hash differs: '+path)
    return [json.loads(line) for line in data.splitlines()] if name.endswith('.jsonl') else json.loads(data)

def supports():
    return [json.loads(l) for l in (HERE/'SUPPORT.jsonl').read_text().splitlines()]

def freeze(repo):
    hashes=json.loads((HERE/'SOURCE_FILES.json').read_text())
    bands=supports()
    lookup={b['id']:b for b in bands}
    need(len(lookup)==614 and Counter(b['q'] for b in bands)==PROV['counts'],'support count')
    slopes={}
    for q in REG:
        prefix='work/main/'+q+'/'
        charts=[c for c in rows(repo,'v2',prefix+'charts.jsonl',hashes) if c['status']=='CHART']
        enc={e['id']:e for e in rows(repo,'v2',prefix+'enclosures.jsonl',hashes)}
        for c in charts:
            b=lookup[c['id']]
            box=tuple(map(rational,c['box']))
            axis=c['cross']
            need(box==tuple(map(Q,b['box'])) and q==b['q']==c['quantity'] and
                 (axis,c['direction'],c['transverse'],c['faces'])==
                 (b['cross'],b['direction'],b['df'],b['faces']),'chart disagreement')
            e=enc[b['df']]
            need(e['box']==c['box'] and e['quantity']==q and e['derivative']==1+axis and
                 signed(iv(e))==b['direction']!=0,'transverse evidence')
            for side,ident in enumerate(c['faces']):
                face=list(box)
                face[2*axis:2*axis+2]=[box[2*axis+side]]*2
                eface=enc[ident]
                need(tuple(map(rational,eface['box']))==tuple(face) and eface['quantity']==q
                     and eface['derivative']==0 and signed(iv(eface))==(2*side-1)*b['direction'],
                     'face evidence')
            slopes[c['id']]=iv(e)
    events=rows(repo,'v3','work/local/proof/intersections.jsonl',hashes)
    rec={r['name']:r for r in events if r.get('record')=='shared'}
    ints={r['id']:r for r in rows(repo,'v3','work/local/proof/integrals.jsonl',hashes)}
    need(rec['cp']['status']=='ORDERED' and signed(tuple(map(rational,rec['cp']['difference'])))==-1,'cp ordering')
    chart=rec['bp']['common_chart']
    for index,q in enumerate(('D1','D2')):
        b=lookup['bp.'+q]
        e=ints[chart['transverse'][index]]
        need(rec['bp']['status']=='ORDERED' and b['df']==e['id'] and e['quantity']==q
             and e['derivative']==2 and chart['box']==e['box'] and b['cross']==1
             and tuple(map(rational,e['box']))==tuple(map(Q,b['box']))
             and signed(iv(e))==chart['direction']==b['direction']==-1,'bp band')
        for j,face in enumerate(chart['faces']):
            pair=tuple(map(rational,face['values'][index]))
            need(pair==tuple(map(Q,b['face_values'][j])) and signed(pair)==1-2*j,'bp face')
        slopes[b['id']]=iv(e)
    receipt=rows(repo,'v4','LEDGER_INSPECTION.json',hashes)
    need(set(slopes)==set(lookup) and receipt['status']=='RELATION_RECORDED'
         and receipt['relations']['Z1+D2']=='EXACTLY_ONE_INTERIOR','support closure')
    return [(b,slopes[b['id']]) for b in bands]
