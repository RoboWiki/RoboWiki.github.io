import 'antd/dist/reset.css'
import { StarOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/community-api'
import { CommunityHeader, IslandProvider } from './providers'
import { Avatar, EmptyState, PostCard, PostSkeleton } from './ui'

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-line bg-surface-2 px-2 py-2 text-center">
      <div className="mono tabular text-[18px] font-semibold leading-tight text-ink">{value}</div>
      <div className="mt-1 text-xs text-ink-3">{label}</div>
    </div>
  )
}

function Profile({ handle }: { handle: string }) {
  const u = useQuery({ queryKey: ['user', handle], queryFn: () => api.user(handle), retry: false })
  const posts = useQuery({
    queryKey: ['posts', 'by', handle],
    queryFn: () => api.posts({ author: handle, limit: 30 }),
    enabled: u.isSuccess,
  })

  const user = u.data

  return (
    <div>
      <CommunityHeader current="top" />

      {u.isLoading ? (
        <div className="grid animate-pulse gap-6 lg:grid-cols-[280px_minmax(0,1fr)]" aria-hidden="true">
          <div className="card h-64" />
          <div className="space-y-3">
            <div className="h-5 w-28 rounded bg-surface-3" />
            <PostSkeleton />
            <PostSkeleton />
          </div>
        </div>
      ) : !user ? (
        <EmptyState
          title="用户不存在"
          hint={u.error ? (u.error as Error).message : '链接里的用户名可能拼错了。'}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="min-w-0">
            <section className="card p-4">
              <div className="flex items-center gap-3">
                <Avatar user={user} size={54} />
                <div className="min-w-0">
                  <h1 className="m-0 truncate text-[20px] font-bold tracking-tight text-ink">
                    {user.display_name}
                  </h1>
                  <p className="mono m-0 truncate text-xs text-ink-3">@{user.handle}</p>
                </div>
              </div>

              {user.bio && (
                <p className="mb-0 mt-3 whitespace-pre-wrap text-sm leading-6 text-ink-2">{user.bio}</p>
              )}

              <div className="mt-3 grid grid-cols-3 gap-2">
                <Stat label="声望" value={user.reputation} />
                <Stat label="帖子" value={user.post_count} />
                <Stat label="评论" value={user.comment_count} />
                <Stat label="评分" value={user.rating_count ?? 0} />
                <Stat label="投稿" value={user.submission_count ?? 0} />
                <Stat label="采纳" value={user.accepted_count ?? 0} />
              </div>

              {(user.badges?.length > 0 || user.is_staff) && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {user.is_staff && (
                    <span className="inline-flex items-center rounded-full border border-line bg-warning-soft px-2 py-1 text-xs font-medium text-warning">
                      站务
                    </span>
                  )}
                  {user.badges?.map(b => (
                    <span key={b}
                      className="inline-flex items-center rounded-full border border-line bg-brand-soft px-2 py-1 text-xs font-medium text-brand">
                      {b}
                    </span>
                  ))}
                </div>
              )}

              <p className="mb-0 mt-3 border-t border-line pt-3 text-xs text-ink-3">
                加入于 <span className="mono tabular">{new Date(user.created_at).toLocaleDateString('zh-CN')}</span>
              </p>
            </section>
          </aside>

          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2 border-b border-line pb-2">
              <h2 className="m-0 flex items-center gap-2 text-base font-semibold text-ink">
                <StarOutlined className="text-ink-3" aria-hidden="true" />
                最近活动
                <span className="mono tabular text-sm font-normal text-ink-3">
                  ({posts.data?.total ?? 0})
                </span>
              </h2>
              <span className="text-xs text-ink-3">最近的帖子与评价</span>
            </div>
            {posts.isLoading ? (
              <>
                <PostSkeleton />
                <PostSkeleton />
              </>
            ) : posts.data?.items?.length ? (
              posts.data.items.map(p => <PostCard key={p.id} post={p} />)
            ) : (
              <EmptyState title="还没发过帖" hint="写一条实测，就能挂到对应的零件上。" />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function ProfileIsland({ handle }: { handle: string }) {
  return (
    <IslandProvider>
      <Profile handle={handle} />
    </IslandProvider>
  )
}
