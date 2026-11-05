import 'antd/dist/reset.css'
import { Card, Table, Tag } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { api, siteHref, type User } from '@/lib/community-api'
import { CommunityHeader, IslandProvider } from './providers'
import { UserBadge } from './ui'

function Leaderboard() {
  const board = useQuery({ queryKey: ['leaderboard', 30], queryFn: () => api.leaderboard(30) })

  return (
    <div>
      <CommunityHeader current="top" />
      <Card>
        <Table<User>
          size="small"
          rowKey="id"
          pagination={false}
          loading={board.isLoading}
          dataSource={board.data || []}
          scroll={{ x: 620 }}
          columns={[
            { title: '#', width: 56, render: (_v, _r, i) => i + 1 },
            {
              title: '成员',
              render: (_v, u) => (
                <a href={siteHref(`/u.html?handle=${encodeURIComponent(u.handle)}`)}><UserBadge user={u} /></a>
              ),
            },
            { title: '声望', dataIndex: 'reputation', width: 90, align: 'right' },
            { title: '帖子', dataIndex: 'post_count', width: 80, align: 'right' },
            { title: '评论', dataIndex: 'comment_count', width: 80, align: 'right' },
            {
              title: '徽章',
              render: (_v, u) => (
                <span className="flex flex-wrap gap-1">
                  {u.badges?.map(b => <Tag key={b} color="blue">{b}</Tag>)}
                </span>
              ),
            },
          ]}
        />
      </Card>
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
