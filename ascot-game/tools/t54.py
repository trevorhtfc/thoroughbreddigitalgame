import asyncio, json
from playwright.async_api import async_playwright
JS='''(()=>{ const band=r=>r<90?"<90":r<100?"90-99":r<110?"100-109":r<120?"110-119":"120+";
 const pileP=st=>st>=4?50000:st===3?25000:10000; const B={};
 const add=(src,r,c)=>{ const k=band(r); B[k]=B[k]||{bred:[],bought:[]}; B[k][src].push(c); };
 for(let c=0;c<60;c++){ newCard(5000+c);
   const sts=STALLIONS.map(s=>stallion(s.name));
   // breeding: every legal pairing, 3 foals each
   for(const m of MARES) for(const s of sts){ if(pairProblem(s,m)) continue; for(let k=0;k<1;k++){ const f=breedPure(s,m); add("bred",Math.max(...f.r),s.fee+pileP(m.stars)); } }
   // auction: the real catalogue and rival buyers; you pay one bid more than the keenest rival
   S.step=2; S.lotN=0; newCatalogue();
   for(const l of S.sale){ const ap=appeal(l), top=Math.max(0,...RIVALS.map(r=>Math.random()<r.keen(l)?l.reserve*ap*r.want(l)*(.7+Math.random()*.9):0));
     let price=l.reserve; if(top>=l.reserve){ while(price<=top) price+=incFor(price); }
     const f=breedPure(stallion(l.sire),byName(l.dam)); add("bought",Math.max(...f.r),price); } }
 const out={}; for(const k of ["<90","90-99","100-109","110-119","120+"]){ const b=B[k]; if(!b) continue; const av=a=>a.length?Math.round(a.reduce((x,y)=>x+y,0)/a.length/1000)+"k":"-";
   const med=a=>{ if(!a.length) return "-"; const s=a.slice().sort((x,y)=>x-y); return Math.round(s[Math.floor(s.length/2)]/1000)+"k"; };
   out[k]={bredAvg:av(b.bred),bredMed:med(b.bred),bredN:b.bred.length,boughtAvg:av(b.bought),boughtMed:med(b.bought),boughtN:b.bought.length}; }
 return JSON.stringify(out,null,1); })()'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(300)
        print(await pg.evaluate(JS)); print(errs); await b.close()
asyncio.run(main())
