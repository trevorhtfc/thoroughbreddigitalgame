import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(300)
        res=[]
        for seed in range(4240,4250):
            pay=await pg.evaluate('''(seed)=>{ newCard(seed); const out=[]; RACES.forEach((race,i)=>{ const C=CARD.races[i], field=fieldFor(i);
              out.push({exp:simRace(i), payload:{type:"race",seed:C.seed,pace:C.pace,going:CARD.going[race.day],race:{name:race.name,course:"Ascot",type:race.grade,f:race.f,prizes:race.prizes},
               field:field.map(h=>({id:h.id,name:h.name,ability:h.ability,edge:h.edge,a:h.a,b:h.b,suits:h.suits,coat:h.coat,stall:h.stall,jockey:h.jockey,trainer:h.trainer,owner:h.owner,mine:!!h.mine}))}}); }); return out; }''', seed)
            res+=pay
        r=await b.new_page(); r.on('pageerror',lambda e:errs.append(str(e)))
        await r.goto('http://localhost:8765/race.html'); await r.wait_for_timeout(500)
        same=0
        for x in res:
            got=await r.evaluate('async (p)=>{ await takeRace(p); return R.finish.map(h=>h.id||h.name); }', x['payload'])
            same+= got==x['exp']
        print(same,'of',len(res),'match', errs[:3]); await b.close()
asyncio.run(main())
