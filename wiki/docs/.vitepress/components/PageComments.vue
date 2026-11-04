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
 * 评论树参考 Artalk（MIT）的「一次性取回、前端组树」：
 *   · 后端 WikiComment API 一次返回整页线程（已做 root + 后代批量查询）
 *   · 前端按 parent_id 组树，根讨论分页显示；回复可以继续往下展开，不会丢节点
 *   · 举报复用现有 /reports 契约（target_kind=wiki_comment），不在前端自研审核
 */
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useData, useRoute } from 'vitepress'
import { giscus as giscusCfg } from '../giscus'
import { apiAvailable, PRIMARY_SITE } from '../lib/api'
import { authHeaders, clearToken, getToken } from '../lib/auth'

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
  created_at: string
  author: Author | null
}
interface Me {
  id: number
  handle: string
  display_name: string
  is_staff: boolean
}
type TreeNode = Comment & { children: TreeNode[] }

const items = ref<Comment[]>([])
const loading = ref(true)
const body = ref('')
const replyTo = ref<Comment | null>(null)
const error = ref('')
const notice = ref('')
/** 探活通过但取数失败（后端刚挂 / 网关超时）——这种才叫失败，静态镜像走的是 readonly 态 */
const offline = ref(false)
const posting = ref(false)
const loggedIn = ref(false)
const me = ref<Me | null>(null)

/** 根讨论分页：后端一次给整页线程，前端只先渲染前 N 条根，避免长页首屏过重 */
const PAGE_SIZE = 24
const visibleRoots = ref(PAGE_SIZE)

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
    const r = await fetch('/api/v1/auth/me', { headers: authHeaders() })
    if (r.status === 401) {
      clearSession()
      return
    }
    if (r.ok) me.value = await r.json() as Me
  } catch {
    // 网络抖动：保留 token；真正写操作时后端会再判一次 401
  }
}

async function readDetail(r: Response, fallback: string): Promise<string> {
  const d = await r.json().catch(() => ({})) as { detail?: unknown }
  if (typeof d.detail === 'string') return d.detail
  if (Array.isArray(d.detail) && d.detail.length) {
    const first = d.detail[0] as { msg?: unknown }
    if (typeof first?.msg === 'string') return first.msg
  }
  return fallback
}

async function load() {
  // 探活没通过就一个请求都不发：镜像端这里调一次只会拿到 404 并渲染成故障
  if (!apiUp.value) return
  loading.value = true
  error.value = ''
  offline.value = false
  try {
    // limit 取 API 上限：一次拿回整页线程，前端再按 parent_id 组树、根分页
    const r = await fetch(
      `/api/v1/wiki/comments?page=${encodeURIComponent(pageId.value)}&limit=200`)
    if (!r.ok) throw new Error(String(r.status))
    items.value = (await r.json()).comments
  } catch (e: any) {
    // 走到这里说明探活过了但请求失败（后端刚挂 / 网关超时），这才是真的「加载失败」
    offline.value = true
    error.value = `讨论加载失败（${e.message}）`
  } finally {
    loading.value = false
  }
}

/** 让某条回复所属的根讨论出现在当前分页里（否则发完回复看不到自己） */
function revealThreadOf(id: number) {
  let cur = items.value.find(c => c.id === id)
  const seen = new Set<number>()
  while (cur?.parent_id != null && !seen.has(cur.id)) {
    seen.add(cur.id)
    cur = items.value.find(c => c.id === cur!.parent_id)
  }
  if (!cur) return
  const idx = tree.value.findIndex(r => r.id === cur!.id)
  if (idx >= visibleRoots.value) visibleRoots.value = idx + 1
}

async function submit() {
  if (!loggedIn.value) {
    error.value = '请先登录再发言'
    return
  }
  // 与后端 WikiComment CommentIn 一致：1–4000 字。前端先拦一道，省一次必然 422 的请求
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
    const r = await fetch('/api/v1/wiki/comments', {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({
        page: pageId.value,
        body: text,
        parent_id: parentId,
      }),
    })
    if (r.status === 401) {
      clearSession()
      error.value = '登录已过期，请重新登录后再发言'
      return
    }
    if (!r.ok) throw new Error(await readDetail(r, '发言失败'))
    body.value = ''
    replyTo.value = null
    notice.value = '已发表'
    await load()
    if (parentId != null) revealThreadOf(parentId)
    else visibleRoots.value = Math.max(visibleRoots.value, tree.value.length)
  } catch (e: any) {
    error.value = e.message
  } finally {
    posting.value = false
  }
}

function startReply(c: Comment) {
  if (!loggedIn.value) {
    error.value = '请先登录再回复'
    return
  }
  replyTo.value = c
  error.value = ''
  notice.value = ''
}

function canDelete(c: Comment): boolean {
  if (!me.value) return false
  return me.value.is_staff || (!!c.author && c.author.handle === me.value.handle)
}

async function remove(c: Comment) {
  if (!loggedIn.value) {
    error.value = '请先登录'
    return
  }
  const hasReplies = items.value.some(x => x.parent_id === c.id)
  if (hasReplies && typeof window !== 'undefined'
      && !window.confirm('这条讨论下还有回复，删除会一并移除。确定删除？')) {
    return
  }
  error.value = ''
  notice.value = ''
  try {
    const r = await fetch(`/api/v1/wiki/comments/${c.id}`, {
      method: 'DELETE', headers: authHeaders(),
    })
    if (r.status === 401) {
      clearSession()
      error.value = '登录已过期，请重新登录'
      return
    }
    if (r.status === 403) {
      error.value = '只能删除自己的讨论'
      return
    }
    if (r.status === 404) {
      notice.value = '这条讨论已经不在了'
      await load()
      return
    }
    if (!r.ok) {
      error.value = '删除失败，请稍后重试'
      return
    }
    notice.value = '已删除'
    await load()
  } catch {
    error.value = '网络异常，删除未完成'
  }
}

