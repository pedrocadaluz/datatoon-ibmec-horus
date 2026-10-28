import { useEffect, useState } from 'react'
import type { ResultadoPersonalizado } from './types'
import { buscarPersona, jornadaRotulo, personas } from './personas'
import { planos, reais, texto } from './format'

const respostasProntas: Record<string, Record<string, string>> = {
  IMO_CASO_00008_01: { conteudo: 'NA_FAIXA', declaracao_unica: 'SIM' },
  IMO_CASO_00016_01: { obra: 'REFORMA_PEQUENA', declaracao_unica: 'SIM' },
  IMO_CASO_00059_01: { ocupacao: 'DESOCUPADO', declaracao_unica: 'SIM' },
}
const canal = (r: ResultadoPersonalizado) => `${r.canal.semaforo.toLowerCase()} · ${r.canal.sugerido.toLowerCase().replace(/_/g, ' ')}`

export function Comparativo() {
  const [inicio, setInicio] = useState<ResultadoPersonalizado[] | null>(null)
  const [fim, setFim] = useState<ResultadoPersonalizado[] | null>(null)
  const [erro, setErro] = useState('')
  useEffect(() => {
    const ctrl = new AbortController()
    Promise.all([
      Promise.all(personas.map(p => buscarPersona(p.id, {}, ctrl.signal))),
      Promise.all(personas.map(p => buscarPersona(p.id, respostasProntas[p.id], ctrl.signal))),
    ]).then(([a, b]) => { setInicio(a); setFim(b) }).catch(e => { if (!ctrl.signal.aborted) setErro(e.message) })
    return () => ctrl.abort()
  }, [])
  if (erro) return <div className="error-banner" role="alert"><div><strong>Não foi possível montar o comparativo.</strong><p>{texto(erro)}</p></div></div>
  if (!inicio || !fim) return <div className="loading-state" role="status"><p>Comparando as 3 personas...</p></div>
  const linhas: [string, (i: ResultadoPersonalizado, f: ResultadoPersonalizado) => React.ReactNode][] = [
    ['Quem é', i => texto(i.personalizacao.perfil.descricao)],
    ['Arquétipo', i => i.personalizacao.perfil.rotulo],
    ['Jornada e tom', i => `${jornadaRotulo[i.personalizacao.perfil.jornada]}: ${texto(i.personalizacao.perfil.tom)}`],
    ['Plano (início → fim)', (i, f) => `${planos[i.recomendacao.plano]} → ${planos[f.recomendacao.plano]}`],
    ['Canal (início → fim)', (i, f) => `${canal(i)} → ${canal(f)}`],
    ['Incêndio, limite sugerido (fim)', (_, f) => { const c = f.coberturas.find(x => x.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA'); return c ? `${reais(c.faixa_valor_min)} a ${reais(c.faixa_valor_max)}` : '-' }],
    ['Adicionais sugeridos', i => <ul>{i.personalizacao.adicionais_sugeridos.map(a => <li key={a.id}>{a.nome} ({a.necessidade})</li>)}</ul>],
    ['Perguntas evitadas', (_, f) => `${f.jornada.perguntas_evitadas} de ${f.jornada.campos_formulario_tradicional}`],
    ['Assistências em destaque', i => i.personalizacao.assistencias.destaque.map(d => d.nome).join(', ') || 'Base do plano'],
    ['Alertas', i => i.personalizacao.alertas.length ? i.personalizacao.alertas.map(a => texto(a.texto)).join(' ') : 'Nenhum'],
    ['Notificação do app', i => texto(i.personalizacao.mensagem_do_app.texto)],
  ]
  return <section className="comp" aria-label="Comparativo das três personas">
    <h2>Mesmo motor, três jornadas</h2>
    <p className="small-note">Nenhuma regra usa idade ou renda. A diferença vem do imóvel, do vínculo, das compras, de dependentes e pet e do uso do app (só para escolher o canal). Dados fictícios.</p>
    <div className="comp-scroll"><table><thead><tr><th scope="col"><span className="sr-only">Item</span></th>{personas.map(p => <th scope="col" key={p.id}>{p.nome}</th>)}</tr></thead>
      <tbody>{linhas.map(([rot, fn]) => <tr key={rot}><th scope="row">{rot}</th>{personas.map((p, k) => <td key={p.id}>{fn(inicio[k], fim[k])}</td>)}</tr>)}</tbody></table></div>
  </section>
}
