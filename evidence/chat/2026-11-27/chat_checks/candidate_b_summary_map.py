import json,sys
from fractions import Fraction as F
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
V2,OUT=sys.argv[1],sys.argv[2]
def r(v): return float(F(int(v['n']))*(F(2)**v['e']))
col={'Z1':'tab:blue','Z2':'tab:cyan','D1':'tab:red','D2':'tab:orange'}; nm={'Z1':'Z1 (A_y=0)','Z2':'Z2 (A_x=0)','D1':'∂1 (T_y=0)','D2':'∂2 (T_x=0)'}
fig,ax=plt.subplots(figsize=(7,9))
for q in col:
    pts=sorted(((r(c['box'][0])+r(c['box'][1]))/2,(r(c['box'][2])+r(c['box'][3]))/2) for c in map(json.loads,open(V2+'/charts.jsonl')) if c['quantity']==q and c['status']=='CHART')
    ax.plot([p[0] for p in pts],[p[1] for p in pts],'-',color=col[q],lw=2.2,label=nm[q])
ax.plot([0.63818],[2.29659],'k*',ms=16,zorder=5); ax.annotate('Z1∩∂2: exactly one\n(0.6382, 2.2966)',(0.63818,2.29659),(0.30,2.9),arrowprops=dict(arrowstyle='->'))
ax.plot([1,1],[4.724,2.065],'ks',ms=7,zorder=5); ax.annotate('c_p (shared end of Z1,Z2)',(1,4.724),(0.62,5.15),arrowprops=dict(arrowstyle='->')); ax.annotate('b_p (shared end of ∂1,∂2)',(1,2.065),(0.70,1.45),arrowprops=dict(arrowstyle='->'))
ax.plot([1],[1],'ko',ms=6); ax.annotate('sphere',(1,1),(0.9,1.12))
ax.set_xlim(0.25,1.005); ax.set_ylim(1,7); ax.set_xlabel('y (short axis, x=1 fixed)'); ax.set_ylabel('z (long axis)'); ax.grid(alpha=.3); ax.legend(loc='upper left')
ax.set_title('Candidate B on R=[1/4,1]×[1,7]: four arcs, six pair relations\n(v2 862220c + v3 7c6cd7e + v4 f58ca0c; DIAGNOSTIC_ONLY records)')
fig.tight_layout(); fig.savefig(OUT,dpi=120)
