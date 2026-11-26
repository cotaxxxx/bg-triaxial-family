"""chat: publication figures for Paper II (centres of the certified strips of the v2 ledger; illustration only).
usage: python3 -I paper2_figures.py V2_RESULT_DIR OUT_DIR"""
import json,sys
from fractions import Fraction as F
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
V2,OUT=sys.argv[1],sys.argv[2]
def r(v): return float(F(int(v['n']))*(F(2)**v['e']))
plt.rcParams.update({'font.size':10,'mathtext.fontset':'cm','axes.spines.top':False,'axes.spines.right':False})
col={'Z1':'#0072B2','Z2':'#56B4E9','D1':'#D55E00','D2':'#E69F00'}; ls={'Z1':'-','Z2':'-','D1':'--','D2':'--'}
nm={'Z1':r'$Z_1$:  $A_y=0$  (centre, short axis)','Z2':r'$Z_2$:  $A_x=0$  (centre, middle axis)','D1':r'$\partial_1$:  $T_y=0$  (poles $\pm e_y$)','D2':r'$\partial_2$:  $T_x=0$  (poles $\pm e_x$)'}
P={q:[] for q in col}
for c in map(json.loads,open(V2+'/charts.jsonl')):
    if c['status']=='CHART': P[c['quantity']].append(((r(c['box'][0])+r(c['box'][1]))/2,(r(c['box'][2])+r(c['box'][3]))/2))
END={'Z1':[(0.40796,1),(1,4.7244)],'Z2':[(0.25,5.86),(1,4.7244)],'D1':[(0.64355,1),(1,2.06538)],'D2':[(0.25,2.20),(1,2.06538)]}
for q in P: P[q]=np.array(sorted(P[q]+END[q]))
def base(ax):
    for q in col: ax.plot(P[q][:,0],P[q][:,1],ls[q],color=col[q],lw=2.2,label=nm[q],zorder=3)
    ax.plot([0.25,1,1,0.25,0.25],[1,1,7,7,1],color='0.35',lw=0.8,zorder=1)
    ax.set_xlim(0.22,1.06); ax.set_ylim(0.62,7.1); ax.set_xlabel(r'$y$  (short semi-axis; middle semi-axis $=1$)'); ax.set_ylabel(r'$z$  (long semi-axis)')
    ax.plot([1,1],[4.7244,2.06538],'s',color='k',ms=6,zorder=5); ax.plot([0.40796,0.64355],[1,1],'s',color='k',ms=6,zorder=5,clip_on=False)
    ax.plot([0.63818],[2.29659],'*',color='k',ms=14,zorder=6); ax.plot([1],[1],'o',color='k',ms=5,zorder=5)
    t=dict(fontsize=10); ax.text(1.012,4.7244,r'$c_p$',va='center',**t); ax.text(1.012,2.06538,r'$b_p$',va='center',**t)
    ax.text(0.40796,0.9,r'$c_o$',ha='center',va='top',**t); ax.text(0.64355,0.9,r'$b_o$',ha='center',va='top',**t); ax.text(1.012,0.97,'ball',va='center',fontsize=8)
    ax.text(0.84,0.93,'oblate spheroids ($z=1$)',fontsize=8,ha='center',va='top',color='0.3'); ax.text(0.985,5.9,'prolate spheroids ($y=1$)',fontsize=8,rotation=90,ha='right',va='center',color='0.3')
# Figure 1
fig,ax=plt.subplots(figsize=(6.2,7.6)); base(ax)
ax.annotate(r'$(y_*,z_*)$',(0.63818,2.29659),(0.48,2.75),arrowprops=dict(arrowstyle='-',lw=0.6),fontsize=10)
ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.09),ncol=2,fontsize=8.5,frameon=False); fig.tight_layout(); fig.savefig(OUT+'/paper2_fig1_map.png',dpi=300); fig.savefig(OUT+'/paper2_fig1_map.pdf')
# Figure 2: side on which the local pair exists (thin band next to each arc)
fig,ax=plt.subplots(figsize=(6.2,7.6)); base(ax)
w=0.22
for q,s in (('Z2',-1),('D2',+1)): ax.fill_between(P[q][:,0],P[q][:,1],P[q][:,1]+s*w,color=col[q],alpha=0.28,lw=0,zorder=2)
wy=0.028
for q,s in (('Z1',+1),('D1',-1)):
    o=np.argsort(P[q][:,1]); zz=P[q][o,1]; yy=P[q][o,0]; ax.fill_betweenx(zz,yy,np.clip(yy+s*wy,0.25,1),color=col[q],alpha=0.28,lw=0,zorder=2)
bb=dict(facecolor='white',edgecolor='none',alpha=0.9,pad=1.2)
ax.text(0.90,3.0,'short-axis pair\non these sides',fontsize=8.5,ha='center',bbox=bb,zorder=7); ax.annotate('',(0.775,3.1),(0.835,3.05),arrowprops=dict(arrowstyle='->',lw=0.7)); ax.annotate('',(0.875,1.72),(0.895,2.78),arrowprops=dict(arrowstyle='->',lw=0.7),zorder=7)
ax.text(0.40,4.1,'middle-axis pair\non these sides',fontsize=8.5,ha='center',bbox=bb); ax.annotate('',(0.40,5.72),(0.40,4.45),arrowprops=dict(arrowstyle='->',lw=0.7)); ax.annotate('',(0.40,2.42),(0.40,3.9),arrowprops=dict(arrowstyle='->',lw=0.7))
ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.09),ncol=2,fontsize=8.5,frameon=False); fig.tight_layout(); fig.savefig(OUT+'/paper2_fig2_sides.png',dpi=300); fig.savefig(OUT+'/paper2_fig2_sides.pdf')
