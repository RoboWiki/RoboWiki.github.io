/** 社区 / 后台 API 客户端。
 *
 * 默认走同源 `/api/v1`（1Panel 反向代理下与主站同域）；
 * 本地开发可用 PUBLIC_API_BASE 覆盖，例如 http://127.0.0.1:8000/api/v1。
 * 会话与 console 一致：access + refresh 两个 key，401 时单飞刷新后重试。
 */

const ACCESS_KEY = 'roboselect.token'
const REFRESH_KEY = 'roboselect.refresh'

const envBase = (import.meta.env.PUBLIC_API_BASE || '').trim()
const mirror = typeof location !== 'undefined' && /(^|\.)robowiki\.github\.io$/.test(location.hostname)
export const API_BASE = (envBase || (mirror ? 'https://robowiki.org.cn/api/v1' : '/api/v1')).replace(/\/+$/, '')

const storage = () => (typeof window === 'undefined' ? null : window.localStorage)

export const auth = {
  get token(): string | null {
    return storage()?.getItem(ACCESS_KEY) ?? null
  },
  get refreshToken(): string | null {
    return storage()?.getItem(REFRESH_KEY) ?? null
  },
  setTokens(access: string | null, refresh: string | null) {
    const s = storage()
    if (!s) return
    if (access) s.setItem(ACCESS_KEY, access)
    else s.removeItem(ACCESS_KEY)
    if (refresh) s.setItem(REFRESH_KEY, refresh)
    else s.removeItem(REFRESH_KEY)
  },
  clear() {
    const s = storage()
    s?.removeItem(ACCESS_KEY)
    s?.removeItem(REFRESH_KEY)
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let refreshing: Promise<boolean> | null = null

async function doRefresh(): Promise<boolean> {
  const rt = auth.refreshToken
  if (!rt) return false
  try {
    const r = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    })
    const data = await r.json().catch(() => null)
    if (r.status >= 400 && r.status < 500) {
      auth.clear()
      return false
    }
    if (!r.ok || !data?.access_token) return false
    auth.setTokens(data.access_token, data.refresh_token ?? rt)
    return true
  } catch {
    return false
  }
}

function refreshOnce(): Promise<boolean> {
  if (!refreshing) refreshing = doRefresh().finally(() => { refreshing = null })
  return refreshing
}

async function request<T>(path: string, init?: RequestInit, retryOnAuth = true): Promise<T> {
  const url = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  const send = (): Promise<Response> => {
    const headers: Record<string, string> = { ...(init?.headers as Record<string, string>) }
    if (init?.body) headers['Content-Type'] = 'application/json'
    const t = auth.token
    if (t) headers['Authorization'] = `Bearer ${t}`
    return fetch(url, { ...init, headers })
  }

  const sentWith = auth.token
  let r = await send()
  if (r.status === 401 && retryOnAuth && auth.refreshToken) {
    if (auth.token && auth.token !== sentWith) r = await send()
    else if (await refreshOnce()) r = await send()
  }
  const text = await r.text()
  let data: { detail?: unknown } | null = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      // 代理没指到后端时会返回 HTML 404/500，这里给出可读错误而不是 JSON 解析异常
      data = null
    }
  }
  if (!r.ok) {
    const detail = data?.detail
    const msg = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).join('；')
        : `HTTP ${r.status}`
    throw new ApiError(r.status, msg)
  }
  if (text && data === null) {
    throw new ApiError(r.status, '接口没有返回 JSON：请检查 /api 反向代理是否指向后端')
  }
  return data as T
}

export function v1Req<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, init)
}

/** 后台接口统一挂在 /admin 下，token 语义与前台相同 */
export function adminReq<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(`/admin${path}`, init)
}

export async function logoutSession(): Promise<void> {
  const rt = auth.refreshToken
  try {
    if (rt) {
      await request<{ ok: boolean }>('/auth/logout',
        { method: 'POST', body: JSON.stringify({ refresh_token: rt }) })
    }
  } catch {
    // 离线或会话已过期：本地照样清掉
  } finally {
    auth.clear()
  }
}

const qs = (o: Record<string, unknown>) => {
  const p = new URLSearchParams()
  Object.entries(o).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p.set(k, String(v))
  })
  return p.toString()
}

// ── 类型 ──────────────────────────────────────────────────────────────────
export interface User {
  id: number
  handle: string
  display_name: string
  bio: string
  avatar_hue: number
  /** 自定义头像；为空时用 avatar_hue 底色 + 首字母 */
  avatar_url?: string | null
  is_staff: boolean
  email_verified?: boolean
  reputation: number
  created_at: string
  post_count: number
  comment_count: number
  rating_count?: number
  submission_count?: number
  trust_level?: number
  trust_sources?: string[]
  handle_provisional?: boolean
  accepted_count?: number
  badges: string[]
}

