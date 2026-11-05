import { useEffect, useId, useMemo, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { categoryLabel, imageUrl, type CatalogPart } from '@/lib/catalog'
import { formatPrice, partHref } from '@/lib/utils'

type Props = { parts: CatalogPart[]; categories: { id: string; name: string }[] }

const PAGE = 24
const INTERACTIVE_HOME = 'https://robowiki.org.cn'

function PartRating({ rating }: { rating?: CatalogPart['rating'] }) {
  const count = Number(rating?.count) || 0
  const rawAvg = rating?.avg
  const avg = typeof rawAvg === 'number' && Number.isFinite(rawAvg) ? rawAvg : null
  if (!count || avg === null) {
    return <span className="text-slate-400">暂无评分</span>
  }
  return (
    <span className="inline-flex items-center gap-1">
      <span aria-hidden="true" className="text-amber-500">★</span>
      <span className="font-medium tabular-nums text-slate-700">{avg.toFixed(1)}</span>
      <span className="tabular-nums text-slate-500">({count})</span>
      <span className="sr-only">分，{count} 人评分</span>
    </span>
  )
}

export default function CatalogExplorer({ parts, categories }: Props) {
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('')
  const [limit, setLimit] = useState(PAGE)
  const searchId = useId()

  // Initial category comes from the plain URL query string — no router involved.
  useEffect(() => {
    if (typeof window === 'undefined') return
    const fromUrl = new URLSearchParams(window.location.search).get('category') || ''
    if (fromUrl && categories.some(c => c.id === fromUrl)) setCat(fromUrl)
  }, [categories])

  const searched = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return parts
    return parts.filter(p =>
      [p.id, p.vendor, p.model, p.notes, p.subtypeLabel, p.category]
        .filter(Boolean).join(' ').toLowerCase().includes(needle),
    )
  }, [parts, q])

  const counts = useMemo(() => {
    const map: Record<string, number> = {}
    for (const p of searched) map[p.category] = (map[p.category] || 0) + 1
    return map
  }, [searched])

  const filtered = useMemo(
    () => (cat ? searched.filter(p => p.category === cat) : searched),
    [searched, cat],
  )

  const shown = filtered.slice(0, limit)
  const needle = q.trim()
  const hasFilter = Boolean(cat || needle)

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

  const reset = () => {
    setQ('')
    selectCategory('')
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
          <div role="search" className="relative w-full sm:flex-1">
            <label htmlFor={searchId} className="sr-only">搜索部件型号、厂商或用途</label>
            <svg
              viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round"
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            >
              <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
            </svg>
            <Input
              id={searchId}
              type="search"
              value={q}
              onChange={e => { setQ(e.target.value); setLimit(PAGE) }}
              placeholder="搜索型号、厂商、用途…"
              className="h-11 pl-9 pr-11 text-base sm:h-10 sm:text-sm"
              autoComplete="off"
              enterKeyHint="search"
            />
            {q && (
              <button
                type="button"
                onClick={() => { setQ(''); setLimit(PAGE) }}
                aria-label="清空搜索"
                className="absolute right-1 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-lg text-lg leading-none text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <span aria-hidden="true">×</span>
              </button>
            )}
          </div>
          <div className="flex min-h-9 items-center justify-between gap-2 sm:justify-end">
            <p className="text-xs text-slate-500" aria-live="polite" aria-atomic="true">
              {filtered.length} 个结果
              {cat && <span className="text-slate-400"> · {categoryLabel(cat)}</span>}
              {needle && <span className="text-slate-400"> · 含“{needle}”</span>}
            </p>
            {hasFilter && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="min-h-9 shrink-0 px-2 text-xs text-slate-500 hover:text-slate-900"
                onClick={reset}
              >
                重置筛选
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="chip-row -mx-1 px-1" role="group" aria-label="按品类筛选">
        <Button
          type="button"
          size="sm"
          variant={cat ? 'outline' : 'default'}
          aria-pressed={!cat}
          className="min-h-11 px-4 sm:min-h-8"
          onClick={() => selectCategory('')}
        >
          全部<span className="ml-1 tabular-nums opacity-70">{searched.length}</span>
        </Button>
        {categories.map(c => (
          <Button
            key={c.id}
            type="button"
            size="sm"
            variant={cat === c.id ? 'default' : 'outline'}
            aria-pressed={cat === c.id}
            className="min-h-11 px-4 sm:min-h-8"
            onClick={() => selectCategory(c.id)}
          >
            {c.name}
            <span className="ml-1 tabular-nums opacity-70">{counts[c.id] || 0}</span>
          </Button>
        ))}
      </div>

      {shown.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center">
          <div aria-hidden="true" className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-400">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
            </svg>
          </div>
          <p className="mt-3 font-medium text-slate-800">
            {parts.length === 0 ? '目录数据尚未就绪' : '没有匹配的部件'}
          </p>
          <p className="mx-auto mt-1 max-w-sm text-sm leading-6 text-slate-500">
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
              target="_blank"
              rel="noopener"
              className="inline-flex min-h-11 items-center gap-1 rounded-lg px-3 text-sm font-medium text-blue-700 hover:bg-blue-50 sm:min-h-9"
            >
              去互动版提问<span aria-hidden="true">↗</span>
            </a>
          </div>
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" role="list">
          {shown.map(p => (
            <li key={p.id} className="min-w-0">
              <a
                href={partHref(p)}
                className="group flex h-full rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
              >
                <Card className="flex h-full w-full flex-col overflow-hidden transition group-hover:-translate-y-0.5 group-hover:shadow-md">
                  <div className="flex h-32 shrink-0 items-center justify-center bg-gradient-to-br from-slate-100 to-slate-50 sm:h-36">
                    {p.image
                      ? <img src={imageUrl(p)} alt={`${p.vendor} ${p.model}`} loading="lazy" className="h-full w-full object-contain p-3" />
                      : <span className="px-4 text-center text-xs text-slate-400">暂无产品图</span>}
                  </div>
                  <div className="flex flex-1 flex-col gap-2 p-4">
                    <div className="flex min-h-6 flex-wrap content-start items-center gap-1.5">
                      <Badge variant="secondary">{categoryLabel(p.category)}</Badge>
                      {p.tier && <Badge variant="outline">来源 {p.tier}</Badge>}
                    </div>
                    <div className="min-w-0">
                      <div className="truncate text-xs text-slate-500">{p.vendor}</div>
                      <div className="mt-0.5 line-clamp-2 min-h-10 text-sm font-semibold leading-5 text-slate-900">{p.model}</div>
                    </div>
                    <div className="mt-auto flex items-center justify-between gap-2 border-t border-slate-100 pt-2 text-xs">
                      <span className="truncate font-medium tabular-nums text-slate-700">{formatPrice(p.price)}</span>
                      <PartRating rating={p.rating} />
                    </div>
                  </div>
                </Card>
              </a>
            </li>
          ))}
        </ul>
      )}

      {filtered.length > PAGE && (
        <div className="flex flex-col items-center gap-2 pt-1">
          <p className="text-xs tabular-nums text-slate-500" aria-live="polite">
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
            <p className="text-xs text-slate-400">已显示全部 {filtered.length} 个部件</p>
          )}
        </div>
      )}
    </div>
  )
}
