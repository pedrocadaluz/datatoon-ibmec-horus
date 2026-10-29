import { type FormEvent, type ReactNode, useEffect, useState } from 'react'
import type { Registro, Resultado } from './types'
import { coberturas as nomesCobertura, nomes, planos, reais } from './format'
import { Icon } from './Icons'
import { AnswerHistory } from './Question'
import { montarDuvidas } from './Duvidas'
import { EnviarEmail } from './Gerente'
import { paraVoce, passoCliente } from './cliente'

export type PassoSac = 1 | 2 | 3
const PASSOS: { n: PassoSac; nome: string }[] = [{ n: 1, nome: 'Abertura' }, { n: 2, nome: 'Roteiro de perguntas' }, { n: 3, nome: 'Encerramento' }]
const RESULTADOS = ['Cliente quer contratar', 'Vai pensar', 'Transferido para um especialista', 'Sem interesse agora']
const lista = (itens: string[]) => itens.length === 1 ? itens[0] : `${itens.slice(0, -1).join(', ')} e ${itens.at(-1)}`
const semaforo: Record<string, string> = {
  VERDE: 'Verde: dá para concluir na ligação.',
  AMARELO: 'Amarelo: faltam confirmações rápidas; faça as perguntas do roteiro.',
  VERMELHO: 'Vermelho: há uma pendência. Se continuar depois das perguntas, transfira para um especialista.',
}

/** Protocolo de demonstração, estável por imóvel e dia. */
const protocolo = (imovel: string) => `SAC-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${imovel.replace(/\D/g, '').slice(-6)}`

