import 'antd/dist/reset.css'
import { Pagination } from 'antd'
import { FireOutlined, HistoryOutlined, TagsOutlined, TrophyOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, siteHref } from '@/lib/community-api'
import {
  clearActivity, loadActivity, subscribeActivity, type LocalActivityItem,
} from '@/lib/local-activity'
import { CommunityHeader, IslandProvider, useAuth } from './providers'
import {
  Composer, EmptyState, PostCard, PostSkeleton, UserBadge, ago,
  type ComposerPrefill,
} from './ui'

const PAGE_SIZE = 10
type Sort = 'new' | 'hot' | 'top'
type Solved = 'all' | 'open' | 'solved'

const KINDS: { value: string; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'discussion', label: '讨论' },
  { value: 'review', label: '评价' },
  { value: 'build', label: '整机方案' },
]

const SOLVED: { value: Solved; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'open', label: '待解决' },
  { value: 'solved', label: '已解决' },
]

const SORTS: { value: Sort; label: string; icon?: ReactNode }[] = [
  { value: 'new', label: '最新' },
  { value: 'hot', label: '热门', icon: <FireOutlined /> },
  { value: 'top', label: '最高分' },
]

/** 只存在本机的「我发过什么」：避免自己翻页找，也不上服务器。 */
function LocalActivityPanel() {
  const [items, setItems] = useState<LocalActivityItem[]>([])

  useEffect(() => {
    const sync = () => setItems(loadActivity())
    sync()
    return subscribeActivity(sync)
  }, [])

  return (
    <section className="card p-4">
      <header className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h2 className="m-0 flex items-center gap-1.5 text-sm font-semibold text-ink">
          <HistoryOutlined className="text-ink-3" aria-hidden="true" /> 本地发言记录
        </h2>
        {items.length > 0 && (
          <button type="button" onClick={() => clearActivity()}
            className="inline-flex min-h-8 items-center rounded px-1 text-xs text-ink-3 transition-colors hover:text-danger">
            清空本地记录
          </button>
        )}
      </header>

      {!items.length ? (
        <p className="m-0 text-xs leading-5 text-ink-3">
          还没有记录。发帖或评论后会出现在这里，只保存在本机浏览器。
        </p>
      ) : (
        <ol className="m-0 list-none space-y-1.5 p-0">
          {items.map(item => (
            <li key={item.id} className="flex items-baseline gap-1.5 text-xs">
              <span aria-hidden="true" className={`mono shrink-0 rounded border border-line px-1 text-[11px] ${
                item.kind === 'post' ? 'bg-surface-2 text-ink-3' : 'bg-brand-soft text-brand'
              }`}>
                {item.kind === 'post' ? '帖' : '评'}
              </span>
              <a href={item.href} title={item.title}
                className="min-w-0 flex-1 truncate text-ink-2 transition-colors hover:text-brand">
                {item.title}
              </a>
              <span className="mono shrink-0 text-ink-3">{ago(item.at)}</span>
            </li>
          ))}
        </ol>
      )}

      <p className="mb-0 mt-2 text-[11px] leading-4 text-ink-3">只在这台设备可见，不上传服务器。</p>
    </section>
  )
}

/** 零件页「写评价」入口：`?kind=review&part=<partId>`。 */
function readComposerPrefill(): ComposerPrefill | null {
  if (typeof window === 'undefined') return null
  const sp = new URLSearchParams(window.location.search)
  if (sp.get('kind') !== 'review') return null
  const partId = (sp.get('part') || '').trim()
  return partId ? { kind: 'review', partId } : null
}

