/* Casco estático Horus. Sem cache de runtime ou de dados do imóvel. */
const CACHE = 'horus-shell-b89474e814d352d8';
const URLS = ["/","/abertura-celular.png","/assets/MobileConnect-DmvjAeQS.js","/assets/index-BJTZwgLu.js","/assets/index-DJuwZItL.css","/assets/inter-latin-400-normal-C38fXH4l.woff2","/assets/inter-latin-400-normal-CyCys3Eg.woff","/assets/inter-latin-500-normal-BL9OpVg8.woff","/assets/inter-latin-500-normal-Cerq10X2.woff2","/assets/inter-latin-600-normal-CiBQ2DWP.woff","/assets/inter-latin-600-normal-LgqL8muc.woff2","/assets/inter-latin-700-normal-BLAVimhd.woff","/assets/inter-latin-700-normal-Yt3aPRUw.woff2","/assets/inter-latin-800-normal-BYj_oED-.woff2","/assets/inter-latin-800-normal-D1mf63XC.woff","/horus.svg","/icons/apple-touch-icon.png","/icons/horus-icon.svg","/icons/icon-192.png","/icons/icon-512.png","/icons/maskable-512.png","/index.html","/manifest.webmanifest","/marca-bb-seguros-branca.svg","/marca-bb-seguros.svg","/marca-bb.svg"];
const SHELL = new Set(URLS);
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(URLS)));
});
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('horus-shell-') && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || /^\/api(?:\/|$)/.test(url.pathname)) return;
  if (request.mode === 'navigate' && ['/', '/index.html', '/celular'].includes(url.pathname)) {
    event.respondWith(fetch(request).catch(() => caches.open(CACHE).then(cache => cache.match('/index.html'))));
    return;
  }
  if (SHELL.has(url.pathname)) {
    event.respondWith(caches.open(CACHE).then(cache => cache.match(url.pathname)).then(cached => cached || fetch(request)));
  }
});
