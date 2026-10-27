/** API 客户端 + 类型。token 存 localStorage，请求自动带 Authorization。 */

const TOKEN_KEY = 'roboselect.token'

export const auth = {
  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },
  set(token: string | null) {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  },
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...(init?.headers as any) }
  if (init?.body) headers['Content-Type'] = 'application/json'
  const t = auth.token
  if (t) headers['Authorization'] = `Bearer ${t}`

  const r = await fetch(`/api${path}`, { ...init, headers })
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

  register: (body: any) =>
    req<{ access_token: string; user: User }>('/auth/register',
      { method: 'POST', body: JSON.stringify(body) }),
  login: (body: any) =>
    req<{ access_token: string; user: User }>('/auth/login',
      { method: 'POST', body: JSON.stringify(body) }),
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
