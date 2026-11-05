# Traffic bench: the energy/pace model (bench4) plus lanes across the track, groups, bends and traffic.
# A sketch for tuning the rules, not the engine. Batched: N races x n runners.
import numpy as np, json
LEN=2.4; PAR=16.25
import math
LOOP=2689.8
LOOP_BENDS=[(2617.8,2424.8,131),(1733.8,1357.8,99),(1343.8,1275.8,35),(839.8,604.8,94)]   # metres to go on the loop, degrees turned (from courses/ascot.json)
FUR=201.168
# rough Ascot winning times on good ground, seconds (approximate; to check against real results)
PAR_TIME={'s5f':60.0,'s6f':73.0,'s7f':86.5,'s1m':99.5,'r1m':100.5,'r1m2f':126.0,'r1m4f':150.5,'r1m6f':178.0,'r2m':207.0,'r2m4f':266.0}
DIST={'s5f':5*FUR,'s6f':6*FUR,'s7f':7*FUR,'s1m':8*FUR,'r1m':1649.4,'r1m2f':10*FUR,'r1m4f':12*FUR,'r1m6f':14*FUR,'r2m':16*FUR,'r2m4f':20*FUR}
PPL={'s5f':3.0,'s6f':2.6,'s7f':2.3,'s1m':2.0,'r1m':2.0,'r1m2f':1.75,'r1m4f':1.5,'r1m6f':1.35,'r2m':1.2,'r2m4f':1.0}   # rating points per length
def make_course(key):
    D=DIST[key]
    if key[0]=='s': return dict(D=D,bends=[],stall1=1.625,kind='straight')
    if key=='r1m': return dict(D=D,bends=[(1311.8,1276.0,math.radians(18)),(840.0,605.0,math.radians(94))],stall1=1.625,kind='round')
    bends=[]
    for k in range(3):
        for (a,b,deg) in LOOP_BENDS:
            A,B=a+k*LOOP,b+k*LOOP
            if B>=D: continue
            ang=math.radians(deg)
            if A>D: ang*= (D-B)/(A-B); A=D            # starts part-way round a bend
            bends.append((A,B,ang))
    bends.sort(key=lambda t:-t[0])
    return dict(D=D,bends=bends,stall1=1.625,kind='round')
COURSES_OLD={
 'straight': dict(D=1609.3, bends=[], stall1=1.625),
 # round mile: down the chute, join the loop at 1311.8 m to go (part of the 35 deg kink), the home bend 840-605 m to go (94 deg)
 'roundmile': dict(D=1649.4, bends=[(1311.8,1276.0,np.radians(18)),(840.0,605.0,np.radians(94))], stall1=1.625),
}
def split_groups(g,n):
    r=g.random()
    if n<=10: return 1
    if n<=15: return 2 if r<0.4 else 1
    if n<=20: return 3 if r<0.1 else (2 if r<0.8 else 1)
    return 3 if r<0.35 else (2 if r<0.95 else 1)
