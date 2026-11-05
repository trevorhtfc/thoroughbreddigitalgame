import json,sys,numpy as np,warnings; warnings.filterwarnings('ignore')
from racebench import run,PAR_TIME
P=json.load(open('settings.json'))
for key in sys.argv[1].split(','):
    Q=dict(P); Q['CHECK_DV']=P['CHECK_DV_BY_COURSE']['straight' if key[0]=='s' else 'round']
    for k,v in json.loads(sys.argv[2] if len(sys.argv)>2 else '{}').items(): Q[k]=v
    N=int(sys.argv[3]) if len(sys.argv)>3 else 500
    r=run(Q,key,N=N,n=12,seed=8); raw=r['raw']; Rd=np.asarray(raw['Rday']); pos=np.asarray(raw['pos'])
    tb=np.random.default_rng(0).random(Rd.shape)*1e-3; ix=np.arange(N); b=np.argmax(Rd+tb,1)
    print(f"{key:6s} time {r['all']['time']:6.1f} (rough real {PAR_TIME[key]}) | best wins {round(float((pos[ix,b]==1).mean())*100,1)}% | margin {r['all']['margin']} | styles {r['style_win']} | traffic 1L+ {r['traffic']['lose1']} | draw {r['draw_win']}",flush=True)
