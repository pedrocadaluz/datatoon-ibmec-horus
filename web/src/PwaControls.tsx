import { useEffect, useState } from 'react'
import { Icon } from './Icons'
import { Modal } from './Modal'

interface InstallEvent extends Event { prompt: () => Promise<void>; userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }> }

export function PwaControls() {
  const [prompt, setPrompt] = useState<InstallEvent | null>(null)
  const [iosHelp, setIosHelp] = useState(false)
  const [installed, setInstalled] = useState(() => matchMedia('(display-mode: standalone)').matches || Boolean((navigator as Navigator & { standalone?: boolean }).standalone))
  const [update, setUpdate] = useState<ServiceWorkerRegistration | null>(null)
  const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  useEffect(() => {
    const before = (event: Event) => { event.preventDefault(); setPrompt(event as InstallEvent) }
    const ready = (event: Event) => setUpdate((event as CustomEvent<ServiceWorkerRegistration>).detail)
    const done = () => { setInstalled(true); setPrompt(null) }
    window.addEventListener('beforeinstallprompt', before)
    window.addEventListener('appinstalled', done)
    window.addEventListener('horus-update-ready', ready)
    return () => { window.removeEventListener('beforeinstallprompt', before); window.removeEventListener('appinstalled', done); window.removeEventListener('horus-update-ready', ready) }
  }, [])
  return <>
    {!installed && (prompt || ios) && <button className="install-button" aria-label="Instalar app" onClick={async () => { if (ios) { setIosHelp(true); return } if (prompt) { await prompt.prompt(); await prompt.userChoice; setPrompt(null) } }}><Icon name="download" size={18} /><span>Instalar app</span></button>}
    <Modal open={iosHelp} onClose={() => setIosHelp(false)} title="Instalar no iPhone" className="install-modal"><h2>Sua Casa Gêmea na tela inicial.</h2><p>No Safari, toque em <b>Compartilhar</b> e depois em <b>Adicionar à Tela de Início</b>.</p><p className="small-note">Para o modo offline completo na rede local, abra o endereço HTTPS configurado para a demonstração.</p><button className="button primary" onClick={() => setIosHelp(false)}>Entendi</button></Modal>
    {update && <div className="update-notice" role="status"><span>Nova versão do app pronta.</span><button onClick={() => { window.dispatchEvent(new Event('horus-apply-update')); update.waiting?.postMessage({ type: 'SKIP_WAITING' }); setUpdate(null) }}>Atualizar agora</button><button aria-label="Atualizar mais tarde" onClick={() => setUpdate(null)}>Depois</button><small>Atualizar reinicia as respostas desta sessão.</small></div>}
  </>
}

export function registerShell() {
  if (!import.meta.env.PROD || !('serviceWorker' in navigator) || !window.isSecureContext) return
  let requested = false
  window.addEventListener('horus-apply-update', () => { requested = true })
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (requested) location.reload() })
  const register = () => navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' }).then(reg => {
    const notify = () => { if (reg.waiting && navigator.serviceWorker.controller) window.dispatchEvent(new CustomEvent('horus-update-ready', { detail: reg })) }
    notify()
    reg.addEventListener('updatefound', () => {
      const worker = reg.installing
      worker?.addEventListener('statechange', () => { if (worker.state === 'installed') notify() })
    })
  }).catch(() => { /* A jornada online continua se o navegador bloquear o cache do casco. */ })
  if (document.readyState === 'complete') void register()
  else window.addEventListener('load', () => { void register() }, { once: true })
}
