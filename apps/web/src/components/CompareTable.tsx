import { useEffect, useMemo, useState } from 'react'
import { formatSpecValue, specLabel } from '@robowiki/content'
import { bestOfferPrice, formatPrice } from '@/lib/utils'

type Part = {
  id: string
  slug: string
  category: string
  vendor: string
  model: string
  price?: number | null
  offers?: Array<Record<string, unknown>>
  specs?: Record<string, unknown>
}

type Catalog = { parts: Part[] }

const MAX = 4
/** 对比优先展示的字段：先比决策相关的，再补其余。 */
const PRIORITY = [
  'tau_peak_Nm',
  'tau_rated_Nm',
  'gear',
  'speed_rated_rpm',
  'voltage_V',
  'mass_kg',
  'comm',
  'encoder',
  'power_w',
  'od_mm',
  'l_mm',
  'dof',
  'payload_kg',
  'soc',
  'npu_tops',
  'ram_gb',
]

const VALUE_KEYS = new Set(PRIORITY)

const isScalar = (v: unknown) => ['string', 'number', 'boolean'].includes(typeof v)
const show = (v: unknown) => formatSpecValue(v)
const isUrl = (v: string) => /^https?:\/\//i.test(v.trim())
const safeHref = (url: string) => url.trim().replace(/[^\x21-\x7E]+/g, chunk => encodeURIComponent(chunk))

/** 链接列只展示短名；完整 URL 放 title，避免一长串地址把表格撑开。 */
function shortUrl(url: string): string {
  try {
    const parsed = new URL(url)
    const host = parsed.hostname.replace(/^www\./, '')
    const rawPath = parsed.pathname.replace(/^\/|\/$/g, '')
    let path = rawPath
    try { path = decodeURIComponent(rawPath) } catch { /* 保留原编码 */ }
    if (/(^|\.)(github|gitee)\.com$/.test(host)) return path || host
    return `${host}${path ? `/${path}` : ''}`
  } catch {
    return url
  }
}

function cellContent(key: string, value: string) {
  const items = value.split('、').filter(Boolean)
  if (!items.length || !items.every(isUrl)) return value
  return (
    <span className="inline-flex max-w-full flex-wrap justify-end gap-x-2 gap-y-0.5">
      {items.map(item => (
        <a
          key={item}
          href={safeHref(item)}
          target="_blank"
          rel="noopener"
          title={item}
          className="max-w-[220px] truncate text-brand hover:underline"
        >
          {key === 'doc_pdf' ? '查看 PDF' : shortUrl(item)} ↗
        </a>
      ))}
    </span>
  )
}

/** 把 specs 里的标量摊平；对象与数组不进对比表（避免 [object Object] 与噪声）。 */
function flatten(specs: Record<string, unknown> = {}): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(specs)) {
    if (isScalar(v)) out[k] = show(v)
    else if (Array.isArray(v) && v.length && v.every(isScalar)) out[k] = show(v)
    else if (v && typeof v === 'object') {
      for (const [sk, sv] of Object.entries(v as Record<string, unknown>)) {
        if (isScalar(sv)) out[`${k}.${sk}`] = show(sv)
      }
    }
  }
  return out
}

type Labels = Record<string, { label: string; unit?: string }>

