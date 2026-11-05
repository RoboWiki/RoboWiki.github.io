/// <reference types="@tarojs/taro" />

declare const __RW_API_BASE__: string

/** H5 构建里指向真实的 react-dom，绕开 react-dom -> shim 的别名。 */
declare module 'react-dom-real' {
  export * from 'react-dom'
}

declare namespace NodeJS {
  interface ProcessEnv {
    TARO_ENV: 'h5' | 'weapp' | 'rn'
    NODE_ENV: 'development' | 'production'
  }
}
