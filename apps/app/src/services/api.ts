import Taro from 'virtual:taro/api'
import {
  ApiClient,
  ApiError,
  type ApiTransport,
  type ApiTransportRequest,
  type ApiTransportResponse,
  type Media,
  type Notification,
  type TokenPair,
  type TokenStore,
  type User,
} from '@robowiki/core'

const ACCESS_KEY = 'rw.app.access'
const REFRESH_KEY = 'rw.app.refresh'
const USER_KEY = 'rw.app.user'
/** 会话列表里显示来源：后端优先读 X-Client。 */
const CLIENT_LABEL = process.env.TARO_ENV === 'h5' ? 'h5' : 'mini'

/**
 * Taro H5 的 getStorageSync 偶尔返回 { data: '...' } 包装，
 * 不解包会让 Authorization 变成 Bearer {"data":"eyJ..."}，登录后全站 401。
 */
function unwrap(value: unknown): string | null {
  if (typeof value === 'string') return value || null
  if (value && typeof value === 'object') {
    const data = (value as { data?: unknown }).data
    if (typeof data === 'string') return data || null
  }
  return null
}

function read(key: string): string | null {
  try {
    return unwrap(Taro.getStorageSync(key))
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
      header: { 'X-Client': CLIENT_LABEL, ...(req.headers || {}) },
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
/** 图片 / 静态资源在静态站点，不在 API 域；API 请求仍走 baseUrl。 */
export const ASSET_ORIGIN = __RW_ASSET_BASE__.replace(/\/+$/, '')

/** 后端返回的相对地址（图片、媒体）补成绝对地址。 */
export function absoluteUrl(url: string | null | undefined): string {
  const value = String(url || '').trim()
  if (!value) return ''
  if (/^(https?:)?\/\//i.test(value)) return value
  if (value.startsWith('/')) return `${ASSET_ORIGIN}${value}`
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
  if (err instanceof Error && err.message) {
    if (/failed to fetch|networkerror|network request failed|timeout/i.test(err.message)) {
      return '网络异常，请检查网络后重试'
    }
    return err.message
  }
  return '网络异常，请检查网络后重试'
}

export async function loginWithPassword(account: string, password: string): Promise<User> {
  const pair = await api.login(account.trim(), password)
  saveSession(pair)
  return pair.user
}

export async function registerAccount(
  handle: string,
  displayName: string,
  password: string,
  email?: string,
): Promise<User> {
  const pair = await api.register(handle.trim(), displayName.trim(), password, email?.trim() || undefined)
  saveSession(pair)
  return pair.user
}

export async function logout(): Promise<void> {
  try {
    await api.request('/auth/logout', { method: 'POST' })
  } catch {
    // 令牌已失效也要清本地，不能把用户困在登录态。
  } finally {
    tokenStore.clear()
  }
}

export type AppNotification = Notification

export type NotificationPage = {
  total: number
  unread: number
  items: AppNotification[]
}

export function listNotifications(limit = 20): Promise<NotificationPage> {
  return api.request(`/notifications?limit=${limit}`)
}

export function markNotificationsRead(): Promise<{ ok: boolean }> {
  return api.markNotificationsRead()
}

/** 单条已读：点击通知时先标记，再决定跳转。 */
export function markNotificationRead(id: number): Promise<AppNotification> {
  return api.markNotificationRead(id)
}

/** 把改密 / 换邮箱返回的新令牌写回本地，其他页面的请求才不会 401。 */
export function applySession(pair: TokenPair): User {
  saveSession(pair)
  return pair.user
}

/**
 * 头像地址走 PATCH /auth/me；core 的 updateMe 签名还没收录 avatar_url，
 * 这里用通用 request 保持同一套鉴权 / 刷新逻辑。
 */
export async function updateAvatar(url: string): Promise<User> {
  const user = await api.request<User>('/auth/me', {
    method: 'PATCH',
    body: { avatar_url: url },
  })
  cacheUser(user)
  return user
}

/**
 * 评论配图：multipart 字段名按 backend media.py 为 `file`。
 * Taro.uploadFile 不走 ApiClient（body 是 FormData），401 需要自己报。
 */
export async function uploadImage(filePath: string): Promise<Media> {
  const access = tokenStore.getAccess()
  const res = await Taro.uploadFile({
    url: `${api.baseUrl}/media`,
    filePath,
    name: 'file',
    header: access ? { Authorization: `Bearer ${access}` } : {},
  })
  let data: unknown = null
  try {
    data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
  } catch {
    data = null
  }
  if (res.statusCode < 200 || res.statusCode >= 300) {
    const detail = (data as { detail?: unknown } | null)?.detail
    throw new ApiError(
      res.statusCode,
      typeof detail === 'string' ? detail : `上传失败（${res.statusCode}）`,
      detail,
    )
  }
  const media = data as Media | null
  if (!media || !media.url) throw new Error('上传没有返回图片地址')
  return media
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

/** 网页发起的扫码登录：把 scene 里的 ticket 与本次 wx.login 的 code 一起交给后端确认。 */
export async function confirmQrLogin(ticket: string, code: string): Promise<void> {
  await api.request<{ ok: boolean }>('/auth/wechat/qr/confirm', {
    method: 'POST',
    body: { ticket, code },
  })
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
