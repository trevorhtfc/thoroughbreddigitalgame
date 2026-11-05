import asyncio, json
from playwright.async_api import async_playwright
JS='''(([per,mx,W,N,from])=>{ CLASS_PER=per; CLASS_MAX=mx; CLASS_FROM=from; if(W) FIELD_W=W; const out={};
  for(const above of [-10,-5,0,5,10,20]){ let w=0,t3=0,n=0,blk=0,runs=0;
    for(let c=0;c<15;c++){ newCard(1000+c);
      RACES.forEach((race,i)=>{ const C=CARD.races[i]; blk+=C.opp.filter(o=>o.deck==="black").length; runs++;
        for(let k=0;k<N;k++){ const field=C.opp.map(o=>({...o})); field.splice(C.myStall,0,{id:"me",name:"ME",deck:above<0?"red":"black",ability:above<0?"L03":"L04",rating:race.bands[0]+above,mine:true});
          field.forEach((h,j)=>{h.stall=j+1; h.edge=classEdge(h.rating,h.deck,race); h.suits=false;});
          const fin=simulate({name:race.name,f:race.f},C.pace,"Good",field).finish.map(h=>h.id); const p=fin.indexOf("me")+1; n++; if(p===1)w++; if(p&&p<=3)t3++; } }); }
    out["+"+above]=[(100*w/n).toFixed(0)+"%",(100*t3/n).toFixed(0)+"%"]; out.aiBlack=(blk/runs).toFixed(2); }
  return JSON.stringify(out); })'''
OLD={"open":{"Weak":[0.3,2,4,2],"Average":[0.6,3,4,1.5],"Strong":[1.2,4,3,1]},"pattern":{"Weak":[0.5,2,3,3],"Average":[1,2,3,2],"Strong":[2,3,2,1]}}
NEW={"open":{"Weak":[0.15,2,4,2],"Average":[0.3,3,4,1.5],"Strong":[0.6,4,3,1]},"pattern":{"Weak":[0.2,2,3,3],"Average":[0.5,2,3,2],"Strong":[1,3,2,1]}}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(300)
        for lab,per,mx,fr in [("race24x1.8",24,1.8,"race"),("race20x2",20,2,"race")]:
            print(lab, await pg.evaluate(JS+'('+json.dumps([per,mx,OLD,25,fr])+')'))
        print(errs); await b.close()
asyncio.run(main())
