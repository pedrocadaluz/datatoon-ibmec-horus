import { useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { buscar } from './api'

export default function MobileConnect() {
  const [urls, setUrls] = useState<string[]>([])
  const [url, setUrl] = useState(location.origin)
  const [image, setImage] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    const ctrl = new AbortController()
    buscar<{ ips: string[] }>('/rede', { signal: ctrl.signal }).then(data => {
      const candidates = data.ips.map(ip => `${location.protocol}//${ip}:${location.port || (location.protocol === 'https:' ? '443' : '80')}`)
      const host = ['localhost', '127.0.0.1', '[::1]'].includes(location.hostname) ? candidates[0] ?? location.origin : location.origin
      setUrls([...new Set([host, ...candidates])]); setUrl(host)
    }).catch(() => { if (!ctrl.signal.aborted) setError('Não foi possível identificar a rede. Abra esta página pelo IP local impresso no terminal.') })
    return () => ctrl.abort()
  }, [])
  useEffect(() => { let active = true; QRCode.toDataURL(url, { width: 560, margin: 2, color: { dark: '#182449', light: '#FFFFFF' } }).then(value => { if (active) setImage(value) }); return () => { active = false } }, [url])
  return <main className="connect-page"><a href="/" className="brand"><img src="/horus.svg" width="40" height="40" alt="" /><span>horus<small>Casa Gêmea</small></span></a><h1>Da sua tela<br />para o seu celular.</h1><p>Conecte o telefone à mesma rede Wi-Fi deste computador e aponte a câmera para o QR code.</p><section className="card"><label htmlFor="local-address">Endereço nesta rede</label><select id="local-address" value={url} onChange={e => setUrl(e.target.value)}>{[...new Set([url, ...urls])].map(value => <option key={value}>{value}</option>)}</select>{image && <img className="connect-qr" src={image} alt={`QR code para abrir ${url}`} width="280" height="280" />}<a className="connect-url" href={url}>{url}</a>{error && <p role="alert">{error}</p>}</section><ol><li>Abra o endereço no celular. O computador precisa continuar ligado com a demonstração aberta.</li><li>No Android, use “Instalar app” quando o navegador oferecer.</li><li>No iPhone, abra no Safari: Compartilhar, Adicionar à Tela de Início.</li></ol><div className="connect-note"><p>{location.protocol === 'https:' ? 'Este endereço usa HTTPS. O telefone também precisa confiar no certificado local configurado.' : 'Em HTTP, a jornada funciona no navegador. Para instalar com modo offline completo no telefone, use o endereço HTTPS com certificado local confiável descrito no README.'}</p><p>O QR é gerado neste computador. As consultas seguem pela rede local.</p></div><a className="button secondary" href="/">Voltar à Casa Gêmea</a></main>
}
