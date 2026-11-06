import {
  App as AntApp, ConfigProvider, Form, Input, Modal, Segmented, theme as antdTheme,
} from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query'
import {
  Component, createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode,
} from 'react'
import { ApiError, api, auth, siteHref, type User } from '@/lib/community-api'

// ── 设计令牌桥接 ──────────────────────────────────────────────────────────
// antd 不认 CSS 变量做派生色，这里在运行时读取 --rw-* 的值传给 ConfigProvider：
// 令牌仍是唯一来源，深色模式切换时重算一次，antd 组件跟着换肤。
type ThemeVars = {
  primary: string
  primaryHover: string
  primarySoft: string
  primaryFg: string
  bg: string
  surface: string
  surface2: string
  surface3: string
  border: string
  borderStrong: string
  ink: string
  ink2: string
  ink3: string
  success: string
  warning: string
  danger: string
  fontSans: string
  fontMono: string
  radiusSm: number
  radiusMd: number
}

const FALLBACK: ThemeVars = {
  primary: '#2563eb',
  primaryHover: '#1d4ed8',
  primarySoft: '#eff5ff',
  primaryFg: '#ffffff',
  bg: '#f5f7fa',
  surface: '#ffffff',
  surface2: '#f8fafc',
  surface3: '#f1f4f8',
  border: '#e3e8ef',
  borderStrong: '#cdd5df',
  ink: '#0b1220',
  ink2: '#475467',
  ink3: '#667085',
  success: '#15803d',
  warning: '#b45309',
  danger: '#b42318',
  fontSans: 'ui-sans-serif, system-ui, sans-serif',
  fontMono: 'ui-monospace, SFMono-Regular, Menlo, monospace',
  radiusSm: 8,
  radiusMd: 12,
}

function readThemeVars(): ThemeVars {
  if (typeof window === 'undefined') return FALLBACK
  const cs = window.getComputedStyle(document.documentElement)
  const raw = (name: string, fallback: string) => cs.getPropertyValue(name).trim() || fallback
  const px = (name: string, fallback: number) => {
    const n = Number.parseInt(raw(name, ''), 10)
    return Number.isFinite(n) ? n : fallback
  }
  return {
    primary: raw('--rw-primary', FALLBACK.primary),
    primaryHover: raw('--rw-primary-hover', FALLBACK.primaryHover),
    primarySoft: raw('--rw-primary-soft', FALLBACK.primarySoft),
    primaryFg: raw('--rw-primary-foreground', FALLBACK.primaryFg),
    bg: raw('--rw-bg', FALLBACK.bg),
    surface: raw('--rw-surface', FALLBACK.surface),
    surface2: raw('--rw-surface-2', FALLBACK.surface2),
    surface3: raw('--rw-surface-3', FALLBACK.surface3),
    border: raw('--rw-border', FALLBACK.border),
    borderStrong: raw('--rw-border-strong', FALLBACK.borderStrong),
    ink: raw('--rw-ink', FALLBACK.ink),
    ink2: raw('--rw-ink-2', FALLBACK.ink2),
    ink3: raw('--rw-ink-3', FALLBACK.ink3),
    success: raw('--rw-success', FALLBACK.success),
    warning: raw('--rw-warning', FALLBACK.warning),
    danger: raw('--rw-danger', FALLBACK.danger),
    fontSans: raw('--rw-font-sans', FALLBACK.fontSans),
    fontMono: raw('--rw-font-mono', FALLBACK.fontMono),
    radiusSm: px('--rw-radius-sm', FALLBACK.radiusSm),
    radiusMd: px('--rw-radius-md', FALLBACK.radiusMd),
  }
}

/** 跟随 <html class="dark"> 变化重算令牌，首帧就能拿到正确色值。 */
function useDesignTheme(): { dark: boolean; vars: ThemeVars } {
  const [dark, setDark] = useState(
    () => typeof document !== 'undefined' && document.documentElement.classList.contains('dark'),
  )

  useEffect(() => {
    const root = document.documentElement
    const sync = () => setDark(root.classList.contains('dark'))
    const observer = new MutationObserver(sync)
    observer.observe(root, { attributes: true, attributeFilter: ['class'] })

    // 没有手动选择过主题时，系统主题变化也要跟上
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onScheme = (e: MediaQueryListEvent) => {
      if (!window.localStorage.getItem('rw-theme')) setDark(e.matches)
    }
    mq.addEventListener('change', onScheme)
    return () => {
      observer.disconnect()
      mq.removeEventListener('change', onScheme)
    }
  }, [])

  const vars = useMemo(() => readThemeVars(), [dark])
  return { dark, vars }
}

