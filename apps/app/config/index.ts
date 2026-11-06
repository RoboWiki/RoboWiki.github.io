import path from 'node:path'
import { createRequire } from 'node:module'

import { defineConfig, type UserConfigExport } from '@tarojs/cli'

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
const appBase = (() => {
  const raw = (process.env.APP_BASE || '/').trim()
  if (!raw || raw === '/') return '/'
  // Windows 上直接写 APP_BASE=/app/ 会被 shell 的路径转换改成 C:/...；
  // 这种值塞进 publicPath 会让页面去加载 file:// 资源，直接退回根路径。
  if (raw.includes(':') || raw.includes('\\')) {
    console.warn(`[taro] APP_BASE 不是合法 URL 路径，已忽略：${raw}`)
    return '/'
  }
  const normalized = raw.startsWith('/') ? raw : `/${raw}`
  return normalized.endsWith('/') ? normalized : `${normalized}/`
})()
const isH5 = process.env.TARO_ENV === 'h5'
// 工作区包直接暴露 TS 源码，H5 与小程序都必须进入 babel 编译范围。
const workspaceSources = [
  path.resolve(__dirname, '..', '..', '..', 'packages', 'core', 'src'),
  path.resolve(__dirname, '..', '..', '..', 'packages', 'content', 'src'),
]

// React 19 删除了 ReactDOM.render，Taro 4.3.2 的 H5 运行时仍在调用它。
// 用 webpack alias 在 H5 构建时替换 react-dom，小程序构建不受影响。
const appRequire = createRequire(path.resolve(__dirname, '..', 'package.json'))
const reactDomReal = appRequire.resolve('react-dom')
const reactDomShim = path.resolve(__dirname, '..', 'src', 'shims', 'react-dom.ts')
const h5Alias = isH5
  ? { 'react-dom$': reactDomShim, 'react-dom-real$': reactDomReal }
  : {}

const config: UserConfigExport<'webpack5'> = {
  projectName: 'robowiki-app',
  date: '2026-11-5',
  designWidth: 375,
  deviceRatio: {
    375: 2,
    640: 2.34 / 2,
    750: 1,
    828: 1.81 / 2,
  },
  sourceRoot: 'src',
  outputRoot: `dist/${process.env.TARO_ENV || 'h5'}`,
  plugins: [],
  defineConstants: {
    __RW_API_BASE__: JSON.stringify(apiBase),
    __RW_ASSET_BASE__: JSON.stringify(assetBase),
  },
  copy: {
    patterns: [],
    options: {},
  },
  framework: 'react',
  compiler: {
    type: 'webpack5',
    prebundle: {
      enable: false,
    },
  },
  cache: {
    enable: false,
  },
  alias: {
    '@': path.resolve(__dirname, '..', 'src'),
    ...h5Alias,
  },
  mini: {
    compile: {
      include: workspaceSources,
    },
    postcss: {
      pxtransform: {
        enable: true,
        config: {},
      },
      cssModules: {
        enable: false,
      },
    },
  },
  h5: {
    publicPath: appBase,
    staticDirectory: 'static',
    compile: {
      include: workspaceSources,
    },
    // alias 配置在平台级更可靠：确保 react-dom 被 shim 替换。
    webpackChain(chain: any) {
      chain.resolve.alias.set('react-dom$', reactDomShim)
      chain.resolve.alias.set('react-dom-real$', reactDomReal)
    },
    router: {
      mode: 'hash',
    },
    postcss: {
      autoprefixer: {
        enable: true,
      },
      cssModules: {
        enable: false,
      },
    },
    devServer: {
      host: '0.0.0.0',
      port: 10086,
    },
  },
}

export default defineConfig<'webpack5'>(async (merge) => {
  if (process.env.NODE_ENV === 'development') {
    return merge({}, config, {
      mini: {},
      h5: {},
    })
  }
  return merge({}, config, {
    mini: {},
    h5: {},
  })
})

export { isH5 }
