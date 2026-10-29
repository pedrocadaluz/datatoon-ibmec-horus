import { Icon } from './Icons'
import { Modal } from './Modal'

const CANAIS: [string, string][] = [
  ['Cliente', 'A casa no topo cresce a cada resposta. Responda as perguntas; no fim, o relatório mostra o plano, os limites e por que não os outros planos, com as dúvidas mais comuns.'],
  ['Gerente', 'Três etapas: o relatório inicial do caso, as perguntas sugeridas com o motivo de cada uma e o resultado para apresentar ao cliente, com relatório para imprimir e envio por e-mail.'],
  ['SAC', 'Três etapas para o atendimento por telefone: abertura com fala pronta, roteiro com respostas prontas e encerramento com resumo para ler, e-mail e registro do atendimento.'],
  ['Agente', 'O mesmo motor chamado por outro sistema: edite a entrada em JSON, execute e veja a saída.'],
]

/** Guia rápido do protótipo. O modo apresentação fica aqui e no atalho P. */
export function ComoUsar({ open, onClose, onApresentar }: { open: boolean; onClose: () => void; onApresentar: () => void }) {
  return <Modal open={open} onClose={onClose} title="Como usar" className="help-sheet">
    <div className="sheet-header"><h2>Como usar</h2><button className="button secondary" onClick={onClose}>Fechar</button></div>
    <div className="sheet-scroll help-body">
      <ol className="help-steps">
        <li><b>Escolha um imóvel</b> no seletor ou toque em “Sortear caso”. “Recomeçar” apaga as respostas daquele imóvel.</li>
        <li><b>Escolha o canal</b>: o mesmo motor e as mesmas respostas aparecem nas quatro visões.</li>
        <li><b>Responda</b> só o que for perguntado. “Não sei” sempre vale: a recomendação segue, com uma faixa maior.</li>
        <li><b>Mude de ideia</b> em “Suas respostas” → “Editar”: o motor refaz a recomendação na hora.</li>
      </ol>
      <dl className="help-canais">{CANAIS.map(([nome, texto]) => <div key={nome}><dt>{nome}</dt><dd>{texto}</dd></div>)}</dl>
      <p className="small-note">Atalhos: P liga o modo apresentação, as setas mudam de etapa e as teclas 1 a 9 respondem a pergunta. A− e A+ mudam o tamanho do texto.</p>
      <p className="small-note">Dados sintéticos. Nenhuma contratação, e-mail ou registro é feito de verdade.</p>
      <button className="button primary" onClick={() => { onClose(); onApresentar() }} aria-label="Modo apresentação"><Icon name="play" size={17} />Iniciar modo apresentação</button>
    </div>
  </Modal>
}
