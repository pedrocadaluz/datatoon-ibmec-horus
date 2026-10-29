import type { Canal, Lista } from './types'
import { Icon } from './Icons'

export const CANAIS: { label: Canal; icon: string; note: string; texto: string }[] = [
  { label: 'Cliente', icon: 'home', note: 'Para quem contrata', texto: 'Vê a Casa Gêmea, responde só o que muda a proteção e recebe o relatório.' },
  { label: 'Gerente', icon: 'person', note: 'Para a agência', texto: 'Relatório inicial, perguntas sugeridas e resultado para apresentar ao cliente.' },
  { label: 'SAC', icon: 'headset', note: 'Para o telefone', texto: 'Abertura, roteiro com respostas prontas e encerramento com registro.' },
  { label: 'Agente', icon: 'code', note: 'Para sistemas', texto: 'O mesmo motor chamado por outro sistema, com entrada e saída em JSON.' },
]

/**
 * Tela de entrada: escolher a Casa Gêmea e o perfil. Não é login de verdade (sem usuário nem senha);
 * cada perfil vê só o seu canal, e "Trocar de canal" volta para cá.
 */
export function Entrada({ list, selected, busy, onChoose, onEnter }: {
  list: Lista | null; selected: string; busy: boolean; onChoose: (id: string) => void; onEnter: (canal: Canal) => void;
}) {
  const sortear = () => {
    const opcoes = list?.imoveis.filter(i => i.imovel_id !== selected)
    if (opcoes?.length) onChoose(opcoes[Math.floor(Math.random() * opcoes.length)].imovel_id)
  }
  return <section className="entrada" aria-labelledby="entrada-titulo">
    <h2 id="entrada-titulo" tabIndex={-1}>Como você quer entrar?</h2>
    <div className="card entrada-imovel">
      <span className="entrada-passo">1</span>
      <div className="entrada-campo"><label htmlFor="imovel-entrada"><Icon name="home" size={17} />Escolha uma Casa Gêmea</label>
        <div><select id="imovel-entrada" aria-label="Imóvel do Teste Comum" value={selected} onChange={e => onChoose(e.target.value)} disabled={!list}>
          {!list && <option>Carregando imóveis...</option>}
          {list?.imoveis.map(i => <option key={i.imovel_id} value={i.imovel_id}>{i.imovel_id.replace('IMO_', '')} · {i.municipio}/{i.uf}</option>)}
        </select><button className="button secondary" disabled={!list || busy} onClick={sortear}><Icon name="shuffle" size={17} />Sortear uma casa</button></div>
      </div>
    </div>
    <div className="entrada-perfis">
      <span className="entrada-passo">2</span>
      <div><p className="entrada-rotulo">Entre como</p>
        <div className="entrada-grid">{CANAIS.map(c => <button key={c.label} className="entrada-perfil" aria-label={c.label} disabled={!list} onClick={() => onEnter(c.label)}>
          <span className="entrada-icone"><Icon name={c.icon} size={22} /></span>
          <strong>{c.label}</strong><small>{c.note}</small><span className="entrada-texto">{c.texto}</span>
          <span className="entrada-cta">Entrar <Icon name="arrow" size={15} /></span>
        </button>)}</div>
      </div>
    </div>
    <p className="small-note entrada-aviso"><Icon name="lock" size={14} />Ambiente de demonstração, sem senha. Cada perfil vê só o seu canal; para mudar, use “Trocar de canal”.</p>
  </section>
}

/** Faixa de abertura no estilo da página do Seguro Residencial da BB Seguros (amarelo, título azul). */
export function Abertura({ onCotar }: { onCotar: () => void }) {
  return <section className="abertura" aria-labelledby="abertura-titulo">
    <div className="abertura-texto">
      <div className="abertura-marca"><img className="abertura-logo-bb" src="/marca-bb.svg" alt="Banco do Brasil" width="34" height="34" /><b>BB Seguros</b></div>
      <h1 id="abertura-titulo">Seguro Residencial</h1>
      <p>Montamos uma cópia da sua casa com o que o banco já sabe, perguntamos só o que muda o resultado e explicamos cada recomendação, inclusive por que não os outros planos.</p>
      <button className="abertura-cta" onClick={onCotar}>Faça sua cotação <Icon name="arrow" size={18} /></button>
    </div>
    <svg className="abertura-arte" viewBox="0 0 500 290" aria-hidden="true">
      <path d="m52 222 201-112 194 112-201 112Z" fill="#FFFFFF" opacity=".6" transform="translate(0,-34)" />
      <path d="m104 162 149-83 140 81-149 84Z" fill="#FFF" stroke="#465EFF" strokeWidth="2.5" />
      <path d="M104 162v67l140 81v-66Z" fill="#EDF0FF" stroke="#465EFF" strokeWidth="2.5" transform="translate(0,-22)" />
      <path d="M244 244v66l149-83v-67Z" fill="#FFF" stroke="#465EFF" strokeWidth="2.5" transform="translate(0,-22)" />
      <path d="m97 144 63-99 147 84-63 98Z" fill="#465EFF" stroke="#2F3FB0" strokeWidth="2.5" />
      <path d="m160 45 156-27 88 126-97-15Z" fill="#7D8DFF" stroke="#2F3FB0" strokeWidth="2.5" />
      <path d="m244 227 63-98 97 15-11 61-149 83Z" fill="#F9F7FF" stroke="#465EFF" strokeWidth="2.5" />
      <path d="m135 179 33 19v35l-33-19Z" fill="#FCFC30" stroke="#2F3FB0" strokeWidth="2.5" />
      <path d="m286 225 32-18v54l-32 18Z" fill="#FCFC30" stroke="#2F3FB0" strokeWidth="2.5" />
      <path d="m345 192 26-15v31l-26 15Z" fill="#FCFC30" stroke="#2F3FB0" strokeWidth="2.5" />
      <path d="M420 40c14 4 26 4 38-2v30c0 22-15 36-38 44-23-8-38-22-38-44V38c12 6 24 6 38 2Z" fill="#2F3FB0" />
      <path d="m408 74 9 9 18-20" stroke="#FCFC30" strokeWidth="5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </section>
}
