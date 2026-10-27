import { defineConfig } from 'vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

// RoboSelect —— 机器人部件选择社区。
// 一页两件事：左边官方参数（带来源与口径），右边真实使用者的评分与评价。
export default defineConfig({
  title: 'RoboSelect',
  description: '机器人部件选择社区：官方参数 + 真实使用者的评分与评价',
  // 两站合一后站点在根目录；GitHub Pages 是 project site，挂在 /RoboSelect/ 下。
  base: process.env.WIKI_BASE || '/',
  lang: 'zh-CN',
  appearance: true,
  // 不用 cleanUrls：产物由 FastAPI StaticFiles(html=True) 托管，保持 .html 最省事。
  cleanUrls: false,
  // dev 模式下把 /api 代理到 FastAPI（评分/评论/控制台都要它）
  vite: {
    server: {
      proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
    },
  },
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#0078d4' }],
  ],

  themeConfig: {
    // 品牌标：不再叫「文档」—— 这是个社区，不是一个说明书
    siteTitle: 'RoboSelect',
    nav: [
      { text: '部件库', link: '/catalog' },
      { text: '按厂商', link: '/parts/' },
      { text: '参数口径', link: '/semantics' },
      { text: '总线协议', link: '/protocols' },
      { text: '数据来源', link: '/sources' },
      { text: '控制台 ↗', link: '/console/' },
    ],
    sidebar,
    outline: { label: '本页', level: [2, 3] },
    docFooter: { prev: '上一页', next: '下一页' },
    lastUpdated: { text: '最后更新于' },
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    skipToContentLabel: '跳到内容',
    notFound: {
      title: '页面没找到',
      quote: '这个型号可能还没建页。部件库里能查到全部在库的型号。',
      linkLabel: '打开部件库',
      linkText: '去部件库',
    },
    docPageLink: { text: '在部件库里按任意列排序' },
    footer: {
      message: '数据带来源 · 口径可追溯 · 不卖零件不收佣金',
      copyright: 'RoboSelect · 机器人部件选择社区',
    },
  },
})
