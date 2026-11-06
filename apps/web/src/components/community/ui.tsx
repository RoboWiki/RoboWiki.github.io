import { App as AntApp, Button, Form, Input, Modal, Rate, Select, Tooltip } from 'antd'
import {
  ArrowDownOutlined, ArrowUpOutlined, CheckCircleFilled, CommentOutlined, EyeOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Markdown, { type Components } from 'react-markdown'
import { useMemo, useState, type ReactNode } from 'react'
import {
  KIND_LABEL, api, assetUrl, siteHref, type Comment, type Post, type User,
} from '@/lib/community-api'

// ── 时间 ──────────────────────────────────────────────────────────────────
export function ago(iso: string): string {
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return ''
  const s = Math.max(0, (Date.now() - t) / 1000)
  if (s < 60) return '刚刚'
  if (s < 3600) return `${Math.floor(s / 60)} 分钟前`
  if (s < 86400) return `${Math.floor(s / 3600)} 小时前`
  if (s < 86400 * 30) return `${Math.floor(s / 86400)} 天前`
  return new Date(iso).toLocaleDateString('zh-CN')
}

// ── 通用空状态 / 骨架 ─────────────────────────────────────────────────────
export function EmptyState({ title, hint, action }: {
  title: string; hint?: string; action?: ReactNode
}) {
  return (
    <div className="card flex flex-col items-center gap-2 px-6 py-12 text-center">
      <span aria-hidden="true"
        className="grid h-10 w-10 place-items-center rounded-full border border-line bg-surface-2 text-ink-3">
        <CommentOutlined />
      </span>
      <p className="mt-1 text-sm font-semibold text-ink">{title}</p>
      {hint && <p className="max-w-sm text-[12.5px] leading-5 text-ink-3">{hint}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

/** 与 PostCard 同构的加载骨架，避免列表在加载时跳高。 */
export function PostSkeleton() {
  return (
    <div className="card mb-3 animate-pulse p-3.5 sm:p-4" aria-hidden="true">
      <div className="flex items-start gap-3">
        <div className="h-16 w-9 shrink-0 rounded-full bg-surface-3" />
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex gap-1.5">
            <div className="h-4 w-12 rounded-full bg-surface-3" />
            <div className="h-4 w-16 rounded-full bg-surface-3" />
          </div>
          <div className="h-4 w-4/5 rounded bg-surface-3" />
          <div className="h-3 w-full rounded bg-surface-3" />
          <div className="h-3 w-3/5 rounded bg-surface-3" />
          <div className="flex gap-3 pt-1">
            <div className="h-3 w-24 rounded bg-surface-3" />
            <div className="h-3 w-14 rounded bg-surface-3" />
            <div className="h-3 w-12 rounded bg-surface-3" />
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Markdown 正文 ─────────────────────────────────────────────────────────
const MD_COMPONENTS: Components = {
  h1: ({ children }) => <h2 className="mt-5 mb-2 text-[20px] font-bold text-ink">{children}</h2>,
  h2: ({ children }) => <h3 className="mt-4 mb-2 text-[17px] font-bold text-ink">{children}</h3>,
  h3: ({ children }) => <h4 className="mt-3 mb-1.5 text-[15px] font-semibold text-ink">{children}</h4>,
  p: ({ children }) => <p className="my-2 leading-7 text-ink-2">{children}</p>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer noopener"
      className="text-brand underline underline-offset-2 hover:opacity-80">
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="my-2 list-disc pl-5 text-ink-2">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal pl-5 text-ink-2">{children}</ol>,
  li: ({ children }) => <li className="my-0.5">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-2 border-line-strong pl-3 text-ink-3">{children}</blockquote>
  ),
  code: ({ className, children }) => (
    className
      ? <code className={`${className} mono block overflow-x-auto rounded-lg border border-line bg-surface-2 p-3 text-[12.5px] text-ink-2`}>{children}</code>
      : <code className="mono rounded border border-line bg-surface-2 px-1 py-[1px] text-[12.5px] text-ink-2">{children}</code>
  ),
  pre: ({ children }) => <pre className="my-3 overflow-x-auto">{children}</pre>,
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full border-collapse text-[13px]">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-line bg-surface-2 px-2 py-1 text-left font-semibold text-ink">{children}</th>
  ),
  td: ({ children }) => <td className="border border-line px-2 py-1 text-ink-2">{children}</td>,
  img: ({ src, alt }) => (
    <img src={typeof src === 'string' ? src : undefined} alt={alt || ''} loading="lazy"
      className="my-3 max-w-full rounded-lg border border-line" />
  ),
  hr: () => <hr className="my-4 border-line" />,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
}

export function MarkdownBody({ children, className = '' }: {
  children: ReactNode; className?: string
}) {
  const source = typeof children === 'string' ? children : ''
  return (
    <div className={`min-w-0 text-[14px] leading-7 ${className}`}>
      <Markdown components={MD_COMPONENTS}>{source}</Markdown>
    </div>
  )
}

// ── 头像 ──────────────────────────────────────────────────────────────────
function hueOf(user?: User | null): number {
  return typeof user?.avatar_hue === 'number' && user.avatar_hue >= 0 ? user.avatar_hue : 160
}

/** 统一头像：有 avatar_url 用图，否则用 avatar_hue 底色 + 首字母。 */
export function Avatar({ user, size = 24, className = '' }: {
  user?: User | null; size?: number; className?: string
}) {
  const src = assetUrl(user?.avatar_url)
  const name = user?.display_name?.trim() || '?'
  if (src) {
    return (
      <img src={src} alt={`${name} 的头像`} width={size} height={size} loading="lazy"
        className={`shrink-0 rounded-full border border-line object-cover ${className}`}
        style={{ width: size, height: size }} />
    )
  }
  return (
    <span role="img" aria-label={`${name} 的头像`}
      className={`grid shrink-0 place-items-center rounded-full font-bold text-brand-fg ${className}`}
      style={{
        width: size,
        height: size,
        fontSize: Math.max(10, Math.round(size * 0.44)),
        backgroundColor: `hsl(${hueOf(user)} 52% 40%)`,
      }}>
      {name.slice(0, 1)}
    </span>
  )
}

export function UserBadge({ user, size = 24 }: { user?: User | null; size?: number }) {
  if (!user) return <span className="text-[12.5px] text-ink-3">已注销</span>
  return (
    <Tooltip title={`${user.display_name} · 声望 ${user.reputation}${user.badges?.length ? ' · ' + user.badges.join('/') : ''}`}>
      <span className="inline-flex min-w-0 items-center gap-1.5">
        <Avatar user={user} size={size} />
        <span className="truncate font-medium text-ink">{user.display_name}</span>
        <span className="mono tabular shrink-0 text-[11.5px] text-ink-3">{user.reputation}</span>
      </span>
    </Tooltip>
  )
}

// ── 投票 ──────────────────────────────────────────────────────────────────
export function VoteButtons({ score, myVote, onVote, disabled, compact = false }: {
  score: number; myVote: number; onVote: (v: number) => void; disabled?: boolean; compact?: boolean
}) {
  const base = 'grid place-items-center rounded-full transition-colors disabled:cursor-not-allowed disabled:opacity-50'
  const box = compact ? 'h-6 w-6 text-[11px]' : 'h-7 w-7 text-[12px]'

  const tone = (dir: 1 | -1) => {
    if (myVote !== dir) return 'text-ink-3 hover:bg-surface-3 hover:text-ink'
    return dir === 1
      ? 'bg-success-soft text-success'
      : 'bg-danger-soft text-danger'
  }

  return (
    <div className={`relative z-10 flex ${compact ? 'min-w-7' : 'min-w-9'} flex-col items-center gap-0.5 self-start`}>
      <button type="button" disabled={disabled}
        aria-label="赞同" aria-pressed={myVote === 1}
        title={myVote === 1 ? '已赞同，再点取消' : '赞同'}
        onClick={e => { e.stopPropagation(); onVote(myVote === 1 ? 0 : 1) }}
        className={`${base} ${box} ${tone(1)}`}>
        <ArrowUpOutlined />
      </button>
      <span className={`mono tabular font-semibold ${myVote !== 0 ? 'text-ink' : 'text-ink-2'} ${compact ? 'text-[12px]' : 'text-[13px]'}`}>
        {score}
      </span>
      <button type="button" disabled={disabled}
        aria-label="反对" aria-pressed={myVote === -1}
        title={myVote === -1 ? '已反对，再点取消' : '反对'}
        onClick={e => { e.stopPropagation(); onVote(myVote === -1 ? 0 : -1) }}
        className={`${base} ${box} ${tone(-1)}`}>
        <ArrowDownOutlined />
      </button>
    </div>
  )
}

// ── 徽标 ──────────────────────────────────────────────────────────────────
const KIND_TONE: Record<string, string> = {
  discussion: 'bg-brand-soft text-brand',
  review: 'bg-success-soft text-success',
  build: 'bg-warning-soft text-warning',
}

function Pill({ children, tone = 'bg-surface-2 text-ink-2' }: { children: ReactNode; tone?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 text-[11.5px] font-medium ${tone}`}>
      {children}
    </span>
  )
}

// ── 帖子卡片 ──────────────────────────────────────────────────────────────
export function PostCard({ post }: { post: Post }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const href = siteHref(`/post.html?id=${post.id}`)
  const vote = useMutation({
    mutationFn: (v: number) => api.vote('post', post.id, v),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['posts'] })
      qc.invalidateQueries({ queryKey: ['post', post.id] })
    },
    onError: (e: Error) => message.error(e.message),
  })
  const excerpt = post.body.replace(/[#>*`\-|]/g, ' ').replace(/\s+/g, ' ').slice(0, 180)

  return (
    <article className="card card-hover relative mb-3 p-3.5 sm:p-4">
      <div className="flex items-start gap-3">
        <VoteButtons score={post.score} myVote={post.my_vote} onVote={v => vote.mutate(v)} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            {post.pinned && <Pill tone="bg-warning-soft text-warning">置顶</Pill>}
            <Pill tone={KIND_TONE[post.kind]}>{KIND_LABEL[post.kind]}</Pill>
            {post.kind === 'discussion' && post.accepted_comment_id != null && (
              <Pill tone="bg-success-soft text-success">已解决</Pill>
            )}
            {post.own_hardware && <Pill tone="bg-success-soft text-success">实测</Pill>}
            {post.part_title && <Pill>{post.part_title}</Pill>}
            {post.rating != null && (
              <span className="inline-flex items-center gap-1">
                <Rate disabled value={post.rating} className="text-[11px]" style={{ fontSize: 11 }} />
              </span>
            )}
          </div>

          <h3 className="mt-1.5 text-[15.5px] font-semibold leading-snug tracking-tight">
            <a href={href}
              className="text-ink transition-colors after:absolute after:inset-0 after:content-[''] hover:text-brand">
              {post.title}
            </a>
          </h3>

          {excerpt && (
            <p className="mt-1 line-clamp-2 text-[13px] leading-6 text-ink-2">{excerpt}…</p>
          )}

          <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-ink-3">
            <UserBadge user={post.author} size={20} />
            <span className="mono tabular">{ago(post.created_at)}</span>
            <span className="inline-flex items-center gap-1">
              <CommentOutlined aria-hidden="true" />
              <span className="mono tabular">{post.comment_count}</span>
              <span className="sr-only">条回复</span>
            </span>
            <span className="inline-flex items-center gap-1">
              <EyeOutlined aria-hidden="true" />
              <span className="mono tabular">{post.view_count}</span>
              <span className="sr-only">次浏览</span>
            </span>
            {post.tags.length > 0 && (
              <span className="flex flex-wrap items-center gap-1.5">
                {post.tags.map(t => (
                  <span key={t} className="mono text-[11.5px] text-ink-3">#{t}</span>
                ))}
              </span>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}

// ── 表单分组标题 ──────────────────────────────────────────────────────────
function FormGroup({ title, hint, children }: {
  title: string; hint?: string; children: ReactNode
}) {
  return (
    <section className="border-t border-line pt-3 first:border-t-0 first:pt-0">
      <div className="mb-2 flex flex-wrap items-baseline gap-x-2">
        <h4 className="m-0 text-[12.5px] font-semibold text-ink">{title}</h4>
        {hint && <span className="text-[11.5px] text-ink-3">{hint}</span>}
      </div>
      {children}
    </section>
  )
}

// ── 发帖 ──────────────────────────────────────────────────────────────────
export function Composer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const kind = Form.useWatch('kind', form) || 'discussion'
  const [partQuery, setPartQuery] = useState('')

  const parts = useQuery({
    queryKey: ['parts-lite', partQuery],
    queryFn: () => api.parts({ q: partQuery, limit: 20 }),
    enabled: open,
  })

  const create = useMutation({
    mutationFn: (body: unknown) => api.createPost(body),
    onSuccess: () => {
      message.success('已发布')
      qc.invalidateQueries({ queryKey: ['posts'] })
      form.resetFields()
      onClose()
    },
    onError: (e: Error) => message.error(e.message),
  })

  return (
    <Modal open={open} onCancel={onClose} title="发帖" width={720} destroyOnHidden
      okText="发布" confirmLoading={create.isPending}
      onOk={async () => {
        const v = await form.validateFields()
        create.mutate({
          kind: v.kind, title: v.title, body: v.body,
          part_id: v.part_id || null,
          tags: (v.tags || []).join(','),
          rating: v.kind === 'review' ? v.rating : null,
          use_case: v.use_case || null,
          own_hardware: !!v.own_hardware,
          total_price_cny: v.kind === 'build' && v.total_price_cny ? Number(v.total_price_cny) : null,
          price_scope: v.kind === 'build' ? (v.price_scope || null) : null,
          price_verified: !!(v.kind === 'build' && v.price_verified),
        })
      }}>
      <Form form={form} layout="vertical" initialValues={{ kind: 'discussion', rating: 5 }}
        requiredMark={false} className="space-y-4 pt-1">
        <FormGroup title="内容" hint="标题一句话说清核心；正文写清工况与数据">
          <Form.Item name="kind" label="类型" rules={[{ required: true }]} className="mb-3">
            <Select options={[
              { value: 'discussion', label: '讨论 — 问题、方法论、踩坑' },
              { value: 'review', label: '评价 — 挂在某个零件上的真实使用反馈' },
              { value: 'build', label: '整机方案 — 一台机器的 BOM 与取舍' },
            ]} />
          </Form.Item>
          <Form.Item name="title" label="标题" className="mb-3" rules={[{ required: true, min: 4, max: 120 }]}>
            <Input placeholder="一句话说清这条的核心" showCount maxLength={120} />
          </Form.Item>
          <Form.Item name="body" label="正文（支持 Markdown）" className="mb-0" rules={[{ required: true, min: 10 }]}>
            <Input.TextArea rows={9} maxLength={20000} showCount
              placeholder="写实测数据比写“好用”有用：哪个关节、多大负载、跑多久、出了什么问题。" />
          </Form.Item>
        </FormGroup>

        <FormGroup title="关联" hint="评价必须挂零件，会自动出现在该零件详情里">
          <div className="grid gap-3 sm:grid-cols-2">
            <Form.Item name="part_id" label="关联零件（评价必填）" className="mb-0">
              <Select allowClear showSearch filterOption={false}
                onSearch={setPartQuery}
                loading={parts.isLoading}
                placeholder="搜型号 / 厂商"
                options={(parts.data?.items || []).map(p => ({
                  value: p.id, label: `${p.model} · ${p.vendor}`,
                }))} />
            </Form.Item>
            <Form.Item name="tags" label="标签" className="mb-0">
              <Select mode="tags" placeholder="回车添加，如 温升 / 背隙 / CAN-FD"
                tokenSeparators={[',', '，']} />
            </Form.Item>
          </div>

          {kind === 'review' && (
            <div className="mt-3 grid gap-3 sm:grid-cols-[auto_1fr_auto]">
              <Form.Item name="rating" label="评分" className="mb-0" rules={[{ required: true }]}>
                <Rate />
              </Form.Item>
              <Form.Item name="use_case" label="用在" className="mb-0">
                <Select allowClear
                  options={['四足', '人形', '机械臂', '其他'].map(v => ({ value: v, label: v }))} />
              </Form.Item>
              <Form.Item name="own_hardware" label="我实际用过" valuePropName="checked" className="mb-0">
                <input type="checkbox" className="h-[18px] w-[18px] accent-[var(--rw-primary)]" />
              </Form.Item>
            </div>
          )}
        </FormGroup>

        {kind === 'build' && (
          <FormGroup title="整机报价" hint="必须说明覆盖范围——只给一个数字比不给更有害">
            <div className="grid gap-3 sm:grid-cols-2">
              <Form.Item name="total_price_cny" label="整机报价（¥）" className="mb-0">
                <Input type="number" placeholder="30000" />
              </Form.Item>
              <Form.Item name="price_verified" label="价格已核实" valuePropName="checked" className="mb-0">
                <input type="checkbox" className="h-[18px] w-[18px] accent-[var(--rw-primary)]" />
              </Form.Item>
            </div>
            <Form.Item name="price_scope" label="覆盖范围（必填，若有报价）" className="mb-0 mt-3"
              rules={[({ getFieldValue }) => ({
                validator(_, v) {
                  if (getFieldValue('total_price_cny') && !v) {
                    return Promise.reject(new Error('有报价就必须写清覆盖范围'))
                  }
                  return Promise.resolve()
                },
              })]}>
              <Input placeholder="12 个关节 + 上位机；结构件、电池、打印件另计" />
            </Form.Item>
          </FormGroup>
        )}

        <p className="m-0 text-[11.5px] leading-5 text-ink-3">
          发布后仍可编辑；被举报并核实的内容会被隐藏，作者可申诉。
        </p>
      </Form>
    </Modal>
  )
}

// ── 评论 ──────────────────────────────────────────────────────────────────
type AcceptProps = {
  acceptedId: number | null
  canAccept: boolean
  onAccept: (commentId: number, accepted: boolean) => void
  acceptingId: number | null
}

function CommentNode({ c, postId, depth = 0, acceptedId, canAccept, onAccept, acceptingId }: {
  c: Comment; postId: number; depth?: number
} & AcceptProps) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [replying, setReplying] = useState(false)
  const [text, setText] = useState('')
  const accepted = c.accepted === true || c.id === acceptedId

  const vote = useMutation({
    mutationFn: (v: number) => api.vote('comment', c.id, v),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['comments', postId] }),
    onError: (e: Error) => message.error(e.message),
  })
  const reply = useMutation({
    mutationFn: () => api.createComment(postId, { body: text, parent_id: c.id }),
    onSuccess: () => {
      setText('')
      setReplying(false)
      qc.invalidateQueries({ queryKey: ['comments', postId] })
      qc.invalidateQueries({ queryKey: ['post', postId] })
    },
    onError: (e: Error) => message.error(e.message),
  })

  const nested = depth > 0
  const action = 'inline-flex min-h-11 items-center rounded px-1 text-[12px] transition-colors sm:min-h-8'

  return (
    <div className={nested ? 'mt-3 border-l border-line pl-3 sm:pl-4' : 'mt-3'}>
      <div className={`flex gap-2.5 ${accepted ? 'rounded-lg border border-success/35 bg-success-soft/55 p-2.5 sm:p-3' : ''}`}>
        <VoteButtons compact score={c.score} myVote={c.my_vote} onVote={v => vote.mutate(v)} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[12px] text-ink-3">
            <UserBadge user={c.author} size={20} />
            <span className="mono tabular">{ago(c.created_at)}</span>
            {accepted && (
              <span className="inline-flex items-center gap-1 rounded-full border border-success/35 bg-success-soft px-2 py-0.5 text-[11.5px] font-semibold text-success">
                <CheckCircleFilled aria-hidden="true" />
                已采纳
              </span>
            )}
            {depth === 0 && (
              <button type="button" onClick={() => setReplying(v => !v)}
                aria-expanded={replying}
                className={`${action} text-ink-3 hover:text-brand`}>
                回复
              </button>
            )}
            {canAccept && (
              <button type="button" disabled={acceptingId === c.id}
                onClick={() => onAccept(c.id, accepted)}
                aria-pressed={accepted}
                className={`${action} disabled:cursor-not-allowed disabled:opacity-50 ${
                  accepted ? 'text-ink-3 hover:text-danger' : 'font-medium text-brand hover:bg-brand-soft'
                }`}>
                {acceptingId === c.id ? '处理中…' : accepted ? '取消采纳' : '采纳'}
              </button>
            )}
          </div>

          <div className="mt-1 whitespace-pre-wrap text-[13.5px] leading-6 text-ink-2">{c.body}</div>

          {replying && (
            <div className="mt-2 flex flex-col gap-2 sm:flex-row">
              <Input.TextArea autoSize={{ minRows: 1, maxRows: 4 }} value={text}
                onChange={e => setText(e.target.value)} placeholder="回复…" />
              <Button type="primary" loading={reply.isPending}
                onClick={() => text.trim().length >= 2 && reply.mutate()}>发送</Button>
            </div>
          )}
        </div>
      </div>

      {c.replies?.length > 0 && (
        <div className="mt-1">
          {c.replies.map(r => (
            <CommentNode key={r.id} c={r} postId={postId} depth={depth + 1}
              acceptedId={acceptedId} canAccept={canAccept}
              onAccept={onAccept} acceptingId={acceptingId} />
          ))}
        </div>
      )}
    </div>
  )
}

export function CommentList({ postId, acceptedId = null, canAccept = false }: {
  postId: number
  acceptedId?: number | null
  canAccept?: boolean
}) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [text, setText] = useState('')
  const [acceptingId, setAcceptingId] = useState<number | null>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['comments', postId], queryFn: () => api.comments(postId),
  })
  const add = useMutation({
    mutationFn: () => api.createComment(postId, { body: text }),
    onSuccess: () => {
      setText('')
      qc.invalidateQueries({ queryKey: ['comments', postId] })
      qc.invalidateQueries({ queryKey: ['post', postId] })
    },
    onError: (e: Error) => message.error(e.message),
  })

  // 已采纳的评论排在最前：读者先看到结论，再看讨论过程。
  const ordered = useMemo(() => {
    const rows = [...(data || [])]
    rows.sort((a, b) => {
      const aa = a.accepted === true || a.id === acceptedId ? 1 : 0
      const bb = b.accepted === true || b.id === acceptedId ? 1 : 0
      return bb - aa
    })
    return rows
  }, [data, acceptedId])

  const accept = async (commentId: number, accepted: boolean) => {
    setAcceptingId(commentId)
    try {
      if (accepted) await api.unacceptComment(postId)
      else await api.acceptComment(postId, commentId)
      await Promise.all([
        qc.invalidateQueries({ queryKey: ['comments', postId] }),
        qc.invalidateQueries({ queryKey: ['post', postId] }),
        qc.invalidateQueries({ queryKey: ['posts'] }),
      ])
      message.success(accepted ? '已取消采纳' : '已采纳这条回复')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setAcceptingId(null)
    }
  }

  return (
    <div>
      <div className="rounded-lg border border-line bg-surface-2 p-2.5">
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input.TextArea autoSize={{ minRows: 2, maxRows: 6 }} value={text}
            onChange={e => setText(e.target.value)} placeholder="补充实测数据、提问或反驳…" />
          <Button type="primary" loading={add.isPending} className="sm:self-end"
            onClick={() => text.trim().length >= 2 && add.mutate()}>评论</Button>
        </div>
        <p className="m-0 mt-1.5 text-[11.5px] text-ink-3">
          评论至少 2 个字；写清工况比下结论有用。
        </p>
      </div>

      {isLoading ? (
        <div className="mt-4 space-y-2" aria-hidden="true">
          {[0, 1].map(i => (
            <div key={i} className="flex animate-pulse gap-2.5 py-2">
              <div className="h-14 w-7 shrink-0 rounded-full bg-surface-3" />
              <div className="min-w-0 flex-1 space-y-2">
                <div className="h-3 w-40 rounded bg-surface-3" />
                <div className="h-3 w-full rounded bg-surface-3" />
              </div>
            </div>
          ))}
        </div>
      ) : !ordered.length ? (
        <EmptyState title="还没有回复" hint="来说第一句：哪个参数不对、哪个工况没覆盖。" />
      ) : (
        <div className="mt-1 divide-y divide-line">
          {ordered.map(c => (
            <CommentNode key={c.id} c={c} postId={postId}
              acceptedId={acceptedId} canAccept={canAccept}
              onAccept={accept} acceptingId={acceptingId} />
          ))}
        </div>
      )}
    </div>
  )
}
