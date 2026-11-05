import 'antd/dist/reset.css'
import { Button, Card, Empty, Pagination, Segmented, Skeleton, Space, Typography } from 'antd'
import { FireOutlined, TrophyOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { api, siteHref } from '@/lib/community-api'
import { CommunityHeader, IslandProvider, useAuth } from './providers'
import { Composer, PostCard, UserBadge } from './ui'

const PAGE_SIZE = 10
type Sort = 'new' | 'hot' | 'top'

function Feed({ initialSort }: { initialSort: Sort }) {
  const { user, openAuth } = useAuth()
  const [kind, setKind] = useState('all')
  const [sort, setSort] = useState<Sort>(initialSort)
  const [page, setPage] = useState(1)
  const [composerOpen, setComposerOpen] = useState(false)

  const query = useMemo(() => ({
    kind: kind === 'all' ? undefined : kind,
    sort, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE,
  }), [kind, sort, page])

  const posts = useQuery({ queryKey: ['posts', query], queryFn: () => api.posts(query) })
  const board = useQuery({ queryKey: ['leaderboard', 6], queryFn: () => api.leaderboard(6) })

  return (
    <div>
      <CommunityHeader current="community" onCompose={() => setComposerOpen(true)} />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Segmented value={kind} onChange={v => { setKind(v as string); setPage(1) }}
              options={[
                { value: 'all', label: '全部' },
                { value: 'discussion', label: '讨论' },
                { value: 'review', label: '评价' },
                { value: 'build', label: '整机方案' },
              ]} />
            <Segmented value={sort} onChange={v => { setSort(v as Sort); setPage(1) }}
              options={[
                { value: 'new', label: '最新' },
                { value: 'hot', label: <span><FireOutlined /> 热门</span> },
                { value: 'top', label: '最高分' },
              ]} />
          </div>

          {posts.isLoading ? <Skeleton active /> :
            posts.isError ? (
              <Empty description={`加载失败：${(posts.error as Error).message}`}>
                <Button onClick={() => posts.refetch()}>重试</Button>
              </Empty>
            ) : !posts.data?.items.length ? (
              <Empty description="还没有帖子">
                {!user && <Button type="primary" onClick={openAuth}>登录后发第一帖</Button>}
              </Empty>
            ) : posts.data.items.map(p => <PostCard key={p.id} post={p} />)}

          <div className="mt-4 text-center">
            <Pagination current={page} pageSize={PAGE_SIZE} total={posts.data?.total || 0}
              onChange={setPage} showSizeChanger={false} hideOnSinglePage />
          </div>
        </div>

        <aside className="min-w-0 space-y-3">
          <Card size="small" title={<span><TrophyOutlined /> 贡献榜</span>}
            extra={<a href={siteHref('/top.html')} className="text-[12px] text-blue-600">全部</a>}>
            <Space orientation="vertical" style={{ width: '100%' }} size={10}>
              {(board.data || []).map((u, i) => (
                <div key={u.id} className="flex items-center justify-between gap-2">
                  <Space size={6}>
                    <Typography.Text type="secondary" style={{ width: 16 }}>{i + 1}</Typography.Text>
                    <a href={siteHref(`/u.html?handle=${encodeURIComponent(u.handle)}`)}><UserBadge user={u} size={20} /></a>
                  </Space>
                  <Typography.Text strong>{u.reputation}</Typography.Text>
                </div>
              ))}
            </Space>
          </Card>

          <Card size="small" title="社区怎么用">
            <Typography.Paragraph type="secondary" style={{ fontSize: 13, marginBottom: 0 }}>
              写<strong>实测</strong>比写“好用”有用：哪个关节、多大负载、跑多久、出了什么问题。
              评价挂在零件上，会自动出现在该零件的详情里。
            </Typography.Paragraph>
            {!user && <Button type="primary" block style={{ marginTop: 10 }} onClick={openAuth}>加入</Button>}
          </Card>
        </aside>
      </div>

      <Composer open={composerOpen} onClose={() => setComposerOpen(false)} />
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
