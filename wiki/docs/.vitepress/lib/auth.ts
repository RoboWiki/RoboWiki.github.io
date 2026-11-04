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

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(LEGACY_KEY)
  } catch { /* ignore */ }
}

export function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * OAuth 回调把令牌放在 `#token=<jwt>`。取出后**立刻**从地址栏抹掉：
 * fragment 不会发给服务器，但留在历史记录里会随刷新/分享泄露。
 *
 * 只认 `#token=` 开头（`#` 可有可无），其余 hash（文档锚点）原样保留。
 * 在 SSR / 非浏览器环境返回 null。
 */
export function consumeHashToken(): string | null {
  if (typeof window === 'undefined') return null
  const m = window.location.hash.match(/^#?token=([^&]+)/)
  if (!m) return null
  let token = m[1]
  try {
    token = decodeURIComponent(token)
  } catch { /* 不是合法编码就按原文用 */ }
  if (!token) return null
  window.history.replaceState(
    null, '', window.location.pathname + window.location.search)
  return token
}
