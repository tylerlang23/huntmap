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
    r = await route.fetch(url=LIVE, headers=hdr)
    await route.fulfill(response=r, headers={**r.headers, 'access-control-allow-origin': '*'})
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, service_workers='block', timezone_id='America/Chicago')
        await ctx.route('**/parcels.pmtiles', pm)
        await ctx.add_init_script("localStorage.setItem('huntmap.introDone','true'); localStorage.setItem('huntmap.wps', %s);" % json.dumps(json.dumps(WPS)))
        pg = await ctx.new_page(); logs = []
        pg.on('pageerror', lambda e: logs.append('PAGEERROR ' + str(e)[:300]))
        await pg.goto('http://localhost:8000/index.html#15.6/%s/%s' % (C[1], C[0])); await pg.wait_for_timeout(16000)
        os.makedirs('shots', exist_ok=True)
        await pg.screenshot(path='shots/1-sat.png')
        print('built parcels:', await pg.evaluate("S.built+' '+S.status.parcels"))
        await pg.mouse.click(250, 520); await pg.wait_for_timeout(2500); await pg.screenshot(path='shots/2-tap.png')
        await pg.evaluate("popup && popup.remove()"); await pg.evaluate("map.jumpTo({zoom:17.2})"); await pg.wait_for_timeout(9000); await pg.screenshot(path='shots/3-z17.png')
        await pg.evaluate("S.base='spring'; applyBase(); map.jumpTo({zoom:15.6})"); await pg.wait_for_timeout(14000); await pg.screenshot(path='shots/4-leafoff.png')
        await pg.evaluate("S.base='topo'; applyBase()"); await pg.wait_for_timeout(9000); await pg.screenshot(path='shots/5-topo.png')
        await pg.evaluate("S.base='sat'; applyBase(); editWp(S.wps[0])"); await pg.wait_for_timeout(4000); await pg.screenshot(path='shots/6-edit.png')
        print('\n'.join(logs)); await b.close()
asyncio.run(main())
