<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { findShareEntry, type ShareEntry } from '../lib/share'

type Me = { handle: string; display_name: string; email_verified?: boolean }
type Mine = { id: number; status: string; payload: Record<string, unknown>; created_at: string }

const API = ((import.meta.env.VITE_ROBOWIKI_API as string | undefined) || '/api/v1')
  .replace(/\/$/, '')
const TOKEN_KEY = 'robowiki.token'

const entry = ref<ShareEntry | null>(null)
const detail = ref<{ params?: { key: string; label: string; value: string }[] } | null>(null)
const me = ref<Me | null>(null)
const mode = ref<'login' | 'register' | 'forgot'>('login')
const handle = ref('')
const password = ref('')
const displayName = ref('')
const email = ref('')
const resetToken = ref('')
const newPassword = ref('')
const authNotice = ref('')
const verifySent = ref(false)
const verifyToken = ref('')
const field = ref('price_cny')
const customField = ref('')
const value = ref('')
const note = ref('')
const sourceUrl = ref('')
const busy = ref(false)
const error = ref('')
const done = ref<number | null>(null)
const mine = ref<Mine[]>([])
const STATUS_LABEL: Record<string, string> = {
  pending: '待审核', accepted: '已通过', rejected: '已驳回',
  pr_open: 'PR 中', merged: '已合并', released: '已发布',
}
const apiReady = ref<boolean | null>(null)

const token = () => localStorage.getItem(TOKEN_KEY)

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...(init?.headers as any) }
  if (init?.body) headers['Content-Type'] = 'application/json'
  const t = token()
  if (t) headers['Authorization'] = `Bearer ${t}`
  const r = await fetch(`${API}${path}`, { ...init, headers })
  const text = await r.text()
  const data = text ? JSON.parse(text) : null
  if (!r.ok) {
    const d = data?.detail
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? d.map((x: any) => x.msg).join('；') : `HTTP ${r.status}`)
  }
  return data as T
}

async function loadMine() {
  if (!token()) return
  mine.value = await req<Mine[]>('/submissions/mine?limit=3').catch(() => [])
}

onMounted(async () => {
  entry.value = await findShareEntry(window.location.pathname)
  if (!entry.value) return
  apiReady.value = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) })
    .then(r => r.ok)
    .catch(() => false)
  if (!apiReady.value) return
  detail.value = await fetch(withBase(entry.value.json)).then(r => r.ok ? r.json() : null).catch(() => null)
  if (token()) {
    me.value = await req<Me>('/auth/me').catch(() => {
      localStorage.removeItem(TOKEN_KEY)
      return null
    })
    await loadMine()
  }
})

const issueUrl = computed(() => {
  if (!entry.value) return ''
  const title = encodeURIComponent(`[数据纠错] ${entry.value.id}`)
  return `https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=data-fix.yml&title=${title}`
})

const options = computed(() => {
  const base = [
    { value: 'price_cny', label: '价格' },
    { value: 'url', label: '官方来源 URL' },
    { value: 'source_tier', label: '来源等级' },
    { value: 'last_checked', label: '最近核对日期' },
    { value: 'notes', label: '备注' },
  ]
  const specs = (detail.value?.params || [])
    .filter(p => p.key)
    .map(p => ({ value: `specs.${p.key}`, label: `${p.label}（${p.value}）` }))
  return [...base, ...specs, { value: '__custom__', label: '其他参数…' }]
})

const key = computed(() => field.value === '__custom__' ? customField.value.trim() : field.value)

