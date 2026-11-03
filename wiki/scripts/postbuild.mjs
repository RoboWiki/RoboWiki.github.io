// VitePress 会把 404.md 也放进 sitemap，但 404 页自带 noindex。
// 这里在构建后删掉它；CI/本地 npm run build 都会走到。
import { readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const dist = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'docs', '.vitepress', 'dist')
const file = path.join(dist, 'sitemap.xml')

try {
  const before = readFileSync(file, 'utf8')
  const after = before.replace(
    /<url>\s*<loc>[^<]*\/404\.html<\/loc>\s*<\/url>\s*/g, '')
  if (before !== after) writeFileSync(file, after)
  const urls = (after.match(/<url>/g) || []).length
  console.log(`[postbuild] sitemap ok（${urls} 条，已排除 404）`)
} catch (err) {
  console.warn(`[postbuild] sitemap 跳过：${err.message}`)
}
