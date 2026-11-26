import json,sys
from fractions import Fraction as F
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
V2,OUT=sys.argv[1],sys.argv[2]
def r(v): return float(F(int(v['n']))*(F(2)**v['e']))
col={'Z1':'tab:blue','Z2':'tab:cyan','D1':'tab:red','D2':'tab:orange'}
nm={'Z1':'Z1: A_y=0  (centre, short-axis pair)','Z2':'Z2: A_x=0  (centre, middle-axis pair)','D1':'∂1: T_y=0  (pole ±e_y, short-axis pair)','D2':'∂2: T_x=0  (pole ±e_x, middle-axis pair)'}
P={}
fig,ax=plt.subplots(figsize=(7.4,9))
for q in col:
    P[q]=sorted(((r(c['box'][0])+r(c['box'][1]))/2,(r(c['box'][2])+r(c['box'][3]))/2) for c in map(json.loads,open(V2+'/charts.jsonl')) if c['quantity']==q and c['status']=='CHART')
    ax.plot([p[0] for p in P[q]],[p[1] for p in P[q]],'-',color=col[q],lw=2.4,label=nm[q])
def band(lower,upper,color,hatch):
    import numpy as np
    ys=np.linspace(0.25,1,400)
    def interp(pts,y):
        xs=[p[0] for p in pts]; zs=[p[1] for p in pts]; return np.interp(y,xs,zs,left=np.nan,right=np.nan)
    lo=np.array([interp(lower,y) for y in ys]); hi=np.array([interp(upper,y) for y in ys]); lo=np.where(np.isnan(lo),1.0,lo)
    ax.fill_between(ys,lo,hi,where=~np.isnan(hi),facecolor='none',edgecolor=color,hatch=hatch,lw=0,alpha=0.35)
band(P['D1'],P['Z1'],'tab:red','///'); band(P['D2'],P['Z2'],'tab:orange','\\\\\\')
bb=dict(facecolor='white',edgecolor='none',alpha=0.85,pad=1.5)
ax.text(0.86,3.1,'both pairs',color='k',ha='center',fontsize=9,bbox=bb)
ax.text(0.62,1.55,'short-axis pair only',color='tab:red',ha='center',fontsize=9,bbox=bb)
ax.text(0.45,4.2,'middle-axis pair only',color='darkorange',ha='center',fontsize=9,bbox=bb)
ax.text(0.33,1.6,'none',ha='center',fontsize=9,bbox=bb); ax.text(0.5,6.5,'none',ha='center',fontsize=9,bbox=bb); ax.text(0.88,1.2,'none',ha='center',fontsize=9,bbox=bb)
ax.plot([0.63818],[2.29659],'k*',ms=15,zorder=5); ax.plot([1,1],[4.724,2.065],'ks',ms=7,zorder=5); ax.plot([1],[1],'ko',ms=6)
ax.annotate('c_p: stationary circle',(1,4.724),(0.62,5.25),arrowprops=dict(arrowstyle='->'),fontsize=8); ax.annotate('b_p: stationary circle',(1,2.065),(0.74,1.85),arrowprops=dict(arrowstyle='->'),fontsize=8)
ax.set_xlim(0.25,1.005); ax.set_ylim(1,7); ax.set_xlabel('y (short axis; middle axis x=1)'); ax.set_ylabel('z (long axis)'); ax.grid(alpha=.3); ax.legend(loc='upper right',fontsize=8)
ax.set_title('Threshold map on R=[1/4,1]×[1,7]\nhatching = side on which the local theorems place the pair (certified only near the curves)',fontsize=10)
fig.tight_layout(); fig.savefig(OUT,dpi=120)
