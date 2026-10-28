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
    <h2 id="entrada-titulo">Como você quer entrar?</h2>
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
