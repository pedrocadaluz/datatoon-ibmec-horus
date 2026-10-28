import { useEffect, useRef, useState } from 'react'
import type { Adicional, Respostas, ResultadoPersonalizado } from './types'
import { buscarPersona, chaveAdicional, jornadaRotulo, personas } from './personas'
import { planos, reais, texto } from './format'
import { Icon } from './Icons'
import { House } from './House'
import { Modal } from './Modal'
import { MotorSheet } from './MotorPensou'

const tons = { EXPRESS: 'tom-express', GUIADA: 'tom-guiada', HUMANA: 'tom-humana' } as const
const nivelTexto = (n: string) => (n === 'ALTA' ? 'alta' : n === 'MEDIA' ? 'média' : 'baixa')

function CartaoAdicional({ a, resposta, dispensado, onResponder, onAdicionar, onDispensar }: {
  a: Adicional; resposta?: string; dispensado: boolean; onResponder: (v: string) => void; onAdicionar: () => void; onDispensar: () => void;
}) {
  const adicionado = resposta === 'SIM' || resposta === 'ADD'
  return <article className={`sim-add ${adicionado ? 'added' : ''}`} aria-label={a.nome}>
    <header><h4>{a.nome}</h4><span className={`sim-badge n-${a.nivel.toLowerCase()}`}>Necessidade {nivelTexto(a.nivel)} · {a.necessidade}</span></header>
    <p className="sim-why"><b>Por que é para você:</b> {texto(a.por_que_para_voce)}</p>
    {a.faixa_valor_min !== undefined && a.faixa_valor_max !== undefined && <p className="sim-range">Limite sugerido de indenização: <b>{reais(a.faixa_valor_min)} a {reais(a.faixa_valor_max)}</b><small> Estimativa, confiança média. Não é preço.</small></p>}
    <details><summary>Cuidados e base</summary><p>{texto(a.cuidado)} ({a.clausula})</p></details>
    {a.pergunta && !adicionado && !dispensado && <div className="sim-ask" role="group" aria-label={a.pergunta}><p>{texto(a.pergunta)}</p>
      <div>{[['SIM', 'Sim'], ['NAO', 'Não'], ['NAO_SEI', 'Não sei']].map(([v, r]) => <button key={v} className="sim-chip" onClick={() => onResponder(v)}>{r}</button>)}</div></div>}
    {adicionado ? <p className="sim-done" role="status"><Icon name="check" size={16} />Adicionado ao seu plano</p>
      : !dispensado && (!a.pergunta || resposta === 'NAO_SEI') && <div className="sim-actions"><button className="button primary" onClick={onAdicionar}>Adicionar</button><button className="text-button" onClick={onDispensar}>Agora não</button></div>}
    {dispensado && <p className="small-note">Deixamos de lado por enquanto.</p>}
  </article>
}

