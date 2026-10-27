import { defineConfig } from 'vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

// 站点结构参考 YunQianDoc（euuen/YunQianDoc）：VitePress + 每页一条讨论串。
// 区别：那边用 giscus（需要公开 GitHub 仓库并开 Discussions），
// 这边用自托管 —— 数据在本地，用户体系也是现成的。
export default defineConfig({
  title: 'RoboSelect',
  description: '四足机器人部件选型文档',
  // 两站合一后站点在根目录；GitHub Pages 是 project site，挂在 /RoboSelect/ 下。
  // 用环境变量切换，避免为部署改源文件。
  base: process.env.WIKI_BASE || '/',
  lang: 'zh-CN',
  // 明暗切换：'true' = 跟随系统 + 右上角手动切换（浅色 / 深色两套都做了）
  appearance: true,
  // 不用 cleanUrls：产物直接由 FastAPI StaticFiles(html=True) 托管，
  // 保持 .html 后缀最省事，也避免兜底路由抢路径。
  cleanUrls: false,
  // dev 模式下把 /api 代理到 FastAPI —— 否则评分组件在 5174 上只能读快照，
  // 走不到「登录后打分」那条链路。生产由 FastAPI 同源托管，不需要代理。
  vite: {
    server: {
      proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
    },
  },
  head: [['link', { rel: 'icon', href: '/favicon.ico' }]],

  themeConfig: {
    siteTitle: 'RoboSelect 文档',
    nav: [
      { text: '交互式检索', link: '/explore' },
      { text: '部件手册', link: '/parts/' },
      { text: '参数口径', link: '/semantics' },
      { text: '总线协议', link: '/protocols' },
      { text: '数据来源', link: '/sources' },
      { text: '控制台 ↗', link: '/console/' },
    ],
    sidebar,
    outline: { label: '页面导航', level: [1, 4] },
    docFooter: { prev: '上一页', next: '下一页' },
    lastUpdated: { text: '最后更新于' },
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    skipToContentLabel: '跳转到内容',
    notFound: {
      title: '页面未找到',
      quote: '这个型号还没有文档页。交互式检索里能查到全部型号。',
      linkLabel: '打开交互式检索',
      linkText: '去检索',
    },
    docPageLink: { text: '在交互式检索里按任意列排序' },
    footer: {
      message: '数据带来源、口径可追溯、不卖零件不收佣金',
      copyright: 'RoboSelect',
    },
  },
})
