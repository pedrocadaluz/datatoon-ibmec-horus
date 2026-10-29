import { useEffect, useRef, useState } from 'react'
import type { Pergunta, Registro, Resultado, ValorResposta } from './types'
import { campoPergunta, texto } from './format'
import { Icon } from './Icons'
import { Selo } from './House'
import { useMobile } from './useMobile'
import { paraVoce } from './cliente'

interface Props {
  data: Resultado; busy: boolean; history: Registro[]; sac?: boolean; simple?: boolean;
  onAnswer: (q: Pergunta, value: ValorResposta, label: string) => void;
  onUndo: (index: number) => void;
}


export function Question({ data, busy, history, sac, simple, onAnswer, onUndo }: Props) {
  const mobile = useMobile()
  const q = data.proximas_perguntas[0]
  const [exact, setExact] = useState('')
  const [exactOpen, setExactOpen] = useState(false)
  const heading = useRef<HTMLHeadingElement>(null)
  const previous = useRef(q?.id)
  useEffect(() => {
    setExact(''); setExactOpen(false)
    if (previous.current !== q?.id) heading.current?.focus({ preventScroll: true })
    previous.current = q?.id
  }, [q?.id, data.imovel_id])
  const campo = q && campoPergunta(q.id, data.casa_gemea)
  const options = q ? [...q.opcoes.filter(o => o.valor !== 'NAO_SEI'), { valor: 'NAO_SEI', rotulo: 'Não sei' }] : []
  return <section className={`card question-card ${sac ? 'sac-question' : ''}`} aria-busy={busy} id="pergunta-atual">
    <div className="section-heading"><span className="eyebrow">{sac ? 'Roteiro de atendimento' : simple ? 'Só o que muda a sua proteção' : '02 / Só o que faz diferença'}</span>{!simple && <span className="question-number">{history.length} respondida{history.length !== 1 ? 's' : ''}</span>}</div>
    {q ? <div className="question-content" key={q.id}>
      <div className="question-kicker">{!simple && <Icon name={sac ? 'headset' : 'spark'} size={18} />}{!simple && <span>{sac ? 'Leia para o cliente' : `Pergunta ${history.length + 1}`}</span>}{!simple && <span className="impact-label">{q.impacto.includes('elegibilidade') ? 'Elegibilidade' : q.impacto.includes('plano') ? 'Plano' : 'Faixa de cobertura'}</span>}</div>
      <h2 tabIndex={-1} ref={heading}>{texto(q.pergunta)}</h2>
      {campo && !simple && <div className="question-estimate" data-testid="metadados-pergunta"><span>{sac ? 'Leia também a classificação deste dado:' : 'O dado que estamos confirmando:'}</span><Selo campo={campo} /></div>}
      {mobile ? <details className="mobile-question-why"><summary aria-label="Por que perguntamos?">Por que?</summary><p>{simple ? paraVoce(q.motivo) : texto(q.motivo)}</p></details> : <p className="question-why"><b>Por que perguntamos?</b> {simple ? paraVoce(q.motivo) : texto(q.motivo)}</p>}
      {sac && <p className="sac-instruction">Aguarde a resposta e registre uma das opções. Nunca presuma uma confirmação.</p>}
      <fieldset disabled={busy} className="options"><legend className="sr-only">Respostas para a pergunta atual</legend>
        {options.map((op, i) => <button data-testid={`resposta-${op.valor}`} className={`option ${op.valor === 'NAO_SEI' ? 'unknown' : ''}`} key={op.valor} onClick={() => onAnswer(q, op.valor, texto(op.rotulo))}>
          <span className="option-key">{i + 1}</span><span>{texto(op.rotulo)}</span><Icon name="arrow" size={17} />
        </button>)}
      </fieldset>
      {q.aceita_numero && !exactOpen && <button type="button" className="exact-link" disabled={busy} onClick={() => setExactOpen(true)}>{q.id === 'area_m2' ? 'Informar a área' : 'Informar o valor'}</button>}
      {q.aceita_numero && exactOpen && <form className="exact-value" onSubmit={e => { e.preventDefault(); if (exact) onAnswer(q, Number(exact), `${exact} ${q.id === 'area_m2' ? 'm²' : 'reais'}`) }}>
        <label htmlFor="exact-value">{q.id === 'area_m2' ? 'Área em m²' : 'Valor dos bens em reais'}</label>
        <div><input id="exact-value" aria-label="Valor exato" type="number" min={q.id === 'area_m2' ? 1 : 100} step={q.id === 'area_m2' ? 1 : 100} value={exact} onChange={e => setExact(e.target.value)} placeholder={q.id === 'area_m2' ? 'Ex.: 160' : 'Ex.: 25000'} disabled={busy} required autoFocus /><button className="button secondary" disabled={busy || !exact}>Confirmar valor</button></div>
      </form>}
      <p className="small-note">{simple ? 'Tudo bem não saber: seguimos com a nossa estimativa.' : '“Não sei” também vale. Sua recomendação continua com a incerteza sinalizada.'}</p>
    </div> : <div className="question-finish" role="status"><div className={`finish-icon ${data.status === 'INELEGIVEL' ? 'danger' : ''}`}><Icon name={data.status === 'INELEGIVEL' ? 'info' : 'check'} size={25} /></div>
      <h2 tabIndex={-1} ref={heading}>{data.status === 'INELEGIVEL' ? 'Imóvel inelegível neste momento.' : data.status === 'ENCAMINHAR_GERENTE' ? 'Agora, seguimos com o gerente.' : 'Sua recomendação está pronta.'}</h2>
      <p>{data.status === 'INELEGIVEL' ? texto(data.elegibilidade.motivo) : data.status === 'ENCAMINHAR_GERENTE' ? 'Falta só uma confirmação. O gerente recebe os dados e o motivo para ajudar você.' : 'Não precisamos de mais nada. Confira as faixas e o que ainda pode mudar.'}</p>
      <a className="button secondary" href="#recomendacao" onClick={e => { if (matchMedia('(max-width: 767px)').matches) { e.preventDefault(); window.dispatchEvent(new Event('horus-show-recommendation')) } }}>Ver minha recomendação <Icon name="arrow" size={16} /></a>
    </div>}
    <AnswerHistory history={history} busy={busy} onUndo={onUndo} />
  </section>
}

export function AnswerHistory({ history, busy, onUndo, open, semContagem }: { semContagem?: boolean; history: Registro[]; busy: boolean; onUndo: (index: number) => void; open?: boolean }) {
  if (!history.length) return null
  return <details className="answer-history" open={open}><summary>Suas respostas{!semContagem && <> <span>{history.length}</span></>}</summary><ol>{history.map((item, i) => <li key={item.campo}><div><span>{texto(item.pergunta)}</span><strong>{item.rotulo}</strong></div><button disabled={busy} onClick={() => onUndo(i)} aria-label={`Editar resposta ${i + 1}`}>Editar</button></li>)}</ol><p className="small-note">Ao editar, as respostas seguintes serão refeitas na ordem de impacto.</p></details>
}
