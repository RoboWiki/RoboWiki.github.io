import { defineConfig } from 'vitepress'
import type { HeadConfig } from 'vitepress'
import { withPwa } from '@vite-pwa/vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

// 站点对外域名（organization pages，站点在域名根）。
// canonical / og:url / sitemap 三处必须用同一个值，否则搜索引擎会把
// /catalog 与 /catalog.html 当成两个页面各收一次。
const SITE = 'https://robowiki.org.cn'
const SITE_DESC = 'RoboWiki —— 机器人开发的开放资料底稿：可核对的参数、可追溯的来源、真实使用者的经验。'

//: 没有产品图的页面（材质/工艺/目录页）共用的 1200×630 分享图。
//: og:image / twitter:image 只在 transformHead 里输出一次 —— 全局 head 也写一份的话，
//: 同一页会有两张图，微信/Slack/X 取哪张取决于解析顺序，产品图经常被默认图挤掉。
const DEFAULT_OG_PATH = '/og-default.png'
const DEFAULT_OG_IMAGE = `${SITE}${DEFAULT_OG_PATH}`

/** frontmatter.image 可以是 /parts/x.jpg，也可以是完整 URL；输出必须是绝对地址。 */
function absoluteImage(src: string): string {
  return /^https?:\/\//i.test(src) ? src : `${SITE}/${src.replace(/^\/+/, '')}`
}

//: 页面 → 规范 URL。cleanUrls 关着（产物是 .html），所以路径要带 .html；
//: 目录型页面（index.md）收成以 / 结尾，和 sitemap.xml 里的写法一致。
function canonicalPath(relativePath: string): string {
  const p = relativePath
    .replace(/(^|\/)index\.md$/, '$1')
    .replace(/\.md$/, '.html')
  return `${SITE}/${p}`
}

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
    { text: '指南', link: '/learn/' },
    { text: '部件库', link: '/catalog' },
    { text: '整机库', link: '/robots' },
    { text: '材质库', link: '/materials' },
    { text: '软件库', link: '/software' },
    { text: '渠道库', link: '/suppliers' },
    { text: '实战资料', link: '/competitions' },
    { text: '登录', link: '/login' },
    {
      text: '关于',
      items: [
        { text: '贡献者', link: '/contributors' },
        { text: '方法与来源', link: '/method' },
        { text: '转载规范', link: '/learn/reprint' },
        { text: '免责声明与许可', link: '/notice' },
        { text: '投稿', link: '/submit' },
      ],
    },
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
  socialLinks: [
    { icon: 'github', link: 'https://github.com/RoboWiki/RoboWiki.github.io', ariaLabel: 'GitHub 仓库：RoboWiki' },
  ],
  footer: {
    message: '数据带来源 · 口径可追溯 · 不卖零件不收佣金 · GPL-3.0 · <a href="/method">方法与来源</a> · <a href="/notice">免责声明与许可</a>',
    copyright: 'RoboWiki · 机器人开发的开放资料底稿',
  },
}

