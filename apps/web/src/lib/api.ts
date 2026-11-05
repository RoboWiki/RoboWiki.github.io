import { ApiClient, type ApiTransport } from '@robowiki/core'

const base = import.meta.env.PUBLIC_API_BASE || 'https://robowiki.org.cn/api/v1'

const transport: ApiTransport = {
  async send(req) {
    const r = await fetch(req.url, {
      method: req.method || 'GET',
      headers: req.headers,
      body: req.body === undefined ? undefined : JSON.stringify(req.body),
    })
    const text = await r.text()
    let data: unknown = null
    try { data = text ? JSON.parse(text) : null } catch { data = text }
    return { status: r.status, data }
  },
}

const tokens = {
  getAccess: () => typeof localStorage === 'undefined' ? null : localStorage.getItem('roboselect.token'),
  getRefresh: () => typeof localStorage === 'undefined' ? null : localStorage.getItem('roboselect.refresh'),
  setTokens(access: string | null, refresh?: string | null) {
    if (typeof localStorage === 'undefined') return
    if (access) localStorage.setItem('roboselect.token', access)
    else localStorage.removeItem('roboselect.token')
    if (refresh) localStorage.setItem('roboselect.refresh', refresh)
    else if (refresh === null) localStorage.removeItem('roboselect.refresh')
  },
  clear() {
    if (typeof localStorage === 'undefined') return
    localStorage.removeItem('roboselect.token')
    localStorage.removeItem('roboselect.refresh')
  },
}

export const api = new ApiClient({ baseUrl: base, transport, tokens })
