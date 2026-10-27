import { defineConfig } from 'vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

// 站点结构参考 YunQianDoc（euuen/YunQianDoc）：VitePress + 每页一条讨论串。
// 区别：那边用 giscus（需要公开 GitHub 仓库并开 Discussions），
// 这边用自托管 —— 数据在本地，用户体系也是现成的。
export default defineConfig({
  title: 'RoboSelect',
  description: '四足机器人部件选型文档',
  // 本地由 FastAPI 托管在 /wiki/；GitHub Pages 上是 /roboselect.github.io/。
  // 用环境变量切换，避免为部署改源文件。
  base: process.env.WIKI_BASE || '/wiki/',
  lang: 'zh-CN',
  // 明暗切换：'true' = 跟随系统 + 右上角手动切换（浅色 / 深色两套都做了）
  appearance: true,
  // 不用 cleanUrls：产物直接由 FastAPI StaticFiles(html=True) 托管，
  // 保持 .html 后缀最省事，也避免 SPA 兜底路由抢路径。
  cleanUrls: false,
  head: [['link', { rel: 'icon', href: '/favicon.ico' }]],

  themeConfig: {
    siteTitle: 'RoboSelect 文档',
    nav: [
      { text: '部件手册', link: '/parts/' },
      { text: '参数口径', link: '/semantics' },
      { text: '总线协议', link: '/protocols' },
      { text: '数据来源', link: '/sources' },
      { text: '选型台 ↗', link: '/' },
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
      quote: '这个型号还没有文档页。选型台里能查到它。',
      linkLabel: '打开选型台',
      linkText: '去选型台',
    },
    docPageLink: { text: '在选型台查看交互式排序' },
    footer: {
      message: '数据带来源、口径可追溯、不卖零件不收佣金',
      copyright: 'RoboSelect',
    },
  },
})
