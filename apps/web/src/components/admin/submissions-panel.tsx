import {
  Alert, App as AntApp, Button, Descriptions, Empty, Form, Input, Modal, Select,
  Spin, Table, Tag, Tooltip,
} from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { ApiError, v1Req } from '@/lib/community-api'
import { useAuth } from '@/components/community/providers'

type Review = {
  id: number
  decision: string
  reason_code: string
  note: string
  reviewer_id: number | null
  created_at: string
}
type Preview = { field: string; old_value: unknown; new_value: unknown }
type Outbox = {
  id: number
  submission_id: number | null
  action?: string
  status: string
  attempts: number
  last_error: string | null
  result: { pr_url?: string; file?: string; skipped?: boolean; reason?: string }
  created_at: string
}
type Sub = {
  id: number
  kind: string
  target_id: string | null
  payload: Record<string, unknown>
  evidence: { note?: string; source_url?: string; preview?: Preview[] }
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
const REASON_LABEL: Record<string, string> = {
  ok: '符合目录口径',
  ...Object.fromEntries(REASONS.map(r => [r.value, r.label])),
}

const OUTBOX_STATUS: Record<string, { color: string; label: string }> = {
  pending: { color: 'gold', label: '排队中' },
  running: { color: 'blue', label: '执行中' },
  done: { color: 'green', label: '已完成' },
  failed: { color: 'red', label: '失败' },
}

const fmt = (v: unknown) => (v === null || v === undefined || v === '' ? '—' : String(v))
const fmtValue = (v: unknown) => {
  if (v === null || v === undefined || v === '') return '—'
  if (Array.isArray(v)) return v.map(x => String(x)).join('、') || '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
const isUrl = (v?: string) => /^https?:\/\//i.test(v || '')
const when = (s: string) => s.slice(0, 16).replace('T', ' ')

/** 常见行级字段的中文名；specs.* 保留口径 key（审核员按 key 核对） */
const FIELD_LABEL: Record<string, string> = {
  price_cny: '价格',
  url: '官方来源',
  source_tier: '来源等级',
  last_checked: '核对日期',
  notes: '备注',
  verified: '已核实',
  title: '标题',
  vendor: '厂商',
}
const fieldLabel = (key: string) => FIELD_LABEL[key] || key

function latestReject(s: Sub): Review | undefined {
  return [...(s.reviews || [])].reverse().find(r => r.decision === 'rejected')
}

function QueryFail({ what, error, onRetry, loading }: {
  what: string; error: unknown; onRetry: () => void; loading?: boolean
}) {
  return (
    <Alert type="error" showIcon
      title={`${what}加载失败`}
      description={(error as Error)?.message || '请求出错'}
      action={<Button size="small" onClick={onRetry} loading={loading}>重试</Button>} />
  )
}

function DiffList({ preview }: { preview?: Preview[] }) {
  if (!preview?.length) return <span className="text-ink-3">—</span>
  return (
    <div className="space-y-1">
      {preview.map(p => (
        <div key={p.field} className="text-xs leading-5">
          <code className="text-xs text-brand">{p.field}</code>
          <span className="mx-1.5 text-ink-3">{fmt(p.old_value)}</span>
          <span className="text-ink-3">→</span>
          <span className="ml-1.5 font-medium text-brand">{fmt(p.new_value)}</span>
        </div>
      ))}
    </div>
  )
}

/** 审核员看到的 diff 来自服务端 evidence.preview（客户端传的会被后端丢弃） */
function Evidence({ sub }: { sub: Sub }) {
  const src = sub.evidence?.source_url
  return (
    <div className="rounded-lg border border-line bg-surface-2 p-3">
      <div className="mb-1.5 text-xs uppercase tracking-wider text-ink-3">
        服务端生成的变更预览（旧值 → 新值）
      </div>
      <DiffList preview={sub.evidence?.preview} />
      <div className="mt-2 space-y-1 border-t border-line pt-2 text-xs text-ink-2">
        <div className="break-words">依据：{sub.evidence?.note || '—'}</div>
        <div className="break-all">
          来源：{isUrl(src)
            ? <a href={src} target="_blank" rel="noreferrer" className="text-brand hover:underline">
              {src} ↗
            </a>
            : (src || '—')}
        </div>
      </div>
    </div>
  )
}

function ReviewList({ reviews }: { reviews: Review[] }) {
  if (!reviews?.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有审核记录" />
  }
  return (
    <div className="space-y-2">
      {reviews.map(r => (
        <div key={r.id} className="rounded-lg border border-line p-2.5">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
            <Tag color={r.decision === 'accepted' ? 'blue' : 'red'} style={{ marginInlineEnd: 0 }}>
              {r.decision === 'accepted' ? '通过' : '驳回'}
            </Tag>
            <span className="text-ink-2">
              理由：{REASON_LABEL[r.reason_code] || r.reason_code || '—'}
            </span>
            <span className="ml-auto text-ink-3">
              {when(r.created_at)} · 审核人 #{r.reviewer_id ?? '?'}
            </span>
          </div>
          {r.note
            ? <div className="mt-1 whitespace-pre-wrap text-xs text-ink-2">{r.note}</div>
            : <div className="mt-1 text-xs text-ink-3">未写补充说明</div>}
        </div>
      ))}
    </div>
  )
}

function ReviewModal({ sub, decision, onClose }: {
  sub: Sub; decision: 'accepted' | 'rejected'; onClose: () => void
}) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const reject = decision === 'rejected'

  const review = useMutation({
    mutationFn: ({ id, decision, reason_code, note }: {
      id: number; decision: string; reason_code: string; note: string
    }) => v1Req(`/submissions/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ decision, reason_code, note }),
    }),
    onSuccess: (_r, v) => {
      message.success({
        content: v.decision === 'accepted'
          ? `#${v.id} 已通过，进入发布队列；通过不等于已发布，数据在下一个 data-v* 发布后生效`
          : `#${v.id} 已驳回`,
        duration: 6,
      })
      qc.invalidateQueries({ queryKey: ['submissions'] })
      qc.invalidateQueries({ queryKey: ['submission', v.id] })
      qc.invalidateQueries({ queryKey: ['outbox'] })
      onClose()
    },
    // 409 = 别处已经审过：刷新后再看，而不是停在旧状态
    onError: (e: Error, v) => {
      message.error(e.message)
      if (e instanceof ApiError && e.status === 409) {
        qc.invalidateQueries({ queryKey: ['submissions'] })
        qc.invalidateQueries({ queryKey: ['submission', v.id] })
        qc.invalidateQueries({ queryKey: ['outbox'] })
      }
    },
  })

  return (
    <Modal
      open
      title={`${reject ? '驳回' : '通过'}提案 #${sub.id}`}
      width={640}
      onCancel={onClose}
      destroyOnHidden
      okText={reject ? '确认驳回' : '确认通过'}
      okButtonProps={{ danger: reject }}
      confirmLoading={review.isPending}
      onOk={async () => {
        try {
          const v = await form.validateFields()
          review.mutate({
            id: sub.id,
            decision,
            reason_code: reject ? v.reason_code : 'ok',
            note: (v.note || '').trim(),
          })
        } catch {
          // 校验失败：错误提示已经挂在字段下方
        }
      }}>
      <div className="space-y-3 pt-1">
        <Evidence sub={sub} />

        <Form form={form} layout="vertical"
          initialValues={{ reason_code: reject ? 'insufficient_evidence' : 'ok', note: '' }}
          onValuesChange={changed => {
            if ('reason_code' in changed) form.validateFields(['note']).catch(() => {})
          }}>
          {reject && (
            <Form.Item name="reason_code" label="驳回理由"
              rules={[{ required: true, message: '请选择驳回理由' }]}>
              <Select options={REASONS} />
            </Form.Item>
          )}
          <Form.Item
            name="note"
            label={reject ? '具体说明（提交者可见）' : '审核备注（可选）'}
            rules={reject ? [({ getFieldValue }) => ({
              validator(_, v) {
                const other = getFieldValue('reason_code') === 'other'
                if (other && (v || '').trim().length < 4) {
                  return Promise.reject(new Error('选择「其他」时必须写明具体原因（至少 4 个字）'))
                }
                return Promise.resolve()
              },
            })] : []}>
            <Input.TextArea rows={3} maxLength={2000} showCount
              placeholder={reject
                ? '建议给出正确数值或缺失的资料，提交者按这条改'
                : '例如：已按官方 datasheet 核对，进入发布队列'} />
          </Form.Item>
        </Form>

        {!!sub.reviews?.length && (
          <div>
            <div className="mb-1.5 text-xs uppercase tracking-wider text-ink-3">历史审核</div>
            <ReviewList reviews={sub.reviews} />
          </div>
        )}
        <div className="text-xs text-ink-3">
          通过只进入发布队列：worker 生成变更并随 release 发布后，目录才更新。
        </div>
      </div>
    </Modal>
  )
}