function AntdTheme({ children }: { children: ReactNode }) {
  const { dark, vars } = useDesignTheme()

  return (
    <ConfigProvider
      theme={{
        algorithm: dark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          colorPrimary: vars.primary,
          colorPrimaryHover: vars.primaryHover,
          colorPrimaryActive: vars.primaryHover,
          colorPrimaryBg: vars.primarySoft,
          colorInfo: vars.primary,
          colorLink: vars.primary,
          colorLinkHover: vars.primaryHover,
          colorSuccess: vars.success,
          colorWarning: vars.warning,
          colorError: vars.danger,
          colorBgBase: vars.bg,
          colorBgLayout: vars.bg,
          colorBgContainer: vars.surface,
          colorBgElevated: vars.surface,
          colorBgSpotlight: vars.surface3,
          colorFillQuaternary: vars.surface2,
          colorFillTertiary: vars.surface3,
          colorFillSecondary: vars.surface3,
          colorBorder: vars.border,
          colorBorderSecondary: vars.border,
          colorSplit: vars.border,
          colorText: vars.ink,
          colorTextHeading: vars.ink,
          colorTextSecondary: vars.ink2,
          colorTextTertiary: vars.ink3,
          colorTextQuaternary: vars.ink3,
          colorTextDescription: vars.ink3,
          colorTextPlaceholder: vars.ink3,
          borderRadius: vars.radiusSm,
          borderRadiusLG: vars.radiusMd,
          fontSize: 14,
          fontFamily: vars.fontSans,
          fontFamilyCode: vars.fontMono,
          controlHeight: 34,
          wireframe: false,
        },
        components: {
          Table: {
            headerBg: vars.surface2,
            headerColor: vars.ink3,
            headerSplitColor: vars.border,
            borderColor: vars.border,
            rowHoverBg: vars.surface2,
            footerBg: vars.surface2,
            cellPaddingBlockSM: 8,
          },
          Card: { headerBg: 'transparent', headerFontSize: 13, headerHeight: 44 },
          Modal: { contentBg: vars.surface, headerBg: vars.surface, footerBg: 'transparent' },
          Segmented: {
            itemSelectedBg: vars.primary,
            itemSelectedColor: vars.primaryFg,
            itemHoverBg: vars.surface3,
            itemColor: vars.ink3,
            itemHoverColor: vars.ink,
            trackBg: vars.surface2,
          },
          Tabs: { itemColor: vars.ink2, itemSelectedColor: vars.primary, inkBarColor: vars.primary },
          Tag: { defaultBg: vars.surface3, defaultColor: vars.ink2 },
          Button: { primaryShadow: 'none', defaultShadow: 'none', dangerShadow: 'none' },
          Input: { activeBorderColor: vars.primary, hoverBorderColor: vars.borderStrong },
          Select: { optionSelectedBg: vars.primarySoft },
          Pagination: { itemActiveBg: vars.primarySoft },
          Empty: { colorTextDescription: vars.ink3 },
        },
      }}
    >
      <AntApp>{children}</AntApp>
    </ConfigProvider>
  )
}

/**
 * 岛屿内发生渲染异常时兜底：宁可显示一条可重试的提示，也不要让整页空白。
 * （chunk 缺失属于模块加载失败，兜不住——那种情况由页面里的 IslandFallback 静态骨架接住。）
 */
class IslandBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch(error: unknown) {
    console.error('[community island]', error)
    // 已经接管显示，撤掉静态骨架，避免骨架和错误卡叠在一起
    document.querySelectorAll('[data-island-fallback]').forEach(el => el.remove())
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <div className="card mx-auto max-w-lg p-6 text-center">
        <p className="m-0 text-sm font-semibold text-ink">内容没能加载出来</p>
        <p className="mb-4 mt-1.5 text-[12.5px] leading-6 text-ink-2">
          页面脚本没有正常运行，可能是网络中断或缓存了旧版本。
        </p>
        <button type="button" onClick={() => window.location.reload()}
          className="inline-flex h-9 items-center rounded-md bg-brand px-3.5 text-[13px] font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
          重新加载
        </button>
      </div>
    )
  }
}

export function IslandProvider({ children }: { children: ReactNode }) {
  const [qc] = useState(() => new QueryClient({
    defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 15_000 } },
  }))

  // 岛屿真正挂载后才撤掉页面里的静态骨架；没挂载（chunk 404/JS 报错）时骨架继续留着。
  useEffect(() => {
    document.querySelectorAll('[data-island-fallback]').forEach(el => el.remove())
  }, [])

  return (
    <IslandBoundary>
      <QueryClientProvider client={qc}>
        <AntdTheme>
          <AuthProvider>{children}</AuthProvider>
        </AntdTheme>
      </QueryClientProvider>
    </IslandBoundary>
  )
}

// ── 认证上下文 ────────────────────────────────────────────────────────────
interface AuthCtx {
  user: User | null
  ready: boolean
  setUser: (u: User | null) => void
  logout: () => void
  openAuth: () => void
}

