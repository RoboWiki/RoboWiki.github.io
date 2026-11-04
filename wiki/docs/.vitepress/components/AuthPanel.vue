<script setup lang="ts">
/**
 * 站内账号面板：登录 / 注册 / 找回密码 / 邮箱验证 / 账号中心。
 *
 * 表单逻辑交给 VeeValidate 4 + Zod（`useForm` + `toTypedSchema`），不再手写
 * 「if (x.length < 2) error = ...」那一套 —— 手写校验和输入框各自演化，
 * 迟早出现「前端说能过、后端 422」的不一致。这里的 Zod schema 与后端
 * `backend/app/schemas.py` 的字段约束逐条对齐，改后端时同步改这里。
 *
 * 可访问性约定（每个字段都遵守）：
 *   · <label for> 真实绑定，不靠 placeholder 当标签
 *   · 出错时 aria-invalid="true" 且 aria-describedby 指向错误文本
 *   · 错误文本 role="alert"（表单失败用 aria-live 播报）
 *   · 提交按钮在请求中 disabled 且表单 aria-busy
 *   · 表单内 Enter 即提交（原生 form + type="submit"），不额外绑 keyup
 *
 * 账号中心的分区（资料 / 密码 / 登录方式）与「危险操作二次确认」参考了
 * Cal.com、Outline 的设置页交互；只借鉴信息结构与反馈方式，没有复制代码
 * （Outline 部分代码使用 BSL 许可）。
 */
