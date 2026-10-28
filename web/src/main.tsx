import React from 'react'
import ReactDOM from 'react-dom/client'
import '@fontsource/inter/latin-400.css'
import '@fontsource/inter/latin-500.css'
import '@fontsource/inter/latin-600.css'
import '@fontsource/inter/latin-700.css'
import '@fontsource/inter/latin-800.css'
import App from './App'
import './styles.css'
import './mobile.css'
import { registerShell } from './PwaControls'
import { lazy, Suspense } from 'react'

const MobileConnect = lazy(() => import('./MobileConnect'))

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode>{location.pathname === '/celular' ? <Suspense fallback={<p>Preparando acesso no celular...</p>}><MobileConnect /></Suspense> : <App />}</React.StrictMode>)
registerShell()
