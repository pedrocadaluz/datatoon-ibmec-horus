import type { Casa, Campo } from './types'
import { confianca, nomes, numero } from './format'
import { origemCliente, valorCliente } from './cliente'
import { Icon } from './Icons'

const selos: Record<string, string> = { OBSERVADO: 'Observado', ESTIMADO: 'Estimado', A_CONFIRMAR: 'A confirmar', CONFIRMADO: 'Confirmado' }
export function Selo({ campo }: { campo: Campo }) {
  return <span className={`data-status status-${campo.selo.toLowerCase()}`}><span>{selos[campo.selo] ?? campo.selo}</span><span className="status-separator">·</span><span>Confiança {confianca[campo.confianca]?.toLowerCase()}</span></span>
}

const CAMPOS = ['tipo_imovel', 'area_m2', 'vinculo', 'conteudo', 'uso_imovel', 'padrao_construtivo', 'material_parede', 'alerta_obra'] as const
const OBRA_PENDENTE = ['REFORMA_MODERADA', 'POSSIVEL_OBRA_RELEVANTE']
const firme = (c: Campo) => c.selo === 'OBSERVADO' || c.selo === 'CONFIRMADO'

/** Quanto da Casa Gêmea já é dado do banco ou confirmado pelo cliente. A declaração conta como mais um dado. */
export function progressoCasa(casa: Casa, aplicadas: string[] = []) {
  const firmes = CAMPOS.filter(c => firme(casa[c])).length + (aplicadas.includes('declaracao_unica') ? 1 : 0)
  return { firmes, total: CAMPOS.length + 1 }
}

// Três tons: dado do banco ou confirmado ganha a cor da marca; estimativa de confiança alta, azul-claro;
// estimativa incerta, cinza. Assim a casa nunca mostra uma estimativa como fato.
const CINZA = { fill: '#EEF0F6', stroke: '#C5CAD9' }
const cor = (c: Campo, fill: string, claro: string, stroke = '#3548CA') =>
  firme(c) ? { fill, stroke } : c.confianca === 'ALTA' ? { fill: claro, stroke: '#9AA8F5' } : CINZA

