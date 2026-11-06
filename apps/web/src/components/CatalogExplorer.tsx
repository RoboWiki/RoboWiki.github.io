import { useEffect, useId, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { categoryLabel, imageUrl, type CatalogPart } from '@/lib/catalog'
import { formatPrice, partHref } from '@/lib/utils'

type Props = { parts: CatalogPart[]; categories: { id: string; name: string }[] }

const PAGE = 24
const INTERACTIVE_HOME = '/community.html'

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

function TierBadge({ tier }: { tier?: string }) {
  if (!tier) return null
  const cls = tier === 'A' ? 'tier tier-a' : tier === 'B' ? 'tier tier-b' : 'tier tier-c'
  return <span className={cls}>{tier} 级</span>
}

export default function CatalogExplorer({ parts, categories }: Props) {
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('')
  const [tier, setTier] = useState('')
  const [openOnly, setOpenOnly] = useState(false)
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

  const filtered = useMemo(() => {
    let list = searched
    if (cat) list = list.filter(p => p.category === cat)
    if (tier === 'verified') list = list.filter(p => p.verified)
    else if (tier) list = list.filter(p => p.tier === tier)
    if (openOnly) list = list.filter(hasRepo)
    return list
  }, [searched, cat, tier, openOnly])

  const tierCounts = useMemo(() => {
    const base = cat ? searched.filter(p => p.category === cat) : searched
    return {
      A: base.filter(p => p.tier === 'A').length,
      B: base.filter(p => p.tier === 'B').length,
      C: base.filter(p => p.tier === 'C').length,
      verified: base.filter(p => p.verified).length,
      all: base.length,
    }
  }, [searched, cat])

  const openCount = useMemo(() => {
    const base = cat ? searched.filter(p => p.category === cat) : searched
    return base.filter(hasRepo).length
  }, [searched, cat])

  const shown = filtered.slice(0, limit)
  const needle = q.trim()
  const hasFilter = Boolean(cat || needle || tier || openOnly)

  const selectCategory = (next: string) => {
    setCat(next)
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
    setTier('')
    setOpenOnly(false)
    selectCategory('')
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

      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] text-ink-3">来源</span>
        {[
          { value: '', label: '全部', n: tierCounts.all },
          { value: 'A', label: 'A 级', n: tierCounts.A },
          { value: 'B', label: 'B 级', n: tierCounts.B },
          ...(tierCounts.C > 0 ? [{ value: 'C', label: 'C 级', n: tierCounts.C }] : []),
          { value: 'verified', label: '已核对', n: tierCounts.verified },
        ].map(t => (
          <button
            key={t.value || 'all'}
            type="button"
            className="chip h-7 px-2.5 text-[12px]"
            aria-pressed={tier === t.value}
            onClick={() => { setTier(t.value); setLimit(PAGE) }}
          >
            {t.label}
            <span className="mono tabular opacity-60">{t.n}</span>
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-line" aria-hidden="true" />
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
                      <TierBadge tier={p.tier} />
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
                    <div className="mt-auto flex items-center justify-between gap-2 border-t border-line pt-2 text-xs">
                      <span className="mono tabular truncate font-medium text-ink-2">{formatPrice(p.price)}</span>
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
