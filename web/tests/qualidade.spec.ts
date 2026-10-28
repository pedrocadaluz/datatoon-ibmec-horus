import { revelar, abrirValor } from './ajudas'
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('acessibilidade AA nas quatro visões e no celular', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await revelar(page)
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
  for (const canal of ['Cliente', 'Gerente', 'SAC', 'Agente']) {
    await page.getByRole('button', { name: canal, exact: true }).click()
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
    expect(result.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => n.target) }))).toEqual([])
  }
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Cliente', exact: true }).click()
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(result.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => n.target) }))).toEqual([])
})

test('justificativa, contador e aluguel usam os campos reais do motor', async ({ page, request }) => {
  const result = await (await request.post('/api/recomendar', { data: { imovel_id: 'IMO_CASO_00003_01', respostas: {} } })).json()
  await page.goto('/')
  await expect(page.getByTestId('perguntas-evitadas')).toContainText(`${result.jornada.perguntas_evitadas} de 8 perguntas evitadas`)
  await revelar(page)
  await expect(page.locator('.short-reason')).toContainText(result.recomendacao.justificativa_curta.replace(/[\u2013\u2014]/g, ', '))
  await expect(page.locator('.rental-highlight strong').first()).toContainText('R$')
  await expect(page.locator('.why-plan')).not.toBeVisible()
  await page.locator('.reason-details > summary').click()
  await expect(page.locator('.why-plan')).toBeVisible()
  await page.locator('.all-coverages > summary').click()
  const rc = result.coberturas.find((c: { cobertura: string }) => c.cobertura === 'RESPONSABILIDADE_CIVIL_FAMILIAR')
  await expect(page.locator('.rc-rule')).toHaveText(rc.regra.replace(/[\u2013\u2014]/g, ', '))
  const list = await (await request.get('/api/imoveis')).json()
  for (const item of list.imoveis) {
    const data = await (await request.post('/api/recomendar', { data: { imovel_id: item.imovel_id, respostas: {} } })).json()
    const larga = data.coberturas.find((c: { faixa_valor_min: number; faixa_valor_max: number }) => c.faixa_valor_max / c.faixa_valor_min > 4)
    if (larga) {
      await page.getByLabel('Imóvel do Teste Comum').selectOption(item.imovel_id)
      await expect(page.getByTestId('caso-atual')).toContainText(item.imovel_id)
      await revelar(page)
      await page.locator('.all-coverages > summary').click()
      await page.locator(`[data-cobertura="${larga.cobertura}"] > summary`).click()
      await expect(page.locator('.wide-range').first()).toHaveText('Faixa larga: confirme para estreitar')
      await page.screenshot({ path: 'evidencias/faixa-larga.png', fullPage: true })
      return
    }
  }
  throw new Error('A base não forneceu caso para exercitar o aviso de faixa larga.')
})

test('apresentação por teclado, zoom e erro de rede preservam respostas', async ({ page }) => {
  await page.goto('/')
  await revelar(page)
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
  await page.keyboard.press('p')
  await expect(page.locator('.presentation-bar')).toBeVisible()
  await page.keyboard.press('ArrowRight')
  await expect(page.locator('.presentation-bar')).toContainText('2 / 3')
  await page.keyboard.press('1')
  await expect(page.getByTestId('respondidas')).toContainText('1')
  await page.keyboard.press('Escape')
  await expect(page.locator('.presentation-bar')).not.toBeVisible()
  await page.route('**/api/recomendar', route => route.abort('failed'))
  await page.getByTestId('resposta-PROPRIETARIO_QUITADO').click()
  await expect(page.getByRole('alert')).toContainText('Suas respostas foram preservadas')
  await expect(page.getByRole('alert')).toContainText('Não conseguimos conectar à API')
  await expect(page.getByTestId('respondidas')).toContainText('1')
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
  await page.unroute('**/api/recomendar')
  await page.getByRole('button', { name: 'Tentar novamente' }).click()
  await expect(page.getByRole('alert')).not.toBeVisible()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Aumentar texto' }).click({ clickCount: 3 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false)
})

test('valor exato não acompanha a troca de imóveis e SAC identifica a estimativa', async ({ page }) => {
  await page.goto('/')
  await revelar(page)
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
  await page.getByLabel('Imóvel do Teste Comum').selectOption('IMO_CASO_00001_01')
  await abrirValor(page)
  await expect(page.getByLabel('Valor exato')).toBeVisible()
  await page.getByLabel('Imóvel do Teste Comum').selectOption('IMO_CASO_00007_01')
  await expect(page.getByTestId('caso-atual')).toContainText('IMO_CASO_00007_01')
  await abrirValor(page)
  await page.getByLabel('Valor exato').fill('777')
  await page.getByLabel('Imóvel do Teste Comum').selectOption('IMO_CASO_00001_01')
  await expect(page.getByTestId('caso-atual')).toContainText('IMO_CASO_00001_01')
  await expect(page.getByLabel('Valor exato')).toHaveCount(0)
  await abrirValor(page)
  await expect(page.getByLabel('Valor exato')).toHaveValue('')
  await page.getByRole('button', { name: 'SAC', exact: true }).click()
  await expect(page.getByTestId('metadados-pergunta')).toContainText('Estimado')
  await expect(page.getByTestId('metadados-pergunta')).toContainText('Confiança média')
  await page.screenshot({ path: 'evidencias/sac-estimativa.png', fullPage: true })
})

test('trocar de imóvel durante execução JSON descarta a resposta anterior', async ({ page }) => {
  await page.goto('/')
  await revelar(page)
  await expect(page.getByTestId('plano-atual')).toHaveText('Total')
  await page.getByRole('button', { name: 'Agente', exact: true }).click()
  await page.getByLabel('Entrada JSON').fill(JSON.stringify({ versao_contrato: '1.0', imovel_id: 'IMO_CASO_00002_01', respostas: { obra: 'NAO' } }))
  let release!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  let delivered!: () => void
  const completed = new Promise<void>(resolve => { delivered = resolve })
  await page.route('**/api/recomendar', async route => {
    const body = route.request().postDataJSON()
    if (body.imovel_id === 'IMO_CASO_00002_01' && body.respostas.obra === 'NAO') {
      const response = await route.fetch()
      await gate
      await route.fulfill({ response }).catch(() => {})
      delivered()
    } else await route.continue()
  })
  await page.getByRole('button', { name: 'Executar contrato' }).click()
  await page.getByLabel('Imóvel do Teste Comum').selectOption('IMO_CASO_00001_01')
  await expect(page.getByTestId('caso-atual')).toContainText('IMO_CASO_00001_01')
  release()
  await completed
  await page.waitForLoadState('networkidle')
  await expect(page.getByTestId('caso-atual')).toContainText('IMO_CASO_00001_01')
})