def pace_level(fs,fps): return np.where(fs<=0.15,0,np.where((fs>=0.40)|(fps>=0.75),3,np.where(fs>0.30,2,1)))
def run(P,course='straight',N=1500,n=10,seed=7,trace=None):
    C=make_course(course) if course in DIST else COURSES_OLD[course]; D=C['D']; kind=C.get('kind','straight' if course=='straight' else 'round'); S=LEN/(2.0*1609.3)*1609.3/D*1.0
    S=LEN/(PPL.get(course,2.0)*D)
    GOING=P.get('GOING','Good'); gs={'Heavy':0.95,'Softer':0.975,'Good':1.0,'Quicker':1.006,'Quick':1.012}[GOING]; gcost={'Heavy':1.25,'Softer':1.1,'Good':1.0,'Quicker':0.97,'Quick':0.95}[GOING]
    PAR=(D/PAR_TIME[course]*P.get('PAR_FUDGE',1.013) if course in PAR_TIME else 16.25)*gs
    tscale=(D/PAR)/99.0                                   # race length against the mile the settings were tuned on
    g=np.random.default_rng(seed)
    sty=g.choice(4,(N,n),p=P.get('MIX',[.25]*4))
    sty0=sty.copy()
    keen=g.random((N,n))<0.3
    # flexibility: 0 set, 1 adaptable (one style either way), 2 versatile
    flex=g.choice(3,(N,n),p=P.get('FLEX_MIX',[0.3,0.5,0.2]))
    # the jockey reads the likely pace from the racecard and, if the horse allows, rides to suit it
    exp=pace_level((sty==0).mean(1),(sty<=1).mean(1))[:,None]
    want_shift=np.where(exp==0,-1,np.where(exp>=3,1,np.where(exp==2,np.where(g.random((N,n))<0.5,1,0),0)))
    reads=g.random((N,n))<P.get('JOCKEY_READ',0.6)
    shift=np.where(reads&(flex>0),want_shift,0)
    shift=np.where(keen&(shift>0),0,shift)          # a keen horse won't settle further back
    shift=np.where((flex==2)&reads&(g.random((N,n))<P.get('DOUBLE',0.0)),shift*2,shift)
    sty=np.clip(sty+shift,0,3)
    R0=g.integers(P.get('R_LO',94),P.get('R_HI',107),(N,n)); R0=R0.astype(float)
    if P.get('FRANKEL'): R0[:,0]=P['FRANKEL']            # one outstanding horse, in stall 1 (moved round below)
    # handicaps: the race-day rating is the true rating plus how far the handicapper's mark is out (agreed 4 Nov)
    if P.get('HANDICAP'):
        mark=R0+g.normal(0,P.get('H_SD',3.0),(N,n)); Rday=100+(R0-mark)
    else: Rday=R0
    # form on the day: a small everyday wobble, an occasional big day, a rarer flop
    form=g.normal(0,P['FORM_SD'],(N,n))
    up=g.random((N,n))<P.get('UP_P',0.0); form+=np.where(up,g.uniform(P.get('UP_MIN',4),P.get('UP_MAX',10),(N,n)),0)
    flop=g.random((N,n))<P.get('FLOP_P',0.0); form-=np.where(flop,g.uniform(P.get('FLOP_MIN',4),P.get('FLOP_MAX',12),(N,n)),0)
    R=Rday+form
    shade=g.choice([-1,1],(N,n))
    skill=g.uniform(0.15,0.45,(N,n))            # jockey: chance per tenth of a second of spotting a gap
    if P.get('FRANKEL'):
        perm=np.argsort(g.random((N,n)),1); R0=np.take_along_axis(R0,perm,1); R=np.take_along_axis(R,perm,1); Rday=np.take_along_axis(Rday,perm,1)
    stallz=C['stall1']+1.05*np.arange(n)        # horse i is in stall i+1
    z=np.tile(stallz,(N,1)).astype(float)
    # groups (straight course): contiguous by draw
    grp=np.zeros((N,n),int)
    if kind=='straight':
        for b in range(N):
            k=split_groups(g,n); cuts=np.array_split(np.arange(n),k)
            for gi,c in enumerate(cuts): grp[b,c]=gi
    ng=grp.max()+1
    gc=np.zeros((N,3)); pace=np.zeros((N,3),int)
    for gi in range(3):
        m=grp==gi; cnt=m.sum(1)
        mz=np.where(cnt>0,(stallz[None,:]*m).sum(1)/np.maximum(cnt,1),15)
        gc[:,gi]=mz+(15-mz)*0.25
        fs=((sty==0)&m).sum(1)/np.maximum(cnt,1); fps=((sty<=1)&m).sum(1)/np.maximum(cnt,1)
        pace[:,gi]=pace_level(fs,fps)
    hp=np.take_along_axis(pace,grp,1)            # each horse's group pace level
    R=R+np.array(P.get('RUN_BOOST',np.zeros((4,4))))[hp,sty]
    PACEA=np.array(P['PACE']); ps=P.get('PACE_ROUND_SCALE',1.0) if kind!='straight' else 1.0
    PACEA=1+(PACEA-1)*ps                      # bends steady the pace: less extreme both ways
    vpg=PAR*PACEA[hp]
    fsA=(sty==0).mean(1); fpsA=(sty<=1).mean(1); vpA=PAR*PACEA[pace_level(fsA,fpsA)][:,None]
    vp=(vpg*(1-P.get('GROUP_WATCH',0.6))+vpA*P.get('GROUP_WATCH',0.6))*(1+g.normal(0,0.003,(N,1)))
    vR=PAR*(1+(R-100)*S); vC=vR*P['COMFORT']; ref=(1-P['COMFORT'])*vR
    vK0=vR*P['TOP']; burst=vR*(P['BURST']+P['SHADE_TOP']*shade+np.array(P.get('BURST_STYLE',[0,0,0,0]))[sty]*(D/1609.3)**P.get('BURST_DIST_EXP',0.0)); E=P['TANK']*tscale/gcost*(1-P['SHADE_TANK']*shade)
    settle=np.array(P['SETTLE'])[sty]; follow=np.array(P['FOLLOW'])[sty]; own=vR*P['OWN']
    kickAt=np.clip(P['KICK_FROM']/1609.3*D,400,1000)+g.normal(0,P['JUDGE_SD'],(N,n))
    react=np.where(g.random((N,n))<0.1,0.5,0.12)
    x=np.full((N,n),-1.55); v=np.zeros((N,n)); vz=np.zeros((N,n)); fin=np.full((N,n),np.nan)
    extra=np.zeros((N,n)); rank700=np.full((N,n),np.nan); E700=np.full((N,n),np.nan); z700=np.full((N,n),np.nan); ovl=0.0; ovn=0
    lost=np.zeros((N,n)); since=np.full((N,n),9.0); blockedT=np.zeros((N,n)); switchT=np.zeros((N,n)); switchDir=np.zeros((N,n)); inB=np.zeros((N,n),bool)
    dt=0.1; t=0.0; frames=[]
    W=P.get('BODY_W',0.95); AHEAD=P.get('BODY_L',2.9)
    while np.isnan(fin).any() and t<D/11+40:
        toGo=D-x; live=np.isnan(fin)
        # ---- what each horse wants (energy and pace model)
        cruise=np.where(vp<=own,vp,follow*vp+(1-follow)*own)
        want=np.where(x<200,vp*(1-settle),cruise)
        T=np.maximum(toGo,1)/np.maximum(v,10)
        hold=vC+ref*np.sqrt(np.maximum(E,0)/(ref*T))
        kick=toGo<=kickAt
        inB=kick&(toGo<=P['BURST_DIST'])&(E>P.get('BURST_NEEDS',3))
        want=np.where(kick,np.minimum(vK0,hold)+np.where(inB,burst,0),want)
        want=np.where(t<react,0,want)
        # ---- who is around whom: dx[b,i,j] = x_j - x_i
        dx=x[:,None,:]-x[:,:,None]; dz=z[:,None,:]-z[:,:,None]
        other=~np.eye(n,dtype=bool)[None]&live[:,None,:]
        front=(dx>0)&(dx<AHEAD)&(np.abs(dz)<W)&other
        vfront=np.where(front,v[:,None,:],np.inf).min(2)
        blocked=np.isfinite(vfront)&(want>vfront+0.05)&(x>30)
        free_want=want
        want=np.where(blocked,np.minimum(want,vfront),want)
        fw_tick=free_want.copy()
        blockedT+=np.where(blocked&live,dt,0)
        # ---- looking for a gap: the lane a horse-width to each side must be clear from half a length behind to a length and a half ahead
        def clear(side):
            tz=z+side*1.15
            occ=((dx>-P.get('GAP_BEHIND',1.8))&(dx<P.get('GAP_AHEAD',3.0))&(np.abs(z[:,None,:]-tz[:,:,None])<W)&other).any(2)
            return ~occ&(tz>0.6)&(tz<29.4)
        cOut,cIn=clear(1.0),clear(-1.0)
        aheadK=P.get('SEE_AHEAD',7.0)
        trouble=((dx>0)&(dx<aheadK)&(np.abs(dz)<W)&other).any(2)&kick
        seek=blocked|trouble
        classk=np.clip(1+P.get('CLASS_LOOK',0.0)*(R-100),0.4,2.0)   # a classy horse travelling easily gives its jockey more options
        look=seek&(switchT<=0)&(g.random((N,n))<np.where(kick,skill*P.get('KICK_LOOK',2.0),skill)*classk)
        prefOut=np.where(kind=='straight',g.random((N,n))<0.5,True)
        dirn=np.where(cOut&(prefOut|~cIn),1.0,np.where(cIn,-1.0,0.0))
        start=look&(dirn!=0)
        switchDir=np.where(start,dirn,switchDir); switchT=np.where(start,1.2,switchT-dt)
        # ---- steering
        rank=np.argsort(np.argsort(-x,1),1)
        if kind=='straight':
            tz=np.take_along_axis(gc,grp,1)
            if ng>1: pass
        else:
            # down the chute they hold their lines, drifting in gently; from the join they want the rail;
            # in the home straight only the leaders keep the rail, the rest hold their line and angle out for room
            join=C['bends'][0][0] if C['bends'] else D
            tz=np.where(toGo>join, 0.6+(z-0.6)*P.get('CHUTE_AIM',0.6), 0.6)
            tz=np.where((toGo<605)&(rank>=2), z, tz)
        az=np.clip((tz-z)*0.25,-0.6,0.6)
        near=(np.abs(dx)<AHEAD)&(np.abs(dz)<1.15)&other
        rep=np.where(near,-np.sign(dz+1e-6)*(1.15-np.abs(dz))*2.2,0).sum(2)
        inlane=((dx>0)&(dx<P.get('FAN_LOOK',12.0))&(np.abs(dz)<1.2)&other).any(2)
        fanSide=np.where(kind=='straight',np.where(z>=tz,1.0,-1.0),1.0) if True else 1.0
        clearFan=np.where(fanSide>0,cOut,cIn)
        fanning=inlane&clearFan&(toGo<P.get('FAN_FROM',650))&(rank>=1)&((kind!='straight')|(P.get('FAN_STRAIGHT',1)>0))
        az=np.where(fanning,fanSide*P.get('FAN_RATE',0.45),az)
        vzt=np.where(switchT>0,switchDir*1.0,az+rep)
        free=np.clip((x-2)/38,0,1)
        vz=np.clip(vz+(vzt-vz)*0.5,-1.1*free,1.1*free)
        BL=P.get('BODY_L',2.9); SW=P.get('SIDE_W',1.05)
        sideOut=((np.abs(dx)<BL)&(dz>0)&(dz<SW)&other).any(2); sideIn=((np.abs(dx)<BL)&(dz<0)&(dz>-SW)&(dx>-P.get('CUT_IN',BL))&other).any(2)
        vz=np.where(sideOut&(vz>0),0,vz); vz=np.where(sideIn&(vz<0),0,vz)
        if kind!='straight':
            join=C['bends'][0][0] if C['bends'] else D
            alongside=((np.abs(dx)<P.get('BODY_L',2.9))&(dz<0)&(dz>-1.6)&other).any(2)
            settling=(z>1.6)&alongside&(toGo<=join+P.get('SETTLE_FROM',150))&(toGo>605)&~kick&(x>40)
            fac=np.where(sty>=2,1-P.get('EASE',0.02),1+P.get('PUSH',0.008))
            want=np.where(settling,want*fac,want)
            want=np.where(blocked,np.minimum(want,vfront),want)
        want=np.where((switchT>0)&kick,want*(1-P.get('SWITCH_COST',0.0)),want)
        # ---- move
        acc=np.where(v<10,6.0,1.5*np.clip(1+P.get('CLASS_ACC',0.0)*(R-100),0.5,1.6))   # and quickens out of a check sooner
        v=v+np.clip(want-v,-0.8*dt,acc*dt)
        over=np.maximum(v-np.where(inB,burst,0)-vC,0)
        covered=((dx>0.5)&(dx<P.get('DRAFT_LEN',8.0))&(np.abs(dz)<1.2)&other).any(2)   # shelter: tucked in behind another horse
        E=E-ref*(over/ref)**2*dt*np.where(covered,1-P.get('DRAFT',0.0),1.0)-np.where(keen&(vp<own)&~kick,P['KEEN_BURN'],0)*dt
        kap=np.zeros((N,n))
        for (a,b,ang) in C['bends']:
            kap=np.where((toGo<=a)&(toGo>b),ang/(a-b),kap)
        z=np.clip(z+vz*dt,0.6,29.4)
        for _ in range(3):
            ddx=x[:,None,:]-x[:,:,None]; ddz=z[:,None,:]-z[:,:,None]
            hit=(ddx>=0)&(ddx<BL)&(np.abs(ddz)<W)&other&live[:,:,None]&(np.arange(n)[None,None,:]!=np.arange(n)[None,:,None])
            hit=hit&((ddx>0)|(np.arange(n)[None,None,:]<np.arange(n)[None,:,None]))
            xcap=np.where(hit,x[:,None,:]-BL,np.inf).min(2); vcap=np.where(hit,v[:,None,:],np.inf).min(2)
            x=np.where(live,np.maximum(np.minimum(x,xcap),x-P.get('MAX_CORR',0.3)),x); v=np.where(live&np.isfinite(vcap),np.minimum(v,vcap-np.where(xcap<x+0.01,P.get('CHECK_DV',0.0),0)),v)
        held=blocked|np.isfinite(vcap)
        since=np.where(held,0.0,since+dt)
        lost+=np.where(live&kick&(since<1.5),np.maximum(fw_tick-v,0),0)*dt
        extra+=np.where(live,v*dt*(1-1/(1+kap*(z-0.6))),0)
        x=x+v*dt/(1+kap*(z-0.6))
        lead=x.max(1,keepdims=True); at=np.isnan(rank700)&(D-lead<=700)
        rk=np.argsort(np.argsort(-x,1),1)
        rank700=np.where(at,rk,rank700); E700=np.where(at,E,E700); z700=np.where(at,z,z700)
        ddx=x[:,None,:]-x[:,:,None]; ddz=z[:,None,:]-z[:,:,None]
        ovl+=((np.abs(ddx)<2.6)&(np.abs(ddz)<0.85)&other&live[:,:,None]).sum()/2; ovn+=N      # running wide on a bend: more ground for the same progress along the rail
        t+=dt
        nw=live&(x>=D); fin[nw]=t-(x[nw]-D)/np.maximum(v[nw],1)
        if trace is not None and int(round(t*10))%10==0: frames.append((round(t,1),x[trace].copy(),z[trace].copy(),blocked[trace].copy()))
    sty_ridden=sty.copy(); sty=sty0     # report by racecard style
    o=np.argsort(fin,1); w=o[:,0]; ix=np.arange(N)
    res=dict(N=N,n=n,course=course)
    # traffic: lengths lost per horse
    L=lost/LEN
    res['traffic']=dict(mean_lost=round(float(L.mean()),2), lose1=round(float((L>=1).mean()),3), lose3=round(float((L>=3).mean()),3),
        by_style={s:round(float(L[sty==k].mean()),2) for k,s in enumerate('FPMH')})
    # draw thirds
    th=np.array_split(np.arange(n),3)
    res['draw_win']={nm:round(float(np.isin(w,c).mean()/(len(c)/n)),2) for nm,c in zip(['low','mid','high'],th)}
    res['lost_by_draw']={nm:round(float(L[:,c].mean()),2) for nm,c in zip(['low','mid','high'],th)}
    res['diag']={nm:dict(extra_m=round(float(extra[:,c].mean()),1),rank700=round(float(np.nanmean(rank700[:,c]))+1,1),E700=round(float(np.nanmean(E700[:,c])),1),wide700=round(float(np.nanmean(z700[:,c])),1)) for nm,c in zip(['low','mid','high'],th)}
    res['overlaps_per_race_second']=round(ovl/ovn*10,2)
    lvl=pace_level((sty==0).mean(1),(sty<=1).mean(1))
    res['style_by_pace']={nm:{s_:round(float((sty[lvl==k][np.arange((lvl==k).sum()),w[lvl==k]]==j).mean()/max((sty[lvl==k]==j).mean(),1e-9)),2) for j,s_ in enumerate('FPMH')} for k,nm in enumerate(['slow','even','strong','fast']) if (lvl==k).sum()>20}
    pos=np.argsort(o,1)+1
    res['raw']=dict(Rday=Rday,R0=R0,sty=sty,lvl=lvl,lost=L,pos=pos,shade=shade,keen=keen,form=R-R0)
    res['style_win']={s:round(float((sty[ix,w]==k).mean()/(sty==k).mean()),2) for k,s in enumerate('FPMH')}
    res['groups']=dict(share_split=round(float((grp.max(1)>0).mean()),2))
    marg=(fin[ix,o[:,1]]-fin[ix,w])*PAR/LEN
    res['all']=dict(fav=round(float((np.argmax(R0+g.random((N,n))*0.1,1)==w).mean()),3),margin=round(float(np.median(marg)),2),time=round(float(np.nanmedian(fin[ix,w])),1))
    if trace is not None: res['lost']=L[trace]; res['fin']=fin[trace]; res['hp']=hp[trace]; res['R']=R0[trace]; res['frames']=frames; res['sty']=sty[trace]; res['order']=o[trace]; res['grp']=grp[trace]
    return res
if __name__=='__main__':
    import time
    P=json.load(open('settings-v3.json'))
    for course,n in [('straight',10),('straight',20),('roundmile',10),('roundmile',16)]:
        t0=time.time(); r=run(P,course,N=1200,n=n); print(course,n,round(time.time()-t0,1),'s'); print(' ',{k:v for k,v in r.items() if k not in('N','n','course')})
COURSES=COURSES_OLD   # the two test courses by their old names ('straight', 'roundmile')
