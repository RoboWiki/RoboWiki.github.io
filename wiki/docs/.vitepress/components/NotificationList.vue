<script setup lang="ts">
/**
 * 账号中心「通知」分区。
 *
 * 契约（backend/app/api/routes/notifications.py）：
 *   GET  /notifications?limit=20   → { total, unread, limit, offset, items[] }
 *   GET  /notifications/unread_count
 *   POST /notifications/{id}/read   → 单条已读，返回更新后的通知
 *   POST /notifications/read-all    → { updated }
 * 通知只由业务侧写入（被回复 / 举报处置结果），前端不做轮询：
 * 登录后拉一次，用户点开通知或点「全部已读」再同步未读数。
 *
 * 错误口径统一走 lib/api：401 清 token 并通知父组件退回登录态；
 * 404/405/501 视为「该后端版本还没开通通知」，显示中性说明而不是报错。
 * 链接是站内相对路径（如 /parts/actuator/cubemars#comment-12），
 * 点击时先尽力标记已读再跳转，标记失败也不拦着用户看内容。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { ApiError, apiErrorMessage, apiFetch } from '../lib/api'

export type Notification = {
  id: number
  type: string
  subject: string
  body: string
  link: string | null
  read_at: string | null
  created_at: string
}

type Payload = {
  items?: Notification[]
  total?: number
  unread?: number
}

const props = defineProps<{
  /** 所在 tab 是否处于激活状态：切到通知时同步一次，后台加载后再拉一次未读 */
  active?: boolean
}>()

const emit = defineEmits<{
  /** 未读数变化：父组件用它渲染 tab 角标 */
  (e: 'unread', value: number): void
  /** 401：token 已被 apiFetch 清掉，父组件应退回未登录态 */
  (e: 'unauthorized', message: string): void
}>()

const items = ref<Notification[]>([])
const unread = ref(0)
const loading = ref(false)
const loaded = ref(false)
const error = ref('')
const notice = ref('')
const unavailable = ref(false)
const busyId = ref<number | null>(null)
const allBusy = ref(false)

const hasUnread = computed(() => unread.value > 0)

function syncUnread(n: number) {
  unread.value = Math.max(0, n)
  emit('unread', unread.value)
}

/** 后端已读判定只看 read_at 是否为空 */
function isUnread(n: Notification): boolean {
  return !n.read_at
}

/** 401 统一交给父组件：这里只负责把文案带出去 */
function handleAuthError(e: unknown): boolean {
  if (e instanceof ApiError && e.status === 401) {
    emit('unauthorized', e.message || '登录已过期，请重新登录')
    return true
  }
  return false
}

/** 旧版后端没有这两条路由；这是「未开通」，不是故障 */
function isMissingEndpoint(e: unknown): boolean {
  return e instanceof ApiError && (e.status === 404 || e.status === 405 || e.status === 501)
}

async function load() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    const d = await apiFetch<Payload>('/notifications?limit=20')
    items.value = Array.isArray(d?.items) ? d.items : []
    syncUnread(typeof d?.unread === 'number'
      ? d.unread
      : items.value.filter(isUnread).length)
    unavailable.value = false
  } catch (e) {
    if (handleAuthError(e)) {
      items.value = []
      syncUnread(0)
      return
    }
    if (isMissingEndpoint(e)) {
      // 后端版本还没带通知：保持空态说明，不反复刷失败请求
      unavailable.value = true
      items.value = []
      syncUnread(0)
      return
    }
    unavailable.value = false
    error.value = apiErrorMessage(e, '通知加载失败，请稍后重试')
  } finally {
    loading.value = false
    loaded.value = true
  }
}

async function markRead(n: Notification): Promise<boolean> {
  if (!isUnread(n)) return true
  if (busyId.value != null) return false
  busyId.value = n.id
  error.value = ''
  try {
    const r = await apiFetch<Notification>(`/notifications/${n.id}/read`, {
      method: 'POST',
      // 点击通知会立刻跳转；keepalive 让标记请求在页面卸载后仍能送到
      keepalive: true,
    })
    n.read_at = r?.read_at || new Date().toISOString()
    // 只扣本地这一条：列表只显示最近 20 条，未读数可能大于列表长度
    syncUnread(unread.value - 1)
    return true
  } catch (e) {
    if (handleAuthError(e)) return false
    if (isMissingEndpoint(e)) {
      unavailable.value = true
      return false
    }
    error.value = apiErrorMessage(e, '标记已读失败，请稍后重试')
    return false
  } finally {
    busyId.value = null
  }
}

