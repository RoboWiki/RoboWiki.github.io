<script setup lang="ts">
/**
 * 页面讨论串。
 *
 * 两种后端，运行时探测，谁在就用谁：
 *   · 有 FastAPI（本地 / 带 Python 的部署）→ 自托管：能聚合进社区、能算贡献、能进搜索
 *   · 纯静态（GitHub Pages）→ giscus：写评论要 GitHub 账号，反垃圾与编辑历史由 GitHub 兜住
 *
 * 不做成配置开关，是因为**同一个构建要同时服务两种部署形态**。
 * 页面标识两边都用路径（等价 giscus 的 `mapping: pathname`）：改标题不掉讨论，改路径才会。
 *
 * 自托管讨论要后端，所以**先探活再决定**：探不到就进入只读镜像态，
 * 既不发请求，也不显示「加载失败」—— 那是把降级说成故障。
 *
 * P1 契约（backend/app/api/routes/wiki.py）：
 *   · 分页按根讨论做：`root_limit` / `root_offset`，回复随根一起返回；
 *   · `root_id` 把整棵子树绑在同一个根上，回复的回复不会再变成孤儿；
 *   · `status=visible|pending|hidden`：pending 只有作者与站务可见；
 *   · 删除是软删除：`deleted=true` 的占位节点保留线程形状，正文不再返回。
 * 前端组树仍按 parent_id；`root_id` 只用于「刷新某一棵子树」与通知锚点定位。
 *
 * 评论树参考 Artalk（MIT）的「一次取回、前端组树」；P1 起改成
 * 「按根分页、按根刷新」—— 根多了不会一次拉整页，回复后也只重取那一棵。
 * 举报复用现有 /reports 契约（target_kind=wiki_comment），不在前端自研审核。
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useData, useRoute } from 'vitepress'
import { giscus as giscusCfg } from '../giscus'
import { ApiError, apiAvailable, apiBase, apiErrorMessage, apiFetch, apiUrl, isConnectivityError, isMirror, MIRROR_READONLY_NOTE, PRIMARY_SITE } from '../lib/api'
import { clearToken, getToken } from '../lib/auth'

const { isDark } = useData()
const route = useRoute()

const giscusHost = ref<HTMLElement | null>(null)
const mode = ref<'probe' | 'self' | 'giscus' | 'readonly'>('probe')
/** 后端可用性：null = 还没探完。探不到就是静态镜像，走只读态 */
const apiUp = ref<boolean | null>(null)

function mountGiscus() {
  if (!giscusCfg || !giscusHost.value) return
  giscusHost.value.innerHTML = ''
  const s = document.createElement('script')
  s.src = 'https://giscus.app/client.js'
  s.async = true
  s.crossOrigin = 'anonymous'
  const mapping = giscusCfg.mapping ?? 'pathname'
  const attrs: Record<string, string> = {
    'data-repo': giscusCfg.repo,
    'data-repo-id': giscusCfg.repoId,
    'data-category': giscusCfg.category,
    'data-category-id': giscusCfg.categoryId,
    'data-mapping': mapping,
    'data-strict': '0',
    'data-reactions-enabled': giscusCfg.reactionsEnabled ?? '1',
    'data-emit-metadata': '0',
    'data-input-position': giscusCfg.inputPosition ?? 'top',
    'data-theme': isDark.value ? 'dark' : 'light',
    'data-lang': giscusCfg.lang ?? 'zh-CN',
  }
  // specific 模式用稳定的 term（不含 base、不含 .html）：
  // 否则仓库改名（域名从 zeitvex.github.io/RoboWiki/ 换成 robowiki.github.io/）会让所有讨论改键、集体消失。
  if (mapping === 'specific') attrs['data-term'] = pageId.value
  for (const [k, v] of Object.entries(attrs)) s.setAttribute(k, v)
  giscusHost.value.appendChild(s)
}

/** 主题切换要通知 iframe，否则评论框会一直停在旧配色 */
function syncGiscusTheme() {
  const frame = document.querySelector<HTMLIFrameElement>('iframe.giscus-frame')
  frame?.contentWindow?.postMessage(
    { giscus: { setConfig: { theme: isDark.value ? 'dark' : 'light' } } },
    'https://giscus.app',
  )
}

interface Author {
  id?: number
  handle: string
  display_name: string
  avatar_hue: number
  reputation: number
  is_staff: boolean
}
interface Comment {
  id: number
  page: string
  body: string
  parent_id: number | null
  /** P1：整棵子树共享的根 id；旧后端没有该字段 */
  root_id?: number | null
  /** P1：visible | pending | hidden */
  status?: string
  /** P1 软删除：占位节点，body 为空 */
  deleted?: boolean
  deleted_at?: string | null
  hidden?: boolean
  created_at: string
  author: Author | null
}
interface CommentPage {
  comments?: Comment[]
  count?: number
  total?: number
  root_total?: number
  root_limit?: number
  root_offset?: number
}
type CommentState = 'visible' | 'pending' | 'deleted' | 'hidden'
type TreeNode = Comment & { children: TreeNode[] }

interface Me {
  id: number
  handle: string
  display_name: string
  is_staff: boolean
}

