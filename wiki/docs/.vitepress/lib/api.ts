/**
 * 主站 API 的唯一入口。
 *
 * 同一个 VitePress 构建同时上两种部署：
 *   · robowiki.org.cn —— FastAPI 同源挂在 /api/v1
 *   · robowiki.github.io —— 静态镜像，跨域调用主站 API
 *
 * 因此 **任何组件都不许再自己拼 `/api/v1` 或直接 fetch API**：
 *   · apiBase()   决定“打哪儿”
 *   · apiFetch()  统一带 Bearer、序列化 JSON、解析 detail/error、401 清 token
 *   · apiAvailable()  探活 base + /health，探不到就降级成快照/只读
 *
 * base 的优先级（依次覆盖）：
 *   1. window.__ROBOWIKI_API__     运行时注入（部署/调试可覆盖，不用重新构建）
 *   2. import.meta.env.VITE_ROBOWIKI_API  构建期覆盖
 *   3. github.io 上固定主域；其余（主站 / 本地 dev）走同源 /api/v1
 *
 * 探活结果按 base 缓存：镜像站 API 挂了不该每次切页都再打一串失败请求。
 */

import { clearAuth, getRefreshToken, getToken, setRefreshToken, setToken } from './auth'

/** 有后端的主站；镜像端跨域请求这里 */
export const PRIMARY_ORIGIN = 'https://robowiki.org.cn'
/** 主站 API 根（同样用于 github.io 的跨域请求） */
export const PRIMARY_API = `${PRIMARY_ORIGIN}/api/v1`
/** 兼容旧引用：组件里的「去主站」链接 */
export const PRIMARY_SITE = PRIMARY_ORIGIN

/** 镜像站的 hostname。只有它跨域；主站/本地一律同源 */
export const MIRROR_HOSTNAME = 'robowiki.github.io'

const DEFAULT_API_PATH = '/api/v1'
/** 3s 够慢网探通；再慢就当没有，页面不能为了一个探测卡住 */
const PROBE_TIMEOUT_MS = 3000

declare global {
  interface Window {
    /** 运行时覆盖 API base（例如预发环境） */
    __ROBOWIKI_API__?: string
  }
}

/** 去掉末尾斜杠，避免拼出 `//health` */
function normalizeBase(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, '')
  return trimmed || DEFAULT_API_PATH
}

function envBase(): string | undefined {
  try {
    // 直接成员访问：Vite 只在字面形式下做构建期替换；
    // 写成 `import.meta.env?.VITE_...` 会退化成运行时属性读取，构建变量就失效了。
    return import.meta.env.VITE_ROBOWIKI_API as string | undefined
  } catch {
    // 非 Vite 环境（单测/Node）：当作没设置
    return undefined
  }
}

/** 当前 hostname 是否是构建产物要跨域打主站的那个镜像域名 */
export function isMirror(hostname?: string): boolean {
  const host = hostname
    ?? (typeof window !== 'undefined' ? window.location.hostname : '')
  return host === MIRROR_HOSTNAME
}

/**
 * 纯函数版 base 解析：方便单测 / 构建产物检查模拟 hostname，
 * 不依赖真实 window。优先级见文件头。
 */
export function resolveApiBase(
  hostname: string,
  injected?: string | null,
  env?: string | null,
): string {
  if (injected && injected.trim()) return normalizeBase(injected)
  if (env && env.trim()) return normalizeBase(env)
  return hostname === MIRROR_HOSTNAME ? PRIMARY_API : DEFAULT_API_PATH
}

/** 唯一 API base。组件只准用它，不准再写字面量 */
export function apiBase(): string {
  const injected = typeof window !== 'undefined' ? window.__ROBOWIKI_API__ : undefined
  const hostname = typeof window !== 'undefined' ? window.location.hostname : ''
  return resolveApiBase(hostname, injected, envBase())
}

/** 把 `/ratings/x` 解析成 `${apiBase()}/ratings/x`；已经是绝对地址就原样用 */
export function apiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path
  const base = apiBase()
  return `${base}${path.startsWith('/') ? '' : '/'}${path}`
}

/* ── 错误模型 ──────────────────────────────────────────────────────────── */

export type ApiErrorKind =
  | 'auth'       // 401，token 已清
  | 'rate'       // 429
  | 'network'    // 断网 / CORS / DNS
  | 'timeout'
  | 'client'     // 4xx
  | 'server'     // 5xx
  | 'http'       // 其他

export class ApiError extends Error {
  readonly status: number
  readonly kind: ApiErrorKind
  /** 后端 detail / error 原文，调用方需要判断具体原因时用 */
  readonly detail?: unknown
  readonly code?: string

  constructor(
    message: string,
    status = 0,
    kind: ApiErrorKind = 'http',
    detail?: unknown,
    code?: string,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.kind = kind
    this.detail = detail
    this.code = code
  }
}