async function markAllRead() {
  if (allBusy.value || !hasUnread.value) return
  allBusy.value = true
  error.value = ''
  notice.value = ''
  try {
    await apiFetch('/notifications/read-all', { method: 'POST' })
    const now = new Date().toISOString()
    for (const n of items.value) if (isUnread(n)) n.read_at = now
    syncUnread(0)
    notice.value = '已全部标为已读'
  } catch (e) {
    if (handleAuthError(e)) return
    if (isMissingEndpoint(e)) {
      unavailable.value = true
      return
    }
    error.value = apiErrorMessage(e, '全部标记失败，请稍后重试')
  } finally {
    allBusy.value = false
  }
}

/**
 * 打开通知：先发标记已读再跳转，让列表与站内未读数一致。
 * 不等待标记完成 —— 断网时不能让用户卡在「点了没反应」；
 * keepalive 让请求在卸载后继续送达，失败也不影响看内容。
 */
function onOpen(evt: MouseEvent, n: Notification) {
  if (!n.link) return
  // 新标签页 / 中键 / 拖拽交给浏览器原生行为
  if (evt.metaKey || evt.ctrlKey || evt.shiftKey || evt.altKey || evt.button !== 0) return
  evt.preventDefault()
  if (isUnread(n)) void markRead(n)
  window.location.assign(n.link)
}

const KIND_LABEL: Record<string, string> = {
  reply: '回复',
  moderation: '审核',
  system: '系统',
}

function kindLabel(type: string): string {
  return KIND_LABEL[type] || '通知'
}

