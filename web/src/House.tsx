import type { Casa, Campo } from './types'
import { confianca, numero } from './format'
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
const CINZA = { fill: '#E9ECFB', stroke: '#A9B4EE' }
const cor = (c: Campo, fill: string, claro: string, stroke = '#3548CA') =>
  firme(c) ? { fill, stroke } : c.confianca === 'ALTA' ? { fill: claro, stroke: '#7F90F2' } : CINZA

// Prédio isométrico: a quina da frente fica em (250, 262); cada face tem 100 de largura e 140 de altura.
// (lado, u, v): lado -1 é a face esquerda e 1 a direita; u vai da quina à ponta e v da base ao topo (0 a 1).
const ponto = (lado: -1 | 1, u: number, v: number) => `${250 + lado * 100 * u} ${262 - 55 * u - 140 * v}`
const quadro = (lado: -1 | 1, u0: number, u1: number, v0: number, v1: number) =>
  `M${ponto(lado, u0, v0)}L${ponto(lado, u1, v0)}L${ponto(lado, u1, v1)}L${ponto(lado, u0, v1)}Z`
const COLUNAS: [number, number][] = [[0.11, 0.29], [0.41, 0.59], [0.71, 0.89]]
const ANDARES = 5
const ANDAR_CLIENTE = 2
const JANELAS = ([-1, 1] as const).flatMap(lado => Array.from({ length: ANDARES }, (_, andar) => COLUNAS.map(([u0, u1], c) => ({ lado, andar, c, u0, u1 }))).flat())
  .filter(j => !(j.lado === 1 && j.andar === 0 && j.c === 1))
const janelaPath = (lado: -1 | 1, andar: number, u0: number, u1: number) => quadro(lado, u0, u1, andar / ANDARES + 0.055, andar / ANDARES + 0.15)

