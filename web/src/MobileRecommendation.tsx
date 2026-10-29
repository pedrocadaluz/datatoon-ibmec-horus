import { useEffect, useRef, useState } from 'react'
import type { Resultado } from './types'
import { planos, reais } from './format'
import { Icon } from './Icons'
import { Modal } from './Modal'
import { Recommendation } from './Recommendation'

export function MobileRecommendation({ data, initial, pending, mobile, client, presentationStep }: {
  data: Resultado; initial: Resultado | null; pending: boolean; mobile: boolean; client?: boolean; presentationStep: number | null;
}) {
  const [open, setOpen] = useState(false)
  const touchStart = useRef<number | null>(null)
  const fire = data.coberturas.find(c => c.cobertura === 'INCENDIO_RAIO_EXPLOSAO_FUMACA')
  useEffect(() => { setOpen(false) }, [data.imovel_id])
  useEffect(() => {
    if (mobile && presentationStep === 2) setOpen(true)
    else if (presentationStep !== 2) setOpen(false)
  }, [mobile, presentationStep])
  useEffect(() => {
    const show = () => setOpen(true)
    window.addEventListener('horus-show-recommendation', show)
    return () => window.removeEventListener('horus-show-recommendation', show)
  }, [])
  if (!mobile) return <Recommendation data={data} initial={initial} pending={pending} />
  const color = data.canal.semaforo
  const signal = client ? { VERDE: 'Pronto', AMARELO: 'Confirmar', VERMELHO: 'Especialista' }[color] : { VERDE: 'Verde', AMARELO: 'Amarelo', VERMELHO: 'Vermelho' }[color]
  return <>
    <button className={`mobile-recommendation-summary signal-${color.toLowerCase()}`} aria-expanded={open} data-testid="resumo-movel" onClick={() => setOpen(true)}
      onTouchStart={e => { touchStart.current = e.touches[0].clientY }} onTouchEnd={e => { if (touchStart.current !== null && touchStart.current - e.changedTouches[0].clientY > 35) setOpen(true); touchStart.current = null }}>
      <span className="sheet-grip" /><span className="mobile-summary-top"><span>Seu plano <b>{planos[data.recomendacao.plano] ?? 'Sem plano'}</b></span><span className="mobile-signal"><i />{signal}<Icon name="arrow" size={16} /></span></span>
      <span className="mobile-summary-bottom">{fire ? <><span>{client ? 'Proteção para incêndio' : `Incêndio · Confiança ${fire.confianca === 'ALTA' ? 'alta' : fire.confianca === 'MEDIA' ? 'média' : 'baixa'}`}</span><strong>{reais(fire.faixa_valor_min)} a {reais(fire.faixa_valor_max)}</strong></> : <span>Veja o motivo e o próximo passo</span>}</span><span className="sr-only">Expandir recomendação</span>
    </button>
    <Modal open={open} onClose={() => setOpen(false)} title="Sua recomendação" className="recommendation-sheet">
      <div className="sheet-header" onTouchStart={e => { touchStart.current = e.touches[0].clientY }} onTouchEnd={e => { if (touchStart.current !== null && e.changedTouches[0].clientY - touchStart.current > 60) setOpen(false); touchStart.current = null }}><span className="sheet-grip" /><div><h2>Sua recomendação</h2><button aria-label="Fechar recomendação" onClick={() => setOpen(false)}>Fechar <span aria-hidden="true">×</span></button></div></div>
      <div className="sheet-scroll"><Recommendation data={data} initial={initial} pending={pending} full={client} /></div>
    </Modal>
  </>
}