/** Casa vista de frente que cresce com as respostas. Cada parte é ligada a um dado da Casa Gêmea. */
export function HouseArt({ casa, aplicadas = [], status }: { casa: Casa; aplicadas?: string[]; status?: string }) {
  const { firmes, total } = progressoCasa(casa, aplicadas)
  const escala = 0.82 + 0.18 * firmes / total
  const uso = String(casa.uso_imovel.valor)
  const luz = uso === 'MORADIA_HABITUAL' ? '#FCFC30' : uso === 'ALUGADO_A_TERCEIROS' ? '#FFF6A8' : '#D5D9E6'
  const obra = (OBRA_PENDENTE.includes(String(casa.alerta_obra.valor)) && casa.alerta_obra.selo !== 'CONFIRMADO') || casa.alerta_obra.valor === 'OBRA_ESTRUTURAL'
  const area = firme(casa.area_m2) ? `${numero(Number(casa.area_m2.valor))} m²` : `${numero(casa.area_faixa_m2[0])} a ${numero(casa.area_faixa_m2[1])} m²`
  const paredes = cor(casa.material_parede, '#FFFFFF', '#F4F6FF')
  const telhado = cor(casa.tipo_imovel, '#5A6FFF', '#C9D1FF')
  const porta = cor(casa.vinculo, '#FCFC30', '#FFFBC8')
  const janela = firme(casa.uso_imovel) ? { fill: luz, stroke: '#3548CA' } : cor(casa.uso_imovel, luz, '#F7F8E8')
  return <svg className="house-art" viewBox="0 0 600 280" role="img" data-progresso={`${firmes}/${total}`}
    aria-label={`Ilustração da sua Casa Gêmea, com ${firmes} de ${total} dados confirmados. Cores mais claras e cinza indicam estimativas. Não representa a planta real do imóvel.`}>
    <rect x="40" y="236" width="520" height="14" rx="7" fill="#E6E9F7" />
    <g className={`house-grow ${status === 'RECOMENDACAO_CONFIRMADA' ? 'complete' : ''}`} style={{ transform: `scale(${escala})` }}>
      <g key={`paredes-${paredes.fill}`} className="part"><rect x="190" y="118" width="220" height="118" rx="4" {...paredes} strokeWidth="3" /></g>
      <g key={`telhado-${telhado.fill}`} className="part"><path d="M168 124 300 42l132 82Z" {...telhado} strokeWidth="3" strokeLinejoin="round" /></g>
      <g key={`porta-${porta.fill}`} className="part"><rect x="278" y="168" width="44" height="68" rx="3" {...porta} strokeWidth="3" /><circle cx="312" cy="204" r="3" fill={porta.stroke} /></g>
      <g key={`janelas-${janela.fill}`} className="part">
        <rect x="212" y="146" width="48" height="42" rx="3" {...janela} strokeWidth="3" /><path d="M236 146v42M212 167h48" stroke={janela.stroke} strokeWidth="2" />
        <rect x="340" y="146" width="48" height="42" rx="3" {...janela} strokeWidth="3" /><path d="M364 146v42M340 167h48" stroke={janela.stroke} strokeWidth="2" />
      </g>
      {casa.conteudo.selo === 'CONFIRMADO' && <g className="part"><rect x="350" y="158" width="28" height="18" rx="2" fill="#3548CA" /><path d="M358 180h12" stroke="#3548CA" strokeWidth="3" /></g>}
      {aplicadas.includes('declaracao_unica') && <g className="part house-seal"><circle cx="300" cy="96" r="20" fill="#FCFC30" stroke="#3548CA" strokeWidth="3" /><path d="m290 96 7 7 13-14" stroke="#3548CA" strokeWidth="3.5" fill="none" strokeLinecap="round" /></g>}
    </g>
    {obra && <g className="part scaffold"><path d="m470 236 16-58 16 58Z" fill="#F29D38" stroke="#805300" strokeWidth="2" /><path d="M476 214h20M481 196h10" stroke="#FFFFFF" strokeWidth="4" /></g>}
    <g className="area-label"><path d="M190 262h220M190 256v12M410 256v12" stroke={firme(casa.area_m2) ? '#3548CA' : '#C5CAD9'} strokeWidth="2" />
      <rect x="252" y="252" width="96" height="20" rx="10" fill="#FFFFFF" /><text x="300" y="267" textAnchor="middle" fontSize="14" fontWeight="600" fill={firme(casa.area_m2) ? '#3548CA' : '#5B6175'}>{area}</text></g>
  </svg>
}

/** Os oito dados da Casa Gêmea em linguagem do cliente: o valor e de onde ele veio. */
export function HouseFacts({ casa, imovel }: { casa: Casa; imovel: string }) {
  return <ul className="house-facts" key={imovel}>{CAMPOS.map(chave => {
    const campo = casa[chave]
    return <li key={chave} className={firme(campo) ? 'firm' : 'estimated'}>
      <span className="field-label">{nomes[chave]}</span><strong>{valorCliente(chave, campo, casa)}</strong><span className="fact-origin">{origemCliente(chave, campo, casa)}</span>
    </li>
  })}</ul>
}

/** Cartão da Casa Gêmea usado no celular, dentro do painel recolhível. */
export function House({ casa, imovel }: { casa: Casa; location?: string; imovel: string; aplicadas?: string[]; status?: string }) {
  return <section className="card twin" aria-labelledby="twin-heading">
    <div className="section-heading"><div><span className="eyebrow">A sua Casa Gêmea</span><h2 id="twin-heading">O que já sabemos da sua casa</h2></div></div>
    <HouseFacts casa={casa} imovel={imovel} />
      </section>
}
