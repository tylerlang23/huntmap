import asyncio, os
from playwright.async_api import async_playwright
async def main():
    os.makedirs('shots', exist_ok=True)
    async with async_playwright() as p:
        b = await p.webkit.launch()
        ctx = await b.new_context(**p.devices['iPhone 13'])
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: print('PAGEERROR', str(e)[:500]))
        pg.on('console', lambda m: print('CONSOLE', m.type, m.text[:300]) if m.type in ('error','warning') else None)
        await pg.goto('http://localhost:8000/index.html#14/44.80198/-94.4531'); await pg.wait_for_timeout(12000)
        await pg.screenshot(path='shots/1.png')
        print('defined', await pg.evaluate("typeof openSheet + ' ' + typeof map + ' ' + typeof WF"))
        try:
            await pg.click('#bar [data-p=tools]', timeout=5000); await pg.wait_for_timeout(800); await pg.screenshot(path='shots/2.png')
            print('sheet', await pg.evaluate("document.querySelector('#sheet').dataset.p"))
        except Exception as e: print('CLICKFAIL', e)
        await b.close()
asyncio.run(main())
