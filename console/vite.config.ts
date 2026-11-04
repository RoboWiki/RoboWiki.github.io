import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // 固定端口 + 固定 host：文档站的 VitePress dev 占 5174，这里让开，别互相抢。
    // host 写死 127.0.0.1，否则只在 ::1 上监听，curl/playwright 用 IPv4 会连不上。
    host: '127.0.0.1',
    port: 5180,
    strictPort: true,
    // 默认对齐 Docker API；直接跑 uvicorn 时用 ROBOWIKI_API_ORIGIN 覆盖。
    proxy: { '/api': { target: process.env.ROBOWIKI_API_ORIGIN || 'http://127.0.0.1:8080', changeOrigin: true } },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // 控制台挂在 /console 下（前台是 VitePress），资源路径要跟着走
    assetsDir: 'assets',
  },
  base: '/console/',
})