function Feed({ initialSort }: { initialSort: Sort }) {
  const { user, openAuth } = useAuth()
  const [kind, setKind] = useState('all')
  const [solved, setSolved] = useState<Solved>('all')
  const [sort, setSort] = useState<Sort>(initialSort)
  const [tag, setTag] = useState('')
  const [page, setPage] = useState(1)
  const [prefill, setPrefill] = useState<ComposerPrefill | null>(() => readComposerPrefill())
  const [composerOpen, setComposerOpen] = useState(() => readComposerPrefill() !== null)

  const query = useMemo(() => ({
    kind: kind === 'all' ? undefined : kind,
    tag: tag || undefined,
    // 仅讨论（以及包含讨论的「全部」）有解决状态；评价/整机方案不显示这组筛选。
    solved: (kind === 'all' || kind === 'discussion') && solved !== 'all'
      ? (solved === 'solved' ? 'true' : 'false')
      : undefined,
    sort, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE,
  }), [kind, tag, solved, sort, page])

  const posts = useQuery({ queryKey: ['posts', query], queryFn: () => api.posts(query) })
  const board = useQuery({ queryKey: ['leaderboard', 6], queryFn: () => api.leaderboard(6) })
  // 标签聚合失败时静默隐藏，不能阻断信息流。
  const tags = useQuery({
    queryKey: ['tags', kind, 20],
    queryFn: () => api.tags({ kind: kind === 'all' ? undefined : kind, limit: 20 }),
    retry: false,
    staleTime: 60_000,
  })
  const hotTags = tags.data?.items?.slice(0, 20) ?? []

  const selectTag = (next: string) => {
    setTag(prev => prev === next ? '' : next)
    setPage(1)
  }

  const clearTag = () => {
    setTag('')
    setPage(1)
  }

  // 关窗即清掉 URL 参数，避免刷新后再次自动弹出。
  const closeComposer = () => {
    setComposerOpen(false)
    if (!prefill) return
    setPrefill(null)
    if (typeof window === 'undefined') return
    const url = new URL(window.location.href)
    url.searchParams.delete('kind')
    url.searchParams.delete('part')
    window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`)
  }

  // 接口挂住时不要无限转圈：超时后给明确状态 + 重试，避免“正文一片空”。
  const [stalled, setStalled] = useState(false)
  useEffect(() => {
    if (!posts.isPending) { setStalled(false); return }
    const timer = window.setTimeout(() => setStalled(true), 8000)
    return () => window.clearTimeout(timer)
  }, [posts.isPending])

  const total = posts.data?.total ?? 0
  const failed = posts.isError || stalled

  return (
    <div>
      <CommunityHeader current="community" onCompose={() => setComposerOpen(true)} />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0">
          {/* 筛选与排序同一行：窄屏筛选横滑，排序固定在右侧 */}
          <div className="mb-3 flex flex-wrap items-center gap-2 border-b border-line pb-3">
            <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
              <div className="chip-row min-w-0" role="group" aria-label="按类型筛选">
                {KINDS.map(k => (
                  <button key={k.value} type="button" className="chip"
                    aria-pressed={kind === k.value}
                    onClick={() => {
                      setKind(k.value)
                      setSolved('all')
                      setTag('')
                      setPage(1)
                    }}>
                    {k.label}
                  </button>
                ))}
              </div>

              {(kind === 'all' || kind === 'discussion') && (
                <div className="chip-row min-w-0" role="group" aria-label="按解决状态筛选">
                  {SOLVED.map(s => (
                    <button key={s.value} type="button" className="chip"
                      aria-pressed={solved === s.value}
                      onClick={() => { setSolved(s.value); setPage(1) }}>
                      {s.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex shrink-0 items-center gap-0.5 rounded-full border border-line bg-surface-2 p-0.5"
              role="group" aria-label="排序">
              {SORTS.map(s => (
                <button key={s.value} type="button"
                  aria-pressed={sort === s.value}
                  onClick={() => { setSort(s.value); setPage(1) }}
                  className={`inline-flex h-7 items-center gap-1 rounded-full px-2.5 text-sm transition-colors ${
                    sort === s.value
                      ? 'bg-surface font-semibold text-ink shadow-xs'
                      : 'text-ink-3 hover:text-ink'
                  }`}>
                  {s.icon}{s.label}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2 text-xs text-ink-3">
            <span className="flex flex-wrap items-center gap-2">
              {tag && (
                <span className="inline-flex items-center gap-1 rounded-full border border-brand/35 bg-brand-soft px-2 py-0.5 font-medium text-brand">
                  标签：<span className="font-semibold">#{tag}</span>
                  <button type="button" onClick={clearTag} aria-label={`取消标签 ${tag}`}
                    className="rounded px-0.5 leading-none transition-colors hover:text-danger">
                    ×
                  </button>
                </span>
              )}
              <span>
                {posts.isPending && !stalled ? '加载中…' : failed ? '—' : <>
                  共 <span className="mono tabular text-ink-2">{total}</span> 帖
                </>}
              </span>
            </span>
            <span className="hidden sm:inline">评价挂在零件上，会自动出现在该零件的详情里</span>
          </div>

          {posts.isPending && !stalled ? (
            <div aria-busy="true">
              <p className="mb-2 text-xs text-ink-3">正在加载帖子…</p>
              <PostSkeleton />
              <PostSkeleton />
              <PostSkeleton />
            </div>
          ) : failed ? (
            <EmptyState
              title={posts.isError ? '帖子加载失败' : '接口没有响应'}
              hint={posts.isError
                ? (posts.error as Error).message
                : '请求超过 8 秒没有返回，可能是后端或反向代理不可达。'}
              action={
                <button type="button" onClick={() => { setStalled(false); posts.refetch() }}
                  className="inline-flex h-9 items-center rounded-md border border-line bg-surface px-3.5 text-sm text-ink-2 transition-colors hover:border-line-strong hover:text-ink">
                  重试
                </button>
              }
            />
          ) : !posts.data?.items.length ? (
            <EmptyState
              title="还没有帖子"
              hint={tag
                ? `标签 #${tag} 下还没有内容，换一个标签或清除筛选。`
                : kind === 'all'
                  ? '第一条可以从你自己的装机记录写起。'
                  : solved !== 'all'
                    ? (solved === 'open' ? '这个类型下没有待解决的讨论。' : '这个类型下还没有已解决的讨论。')
                    : '这个类型下还没有内容，换一个筛选看看。'}
              action={!user ? (
                <button type="button" onClick={openAuth}
                  className="inline-flex h-9 items-center rounded-md bg-brand px-3.5 text-sm font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
                  登录后发第一帖
                </button>
              ) : undefined}
            />
          ) : (
            posts.data.items.map(p => <PostCard key={p.id} post={p} onTag={selectTag} />)
          )}

          <div className="mt-4 flex justify-center">
            <Pagination current={page} pageSize={PAGE_SIZE} total={total}
              onChange={setPage} showSizeChanger={false} hideOnSinglePage />
          </div>
        </div>

        <aside className="min-w-0 space-y-3 lg:sticky lg:top-20 lg:self-start">
          {hotTags.length > 0 && (
            <section className="card p-4">
              <header className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h2 className="m-0 flex items-center gap-1.5 text-sm font-semibold text-ink">
                  <TagsOutlined className="text-brand" aria-hidden="true" /> 热门标签
                </h2>
                {tag && (
                  <button type="button" onClick={clearTag}
                    className="inline-flex min-h-8 items-center rounded px-1 text-xs text-ink-3 transition-colors hover:text-brand">
                    清除
                  </button>
                )}
              </header>
              <div className="chip-row" role="group" aria-label="按标签筛选">
                {hotTags.map(t => (
                  <button key={t.name} type="button" className="chip"
                    aria-pressed={tag === t.name}
                    title={`${t.count} 帖`}
                    onClick={() => selectTag(t.name)}>
                    #{t.name}
                    <span className="mono tabular text-xs opacity-70">{t.count}</span>
                  </button>
                ))}
              </div>
              {tags.data && tags.data.total > hotTags.length && (
                <p className="mb-0 mt-2 text-[11px] leading-4 text-ink-3">
                  共 {tags.data.total} 个标签，显示前 {hotTags.length} 个。
                </p>
              )}
            </section>
          )}

          <section className="card p-4">
            <header className="mb-3 flex items-center justify-between gap-2">
              <h2 className="m-0 flex items-center gap-1.5 text-sm font-semibold text-ink">
                <TrophyOutlined className="text-warning" aria-hidden="true" /> 贡献榜
              </h2>
              <a href={siteHref('/top.html')} className="text-xs text-ink-3 transition-colors hover:text-brand">
                全部 →
              </a>
            </header>

            {board.isLoading ? (
              <div className="space-y-2.5" aria-hidden="true">
                {[0, 1, 2, 3].map(i => (
                  <div key={i} className="flex animate-pulse items-center justify-between">
                    <div className="h-5 w-28 rounded bg-surface-3" />
                    <div className="h-4 w-8 rounded bg-surface-3" />
                  </div>
                ))}
              </div>
            ) : !board.data?.length ? (
              <p className="m-0 text-xs text-ink-3">还没有排名数据。</p>
            ) : (
              <ol className="m-0 list-none space-y-2 p-0">
                {board.data.map((u, i) => (
                  <li key={u.id} className="flex items-center justify-between gap-2">
                    <span className="flex min-w-0 items-center gap-2">
                      <span className="mono tabular w-4 shrink-0 text-xs text-ink-3">{i + 1}</span>
                      <a href={siteHref(`/u.html?handle=${encodeURIComponent(u.handle)}`)}
                        className="min-w-0 hover:text-brand">
                        <UserBadge user={u} size={20} />
                      </a>
                    </span>
                    <span className="mono tabular shrink-0 text-xs font-semibold text-ink-2">
                      {u.reputation}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <LocalActivityPanel />

          <section className="card p-4">
            <h2 className="m-0 text-sm font-semibold text-ink">社区怎么用</h2>
            <p className="mb-0 mt-2 text-sm leading-6 text-ink-2">
              写<strong className="font-semibold text-ink">实测</strong>比写“好用”有用：哪个关节、多大负载、跑多久、出了什么问题。
              评价挂在零件上，会自动出现在该零件的详情里。
            </p>
            {!user && (
              <button type="button" onClick={openAuth}
                className="mt-3 inline-flex h-9 w-full items-center justify-center rounded-md bg-brand text-sm font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
                加入社区
              </button>
            )}
          </section>
        </aside>
      </div>

      <Composer open={composerOpen} onClose={closeComposer} prefill={prefill} />
    </div>
  )
}

export default function CommunityFeed({ initialSort = 'new' }: { initialSort?: Sort }) {
  return (
    <IslandProvider>
      <Feed initialSort={initialSort} />
    </IslandProvider>
  )
}
