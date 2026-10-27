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
 */
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useData, useRoute } from 'vitepress'
import { giscus as giscusCfg } from '../giscus'

const { isDark } = useData()
const route = useRoute()

const giscusHost = ref<HTMLElement | null>(null)
const mode = ref<'probe' | 'self' | 'giscus'>('probe')

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
  // 否则仓库改名（/roboselect/ → /RoboSelect/）会让所有讨论改键、集体消失。
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

const items = ref<Comment[]>([])
const loading = ref(true)
const body = ref('')
const replyTo = ref<Comment | null>(null)
const error = ref('')
/** 静态部署（GitHub Pages）没有后端，把「连不上」说清楚，不要显示成红色报错 */
const offline = ref(false)
const posting = ref(false)

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

function token(): string | null {
  try {
    return localStorage.getItem('roboselect.token')
  } catch {
    return null
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const r = await fetch(`/api/wiki/comments?page=${encodeURIComponent(pageId.value)}`)
    if (!r.ok) throw new Error(String(r.status))
    items.value = (await r.json()).comments
  } catch (e: any) {
    error.value = `讨论加载失败（${e.message}）`
  } finally {
    loading.value = false
  }
}

async function submit() {
  const t = token()
  if (!t) {
    error.value = '先登录才能发言'
    return
  }
  posting.value = true
  error.value = ''
  try {
    const r = await fetch('/api/wiki/comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` },
      body: JSON.stringify({
        page: pageId.value,
        body: body.value.trim(),
        parent_id: replyTo.value?.id ?? null,
      }),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : '发言失败')
    body.value = ''
    replyTo.value = null
    await load()
  } catch (e: any) {
    error.value = e.message
  } finally {
    posting.value = false
  }
}

async function remove(c: Comment) {
  const t = token()
  if (!t) return
  const r = await fetch(`/api/wiki/comments/${c.id}`, {
    method: 'DELETE', headers: { Authorization: `Bearer ${t}` },
  })
  if (r.ok) await load()
}

const roots = computed(() => items.value.filter(c => c.parent_id === null))
const childrenOf = (id: number) => items.value.filter(c => c.parent_id === id)

function fmt(s: string) {
  return s.slice(0, 16).replace('T', ' ')
}

/** 决定这一页用哪种后端：配了 giscus 就走 giscus（门槛 = GitHub 账号），否则回落自托管 */
async function decide() {
  if (giscusCfg) {
    mode.value = 'giscus'
    await nextTick()
    mountGiscus()
    return
  }
  mode.value = 'self'
  await load()
}

onMounted(decide)
watch(() => route.path, () => {
  mode.value = 'probe'
  decide()
})
watch(isDark, syncGiscusTheme)
</script>

<template>
  <section class="rsw">
    <h2 class="rsw-title">
      这一页的讨论
      <span v-if="mode === 'self'" class="rsw-count">{{ items.length }}</span>
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
        讨论加载失败。本地可运行 <code>uvicorn app.main:app --port 8000</code> 后重试。
      </p>
      <p v-else-if="loading" class="rsw-muted">加载中…</p>
      <p v-else-if="!items.length" class="rsw-muted">还没有讨论。第一条就由你来写。</p>

      <ul v-else class="rsw-list">
        <li v-for="c in roots" :key="c.id" class="rsw-item">
          <div class="rsw-head">
            <span class="rsw-avatar"
                  :style="{ background: `hsl(${c.author?.avatar_hue ?? 160} 55% 55%)` }">
              {{ c.author?.display_name?.slice(0, 1) ?? '?' }}
            </span>
            <span class="rsw-name">{{ c.author?.display_name ?? '匿名' }}</span>
            <span v-if="c.author?.is_staff" class="rsw-badge">站方</span>
            <span class="rsw-time">{{ fmt(c.created_at) }}</span>
            <button class="rsw-link" @click="replyTo = c">回复</button>
            <button v-if="token()" class="rsw-link" @click="remove(c)">删除</button>
          </div>
          <div class="rsw-body">{{ c.body }}</div>

          <ul v-if="childrenOf(c.id).length" class="rsw-replies">
            <li v-for="r in childrenOf(c.id)" :key="r.id" class="rsw-reply">
              <div class="rsw-head">
                <span class="rsw-avatar sm"
                      :style="{ background: `hsl(${r.author?.avatar_hue ?? 160} 55% 55%)` }">
                  {{ r.author?.display_name?.slice(0, 1) ?? '?' }}
                </span>
                <span class="rsw-name">{{ r.author?.display_name ?? '匿名' }}</span>
                <span class="rsw-time">{{ fmt(r.created_at) }}</span>
              </div>
              <div class="rsw-body">{{ r.body }}</div>
            </li>
          </ul>
        </li>
      </ul>

      <div class="rsw-form">
        <div v-if="replyTo" class="rsw-replying">
          正在回复 <strong>{{ replyTo.author?.display_name }}</strong>
          <button class="rsw-link" @click="replyTo = null">取消</button>
        </div>
        <textarea v-model="body" rows="3" class="rsw-input"
                  :placeholder="token() ? '写下你的实测/核对结果，附工况' : '先登录才能发言（选型台右上角登录，全站共用）'" />
        <div class="rsw-actions">
          <button class="rsw-btn" :disabled="!body.trim() || posting" @click="submit">
            {{ posting ? '发送中…' : '发表讨论' }}
          </button>
          <a class="rsw-muted" href="/" target="_blank">去选型台登录 ↗</a>
        </div>
        <p v-if="error" class="rsw-error">{{ error }}</p>
      </div>
    </template>
  </section>
</template>

<style scoped>
.rsw {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--vp-c-divider);
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
.rsw-head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
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
.rsw-link {
  margin-left: auto;
  background: none;
  border: none;
  padding: 0;
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
  cursor: pointer;
}
.rsw-link + .rsw-link {
  margin-left: 0.6rem;
}
.rsw-link:hover {
  color: var(--vp-c-brand-1);
}
.rsw-body {
  font-size: 0.86rem;
  line-height: 1.7;
  margin-top: 0.3rem;
  white-space: pre-wrap;
  color: var(--vp-c-text-1);
}
.rsw-replies {
  list-style: none;
  padding: 0 0 0 1.4rem;
  margin: 0.5rem 0 0;
  border-left: 2px solid var(--vp-c-divider);
}
.rsw-reply {
  padding: 0.35rem 0 0.35rem 0.7rem;
}
.rsw-form {
  margin-top: 0.5rem;
}
.rsw-replying {
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
  margin-bottom: 0.35rem;
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
