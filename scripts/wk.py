import asyncio, os
from playwright.async_api import async_playwright
async def main():
    os.makedirs('shots', exist_ok=True)
    async with async_playwright() as p:
        b = await p.webkit.launch()
        ctx = await b.new_context(**p.devices['iPhone 13'])
        await ctx.add_init_script(script='''localStorage.setItem('huntmap.introDone','true'); localStorage.setItem('huntmap.wps', JSON.stringify([{id:1731000000000,p:[-94.4531,44.80198],type:'stand',name:'North',winds:['NW'],photos:['p1'],u:1731000000000},{id:2,p:[-94.452,44.802],type:'sight',name:'',notes:'x'}])); localStorage.setItem('huntmap.hp', JSON.stringify({day:'2026-11-18',sit:'eve'})); localStorage.setItem('huntmap.akey', JSON.stringify('sk-ant-x')); localStorage.setItem('huntmap.wflow','true');''')
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: print('PAGEERROR', str(e)[:500]))
        pg.on('console', lambda m: print('CONSOLE', m.type, m.text[:300]) if m.type in ('error','warning') else None)
        await pg.goto('http://localhost:8000/index.html#14/44.80198/-94.4531'); await pg.wait_for_timeout(12000)
        await pg.screenshot(path='shots/1.png')
        print('defined', await pg.evaluate("typeof openSheet + ' ' + typeof map + ' ' + typeof WF"))
        try:
            await pg.tap('#bar [data-p=tools]', timeout=5000); await pg.wait_for_timeout(800); await pg.screenshot(path='shots/2.png')
            print('sheet', await pg.evaluate("document.querySelector('#sheet').dataset.p"))
        except Exception as e: print('CLICKFAIL', e)
        import json
        async def fake(route):
            d = {"summary":"Test.","routes":[{"n":1,"from":"bedding","to":"field","pts":[{"x":300,"y":700},{"x":400,"y":550},{"x":500,"y":400},{"x":600,"y":250}]}],"trails":[{"pts":[[100,500],[300,480],[500,460]]}],"ambush":[{"x":520,"y":430,"label":"Pinch","winds":["NW"],"why":"x"}]}
            await route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin':'*'}, body=json.dumps({"usage":{"input_tokens":1,"output_tokens":1},"content":[{"type":"text","text":"```json\n"+json.dumps(d)+"\n```"}]}))
        await pg.route('https://api.anthropic.com/**', fake)
        d = {"summary":"Test.","routes":[{"n":1,"from":"bedding","to":"field","pts":[{"x":300,"y":700},{"x":400,"y":550},{"x":500,"y":400},{"x":600,"y":250}]}],"trails":[{"pts":[[100,500],[300,480],[500,460]]}],"ambush":[{"x":520,"y":430,"label":"Pinch","winds":["NW"],"why":"x"}]}
        await pg.evaluate("t => { claudeCall = async () => t; }", "```json\n"+json.dumps(d)+"\n```")
        await pg.evaluate("closeSheet(); map.jumpTo({zoom:15})"); await pg.wait_for_timeout(3000)
        await pg.evaluate("openSheet('move')"); await pg.wait_for_timeout(500)
        await pg.tap('[data-act=mv-run]'); await pg.wait_for_timeout(9000)
        print('mvres', await pg.evaluate("MV.res ? JSON.stringify([MV.res.routes.length, MV.res.trails.length, MV.res.spots.length, !!map.getLayer('mv-route'), map.queryRenderedFeatures({layers:['mv-route','mv-trail']}).length]) : 'none ' + document.getElementById('mvOut').innerText.slice(0,300)"))
        await pg.evaluate("closeSheet()"); await pg.wait_for_timeout(1200); await pg.screenshot(path='shots/2.png')
        await b.close()
asyncio.run(main())
