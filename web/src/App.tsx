import { useCallback, useEffect, useRef, useState } from 'react'
import type { Canal, Lista, Pergunta, Registro, Respostas, Resultado, ValorResposta } from './types'
import { buscar, recomendar } from './api'
import { nomes, planos, texto } from './format'
import { Icon } from './Icons'
import { House, HouseArt } from './House'
import { Question } from './Question'
import { MobileRecommendation } from './MobileRecommendation'
import { PwaControls } from './PwaControls'
import { useMobile } from './useMobile'
import { Agent } from './Channels'
import { ClientReport, HouseHero } from './Story'
import { ManagerFlow, type PassoGerente } from './Gerente'
import { SacFlow, type PassoSac } from './Sac'
import { ComoUsar } from './Ajuda'
import { Abertura, CANAIS, Entrada } from './Entrada'
import './story.css'
import './app.css'

interface Session { history: Registro[]; result: Resultado; initial: Resultado }
const steps = ['Conheça a Casa Gêmea', 'Responda o que importa', 'Entenda sua proteção']
const answersFrom = (history: Registro[]): Respostas => Object.fromEntries(history.map(h => [h.campo, h.valor]))

export default function App() {
  const mobile = useMobile()
  const [entrou, setEntrou] = useState(false)
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
  const [reportOpen, setReportOpen] = useState(false)
  const [ajuda, setAjuda] = useState(false)
  const [passos, setPassos] = useState<Record<string, PassoGerente>>({})
  const [passosSac, setPassosSac] = useState<Record<string, PassoSac>>({})
  const seq = useRef(0)
  const controller = useRef<AbortController | null>(null)
  const data = sessions[selected]?.result
  const history = sessions[selected]?.history ?? []
  const item = list?.imoveis.find(i => i.imovel_id === selected)
  // Desktop, visão Cliente: perguntas à esquerda, casa que cresce à direita; no fim, o relatório ocupa o lugar das perguntas.
  const story = channel === 'Cliente' && !mobile
  const passo = passos[selected] ?? 1
  const irPara = (p: PassoGerente) => setPassos(prev => ({ ...prev, [selected]: p }))
  const passoSac = passosSac[selected] ?? 1
  const irParaSac = (p: PassoSac) => setPassosSac(prev => ({ ...prev, [selected]: p }))
  const showReport = story && Boolean(data) && (reportOpen || !data?.proximas_perguntas.length || data?.status === 'INELEGIVEL')

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
        setNotice(before && before !== result.recomendacao.plano ? `Resposta registrada. O plano passou de ${planos[before]} para ${planos[result.recomendacao.plano] ?? 'sem plano'}.` : 'Resposta registrada. Atualizamos sua recomendação.')
      }
    } catch (e) {
      if (current === seq.current && !ctrl.signal.aborted) setError(e instanceof Error ? e.message : 'Não conseguimos atualizar agora.')
    } finally { if (current === seq.current) setBusy(false) }
  }, [])

  useEffect(() => {
    if (!selected) return
    void load(selected, sessionsRef.current[selected]?.history ?? [])
    return () => { controller.current?.abort(); seq.current++ }
  }, [selected, retry, load])

  function choose(id: string) {
    controller.current?.abort(); seq.current++
    setNotice(''); setError(''); setStep(0); setBusy(true); setReportOpen(false); setSelected(id)
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
  useEffect(() => { if (presentation && story) setReportOpen(step === 2) }, [presentation, story, step])
  useEffect(() => {
    const acabou = data && !busy && (!data.proximas_perguntas.length || data.status === 'INELEGIVEL')
    if (channel === 'Gerente' && passo === 2 && acabou) irPara(3)
    if (channel === 'SAC' && passoSac === 2 && acabou) irParaSac(3)
  }, [channel, passo, passoSac, data, busy]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (presentation) {
      if (!entrou) setEntrou(true)
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
      setNotice('Contrato executado. As respostas valem nos quatro canais.')
    } catch (e) {
      if (!ctrl.signal.aborted && current === seq.current) throw e
    } finally {
      if (current === seq.current) setBusy(false)
    }
  }

  const undo = (i: number) => { setReportOpen(false); void load(selected, history.slice(0, i), 'Edição') }
  const question = data && <Question sac={channel === 'SAC'} simple={channel === 'Cliente'} house={channel === 'Cliente' && mobile ? <HouseArt casa={data.casa_gemea} aplicadas={data.respostas_aplicadas} status={data.status} /> : undefined} data={data} busy={busy} history={history} onAnswer={answer} onUndo={undo} />
  const house = data && <House casa={data.casa_gemea} location={`${item?.municipio} / ${item?.uf}`} imovel={selected} aplicadas={data.respostas_aplicadas} status={data.status} />
  return <div className={`app ${presentation ? `presentation focus-${step}` : ''}`}>
    <a className="skip-link" href="#conteudo">Pular para o conteúdo</a>
    <header className="topbar"><div className="topbar-inner"><a href="#conteudo" className="brand" aria-label="Horus, Casa Gêmea"><img src="/horus.svg" alt="" width="38" height="38" /><span>horus<span className="brand-divider" /><small>Casa Gêmea</small></span></a><div className="header-actions"><PwaControls /><div className="font-controls" role="group" aria-label="Tamanho do texto"><button onClick={() => setFont(f => Math.max(90, f - 10))} aria-label="A− Diminuir texto" disabled={font <= 90}>A−</button><button onClick={() => setFont(f => Math.min(130, f + 10))} aria-label="A+ Aumentar texto" disabled={font >= 130}>A+</button></div><button className="presentation-toggle" onClick={() => setAjuda(true)} aria-haspopup="dialog" aria-label="Como usar" title="Como usar"><Icon name="info" size={17} /><span>Como usar</span></button></div></div></header>
    <main id="conteudo">{!entrou && <Abertura onCotar={() => { setChannel('Cliente'); setEntrou(true) }} />}
      {!entrou ? <Entrada list={list} selected={selected} busy={busy} onChoose={choose} onEnter={c => { setChannel(c); setEntrou(true) }} />
        : <section className="session-bar" aria-label="Sessão"><div><span className="session-icon"><Icon name={CANAIS.find(c => c.label === channel)?.icon ?? 'home'} size={18} /></span><span><b>{channel}</b><small>{CANAIS.find(c => c.label === channel)?.note}</small></span><span className="session-case">{selected.replace('IMO_', '')} · {item?.municipio}/{item?.uf}</span></div><div><button className="text-button reset" disabled={busy || !data} onClick={() => { setReportOpen(false); irPara(1); irParaSac(1); void load(selected, [], 'Reinício') }}><Icon name="reset" size={16} />Recomeçar</button><button className="button secondary" onClick={() => { setPresentation(false); setEntrou(false) }}>Trocar de canal</button></div></section>}
      {presentation && <div className="presentation-bar"><span><Icon name="play" size={17} />Apresentação <b>{step + 1} / 3</b></span><strong>{steps[step]}</strong><div><button aria-label="Etapa anterior" disabled={step === 0} onClick={() => setStep(s => s - 1)}>←</button><button aria-label="Próxima etapa" disabled={step === 2} onClick={() => setStep(s => s + 1)}>→</button><button onClick={() => setPresentation(false)}>Sair</button></div>{!mobile && <small>Setas navegam · números respondem · Esc sai</small>}</div>}
      {error && <div className={`error-banner ${!data ? 'offline-card' : ''}`} role="alert"><Icon name="info" /><div><strong>{data ? 'Não foi possível atualizar a Casa Gêmea.' : 'Sua Casa Gêmea espera pela conexão.'}</strong>{!data && <p>O app pode abrir sem internet. Para consultar o imóvel, reconecte à mesma rede do computador da demonstração.</p>}<p>{texto(error)}</p>{data && <span>Os dados abaixo são a última resposta válida. Suas respostas foram preservadas.</span>}</div><button className="button secondary" onClick={() => setRetry(n => n + 1)}>Tentar novamente</button></div>}
      {entrou && (!data ? !error && <div className="loading-state" role="status"><div className="loading-house"><Icon name="home" size={45} /></div><h2>Montando a Casa Gêmea...</h2><p>Estamos juntando o que já sabemos para calcular sua proteção.</p><div className="skeleton" /></div> : <>
        <div className="journey-strip"><div><span className="case-id" data-testid="caso-atual">{data.imovel_id}</span><span className="location-text"><Icon name="pin" size={14} />{item?.municipio}/{item?.uf}</span></div><div className="answered-counter" data-testid="respondidas"><b>{history.length}</b> {history.length === 1 ? 'respondida' : 'respondidas'}</div></div>
        <div className="status-announcement" role="status" aria-live="polite">{busy ? 'Atualizando...' : notice}</div>
        {story && <HouseHero data={data} location={`${item?.municipio}/${item?.uf}`} pending={busy} showPlan={!showReport} onOpenReport={() => setReportOpen(true)} imovel={selected} />}
        <div className={`workspace ${story ? 'story' : channel === 'Gerente' || channel === 'SAC' ? 'manager' : ''}`}><div className="workspace-main">{story && (showReport ? <ClientReport data={data} initial={sessions[selected]?.initial ?? null} pending={busy} history={history} onBack={() => setReportOpen(false)} onUndo={undo} /> : question)}
          {channel === 'Cliente' && mobile && <>{question}<details className="mobile-twin"><summary><Icon name="home" size={19} /><span>Ver sua Casa Gêmea<small>O que já sabemos e de onde veio</small></span><b>+</b></summary>{house}</details></>}
          {channel === 'Gerente' && <ManagerFlow data={data} initial={sessions[selected]?.initial ?? null} history={history} busy={busy} passo={passo} onPasso={irPara} question={question} onUndo={undo} cidade={`${item?.municipio}/${item?.uf}`} />}
          {channel === 'SAC' && <SacFlow data={data} history={history} busy={busy} passo={passoSac} onPasso={irParaSac} question={question} onUndo={undo} cidade={`${item?.municipio}/${item?.uf}`} />}
          {channel === 'Agente' && <Agent data={data} answers={answersFrom(history)} busy={busy} onApply={applyJson} />}
        </div>{!story && channel !== 'Gerente' && channel !== 'SAC' && <MobileRecommendation key={selected} data={data} initial={sessions[selected]?.initial ?? null} pending={busy} mobile={mobile} client={channel === 'Cliente'} presentationStep={presentation ? step : null} />}</div>
      </>)}
      <details className="privacy-note"><summary><Icon name="lock" size={17} />Como usamos seus dados</summary><p>Usamos só o que ajuda a proteger sua casa. Idade e renda não entram na conta. Cada estimativa mostra de onde veio. Dados de demonstração.</p></details>
    </main><footer><span><b>horus</b> · Casa Gêmea</span><p>Datathon Proteção Inteligente · BBDW + Ibmec · 2026</p><span>Dados sintéticos. Sem contratação real.</span></footer><ComoUsar open={ajuda} onClose={() => setAjuda(false)} onApresentar={() => setPresentation(true)} />
  </div>
}
