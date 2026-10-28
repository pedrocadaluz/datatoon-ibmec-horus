import type { Page } from '@playwright/test'

/** A recomendação só aparece ao fim das perguntas ou quando a pessoa pede. */
export async function revelar(page: Page) {
  const botao = page.getByRole('button', { name: 'Ver recomendação até agora' })
  await botao.waitFor({ timeout: 4000 }).catch(() => {})
  if (await botao.count()) await botao.click()
}

/** O campo numérico fica atrás de um link discreto. */
export async function abrirValor(page: Page) {
  await page.getByRole('button', { name: /^Informar (a área|o valor)$/ }).click()
}
