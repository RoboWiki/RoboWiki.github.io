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
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
  },
  build: { outDir: 'dist', sourcemap: false },
})