import { computed, nextTick, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { TabsContent, TabsList, TabsRoot, TabsTrigger } from 'reka-ui'
import { ApiError, apiAvailable, apiBase, apiErrorMessage, apiFetch, isMirror, MIRROR_READONLY_NOTE, PRIMARY_SITE } from '../lib/api'
import { clearAuth, clearHashAuth, getRefreshToken, getToken, readHashAuth, setRefreshToken, setToken } from '../lib/auth'
import NotificationList from './NotificationList.vue'

type Me = {
  handle: string
  display_name: string
  email?: string | null
  email_verified?: boolean
  password_set?: boolean
}
type Providers = { email: boolean; github: boolean; wechat_mini: boolean }
type Identity = {
  provider: string
  subject: string
  email?: string | null
  created_at: string
}
type AccountTab = 'profile' | 'security' | 'notifications' | 'identities'

/** 与后端 RegisterIn 完全一致的约束 */
const HANDLE_RE = /^[A-Za-z0-9][A-Za-z0-9_-]*$/
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/

const MODES = ['login', 'register', 'forgot'] as const
type Mode = (typeof MODES)[number]
const TAB_LABEL: Record<Mode, string> = { login: '登录', register: '注册', forgot: '找回密码' }

type AccountValues = { handle: string; displayName: string; email: string; password: string }
type ChangeValues = {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

/**
 * 按当前模式生成 schema。三种模式共用同一份字段集（未渲染的字段保持空串），
 * 这样切换模式时不用重建整个 form 实例，输入内容也不会丢。
 */
function accountSchema(m: Mode): z.ZodType<AccountValues, z.ZodTypeDef, AccountValues> {
  const handle = z.string().trim().min(2, '账号至少 2 位').max(24, '账号最多 24 位')
    .regex(HANDLE_RE, '账号只能用 a-z、0-9、-、_，并以字母或数字开头')
  const password = z.string().min(6, '密码至少 6 位').max(128, '密码最多 128 位')
  const displayName = z.string().trim().min(1, '请填写显示名').max(32, '显示名最多 32 字')
  const emailOptional = z.string().trim().max(200, '邮箱过长')
    .refine(v => !v || EMAIL_RE.test(v), '邮箱格式不正确')
  const emailRequired = z.string().trim().min(1, '请填写注册邮箱').max(200, '邮箱过长')
    .refine(v => EMAIL_RE.test(v), '邮箱格式不正确')

  if (m === 'forgot') {
    return z.object({
      email: emailRequired,
      handle: z.string().trim().max(24),
      displayName: z.string().trim().max(32),
      password: z.string().max(128),
    })
  }
  if (m === 'register') {
    return z.object({ handle, password, displayName, email: emailOptional })
  }
  return z.object({
    handle,
    password,
    displayName: z.string().trim().max(32),
    email: emailOptional,
  })
}

const apiReady = ref<boolean | null>(null)
const me = ref<Me | null>(null)
const mode = ref<Mode>('login')
const serverError = ref('')
const notice = ref('')
const tabEls = ref<HTMLButtonElement[]>([])
/** 服务端渠道能力；null = 还没读到或读取失败（不是「没有 GitHub」） */
const providers = ref<Providers | null>(null)
const providersChecked = ref(false)

/* ── 账号中心：身份与改密状态 ──────────────────────────────────────────── */
const accountTab = ref<AccountTab>('profile')
const identities = ref<Identity[]>([])
const identitiesBusy = ref(false)
const identitiesLoaded = ref(false)
const identityError = ref('')
const identityNotice = ref('')
const pendingUnbind = ref<string | null>(null)
const unbindBusy = ref<string | null>(null)
const changeError = ref('')
const changeNotice = ref('')

/* ── 通知 ──────────────────────────────────────────────────────────────── */
/** 未读角标：由 NotificationList 拉完列表后回传，退出/401 时清零 */
const unreadCount = ref(0)

/** 401：apiFetch 已清 token，这里把界面退回登录态，不要让「账号中心」继续挂着 */
function onNotificationAuthExpired(message: string) {
  me.value = null
  identities.value = []
  identitiesLoaded.value = false
  unreadCount.value = 0
  notice.value = message || '登录已过期，请重新登录'
}

/** 后端 detail 的解析与 401/429/断网文案统一收在 lib/api */
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  return apiFetch<T>(path, init)
}

/**
 * GitHub 登录必须回主站：OAuth 的 redirect_uri 绑在主域，
 * 成功后由后端把一次性 code 送回 return_to（当前站点 origin）。
 */
const githubHref = computed(() => {
  const origin = typeof window !== 'undefined' ? window.location.origin : PRIMARY_SITE
  return `${apiBase()}/auth/github/login?return_to=${encodeURIComponent(origin)}`
})

/** 只接受站内相对路径，避免 ?redirect=https://… 变成开放跳转 */
function goAfterLogin() {
  const redirect = new URLSearchParams(window.location.search).get('redirect')
  if (redirect && redirect.startsWith('/') && !redirect.startsWith('//')) {
    window.location.href = redirect
  }
}

/* ── 登录 / 注册 / 找回密码 ─────────────────────────────────────────────── */
const {
  errors: accountErrors,
  isSubmitting: accountBusy,
  handleSubmit: onAccountSubmitRaw,
  defineField: accountField,
  setErrors: setAccountErrors,
  resetForm: resetAccount,
} = useForm<AccountValues>({
  validationSchema: computed(() => toTypedSchema(accountSchema(mode.value))),
  initialValues: { handle: '', displayName: '', email: '', password: '' },
})

const [handle, handleAttrs] = accountField('handle')
const [displayName, displayNameAttrs] = accountField('displayName')
const [email, emailAttrs] = accountField('email')
const [password, passwordAttrs] = accountField('password')

const onAccountSubmit = onAccountSubmitRaw(async values => {
  serverError.value = ''
  notice.value = ''
  try {
    if (mode.value === 'forgot') {
      const r = await req<{ message: string }>('/auth/password/forgot', {
        method: 'POST', body: JSON.stringify({ email: values.email }),
      })
      notice.value = r.message || '如果该邮箱已注册，重置邮件已发送'
      return
    }
    const body: Record<string, string> = { handle: values.handle, password: values.password }
    if (mode.value === 'register') {
      body.display_name = values.displayName
      if (values.email) body.email = values.email
    }
    const r = await req<{ access_token: string; refresh_token?: string; user: Me }>(
      mode.value === 'login' ? '/auth/login' : '/auth/register',
      { method: 'POST', body: JSON.stringify(body) },
    )
    setToken(r.access_token)
    setRefreshToken(r.refresh_token)
    me.value = r.user
    password.value = ''
    notice.value = mode.value === 'login' ? '登录成功' : '注册成功'
    // 身份列表异步加载，不阻塞 ?redirect= 跳转；账号中心自己显示加载态。
    void loadIdentities()
    goAfterLogin()
  } catch (e: any) {
    serverError.value = apiErrorMessage(e, '请求失败，请稍后再试')
  }
})

/* ── 重置密码（令牌 + 新密码） ──────────────────────────────────────────── */
const resetCtx = useForm({
  validationSchema: toTypedSchema(z.object({
    token: z.string().trim().min(10, '令牌至少 10 位').max(200, '令牌过长'),
    password: z.string().min(6, '新密码至少 6 位').max(128, '新密码最多 128 位'),
  })),
  initialValues: { token: '', password: '' },
})
const {
  errors: resetErrors,
  isSubmitting: resetBusy,
  handleSubmit: onResetSubmitRaw,
  defineField: resetField,
} = resetCtx
const [resetToken, resetTokenAttrs] = resetField('token')
const [newPassword, newPasswordAttrs] = resetField('password')

const onResetSubmit = onResetSubmitRaw(async values => {
  serverError.value = ''
  notice.value = ''
  try {
    await req('/auth/password/reset', {
      method: 'POST',
      body: JSON.stringify({ token: values.token, password: values.password }),
    })
    notice.value = '密码已重置，请用新密码登录'
    // 先切回登录态再提示：notice 留给登录表单显示，切换动作本身不清空它
    mode.value = 'login'
    resetCtx.resetForm()
  } catch (e: any) {
    serverError.value = apiErrorMessage(e, '请求失败，请稍后再试')
  }
})

/* ── 邮箱验证 ──────────────────────────────────────────────────────────── */
const verifySent = ref(false)
const verifyRequestBusy = ref(false)
const verifyCtx = useForm({
  validationSchema: toTypedSchema(z.object({
    token: z.string().trim().min(10, '令牌至少 10 位').max(200, '令牌过长'),
  })),
  initialValues: { token: '' },
})
const {
  errors: verifyErrors,
  isSubmitting: verifyBusy,
  handleSubmit: onVerifySubmitRaw,
  defineField: verifyField,
} = verifyCtx
const [verifyToken, verifyTokenAttrs] = verifyField('token')

async function requestVerify() {
  if (verifyRequestBusy.value) return
  serverError.value = ''
  notice.value = ''
  verifyRequestBusy.value = true
  try {
    await req('/auth/email/verify/request', { method: 'POST' })
    verifySent.value = true
    notice.value = '验证邮件已发送；开发环境可在服务端日志看到令牌'
  } catch (e: any) {
    serverError.value = apiErrorMessage(e, '请求失败，请稍后再试')
  } finally {
    verifyRequestBusy.value = false
  }
}

const onVerifySubmit = onVerifySubmitRaw(async values => {
  serverError.value = ''
  notice.value = ''
  try {
    me.value = await req<Me>('/auth/email/verify', {
      method: 'POST', body: JSON.stringify({ token: values.token }),
    })
    verifySent.value = false
    verifyCtx.resetForm()
    notice.value = '邮箱已验证'
  } catch (e: any) {
    serverError.value = apiErrorMessage(e, '请求失败，请稍后再试')
  }
})

/* ── 修改密码：成功后当场换新 token ─────────────────────────────────────── */
const changeCtx = useForm<ChangeValues>({
  validationSchema: toTypedSchema(
    z.object({
      currentPassword: z.string().min(1, '请输入当前密码').max(128, '密码最多 128 位'),
      newPassword: z.string().min(6, '新密码至少 6 位').max(128, '新密码最多 128 位'),
      confirmPassword: z.string().min(1, '请再次输入新密码').max(128, '密码最多 128 位'),
    }).refine(v => v.newPassword === v.confirmPassword, {
      message: '两次输入的新密码不一致',
      path: ['confirmPassword'],
    }),
  ),
  initialValues: { currentPassword: '', newPassword: '', confirmPassword: '' },
})
const {
  errors: changeErrors,
  isSubmitting: changeBusy,
  handleSubmit: onChangeSubmitRaw,
  defineField: changeField,
  resetForm: resetChange,
} = changeCtx
const [currentPassword, currentPasswordAttrs] = changeField('currentPassword')
const [newPasswordInput, newPasswordInputAttrs] = changeField('newPassword')
const [confirmPassword, confirmPasswordAttrs] = changeField('confirmPassword')

const onChangeSubmit = onChangeSubmitRaw(async values => {
  changeError.value = ''
  changeNotice.value = ''
  try {
    const r = await req<{ access_token: string; refresh_token?: string; user: Me }>('/auth/password/change', {
      method: 'POST',
      body: JSON.stringify({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      }),
    })
    // 旧 token 因 pv 变化立即失效；换上新 token，当前会话无缝继续。
    setToken(r.access_token)
    setRefreshToken(r.refresh_token)
    me.value = r.user
    resetChange()
    changeNotice.value = '密码已更新，本设备已换用新令牌；其他设备的登录已失效'
  } catch (e: any) {
    changeError.value = e.status === 403
      ? '当前密码不正确'
      : apiErrorMessage(e, '修改失败，请稍后再试')
  }
})

/* ── 已绑定身份 ────────────────────────────────────────────────────────── */
const KNOWN_PROVIDERS: { id: string; label: string }[] = [
  { id: 'github', label: 'GitHub' },
  { id: 'wechat_mini', label: '微信小程序' },
]

const identityRows = computed(() => {
  const bound = new Map(identities.value.map(i => [i.provider, i]))
  const rows = KNOWN_PROVIDERS.map(p => ({
    provider: p.id, label: p.label, identity: bound.get(p.id) || null,
  }))
  for (const ident of identities.value) {
    if (!KNOWN_PROVIDERS.some(p => p.id === ident.provider)) {
      rows.push({ provider: ident.provider, label: ident.provider, identity: ident })
    }
  }
  return rows
})

function providerLabel(provider: string): string {
  return KNOWN_PROVIDERS.find(p => p.id === provider)?.label || provider
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? ''
    : d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

async function loadIdentities() {
  identitiesBusy.value = true
  identityError.value = ''
  identityNotice.value = ''
  pendingUnbind.value = null
  try {
    identities.value = await req<Identity[]>('/auth/identities')
  } catch (e: any) {
    identityError.value = apiErrorMessage(e, '无法读取已绑定身份，请稍后重试')
  } finally {
    identitiesBusy.value = false
    identitiesLoaded.value = true
  }
}

function askUnbind(provider: string) {
  identityError.value = ''
  identityNotice.value = ''
  pendingUnbind.value = provider
}

async function confirmUnbind(provider: string) {
  if (unbindBusy.value) return
  identityError.value = ''
  identityNotice.value = ''
  unbindBusy.value = provider
  try {
    await req(`/auth/identities/${encodeURIComponent(provider)}`, { method: 'DELETE' })
    identities.value = identities.value.filter(i => i.provider !== provider)
    identityNotice.value = `已解绑 ${providerLabel(provider)}`
  } catch (e: any) {
    identityError.value = e.status === 409
      ? '至少保留一种登录方式：请先设置本站密码，或保留另一种已绑定身份。'
      : apiErrorMessage(e, '解绑失败，请稍后再试')
  } finally {
    unbindBusy.value = null
    pendingUnbind.value = null
  }
}

/* ── 模式切换（tablist 语义 + 方向键） ─────────────────────────────────── */
function selectMode(m: Mode) {
  if (mode.value === m) return
  mode.value = m
  serverError.value = ''
  notice.value = ''
  setAccountErrors({})
}

function onTabKey(evt: KeyboardEvent) {
  const idx = MODES.indexOf(mode.value)
  let next = idx
  if (evt.key === 'ArrowRight') next = (idx + 1) % MODES.length
  else if (evt.key === 'ArrowLeft') next = (idx - 1 + MODES.length) % MODES.length
  else if (evt.key === 'Home') next = 0
  else if (evt.key === 'End') next = MODES.length - 1
  else return
  evt.preventDefault()
  selectMode(MODES[next])
  nextTick(() => tabEls.value[next]?.focus())
}

async function logout() {
  try {
    const refresh = getRefreshToken()
    if (refresh) await apiFetch('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refresh }) })
  } catch { /* 本地仍要退出 */ }
  clearAuth()
  me.value = null
  identities.value = []
  identitiesLoaded.value = false
  identityError.value = ''
  identityNotice.value = ''
  pendingUnbind.value = null
  changeError.value = ''
  changeNotice.value = ''
  unreadCount.value = 0
  accountTab.value = 'profile'
  // 用 resetForm 清值 + 清错误；直接改 password 会让表单在重新挂载时闪一条「至少 6 位」
  resetAccount()
  resetChange()
  notice.value = '已退出登录'
}

onMounted(async () => {
  // OAuth 回调有两种：
  //   · #token=<jwt>  旧形式，直接落盘
  //   · #code=<code>  新形式（主站 → github.io 跨域），先 POST /auth/handoff 换 token
  // 读取与清理分开：code 是一次性的，兑成功后再抹 fragment，避免失败时连重试机会都没有。
  const hash = readHashAuth()
  if (hash.error) {
    serverError.value = hash.errorDescription || `GitHub 登录未完成（${hash.error}）`
    clearHashAuth()
  }
  if (hash.token) {
    setToken(hash.token)
    clearHashAuth()
    notice.value = '登录成功'
  }

  apiReady.value = await apiAvailable()
  if (!apiReady.value) {
    // 镜像站主站暂时探不到：清掉一次性 code，只展示只读说明
    if (hash.code) clearHashAuth()
    return
  }

  if (hash.code) {
    try {
      const r = await req<{ access_token?: string; token?: string; user?: Me }>('/auth/handoff', {
        method: 'POST',
        body: JSON.stringify({ code: hash.code }),
      })
      const issued = r?.access_token || r?.token
      if (!issued) throw new Error('主站没有返回登录令牌，请重新登录')
      setToken(issued)
      setRefreshToken(r.refresh_token)
      if (r.user) me.value = r.user
      notice.value = '登录成功'
    } catch (e: any) {
      // handoff 的 401 是「code 过期/已用」，比通用「登录已过期」更准确
      const detail = e instanceof ApiError && typeof e.detail === 'string' ? e.detail : ''
      serverError.value = detail || apiErrorMessage(e, '登录未能完成，请重新点击 GitHub 登录')
    } finally {
      clearHashAuth()
    }
  }

  // 先问服务端能开哪些渠道：未配置的 GitHub 不渲染链接，也就不发无效请求
  try {
    providers.value = await req<Providers>('/auth/providers')
  } catch {
    providers.value = null
  } finally {
    providersChecked.value = true
  }
  if (!getToken()) return
  try {
    me.value = await req<Me>('/auth/me')
    await loadIdentities()
  } catch {
    // 401 已由 apiFetch 清 token；网络抖动不要误清
    if (!getToken()) me.value = null
  }
})
</script>

<template>
  <section class="auth-page">
    <div v-if="apiReady === false" class="auth-card">
      <h1>当前为只读快照</h1>
      <p>{{ isMirror() ? MIRROR_READONLY_NOTE : '主站服务暂时不可达，当前显示构建快照。' }}</p>
      <p>登录、评分、评论与纠错需要主站服务，可以稍后重试，或直接到主站操作：</p>
      <a class="auth-primary" :href="`${PRIMARY_SITE}/login`">去 {{ PRIMARY_SITE }} 登录 ↗</a>
    </div>

    <!-- ── 已登录：账号中心 ────────────────────────────────────────────── -->
    <div v-else-if="me" class="auth-card"
      :aria-busy="accountBusy || verifyBusy || verifyRequestBusy || identitiesBusy || !!unbindBusy || changeBusy">
      <h1>账号中心</h1>
      <p class="auth-lead">管理账号资料、邮箱验证、本站密码与第三方登录方式。</p>

      <TabsRoot v-model="accountTab" class="acct" :unmount-on-hide="false">
        <TabsList class="acct-tabs" aria-label="账号设置">
          <TabsTrigger value="profile" class="acct-tab">账号信息</TabsTrigger>
          <TabsTrigger value="security" class="acct-tab">修改密码</TabsTrigger>
          <TabsTrigger value="notifications" class="acct-tab">
            通知
            <span v-if="unreadCount > 0" class="acct-tab-count">
              {{ unreadCount > 99 ? '99+' : unreadCount }}
              <span class="acct-sr">条未读</span>
            </span>
          </TabsTrigger>
          <TabsTrigger value="identities" class="acct-tab">登录方式</TabsTrigger>
        </TabsList>

        <!-- 账号信息 + 邮箱验证 -->
        <TabsContent value="profile" class="acct-panel">
          <dl class="acct-facts">
            <div class="acct-fact">
              <dt>显示名</dt>
              <dd>{{ me.display_name }}</dd>
            </div>
            <div class="acct-fact">
              <dt>账号</dt>
              <dd>@{{ me.handle }}</dd>
            </div>
            <div class="acct-fact">
              <dt>邮箱</dt>
              <dd>
                <template v-if="me.email">{{ me.email }}</template>
                <template v-else>未填写</template>
                <span v-if="me.email" class="acct-badge"
                  :class="{ 'acct-badge-warn': !me.email_verified }">
                  {{ me.email_verified ? '已验证' : '未验证' }}
                </span>
              </dd>
            </div>
            <div class="acct-fact">
              <dt>本站密码</dt>
              <dd>{{ me.password_set === false ? '未设置（只能用第三方身份登录）' : '已设置' }}</dd>
            </div>
          </dl>

          <p v-if="me.email && me.email_verified" class="auth-hint" role="status">
            邮箱已验证，可用于找回密码与接收站务通知。
          </p>
          <p v-else-if="me.email" class="auth-warn" role="status">
            邮箱尚未验证：验证只是确认邮箱归属，不影响当前登录。
          </p>
          <p v-else class="auth-warn">
            账号未填写邮箱，不能通过邮件找回密码；可继续使用当前登录方式。
          </p>

          <div v-if="me.email && !me.email_verified" class="auth-verify">
            <button type="button" class="auth-primary" :disabled="verifyRequestBusy"
              @click="requestVerify">
              {{ verifyRequestBusy ? '发送中…' : verifySent ? '重新发送验证邮件' : '发送验证邮件' }}
            </button>
            <form v-if="verifySent" class="auth-form" novalidate :aria-busy="verifyBusy"
              @submit.prevent="onVerifySubmit">
              <div class="auth-field">
                <label class="auth-label" for="auth-verify-token">验证令牌</label>
                <input id="auth-verify-token" v-model="verifyToken" v-bind="verifyTokenAttrs"
                  autocomplete="one-time-code" placeholder="邮件里的验证令牌"
                  :aria-invalid="!!verifyErrors.token"
                  :aria-describedby="verifyErrors.token ? 'err-verify-token' : undefined" />
                <p v-if="verifyErrors.token" id="err-verify-token" class="auth-err-inline" role="alert">
                  {{ verifyErrors.token }}
                </p>
              </div>
              <button type="submit" class="auth-ghost" :disabled="verifyBusy">
                {{ verifyBusy ? '验证中…' : '验证' }}
              </button>
            </form>
          </div>
        </TabsContent>

        <!-- 修改密码 -->
        <TabsContent value="security" class="acct-panel">
          <template v-if="me.password_set === false">
            <p class="auth-hint">
              这个账号由第三方登录创建，还没有本站密码。请退出后用「找回密码」通过
              {{ me.email || '已绑定邮箱' }} 设置密码，或继续使用已绑定身份登录。
            </p>
          </template>
          <template v-else>
            <form class="auth-form" novalidate :aria-busy="changeBusy"
              @submit.prevent="onChangeSubmit">
              <div class="auth-field">
                <label class="auth-label" for="acct-current-password">当前密码</label>
                <input id="acct-current-password" v-model="currentPassword"
                  v-bind="currentPasswordAttrs" type="password" autocomplete="current-password"
                  placeholder="输入当前密码"
                  :aria-invalid="!!changeErrors.currentPassword"
                  :aria-describedby="changeErrors.currentPassword ? 'err-acct-current-password' : undefined" />
                <p v-if="changeErrors.currentPassword" id="err-acct-current-password"
                  class="auth-err-inline" role="alert">
                  {{ changeErrors.currentPassword }}
                </p>
              </div>

              <div class="auth-field">
                <label class="auth-label" for="acct-new-password">新密码</label>
                <input id="acct-new-password" v-model="newPasswordInput"
                  v-bind="newPasswordInputAttrs" type="password" autocomplete="new-password"
                  placeholder="至少 6 位"
                  :aria-invalid="!!changeErrors.newPassword"
                  :aria-describedby="changeErrors.newPassword
                    ? 'acct-new-password-hint err-acct-new-password' : 'acct-new-password-hint'" />
                <p id="acct-new-password-hint" class="auth-hint auth-field-hint">
                  至少 6 位；不要与其他网站复用同一密码。
                </p>
                <p v-if="changeErrors.newPassword" id="err-acct-new-password"
                  class="auth-err-inline" role="alert">
                  {{ changeErrors.newPassword }}
                </p>
              </div>

              <div class="auth-field">
                <label class="auth-label" for="acct-confirm-password">确认新密码</label>
                <input id="acct-confirm-password" v-model="confirmPassword"
                  v-bind="confirmPasswordAttrs" type="password" autocomplete="new-password"
                  placeholder="再输入一次新密码"
                  :aria-invalid="!!changeErrors.confirmPassword"
                  :aria-describedby="changeErrors.confirmPassword ? 'err-acct-confirm-password' : undefined" />
                <p v-if="changeErrors.confirmPassword" id="err-acct-confirm-password"
                  class="auth-err-inline" role="alert">
                  {{ changeErrors.confirmPassword }}
                </p>
              </div>

              <button type="submit" class="auth-primary" :disabled="changeBusy">
                {{ changeBusy ? '修改中…' : '修改密码' }}
              </button>
            </form>
            <p v-if="changeError" class="auth-err" role="alert" aria-live="assertive">
              {{ changeError }}
            </p>
            <p v-if="changeNotice" class="auth-notice" role="status" aria-live="polite">
              {{ changeNotice }}
            </p>
            <p class="auth-hint">
              修改成功后，其他设备上的旧令牌会立即失效；本设备会自动换用新令牌，无需重新登录。
            </p>
          </template>
        </TabsContent>

        <!-- 通知：被回复 / 举报处置结果，登录后自动加载 -->
        <TabsContent value="notifications" class="acct-panel">
          <NotificationList :active="accountTab === 'notifications'"
            @unread="unreadCount = $event"
            @unauthorized="onNotificationAuthExpired" />
        </TabsContent>

        <!-- 已绑定身份 -->
        <TabsContent value="identities" class="acct-panel">
          <p v-if="identitiesBusy" class="auth-hint" role="status">正在读取已绑定身份…</p>
          <p v-if="identityError" class="auth-err" role="alert">{{ identityError }}</p>
          <button v-if="identityError" type="button" class="auth-ghost acct-small"
            @click="loadIdentities">重试</button>

          <ul v-if="identitiesLoaded && !identityError" class="acct-ids">
            <li v-for="row in identityRows" :key="row.provider" class="acct-id">
              <div class="acct-id-main">
                <span class="acct-id-name">{{ row.label }}</span>
                <span class="acct-badge" :class="{ 'acct-badge-warn': !row.identity }">
                  {{ row.identity ? '已绑定' : '未绑定' }}
                </span>
                <span v-if="row.identity?.email" class="acct-id-meta">{{ row.identity.email }}</span>
                <span v-else-if="row.identity" class="acct-id-meta">
                  绑定于 {{ formatDate(row.identity.created_at) }}
                </span>
              </div>
              <div v-if="row.identity" class="acct-id-actions">
                <template v-if="pendingUnbind === row.provider">
                  <button type="button" class="acct-danger" :disabled="unbindBusy === row.provider"
                    @click="confirmUnbind(row.provider)">
                    {{ unbindBusy === row.provider ? '解绑中…' : '确认解绑' }}
                  </button>
                  <button type="button" class="acct-link" @click="pendingUnbind = null">取消</button>
                </template>
                <button v-else type="button" class="auth-ghost acct-small"
                  @click="askUnbind(row.provider)">解绑</button>
              </div>
            </li>
          </ul>

          <p v-if="pendingUnbind" class="auth-warn" role="alert">
            解绑后只能通过剩余方式登录；若这是唯一的登录方式，服务端会拒绝。
            确认解绑 {{ providerLabel(pendingUnbind) }}？
          </p>
          <p v-if="identityNotice" class="auth-notice" role="status">{{ identityNotice }}</p>
          <p class="auth-hint">
            登录后不支持新增绑定：GitHub / 微信身份在对应渠道登录时自动建立。
            这里只显示已绑定状态；解绑前请确保还有本站密码或另一种身份。
          </p>
        </TabsContent>
      </TabsRoot>

      <div class="auth-actions">
        <a class="auth-primary" href="/submit">去投稿</a>
        <a class="auth-ghost" href="/catalog">去部件库</a>
        <button type="button" class="auth-ghost" @click="logout">退出登录</button>
      </div>
      <p v-if="serverError" class="auth-err" role="alert">{{ serverError }}</p>
      <p v-if="notice" class="auth-notice" role="status">{{ notice }}</p>
    </div>

    <!-- ── 未登录：登录 / 注册 / 找回密码 ──────────────────────────────── -->
    <div v-else class="auth-card" :aria-busy="accountBusy || resetBusy">
      <h1>{{ mode === 'forgot' ? '找回密码' : mode === 'register' ? '注册账号' : '登录' }}</h1>
      <p class="auth-lead">
        站内账号用于评分、评论与参数纠错；邮箱注册即可，GitHub 登录是可选项。
      </p>

      <!-- 渠道能力由服务端 /auth/providers 决定：未配置时不渲染链接，避免 503 -->
      <div v-if="mode !== 'forgot'" class="auth-provider">
        <a v-if="providers?.github" class="auth-gh" :href="githubHref">
          使用 GitHub 登录 ↗
        </a>
        <button v-else type="button" class="auth-gh" disabled aria-describedby="auth-gh-note">
          使用 GitHub 登录
        </button>
        <p v-if="!providers?.github" id="auth-gh-note" class="auth-hint auth-provider-note">
          <template v-if="!providersChecked">正在读取可用的登录方式…</template>
          <template v-else-if="providers">本服务未配置 GitHub 登录，请使用邮箱账号。</template>
          <template v-else>暂时无法读取登录方式，请使用邮箱账号。</template>
        </p>
        <p v-else class="auth-hint auth-provider-note">
          首次 GitHub 登录会自动建号，签发的令牌与邮箱登录完全等价。
        </p>
        <p v-if="providers?.wechat_mini" class="auth-hint auth-provider-note">
          微信小程序内可直接登录；网页端请用邮箱或 GitHub。
        </p>
      </div>

      <div class="auth-tabs" role="tablist" aria-label="账号操作" @keydown="onTabKey">
        <button v-for="m in MODES" :key="m" :id="`auth-tab-${m}`" ref="tabEls" type="button"
          role="tab" :aria-selected="mode === m" :aria-controls="`auth-panel-${m}`"
          :tabindex="mode === m ? 0 : -1" :class="{ on: mode === m }" @click="selectMode(m)">
          {{ TAB_LABEL[m] }}
        </button>
      </div>

      <div :id="`auth-panel-${mode}`" role="tabpanel" :aria-labelledby="`auth-tab-${mode}`" tabindex="0">
        <!-- 登录 / 注册 / 找回密码：同一个表单，字段随模式显隐 -->
        <form class="auth-form" novalidate :aria-busy="accountBusy" @submit.prevent="onAccountSubmit">
          <template v-if="mode !== 'forgot'">
            <div class="auth-field">
              <label class="auth-label" for="auth-handle">账号</label>
              <input id="auth-handle" v-model="handle" v-bind="handleAttrs"
                autocomplete="username" placeholder="2–24 位 a-z、0-9、-、_"
                :aria-invalid="!!accountErrors.handle"
                :aria-describedby="accountErrors.handle ? 'err-account-handle' : undefined" />
              <p v-if="accountErrors.handle" id="err-account-handle" class="auth-err-inline" role="alert">
                {{ accountErrors.handle }}
              </p>
            </div>

            <div v-if="mode === 'register'" class="auth-field">
              <label class="auth-label" for="auth-display-name">显示名</label>
              <input id="auth-display-name" v-model="displayName" v-bind="displayNameAttrs"
                autocomplete="nickname" placeholder="别人看到的名字"
                :aria-invalid="!!accountErrors.displayName"
                :aria-describedby="accountErrors.displayName ? 'err-account-display-name' : undefined" />
              <p v-if="accountErrors.displayName" id="err-account-display-name" class="auth-err-inline" role="alert">
                {{ accountErrors.displayName }}
              </p>
            </div>

            <div v-if="mode === 'register'" class="auth-field">
              <label class="auth-label" for="auth-email">邮箱（建议填写）</label>
              <input id="auth-email" v-model="email" v-bind="emailAttrs" type="email"
                autocomplete="email" placeholder="用于验证与找回密码"
                :aria-invalid="!!accountErrors.email"
                :aria-describedby="accountErrors.email ? 'err-account-email' : undefined" />
              <p v-if="accountErrors.email" id="err-account-email" class="auth-err-inline" role="alert">
                {{ accountErrors.email }}
              </p>
            </div>

            <div class="auth-field">
              <label class="auth-label" for="auth-password">密码</label>
              <input id="auth-password" v-model="password" v-bind="passwordAttrs" type="password"
                :autocomplete="mode === 'register' ? 'new-password' : 'current-password'"
                placeholder="至少 6 位"
                :aria-invalid="!!accountErrors.password"
                :aria-describedby="accountErrors.password ? 'err-account-password' : undefined" />
              <p v-if="accountErrors.password" id="err-account-password" class="auth-err-inline" role="alert">
                {{ accountErrors.password }}
              </p>
            </div>
          </template>

          <div v-else class="auth-field">
            <label class="auth-label" for="auth-forgot-email">注册邮箱</label>
            <input id="auth-forgot-email" v-model="email" v-bind="emailAttrs" type="email"
              autocomplete="email" placeholder="注册时填写的邮箱"
              :aria-invalid="!!accountErrors.email"
              :aria-describedby="accountErrors.email ? 'err-account-forgot-email' : undefined" />
            <p v-if="accountErrors.email" id="err-account-forgot-email" class="auth-err-inline" role="alert">
              {{ accountErrors.email }}
            </p>
          </div>

          <button type="submit" class="auth-primary" :disabled="accountBusy">
            {{ accountBusy ? '请稍候…' : mode === 'forgot' ? '发送重置邮件' : mode === 'login' ? '登录' : '注册并登录' }}
          </button>
        </form>

        <!-- 找回密码第二步：邮件里的令牌 + 新密码 -->
        <form v-if="mode === 'forgot'" class="auth-form auth-form-sub" novalidate
          :aria-busy="resetBusy" @submit.prevent="onResetSubmit">
          <div class="auth-field">
            <label class="auth-label" for="auth-reset-token">邮件里的重置令牌</label>
            <input id="auth-reset-token" v-model="resetToken" v-bind="resetTokenAttrs"
              autocomplete="one-time-code" placeholder="粘贴邮件中的令牌"
              :aria-invalid="!!resetErrors.token"
              :aria-describedby="resetErrors.token ? 'err-reset-token' : undefined" />
            <p v-if="resetErrors.token" id="err-reset-token" class="auth-err-inline" role="alert">
              {{ resetErrors.token }}
            </p>
          </div>
          <div class="auth-field">
            <label class="auth-label" for="auth-reset-password">新密码</label>
            <input id="auth-reset-password" v-model="newPassword" v-bind="newPasswordAttrs"
              type="password" autocomplete="new-password" placeholder="至少 6 位"
              :aria-invalid="!!resetErrors.password"
              :aria-describedby="resetErrors.password ? 'err-reset-password' : undefined" />
            <p v-if="resetErrors.password" id="err-reset-password" class="auth-err-inline" role="alert">
              {{ resetErrors.password }}
            </p>
          </div>
          <button type="submit" class="auth-ghost" :disabled="resetBusy">
            {{ resetBusy ? '重置中…' : '重置密码' }}
          </button>
        </form>
      </div>

      <p v-if="serverError" class="auth-err" role="alert">{{ serverError }}</p>
      <p v-if="notice" class="auth-notice" role="status">{{ notice }}</p>
      <p class="auth-hint">
        开发环境（EMAIL_MODE=log）的验证/重置令牌在服务端日志里；生产会发到邮箱。
      </p>
    </div>
  </section>
</template>

<style scoped>
.auth-page { max-width: 34rem; margin: 2rem auto 4rem; padding: 0 1rem; }
.auth-card {
  border: 1px solid var(--vp-c-divider); border-radius: 14px;
  background: var(--vp-c-bg-soft); padding: 1.4rem 1.5rem;
}
.auth-card h1 { font-size: 1.35rem; margin: 0 0 0.5rem; }
.auth-lead { margin: 0 0 1rem; font-size: 0.9rem; line-height: 1.8; color: var(--vp-c-text-2); }
.auth-provider { margin: 0 0 1rem; padding-bottom: 1rem; border-bottom: 1px dashed var(--vp-c-divider); }
.auth-gh {
  display: inline-flex; align-items: center; justify-content: center; width: 100%;
  min-height: 44px; box-sizing: border-box;
  border: 1px solid var(--vp-c-divider); border-radius: 9px;
  background: var(--vp-c-bg); color: var(--vp-c-text-1);
  padding: 0.55rem 1rem; font-size: 0.9rem; font-weight: 600; text-decoration: none;
}
.auth-gh:hover:not(:disabled) { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); }
.auth-gh:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px; }
.auth-gh:disabled { opacity: 0.55; cursor: not-allowed; }
.auth-provider-note { margin: 0.45rem 0 0; }
.auth-status { margin: 0 0 0.6rem; font-size: 0.86rem; line-height: 1.7; color: var(--vp-c-text-2); }
.auth-tabs { display: flex; gap: 0.4rem; margin-bottom: 1rem; flex-wrap: wrap; }
.auth-tabs button {
  min-height: 36px;
  border: 1px solid var(--vp-c-divider); background: transparent; color: var(--vp-c-text-2);
  border-radius: 999px; padding: 0.35rem 0.8rem; font-size: 0.82rem; cursor: pointer;
}
.auth-tabs button.on { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); background: var(--vp-c-brand-soft); }
.auth-tabs button:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px; }
.auth-form { display: flex; flex-direction: column; gap: 0.7rem; }
.auth-form-sub { margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px dashed var(--vp-c-divider); }
.auth-field { display: flex; flex-direction: column; gap: 0.3rem; }
.auth-label { font-size: 0.82rem; color: var(--vp-c-text-2); }
.auth-field-hint { margin: 0; }
.auth-form input {
  width: 100%; box-sizing: border-box; padding: 0.55rem 0.65rem;
  border: 1px solid var(--vp-c-divider); border-radius: 8px;
  background: var(--vp-c-bg); color: var(--vp-c-text-1); font: inherit;
}
.auth-form input:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 1px; }
.auth-form input[aria-invalid="true"] { border-color: var(--rw-danger); }
.auth-err-inline { margin: 0; font-size: 0.76rem; line-height: 1.6; color: var(--rw-danger); }
.auth-primary {
  display: inline-flex; align-items: center; justify-content: center; min-height: 44px;
  border: 1px solid var(--vp-c-brand-1); border-radius: 9px;
  background: var(--vp-c-brand-1); color: var(--rw-on-brand);
  padding: 0.55rem 1rem; font-size: 0.9rem; font-weight: 600;
  text-decoration: none; cursor: pointer;
}
.auth-primary:disabled { opacity: 0.55; cursor: default; }
.auth-ghost {
  display: inline-flex; align-items: center; justify-content: center; min-height: 44px;
  border: 1px solid var(--vp-c-divider); border-radius: 9px;
  background: transparent; color: var(--vp-c-text-1); padding: 0.55rem 1rem;
  font-size: 0.9rem; cursor: pointer;
}
.auth-ghost:disabled { opacity: 0.55; cursor: default; }
.auth-actions { display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center; margin-top: 1rem; }
.auth-verify { display: flex; flex-direction: column; gap: 0.6rem; margin: 0.8rem 0; }
.auth-warn { color: var(--rw-accent-1); font-size: 0.86rem; line-height: 1.7; }
.auth-err { color: var(--rw-danger); font-size: 0.86rem; line-height: 1.7; margin: 0.8rem 0 0; }
.auth-notice { color: var(--rw-link); font-size: 0.86rem; line-height: 1.7; margin: 0.8rem 0 0; }
.auth-hint { color: var(--vp-c-text-3); font-size: 0.76rem; line-height: 1.8; margin: 1rem 0 0; }

