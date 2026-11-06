import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import RatingEditor from '@/components/RatingEditor'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { RatingSummary as RatingData } from '@robowiki/core'

const APP_PART_PATH = '/app/#/pages/part/index?id='
const USAGE_LABELS: Record<string, string> = {
  long: '长期用过（>6 个月）',
  short: '短期用过（<1 个月）',
  unboxed: '只开箱测过',
}
const TAG_LABELS: Record<string, string> = {
  good_value: '性价比高',
  better_than_spec: '比标称好',
  overstated: '参数虚标',
  heat: '发热/功耗',
  build_quality: '做工问题',
  docs_missing: '文档缺失',
  shipping: '发货/售后',
  not_recommend: '不推荐',
  encoder_drift: '编码器漂移',
  backlash: '背隙大',
  fake_chip: '假货/翻新',
  hard_to_solder: '封装难焊',
  calibration: '标定困难',
  drift: '漂移',
  lighting: '受光照影响',
}
const DIM_LABELS: Record<string, string> = {
  value: '性价比',
  build: '做工',
  docs: '文档与支持',
  spec_trust: '参数可信度',
  compat: '兼容与生态',
}

type State =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'ready'; data: RatingData }

function Stars({ value }: { value: number }) {
  return (
    <span className="flex items-center gap-0.5" aria-hidden="true">
      {[1, 2, 3, 4, 5].map(n => (
        <span key={n} className={n <= Math.round(value) ? 'text-warning' : 'text-line-strong'}>★</span>
      ))}
    </span>
  )
}

export default function RatingSummary({ partId }: { partId: string }) {
  const [state, setState] = useState<State>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const interactiveHref = `${typeof location === 'undefined' ? 'https://robowiki.org.cn' : location.origin}${APP_PART_PATH}${encodeURIComponent(partId)}`

  useEffect(() => {
    let alive = true
    // 重新拉取时不要退回 loading：那会把打分表单整个卸载，
    // 提交成功的提示也就跟着消失了。只在没有数据时才显示骨架。
    setState(prev => (prev.status === 'ready' ? prev : { status: 'loading' }))
    api.getRating(partId)
      .then(data => { if (alive) setState({ status: 'ready', data }) })
      .catch(() => { if (alive) setState({ status: 'error' }) })
    return () => { alive = false }
  }, [partId, attempt])

  if (state.status === 'loading') {
    return (
      <div className="space-y-3" role="status" aria-live="polite">
        <span className="sr-only">正在加载评分</span>
        <div className="h-9 w-24 animate-pulse rounded-lg bg-surface-3" aria-hidden="true" />
        <div className="h-3 w-full animate-pulse rounded bg-surface-3" aria-hidden="true" />
        <div className="h-3 w-4/5 animate-pulse rounded bg-surface-3" aria-hidden="true" />
      </div>
    )
  }

  if (state.status === 'error') {
    return (
      <div className="space-y-2" role="alert">
        <p className="text-sm leading-6 text-ink-2">评分暂时拉取不到，可能是网络或接口限制。</p>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="min-h-11 sm:min-h-8"
            onClick={() => setAttempt(v => v + 1)}
          >
            重试
          </Button>
          <a
            href={interactiveHref}
            target="_blank"
            rel="noopener"
            className="inline-flex min-h-11 items-center gap-1 rounded-lg px-2 text-xs font-medium text-blue-700 hover:bg-blue-50 sm:min-h-8"
          >
            去互动版查看<span aria-hidden="true">↗</span>
          </a>
        </div>
      </div>
    )
  }

  const { data } = state
  const count = Math.max(0, Number(data.count) || 0)
  const avg = typeof data.avg === 'number' && Number.isFinite(data.avg) ? data.avg : null
  const hasRating = count > 0 && avg !== null
  const histogram = data.histogram || {}
  const mine = data.mine ?? null
  // 新字段可能尚未出现在旧接口的 TS 类型里；缺失时整块不渲染。
  const extra = data as unknown as {
    usage_level_counts?: Record<string, number>
    reason_tag_counts?: Record<string, number>
  }
  const usageCounts = Object.entries(extra.usage_level_counts || {}).sort((a, b) => b[1] - a[1])
  const tagCounts = Object.entries(extra.reason_tag_counts || {}).sort((a, b) => b[1] - a[1]).slice(0, 6)

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
          还没有人留下真实使用评分。缺数据就是缺数据，这里不做推测，也不显示 0 分。
        </p>
      )}

      {(usageCounts.length > 0 || tagCounts.length > 0) && (
        <div className="space-y-2.5 border-t border-line pt-3">
          {usageCounts.length > 0 && (
            <div>
              <h3 className="text-[11px] font-semibold tracking-wide text-ink-3">使用时长</h3>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {usageCounts.map(([key, n]) => (
                  <span key={key} className="rounded-full border border-line bg-surface-2 px-2 py-0.5 text-[11px] text-ink-2">
                    {USAGE_LABELS[key] ?? key}
                    <span className="mono tabular ml-1 text-ink-3">{n}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
          {tagCounts.length > 0 && (
            <div>
              <h3 className="text-[11px] font-semibold tracking-wide text-ink-3">评价理由</h3>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {tagCounts.map(([key, n]) => (
                  <span key={key} className="rounded-full border border-line bg-surface px-2 py-0.5 text-[11px] text-ink-2">
                    {TAG_LABELS[key] ?? key}
                    <span className="mono tabular ml-1 text-ink-3">{n}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <RatingEditor partId={partId} onDone={() => setAttempt(v => v + 1)} />

      {data.dims_avg && Object.keys(data.dims_avg).length > 0 && (
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
      {typeof data.own_hardware_avg === 'number' && (data.own_hardware_count || 0) > 0 && (
        <p className="text-xs text-ink-3">
          装过机的人均分 <span className="font-medium text-ink-2">{data.own_hardware_avg.toFixed(1)}</span>
          （{data.own_hardware_count} 条）
        </p>
      )}

      <div className="space-y-2 rounded-lg border border-line bg-surface-2/70 p-3">
        {mine ? (
          <p className="text-xs leading-5 text-ink-2">
            你已打分 <span className="font-semibold tabular-nums">{mine.score}</span> 分
            {mine.own_hardware && <span className="text-ink-3"> · 基于自有硬件</span>}
            {mine.hidden && <span className="text-ink-3"> · 待审核</span>}
          </p>
        ) : (
          <p className="text-xs leading-5 text-ink-3">未登录或还没打分。登录互动版后可以打分、写使用备注。</p>
        )}
        <a
          href={interactiveHref}
          target="_blank"
          rel="noopener"
          className="inline-flex min-h-11 items-center gap-1 rounded-lg bg-brand px-3 text-xs font-medium text-brand-fg hover:bg-brand-hover sm:min-h-9"
        >
          去互动版评分 / 评论<span aria-hidden="true">↗</span>
          <span className="sr-only">（在 robowiki.org.cn 打开，新窗口）</span>
        </a>
      </div>
    </div>
  )
}