function DetailModal({ id, onClose }: { id: number; onClose: () => void }) {
  const detail = useQuery({
    queryKey: ['submission', id],
    queryFn: () => v1Req<Sub>(`/submissions/${id}`),
  })
  const sub = detail.data
  const rejected = sub ? latestReject(sub) : undefined

  return (
    <Modal open title={`提案 #${id}`} width={720} footer={null} onCancel={onClose} destroyOnHidden>
      {detail.isLoading ? (
        <div className="py-12 text-center"><Spin /></div>
      ) : detail.isError ? (
        <QueryFail what="提案详情" error={detail.error}
          onRetry={() => detail.refetch()} loading={detail.isFetching} />
      ) : !sub ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="提案不存在或无权限查看" />
      ) : (
        <div className="space-y-3">
          <Descriptions
            size="small"
            column={{ xs: 1, sm: 2 }}
            bordered
            items={[
              {
                key: 'status', label: '状态',
                children: (
                  <div>
                    <Tag color={(STATUS[sub.status] || { color: 'default' }).color}
                      style={{ marginInlineEnd: 0 }}>
                      {(STATUS[sub.status] || { label: sub.status }).label}
                    </Tag>
                    {rejected && (
                      <div className="mt-1 break-words text-xs text-danger">
                        {REASON_LABEL[rejected.reason_code] || rejected.reason_code}
                        {rejected.note ? `：${rejected.note}` : ''}
                        <span className="ml-1 text-ink-3">
                          （审核人 #{rejected.reviewer_id ?? '?'} · {when(rejected.created_at)}）
                        </span>
                      </div>
                    )}
                  </div>
                ),
              },
              { key: 'target', label: '目标部件', children: sub.target_id || '—' },
              { key: 'submitter', label: '提交人', children: `#${sub.submitter_id ?? '?'}` },
              { key: 'created', label: '提交时间', children: when(sub.created_at) },
              { key: 'revision', label: '修订', children: sub.revision },
              { key: 'kind', label: '类型', children: sub.kind },
            ]}
          />

          <div>
            <div className="mb-1.5 text-xs uppercase tracking-wider text-ink-3">
              提案写入的值（payload）
            </div>
            <div className="rounded-lg border border-line">
              {Object.entries(sub.payload || {}).map(([k, v], i) => (
                <div key={k}
                  className={`flex items-start justify-between gap-3 px-2.5 py-1.5 text-xs
                    ${i ? 'border-t border-line' : ''}`}>
                  <span className="min-w-0 break-all">
                    <span className="text-ink-2">{fieldLabel(k)}</span>
                    <code className="ml-1.5 text-xs text-brand">{k}</code>
                  </span>
                  <span className="min-w-0 max-w-[65%] break-all text-right text-ink-2">{fmtValue(v)}</span>
                </div>
              ))}
              {!Object.keys(sub.payload || {}).length && (
                <div className="px-2.5 py-2 text-xs text-ink-3">没有字段</div>
              )}
            </div>
          </div>

          <Evidence sub={sub} />

          <div>
            <div className="mb-1.5 text-xs uppercase tracking-wider text-ink-3">
              审核记录（{sub.reviews?.length ?? 0}）
            </div>
            <ReviewList reviews={sub.reviews || []} />
          </div>
        </div>
      )}
    </Modal>
  )
}