/** 相对时间：列表里「3 分钟前」比完整时间戳更好扫读 */
function when(iso: string): string {
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return ''
  const diff = Date.now() - t
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)} 天前`
  return new Date(t).toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  })
}

onMounted(load)

watch(() => props.active, v => {
  if (v) void load()
})

defineExpose({ refresh: load })
</script>

<template>
  <div class="notif">
    <div class="notif-head">
      <p class="notif-title">
        最近通知
        <span v-if="unread > 0" class="notif-badge" aria-live="polite">
          {{ unread > 99 ? '99+' : unread }} 条未读
        </span>
      </p>
      <div class="notif-head-actions">
        <button type="button" class="notif-btn"
          :disabled="allBusy || !hasUnread || unavailable"
          @click="markAllRead">
          {{ allBusy ? '处理中…' : '全部已读' }}
        </button>
        <button type="button" class="notif-btn notif-ghost" :disabled="loading" @click="load">
          {{ loading ? '刷新中…' : '刷新' }}
        </button>
      </div>
    </div>

    <p v-if="loading && !loaded" class="notif-muted" role="status">正在加载通知…</p>

    <template v-else>
      <p v-if="error" class="notif-error" role="alert">
        {{ error }}
        <button type="button" class="notif-inline-btn" @click="load">重试</button>
      </p>
      <p v-else-if="unavailable" class="notif-muted" role="status">
        当前后端还没有开通站内通知；被回复或站务处理时会在这里出现消息。
      </p>
      <p v-else-if="!items.length" class="notif-empty">
        还没有通知。被人回复、或你举报的内容被站务处理时，消息会出现在这里。
      </p>

      <ul v-else class="notif-list">
        <li v-for="n in items" :key="n.id" class="notif-item"
          :class="{ 'is-unread': isUnread(n) }">
          <div class="notif-item-head">
            <span class="notif-kind">{{ kindLabel(n.type) }}</span>
            <a v-if="n.link" class="notif-subject" :href="n.link"
              @click="onOpen($event, n)">{{ n.subject || '查看详情' }}</a>
            <span v-else class="notif-subject">{{ n.subject || '通知' }}</span>
            <span v-if="isUnread(n)" class="notif-dot" aria-label="未读" />
            <time class="notif-time" :datetime="n.created_at">{{ when(n.created_at) }}</time>
          </div>
          <p v-if="n.body" class="notif-body">{{ n.body }}</p>
          <div class="notif-item-foot">
            <button v-if="isUnread(n)" type="button" class="notif-inline-btn"
              :disabled="busyId === n.id" @click="markRead(n)">
              {{ busyId === n.id ? '标记中…' : '标记已读' }}
            </button>
            <a v-if="n.link" class="notif-open" :href="n.link" @click="onOpen($event, n)">
              打开 ↗
            </a>
          </div>
        </li>
      </ul>

      <p v-if="notice" class="notif-notice" role="status">{{ notice }}</p>
      <p v-if="items.length" class="notif-hint">
        只显示最近 20 条；更早的通知不再列出。
      </p>
    </template>
  </div>
</template>

<style scoped>
.notif { display: flex; flex-direction: column; gap: 0.6rem; }
.notif-head {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 0.5rem;
}
.notif-title {
  margin: 0; font-size: 0.9rem; font-weight: 600; color: var(--vp-c-text-1);
  display: flex; flex-wrap: wrap; align-items: center; gap: 0.45rem;
}
.notif-badge {
  padding: 0.1rem 0.45rem; border-radius: 999px;
  font-size: 0.7rem; font-weight: 600;
  color: var(--rw-on-brand); background: var(--vp-c-brand-1);
}
.notif-head-actions { display: flex; flex-wrap: wrap; gap: 0.45rem; }
.notif-btn {
  min-height: 36px; padding: 0.35rem 0.8rem;
  border: 1px solid var(--vp-c-brand-1); border-radius: 999px;
  background: var(--vp-c-brand-1); color: var(--rw-on-brand);
  font-size: 0.8rem; font-weight: 600; cursor: pointer;
}
.notif-btn:disabled { opacity: 0.5; cursor: default; }
.notif-ghost { background: transparent; color: var(--vp-c-text-1); border-color: var(--vp-c-divider); }
.notif-btn:focus-visible, .notif-inline-btn:focus-visible, .notif-subject:focus-visible, .notif-open:focus-visible {
  outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px;
}
.notif-muted, .notif-empty {
  margin: 0.2rem 0 0; font-size: 0.84rem; line-height: 1.7; color: var(--vp-c-text-3);
}
.notif-error { margin: 0.2rem 0 0; font-size: 0.84rem; line-height: 1.7; color: var(--rw-danger); }
.notif-notice { margin: 0; font-size: 0.8rem; color: var(--vp-c-brand-1); }
.notif-hint { margin: 0; font-size: 0.72rem; color: var(--vp-c-text-3); }
.notif-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.5rem; }
.notif-item {
  border: 1px solid var(--vp-c-divider); border-radius: 10px;
  padding: 0.6rem 0.7rem; background: var(--vp-c-bg);
}
.notif-item.is-unread { border-left: 3px solid var(--vp-c-brand-1); }
.notif-item-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.45rem; }
.notif-kind {
  font-size: 0.68rem; font-weight: 600; color: var(--rw-link);
  background: var(--vp-c-brand-soft); border-radius: 4px; padding: 0 0.3rem;
}
.notif-subject {
  font-size: 0.86rem; font-weight: 600; color: var(--vp-c-text-1);
  text-decoration: none; overflow-wrap: anywhere;
}
a.notif-subject:hover { color: var(--vp-c-brand-1); text-decoration: underline; }
.notif-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--vp-c-brand-1); flex: none;
}
.notif-time { margin-left: auto; font-size: 0.72rem; color: var(--vp-c-text-3); white-space: nowrap; }
.notif-body {
  margin: 0.3rem 0 0; font-size: 0.8rem; line-height: 1.6;
  color: var(--vp-c-text-2); overflow-wrap: anywhere;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.notif-item-foot { display: flex; flex-wrap: wrap; align-items: center; gap: 0.8rem; margin-top: 0.35rem; }
.notif-inline-btn {
  border: 0; background: none; padding: 0;
  font-size: 0.75rem; color: var(--vp-c-text-3);
  text-decoration: underline; cursor: pointer;
}
.notif-inline-btn:disabled { opacity: 0.5; cursor: default; }
.notif-open { font-size: 0.75rem; color: var(--rw-link); text-decoration: none; }
.notif-open:hover { text-decoration: underline; }

@media (max-width: 480px) {
  .notif-time { margin-left: 0; }
  .notif-head { align-items: flex-start; }
}
</style>
