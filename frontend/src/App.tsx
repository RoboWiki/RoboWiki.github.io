import { App as AntApp, Button, ConfigProvider, Form, Input, Modal, Segmented, theme as antdTheme } from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { auth, api, type User } from './api'
import { Composer } from './ui'
import Catalog from './Catalog'
import Admin from './Admin'
import { CommunityPage, PostPage, ProfilePage, SemanticsPage, TopPage } from './pages'

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

function AuthModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { setUser } = useAuth()
  const { message } = AntApp.useApp()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [form] = Form.useForm()

  const submit = async () => {
    const v = await form.validateFields()
    try {
      const r = mode === 'login' ? await api.login({ handle: v.handle, password: v.password })
        : await api.register(v)
      auth.set(r.access_token)
      setUser(r.user)
      message.success(mode === 'login' ? `欢迎回来，${r.user.display_name}` : '注册成功')
      form.resetFields()
      onClose()
    } catch (e: any) {
      message.error(e.message)
    }
  }

  return (
    <Modal open={open} onCancel={onClose} footer={null} title={null} width={400} destroyOnHidden>
      <div className="mb-4 text-center">
        <div className="text-[22px] font-extrabold tracking-tight">
          Robo<span className="text-blue-600">Select</span>
        </div>
        <div className="mt-1 text-[12.5px] text-slate-500">
          选型是底座，真实反馈才是值钱的部分
        </div>
      </div>
      <Segmented block value={mode} style={{ marginBottom: 16 }}
        onChange={v => setMode(v as any)}
        options={[{ label: '登录', value: 'login' }, { label: '注册', value: 'register' }]} />
      <Form form={form} layout="vertical" onFinish={submit}>
        <Form.Item name="handle" label="账号" rules={[{ required: true, min: 2 }]}>
          <Input placeholder="字母数字，用作主页地址" autoComplete="username" />
        </Form.Item>
        {mode === 'register' && (
          <Form.Item name="display_name" label="显示名" rules={[{ required: true }]}>
            <Input placeholder="别人看到的名字" />
          </Form.Item>
        )}
        <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
          <Input.Password placeholder="至少 6 位" autoComplete="current-password" />
        </Form.Item>
        <Button type="primary" block onClick={submit}>
          {mode === 'login' ? '登录' : '注册并登录'}
        </Button>
      </Form>
      <div className="mt-3.5 text-[11.5px] text-slate-400">
        演示账号：<code>lcs</code> / <code>wangh</code> / <code>tinybot</code>，密码都是 <code>roboselect</code>
      </div>
    </Modal>
  )
}

const NAV = [
  { key: 'catalog', to: '/', label: '选型台' },
  { key: 'community', to: '/community', label: '社区' },
  { key: 'people', to: '/top', label: '贡献榜' },
  { key: 'semantics', to: '/semantics', label: '口径' },
  { key: 'admin', to: '/admin', label: '后台' },
]