/** Resumo para o atendente ler ao cliente no fim da ligação. */
function falaFinal(data: Resultado): string[] {
  const rec = data.recomendacao
  const plano = planos[rec.plano]
  if (!plano) return [`Pelo que conversamos, ainda não conseguimos seguir com o seguro deste imóvel: ${paraVoce(data.elegibilidade.motivo)}`]
  const comparacao = data.comparacao_planos ?? []
  const escolhido = comparacao.find(p => p.situacao === 'RECOMENDADO')
  const fire = data.coberturas.find(c => c.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA')
  const nomesDif = (p: typeof comparacao[number]) => lista(p.diferenca.map(d => nomesCobertura[d.cobertura]?.toLowerCase() ?? d.nome))
  return [
    `Pelo que conversamos, o plano que faz mais sentido para a sua casa é o ${plano}${escolhido?.motivos.length ? `, porque ${lista(escolhido.motivos.slice(0, 3).map(paraVoce))}` : ''}.`,
    ...(fire ? [`Os valores são limites de proteção, não o preço. Para incêndio, o seguro pagaria até ${reais(fire.faixa_valor_min)} a ${reais(fire.faixa_valor_max)}.`] : []),
    ...comparacao.filter(p => p.situacao === 'ABAIXO' && p.diferenca.length).slice(-1).map(p => `Se escolher o ${p.nome}, ficaria sem ${nomesDif(p)}.`),
    ...comparacao.filter(p => p.situacao === 'ACIMA' && p.diferenca.length).slice(0, 1).map(p => `O ${p.nome} acrescentaria ${nomesDif(p)}, que hoje não são prioridade para a sua casa.`),
    `O próximo passo é ${passoCliente(data).toLowerCase()}.`,
  ]
}

function Leia({ children }: { children: ReactNode }) {
  return <div className="sac-leia"><span className="sac-leia-tag"><Icon name="headset" size={15} />Leia</span><div>{children}</div></div>
}

/** Atendimento por telefone em três etapas: abertura, roteiro de perguntas e encerramento com registro. */
export function SacFlow({ data, history, busy, passo, onPasso, question, onUndo, cidade }: {
  data: Resultado; history: Registro[]; busy: boolean; passo: PassoSac; onPasso: (p: PassoSac) => void;
  question: ReactNode; onUndo: (index: number) => void; cidade: string;
}) {
  const [email, setEmail] = useState(false)
  const [resultado, setResultado] = useState('')
  const [nota, setNota] = useState('')
  const [registrado, setRegistrado] = useState(false)
  useEffect(() => { setResultado(''); setNota(''); setRegistrado(false) }, [data.imovel_id])
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior }) }, [passo])
  const rec = data.recomendacao
  const perguntas = data.status === 'INELEGIVEL' ? 0 : data.proximas_perguntas.length
  const duvidas = montarDuvidas(data, history)
  const registrar = (e: FormEvent) => { e.preventDefault(); setRegistrado(true) }

  return <section className="manager-flow sac-flow" aria-label="Atendimento por telefone">
    <ol className="manager-steps">{PASSOS.map(p => <li key={p.n}><button className={passo === p.n ? 'active' : passo > p.n ? 'done' : ''} aria-current={passo === p.n ? 'step' : undefined} onClick={() => onPasso(p.n)}><span>{passo > p.n ? <Icon name="check" size={14} /> : p.n}</span>{p.nome}</button></li>)}</ol>

    {passo === 1 && <div className="manager-grid">
      <section className="card manager-summary"><span className="eyebrow">Abertura da ligação · {cidade}</span><h2>Comece por aqui</h2>
        <Leia><p>“Olá! Aqui é da BB Seguros. Estou falando sobre o seguro da sua casa em {cidade}. Esta ligação pode ser gravada.”</p>
          <p>“Já usamos os dados que o banco tem para entender a sua casa. Vou confirmar só o que pode mudar a sua proteção, leva poucos minutos. Se não souber alguma resposta, tudo bem.”</p></Leia>
        <p className="manager-alert"><Icon name="lock" size={16} />Confirme que fala com o titular. Nunca peça senha, código ou dados de cartão.</p>
        <button className="button primary" onClick={() => onPasso(perguntas ? 2 : 3)}>{perguntas ? 'Iniciar roteiro de perguntas' : 'Ir para o encerramento'} <Icon name="arrow" size={16} /></button>
      </section>
      <section className="card"><span className="eyebrow">Só para você, atendente</span><h2>Resumo do caso</h2>
        <dl className="manager-kpis sac-kpis">
          <div><dt>Plano inicial</dt><dd>{planos[rec.plano] ?? 'Sem plano'}</dd></div>
          <div><dt>Perguntas</dt><dd>{perguntas}</dd></div>
        </dl>
        <p className={`sac-semaforo channel-${data.canal.semaforo.toLowerCase()}`}><span className="traffic-light" />{semaforo[data.canal.semaforo]}</p>
        {rec.campos_que_podem_mudar_o_plano.length > 0 && <p className="small-note">O plano ainda pode mudar com: {rec.campos_que_podem_mudar_o_plano.map(c => (nomes[c] ?? c.replace(/_/g, ' ')).toLowerCase()).join(', ')}.</p>}
        {data.elegibilidade.motivo && <p className="small-note">Atenção: {paraVoce(data.elegibilidade.motivo)}</p>}
      </section>
    </div>}

    {passo === 2 && <>
      <div className="manager-grid">{question}
        <section className="card sac-faq"><span className="eyebrow">Se o cliente perguntar</span><h2>Respostas prontas</h2>
          {duvidas.map(d => <details key={d.id}><summary>{d.pergunta}</summary><Leia>{d.resposta.map((l, i) => <p key={i}>{l}</p>)}</Leia></details>)}
        </section></div>
      <div className="manager-nav"><button className="button secondary" onClick={() => onPasso(1)}>← Abertura</button><button className="button primary" onClick={() => onPasso(3)}>Ir para o encerramento <Icon name="arrow" size={16} /></button></div>
    </>}

    {passo === 3 && <div className="manager-grid">
      <div className="sac-close">
        <section className="card manager-summary"><span className="eyebrow">Encerramento</span><h2>{perguntas ? 'Resumo até agora' : 'Resumo para o cliente'}</h2>
          <Leia>{falaFinal(data).map((l, i) => <p key={i}>“{l}”</p>)}</Leia>
          {data.canal.semaforo === 'VERMELHO' && <p className="manager-alert"><Icon name="info" size={16} />Ainda há uma pendência: transfira para um especialista com as respostas já registradas.</p>}
          <div className="manager-actions">
            <button className="button primary" onClick={() => setEmail(true)}>Enviar resumo por e-mail</button>
            {perguntas > 0 && <button className="button secondary" onClick={() => onPasso(2)}>← Voltar ao roteiro</button>}
          </div>
          <Leia><p>“Posso enviar este resumo para o seu e-mail?”</p></Leia>
        </section>
        <AnswerHistory history={history} busy={busy} onUndo={i => { onPasso(2); onUndo(i) }} />
      </div>
      <section className="card sac-registro"><span className="eyebrow">Registro do atendimento</span><h2>Protocolo {protocolo(data.imovel_id)}</h2>
        <p className="small-note">Informe o protocolo ao cliente antes de encerrar.</p>
        {registrado ? <p className="sim-done" role="status"><Icon name="check" size={16} />Atendimento registrado (simulação): {resultado}. Nada foi gravado em sistema.</p>
          : <form onSubmit={registrar}>
            <fieldset><legend>Como terminou a ligação?</legend>{RESULTADOS.map(r => <label key={r} className="sac-radio"><input type="radio" name="resultado" value={r} required checked={resultado === r} onChange={() => setResultado(r)} />{r}</label>)}</fieldset>
            <label htmlFor="sac-nota">Observação</label>
            <textarea id="sac-nota" rows={3} value={nota} onChange={e => setNota(e.target.value)} placeholder="Ex.: cliente quer comparar com outra seguradora" />
            <button className="button primary">Registrar atendimento</button>
          </form>}
      </section>
      <EnviarEmail open={email} onClose={() => setEmail(false)} data={data} cidade={cidade} />
    </div>}
  </section>
}
