import { Badge } from '@/components/ui/badge'
import { TAG_LABELS } from '@robowiki/content'
import ratingsRaw from '@/data/ratings.json'

const DATA_REPO = 'RoboWiki/RoboWiki'
const ISSUES = `https://github.com/${DATA_REPO}/issues`

const USAGE_LABELS: Record<string, string> = {
  long: '长期用过（>6 个月）',
  short: '短期用过（<1 个月）',
  unboxed: '只开箱测过',
}

const DIM_LABELS: Record<string, string> = {
  value: '性价比',
  build: '做工',
  docs: '文档与支持',
  spec_trust: '参数可信度',
  compat: '兼容与生态',
}

type RatingData = {
  count: number
  avg: number | null
  histogram: Record<string, number>
  dims_avg?: Record<string, number> | null
  dims_n?: Record<string, number> | null
  own_hardware_count?: number | null
  own_hardware_avg?: number | null
  usage_level_counts?: Record<string, number>
  reason_tag_counts?: Record<string, number>
  review_count?: number
}

type Snapshot = { parts?: Record<string, RatingData>; total_ratings?: number }

function Stars({ value }: { value: number }) {
  return (
    <span className="flex items-center gap-0.5" aria-hidden="true">
      {[1, 2, 3, 4, 5].map(n => (
        <span key={n} className={n <= Math.round(value) ? 'text-warning' : 'text-line-strong'}>★</span>
      ))}
    </span>
  )
}

export default function RatingSummary({ partId }: { partId: string; category?: string | null }) {
  const data = ((ratingsRaw as Snapshot).parts || {})[partId]
  const count = Math.max(0, Number(data?.count) || 0)
  const avg = typeof data?.avg === 'number' && Number.isFinite(data.avg) ? data.avg : null
  const hasRating = count > 0 && avg !== null
  const histogram = data?.histogram || {}
  const reviewCount = Math.max(0, Number(data?.review_count) || 0)
  const ownCount = Number(data?.own_hardware_count) || 0
  const ownAvg = typeof data?.own_hardware_avg === 'number' ? data.own_hardware_avg : null
  const usageCounts = Object.entries(data?.usage_level_counts || {}).sort((a, b) => b[1] - a[1])
  const tagCounts = Object.entries(data?.reason_tag_counts || {}).sort((a, b) => b[1] - a[1]).slice(0, 6)

  const rateHref = `${ISSUES}/new?template=rate-part.yml&title=${encodeURIComponent(`[评分] ${partId}`)}`
  const reviewHref = `${ISSUES}/new?template=review-part.yml&title=${encodeURIComponent(`[实测] ${partId}`)}`
  const issueHref = `${ISSUES}?q=${encodeURIComponent(`is:issue (label:rating OR label:review) ${partId}`)}`
  const reviewCountHref = `${ISSUES}?q=${encodeURIComponent(`is:issue label:review ${partId}`)}`

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold tabular-nums text-ink">{hasRating ? avg!.toFixed(1) : '—'}</span>
            <span className="text-xs text-ink-3">/ 5</span>
          </div>
          <p className="mt-1 text-xs text-ink-3">
            {hasRating ? `${count} 人评分` : '暂无评分样本'}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {reviewCount > 0 && (
              <a href={reviewCountHref} target="_blank" rel="noopener"
                className="inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline">
                {reviewCount} 条实测<span aria-hidden="true">→</span>
              </a>
            )}
            <a href={rateHref} target="_blank" rel="noopener"
              className="inline-flex min-h-11 items-center gap-1 rounded-md border border-line bg-surface px-2.5 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink sm:min-h-8">
              写评分<span aria-hidden="true">↗</span>
            </a>
            <a href={reviewHref} target="_blank" rel="noopener"
              className="inline-flex min-h-11 items-center gap-1 rounded-md px-2 text-xs font-medium text-ink-3 transition-colors hover:text-ink sm:min-h-8">
              写实测<span aria-hidden="true">↗</span>
            </a>
          </div>
        </div>
        {hasRating && count < 3 && <Badge variant="warning">样本不足</Badge>}
      </div>

      {hasRating ? (
        <>
          <div className="flex items-center gap-2">
            <Stars value={avg!} />
            <span className="text-xs text-ink-3">
              平均 <span className="font-medium tabular-nums text-ink-2">{avg!.toFixed(1)}</span> 分
            </span>
            {ownCount > 0 && ownAvg !== null && (
              <span className="text-xs text-ink-3">
                · 自有硬件 {ownAvg.toFixed(1)} 分（{ownCount} 人）
              </span>
            )}
          </div>
          <ul className="space-y-1.5" aria-label="评分分布">
            {[5, 4, 3, 2, 1].map(score => {
              const n = Number(histogram[String(score)]) || 0
              const pct = count ? Math.round((n / count) * 100) : 0
              return (
                <li key={score} className="flex items-center gap-2 text-xs text-ink-3">
                  <span className="w-7 shrink-0 tabular-nums">{score} 星</span>
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-3" aria-hidden="true">
                    <span className="block h-full rounded-full bg-brand" style={{ width: `${pct}%` }} />
                  </span>
                  <span className="w-16 shrink-0 text-right tabular-nums">{n} 人 · {pct}%</span>
                  <span className="sr-only">{score} 星 {n} 人，占 {pct}%</span>
                </li>
              )
            })}
          </ul>
        </>
      ) : (
        <p className="rounded-lg bg-surface-2 p-3 text-xs leading-5 text-ink-3">
          还没有人留下真实使用评分。评分和实测都在 GitHub Issue 里收集；本站不保存账号、邮箱或密码。
        </p>
      )}

      {(usageCounts.length > 0 || tagCounts.length > 0) && (
        <div className="space-y-2.5 border-t border-line pt-3">
          {usageCounts.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold tracking-wide text-ink-3">使用时长</h3>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {usageCounts.map(([key, n]) => (
                  <span key={key} className="rounded-full border border-line bg-surface-2 px-2 py-0.5 text-xs text-ink-2">
                    {USAGE_LABELS[key] ?? key}
                    <span className="mono tabular ml-1 text-ink-3">{n}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
          {tagCounts.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold tracking-wide text-ink-3">评价理由</h3>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {tagCounts.map(([key, n]) => (
                  <span key={key} className="rounded-full border border-line bg-surface px-2 py-0.5 text-xs text-ink-2">
                    {TAG_LABELS[key] ?? key}
                    <span className="mono tabular ml-1 text-ink-3">{n}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {data?.dims_avg && Object.keys(data.dims_avg).length > 0 && (
        <dl className="grid grid-cols-2 gap-2" aria-label="分维度评分">
          {Object.entries(data.dims_avg).map(([key, value]) => (
            <div key={key} className="rounded-lg border border-line bg-surface-2/60 p-2">
              <dt className="text-xs text-ink-3">{DIM_LABELS[key] || key}</dt>
              <dd className="mt-0.5 text-sm font-semibold tabular-nums text-ink">
                {Number(value).toFixed(1)}<span className="text-xs font-normal text-ink-3">/{data.dims_n?.[key] ?? '—'}</span>
              </dd>
            </div>
          ))}
        </dl>
      )}

      <div className="border-t border-line pt-3 text-xs leading-5 text-ink-3">
        评分与实测由 GitHub Issue 收集，按 GitHub 账号去重；
        <a href={issueHref} target="_blank" rel="noopener" className="font-medium text-brand hover:underline">
          查看全部 issue
        </a>
        。本站不提供站内登录，也不保存密码或邮箱。
      </div>
    </div>
  )
}
