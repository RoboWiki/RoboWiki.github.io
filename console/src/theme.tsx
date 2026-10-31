/**
 * 明暗主题。
 *
 * 参考 zeitvex.github.io 的做法：`[data-theme]` 挂在 <html> 上，
 * 配色全走 CSS 变量，组件里不写死颜色。
 *
 * 之所以能「一行切换全站」：Tailwind v4 的工具类输出的是
 * `color: var(--color-slate-500)` 这种引用，所以只要在
 * `[data-theme="dark"]` 里把 `--color-slate-*` / `--color-blue-*` 换掉，
 * 200 多处既有类名全部跟着变，不用改组件。
 *
 * antd 不吃 CSS 变量，得单独给 algorithm 和 token，所以这里也存了 mode 供 ConfigProvider 用。
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

export type Mode = 'light' | 'dark'

const KEY = 'roboselect.theme'

interface ThemeCtx {
  mode: Mode
  setMode: (m: Mode) => void
  toggle: () => void
}

const Ctx = createContext<ThemeCtx>({ mode: 'light', setMode: () => {}, toggle: () => {} })
export const useTheme = () => useContext(Ctx)

function initial(): Mode {
  try {
    const saved = localStorage.getItem(KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    /* 无痕模式等拿不到 localStorage */
  }
  // 没存过就跟随系统（和 VitePress 一致）
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<Mode>(() =>
    typeof window === 'undefined' ? 'light' : initial())

  useEffect(() => {
    const root = document.documentElement
    root.dataset.theme = mode
    root.style.colorScheme = mode
    try {
      localStorage.setItem(KEY, mode)
    } catch {
      /* 忽略 */
    }
  }, [mode])

  // 跟随系统变化 —— 只在本机没手动选过时生效
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!mq) return
    const on = (e: MediaQueryListEvent) => {
      try {
        if (localStorage.getItem(KEY)) return
      } catch {
        /* 忽略 */
      }
      setModeState(e.matches ? 'dark' : 'light')
    }
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])

  const setMode = useCallback((m: Mode) => setModeState(m), [])
  const toggle = useCallback(() => setModeState(m => (m === 'dark' ? 'light' : 'dark')), [])
  const value = useMemo(() => ({ mode, setMode, toggle }), [mode, setMode, toggle])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
