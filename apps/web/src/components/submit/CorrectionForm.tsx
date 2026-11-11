import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'

/**
 * 站内纠错表单：一次只改一个字段，写清依据后进审核队列。
 * 目标部件直接用静态目录，避免为了一个下拉框再引一次接口。
 */
type Part = { id: string; vendor: string; model: string; category: string }

const TOKEN_KEY = 'roboselect.token'

const COMMON_FIELDS = [
  { key: 'price_cny', label: '价格（元）' },
  { key: 'url', label: '官方来源 URL' },
  { key: 'last_checked', label: '最近核对日期' },
  { key: 'notes', label: '备注' },
  { key: 'title', label: '标题' },
  { key: 'vendor', label: '厂商' },
  { key: 'model', label: '型号' },
]

const FIELD_KEY_RE = /^(specs\.)?[A-Za-z0-9_]+$/

/** 与互动端同口径：价格是数，其余能转数字就转。 */
function typedValue(field: string, raw: string): string | number {
  const text = raw.trim()
  if (field === 'last_checked' || field === 'url') return text
  if (field === 'price_cny') {
    const n = Number(text)
    return Number.isFinite(n) ? n : text
  }
  return /^-?\d+(\.\d+)?$/.test(text) ? Number(text) : text
}

const inputClass =
  'h-10 w-full rounded-md border border-line bg-surface px-2.5 text-sm text-ink placeholder:text-ink-3 focus:border-brand focus:outline-none'
const labelClass = 'mb-1 block text-xs font-medium text-ink-2'

export default function CorrectionForm() {
  const [parts, setParts] = useState<Part[] | null>(null)
  const [signedIn, setSignedIn] = useState<boolean | null>(null)
  const [partId, setPartId] = useState('')
  const [field, setField] = useState('price_cny')
  const [customField, setCustomField] = useState('')
  const [value, setValue] = useState('')
  const [note, setNote] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState<number | null>(null)

  useEffect(() => {
    try {
      setSignedIn(Boolean(localStorage.getItem(TOKEN_KEY)))
    } catch {
      setSignedIn(false)
    }
    fetch(`${import.meta.env.BASE_URL}catalog.json`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: { parts?: Part[] }) => setParts(data.parts || []))
      .catch(() => setParts([]))
  }, [])

  const options = useMemo(
    () => [...(parts || [])].sort((a, b) =>
      `${a.vendor}${a.model}`.localeCompare(`${b.vendor}${b.model}`, 'zh-CN')),
    [parts],
  )

  const key = field === '__custom__' ? customField.trim() : field

  const submit = async () => {
    if (busy) return
    setError('')
    if (!partId) return setError('先选一个部件')
    if (!FIELD_KEY_RE.test(key)) return setError('字段名只能包含字母、数字、下划线，可加 specs. 前缀')
    if (!value.trim()) return setError('写上新值')
    if (note.trim().length < 2) return setError('写清依据：至少 2 个字的说明或手册页码')

    setBusy(true)
    try {
      const submission = await api.createSubmission({
        kind: 'part_patch',
        target_id: partId,
        payload: { [key]: typedValue(key, value) },
        evidence: {
          note: note.trim(),
          ...(sourceUrl.trim() ? { source_url: sourceUrl.trim() } : {}),
        },
      })
      setDone(submission.id)
      setValue('')
      setNote('')
      setSourceUrl('')
    } catch (err) {
      const status = (err as { status?: number })?.status
      setError(status === 401 ? '登录已失效，请重新登录后再提交。' : (err as Error)?.message || '提交失败，稍后重试')
    } finally {
      setBusy(false)
    }
  }

  if (signedIn === false) {
    return (
      <div className="rounded-lg border border-line bg-surface-2 p-4">
        <p className="m-0 text-sm leading-6 text-ink-2">登录后才能提交参数纠错，提案会进入站务审核队列。</p>
        <a
          href={`${import.meta.env.BASE_URL}account.html`}
          className="mt-3 inline-flex h-11 items-center rounded-md bg-brand px-4 text-sm font-semibold text-brand-fg hover:bg-brand-hover"
        >
          去登录
        </a>
      </div>
    )
  }

  if (done !== null) {
    return (
      <div className="rounded-lg border border-success/35 bg-success-soft p-4" role="status" aria-live="polite">
        <p className="m-0 text-sm font-semibold text-success">提案 #{done} 已进入审核队列</p>
        <p className="m-0 mt-1.5 text-sm leading-6 text-ink-2">
          审核通过不等于页面已更新；数据在下一个 <span className="mono">data-v*</span> 发布后生效，结果会以站内通知告知。
        </p>
        <button
          type="button"
          onClick={() => setDone(null)}
          className="mt-3 inline-flex h-11 items-center rounded-md border border-line bg-surface px-4 text-sm font-medium text-ink hover:border-line-strong"
        >
          再提一条
        </button>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className={labelClass} htmlFor="fix-part">部件</label>
          <select
            id="fix-part"
            value={partId}
            onChange={e => setPartId(e.target.value)}
            className={inputClass}
          >
            <option value="">{parts === null ? '正在加载目录…' : '选择部件…'}</option>
            {options.map(p => (
              <option key={p.id} value={p.id}>{p.vendor} · {p.model}</option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelClass} htmlFor="fix-field">字段</label>
          <select
            id="fix-field"
            value={field}
            onChange={e => setField(e.target.value)}
            className={inputClass}
          >
            {COMMON_FIELDS.map(item => (
              <option key={item.key} value={item.key}>{item.label}</option>
            ))}
            <option value="__custom__">其他字段…</option>
          </select>
        </div>

        {field === '__custom__' && (
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="fix-custom-field">字段 key</label>
            <input
              id="fix-custom-field"
              value={customField}
              onChange={e => setCustomField(e.target.value)}
              placeholder="例：specs.tau_peak_Nm"
              className={inputClass}
            />
          </div>
        )}

        <div>
          <label className={labelClass} htmlFor="fix-value">正确值</label>
          <input
            id="fix-value"
            value={value}
            onChange={e => setValue(e.target.value)}
            placeholder="例：3288"
            className={inputClass}
          />
        </div>

        <div>
          <label className={labelClass} htmlFor="fix-source">依据链接（可选）</label>
          <input
            id="fix-source"
            value={sourceUrl}
            onChange={e => setSourceUrl(e.target.value)}
            placeholder="https://… 厂商手册或报价页"
            className={inputClass}
          />
        </div>

        <div className="sm:col-span-2">
          <label className={labelClass} htmlFor="fix-note">依据说明（必填）</label>
          <input
            id="fix-note"
            value={note}
            onChange={e => setNote(e.target.value)}
            maxLength={2000}
            placeholder="例：手册第 12 页标称峰值扭矩 6 N·m"
            className={inputClass}
          />
        </div>
      </div>

      {error && <p className="m-0 mt-3 text-sm leading-5 text-danger" role="alert">{error}</p>}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={submit}
          disabled={busy || signedIn === null}
          className="inline-flex h-11 items-center rounded-md bg-brand px-4 text-sm font-semibold text-brand-fg hover:bg-brand-hover disabled:opacity-50"
        >
          {busy ? '提交中…' : '提交纠错'}
        </button>
        <span className="text-xs leading-5 text-ink-3">
          一次改一个字段；通过后由数据流水线发布，页面不会立刻变化。
        </span>
      </div>
    </div>
  )
}