export function AppSim({ onComparar }: { onComparar: () => void }) {
  const [id, setId] = useState(personas[0].id)
  const [respostas, setRespostas] = useState<Record<string, Respostas>>({})
  const [data, setData] = useState<ResultadoPersonalizado | null>(null)
  const [erro, setErro] = useState('')
  const [tela, setTela] = useState<'home' | 'jornada'>('home')
  const [personalizar, setPersonalizar] = useState(true)
  const [recibos, setRecibos] = useState(false)
  const [motor, setMotor] = useState(false)
  const [escolhas, setEscolhas] = useState<Record<string, string>>({})
  const [dispensados, setDispensados] = useState<string[]>([])
  const resp = respostas[id] ?? {}
  const seq = useRef(0)

  useEffect(() => {
    const n = ++seq.current, ctrl = new AbortController()
    setErro('')
    buscarPersona(id, resp, ctrl.signal).then(r => { if (n === seq.current) setData(r) })
      .catch(e => { if (!ctrl.signal.aborted) setErro(e.message) })
    return () => ctrl.abort()
  }, [id, respostas]) // eslint-disable-line react-hooks/exhaustive-deps

  const pers = data?.personalizacao
  const perfil = pers?.perfil
  const pergunta = data?.proximas_perguntas[0]
  const tom = personalizar && perfil ? tons[perfil.jornada] : 'tom-neutro'
  function trocar(novo: string) { if (novo !== id) { setId(novo); setData(null) }; setTela('home'); setEscolhas({}); setDispensados([]); setPersonalizar(true) }
  function responder(campo: string, v: string | number) { setRespostas(r => ({ ...r, [id]: { ...(r[id] ?? {}), [campo]: v } })) }
  function adicional(a: Adicional, v: string) {
    if (a.pergunta) responder(chaveAdicional(a.id), v)
    setEscolhas(e => ({ ...e, [a.id]: v }))
  }
  const fire = data?.coberturas.find(c => c.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA')
  const visiveis = (pers?.adicionais_sugeridos ?? []).filter(a => !(a.pergunta && resp[chaveAdicional(a.id)] === 'NAO'))
  const nome = personas.find(p => p.id === id)?.nome

  return <section className="sim" aria-label="Simulador do app do banco">
    <div className="sim-personas" role="group" aria-label="Escolha uma persona">
      {personas.map(p => <button key={p.id} aria-pressed={id === p.id} className={id === p.id ? 'active' : ''} onClick={() => trocar(p.id)}><b>{p.nome}</b><small>{p.frase}</small></button>)}
    </div>
    <div className="sim-tools"><button className="button secondary" onClick={() => setMotor(true)} disabled={!data}>Como o motor pensou</button><button className="button secondary" onClick={onComparar}>Comparar as 3 personas</button></div>
    {erro && <div className="error-banner" role="alert"><Icon name="info" /><div><strong>Não foi possível consultar o motor.</strong><p>{texto(erro)}</p></div></div>}
    <div className="phone" data-testid="celular-simulado"><div className="phone-screen">
      {!data ? <div className="loading-state" role="status"><p>Carregando a persona...</p></div> : tela === 'home' ? <div className="bank-home">
        <header className="bank-head"><span>Olá, {nome}</span><span className="bank-proto">Banco fictício</span></header>
        <div className="bank-balance"><small>Saldo disponível</small><b>R$ 4.280,00</b></div>
        <div className="bank-shortcuts" aria-hidden="true">{['Pix', 'Pagar', 'Cartões', 'Investir'].map(s => <span key={s}>{s}</span>)}</div>
        {pers && <button className={`notif ${tom}`} onClick={() => setTela('jornada')} data-testid="notificacao">
          <span className="notif-top"><Icon name="shield" size={16} />Sugestão para a sua casa</span>
          <strong>{personalizar ? texto(pers.mensagem_do_app.titulo) : 'Conheça o seguro residencial'}</strong>
          <span>{personalizar ? texto(pers.mensagem_do_app.texto) : 'Proteja a sua casa com um plano básico.'}</span><span className="notif-cta">Ver sugestão</span></button>}
      </div> : data.elegibilidade.status === 'INELEGIVEL' ? <div className="jornada"><button className="text-button" onClick={() => setTela('home')}>← Voltar</button><p>Este imóvel precisa de validação com um especialista.</p></div> : <div className={`jornada ${tom}`}>
        <div className="jornada-top"><button className="text-button" onClick={() => setTela('home')}>← Voltar</button>
          <label className="switch"><input type="checkbox" role="switch" checked={personalizar} onChange={e => setPersonalizar(e.target.checked)} /><span>Personalizar para mim</span></label></div>
        {personalizar && perfil && <p className="sim-profile"><span className="sim-badge">{perfil.rotulo}</span> Jornada {jornadaRotulo[perfil.jornada]}. <button className="link" onClick={() => setRecibos(true)}>Por que estou vendo isto?</button></p>}
        {!personalizar && <p className="small-note">Versão padrão, sem tom, destaques nem adicionais. <button className="link" onClick={() => setRecibos(true)}>Por que estou vendo isto?</button></p>}
        <details className="mobile-twin" open><summary><Icon name="home" size={18} /><span>Sua Casa Gêmea<small>Cada dado com selo e confiança</small></span></summary><House casa={data.casa_gemea} location={data.imovel_id} imovel={id} /></details>
        {pergunta && <section className="sim-q" aria-live="polite"><h3>{texto(pergunta.pergunta)}</h3>
          {personalizar && perfil?.jornada === 'GUIADA' && <p className="small-note"><b>Por que perguntamos:</b> {texto(pergunta.motivo)}</p>}
          <div className="sim-opts">{[...pergunta.opcoes, ...(pergunta.opcoes.some(o => o.valor === 'NAO_SEI') ? [] : [{ valor: 'NAO_SEI', rotulo: 'Não sei' }])].map(o => <button key={o.valor} className="sim-chip" onClick={() => responder(pergunta.id, o.valor)}>{texto(o.rotulo)}</button>)}</div>
          {personalizar && perfil?.jornada === 'HUMANA' && <button className="button secondary sim-human" onClick={() => setEscolhas(e => ({ ...e, __especialista: 'SIM' }))}>Falar com um especialista</button>}
          {escolhas.__especialista && <p className="sim-done" role="status">Simulação: um especialista entraria em contato.</p>}</section>}
        <section className="sim-plan"><span className="eyebrow">Seu plano</span><h3>{planos[data.recomendacao.plano] ?? 'Sem plano'}</h3>
          <p>{texto(data.recomendacao.justificativa_curta)}</p>
          {fire && <p className="sim-range">Limite sugerido de indenização para incêndio: <b>{reais(fire.faixa_valor_min)} a {reais(fire.faixa_valor_max)}</b><small> Confiança {nivelTexto(fire.confianca)}. Não é preço.</small></p>}
          <p className="small-note">Canal: {data.canal.semaforo.toLowerCase()} · {data.jornada.perguntas_evitadas} de {data.jornada.campos_formulario_tradicional} perguntas evitadas.</p></section>
        {personalizar && pers && <>
          {pers.alertas.map(al => <p key={al.tipo} className="sim-alert" role="note"><Icon name="info" size={16} />{texto(al.texto)}</p>)}
          {visiveis.length > 0 && <section><h3>Adicionais para a sua casa</h3>{visiveis.map(a => <CartaoAdicional key={a.id} a={a} resposta={escolhas[a.id] ?? resp[chaveAdicional(a.id)]} dispensado={dispensados.includes(a.id)}
            onResponder={v => adicional(a, v)} onAdicionar={() => adicional(a, a.pergunta ? 'SIM' : 'ADD')} onDispensar={() => setDispensados(d => [...d, a.id])} />)}</section>}
          <section className="sim-assist"><h3>Assistências em destaque</h3><p className="small-note">Base do plano: {pers.assistencias.base}</p>
            {pers.assistencias.destaque.map(d => <p key={d.nome}><b>{d.nome}:</b> {texto(d.por_que)}</p>)}
            {pers.assistencias.beneficio_premium_sugerido && <p><b>Benefício sugerido: {pers.assistencias.beneficio_premium_sugerido.nome}.</b> {texto(pers.assistencias.beneficio_premium_sugerido.por_que)}</p>}</section></>}
        <p className="small-note">Protótipo sem contratação real. Idade e renda nunca são usadas.</p>
      </div>}
    </div></div>
    <Modal open={recibos} onClose={() => setRecibos(false)} title="Por que estou vendo isto?" className="mp-sheet"><div className="sheet-header"><h2>Por que estou vendo isto?</h2><button className="button secondary" onClick={() => setRecibos(false)}>Fechar</button></div>
      <div className="sheet-scroll"><p className="small-note">Dados do banco usados nesta sugestão. Idade e renda nunca entram.</p><ul className="sim-receipts">{pers?.recibos.map(r => <li key={r.dado}><b>{texto(r.dado)}</b><span>usado para {texto(r.usado_para)}</span></li>)}</ul></div></Modal>
    {data && <MotorSheet open={motor} onClose={() => setMotor(false)} data={data} />}
  </section>
}
