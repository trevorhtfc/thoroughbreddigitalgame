import asyncio
from playwright.async_api import async_playwright
SETUP='''(()=>{localStorage.clear(); newCard(2024); S.dealt=true; menuOpen=false; document.querySelector("#menu").hidden=true; document.body.style.overflow="";
  const st=STALLIONS.map(s=>stallion(s.name)); MARES.slice(3,13).forEach((m,k)=>{ const ok=st.filter(s=>!pairProblem(s,m)).sort((a,b)=>b.trueStars-a.trueStars); breed(ok[k%3].name,m.name,"bred",0); S.foal.h.age=2+(k%3); S.stable.push(S.foal.h); S.usedMares.push(m.name); S.foal=null; });
  S.targets={[RACES[0].id]:S.stable[0].id}; S.step=1; S.view="plan"; save(); render(); })()'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); errs=[]
        for w,h,n in [(1280,900,'d'),(700,900,'m'),(390,844,'p')]:
            pg=await b.new_page(viewport={'width':w,'height':h}); pg.on('pageerror',lambda e:errs.append(n+': '+str(e)))
            await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(300); await pg.evaluate(SETUP); await pg.wait_for_timeout(150)
            J=pg.evaluate
            print(n, await J('''JSON.stringify({cols:getComputedStyle(document.querySelector(".hk-cols")).gridTemplateColumns.split(" ").length,cardH:document.querySelector(".hc2").offsetHeight,silks:document.querySelectorAll(".hc2 .silk").length,
              ageShown:document.querySelector(".hc2").innerText.match(/\\dYO/g).length,overflow:[...document.querySelectorAll(".hc2")].filter(c=>c.scrollWidth>c.clientWidth+1).length,slotH:document.querySelector(".hc2 .pl-slot").offsetHeight,side:document.documentElement.scrollWidth>innerWidth+1})'''))
            el=await pg.query_selector('.hk-cols'); await el.scroll_into_view_if_needed(); await pg.screenshot(path=f'tools/c3_{n}.png')
            # card popup: page locked, popup scrolls
            await pg.click('.hc2-card >> nth=0'); await pg.wait_for_timeout(800)
            y0=await J('scrollY')
            await pg.mouse.move(w/2, h/2); await pg.mouse.wheel(0, 600); await pg.wait_for_timeout(300)
            print(n,'popup', await J(f'JSON.stringify({{locked:document.body.classList.contains("modal-open"),pageMoved:scrollY!=={y0},wrapScroll:document.querySelector("#devCard").scrollTop,wrapCan:document.querySelector("#devCard").scrollHeight-document.querySelector("#devCard").clientHeight}})'))
            await pg.mouse.click(5, h-5); await pg.wait_for_timeout(200)
            print(n,'closed by backdrop', await J('!document.querySelector("#devCard") && !document.body.classList.contains("modal-open")'))
            await pg.close()
        print(errs); await b.close()
asyncio.run(main())
