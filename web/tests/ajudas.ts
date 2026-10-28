import type { Page } from '@playwright/test'

/** O plano já aparece no topo (desktop) ou no resumo fixo (celular); o relatório completo vem no fim. */
export async function revelar(page: Page) {
  await page.getByTestId('plano-atual').or(page.getByTestId('resumo-movel')).first().waitFor()
}

/** O campo numérico fica atrás de um link discreto. */
export async function abrirValor(page: Page) {
  await page.getByRole('button', { name: /^Informar (a área|o valor)$/ }).click()
}