/** `/auth/me` 的本人视角：比公开 User 多邮箱与口令状态。 */
export interface Account extends User {
  email?: string | null
  password_set?: boolean
  email_notify?: boolean
}

export interface AuthSession {
  id: number
  client: string
  created_at: string
  expires_at: string
}

export interface Identity {
  provider: string
  subject: string
  email: string | null
  created_at: string
}

export interface Notification {
  id: number
  type: string
  subject: string
  body: string
  link: string | null
  read_at: string | null
  created_at: string
}

export interface NotificationList {
  total: number
  unread: number
  limit: number
  offset: number
  items: Notification[]
}

export interface Media {
  id: string
  url: string
  content_type: string
  size: number
}

export interface SubmissionReview {
  id: number
  decision: string
  reason_code: string
  note: string
  reviewer_id: number | null
  created_at: string
}

export interface Submission {
  id: number
  kind: string
  target_id: string | null
  payload: Record<string, unknown>
  evidence: Record<string, unknown>
  submitter_id: number | null
  status: string
  revision: number
  created_at: string
  reviews: SubmissionReview[]
}

export interface Part {
  id: string
  category: string
  category_label?: string
  subtype: string
  subtype_label: string
  vendor: string
  vendor_cn?: string | null
  model: string
  title?: string
  url: string | null
  source_tier: string
  verified: boolean
  last_checked: string | null
  price_cny: number | null
  specs: Record<string, unknown>
  derived: Record<string, unknown>
  notes: string
  origin?: string | null
  image_url?: string | null
  posts?: Post[]
}

export interface Post {
  id: number
  kind: 'discussion' | 'review' | 'build'
  title: string
  body: string
  tags: string[]
  part_id: string | null
  part_title: string | null
  rating: number | null
  use_case: string | null
  own_hardware: boolean
  score: number
  comment_count: number
  view_count: number
  pinned: boolean
  created_at: string
  updated_at?: string | null
  accepted_comment_id?: number | null
  author: User | null
  my_vote: number
}

export interface Comment {
  id: number
  post_id: number
  parent_id: number | null
  body: string
  score: number
  created_at: string
  accepted?: boolean
  author: User | null
  my_vote: number
  replies: Comment[]
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  user: User
}

export interface PostList {
  total: number
  limit: number
  offset: number
  items: Post[]
}

