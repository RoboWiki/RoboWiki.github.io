/**
 * 站点 / 控制台共用的登录态。
 *
 * 唯一写入键是 roboselect.token。历史上站点早期写过 robowiki.token，
 * 现在只做**只读兼容**：读的时候新键优先、旧键兜底；不再在读取时顺手
 * 搬家 —— 读取函数带写副作用会在并发组件里互相覆盖，也会让「只是看一眼
 * 有没有登录」变成一次存储写操作。签名登录 / 退出时才显式改写两个键。
 *
 * 新代码不要直接碰 localStorage，一律走这里。
 */
const TOKEN_KEY = 'roboselect.token'
const LEGACY_KEY = 'robowiki.token'
const REFRESH_KEY = 'roboselect.refresh'

export function getToken(): string | null {
  try {
    const current = localStorage.getItem(TOKEN_KEY)
    if (current) return current
    return localStorage.getItem(LEGACY_KEY)
  } catch {
    /* 隐私模式禁用存储：当作未登录，不中断页面 */
    return null
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
    // 旧键留着会让「新键被清掉后旧 token 复活」，写入即清
    localStorage.removeItem(LEGACY_KEY)
  } catch { /* ignore */ }
}

export function getRefreshToken(): string | null {
  try { return localStorage.getItem(REFRESH_KEY) } catch { return null }
}

export function setRefreshToken(token: string | null | undefined): void {
  try {
    if (token) localStorage.setItem(REFRESH_KEY, token)
    else localStorage.removeItem(REFRESH_KEY)
  } catch { /* ignore */ }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(LEGACY_KEY)
  } catch { /* ignore */ }
}

/** 退出 / refresh 失效：access 与 refresh 一起清，避免半登录状态。 */
export function clearAuth(): void {
  clearToken()
  setRefreshToken(null)
}

export function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export type HashAuth = {
  /** 兼容旧回调：`#token=<jwt>` 直接就是登录令牌 */
  token?: string
  /** 新回调（跨域镜像）：`#code=<一次性兑换码>`，需 POST /auth/handoff */
  code?: string
  /** OAuth 失败时后端/网关带回的 `#error=` */
  error?: string
  errorDescription?: string
}

function decode(value: string | null): string | undefined {
  if (!value) return undefined
  try {
    return decodeURIComponent(value) || undefined
  } catch {
    return value || undefined
  }
}

/**
 * 读取地址栏 fragment 里的登录结果，**不改地址栏**。
 * 解析失败（比如文档锚点 `#section`）返回空对象。
 */
export function readHashAuth(): HashAuth {
  if (typeof window === 'undefined') return {}
  const raw = window.location.hash.replace(/^#/, '')
  if (!raw) return {}
  const params = new URLSearchParams(raw)
  const result: HashAuth = {
    token: decode(params.get('token')),
    code: decode(params.get('code')),
    error: decode(params.get('error')) || decode(params.get('error_code')),
    errorDescription: decode(params.get('error_description')),
  }
  return result.token || result.code || result.error ? result : {}
}

/** 把登录结果从地址栏抹掉：fragment 不发服务器，但会留在历史/分享链接里 */
export function clearHashAuth(): void {
  if (typeof window === 'undefined') return
  const auth = readHashAuth()
  if (!auth.token && !auth.code && !auth.error) return
  window.history.replaceState(
    null, '', window.location.pathname + window.location.search)
}

/**
 * 兼容入口：OAuth 回调用 `#token=<jwt>` 时取令牌并清理 fragment。
 * 新代码请用 readHashAuth() / clearHashAuth()，把「读」和「清理」分开 ——
 * `#code=` 要先换 token 成功再清理，不能读到就抹。
 */
export function consumeHashToken(): string | null {
  const { token } = readHashAuth()
  if (!token) return null
  clearHashAuth()
  return token
}
