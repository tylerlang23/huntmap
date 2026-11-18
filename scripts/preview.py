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
        import datetime, math
        def om(route):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(route.request.url).query); la = q['latitude'][0].split(','); n = len(la)
            base = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
            times = [(base + datetime.timedelta(hours=k-2)).strftime('%Y-%m-%dT%H:%M') for k in range(80)]
            def one(idx):
                return {"hourly":{"time":times,"wind_speed_10m":[6+8*abs(math.sin(k/9))+idx*.6 for k in range(80)],"wind_direction_10m":[(300+k*3+idx*6)%360 for k in range(80)],"wind_gusts_10m":[14+k%7 for k in range(80)],"temperature_2m":[33]*80,"precipitation_probability":[10]*80,"pressure_msl":[1015]*80,"weather_code":[2]*80,"is_day":[1]*80},
                        "current":{"temperature_2m":33,"apparent_temperature":27,"relative_humidity_2m":70,"weather_code":2,"is_day":1,"wind_speed_10m":9,"wind_direction_10m":300,"wind_gusts_10m":16},
                        "daily":{"time":[t[:10] for t in times[::24]][:4],"sunrise":[t[:10]+'T07:12' for t in times[::24]][:4],"sunset":[t[:10]+'T16:44' for t in times[::24]][:4],"weather_code":[2,3,71,0],"temperature_2m_max":[36,30,28,40],"temperature_2m_min":[22,20,15,25],"precipitation_probability_max":[10,40,60,0],"wind_speed_10m_max":[12,18,20,8],"wind_direction_10m_dominant":[300,320,340,200]}}
            body = [one(k) for k in range(n)] if n > 1 else one(0)
            return route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin':'*'}, body=_j.dumps(body))
        await pg.route('https://api.open-meteo.com/**', om)
        await pg.evaluate("loadWind && loadWind(true)"); await pg.wait_for_timeout(1500)
        await pg.evaluate("map.jumpTo({zoom:13.5})"); await pg.wait_for_timeout(3000)
        await pg.click('#fWind'); await pg.wait_for_timeout(3500); await pg.screenshot(path='shots/1-wind.png')
        await pg.evaluate("map.jumpTo({zoom:9})"); await pg.wait_for_timeout(4000); await pg.screenshot(path='shots/2-wind-far.png')
        await pg.click('#wbPlay'); await pg.wait_for_timeout(5000); await pg.screenshot(path='shots/3-playing.png')
        print('wf', await pg.evaluate("JSON.stringify([WF.src, WF.field && WF.field.n, WF.field && WF.field.nx, WF.t.toFixed(1), WF.parts.length])"))
        print('\n'.join(logs)); print('FAILS', '\n'.join(sorted(set(fails))[:30])); await b.close()
asyncio.run(main())
