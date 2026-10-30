import { defineConfig } from 'vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

// RoboWiki —— 机器人部件选择社区。
// 一页两件事：左边官方参数（带来源与口径），右边真实使用者的评分与评价。
//
// 中英双语：root = 中文，/en/ = English。
// 每个语言的 nav / footer 必须写在 locales[key].themeConfig 下 ——
// 这是 VitePress 的官方做法；把 nav 写在顶层 themeConfig 会被 root 语言吃掉，
// 表现就是「页面是英文，导航还是中文」。
const zhTheme = {
  nav: [
    { text: '首页', link: '/' },
    { text: '机器人部件', link: '/catalog' },
    { text: '机器人整机', link: '/robots' },
    { text: '机器人软件', link: '/software' },
    { text: '使用指南', link: '/learn/' },
    { text: '加工与采购', link: '/suppliers' },
    { text: '贡献者', link: '/contributors' },
    { text: '投稿', link: '/submit' },
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
    copyright: 'RoboWiki · 机器人部件选择社区',
  },
}

const enTheme = {
  nav: [
    { text: 'Home', link: '/en/' },
    { text: 'Learning path', link: '/en/learn/' },
    { text: 'Robots', link: '/en/robots' },
    { text: 'Parts', link: '/en/catalog' },
    { text: 'Suppliers', link: '/en/suppliers' },
    { text: 'Contributors', link: '/en/contributors' },
  ],
  outline: { label: 'On this page', level: [2, 3] },
  docFooter: { prev: 'Previous', next: 'Next' },
  lastUpdated: { text: 'Updated' },
  returnToTopLabel: 'Back to top',
  sidebarMenuLabel: 'Menu',
  darkModeSwitchLabel: 'Theme',
  lightModeSwitchTitle: 'Switch to light mode',
  darkModeSwitchTitle: 'Switch to dark mode',
  skipToContentLabel: 'Skip to content',
  notFound: {
    title: 'Page not found',
    quote: 'This model may not have a page yet. The parts library lists everything we hold.',
    linkLabel: 'Open parts library',
    linkText: 'Go to parts',
  },
  docPageLink: { text: 'Sort by any column in the parts library' },
  footer: {
    message: 'Every number sourced · semantics traceable · we do not sell parts',
    copyright: 'RoboWiki · a robot parts selection community',
  },
}

export default defineConfig({
  title: 'RoboWiki',
  // 标签页统一成「页面 · RoboWiki」；首页只有 RoboWiki，不重复
  titleTemplate: ':title · RoboWiki',
  description: '机器人部件选择社区：官方参数 + 真实使用者的评分与评价',
  // 仓库是 organization pages（RoboWiki.github.io）→ 站点在域名根，base 用 /。
  base: process.env.WIKI_BASE || '/',
  appearance: true,
  // 中英双语：VitePress 会自动在页头放语言切换
  locales: {
    root: { label: '中文', lang: 'zh-CN', themeConfig: zhTheme },
    en: { label: 'English', lang: 'en-US', link: '/en/', themeConfig: enTheme },
  },
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
    siteTitle: 'RoboWiki',
  },
})
