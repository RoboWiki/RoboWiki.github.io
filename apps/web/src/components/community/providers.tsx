import {
  Alert, App as AntApp, Button, ConfigProvider, Form, Input, Modal, Segmented, theme as antdTheme,
} from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query'
import {
  createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode,
} from 'react'
import { ApiError, api, auth, siteHref, type User } from '@/lib/community-api'

// ── 基础 Provider ─────────────────────────────────────────────────────────
const TOKENS = {
  colorPrimary: '#0078d4',
  colorInfo: '#0078d4',
  colorLink: '#0078d4',
  colorWarning: '#a06a00',
  colorError: '#c02b2b',
  colorBgBase: '#ffffff',
  colorBgContainer: '#ffffff',
  colorBgLayout: '#ffffff',
  colorBorder: '#d0d0d0',
  colorBorderSecondary: '#e6e6e6',
  colorText: '#1f1f1f',
  colorTextSecondary: '#616161',
  colorTextTertiary: '#8a8a8a',
}

export function IslandProvider({ children }: { children: ReactNode }) {
  const [qc] = useState(() => new QueryClient({
    defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 15_000 } },
  }))
  return (
    <QueryClientProvider client={qc}>
      <ConfigProvider theme={{
        algorithm: antdTheme.defaultAlgorithm,
        token: {
          ...TOKENS,
          borderRadius: 8,
          fontSize: 14,
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", '
            + '"Microsoft YaHei", "Noto Sans SC", Roboto, sans-serif',
        },
        components: {
          Table: { headerBg: '#f8f8f8', headerColor: '#616161', rowHoverBg: '#f8f8f8' },
          Card: { headerBg: 'transparent' },
          Segmented: {
            itemSelectedBg: '#0078d4',
            itemSelectedColor: '#ffffff',
            itemHoverBg: '#e8e8e8',
            trackBg: '#f8f8f8',
          },
        },
      }}>
        <AntApp>
          <AuthProvider>{children}</AuthProvider>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
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
        <div className="mb-4 text-center">
          <div className="text-[22px] font-extrabold tracking-tight">
            Robo<span className="text-blue-600">Wiki</span>
          </div>
          <div className="mt-1 text-[12.5px] text-slate-500">选型是底座，真实反馈才是值钱的部分</div>
        </div>
      )}
      <Segmented block value={mode} style={{ marginBottom: 16 }} disabled={busy}
        onChange={v => {
          setMode(v as 'login' | 'register')
          setError(null)
          form.setFieldValue('password', '')
        }}
        options={[{ label: '登录', value: 'login' }, { label: '注册', value: 'register' }]} />
      <Form form={form} layout="vertical" onFinish={submit} disabled={busy} autoComplete="on">
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
        <Form.Item name="password" label="密码"
          rules={[
            { required: true, message: '请填写密码' },
            { min: 6, message: '密码至少 6 位' },
            { max: 128 },
          ]}>
          <Input.Password placeholder="至少 6 位"
            autoComplete={mode === 'register' ? 'new-password' : 'current-password'} />
        </Form.Item>
        {error && <Alert className="mb-3" type="error" showIcon title={error} />}
        <Button type="primary" block htmlType="submit" loading={busy} disabled={busy}>
          {mode === 'login' ? '登录' : '注册并登录'}
        </Button>
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
      className={`rounded-lg px-2.5 py-1.5 text-[13px] transition ${
        current ? 'bg-slate-100 font-semibold text-slate-900' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
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
    <div className="mb-5 flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
      <a href={siteHref('/')} className="mr-1 text-[15px] font-extrabold tracking-tight text-slate-900">
        社区<span className="ml-1 rounded-full border border-slate-300 px-1.5 py-[1px] text-[10px] font-semibold text-slate-500">RoboWiki</span>
      </a>
      <nav className="flex items-center gap-0.5" aria-label="社区导航">
        <NavLink href="/community.html" label="社区" current={current === 'community'} />
        <NavLink href="/top.html" label="贡献榜" current={current === 'top'} />
        <NavLink href="/catalog.html" label="部件库 ↗" />
        {user?.is_staff && <NavLink href="/admin.html" label="后台" current={current === 'admin'} />}
      </nav>

      <div className="ml-auto flex items-center gap-2">
        {onCompose && (
          <button onClick={() => (user ? onCompose() : openAuth())}
            className="min-h-9 rounded-full bg-blue-600 px-3.5 text-[13px] font-semibold text-white transition hover:bg-blue-700">
            发帖
          </button>
        )}
        {!ready ? <span className="text-[12px] text-slate-400">…</span> : user ? (
          <div className="relative">
            <button onClick={() => setMenuOpen(v => !v)}
              className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white py-[3px] pl-[3px] pr-2.5 transition hover:border-slate-300"
              aria-haspopup="menu" aria-expanded={menuOpen}>
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-[11px] font-bold text-white">
                {user.display_name.slice(0, 1)}
              </span>
              <span className="max-w-[110px] truncate text-[12.5px] text-slate-800">{user.display_name}</span>
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div role="menu"
                  className="absolute right-0 z-20 mt-1.5 w-40 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
                  <a role="menuitem" href={siteHref(`/u.html?handle=${encodeURIComponent(user.handle)}`)} onClick={() => setMenuOpen(false)}
                    className="block px-3 py-2 text-[12.5px] text-slate-700 hover:bg-slate-100">
                    我的主页
                  </a>
                  <button role="menuitem" onClick={() => { setMenuOpen(false); logout() }}
                    className="flex w-full items-center gap-1.5 px-3 py-2 text-left text-[12.5px] text-slate-500 hover:bg-slate-100">
                    <LogoutOutlined className="text-[11px]" /> 退出登录
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <>
            <button onClick={openAuth}
              className="min-h-9 rounded-full border border-slate-200 bg-white px-3.5 text-[13px] text-slate-700 transition hover:border-slate-300 hover:text-slate-900">
              登录
            </button>
            <a href={siteHref('/login.html')}
              className="hidden text-[12px] text-slate-400 hover:text-slate-700 sm:inline">登录遇到问题？</a>
          </>
        )}
      </div>
    </div>
  )
}
