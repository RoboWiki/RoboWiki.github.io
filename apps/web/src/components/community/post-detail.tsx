import 'antd/dist/reset.css'
import { Alert, App as AntApp, Input, Modal, Rate, Select } from 'antd'
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
  const { message, modal } = AntApp.useApp()
  const { user, openAuth } = useAuth()
  const [reportOpen, setReportOpen] = useState(false)
  const [reason, setReason] = useState('spam')
  const [detail, setDetail] = useState('')
  const [sending, setSending] = useState(false)

  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editBody, setEditBody] = useState('')
  const [editTags, setEditTags] = useState<string[]>([])
  const [editRating, setEditRating] = useState(5)
  const [editError, setEditError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

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
  const canManage = !!p && !!user && (user.is_staff || user.id === p.author?.id)

  const beginEdit = () => {
    if (!p) return
    setEditTitle(p.title)
    setEditBody(p.body)
    setEditTags(p.tags || [])
    setEditRating(p.rating ?? 5)
    setEditError(null)
    setActionError(null)
    setEditing(true)
  }

  const saveEdit = async () => {
    if (!p || saving) return
    const title = editTitle.trim()
    const body = editBody.trim()
    if (title.length < 4) return setEditError('标题至少 4 个字')
    if (body.length < 10) return setEditError('正文至少 10 个字')
    setSaving(true)
    setEditError(null)
    try {
      const payload: Record<string, unknown> = { title, body, tags: editTags.join(',') }
      if (p.kind === 'review') payload.rating = editRating
      const updated = await api.updatePost(postId, payload)
      qc.setQueryData(['post', postId], updated)
      await qc.invalidateQueries({ queryKey: ['posts'] })
      setEditing(false)
      message.success('已保存修改')
    } catch (e) {
      setEditError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const removePost = () => {
    modal.confirm({
      title: '删除这条内容？',
      content: '删除后讨论与回复都会一并消失，且无法恢复。',
      okText: '删除',
      cancelText: '保留',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await api.deletePost(postId)
          await qc.invalidateQueries({ queryKey: ['posts'] })
          message.success('已删除')
          window.location.assign(siteHref('/community.html'))
        } catch (e) {
          setActionError((e as Error).message)
        }
      },
    })
  }

  return (
    <div>
      <CommunityHeader current="community" />

      {actionError && (
        <div role="alert" className="mb-3">
          <Alert type="error" showIcon title={actionError}
            closable onClose={() => setActionError(null)} />
        </div>
      )}

      {post.isLoading ? <DetailSkeleton /> : !p ? (
        <EmptyState
          title="帖子不存在或已被隐藏"
          hint={post.error ? (post.error as Error).message : '链接可能不完整，或内容已被站务处理。'}
          action={
            <a href={siteHref('/community.html')}
              className="inline-flex h-9 items-center rounded-md bg-brand px-3.5 text-sm font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
              回社区
            </a>
          }
        />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
          <div className="min-w-0">
            <article className="card p-4 sm:p-6">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className={`inline-flex items-center rounded-full border border-line px-2 py-0.5 text-xs font-medium ${KIND_TONE[p.kind] || 'bg-surface-2 text-ink-2'}`}>
                  {KIND_LABEL[p.kind]}
                </span>
                {p.accepted_comment_id != null && (
                  <span className="inline-flex items-center rounded-full border border-success/35 bg-success-soft px-2 py-0.5 text-xs font-semibold text-success">
                    已解决
                  </span>
                )}
                {p.own_hardware && (
                  <span className="inline-flex items-center rounded-full border border-line bg-success-soft px-2 py-0.5 text-xs font-medium text-success">
                    实测
                  </span>
                )}
                {p.part_title && (
                  <span className="inline-flex items-center rounded-full border border-line bg-surface-2 px-2 py-0.5 text-xs font-medium text-ink-2">
                    {p.part_title}
                  </span>
                )}
                {p.tags.map(t => (
                  <span key={t} className="mono text-xs text-ink-3">#{t}</span>
                ))}
              </div>

              {editing ? (
                <div className="mt-3 space-y-3">
                  <div>
                    <label htmlFor="edit-title" className="mb-1 block text-xs font-medium text-ink-2">标题</label>
                    <Input id="edit-title" value={editTitle} maxLength={120} showCount
                      onChange={e => setEditTitle(e.target.value)} />
                  </div>
                  <div>
                    <label htmlFor="edit-body" className="mb-1 block text-xs font-medium text-ink-2">
                      正文（支持 Markdown）
                    </label>
                    <Input.TextArea id="edit-body" rows={10} value={editBody} maxLength={20000}
                      onChange={e => setEditBody(e.target.value)} />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <label htmlFor="edit-tags" className="mb-1 block text-xs font-medium text-ink-2">标签</label>
                      <Select id="edit-tags" mode="tags" value={editTags} onChange={setEditTags}
                        tokenSeparators={[',', '，']} style={{ width: '100%' }}
                        placeholder="回车添加标签" />
                    </div>
                    {p.kind === 'review' && (
                      <div>
                        <span className="mb-1 block text-xs font-medium text-ink-2">评分</span>
                        <Rate value={editRating} onChange={setEditRating} />
                      </div>
                    )}
                  </div>

                  <div aria-live="polite">
                    {editError && (
                      <p role="alert"
                        className="m-0 rounded-md border border-danger/35 bg-danger-soft px-3 py-2 text-sm leading-5 text-danger">
                        {editError}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 border-t border-line pt-3">
                    <button type="button" onClick={saveEdit} disabled={saving}
                      className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 text-sm font-semibold text-brand-fg transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-60 sm:min-h-9">
                      {saving ? '保存中…' : '保存修改'}
                    </button>
                    <button type="button" onClick={() => setEditing(false)} disabled={saving}
                      className="inline-flex min-h-11 items-center rounded-md border border-line bg-surface px-4 text-sm text-ink-2 transition-colors hover:border-line-strong hover:text-ink disabled:opacity-60 sm:min-h-9">
                      取消
                    </button>
                    <span className="text-xs text-ink-3">修改后会记录编辑时间，讨论不受影响。</span>
                  </div>
                </div>
              ) : (
                <>
                  <h1 className="mt-2 text-[24px] font-extrabold leading-[1.25] tracking-tight text-ink sm:text-[28px]">
                    {p.title}
                  </h1>

                  <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-line pb-3 text-sm text-ink-3">
                    {p.author ? (
                      <a href={siteHref(`/u.html?handle=${encodeURIComponent(p.author.handle)}`)}
                        className="hover:text-brand">
                        <UserBadge user={p.author} />
                      </a>
                    ) : <UserBadge user={null} />}
                    <span className="mono tabular">{new Date(p.created_at).toLocaleString('zh-CN')}</span>
                    {p.updated_at && p.updated_at !== p.created_at && (
                      <span className="mono tabular">已编辑 {new Date(p.updated_at).toLocaleDateString('zh-CN')}</span>
                    )}
                    <span className="inline-flex items-center gap-1">
                      <EyeOutlined aria-hidden="true" />
                      <span className="mono tabular">{p.view_count}</span>
                      <span className="sr-only">次浏览</span>
                    </span>
                    {p.use_case && <span>用在：{p.use_case}</span>}

                    <span className="ml-auto flex items-center gap-1">
                      {canManage ? (
                        <>
                          <button type="button" onClick={beginEdit}
                            className="inline-flex min-h-11 items-center rounded px-2 text-xs text-ink-2 transition-colors hover:bg-surface-3 hover:text-ink sm:min-h-8">
                            编辑
                          </button>
                          <button type="button" onClick={removePost}
                            className="inline-flex min-h-11 items-center rounded px-2 text-xs text-ink-3 transition-colors hover:bg-danger-soft hover:text-danger sm:min-h-8">
                            删除
                          </button>
                        </>
                      ) : (
                        <button type="button"
                          onClick={() => (user ? setReportOpen(true) : openAuth())}
                          className="inline-flex min-h-11 items-center rounded px-2 text-xs text-ink-3 transition-colors hover:text-danger sm:min-h-8">
                          举报
                        </button>
                      )}
                    </span>
                  </div>

                  <div className="mt-4 min-w-0">
                    <MarkdownBody className="max-w-[70ch]">{p.body}</MarkdownBody>
                  </div>
                  <div className="mt-4 flex justify-end border-t border-line pt-3">
                    <VoteButtons score={p.score} myVote={p.my_vote} onVote={vote} />
                  </div>
                </>
              )}
            </article>

            <section id="comments" className="card mt-4 p-4 sm:p-6">
              <header className="mb-3 flex flex-wrap items-baseline justify-between gap-2 border-b border-line pb-2.5">
                <h2 className="m-0 flex items-center gap-1.5 text-base font-semibold text-ink">
                  <MessageOutlined aria-hidden="true" className="text-ink-3" />
                  评论
                  <span className="mono tabular text-sm font-normal text-ink-3">({p.comment_count})</span>
                  {p.accepted_comment_id != null && (
                    <span className="text-xs font-normal text-success">· 已采纳一条回复</span>
                  )}
                </h2>
                <span className="text-xs text-ink-3">
                  {canManage ? '你是作者，可以采纳一条回复作为结论' : '按时间排序，采纳的回复会置顶'}
                </span>
              </header>
              {user
                ? <CommentList postId={postId} acceptedId={p.accepted_comment_id ?? null}
                    canAccept={canManage} />
                : (
                  <div className="flex flex-col items-start gap-2 rounded-lg border border-line bg-surface-2 p-4">
                    <p className="m-0 text-sm text-ink-2">登录后才能评论、投票。</p>
                    <button type="button" onClick={openAuth}
                      className="inline-flex h-9 items-center rounded-md bg-brand px-3.5 text-sm font-semibold text-brand-fg transition-colors hover:bg-brand-hover">
                      登录后参与讨论
                    </button>
                  </div>
                )}
            </section>
          </div>

          <aside className="min-w-0 space-y-3 lg:sticky lg:top-20 lg:self-start">
            <section className="card p-4">
              <h2 className="m-0 text-sm font-semibold text-ink">关于这条内容</h2>
              <p className="mb-3 mt-2 text-sm leading-6 text-ink-2">
                投票与评论都记在账号上；写实测数据比写“好用”有用。举报不会自动下架，站务核实后处理。
              </p>
              <a href={siteHref('/community.html')}
                className="inline-flex items-center text-sm text-ink-3 transition-colors hover:text-brand">
                ← 回社区
              </a>
            </section>

            <section className="card p-4">
              <h2 className="m-0 text-sm font-semibold text-ink">这条内容的口径</h2>
              <dl className="m-0 mt-2 space-y-1.5 text-xs">
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
          <p className="m-0 text-xs leading-5 text-ink-3">
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