async function auth() {
  error.value = ''
  authNotice.value = ''
  if (mode.value === 'forgot') {
    if (!email.value.trim()) { error.value = '请填写注册邮箱'; return }
    busy.value = true
    try {
      const r = await req<{ message: string }>('/auth/password/forgot', {
        method: 'POST', body: JSON.stringify({ email: email.value.trim() }),
      })
      authNotice.value = r.message || '如果该邮箱已注册，重置邮件已发送'
    } catch (e: any) {
      error.value = e.message
    } finally {
      busy.value = false
    }
    return
  }
  if (handle.value.trim().length < 2 || password.value.length < 6) {
    error.value = '账号至少 2 位、密码至少 6 位'
    return
  }
  if (mode.value === 'register' && !displayName.value.trim()) {
    error.value = '请填写显示名'
    return
  }
  busy.value = true
  try {
    const body: Record<string, string> = { handle: handle.value.trim(), password: password.value }
    if (mode.value === 'register') {
      body.display_name = displayName.value.trim()
      if (email.value.trim()) body.email = email.value.trim()
    }
    const r = await req<{ access_token: string; user: Me }>(
      mode.value === 'login' ? '/auth/login' : '/auth/register', {
        method: 'POST', body: JSON.stringify(body),
      })
    localStorage.setItem(TOKEN_KEY, r.access_token)
    me.value = r.user
    await loadMine()
  } catch (e: any) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function resetPassword() {
  error.value = ''
  authNotice.value = ''
  if (newPassword.value.length < 6) { error.value = '新密码至少 6 位'; return }
  busy.value = true
  try {
    await req('/auth/password/reset', {
      method: 'POST',
      body: JSON.stringify({ token: resetToken.value.trim(), password: newPassword.value }),
    })
    authNotice.value = '密码已重置，请用新密码登录'
    mode.value = 'login'
    resetToken.value = ''
    newPassword.value = ''
  } catch (e: any) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function requestVerify() {
  error.value = ''
  verifySent.value = false
  try {
    await req('/auth/email/verify/request', { method: 'POST' })
    verifySent.value = true
    authNotice.value = '验证邮件已发送；开发环境可在服务端日志看到令牌'
  } catch (e: any) {
    error.value = e.message
  }
}

async function verifyEmail() {
  error.value = ''
  try {
    const u = await req<Me>('/auth/email/verify', {
      method: 'POST', body: JSON.stringify({ token: verifyToken.value.trim() }),
    })
    me.value = u
    verifySent.value = false
    verifyToken.value = ''
    authNotice.value = '邮箱已验证'
  } catch (e: any) {
    error.value = e.message
  }
}

function typed() {
  if (field.value === 'source_tier') return value.value
  if (field.value === 'price_cny') {
    const n = Number(value.value)
    return Number.isFinite(n) ? n : value.value
  }
  const s = value.value.trim()
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s)
  return s
}

async function submit() {
  error.value = ''
  done.value = null
  if (!key.value) { error.value = '请选择或填写字段'; return }
  if (!value.value.trim()) { error.value = '请填写正确的值'; return }
  if (note.value.trim().length < 5) { error.value = '请写清依据（至少 5 个字）'; return }
  if (!/^https?:\/\//i.test(sourceUrl.value.trim())) {
    error.value = '来源链接需要以 http:// 或 https:// 开头'; return
  }
  busy.value = true
  try {
    const s = await req<{ id: number }>('/submissions', {
      method: 'POST',
      body: JSON.stringify({
        kind: 'part_patch',
        target_id: entry.value!.id,
        payload: { [key.value]: typed() },
        evidence: { note: note.value.trim(), source_url: sourceUrl.value.trim() },
      }),
    })
    done.value = s.id
    value.value = ''
    note.value = ''
    sourceUrl.value = ''
    await loadMine()
  } catch (e: any) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function logout() {
  localStorage.removeItem(TOKEN_KEY)
  me.value = null
  mine.value = []
}
</script>

<template>
  <section v-if="entry" class="rw-fix" aria-label="提交参数纠错">
    <div class="rw-fix-head">
      <b>发现参数有问题？</b>
      <span v-if="me">{{ me.display_name }}（{{ me.handle }}）· <a href="#" @click.prevent="logout">退出</a></span>
    </div>

    <template v-if="apiReady === false">
      <p class="rw-fix-text">
        当前是只读镜像，登录与站内提交没有后端；可以到 GitHub 用表单纠错，维护者会转成提案。
      </p>
      <a class="rw-fix-alt" :href="issueUrl" target="_blank" rel="noopener">去 GitHub 提交纠错 ↗</a>
    </template>

    <template v-else>
    <template v-if="!me">
      <p class="rw-fix-text">
        登录后提交纠错，站务审核通过会转成 PR；合并并发布数据版本后页面才更新。
        不需要 GitHub 账号。
      </p>
      <div class="rw-fix-auth">
        <button type="button" :class="{ on: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button type="button" :class="{ on: mode === 'register' }" @click="mode = 'register'">注册</button>
        <button type="button" :class="{ on: mode === 'forgot' }" @click="mode = 'forgot'; authNotice = ''">找回密码</button>
      </div>

      <template v-if="mode === 'forgot'">
        <div class="rw-fix-grid">
          <input v-model="email" type="email" placeholder="注册邮箱" autocomplete="email" />
          <button type="button" :disabled="busy" @click="auth">发送重置邮件</button>
        </div>
        <div class="rw-fix-grid">
          <input v-model="resetToken" placeholder="邮件里的重置令牌" />
          <input v-model="newPassword" type="password" placeholder="新密码（至少 6 位）" autocomplete="new-password" />
          <button type="button" :disabled="busy || !resetToken.trim()" @click="resetPassword">重置密码</button>
        </div>
        <p class="rw-fix-hint">令牌只发到注册邮箱；开发环境（EMAIL_MODE=log）在服务端日志查看。</p>
      </template>

      <div v-else class="rw-fix-grid">
        <input v-model="handle" placeholder="账号（2–24 位 a-z、0-9、-、_）" autocomplete="username" />
        <input v-if="mode === 'register'" v-model="displayName" placeholder="显示名" />
        <input v-if="mode === 'register'" v-model="email" type="email" placeholder="邮箱（用于验证/找回，建议填写）" autocomplete="email" />
        <input v-model="password" type="password" placeholder="密码（至少 6 位）"
          autocomplete="current-password" @keyup.enter="auth" />
        <button type="button" :disabled="busy" @click="auth">{{ busy ? '请稍候…' : (mode === 'login' ? '登录' : '注册并登录') }}</button>
      </div>
    </template>

    <template v-else>
      <div v-if="!me.email_verified" class="rw-fix-verify">
        <span>邮箱未验证。</span>
        <button type="button" @click="requestVerify">发送验证邮件</button>
        <template v-if="verifySent">
          <input v-model="verifyToken" placeholder="邮件里的验证令牌" />
          <button type="button" :disabled="!verifyToken.trim()" @click="verifyEmail">验证</button>
        </template>
      </div>
      <p class="rw-fix-text">
        只提交你核对过的字段与来源；审核通过不等于生效，合并并发布 <code>data-v*</code> 后才更新。
      </p>
      <div class="rw-fix-grid">
        <label>
          <span>字段</span>
          <select v-model="field">
            <option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
        <label v-if="field === '__custom__'">
          <span>参数名</span>
          <input v-model="customField" placeholder="specs.xxx" />
        </label>
        <label>
          <span>正确的值</span>
          <select v-if="field === 'source_tier'" v-model="value">
            <option value="A">A（逐项核对官方手册）</option>
            <option value="B">B（公开网页来源）</option>
          </select>
          <input v-else v-model="value" placeholder="数值或文本" />
        </label>
      </div>
      <textarea v-model="note" rows="2" placeholder="依据：哪份手册的哪一页 / 哪封厂商邮件 / 实测条件" />
      <input v-model="sourceUrl" placeholder="来源链接（http/https）" />
      <div class="rw-fix-actions">
        <button type="button" :disabled="busy" @click="submit">{{ busy ? '提交中…' : '提交纠错' }}</button>
        <span v-if="done" class="ok">已提交提案 #{{ done }}，等待审核</span>
      </div>
    </template>

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="authNotice" class="notice">{{ authNotice }}</p>

    <div v-if="mine.length" class="rw-fix-mine">
      <div v-for="s in mine" :key="s.id">
        #{{ s.id }} · {{ STATUS_LABEL[s.status] || s.status }} · {{ Object.keys(s.payload).join(', ') }}
        <span>{{ s.created_at.slice(0, 10) }}</span>
      </div>
    </div>
    </template>
  </section>
</template>

<style scoped>
.rw-fix {
  margin: 1rem 0;
  padding: 1rem 1.1rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
}
.rw-fix-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--vp-c-text-2);
}
.rw-fix-text {
  margin: 0.5rem 0 0.8rem;
  font-size: 0.9rem;
}
.rw-fix-auth {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}
.rw-fix-auth button,
.rw-fix-actions button,
.rw-fix-grid button {
  border: 1px solid var(--vp-c-brand-1);
  background: transparent;
  color: var(--vp-c-brand-1);
  padding: 0.4rem 0.85rem;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
}
.rw-fix-auth button.on,
.rw-fix-actions button,
.rw-fix-grid button {
  background: var(--vp-c-brand-1);
  color: #fff;
}
.rw-fix-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
}
.rw-fix-grid label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
}
.rw-fix input,
.rw-fix select,
.rw-fix textarea {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  padding: 0.45rem 0.6rem;
  font-size: 0.86rem;
  margin-bottom: 0.5rem;
}
.rw-fix-grid input,
.rw-fix-grid select {
  margin-bottom: 0;
}
.rw-fix-actions {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}
.rw-fix .ok {
  color: var(--vp-c-success-1);
  font-size: 0.85rem;
}
.rw-fix .err {
  color: var(--vp-c-danger-1);
  font-size: 0.85rem;
  margin: 0.5rem 0 0;
}
.rw-fix .notice {
  color: var(--vp-c-success-1);
  font-size: 0.85rem;
  margin: 0.5rem 0 0;
}
.rw-fix-hint {
  margin: 0.2rem 0 0.4rem;
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
}
.rw-fix-verify {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0.2rem 0 0.8rem;
  padding: 0.5rem 0.7rem;
  border: 1px solid var(--vp-c-warning-1);
  border-radius: 8px;
  background: var(--vp-c-warning-soft);
  font-size: 0.82rem;
}
.rw-fix-verify button {
  border: 1px solid var(--vp-c-warning-1);
  background: transparent;
  color: var(--vp-c-warning-1);
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  cursor: pointer;
}
.rw-fix-verify input {
  margin: 0;
  max-width: 220px;
}
.rw-fix-alt {
  display: inline-block;
  margin-top: 0.2rem;
  font-size: 0.88rem;
  color: var(--vp-c-brand-1);
  font-weight: 600;
}
.rw-fix-mine {
  margin-top: 0.8rem;
  border-top: 1px solid var(--vp-c-divider);
  padding-top: 0.6rem;
  font-size: 0.8rem;
  color: var(--vp-c-text-2);
}
.rw-fix-mine div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.15rem 0;
}
@media (max-width: 640px) {
  .rw-fix-grid { grid-template-columns: 1fr; }
}
</style>
