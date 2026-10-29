import type { Lista } from './types'

/**
 * Personas da demonstração, ligadas a imóveis do Teste Comum (dados fictícios).
 * Marina, Rafael e Helena: casos reais escolhidos em docs/11_personas.md.
 * Luiza, Luigi e Júlia: desenhadas só pelas características (docs/16_personas.md) e ligadas
 * ao imóvel mais parecido, escolhido sem olhar o resultado do motor.
 */
export const PERSONAS_SELETOR: { id: string; nome: string; resumo: string }[] = [
  { id: 'IMO_CASO_00008_01', nome: 'Marina', resumo: 'inquilina com família' },
  { id: 'IMO_CASO_00016_01', nome: 'Rafael', resumo: 'casa com muitos eletrônicos' },
  { id: 'IMO_CASO_00059_01', nome: 'Helena', resumo: 'apartamento de temporada' },
  { id: 'IMO_CASO_00036_02', nome: 'Luiza', resumo: 'inquilina que resolve tudo no app' },
  { id: 'IMO_CASO_00098_01', nome: 'Luigi', resumo: 'casa grande, família e pet' },
  { id: 'IMO_CASO_00015_02', nome: 'Júlia', resumo: 'imóvel alugado para outra pessoa' },
]

const rotulo = (i: Lista['imoveis'][number]) => `${i.imovel_id.replace('IMO_', '')} · ${i.municipio}/${i.uf}`

/** Opções do seletor de imóvel: primeiro as personas, depois todos os imóveis. */
export function OpcoesImoveis({ list }: { list: Lista | null }) {
  if (!list) return <option>Carregando imóveis...</option>
  const porId = new Map(list.imoveis.map(i => [i.imovel_id, i]))
  const personas = PERSONAS_SELETOR.filter(p => porId.has(p.id))
  return <>
    {personas.length > 0 && <optgroup label="Personas">
      {personas.map(p => <option key={`persona-${p.id}`} value={p.id}>{p.nome}, {p.resumo} ({rotulo(porId.get(p.id)!)})</option>)}
    </optgroup>}
    <optgroup label="Todos os imóveis">
      {list.imoveis.filter(i => !personas.some(p => p.id === i.imovel_id)).map(i => <option key={i.imovel_id} value={i.imovel_id}>{rotulo(i)}</option>)}
    </optgroup>
  </>
}
