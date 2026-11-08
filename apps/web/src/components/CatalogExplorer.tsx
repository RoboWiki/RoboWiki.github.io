import { useEffect, useId, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { categoryLabel, imageUrl, type CatalogPart } from '@/lib/catalog'
import { partFacts } from '@/lib/partFacts'
import { bestOfferPrice, effectivePrice, formatPrice, partHref } from '@/lib/utils'

type CategoryMeta = {
  id: string
  name: string
  keys?: Array<{ k: string; label?: string; unit?: string }>
  sorts?: Array<{ k: string; label: string }>
}
type Props = { parts: CatalogPart[]; categories: CategoryMeta[] }

const PAGE = 24
const INTERACTIVE_HOME = '/community.html'
const DEFAULT_SORT = 'effective_price:asc'
const DEFAULT_CATEGORY = 'actuator'

function PartRating({ rating }: { rating?: CatalogPart['rating'] }) {
  const count = Number(rating?.count) || 0
  const rawAvg = rating?.avg
  const avg = typeof rawAvg === 'number' && Number.isFinite(rawAvg) ? rawAvg : null
  if (!count || avg === null) {
    return <span className="text-ink-3">暂无评分</span>
  }
  return (
    <span className="inline-flex items-center gap-1">
      <span aria-hidden="true" className="text-warning">★</span>
      <span className="mono tabular font-medium text-ink">{avg.toFixed(1)}</span>
      <span className="mono tabular text-ink-3">({count})</span>
      <span className="sr-only">分，{count} 人评分</span>
    </span>
  )
}

function hasOffer(p: CatalogPart) {
  const today = new Date().toISOString().slice(0, 10)
  return (p.offers ?? []).some(o => {
    const offer = o as { demo?: boolean; expires?: string | null }
    return !offer.demo && (!offer.expires || offer.expires >= today)
  })
}

export default function CatalogExplorer({ parts, categories }: Props) {
  const [q, setQ] = useState('')
  const [cat, setCat] = useState(DEFAULT_CATEGORY)
  const [openOnly, setOpenOnly] = useState(false)
  const [offerOnly, setOfferOnly] = useState(false)
  const [vendor, setVendor] = useState('')
  const [sort, setSort] = useState(DEFAULT_SORT)
  // 对比托盘：最多 4 个，落 localStorage，跨页面（部件库 → 对比页）复用
  const [picked, setPicked] = useState<string[]>([])
  const [limit, setLimit] = useState(PAGE)
  const searchId = useId()

  // Initial filters come from the plain URL query string — no router involved.
  // `?category=` 来自品类入口，`?q=` 来自全站搜索框，两者可叠加。
  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      const raw = localStorage.getItem('rw-compare')
      const list = raw ? (JSON.parse(raw) as unknown) : []
      if (Array.isArray(list)) setPicked(list.filter((v): v is string => typeof v === 'string').slice(0, 4))
    } catch { /* 存储不可用时忽略 */ }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      localStorage.setItem('rw-compare', JSON.stringify(picked))
    } catch { /* 隐私模式下写不进去也不影响使用 */ }
  }, [picked])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    const fromUrl = params.get('category') || ''
    const fromQuery = params.get('q') || ''
    if (fromUrl && categories.some(c => c.id === fromUrl)) setCat(fromUrl)
    if (fromQuery) setQ(fromQuery)
    if (params.get('offer') === '1') setOfferOnly(true)
  }, [categories])

  const searched = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return parts
    return parts.filter(p =>
      [p.id, p.slug, p.vendor, p.model, p.notes, p.subtypeLabel, p.category]
        .filter(Boolean).join(' ').toLowerCase().includes(needle),
    )
  }, [parts, q])

  const counts = useMemo(() => {
    const map: Record<string, number> = {}
    for (const p of searched) map[p.category] = (map[p.category] || 0) + 1
    return map
  }, [searched])

  const hasRepo = (p: CatalogPart) => {
    const repos = (p.specs as Record<string, unknown> | undefined)?.repo_urls
    return Array.isArray(repos) && repos.length > 0
  }

  const catMeta = categories.find(c => c.id === cat)
  const sortOptions = useMemo(() => {
    const keySorts = (catMeta?.sorts || []).filter(item => !['price', 'rating'].includes(item.k))
    return [
      { value: DEFAULT_SORT, label: '优惠价 / 价格从低到高（默认）' },
      { value: '', label: '综合排序' },
      ...keySorts.map(item => ({ value: `${item.k}:desc`, label: `${item.label} 从高到低` })),
      { value: 'price:asc', label: '普通参考价从低到高' },
      { value: 'price:desc', label: '普通参考价从高到低' },
      { value: 'rating:desc', label: '评分从高到低' },
    ]
  }, [catMeta])

  const vendorBase = useMemo(
    () => (cat ? searched.filter(p => p.category === cat) : searched),
    [searched, cat],
  )
  const vendors = useMemo(() => {
    const map = new Map<string, number>()
    for (const p of vendorBase) map.set(p.vendor, (map.get(p.vendor) || 0) + 1)
    return [...map.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh-CN'))
  }, [vendorBase])

  const sortValue = (p: CatalogPart, key: string): number | string | null => {
    if (key === 'effective_price') return effectivePrice(p.price, p.offers)
    if (key === 'price') return typeof p.price === 'number' ? p.price : null
    if (key === 'rating') return typeof p.rating?.avg === 'number' ? p.rating.avg : null
    const raw = (p.specs as Record<string, unknown> | undefined)?.[key] ?? (p as unknown as Record<string, unknown>)[key]
    if (typeof raw === 'number') return raw
    if (typeof raw === 'string') {
      const n = Number(raw.replace(/,/g, '').match(/-?\d+(?:\.\d+)?/)?.[0])
      return Number.isFinite(n) ? n : raw
    }
    return null
  }

  const filtered = useMemo(() => {
    let list = searched
    if (cat) list = list.filter(p => p.category === cat)
    if (vendor) list = list.filter(p => p.vendor === vendor)
    if (openOnly) list = list.filter(hasRepo)
    if (offerOnly) list = list.filter(hasOffer)
    if (sort) {
      const [key, dir] = sort.split(':')
      const sign = dir === 'asc' ? 1 : -1
      list = [...list].sort((a, b) => {
        const av = sortValue(a, key)
        const bv = sortValue(b, key)
        if (av === null && bv === null) {
          const ra = Number(a.rating?.avg ?? -1)
          const rb = Number(b.rating?.avg ?? -1)
          return rb - ra || a.model.localeCompare(b.model, 'zh-CN')
        }
        if (av === null) return 1
        if (bv === null) return -1
        if (typeof av === 'number' && typeof bv === 'number') {
          if (av === bv) {
            const ra = Number(a.rating?.avg ?? -1)
            const rb = Number(b.rating?.avg ?? -1)
            return rb - ra || a.model.localeCompare(b.model, 'zh-CN')
          }
          return (av - bv) * sign
        }
        return String(av).localeCompare(String(bv), 'zh-CN') * sign
      })
    }
    return list
  }, [searched, cat, vendor, openOnly, offerOnly, sort])

  const openCount = useMemo(() => {
    const base = cat ? searched.filter(p => p.category === cat) : searched
    return base.filter(hasRepo).length
  }, [searched, cat])

  const offerCount = useMemo(() => {
    let base = cat ? searched.filter(p => p.category === cat) : searched
    if (vendor) base = base.filter(p => p.vendor === vendor)
    return base.filter(hasOffer).length
  }, [searched, cat, vendor])

  const shown = filtered.slice(0, limit)
  const needle = q.trim()
  const hasFilter = Boolean(
    (cat && cat !== DEFAULT_CATEGORY) || needle || openOnly || offerOnly || vendor
    || (sort && sort !== DEFAULT_SORT),
  )

  const selectCategory = (next: string) => {
    setCat(next)
    setVendor('')
    setLimit(PAGE)
    if (typeof window === 'undefined') return
    // Keep the filter shareable without pulling in a router.
    try {
      const url = new URL(window.location.href)
      if (next) url.searchParams.set('category', next)
      else url.searchParams.delete('category')
      window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`)
    } catch { /* history unavailable: filter still works */ }
  }

  const togglePick = (id: string) => {
    setPicked(prev => {
      if (prev.includes(id)) return prev.filter(item => item !== id)
      if (prev.length >= 4) return prev
      return [...prev, id]
    })
  }

  const reset = () => {
    setQ('')
    setOpenOnly(false)
    setOfferOnly(false)
    setVendor('')
    setSort(DEFAULT_SORT)
    selectCategory(DEFAULT_CATEGORY)
  }

  return (
    <div className="space-y-4">
      <div className="sticky top-16 z-30 -mx-4 border-y border-line bg-bg/90 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-lg sm:border sm:px-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
          <div role="search" className="relative w-full sm:flex-1">
            <label htmlFor={searchId} className="sr-only">搜索部件型号、厂商或用途</label>
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
              onChange={e => {
                const value = e.target.value
                setQ(value)
                setLimit(PAGE)
                if (typeof window === 'undefined') return
                try {
                  const url = new URL(window.location.href)
                  if (value) url.searchParams.set('q', value)
                  else url.searchParams.delete('q')
                  window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`)
                } catch { /* history unavailable: search still works */ }
              }}
              placeholder="搜索型号、厂商、用途…"
              className="h-11 pl-9 pr-11 text-base sm:h-9 sm:text-sm"
              autoComplete="off"
              enterKeyHint="search"
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
              <span className="mono tabular font-semibold text-ink">{filtered.length}</span> 个结果
              {cat && <span> · {categoryLabel(cat)}</span>}
              {needle && <span> · 含“{needle}”</span>}
            </p>
            {hasFilter && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="min-h-9 shrink-0 px-2 text-xs"
                onClick={reset}
              >
                重置
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="chip-row -mx-1 px-1" role="group" aria-label="按品类筛选">
        <button
          type="button"
          className="chip"
          aria-pressed={!cat}
          onClick={() => selectCategory('')}
        >
          全部<span className="mono tabular opacity-60">{searched.length}</span>
        </button>
        {categories.map(c => (
          <button
            key={c.id}
            type="button"
            className="chip"
            aria-pressed={cat === c.id}
            onClick={() => selectCategory(c.id)}
          >
            {c.name}
            <span className="mono tabular opacity-60">{counts[c.id] || 0}</span>
          </button>
        ))}
      </div>

      <div className="chip-row -mx-1 px-1" role="group" aria-label="按品牌筛选">
        <button
          type="button"
          className="chip h-7 px-2.5 text-[12px]"
          aria-pressed={!vendor}
          onClick={() => { setVendor(''); setLimit(PAGE) }}
        >
          全部品牌<span className="mono tabular opacity-60">{vendorBase.length}</span>
        </button>
        {vendors.slice(0, 10).map(([name, count]) => (
          <button
            key={name}
            type="button"
            className="chip h-7 px-2.5 text-[12px]"
            aria-pressed={vendor === name}
            onClick={() => { setVendor(vendor === name ? '' : name); setLimit(PAGE) }}
          >
            {name}<span className="mono tabular opacity-60">{count}</span>
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <button
          type="button"
          className={`chip h-7 px-2.5 text-[12px] ${offerOnly ? 'border-brand bg-brand-soft text-brand' : ''}`}
          aria-pressed={offerOnly}
          onClick={() => {
            setOfferOnly(v => !v)
            setLimit(PAGE)
            try {
              const url = new URL(window.location.href)
              if (!offerOnly) url.searchParams.set('offer', '1')
              else url.searchParams.delete('offer')
              window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`)
            } catch { /* history unavailable */ }
          }}
          title="只显示当前有优惠价/渠道优惠的部件"
        >
          有优惠
          <span className="mono tabular opacity-60">{offerCount}</span>
        </button>
        <button
          type="button"
          className="chip h-7 px-2.5 text-[12px]"
          aria-pressed={openOnly}
          onClick={() => { setOpenOnly(v => !v); setLimit(PAGE) }}
          title="只显示带开源仓库的条目"
        >
          开源
          <span className="mono tabular opacity-60">{openCount}</span>
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label className="inline-flex items-center gap-2 text-[11px] text-ink-3">
          品牌
          <select
            value={vendor}
            onChange={event => { setVendor(event.target.value); setLimit(PAGE) }}
            className="h-8 rounded-md border border-line bg-surface px-2 text-[12px] text-ink"
          >
            <option value="">全部品牌（{vendorBase.length}）</option>
            {vendors.map(([name, count]) => <option value={name}>{name}（{count}）</option>)}
          </select>
        </label>
        <label className="inline-flex items-center gap-2 text-[11px] text-ink-3">
          排序
          <select
            value={sort}
            onChange={event => { setSort(event.target.value); setLimit(PAGE) }}
            className="h-8 rounded-md border border-line bg-surface px-2 text-[12px] text-ink"
          >
            {sortOptions.map(item => <option value={item.value}>{item.label}</option>)}
          </select>
        </label>
      </div>

      {shown.length === 0 ? (
        <div className="card border-dashed px-6 py-16 text-center">
          <div aria-hidden="true" className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-surface-3 text-ink-3">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
            </svg>
          </div>
          <p className="mt-4 font-semibold text-ink">
            {parts.length === 0 ? '目录数据尚未就绪' : '没有匹配的部件'}
          </p>
          <p className="mx-auto mt-1.5 max-w-sm text-sm leading-6 text-ink-3">
            {parts.length === 0
              ? '数据集还在生成中，稍后刷新即可。'
              : '换个关键词，或清空品类筛选。也可以把需求发到互动版，让用过的同行补充。'}
          </p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            {hasFilter && (
              <Button type="button" variant="outline" className="min-h-11 sm:min-h-9" onClick={reset}>
                清空筛选
              </Button>
            )}
            <a
              href={INTERACTIVE_HOME}
              className="inline-flex min-h-11 items-center gap-1 rounded-md px-3 text-sm font-medium text-brand hover:bg-brand-soft sm:min-h-9"
            >
              去社区提问<span aria-hidden="true">→</span>
            </a>
          </div>
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" role="list">
          {shown.map(p => (
            <li key={p.id} className="relative min-w-0">
              <button
                type="button"
                onClick={() => togglePick(p.id)}
                aria-pressed={picked.includes(p.id)}
                aria-label={`${picked.includes(p.id) ? '移出对比' : '加入对比'}：${p.vendor} ${p.model}`}
                title={picked.includes(p.id) ? '移出对比' : '加入对比（最多 4 个）'}
                className={`absolute right-2 top-2 z-10 grid h-7 w-7 place-items-center rounded-sm border text-[12px] transition-colors ${
                  picked.includes(p.id)
                    ? 'border-brand bg-brand text-brand-fg'
                    : 'border-line bg-surface/90 text-ink-3 backdrop-blur hover:border-line-strong hover:text-ink'
                }`}
              >
                {picked.includes(p.id) ? '✓' : '+'}
              </button>
              <a
                href={partHref(p)}
                className="group flex h-full rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 focus-visible:ring-offset-2"
              >
                <Card className="flex h-full w-full flex-col overflow-hidden transition duration-200 group-hover:-translate-y-0.5 group-hover:border-line-strong group-hover:shadow-md">
                  <div className="relative flex h-32 shrink-0 items-center justify-center border-b border-line bg-surface-2 sm:h-36">
                    {p.image
                      ? <img src={imageUrl(p)} alt={`${p.vendor} ${p.model}`} loading="lazy" className="h-full w-full object-contain p-4 transition-transform duration-300 group-hover:scale-[1.03]" />
                      : <span className="px-4 text-center text-xs text-ink-3">暂无产品图</span>}
                    <div className="absolute left-2 top-2">
                      {hasOffer(p) && <span className="rounded-full border border-line bg-brand-soft px-2 py-0.5 text-[11px] font-medium text-brand">有优惠</span>}
                    </div>
                  </div>
                  <div className="flex flex-1 flex-col gap-2 p-4">
                    <div className="flex items-center gap-1.5 text-[11px] text-ink-3">
                      <span>{categoryLabel(p.category)}</span>
                      <span aria-hidden="true">·</span>
                      <span className="truncate">{p.vendor}</span>
                    </div>
                    <div className="line-clamp-2 min-h-10 text-sm font-semibold leading-5 text-ink">{p.model}</div>
                    <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                      {partFacts(p).map(f => (
                        <div key={f.label} className="min-w-0">
                          <dt className="text-[10px] leading-4 text-ink-3">{f.label}</dt>
                          <dd className="mono tabular truncate text-[12px] leading-5 text-ink-2">{f.value}</dd>
                        </div>
                      ))}
                    </dl>
                    <div className="mt-auto flex items-center justify-between gap-2 border-t border-line pt-2 text-xs">
                      <span className="flex min-w-0 flex-col">
                        {(() => {
                          const offer = bestOfferPrice(p.offers)
                          const regular = typeof p.price === 'number' ? p.price : null
                          const showCompare = offer !== null && regular !== null && offer < regular
                          return (
                            <>
                              <span className="flex items-baseline gap-1.5">
                                <span className={`mono tabular truncate font-semibold ${offer !== null ? 'text-brand' : 'text-ink-2'}`}>
                                  {formatPrice(offer ?? regular)}
                                </span>
                                {offer !== null && <span className="shrink-0 text-[10px] font-medium text-brand" title="需满足活动资格，详见详情">优惠价</span>}
                              </span>
                              {showCompare && <span className="mono tabular text-[10px] text-ink-3 ">参考 {formatPrice(regular)}</span>}
                            </>
                          )
                        })()}
                      </span>
                      <PartRating rating={p.rating} />
                    </div>
                  </div>
                </Card>
              </a>
            </li>
          ))}
        </ul>
      )}

      {picked.length > 0 && (
        <div className="fixed inset-x-3 bottom-4 z-40 mx-auto flex max-w-xl items-center gap-3 rounded-lg border border-line bg-surface px-3 py-2 shadow-lg sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2">
          <span className="mono tabular text-[12px] text-ink-2">已选 {picked.length}/4</span>
          <a
            href={`${import.meta.env.BASE_URL}compare.html?ids=${picked.join(',')}`}
            className="inline-flex h-8 items-center rounded-md bg-brand px-3 text-[12px] font-semibold text-brand-fg hover:bg-brand-hover"
          >
            去对比
          </a>
          <button
            type="button"
            onClick={() => setPicked([])}
            className="ml-auto text-[12px] text-ink-3 hover:text-ink"
          >
            清空
          </button>
        </div>
      )}

      {filtered.length > PAGE && (
        <div className="flex flex-col items-center gap-2 pt-1">
          <p className="mono tabular text-xs text-ink-3" aria-live="polite">
            已显示 {shown.length} / {filtered.length}
          </p>
          {limit < filtered.length ? (
            <Button
              type="button"
              variant="outline"
              className="min-h-11 w-full sm:min-h-9 sm:w-auto"
              onClick={() => setLimit(v => v + PAGE)}
            >
              加载更多（剩余 {filtered.length - limit}）
            </Button>
          ) : (
            <p className="text-xs text-ink-3">已显示全部 {filtered.length} 个部件</p>
          )}
        </div>
      )}
    </div>
  )
}