// ── 端点 ──────────────────────────────────────────────────────────────────
export const api = {
  posts: (p: Record<string, unknown>) => request<PostList>(`/posts?${qs(p)}`),
  post: (id: number) => request<Post>(`/posts/${id}`),
  createPost: (body: unknown) =>
    request<Post>('/posts', { method: 'POST', body: JSON.stringify(body) }),
  updatePost: (id: number, body: unknown) =>
    request<Post>(`/posts/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deletePost: (id: number) =>
    request<void>(`/posts/${id}`, { method: 'DELETE' }),

  comments: (postId: number) => request<Comment[]>(`/posts/${postId}/comments`),
  createComment: (postId: number, body: unknown) =>
    request<Comment>(`/posts/${postId}/comments`, { method: 'POST', body: JSON.stringify(body) }),
  acceptComment: (postId: number, commentId: number) =>
    request<Post>(`/posts/${postId}/accept`,
      { method: 'POST', body: JSON.stringify({ comment_id: commentId }) }),
  unacceptComment: (postId: number) =>
    request<Post>(`/posts/${postId}/accept`, { method: 'DELETE' }),

  vote: (target_kind: 'post' | 'comment', target_id: number, value: number) =>
    request<{ score: number; my_vote: number }>('/votes',
      { method: 'POST', body: JSON.stringify({ target_kind, target_id, value }) }),

  parts: (p: Record<string, unknown>) =>
    request<{ total: number; items: Part[] }>(`/parts?${qs(p)}`),

  user: (handle: string) => request<User>(`/users/${encodeURIComponent(handle)}`),
  leaderboard: (limit = 10) => request<User[]>(`/leaderboard?limit=${limit}`),

  report: (body: { target_kind: string; target_id: number; reason: string; detail: string }) =>
    request<{ id: number }>('/reports', { method: 'POST', body: JSON.stringify(body) }),

  // 登录/注册的 401 是凭据错误，不是 access 过期：不触发刷新重试
  register: (body: unknown) =>
    request<TokenPair>('/auth/register', { method: 'POST', body: JSON.stringify(body) }, false),
  login: (body: unknown) =>
    request<TokenPair>('/auth/login', { method: 'POST', body: JSON.stringify(body) }, false),
  logout: logoutSession,
  me: () => request<Account>('/auth/me'),
  /** 公开端点：哪些第三方登录已配置。GitHub 按钮只在 github=true 时出现。 */
  providers: () => request<{ email: boolean; github: boolean; wechat_mini: boolean }>(
    '/auth/providers', undefined, false),
  updateMe: (body: {
    display_name?: string
    bio?: string
    avatar_hue?: number
    avatar_url?: string | null
    email_notify?: boolean
  }) => request<Account>('/auth/me', { method: 'PATCH', body: JSON.stringify(body) }),

  sessions: () => request<AuthSession[]>('/auth/sessions'),
  revokeSession: (id: number) =>
    request<void>(`/auth/sessions/${id}`, { method: 'DELETE' }),
  logoutAll: () =>
    request<{ ok: boolean; revoked: number; session_epoch?: number }>(
      '/auth/logout-all', { method: 'POST' }),

  identities: () => request<Identity[]>('/auth/identities'),
  unlinkIdentity: (provider: string) =>
    request<{ ok: boolean; provider: string; remaining: number }>(
      `/auth/identities/${encodeURIComponent(provider)}`, { method: 'DELETE' }),

  changePassword: (current_password: string, new_password: string) =>
    request<TokenPair>('/auth/password/change',
      { method: 'POST', body: JSON.stringify({ current_password, new_password }) }),
  setPassword: (password: string) =>
    request<TokenPair>('/auth/password/set',
      { method: 'POST', body: JSON.stringify({ password }) }),

  notifications: (p: Record<string, unknown> = {}) =>
    request<NotificationList>(`/notifications?${qs(p)}`),
  readNotification: (id: number) =>
    request<Notification>(`/notifications/${id}/read`, { method: 'POST' }),
  readAllNotifications: () =>
    request<{ updated: number }>('/notifications/read-all', { method: 'POST' }),

  mySubmissions: (limit = 50) =>
    request<Submission[]>(`/submissions/mine?limit=${limit}`),
  exportAccount: () => request<unknown>('/auth/export'),
}

/** 相对媒体地址在镜像站需要补上 API 源，否则 `/api/v1/media/…` 会落到静态站。 */
export function assetUrl(url: string | null | undefined): string | null {
  if (!url) return null
  if (/^(https?:)?\/\//i.test(url) || url.startsWith('data:') || url.startsWith('blob:')) return url
  const base = API_BASE.replace(/\/+$/, '')
  // `/media/x` 是后端规范化的头像路径（相对于 API 前缀），不是站点根路径。
  if (url.startsWith('/media/')) {
    if (/^https?:/i.test(base)) {
      const api = new URL(base)
      return `${api.origin}${api.pathname.replace(/\/$/, '')}${url}`
    }
    return `${base}${url}`
  }
  if (url.startsWith('/') && /^https?:/i.test(base)) return new URL(url, base).href
  return url
}

const mediaError = async (r: Response): Promise<ApiError> => {
  const text = await r.text().catch(() => '')
  let detail: unknown = null
  try {
    detail = text ? JSON.parse(text).detail : null
  } catch {
    detail = null
  }
  const msg = typeof detail === 'string' ? detail
    : Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('；')
      : `上传失败（HTTP ${r.status}）`
  return new ApiError(r.status, msg)
}

/** multipart 上传单独走一条路径：request() 会强制 JSON Content-Type。 */
export async function uploadMedia(file: File): Promise<Media> {
  const send = (): Promise<Response> => {
    const headers: Record<string, string> = {}
    const t = auth.token
    if (t) headers.Authorization = `Bearer ${t}`
    const form = new FormData()
    form.append('file', file)
    return fetch(`${API_BASE}/media`, { method: 'POST', headers, body: form })
  }

  const sentWith = auth.token
  let r = await send()
  if (r.status === 401 && auth.refreshToken) {
    if (auth.token && auth.token !== sentWith) r = await send()
    else if (await refreshOnce()) r = await send()
  }
  if (!r.ok) throw await mediaError(r)
  const text = await r.text()
  try {
    return JSON.parse(text) as Media
  } catch {
    throw new ApiError(r.status, '上传接口没有返回 JSON')
  }
}

export const KIND_LABEL: Record<string, string> = {
  discussion: '讨论',
  review: '评价',
  build: '整机方案',
}
export const KIND_COLOR: Record<string, string> = {
  discussion: 'blue',
  review: 'green',
  build: 'purple',
}

/** 站内链接统一带 BASE_PATH，和静态站部署前缀保持一致 */
export function siteHref(path: string): string {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}
