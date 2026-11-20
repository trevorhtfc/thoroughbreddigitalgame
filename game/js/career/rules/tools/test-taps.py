# Thousands of random taps on the reference game in a phone-sized browser, to find crashes.   python3 test-taps.py   (needs playwright and Chrome)
import asyncio, random, os
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        for seed in range(3):
            ctx = await b.new_context(viewport={'width':390,'height':844}); pg = await ctx.new_page(); errs=[]
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto('file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), '../reference/index.html'))); await pg.wait_for_timeout(300)
            random.seed(seed); n=0; seasons=0
            # tap things at random, biased towards moving the game on; skip the reset button
            for i in range(2600):
                r = await pg.evaluate("""(u) => { const els=[...document.querySelectorAll('[data-a]')].filter(e=>!e.disabled && e.dataset.a!=='reset' && e.offsetParent!==null);
                    const sheet=document.querySelector('.sheet'); let pool=sheet? els.filter(e=>sheet.contains(e)) : els; if(!pool.length) pool=els; if(!pool.length) return 'none';
                    const fwd=pool.filter(e=>e.classList.contains('gold')); const el = (fwd.length && u[0]<0.3) ? fwd[0] : pool[Math.floor(u[1]*pool.length)];
                    const a=el.dataset.a; el.click(); return a+'|'+(window.TB&&TB.S? TB.S.season+':'+TB.S.phase:''); }""", [random.random(), random.random()])
                n+=1
                if errs: print('seed',seed,'ERROR after',n,'taps, last',r, errs[:2]); break
                if i%40==0: await pg.wait_for_timeout(30)
            print('seed',seed,'taps',n,'state',await pg.evaluate("TB.S? ('season '+TB.S.season+' f'+TB.S.f+' '+TB.S.phase+' horses '+TB.S.horses.length+' cash '+TB.S.cash+' tier '+TB.tier()) : 'setup'"), 'errors', len(errs))
            await ctx.close()
        await b.close()
asyncio.run(main())
