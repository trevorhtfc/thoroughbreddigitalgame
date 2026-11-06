import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(300)
        await pg.add_script_tag(path='tools/harness.js')
        for per,mx in [(24,1.8)]:
            for name in ["Card-aware planner","Breeder (10 mares, top sires)"]:
                r=await pg.evaluate('''([per,mx,name])=>{ CLASS_PER=per; CLASS_MAX=mx; CLASS_FROM="race"; const res=HARNESS.run(name,60,7000); const avg=k=>res.reduce((a,x)=>a+(x[k]||0),0)/res.length;
                  const bl=res.reduce((a,x)=>a+x.decks.black,0); return JSON.stringify({prize:Math.round(avg("prize")/1000)+"k",wins:avg("wins").toFixed(2),top3:avg("top3").toFixed(2),runners:avg("runners").toFixed(1),blackRunners:(bl/res.length).toFixed(1)}); }''',[per,mx,name])
                print(per,mx,name,r)
        print(errs); await b.close()
asyncio.run(main())
