import type { Respostas, Resultado } from './types'

export async function buscar<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try { response = await fetch(`/api${path}`, init) }
  catch (error) {
    if (init?.signal?.aborted) throw error
    throw new Error('Não conseguimos conectar à API. Confira se ela está em execução e tente novamente.')
  }
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : 'Não conseguimos consultar o motor. Confira se a API está em execução e tente de novo.')
  return body as T
}
export const recomendar = (imovel: string, respostas: Respostas, signal?: AbortSignal) => buscar<Resultado>('/recomendar', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ versao_contrato: '1.0', imovel_id: imovel, respostas }), signal,
})
