import { test, expect } from '@playwright/test'

test('cliente percorre jornada real, muda plano e confirma faixa', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
  await expect(page.getByTestId('semaforo')).toContainText('Gerente')
  await page.screenshot({ path: 'evidencias/cliente-inicial.png', fullPage: true })
  await page.getByTestId('resposta-NAO').click()
  await expect(page.getByTestId('semaforo')).toContainText('Confirmações')
  await page.getByTestId('resposta-PROPRIETARIO_QUITADO').click()
  await expect(page.getByTestId('plano-atual')).toHaveText('Prático')
  await page.getByLabel('Valor exato').fill('160')
  await page.getByRole('button', { name: 'Confirmar valor' }).click()
  await page.getByTestId('resposta-SIM').click()
  await expect(page.getByTestId('faixa-incendio')).toContainText('505.300')
  await expect(page.getByTestId('faixa-incendio')).toContainText('633.500')
  await expect(page.getByRole('heading', { name: 'Sua recomendação está pronta.' })).toBeVisible()
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: 'evidencias/cliente-confirmado.png', fullPage: true })
  await page.getByRole('button', { name: 'Gerente', exact: true }).click()
  await expect(page.getByText('declaração do cliente', { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: 'Agente', exact: true }).click()
  await expect(page.getByLabel('Entrada JSON')).toContainText('160')
})

test('tres imóveis, semáforos, SAC, não sei e reinício', async ({ page, request }) => {
  const list = await (await request.get('/api/imoveis')).json()
  const found: Record<string, string> = {}
  for (const imovel of list.imoveis) {
    const result = await (await request.post('/api/recomendar', { data: { imovel_id: imovel.imovel_id, respostas: {} } })).json()
    found[result.canal.semaforo] ??= imovel.imovel_id
    if (Object.keys(found).length === 3) break
  }
  expect(Object.keys(found).sort()).toEqual(['AMARELO', 'VERDE', 'VERMELHO'])
  await page.goto('/')
  for (const [color, id] of Object.entries(found)) {
    await page.getByLabel('Imóvel do Teste Comum').selectOption(id)
    await expect(page.getByTestId('caso-atual')).toContainText(id)
    const data = await (await request.post('/api/recomendar', { data: { imovel_id: id, respostas: {} } })).json()
    const nomes: Record<string, string> = { TOTAL: 'Total', PRATICO: 'Prático', ESSENCIAL: 'Essencial' }
    await expect(page.getByTestId('plano-atual')).toHaveText(nomes[data.recomendacao.plano])
    await page.getByRole('button', { name: 'SAC', exact: true }).click()
    await page.getByTestId('resposta-NAO_SEI').click()
    await expect(page.getByTestId('respondidas')).toContainText('1')
    await page.getByRole('button', { name: 'Recomeçar' }).click()
    await expect(page.getByTestId('respondidas')).toContainText('0')
    await page.screenshot({ path: `evidencias/caso-${color.toLowerCase()}.png`, fullPage: true })
  }
})

test('obra estrutural encerra e celular não transborda', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByTestId('resposta-OBRA_ESTRUTURAL').click()
  await expect(page.getByTestId('plano-atual')).toHaveText('Sem plano')
  await expect(page.getByText('Imóvel inelegível neste momento.')).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
  expect(overflow).toBe(false)
  await page.screenshot({ path: 'evidencias/celular-inelegivel.png', fullPage: true })
})
