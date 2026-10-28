import type { Casa, Campo } from './types'
import { confianca, nomes, valorCampo } from './format'
import { Icon } from './Icons'

const selos: Record<string, string> = { OBSERVADO: 'Observado', ESTIMADO: 'Estimado', A_CONFIRMAR: 'A confirmar', CONFIRMADO: 'Confirmado' }
export function Selo({ campo }: { campo: Campo }) {
  return <span className={`data-status status-${campo.selo.toLowerCase()}`}><span>{selos[campo.selo] ?? campo.selo}</span><span className="status-separator">·</span><span>Confiança {confianca[campo.confianca]?.toLowerCase()}</span></span>
}

export function House({ casa, location, imovel }: { casa: Casa; location: string; imovel: string }) {
  const confirmados = Object.values(casa).filter(c => !Array.isArray(c) && c.selo === 'CONFIRMADO').length
  const field = (chave: string, i: number) => {
    const campo = casa[chave as keyof Casa] as Campo
    return <details className="field" key={chave} style={{ animationDelay: `${i * 35}ms` }}>
      <summary><span className="field-label">{nomes[chave]}</span><strong>{valorCampo(chave, campo, casa)}</strong><Selo campo={campo} /></summary>
      <p className="evidence">{campo.evidencia.replace(/[\u2013\u2014]/g, ', ')}</p>
    </details>
  }
  return <section className="card twin" aria-labelledby="twin-heading">
    <div className="section-heading"><div><span className="eyebrow">01 / A sua Casa Gêmea</span><h2 id="twin-heading">Sua casa já conta uma história.</h2></div><span className="live-pill"><i />Motor conectado</span></div>
    <div className="house-scene">
      <div className="scene-grid" />
      <div className="scene-location"><Icon name="pin" size={15} /><span>{location}</span></div>
      <svg className="house-art" viewBox="0 0 500 290" role="img" aria-label="Ilustração conceitual da Casa Gêmea. A geometria não representa uma planta real do imóvel.">
        <defs><pattern id="wall-lines" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M0 10 10 0" stroke="#DDE4FC" strokeWidth=".8" /></pattern></defs>
        <path d="m52 222 201-112 194 112-201 112Z" fill="#ECEEFD" transform="translate(0,-34)" />
        <path d="m104 162 149-83 140 81-149 84Z" fill="#FFF" stroke="#5A6FFF" strokeWidth="2" />
        <path d="M104 162v67l140 81v-66Z" fill="#EDF0FF" stroke="#5A6FFF" strokeWidth="2" transform="translate(0,-22)" />
        <path d="M244 244v66l149-83v-67Z" fill="#FFF" stroke="#5A6FFF" strokeWidth="2" transform="translate(0,-22)" />
        <path d="m97 144 63-99 147 84-63 98Z" fill="#5A6FFF" stroke="#4355CE" strokeWidth="2" />
        <path d="m160 45 156-27 88 126-97-15Z" fill="#7D8DFF" stroke="#4355CE" strokeWidth="2" />
        <path d="m244 227 63-98 97 15-11 61-149 83Z" fill="#F9F7FF" stroke="#5A6FFF" strokeWidth="2" />
        <path d="m306 132-36 56 73-41Z" fill="url(#wall-lines)" />
        <path d="m135 179 33 19v35l-33-19Z" fill="#FCFC30" stroke="#4355CE" strokeWidth="2" />
        <path d="m151 188 0 36m-16-27 33 19" stroke="#4355CE" strokeWidth="1.5" />
        <path d="m286 225 32-18v54l-32 18Z" fill={confirmados > 0 ? '#FCFC30' : '#DDE4FC'} stroke="#5A6FFF" strokeWidth="2" className="house-door" />
        <path d="m345 192 26-15v31l-26 15Z" fill="#FCFC30" stroke="#4355CE" strokeWidth="2" />
        <path d="m358 184 0 31" stroke="#4355CE" strokeWidth="1.5" />
        <path d="m79 238 21 12m297-4 22-13" stroke="#5A6FFF" strokeWidth="2" />
        <circle cx="82" cy="132" r="5" fill="#5A6FFF" /><path d="M82 132h-36v-31" stroke="#5A6FFF" strokeDasharray="3 3" fill="none" />
        <circle cx="406" cy="197" r="5" fill="#5A6FFF" /><path d="M406 197h42v-39" stroke="#5A6FFF" strokeDasharray="3 3" fill="none" />
      </svg>
      <div className="scene-note"><Icon name="spark" size={14} />Dados que viram proteção</div>
      <span className="scene-caption">Visual conceitual do imóvel</span>
    </div>
    <div className="house-fields" key={imovel}>
      {['tipo_imovel', 'area_m2', 'vinculo', 'conteudo'].map(field)}
    </div>
    <details className="more-house-fields"><summary>Ver os outros dados da casa <span>4</span></summary><div className="house-fields">{['uso_imovel', 'padrao_construtivo', 'material_parede', 'alerta_obra'].map(field)}</div></details>
    <div className="twin-foot"><Icon name="info" size={15} /><span>Toque em um dado para ver sua origem. Estimativa sempre vem com selo e confiança.</span></div>
  </section>
}
