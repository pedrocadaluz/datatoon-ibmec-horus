import { useEffect, useRef } from 'react'
import type { Registro, Resultado } from './types'
import { planos, reais, texto } from './format'
import { Icon } from './Icons'
import { Recommendation } from './Recommendation'
import { AnswerHistory } from './Question'
import { HouseArt, HouseFacts, progressoCasa } from './House'
import { passoCliente } from './cliente'

/** Faixa do topo: a casa que cresce à esquerda e, à direita, só o essencial do plano. */
export function HouseHero({ data, location, pending, showPlan, onOpenReport, imovel }: {
  data: Resultado; location: string; pending: boolean; showPlan: boolean; onOpenReport: () => void; imovel: string;
}) {
  const rec = data.recomendacao
  const fire = data.coberturas.find(c => c.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA')
  const { firmes, total } = progressoCasa(data.casa_gemea, data.respostas_aplicadas)
  const completa = data.status === 'RECOMENDACAO_CONFIRMADA'
  return <section className="card house-hero" aria-labelledby="twin-heading" aria-busy={pending}>
    <div className="hero-art"><HouseArt casa={data.casa_gemea} aplicadas={data.respostas_aplicadas} status={data.status} /></div>
    <div className="hero-side">
      <span className="eyebrow">Sua Casa Gêmea · {location}</span>
      <h2 id="twin-heading">{completa ? 'Sua Casa Gêmea está pronta.' : 'Montamos sua casa com o que o banco já sabe.'}</h2>
      <div className="hero-progress" data-testid="progresso-casa">
        <strong>{firmes} de {total} dados confirmados</strong>
        <div className="house-progress-bar" role="progressbar" aria-label="Dados da Casa Gêmea confirmados" aria-valuemin={0} aria-valuemax={total} aria-valuenow={firmes}><i style={{ width: `${100 * firmes / total}%` }} /></div>
        <span>Partes claras ou cinza ainda são estimativas. Cada resposta completa a casa.</span>
      </div>
      {showPlan && <div className="hero-plan">
        <div><span>Seu plano agora</span><strong data-testid="plano-atual">{planos[rec.plano] ?? 'Sem plano'}</strong></div>
        {fire && <div data-testid="faixa-incendio"><span>Proteção para incêndio</span><strong>{reais(fire.faixa_valor_min)} a {reais(fire.faixa_valor_max)}</strong></div>}
        <div className={`hero-step channel-${data.canal.semaforo.toLowerCase()}`} data-testid="semaforo"><span className="traffic-light" />Próximo passo: <b>{passoCliente(data)}</b></div>
        <button className="button secondary" onClick={onOpenReport}>Ver relatório completo <Icon name="arrow" size={16} /></button>
      </div>}
      <details className="hero-facts"><summary>Ver o que já sabemos da sua casa</summary><HouseFacts casa={data.casa_gemea} imovel={imovel} /></details>
    </div>
  </section>
}

const titulo: Record<string, string> = {
  INELEGIVEL: 'Imóvel inelegível neste momento.',
  ENCAMINHAR_GERENTE: 'Agora, seguimos com o gerente.',
  RECOMENDACAO_CONFIRMADA: 'Sua recomendação está pronta.',
}

/** Relatório que ocupa o lugar das perguntas quando elas acabam (ou quando o cliente pede para ver antes). */
export function ClientReport({ data, initial, pending, history, onBack, onUndo }: {
  data: Resultado; initial: Resultado | null; pending: boolean; history: Registro[];
  onBack?: () => void; onUndo: (index: number) => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => { heading.current?.focus({ preventScroll: true }) }, [data.imovel_id])
  const pendentes = data.status === 'INELEGIVEL' ? 0 : data.proximas_perguntas.length
  const titulo_ = pendentes ? 'Sua recomendação até agora.' : titulo[data.status] ?? 'Sua recomendação está pronta.'
  const texto_ = pendentes ? `Ainda ${pendentes === 1 ? 'falta 1 pergunta' : `faltam ${pendentes} perguntas`} para confirmar. Esta é a recomendação com o que sabemos até agora.`
    : data.status === 'INELEGIVEL' ? texto(data.elegibilidade.motivo)
    : data.status === 'ENCAMINHAR_GERENTE' ? 'As perguntas terminaram, mas ainda há uma pendência. O gerente recebe os dados e o motivo para ajudar você.'
    : 'Confira as faixas e os pontos que ainda dependem de confirmação.'
  return <section className="client-report" aria-labelledby="relatorio-titulo">
    <div className="card report-head" role="status">
      <div className={`finish-icon ${data.status === 'INELEGIVEL' ? 'danger' : ''}`}><Icon name={data.status === 'INELEGIVEL' ? 'info' : 'check'} size={25} /></div>
      <div><span className="eyebrow">Sua proteção</span><h2 id="relatorio-titulo" tabIndex={-1} ref={heading}>{titulo_}</h2><p>{texto_}</p></div>
      {onBack && pendentes > 0 && <button className="button secondary" onClick={onBack}>Voltar às perguntas <Icon name="arrow" size={16} /></button>}
    </div>
    <Recommendation data={data} initial={initial} pending={pending} full history={history} />
    <AnswerHistory history={history} busy={pending} onUndo={onUndo} />
  </section>
}

