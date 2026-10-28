import { useState } from 'react'
import type { Cobertura, Registro, Resultado } from './types'
import { coberturas, confianca, planos, reais, texto } from './format'
import { Icon } from './Icons'
import { PlanCompare } from './PlanCompare'
import { Duvidas } from './Duvidas'
import { ajusteCliente, descricaoCobertura, elegibilidadeCliente, estabilidadeCliente, paraVoce, passoCliente } from './cliente'

const elegibilidade: Record<string, string> = { ELEGIVEL: 'Elegível', ELEGIVEL_CONDICIONADO: 'Elegível condicionado', INELEGIVEL: 'Inelegível' }
const lights: Record<string, string> = { VERDE: 'Verde', AMARELO: 'Amarelo', VERMELHO: 'Vermelho' }

function Range({ coverage, initial, client }: { coverage: Cobertura; initial?: Cobertura; client?: boolean }) {
  // Eixo fixo por imóvel e cobertura: a confirmação reduz a faixa no mesmo eixo.
  const scale = Math.max((initial?.faixa_valor_max ?? coverage.faixa_valor_max) * 1.3, coverage.faixa_valor_max * 1.05, 1)
  const left = coverage.faixa_valor_min / scale * 100
  const width = Math.max(.4, (coverage.faixa_valor_max - coverage.faixa_valor_min) / scale * 100)
  return <><div className="range-values"><strong>{reais(coverage.faixa_valor_min)}</strong><span>a</span><strong>{reais(coverage.faixa_valor_max)}</strong></div>
    {coverage.faixa_valor_max / Math.max(coverage.faixa_valor_min, 1) > 4 && <p className="wide-range"><Icon name="info" size={14} />Faixa larga: confirme para estreitar</p>}
    <div className="range-track" role="img" aria-label={`Faixa de cobertura de ${reais(coverage.faixa_valor_min)} a ${reais(coverage.faixa_valor_max)}.${client ? '' : ` Confiança ${confianca[coverage.confianca]}.`}`}>
      {initial && <div className="range-initial" style={{ left: `${initial.faixa_valor_min / scale * 100}%`, width: `${(initial.faixa_valor_max - initial.faixa_valor_min) / scale * 100}%` }} />}
      <div className="range-current" style={{ left: `${left}%`, width: `${width}%` }}><i /><i /></div>
    </div><div className="range-scale"><span>R$ 0</span><span>{reais(scale)}</span></div></>
}

