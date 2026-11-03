import { App as AntApp, Button, Input, Modal, Segmented, Table, Tag } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { v1Req } from './api'
import { useAuth } from './App'

type Target = {
  title?: string
  body?: string
  kind?: string
  post_id?: number
  post_title?: string
  page?: string
  hidden?: boolean
  author?: { handle: string; display_name: string } | null
}

type Rep = {
  id: number
  target_kind: 'post' | 'comment' | 'wiki_comment'
  target_id: number
  reason: string
  detail: string
  status: 'open' | 'resolved' | 'dismissed'
  resolution_note: string
  reporter: { handle: string; display_name: string } | null
  created_at: string
  resolved_at: string | null
  target: Target | null
}

type Queue = {
  total: number
  counts: { open: number; resolved: number; dismissed: number }
  items: Rep[]
}

const KIND: Record<string, string> = {
  post: '帖子', comment: '评论', wiki_comment: '文档讨论',
}
const REASON: Record<string, string> = {
  spam: '垃圾广告', abuse: '攻击辱骂', misinfo: '虚假信息', other: '其他',
}
const STATUS: Record<string, { color: string; label: string }> = {
  open: { color: 'gold', label: '待处理' },
  resolved: { color: 'green', label: '已处置' },
  dismissed: { color: 'default', label: '已驳回' },
}

const when = (s: string) => s.slice(0, 16).replace('T', ' ')

export default function Reports() {
  const { user } = useAuth()
  const { message } = AntApp.useApp()
  const qc = useQueryClient()
  const [status, setStatus] = useState<'open' | 'resolved' | 'dismissed'>('open')
  const [acting, setActing] = useState<{ report: Rep; action: 'hide' | 'dismiss' | 'restore' } | null>(null)
  const [note, setNote] = useState('')

  const queue = useQuery({
    queryKey: ['reports', status],
    queryFn: () => v1Req<Queue>(`/admin/reports?status=${status}&limit=200`),
    enabled: !!user?.is_staff,
  })

  const resolve = useMutation({
    mutationFn: ({ id, action, note }: { id: number; action: string; note: string }) =>
      v1Req(`/admin/reports/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ action, note }),
      }),
    onSuccess: () => {
      message.success('处置已记录')
      setActing(null)
      setNote('')
      qc.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: (e: any) => message.error(e.message),
  })

  if (!user?.is_staff) {
    return <div className="mx-auto max-w-[900px] px-5 py-16 text-[13px] text-slate-500">举报队列只有站务可以查看。</div>
  }

  const counts = queue.data?.counts
  const options = [
    { value: 'open', label: `待处理 ${counts?.open ?? 0}` },
    { value: 'resolved', label: `已处置 ${counts?.resolved ?? 0}` },
    { value: 'dismissed', label: `已驳回 ${counts?.dismissed ?? 0}` },
  ]

  return (
    <div className="mx-auto max-w-[1240px] px-5 py-6">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="m-0 text-[20px] font-bold text-slate-900">举报与内容处置</h1>
          <p className="m-0 mt-1 text-[12.5px] text-slate-500">
            举报不会自动下架；隐藏与驳回都必须写依据。隐藏是软操作，可恢复。
          </p>
        </div>
        <Segmented value={status} onChange={v => setStatus(v as typeof status)} options={options} />
      </div>

      <Table<Rep>
        rowKey="id"
        size="small"
        loading={queue.isLoading}
        dataSource={queue.data?.items || []}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: status === 'open' ? '没有待处理举报' : '没有记录' }}
        columns={[
          { title: '#', dataIndex: 'id', width: 50 },
          {
            title: '对象 / 内容', width: 380,
            render: (_, r) => (
              <div>
                <div className="flex items-center gap-1.5">
                  <Tag>{KIND[r.target_kind] || r.target_kind}</Tag>
                  <span className="text-[11.5px] text-slate-400">#{r.target_id}</span>
                  {r.target?.hidden && <Tag color="red">已隐藏</Tag>}
                </div>
                <div className="mt-1 line-clamp-2 text-[12px] text-slate-700">
                  {r.target?.title || r.target?.post_title || r.target?.body || '内容已删除'}
                </div>
                {r.target?.body && r.target?.title && (
                  <div className="mt-0.5 line-clamp-1 text-[11.5px] text-slate-500">{r.target.body}</div>
                )}
                {r.target?.page && (
                  <a href={`/${r.target.page}`} target="_blank" rel="noreferrer"
                    className="text-[11px] text-blue-600 hover:underline">{r.target.page} ↗</a>
                )}
              </div>
            ),
          },
          {
            title: '举报理由', width: 200,
            render: (_, r) => (
              <div className="text-[12px]">
                <div className="text-slate-700">{REASON[r.reason] || r.reason}</div>
                {r.detail && <div className="mt-0.5 text-[11.5px] text-slate-500">{r.detail}</div>}
              </div>
            ),
          },
          {
            title: '举报人 / 时间', width: 150,
            render: (_, r) => (
              <div className="text-[11.5px] text-slate-500">
                <div className="text-slate-700">@{r.reporter?.handle || '—'}</div>
                {when(r.created_at)}
              </div>
            ),
          },
          {
            title: '状态', width: 90,
            render: (_, r) => {
              const s = STATUS[r.status] || { color: 'default', label: r.status }
              return <Tag color={s.color}>{s.label}</Tag>
            },
          },
          {
            title: '处置记录', width: 220,
            render: (_, r) => r.resolution_note
              ? <div className="text-[11.5px] text-slate-600">{r.resolution_note}</div>
              : <span className="text-slate-300">—</span>,
          },
          {
            title: '操作', width: 170, fixed: 'right',
            render: (_, r) => (
              <div className="flex flex-wrap gap-1.5">
                {r.status === 'open' && (
                  <>
                    <Button size="small" danger
                      onClick={() => { setActing({ report: r, action: 'hide' }); setNote('') }}>
                      隐藏
                    </Button>
                    <Button size="small"
                      onClick={() => { setActing({ report: r, action: 'dismiss' }); setNote('') }}>
                      驳回
                    </Button>
                  </>
                )}
                {r.status === 'resolved' && r.target?.hidden && (
                  <Button size="small"
                    onClick={() => { setActing({ report: r, action: 'restore' }); setNote('') }}>
                    恢复
                  </Button>
                )}
              </div>
            ),
          },
        ]}
        scroll={{ x: 1260 }}
      />

      <Modal
        open={!!acting}
        title={acting ? `${acting.action === 'hide' ? '隐藏' : acting.action === 'restore' ? '恢复' : '驳回'} #${acting.report.id}` : ''}
        onCancel={() => setActing(null)}
        footer={null}
        destroyOnHidden
      >
        <div className="space-y-3 pt-2">
          <div className="rounded-md bg-slate-50 px-3 py-2 text-[12px] text-slate-600">
            对象：{acting ? KIND[acting.report.target_kind] : ''} #{acting?.report.target_id}
            <br />
            {acting?.report.target?.title || acting?.report.target?.body || ''}
          </div>
          <Input.TextArea rows={3} value={note} onChange={e => setNote(e.target.value)}
            placeholder="写明依据；这条记录会进入处置留痕" />
          <Button
            block
            danger={acting?.action === 'hide'}
            type={acting?.action === 'restore' ? 'primary' : undefined}
            loading={resolve.isPending}
            disabled={note.trim().length < 2}
            onClick={() => acting && resolve.mutate({
              id: acting.report.id, action: acting.action, note,
            })}
          >
            确认{acting?.action === 'hide' ? '隐藏' : acting?.action === 'restore' ? '恢复' : '驳回'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
