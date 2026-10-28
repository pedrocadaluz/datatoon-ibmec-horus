import { useCallback, useEffect, useRef, useState } from 'react'
import type { Canal, Lista, Pergunta, Registro, Respostas, Resultado, ValorResposta } from './types'
import { buscar, recomendar } from './api'
import { nomes, planos, texto } from './format'
import { Icon } from './Icons'
import { House } from './House'
import { Question } from './Question'
import { MobileRecommendation } from './MobileRecommendation'
import { CasePicker } from './CasePicker'
import { PwaControls } from './PwaControls'
import { useMobile } from './useMobile'
import { Agent, Manager } from './Channels'

interface Session { history: Registro[]; result: Resultado; initial: Resultado }
const canais: { label: Canal; icon: string; note: string }[] = [
  { label: 'Cliente', icon: 'home', note: 'Sua proteção' }, { label: 'Gerente', icon: 'person', note: 'A decisão explicada' },
  { label: 'SAC', icon: 'headset', note: 'Atendimento guiado' }, { label: 'Agente', icon: 'code', note: 'Contrato JSON' },
]
const steps = ['Conheça a Casa Gêmea', 'Responda o que importa', 'Entenda sua proteção']
const answersFrom = (history: Registro[]): Respostas => Object.fromEntries(history.map(h => [h.campo, h.valor]))

