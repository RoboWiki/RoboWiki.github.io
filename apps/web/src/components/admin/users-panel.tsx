import { App as AntApp, Button, Input, Modal, Space, Table, Tag } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { v1Req } from '@/lib/community-api'
import { useAuth } from '@/components/community/providers'

type Row = {
  id: number
  handle: string
  display_name: string
  email: string | null
  is_staff: boolean
  reputation: number
  posts: number
  comments: number
  banned: boolean
  ban_reason: string | null
  created_at: string
}

type ListOut = { total: number; items: Row[] }

const when = (s?: string | null) => (s ? s.slice(0, 16).replace('T', ' ') : '—')

/**
 * 用户管理：查账号、改角色、封禁/解封。
 * 护栏在服务端：不能动自己、不能降级最后一名站务、封禁即下线（会话代次 +1）。
 */
export default function UsersPanel() {
  const { user: me } = useAuth()
  const { message, modal } = AntApp.useApp()
  const qc = useQueryClient()
  const [q, setQ] = useState('')
  const [keyword, setKeyword] = useState('')
  const [banTarget, setBanTarget] = useState<Row | null>(null)
  const [reason, setReason] = useState('')

  const list = useQuery({
    queryKey: ['admin-users', keyword],
    queryFn: () => v1Req<ListOut>(
      `/admin/users?limit=100${keyword ? `&q=${encodeURIComponent(keyword)}` : ''}`),
    staleTime: 10_000,
  })

  const patch = useMutation({
    mutationFn: (v: { id: number; body: Record<string, unknown> }) =>
      v1Req(`/admin/users/${v.id}`, { method: 'PATCH', body: JSON.stringify(v.body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['admin-users'] })
      message.success('已更新')
      setBanTarget(null)
      setReason('')
    },
    onError: (e) => message.error(e instanceof Error ? e.message : '操作失败'),
  })

  const toggleStaff = (row: Row) => {
    modal.confirm({
      title: row.is_staff ? `取消 ${row.handle} 的站务权限？` : `把 ${row.handle} 设为站务？`,
      content: '站务可以审核投稿、处置举报、修改零件数据。至少要保留一名站务。',
      okText: row.is_staff ? '取消站务' : '设为站务',
      cancelText: '返回',
      onOk: () => patch.mutateAsync({ id: row.id, body: { is_staff: !row.is_staff } }),
    })
  }

  const unban = (row: Row) =>
    patch.mutate({ id: row.id, body: { banned: false } })

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Input.Search
          value={q}
          onChange={e => setQ(e.target.value)}
          onSearch={v => setKeyword(v.trim())}
          placeholder="搜索账号或显示名"
          allowClear
          style={{ maxWidth: 280 }}
        />
        <span className="text-xs text-ink-3">
          共 {list.data?.total ?? '…'} 个账号；封禁后该账号所有会话立即失效
        </span>
      </div>

      <Table<Row>
        rowKey="id"
        size="middle"
        loading={list.isLoading}
        dataSource={list.data?.items ?? []}
        pagination={false}
        scroll={{ x: 860 }}
        columns={[
          {
            title: '账号', dataIndex: 'handle', width: 200,
            render: (_, r) => (
              <div className="leading-5">
                <a href={`/u/${r.handle}.html`} className="font-medium text-brand">{r.handle}</a>
                <div className="text-xs text-ink-3">{r.display_name}</div>
              </div>
            ),
          },
          { title: '邮箱', dataIndex: 'email', width: 200, render: v => v || '—' },
          {
            title: '角色', dataIndex: 'is_staff', width: 90,
            render: (v: boolean) => v ? <Tag color="blue">站务</Tag> : <Tag>用户</Tag>,
          },
          {
            title: '内容', width: 110,
            render: (_, r) => <span className="text-xs text-ink-2">{r.posts} 帖 / {r.comments} 评</span>,
          },
          {
            title: '状态', dataIndex: 'banned', width: 150,
            render: (v: boolean, r) => v
              ? <span><Tag color="red">已封禁</Tag><span className="text-xs text-ink-3">{r.ban_reason || '未填原因'}</span></span>
              : <Tag>正常</Tag>,
          },
          { title: '注册', dataIndex: 'created_at', width: 140, render: v => <span className="mono text-xs text-ink-3">{when(v)}</span> },
          {
            title: '操作', width: 220,
            render: (_, r) => {
              const self = me?.id === r.id || me?.handle === r.handle
              return (
                <Space size={4} wrap>
                  <Button size="small" disabled={self} onClick={() => toggleStaff(r)}>
                    {r.is_staff ? '取消站务' : '设为站务'}
                  </Button>
                  {r.banned ? (
                    <Button size="small" onClick={() => unban(r)}>解封</Button>
                  ) : (
                    <Button size="small" danger disabled={self} onClick={() => setBanTarget(r)}>封禁</Button>
                  )}
                </Space>
              )
            },
          },
        ]}
      />

      <Modal
        open={banTarget !== null}
        title={`封禁 ${banTarget?.handle ?? ''}`}
        okText="确认封禁"
        okButtonProps={{ danger: true, loading: patch.isPending }}
        cancelText="取消"
        onCancel={() => { setBanTarget(null); setReason('') }}
        onOk={() => {
          if (!banTarget) return
          patch.mutate({ id: banTarget.id, body: { banned: true, reason: reason.trim() } })
        }}
      >
        <p className="mb-2 text-sm leading-6 text-ink-2">
          封禁后该账号的所有登录会话立即失效，且无法重新登录。解封后可正常登录。
        </p>
        <Input.TextArea
          value={reason}
          onChange={e => setReason(e.target.value)}
          placeholder="封禁原因（会记录在审计里，建议写清违规内容）"
          maxLength={200}
          showCount
          rows={3}
        />
      </Modal>
    </div>
  )
}
