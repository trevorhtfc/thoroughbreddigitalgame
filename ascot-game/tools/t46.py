import asyncio
from playwright.async_api import async_playwright
SETUP=open('tools/t41.py').read().split("SETUP='''")[1].split("'''")[0]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); errs=[]
        for w in [1440,1280,1024,900,800,700,641,640,430,390,360,320]:
            pg=await b.new_page(viewport={'width':w,'height':900},device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
            await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(300); await pg.evaluate(SETUP)
            # give some horses long names and several targets
            r=await pg.evaluate('''(()=>{ S.stable.forEach((h,i)=>{ if(i%3==0) h.name="Thunderous Applause Magnificent"; });
              S.targets={}; RACES.forEach((r,i)=>{ const h=S.stable.find(h=>!fitFor(h,r).no && i%2==0); if(h) S.targets[r.id]=h.id; }); save(); render();
              const c=[...document.querySelectorAll(".hc2")]; const H=c.map(x=>x.offsetHeight), I=c.map(x=>x.querySelector(".hc2-id").offsetHeight), P=c.map(x=>x.querySelector(".hc2-pic").offsetHeight);
              const over=c.filter(x=>[...x.querySelectorAll("*")].some(e=>e.getBoundingClientRect().right>x.getBoundingClientRect().right+1)).length;
              return JSON.stringify({n:c.length,cardH:[...new Set(H)],idH:[...new Set(I)],picH:[...new Set(P)],over,pageOver:document.documentElement.scrollWidth>innerWidth})})()''')
            print(w,r)
            if w in (1280,700,390,320):
                el=await pg.query_selector('.hc2 >> nth=0'); await el.scroll_into_view_if_needed(); await el.screenshot(path=f'tools/c5_{w}.png')
            await pg.close()
        print(errs); await b.close()
asyncio.run(main())