const items = ref<Comment[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const body = ref('')
const replyTo = ref<Comment | null>(null)
const error = ref('')
const notice = ref('')
/** 探活通过但取数失败（后端刚挂 / 网关超时）——这种才叫失败，静态镜像走的是 readonly 态 */
const offline = ref(false)
const posting = ref(false)
const loggedIn = ref(false)
const me = ref<Me | null>(null)

/** 根讨论分页：每页 24 条根，回复随根返回，不单独分页 */
const PAGE_SIZE = 24
/** 旧后端没有根分页参数时，limit 仍按 API 上限取回整页，再由前端截根 */
const ROW_LIMIT = 200
/** P1：服务端返回 root_total 时按 root_offset 翻页；否则退回前端截根 */
const serverPaged = ref(false)
const rootTotal = ref<number | null>(null)
/** 服务端已加载的根数（root_offset 的游标）；本地上屏的新根不计入 */
const rootsLoaded = ref(0)
/** 旧后端的前端截根数量 */
const visibleRoots = ref(PAGE_SIZE)
/** 通知链接 #comment-<id> 定位到的评论 */
const highlightId = ref<number | null>(null)
/** 已经按锚点翻过页；避免同一条通知反复触发翻页 */
let hashHandled = ''

/* ── 评论配图 ──────────────────────────────────────────────────────────── */
/** 与后端 settings.media_max_bytes 一致；改这里要同时改后端与提示文案 */
const MEDIA_MAX_BYTES = 5 * 1024 * 1024
const MEDIA_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const mediaReady = ref(false)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const uploads = ref<{ id: string; url: string }[]>([])
/**
 * /media 是否存在：每个浏览器会话只探一次。
 * GET /media 需要登录且返回自己的上传列表 —— 200 即接口已就绪；
 * 404/405/501 说明后端版本还没有媒体路由，按钮直接隐藏，不影响文字评论。
 */
let mediaProbe: Promise<boolean> | null = null

/** 举报只走现有 /reports 契约：reason 必须是 spam / abuse / misinfo / other */
const REPORT_REASONS = [
  { value: 'spam', label: '垃圾广告 / 刷屏' },
  { value: 'abuse', label: '人身攻击 / 辱骂' },
  { value: 'misinfo', label: '错误信息 / 误导' },
  { value: 'other', label: '其他' },
] as const
const reportFor = ref<number | null>(null)
const reportReason = ref<string>('spam')
const reportDetail = ref('')
const reportBusy = ref(false)

/**
 * /wiki/parts/actuator/dm.html → parts/actuator/dm
 *
 * 注意：VitePress 的 route.path **包含 base**（本站 base = '/wiki/'），
 * 所以要先剥掉 BASE_URL，否则查到的永远是空线程 —— 两边 page 标识对不上。
 */
const BASE = import.meta.env.BASE_URL.replace(/\/$/, '')   // '/wiki' 或 ''

const pageId = computed(() => {
  let p = route.path
  if (BASE && p.startsWith(BASE)) p = p.slice(BASE.length)
  p = p.replace(/^\/+|\/+$/g, '').replace(/\.html$/, '')
  return p || 'index'
})

const loginHref = computed(() =>
  `/login?redirect=${encodeURIComponent(route.path)}`)

function token(): string | null {
  return getToken()
}

function clearSession() {
  clearToken()
  loggedIn.value = false
  me.value = null
}

/** 登录态以 /auth/me 为准：只认 token 存在会在 token 过期后仍显示可写 UI */
async function refreshSession() {
  loggedIn.value = !!token()
  me.value = null
  if (!loggedIn.value || !apiUp.value) return
  try {
    me.value = await apiFetch<Me>('/auth/me')
    loggedIn.value = true
  } catch (e) {
    // 401 已由 apiFetch 清 token；其它错误（断网/CORS）保留 token，写操作时再判
    if (!getToken()) {
      loggedIn.value = false
      me.value = null
    }
  }
}

/** 镜像站断网时切成只读快照，不把「主站暂时连不上」说成故障 */
function goReadonlyIfMirror(e: unknown): boolean {
  if (isMirror() && isConnectivityError(e)) {
    mode.value = 'readonly'
    error.value = ''
    offline.value = false
    return true
  }
  return false
}

/* ── 取数与组树 ────────────────────────────────────────────────────────── */

function commentState(c: Comment): CommentState {
  if (c.deleted || c.deleted_at) return 'deleted'
  if (c.status === 'pending') return 'pending'
  if (c.status === 'hidden' || c.hidden) return 'hidden'
  return 'visible'
}

function countRoots(list: Comment[]): number {
  return list.filter(c => c.parent_id == null).length
}

function fetchComments(opts: { rootOffset?: number; rootId?: number } = {}) {
  const params = new URLSearchParams({
    page: pageId.value,
    limit: String(ROW_LIMIT),
    root_limit: String(PAGE_SIZE),
  })
  if (opts.rootOffset != null) params.set('root_offset', String(opts.rootOffset))
  if (opts.rootId != null) params.set('root_id', String(opts.rootId))
  return apiFetch<CommentPage>(`/wiki/comments?${params.toString()}`)
}

/** P1 返回 root_total 才走服务端根分页；旧后端继续用前端截根 */
function applyPaging(page: CommentPage | null | undefined) {
  const total = page?.root_total
  serverPaged.value = typeof total === 'number'
  rootTotal.value = serverPaged.value ? Number(total) : null
}

let loadSeq = 0

async function load() {
  // 探活没通过就一个请求都不发：镜像端这里调一次只会拿到失败并渲染成故障
  if (!apiUp.value) return
  const seq = ++loadSeq
  loading.value = true
  error.value = ''
  offline.value = false
  loadingMore.value = false
  try {
    const d = await fetchComments()
    if (seq !== loadSeq) return
    const list = Array.isArray(d?.comments) ? d.comments : []
    items.value = list
    applyPaging(d)
    rootsLoaded.value = countRoots(list)
    visibleRoots.value = PAGE_SIZE
    await focusHashComment()
  } catch (e: any) {
    if (seq !== loadSeq) return
    if (goReadonlyIfMirror(e)) return
    // 走到这里说明探活过了但请求失败（后端刚挂 / 网关超时），这才是真的「加载失败」
    offline.value = true
    error.value = apiErrorMessage(e, '讨论加载失败，请稍后重试')
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

/** 继续加载下一批根讨论（服务端分页）；旧后端只增加前端截根数量。返回是否成功 */
async function loadMore(silent = false): Promise<boolean> {
  if (!silent) error.value = ''
  if (!serverPaged.value) {
    visibleRoots.value += PAGE_SIZE
    return true
  }
  if (loadingMore.value) return false
  if (rootTotal.value != null && rootsLoaded.value >= rootTotal.value) return false
  loadingMore.value = true
  try {
    const d = await fetchComments({ rootOffset: rootsLoaded.value })
    const list = Array.isArray(d?.comments) ? d.comments : []
    const known = new Set(items.value.map(c => c.id))
    items.value = items.value.concat(list.filter(c => !known.has(c.id)))
    rootsLoaded.value += countRoots(list)
    applyPaging(d)
    return true
  } catch (e: any) {
    if (!goReadonlyIfMirror(e)) {
      error.value = apiErrorMessage(e, '加载更多讨论失败，请稍后重试')
    }
    return false
  } finally {
    loadingMore.value = false
  }
}

/* ── 根定位 ────────────────────────────────────────────────────────────── */

/** 沿 parent 链找根；优先用 P1 的 root_id（父节点可能不在当前页） */
function rootKeyOf(c: Comment, index?: Map<number, Comment>): number | null {
  const byId = index ?? new Map(items.value.map(x => [x.id, x]))
  if (c.parent_id == null) return c.id
  if (c.root_id != null) return c.root_id
  let cur: Comment | undefined = c
  const seen = new Set<number>()
  while (cur && cur.parent_id != null && !seen.has(cur.id)) {
    seen.add(cur.id)
    if (cur.root_id != null) return cur.root_id
    cur = byId.get(cur.parent_id)
  }
  return cur && cur.parent_id == null ? cur.id : null
}

/**
 * 只刷新一棵子树：回复 / 删除后不需要重新拉整页，
 * 也从通知锚点定位时避免把用户已经翻到的页重置回第一页。
 */
async function refreshRoot(rootId: number | null) {
  if (rootId == null || !serverPaged.value) {
    await load()
    return
  }
  const d = await fetchComments({ rootId })
  const list = Array.isArray(d?.comments) ? d.comments : []
  const index = new Map(items.value.map(c => [c.id, c]))
  // 原位替换，别把刚回复过的根讨论挪到列表末尾
  const at = items.value.findIndex(c => rootKeyOf(c, index) === rootId)
  const keep = items.value.filter(c => rootKeyOf(c, index) !== rootId)
  const known = new Set(keep.map(c => c.id))
  const added = list.filter(c => !known.has(c.id))
  const insertAt = at >= 0 ? Math.min(at, keep.length) : keep.length
  items.value = keep.slice(0, insertAt).concat(added, keep.slice(insertAt))
  if (!list.length) {
    // 整棵根被隐藏且没有可见后代：服务端不再返回它
    if (rootTotal.value != null) rootTotal.value = Math.max(0, rootTotal.value - 1)
    rootsLoaded.value = Math.max(0, rootsLoaded.value - 1)
  }
}

function scrollToComment(id: number) {
  const el = document.getElementById(`comment-${id}`)
  if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

/**
 * 通知里的 `link` 是 `/{page}#comment-<id>`：
 * 目标可能不在第一页根讨论里，按需往后翻（最多 20 页，避免坏锚点把整线程拉完）。
 */
async function focusHashComment() {
  if (typeof window === 'undefined') return
  const m = /^#comment-(\d+)$/.exec(window.location.hash)
  if (!m) return
  if (hashHandled === window.location.hash) return
  const id = Number(m[1])
  if (!Number.isFinite(id)) return
  hashHandled = window.location.hash
  highlightId.value = id
  let guard = 0
  while (serverPaged.value && rootTotal.value != null
    && !items.value.some(c => c.id === id)
    && rootsLoaded.value < rootTotal.value && guard < 20) {
    const ok = await loadMore(true)
    if (!ok) break
    guard += 1
  }
  await nextTick()
  if (items.value.some(c => c.id === id)) scrollToComment(id)
}

function onHashChange() {
  hashHandled = ''
  void focusHashComment()
}

/* ── 写操作 ────────────────────────────────────────────────────────────── */

async function submit() {
  if (!loggedIn.value) {
    error.value = '请先登录再发言'
    return
  }
  // 与后端 WikiCommentIn 一致：1–4000 字。前端先拦一道，省一次必然 422 的请求
  const text = body.value.trim()
  if (text.length < 2) {
    error.value = '至少写 2 个字'
    return
  }
  posting.value = true
  error.value = ''
  notice.value = ''
  const parentId = replyTo.value?.id ?? null
  try {
    const created = await apiFetch<Comment>('/wiki/comments', {
      method: 'POST',
      body: JSON.stringify({
        page: pageId.value,
        body: text,
        parent_id: parentId,
      }),
    })
    body.value = ''
    replyTo.value = null
    notice.value = commentState(created) === 'pending'
      ? '已提交，审核通过后公开'
      : '已发表'

    if (parentId == null) {
      // 新根按时间正序排在最后，可能不在当前已加载的根里：先本地补上，
      // 保证作者立刻能看到自己刚发的内容（下次翻页按 id 去重）。
      if (!items.value.some(c => c.id === created.id)) {
        items.value = items.value.concat(created)
      }
    } else {
      // 已经发成功了：刷新失败不能再报「发言失败」
      try {
        await refreshRoot(created.root_id ?? null)
      } catch (e2: any) {
        if (goReadonlyIfMirror(e2)) return
        notice.value = '已发表；列表刷新失败，请手动刷新页面'
      }
    }
    highlightId.value = created.id
    await nextTick()
    scrollToComment(created.id)
  } catch (e: any) {
    if (e instanceof ApiError && e.status === 401) {
      clearSession()
      error.value = '登录已过期，请重新登录后再发言'
      return
    }
    if (goReadonlyIfMirror(e)) {
      notice.value = ''
      error.value = MIRROR_READONLY_NOTE
      return
    }
    error.value = apiErrorMessage(e, '发言失败，请稍后重试')
  } finally {
    posting.value = false
  }
}

function startReply(c: Comment) {
  if (!loggedIn.value) {
    error.value = '请先登录再回复'
    return
  }
  if (commentState(c) !== 'visible') {
    error.value = commentState(c) === 'pending'
      ? '这条讨论正在审核，暂不能回复'
      : '这条讨论已被删除'
    return
  }
  replyTo.value = c
  error.value = ''
  notice.value = ''
}

function canDelete(c: Comment): boolean {
  if (!me.value || commentState(c) === 'deleted') return false
  if (me.value.is_staff) return true
  const author = c.author
  if (!author) return false
  return author.handle === me.value.handle
    || (typeof author.id === 'number' && author.id === me.value.id)
}

async function remove(c: Comment) {
  if (!loggedIn.value) {
    error.value = '请先登录'
    return
  }
  const rootId = rootKeyOf(c)
  const hasReplies = items.value.some(x => x.parent_id === c.id)
  if (hasReplies && typeof window !== 'undefined'
      && !window.confirm('删除后这条内容会变成「已删除」占位，下面的回复仍会保留。确定删除？')) {
    return
  }
  error.value = ''
  notice.value = ''
  try {
    await apiFetch(`/wiki/comments/${c.id}`, { method: 'DELETE' })
    notice.value = '已删除'
    try {
      await refreshRoot(rootId)
    } catch (e2: any) {
      if (goReadonlyIfMirror(e2)) return
      notice.value = '已删除；列表刷新失败，请手动刷新页面'
    }
  } catch (e: any) {
    if (e instanceof ApiError) {
      if (e.status === 401) {
        clearSession()
        error.value = '登录已过期，请重新登录'
        return
      }
      if (e.status === 404) {
        notice.value = '这条讨论已经不在了'
        await refreshRoot(rootId)
        return
      }
    }
    if (goReadonlyIfMirror(e)) {
      error.value = MIRROR_READONLY_NOTE
      return
    }
    error.value = apiErrorMessage(e, '删除失败，请稍后重试')
  }
}

function toggleReport(c: Comment) {
  if (!loggedIn.value) {
    error.value = '举报需要登录，请先登录'
    return
  }
  if (commentState(c) !== 'visible') return
  error.value = ''
  notice.value = ''
  reportFor.value = reportFor.value === c.id ? null : c.id
  reportReason.value = 'spam'
  reportDetail.value = ''
}

async function submitReport(c: Comment) {
  if (!loggedIn.value) {
    error.value = '请先登录再举报'
    return
  }
  reportBusy.value = true
  error.value = ''
  notice.value = ''
  try {
    await apiFetch('/reports', {
      method: 'POST',
      body: JSON.stringify({
        target_kind: 'wiki_comment',
        target_id: c.id,
        reason: reportReason.value,
        detail: reportDetail.value.trim(),
      }),
    })
    notice.value = '已提交举报，站务会审核'
    reportFor.value = null
    reportDetail.value = ''
  } catch (e: any) {
    if (e instanceof ApiError) {
      if (e.status === 409) {
        notice.value = '你已经举报过这条，站务会处理'
        reportFor.value = null
        return
      }
      if (e.status === 401) {
        clearSession()
        error.value = '登录已过期，请重新登录后再举报'
        return
      }
    }
    if (goReadonlyIfMirror(e)) {
      error.value = MIRROR_READONLY_NOTE
      return
    }
    error.value = apiErrorMessage(e, '举报未提交，请稍后再试')
  } finally {
    reportBusy.value = false
  }
}

/* ── 评论配图 ──────────────────────────────────────────────────────────── */

async function probeMedia(): Promise<boolean> {
  if (mediaProbe) return mediaProbe
  mediaProbe = (async () => {
    try {
      await apiFetch('/media')
      return true
    } catch (e) {
      // 404/405/501：后端没有媒体路由；401/断网也不该把按钮亮出来
      return false
    }
  })()
  return mediaProbe
}

/** 后端的媒体 URL 是 `/api/v1/media/<id>`；镜像端要按当前 API base 重写 */
function resolveMediaUrl(url: string): string {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const idx = url.indexOf('/media/')
  return idx >= 0 ? apiUrl(url.slice(idx)) : url
}

/** 只把本站媒体链接渲染成图片，其他 http(s) 链接仍是普通外链。 */
function isOwnMediaUrl(url: string): boolean {
  const abs = resolveMediaUrl(url)
  return abs.startsWith(apiBase() + '/media/')
    && /^[A-Za-z0-9_-]+$/.test(abs.slice((apiBase() + '/media/').length))
}

type BodyPart = { kind: 'text' | 'link' | 'image'; value: string }

/**
 * 把评论文本切成文本/链接/图片，模板按类型渲染。
 * 不用 v-html：用户正文永远当文本处理，避免 XSS。
 */
function bodyParts(text: string): BodyPart[] {
  const out: BodyPart[] = []
  const re = /(https?:\/\/[^\s<>"']+|\/api\/v1\/media\/[A-Za-z0-9_-]+)/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(text)) !== null) {
    const raw = m[0]
    const trailing = raw.match(/[.,;:!?，。；：！？）)\]]+$/)?.[0] || ''
    const value = trailing ? raw.slice(0, -trailing.length) : raw
    if (m.index > last) out.push({ kind: 'text', value: text.slice(last, m.index) })
    if (value) {
      out.push({
        kind: isOwnMediaUrl(value) ? 'image' : 'link',
        value: isOwnMediaUrl(value) ? resolveMediaUrl(value) : value,
      })
    }
    if (trailing) out.push({ kind: 'text', value: trailing })
    last = m.index + raw.length
  }
  if (last < text.length) out.push({ kind: 'text', value: text.slice(last) })
  return out
}

function pickMedia() {
  if (uploading.value) return
  fileInput.value?.click()
}

function insertMediaUrl(url: string) {
  const needsNewline = !!body.value && !body.value.endsWith('\n')
  body.value += `${needsNewline ? '\n' : ''}${url}\n`
}

async function onMediaChange(evt: Event) {
  const input = evt.target as HTMLInputElement
  const file = input.files?.[0]
  // 清空 value，允许连续选同一个文件
  input.value = ''
  if (!file) return
  await uploadMedia(file)
}

async function uploadMedia(file: File) {
  if (uploading.value) return
  error.value = ''
  notice.value = ''
  if (!loggedIn.value) {
    error.value = '请先登录再上传图片'
    return
  }
  if (!MEDIA_TYPES.includes(file.type)) {
    error.value = '只支持 JPEG / PNG / WebP 图片'
    return
  }
  if (file.size > MEDIA_MAX_BYTES) {
    error.value = '图片不能超过 5 MB'
    return
  }
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const r = await apiFetch<{ id: string; url: string }>('/media', {
      method: 'POST',
      body: form,
    })
    const url = resolveMediaUrl(r.url)
    uploads.value = uploads.value.concat({ id: r.id, url })
    // 正文上限 4000：放不下就不插，保留预览让用户自己决定
    if (body.value.length + url.length + 1 > 4000) {
      notice.value = '图片已上传；正文接近 4000 字，请手动插入链接'
      return
    }
    insertMediaUrl(url)
    notice.value = '图片已上传，链接已插入正文'
  } catch (e: any) {
    if (e instanceof ApiError) {
      if (e.status === 401) {
        clearSession()
        error.value = '登录已过期，请重新登录'
        return
      }
      if (e.status === 404 || e.status === 405 || e.status === 501) {
        mediaReady.value = false
        mediaProbe = Promise.resolve(false)
        return
      }
    }
    if (goReadonlyIfMirror(e)) {
      error.value = MIRROR_READONLY_NOTE
      return
    }
    // 后端 413/415 已给中文原因（超 5MB / 格式不支持），统一走 apiErrorMessage
    error.value = apiErrorMessage(e, '图片上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
}

function insertUpload(u: { id: string; url: string }) {
  if (body.value.includes(u.url)) return
  if (body.value.length + u.url.length + 1 > 4000) {
    error.value = '正文已到 4000 字上限，无法再插入图片链接'
    return
  }
  insertMediaUrl(u.url)
  notice.value = '链接已插入正文'
}

function removeUpload(u: { id: string; url: string }) {
  uploads.value = uploads.value.filter(x => x.id !== u.id)
  // 只移除完整 URL（含可能的换行），不动用户自己写的内容
  body.value = body.value.split(u.url).join('').replace(/\n{3,}/g, '\n\n')
}

/* ── 树与计数 ──────────────────────────────────────────────────────────── */

const tree = computed<TreeNode[]>(() => {
  const map = new Map<number, TreeNode>()
  for (const c of items.value) map.set(c.id, { ...c, children: [] })
  const roots: TreeNode[] = []
  for (const node of map.values()) {
    if (node.parent_id == null) {
      roots.push(node)
      continue
    }
    const parent = map.get(node.parent_id)
    if (parent) {
      parent.children.push(node)
      continue
    }
    // 父节点不在当前页时，用 root_id 挂回所属根，避免通知定位到的回复凭空消失。
    const rootId = node.root_id
    const root = rootId != null && rootId !== node.id ? map.get(rootId) : undefined
    if (root) root.children.push(node)
    // 父节点被站务隐藏且没有可见后代时整支不渲染，等恢复后一起回来。
  }
  return roots
})

/** 根分页 + 后代一次展开：服务端分页时已加载的根全部展示；旧后端仍前端截根 */
const visible = computed<Array<{ c: TreeNode; depth: number }>>(() => {
  const out: Array<{ c: TreeNode; depth: number }> = []
  const walk = (n: TreeNode, depth: number) => {
    out.push({ c: n, depth })
    for (const child of n.children) walk(child, depth + 1)
  }
  const roots = serverPaged.value ? tree.value : tree.value.slice(0, visibleRoots.value)
  for (const root of roots) walk(root, 0)
  return out
})
const remainingRoots = computed(() => {
  if (serverPaged.value && rootTotal.value != null) {
    return Math.max(0, rootTotal.value - rootsLoaded.value)
  }
  return Math.max(0, tree.value.length - visibleRoots.value)
})
/** 实际渲染的条数（已删除占位不算讨论数，父节点被隐藏的孤儿回复不算） */
const commentCount = computed(() => {
  let n = 0
  const walk = (node: TreeNode) => {
    if (commentState(node) !== 'deleted') n += 1
    for (const child of node.children) walk(child)
  }
  for (const root of tree.value) walk(root)
  return n
})

function fmt(s: string) {
  return s.slice(0, 16).replace('T', ' ')
}

/** 主站有后端时用站内账号；纯静态镜像才回落 giscus。 */
async function decide() {
  if (apiUp.value === null) apiUp.value = await apiAvailable()
  if (apiUp.value) {
    mode.value = 'self'
    await refreshSession()
    if (loggedIn.value) {
      // 配图是否可用不阻塞讨论加载；探测失败就永远隐藏按钮
      void probeMedia().then(ok => { mediaReady.value = ok })
    }
    await load()
    return
  }
  if (giscusCfg) {
    // GitHub Pages 镜像：giscus 静态可用，不需要后端
    mode.value = 'giscus'
    await nextTick()
    mountGiscus()
    return
  }
  // 纯静态镜像：只说清楚现状，不请求、不报错
  mode.value = 'readonly'
}

onMounted(() => {
  if (typeof window !== 'undefined') window.addEventListener('hashchange', onHashChange)
  void decide()
})
onUnmounted(() => {
  if (typeof window !== 'undefined') window.removeEventListener('hashchange', onHashChange)
})
watch(() => route.path, () => {
  loadSeq++                    // 让上一页在途的加载结果作废
  mode.value = 'probe'
  items.value = []
  body.value = ''
  replyTo.value = null
  reportFor.value = null
  notice.value = ''
  error.value = ''
  visibleRoots.value = PAGE_SIZE
  serverPaged.value = false
  rootTotal.value = null
  rootsLoaded.value = 0
  highlightId.value = null
  uploads.value = []
  hashHandled = ''
  decide()
})
watch(isDark, syncGiscusTheme)
</script>

<template>
  <!-- id 是部件页「去写评论 ↓」(#这一页的讨论) 的落点：
       少了它那个锚点只是改 URL、页面不动，等于点了没反应。 -->
  <section id="这一页的讨论" class="rsw">
    <h2 class="rsw-title">
      这一页的讨论
      <span v-if="mode === 'self'" class="rsw-count">{{ commentCount }}</span>
    </h2>

    <!-- 静态站：giscus（GitHub Discussions）。写评论要 GitHub 账号，读不用。 -->
    <template v-if="mode === 'giscus'">
      <p class="rsw-hint">
        讨论托管在 <strong>GitHub Discussions</strong>，
        <strong>发言需要一个 GitHub 账号</strong>（读不用登录）。
        带上具体工况（负载、占空比、环境温度）比「好用 / 不好用」有用得多。
      </p>
      <div ref="giscusHost" class="giscus-host" />
    </template>

    <template v-else-if="mode === 'self'">
      <p class="rsw-hint">
        用过的坑、量到的数、和厂商确认过的事，写在<strong>对应这一页</strong>下面才有用。
        带上具体工况（负载、占空比、环境温度）——只写「好用/不好用」对下一个人没有价值。
      </p>

      <p v-if="offline" class="rsw-muted">
        讨论加载失败，请稍后重试。
        <button type="button" class="rsw-btn rsw-retry" @click="load">重试</button>
      </p>
      <p v-else-if="loading" class="rsw-muted">加载中…</p>
      <p v-else-if="!tree.length" class="rsw-muted">还没有讨论。第一条就由你来写。</p>

      <template v-else>
        <ul class="rsw-list">
          <li v-for="node in visible" :id="`comment-${node.c.id}`" :key="node.c.id" class="rsw-item"
              :class="{ 'rsw-child': node.depth > 0, 'rsw-target': highlightId === node.c.id }"
              :style="{ marginLeft: Math.min(node.depth, 4) * 1.1 + 'rem' }">
            <div class="rsw-head">
              <span class="rsw-avatar"
                    :class="{ sm: node.depth > 0 }"
                    :style="{ background: `hsl(${node.c.author?.avatar_hue ?? 160} 55% 55%)` }">
                {{ node.c.author?.display_name?.slice(0, 1) ?? (commentState(node.c) === 'deleted' ? '·' : '?') }}
              </span>
              <span class="rsw-name">
                {{ node.c.author?.display_name
                  ?? (commentState(node.c) === 'deleted' ? '已删除' : '匿名') }}
              </span>
              <span v-if="node.c.author?.is_staff" class="rsw-badge">站方</span>
              <span v-if="commentState(node.c) === 'pending'" class="rsw-badge rsw-badge-pending">待审核</span>
              <span class="rsw-time">{{ fmt(node.c.created_at) }}</span>
              <span class="rsw-actions-inline">
                <button v-if="loggedIn && commentState(node.c) === 'visible'" type="button"
                        class="rsw-link" @click="startReply(node.c)">回复</button>
                <button v-if="canDelete(node.c)" type="button" class="rsw-link"
                        @click="remove(node.c)">
                  {{ commentState(node.c) === 'pending' ? '撤回' : '删除' }}
                </button>
                <button v-if="loggedIn && commentState(node.c) === 'visible'" type="button"
                        class="rsw-link" @click="toggleReport(node.c)">
                  {{ reportFor === node.c.id ? '收起举报' : '举报' }}
                </button>
              </span>
            </div>

            <!-- P1：待审核 / 已删除只给占位，不渲染正文 -->
            <div v-if="commentState(node.c) === 'pending'" class="rsw-placeholder">
              待审核，通过后公开（仅你与站务可见）
            </div>
            <div v-else-if="commentState(node.c) === 'deleted'" class="rsw-placeholder">
              已删除
            </div>
            <div v-else class="rsw-body">
              <template v-for="(part, pi) in bodyParts(node.c.body)" :key="pi">
                <a v-if="part.kind === 'image'" :href="part.value" target="_blank"
                   rel="nofollow ugc noopener">
                  <img :src="part.value" alt="评论配图" loading="lazy" class="rsw-body-img" />
                </a>
                <a v-else-if="part.kind === 'link'" :href="part.value" target="_blank"
                   rel="nofollow ugc noopener" class="rsw-body-link">{{ part.value }}</a>
                <template v-else>{{ part.value }}</template>
              </template>
            </div>

            <!-- 举报：只调用现有 /reports，不在前端做审核或折叠逻辑 -->
            <div v-if="reportFor === node.c.id" class="rsw-report">
              <label class="rsw-report-label" :for="`rsw-reason-${node.c.id}`">举报原因</label>
              <select :id="`rsw-reason-${node.c.id}`" v-model="reportReason"
                      class="rsw-select" :disabled="reportBusy">
                <option v-for="opt in REPORT_REASONS" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
              <label class="rsw-report-label" :for="`rsw-detail-${node.c.id}`">
                补充说明（可选）
              </label>
              <textarea :id="`rsw-detail-${node.c.id}`" v-model="reportDetail"
                        class="rsw-input rsw-report-input" rows="2" maxlength="500"
                        :disabled="reportBusy"
                        placeholder="哪一句有问题？站务需要可判断的上下文" />
              <div class="rsw-report-actions">
                <button type="button" class="rsw-btn" :disabled="reportBusy"
                        @click="submitReport(node.c)">
                  {{ reportBusy ? '提交中…' : '提交举报' }}
                </button>
                <button type="button" class="rsw-link" :disabled="reportBusy"
                        @click="reportFor = null">取消</button>
                <span class="rsw-count-inline">{{ reportDetail.length }}/500</span>
              </div>
            </div>
          </li>
        </ul>
        <button v-if="remainingRoots" type="button" class="rsw-more"
                :disabled="loadingMore" @click="loadMore()">
          {{ loadingMore
            ? '加载中…'
            : `显示更多讨论（还有 ${remainingRoots} 条根讨论）` }}
        </button>
      </template>

      <!-- 未登录：明确说清楚能做什么、去哪里登录，而不是等用户写完再报 401 -->
      <div v-if="!loggedIn" class="rsw-login">
        <strong>登录后才能发言、回复和举报</strong>
        <span class="rsw-muted">站内账号，全站共用</span>
        <a class="rsw-login-link" :href="loginHref">登录 / 注册 →</a>
      </div>

      <div v-else class="rsw-form">
        <div v-if="replyTo" class="rsw-replying">
          正在回复 <strong>{{ replyTo.author?.display_name ?? '匿名' }}</strong>
          <button type="button" class="rsw-link" @click="replyTo = null">取消</button>
        </div>
        <label class="rsw-label" for="rsw-input">写下你的实测 / 核对结果</label>
        <textarea id="rsw-input" v-model="body" rows="3" class="rsw-input" maxlength="4000"
                  :disabled="posting || uploading"
                  :aria-describedby="error ? 'rsw-error' : undefined"
                  :aria-invalid="!!error"
                  placeholder="写下你的实测/核对结果，附工况" />
        <div class="rsw-actions">
          <button type="button" class="rsw-btn" :disabled="!body.trim() || posting || uploading"
                  @click="submit">
            {{ posting ? '发送中…' : '发表讨论' }}
          </button>
          <span class="rsw-count-inline">{{ body.length }}/4000</span>
        </div>

        <!-- 配图：后端没有 /media 时整块不渲染，文本评论完全不受影响 -->
        <div v-if="mediaReady" class="rsw-media">
          <button type="button" class="rsw-upload" :disabled="uploading || posting"
                  @click="pickMedia">
            {{ uploading ? '上传中…' : '上传图片' }}
          </button>
          <input ref="fileInput" class="rsw-file" type="file" accept="image/*"
                 :disabled="uploading || posting" @change="onMediaChange" />
          <span class="rsw-media-hint">JPEG / PNG / WebP，≤ 5 MB；上传后链接插入正文</span>
          <ul v-if="uploads.length" class="rsw-previews">
            <li v-for="u in uploads" :key="u.id" class="rsw-preview">
              <img :src="u.url" alt="已上传图片预览" loading="lazy" />
              <span class="rsw-preview-actions">
                <button type="button" class="rsw-link" :disabled="posting"
                        @click="insertUpload(u)">插入正文</button>
                <button type="button" class="rsw-link" :disabled="posting"
                        @click="removeUpload(u)">移除</button>
              </span>
            </li>
          </ul>
        </div>
      </div>

      <p v-if="notice" class="rsw-notice" role="status">{{ notice }}</p>
      <p v-if="error" id="rsw-error" class="rsw-error" role="alert">{{ error }}</p>
    </template>

    <!-- 纯静态镜像（GitHub Pages）：没有后端就没有讨论串。
         不请求、不报错，一行中性说明 + 主站入口；评论框整个隐藏。 -->
    <p v-else-if="mode === 'readonly'" class="rsw-muted">
      {{ MIRROR_READONLY_NOTE }} ·
      <a :href="PRIMARY_SITE" target="_blank" rel="noopener">robowiki.org.cn</a>
    </p>
  </section>
</template>

<style scoped>
.rsw {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--vp-c-divider);
  /* 锚点跳过来时别被吸顶导航盖住标题 */
  scroll-margin-top: calc(var(--vp-nav-height, 64px) + 16px);
}
.rsw-title {
  font-size: 1.05rem;
  font-weight: 600;
  border-top: none;
  padding-top: 0;
  margin: 0 0 0.35rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.rsw-count {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--vp-c-text-3);
  background: var(--vp-c-default-soft);
  border-radius: 999px;
  padding: 0 0.45rem;
}
.rsw-hint {
  font-size: 0.8rem;
  color: var(--vp-c-text-3);
  margin: 0 0 1rem;
  line-height: 1.6;
}
.rsw-muted {
  font-size: 0.82rem;
  color: var(--vp-c-text-3);
}
.rsw-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1.2rem;
}
.rsw-item {
  padding: 0.7rem 0;
  border-bottom: 1px solid var(--vp-c-divider);
  /* 通知 #comment-<id> 跳转时不要被吸顶导航盖住 */
  scroll-margin-top: calc(var(--vp-nav-height, 64px) + 16px);
  border-radius: 4px;
}
.rsw-item.rsw-target {
  background: var(--vp-c-brand-soft);
  box-shadow: 0 0 0 2px var(--vp-c-brand-soft);
}
.rsw-item.rsw-child {
  border-left: 2px solid var(--vp-c-divider);
  padding-left: 0.7rem;
}
.rsw-head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
  flex-wrap: wrap;
}
.rsw-avatar {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.7);
  flex: none;
}
.rsw-avatar.sm {
  width: 16px;
  height: 16px;
  font-size: 9px;
  border-radius: 4px;
}
.rsw-name {
  color: var(--vp-c-text-1);
  font-weight: 500;
}
.rsw-badge {
  font-size: 0.65rem;
  padding: 0 0.3rem;
  border-radius: 4px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
}
.rsw-badge-pending {
  background: transparent;
  border: 1px solid var(--rw-accent-1);
  color: var(--rw-accent-1);
}
.rsw-time {
  font-variant-numeric: tabular-nums;
}
.rsw-actions-inline {
  margin-left: auto;
  display: inline-flex;
  gap: 0.6rem;
}
.rsw-link {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
  cursor: pointer;
}
.rsw-link:hover {
  color: var(--vp-c-brand-1);
}
.rsw-link:disabled {
  opacity: 0.5;
  cursor: default;
}
.rsw-body {
  font-size: 0.86rem;
  line-height: 1.7;
  margin-top: 0.3rem;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: var(--vp-c-text-1);
}
.rsw-body-img {
  display: block;
  max-width: min(100%, 420px);
  max-height: 420px;
  margin: 0.4rem 0;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
}
.rsw-body-link { color: var(--rw-link); text-decoration: underline; }
.rsw-retry { margin-left: 0.35rem; padding: 0.2rem 0.5rem; font-size: 0.78rem; }
.rsw-placeholder {
  margin-top: 0.3rem;
  font-size: 0.82rem;
  font-style: italic;
  color: var(--vp-c-text-3);
}
.rsw-login {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.45rem;
  padding: 0.7rem 0.8rem;
  border: 1px dashed var(--vp-c-divider);
  border-radius: 8px;
  font-size: 0.82rem;
  color: var(--vp-c-text-2);
}
.rsw-login-link {
  margin-left: auto;
  font-weight: 600;
  color: var(--vp-c-brand-1);
  text-decoration: none;
}
.rsw-login-link:hover {
  text-decoration: underline;
}
.rsw-form {
  margin-top: 0.5rem;
}
.rsw-replying {
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
  margin-bottom: 0.35rem;
}
.rsw-replying .rsw-link {
  margin-left: 0.6rem;
}
.rsw-label {
  display: block;
  font-size: 0.76rem;
  color: var(--vp-c-text-3);
  margin-bottom: 0.3rem;
}
.rsw-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.6rem 0.7rem;
  font-size: 0.86rem;
  line-height: 1.6;
  font-family: inherit;
  color: var(--vp-c-text-1);
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  resize: vertical;
}
.rsw-input:focus {
  outline: none;
  border-color: var(--vp-c-brand-1);
}
.rsw-input:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 2px;
}
.rsw-input[aria-invalid="true"] { border-color: var(--vp-c-danger-1); }
.rsw-input:disabled { opacity: 0.6; }
.rsw-count-inline {
  font-size: 0.72rem;
  color: var(--vp-c-text-3);
  font-variant-numeric: tabular-nums;
}
.rsw-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-top: 0.55rem;
}
.rsw-btn {
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: 1px solid var(--vp-c-brand-1);
  background: var(--vp-c-brand-1);
  color: #ffffff;
  cursor: pointer;
}
.rsw-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
/* ── 配图 ─────────────────────────────────────────────────────────────── */
.rsw-media {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.6rem;
}
.rsw-upload {
  min-height: 34px;
  padding: 0.3rem 0.75rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 999px;
  background: transparent;
  color: var(--vp-c-text-2);
  font-size: 0.78rem;
  cursor: pointer;
}
.rsw-upload:hover:not(:disabled) {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}
.rsw-upload:disabled { opacity: 0.5; cursor: default; }
.rsw-file { display: none; }
.rsw-media-hint { font-size: 0.72rem; color: var(--vp-c-text-3); }
.rsw-previews {
  list-style: none;
  margin: 0.2rem 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  width: 100%;
}
.rsw-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 0.3rem 0.45rem;
  background: var(--vp-c-bg);
}
.rsw-preview img {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}
.rsw-preview-actions { display: flex; flex-direction: column; gap: 0.2rem; }
.rsw-report {
  margin-top: 0.55rem;
  padding: 0.6rem 0.7rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg-soft);
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.rsw-report-label {
  font-size: 0.72rem;
  color: var(--vp-c-text-3);
}
.rsw-select {
  align-self: flex-start;
  min-height: 32px;
  padding: 0.2rem 0.45rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  font: inherit;
  font-size: 0.8rem;
}
.rsw-report-input {
  background: var(--vp-c-bg);
  font-size: 0.8rem;
}
.rsw-report-actions {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-top: 0.15rem;
}
.rsw-more {
  display: block;
  width: 100%;
  margin: 0 0 1rem;
  padding: 0.45rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: transparent;
  color: var(--vp-c-text-2);
  font-size: 0.8rem;
  cursor: pointer;
}
.rsw-more:hover:not(:disabled) {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}
.rsw-more:disabled { opacity: 0.5; cursor: default; }
.rsw-notice {
  font-size: 0.78rem;
  color: var(--vp-c-brand-1);
  margin: 0.5rem 0 0;
}
.rsw-error {
  font-size: 0.78rem;
  color: var(--vp-c-danger-1);
  margin: 0.5rem 0 0;
}

.giscus-host {
  margin-top: 0.8rem;
}
.giscus-host :deep(.giscus) {
  margin-top: 0.5rem;
}
</style>