/* ── 账号中心 ─────────────────────────────────────────────────────────── */
.acct-tabs {
  display: flex; flex-wrap: wrap; gap: 0.2rem;
  border-bottom: 1px solid var(--vp-c-divider); margin: 0.2rem 0 1rem;
}
.acct-tab {
  min-height: 44px; padding: 0.5rem 0.7rem;
  border: 0; border-bottom: 2px solid transparent; background: transparent;
  color: var(--vp-c-text-2); font-size: 0.86rem; font-weight: 600; cursor: pointer;
}
.acct-tab[data-state="active"] { color: var(--vp-c-brand-1); border-bottom-color: var(--vp-c-brand-1); }
.acct-tab:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: -2px; }
.acct-tab-count {
  display: inline-block; margin-left: 0.2rem; padding: 0 0.35rem;
  border-radius: 999px; font-size: 0.68rem; font-weight: 700;
  color: var(--rw-on-brand); background: var(--vp-c-brand-1);
}
.acct-sr {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}
.acct-panel:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 3px; }
.acct-facts { display: grid; gap: 0.55rem; margin: 0 0 1rem; }
.acct-fact { display: grid; grid-template-columns: 5.5rem 1fr; gap: 0.6rem; align-items: baseline; }
.acct-fact dt { color: var(--vp-c-text-3); font-size: 0.78rem; }
.acct-fact dd {
  margin: 0; font-size: 0.9rem; overflow-wrap: anywhere;
  display: flex; flex-wrap: wrap; align-items: center; gap: 0.45rem;
}
.acct-badge {
  display: inline-block; padding: 0.1rem 0.45rem; border-radius: 999px;
  font-size: 0.7rem; font-weight: 600;
  color: var(--rw-link); background: var(--vp-c-brand-soft);
}
.acct-badge-warn {
  color: var(--rw-accent-1); background: transparent;
  border: 1px solid var(--rw-accent-1);
}
.acct-ids { list-style: none; padding: 0; margin: 0.4rem 0 0; display: flex; flex-direction: column; gap: 0.6rem; }
.acct-id {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
  gap: 0.6rem; border: 1px solid var(--vp-c-divider); border-radius: 10px;
  padding: 0.7rem 0.8rem; background: var(--vp-c-bg);
}
.acct-id-main { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
.acct-id-name { font-weight: 600; font-size: 0.9rem; }
.acct-id-meta { color: var(--vp-c-text-3); font-size: 0.76rem; overflow-wrap: anywhere; }
.acct-id-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
.acct-small { min-height: 36px; padding: 0.35rem 0.8rem; font-size: 0.8rem; }
.acct-danger {
  min-height: 44px; border: 1px solid var(--rw-danger); border-radius: 9px;
  background: transparent; color: var(--rw-danger); padding: 0.4rem 0.8rem;
  font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.acct-danger:disabled { opacity: 0.55; cursor: default; }
.acct-link {
  border: 0; background: none; color: var(--vp-c-text-3);
  font-size: 0.8rem; text-decoration: underline; cursor: pointer;
}
.acct-link:focus-visible, .acct-danger:focus-visible {
  outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px;
}
@media (max-width: 480px) {
  .auth-page { margin-top: 1rem; }
  .auth-card { padding: 1.1rem 1rem; }
  .acct-fact { grid-template-columns: 1fr; gap: 0.1rem; }
  .acct-id { align-items: flex-start; }
}
</style>
