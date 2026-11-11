import { useId, useMemo, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { imageUrl, type CatalogPart } from '@/lib/catalog'
import { partFacts } from '@/lib/partFacts'
import { formatPrice, partHref } from '@/lib/utils'

type SubtypeMeta = { id: string; label: string }

type Props = { parts: CatalogPart[]; subtypes: SubtypeMeta[] }

const PAGE = 24

function sortValue(p: CatalogPart, key: string): number | string | null {
  if (key === 'price') return typeof p.price === 'number' ? p.price : null
  if (key === 'rating') return typeof p.rating?.avg === 'number' ? p.rating.avg : null
  const raw = (p.specs as Record<string, unknown> | undefined)?.[key]
  if (typeof raw === 'number') return raw
  if (typeof raw === 'string') {
    const n = Number(raw.replace(/,/g, '').match(/-?\d+(?:\.\d+)?/)?.[0])
    return Number.isFinite(n) ? n : raw
  }
  return null
}

/**
 * 设备库浏览器：与部件库同一种卡片与筛选语言（搜索 + 类型 chips + 厂商 chips + 排序），
 * 但只装 equipment 一个品类，筛选项换成设备子类（3D 打印机 / 激光 / 焊台 / 电源 / 仪器）。
 */
export default function EquipmentExplorer({ parts, subtypes }: Props) {
  const [q, setQ] = useState('')
  const [sub, setSub] = useState('')
  const [vendor, setVendor] = useState('')
  const [sort, setSort] = useState('')
  const [limit, setLimit] = useState(PAGE)
  const searchId = useId()

  const searched = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return parts
    return parts.filter(p =>
      [p.id, p.slug, p.vendor, p.model, p.notes, p.subtypeLabel, p.subtype]
        .filter(Boolean).join(' ').toLowerCase().includes(needle),
    )
  }, [parts, q])

  const subCounts = useMemo(() => {
    const map: Record<string, number> = {}
    for (const p of searched) {
      const key = p.subtype || ''
      map[key] = (map[key] || 0) + 1
    }
    return map
  }, [searched])

  // 厂商 chips 跟随当前选中的类型（与部件库「品类内选品牌」同构）
  const subBase = useMemo(
    () => (sub ? searched.filter(p => p.subtype === sub) : searched),
    [searched, sub],
  )
  const vendors = useMemo(() => {
    const map = new Map<string, number>()
    for (const p of subBase) map.set(p.vendor, (map.get(p.vendor) || 0) + 1)
    return [...map.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh-CN'))
  }, [subBase])

  const filtered = useMemo(() => {
    let list = searched
    if (sub) list = list.filter(p => p.subtype === sub)
    if (vendor) list = list.filter(p => p.vendor === vendor)
    if (sort) {
      const [key, dir] = sort.split(':')
      const sign = dir === 'asc' ? 1 : -1
      list = [...list].sort((a, b) => {
        const av = sortValue(a, key)
        const bv = sortValue(b, key)
        if (av === null && bv === null) return a.model.localeCompare(b.model, 'zh-CN')
        if (av === null) return 1
        if (bv === null) return -1
        if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * sign
        return String(av).localeCompare(String(bv), 'zh-CN') * sign
      })
    }
    return list
  }, [searched, sub, vendor, sort])

  const shown = filtered.slice(0, limit)
  const hasFilter = Boolean(sub || vendor || q.trim() || sort)

  const reset = () => {
    setQ('')
    setSub('')
    setVendor('')
    setSort('')
    setLimit(PAGE)
  }

  const pickSub = (next: string) => {
    setSub(next)
    setVendor('')
    setLimit(PAGE)
  }

  return (
    <div className="space-y-4">
      <div className="sticky top-16 z-30 -mx-4 border-y border-line bg-bg/90 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-lg sm:border sm:px-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
          <div role="search" className="relative w-full sm:flex-1">
            <label htmlFor={searchId} className="sr-only">搜索设备型号、厂商或用途</label>
            <svg
              viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round"
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-3"
            >
              <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
            </svg>
            <Input
              id={searchId}
              type="search"
              value={q}
              onChange={e => { setQ(e.target.value); setLimit(PAGE) }}
              placeholder="例如：P1S、万用表、热风枪"
              className="h-11 pl-9 text-base sm:h-9 sm:text-sm"
            />
            {q && (
              <button
                type="button"
                onClick={() => { setQ(''); setLimit(PAGE) }}
                aria-label="清空搜索"
                className="absolute right-1 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-sm text-lg leading-none text-ink-3 hover:bg-surface-3 hover:text-ink"
              >
                <span aria-hidden="true">×</span>
              </button>
            )}
          </div>
          <div className="flex min-h-8 items-center justify-between gap-2 sm:justify-end">
            <p className="text-xs text-ink-3" aria-live="polite" aria-atomic="true">
              <span className="mono tabular font-semibold text-ink">{filtered.length}</span> 台设备
              {sub && <span> · {subtypes.find(s => s.id === sub)?.label ?? sub}</span>}
              {vendor && <span> · {vendor}</span>}
            </p>
            {hasFilter && (
              <button
                type="button"
                onClick={reset}
                className="inline-flex h-9 shrink-0 items-center rounded-md px-2 text-xs font-medium text-ink-3 transition-colors hover:text-ink"
              >
                重置
              </button>
            )}
          </div>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
          <div className="flex items-center gap-2">
            <label htmlFor={`${searchId}-sort`} className="text-xs text-ink-3">排序</label>
            <select
              id={`${searchId}-sort`}
              value={sort}
              onChange={e => setSort(e.target.value)}
              className="h-9 rounded-md border border-line bg-surface px-2 text-sm text-ink focus-visible:border-brand focus-visible:outline-none"
            >
              <option value="">综合排序</option>
              <option value="price:asc">参考价从低到高</option>
              <option value="price:desc">参考价从高到低</option>
              <option value="rating:desc">评分从高到低</option>
            </select>
          </div>
        </div>
      </div>

      <div className="chip-row -mx-1 px-1" role="group" aria-label="按设备类型筛选">
        <button
          type="button"
          className="chip"
          aria-pressed={!sub}
          onClick={() => pickSub('')}
        >
          全部<span className="mono tabular opacity-60">{searched.length}</span>
        </button>
        {subtypes.map(s => (
          <button
            key={s.id}
            type="button"
            className="chip"
            aria-pressed={sub === s.id}
            onClick={() => pickSub(sub === s.id ? '' : s.id)}
          >
            {s.label}
            <span className="mono tabular opacity-60">{subCounts[s.id] || 0}</span>
          </button>
        ))}
      </div>

      <div className="chip-row -mx-1 px-1" role="group" aria-label="按厂商筛选">
        <button
          type="button"
          className="chip h-7 px-2.5 text-xs"
          aria-pressed={!vendor}
          onClick={() => { setVendor(''); setLimit(PAGE) }}
        >
          全部厂商<span className="mono tabular opacity-60">{subBase.length}</span>
        </button>
        {vendors.slice(0, 10).map(([name, count]) => (
          <button
            key={name}
            type="button"
            className="chip h-7 px-2.5 text-xs"
            aria-pressed={vendor === name}
            onClick={() => { setVendor(vendor === name ? '' : name); setLimit(PAGE) }}
          >
            {name}
            <span className="mono tabular opacity-60">{count}</span>
          </button>
        ))}
      </div>

      {shown.length === 0 ? (
        <div className="card p-10 text-center" data-empty="">
          <p className="text-sm font-semibold text-ink">没有匹配的设备</p>
          <p className="mx-auto mt-1.5 max-w-sm text-sm leading-6 text-ink-3">
            换个关键词，或切回全部类型。
          </p>
          {hasFilter && (
            <button
              type="button"
              onClick={reset}
              className="mt-5 inline-flex h-9 items-center rounded-md border border-line px-3 text-sm font-medium text-ink-2 hover:text-ink"
            >
              清除筛选
            </button>
          )}
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" role="list">
          {shown.map(p => (
            <li key={p.id} className="min-w-0">
              <a href={partHref(p)} className="group flex h-full rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 focus-visible:ring-offset-2">
                <Card className="flex h-full w-full flex-col overflow-hidden transition duration-200 group-hover:-translate-y-0.5 group-hover:border-line-strong group-hover:shadow-md">
                  <div className="relative flex h-32 shrink-0 items-center justify-center border-b border-line bg-surface-2 sm:h-36">
                    {p.image
                      ? <img src={imageUrl(p)} alt={`${p.vendor} ${p.model}`} loading="lazy" className="h-full w-full object-contain p-4 transition-transform duration-300 group-hover:scale-[1.03]" />
                      : <span className="px-4 text-center text-xs text-ink-3">暂无产品图</span>}
                  </div>
                  <div className="flex flex-1 flex-col gap-2 p-4">
                    <div className="flex items-center gap-1.5 text-xs text-ink-3">
                      <span>{p.subtypeLabel || '设备'}</span>
                      <span aria-hidden="true">·</span>
                      <span className="truncate">{p.vendor}</span>
                    </div>
                    <div className="line-clamp-2 min-h-10 text-sm font-semibold leading-5 text-ink">{p.model}</div>
                    <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                      {partFacts(p).map(f => (
                        <div key={f.label} className="min-w-0">
                          <dt className="text-xs leading-4 text-ink-3">{f.label}</dt>
                          <dd className="mono tabular truncate text-xs leading-5 text-ink-2">{f.value}</dd>
                        </div>
                      ))}
                    </dl>
                    <div className="mt-auto flex items-center justify-between gap-2 border-t border-line pt-2 text-xs">
                      <span className="mono tabular font-medium text-ink">{formatPrice(p.price)}</span>
                      <span className="text-ink-3 transition-transform group-hover:translate-x-0.5" aria-hidden="true">→</span>
                    </div>
                  </div>
                </Card>
              </a>
            </li>
          ))}
        </ul>
      )}

      {shown.length < filtered.length && (
        <div className="flex justify-center">
          <button
            type="button"
            onClick={() => setLimit(v => v + PAGE)}
            className="inline-flex h-10 items-center rounded-md border border-line px-4 text-sm font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
          >
            加载更多（还有 {filtered.length - shown.length} 台）
          </button>
        </div>
      )}
    </div>
  )
}
