import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import { shellPlugin } from './pwa-build.ts'

const https = process.env.HORUS_HTTPS_CERT && process.env.HORUS_HTTPS_KEY ? {
  cert: readFileSync(process.env.HORUS_HTTPS_CERT), key: readFileSync(process.env.HORUS_HTTPS_KEY),
} : undefined
const api = `http://127.0.0.1:${process.env.HORUS_API_PORT ?? '8000'}`

export default defineConfig({
  plugins: [react(), shellPlugin()],
  server: {
    host: '0.0.0.0', port: 5173, strictPort: true, https,
    proxy: { '/api': api },
  },
  preview: { host: '0.0.0.0', port: 4173, strictPort: true, https, proxy: { '/api': api } },
})
