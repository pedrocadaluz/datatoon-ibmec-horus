import type { ComparacaoPlano, Resultado } from './types'
import { coberturas as nomesCobertura, reais, texto } from './format'
import { Icon } from './Icons'
import { paraVoce, prioridadeCliente } from './cliente'

const ordem = Object.keys(nomesCobertura)

/** Os três planos lado a lado, como na página do produto, e o porquê de cada plano não recomendado. */
export function PlanCompare({ data }: { data: Resultado }) {
  const planos = data.comparacao_planos ?? []
  if (!planos.length) return null
  const recomendado = planos.find(p => p.situacao === 'RECOMENDADO')!
  const outros = planos.filter(p => p.situacao !== 'RECOMENDADO')
  const faixa = Object.fromEntries(data.coberturas.map(c => [c.cobertura, c]))
  return <section className="plan-compare" aria-labelledby="comparacao-titulo" data-testid="comparacao-planos">
    <span className="eyebrow">Comparação dos planos</span>
    <h3 id="comparacao-titulo">Por que o {recomendado.nome} e não os outros</h3>
    <p className="small-note">Comparamos pelo que cada plano cobre e pelo que a sua casa precisa, não pelo preço.</p>

    <div className="plan-cards">{planos.map(p => <div key={p.plano} className={`plan-card ${p.situacao === 'RECOMENDADO' ? 'chosen' : ''}`}>
      <span className="plan-card-tag">{p.situacao === 'RECOMENDADO' ? 'Recomendado para você' : 'Não recomendado'}</span>
      <strong>{p.nome}</strong>
      <span className="plan-card-count">{p.coberturas.length} coberturas + {p.assistencias.length} {p.assistencias.length === 1 ? 'assistência' : 'assistências'}</span>
      <p>{paraVoce(p.resumo)}</p>
    </div>)}</div>

    <details className="pc-more"><summary>Ver as coberturas de cada plano</summary><div className="matrix-wrap"><table className="coverage-matrix">
      <caption className="sr-only">Coberturas incluídas em cada plano</caption>
      <thead><tr><th scope="col">Cobertura</th>{planos.map(p => <th scope="col" key={p.plano} className={p.situacao === 'RECOMENDADO' ? 'chosen' : ''}>{p.nome}</th>)}</tr></thead>
      <tbody>{ordem.map(c => <tr key={c}><th scope="row">{nomesCobertura[c]}{faixa[c] && <small>{reais(faixa[c].faixa_valor_min)} a {reais(faixa[c].faixa_valor_max)}</small>}</th>
        {planos.map(p => <td key={p.plano} className={p.situacao === 'RECOMENDADO' ? 'chosen' : ''}>{p.coberturas.includes(c) ? <><Icon name="check" size={15} /><span className="sr-only">Incluída</span></> : <span aria-label="Não incluída">–</span>}</td>)}</tr>)}</tbody>
    </table></div></details>

    <article className="why-card why-chosen">
      <h4><Icon name="check" size={17} />Por que o {recomendado.nome}</h4>
      {recomendado.motivos.length ? <ul>{recomendado.motivos.map((m, i) => <li key={i}>{paraVoce(m)}</li>)}</ul> : <p>Os dados não mostram bens de valor, aluguel ou família que peçam mais coberturas. O {recomendado.nome} protege o essencial da casa.</p>}
    </article>
    {outros.map(p => <WhyNot key={p.plano} plano={p} />)}
  </section>
}

function WhyNot({ plano }: { plano: ComparacaoPlano }) {
  const abaixo = plano.situacao === 'ABAIXO'
  return <details className={`why-card why-${abaixo ? 'below' : 'above'}`} data-testid={`por-que-nao-${plano.plano}`}>
    <summary><h4><Icon name="info" size={17} />Por que não o {plano.nome}</h4><p className="why-summary">{paraVoce(plano.resumo)}</p></summary>
    {plano.motivos.map((m, i) => <p key={i}>{paraVoce(m)}</p>)}
    {plano.diferenca.length > 0 && <>
      <span className="mini-label">{abaixo ? 'O que ficaria sem proteção' : 'O que ele acrescentaria'}</span>
      <ul className="gap-list">{plano.diferenca.map(d => <li key={d.cobertura}>
        <div><strong>{nomesCobertura[d.cobertura] ?? texto(d.nome)}</strong>{d.necessidade && <span className={`need need-${d.necessidade.toLowerCase()}`}>{prioridadeCliente[d.necessidade]}</span>}</div>
        {d.faixa_valor_min !== null && d.faixa_valor_max !== null && <span className="gap-range">Limite sugerido de {reais(d.faixa_valor_min)} a {reais(d.faixa_valor_max)}</span>}
        {d.sinais.length > 0 && <span className="gap-signal">Na sua casa: {d.sinais.map(paraVoce).join('; ')}</span>}
      </li>)}</ul>
    </>}
  </details>
}
