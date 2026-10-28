import { createHash } from 'node:crypto'
import { readdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import type { Plugin } from 'vite'

/** Precache fechado: apenas arquivos estáticos emitidos, jamais respostas HTTP da API. */
export function shellPlugin(): Plugin {
  let output = ''
  return {
    name: 'horus-shell-only', apply: 'build',
    configResolved(config) { output = resolve(config.root, config.build.outDir) },
    async closeBundle() {
      async function files(dir: string, prefix = ''): Promise<string[]> {
        const entries = await readdir(dir, { withFileTypes: true })
        const nested = await Promise.all(entries.map(entry => entry.isDirectory() ? files(resolve(dir, entry.name), `${prefix}${entry.name}/`) : Promise.resolve([`${prefix}${entry.name}`])))
        return nested.flat()
      }
      const assets = (await files(output)).filter(name => name !== 'sw.js' && /\.(?:html|js|css|woff2?|svg|png|ico|webmanifest)$/.test(name)).sort()
      const hash = createHash('sha256')
      for (const file of assets) { hash.update(file); hash.update(await readFile(resolve(output, file))) }
      const urls = ['/', ...assets.map(name => `/${name}`)]
      const worker = `/* Casco estático Horus. Sem cache de runtime ou de dados do imóvel. */
const CACHE = 'horus-shell-${hash.digest('hex').slice(0, 16)}';
const URLS = ${JSON.stringify(urls)};
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
  if (request.method !== 'GET' || url.origin !== self.location.origin || /^\\/api(?:\\/|$)/.test(url.pathname)) return;
  if (request.mode === 'navigate' && ['/', '/index.html', '/celular'].includes(url.pathname)) {
    event.respondWith(fetch(request).catch(() => caches.open(CACHE).then(cache => cache.match('/index.html'))));
    return;
  }
  if (SHELL.has(url.pathname)) {
    event.respondWith(caches.open(CACHE).then(cache => cache.match(url.pathname)).then(cached => cached || fetch(request)));
  }
});
`
      await writeFile(resolve(output, 'sw.js'), worker)
    },
  }
}
