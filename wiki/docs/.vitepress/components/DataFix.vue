<script setup lang="ts">
/**
 * 部件页底部的「参数纠错」块。
 *
 * 表单校验交给 VeeValidate 4 + Zod：字段必填、值必填、依据≥5 字、来源必须是
 * http(s) 链接 —— 与后端 SubmissionIn 的 evidence 约定一致。这样服务端 422
 * 变成前端当场能看懂的提示，而不是一次白跑的请求。
 *
 * 登录表单**不在这里再写一份**：AuthPanel 已经有一份（VeeValidate + Zod）。
 * 之前两边各写一套，注册规则、找回密码流程分头演化，结果就是「这边能注册、
 * 那边说参数错」。这里只放一个带 ?redirect= 的登录链接，登录态本身仍从
 * lib/auth 的同一个 token 读。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, withBase } from 'vitepress'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { findShareEntry, type ShareEntry } from '../lib/share'
import { ApiError, apiAvailable, apiErrorMessage, apiFetch, isMirror, MIRROR_READONLY_NOTE, PRIMARY_SITE } from '../lib/api'
import { clearToken, getToken } from '../lib/auth'

type Me = { handle: string; display_name: string; email_verified?: boolean }
type Preview = { field: string; old_value: unknown; new_value: unknown }
type Review = { decision: string; reason_code: string; note: string }
type Mine = {
  id: number
  status: string
  payload: Record<string, unknown>
  evidence?: { note?: string; source_url?: string; preview?: Preview[] }
  created_at: string
  reviews?: Review[]
}

const route = useRoute()
const entry = ref<ShareEntry | null>(null)
const detail = ref<{ params?: { key: string; label: string; value: string }[] } | null>(null)
const me = ref<Me | null>(null)
const serverError = ref('')
const notice = ref('')
const verifySent = ref(false)
const done = ref<number | null>(null)
const mine = ref<Mine[]>([])
const apiReady = ref<boolean | null>(null)

const STATUS_LABEL: Record<string, string> = {
  pending: '待审核', accepted: '已通过', rejected: '已驳回',
  pr_open: 'PR 中', merged: '已合并', released: '已发布',
}

/** 字段 key → 人读的标签；specs.* 去掉前缀后原样显示（口径名本身是英文） */
const FIELD_LABEL: Record<string, string> = {
  price_cny: '价格',
  url: '官方来源 URL',
  source_tier: '来源等级',
  last_checked: '最近核对日期',
  notes: '备注',
}

const REASON_LABEL: Record<string, string> = {
  ok: '符合目录口径',
  insufficient_evidence: '依据不足',
  wrong_value: '数值 / 口径不对',
  out_of_scope: '不属于可改字段',
  duplicate: '重复提案',
  other: '其他',
}

function fieldLabel(key: string): string {
  return FIELD_LABEL[key] || (key.startsWith('specs.') ? key.slice(6) : key)
}

function fmtValue(v: unknown): string {
  if (v === null || v === undefined || v === '') return '—'
  if (Array.isArray(v)) return v.map(x => String(x)).join('、') || '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

/** 服务端按当前目录生成的 old → new；客户端从来不能自己传 preview */
function previewOf(s: Mine, key: string): Preview | undefined {
  return (s.evidence?.preview || []).find(p => p.field === key)
}

function latestReview(s: Mine): Review | undefined {
  return s.reviews && s.reviews.length ? s.reviews[s.reviews.length - 1] : undefined
}

function reviewText(r: Review): string {
  const decision = r.decision === 'rejected' ? '已驳回' : '已通过'
  const reason = REASON_LABEL[r.reason_code] || r.reason_code || ''
  return [decision, reason && `理由：${reason}`, r.note && `说明：${r.note}`]
    .filter(Boolean).join(' · ')
}

function reviewTextOf(s: Mine): string {
  const r = latestReview(s)
  return r ? reviewText(r) : ''
}

function statusClass(status: string): string {
  if (status === 'rejected') return 'is-bad'
  if (['accepted', 'merged', 'released'].includes(status)) return 'is-ok'
  return 'is-wait'
}

const loginHref = computed(() => `/login?redirect=${encodeURIComponent(route.path)}`)

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '')

