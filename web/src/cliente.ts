import type { Campo, Casa, Resultado } from './types'
import { numero, reais, texto, valorCampo } from './format'

/**
 * Linguagem do cliente. O motor fala em selos, confiança, cláusulas e códigos; o cliente lê
 * de onde veio cada dado e o que fazer. Gerente, SAC e Agente continuam com os termos do motor.
 */

/** Tira referências a cláusulas, como "(CG 7.1 w/x)" ou "(CG V1.6, item 4.1 g)". */
export const semClausula = (s: string) => s.replace(/\s*\((?:CG|Condições Gerais)[^)]*\)/g, '')

/** Textos do motor falam "do cliente"; para o cliente, "você". */
export const paraVoce = (s: string) => semClausula(texto(s))
  .replace(/\bO cliente\b/g, 'Você').replace(/\bo cliente\b/g, 'você')
  .replace(/\bse ele quiser\b/g, 'se você quiser').replace(/\bpara este perfil\b/g, 'para você')

/** Valor do dado; estimativas de área e bens ganham "cerca de". */
export function valorCliente(chave: string, campo: Campo, casa: Casa): string {
  const estimado = campo.selo !== 'CONFIRMADO' && campo.selo !== 'OBSERVADO'
  if (chave === 'area_m2' && estimado) return `Cerca de ${numero(casa.area_faixa_m2[0])} a ${numero(casa.area_faixa_m2[1])} m²`
  if (chave === 'conteudo' && estimado) return `Cerca de ${reais(casa.conteudo_faixa[0])} a ${reais(casa.conteudo_faixa[1])}`
  return valorCampo(chave, campo, casa)
}

/** Próximo passo, sem cor do semáforo nem código do canal. */
export const passoCliente = (data: Resultado) => data.canal.semaforo === 'VERMELHO' ? 'Conversar com um especialista'
  : data.canal.semaforo === 'AMARELO' ? 'Confirmar mais algumas informações'
  : data.canal.sugerido === 'ONE_CLICK_BUY' ? 'Contratar pelo app' : 'Concluir com um atendente'

export const elegibilidadeCliente: Record<string, string> = {
  ELEGIVEL: 'Sua casa pode ser segurada', ELEGIVEL_CONDICIONADO: 'Falta uma confirmação para seguir', INELEGIVEL: 'Sua casa não pode ser segurada agora',
}

/** O que cada cobertura protege, no lugar da fórmula de cálculo. */
export const descricaoCobertura: Record<string, string> = {
  INCENDIO_RAIO_EXPLOSAO_FUMACA: 'Reconstrução da casa e reposição dos bens depois de incêndio, raio, explosão ou fumaça.',
  DANOS_POR_AGUA: 'Estragos causados por vazamento, cano rompido ou chuva que entra pelo telhado.',
  VENDAVAL_GRANIZO: 'Danos causados por vento forte, ciclone, tornado ou granizo.',
  IMPACTO_VEICULOS_TERRESTRES: 'Danos quando um veículo bate na casa.',
  QUEDA_AERONAVE: 'Danos causados pela queda de avião ou helicóptero.',
  DANOS_ELETRICOS: 'Aparelhos e instalação elétrica queimados por pico de energia ou curto-circuito.',
  ROUBO_FURTO_ARROMBAMENTO: 'Bens levados em roubo ou em furto com arrombamento. Celulares, joias e dinheiro não entram.',
  QUEBRA_DE_VIDROS: 'Troca de vidros, espelhos e tampos quebrados por acidente.',
  RESPONSABILIDADE_CIVIL_FAMILIAR: 'Danos que você, sua família ou seu pet causarem a outras pessoas.',
  PERDA_PAGAMENTO_ALUGUEL: 'O aluguel que você paga ou deixa de receber se a casa ficar sem condições de uso.',
  DESPESAS_EMERGENCIAIS: 'Hospedagem, alimentação e transporte da família enquanto a casa estiver interditada.',
}

/** "Informação a confirmar" do motor, só quando há algo a confirmar. */
export const ajusteCliente = (aConfirmar: string) => !aConfirmar || aConfirmar.startsWith('nenhuma') ? '' : `Para ajustar este valor, confirme: ${paraVoce(aConfirmar)}.`

export const prioridadeCliente: Record<string, string> = { ALTA: 'Prioridade alta', MEDIA: 'Prioridade média', BAIXA: 'Prioridade baixa' }
