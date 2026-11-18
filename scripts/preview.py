import asyncio, json, os, sys
from playwright.async_api import async_playwright
LIVE = 'https://tylerlang23.github.io/huntmap/parcels.pmtiles'
C = (-94.4531, 44.80198)
def off(dx, dy): return [round(C[0] + dx / 78000, 6), round(C[1] + dy / 111000, 6)]
WPS = [
  {'id': 1, 'p': off(-150, 120), 'type': 'stand', 'name': 'North ridge', 'notes': '', 'winds': ['NW', 'W'], 'u': 1},
  {'id': 2, 'p': off(220, -60), 'type': 'blind', 'name': 'Slough blind', 'notes': '', 'winds': ['S'], 'u': 1},
  {'id': 3, 'p': off(60, 260), 'type': 'sign', 'name': 'Scrape line', 'notes': '', 'u': 1},
  {'id': 4, 'p': off(-320, -220), 'type': 'access', 'name': 'Truck', 'notes': '', 'u': 1},
  {'id': 5, 'p': off(330, 200), 'type': 'cam', 'name': 'Cam 2', 'notes': '', 'u': 1},
  {'id': 6, 'p': off(-40, -260), 'type': 'bed', 'name': 'Bedding thicket', 'notes': '', 'u': 1},
  {'id': 7, 'p': off(1200, 2400), 'type': 'other', 'name': 'Far mark', 'notes': '', 'u': 1},
]
async def pm(route):
    req = route.request; hdr = {k: v for k, v in req.headers.items() if k.lower() == 'range'}
    hdr['accept-encoding'] = 'identity'
    try: r = await route.fetch(url=LIVE, headers=hdr)
    except Exception as e: print('pm fetch failed', e); return await route.abort()
    h = {k: v for k, v in r.headers.items() if k.lower() not in ('content-encoding', 'transfer-encoding')}; h['access-control-allow-origin'] = '*'
    await route.fulfill(status=r.status, body=await r.body(), headers=h)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, service_workers='block', timezone_id='America/Chicago')
        await ctx.route('**/parcels.pmtiles', pm)
        await ctx.add_init_script("localStorage.setItem('huntmap.introDone','true'); localStorage.setItem('huntmap.wps', %s);" % json.dumps(json.dumps(WPS)))
        pg = await ctx.new_page(); logs = []; fails = []
        pg.on('requestfailed', lambda r: fails.append(r.url[:90] + ' ' + str(r.failure)))
        pg.on('response', lambda r: fails.append('HTTP %d %s' % (r.status, r.url[:90])) if r.status >= 400 else None)
        pg.on('pageerror', lambda e: logs.append('PAGEERROR ' + str(e)[:300]))
        pg.on('console', lambda m: print('CONSOLE', m.type, m.text[:300]) if m.type in ('warning','error') else None)
        await pg.goto('http://localhost:8000/index.html#15.6/%s/%s' % (C[1], C[0])); await pg.wait_for_timeout(16000)
        os.makedirs('shots', exist_ok=True)
        import json as _j
        cap = {}
        async def fake(route):
            body = _j.loads(route.request.post_data); cap['img'] = body['messages'][0]['content'][0]['source']['data']; cap['txt'] = body['messages'][0]['content'][1]['text']
            spots = {"summary":"Hunt the edge where the grass meets the timber on the west wind.","spots":[{"x":500,"y":500,"type":"stand","name":"Center check","why":"Grid center test.","winds":["W","NW"],"approach":"From the road","when":"evening"},{"x":250,"y":250,"type":"bed","name":"Upper left","why":"Quarter test.","winds":[],"approach":"","when":"all day"},{"x":800,"y":850,"type":"travel","name":"Lower right","why":"Test.","winds":["N"],"approach":"","when":"morning"}]}
            await route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin':'*'}, body=_j.dumps({"content":[{"type":"text","text":"```json\n"+_j.dumps(spots)+"\n```"}]}))
        await pg.route('https://api.anthropic.com/**', fake)
        await pg.evaluate("localStorage.setItem('huntmap.akey', JSON.stringify('sk-ant-test'))"); await pg.reload(); await pg.wait_for_timeout(14000)
        await pg.evaluate("map.jumpTo({zoom:15.2})"); await pg.wait_for_timeout(5000)
        await pg.unroute('https://api.anthropic.com/**')
        async def fake2(route):
            body = _j.loads(route.request.post_data); cap['txt'] = body['messages'][0]['content'][1]['text']
            t = "**Getting in**\n- Park on Wells Ave and walk the field edge west of [1] with a NW wind.\n\n**Points of interest**\n- [2] Thick cattail bedding south of the road.\n- [3] Timber edge funnel.\n\n**Best bet tonight**\n- Sit [1] facing [3].\n\n```json\n" + _j.dumps({"points":[{"n":1,"x":500,"y":500,"label":"Field edge stand","type":"stand"},{"n":2,"x":300,"y":700,"label":"Cattail bedding","type":"bed"},{"n":3,"x":700,"y":300,"label":"Timber funnel","type":"travel"}]}) + "\n```"
            await route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin':'*'}, body=_j.dumps({"usage":{"input_tokens":3000,"output_tokens":900},"content":[{"type":"text","text":t}]}))
        await pg.route('https://api.anthropic.com/**', fake2)
        await pg.evaluate("openSheet('tools')"); await pg.wait_for_timeout(400); await pg.click('[data-act=ask-view]'); await pg.wait_for_timeout(8000)
        await pg.screenshot(path='shots/1-view-ask.png')
        await pg.click('[data-act=ask-here]'); await pg.wait_for_timeout(2500)
        await pg.evaluate("document.getElementById('askOut').scrollIntoView()"); await pg.wait_for_timeout(300); await pg.screenshot(path='shots/2-answer.png')
        print('pts', await pg.evaluate("JSON.stringify(VW.pts)"))
        await pg.click('[data-act=vw-hide]'); await pg.wait_for_timeout(800); await pg.screenshot(path='shots/3-map.png')
        print('PROMPT', cap.get('txt','')[:3000])
        print('\n'.join(logs)); print('FAILS', '\n'.join(sorted(set(fails))[:30])); await b.close()
asyncio.run(main())
