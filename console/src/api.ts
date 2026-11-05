/** API 客户端 + 类型。token 存 localStorage，请求自动带 Authorization。
 *
 * 会话与网页端一致：access（短寿命）+ refresh（可轮换）。401 时用 refresh
 * 换一对新 token 再重试原请求；refresh 也失效才清空本地会话。
 */

const ACCESS_KEY = 'roboselect.token'
const REFRESH_KEY = 'roboselect.refresh'

export const auth = {
  get token(): string | null {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY)
  },
  /** 登录 / 刷新成功后同时写入两项 */
  setTokens(access: string | null, refresh: string | null) {
    if (access) localStorage.setItem(ACCESS_KEY, access)
    else localStorage.removeItem(ACCESS_KEY)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
    else localStorage.removeItem(REFRESH_KEY)
  },
  /** 兼容旧调用：只写 access，不动 refresh */
  set(token: string | null) {
    if (token) localStorage.setItem(ACCESS_KEY, token)
    else localStorage.removeItem(ACCESS_KEY)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** 模块级单飞：并发 401 只触发一次刷新，其余请求等同一个 Promise */
let refreshing: Promise<boolean> | null = null

async function doRefresh(): Promise<boolean> {
  const rt = auth.refreshToken
  if (!rt) return false
  try {
    const r = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    })
    const data = await r.json().catch(() => null)
    // 4xx：refresh 已被撤销或过期 → 会话确定失效，清本地；
    // 5xx 是服务端临时故障，保留 refresh 等下次
    if (r.status >= 400 && r.status < 500) {
      auth.clear()
      return false
    }
    if (!r.ok || !data?.access_token) return false
    auth.setTokens(data.access_token, data.refresh_token ?? rt)
    return true
  } catch {
    // 网络错误 / 服务暂时不可达：保留 refresh，下次请求再试
    return false
  }
}

function refreshOnce(): Promise<boolean> {
  if (!refreshing) refreshing = doRefresh().finally(() => { refreshing = null })
  return refreshing
}

/** 统一请求：拼好完整 URL，401 时刷新一次并重试 */
async function request<T>(url: string, init?: RequestInit, retryOnAuth = true): Promise<T> {
  const send = (): Promise<Response> => {
    const headers: Record<string, string> = { ...(init?.headers as any) }
    if (init?.body) headers['Content-Type'] = 'application/json'
    const t = auth.token
    if (t) headers['Authorization'] = `Bearer ${t}`
    return fetch(url, { ...init, headers })
  }

  const sentWith = auth.token
  let r = await send()
  if (r.status === 401 && retryOnAuth && auth.refreshToken) {
    // 并发 401：若别的请求已经把 access 换新，直接重试，不重复刷新
    if (auth.token && auth.token !== sentWith) r = await send()
    else if (await refreshOnce()) r = await send()
  }
  const text = await r.text()
  const data = text ? JSON.parse(text) : null
  if (!r.ok) {
    const detail = data?.detail
    const msg = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map((d: any) => d.msg).join('；')
        : `HTTP ${r.status}`
    throw new ApiError(r.status, msg)
  }
  return data as T
}

async function req<T>(path: string, init?: RequestInit, retryOnAuth = true): Promise<T> {
  return request<T>(`/api${path}`, init, retryOnAuth)
}

/** v1 规范接口（非 /admin 前缀），带同一份 Bearer token */
export async function v1Req<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(`/api/v1${path}`, init)
}

/** 退出：先撤销服务端会话，再清理本地（撤销失败不阻塞退出） */
export async function logoutSession(): Promise<void> {
  const rt = auth.refreshToken
  try {
    if (rt) {
      await v1Req<{ ok: boolean }>('/auth/logout',
        { method: 'POST', body: JSON.stringify({ refresh_token: rt }) })
    }
  } catch {
    // 离线 / access 与 refresh 都过期：本地照样清掉
  } finally {
    auth.clear()
  }
}

const qs = (o: Record<string, any>) => {
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
  is_staff: boolean
  reputation: number
  created_at: string
  post_count: number
  comment_count: number
  badges: string[]
}

export interface Part {
  id: string
  category: string
  category_label: string
  subtype: string
  subtype_label: string
  vendor: string
  vendor_cn: string | null
  model: string
  title: string
  url: string | null
  source_tier: string
  verified: boolean
  last_checked: string | null
  price_cny: number | null
  specs: Record<string, any>
  derived: Record<string, any>
  notes: string
  origin: string | null
  image_url?: string | null
  offers?: any[]
  posts?: Post[]
  review_count?: number
  rating_avg?: number | null
  top_review?: {
    id: number
    title: string
    excerpt: string
    score: number
    rating: number | null
    own_hardware: boolean
    author: { handle: string; display_name: string; avatar_hue: number; reputation: number } | null
  } | null
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
  author: User | null
  my_vote: number
  replies: Comment[]
}

export interface Catalog {
  total: number
  categories: Record<string, string>
  subtypes: Record<string, string>
  facets: { category: string; category_label: string; subtype: string; subtype_label: string; n: number }[]
  vendors: { vendor: string; n: number }[]
  sortable: string[]
}

/** 登录 / 注册 / 刷新共用的会话响应 */
export interface TokenPair {
  access_token: string
  refresh_token: string
  user: User
}

// ── 端点 ──────────────────────────────────────────────────────────────────
export const api = {
  health: () => req<{ ok: boolean; project: string }>('/health'),
  stats: () => req<Record<string, number>>('/stats'),
  catalog: (category?: string) => req<Catalog>(`/catalog?${qs({ category })}`),

  parts: (p: Record<string, any>) =>
    req<{ total: number; limit: number; offset: number; items: Part[] }>(`/parts?${qs(p)}`),
  part: (id: string) => req<Part>(`/parts/${encodeURIComponent(id)}`),

  posts: (p: Record<string, any>) =>
    req<{ total: number; limit: number; offset: number; items: Post[] }>(`/posts?${qs(p)}`),
  post: (id: number) => req<Post>(`/posts/${id}`),
  createPost: (body: any) =>
    req<Post>('/posts', { method: 'POST', body: JSON.stringify(body) }),

  comments: (postId: number) => req<Comment[]>(`/posts/${postId}/comments`),
  createComment: (postId: number, body: any) =>
    req<Comment>(`/posts/${postId}/comments`, { method: 'POST', body: JSON.stringify(body) }),

  vote: (target_kind: 'post' | 'comment', target_id: number, value: number) =>
    req<{ score: number; my_vote: number }>('/votes',
      { method: 'POST', body: JSON.stringify({ target_kind, target_id, value }) }),

  user: (handle: string) => req<User>(`/users/${encodeURIComponent(handle)}`),
  leaderboard: (limit = 10) => req<User[]>(`/leaderboard?limit=${limit}`),

  // 登录/注册的 401 是「凭据不对」，不是 access 过期：不触发刷新重试
  register: (body: any) =>
    req<TokenPair>('/auth/register',
      { method: 'POST', body: JSON.stringify(body) }, false),
  login: (body: any) =>
    req<TokenPair>('/auth/login',
      { method: 'POST', body: JSON.stringify(body) }, false),
  logout: logoutSession,
  me: () => req<User>('/auth/me'),

  exportDraft: (ids?: string[]) =>
    req<{ n: number; actuators_yaml: string; mjcf_joints: any[]; note: string }>(
      `/export/draft?${qs({ ids: ids?.join(',') })}`),
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
