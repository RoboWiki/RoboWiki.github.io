import { fileURLToPath } from 'node:url'
import { defineConfig } from 'astro/config'
import react from '@astrojs/react'
import sitemap from '@astrojs/sitemap'
import tailwindcss from '@tailwindcss/vite'

/**
 * 部署根路径由环境变量控制，默认部署在域名根（GitHub Pages + 自定义域 / 用户站点）。
 * 若挂到项目页（https://<user>.github.io/<repo>/），构建时传 BASE_PATH=/<repo> 即可。
 * 例：BASE_PATH=/robowiki pnpm --filter @robowiki/web build
 */
function resolveBasePath() {
  const raw = (process.env.BASE_PATH ?? '').trim()
  if (!raw || raw === '/') return '/'
  // 只接受 URL 路径片段：/repo 或 /a/b。像 C:\repo 这种值直接拒绝，
  // 否则会被当成 base 塞进 sitemap，生成带盘符的死链。
  if (raw.includes(':') || raw.includes('\\')) {
    console.warn(`[astro.config] BASE_PATH 不是合法 URL 路径，已忽略：${raw}`)
    return '/'
  }
  const withLeadingSlash = raw.startsWith('/') ? raw : `/${raw}`
  return withLeadingSlash.endsWith('/') ? withLeadingSlash.slice(0, -1) : withLeadingSlash
}

const base = resolveBasePath()

export default defineConfig({
  site: 'https://robowiki.org.cn',
  base,
  output: 'static',
  // 保持与 VitePress 现有 deep link 一致：/parts/x.html、/catalog.html。
  // 迁移期不制造 301 链，旧书签/外链可以直接打开。
  trailingSlash: 'never',
  build: {
    format: 'file',
  },
  integrations: [
    react(),
    sitemap({
      // 404 / 500 由集成自动排除，这里只兜底过滤无索引价值的页。
      filter: page => !/\/(404|500)\/?$/.test(page),
      // Astro 的 sitemap 会按路由去扩展名；本项目的静态产物是 .html。
      // 目录型 URL（首页 /next/）和 404 等页面保持原样：补成 /next.html 会指向不存在的文件。
      serialize(item) {
        const url = new URL(item.url)
        if (!url.pathname.endsWith('/') && !/\.[a-z0-9]+$/i.test(url.pathname)) {
          url.pathname = `${url.pathname}.html`
        }
        return { ...item, url: url.href }
      },
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: { fs: { allow: ['../..'] } },
  },
})
