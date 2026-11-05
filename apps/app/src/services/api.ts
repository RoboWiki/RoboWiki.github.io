import Taro from '@tarojs/taro'
import {
  ApiClient,
  ApiError,
  type ApiTransport,
  type ApiTransportRequest,
  type ApiTransportResponse,
  type TokenPair,
  type TokenStore,
  type User,
} from '@robowiki/core'

const ACCESS_KEY = 'rw.app.access'
const REFRESH_KEY = 'rw.app.refresh'
const USER_KEY = 'rw.app.user'

function read(key: string): string | null {
  try {
    const value = Taro.getStorageSync(key)
    return typeof value === 'string' && value ? value : null
  } catch {
    return null
  }
}

function write(key: string, value: string | null): void {
  try {
    if (value) Taro.setStorageSync(key, value)
    else Taro.removeStorageSync(key)
  } catch {
    // 存储不可用（隐私模式/配额满）时保持内存态，不阻断页面。
  }
}

/** token 落 Taro storage：H5 是 localStorage，小程序是 wx storage。 */
export const tokenStore: TokenStore = {
  getAccess: () => read(ACCESS_KEY),
  getRefresh: () => read(REFRESH_KEY),
  setTokens(access, refresh) {
    write(ACCESS_KEY, access)
    if (refresh !== undefined) write(REFRESH_KEY, refresh)
    if (!access) write(USER_KEY, null)
  },
  clear() {
    write(ACCESS_KEY, null)
    write(REFRESH_KEY, null)
    write(USER_KEY, null)
  },
}

export function cacheUser(user: User | null): void {
  write(USER_KEY, user ? JSON.stringify(user) : null)
}

export function cachedUser(): User | null {
  const raw = read(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

type TaroMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

/** ApiClient 的传输层：H5 与小程序共用 Taro.request。 */
class TaroTransport implements ApiTransport {
  async send(req: ApiTransportRequest): Promise<ApiTransportResponse> {
    const res = await Taro.request({
      url: req.url,
      method: (req.method || 'GET') as TaroMethod,
      header: req.headers,
      data: req.body as Taro.request.Option['data'],
      timeout: 20000,
      dataType: 'json',
    })
    return {
      status: res.statusCode,
      data: res.data,
      headers: res.header as Record<string, string> | undefined,
    }
  }
}

export const api = new ApiClient({
  baseUrl: __RW_API_BASE__,
  transport: new TaroTransport(),
  tokens: tokenStore,
  timeoutMs: 20000,
})

export const API_ORIGIN = __RW_API_BASE__.replace(/\/api\/v\d+\/?$/i, '')

/** 后端返回的相对地址（图片、媒体）补成绝对地址。 */
export function absoluteUrl(url: string | null | undefined): string {
  const value = String(url || '').trim()
  if (!value) return ''
  if (/^(https?:)?\/\//i.test(value)) return value
  if (value.startsWith('/')) return `${API_ORIGIN}${value}`
  return value
}

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401) return '登录已失效，请重新登录'
    if (err.status === 403) return '没有权限执行这个操作'
    if (err.status === 404) return '内容不存在或已被删除'
    if (err.status === 429) return '操作太频繁，请稍后再试'
    if (err.status === 503) return '服务暂未开放，请稍后再试'
    return err.message || `请求失败（${err.status}）`
  }
  if (err instanceof Error && err.message) return err.message
  return '网络异常，请检查网络后重试'
}

export async function loginWithPassword(account: string, password: string): Promise<User> {
  const pair = await api.login(account.trim(), password)
  saveSession(pair)
  return pair.user
}

/** 微信小程序：wx.login 的 code 换本站令牌。 */
export async function loginWithWechat(): Promise<User> {
  const login = await Taro.login()
  if (!login.code) throw new Error('微信登录没有返回 code，请重试')
  const pair = await api.request<TokenPair>('/auth/wechat/mini', {
    method: 'POST',
    body: { code: login.code },
  })
  saveSession(pair)
  return pair.user
}

function saveSession(pair: TokenPair): void {
  tokenStore.setTokens(pair.access_token, pair.refresh_token ?? null)
  cacheUser(pair.user)
}

/** 有 access 才请求 /auth/me；401 视为未登录，不弹错误。 */
export async function loadMe(): Promise<User | null> {
  if (!tokenStore.getAccess()) return null
  try {
    const user = await api.me()
    cacheUser(user)
    return user
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      tokenStore.clear()
      return null
    }
    return cachedUser()
  }
}

/** /reports 还没有进 core 的便捷方法，直接走通用 request。 */
export function reportComment(
  commentId: number,
  reason: 'spam' | 'abuse' | 'misinfo' | 'other',
  detail = '',
): Promise<{ id: number; status: string }> {
  return api.request('/reports', {
    method: 'POST',
    body: {
      target_kind: 'wiki_comment',
      target_id: commentId,
      reason,
      detail,
    },
  })
}

export type CatalogFacet = {
  category: string
  category_label: string
  subtype?: string
  n: number
}

export type CatalogResponse = {
  total: number
  facets: CatalogFacet[]
  categories: Record<string, string>
}

/** 品类 chips：只展示确实有条目的品类，标签取服务端，不在客户端硬编码。 */
export async function listCategories(): Promise<CatalogFacet[]> {
  const data = await api.request<CatalogResponse>('/catalog')
  const seen = new Set<string>()
  return (data.facets || [])
    .filter((f) => f && f.category && f.n > 0 && !seen.has(f.category) && seen.add(f.category))
    .map((f) => ({ ...f, category_label: f.category_label || f.category }))
}
