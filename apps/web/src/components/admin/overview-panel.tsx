import { Alert, Skeleton } from 'antd'
import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { api, siteHref, type AdminOverview } from '@/lib/community-api'

const num = (n: number) => n.toLocaleString('zh-CN')
const pct = (n: number) => `${n.toFixed(1)}%`
const when = (iso: string) => iso.slice(0, 16).replace('T', ' ')

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-lg border border-line bg-surface-2 px-3 py-2.5">
      <div className="text-xs uppercase tracking-wider text-ink-3">{label}</div>
      <div className="mono tabular mt-0.5 text-[20px] font-semibold text-ink">{value}</div>
      <div className="mt-0.5 text-xs leading-5 text-ink-3">{hint}</div>
    </div>
  )
}

function Coverage({ label, value, detail }: { label: string; value: number; detail: string }) {
  const width = Math.max(0, Math.min(100, value))
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 text-xs">
        <span className="font-medium text-ink-2">{label}</span>
        <span className="mono tabular text-ink">{pct(value)}</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-3" role="presentation">
        <div className="h-full rounded-full bg-brand" style={{ width: `${width}%` }} />
      </div>
      <div className="mt-1 text-xs leading-5 text-ink-3">{detail}</div>
    </div>
  )
}

function Trend({ data }: { data: AdminOverview['trend'] }) {
  const max = Math.max(1, ...data.flatMap(d => [d.posts, d.comments, d.ratings]))
  const rows: { key: 'posts' | 'comments' | 'ratings'; label: string; tone: string }[] = [
    { key: 'posts', label: '发帖', tone: 'bg-brand' },
    { key: 'comments', label: '评论', tone: 'bg-success' },
    { key: 'ratings', label: '评分', tone: 'bg-warning' },
  ]
  return (
    <section className="card p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="m-0 text-sm font-semibold text-ink">近 14 天社区活跃</h2>
        <span className="text-xs text-ink-3">按 UTC 自然日；柱高按三项中的最大值归一</span>
      </div>
      <div className="mt-3 space-y-3">
        {rows.map(row => (
          <div key={row.key}>
            <div className="mb-1 flex items-center justify-between text-xs text-ink-3">
              <span>{row.label}</span>
              <span className="mono tabular">
                近 7 天 {num(data.slice(-7).reduce((s, d) => s + d[row.key], 0))}
              </span>
            </div>
            <div className="flex h-10 items-end gap-1" aria-hidden="true">
              {data.map(d => (
                <div
                  key={d.date}
                  title={`${d.date} ${row.label} ${d[row.key]}`}
                  className={`min-h-[3px] flex-1 rounded-sm ${row.tone} ${d[row.key] ? 'opacity-90' : 'opacity-25'}`}
                  style={{ height: `${Math.max(3, (d[row.key] / max) * 100)}%` }}
                />
              ))}
            </div>
          </div>
        ))}
        <div className="flex justify-between text-[11px] text-ink-3">
          <span>{data[0]?.date}</span>
          <span>{data[Math.floor(data.length / 2)]?.date}</span>
          <span>{data[data.length - 1]?.date}</span>
        </div>
      </div>
    </section>
  )
}

function ListCard({ title, hint, children }: {
  title: string; hint?: string; children: ReactNode
}) {
  return (
    <section className="card p-4">
      <div className="mb-2">
        <h2 className="m-0 text-sm font-semibold text-ink">{title}</h2>
        {hint && <p className="m-0 mt-0.5 text-xs leading-5 text-ink-3">{hint}</p>}
      </div>
      {children}
    </section>
  )
}

