import { useEffect } from 'react'

const BORDA = 24       // px a partir da borda esquerda onde o gesto pode começar
const DISTANCIA = 90   // px arrastados para a direita para voltar

/**
 * Arrastar da borda esquerda para a direita volta uma tela (o mesmo que o botão Voltar do navegador).
 * Só liga onde o sistema não tem esse gesto: app instalado (no iPhone, o iOS não oferece) e a moldura
 * de celular do Maestri (iframe, com o mouse). No Safari e no Android o gesto do sistema já faz isso.
 */
export function useGestoVoltar() {
  useEffect(() => {
    const instalado = matchMedia('(display-mode: standalone)').matches || (navigator as Navigator & { standalone?: boolean }).standalone === true
    const naMoldura = window.self !== window.top
    if (!instalado && !naMoldura) return

    const seta = document.createElement('div')
    seta.className = 'gesto-voltar'
    seta.setAttribute('aria-hidden', 'true')
    seta.textContent = '‹'
    document.body.appendChild(seta)

    let inicio: { x: number; y: number } | null = null
    const mostrar = (dx: number) => {
      const p = Math.max(0, Math.min(1, dx / DISTANCIA))
      seta.style.opacity = String(p)
      seta.style.transform = `translate(${-40 + 52 * p}px, -50%)`
      seta.classList.toggle('pronto', p >= 1)
    }
    const comecar = (x: number, y: number) => { if (x <= BORDA) inicio = { x, y } }
    const mover = (x: number, y: number) => {
      if (!inicio) return
      const dx = x - inicio.x, dy = Math.abs(y - inicio.y)
      if (dy > 60 && dy > dx) { inicio = null; mostrar(0); return }  // virou rolagem vertical
      mostrar(dx)
    }
    const soltar = (x: number, y: number) => {
      if (!inicio) return
      const dx = x - inicio.x, dy = Math.abs(y - inicio.y)
      inicio = null
      mostrar(0)
      if (dx >= DISTANCIA && dx > dy * 1.5) window.history.back()
    }
    const cancelar = () => { inicio = null; mostrar(0) }

    // Dedo: eventos de toque (o navegador não os cancela ao rolar). Mouse: a moldura do Maestri.
    const t = (f: (x: number, y: number) => void) => (e: TouchEvent) => { const p = e.changedTouches[0]; if (p) f(p.clientX, p.clientY) }
    const m = (f: (x: number, y: number) => void) => (e: MouseEvent) => { if (e.button === 0) f(e.clientX, e.clientY) }
    const ouvintes: [string, EventListener][] = [
      ['touchstart', t(comecar) as EventListener], ['touchmove', t(mover) as EventListener], ['touchend', t(soltar) as EventListener], ['touchcancel', cancelar],
      ['mousedown', m(comecar) as EventListener], ['mousemove', (e => mover((e as MouseEvent).clientX, (e as MouseEvent).clientY)) as EventListener], ['mouseup', m(soltar) as EventListener],
    ]
    ouvintes.forEach(([tipo, f]) => addEventListener(tipo, f, { passive: true }))
    return () => {
      ouvintes.forEach(([tipo, f]) => removeEventListener(tipo, f))
      seta.remove()
    }
  }, [])
}
