import { useEffect, useState } from 'react'
import type { Registro, Resultado } from './types'
import { coberturas as nomesCobertura, nomes, planos, reais } from './format'
import { Icon } from './Icons'
import { passoCliente, paraVoce, valorCliente } from './cliente'

interface Duvida { id: string; pergunta: string; resposta: string[] }

// Pergunta do motor → campo da Casa Gêmea que ela confirma.
const CAMPO_DA_PERGUNTA: Record<string, string> = { obra: 'alerta_obra', ocupacao: 'uso_imovel', declaracao_unica: 'material_parede' }
const lista = (itens: string[]) => itens.length === 1 ? itens[0] : `${itens.slice(0, -1).join(', ')} e ${itens.at(-1)}`

/**
 * Dúvidas frequentes sobre o relatório, respondidas só com o que o motor devolveu para este caso.
 * Sem IA: cada frase vem de um campo do contrato (plano, comparação, faixas, Casa Gêmea, canal).
 */
export function montarDuvidas(data: Resultado, history: Registro[] = []): Duvida[] {
  const rec = data.recomendacao
  const plano = planos[rec.plano]
  if (!plano) return []
  const comparacao = data.comparacao_planos ?? []
  const escolhido = comparacao.find(p => p.situacao === 'RECOMENDADO')
  const fire = data.coberturas.find(c => c.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA')
  const casa = data.casa_gemea
  const vazio = casa.uso_imovel.valor === 'TEMPORADA_OU_SEGUNDA_RESIDENCIA'
  const duvidas: Duvida[] = []

  duvidas.push({ id: 'por-que', pergunta: `Por que o ${plano}?`, resposta: escolhido?.motivos.length
    ? ['Porque a sua casa mostrou estes sinais:', ...escolhido.motivos.map(m => `• ${paraVoce(m)}`)]
    : [`Os dados não mostram bens de valor, aluguel ou família que peçam mais coberturas. O ${plano} protege o essencial da casa.`] })

  for (const outro of comparacao.filter(p => p.situacao !== 'RECOMENDADO')) {
    const itens = outro.diferenca.map(d => nomesCobertura[d.cobertura]?.toLowerCase() ?? d.nome)
    const resumo = outro.situacao === 'ABAIXO' ? `O ${outro.nome} deixaria sem proteção ${lista(itens)}.` : `O ${outro.nome} acrescentaria ${lista(itens)}.`
    // Um degrau: a explicação do motor já diz tudo. Dois degraus: o resumo junta o que muda nos dois.
    duvidas.push({ id: `nao-${outro.plano}`, pergunta: `Por que não o ${outro.nome}?`,
      resposta: outro.motivos.length === 1 ? [paraVoce(outro.motivos[0])] : [resumo, ...outro.motivos.slice(-1).map(paraVoce)] })
  }

  if (fire) duvidas.push({ id: 'preco', pergunta: `Os ${reais(fire.faixa_valor_min)} a ${reais(fire.faixa_valor_max)} são o preço do seguro?`, resposta: [
    'Não. É o valor máximo que o seguro pagaria se a casa precisasse ser reconstruída depois de um incêndio, somando a construção e os seus bens.',
    'O seguro paga até o limite contratado. Por isso o limite não deve ficar abaixo do que custaria reconstruir, nem muito acima, para você não pagar por uma proteção que não usaria.',
    'O preço depende da cotação e não aparece neste protótipo.',
  ] })

  // Dados que continuam estimados e que o motor decidiu não perguntar.
  const pendentes = new Set(data.proximas_perguntas.map(p => CAMPO_DA_PERGUNTA[p.id] ?? p.id))
  const respondidos = new Set(data.respostas_aplicadas.map(c => CAMPO_DA_PERGUNTA[c] ?? c))
  const naoPerguntados = (['area_m2', 'conteudo', 'padrao_construtivo', 'tipo_imovel'] as const)
    .filter(c => !['OBSERVADO', 'CONFIRMADO'].includes(casa[c].selo) && !pendentes.has(c) && !respondidos.has(c))
  if (naoPerguntados.length) duvidas.push({ id: 'nao-perguntados', pergunta: `Por que vocês não perguntaram ${lista(naoPerguntados.map(c => nomes[c].toLowerCase()))}?`, resposta: [
    'Porque nenhuma resposta mudaria o seu plano. Preferimos fazer menos perguntas e só as que mudam o resultado.',
    ...naoPerguntados.map(c => `• ${nomes[c]}: ${valorCliente(c, casa[c], casa).replace(/^Cerca de/, 'cerca de')} (estimativa).`),
    'A faixa de valores já leva em conta essa incerteza. Se quiser deixar o valor mais exato, você pode informar esses dados na contratação.',
  ] })

  if (history.some(h => h.valor === 'NAO_SEI')) duvidas.push({ id: 'nao-sei', pergunta: 'Respondi "Não sei". Tem problema?', resposta: [
    'Não. Seguimos com a nossa estimativa, e a faixa de valores fica um pouco mais larga para cobrir a dúvida.',
  ] })

  duvidas.push({ id: 'fora', pergunta: 'O que não está coberto?', resposta: [
    '• Celulares, joias, relógios e dinheiro.',
    '• Bens de outras pessoas que estejam na casa' + (casa.vinculo.valor === 'PROPRIETARIO_LOCADOR' ? ', como os do seu inquilino.' : '.'),
    '• Danos durante obra, reforma ou reconstrução, e problemas de desgaste ou falta de manutenção.',
    vazio ? '• Roubo e aluguel quando a casa fica vazia por muito tempo. Para isso existe a extensão de desocupação temporária.' : '• Roubo quando a casa fica vazia por longos períodos.',
  ] })

  if (escolhido?.assistencias.length) duvidas.push({ id: 'servicos', pergunta: 'Quais serviços vêm com o plano?', resposta: [
    `O ${plano} inclui: ${lista(escolhido.assistencias)}.`,
    'São serviços para imprevistos do dia a dia, como chaveiro, eletricista e encanador, e não contam como sinistro.',
  ] })

  duvidas.push({ id: 'errado', pergunta: 'E se alguma informação estiver errada?', resposta: [
    'Confira as suas respostas: você pode editar qualquer uma delas, e a recomendação é refeita na hora.',
    'É importante que as informações estejam certas. Uma declaração errada pode fazer você perder o direito à indenização.',
  ] })

  duvidas.push({ id: 'seguir', pergunta: 'Como eu sigo daqui?', resposta: [
    `Próximo passo: ${passoCliente(data).toLowerCase()}.`,
    data.canal.semaforo === 'VERMELHO' ? 'Um especialista recebe as suas respostas e os motivos da recomendação, para você não precisar repetir nada.'
      : data.canal.semaforo === 'AMARELO' ? 'Responda as perguntas que faltam e a recomendação fica confirmada.'
      : 'A recomendação está confirmada. Neste protótipo nenhuma contratação é feita.',
  ] })
  return duvidas
}

/** Bloco de conversa: o cliente toca numa dúvida e a resposta aparece logo abaixo. */
export function Duvidas({ data, history }: { data: Resultado; history?: Registro[] }) {
  const duvidas = montarDuvidas(data, history)
  const [abertas, setAbertas] = useState<string[]>([])
  const [especialista, setEspecialista] = useState(false)
  useEffect(() => { setAbertas([]); setEspecialista(false) }, [data.imovel_id])
  if (!duvidas.length) return null
  const restantes = duvidas.filter(d => !abertas.includes(d.id))
  return <section className="duvidas" aria-labelledby="duvidas-titulo" data-testid="duvidas">
    <div className="duvidas-head"><span className="duvidas-avatar" aria-hidden="true"><Icon name="spark" size={18} /></span><div><h3 id="duvidas-titulo">Dúvidas sobre o seu relatório</h3><p>Toque numa pergunta. As respostas usam só os dados da sua recomendação.</p></div></div>
    <div className="duvidas-log" role="log" aria-live="polite">
      {abertas.map(id => { const d = duvidas.find(x => x.id === id); return d && <div key={id} className="duvida-par">
        <p className="bolha cliente">{d.pergunta}</p>
        <div className="bolha resposta">{d.resposta.map((linha, i) => <p key={i}>{linha}</p>)}</div>
      </div> })}
      {especialista && <div className="duvida-par"><p className="bolha cliente">Quero falar com um especialista.</p><div className="bolha resposta"><p>Simulação: um especialista entraria em contato com as suas respostas e o motivo da recomendação, para você não precisar repetir nada.</p></div></div>}
    </div>
    <div className="duvidas-chips">{restantes.map(d => <button key={d.id} className="chip-duvida" onClick={() => setAbertas(a => [...a, d.id])}>{d.pergunta}</button>)}
      {!especialista && <button className="chip-duvida humano" onClick={() => setEspecialista(true)}><Icon name="person" size={15} />Falar com um especialista</button>}</div>
  </section>
}
