import type { Lista } from './types'
import { Icon } from './Icons'
import { Modal } from './Modal'

interface Props { list: Lista | null; selected: string; busy: boolean; hasData: boolean; mobile: boolean; open: boolean; onClose: () => void; onChoose: (id: string) => void; onReset: () => void }
export function CasePicker({ list, selected, busy, hasData, mobile, open, onClose, onChoose, onReset }: Props) {
  const contents = <section className="case-toolbar" aria-label="Seleção do imóvel"><div className="case-selector"><label htmlFor="imovel"><Icon name="home" size={17} />Escolha uma Casa Gêmea</label><select id="imovel" aria-label="Imóvel do Teste Comum" value={selected} onChange={e => onChoose(e.target.value)} disabled={!list}>{!list && <option>Carregando imóveis...</option>}{list?.imoveis.map(i => <option key={i.imovel_id} value={i.imovel_id}>{i.imovel_id.replace('IMO_', '')} · {i.municipio}/{i.uf}</option>)}</select></div><button className="text-button random" disabled={!list || busy} onClick={() => { const choices = list?.imoveis.filter(i => i.imovel_id !== selected); if (choices?.length) onChoose(choices[Math.floor(Math.random() * choices.length)].imovel_id) }}><Icon name="shuffle" size={17} />Sortear caso</button><button className="text-button reset" disabled={busy || !hasData} onClick={() => { onReset(); onClose() }}><Icon name="reset" size={16} />Recomeçar</button></section>
  if (!mobile) return contents
  return <Modal open={open} onClose={onClose} title="Escolher imóvel" className="case-sheet"><div className="sheet-header"><div><h2>Escolha sua Casa Gêmea</h2><button aria-label="Fechar seleção de imóvel" onClick={onClose}>Fechar ×</button></div></div>{contents}<button className="button primary case-confirm" onClick={onClose}>Continuar com este imóvel <Icon name="arrow" size={17} /></button></Modal>
}
