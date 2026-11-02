import { App as AntApp, Button, Input, Modal, Select, Table, Tag } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { v1Req } from './api'
import { useAuth } from './App'

type Review = { id: number; decision: string; reason_code: string; note: string; reviewer_id: number | null; created_at: string }
type Sub = {
  id: number
  kind: string
  target_id: string | null
  payload: Record<string, unknown>
  evidence: { note?: string; source_url?: string; preview?: { field: string; old_value: unknown; new_value: unknown }[] }
  submitter_id: number | null
  status: string
  revision: number
  created_at: string
  reviews: Review[]
}

const STATUS: Record<string, { color: string; label: string }> = {
  pending: { color: 'gold', label: '待审' },
  accepted: { color: 'blue', label: '已通过' },
  rejected: { color: 'red', label: '已驳回' },
  pr_open: { color: 'cyan', label: 'PR 中' },
  merged: { color: 'green', label: '已合并' },
  released: { color: 'green', label: '已发布' },
}

const REASONS = [
  { value: 'insufficient_evidence', label: '依据不足' },
  { value: 'wrong_value', label: '数值/口径不对' },
  { value: 'out_of_scope', label: '不属于可改字段' },
  { value: 'duplicate', label: '重复提案' },
  { value: 'other', label: '其他（写明原因）' },
]

const fmt = (v: unknown) => (v === null || v === undefined || v === '' ? '—' : String(v))

export default function Submissions() {
  const { user } = useAuth()
  const { message } = AntApp.useApp()
  const qc = useQueryClient()
  const [status, setStatus] = useState('pending')
  const [rejecting, setRejecting] = useState<Sub | null>(null)
  const [reason, setReason] = useState('insufficient_evidence')
  const [note, setNote] = useState('')

  const list = useQuery({
    queryKey: ['submissions', status],
    queryFn: () => v1Req<Sub[]>(`/submissions/queue?status=${status}&limit=200`),
    enabled: !!user?.is_staff,
  })

  const review = useMutation({
    mutationFn: ({ id, decision, reason_code, note }: {
      id: number; decision: string; reason_code: string; note: string
    }) => v1Req(`/submissions/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ decision, reason_code, note }),
    }),
    onSuccess: (_r, v) => {
      message.success(v.decision === 'accepted' ? `#${v.id} 已通过，进入 outbox` : `#${v.id} 已驳回`)
      setRejecting(null)
      setNote('')
      qc.invalidateQueries({ queryKey: ['submissions'] })
    },
    onError: (e: any) => message.error(e.message),
  })

  if (!user?.is_staff) {
    return <div className="mx-auto max-w-[900px] px-5 py-16 text-[13px] text-slate-500">提案队列只有站务可以查看。</div>
  }

  return (
    <div className="mx-auto max-w-[1240px] px-5 py-6">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="m-0 text-[20px] font-bold text-slate-900">目录变更提案</h1>
          <p className="m-0 mt-1 text-[12.5px] text-slate-500">
            通过后只进入 outbox；目录要等 worker 生成 PR 并发布 release 才更新。
          </p>
        </div>
        <Select value={status} onChange={setStatus} style={{ width: 150 }}
          options={[
            { value: 'pending', label: '待审' },
            { value: 'accepted', label: '已通过' },
            { value: 'rejected', label: '已驳回' },
          ]} />
      </div>

      <Table<Sub>
        rowKey="id"
        size="small"
        loading={list.isLoading}
        dataSource={list.data || []}
        pagination={{ pageSize: 20, hideOnSinglePage: true }}
        locale={{ emptyText: status === 'pending' ? '没有待审提案' : '没有记录' }}
        columns={[
          { title: '#', dataIndex: 'id', width: 50 },
          {
            title: '目标 / 字段', width: 220,
            render: (_, r) => (
              <div>
                <div className="text-[12.5px] font-medium text-slate-800">{r.target_id || '—'}</div>
                <div className="text-[11px] text-sky-700">{Object.keys(r.payload).join(', ')}</div>
              </div>
            ),
          },
          {
            title: '变更预览', width: 270,
            render: (_, r) => (
              <div className="text-[11.5px]">
                {(r.evidence.preview || []).map(p => (
                  <div key={p.field}>
                    <code className="text-[11px] text-sky-700">{p.field}</code>
                    <span className="mx-1 text-slate-400">{fmt(p.old_value)} →</span>
                    <span className="text-blue-600">{fmt(p.new_value)}</span>
                  </div>
                ))}
                {!r.evidence.preview?.length && <span className="text-slate-400">—</span>}
              </div>
            ),
          },
          {
            title: '依据', width: 260,
            render: (_, r) => (
              <div className="text-[11.5px]">
                <div className="text-slate-600">{r.evidence.note || '—'}</div>
                {/^https?:\/\//i.test(r.evidence.source_url || '') && (
                  <a className="text-blue-600 hover:underline" href={r.evidence.source_url}
                    target="_blank" rel="noreferrer">来源 ↗</a>
                )}
              </div>
            ),
          },
          {
            title: '状态', width: 80,
            render: (_, r) => {
              const s = STATUS[r.status] || { color: 'default', label: r.status }
              return <Tag color={s.color}>{s.label}</Tag>
            },
          },
          {
            title: '提交', width: 100,
            render: (_, r) => (
              <div className="text-[11.5px] text-slate-500">
                #{r.submitter_id ?? '?'}<br />{r.created_at.slice(0, 16).replace('T', ' ')}
              </div>
            ),
          },
          {
            title: '操作', width: 130, fixed: 'right',
            render: (_, r) => r.status !== 'pending' ? <span className="text-slate-300">—</span> : (
              <div className="flex gap-1.5">
                <Button size="small" type="primary"
                  loading={review.isPending}
                  onClick={() => review.mutate({ id: r.id, decision: 'accepted', reason_code: 'ok', note: '' })}>
                  通过
                </Button>
                <Button size="small" danger onClick={() => { setRejecting(r); setReason('insufficient_evidence') }}>
                  驳回
                </Button>
              </div>
            ),
          },
        ]}
        scroll={{ x: 1110 }}
      />

      <Modal open={!!rejecting} title={`驳回提案 #${rejecting?.id ?? ''}`}
        onCancel={() => setRejecting(null)} footer={null} destroyOnHidden>
        <div className="space-y-3 pt-2">
          <Select value={reason} onChange={setReason} style={{ width: '100%' }} options={REASONS} />
          <Input.TextArea rows={3} value={note} onChange={e => setNote(e.target.value)}
            placeholder="说明原因，提交者会看到；建议给出正确数值或缺失的资料" />
          <Button danger block loading={review.isPending}
            onClick={() => rejecting && review.mutate({
              id: rejecting.id, decision: 'rejected', reason_code: reason, note,
            })}>
            确认驳回
          </Button>
        </div>
      </Modal>
    </div>
  )
}