const enTheme = {
  socialLinks: [
    { icon: 'github', link: 'https://github.com/RoboWiki/RoboWiki.github.io',
      ariaLabel: 'GitHub repository: RoboWiki' },
  ],
  // 英文区是子集：只放已有英文页面的入口，避免导航指向 404。
  // （robots / software / submit / method / competitions 目前只有中文版。）
  nav: [
    { text: 'Home', link: '/en/' },
    { text: 'Guide', link: '/en/learn/' },
    { text: 'Parts', link: '/en/catalog' },
    { text: 'Suppliers', link: '/en/suppliers' },
    {
      text: 'About',
      items: [
        { text: 'Method & sources', link: '/en/sources' },
        { text: 'Contributors', link: '/en/contributors' },
      ],
    },
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

export default withPwa(defineConfig({
  title: 'RoboWiki',
  // 标签页统一成「页面 · RoboWiki」；首页/404/英文首页用各自 frontmatter 关掉模板。
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
  // 站点地图：VitePress 构建期按页面列表生成 /sitemap.xml。
  // 之前没有这一项，线上 /sitemap.xml 与 /robots.txt 都是 404 ——
  // 311 个型号页只能靠外链被发现，搜索引擎与 AI 抓取器都不知道全站有什么。
  sitemap: {
    hostname: SITE,
  },
  // dev 模式下把 /api 代理到 FastAPI（评分/评论/控制台都要它）。
  // 默认对齐 Docker 的 127.0.0.1:8080；直接跑 uvicorn 时用 ROBOWIKI_API_ORIGIN 覆盖。
  vite: {
    server: {
      proxy: { '/api': { target: process.env.ROBOWIKI_API_ORIGIN || 'http://127.0.0.1:8080', changeOrigin: true } },
    },
  },
  head: [
    // 现代浏览器优先 PNG，老的回退 ico；apple-touch-icon 给 iOS 主屏
    ['link', { rel: 'icon', type: 'image/png', href: '/icon-192.png' }],
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['link', { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' }],
    ['meta', { name: 'theme-color', content: '#0078d4' }],
    // 分享卡片只放全站字段；每页的图在 transformHead 里按 frontmatter 输出，
    // 全局不再写 og:image / twitter:image，避免同页两张图互相覆盖。
    ['meta', { property: 'og:site_name', content: 'RoboWiki' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
  ],
  // 每页的 canonical / og:url / 结构化数据。VitePress 原来只给全站一句描述，
  // 311 个型号页在搜索结果里长得一模一样；canonical 也缺，/catalog 与
  // /catalog.html 会被当成两个 URL 各收一次。
  transformHead({ pageData }) {
    const url = canonicalPath(pageData.relativePath)
    const isHome = pageData.relativePath === 'index.md'
    const isEn = pageData.relativePath.startsWith('en/')
    const isNotFound = pageData.relativePath === '404.md'
      || pageData.frontmatter.title === '404'
      || pageData.title === '404'
    const title = pageData.frontmatter.title || pageData.title || 'RoboWiki'
    const description = pageData.frontmatter.description || SITE_DESC

    // 每页一张图：部件页 frontmatter.image 是产品图，材质/目录页是默认 OG。
    // pipeline 写根相对路径，这里补成绝对地址，微信 / Slack / X 才能抓到。
    const fmImage = typeof pageData.frontmatter.image === 'string'
      ? pageData.frontmatter.image.trim()
      : ''
    const image = absoluteImage(fmImage || DEFAULT_OG_PATH)
    const isDefaultImage = image === DEFAULT_OG_IMAGE
    const imageAlt = isDefaultImage ? `${title} · RoboWiki` : `${title} 产品图 · RoboWiki`

    // 404 页不该被索引，也不该把 canonical 指到自己；群里的坏链会固化错误 URL。
    if (isNotFound) {
      return [
        ['meta', { name: 'robots', content: 'noindex, nofollow' }],
        ['meta', { property: 'og:image', content: DEFAULT_OG_IMAGE }],
        ['meta', { property: 'og:image:alt', content: 'RoboWiki · 机器人开发的开放资料底稿' }],
        ['meta', { name: 'twitter:image', content: DEFAULT_OG_IMAGE }],
      ]
    }

    const webPage = {
      '@context': 'https://schema.org',
      '@type': isHome ? 'WebSite' : 'WebPage',
      name: isHome ? 'RoboWiki' : title,
      url,
      description,
      inLanguage: isEn ? 'en-US' : 'zh-CN',
      isPartOf: { '@type': 'WebSite', name: 'RoboWiki', url: `${SITE}/` },
    }

    const head: HeadConfig[] = [
      ['link', { rel: 'canonical', href: url }],
      ['meta', { property: 'og:type', content: isHome ? 'website' : 'article' }],
      ['meta', { property: 'og:title', content: title }],
      ['meta', { property: 'og:description', content: description }],
      ['meta', { property: 'og:url', content: url }],
      ['meta', { property: 'og:locale', content: isEn ? 'en_US' : 'zh_CN' }],
      ['meta', { property: 'og:image', content: image }],
      ['meta', { property: 'og:image:alt', content: imageAlt }],
      ['meta', { name: 'twitter:image', content: image }],
      ['meta', { name: 'twitter:image:alt', content: imageAlt }],
      ['script', { type: 'application/ld+json' }, JSON.stringify(webPage)],
    ]
    // 默认图尺寸是确定的；产品图尺寸各不相同，交给平台自己抓，别写错提示。
    if (isDefaultImage) {
      head.push(
        ['meta', { property: 'og:image:width', content: '1200' }],
        ['meta', { property: 'og:image:height', content: '630' }],
      )
    }
    return head
  },

  themeConfig: {
    // 品牌标：不再叫「文档」—— 这是个社区，不是一个说明书
    siteTitle: 'RoboWiki',
    // 英文站只有少数页面；不要让语言切换链到不存在的对应路径（404）。
    i18nRouting: false,
    // 站内搜索：local = 构建期生成本地索引，浏览器内检索，不需要后端也不需要 Algolia。
    // 243 部件 / 21 整机 / 207 渠道 + 全部文章，靠点导航找不到时这是唯一入口。
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '没有找到结果',
            resetButtonTitle: '清空',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
          },
        },
      },
    },
  },

  pwa: {
    registerType: 'autoUpdate',
    includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png'],
    manifest: {
      name: 'RoboWiki',
      short_name: 'RoboWiki',
      id: '/',
      description: SITE_DESC,
      lang: 'zh-CN',
      start_url: '/',
      scope: '/',
      display: 'standalone',
      background_color: '#0b1220',
      theme_color: '#0078d4',
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
      ],
    },
    workbox: {
      // 只预缓存外壳；页面与图片按访问缓存，避免把 100+ MB 目录塞进安装包
      // 只预缓存真正的壳（入口 + 图标/字体）。CSS/JS/搜索索引按访问走 runtimeCaching，
      // 否则 547 个页面 chunk + 2.3MB 搜索索引会把安装包撑到 8MB 以上。
      globPatterns: ['*.html', '**/*.{ico,svg,woff2}'],
      maximumFileSizeToCacheInBytes: 2 * 1024 * 1024,
      // 静态站是多页：不要把所有导航都回退到首页，按访问缓存真实页面
      navigateFallback: null,
      cleanupOutdatedCaches: true,
      clientsClaim: true,
      skipWaiting: true,
      runtimeCaching: [
        {
          urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
          handler: 'NetworkOnly',
        },
        {
          urlPattern: ({ request }) => request.mode === 'navigate',
          handler: 'NetworkFirst',
          options: {
            cacheName: 'pages',
            networkTimeoutSeconds: 3,
            expiration: { maxEntries: 60, maxAgeSeconds: 7 * 86400 },
          },
        },
        {
          urlPattern: ({ url }) => url.pathname.startsWith('/share/'),
          handler: 'StaleWhileRevalidate',
          options: {
            cacheName: 'share',
            expiration: { maxEntries: 400, maxAgeSeconds: 30 * 86400 },
          },
        },
        {
          // 列表数据虽在构建期打进页面，ShareBox/评分仍会取 JSON；离线时不空白。
          urlPattern: ({ url }) => url.pathname.endsWith('.json'),
          handler: 'StaleWhileRevalidate',
          options: {
            cacheName: 'data-json',
            expiration: { maxEntries: 40, maxAgeSeconds: 7 * 86400 },
          },
        },
        {
          urlPattern: ({ url }) => /\.(?:js|css)$/.test(url.pathname),
          handler: 'StaleWhileRevalidate',
          options: {
            cacheName: 'assets',
            expiration: { maxEntries: 160, maxAgeSeconds: 30 * 86400 },
          },
        },
        {
          urlPattern: ({ request }) => request.destination === 'image',
          handler: 'CacheFirst',
          options: {
            cacheName: 'images',
            expiration: { maxEntries: 200, maxAgeSeconds: 30 * 86400 },
          },
        },
      ],
    },
  },
}))
