import { type FormEvent, type ReactNode, useEffect, useState } from 'react'
import type { Registro, Resultado } from './types'
import { confianca, coberturas as nomesCobertura, nomes, planos, reais } from './format'
import { Icon } from './Icons'
import { Modal } from './Modal'
import { Manager, ManagerQueue } from './Channels'
import { Recommendation } from './Recommendation'
import { AnswerHistory } from './Question'
import { descricaoCobertura, paraVoce, passoCliente } from './cliente'

export type PassoGerente = 1 | 2 | 3
const PASSOS: { n: PassoGerente; nome: string }[] = [
  { n: 1, nome: 'Relatório inicial' }, { n: 2, nome: 'Perguntas sugeridas' }, { n: 3, nome: 'Resultado para o cliente' },
]
const canal: Record<string, string> = { VERDE: 'Verde', AMARELO: 'Amarelo', VERMELHO: 'Vermelho' }
const hoje = () => new Date().toLocaleDateString('pt-BR')

/** Texto do relatório para o cliente: o mesmo conteúdo da tela, em linhas, para impressão e e-mail. */
export function relatorioTexto(data: Resultado, cidade: string): string[] {
  const rec = data.recomendacao
  const comparacao = data.comparacao_planos ?? []
  const escolhido = comparacao.find(p => p.situacao === 'RECOMENDADO')
  const linhas = [
    `Recomendação de Seguro Residencial · ${cidade} · ${hoje()}`, '',
    `Plano recomendado: ${planos[rec.plano] ?? 'sem plano'}`,
    ...(escolhido?.motivos.length ? ['Por quê:', ...escolhido.motivos.map(m => `- ${paraVoce(m)}`)] : []), '',
    'Coberturas e limites sugeridos (valor máximo que o seguro pagaria; não é o preço):',
    ...data.coberturas.map(c => `- ${nomesCobertura[c.cobertura] ?? c.cobertura}: ${reais(c.faixa_valor_min)} a ${reais(c.faixa_valor_max)}`), '',
    ...comparacao.filter(p => p.situacao !== 'RECOMENDADO').flatMap(p => [`Por que não o ${p.nome}: ${paraVoce(p.resumo)}`]), '',
    `Próximo passo: ${passoCliente(data).toLowerCase()}.`,
    'Recomendação inicial feita com os dados do banco e as suas respostas. Não é proposta nem cotação.',
  ]
  return linhas
}

/** Versão para imprimir ou salvar em PDF. Só aparece na impressão (ver story.css). */
function RelatorioImpressao({ data, cidade }: { data: Resultado; cidade: string }) {
  const rec = data.recomendacao
  const comparacao = data.comparacao_planos ?? []
  const escolhido = comparacao.find(p => p.situacao === 'RECOMENDADO')
  return <article className="print-only" aria-hidden="true">
    <header><strong>Seguro Residencial · recomendação para você</strong><span>{cidade} · {hoje()}</span></header>
    <h1>Plano recomendado: {planos[rec.plano] ?? 'sem plano'}</h1>
    {escolhido && escolhido.motivos.length > 0 && <><h2>Por que este plano</h2><ul>{escolhido.motivos.map((m, i) => <li key={i}>{paraVoce(m)}</li>)}</ul></>}
    <h2>O que o seu plano cobre</h2>
    <table><thead><tr><th>Cobertura</th><th>Limite sugerido</th><th>O que protege</th></tr></thead>
      <tbody>{data.coberturas.map(c => <tr key={c.cobertura}><td>{nomesCobertura[c.cobertura] ?? c.cobertura}</td><td>{reais(c.faixa_valor_min)} a {reais(c.faixa_valor_max)}</td><td>{descricaoCobertura[c.cobertura] ?? ''}</td></tr>)}</tbody></table>
    <p className="print-note">O limite é o valor máximo que o seguro pagaria. Não é o preço do seguro.</p>
    {comparacao.filter(p => p.situacao !== 'RECOMENDADO').map(p => <section key={p.plano}><h2>Por que não o {p.nome}</h2><p>{paraVoce(p.resumo)}</p>{p.motivos.slice(-1).map((m, i) => <p key={i}>{paraVoce(m)}</p>)}</section>)}
    <h2>Próximo passo</h2><p>{passoCliente(data)}.</p>
    <p className="print-note">Recomendação inicial feita com os dados do banco e as suas respostas. Não é proposta nem cotação. Protótipo do Datathon Proteção Inteligente.</p>
  </article>
}

