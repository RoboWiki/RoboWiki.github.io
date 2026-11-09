import path from 'node:path'

import { APP_TABS } from '@robowiki/content'
import unitConverter, { presets } from 'postcss-rule-unit-converter'
import { defineConfig } from 'vite'
import vpt, { type VptJsonObject, type VptTarget } from 'vite-plugin-taro'

// 默认线上 API；本地联调可用 PUBLIC_API_BASE / VITE_API_BASE / RW_API_BASE 覆盖。
const apiBase =
  process.env.PUBLIC_API_BASE ||
  process.env.VITE_API_BASE ||
  process.env.RW_API_BASE ||
  'https://robowiki.org.cn/api/v1'
// 图片 / 静态资源默认与 API 同域；本地联调可指向静态站点（如 4321）。
const assetBase =
  process.env.PUBLIC_ASSET_BASE ||
  process.env.RW_ASSET_BASE ||
  apiBase.replace(/\/api\/v\d+\/?$/i, '')
// Windows 上直接写 APP_BASE=/app/ 会被 shell 的路径转换改成 C:/...；
// 这种值塞进 base 会让页面去加载 file:// 资源，直接退回根路径。
const appBase = (() => {
  const raw = (process.env.APP_BASE || '/').trim()
  if (!raw || raw === '/') return '/'
  if (raw.includes(':') || raw.includes('\\')) {
    console.warn(`[vpt] APP_BASE 不是合法 URL 路径，已忽略：${raw}`)
    return '/'
  }
  const normalized = raw.startsWith('/') ? raw : `/${raw}`
  return normalized.endsWith('/') ? normalized : `${normalized}/`
})()

const pages = [
  // 首页放在第一位：冷启动直接进现场助手，而不是目录。
  { path: 'pages/home/index', config: { navigationBarTitleText: 'RoboWiki', enablePullDownRefresh: false } },
  { path: 'pages/index/index', config: { navigationBarTitleText: '部件目录', enablePullDownRefresh: false } },
  { path: 'pages/builds/index', config: { navigationBarTitleText: '方案库', enablePullDownRefresh: false } },
  { path: 'pages/community/index', config: { navigationBarTitleText: '社区', enablePullDownRefresh: false } },
  { path: 'pages/account/index', config: { navigationBarTitleText: '账号' } },
  // 非 tab 页面
  { path: 'pages/layers/index', config: { navigationBarTitleText: '能力地图', enablePullDownRefresh: false } },
  { path: 'pages/part/index', config: { navigationBarTitleText: '部件详情' } },
  { path: 'pages/equipment/index', config: { navigationBarTitleText: '设备库', enablePullDownRefresh: false } },
  { path: 'pages/build/index', config: { navigationBarTitleText: '方案详情', enablePullDownRefresh: false } },
  { path: 'pages/post/index', config: { navigationBarTitleText: '帖子', enablePullDownRefresh: false } },
  { path: 'pages/compare/index', config: { navigationBarTitleText: '部件对比', enablePullDownRefresh: false } },
  { path: 'pages/learn/index', config: { navigationBarTitleText: '学习', enablePullDownRefresh: false } },
  { path: 'pages/login/index', config: { navigationBarTitleText: '登录' } },
  { path: 'pages/login/confirm/index', config: { navigationBarTitleText: '确认登录' } },
  { path: 'pages/submit/index', config: { navigationBarTitleText: '投稿纠错' } },
  { path: 'pages/compose/index', config: { navigationBarTitleText: '发帖' } },
]

const appJson: VptJsonObject = {
  lazyCodeLoading: 'requiredComponents',
  tabBar: {
    color: '#667085',
    selectedColor: '#2563eb',
    backgroundColor: '#ffffff',
    borderStyle: 'white',
    // 不引入图标依赖：微信小程序 tabBar 的 iconPath 是可选项，纯文字即可构建。
    list: APP_TABS.map((tab) => ({ pagePath: tab.pagePath, text: tab.label })),
  },
  window: {
    backgroundTextStyle: 'dark',
    navigationBarBackgroundColor: '#ffffff',
    navigationBarTitleText: 'RoboWiki',
    navigationBarTextStyle: 'black',
    backgroundColor: '#f7f8fb',
  },
}

const projectConfigJson: VptJsonObject = {
  appid: 'wx13bffd77b0b597e2',
  projectname: 'robowiki-app',
  description: 'RoboWiki 交互端：目录、详情、评分/讨论、账号、投稿纠错',
  compileType: 'miniprogram',
  setting: {
    urlCheck: false,
    es6: false,
    enhance: false,
    postcss: false,
    minified: false,
    minifyWXML: false,
    minifyWXSS: false,
    compileHotReLoad: true,
  },
}

export default defineConfig(() => {
  const target = (process.env.VITE_VPT_TARGET || 'wx') as VptTarget
  return {
    base: target === 'h5' ? appBase : '/',
    define: {
      __RW_API_BASE__: JSON.stringify(apiBase),
      __RW_ASSET_BASE__: JSON.stringify(assetBase),
    },
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, 'src'),
      },
    },
    build: {
      outDir: path.resolve(import.meta.dirname, 'dist', target),
    },
    css: {
      // 样式按 375 设计稿书写：小程序 1px → 2rpx，H5 同步换算成 vw。
      postcss: {
        plugins: [
          unitConverter({
            rules:
              target === 'h5'
                ? [presets.pxToVw({ viewportWidth: 375 }), presets.rpxToVw({ viewportWidth: 375, ratio: 1 })]
                : [presets.pxToRpx({ ratio: 2 })],
          }),
        ],
      },
    },
    plugins: [
      vpt({
        target,
        renderer: 'template',
        app: 'src/app.tsx',
        pages,
        appJson,
        projectConfigJson,
        hmr: {
          mode: target === 'wx' ? 'devtools' : 'interpreter',
        },
      }),
    ],
  }
})
