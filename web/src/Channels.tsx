import { useEffect, useState } from 'react'
import type { Campo, Respostas, Resultado } from './types'
import { buscar } from './api'
import { campoPergunta, confianca, json, nomes, texto, valorCampo } from './format'
import { Selo } from './House'
import { Icon } from './Icons'

/** Ficha técnica: cada dado da Casa Gêmea com selo, evidência e conflitos da inferência. */
export function Manager({ data }: { data: Resultado }) {
  const [signals, setSignals] = useState<string[]>([])
  const [error, setError] = useState('')
  useEffect(() => {
    const control = new AbortController()
    setSignals([]); setError('')
    buscar<{ inconsistencias: string[] }>(`/imoveis/${encodeURIComponent(data.imovel_id)}/sinais`, { signal: control.signal })
      .then(s => setSignals(s.inconsistencias)).catch(e => { if (!control.signal.aborted) setError(e.message) })
    return () => control.abort()
  }, [data.imovel_id])
  return <section className="card"><span className="eyebrow">Ficha técnica / Gerente</span><h2>Cada dado, com sua evidência.</h2><p className="muted">Os mesmos sinais e a mesma recomendação da visão Cliente.</p>
      <div className="manager-fields">{Object.keys(nomes).map(key => {
        const campo = data.casa_gemea[key as keyof typeof data.casa_gemea] as Campo
        return <article key={key}><div className="manager-field-heading"><span>{nomes[key]}</span><Selo campo={campo} /></div><strong>{valorCampo(key, campo, data.casa_gemea)}</strong><p>{texto(campo.evidencia)}</p></article>
      })}</div>
      <div className="conflicts"><h3>Sinais em conflito na inferência inicial</h3>{error ? <p role="alert">{texto(error)}</p> : signals.length ? <ul>{signals.map((s, i) => <li key={i}>{texto(s)}</li>)}</ul> : <p>Nenhum conflito registrado nesta ficha.</p>}<p className="small-note">As confirmações atuais aparecem nos selos acima.</p></div>
    </section>
}

/** Fila de perguntas na ordem de impacto, com o motivo de cada uma. */
export function ManagerQueue({ data }: { data: Resultado }) {
  return <section className="card"><span className="eyebrow">Ordem de impacto</span><h2>Por que perguntar, e por que agora?</h2>{data.proximas_perguntas.length ? <ol className="question-queue">{data.proximas_perguntas.map(q => <li key={q.id}><span className="impact-label">{texto(q.impacto)}</span><h3>{texto(q.pergunta)}</h3>{campoPergunta(q.id, data.casa_gemea) && <Selo campo={campoPergunta(q.id, data.casa_gemea)!} />}<p>{texto(q.motivo)}</p><span className="small-note">{q.opcoes.map(o => texto(o.rotulo)).join(' / ')}</span></li>)}</ol> : <p>O motor não selecionou mais perguntas para este caso.</p>}</section>
}

/** Explica a função da aba Agente para a banca: aberta no computador, fechada no celular. */
function AgenteExplica() {
  const [aberto, setAberto] = useState(() => matchMedia('(min-width: 768px)').matches)
  const quem = ['App e internet banking do BB', 'Bot de WhatsApp ou assistente com IA', 'Sistema do gerente', 'Imobiliárias e construtoras, na compra ou no aluguel']
  const passos = ['Envia o JSON de entrada', 'Recebe o JSON de saída', 'Envia de novo com a nova resposta']
  return <details className="agente-explica" open={aberto} onToggle={e => setAberto(e.currentTarget.open)}>
    <summary><Icon name="info" size={18} />Para que serve esta aba</summary>
    <div className="agente-grid">
      <article><h3><Icon name="code" size={18} />Para que serve</h3><p>O motor é uma peça que outros sistemas chamam.</p><p>O sistema manda o imóvel e as respostas que já tem.</p><p>O motor devolve plano, faixas, confiança e a próxima pergunta.</p><p>É a mesma decisão do Cliente, do Gerente e do SAC.</p></article>
      <article><h3><Icon name="person" size={18} />Quem usaria</h3><ul>{quem.map(q => <li key={q}>{q}</li>)}</ul><p className="small-note">A IA conversa e explica. Quem decide plano e valor é o motor.</p></article>
      <article><h3><Icon name="shuffle" size={18} />Como funciona</h3><ol>{passos.map(p => <li key={p}>{p}</li>)}</ol><p className="small-note">O motor não guarda estado.</p></article>
    </div>
    <p className="agente-garantia"><Icon name="shield" size={16} />Mesma regra em todos os canais, sem idade nem renda, e toda estimativa com selo e confiança.</p>
  </details>
}

export function Agent({ data, answers, busy, onApply }: { data: Resultado; answers: Respostas; busy: boolean; onApply: (value: string) => Promise<void> }) {
  const entrada = { versao_contrato: data.versao_contrato, imovel_id: data.imovel_id, respostas: answers }
  const [input, setInput] = useState(json(entrada))
  const [copied, setCopied] = useState('')
  const [error, setError] = useState('')
  const serialized = json(entrada)
  useEffect(() => { setInput(serialized); setError('') }, [serialized])
  async function copy(value: string, name: string) {
    try { await navigator.clipboard.writeText(value); setCopied(name) }
    catch { setCopied('Selecione o texto e use Ctrl+C.') }
  }
  return <section className="card agent-panel"><span className="eyebrow">Contrato aberto / Agente</span><h2>Um motor. Qualquer canal.</h2><p className="muted">Cada chamada envia todas as respostas. A saída é o contrato real, sem decisão no navegador.</p><AgenteExplica />
    <div className="code-toolbar"><label htmlFor="input-json">Entrada JSON</label><button className="text-button" onClick={() => copy(input, 'Entrada copiada')}><Icon name="copy" size={15} />Copiar entrada</button></div>
    <textarea id="input-json" className="json-editor" spellCheck={false} value={input} onChange={e => setInput(e.target.value)} disabled={busy} rows={12} />
    <button className="button primary" disabled={busy} onClick={async () => { try { setError(''); await onApply(input) } catch (e) { setError(e instanceof Error ? e.message : 'JSON inválido.') } }}>Executar contrato <Icon name="arrow" size={16} /></button>
    {error && <p role="alert" className="inline-error">{texto(error)}</p>}
    <div className="code-toolbar"><span>Saída JSON</span><button className="text-button" onClick={() => copy(json(data), 'Saída copiada')}><Icon name="copy" size={15} />Copiar saída</button></div>
    <pre className="json-output" aria-label="Saída JSON" tabIndex={0}>{json(data)}</pre><p className="small-note" role="status">{copied || `Contrato ${data.versao_contrato} · Confiança ${confianca[data.recomendacao.confianca_geral]?.toLowerCase()}`}</p>
  </section>
}
