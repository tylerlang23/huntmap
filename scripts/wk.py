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
            d = {"summary":"Day test.","periods":{"morning":{"summary":"Back to bed.","routes":[{"from":"field","to":"cattails","when":"first light","confidence":"high","why":"x","pts":[[600,250],[500,400],[400,550],[300,700]]}]},"midday":{"summary":"Quiet.","routes":[]},"evening":{"summary":"Out to feed.","routes":[{"from":"cattails","to":"field","when":"last hour","confidence":"medium","why":"y","pts":[{"x":300,"y":700},{"x":420,"y":560},{"x":520,"y":400},{"x":620,"y":260}]},{"from":"timber","to":"corner","when":"evening","confidence":"low","why":"z","pts":[[800,700],[700,550],[650,400]]}]}},"trails":[{"kind":"game","size":"main","use":"high","pts":[[100,500],[300,480],[500,460]]},{"kind":"creek","pts":[[0,900],[500,880],[1000,860]]},{"kind":"unsure","size":"faint","use":"low","pts":[[700,100],[750,300]]}],"ambush":[{"x":520,"y":430,"period":"evening","label":"Pinch","winds":["NW"],"why":"x"},{"x":450,"y":480,"period":"morning","label":"AM spot","winds":["S"],"why":"y"}]}
            await route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin':'*'}, body=json.dumps({"usage":{"input_tokens":1,"output_tokens":1},"content":[{"type":"text","text":"```json\n"+json.dumps(d)+"\n```"}]}))
        await pg.route('https://api.anthropic.com/**', fake)
        d = {"summary":"Day test.","periods":{"morning":{"summary":"Back to bed.","routes":[{"from":"field","to":"cattails","when":"first light","confidence":"high","why":"x","pts":[[600,250],[500,400],[400,550],[300,700]]}]},"midday":{"summary":"Quiet.","routes":[]},"evening":{"summary":"Out to feed.","routes":[{"from":"cattails","to":"field","when":"last hour","confidence":"medium","why":"y","pts":[{"x":300,"y":700},{"x":420,"y":560},{"x":520,"y":400},{"x":620,"y":260}]},{"from":"timber","to":"corner","when":"evening","confidence":"low","why":"z","pts":[[800,700],[700,550],[650,400]]}]}},"trails":[{"kind":"game","size":"main","use":"high","pts":[[100,500],[300,480],[500,460]]},{"kind":"creek","pts":[[0,900],[500,880],[1000,860]]},{"kind":"unsure","size":"faint","use":"low","pts":[[700,100],[750,300]]}],"ambush":[{"x":520,"y":430,"period":"evening","label":"Pinch","winds":["NW"],"why":"x"},{"x":450,"y":480,"period":"morning","label":"AM spot","winds":["S"],"why":"y"}]}
        await pg.evaluate("t => { claudeCall = async () => t; }", "```json\n"+json.dumps(d)+"\n```")
        await pg.evaluate("closeSheet(); map.jumpTo({zoom:15})"); await pg.wait_for_timeout(3000)
        await pg.evaluate("openSheet('move')"); await pg.wait_for_timeout(500)
        await pg.evaluate("document.getElementById('mvTr').checked=false")
        await pg.evaluate("t => { claudeCall = async (b) => { window.__imgs = b.messages[0].content.filter(c => c.type === 'image').length; window.__txt = b.messages[0].content.filter(c=>c.type==='text').map(c=>c.text).join(' | ').slice(0,1500); await new Promise(r=>setTimeout(r,4000)); return t; }; }", "```json\n"+json.dumps(d)+"\n```")
        await pg.tap('[data-act=mv-run]'); await pg.wait_for_timeout(5500); await pg.screenshot(path='shots/2.png')
        print('during', await pg.evaluate("[S.base, S.on.enh, document.getElementById('job').innerText.replace(/\\n/g,' | ')]"))
        await pg.wait_for_timeout(15000); await pg.screenshot(path='shots/3.png')
        print('imgs', await pg.evaluate('window.__imgs'), await pg.evaluate('window.__txt')); print('spots', await pg.evaluate("JSON.stringify(MV.res && MV.res.spots.map(s=>[s.id,s.pub]))"), await pg.evaluate("JSON.stringify(MV.res && MV.res.routes.map(r=>[r.n, r.onTrail]))"), await pg.evaluate("$('#mvChip').textContent")); print('after', await pg.evaluate("[MV.res && MV.res.routes.length, MV.res && MV.res.trails.length, MV.res && JSON.stringify(MV.res.skipped), MV.view, map.queryRenderedFeatures({layers:['mv-route']}).length, S.base, S.on.enh, document.getElementById('job').innerText.replace(/\\n/g,' | '), getComputedStyle(document.getElementById('mvChip')).display, !!store.get('mvlast')]"))
        await pg.evaluate("openSheet('move')"); await pg.wait_for_timeout(500); await pg.screenshot(path='shots/5.png'); await pg.tap('[data-act=mv-view][data-k=morn] >> nth=-1'); await pg.wait_for_timeout(600); print('morn', await pg.evaluate("[MV.view, map.queryRenderedFeatures({layers:['mv-route']}).length]")); await pg.screenshot(path='shots/6.png')
        await pg.evaluate("openSheet('move')"); await pg.wait_for_timeout(300); await pg.tap('[data-act=mv-run]'); await pg.wait_for_timeout(600)
        print('again', await pg.evaluate("document.getElementById('banner').innerText.replace(/\\n/g,' | ')")); await pg.screenshot(path='shots/4.png')
        await pg.reload(); await pg.wait_for_timeout(10000)
        print('reload', await pg.evaluate("[!!MV.res, getComputedStyle(document.getElementById('mvChip')).display]"))
        await b.close()
asyncio.run(main())