function Shell() {
  const [user, setUserState] = useState<User | null>(null)
  const [ready, setReady] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [composer, setComposer] = useState<{ open: boolean; partId?: string; kind?: string }>({ open: false })
  const nav = useNavigate()
  const loc = useLocation()
  const qc = useQueryClient()

  useEffect(() => {
    if (!auth.token) { setReady(true); return }
    api.me().then(u => setUserState(u)).catch(() => auth.set(null)).finally(() => setReady(true))
  }, [])

  const setUser = useCallback((u: User | null) => setUserState(u), [])
  const logout = useCallback(() => { auth.set(null); setUserState(null); qc.clear() }, [qc])
  const ctx = useMemo<AuthCtx>(() => ({
    user, ready, setUser, logout, openAuth: () => setAuthOpen(true),
  }), [user, ready, setUser, logout])

  const section = loc.pathname.startsWith('/community') || loc.pathname.startsWith('/post') ? 'community'
    : loc.pathname.startsWith('/top') || loc.pathname.startsWith('/u/') ? 'people'
      : loc.pathname.startsWith('/semantics') ? 'semantics'
        : loc.pathname.startsWith('/admin') ? 'admin' : 'catalog'

  return (
    <Ctx.Provider value={ctx}>
      {/* 顶栏：白底 + 终端药丸品牌标（VS Code 风） */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-[#f3f3f3]/95 backdrop-blur">
        <div className="mx-auto flex h-[56px] max-w-[1240px] items-center gap-5 px-5">
          <Link to="/" className="terminal-pill shrink-0" title="RoboSelect 选型台">
            roboselect@parts:~$
          </Link>

          <nav className="hidden items-center gap-0.5 sm:flex">
            {NAV.map(n => {
              const on = section === n.key
              return (
                <Link key={n.key} to={n.to}
                  className={`relative px-3 py-[18px] text-[13px] transition
                    ${on ? 'font-semibold text-blue-600' : 'text-slate-500 hover:text-slate-800'}`}>
                  {n.label}
                  {on && (
                    <span className="absolute inset-x-2.5 bottom-0 h-[2px] rounded-t bg-blue-600" />
                  )}
                </Link>
              )
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => user ? setComposer({ open: true }) : setAuthOpen(true)}
              className="rounded-full bg-blue-600 px-4 py-[7px] text-[13px] font-semibold
                         text-white transition hover:bg-blue-700">
              发帖
            </button>
            {user ? (
              <div className="relative">
                <button onClick={() => setMenuOpen(v => !v)}
                  className="flex items-center gap-1.5 rounded-full border border-slate-200
                             bg-white py-[3px] pl-[3px] pr-3 transition hover:border-slate-300">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold text-white"
                    style={{ background: `hsl(212 72% 45%)` }}>
                    {user.display_name.slice(0, 1)}
                  </span>
                  <span className="text-[12.5px] text-slate-800">{user.display_name}</span>
                </button>
                {menuOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                    <div className="absolute right-0 z-20 mt-1.5 w-40 overflow-hidden rounded-lg border
                                    border-slate-200 bg-white py-1 shadow-[0_8px_18px_rgba(0,0,0,0.09)]">
                      <Link to={`/u/${user.handle}`} onClick={() => setMenuOpen(false)}
                        className="block px-3 py-2 text-[12.5px] text-slate-700 hover:bg-slate-100">
                        我的主页
                      </Link>
                      <button onClick={() => { setMenuOpen(false); logout() }}
                        className="flex w-full items-center gap-1.5 px-3 py-2 text-left text-[12.5px]
                                   text-slate-500 hover:bg-slate-100">
                        <LogoutOutlined className="text-[11px]" /> 退出登录
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <button onClick={() => setAuthOpen(true)}
                className="rounded-full border border-slate-200 bg-white px-4 py-[7px]
                           text-[13px] text-slate-700 transition hover:border-slate-300 hover:text-slate-900">
                登录
              </button>
            )}
          </div>
        </div>
        {/* 移动端导航 */}
        <nav className="flex gap-1 overflow-x-auto border-t border-slate-100 px-4 pb-2 pt-1 sm:hidden">
          {NAV.map(n => (
            <Link key={n.key} to={n.to}
              className={`whitespace-nowrap rounded-md px-2.5 py-1 text-[12.5px]
                ${section === n.key ? 'bg-slate-100 font-semibold text-slate-900' : 'text-slate-500'}`}>
              {n.label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-[1240px] px-5 pb-24 pt-6">
        <Routes>
          <Route path="/" element={<Catalog
            onOpenPost={id => nav(`/post/${id}`)}
            onCompose={partId => user ? setComposer({ open: true, partId, kind: 'review' }) : setAuthOpen(true)}
            openAuth={() => setAuthOpen(true)} />} />
          <Route path="/community" element={<CommunityPage onOpenPost={id => nav(`/post/${id}`)} openAuth={() => setAuthOpen(true)} />} />
          <Route path="/post/:id" element={<PostPage />} />
          <Route path="/u/:handle" element={<ProfilePage onOpenPost={id => nav(`/post/${id}`)} />} />
          <Route path="/top" element={<TopPage />} />
          <Route path="/semantics" element={<SemanticsPage />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>

      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
      <Composer open={composer.open} defaultPartId={composer.partId} defaultKind={composer.kind}
        onClose={() => setComposer({ open: false })} />
    </Ctx.Provider>
  )
}

export default function App() {
  return (
    <ConfigProvider theme={{
      // VS Code 2026 浅色：中性灰 + #0078d4，8px 圆角
      algorithm: antdTheme.defaultAlgorithm,
      token: {
        colorPrimary: '#0078d4',
        colorInfo: '#0078d4',
        colorLink: '#0078d4',
        colorSuccess: '#107c10',
        colorWarning: '#a06a00',
        colorError: '#c02b2b',
        borderRadius: 8,
        colorBgBase: '#ffffff',
        colorBgContainer: '#ffffff',
        colorBgLayout: '#f3f3f3',
        colorBorder: '#d0d0d0',
        colorBorderSecondary: '#e6e6e6',
        colorText: '#1f1f1f',
        colorTextSecondary: '#616161',
        colorTextTertiary: '#8a8a8a',
        fontSize: 14,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", '
          + '"Microsoft YaHei", "Noto Sans SC", Roboto, sans-serif',
      },
      components: {
        Table: { headerBg: '#f8f8f8', headerColor: '#616161', rowHoverBg: '#f8f8f8' },
        Modal: { contentBg: '#ffffff', headerBg: '#ffffff' },
        Card: { headerBg: 'transparent' },
        Segmented: {
          itemSelectedBg: '#0078d4',
          itemSelectedColor: '#ffffff',
          itemHoverBg: '#e8e8e8',
          itemHoverColor: '#1f1f1f',
          trackBg: '#f8f8f8',
        },
      },
    }}>
      <AntApp>
        <Shell />
      </AntApp>
    </ConfigProvider>
  )
}
