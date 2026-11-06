import 'antd/dist/reset.css'
import { Alert, Button } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { ApiError, api, auth, siteHref, v1Req, type TokenPair } from '@/lib/community-api'
import { AuthForm, IslandProvider } from './providers'

type Phase = 'checking' | 'form' | 'done'

const ACCOUNT_TARGET = '/account.html'

function Bridge() {
  const [phase, setPhase] = useState<Phase>('checking')
  const [error, setError] = useState<string | null>(null)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true

    const hash = window.location.hash.replace(/^#/, '')
    const params = new URLSearchParams(hash)
    const token = params.get('token')
    const code = params.get('code')
    const next = params.get('next') || new URLSearchParams(window.location.search).get('next')

    // next=account 时回账号中心；其余一律回社区。不接受任意 URL，避免开放跳转。
    const target = next === 'account' ? siteHref(ACCOUNT_TARGET) : siteHref('/community.html')
    // 账号页发起的 GitHub 授权会先离开站点：只认账号页这一个回跳落点。
    let saved: string | null = null
    try {
      saved = window.sessionStorage.getItem('rw-auth-return')
      window.sessionStorage.removeItem('rw-auth-return')
    } catch {
      // 隐私模式可能禁用 sessionStorage；回跳落点退回默认值。
    }
    const back = saved === '/account.html' ? siteHref(saved) : target
    const go = () => { window.location.replace(back) }

    if (!token && !code) { setPhase('form'); return }

    // 一次性 code / token 不留在地址栏，避免刷新重放
    window.history.replaceState(null, '', window.location.pathname + window.location.search)

    const run = async () => {
      try {
        if (code) {
          const r = await v1Req<TokenPair>('/auth/handoff', {
            method: 'POST',
            body: JSON.stringify({ code }),
          })
          auth.setTokens(r.access_token, r.refresh_token)
        } else if (token) {
          auth.setTokens(token, null)
          // token 交接只带 access：用 /auth/me 确认可用并拿到账号
          const me = await api.me()
          if (!me?.handle) throw new ApiError(401, '登录凭证无效或已过期')
        }
        setPhase('done')
        go()
      } catch (e) {
        auth.clear()
        setError(e instanceof Error ? e.message : '登录凭证无效或已过期')
        setPhase('form')
      }
    }
    void run()
  }, [])

  if (phase === 'checking') {
    return (
      <div className="card p-5" aria-live="polite">
        <div className="space-y-2 animate-pulse" aria-hidden="true">
          <div className="h-3 w-24 rounded bg-surface-3" />
          <div className="h-9 w-full rounded-md bg-surface-3" />
          <div className="h-9 w-full rounded-md bg-surface-3" />
        </div>
        <p className="mb-0 mt-3 text-[12px] text-ink-3">正在校验登录凭证…</p>
      </div>
    )
  }

  return (
    <div className="card p-5">
      {/* 错误固定在表单上方，出现时不再顶动按钮位置 */}
      <div aria-live="assertive" className={error ? 'mb-4' : ''}>
        {error && (
          <Alert type="error" showIcon title={error}
            description="凭证只能用一次，且 60 秒内有效；可以重新登录，或回 App 重新发起。"
            action={<a href={siteHref('/community.html')}><Button size="small">回社区</Button></a>} />
        )}
      </div>

      <AuthForm onSuccess={() => { window.location.replace(siteHref('/community.html')) }} />
    </div>
  )
}

export default function LoginBridge() {
  return (
    <IslandProvider>
      <div className="mx-auto max-w-[420px]">
        <Bridge />
      </div>
    </IslandProvider>
  )
}
