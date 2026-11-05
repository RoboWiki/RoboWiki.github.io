import 'antd/dist/reset.css'
import { Card, Empty, Skeleton, Space, Tag, Typography } from 'antd'
import { StarOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/community-api'
import { CommunityHeader, IslandProvider } from './providers'
import { PostCard } from './ui'

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

      {u.isLoading ? <Skeleton active /> : !user ? (
        <Empty description={`用户不存在${u.error ? `：${(u.error as Error).message}` : ''}`} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="min-w-0">
            <Card>
              <Space orientation="vertical" size={12} style={{ width: '100%' }}>
                <Space size={12}>
                  <span className="inline-flex h-[54px] w-[54px] items-center justify-center rounded-full bg-blue-600 text-[22px] font-bold text-white">
                    {user.display_name.slice(0, 1)}
                  </span>
                  <div className="min-w-0">
                    <Typography.Title level={1} style={{ margin: 0, fontSize: 20 }}>{user.display_name}</Typography.Title>
                    <Typography.Text type="secondary">@{user.handle}</Typography.Text>
                  </div>
                </Space>
                {user.bio && (
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>{user.bio}</Typography.Paragraph>
                )}
                <div className="grid grid-cols-3 gap-2 text-center">
                  {[
                    { label: '声望', value: user.reputation },
                    { label: '帖子', value: user.post_count },
                    { label: '评论', value: user.comment_count },
                  ].map(s => (
                    <div key={s.label} className="rounded-lg bg-slate-50 py-2">
                      <div className="text-[17px] font-semibold tabular-nums text-slate-900">{s.value}</div>
                      <div className="text-[11px] text-slate-500">{s.label}</div>
                    </div>
                  ))}
                </div>
                <Space wrap size={4}>
                  {user.badges?.map(b => <Tag key={b} color="blue">{b}</Tag>)}
                  {user.is_staff && <Tag color="gold">站务</Tag>}
                </Space>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  加入于 {new Date(user.created_at).toLocaleDateString('zh-CN')}
                </Typography.Text>
              </Space>
            </Card>
          </aside>

          <div className="min-w-0">
            <Typography.Title level={2} style={{ fontSize: 16 }}>
              <StarOutlined /> 帖子（{posts.data?.total ?? 0}）
            </Typography.Title>
            {posts.isLoading ? <Skeleton active /> :
              posts.data?.items?.length
                ? posts.data.items.map(p => <PostCard key={p.id} post={p} />)
                : <Empty description="还没发过帖" />}
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
