import { useEffect, type PropsWithChildren } from 'react'

import '@robowiki/tokens/tokens.css'
import './app.css'

import { applyTheme, getTheme } from './utils/theme'

function App({ children }: PropsWithChildren) {
  // 冷启动先落地已保存的主题；H5 切 html.dark，小程序同步原生导航栏与 tabBar。
  useEffect(() => {
    applyTheme(getTheme())
  }, [])

  return children
}

export default App