const Ctx = createContext<AuthCtx>({
  user: null, ready: false, setUser: () => {}, logout: () => {}, openAuth: () => {},
})

export const useAuth = () => useContext(Ctx)

function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [user, setUserState] = useState<User | null>(null)
  const [ready, setReady] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)

  useEffect(() => {
    if (!auth.token && !auth.refreshToken) { setReady(true); return }
    api.me()
      .then(u => setUserState(u))
      .catch((e: unknown) => {
        // 只有 401 且 refresh 也没了才算会话失效；网络/5xx 保留 refresh 下次再试
        if (e instanceof ApiError && e.status === 401 && !auth.refreshToken) auth.clear()
      })
      .finally(() => setReady(true))
  }, [])

  const setUser = useCallback((u: User | null) => setUserState(u), [])
  const logout = useCallback(() => {
    setUserState(null)
    qc.clear()
    void api.logout()
  }, [qc])
  const openAuth = useCallback(() => setAuthOpen(true), [])

  const ctx = useMemo<AuthCtx>(() => ({ user, ready, setUser, logout, openAuth }),
    [user, ready, setUser, logout, openAuth])

  return (
    <Ctx.Provider value={ctx}>
      {children}
      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </Ctx.Provider>
  )
}

// ── 登录 / 注册表单 ───────────────────────────────────────────────────────
export function AuthForm({ onSuccess, compact = false }: {
  onSuccess?: (u: User) => void
  compact?: boolean
}) {
  const { setUser } = useAuth()
  const { message } = AntApp.useApp()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form] = Form.useForm()

  const submit = async (v: Record<string, string>) => {
    setBusy(true)
    setError(null)
    try {
      const r = mode === 'login'
        ? await api.login({ handle: String(v.handle).trim(), password: v.password })
        : await api.register({
          handle: String(v.handle).trim(),
          display_name: String(v.display_name).trim(),
          password: v.password,
          // 空邮箱不发，避免占用「空邮箱」唯一约束
          email: v.email ? String(v.email).trim() : undefined,
        })
      auth.setTokens(r.access_token, r.refresh_token)
      setUser(r.user)
      message.success(mode === 'login' ? `欢迎回来，${r.user.display_name}` : '注册成功')
      form.resetFields()
      onSuccess?.(r.user)
    } catch (e) {
      setError(e instanceof Error ? e.message : '请求失败，请检查网络后重试')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      {!compact && (
        <div className="mb-5 text-center">
          <div className="text-[22px] font-extrabold tracking-tight text-ink">
            Robo<span className="text-brand">Wiki</span>
          </div>
          <div className="mt-1 text-[12.5px] text-ink-3">选型是底座，真实反馈才是值钱的部分</div>
        </div>
      )}

      <Segmented block value={mode} className="mb-4" disabled={busy}
        onChange={v => {
          setMode(v as 'login' | 'register')
          setError(null)
          form.setFieldValue('password', '')
        }}
        options={[{ label: '登录', value: 'login' }, { label: '注册', value: 'register' }]} />

      <Form form={form} layout="vertical" onFinish={submit} disabled={busy} autoComplete="on"
        requiredMark={false}>
        <Form.Item name="handle" label="账号"
          normalize={v => (v || '').trim()}
          rules={[
            { required: true, message: '请填写账号' },
            { min: 2, max: 24, message: '账号长度 2–24 位' },
            { pattern: /^[a-z0-9][a-z0-9_-]*$/i, message: '只能使用 a-z、0-9、-、_，且以字母或数字开头' },
          ]}>
          <Input placeholder="2–24 位 a-z、0-9、-、_，用作主页地址"
            autoComplete="username" autoFocus />
        </Form.Item>
        {mode === 'register' && (
          <>
            <Form.Item name="display_name" label="显示名"
              normalize={v => (v || '').trim()}
              rules={[{ required: true, message: '请填写显示名' }, { max: 32 }]}>
              <Input placeholder="别人看到的名字" autoComplete="nickname" />
            </Form.Item>
            <Form.Item name="email" label="邮箱（可选，建议填写）"
              normalize={v => (v || '').trim()}
              rules={[
                { type: 'email', message: '邮箱格式不正确，例如 name@example.com' },
                { max: 200, message: '邮箱过长' },
              ]}>
              <Input placeholder="用于邮箱验证与找回密码" autoComplete="email" inputMode="email" />
            </Form.Item>
          </>
        )}
        <Form.Item name="password" label="密码" className="mb-3"
          rules={[
            { required: true, message: '请填写密码' },
            { min: 6, message: '密码至少 6 位' },
            { max: 128 },
          ]}>
          <Input.Password placeholder="至少 6 位"
            autoComplete={mode === 'register' ? 'new-password' : 'current-password'} />
        </Form.Item>

        {/* 错误提示固定在提交按钮上方，避免出现时顶动按钮位置 */}
        <div aria-live="polite" className="mb-3">
          {error && (
            <div role="alert"
              className="rounded-md border border-danger/35 bg-danger-soft px-3 py-2 text-[12.5px] leading-5 text-danger">
              {error}
            </div>
          )}
        </div>

        <button type="submit" disabled={busy}
          className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-brand px-4 text-sm font-semibold text-brand-fg transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-60">
          {busy ? '提交中…' : mode === 'login' ? '登录' : '注册并登录'}
        </button>
      </Form>
    </div>
  )
}

function AuthModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Modal open={open} onCancel={onClose} footer={null} title={null}
      width={400} destroyOnHidden>
      <AuthForm onSuccess={onClose} />
    </Modal>
  )
}

// ── 页头 ──────────────────────────────────────────────────────────────────
function NavLink({ href, label, current }: { href: string; label: string; current?: boolean }) {
  return (
    <a href={siteHref(href)} aria-current={current ? 'page' : undefined}
      className={`inline-flex min-h-8 items-center rounded-md px-2.5 text-[13px] transition-colors ${
        current
          ? 'bg-brand-soft font-semibold text-brand'
          : 'text-ink-2 hover:bg-surface-3 hover:text-ink'
      }`}>
      {label}
    </a>
  )
}

export function CommunityHeader({ current, onCompose }: {
  current?: 'community' | 'top' | 'admin'
  onCompose?: () => void
}) {
  const { user, ready, openAuth, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="mb-5 flex flex-wrap items-center gap-2 border-b border-line pb-3">
      <a href={siteHref('/')} className="mr-1 flex items-baseline gap-1.5">
        <span className="text-[15px] font-extrabold tracking-tight text-ink">社区</span>
        <span className="mono rounded-full border border-line bg-surface-2 px-1.5 py-[1px] text-[10px] font-semibold text-ink-3">
          RoboWiki
        </span>
      </a>

      <nav className="flex flex-wrap items-center gap-0.5" aria-label="社区导航">
        <NavLink href="/community.html" label="社区" current={current === 'community'} />
        <NavLink href="/top.html" label="贡献榜" current={current === 'top'} />
        <NavLink href="/catalog.html" label="部件库 ↗" />
        {user?.is_staff && <NavLink href="/admin.html" label="后台" current={current === 'admin'} />}
      </nav>

      <div className="ml-auto flex items-center gap-2">
        {onCompose && (
          <button onClick={() => (user ? onCompose() : openAuth())}
            className="inline-flex min-h-9 items-center rounded-full bg-brand px-3.5 text-[13px] font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
            发帖
          </button>
        )}

        {!ready ? (
          <span className="text-[12px] text-ink-3" aria-hidden="true">…</span>
        ) : user ? (
          <div className="relative">
            <button onClick={() => setMenuOpen(v => !v)}
              className="flex items-center gap-1.5 rounded-full border border-line bg-surface py-[3px] pl-[3px] pr-2.5 transition-colors hover:border-line-strong"
              aria-haspopup="menu" aria-expanded={menuOpen}>
              <span className="grid h-6 w-6 place-items-center rounded-full bg-brand text-[11px] font-bold text-brand-fg">
                {user.display_name.slice(0, 1)}
              </span>
              <span className="max-w-[110px] truncate text-[12.5px] text-ink">{user.display_name}</span>
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div role="menu"
                  className="absolute right-0 z-20 mt-1.5 w-40 overflow-hidden rounded-lg border border-line bg-surface py-1 shadow-lg">
                  <a role="menuitem" href={siteHref(`/u.html?handle=${encodeURIComponent(user.handle)}`)}
                    onClick={() => setMenuOpen(false)}
                    className="block px-3 py-2 text-[12.5px] text-ink-2 hover:bg-surface-3 hover:text-ink">
                    我的主页
                  </a>
                  <button role="menuitem" onClick={() => { setMenuOpen(false); logout() }}
                    className="flex w-full items-center gap-1.5 px-3 py-2 text-left text-[12.5px] text-ink-3 hover:bg-surface-3 hover:text-ink">
                    <LogoutOutlined className="text-[11px]" /> 退出登录
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <>
            <button onClick={openAuth}
              className="inline-flex min-h-9 items-center rounded-full border border-line bg-surface px-3.5 text-[13px] text-ink-2 transition-colors hover:border-line-strong hover:text-ink">
              登录
            </button>
            <a href={siteHref('/login.html')}
              className="hidden text-[12px] text-ink-3 hover:text-ink sm:inline">登录遇到问题？</a>
          </>
        )}
      </div>
    </div>
  )
}
