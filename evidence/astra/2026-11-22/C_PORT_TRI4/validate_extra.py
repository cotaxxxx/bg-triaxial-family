import json
from pathlib import Path
def validate(d):
    load=lambda name:[json.loads(line) for line in (d/name).read_text().splitlines()]
    p,c=[load('branches_'+s+'.jsonl') for s in ('python','c')]
    errors=[]
    if len(p)!=7 or p!=c:errors.append(dict(test='branch cases',python=p,c=c))
    tags={k:[r['label'] for r in p if r['observed'].get(k)] for k in ('contact','coarse','lazy','p0','outside','point')}
    normals=load('A_c.jsonl')
    tags['graded']=[r['label'] for r in p if r['grade']!=0]
    tags['kinds']=sorted({r['kind'] for r in normals})
    if not all(tags.values()) or tags['kinds']!=['C12','H33','W3']:errors.append(dict(test='branch coverage',observed=tags))
    x,y=[load('array_'+s+'.jsonl') for s in ('python','c')]
    if x!=y or len(x)!=8:errors.append(dict(test='primitive arrays',python=x,c=y))
    return tags,errors
