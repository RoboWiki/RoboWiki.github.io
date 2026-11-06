import 'antd/dist/reset.css'
import { App as AntApp, Input, Modal, Select } from 'antd'
import { EyeOutlined, MessageOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { KIND_LABEL, api, siteHref } from '@/lib/community-api'
import { CommunityHeader, IslandProvider, useAuth } from './providers'
import { CommentList, EmptyState, MarkdownBody, UserBadge, VoteButtons } from './ui'

const KIND_TONE: Record<string, string> = {
  discussion: 'bg-brand-soft text-brand',
  review: 'bg-success-soft text-success',
  build: 'bg-warning-soft text-warning',
}

function DetailSkeleton() {
  return (
    <div className="grid animate-pulse gap-5 lg:grid-cols-[minmax(0,1fr)_260px]" aria-hidden="true">
      <div className="card space-y-3 p-4 sm:p-6">
        <div className="flex gap-1.5">
          <div className="h-4 w-12 rounded-full bg-surface-3" />
          <div className="h-4 w-20 rounded-full bg-surface-3" />
        </div>
        <div className="h-7 w-3/4 rounded bg-surface-3" />
        <div className="flex gap-3">
          <div className="h-3 w-24 rounded bg-surface-3" />
          <div className="h-3 w-16 rounded bg-surface-3" />
        </div>
        <div className="space-y-2 border-t border-line pt-4">
          <div className="h-3 w-full rounded bg-surface-3" />
          <div className="h-3 w-11/12 rounded bg-surface-3" />
          <div className="h-3 w-4/5 rounded bg-surface-3" />
        </div>
      </div>
      <div className="card h-32" />
    </div>
  )
}

function Detail({ postId }: { postId: number }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const { user, openAuth } = useAuth()
  const [reportOpen, setReportOpen] = useState(false)
  const [reason, setReason] = useState('spam')
  const [detail, setDetail] = useState('')
  const [sending, setSending] = useState(false)

  const post = useQuery({
    queryKey: ['post', postId],
    queryFn: () => api.post(postId),
    retry: false,
  })

  const vote = async (v: number) => {
    if (!user) return openAuth()
    try {
      await api.vote('post', postId, v)
      qc.invalidateQueries({ queryKey: ['post', postId] })
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const submitReport = async () => {
    if (!user) return openAuth()
    setSending(true)
    try {
      await api.report({ target_kind: 'post', target_id: postId, reason, detail })
      message.success('已提交，站务会审核')
      setReportOpen(false)
      setDetail('')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSending(false)
    }
  }

  const p = post.data

  return (
    <div>
      <CommunityHeader current="community" />

      {post.isLoading ? <DetailSkeleton /> : !p ? (
        <EmptyState
          title="帖子不存在或已被隐藏"
          hint={post.error ? (post.error as Error).message : '链接可能不完整，或内容已被站务处理。'}
          action={
            <a href={siteHref('/community.html')}
              className="inline-flex h-9 items-center rounded-md bg-brand px-3.5 text-[13px] font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
              回社区
            </a>
          }
        />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
          <div className="min-w-0">
            <article className="card p-4 sm:p-6">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className={`inline-flex items-center rounded-full border border-line px-2 py-0.5 text-[11.5px] font-medium ${KIND_TONE[p.kind] || 'bg-surface-2 text-ink-2'}`}>
                  {KIND_LABEL[p.kind]}
                </span>
                {p.own_hardware && (
                  <span className="inline-flex items-center rounded-full border border-line bg-success-soft px-2 py-0.5 text-[11.5px] font-medium text-success">
                    实测
                  </span>
                )}
                {p.part_title && (
                  <span className="inline-flex items-center rounded-full border border-line bg-surface-2 px-2 py-0.5 text-[11.5px] font-medium text-ink-2">
                    {p.part_title}
                  </span>
                )}
                {p.tags.map(t => (
                  <span key={t} className="mono text-[11.5px] text-ink-3">#{t}</span>
                ))}
              </div>

              <h1 className="mt-2 text-[24px] font-extrabold leading-[1.25] tracking-tight text-ink sm:text-[28px]">
                {p.title}
              </h1>

              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-line pb-3 text-[12.5px] text-ink-3">
                {p.author ? (
                  <a href={siteHref(`/u.html?handle=${encodeURIComponent(p.author.handle)}`)}
                    className="hover:text-brand">
                    <UserBadge user={p.author} />
                  </a>
                ) : <UserBadge user={null} />}
                <span className="mono tabular">{new Date(p.created_at).toLocaleString('zh-CN')}</span>
                <span className="inline-flex items-center gap-1">
                  <EyeOutlined aria-hidden="true" />
                  <span className="mono tabular">{p.view_count}</span>
                  <span className="sr-only">次浏览</span>
                </span>
                {p.use_case && <span>用在：{p.use_case}</span>}
                <button type="button"
                  onClick={() => (user ? setReportOpen(true) : openAuth())}
                  className="ml-auto rounded px-1 text-[12px] text-ink-3 transition-colors hover:text-danger">
                  举报
                </button>
              </div>

              <div className="mt-4 flex gap-3 sm:gap-4">
                <VoteButtons score={p.score} myVote={p.my_vote} onVote={vote} />
                <div className="min-w-0 flex-1">
                  <MarkdownBody className="max-w-[70ch]">{p.body}</MarkdownBody>
                </div>
              </div>
            </article>

            <section id="comments" className="card mt-4 p-4 sm:p-6">
              <header className="mb-3 flex flex-wrap items-baseline justify-between gap-2 border-b border-line pb-2.5">
                <h2 className="m-0 flex items-center gap-1.5 text-[15px] font-semibold text-ink">
                  <MessageOutlined aria-hidden="true" className="text-ink-3" />
                  评论
                  <span className="mono tabular text-[13px] font-normal text-ink-3">({p.comment_count})</span>
                </h2>
                <span className="text-[11.5px] text-ink-3">按时间排序，回复挂在上一层下面</span>
              </header>
              {user
                ? <CommentList postId={postId} />
                : (
                  <div className="flex flex-col items-start gap-2 rounded-lg border border-line bg-surface-2 p-4">
                    <p className="m-0 text-[13px] text-ink-2">登录后才能评论、投票。</p>
                    <button type="button" onClick={openAuth}
                      className="inline-flex h-9 items-center rounded-md bg-brand px-3.5 text-[13px] font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
                      登录后参与讨论
                    </button>
                  </div>
                )}
            </section>
          </div>

          <aside className="min-w-0 space-y-3 lg:sticky lg:top-20 lg:self-start">
            <section className="card p-4">
              <h2 className="m-0 text-[13px] font-semibold text-ink">关于这条内容</h2>
              <p className="mb-3 mt-2 text-[12.5px] leading-6 text-ink-2">
                投票与评论都记在账号上；写实测数据比写“好用”有用。举报不会自动下架，站务核实后处理。
              </p>
              <a href={siteHref('/community.html')}
                className="inline-flex items-center text-[12.5px] text-ink-3 transition-colors hover:text-brand">
                ← 回社区
              </a>
            </section>

            <section className="card p-4">
              <h2 className="m-0 text-[13px] font-semibold text-ink">这条内容的口径</h2>
              <dl className="m-0 mt-2 space-y-1.5 text-[12px]">
                {[
                  { k: '类型', v: KIND_LABEL[p.kind] },
                  { k: '回复', v: String(p.comment_count) },
                  { k: '浏览', v: String(p.view_count) },
                  { k: '得分', v: String(p.score) },
                ].map(row => (
                  <div key={row.k} className="flex items-baseline justify-between gap-2">
                    <dt className="text-ink-3">{row.k}</dt>
                    <dd className="mono tabular m-0 text-ink-2">{row.v}</dd>
                  </div>
                ))}
              </dl>
            </section>
          </aside>
        </div>
      )}

      <Modal open={reportOpen} title="举报这条内容" onCancel={() => setReportOpen(false)}
        okText="提交举报" confirmLoading={sending} onOk={submitReport} destroyOnHidden>
        <div className="space-y-2.5 pt-1">
          <Select value={reason} onChange={setReason} style={{ width: '100%' }}
            options={[
              { value: 'spam', label: '垃圾广告' },
              { value: 'abuse', label: '攻击辱骂' },
              { value: 'misinfo', label: '虚假信息' },
              { value: 'other', label: '其他' },
            ]} />
          <Input.TextArea rows={3} value={detail} onChange={e => setDetail(e.target.value)}
            placeholder="补充说明（选填）" maxLength={500} />
          <p className="m-0 text-[12px] leading-5 text-ink-3">
            举报不会自动下架；站务核实后决定隐藏或驳回。
          </p>
        </div>
      </Modal>
    </div>
  )
}

export default function PostDetail({ postId }: { postId: number }) {
  return (
    <IslandProvider>
      <Detail postId={postId} />
    </IslandProvider>
  )
}
