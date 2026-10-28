import { revelar, abrirValor } from './ajudas'
import { test, expect, chromium } from '@playwright/test'
import { writeFile } from 'node:fs/promises'

test.use({ baseURL: 'http://127.0.0.1:4173', serviceWorkers: 'allow' })

test('PWA tem manifesto, ícones e critérios de instalação do Chrome', async ({}, testInfo) => {
  const context = await chromium.launchPersistentContext(testInfo.outputPath('install-profile'), { channel: 'chrome', headless: true, baseURL: 'http://127.0.0.1:4173' })
  try {
  const page = context.pages()[0] ?? await context.newPage()
  await page.goto('/')
  await page.evaluate(() => navigator.serviceWorker.ready)
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller))
  const manifest = await (await page.request.get('/manifest.webmanifest')).json()
  expect(manifest).toMatchObject({ name: 'Horus · Casa Gêmea', short_name: 'Casa Gêmea', start_url: '/', display: 'standalone', theme_color: '#465EFF' })
  expect(manifest.icons.map((icon: { sizes: string }) => icon.sizes)).toEqual(['192x192', '512x512', '512x512'])
  expect(manifest.icons.some((icon: { purpose: string }) => icon.purpose === 'maskable')).toBe(true)
  for (const icon of manifest.icons) expect((await page.request.get(icon.src)).status()).toBe(200)
  const cdp = await page.context().newCDPSession(page)
  const app = await cdp.send('Page.getAppManifest')
  expect(app.errors).toEqual([])
  const install = await cdp.send('Page.getInstallabilityErrors')
  expect(install.installabilityErrors).toEqual([])
  await writeFile('evidencias/pwa-instalabilidade.json', JSON.stringify({ data: new Date().toISOString(), url: page.url(), chrome: context.browser()?.version(), contextoSeguro: await page.evaluate(() => isSecureContext), manifesto: manifest, errosManifesto: app.errors, errosInstalacao: install.installabilityErrors, serviceWorkerControlaPagina: await page.evaluate(() => Boolean(navigator.serviceWorker.controller)), telefoneFisicoTestado: false }, null, 2))
  await cdp.detach()
  } finally { await context.close() }
})

test('offline armazena somente casco e nunca revive dados de imóvel', async ({ page, context }) => {
  await page.goto('/')
  await revelar(page)
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
  await page.evaluate(() => navigator.serviceWorker.ready)
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller))
  const api = await page.request.get('/api/imoveis')
  expect(api.headers()['cache-control']).toBe('no-store')
  const cached = await page.evaluate(async () => {
    const urls: string[] = []
    for (const key of await caches.keys()) for (const request of await (await caches.open(key)).keys()) urls.push(new URL(request.url).pathname)
    return urls
  })
  expect(cached).toContain('/index.html')
  expect(cached.some(url => url.endsWith('.js'))).toBe(true)
  expect(cached.some(url => url.endsWith('.woff2'))).toBe(true)
  expect(cached.some(url => url.startsWith('/api'))).toBe(false)
  await context.setOffline(true)
  await page.reload()
  await expect(page.getByRole('alert')).toContainText('Sua Casa Gêmea espera pela conexão.')
  await expect(page.getByTestId('caso-atual')).toHaveCount(0)
  expect(await page.evaluate(() => localStorage.length)).toBe(0)
  expect(await page.evaluate(() => fetch('/api/imoveis').then(() => 'cache indevido').catch(() => 'sem cache'))).toBe('sem cache')
  await page.screenshot({ path: 'evidencias/pwa-offline.png', fullPage: true })
  await context.setOffline(false)
  await page.getByRole('button', { name: 'Tentar novamente' }).click()
  await revelar(page)
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
})

test('QR é local e a página não exige dados de imóvel', async ({ page }) => {
  await page.goto('/celular')
  await expect(page.getByRole('heading', { name: 'Da sua tela para o seu celular.' })).toBeVisible()
  await expect(page.locator('.connect-qr')).toHaveAttribute('src', /^data:image\/png;base64,/)
  await expect(page.getByTestId('caso-atual')).toHaveCount(0)
  await page.screenshot({ path: 'evidencias/pwa-acesso-celular-qr.png', fullPage: true })
})
