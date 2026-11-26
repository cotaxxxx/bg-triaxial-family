import json,sys
from fractions import Fraction as F
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R,OUT=sys.argv[1],sys.argv[2]
def r(v): return float(F(int(v['n']))*(F(2)**v['e'] if 'e' in v else F(1,int(v['d']))))
L=lambda f:[json.loads(l) for l in open(f'{R}/{f}')]
CH=[c for c in L('charts.jsonl') if c['status']=='CHART']; P=[p for p in L('pending.jsonl') if 'box' in p]
fig,ax=plt.subplots(1,4,figsize=(16,6),sharey=True)
names={'Z1':'Z1 (A_y)','Z2':'Z2 (A_x)','D1':'∂1 (T_y)','D2':'∂2 (T_x)'}
for a,q in zip(ax,('Z1','Z2','D1','D2')):
    for c in CH:
        if c['quantity']==q:
            b=[r(v) for v in c['box']]; a.add_patch(Rectangle((b[0],b[2]),b[1]-b[0],b[3]-b[2],color='tab:blue',lw=0.6,fill=False))
    for p in P:
        if p['quantity']==q:
            b=[r(v) for v in p['box']]; a.add_patch(Rectangle((b[0],b[2]),max(b[1]-b[0],0.004),max(b[3]-b[2],0.02),color='tab:red',alpha=0.8))
    a.set_xlim(0.25,1); a.set_ylim(1,7); a.set_title(names[q]+'\nblue=chart band, red=open (%d)'%sum(p['quantity']==q for p in P)); a.set_xlabel('y'); a.grid(alpha=.3)
ax[0].set_ylabel('z')
fig.suptitle('Candidate B v2 (862220c): where the curves are certified and where boxes remain open')
fig.tight_layout(); fig.savefig(OUT,dpi=110)