/**
 * 只有部件页（/parts/<category>/<slug>.html）才有 Part。
 * 材质/工艺页虽然也有 share JSON，但没有 part id：在这里渲染会允许提交
 * `part_patch`，服务端必然 404。所以材料页整块不初始化、不渲染。
 */
function isPartPage(pathname: string): boolean {
  const p = BASE && pathname.startsWith(BASE) ? pathname.slice(BASE.length) : pathname
  return p.startsWith('/parts/')
}

const token = () => getToken()

/** detail 解析 + 401/429/断网文案统一在 lib/api，组件不再自己拼 base */
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  return apiFetch<T>(path, init)
}

async function loadMine() {
  if (!token()) return
  mine.value = await req<Mine[]>('/submissions/mine?limit=10').catch(() => [])
}

let pageSeq = 0

async function loadPage() {
  const seq = ++pageSeq
  resetFix()
  entry.value = null
  detail.value = null
  mine.value = []
  done.value = null
  serverError.value = ''
  notice.value = ''
  verifySent.value = false

  // 材料/工艺页没有 Part：不渲染纠错块，也不发 /auth/me 与 /submissions。
  if (!isPartPage(window.location.pathname)) return

  const next = await findShareEntry(window.location.pathname)
  if (seq !== pageSeq) return
  entry.value = next
  if (!next) return
  apiReady.value = await apiAvailable()
  if (seq !== pageSeq || !apiReady.value) return
  detail.value = await fetch(withBase(next.json)).then(r => r.ok ? r.json() : null).catch(() => null)
  if (seq !== pageSeq) return
  if (token()) {
    me.value = await req<Me>('/auth/me').catch((e) => {
      // 只有 401 才清 token；断网/CORS 不要把用户踢下线
      if (e instanceof ApiError && e.status === 401) clearToken()
      return null
    })
    if (seq === pageSeq) await loadMine()
  }
}

onMounted(() => { void loadPage() })

// doc-after 插槽在客户端路由切换时会复用组件；必须重新解析当前页，
// 否则纠错提案会带着上一页的 part id 提交。
watch(() => route.path, () => { void loadPage() })

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

/** 值按字段转类型：价格必须是数，来源等级保持字符串，其他能转数字就转 */
function typedValue(field: string, raw: string): string | number {
  if (field === 'source_tier') return raw
  if (field === 'price_cny') {
    const n = Number(raw)
    return Number.isFinite(n) ? n : raw
  }
  const s = raw.trim()
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s)
  return s
}

/* ── 纠错表单 ──────────────────────────────────────────────────────────── */
const fixCtx = useForm({
  validationSchema: toTypedSchema(z.object({
    field: z.string().min(1, '请选择字段'),
    customField: z.string().trim().max(120, '参数名过长'),
    value: z.string().trim().min(1, '请填写正确的值').max(500, '值最多 500 字'),
    note: z.string().trim().min(5, '请写清依据（至少 5 个字）').max(2000, '依据最多 2000 字'),
    sourceUrl: z.string().trim().max(500, '链接过长')
      .regex(/^https?:\/\/\S+$/i, '来源链接需要以 http:// 或 https:// 开头'),
  }).superRefine((v, ctx) => {
    if (v.field === '__custom__' && !v.customField) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['customField'], message: '请填写参数名（如 specs.voltage）' })
    }
    // 值域与服务端同口径：UI 先拦一次，免得提交后才看到 422。
    const raw = (v.value || '').trim()
    if (v.field === 'price_cny') {
      if (!/^\d+(\.\d+)?$/.test(raw)) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['value'], message: '价格必须是非负数字（不要带 ¥ / 逗号）' })
      } else if (Number(raw) > 10_000_000) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['value'], message: '价格超出合理范围（≤ 1000 万）' })
      }
    }
    if (v.field === 'last_checked' && !/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['value'], message: '日期格式为 YYYY-MM-DD' })
    }
    if (v.field === 'url' && !/^https?:\/\/\S+$/i.test(raw)) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['value'], message: '官方来源需要以 http:// 或 https:// 开头' })
    }
  })),
  initialValues: { field: 'price_cny', customField: '', value: '', note: '', sourceUrl: '' },
})
const {
  errors: fixErrors,
  isSubmitting: fixBusy,
  handleSubmit: onFixSubmitRaw,
  defineField: fixField,
  resetForm: resetFix,
} = fixCtx
const [field, fieldAttrs] = fixField('field')
const [customField, customFieldAttrs] = fixField('customField')
const [value, valueAttrs] = fixField('value')
const [note, noteAttrs] = fixField('note')
const [sourceUrl, sourceUrlAttrs] = fixField('sourceUrl')

