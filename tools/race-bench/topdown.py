import json,sys,numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from racebench import run, COURSES
P=json.load(open('settings.json'))
COL={0:'#c0392b',1:'#e0902b',2:'#2e6fa8',3:'#7a56a6'}; NAME=['Front-runner','Prominent','Midfield','Hold-up']
PACE=['slow','even','strong','fast']
def grab(course,n,seed,moments,title,out):
    r=run(P,course,N=1,n=n,seed=seed,trace=0); D=COURSES[course]['D']
    fr=r['frames']; fig,axs=plt.subplots(len(moments),1,figsize=(11,2.35*len(moments)+0.6))
    for ax,(togo,label) in zip(axs,moments):
        # nearest second to the moment the leader is at that distance to go
        k=int(np.argmin([abs((D-f[1].max())-togo) for f in fr])); t,x,z,b=fr[k]; lead=x.max()
        x0=lead-62; x1=lead+8
        ax.add_patch(Rectangle((x0,0),x1-x0,30,color='#cfe3bf',zorder=0))
        for zz in range(0,31,4): ax.axhline(zz,color='#c2d9b0',lw=0.6,zorder=0)
        ax.axhline(0,color='#555',lw=2); ax.axhline(30,color='#555',lw=2)
        if x1>=D: ax.axvline(D,color='#b00',lw=2); ax.text(D+0.5,30.6,'winning post',color='#b00',fontsize=7)
        for i in range(n):
            if not (x0<x[i]<x1+3): continue
            ax.add_patch(Rectangle((x[i]-1.2,z[i]-0.45),2.4,0.9,color=COL[r['sty'][i]],zorder=3,ec='black' if b[i] else 'none',lw=2.2 if b[i] else 0))
            ax.text(x[i],z[i]+0.75,str(i+1),fontsize=7,ha='center',va='bottom',zorder=4)
        ax.set_xlim(x0,x1); ax.set_ylim(-1,31.5)
        ax.set_yticks([0,30]); ax.set_yticklabels(['inside rail\n(stall 1)','outer rail' if course!='straight' else "stands' side"],fontsize=7)
        ax.set_xticks([]); ax.set_title(f"{togo:,.0f} m to go (leader), {t:.0f} s: {label}",fontsize=9,loc='left')
    h=[Rectangle((0,0),1,1,color=COL[k]) for k in range(4)]+[Rectangle((0,0),1,1,fc='white',ec='black',lw=2)]
    fig.legend(h,NAME+['boxed in (black outline)'],loc='lower center',ncol=5,fontsize=8,frameon=False)
    order=[int(i)+1 for i in r['order']]
    fig.suptitle(title+f"\nFinishing order by draw: {order[:6]} ...   Running left to right; each strip shows 70 m of track, every horse to scale.",fontsize=10,x=0.01,ha='left')
    fig.tight_layout(rect=(0,0.04,1,0.95)); fig.savefig(out,dpi=140); plt.close(fig)
    return r
if __name__=='__main__':
    import warnings; warnings.filterwarnings('ignore')
    rs={}
    rs['A']=grab('straight',20,14,[(1450,'groups forming'),(900,'three groups'),(400,'the run for home: groups merging'),(60,'the finish')],'Race A: straight mile, 20 runners','v5-race-A-straight-20.png')
    rs['B']=grab('roundmile',16,14,[(1400,'down the chute'),(1050,'joined the loop'),(720,'round the home bend'),(380,'into the straight'),(150,'the last furlong'),(40,'the finish')],'Race B: round mile, 16 runners','v5-race-B-roundmile-16.png')
    rs['C']=grab('roundmile',16,21,[(1400,'down the chute'),(720,'round the home bend'),(380,'into the straight'),(150,'the last furlong'),(40,'the finish')],'Race C: round mile, 16 runners','v5-race-C-roundmile-16.png')
    for k,r in rs.items():
        print(k,'paces',r['hp'].tolist(),'groups',r['grp'].tolist()); print(' styles',''.join('FPMH'[s] for s in r['sty'])); print(' rating',r['R'].tolist())
        print(' lost',[round(float(v),1) for v in r['lost']]); print(' order',[int(i)+1 for i in r['order']])
