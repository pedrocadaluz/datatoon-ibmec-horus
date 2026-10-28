import { revelar, abrirValor } from './ajudas'
import { test, expect, devices } from '@playwright/test'

for (const device of ['Pixel 7', 'iPhone 14'] as const) {
  const { defaultBrowserType: _browser, ...profile } = devices[device]
  test.describe(device, () => {
    test.use(profile)
    test('jornada completa no app móvel com recomendação expansível', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto('/')
      await expect(page.getByRole('navigation', { name: 'Canal de atendimento' })).toHaveAttribute('data-mobile', 'true')
      await revelar(page)
      await expect(page.getByTestId('resumo-movel')).toContainText('Total')
      // A visão Cliente não mostra selos na pergunta; eles ficam no painel da Casa Gêmea, no Gerente e no SAC.
      await expect(page.getByTestId('metadados-pergunta')).toHaveCount(0)
      const unknown = await page.getByTestId('resposta-NAO_SEI').boundingBox()
      const summary = await page.getByTestId('resumo-movel').boundingBox()
      expect(unknown!.y + unknown!.height).toBeLessThanOrEqual(summary!.y)
      await page.screenshot({ path: `evidencias/pwa-${device.replace(' ', '-').toLowerCase()}-inicio.png` })
      await page.getByTestId('resposta-NAO').click()
      await page.getByTestId('resposta-PROPRIETARIO_QUITADO').click()
      await abrirValor(page)
      await page.getByLabel('Valor exato').fill('160')
      await page.getByRole('button', { name: 'Confirmar valor' }).click()
      await page.getByTestId('resposta-SIM').click()
      await expect(page.getByRole('heading', { name: 'Sua recomendação está pronta.' })).toBeVisible()
      await expect(page.getByTestId('resumo-movel')).toContainText('Prático')
      await expect(page.getByTestId('resumo-movel')).toContainText('505.300')
      await page.getByRole('button', { name: 'Expandir recomendação' }).click()
      await expect(page.getByRole('dialog', { name: 'Sua recomendação' })).toBeVisible()
      await expect(page.getByTestId('faixa-incendio')).toContainText('633.500')
      await page.screenshot({ path: `evidencias/pwa-${device.replace(' ', '-').toLowerCase()}-painel.png` })
      await page.getByRole('button', { name: 'Fechar recomendação' }).click()
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false)
    })
  })
}

for (const width of [360, 390, 430, 768, 1280]) {
  test(`todos os canais cabem em ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/')
    await expect(page.getByTestId('caso-atual')).toBeVisible()
    for (const name of ['Cliente', 'Gerente', 'SAC', 'Agente']) {
      await page.getByRole('button', { name, exact: true }).click()
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), name).toBe(false)
      if (width === 390) await page.screenshot({ path: `evidencias/pwa-celular-${name.toLowerCase()}.png` })
    }
    await page.getByRole('button', { name: 'Como usar' }).click()
    await page.getByRole('button', { name: 'Modo apresentação' }).click()
    await expect(page.locator('.presentation-bar')).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false)
    if (width < 768) {
      await expect(page.locator('.mobile-twin')).toHaveAttribute('open', '')
      await page.getByRole('button', { name: 'Próxima etapa' }).click()
      await expect(page.locator('.mobile-twin')).not.toHaveAttribute('open', '')
      await page.getByRole('button', { name: 'Próxima etapa' }).click()
      await expect(page.getByRole('dialog', { name: 'Sua recomendação' })).toBeVisible()
      await page.getByRole('button', { name: 'Fechar recomendação' }).click()
      await page.getByRole('button', { name: 'Sair', exact: true }).click()
      const smallTargets = await page.evaluate(() => [...document.querySelectorAll('button, input, select, summary, a:not(.skip-link)')].filter(node => {
        const box = node.getBoundingClientRect()
        return box.width > 0 && box.height > 0 && (box.height < 44 || (node.tagName !== 'SUMMARY' && box.width < 44))
      }).map(node => ({ tag: node.tagName, text: node.textContent?.trim().slice(0, 40) })))
      expect(smallTargets).toEqual([])
      await page.getByRole('button', { name: 'Aumentar texto' }).click({ clickCount: 3 })
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false)
    }
  })
}