const targetKey = computed(() => field.value === '__custom__'
  ? (customField.value || '').trim()
  : field.value)

const onFixSubmit = onFixSubmitRaw(async values => {
  serverError.value = ''
  notice.value = ''
  done.value = null
  try {
    const key = values.field === '__custom__' ? values.customField : values.field
    const s = await req<{ id: number }>('/submissions', {
      method: 'POST',
      body: JSON.stringify({
        kind: 'part_patch',
        target_id: entry.value!.id,
        payload: { [key]: typedValue(values.field, values.value) },
        evidence: { note: values.note, source_url: values.sourceUrl },
      }),
    })
    done.value = s.id
    // 保留已填内容（同一份手册常要连着改几个值），只清错误/触碰态；
    // 若清空字段，VeeValidate 会立刻把空值重新标成必填错误。
    resetFix({ values: {
      field: values.field, customField: values.customField,
      value: values.value, note: values.note, sourceUrl: values.sourceUrl,
    } })
    await loadMine()
  } catch (e: any) {
    serverError.value = apiErrorMessage(e, '请求失败，请稍后再试')
  }
})

/* ── 邮箱验证（登录后可补验证） ────────────────────────────────────────── */
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
  serverError.value = ''
  notice.value = ''
  verifySent.value = false
  try {
    await req('/auth/email/verify/request', { method: 'POST' })
    verifySent.value = true
    notice.value = '验证邮件已发送；开发环境可在服务端日志看到令牌'
  } catch (e: any) {
    serverError.value = apiErrorMessage(e, '请求失败，请稍后再试')
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

function logout() {
  clearToken()
  me.value = null
  mine.value = []
  verifySent.value = false
  verifyCtx.resetForm()
  resetFix()
}
</script>

<template>
  <section v-if="entry" id="纠错" class="rw-fix" aria-label="提交参数纠错">
    <div class="rw-fix-head">
      <b>发现参数有问题？</b>
      <span v-if="me">{{ me.display_name }}（{{ me.handle }}）· <a href="#" @click.prevent="logout">退出</a></span>
    </div>

    <!-- 纯静态镜像（GitHub Pages）：交互入口整块不渲染，包括「提交纠错」按钮 ——
         探不到后端就不要给一个点了必然失败的按钮。只留主站与 GitHub 两条出口。 -->
    <template v-if="apiReady === false">
      <p class="rw-fix-text">
        {{ isMirror() ? MIRROR_READONLY_NOTE : '主站服务暂时不可达，当前显示构建快照（只读）' }} ·
        <a :href="PRIMARY_SITE" target="_blank" rel="noopener">robowiki.org.cn</a>
      </p>
      <p class="rw-fix-hint">
        没有主站账号也可以到 GitHub 用表单纠错，维护者会转成提案。
      </p>
      <a class="rw-fix-alt" :href="issueUrl" target="_blank" rel="noopener">去 GitHub 提交纠错 ↗</a>
    </template>

    <!-- 探测中什么都不渲染：短暂的空白，好过先给表单再收走 -->
    <template v-else-if="apiReady === true">
      <template v-if="!me">
        <p class="rw-fix-text">
          登录后提交纠错，站务审核通过会转成 PR；合并并发布数据版本后页面才更新。
          不需要 GitHub 账号。
        </p>
        <a class="rw-fix-alt" :href="loginHref">登录 / 注册 ↗</a>
        <p class="rw-fix-hint">
          只想用 GitHub？<a :href="issueUrl" target="_blank" rel="noopener">也可以开一条纠错 issue ↗</a>
        </p>
      </template>

      <template v-else>
        <div v-if="!me.email_verified" class="rw-fix-verify">
          <span>邮箱未验证（找回密码需要它）。</span>
          <button type="button" @click="requestVerify">发送验证邮件</button>
          <form v-if="verifySent" class="rw-fix-verify-form" novalidate
            :aria-busy="verifyBusy" @submit.prevent="onVerifySubmit">
            <label class="rw-fix-label" for="fix-verify-token">验证令牌</label>
            <input id="fix-verify-token" v-model="verifyToken" v-bind="verifyTokenAttrs"
              autocomplete="one-time-code" placeholder="邮件里的验证令牌"
              :aria-invalid="!!verifyErrors.token"
              :aria-describedby="verifyErrors.token ? 'err-fix-verify-token' : undefined" />
            <button type="submit" :disabled="verifyBusy">{{ verifyBusy ? '验证中…' : '验证' }}</button>
            <p v-if="verifyErrors.token" id="err-fix-verify-token" class="rw-fix-err-inline" role="alert">
              {{ verifyErrors.token }}
            </p>
          </form>
        </div>

        <p class="rw-fix-text">
          只提交你核对过的字段与来源；审核通过不等于生效，合并并发布 <code>data-v*</code> 后才更新。
        </p>

        <form class="rw-fix-form" novalidate :aria-busy="fixBusy" @submit.prevent="onFixSubmit">
          <div class="rw-fix-grid">
            <div class="rw-fix-field">
              <label class="rw-fix-label" for="fix-field">字段</label>
              <select id="fix-field" v-model="field" v-bind="fieldAttrs"
                :aria-invalid="!!fixErrors.field"
                :aria-describedby="fixErrors.field ? 'err-fix-field' : undefined">
                <option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
              <p v-if="fixErrors.field" id="err-fix-field" class="rw-fix-err-inline" role="alert">
                {{ fixErrors.field }}
              </p>
            </div>

            <div v-if="field === '__custom__'" class="rw-fix-field">
              <label class="rw-fix-label" for="fix-custom">参数名</label>
              <input id="fix-custom" v-model="customField" v-bind="customFieldAttrs"
                placeholder="specs.xxx"
                :aria-invalid="!!fixErrors.customField"
                :aria-describedby="fixErrors.customField ? 'err-fix-custom' : undefined" />
              <p v-if="fixErrors.customField" id="err-fix-custom" class="rw-fix-err-inline" role="alert">
                {{ fixErrors.customField }}
              </p>
            </div>

            <div class="rw-fix-field">
              <label class="rw-fix-label" for="fix-value">正确的值</label>
              <select v-if="field === 'source_tier'" id="fix-value" v-model="value" v-bind="valueAttrs"
                :aria-invalid="!!fixErrors.value"
                :aria-describedby="fixErrors.value ? 'err-fix-value' : undefined">
                <option value="A">A（逐项核对官方手册）</option>
                <option value="B">B（公开网页来源）</option>
                <option value="C">C（社区整理 / 待核实）</option>
              </select>
              <input v-else id="fix-value" v-model="value" v-bind="valueAttrs"
                placeholder="数值或文本"
                :aria-invalid="!!fixErrors.value"
                :aria-describedby="fixErrors.value ? 'err-fix-value' : undefined" />
              <p v-if="fixErrors.value" id="err-fix-value" class="rw-fix-err-inline" role="alert">
                {{ fixErrors.value }}
              </p>
            </div>
          </div>

          <div class="rw-fix-field">
            <label class="rw-fix-label" for="fix-note">纠错依据（至少 5 字）</label>
            <textarea id="fix-note" v-model="note" v-bind="noteAttrs" rows="2"
              placeholder="依据：哪份手册的哪一页 / 哪封厂商邮件 / 实测条件"
              :aria-invalid="!!fixErrors.note"
              :aria-describedby="fixErrors.note ? 'err-fix-note' : undefined" />
            <p v-if="fixErrors.note" id="err-fix-note" class="rw-fix-err-inline" role="alert">
              {{ fixErrors.note }}
            </p>
          </div>

          <div class="rw-fix-field">
            <label class="rw-fix-label" for="fix-source">来源链接（http / https）</label>
            <input id="fix-source" v-model="sourceUrl" v-bind="sourceUrlAttrs" type="url"
              inputmode="url" placeholder="https://厂商手册或产品页"
              :aria-invalid="!!fixErrors.sourceUrl"
              :aria-describedby="fixErrors.sourceUrl ? 'err-fix-source' : undefined" />
            <p v-if="fixErrors.sourceUrl" id="err-fix-source" class="rw-fix-err-inline" role="alert">
              {{ fixErrors.sourceUrl }}
            </p>
          </div>

          <div class="rw-fix-actions">
            <button type="submit" :disabled="fixBusy">{{ fixBusy ? '提交中…' : '提交纠错' }}</button>
            <span class="rw-fix-target">{{ targetKey || '（未选字段）' }}</span>
            <span v-if="done" class="ok" role="status" aria-live="polite">
              已提交提案 #{{ done }}，等待审核
            </span>
          </div>
        </form>
      </template>

      <p v-if="serverError" class="err" role="alert">{{ serverError }}</p>
      <p v-if="notice" class="notice" role="status">{{ notice }}</p>

      <section v-if="mine.length" class="rw-fix-mine" aria-labelledby="fix-mine-title">
        <h3 id="fix-mine-title" class="rw-fix-mine-title">我的提案（最近 {{ mine.length }} 条）</h3>
        <ul class="rw-fix-mine-list">
          <li v-for="s in mine" :key="s.id" class="rw-fix-mine-item"
            :aria-label="`提案 #${s.id}，${STATUS_LABEL[s.status] || s.status}`">
            <div class="rw-fix-mine-row">
              <span class="rw-fix-mine-id">#{{ s.id }}</span>
              <span class="rw-fix-chip" :class="statusClass(s.status)">
                {{ STATUS_LABEL[s.status] || s.status }}
              </span>
              <span class="rw-fix-mine-date">{{ s.created_at.slice(0, 10) }}</span>
            </div>

            <dl class="rw-fix-mine-fields">
              <template v-for="(v, k) in s.payload" :key="k">
                <dt>{{ fieldLabel(String(k)) }}</dt>
                <dd>
                  <template v-if="previewOf(s, String(k))">
                    <span class="rw-fix-old">{{ fmtValue(previewOf(s, String(k))?.old_value) }}</span>
                    <span class="rw-fix-arrow" aria-hidden="true">→</span>
                    <span class="rw-fix-new">{{ fmtValue(previewOf(s, String(k))?.new_value) }}</span>
                  </template>
                  <template v-else>{{ fmtValue(v) }}</template>
                  <code class="rw-fix-key">{{ k }}</code>
                </dd>
              </template>
            </dl>

            <div v-if="s.evidence?.note" class="rw-fix-mine-meta">
              <span class="rw-fix-meta-label">依据</span>{{ s.evidence.note }}
            </div>
            <div v-if="s.evidence?.source_url" class="rw-fix-mine-meta">
              <span class="rw-fix-meta-label">来源</span>
              <a :href="s.evidence.source_url" target="_blank" rel="noopener noreferrer"
                :aria-label="`提案 #${s.id} 的来源链接`">{{ s.evidence.source_url }} ↗</a>
            </div>

            <p v-if="latestReview(s)" class="rw-fix-review">
              <span class="rw-fix-meta-label">审核</span>{{ reviewTextOf(s) }}
            </p>
          </li>
        </ul>
      </section>
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
.rw-fix-form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.rw-fix-actions button,
.rw-fix-verify button,
.rw-fix-verify-form button {
  border: 1px solid var(--vp-c-brand-1);
  background: var(--vp-c-brand-1);
  color: #fff;
  padding: 0.4rem 0.85rem;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  min-height: 36px;
}
.rw-fix-actions button:disabled,
.rw-fix-verify-form button:disabled { opacity: 0.55; cursor: default; }
.rw-fix-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}
.rw-fix-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.rw-fix-label {
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
}
.rw-fix input:focus-visible,
.rw-fix select:focus-visible,
.rw-fix textarea:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 1px;
}
.rw-fix [aria-invalid="true"] { border-color: var(--vp-c-danger-1); }
.rw-fix-err-inline {
  margin: 0;
  font-size: 0.74rem;
  line-height: 1.6;
  color: var(--vp-c-danger-1);
}
.rw-fix-actions {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  flex-wrap: wrap;
}
.rw-fix-target {
  font-size: 0.74rem;
  color: var(--vp-c-text-3);
  font-variant-numeric: tabular-nums;
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
  border-color: var(--vp-c-warning-1);
  background: transparent;
  color: var(--vp-c-warning-1);
}
.rw-fix-verify-form {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  flex-basis: 100%;
}
.rw-fix-verify-form .rw-fix-label { flex-basis: 100%; }
.rw-fix-verify-form input { max-width: 260px; }
.rw-fix-alt {
  display: inline-block;
  margin-top: 0.2rem;
  font-size: 0.88rem;
  color: var(--vp-c-brand-1);
  font-weight: 600;
}
.rw-fix-mine {
  margin-top: 0.9rem;
  border-top: 1px solid var(--vp-c-divider);
  padding-top: 0.6rem;
  font-size: 0.8rem;
  color: var(--vp-c-text-2);
}
.rw-fix-mine-title {
  margin: 0 0 0.4rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--vp-c-text-2);
}
.rw-fix-mine-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.rw-fix-mine-item {
  padding: 0.5rem 0.6rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  min-width: 0;
}
.rw-fix-mine-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.2rem 0.5rem;
}
.rw-fix-mine-id {
  font-weight: 600;
  color: var(--vp-c-text-1);
  font-variant-numeric: tabular-nums;
}
.rw-fix-mine-date {
  margin-left: auto;
  color: var(--vp-c-text-3);
  font-size: 0.74rem;
  font-variant-numeric: tabular-nums;
}
.rw-fix-chip {
  padding: 0 0.4rem;
  border-radius: 999px;
  border: 1px solid currentColor;
  font-size: 0.72rem;
  line-height: 1.7;
}
.rw-fix-chip.is-ok { color: var(--vp-c-success-1); }
.rw-fix-chip.is-wait { color: var(--vp-c-warning-1); }
.rw-fix-chip.is-bad { color: var(--vp-c-danger-1); }
.rw-fix-mine-fields {
  margin: 0.35rem 0 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.15rem 0.6rem;
  font-size: 0.78rem;
}
.rw-fix-mine-fields dt {
  color: var(--vp-c-text-3);
  white-space: nowrap;
}
.rw-fix-mine-fields dd {
  margin: 0;
  min-width: 0;
  color: var(--vp-c-text-1);
  overflow-wrap: anywhere;
}
.rw-fix-old { color: var(--vp-c-text-3); text-decoration: line-through; }
.rw-fix-arrow { margin: 0 0.3rem; color: var(--vp-c-text-3); }
.rw-fix-new { color: var(--vp-c-brand-1); font-weight: 600; }
.rw-fix-key {
  margin-left: 0.4rem;
  font-size: 0.68rem;
  color: var(--vp-c-text-3);
  background: transparent;
  border: 0;
  padding: 0;
}
.rw-fix-mine-meta {
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
  overflow-wrap: anywhere;
}
.rw-fix-mine-meta a { color: var(--vp-c-brand-1); }
.rw-fix-meta-label {
  display: inline-block;
  margin-right: 0.35rem;
  padding: 0 0.3rem;
  border-radius: 4px;
  background: var(--vp-c-default-soft);
  color: var(--vp-c-text-3);
  font-size: 0.68rem;
}
.rw-fix-review {
  margin: 0.3rem 0 0;
  color: var(--vp-c-text-2);
  font-size: 0.75rem;
  overflow-wrap: anywhere;
}
@media (max-width: 640px) {
  .rw-fix-grid { grid-template-columns: 1fr; }
}
</style>
