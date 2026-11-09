import {
  App as AntApp, ConfigProvider, Form, Input, Modal, Segmented, theme as antdTheme,
} from 'antd'
import { GithubOutlined, LogoutOutlined } from '@ant-design/icons'
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Component, createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode,
} from 'react'
import { API_BASE, ApiError, api, auth, siteHref, v1Req, type TokenPair, type User } from '@/lib/community-api'
import { Avatar } from './ui'

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

/**
 * 微信扫码登录：网页只拿 ticket 和小程序码，身份确认发生在小程序里。
 * 轮询 1.5s；confirmed 时取走一次性会话并跳转，expired 时提示重新生成。
 */
function WechatQrLogin() {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [qr, setQr] = useState<{ ticket: string; src: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timer = useRef<number | null>(null)

  const stop = useCallback(() => {
    if (timer.current !== null) {
      window.clearInterval(timer.current)
      timer.current = null
    }
  }, [])

  useEffect(() => stop, [stop])

  const poll = useCallback((ticket: string) => {
    stop()
    timer.current = window.setInterval(async () => {
      try {
        const r = await v1Req<{ status: 'pending' | 'confirmed' | 'expired'; token?: TokenPair }>(
          `/auth/wechat/qr/status?ticket=${encodeURIComponent(ticket)}`,
        )
        if (r.status === 'confirmed' && r.token) {
          stop()
          auth.setTokens(r.token.access_token, r.token.refresh_token ?? null)
          window.location.replace(siteHref('/community.html'))
        } else if (r.status === 'expired') {
          stop()
          setQr(null)
          setError('二维码已过期，请重新生成')
        }
      } catch {
        // 单次轮询失败不打断，下一次再试；二维码过期由状态接口给出
      }
    }, 1500)
  }, [stop])

  const start = async () => {
    setBusy(true)
    setError(null)
    setOpen(true)
    try {
      const r = await v1Req<{ ticket: string; qrcode: string }>('/auth/wechat/qr', { method: 'POST' })
      setQr({ ticket: r.ticket, src: `data:image/png;base64,${r.qrcode}` })
      poll(r.ticket)
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成二维码失败，请稍后再试')
    } finally {
      setBusy(false)
    }
  }

  const close = () => {
    stop()
    setOpen(false)
    setQr(null)
    setError(null)
  }

  return (
    <div className="mb-4">
      {!open ? (
        <button type="button" onClick={start} disabled={busy}
          className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-line bg-surface px-4 text-sm font-semibold text-ink transition-colors hover:border-line-strong hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-60">
          微信扫码登录
        </button>
      ) : (
        <div className="rounded-lg border border-line bg-surface-2 p-4 text-center" aria-live="polite">
          {qr ? (
            <>
              <img src={qr.src} alt="微信扫码登录二维码" width={200} height={200}
                className="mx-auto rounded-md bg-white p-2" />
              <p className="mt-2 text-[12.5px] leading-5 text-ink-2">
                用微信扫一扫，在小程序里点「确认登录」
              </p>
              <p className="mt-1 text-[11px] text-ink-3">二维码 5 分钟内有效</p>
            </>
          ) : (
            <p className="py-10 text-[12.5px] text-ink-3">{busy ? '正在生成二维码…' : '二维码不可用'}</p>
          )}
          {error && <p className="mt-2 text-[12px] text-danger">{error}</p>}
          <div className="mt-3 flex justify-center gap-2">
            <button type="button" onClick={start} disabled={busy}
              className="inline-flex h-8 items-center rounded-md border border-line px-3 text-xs font-medium text-ink-2 hover:text-ink">
              重新生成
            </button>
            <button type="button" onClick={close}
              className="inline-flex h-8 items-center rounded-md px-3 text-xs text-ink-3 hover:text-ink">
              收起
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export function AuthForm({ onSuccess, compact = false }: {
  onSuccess?: (u: User) => void
  compact?: boolean
}) {
  const { setUser } = useAuth()
  const { message } = AntApp.useApp()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [forgot, setForgot] = useState(false)
  const [form] = Form.useForm()

  // GitHub OAuth 只有在服务端配了 client id/secret 时才出现；
  // 回调由 /login.html 的 handoff 桥接，JWT 不经过地址栏。
  const providers = useQuery({
    queryKey: ['auth-providers'],
    queryFn: () => api.providers(),
    staleTime: 60_000,
    retry: false,
  })
  const githubEnabled = providers.data?.github === true
  const wechatQrEnabled = providers.data?.wechat_mini === true
  const startGithub = () => {
    const origin = typeof window !== 'undefined' ? window.location.origin : ''
    if (!origin) return
    window.location.href = `${API_BASE}/auth/github/login?return_to=${encodeURIComponent(origin)}`
  }

  if (forgot) {
    return <ForgotPasswordPanel onBack={() => setForgot(false)} />
  }

  const submit = async (v: Record<string, string>) => {
    setBusy(true)
    setError(null)
    try {
      const r = mode === 'login'
        ? await api.login({ handle: String(v.handle).trim(), password: v.password })
        : await api.register({
          handle: String(v.handle).trim(),
          display_name: String(v.display_name || '').trim() || String(v.handle).trim(),
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
      if (mode === 'register' && e instanceof ApiError
          && (e.status === 400 || e.status === 409)) {
        setError('账号或邮箱可能已被占用；如果邮箱已注册，请直接登录或点「忘记密码」找回')
      } else {
        setError(e instanceof Error ? e.message : '请求失败，请检查网络后重试')
      }
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

      {githubEnabled && (
        <>
          <button type="button" onClick={startGithub} disabled={busy}
            className="mb-3 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-line bg-surface px-4 text-sm font-semibold text-ink transition-colors hover:border-line-strong hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-60">
            <GithubOutlined aria-hidden="true" />
            使用 GitHub 登录
          </button>
        </>
      )}

      {wechatQrEnabled && <WechatQrLogin />}

      {(githubEnabled || wechatQrEnabled) && (
        <div className="mb-4 flex items-center gap-3 text-[11px] text-ink-3" aria-hidden="true">
          <span className="h-px flex-1 bg-line" />
          或使用邮箱
          <span className="h-px flex-1 bg-line" />
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
            <Form.Item name="display_name" label="昵称（可选）"
              normalize={v => (v || '').trim()}
              rules={[{ max: 32, message: '昵称最多 32 个字符' }]}>
              <Input placeholder="别人看到的名字，默认同账号" autoComplete="nickname" />
            </Form.Item>
            <Form.Item name="email" label="邮箱（建议填写）"
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
        {mode === 'login' && (
          <button type="button" onClick={() => setForgot(true)}
            className="mt-2 w-full text-center text-[12.5px] text-ink-3 underline-offset-2 hover:text-brand hover:underline">
            忘记密码？
          </button>
        )}
      </Form>
    </div>
  )
}

function ForgotPasswordPanel({ onBack }: { onBack: () => void }) {
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const [sent, setSent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMail = async ({ email }: { email: string }) => {
    setBusy(true)
    setError(null)
    try {
      await v1Req('/auth/password/forgot', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim() }),
      })
      setSent(true)
      message.success('如果该邮箱已注册，重置邮件已发送')
    } catch (e) {
      setError(e instanceof Error ? e.message : '发送失败，请稍后再试')
    } finally {
      setBusy(false)
    }
  }

  const reset = async (v: Record<string, string>) => {
    setBusy(true)
    setError(null)
    try {
      await v1Req('/auth/password/reset', {
        method: 'POST',
        body: JSON.stringify({ token: String(v.token).trim(), password: v.password }),
      })
      message.success('密码已重置，请用新密码登录')
      form.resetFields()
      onBack()
    } catch (e) {
      setError(e instanceof Error ? e.message : '重置失败，令牌可能已过期')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="mb-4">
        <h2 className="m-0 text-[18px] font-extrabold text-ink">找回密码</h2>
        <p className="m-0 mt-1 text-[12.5px] leading-5 text-ink-3">
          {sent ? '把邮件里的令牌和新密码填在下面。' : '输入注册邮箱，我们会发一封含重置令牌的邮件。'}
        </p>
      </div>
      <Form form={form} layout="vertical" requiredMark={false} onFinish={sent ? reset : sendMail}
        disabled={busy}>
        {!sent ? (
          <Form.Item name="email" label="注册邮箱" className="mb-3"
            rules={[{ required: true, message: '请填写邮箱' }, { type: 'email', message: '邮箱格式不正确' }]}>
            <Input placeholder="name@example.com" autoComplete="email" inputMode="email" />
          </Form.Item>
        ) : (
          <>
            <Form.Item name="token" label="邮件里的令牌" className="mb-3"
              rules={[{ required: true, message: '请填写令牌' }, { min: 10, message: '令牌不完整' }]}>
              <Input placeholder="粘贴邮件中的令牌" />
            </Form.Item>
            <Form.Item name="password" label="新密码" className="mb-3"
              rules={[{ required: true, message: '请填写新密码' }, { min: 6, message: '密码至少 6 位' }]}>
              <Input.Password placeholder="至少 6 位" autoComplete="new-password" />
            </Form.Item>
            <Form.Item name="confirm" label="确认新密码" className="mb-3"
              dependencies={['password']}
              rules={[
                { required: true, message: '请再次输入新密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    return !value || getFieldValue('password') === value
                      ? Promise.resolve()
                      : Promise.reject(new Error('两次输入不一致'))
                  },
                }),
              ]}>
              <Input.Password placeholder="再输入一次" autoComplete="new-password" />
            </Form.Item>
          </>
        )}
        <div aria-live="polite" className="mb-3">
          {error && (
            <div role="alert"
              className="rounded-md border border-danger/35 bg-danger-soft px-3 py-2 text-[12.5px] leading-5 text-danger">
              {error}
            </div>
          )}
        </div>
        <button type="submit" disabled={busy}
          className="inline-flex h-10 w-full items-center justify-center rounded-md bg-brand px-4 text-sm font-semibold text-brand-fg transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-60">
          {busy ? '提交中…' : sent ? '重置密码' : '发送重置邮件'}
        </button>
        <div className="mt-2 flex items-center justify-between text-[12.5px] text-ink-3">
          {sent ? (
            <button type="button" onClick={() => setSent(false)} className="hover:text-brand">
              换一个邮箱
            </button>
          ) : <span />}
          <button type="button" onClick={onBack} className="hover:text-brand">
            返回登录
          </button>
        </div>
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
              <Avatar user={user} size={24} />
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