/** 统一文案：401 / 429 / 网络错误不把后端英文原样甩给用户 */
export const MSG_AUTH = '登录已过期，请重新登录'
export const MSG_RATE = '操作太频繁，请稍等一会儿再试'
export const MSG_SERVER = '主站服务暂时不可用，请稍后重试'
export const MSG_NETWORK = '网络异常，请检查网络后重试'
export const MSG_MIRROR_NETWORK = '暂时连不上主站服务，请稍后重试；当前页面内容是构建快照'
/** github.io 上探活失败时给用户看的说明：说清「快照/只读」，不说「镜像坏了」 */
export const MIRROR_READONLY_NOTE = '主站服务暂时不可达，当前显示构建快照（只读）'

/**
 * 把任意异常转成一句能直接展示的话。
 * 统一从这里出口，避免各组件各写一套 401/429/断网文案。
 */
export function apiErrorMessage(e: unknown, fallback = '请求失败，请稍后再试'): string {
  if (e instanceof ApiError) return e.message || fallback
  if (e instanceof Error) {
    // 组件里 throw new Error(String(r.status)) 这类裸状态码不要直接展示
    if (!/^\d{3}$/.test(e.message)) return e.message || fallback
  }
  return fallback
}

/** 是否属于「网络层没通」——镜像端据此显示快照而不是故障 */
export function isConnectivityError(e: unknown): boolean {
  return e instanceof ApiError && (e.kind === 'network' || e.kind === 'timeout')
}

/* ── 请求 ──────────────────────────────────────────────────────────────── */

function pickMessage(data: unknown): string | undefined {
  if (!data || typeof data !== 'object') return undefined
  const obj = data as Record<string, unknown>
  const raw = obj.detail ?? obj.error ?? obj.message
  if (typeof raw === 'string' && raw.trim()) return raw.trim()
  if (Array.isArray(raw)) {
    // FastAPI/pydantic 422：detail 是 [{loc, msg, type}]
    const parts = raw
      .map(x => (x && typeof x === 'object' && typeof (x as any).msg === 'string'
        ? (x as any).msg
        : String(x)))
      .filter(Boolean)
    return parts.length ? parts.join('；') : undefined
  }
  if (raw && typeof raw === 'object') {
    const nested = (raw as Record<string, unknown>).message
    if (typeof nested === 'string' && nested.trim()) return nested.trim()
  }
  return undefined
}

async function readBody(res: Response): Promise<unknown> {
  if (res.status === 204 || res.status === 205) return null
  const type = res.headers.get('content-type') || ''
  try {
    if (type.includes('json')) return await res.json()
    const text = await res.text()
    if (!text) return null
    // 网关有时用 text/html 返回 JSON 错误体
    try { return JSON.parse(text) } catch { return text }
  } catch {
    return null
  }
}

function errorFrom(res: Response, data: unknown): ApiError {
  const detail = data && typeof data === 'object'
    ? (data as Record<string, unknown>).detail
      ?? (data as Record<string, unknown>).error
      ?? (data as Record<string, unknown>).message
    : data
  const code = data && typeof data === 'object'
    ? (data as Record<string, any>).code ?? (data as Record<string, any>).error_code
    : undefined
  const serverMsg = pickMessage(data)

  // 401 的文案分两种：
  //   · 资源接口（/auth/me、评论、评分）→ 统一「登录已过期」
  //   · 登录/handoff 自己返回的中文原因（账号密码不对、code 已用过）→ 原样展示
  // 判据是「后端有意写了中文」；HTTPBearer 默认的 "Not authenticated" 走统一文案。
  if (res.status === 401) {
    const readable = serverMsg && /[\u4e00-\u9fff]/.test(serverMsg) ? serverMsg : MSG_AUTH
    return new ApiError(readable, 401, 'auth', detail, code)
  }
  if (res.status === 429) return new ApiError(MSG_RATE, 429, 'rate', detail, code)
  if (res.status >= 500) {
    return new ApiError(serverMsg || MSG_SERVER, res.status, 'server', detail, code)
  }
  return new ApiError(
    serverMsg || `请求未完成（HTTP ${res.status}）`,
    res.status,
    'client',
    detail,
    code,
  )
}

/**
 * 统一请求入口。
 *
 * - 自动拼 apiBase()（绝对 URL 原样用）
 * - 自动带 `Authorization: Bearer`（lib/auth 的唯一 token）
 * - 字符串 body 自动补 `Content-Type: application/json`
 * - 成功返回解析后的 JSON（空响应返回 null）
 * - 失败抛 ApiError：detail/error 已解析，401 会清 token，429/5xx/断网用统一文案
 *
 * 需要区分 403 / 404 / 409 时读 `err.status`。
 */
type RefreshResult = 'ok' | 'auth' | 'unavailable'
let refreshInFlight: Promise<RefreshResult> | null = null

/** 同一标签页的并发 401 共用一个刷新；跨标签页用 Web Locks 串行，避免轮换重放。 */
function withRefreshLock<T>(fn: () => Promise<T>): Promise<T> {
  const locks = typeof navigator !== 'undefined'
    ? (navigator as Navigator & { locks?: { request<T>(name: string, cb: () => Promise<T>): Promise<T> } }).locks
    : undefined
  return locks?.request ? locks.request('robowiki-refresh', fn) : fn()
}

