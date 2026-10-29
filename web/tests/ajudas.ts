import type { Page } from '@playwright/test'

/** Entra pela tela inicial como um perfil (Cliente, Gerente, SAC ou Agente), opcionalmente escolhendo o imóvel. */
export async function entrar(page: Page, canal = 'Cliente', imovel?: string, etapa: 'casa' | 'perguntas' = 'perguntas') {
  const trocar = page.getByRole('button', { name: 'Trocar de canal' })
  if (await trocar.isVisible()) await trocar.click()
  if (imovel) await page.getByLabel('Imóvel do Teste Comum').selectOption(imovel)
  await page.getByRole('button', { name: canal, exact: true }).click()
  // No desktop, o cliente começa pela etapa "Sua Casa Gêmea"; os testes seguem direto para as perguntas.
  if (canal === 'Cliente' && etapa === 'perguntas') {
    const comecar = page.getByRole('button', { name: /^Começar as perguntas \(/ })
    await comecar.waitFor({ timeout: 2500 }).catch(() => {})
    if (await comecar.isVisible()) await comecar.click()
  }
}

/** O plano já aparece no topo (desktop) ou no resumo fixo (celular); entra como Cliente se ainda estiver na tela inicial. */
export async function revelar(page: Page) {
  if (await page.getByRole('heading', { name: 'Como você quer entrar?' }).isVisible()) await entrar(page)
  await page.getByTestId('plano-atual').or(page.getByTestId('resumo-movel')).first().waitFor()
}

/** O campo numérico fica atrás de um link discreto. */
export async function abrirValor(page: Page) {
  await page.getByRole('button', { name: /^Informar (a área|o valor)$/ }).click()
}