export function EnviarEmail({ open, onClose, data, cidade }: { open: boolean; onClose: () => void; data: Resultado; cidade: string }) {
  const [email, setEmail] = useState('')
  const [enviado, setEnviado] = useState('')
  useEffect(() => { if (open) setEnviado('') }, [open])
  const assunto = `Sua recomendação de Seguro Residencial: plano ${planos[data.recomendacao.plano] ?? ''}`
  const enviar = (e: FormEvent) => { e.preventDefault(); setEnviado(email) }
  return <Modal open={open} onClose={onClose} title="Enviar relatório por e-mail" className="email-sheet">
    <div className="sheet-header"><h2>Enviar relatório por e-mail</h2><button className="button secondary" onClick={onClose}>Fechar</button></div>
    <div className="sheet-scroll email-body">
      {enviado ? <p className="sim-done" role="status"><Icon name="check" size={16} />Simulação concluída: nenhum e-mail foi enviado. Em produção, o relatório iria para {enviado} pelos canais oficiais do banco.</p>
        : <form onSubmit={enviar}>
          <label htmlFor="email-cliente">E-mail do cliente</label>
          <input id="email-cliente" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="nome@exemplo.com" />
          <p className="small-note">Envie só com a autorização do cliente. O e-mail leva a recomendação, não dados de cadastro.</p>
          <button className="button primary">Enviar (simulação)</button>
        </form>}
      <div className="email-preview"><span className="mini-label">Assunto</span><p><b>{assunto}</b></p><span className="mini-label">Mensagem</span>{relatorioTexto(data, cidade).map((l, i) => l ? <p key={i}>{l}</p> : <br key={i} />)}</div>
    </div>
  </Modal>
}

/** Visão do gerente em três páginas: o relatório do motor, as perguntas e o resultado para apresentar. */
export function ManagerFlow({ data, initial, history, busy, passo, onPasso, question, onUndo, cidade }: {
  data: Resultado; initial: Resultado | null; history: Registro[]; busy: boolean; passo: PassoGerente;
  onPasso: (p: PassoGerente) => void; question: ReactNode; onUndo: (index: number) => void; cidade: string;
}) {
  const [email, setEmail] = useState(false)
  const rec = data.recomendacao
  const perguntas = data.status === 'INELEGIVEL' ? 0 : data.proximas_perguntas.length
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior }) }, [passo])
  return <section className="manager-flow" aria-label="Atendimento do gerente">
    <ol className="manager-steps">{PASSOS.map(p => <li key={p.n}><button className={passo === p.n ? 'active' : passo > p.n ? 'done' : ''} aria-current={passo === p.n ? 'step' : undefined} onClick={() => onPasso(p.n)}><span>{passo > p.n ? <Icon name="check" size={14} /> : p.n}</span>{p.nome}</button></li>)}</ol>

    {passo === 1 && <>
      <section className="card manager-summary">
        <div><span className="eyebrow">Relatório inicial · {data.cliente_id} · {cidade}</span><h2>Antes de falar com o cliente</h2>
          <p className="muted">Recomendação feita só com os dados do banco. Confira os selos e as evidências; as perguntas da próxima página confirmam o que falta.</p></div>
        <dl className="manager-kpis">
          <div><dt>Plano inicial</dt><dd>{planos[rec.plano] ?? 'Sem plano'}</dd></div>
          <div><dt>Confiança</dt><dd>{confianca[rec.confianca_geral]}</dd></div>
          <div><dt>Semáforo</dt><dd>{canal[data.canal.semaforo]}</dd></div>
          <div><dt>Perguntas sugeridas</dt><dd>{perguntas}</dd></div>
        </dl>
        {rec.campos_que_podem_mudar_o_plano.length > 0 && <p className="manager-alert"><Icon name="info" size={16} />O plano ainda pode mudar com: {rec.campos_que_podem_mudar_o_plano.map(c => (nomes[c] ?? c.replace(/_/g, ' ')).toLowerCase()).join(', ')}.</p>}
        <button className="button primary" onClick={() => onPasso(perguntas ? 2 : 3)}>{perguntas ? 'Começar as perguntas sugeridas' : 'Ver resultado para o cliente'} <Icon name="arrow" size={16} /></button>
      </section>
      <div className="manager-grid"><Manager data={data} /><Recommendation data={data} initial={initial} pending={busy} /></div>
    </>}

    {passo === 2 && <>
      <div className="manager-grid">{question}<ManagerQueue data={data} /></div>
      <div className="manager-nav"><button className="button secondary" onClick={() => onPasso(1)}>← Relatório inicial</button><button className="button primary" onClick={() => onPasso(3)}>Ver resultado para o cliente <Icon name="arrow" size={16} /></button></div>
    </>}

    {passo === 3 && <>
      <section className="card manager-summary">
        <div><span className="eyebrow">Resultado para apresentar · {cidade}</span><h2>{perguntas ? 'Resultado até agora' : 'Recomendação pronta para o cliente'}</h2>
          <p className="muted">Esta é a versão que o cliente entende, sem termos técnicos. Mostre na tela, gere o relatório ou envie por e-mail.</p></div>
        <div className="manager-actions">
          <button className="button primary" onClick={() => window.print()}>Gerar relatório para o cliente</button>
          <button className="button secondary" onClick={() => setEmail(true)}>Enviar por e-mail</button>
          {perguntas > 0 && <button className="button secondary" onClick={() => onPasso(2)}>← Voltar às perguntas</button>}
        </div>
      </section>
      <div className="manager-result"><Recommendation data={data} initial={initial} pending={busy} full history={history} duvidas={false} /><AnswerHistory history={history} busy={busy} onUndo={i => { onPasso(2); onUndo(i) }} open /></div>
      <RelatorioImpressao data={data} cidade={cidade} />
      <EnviarEmail open={email} onClose={() => setEmail(false)} data={data} cidade={cidade} />
    </>}
  </section>
}