export default function App() {
  const mobile = useMobile()
  const [caseOpen, setCaseOpen] = useState(false)
  const [list, setList] = useState<Lista | null>(null)
  const [selected, setSelected] = useState('')
  const [sessions, setSessions] = useState<Record<string, Session>>({})
  const sessionsRef = useRef(sessions)
  sessionsRef.current = sessions
  const [channel, setChannel] = useState<Canal>('Cliente')
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [notice, setNotice] = useState('')
  const [presentation, setPresentation] = useState(false)
  const [step, setStep] = useState(0)
  const [font, setFont] = useState(100)
  const seq = useRef(0)
  const controller = useRef<AbortController | null>(null)
  const data = sessions[selected]?.result
  const history = sessions[selected]?.history ?? []
  const item = list?.imoveis.find(i => i.imovel_id === selected)

  useEffect(() => { document.documentElement.style.fontSize = `${font}%` }, [font])
  useEffect(() => {
    if (selected) return
    const ctrl = new AbortController()
    setBusy(true); setError('')
    buscar<Lista>('/imoveis', { signal: ctrl.signal }).then(result => {
      setList(result)
      setSelected(result.imoveis.find(i => i.imovel_id === 'IMO_CASO_00003_01')?.imovel_id ?? result.imoveis[0]?.imovel_id ?? '')
      if (!result.imoveis.length) { setError('A base de teste está vazia. Confira os dados da API.'); setBusy(false) }
    }).catch(e => { if (!ctrl.signal.aborted) { setError(e.message); setBusy(false) } })
    return () => ctrl.abort()
  }, [retry, selected])

  const load = useCallback(async (id: string, next: Registro[], label?: string) => {
    const current = ++seq.current
    controller.current?.abort()
    const ctrl = new AbortController()
    controller.current = ctrl
    setBusy(true); setError(''); setNotice('')
    try {
      const result = await recomendar(id, answersFrom(next), ctrl.signal)
      if (current !== seq.current) return
      setSessions(prev => ({ ...prev, [id]: { history: next, result, initial: prev[id]?.initial ?? result } }))
      if (label) {
        if ('vibrate' in navigator && !matchMedia('(prefers-reduced-motion: reduce)').matches) navigator.vibrate(12)
        const before = sessionsRef.current[id]?.result.recomendacao.plano
        setNotice(before && before !== result.recomendacao.plano ? `Resposta registrada. O plano passou de ${planos[before]} para ${planos[result.recomendacao.plano] ?? 'sem plano'}.` : 'Resposta registrada. Recomendação e faixas atualizadas pelo motor.')
      }
    } catch (e) {
      if (current === seq.current && !ctrl.signal.aborted) setError(e instanceof Error ? e.message : 'Não conseguimos consultar o motor.')
    } finally { if (current === seq.current) setBusy(false) }
  }, [])

  useEffect(() => {
    if (!selected) return
    void load(selected, sessionsRef.current[selected]?.history ?? [])
    return () => { controller.current?.abort(); seq.current++ }
  }, [selected, retry, load])

  function choose(id: string) {
    controller.current?.abort(); seq.current++
    setNotice(''); setError(''); setStep(0); setBusy(true); setSelected(id)
    if (id === selected) setRetry(n => n + 1)
  }
  function answer(q: Pergunta, value: ValorResposta, label: string) {
    if (busy) return
    void load(selected, [...history, { campo: q.id, pergunta: q.pergunta, valor: value, rotulo: label }], label)
  }

  useEffect(() => {
    function keys(event: KeyboardEvent) {
      if ((event.target as HTMLElement).closest('input, textarea, select, button, a, summary') || event.ctrlKey || event.metaKey || event.altKey) return
      if (event.key.toLowerCase() === 'p') { event.preventDefault(); setPresentation(p => !p); return }
      if (!presentation) return
      if (event.key === 'Escape') setPresentation(false)
      if (event.key === 'ArrowRight') { event.preventDefault(); setStep(s => Math.min(2, s + 1)) }
      if (event.key === 'ArrowLeft') { event.preventDefault(); setStep(s => Math.max(0, s - 1)) }
      const q = data?.proximas_perguntas[0]
      if (q && !busy && /^[1-9]$/.test(event.key) && (channel === 'Cliente' || channel === 'SAC')) {
        const ops = [...q.opcoes.filter(o => o.valor !== 'NAO_SEI'), { valor: 'NAO_SEI', rotulo: 'Não sei' }]
        const op = ops[Number(event.key) - 1]
        if (op) { event.preventDefault(); answer(q, op.valor, texto(op.rotulo)) }
      }
    }
    window.addEventListener('keydown', keys)
    return () => window.removeEventListener('keydown', keys)
  })
  useEffect(() => {
    if (presentation) {
      if (channel !== 'Cliente') { setChannel('Cliente'); return }
      const twin = document.querySelector<HTMLDetailsElement>('.mobile-twin')
      if (mobile && twin) twin.open = step === 0
      if (mobile && step === 2) return
      const el = document.getElementById(['twin-heading', 'pergunta-atual', 'recomendacao'][step])
      el?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'center' })
    }
  }, [presentation, step, mobile, channel])

  async function applyJson(value: string) {
    let parsed
    try { parsed = JSON.parse(value) } catch { throw new Error('JSON inválido. Confira chaves, aspas e vírgulas.') }
    if (!parsed || parsed.versao_contrato !== '1.0' || !list?.imoveis.some(i => i.imovel_id === parsed.imovel_id) || typeof parsed.respostas !== 'object' || !parsed.respostas || Array.isArray(parsed.respostas)) throw new Error('Use versão 1.0, um imóvel do Teste Comum e um objeto de respostas.')
    const id = parsed.imovel_id as string
    const current = ++seq.current
    controller.current?.abort()
    const ctrl = new AbortController()
    controller.current = ctrl
    setBusy(true)
    try {
      const result = await buscar<Resultado>('/recomendar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(parsed), signal: ctrl.signal })
      const initial = sessionsRef.current[id]?.initial ?? await recomendar(id, {}, ctrl.signal)
      if (current !== seq.current) return
      const next = Object.entries(parsed.respostas as Respostas).map(([campo, valor]) => ({ campo, valor, pergunta: nomes[campo] ?? campo, rotulo: String(valor).replace(/_/g, ' ') }))
      setSessions(prev => ({ ...prev, [id]: { history: next, result, initial } }))
      if (id !== selected) setSelected(id)
      setNotice('Contrato executado. As respostas estão disponíveis nos quatro canais.')
    } catch (e) {
      if (!ctrl.signal.aborted && current === seq.current) throw e
    } finally {
      if (current === seq.current) setBusy(false)
    }
  }

  const question = data && <Question sac={channel === 'SAC'} data={data} busy={busy} history={history} onAnswer={answer} onUndo={i => void load(selected, history.slice(0, i), 'Edição')} />
  return <div className={`app ${presentation ? `presentation focus-${step}` : ''}`}>
    <a className="skip-link" href="#conteudo">Pular para o conteúdo</a>
    <header className="topbar"><div className="topbar-inner"><a href="#conteudo" className="brand" aria-label="Horus, Casa Gêmea"><img src="/horus.svg" alt="" width="38" height="38" /><span>horus<span className="brand-divider" /><small>Casa Gêmea</small></span></a><div className="header-actions"><PwaControls /><span className="prototype">Protótipo · Datathon 2026</span><div className="font-controls" role="group" aria-label="Tamanho do texto"><button onClick={() => setFont(f => Math.max(90, f - 10))} aria-label="A− Diminuir texto" disabled={font <= 90}>A−</button><button onClick={() => setFont(f => Math.min(130, f + 10))} aria-label="A+ Aumentar texto" disabled={font >= 130}>A+</button></div><button className={`presentation-toggle ${presentation ? 'active' : ''}`} onClick={() => setPresentation(p => !p)} aria-pressed={presentation} aria-label="Apresentar, Modo apresentação" title="Atalho P"><Icon name="play" size={17} /><span>Apresentar</span><kbd>P</kbd></button></div></div></header>
    <main id="conteudo"><section className="intro"><div><div className="breadcrumb">Proteção inteligente <span>/</span> Seguro residencial</div><h1>Menos perguntas.<br /><span>Mais sentido para sua proteção.</span></h1><p>Seu banco já conhece parte da sua casa. A gente conecta os pontos.</p></div><div className="intro-stamp"><Icon name="shield" size={24} /><span>Cada decisão<br /><b>tem uma explicação.</b></span></div></section>
<CasePicker list={list} selected={selected} busy={busy} hasData={Boolean(data)} mobile={mobile} open={caseOpen} onClose={() => setCaseOpen(false)} onChoose={choose} onReset={() => void load(selected, [], 'Reinício')} />
      <nav className="channel-nav" aria-label="Canal de atendimento" data-mobile={String(mobile)}>{canais.map(c => <button key={c.label} aria-label={c.label} aria-pressed={channel === c.label} className={channel === c.label ? 'active' : ''} onClick={() => setChannel(c.label)}><Icon name={c.icon} size={18} /><span>{c.label}<small>{c.note}</small></span>{channel === c.label && <span className="nav-marker" />}</button>)}{mobile && <button className="mobile-case-button" aria-label="Escolher imóvel" aria-expanded={caseOpen} onClick={() => setCaseOpen(true)}><Icon name="pin" size={18} /><span>Imóvel</span></button>}<span className="one-engine"><span />Um motor. Quatro canais.</span></nav>
      {presentation && <div className="presentation-bar"><span><Icon name="play" size={17} />Apresentação <b>{step + 1} / 3</b></span><strong>{steps[step]}</strong><div><button aria-label="Etapa anterior" disabled={step === 0} onClick={() => setStep(s => s - 1)}>←</button><button aria-label="Próxima etapa" disabled={step === 2} onClick={() => setStep(s => s + 1)}>→</button><button onClick={() => setPresentation(false)}>Sair</button></div>{!mobile && <small>Setas navegam · números respondem · Esc sai</small>}</div>}
      {error && <div className={`error-banner ${!data ? 'offline-card' : ''}`} role="alert"><Icon name="info" /><div><strong>{data ? 'Não foi possível atualizar a Casa Gêmea.' : 'Sua Casa Gêmea espera pela conexão.'}</strong>{!data && <p>O app pode abrir sem internet. Para consultar o imóvel, reconecte à mesma rede do computador da demonstração.</p>}<p>{texto(error)}</p>{data && <span>Os dados abaixo são a última resposta válida. Suas respostas foram preservadas.</span>}</div><button className="button secondary" onClick={() => setRetry(n => n + 1)}>Tentar novamente</button></div>}
      {!data ? !error && <div className="loading-state" role="status"><div className="loading-house"><Icon name="home" size={45} /></div><h2>Conectando os pontos da sua casa...</h2><p>O motor está montando a Casa Gêmea e calculando sua proteção.</p><div className="skeleton" /></div> : <>
        <div className="journey-strip"><div><span className="case-id" data-testid="caso-atual">{data.imovel_id}</span><span className="location-text"><Icon name="pin" size={14} />{item?.municipio}/{item?.uf}</span></div><div className="avoided-counter" data-testid="perguntas-evitadas"><Icon name="spark" size={18} /><strong>{data.jornada.perguntas_evitadas} de {data.jornada.campos_formulario_tradicional} perguntas evitadas</strong><span>{data.jornada.percentual_evitado}% menos formulário</span></div><div className="answered-counter" data-testid="respondidas"><b>{history.length}</b> respondidas</div><div className="mobile-count-progress" role="progressbar" aria-label="Perguntas evitadas" aria-valuemin={0} aria-valuemax={data.jornada.campos_formulario_tradicional} aria-valuenow={data.jornada.perguntas_evitadas}><i style={{ width: `${data.jornada.percentual_evitado}%` }} /></div></div>
        <div className="status-announcement" role="status" aria-live="polite">{busy ? 'Consultando o motor...' : notice}</div>
        <div className="workspace"><div className="workspace-main">{channel === 'Cliente' && <>{mobile && question}{mobile ? <details className="mobile-twin"><summary><Icon name="home" size={19} /><span>Ver sua Casa Gêmea<small>8 dados, com selo e confiança</small></span><b>+</b></summary><House casa={data.casa_gemea} location={`${item?.municipio} / ${item?.uf}`} imovel={selected} /></details> : <House casa={data.casa_gemea} location={`${item?.municipio} / ${item?.uf}`} imovel={selected} />}{!mobile && question}</>}
          {channel === 'Gerente' && <><Manager data={data} />{question}</>}
          {channel === 'SAC' && <><section className="card sac-intro"><div className="sac-symbol"><Icon name="headset" size={30} /></div><div><span className="eyebrow">Atendimento por voz</span><h2>Uma conversa, sem formulário longo.</h2><p>Leia: “Já usamos os dados disponíveis para entender sua casa. Vou confirmar só o que pode mudar sua proteção. Se não souber, tudo bem.”</p><span className="small-note">Imóvel {data.imovel_id} · {item?.municipio}/{item?.uf}</span></div></section>{question}</>}
          {channel === 'Agente' && <Agent data={data} answers={answersFrom(history)} busy={busy} onApply={applyJson} />}
        </div><MobileRecommendation key={selected} data={data} initial={sessions[selected]?.initial ?? null} pending={busy} mobile={mobile} presentationStep={presentation ? step : null} /></div>
      </>}
      <section className="privacy-note"><Icon name="lock" size={19} /><div><strong>Sua casa no centro. Seus dados com propósito.</strong><p>Usamos apenas sinais necessários sobre o imóvel e suas necessidades de cobertura. Cada estimativa pode ser conferida. O canal muda, o motor é o mesmo.</p></div><span>Dados sintéticos<br />Motor determinístico</span></section>
    </main><footer><span><b>horus</b> · Casa Gêmea</span><p>Datathon Proteção Inteligente · BBDW + Ibmec · 2026</p><span>Protótipo demonstrativo. Sem contratação real.</span></footer>
  </div>
}
