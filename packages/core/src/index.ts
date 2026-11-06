export type ApiTransportRequest = {
  url: string
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  headers?: Record<string, string>
  body?: unknown
}

export type ApiTransportResponse = {
  status: number
  data: unknown
  headers?: Record<string, string>
}

export interface ApiTransport {
  send(req: ApiTransportRequest): Promise<ApiTransportResponse>
}

export interface TokenStore {
  getAccess(): string | null
  getRefresh(): string | null
  setTokens(access: string | null, refresh?: string | null): void
  clear(): void
}

export class ApiError extends Error {
  status: number
  detail?: unknown
  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export type User = {
  id: number
  handle: string
  display_name: string
  bio?: string
  avatar_hue?: number
  email?: string | null
  email_verified?: boolean
  email_notify?: boolean
  password_set?: boolean
  is_staff?: boolean
}

export type TokenPair = {
  access_token: string
  refresh_token?: string | null
  user: User
}

export type PartSummary = {
  id: string
  slug?: string
  category: string
  category_label?: string
  subtype?: string
  subtypeLabel?: string
  subtype_label?: string
  vendor: string
  vendor_cn?: string
  title?: string
  model: string
  url?: string | null
  source_tier?: string
  last_checked?: string | null
  price_cny?: number | null
  web_path?: string
  image_url?: string | null
  key_specs?: Array<{ key: string; label: string; value: string }>
  tier?: string
  verified?: boolean
  price?: number | null
  image?: string | null
  tauPeak?: number | null
  tauRated?: number | null
  gear?: number | null
  mass?: number | null
  rpm?: number | null
  rating?: { avg?: number | null; count?: number }
  specs?: Record<string, unknown>
  notes?: string
}

export type PartList = {
  total: number
  limit: number
  offset: number
  data_version?: string
  items: PartSummary[]
}

export type ReproductionSummary = {
  build_id: string
  total: number
  success: number
  partial: number
  failed: number
  updated_at?: string | null
  created?: boolean
  mine?: {
    outcome: 'success' | 'partial' | 'failed'
    changes?: string
    note?: string
    updated_at?: string
  } | null
}

export type RatingSummary = {
  count: number
  avg: number | null
  histogram: Record<string, number>
  dims_avg?: Record<string, number> | null
  dims_n?: Record<string, number> | null
  own_hardware_count?: number | null
  own_hardware_avg?: number | null
  usage_count?: number | null
  low_sample?: boolean
  mine?: {
    score: number
    own_hardware: boolean
    note?: string
    updated_at?: string
    hidden?: boolean
  } | null
}

export type Comment = {
  id: number
  page: string
  body: string
  parent_id: number | null
  root_id?: number | null
  status?: 'visible' | 'pending' | 'hidden'
  deleted?: boolean
  created_at: string
  author?: { id?: number; handle: string; display_name: string; is_staff?: boolean }
}

export type CommentList = {
  page: string
  count: number
  comments: Comment[]
}

export type AuthSession = {
  id: number
  client: string
  created_at: string
  expires_at: string
}

export type Identity = {
  provider: string
  subject: string
  email?: string | null
  created_at: string
}

export type Media = {
  id: string
  url: string
  content_type: string
  size: number
}

export type Notification = {
  id: number
  type: string
  subject: string
  body: string
  link: string | null
  read_at: string | null
  created_at: string
}

export type NotificationList = {
  total: number
  unread: number
  limit: number
  offset: number
  items: Notification[]
}

export type Submission = {
  id: number
  kind: string
  target_id: string | null
  payload: Record<string, unknown>
  evidence: Record<string, unknown>
  submitter_id?: number | null
  status: string
  revision: number
  created_at: string
  reviews?: Array<{
    id: number
    decision: string
    reason_code: string
    note: string
    reviewer_id?: number | null
    created_at: string
  }>
}

export type SubmissionIn = {
  kind?: 'part_patch'
  target_id?: string | null
  payload: Record<string, unknown>
  evidence: Record<string, unknown>
}

export type ApiOptions = {
  baseUrl: string
  transport: ApiTransport
  tokens: TokenStore
  timeoutMs?: number
}

const AUTH_PATHS = ['/auth/login', '/auth/register', '/auth/refresh']

function join(base: string, path: string): string {
  if (/^https?:\/\//i.test(path)) return path
  return `${base.replace(/\/+$/, '')}${path.startsWith('/') ? '' : '/'}${path}`
}

export class ApiClient {
  private refreshing: Promise<boolean> | null = null

  constructor(private opts: ApiOptions) {}

  get baseUrl(): string {
    return this.opts.baseUrl.replace(/\/+$/, '')
  }

  private async refresh(): Promise<boolean> {
    if (this.refreshing) return this.refreshing
    this.refreshing = (async () => {
      const refresh = this.opts.tokens.getRefresh()
      if (!refresh) return false
      try {
        const r = await this.opts.transport.send({
          url: join(this.baseUrl, '/auth/refresh'),
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: { refresh_token: refresh },
        })
        if (r.status === 401 || r.status === 403) {
          this.opts.tokens.clear()
          return false
        }
        if (r.status < 200 || r.status >= 300) return false
        const d = r.data as TokenPair
        this.opts.tokens.setTokens(d.access_token, d.refresh_token || refresh)
        return true
      } catch {
        return false
      }
    })().finally(() => { this.refreshing = null })
    return this.refreshing
  }

  async request<T>(path: string, init: Omit<ApiTransportRequest, 'url'> = {}): Promise<T> {
    const access = this.opts.tokens.getAccess()
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...(init.headers || {}),
    }
    if (init.body !== undefined && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }
    if (access) headers.Authorization = `Bearer ${access}`
    const run = () => this.opts.transport.send({
      url: join(this.baseUrl, path),
      method: init.method || 'GET',
      headers,
      body: init.body,
    })
    let r = await run()
    if (r.status === 401 && access && !AUTH_PATHS.some(p => path.startsWith(p))
        && this.opts.tokens.getRefresh()) {
      if (await this.refresh()) {
        headers.Authorization = `Bearer ${this.opts.tokens.getAccess()}`
        r = await run()
      }
    }
    if (r.status < 200 || r.status >= 300) {
      const detail = (r.data as any)?.detail ?? (r.data as any)?.error
      const message = typeof detail === 'string' ? detail
        : Array.isArray(detail) ? detail.map((x: any) => x.msg).join('；')
          : `HTTP ${r.status}`
      throw new ApiError(r.status, message, detail)
    }
    return r.data as T
  }

  meta() {
    return this.request<{ data_version: string; site_url: string }>('/meta')
  }

  listParts(params: {
    q?: string
    category?: string
    limit?: number
    offset?: number
    compact?: boolean
  } = {}) {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '' && v !== null) q.set(k, String(v))
    })
    const s = q.toString()
    return this.request<PartList>(`/parts${s ? `?${s}` : ''}`)
  }

  getPart(id: string) {
    return this.request<PartSummary>(`/parts/${encodeURIComponent(id)}`)
  }

  getRating(partId: string) {
    return this.request<RatingSummary>(`/ratings/${encodeURIComponent(partId)}`)
  }

  putRating(partId: string, body: {
    score: number
    own_hardware?: boolean
    note?: string
    /** 使用时长分档：long / short / unboxed */
    usage_level?: string
    /** 理由标签（白名单，最多 3 个） */
    reason_tags?: string[]
  }) {
    return this.request<RatingSummary & { created?: boolean }>(
      `/ratings/${encodeURIComponent(partId)}`, { method: 'POST', body })
  }

  deleteRating(partId: string) {
    return this.request<void>(`/ratings/${encodeURIComponent(partId)}`, { method: 'DELETE' })
  }

  // 方案复现记录：与部件评分分开，回答的是「装不装得出来」。
  getReproductions(buildId: string) {
    return this.request<ReproductionSummary>(`/reproductions/${encodeURIComponent(buildId)}`)
  }

  recordReproduction(buildId: string, body: {
    outcome: 'success' | 'partial' | 'failed'
    changes?: string
    note?: string
  }) {
    return this.request<ReproductionSummary & { created?: boolean }>(
      `/reproductions/${encodeURIComponent(buildId)}`, { method: 'POST', body })
  }

  listComments(page: string) {
    return this.request<CommentList>(`/wiki/comments?page=${encodeURIComponent(page)}`)
  }

  addComment(page: string, body: string, parentId?: number) {
    return this.request<Comment>('/wiki/comments', {
      method: 'POST',
      body: { page, body, parent_id: parentId ?? null },
    })
  }

  deleteComment(id: number) {
    return this.request<void>(`/wiki/comments/${id}`, { method: 'DELETE' })
  }

  login(handle: string, password: string) {
    return this.request<TokenPair>('/auth/login', {
      method: 'POST', body: { handle, password },
    })
  }

  register(handle: string, displayName: string, password: string, email?: string) {
    return this.request<TokenPair>('/auth/register', {
      method: 'POST',
      body: { handle, display_name: displayName, password, email: email || undefined },
    })
  }

  me() {
    return this.request<User>('/auth/me')
  }

  updateMe(patch: {
    display_name?: string
    bio?: string
    avatar_hue?: number
    email_notify?: boolean
  }) {
    return this.request<User>('/auth/me', { method: 'PATCH', body: patch })
  }

  listSessions() {
    return this.request<AuthSession[]>('/auth/sessions')
  }

  revokeSession(id: number) {
    return this.request<void>(`/auth/sessions/${id}`, { method: 'DELETE' })
  }

  logoutAll() {
    return this.request<{ ok: boolean }>('/auth/logout-all', { method: 'POST' })
  }

  listIdentities() {
    return this.request<Identity[]>('/auth/identities')
  }

  unlinkIdentity(provider: string) {
    return this.request<{ ok: boolean; provider: string; remaining: number }>(
      `/auth/identities/${encodeURIComponent(provider)}`, { method: 'DELETE' })
  }

  /** 改密会 bump session_epoch：返回的新令牌必须立刻替换本地旧令牌。 */
  changePassword(currentPassword: string, newPassword: string) {
    return this.request<TokenPair>('/auth/password/change', {
      method: 'POST',
      body: { current_password: currentPassword, new_password: newPassword },
    })
  }

  setPassword(password: string) {
    return this.request<TokenPair>('/auth/password/set', {
      method: 'POST', body: { password },
    })
  }

  requestEmailChange(email: string, password?: string) {
    return this.request<{ ok: boolean; email: string }>('/auth/email/change/request', {
      method: 'POST',
      body: { email, ...(password ? { password } : {}) },
    })
  }

  confirmEmailChange(token: string) {
    return this.request<TokenPair>('/auth/email/change/confirm', {
      method: 'POST', body: { token },
    })
  }

  listNotifications(limit = 20, offset = 0) {
    return this.request<NotificationList>(
      `/notifications?limit=${limit}&offset=${offset}`)
  }

  markNotificationRead(id: number) {
    return this.request<Notification>(`/notifications/${id}/read`, { method: 'POST' })
  }

  markNotificationsRead() {
    return this.request<{ ok: boolean }>('/notifications/read-all', { method: 'POST' })
  }

  createSubmission(body: SubmissionIn) {
    return this.request<Submission>('/submissions', { method: 'POST', body })
  }

  mySubmissions(limit = 10) {
    return this.request<Submission[]>(`/submissions/mine?limit=${limit}`)
  }
}
