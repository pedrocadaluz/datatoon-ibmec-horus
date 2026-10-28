import { useState } from 'react'
import type { ResultadoPersonalizado } from './types'
import { coberturas, planos, texto } from './format'
import { Modal } from './Modal'

function Barras({ titulo, itens, total }: { titulo: string; itens: { pontos: number; sinal: string }[]; total: number }) {
  return <div className="mp-bars"><h4>{titulo}: {total} ponto{total === 1 ? '' : 's'}</h4>
    {itens.length ? <ul>{itens.map(s => <li key={s.sinal}><span className="mp-bar"><i style={{ width: `${Math.min(100, s.pontos * 33)}%` }} /></span><b>{s.pontos}</b> {texto(s.sinal)}</li>)}</ul> : <p className="small-note">Nenhum sinal.</p>}</div>
}

export function MotorConteudo({ data }: { data: ResultadoPersonalizado }) {
  const [aberta, setAberta] = useState('')
  const passo = (id: string) => data.explicacao.passos.find(p => p.id === id)
  const eleg = passo('elegibilidade'), plano = passo('plano'), perg = passo('perguntas')
  return <div className="mp">
    <section><h3>1. Este imóvel pode ser segurado?</h3><p className="mp-result">{eleg?.resultado === 'ELEGIVEL' ? 'Sim, sem pendências.' : texto(eleg?.resultado)}</p>
      <ul className="mp-checks">{eleg?.checagens?.map(c => <li key={c.regra}><span className={c.ok && !c.pendente ? 'ok' : 'pend'} aria-hidden="true">{c.ok && !c.pendente ? '✓' : '!'}</span><span>{texto(c.regra)}<small>{c.pendente ? 'A confirmar com você' : c.ok ? 'Conferido' : 'Não atende'} · {c.base}</small></span></li>)}</ul></section>
    <section><h3>2. Qual plano faz sentido?</h3><p className="mp-result">Plano {texto(plano?.resultado)}</p>
      <Barras titulo="Prático" itens={plano?.sinais_pratico ?? []} total={plano?.pontos_pratico ?? 0} />
      <Barras titulo="Total" itens={plano?.sinais_total ?? []} total={plano?.pontos_total ?? 0} />
      <p className="small-note"><b>Regra:</b> {texto(plano?.regra)}</p>
      <details><summary>Por que não o plano de baixo?</summary><p>{texto(plano?.por_que_nao_o_de_baixo)}</p></details>
      <details><summary>Por que não o plano de cima?</summary><p>{texto(plano?.por_que_nao_o_de_cima)}</p></details></section>
    <section><h3>3. O que ainda pode mudar o plano</h3>
      <p>{perg?.campos_que_mudam_o_plano?.length ? `Só perguntamos o que muda o resultado: ${perg.campos_que_mudam_o_plano.join(', ')}.` : 'Nenhuma resposta restante muda o plano. Por isso paramos de perguntar.'}</p></section>
    <section><h3>4. Necessidade por cobertura</h3><p className="small-note">Índice de 0 a 100. Toque para ver os fatores.</p>
      <ul className="mp-need">{data.personalizacao.necessidades.map(n => <li key={n.cobertura}><button aria-expanded={aberta === n.cobertura} onClick={() => setAberta(aberta === n.cobertura ? '' : n.cobertura)}>
        <span className="mp-need-name">{coberturas[n.cobertura] ?? n.cobertura}{n.no_plano_recomendado ? '' : <small> · fora do plano</small>}</span>
        <span className="mp-bar"><i className={`n-${n.nivel.toLowerCase()}`} style={{ width: `${n.indice}%` }} /></span><b>{n.indice}</b></button>
        {aberta === n.cobertura && <p className="mp-factors">{n.fatores.length ? n.fatores.map(f => `+${f.pontos} ${texto(f.fator)}`).join(' · ') : 'Sem fator específico: nível básico da carteira.'}</p>}</li>)}</ul></section>
    <section><h3>5. Limites do motor</h3><ul className="mp-limits">{data.explicacao.limites_do_motor.map(l => <li key={l}>{texto(l)}</li>)}</ul>
      <p className="small-note">As faixas são “limite sugerido de indenização”, não preço. O plano {planos[data.recomendacao.plano] ?? ''} é uma recomendação transparente, não uma contratação.</p></section>
  </div>
}

export function MotorSheet({ open, onClose, data }: { open: boolean; onClose: () => void; data: ResultadoPersonalizado }) {
  return <Modal open={open} onClose={onClose} title="Como o motor pensou" className="mp-sheet"><div className="sheet-header"><h2>Como o motor pensou</h2><button className="button secondary" onClick={onClose}>Fechar</button></div><div className="sheet-scroll"><MotorConteudo data={data} /></div></Modal>
}
