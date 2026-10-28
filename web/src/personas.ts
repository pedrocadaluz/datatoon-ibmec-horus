import type { Persona, ResultadoPersonalizado } from './types'
import { recomendar } from './api'

export const personas: Persona[] = [
  { id: 'IMO_CASO_00008_01', nome: 'Marina', frase: 'Inquilina de apartamento, com família e pet, usa muito o app.' },
  { id: 'IMO_CASO_00016_01', nome: 'Rafael', frase: 'Dono de casa financiada, muitos eletrônicos, obra recente.' },
  { id: 'IMO_CASO_00059_01', nome: 'Helena', frase: 'Apartamento de temporada que fica vazio, quase não usa o app.' },
]
export const chaveAdicional = (id: string) => ({ EQUIPAMENTOS_PORTATEIS: 'equipamentos', BICICLETA: 'bicicleta', DESOCUPACAO_TEMPORARIA: 'desocupacao' } as Record<string, string>)[id] ?? (id.includes('MEI') ? 'mei' : id.toLowerCase())
export const buscarPersona = (id: string, respostas: Record<string, string | number> = {}, signal?: AbortSignal) =>
  recomendar(id, respostas, signal) as Promise<ResultadoPersonalizado>
export const jornadaRotulo = { EXPRESS: 'Express', GUIADA: 'Guiada', HUMANA: 'Com especialista' } as const
