import sharp from 'sharp'
import { mkdir, writeFile } from 'node:fs/promises'

const icon = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" fill="#5A6FFF"/><path d="M128 315V202l128-85 128 85v113l-128 80Z" fill="none" stroke="#FCFC30" stroke-width="22" stroke-linejoin="round"/><path d="m192 264 64-43 64 43-64 43Z" fill="#FCFC30"/><path d="M192 338v-35m128 35v-35" fill="none" stroke="#FCFC30" stroke-width="14" stroke-linecap="round"/></svg>`
await mkdir(new URL('../public/icons/', import.meta.url), { recursive: true })
await writeFile(new URL('../public/icons/horus-icon.svg', import.meta.url), icon)
for (const [file, size] of [['icon-192.png', 192], ['icon-512.png', 512], ['maskable-512.png', 512], ['apple-touch-icon.png', 180]]) {
  await sharp(Buffer.from(icon)).resize(size, size).png().toFile(new URL(`../public/icons/${file}`, import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'))
}