/** Casa (em perspectiva) ou prédio que cresce com as respostas. Cada parte é ligada a um dado da Casa Gêmea. */
export function HouseArt({ casa, aplicadas = [], status }: { casa: Casa; aplicadas?: string[]; status?: string }) {
  const { firmes, total } = progressoCasa(casa, aplicadas)
  const escala = 0.82 + 0.18 * firmes / total
  const uso = String(casa.uso_imovel.valor)
  const luz = uso === 'MORADIA_HABITUAL' ? '#FCFC30' : uso === 'ALUGADO_A_TERCEIROS' ? '#FFF6A8' : '#D5D9E6'
  const obra = (OBRA_PENDENTE.includes(String(casa.alerta_obra.valor)) && casa.alerta_obra.selo !== 'CONFIRMADO') || casa.alerta_obra.valor === 'OBRA_ESTRUTURAL'
  const area = firme(casa.area_m2) ? `${numero(Number(casa.area_m2.valor))} m²` : `${numero(casa.area_faixa_m2[0])} a ${numero(casa.area_faixa_m2[1])} m²`
  const paredes = cor(casa.material_parede, '#FFFFFF', '#F4F6FF')
  const telhado = cor(casa.tipo_imovel, '#465EFF', '#C9D1FF')
  const telhado2 = firme(casa.tipo_imovel) ? '#7D8DFF' : casa.tipo_imovel.confianca === 'ALTA' ? '#DCE1FF' : '#F1F3FD'
  const porta = cor(casa.vinculo, '#FCFC30', '#FFFBC8')
  const janela = firme(casa.uso_imovel) ? { fill: luz, stroke: '#3548CA' } : cor(casa.uso_imovel, luz, '#F7F8E8')
  const apartamento = casa.tipo_imovel.valor === 'APARTAMENTO'
  return <svg className="house-art" viewBox="0 0 600 280" role="img" data-progresso={`${firmes}/${total}`} data-tipo={apartamento ? 'apartamento' : 'casa'}
    aria-label={`Ilustração da sua Casa Gêmea (${apartamento ? 'apartamento' : 'casa'}). Cores mais claras e cinza indicam estimativas. Não representa a planta real do imóvel.`}>
    {apartamento ? <g className={`house-grow ${status === 'RECOMENDACAO_CONFIRMADA' ? 'complete' : ''}`} style={{ transform: `scale(${escala})` }}>
      {/* Prédio em perspectiva (desenho do projeto); o andar do cliente fica destacado. Coordenadas do desenho original 500 × 290. */}
      <g transform="translate(75 6) scale(.9)">
        <path d="m110 207 140-77 140 77-140 77Z" fill={firme(casa.area_m2) ? '#DDE4FC' : '#EEF0F6'} />
        <g key={`predio-${paredes.fill}`} className="part">
          <path d={quadro(-1, 0, 1, 0, 1)} fill={firme(casa.material_parede) ? '#EDF0FF' : paredes.fill} stroke={paredes.stroke} strokeWidth="2" />
          <path d={quadro(1, 0, 1, 0, 1)} {...paredes} strokeWidth="2" />
        </g>
        <g key={`topo-${telhado.fill}`} className="part">
          <path d="M250 122 150 67 250 12 350 67Z" fill={telhado2} stroke={telhado.stroke} strokeWidth="2" />
          <path d="m228 70 22-12 22 12-22 12Z" {...telhado} strokeWidth="1.5" />
        </g>
        {Array.from({ length: ANDARES - 1 }, (_, i) => (i + 1) / ANDARES).map(v => <g key={v} stroke="#DDE4FC" strokeWidth="1.2">
          <path d={`M${ponto(-1, 0, v)}L${ponto(-1, 1, v)}`} /><path d={`M${ponto(1, 0, v)}L${ponto(1, 1, v)}`} />
        </g>)}
        {([-1, 1] as const).map(lado => <path key={`faixa${lado}`} d={quadro(lado, 0.03, 0.97, ANDAR_CLIENTE / ANDARES + 0.02, (ANDAR_CLIENTE + 1) / ANDARES - 0.02)} fill="#E3E8FF" stroke="#465EFF" strokeWidth="1.5" strokeDasharray="5 4" />)}
        {JANELAS.filter(j => j.andar !== ANDAR_CLIENTE).map(({ lado, andar, c, u0, u1 }) => <path key={`${lado}-${andar}-${c}`} d={janelaPath(lado, andar, u0, u1)} fill="#E8EBF5" stroke="#C5CAD9" strokeWidth="1.5" />)}
        <g key={`janelas-${janela.fill}`} className="part">{JANELAS.filter(j => j.andar === ANDAR_CLIENTE).map(({ lado, andar, c, u0, u1 }) => <path key={`${lado}-${c}`} d={janelaPath(lado, andar, u0, u1)} {...janela} strokeWidth="2" />)}</g>
        <path d={`M${ponto(1, 1, (ANDAR_CLIENTE + 0.1) / ANDARES)}h34`} stroke="#3548CA" strokeWidth="2" />
        <text x="388" y={Number(ponto(1, 1, (ANDAR_CLIENTE + 0.1) / ANDARES).split(' ')[1]) + 5} fontSize="15" fontWeight="600" fill="#2F3FB0">seu apartamento</text>
        {casa.conteudo.selo === 'CONFIRMADO' && <g className="part"><path d={quadro(-1, 0.15, 0.25, (ANDAR_CLIENTE + 0.07) / ANDARES, (ANDAR_CLIENTE + 0.13) / ANDARES)} fill="#3548CA" /></g>}
        <g key={`porta-${porta.fill}`} className="part"><path d={quadro(1, 0.38, 0.62, 0, 0.17)} {...porta} strokeWidth="2" /></g>
        {aplicadas.includes('declaracao_unica') && <g className="part house-seal"><circle cx="372" cy="34" r="22" fill="#FCFC30" stroke="#3548CA" strokeWidth="3" /><path d="m361 34 8 8 14-15" stroke="#3548CA" strokeWidth="3.5" fill="none" strokeLinecap="round" /></g>}
      </g>
    </g> : <g className={`house-grow ${status === 'RECOMENDACAO_CONFIRMADA' ? 'complete' : ''}`} style={{ transform: `scale(${escala})` }}>
      {/* Casa em perspectiva (desenho do projeto), com cada parte ligada a um dado. Coordenadas do desenho original 500 × 290. */}
      <g transform="translate(75 6) scale(.9)">
        <defs><pattern id="wall-lines" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M0 10 10 0" stroke="#DDE4FC" strokeWidth=".8" /></pattern></defs>
        <path d="m52 222 201-112 194 112-201 112Z" fill={firme(casa.area_m2) ? '#DDE4FC' : '#EEF0F6'} stroke="#C9D1F7" strokeWidth="1.5" transform="translate(0,-34)" />
        <ellipse cx="250" cy="250" rx="150" ry="34" fill="#2F3FB0" opacity=".08" />
        <path d="m292 276 26-14 40 22-26 14Z" fill="#EFE6C8" stroke="#D8CC9F" strokeWidth="1.2" />
        <g aria-hidden="true"><path d="M86 196v-22" stroke="#7A5530" strokeWidth="5" strokeLinecap="round" /><circle cx="86" cy="160" r="20" fill="#3BAA6B" stroke="#17643F" strokeWidth="2" /><circle cx="74" cy="168" r="12" fill="#48B97A" stroke="#17643F" strokeWidth="2" /><circle cx="99" cy="166" r="11" fill="#2F9A5D" stroke="#17643F" strokeWidth="2" /></g>
        <g aria-hidden="true"><ellipse cx="412" cy="196" rx="20" ry="11" fill="#3BAA6B" stroke="#17643F" strokeWidth="2" /><ellipse cx="428" cy="200" rx="12" ry="8" fill="#48B97A" stroke="#17643F" strokeWidth="2" /></g>
        <g key={`paredes-${paredes.fill}`} className="part">
          <path d="m104 162 149-83 140 81-149 84Z" {...paredes} strokeWidth="2.4" />
          <path d="M104 162v67l140 81v-66Z" fill={firme(casa.material_parede) ? '#EDF0FF' : paredes.fill} stroke={paredes.stroke} strokeWidth="2" transform="translate(0,-22)" />
          <path d="M244 244v66l149-83v-67Z" {...paredes} strokeWidth="2" transform="translate(0,-22)" />
          <path d="m244 227 63-98 97 15-11 61-149 83Z" fill={firme(casa.material_parede) ? '#F9F7FF' : paredes.fill} stroke={paredes.stroke} strokeWidth="2" />
          <path d="m306 132-36 56 73-41Z" fill="url(#wall-lines)" />
        </g>
        <g key={`telhado-${telhado.fill}`} className="part">
          <path d="m97 144 63-99 147 84-63 98Z" {...telhado} strokeWidth="2" />
          <path d="m160 45 156-27 88 126-97-15Z" fill={telhado2} stroke={telhado.stroke} strokeWidth="2" />
          <g stroke={telhado.stroke} strokeWidth="1.2" opacity=".35">{[0.25, 0.5, 0.75].map(t => <path key={t} d={`M${160 - 63 * t} ${45 + 99 * t}L${307 - 63 * t} ${129 + 98 * t}`} />)}</g>
          <path d="m280 50 0-30 18-3 0 30Z" fill={telhado.fill} stroke={telhado.stroke} strokeWidth="2" /><path d="m298 47 0-30 11 6 0 29Z" fill={telhado2} stroke={telhado.stroke} strokeWidth="2" /><path d="m280 20 18-3 11 6-18 3Z" fill="#2F3FB0" />
        </g>
        <g key={`janelas-${janela.fill}`} className="part">
          <path d="m135 179 33 19v35l-33-19Z" {...janela} strokeWidth="2" />
          <path d="m151 188 0 36m-16-27 33 19" stroke={janela.stroke} strokeWidth="1.5" />
          <path d="m345 192 26-15v31l-26 15Z" {...janela} strokeWidth="2" />
          <path d="m358 184 0 31m-13-8 26-15" stroke={janela.stroke} strokeWidth="1.5" />
        </g>
        {casa.conteudo.selo === 'CONFIRMADO' && <g className="part"><path d="m140 204 20 11v10l-20-11Z" fill="#3548CA" /></g>}
        <g key={`porta-${porta.fill}`} className="part"><path d="m286 225 32-18v54l-32 18Z" {...porta} strokeWidth="2" /><circle cx="311" cy="241" r="2.6" fill={porta.stroke} /></g>
        {aplicadas.includes('declaracao_unica') && <g className="part house-seal"><circle cx="440" cy="52" r="22" fill="#FCFC30" stroke="#3548CA" strokeWidth="3" /><path d="m429 52 8 8 14-15" stroke="#3548CA" strokeWidth="3.5" fill="none" strokeLinecap="round" /></g>}
      </g>
    </g>}
    {obra && <g className="part scaffold"><path d="m470 236 16-58 16 58Z" fill="#F29D38" stroke="#805300" strokeWidth="2" /><path d="M476 214h20M481 196h10" stroke="#FFFFFF" strokeWidth="4" /></g>}
    <g className="area-label">
      <rect x="252" y="252" width="96" height="20" rx="10" fill="#FFFFFF" /><text x="300" y="267" textAnchor="middle" fontSize="14" fontWeight="600" fill={firme(casa.area_m2) ? '#3548CA' : '#5B6175'}>{area}</text></g>
  </svg>
}