export default function OverviewPanel({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const q = useQuery({
    queryKey: ['admin-overview'],
    queryFn: () => api.adminOverview(),
    staleTime: 30_000,
  })

  if (q.isPending) return <Skeleton active paragraph={{ rows: 10 }} />
  if (q.isError) {
    return (
      <Alert type="error" showIcon
        message="运营总览加载失败"
        description={q.error instanceof Error ? q.error.message : '请稍后重试'}
        action={<button type="button" className="chip h-8 px-3 text-xs" onClick={() => q.refetch()}>重试</button>}
      />
    )
  }

  const d = q.data
  const gapTotal = d.data_quality.no_image + d.data_quality.no_price

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="m-0 text-base font-semibold text-ink">社区运营总览</h2>
          <p className="m-0 mt-0.5 text-xs text-ink-3">
            数据来自站内库，不含流量日志；生成于 {when(d.generated_at)}
          </p>
        </div>
        <button type="button" className="chip h-8 px-3 text-xs" onClick={() => q.refetch()}
          disabled={q.isFetching}>
          {q.isFetching ? '刷新中…' : '刷新'}
        </button>
      </div>

      <section className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5" aria-label="运营待办">
        {d.actions.map(a => {
          const inner = (
            <>
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xs font-medium text-ink-2">{a.label}</span>
                <span className={`mono tabular text-[18px] font-semibold ${a.count ? 'text-warning' : 'text-brand'}`}>
                  {num(a.count)}
                </span>
              </div>
              <p className="m-0 mt-1 text-xs leading-5 text-ink-3">{a.hint}</p>
            </>
          )
          const cls = 'rounded-lg border border-line bg-surface px-3 py-2.5 text-left transition-colors hover:border-line-strong hover:bg-surface-2'
          if (a.tab) {
            return <button key={a.key} type="button" className={cls} onClick={() => onNavigate(a.tab as string)}>{inner}</button>
          }
          if (a.href) {
            return <a key={a.key} href={a.href} className={cls}>{inner}</a>
          }
          return <div key={a.key} className={cls}>{inner}</div>
        })}
      </section>

      <section className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4" aria-label="核心指标">
        <Stat
          label="用户"
          value={num(d.users.total)}
          hint={`7 天新增 ${num(d.users.new_7d)} · 7 天活跃 ${num(d.users.active_7d)} · 站务 ${num(d.users.staff)} · 封禁 ${num(d.users.banned)}`}
        />
        <Stat
          label="内容"
          value={num(d.content.posts)}
          hint={`7 天 +${num(d.content.posts_7d)} · 讨论 ${num(d.content.discussions)} · 评价 ${num(d.content.reviews)} · 整机 ${num(d.content.builds)}`}
        />
        <Stat
          label="评论 / 评分"
          value={`${num(d.content.comments)} / ${num(d.content.ratings)}`}
          hint={`7 天新增评论 ${num(d.content.comments_7d)} · 评分 ${num(d.content.ratings_7d)} · 平均每帖 ${d.engagement.comments_per_post.toFixed(2)} 条评论`}
        />
        <Stat
          label="治理"
          value={num(d.moderation.open_reports)}
          hint={`待处理举报 · 待审投稿 ${num(d.moderation.pending_submissions)} · 7 天举报 ${num(d.moderation.reports_7d)} · 隐藏 ${num(d.moderation.hidden_posts + d.moderation.hidden_comments)} · 锁定 ${num(d.moderation.locked_posts)}`}
        />
      </section>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Trend data={d.trend} />
        <section className="card p-4">
          <h2 className="m-0 text-sm font-semibold text-ink">共建完成度</h2>
          <p className="m-0 mt-0.5 text-xs leading-5 text-ink-3">
            解决率按讨论帖是否采纳回答；覆盖率按全部零件中有评分/评价的比例。
          </p>
          <div className="mt-3 space-y-3">
            <Coverage label="讨论解决率" value={d.engagement.solve_rate}
              detail={`${num(d.engagement.solved_discussions)} / ${num(d.content.discussions)} 个讨论帖已采纳答案`} />
            <Coverage label="评分覆盖率" value={d.engagement.rating_coverage}
              detail={`${num(d.engagement.parts_with_ratings)} / ${num(d.engagement.parts)} 个零件至少有一条评分`} />
            <Coverage label="长评覆盖率" value={d.engagement.review_coverage}
              detail={`${num(d.engagement.parts_with_reviews)} / ${num(d.engagement.parts)} 个零件有评价帖`} />
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 border-t border-line pt-3 text-xs text-ink-3">
            <div>缺产品图 <span className="mono tabular text-warning">{num(d.data_quality.no_image)}</span></div>
            <div>缺报价 <span className="mono tabular text-warning">{num(d.data_quality.no_price)}</span></div>
            <div>缺来源 <span className="mono tabular text-warning">{num(d.data_quality.no_url)}</span></div>
            <div>未核对 <span className="mono tabular text-warning">{num(d.data_quality.unverified)}</span></div>
          </div>
          {gapTotal > 0 && (
            <button type="button" className="mt-2 text-xs font-medium text-brand hover:underline"
              onClick={() => onNavigate('gaps')}>
              去数据缺口处理 →
            </button>
          )}
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ListCard title="近 30 天活跃贡献者" hint="发帖 ×3 + 评论 ×2 + 评分 ×1，仅作活跃度参考">
          {!d.top_contributors.length ? (
            <p className="m-0 text-xs text-ink-3">近 30 天还没有新贡献。</p>
          ) : (
            <ol className="m-0 list-none space-y-2 p-0">
              {d.top_contributors.map((u, i) => (
                <li key={u.handle} className="flex items-center gap-2 text-xs">
                  <span className="mono w-4 shrink-0 text-ink-3">{i + 1}</span>
                  <a href={siteHref(`/u/${encodeURIComponent(u.handle)}.html`)}
                    className="min-w-0 flex-1 truncate font-medium text-ink hover:text-brand">
                    {u.display_name || u.handle}
                    <span className="ml-1 text-ink-3">@{u.handle}</span>
                  </a>
                  <span className="mono tabular shrink-0 text-ink-3">
                    {u.posts} 帖 · {u.comments} 评 · {u.ratings} 分
                  </span>
                  <span className="mono tabular w-8 shrink-0 text-right font-semibold text-brand">{u.score}</span>
                </li>
              ))}
            </ol>
          )}
        </ListCard>

        <ListCard title="热门帖子" hint="按浏览量排序；看社区真正被读的内容">
          {!d.top_posts.length ? (
            <p className="m-0 text-xs text-ink-3">还没有帖子。</p>
          ) : (
            <ol className="m-0 list-none space-y-2 p-0">
              {d.top_posts.map(p => (
                <li key={p.id} className="flex items-baseline gap-2 text-xs">
                  <a href={siteHref(`/post.html?id=${p.id}`)}
                    className="min-w-0 flex-1 truncate text-ink-2 hover:text-brand">{p.title}</a>
                  <span className="mono tabular shrink-0 text-ink-3">
                    {num(p.view_count)} 阅 · {p.comment_count} 评 · {p.score} 分
                  </span>
                </li>
              ))}
            </ol>
          )}
        </ListCard>

        <ListCard title="热门零件（按评分数）" hint="有评分的零件；评价数单独列出，避免把打分当长评">
          {!d.top_parts.length ? (
            <p className="m-0 text-xs text-ink-3">还没有评分。</p>
          ) : (
            <ol className="m-0 list-none space-y-2 p-0">
              {d.top_parts.map(p => (
                <li key={p.id} className="flex items-baseline gap-2 text-xs">
                  <a href={siteHref(`/search.html?q=${encodeURIComponent(p.model)}`)}
                    className="min-w-0 flex-1 truncate text-ink-2 hover:text-brand">
                    {p.model} <span className="text-ink-3">{p.vendor}</span>
                  </a>
                  <span className="mono tabular shrink-0 text-ink-3">
                    {p.rating_avg.toFixed(1)} 分 · {p.rating_count} 票 · {p.review_count} 评
                  </span>
                </li>
              ))}
            </ol>
          )}
        </ListCard>

        <ListCard title="热门零件缺长评" hint="评分 ≥3 但还没有评价帖；优先邀请这些零件的评分者补充体验">
          {!d.zero_review_parts.length ? (
            <p className="m-0 text-xs text-ink-3">没有明显缺口。</p>
          ) : (
            <ol className="m-0 list-none space-y-2 p-0">
              {d.zero_review_parts.map(p => (
                <li key={p.id} className="flex items-baseline gap-2 text-xs">
                  <a href={siteHref(`/community.html?kind=review&part=${encodeURIComponent(p.id)}`)}
                    className="min-w-0 flex-1 truncate text-ink-2 hover:text-brand">
                    {p.model} <span className="text-ink-3">{p.vendor}</span>
                  </a>
                  <span className="mono tabular shrink-0 text-ink-3">
                    {p.rating_avg.toFixed(1)} 分 · {p.rating_count} 票
                  </span>
                  <span className="shrink-0 text-xs font-medium text-brand">去邀请</span>
                </li>
              ))}
            </ol>
          )}
        </ListCard>
      </div>
    </div>
  )
}
