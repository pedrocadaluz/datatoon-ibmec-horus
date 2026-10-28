import { useState } from 'react'
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

/**
 * Faixa de abertura no estilo da página do Seguro Residencial da BB Seguros (amarelo, título azul).
 * Sem logotipo oficial: "horus para BB Seguros" em texto. Se a organização liberar o arquivo da marca,
 * basta salvá-lo em web/public/marca-bb.svg que ele aparece no lugar do texto.
 */
export function Abertura({ onCotar }: { onCotar: () => void }) {
  const [marca, setMarca] = useState(true)
  return <section className="abertura" aria-labelledby="abertura-titulo">
    <div className="abertura-texto">
      <div className="abertura-marca"><img src="/horus.svg" alt="" width="34" height="34" /><b>horus</b><span>para</span>
        {marca ? <img className="abertura-logo-bb" src="/marca-bb.svg" alt="BB Seguros" height="28" onError={() => setMarca(false)} /> : <b>BB Seguros</b>}</div>
      <h1 id="abertura-titulo">Seguro Residencial</h1>
      <p className="abertura-lema">Menos perguntas. Mais sentido para a sua proteção.</p>
      <p>Montamos uma cópia da sua casa com o que o banco já sabe, perguntamos só o que muda o resultado e explicamos cada recomendação, inclusive por que não os outros planos.</p>
      <button className="abertura-cta" onClick={onCotar}>Faça sua cotação <Icon name="arrow" size={18} /></button>
    </div>
    <svg className="abertura-arte" viewBox="0 0 320 240" aria-hidden="true">
      <circle cx="160" cy="120" r="108" fill="#FFFFFF" opacity=".55" />
      <path d="M78 122 160 58l82 64Z" fill="#465EFF" stroke="#2F3FB0" strokeWidth="4" strokeLinejoin="round" />
      <rect x="96" y="120" width="128" height="80" rx="4" fill="#FFFFFF" stroke="#2F3FB0" strokeWidth="4" />
      <rect x="146" y="150" width="28" height="50" rx="3" fill="#FCFC30" stroke="#2F3FB0" strokeWidth="4" />
      <rect x="110" y="136" width="26" height="22" rx="3" fill="#FCFC30" stroke="#2F3FB0" strokeWidth="3" />
      <rect x="184" y="136" width="26" height="22" rx="3" fill="#FCFC30" stroke="#2F3FB0" strokeWidth="3" />
      <path d="M232 64c14 4 26 4 38-2v30c0 22-15 36-38 44-23-8-38-22-38-44V62c12 6 24 6 38 2Z" fill="#2F3FB0" />
      <path d="m220 98 9 9 18-20" stroke="#FCFC30" strokeWidth="5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </section>
}
