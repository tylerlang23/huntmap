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
        await pg.screenshot(path='shots/1-sat.png')
        print('styleLoaded', await pg.evaluate('map.isStyleLoaded()'), await pg.evaluate('typeof mlcontour'))
        await pg.evaluate("S.base='hyb'; applyBase()"); await pg.wait_for_timeout(8000); await pg.screenshot(path='shots/2-hybrid.png')
        print('contours here', await pg.evaluate("map.getLayer('contour-ln') ? map.getLayer('contour-ln').type + ' ' + map.queryRenderedFeatures({layers:['contour-ln']}).length : 'none'"), 'mlcontour', await pg.evaluate("typeof mlcontour"))
        await pg.evaluate("map.jumpTo({center:[-91.99,44.06], zoom:14.6})"); await pg.wait_for_timeout(12000); await pg.screenshot(path='shots/3-hybrid-hills.png')
        print('contours hills', await pg.evaluate("map.getLayer('contour-ln').type=='line' ? map.queryRenderedFeatures({layers:['contour-ln']}).length + ' lbl ' + map.queryRenderedFeatures({layers:['contour-lbl']}).length : 'raster'"))
        await pg.evaluate("S.base='sat'; applyBase(); map.jumpTo({center:[-94.4531,44.80198], zoom:17.6})"); await pg.wait_for_timeout(9000); await pg.screenshot(path='shots/4-sat-z17.png')
        await pg.evaluate("localStorage.setItem('huntmap.hd','true'); localStorage.setItem('huntmap.base','\"sat\"')"); await pg.reload(); await pg.wait_for_timeout(14000); await pg.screenshot(path='shots/5-sat-z17-sharp.png')
        print('hd tileSize', await pg.evaluate("map.getSource('sat').tileSize"))
        await pg.evaluate("openSheet('wind')"); await pg.wait_for_timeout(1500); await pg.screenshot(path='shots/6-weather.png')
        print('\n'.join(logs)); print('FAILS', '\n'.join(sorted(set(fails))[:30])); await b.close()
asyncio.run(main())
