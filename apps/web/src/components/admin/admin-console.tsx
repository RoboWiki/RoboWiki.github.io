import 'antd/dist/reset.css'
import { Button, Card, Result, Skeleton, Tabs } from 'antd'
import { useState } from 'react'
import { CommunityHeader, IslandProvider, useAuth } from '@/components/community/providers'
import SubmissionsPanel from './submissions-panel'
import ReportsPanel from './reports-panel'
import GapsPanel from './gaps-panel'
import UsersPanel from './users-panel'
import OverviewPanel from './overview-panel'

type TabKey = 'overview' | 'submissions' | 'reports' | 'users' | 'gaps'

function Console() {
  const { user, ready, openAuth } = useAuth()
  const [tab, setTab] = useState<TabKey>('overview')

  return (
    <div>
      <CommunityHeader current="admin" />
      {!ready ? <Skeleton active /> : !user ? (
        <Card>
          <Result
            status="403"
            title="需要先登录"
            subTitle="后台只对站务开放；请用站务账号登录后再进入。"
            extra={<Button type="primary" onClick={openAuth}>登录</Button>}
          />
        </Card>
      ) : !user.is_staff ? (
        <Card>
          <Result
            status="403"
            title="没有站务权限"
            subTitle="当前账号不是站务。权限由服务端校验，前端不缓存任何后台数据。"
            extra={<a href="/community.html"><Button>回社区</Button></a>}
          />
        </Card>
      ) : (
        <Tabs
          activeKey={tab}
          onChange={k => setTab(k as TabKey)}
          items={[
            { key: 'overview', label: '运营总览', children: <OverviewPanel onNavigate={k => setTab(k as TabKey)} /> },
            { key: 'submissions', label: '投稿审核', children: <SubmissionsPanel active={tab === 'submissions'} /> },
            { key: 'reports', label: '举报处置', children: <ReportsPanel active={tab === 'reports'} /> },
            { key: 'users', label: '用户管理', children: <UsersPanel /> },
            { key: 'gaps', label: '数据缺口', children: <GapsPanel active={tab === 'gaps'} /> },
          ]}
        />
      )}
    </div>
  )
}

export default function AdminConsole() {
  return (
    <IslandProvider>
      <Console />
    </IslandProvider>
  )
}