export default function CompareTable({ labels = {} }: { labels?: Labels }) {
  const [catalog, setCatalog] = useState<Part[] | null>(null)
  const [ids, setIds] = useState<string[]>(['', ''])
  const [diffOnly, setDiffOnly] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fromUrl = new URLSearchParams(window.location.search).get('ids') || ''
    let initial = fromUrl.split(',').filter(Boolean).slice(0, MAX)
    // 没有显式 ids 时，沿用部件库勾选的「对比托盘」
    if (!initial.length) {
      try {
        const raw = localStorage.getItem('rw-compare')
        const list = raw ? (JSON.parse(raw) as unknown) : []
        if (Array.isArray(list)) initial = list.filter((v): v is string => typeof v === 'string').slice(0, MAX)
      } catch { /* 忽略 */ }
    }
    if (initial.length >= 1) {
      setIds([...initial, ...Array(Math.max(0, 2 - initial.length)).fill('')].slice(0, MAX))
    }

    fetch(`${import.meta.env.BASE_URL}catalog.json`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: Catalog) => setCatalog(data.parts || []))
      .catch(() => setError('目录数据加载失败，稍后刷新重试。'))
  }, [])

  const byId = useMemo(() => {
    const map = new Map<string, Part>()
    for (const p of catalog || []) map.set(p.id, p)
    return map
  }, [catalog])

  const picked = ids.map(id => (id ? byId.get(id) : undefined)).filter(Boolean) as Part[]

  useEffect(() => {
    if (typeof window === 'undefined') return
    const url = new URL(window.location.href)
    const clean = ids.filter(Boolean)
    if (clean.length) url.searchParams.set('ids', clean.join(','))
    else url.searchParams.delete('ids')
    window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`)
  }, [ids])

  const rows = useMemo(() => {
    const flattened = picked.map(p => flatten(p.specs))
    const keys = new Set<string>()
    for (const f of flattened) for (const k of Object.keys(f)) if (!VALUE_KEYS.has(k)) keys.add(k)
    const ordered = [
      ...PRIORITY.filter(k => flattened.some(f => k in f)),
      ...[...keys].sort(),
    ]
    return ordered.map(key => {
      const values = flattened.map(f => f[key] ?? '—')
      const differs = new Set(values).size > 1
      return { key, values, differs }
    })
  }, [picked])

  const visibleRows = diffOnly ? rows.filter(r => r.differs) : rows

  const setSlot = (index: number, value: string) => {
    setIds(prev => {
      const next = [...prev]
      next[index] = value
      return next
    })
  }

  const addSlot = () => setIds(prev => (prev.length < MAX ? [...prev, ''] : prev))
  const removeSlot = (index: number) => setIds(prev => prev.filter((_, i) => i !== index))

  const options = useMemo(
    () => [...(catalog || [])].sort((a, b) => `${a.vendor}${a.model}`.localeCompare(`${b.vendor}${b.model}`, 'zh-CN')),
    [catalog],
  )

  if (error) {
    return <p className="card border-dashed p-6 text-sm text-ink-3">{error}</p>
  }

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <div className="flex flex-wrap items-end gap-3">
          {ids.map((id, index) => (
            <div key={index} className="min-w-[220px] flex-1">
              <label className="mb-1 block text-[11px] text-ink-3" htmlFor={`cmp-${index}`}>
                第 {index + 1} 个
              </label>
              <div className="flex items-center gap-1">
                <select
                  id={`cmp-${index}`}
                  value={id}
                  onChange={e => setSlot(index, e.target.value)}
                  className="h-9 w-full rounded-md border border-line bg-surface px-2 text-[13px] text-ink focus:border-brand focus:outline-none"
                >
                  <option value="">选择部件…</option>
                  {options.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.vendor} · {p.model}
                    </option>
                  ))}
                </select>
                {ids.length > 2 && (
                  <button
                    type="button"
                    onClick={() => removeSlot(index)}
                    className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-line text-ink-3 hover:text-danger"
                    aria-label={`移除第 ${index + 1} 个`}
                  >
                    ×
                  </button>
                )}
              </div>
            </div>
          ))}
          {ids.length < MAX && (
            <button
              type="button"
              onClick={addSlot}
              className="inline-flex h-9 items-center rounded-md border border-line px-3 text-[13px] text-ink-2 hover:border-line-strong"
            >
              + 加一个
            </button>
          )}
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-line pt-3">
          <label className="inline-flex items-center gap-2 text-[12px] text-ink-2">
            <input
              type="checkbox"
              checked={diffOnly}
              onChange={e => setDiffOnly(e.target.checked)}
              className="h-3.5 w-3.5 accent-[var(--rw-primary)]"
            />
            只看差异项
          </label>
          <span className="mono text-[11px] text-ink-3">
            {picked.length} / {MAX} 已选
          </span>
        </div>
      </div>

      {picked.length < 2 ? (
        <div className="card border-dashed px-6 py-14 text-center">
          <p className="text-sm font-semibold text-ink">选两个以上的部件开始对比</p>
          <p className="mt-1.5 text-[13px] text-ink-3">参数字段不同、口径不一致的地方会被标出来。</p>
        </div>
      ) : (
        <>
          <p className="sm:hidden text-[12px] leading-5 text-ink-3">左右滑动查看全部列；首列固定。</p>
          <div
            className="overflow-x-auto rounded-lg border border-line bg-surface"
            style={{ WebkitOverflowScrolling: 'touch' }}
          >
            <table className="w-full min-w-[560px] border-collapse text-[13px]">
            <thead>
              <tr className="border-b border-line bg-surface-2">
                <th className="sticky left-0 z-10 bg-surface-2 px-3 py-2.5 text-left text-[11px] font-semibold text-ink-3">
                  字段
                </th>
                {picked.map(p => (
                  <th key={p.id} className="px-3 py-2.5 text-left align-top">
                    <a href={`${import.meta.env.BASE_URL}parts/${p.category}/${p.slug}.html`} className="block text-[13px] font-semibold text-ink hover:text-brand">
                      {p.model}
                    </a>
                    <span className="mt-0.5 block text-[11px] font-normal text-ink-3">{p.vendor}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-line">
                <th scope="row" className="sticky left-0 z-10 bg-surface px-3 py-2 text-left font-medium text-ink-2">价格</th>
                {picked.map(p => {
                  const offer = bestOfferPrice(p.offers)
                  const regular = typeof p.price === 'number' ? p.price : null
                  return (
                    <td key={p.id} className="mono tabular px-3 py-2 text-ink">
                      <span className={offer !== null ? 'font-semibold text-brand' : ''}>
                        {formatPrice(offer ?? regular)}
                        {offer !== null && <span className="ml-1 text-[10px] font-normal">优惠价</span>}
                      </span>
                      {offer !== null && regular !== null && offer < regular && (
                        <span className="ml-1.5 text-[10px] text-ink-3 ">{formatPrice(regular)}</span>
                      )}
                    </td>
                  )
                })}
              </tr>
              {visibleRows.map(row => {
                // 语义表优先；目录里新增、semantics.json 还没收录的 key 用内容包兜底，
                // 否则对比表左侧只剩一串 snake_case。
                const known = labels[row.key]
                const fallback = known?.label ? null : specLabel(row.key)
                const label = known?.label ?? fallback?.label ?? row.key
                const unit = known?.unit ?? fallback?.unit ?? ''
                return (
                  <tr key={row.key} className={row.differs ? 'border-b border-line bg-warning-soft/70' : 'border-b border-line'}>
                    <th scope="row" className="sticky left-0 z-10 bg-surface px-3 py-2 text-left font-medium text-ink-2">
                      <span>{label}</span>
                      {label !== row.key && (
                        <span className="mono ml-1.5 text-[10px] text-ink-3">{row.key}</span>
                      )}
                      {unit && <span className="ml-1 text-[10px] text-ink-3">({unit})</span>}
                    </th>
                    {row.values.map((v, i) => (
                      <td key={i} className="mono tabular px-3 py-2 text-ink">{cellContent(row.key, v)}</td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
          </div>
        </>
      )}

      <p className="text-[11px] leading-5 text-ink-3">
        高亮行表示这一列的值不一致。口径不同的数字（例如峰值与额定混比）不能直接比较，先看
        <a href={`${import.meta.env.BASE_URL}semantics.html`} className="mx-1 text-brand hover:underline">参数口径</a>
        再下结论。
      </p>
    </div>
  )
}
