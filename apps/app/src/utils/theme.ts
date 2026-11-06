import { useEffect, useState } from 'react'

import Taro from '@tarojs/taro'

export type ThemeMode = 'light' | 'dark'

/** 与 token 包深色语义色保持一致，仅用于原生导航栏 / tabBar。 */
const NATIVE = {
  light: {
    background: '#f5f7fa',
    navBackground: '#ffffff',
    front: '#000000',
    tabBackground: '#ffffff',
    tabText: '#667085',
    tabSelected: '#2563eb',
    border: 'white' as const,
  },
  dark: {
    background: '#0a0f18',
    navBackground: '#121826',
    front: '#ffffff',
    tabBackground: '#121826',
    tabText: '#7d8a9f',
    tabSelected: '#4f8cff',
    border: 'black' as const,
  },
}

const THEME_KEY = 'rw.app.theme'
const listeners = new Set<(mode: ThemeMode) => void>()

function normalize(value: unknown): ThemeMode {
  return value === 'dark' ? 'dark' : 'light'
}

/** 从 Taro storage 读取主题；没有存过时按浅色启动。 */
export function getTheme(): ThemeMode {
  try {
    return normalize(Taro.getStorageSync(THEME_KEY))
  } catch {
    return 'light'
  }
}

/**
 * 应用主题：H5 切 html.dark，小程序改原生导航栏 / tabBar / 页面底色；
 * 页面根节点同时会带 dark class（tokens.css 里 `.dark` 会重写全部 --rw-*）。
 */
export function applyTheme(mode: ThemeMode): void {
  const next = normalize(mode)
  try {
    Taro.setStorageSync(THEME_KEY, next)
  } catch {
    // 隐私模式下写不进去，本次会话仍然按内存态生效。
  }

  if (process.env.TARO_ENV === 'h5') {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', next === 'dark')
    }
  } else {
    const palette = NATIVE[next]
    try {
      Taro.setBackgroundColor({
        backgroundColor: palette.background,
        backgroundColorTop: palette.background,
        backgroundColorBottom: palette.background,
      }).catch(() => {})
    } catch {
      // 部分基础库不支持 setBackgroundColor，页面根节点仍是深色。
    }
    try {
      Taro.setNavigationBarColor({
        frontColor: palette.front,
        backgroundColor: palette.navBackground,
      }).catch(() => {})
    } catch {
      // 同上，导航栏颜色失败不影响内容。
    }
    try {
      Taro.setTabBarStyle({
        color: palette.tabText,
        selectedColor: palette.tabSelected,
        backgroundColor: palette.tabBackground,
        borderStyle: palette.border,
      }).catch(() => {})
    } catch {
      // 不在 tab 页面或平台不支持时忽略。
    }
  }

  listeners.forEach((listener) => listener(next))
}

/** 订阅主题变化；跨页面切换时每个已挂载页面都会同步更新。 */
export function useThemeMode(): ThemeMode {
  const [mode, setMode] = useState<ThemeMode>(() => getTheme())

  useEffect(() => {
    const listener = (next: ThemeMode) => setMode(next)
    listeners.add(listener)
    applyTheme(getTheme())
    return () => {
      listeners.delete(listener)
    }
  }, [])

  return mode
}

export function setTheme(mode: ThemeMode): void {
  applyTheme(mode)
}
