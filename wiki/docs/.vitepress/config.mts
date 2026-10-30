import { defineConfig } from 'vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

// RoboWiki —— 机器人开发的开放资料底稿。
// 一页两件事：左边官方参数（带来源与口径），右边真实使用者的评分与评价。
//
// 中英双语：root = 中文，/en/ = English。
// 每个语言的 nav / footer 必须写在 locales[key].themeConfig 下 ——
// 这是 VitePress 的官方做法；把 nav 写在顶层 themeConfig 会被 root 语言吃掉，
// 表现就是「页面是英文，导航还是中文」。
const zhTheme = {
  // 导航按「任务」收敛成 6 项，同类内容并拢（多方评审的共同结论）：
  //   部件 / 整机 / 软件本质是可查询对比的数据库 → 收进「资源库」
  //   学习路线与竞赛都是「帮我做出东西」的内容 → 收进「学习与竞赛」
  //   方法与来源是信任底座，必须全局可达，但不占一级入口的叙事位 → 收进「关于」
  //   投稿是全站动作，不是一个内容页 → 放导航最右，视觉上像按钮
  // 导航全平铺：资源库三项（部件/整机/软件）是全站最高频目的地，
  // 折叠进「资源库」下拉等于给第一名入口加一次悬停 —— 发现性比分组美观重要。
  // 「关于」仍折叠：方法/来源/贡献者/转载属信任层，需要全局可达、但不抢一级叙事位。
  nav: [
    { text: '首页', link: '/' },
    { text: '部件库', link: '/catalog' },
    { text: '整机库', link: '/robots' },
    { text: '软件库', link: '/software' },
    { text: '学习', link: '/learn/' },
    { text: '竞赛', link: '/competitions' },
    { text: '加工采购', link: '/suppliers' },
    {
      text: '关于',
      items: [
        { text: '方法与来源', link: '/method' },
        { text: '数据来源', link: '/sources' },
        { text: '贡献者', link: '/contributors' },
        { text: '转载规范', link: '/learn/reprint' },
        { text: '免责声明与许可', link: '/notice' },
      ],
    },
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
    quote: '这个地址没有对应的页面 —— 可能是链接写错了，或内容还没建。首页能进所有板块。',
    linkLabel: '回到首页',
    linkText: '去首页',
  },
  docPageLink: { text: '在部件库里按任意列排序' },
  footer: {
    message: '数据带来源 · 口径可追溯 · 不卖零件不收佣金 · GPL-3.0 · <a href="/method">方法与来源</a> · <a href="/notice">免责声明与许可</a>',
    copyright: 'RoboWiki · 机器人开发的开放资料底稿',
  },
}

const enTheme = {
  // 英文区是子集：只放已有英文页面的入口，避免导航指向 404。
  // （robots / software / submit / method / competitions 目前只有中文版。）
  nav: [
    { text: 'Home', link: '/en/' },
    { text: 'Parts', link: '/en/catalog' },
    { text: 'Suppliers', link: '/en/suppliers' },
    { text: 'Learn', link: '/en/learn/' },
    { text: 'Sources', link: '/en/sources' },
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
    quote: 'Nothing lives at this address yet. The home page reaches every section.',
    linkLabel: 'Back to home',
    linkText: 'Go home',
  },
  docPageLink: { text: 'Sort by any column in the parts library' },
  footer: {
    message: 'Every number sourced · semantics traceable · we do not sell parts',
    copyright: 'RoboWiki · an open knowledge base for robot builders',
  },
}

export default defineConfig({
  title: 'RoboWiki',
  // 标签页统一成「页面 · RoboWiki」；首页只有 RoboWiki，不重复
  titleTemplate: ':title · RoboWiki',
  description: 'RoboWiki —— 机器人开发的开放资料底稿：可核对的参数、可追溯的来源、真实使用者的经验。',
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
    // 现代浏览器优先 PNG，老的回退 ico；apple-touch-icon 给 iOS 主屏
    ['link', { rel: 'icon', type: 'image/png', href: '/icon-192.png' }],
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['link', { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' }],
    ['meta', { name: 'theme-color', content: '#0078d4' }],
  ],

  themeConfig: {
    // 品牌标：不再叫「文档」—— 这是个社区，不是一个说明书
    siteTitle: 'RoboWiki',
  },
})