export default function SubmissionsPanel({ active }: { active: boolean }) {
  const { user } = useAuth()
  const { message } = AntApp.useApp()
  const qc = useQueryClient()
  const [status, setStatus] = useState('pending')
  const [reviewTarget, setReviewTarget] = useState<{ sub: Sub; decision: 'accepted' | 'rejected' } | null>(null)
  const [detailId, setDetailId] = useState<number | null>(null)

  const enabled = !!user?.is_staff && active

  const list = useQuery({
    queryKey: ['submissions', status],
    queryFn: () => v1Req<Sub[]>(`/submissions/queue?status=${status}&limit=200`),
    enabled,
  })

  const outbox = useQuery({
    queryKey: ['outbox'],
    queryFn: () => v1Req<Outbox[]>('/submissions/outbox?limit=20'),
    enabled,
    // 通过后 worker 可能几秒内就处理完，任务没落地前轻量轮询
    refetchInterval: q => (q.state.data || []).some(r => r.status === 'pending' || r.status === 'running')
      ? 5000 : false,
  })

  const retry = useMutation({
    mutationFn: (id: number) => v1Req(`/submissions/outbox/${id}/retry`, { method: 'POST' }),
    onSuccess: () => { message.success('已重新排队'); qc.invalidateQueries({ queryKey: ['outbox'] }) },
    onError: (e: Error) => message.error(e.message),
  })

  const runningCount = (outbox.data || [])
    .filter(r => r.status === 'pending' || r.status === 'running').length

  return (
    <div className="w-full min-w-0">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h2 className="m-0 text-[18px] font-bold text-ink">目录变更提案</h2>
          <p className="m-0 mt-1 text-sm text-ink-3">
            通过后只进入 outbox；目录要等 worker 生成 PR 并发布 release 才更新。
          </p>
        </div>
        <div className="flex w-full items-center gap-2 sm:w-auto">
          <Select value={status} onChange={setStatus} style={{ width: 150 }}
            options={[
              { value: 'pending', label: '待审' },
              { value: 'accepted', label: '已通过' },
              { value: 'rejected', label: '已驳回' },
            ]} />
          <Button onClick={() => { list.refetch(); outbox.refetch() }}
            loading={list.isFetching || outbox.isFetching}>刷新</Button>
        </div>
      </div>

      {list.isError ? (
        <QueryFail what="提案队列" error={list.error}
          onRetry={() => list.refetch()} loading={list.isFetching} />
      ) : (
        <Table<Sub>
          rowKey="id"
          size="small"
          loading={list.isLoading}
          dataSource={list.data || []}
          pagination={{ pageSize: 20, hideOnSinglePage: true }}
          locale={{
            emptyText: (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={status === 'pending'
                  ? '没有待审提案，队列是空的'
                  : status === 'rejected' ? '没有已驳回的提案' : '没有已通过的提案'} />
            ),
          }}
          columns={[
            { title: '#', dataIndex: 'id', width: 56 },
            {
              title: '目标 / 字段', width: 200,
              render: (_v, r) => (
                <div className="min-w-0">
                  <div className="break-all text-sm font-medium text-ink-2">
                    {r.target_id || '—'}
                  </div>
                  <div className="break-all text-xs text-brand">
                    {Object.keys(r.payload || {}).join(', ') || '—'}
                  </div>
                </div>
              ),
            },
            {
              title: '变更预览', width: 250,
              render: (_v, r) => <DiffList preview={r.evidence?.preview} />,
            },
            {
              title: '依据', width: 220,
              render: (_v, r) => (
                <div className="text-xs">
                  <div className="line-clamp-2 text-ink-2">{r.evidence?.note || '—'}</div>
                  {isUrl(r.evidence?.source_url) && (
                    <a className="text-brand hover:underline" href={r.evidence.source_url}
                      target="_blank" rel="noreferrer">来源 ↗</a>
                  )}
                </div>
              ),
            },
            {
              title: '状态', width: 150,
              render: (_v, r) => {
                const s = STATUS[r.status] || { color: 'default', label: r.status }
                const rej = latestReject(r)
                return (
                  <div>
                    <Tag color={s.color} style={{ marginInlineEnd: 0 }}>{s.label}</Tag>
                    {rej && (
                      <Tooltip title={rej.note || REASON_LABEL[rej.reason_code] || rej.reason_code}>
                        <div className="mt-1 line-clamp-2 text-xs text-danger">
                          {REASON_LABEL[rej.reason_code] || rej.reason_code || '驳回'}
                          {rej.note ? `：${rej.note}` : ''}
                        </div>
                      </Tooltip>
                    )}
                  </div>
                )
              },
            },
            {
              title: '提交', width: 110,
              render: (_v, r) => (
                <div className="text-xs text-ink-3">
                  #{r.submitter_id ?? '?'}<br />{when(r.created_at)}
                </div>
              ),
            },
            {
              title: '操作', width: 210,
              render: (_v, r) => (
                <div className="flex flex-wrap gap-1.5">
                  <Button size="small" onClick={() => setDetailId(r.id)}>详情</Button>
                  {r.status === 'pending' && (
                    <>
                      <Button size="small" type="primary"
                        onClick={() => setReviewTarget({ sub: r, decision: 'accepted' })}>
                        通过
                      </Button>
                      <Button size="small" danger
                        onClick={() => setReviewTarget({ sub: r, decision: 'rejected' })}>
                        驳回
                      </Button>
                    </>
                  )}
                </div>
              ),
            },
          ]}
          scroll={{ x: 1160 }}
        />
      )}

      <div className="mt-8">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-1">
          <h2 className="m-0 text-base font-bold text-ink">
            发布队列{runningCount > 0 ? `（进行中 ${runningCount}）` : ''}
          </h2>
          <span className="text-xs text-ink-3">失败会自动退避重试；也可以手动重排</span>
        </div>
        {outbox.isError ? (
          <QueryFail what="发布队列" error={outbox.error}
            onRetry={() => outbox.refetch()} loading={outbox.isFetching} />
        ) : (
          <Table<Outbox>
            rowKey="id"
            size="small"
            loading={outbox.isLoading}
            dataSource={outbox.data || []}
            pagination={false}
            locale={{
              emptyText: (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="还没有发布任务：通过一条提案后会出现在这里" />
              ),
            }}
            columns={[
              { title: '#', dataIndex: 'id', width: 56 },
              { title: '提案', dataIndex: 'submission_id', width: 76, render: v => (v ? `#${v}` : '—') },
              {
                title: '状态', width: 96,
                render: (_v, r) => {
                  const s = OUTBOX_STATUS[r.status] || { color: 'default', label: r.status }
                  return <Tag color={s.color} style={{ marginInlineEnd: 0 }}>{s.label}</Tag>
                },
              },
              { title: '尝试', dataIndex: 'attempts', width: 64 },
              {
                title: '结果 / 错误',
                render: (_v, r) => r.result?.pr_url
                  ? <a href={r.result.pr_url} target="_blank" rel="noreferrer" className="text-brand">PR ↗</a>
                  : r.result?.file
                    ? <code className="break-all text-xs">{r.result.file}</code>
                    : <span className="break-all text-xs text-ink-3">
                      {r.last_error || (r.result?.reason ?? '—')}
                    </span>,
              },
              {
                title: '操作', width: 96,
                render: (_v, r) => r.status === 'failed' || r.status === 'pending'
                  ? <Button size="small"
                    loading={retry.isPending && retry.variables === r.id}
                    disabled={retry.isPending && retry.variables !== r.id}
                    onClick={() => retry.mutate(r.id)}>重试</Button>
                  : <span className="text-ink-3">—</span>,
              },
            ]}
            scroll={{ x: 720 }}
          />
        )}
      </div>

      {reviewTarget && (
        <ReviewModal sub={reviewTarget.sub} decision={reviewTarget.decision}
          onClose={() => setReviewTarget(null)} />
      )}
      {detailId !== null && (
        <DetailModal id={detailId} onClose={() => setDetailId(null)} />
      )}
    </div>
  )
}
