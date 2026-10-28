import type { Campo, Casa } from './types'

export const reais = (n: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(n)
export const numero = (n: number) => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(n)
export const texto = (s: unknown) => String(s ?? '').replace(/[\u2013\u2014]/g, ', ')
export const json = (s: unknown) => JSON.stringify(s, null, 2).replace(/\u2014/g, '\\u2014')
export const planos: Record<string, string> = { ESSENCIAL: 'Essencial', PRATICO: 'Prático', TOTAL: 'Total' }
export const confianca: Record<string, string> = { ALTA: 'Alta', MEDIA: 'Média', BAIXA: 'Baixa' }
export const nomes: Record<string, string> = {
  tipo_imovel: 'Tipo de imóvel', vinculo: 'Sua relação com o imóvel', uso_imovel: 'Uso do imóvel',
  area_m2: 'Área construída', padrao_construtivo: 'Acabamento', material_parede: 'Paredes externas',
  alerta_obra: 'Obras e reformas', conteudo: 'Bens no imóvel',
}
export const valores: Record<string, string> = {
  CASA: 'Casa', APARTAMENTO: 'Apartamento', CASA_EM_CONDOMINIO: 'Casa em condomínio',
  PROPRIETARIO_QUITADO: 'Próprio, sem financiamento', PROPRIETARIO_FINANCIADO: 'Próprio, financiado',
  PROPRIETARIO_LOCADOR: 'Alugado a outra pessoa', INQUILINO: 'Moro de aluguel',
  MORADIA_HABITUAL: 'Moradia habitual', TEMPORADA_OU_SEGUNDA_RESIDENCIA: 'Segunda residência',
  ALUGADO_A_TERCEIROS: 'Alugado a terceiros', ECONOMICO: 'Simples', NORMAL: 'Médio', SUPERIOR: 'Alto padrão',
  ALVENARIA: 'Alvenaria', NAO_INFORMADO: 'Não informado', SEM_SINAL: 'Sem sinal de obra',
  REFORMA_LEVE: 'Reforma leve', REFORMA_MODERADA: 'Possível reforma', POSSIVEL_OBRA_RELEVANTE: 'Possível obra relevante',
  OBRA_ESTRUTURAL: 'Obra estrutural', INDEFINIDO: 'A confirmar',
}
export const coberturas: Record<string, string> = {
  INCENDIO_RAIO_EXPLOSAO_FUMACA: 'Incêndio, raio, explosão e fumaça', DANOS_POR_AGUA: 'Danos por água',
  VENDAVAL_GRANIZO: 'Vendaval e granizo', IMPACTO_VEICULOS_TERRESTRES: 'Impacto de veículos',
  QUEDA_AERONAVE: 'Queda de aeronave', DANOS_ELETRICOS: 'Danos elétricos',
  ROUBO_FURTO_ARROMBAMENTO: 'Roubo e furto com arrombamento', QUEBRA_DE_VIDROS: 'Quebra de vidros',
  RESPONSABILIDADE_CIVIL_FAMILIAR: 'Responsabilidade civil familiar', PERDA_PAGAMENTO_ALUGUEL: 'Perda ou pagamento de aluguel',
  DESPESAS_EMERGENCIAIS: 'Despesas emergenciais',
}
export function valorCampo(chave: string, campo: Campo, casa: Casa) {
  if (chave === 'area_m2') return casa.area_faixa_m2[0] === casa.area_faixa_m2[1] ? `${numero(casa.area_faixa_m2[0])} m²` : `${numero(casa.area_faixa_m2[0])} a ${numero(casa.area_faixa_m2[1])} m²`
  if (chave === 'conteudo') return casa.conteudo_faixa[0] === casa.conteudo_faixa[1] ? reais(casa.conteudo_faixa[0]) : `${reais(casa.conteudo_faixa[0])} a ${reais(casa.conteudo_faixa[1])}`
  return valores[String(campo.valor)] ?? texto(campo.valor)
}

export function campoPergunta(id: string, casa: Casa): Campo | undefined {
  const chave = id === 'obra' ? 'alerta_obra' : id === 'ocupacao' ? 'uso_imovel' : id
  const campo = casa[chave as keyof Casa]
  return campo && !Array.isArray(campo) ? campo : undefined
}
