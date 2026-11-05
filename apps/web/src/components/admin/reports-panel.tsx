import { Alert, App as AntApp, Button, Empty, Form, Input, Modal, Segmented, Table, Tag } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { siteHref, v1Req } from '@/lib/community-api'
import { useAuth } from '@/components/community/providers'

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

type Action = 'hide' | 'restore' | 'dismiss'

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
const ACTION_LABEL: Record<Action, string> = {
  hide: '隐藏', restore: '恢复', dismiss: '驳回',
}

const when = (s?: string | null) => (s ? s.slice(0, 16).replace('T', ' ') : '—')

/** 站内可点开的原文位置；wiki 评论指向主站页面 */
function targetHref(r: Rep): string | null {
  if (r.target_kind === 'post') return siteHref(`/post/${r.target_id}.html`)
  if (r.target_kind === 'comment' && r.target?.post_id) return siteHref(`/post/${r.target.post_id}.html`)
  if (r.target_kind === 'wiki_comment' && r.target?.page) return siteHref(`/${r.target.page}`)
  return null
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

// ── 处置弹窗：必须写依据，提交后同时刷新队列与内容缓存 ─────────────────────
function ActionModal({ report, action, onClose }: {
  report: Rep; action: Action; onClose: () => void
}) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()

  const resolve = useMutation({
    mutationFn: ({ id, action, note }: { id: number; action: Action; note: string }) =>
      v1Req(`/admin/reports/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ action, note }),
      }),
    onSuccess: () => {
      message.success('处置已记录')
      // 举报队列 + 前台内容一起失效：隐藏/恢复会改变可见性
      qc.invalidateQueries({ queryKey: ['reports'] })
      qc.invalidateQueries({ queryKey: ['posts'] })
      qc.invalidateQueries({ queryKey: ['post'] })
      qc.invalidateQueries({ queryKey: ['comments'] })
      onClose()
    },
    onError: (e: Error) => message.error(e.message),
  })

  const label = ACTION_LABEL[action]
  const href = targetHref(report)

  return (
    <Modal
      open
      title={`${label} ${KIND[report.target_kind] || report.target_kind} #${report.target_id}`}
      width={560}
      onCancel={onClose}
      destroyOnHidden
      okText={`确认${label}`}
      okButtonProps={{ danger: action === 'hide', type: action === 'restore' ? 'primary' : 'default' }}
      confirmLoading={resolve.isPending}
      onOk={async () => {
        try {
          const v = await form.validateFields()
          resolve.mutate({ id: report.id, action, note: (v.note || '').trim() })
        } catch {
          // 校验错误已显示在字段下方
        }
      }}>
      <div className="space-y-3 pt-1">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-[12px] text-slate-600">
          <div className="mb-1 flex flex-wrap items-center gap-1.5">
            <Tag style={{ marginInlineEnd: 0 }}>{KIND[report.target_kind] || report.target_kind}</Tag>
            <span className="text-[11.5px] text-slate-400">#{report.target_id}</span>
            {report.target?.hidden && <Tag color="red" style={{ marginInlineEnd: 0 }}>当前已隐藏</Tag>}
            {href && (
              <a href={href} target="_blank" rel="noreferrer"
                className="ml-auto text-[11px] text-blue-600 hover:underline">查看原文 ↗</a>
            )}
          </div>
          <div className="line-clamp-3 text-slate-800">
            {report.target?.title || report.target?.post_title || report.target?.body || '内容已删除'}
          </div>
          {report.target?.body && report.target?.title && (
            <div className="mt-1 line-clamp-2 text-[11.5px] text-slate-500">{report.target.body}</div>
          )}
          <div className="mt-2 border-t border-slate-200 pt-1.5 text-[11.5px] text-slate-500">
            举报理由：{REASON[report.reason] || report.reason}
            {report.detail ? ` · ${report.detail}` : ''}
          </div>
        </div>

        <Form form={form} layout="vertical" initialValues={{ note: '' }}>
          <Form.Item
            name="note"
            label="处置依据（写入留痕，必填）"
            rules={[{
              validator: (_, v) => (v || '').trim().length >= 2
                ? Promise.resolve()
                : Promise.reject(new Error('至少写 2 个字，说明为什么这样处置')),
            }]}>
            <Input.TextArea rows={3} maxLength={500} showCount
              placeholder={action === 'hide'
                ? '例如：广告引流，已隐藏；作者可申诉'
                : action === 'restore'
                  ? '例如：复核后原文不违规，恢复可见'
                  : '例如：重复举报，原文不违反社区规则'} />
          </Form.Item>
        </Form>
        <div className="text-[11px] text-slate-400">
          隐藏是软操作：内容仍在库中，站务可在「已处置」里恢复。举报不会自动下架。
        </div>
      </div>
    </Modal>
  )
}

export default function ReportsPanel({ active }: { active: boolean }) {
  const { user } = useAuth()
  const [status, setStatus] = useState<'open' | 'resolved' | 'dismissed'>('open')
  const [acting, setActing] = useState<{ report: Rep; action: Action } | null>(null)

  const queue = useQuery({
    queryKey: ['reports', status],
    queryFn: () => v1Req<Queue>(`/admin/reports?status=${status}&limit=200`),
    enabled: !!user?.is_staff && active,
  })

  const counts = queue.data?.counts
  const options = [
    { value: 'open', label: `待处理 ${counts?.open ?? 0}` },
    { value: 'resolved', label: `已处置 ${counts?.resolved ?? 0}` },
    { value: 'dismissed', label: `已驳回 ${counts?.dismissed ?? 0}` },
  ]
  const emptyText = status === 'open'
    ? '没有待处理举报，队列是空的'
    : status === 'resolved' ? '还没有处置记录' : '没有已驳回的举报'

  return (
    <div className="w-full min-w-0">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h2 className="m-0 text-[18px] font-bold text-slate-900">举报与内容处置</h2>
          <p className="m-0 mt-1 text-[12.5px] text-slate-500">
            举报不会自动下架；隐藏与驳回都必须写依据。隐藏是软操作，可恢复。
          </p>
        </div>
        <div className="flex w-full items-center gap-2 sm:w-auto">
          <Segmented block value={status} onChange={v => setStatus(v as typeof status)}
            options={options} className="min-w-0 flex-1 sm:flex-none" />
          <Button onClick={() => queue.refetch()} loading={queue.isFetching}>刷新</Button>
        </div>
      </div>

      <div className="mb-2 text-[11.5px] text-slate-400">
        共 {queue.data?.total ?? 0} 条{queue.isFetching && !queue.isLoading ? ' · 刷新中…' : ''}
      </div>

      {queue.isError ? (
        <QueryFail what="举报队列" error={queue.error}
          onRetry={() => queue.refetch()} loading={queue.isFetching} />
      ) : (
        <Table<Rep>
          rowKey="id"
          size="small"
          loading={queue.isLoading}
          dataSource={queue.data?.items || []}
          pagination={{ pageSize: 20, hideOnSinglePage: true }}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} /> }}
          columns={[
            { title: '#', dataIndex: 'id', width: 56 },
            {
              title: '对象 / 内容', width: 360,
              render: (_v, r) => {
                const href = targetHref(r)
                return (
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Tag style={{ marginInlineEnd: 0 }}>{KIND[r.target_kind] || r.target_kind}</Tag>
                      <span className="text-[11.5px] text-slate-400">#{r.target_id}</span>
                      {r.target?.hidden && <Tag color="red" style={{ marginInlineEnd: 0 }}>已隐藏</Tag>}
                      {r.target?.author && (
                        <span className="text-[11px] text-slate-400">@{r.target.author.handle}</span>
                      )}
                      {href && (
                        <a href={href} target="_blank" rel="noreferrer"
                          className="ml-auto text-[11px] text-blue-600 hover:underline">查看 ↗</a>
                      )}
                    </div>
                    <div className="mt-1 line-clamp-2 break-all text-[12px] text-slate-700">
                      {r.target?.title || r.target?.post_title || r.target?.body || '内容已删除'}
                    </div>
                    {r.target?.body && r.target?.title && (
                      <div className="mt-0.5 line-clamp-1 text-[11.5px] text-slate-500">{r.target.body}</div>
                    )}
                    {r.target?.page && (
                      <a href={siteHref(`/${r.target.page}`)} target="_blank" rel="noreferrer"
                        className="break-all text-[11px] text-blue-600 hover:underline">{r.target.page} ↗</a>
                    )}
                  </div>
                )
              },
            },
            {
              title: '举报理由', width: 180,
              render: (_v, r) => (
                <div className="text-[12px]">
                  <div className="text-slate-700">{REASON[r.reason] || r.reason}</div>
                  {r.detail && <div className="mt-0.5 line-clamp-2 text-[11.5px] text-slate-500">{r.detail}</div>}
                </div>
              ),
            },
            {
              title: '举报人 / 时间', width: 140,
              render: (_v, r) => (
                <div className="text-[11.5px] text-slate-500">
                  <div className="text-slate-700">@{r.reporter?.handle || '—'}</div>
                  {when(r.created_at)}
                </div>
              ),
            },
            {
              title: '状态', width: 90,
              render: (_v, r) => {
                const s = STATUS[r.status] || { color: 'default', label: r.status }
                return <Tag color={s.color} style={{ marginInlineEnd: 0 }}>{s.label}</Tag>
              },
            },
            {
              title: '处置记录', width: 210,
              render: (_v, r) => r.resolution_note
                ? (
                  <div className="text-[11.5px] text-slate-600">
                    <div className="line-clamp-2 break-words">{r.resolution_note}</div>
                    {r.resolved_at && <div className="mt-0.5 text-[11px] text-slate-400">{when(r.resolved_at)}</div>}
                  </div>
                )
                : <span className="text-slate-300">—</span>,
            },
            {
              title: '操作', width: 170,
              render: (_v, r) => (
                <div className="flex flex-wrap gap-1.5">
                  {r.status === 'open' && (
                    <>
                      <Button size="small" danger
                        onClick={() => setActing({ report: r, action: 'hide' })}>隐藏</Button>
                      <Button size="small"
                        onClick={() => setActing({ report: r, action: 'dismiss' })}>驳回</Button>
                    </>
                  )}
                  {r.status === 'resolved' && r.target?.hidden && (
                    <Button size="small" type="primary"
                      onClick={() => setActing({ report: r, action: 'restore' })}>恢复</Button>
                  )}
                  {r.status !== 'open' && !(r.status === 'resolved' && r.target?.hidden) && (
                    <span className="text-[11.5px] text-slate-300">已处理</span>
                  )}
                </div>
              ),
            },
          ]}
          scroll={{ x: 1206 }}
        />
      )}

      {acting && (
        <ActionModal report={acting.report} action={acting.action}
          onClose={() => setActing(null)} />
      )}
    </div>
  )
}
