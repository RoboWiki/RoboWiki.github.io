import 'antd/dist/reset.css'
import { Table } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { api, siteHref, type User } from '@/lib/community-api'
import { CommunityHeader, IslandProvider } from './providers'
import { EmptyState, UserBadge } from './ui'

function Rank({ index }: { index: number }) {
  const top = index < 3
  return (
    <span
      className={`mono tabular inline-grid h-6 w-6 place-items-center rounded-full text-[11.5px] ${
        top ? 'bg-brand-soft font-semibold text-brand' : 'text-ink-3'
      }`}>
      {index + 1}
    </span>
  )
}

function NumberCell({ value }: { value?: number }) {
  return <span className="mono tabular text-[12.5px] text-ink-2">{value ?? 0}</span>
}

function Leaderboard() {
  const board = useQuery({ queryKey: ['leaderboard', 30], queryFn: () => api.leaderboard(30) })
  const rows = board.data || []

  return (
    <div>
      <CommunityHeader current="top" />

      <section className="card overflow-hidden">
        <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line px-4 py-3">
          <h2 className="m-0 text-[13px] font-semibold text-ink">按声望排序</h2>
          <p className="m-0 text-[11.5px] text-ink-3">
            共 <span className="mono tabular text-ink-2">{rows.length}</span> 位成员
          </p>
        </header>

        {board.isError ? (
          <div className="p-4">
            <EmptyState
              title="榜单加载失败"
              hint={(board.error as Error).message}
              action={
                <button type="button" onClick={() => board.refetch()}
                  className="inline-flex h-9 items-center rounded-md border border-line bg-surface px-3.5 text-[13px] text-ink-2 transition-colors hover:border-line-strong hover:text-ink">
                  重试
                </button>
              }
            />
          </div>
        ) : (
          <Table<User>
            size="small"
            rowKey="id"
            pagination={false}
            loading={board.isLoading}
            dataSource={rows}
            scroll={{ x: 620 }}
            locale={{
              emptyText: (
                <div className="py-8 text-[12.5px] text-ink-3">还没有排名数据。</div>
              ),
            }}
            columns={[
              {
                title: '#', width: 60, align: 'center',
                render: (_v, _r, i) => <Rank index={i} />,
              },
              {
                title: '成员',
                render: (_v, u) => (
                  <a href={siteHref(`/u.html?handle=${encodeURIComponent(u.handle)}`)}
                    className="block min-w-0 hover:text-brand">
                    <UserBadge user={u} />
                    <span className="mono ml-[26px] block text-[11px] text-ink-3">@{u.handle}</span>
                  </a>
                ),
              },
              {
                title: '声望', dataIndex: 'reputation', width: 90, align: 'right',
                render: v => <span className="mono tabular text-[13px] font-semibold text-ink">{v ?? 0}</span>,
              },
              { title: '帖子', dataIndex: 'post_count', width: 80, align: 'right', render: v => <NumberCell value={v} /> },
              { title: '评论', dataIndex: 'comment_count', width: 80, align: 'right', render: v => <NumberCell value={v} /> },
              {
                title: '徽章', width: 180,
                render: (_v, u) => (
                  <span className="flex flex-wrap gap-1">
                    {u.is_staff && (
                      <span className="inline-flex items-center rounded-full border border-line bg-warning-soft px-2 py-0.5 text-[11px] font-medium text-warning">
                        站务
                      </span>
                    )}
                    {u.badges?.map(b => (
                      <span key={b}
                        className="inline-flex items-center rounded-full border border-line bg-brand-soft px-2 py-0.5 text-[11px] font-medium text-brand">
                        {b}
                      </span>
                    ))}
                    {!u.badges?.length && !u.is_staff && (
                      <span className="text-[11.5px] text-ink-3">—</span>
                    )}
                  </span>
                ),
              },
            ]}
          />
        )}
      </section>

      <p className="mt-3 text-[11.5px] leading-5 text-ink-3">
        声望 = 收到的赞之和。写实测、回答问题都会涨；被隐藏的内容不计分。
      </p>
    </div>
  )
}

export default function LeaderboardIsland() {
  return (
    <IslandProvider>
      <Leaderboard />
    </IslandProvider>
  )
}
