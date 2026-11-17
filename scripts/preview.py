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
        await pg.goto('http://localhost:8000/index.html#15.6/%s/%s' % (C[1], C[0])); await pg.wait_for_timeout(16000)
        os.makedirs('shots', exist_ok=True)
        await pg.screenshot(path='shots/1-sat.png')
        print('diag', await pg.evaluate('''(() => { const c = map.project(map.getCenter()); const q = l => map.getLayer(l) ? map.queryRenderedFeatures([[0,0],[390,844]], { layers: [l] }).length : 'nolayer';
          const f = map.getLayer('pt-fill') ? map.queryRenderedFeatures([[0,0],[390,844]], { layers: ['pt-fill'] })[0] : null;
          return JSON.stringify({ z: map.getZoom(), pt: q('pt-fill'), ptl: q('pt-line'), lbl: q('pt-lbl'), wma: q('wma-fill'), status: S.status, props: f && f.properties, srcLayers: map.getStyle().layers.filter(x => x.source === 'pt').map(x => x.id + ':' + (x['source-layer'] || '') + ':' + (x.minzoom || '')), wind: !!S.wind }); })()'''))
        print('built parcels:', await pg.evaluate("S.built+' '+S.status.parcels"))
        await pg.mouse.click(250, 520); await pg.wait_for_timeout(2500); await pg.screenshot(path='shots/2-tap.png')
        await pg.evaluate("popup && popup.remove()"); await pg.evaluate("map.jumpTo({zoom:17.2})"); await pg.wait_for_timeout(9000); await pg.screenshot(path='shots/3-z17.png')
        await pg.evaluate("S.base='spring'; applyBase(); map.jumpTo({zoom:15.6})"); await pg.wait_for_timeout(14000); await pg.screenshot(path='shots/4-leafoff.png')
        await pg.evaluate("S.base='topo'; applyBase()"); await pg.wait_for_timeout(9000); await pg.screenshot(path='shots/5-topo.png')
        await pg.evaluate("S.base='sat'; applyBase(); editWp(S.wps[0])"); await pg.wait_for_timeout(4000); await pg.screenshot(path='shots/6-edit.png')
        print('\n'.join(logs)); print('FAILS', '\n'.join(sorted(set(fails))[:30])); await b.close()
asyncio.run(main())