async function doRefresh(refresh: string): Promise<RefreshResult> {
  try {
    const timeout = (AbortSignal as any)?.timeout
    const signal = typeof timeout === 'function' ? timeout(8000) : undefined
    const res = await fetch(apiUrl('/auth/refresh'), {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
      cache: 'no-store',
      signal,
    })
    if (!res.ok) {
      if (res.status === 401 || res.status === 403) {
        clearAuth()
        return 'auth'
      }
      return 'unavailable'
    }
    const data = await res.json()
    if (!data || !data.access_token) {
      clearAuth()
      return 'auth'
    }
    setToken(data.access_token)
    setRefreshToken(data.refresh_token || refresh)
    return 'ok'
  } catch {
    // 断网/超时：保留 refresh，下一次请求还能再试；不能把用户误登出。
    return 'unavailable'
  }
}

async function refreshAccessToken(staleToken?: string): Promise<RefreshResult> {
  if (refreshInFlight) return refreshInFlight
  refreshInFlight = withRefreshLock(async () => {
    // 另一个标签页可能已经刷新并写回了新 access；此时不要再消费旧 refresh。
    const current = getToken()
    if (staleToken && current && current !== staleToken) return 'ok'
    const refresh = getRefreshToken()
    if (!refresh) return 'auth'
    return doRefresh(refresh)
  }).finally(() => { refreshInFlight = null })
  return refreshInFlight
}

export async function apiFetch<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Accept')) headers.set('Accept', 'application/json')

  const token = getToken()
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  // FormData 不能手动设 Content-Type（boundary 由浏览器生成）
  const isForm = typeof FormData !== 'undefined' && init.body instanceof FormData
  if (init.body && !isForm && typeof init.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const isAuthPath = path.startsWith('/auth/login') || path.startsWith('/auth/register')
    || path.startsWith('/auth/refresh') || path.startsWith('/auth/handoff')

  let res: Response
  try {
    res = await fetch(apiUrl(path), { ...init, headers })
  } catch (err: any) {
    const aborted = err?.name === 'TimeoutError' || err?.name === 'AbortError'
    throw new ApiError(
      aborted ? '请求超时，请稍后重试' : (isMirror() ? MSG_MIRROR_NETWORK : MSG_NETWORK),
      0,
      aborted ? 'timeout' : 'network',
    )
  }

  // access 过期时先尝试 refresh 一次；refresh 也失效才真正登出。
  if (res.status === 401 && !isAuthPath && getRefreshToken()) {
    const refreshed = await refreshAccessToken(token)
    if (refreshed === 'unavailable') {
      throw new ApiError(isMirror() ? MSG_MIRROR_NETWORK : MSG_NETWORK, 0, 'network')
    }
    if (refreshed === 'ok') {
      // 复用首轮 headers：Content-Type 等由 apiFetch 补的字段不能丢，
      // 否则重试的写请求会退化成 text/plain 并收到 422。
      const retryHeaders = new Headers(headers)
      const fresh = getToken()
      if (fresh) retryHeaders.set('Authorization', `Bearer ${fresh}`)
      try {
        res = await fetch(apiUrl(path), { ...init, headers: retryHeaders })
      } catch (err: any) {
        const aborted = err?.name === 'TimeoutError' || err?.name === 'AbortError'
        throw new ApiError(
          aborted ? '请求超时，请稍后重试' : (isMirror() ? MSG_MIRROR_NETWORK : MSG_NETWORK),
          0,
          aborted ? 'timeout' : 'network',
        )
      }
    }
  }

  const data = await readBody(res)
  if (res.ok) return data as T
  const error = errorFrom(res, data)
  if (error.status === 401) clearAuth()
  throw error
}

/* ── 探活 ──────────────────────────────────────────────────────────────── */

/** base → 探活结果。失败也缓存：镜像站永远探不到时不该每次切页都重试 */
const probes = new Map<string, Promise<boolean>>()

async function probeOnce(base: string): Promise<boolean> {
  try {
    const r = await fetch(`${base}/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      // 主站同源可带 cookie；跨域不带（本站鉴权只靠 Bearer）
      credentials: 'same-origin',
      cache: 'no-store',
      signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
    })
    return r.ok
  } catch {
    // 超时、断网、404、CORS、SW 拦截……一律视为「这里暂时没有后端」
    return false
  }
}

/**
 * 后端是否可用：探测 `apiBase() + /health`。
 * 失败结果同样缓存 —— 镜像站每次切页重探只会多出一串失败请求。
 */
export function apiAvailable(): Promise<boolean> {
  const base = apiBase()
  let probe = probes.get(base)
  if (!probe) {
    probe = probeOnce(base)
    probes.set(base, probe)
  }
  return probe
}

/** 只给测试/手动重试用：清掉探活缓存 */
export function resetApiProbe(): void {
  probes.clear()
}
