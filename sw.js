/* Hunt Map offline support.
   - app shell: index.html network-first, libraries cache-first
   - map tiles: served from the "hm-tiles" cache when a download put them there
   - Esri satellite: falls back to downloaded USGS imagery for the same tile when offline
   - parcels.pmtiles: byte ranges cached as they load, replayed when offline */
const V = 'v8', SHELL = 'hm-shell-' + V, TILES = 'hm-tiles', PM = 'hm-pm';
const LIBS = ['https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js', 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css', 'https://unpkg.com/pmtiles@3/dist/pmtiles.js', 'https://unpkg.com/maplibre-contour@0.1.0/dist/index.min.js'];
const TILE_HOSTS = ['server.arcgisonline.com', 'basemap.nationalmap.gov', 'imageserver.gisdata.mn.gov'];
const EMPTY_PNG = Uint8Array.from(atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='), c => c.charCodeAt(0));

function tileKey(url) {
  try {
    const u = new URL(url), q = u.searchParams, bb = q.get('BBOX') || q.get('bbox');
    if (bb && /GetMap/i.test(q.get('REQUEST') || q.get('request') || '')) {
      const [x0, y0, x1, y1] = bb.split(',').map(Number), C = 20037508.342789244, z = Math.round(Math.log2(2 * C / (x1 - x0)));
      const x = Math.round((x0 + C) / (x1 - x0)), y = Math.round((C - y1) / (y1 - y0)), L = q.get('LAYERS') || q.get('layers') || '';
      let h = 5381; for (let i = 0; i < L.length; i++) h = ((h * 33) ^ L.charCodeAt(i)) >>> 0;
      return 'https://offline.key/wms/' + u.host + u.pathname + '/' + h.toString(36) + '/' + z + '/' + x + '/' + y;
    }
  } catch (e) { }
  return url;
}
const empty = () => new Response(EMPTY_PNG, { headers: { 'Content-Type': 'image/png', 'Access-Control-Allow-Origin': '*', 'X-HM-Empty': '1' } });
const timeout = (p, ms) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms))]);

self.addEventListener('install', e => { e.waitUntil(caches.open(SHELL).then(c => Promise.all(['./', 'manifest.webmanifest', 'icon-192.png', ...LIBS].map(u => c.add(new Request(u, { mode: u.startsWith('http') ? 'cors' : 'same-origin' })).catch(() => { })))).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('hm-shell-') && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim())); });

self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.origin === location.origin && u.pathname.endsWith('/parcels.pmtiles')) { e.respondWith(pmtiles(req)); return; }
  if (req.mode === 'navigate' || (u.origin === location.origin && /\/(index\.html)?$/.test(u.pathname))) { e.respondWith(page(req)); return; }
  if (/^(unpkg\.com|cdn\.jsdelivr\.net|fonts\.openmaptiles\.org|fonts\.googleapis\.com|fonts\.gstatic\.com)$/.test(u.host)) { e.respondWith(cacheFirst(req, SHELL)); return; }
  if (TILE_HOSTS.includes(u.host) && (/\/tile\/\d+\/\d+\/\d+/.test(u.pathname) || /GetMap/i.test(u.search))) { e.respondWith(tile(req)); return; }
});

async function page(req) {
  const c = await caches.open(SHELL);
  try { const r = await timeout(fetch(req), 6000); if (r.ok) c.put('./', r.clone()); return r; }
  catch (e) { return (await c.match('./')) || (await c.match(req)) || new Response('Offline and the app has not been saved yet. Open it once with signal.', { status: 503 }); }
}
async function cacheFirst(req, name) {
  const c = await caches.open(name), hit = await c.match(req); if (hit) return hit;
  try { const r = await fetch(req); if (r.ok) c.put(req, r.clone()); return r; } catch (e) { return new Response('', { status: 504 }); }
}
async function tile(req) {
  const c = await caches.open(TILES), key = tileKey(req.url), hit = await c.match(key); if (hit) return hit;
  const esri = /World_Imagery\/MapServer\/tile\//.test(req.url), ref = /server\.arcgisonline\.com\/.*Reference\//.test(req.url);
  const usgs = esri ? req.url.replace(/^https:\/\/server\.arcgisonline\.com\/ArcGIS\/rest\/services\/World_Imagery\/MapServer/, 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer') : null;
  const fallback = async () => (usgs && (await c.match(usgs))) || empty();
  if (self.navigator && self.navigator.onLine === false) return fallback();
  try { return await timeout(fetch(req), usgs || ref ? 8000 : 20000); } catch (e) { return fallback(); }
}
async function pmtiles(req) {
  const range = req.headers.get('range') || 'all', c = await caches.open(PM), key = new URL('pm/' + encodeURIComponent(range), self.registration.scope).href;
  try {
    const r = await fetch(req);
    if (r.status === 206 || r.status === 200) {
      const etag = r.headers.get('ETag') || '', body = await r.clone().arrayBuffer(), meta = await c.match(new URL('pm/etag', self.registration.scope).href);
      if (meta && (await meta.text()) !== etag) { for (const k of await c.keys()) await c.delete(k); }
      await c.put(new URL('pm/etag', self.registration.scope).href, new Response(etag));
      await c.put(key, new Response(body, { headers: { 'x-status': String(r.status), 'x-etag': etag, 'x-range': r.headers.get('Content-Range') || '', 'x-type': r.headers.get('Content-Type') || 'application/octet-stream' } }));
    }
    return r;
  } catch (e) {
    const hit = await c.match(key); if (!hit) return new Response('', { status: 504 });
    const h = hit.headers, body = await hit.arrayBuffer(), hd = { 'Content-Type': h.get('x-type'), 'Content-Length': String(body.byteLength), 'Accept-Ranges': 'bytes' };
    if (h.get('x-etag')) hd.ETag = h.get('x-etag'); if (h.get('x-range')) hd['Content-Range'] = h.get('x-range');
    return new Response(body, { status: +h.get('x-status') || 206, headers: hd });
  }
}
self.addEventListener('message', e => { if (e.data === 'ping') e.source && e.source.postMessage('pong'); });