function toggleReport(c: Comment) {
  if (!loggedIn.value) {
    error.value = '举报需要登录，请先登录'
    return
  }
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
    const r = await fetch('/api/v1/reports', {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_kind: 'wiki_comment',
        target_id: c.id,
        reason: reportReason.value,
        detail: reportDetail.value.trim(),
      }),
    })
    if (r.status === 201) {
      notice.value = '已提交举报，站务会审核'
      reportFor.value = null
      reportDetail.value = ''
      return
    }
    if (r.status === 409) {
      notice.value = '你已经举报过这条，站务会处理'
      reportFor.value = null
      return
    }
    if (r.status === 401) {
      clearSession()
      error.value = '登录已过期，请重新登录后再举报'
      return
    }
    error.value = await readDetail(r, '举报未提交，请稍后再试')
  } catch {
    error.value = '网络异常，举报未提交'
  } finally {
    reportBusy.value = false
  }
}

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
    // 父节点被站务隐藏时，API 不会返回它，但更深的回复可能还在。
    // 不能把孤儿回复提升成根（那会把被隐藏的线程重新顶到页面上）；
    // 直接不渲染，等站务恢复父节点后整条线程一起回来。
    if (parent) parent.children.push(node)
  }
  return roots
})

/** 根分页 + 后代一次展开：只限制根的数量，回复始终跟着父节点 */
const visible = computed<Array<{ c: TreeNode; depth: number }>>(() => {
  const out: Array<{ c: TreeNode; depth: number }> = []
  const walk = (n: TreeNode, depth: number) => {
    out.push({ c: n, depth })
    for (const child of n.children) walk(child, depth + 1)
  }
  for (const root of tree.value.slice(0, visibleRoots.value)) walk(root, 0)
  return out
})
const remainingRoots = computed(() =>
  Math.max(0, tree.value.length - visibleRoots.value))
/** 实际渲染的条数（父节点被隐藏的孤儿回复不算） */
const treeCount = computed(() => {
  let n = 0
  const walk = (node: TreeNode) => {
    n += 1
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

onMounted(decide)
watch(() => route.path, () => {
  mode.value = 'probe'
  items.value = []
  replyTo.value = null
  reportFor.value = null
  notice.value = ''
  error.value = ''
  visibleRoots.value = PAGE_SIZE
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
      <span v-if="mode === 'self'" class="rsw-count">{{ treeCount }}</span>
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
        讨论加载失败，请稍后重试。本地开发需先起后端：<code>uvicorn app.main:app --port 8000</code>。
      </p>
      <p v-else-if="loading" class="rsw-muted">加载中…</p>
      <p v-else-if="!tree.length" class="rsw-muted">还没有讨论。第一条就由你来写。</p>

      <template v-else>
        <ul class="rsw-list">
          <li v-for="node in visible" :key="node.c.id" class="rsw-item"
              :class="{ 'rsw-child': node.depth > 0 }"
              :style="{ marginLeft: Math.min(node.depth, 4) * 1.1 + 'rem' }">
            <div class="rsw-head">
              <span class="rsw-avatar"
                    :class="{ sm: node.depth > 0 }"
                    :style="{ background: `hsl(${node.c.author?.avatar_hue ?? 160} 55% 55%)` }">
                {{ node.c.author?.display_name?.slice(0, 1) ?? '?' }}
              </span>
              <span class="rsw-name">{{ node.c.author?.display_name ?? '匿名' }}</span>
              <span v-if="node.c.author?.is_staff" class="rsw-badge">站方</span>
              <span class="rsw-time">{{ fmt(node.c.created_at) }}</span>
              <span class="rsw-actions-inline">
                <button v-if="loggedIn" type="button" class="rsw-link"
                        @click="startReply(node.c)">回复</button>
                <button v-if="canDelete(node.c)" type="button" class="rsw-link"
                        @click="remove(node.c)">删除</button>
                <button v-if="loggedIn" type="button" class="rsw-link"
                        @click="toggleReport(node.c)">
                  {{ reportFor === node.c.id ? '收起举报' : '举报' }}
                </button>
              </span>
            </div>
            <div class="rsw-body">{{ node.c.body }}</div>

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
                @click="visibleRoots += PAGE_SIZE">
          显示更多讨论（还有 {{ remainingRoots }} 条根讨论）
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
                  :disabled="posting"
                  :aria-describedby="error ? 'rsw-error' : undefined"
                  :aria-invalid="!!error"
                  placeholder="写下你的实测/核对结果，附工况" />
        <div class="rsw-actions">
          <button type="button" class="rsw-btn" :disabled="!body.trim() || posting"
                  @click="submit">
            {{ posting ? '发送中…' : '发表讨论' }}
          </button>
          <span class="rsw-count-inline">{{ body.length }}/4000</span>
        </div>
      </div>

      <p v-if="notice" class="rsw-notice" role="status">{{ notice }}</p>
      <p v-if="error" id="rsw-error" class="rsw-error" role="alert">{{ error }}</p>
    </template>

    <!-- 纯静态镜像（GitHub Pages）：没有后端就没有讨论串。
         不请求、不报错，一行中性说明 + 主站入口；评论框整个隐藏。 -->
    <p v-else-if="mode === 'readonly'" class="rsw-muted">
      评论需要主站服务，当前为只读镜像 ·
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
  color: var(--vp-c-text-1);
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
.rsw-more:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}
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
