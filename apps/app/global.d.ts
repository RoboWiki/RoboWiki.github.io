/// <reference types="vite-plugin-taro/client" />

declare const __RW_API_BASE__: string
declare const __RW_ASSET_BASE__: string

declare namespace NodeJS {
  interface ProcessEnv {
    TARO_ENV: 'h5' | 'weapp' | 'alipay' | 'tt'
    NODE_ENV: 'development' | 'production'
  }
}