export function Recommendation({ data, initial, pending, full, history, duvidas = true }: { data: Resultado; initial: Resultado | null; pending: boolean; full?: boolean; history?: Registro[]; duvidas?: boolean }) {
  const [demo, setDemo] = useState(false)
  if (full) return <ClientRecommendation data={data} initial={initial} pending={pending} history={history} duvidas={duvidas} />
  const rec = data.recomendacao
  const fire = data.coberturas.find(c => c.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA')
  const firstFire = initial?.coberturas.find(c => c.cobertura === fire?.cobertura)
  const canal = data.canal
  const completed = data.status === 'RECOMENDACAO_CONFIRMADA' && canal.semaforo === 'VERDE'
  return <aside className={`recommendation ${pending ? 'updating' : ''}`} id="recomendacao" aria-label="Recomendação" aria-busy={pending}>
    <div className="recommendation-top"><span className="eyebrow">A proteção que faz sentido</span>{pending && <span className="engine-status"><i />Atualizando</span>}</div>
    <div className="eligibility"><Icon name="shield" size={19} /><span>Elegibilidade</span><strong className={`elig-${data.elegibilidade.status.toLowerCase()}`}>{elegibilidade[data.elegibilidade.status]}</strong></div>
    {data.elegibilidade.motivo && <p className="eligibility-reason">{texto(data.elegibilidade.motivo)}</p>}
    <div className="plan-header"><div><span className="mini-label">Plano recomendado</span><h2 data-testid="plano-atual">{planos[rec.plano] ?? 'Sem plano'}</h2></div><span className="plan-icon"><Icon name="shield" size={30} /></span></div>
    {rec.justificativa_curta && <p className="short-reason">{texto(rec.justificativa_curta)}</p>}
    <div className="plan-tabs" aria-label="Comparação de planos">{Object.entries(planos).map(([key, label]) => <span className={rec.plano === key ? 'selected' : ''} key={key}>{rec.plano === key && <Icon name="check" size={13} />}{label}</span>)}</div>
    <div className="plan-confidence"><span>Segurança da recomendação</span><b>{confianca[rec.confianca_geral]}</b></div>
    <div className="confidence-steps" role="img" aria-label={`Segurança da recomendação: ${confianca[rec.confianca_geral]?.toLowerCase()}.`}>{[1, 2, 3].map(n => <i className={n <= ({ ALTA: 3, MEDIA: 2, BAIXA: 1 }[rec.confianca_geral] ?? 0) ? 'filled' : ''} key={n} />)}</div>
    <p className="small-note">{rec.campos_que_podem_mudar_o_plano.length ? `${rec.campos_que_podem_mudar_o_plano.length} dado(s) ainda podem mudar o plano.` : 'Nenhuma resposta que falta mudaria o plano.'}</p>
    {fire && <section className="main-coverage" data-testid="faixa-incendio"><div className="coverage-title"><span><Icon name="home" size={18} />Incêndio e reconstrução</span><b>Confiança {confianca[fire.confianca]?.toLowerCase()}</b></div><Range coverage={fire} initial={firstFire} /><p className="small-note">Valor máximo que o seguro pagaria. Não é o preço do seguro.</p><div className="range-legend"><i />Faixa atual<span /><i />Faixa inicial</div></section>}
    <div className={`channel channel-${canal.semaforo.toLowerCase()}`} data-testid="semaforo"><span className="traffic-light" /><div><span className="mini-label">{lights[canal.semaforo]} · Próximo passo</span><strong>{canal.semaforo === 'VERMELHO' ? 'Gerente' : canal.semaforo === 'AMARELO' ? 'Confirmações rápidas' : canal.sugerido === 'ONE_CLICK_BUY' ? 'One Click Buy' : 'Atendimento assistido'}</strong></div></div>
    {completed && <button className="button primary demo-cta" onClick={() => setDemo(true)}>Simular próximo passo <Icon name="arrow" size={18} /></button>}
    {demo && completed && <p className="demo-message" role="status">Demonstração concluída. Nada foi contratado.</p>}
    {rec.plano === 'TOTAL' && ['INQUILINO', 'PROPRIETARIO_LOCADOR'].includes(String(data.casa_gemea.vinculo.valor)) && <div className="rental-highlight"><span className="eyebrow">O que o Prático deixaria sem proteção</span><p>{texto(rec.por_que_nao_plano_abaixo).split(/(R\$\s?[\d.,]+)/g).map((part, i) => part.startsWith('R$') ? <strong key={i}>{part}</strong> : part)}</p></div>}
    {rec.plano && <details className="reason-details"><summary>Por que este plano <Icon name="info" size={16} /></summary><div className="why-plan"><h3>Motivos</h3>{rec.por_que_este_plano.length ? <ul>{rec.por_que_este_plano.map((reason, i) => <li key={i}><Icon name="check" size={15} /><span>{texto(reason)}</span></li>)}</ul> : <p>Não encontramos sinais para ir além das coberturas do Essencial.</p>}</div><div className="compare"><div><span className="mini-label">Por que não o plano de baixo?</span><p>{texto(rec.por_que_nao_plano_abaixo)}</p></div><div><span className="mini-label">E o plano de cima?</span><p>{texto(rec.por_que_nao_plano_acima)}</p></div><span className="small-note">A comparação olha o que cada plano deixa de cobrir.</span></div></details>}
    {data.coberturas.length > 0 && <details className="all-coverages"><summary>Todas as coberturas <span>{data.coberturas.length}</span></summary>{data.coberturas.map(c => <details className="coverage-detail" key={c.cobertura} data-cobertura={c.cobertura}><summary><span>{coberturas[c.cobertura] ?? texto(c.cobertura)}</span><strong>{reais(c.faixa_valor_min)} a {reais(c.faixa_valor_max)}</strong><small>Estimativa · Confiança {confianca[c.confianca]?.toLowerCase()}</small>{c.cobertura === 'RESPONSABILIDADE_CIVIL_FAMILIAR' && <small className="rc-rule">{texto(c.regra)}</small>}</summary><Range coverage={c} initial={initial?.coberturas.find(i => i.cobertura === c.cobertura)} /><p>{texto(c.justificativa)}</p><p><b>Cálculo:</b> {texto(c.regra)}</p>{c.a_confirmar && <p><b>A confirmar:</b> {texto(c.a_confirmar)}</p>}{c.observacao && <p>{texto(c.observacao)}</p>}</details>)}</details>}
  </aside>
}

/** Relatório para o cliente: o mesmo resultado do motor, sem selos, cores de semáforo, códigos nem fórmulas. */
function ClientRecommendation({ data, initial, pending, history, duvidas }: { data: Resultado; initial: Resultado | null; pending: boolean; history?: Registro[]; duvidas?: boolean }) {
  const [demo, setDemo] = useState(false)
  const rec = data.recomendacao
  const fire = data.coberturas.find(c => c.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA')
  const firstFire = initial?.coberturas.find(c => c.cobertura === fire?.cobertura)
  const completed = data.status === 'RECOMENDACAO_CONFIRMADA' && data.canal.semaforo === 'VERDE'
  return <aside className={`recommendation client ${pending ? 'updating' : ''}`} id="recomendacao" aria-label="Sua recomendação" aria-busy={pending}>
    <div className="eligibility"><Icon name="shield" size={19} /><strong className={`elig-${data.elegibilidade.status.toLowerCase()}`}>{elegibilidadeCliente[data.elegibilidade.status]}</strong></div>
    {data.elegibilidade.motivo && <p className="eligibility-reason">{paraVoce(data.elegibilidade.motivo)}</p>}
    <div className="plan-header"><div><span className="mini-label">Plano recomendado para você</span><h2 data-testid="plano-atual">{planos[rec.plano] ?? 'Sem plano'}</h2></div><span className="plan-icon"><Icon name="shield" size={30} /></span></div>
    {rec.plano && <p className="small-note">{estabilidadeCliente(data)}</p>}
    {fire && <section className="main-coverage" data-testid="faixa-incendio"><div className="coverage-title"><span><Icon name="home" size={18} />Proteção para incêndio e reconstrução</span></div><Range coverage={fire} initial={firstFire} client /><p className="small-note">É o valor máximo que o seguro pagaria. Não é o preço do seguro.</p><div className="range-legend"><i />Agora<span /><i />Antes das suas respostas</div></section>}
    <div className={`channel channel-${data.canal.semaforo.toLowerCase()}`} data-testid="semaforo"><span className="traffic-light" /><div><span className="mini-label">Próximo passo</span><strong>{passoCliente(data)}</strong></div></div>
    {completed && <button className="button primary demo-cta" onClick={() => setDemo(true)}>Simular próximo passo <Icon name="arrow" size={18} /></button>}
    {demo && completed && <p className="demo-message" role="status">Demonstração concluída. Nenhuma contratação foi realizada. Esta interface não envia propostas.</p>}
    {rec.plano && <PlanCompare data={data} />}
    {data.coberturas.length > 0 && <details className="all-coverages"><summary>O que o seu plano cobre <span>{data.coberturas.length}</span></summary>{data.coberturas.map(c => <details className="coverage-detail" key={c.cobertura} data-cobertura={c.cobertura}><summary><span>{coberturas[c.cobertura] ?? texto(c.cobertura)}</span><strong>{reais(c.faixa_valor_min)} a {reais(c.faixa_valor_max)}</strong></summary><Range coverage={c} initial={initial?.coberturas.find(i => i.cobertura === c.cobertura)} client /><p>{descricaoCobertura[c.cobertura] ?? ''}</p>{ajusteCliente(c.a_confirmar) && <p>{ajusteCliente(c.a_confirmar)}</p>}</details>)}</details>}
    {duvidas && <Duvidas data={data} history={history} />}
  </aside>
}
