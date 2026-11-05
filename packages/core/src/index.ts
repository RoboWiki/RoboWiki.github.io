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
  subtype?: string
  subtypeLabel?: string
  vendor: string
  model: string
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

export type RatingSummary = {
  count: number
  avg: number | null
  histogram: Record<string, number>
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

  listParts(params: { q?: string; category?: string; limit?: number; offset?: number } = {}) {
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

  putRating(partId: string, body: { score: number; own_hardware?: boolean; note?: string }) {
    return this.request<RatingSummary & { created?: boolean }>(
      `/ratings/${encodeURIComponent(partId)}`, { method: 'POST', body })
  }

  deleteRating(partId: string) {
    return this.request<void>(`/ratings/${encodeURIComponent(partId)}`, { method: 'DELETE' })
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
}
