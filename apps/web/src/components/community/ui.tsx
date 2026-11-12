import { App as AntApp, Button, Form, Input, Modal, Rate, Select, Tooltip } from 'antd'
import {
  CheckCircleFilled, CommentOutlined, DislikeFilled, DislikeOutlined, EyeOutlined,
  LikeFilled, LikeOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Markdown, { type Components } from 'react-markdown'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  KIND_LABEL, api, assetUrl, siteHref, type Comment, type Post, type User,
} from '@/lib/community-api'
import { api as coreApi } from '@/lib/api'
import {
  clearDraft, loadDraft, normalizeDraft, recordActivity, saveDraft,
  type ComposerDraft,
} from '@/lib/local-activity'

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
      {hint && <p className="max-w-sm text-sm leading-5 text-ink-3">{hint}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

/** 与 PostCard 同构的加载骨架，避免列表在加载时跳高。 */
export function PostSkeleton() {
  return (
    <div className="card mb-3 animate-pulse p-3.5 sm:p-4" aria-hidden="true">
      <div className="space-y-2">
        <div className="flex gap-1.5">
          <div className="h-4 w-12 rounded-full bg-surface-3" />
          <div className="h-4 w-16 rounded-full bg-surface-3" />
        </div>
        <div className="h-4 w-4/5 rounded bg-surface-3" />
        <div className="h-3 w-full rounded bg-surface-3" />
        <div className="h-3 w-3/5 rounded bg-surface-3" />
        <div className="flex items-center gap-3 pt-1">
          <div className="h-3 w-24 rounded bg-surface-3" />
          <div className="h-3 w-14 rounded bg-surface-3" />
          <div className="h-3 w-12 rounded bg-surface-3" />
          <div className="ml-auto h-7 w-32 rounded-full bg-surface-3" />
        </div>
      </div>
    </div>
  )
}

// ── Markdown 正文 ─────────────────────────────────────────────────────────
const MD_COMPONENTS: Components = {
  h1: ({ children }) => <h2 className="mt-5 mb-2 text-[20px] font-bold text-ink">{children}</h2>,
  h2: ({ children }) => <h3 className="mt-4 mb-2 text-[17px] font-bold text-ink">{children}</h3>,
  h3: ({ children }) => <h4 className="mt-3 mb-1.5 text-base font-semibold text-ink">{children}</h4>,
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
      ? <code className={`${className} mono block overflow-x-auto rounded-lg border border-line bg-surface-2 p-3 text-sm text-ink-2`}>{children}</code>
      : <code className="mono rounded border border-line bg-surface-2 px-1 py-[1px] text-sm text-ink-2">{children}</code>
  ),
  pre: ({ children }) => <pre className="my-3 overflow-x-auto">{children}</pre>,
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full border-collapse text-sm">{children}</table>
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
    <div className={`min-w-0 text-sm leading-7 ${className}`}>
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
  if (!user) return <span className="text-sm text-ink-3">已注销</span>
  return (
    <Tooltip title={`${user.display_name} · 声望 ${user.reputation}${user.badges?.length ? ' · ' + user.badges.join('/') : ''}`}>
      <span className="inline-flex min-w-0 items-center gap-1.5">
        <Avatar user={user} size={size} />
        <span className="truncate font-medium text-ink">{user.display_name}</span>
        <span className="mono tabular shrink-0 text-xs text-ink-3">{user.reputation}</span>
      </span>
    </Tooltip>
  )
}

// ── 投票 ──────────────────────────────────────────────────────────────────
export function VoteButtons({ score, myVote, onVote, disabled, compact = false }: {
  score: number; myVote: number; onVote: (v: number) => void; disabled?: boolean; compact?: boolean
}) {
  const button = `inline-flex items-center justify-center gap-1.5 rounded-full font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
    compact ? 'h-6 min-w-6 px-1.5 text-xs' : 'h-8 px-2.5 text-sm'
  }`
  const tone = (dir: 1 | -1) => {
    if (myVote !== dir) {
      return dir === 1
        ? 'text-ink-3 hover:bg-success-soft/70 hover:text-success'
        : 'text-ink-3 hover:bg-danger-soft/70 hover:text-danger'
    }
    return dir === 1 ? 'bg-success-soft text-success' : 'bg-danger-soft text-danger'
  }
  const title = (dir: 1 | -1) => {
    const name = dir === 1 ? '赞同' : '反对'
    return myVote === dir ? `已${name}，再点取消` : name
  }

  return (
    <div role="group" aria-label="投票"
      className={`relative z-10 inline-flex shrink-0 items-center rounded-full border border-line bg-surface-2/70 p-0.5 ${
        compact ? '' : 'shadow-[0_1px_0_rgba(0,0,0,0.04)]'
      }`}>
      <button type="button" disabled={disabled}
        aria-label="赞同" aria-pressed={myVote === 1}
        title={title(1)}
        onClick={e => { e.stopPropagation(); onVote(myVote === 1 ? 0 : 1) }}
        className={`${button} ${tone(1)}`}>
        {myVote === 1 ? <LikeFilled aria-hidden="true" /> : <LikeOutlined aria-hidden="true" />}
        {!compact && <span>赞同</span>}
      </button>
      <span aria-hidden="true" className="mx-0.5 h-4 w-px bg-line" />
      <span aria-live="polite" aria-label={`净赞同 ${score}`}
        title="净赞同数 = 赞同 − 反对"
        className={`mono tabular text-center font-semibold ${myVote !== 0 ? 'text-ink' : 'text-ink-2'} ${
          compact ? 'min-w-6 px-1 text-xs' : 'min-w-7 px-1.5 text-sm'
        }`}>
        {score}
      </span>
      <span aria-hidden="true" className="mx-0.5 h-4 w-px bg-line" />
      <button type="button" disabled={disabled}
        aria-label="反对" aria-pressed={myVote === -1}
        title={title(-1)}
        onClick={e => { e.stopPropagation(); onVote(myVote === -1 ? 0 : -1) }}
        className={`${button} ${tone(-1)}`}>
        {!compact && <span>反对</span>}
        {myVote === -1 ? <DislikeFilled aria-hidden="true" /> : <DislikeOutlined aria-hidden="true" />}
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
    <span className={`inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 text-xs font-medium ${tone}`}>
      {children}
    </span>
  )
}

// ── 帖子卡片 ──────────────────────────────────────────────────────────────
export function PostCard({ post, onTag }: {
  post: Post
  /** 传入时标签变成可点筛选；不传保持纯展示，不影响其他使用处。 */
  onTag?: (tag: string) => void
}) {
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
      <div className="flex flex-wrap items-center gap-1.5">
        {post.pinned && <Pill tone="bg-warning-soft text-warning">置顶</Pill>}
        {post.locked && <Pill tone="bg-surface-3 text-ink-2">已锁定</Pill>}
        <Pill tone={KIND_TONE[post.kind]}>{KIND_LABEL[post.kind]}</Pill>
        {post.kind === 'discussion' && post.accepted_comment_id != null && (
          <Pill tone="bg-success-soft text-success">已解决</Pill>
        )}
        {post.own_hardware && <Pill tone="bg-success-soft text-success">实测</Pill>}
        {post.part_title && <Pill>{post.part_title}</Pill>}
        {post.rating != null && (
          <span className="inline-flex items-center gap-1">
            <Rate disabled value={post.rating} className="text-xs" style={{ fontSize: 11 }} />
          </span>
        )}
      </div>

      <h3 className="mt-1.5 text-base font-semibold leading-snug tracking-tight">
        <a href={href}
          className="text-ink transition-colors after:absolute after:inset-0 after:content-[''] hover:text-brand">
          {post.title}
        </a>
      </h3>

      {excerpt && (
        <p className="mt-1 line-clamp-2 text-sm leading-6 text-ink-2">{excerpt}…</p>
      )}

      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-ink-3">
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
          <span className="relative z-10 flex flex-wrap items-center gap-1.5">
            {post.tags.map(t => onTag ? (
              <button key={t} type="button"
                onClick={e => {
                  // 整张卡片被标题链接的 ::after 覆盖，点标签不能触发跳转。
                  e.preventDefault()
                  e.stopPropagation()
                  onTag(t)
                }}
                className="mono rounded text-xs text-ink-3 transition-colors hover:text-brand focus-visible:text-brand">
                #{t}
              </button>
            ) : (
              <span key={t} className="mono text-xs text-ink-3">#{t}</span>
            ))}
          </span>
        )}
        <span className="ml-auto">
          <VoteButtons score={post.score} myVote={post.my_vote} onVote={v => vote.mutate(v)} />
        </span>
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
        <h4 className="m-0 text-sm font-semibold text-ink">{title}</h4>
        {hint && <span className="text-xs text-ink-3">{hint}</span>}
      </div>
      {children}
    </section>
  )
}

// ── 发帖 ──────────────────────────────────────────────────────────────────
/** 零件页「写评价」入口带进来的预填参数。 */
export interface ComposerPrefill {
  kind: 'review'
  partId: string
}

export function Composer({ open, onClose, prefill = null }: {
  open: boolean
  onClose: () => void
  prefill?: ComposerPrefill | null
}) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const kind = Form.useWatch('kind', form) || 'discussion'
  const [partQuery, setPartQuery] = useState('')
  // 本地草稿：打开时提示恢复/丢弃；编辑时自动保存；发布成功清掉。
  const [draft, setDraft] = useState<ComposerDraft | null>(null)
  const saveTimer = useRef<number | null>(null)

  const flushDraftTimer = () => {
    if (saveTimer.current != null) {
      window.clearTimeout(saveTimer.current)
      saveTimer.current = null
    }
  }

  useEffect(() => {
    if (!open) {
      setDraft(null)
      flushDraftTimer()
      return
    }
    setDraft(loadDraft())
    return () => flushDraftTimer()
  }, [open])

  useEffect(() => () => flushDraftTimer(), [])

  const parts = useQuery({
    queryKey: ['parts-lite', partQuery],
    queryFn: () => api.parts({ q: partQuery, limit: 20 }),
    enabled: open,
  })

  // 零件页「写评价」预填：标题需要型号，评分需要本人已有打分。
  const prefillPartId = prefill?.partId ?? null
  const prefillPart = useQuery({
    queryKey: ['part-lite', prefillPartId],
    queryFn: () => api.part(prefillPartId as string),
    enabled: open && !!prefillPartId,
    staleTime: 5 * 60_000,
    retry: false,
  })
  const myRating = useQuery({
    queryKey: ['rating-mine', prefillPartId],
    queryFn: () => coreApi.getRating(prefillPartId as string),
    enabled: open && !!prefillPartId,
    staleTime: 60_000,
    retry: false,
  })

  // 只在首次打开时填一次：用户改过（或被草稿恢复覆盖）就不再动。
  const prefilledKind = useRef(false)
  const prefilledTitle = useRef(false)
  const prefilledRating = useRef(false)

  useEffect(() => {
    if (!open) {
      prefilledKind.current = false
      prefilledTitle.current = false
      prefilledRating.current = false
      return
    }
    if (!prefill || prefilledKind.current) return
    prefilledKind.current = true
    form.setFieldsValue({ kind: prefill.kind, part_id: prefill.partId })
  }, [open, prefill, form])

  useEffect(() => {
    if (!open || !prefill || prefilledTitle.current) return
    const model = prefillPart.data?.model?.trim()
    if (!model) return
    prefilledTitle.current = true
    const current = form.getFieldValue('title')
    if (typeof current !== 'string' || !current.trim()) {
      form.setFieldsValue({ title: `${model} 使用体验` })
    }
  }, [open, prefill, prefillPart.data, form])

  useEffect(() => {
    if (!open || !prefill || prefilledRating.current) return
    const mine = myRating.data?.mine
    if (!mine) return
    prefilledRating.current = true
    if (!form.isFieldTouched('rating')) form.setFieldsValue({ rating: mine.score })
    if (!form.isFieldTouched('own_hardware')) {
      form.setFieldsValue({ own_hardware: !!mine.own_hardware })
    }
  }, [open, prefill, myRating.data, form])

  const partOptions = useMemo(() => {
    const rows = parts.data?.items || []
    const extra = prefillPart.data && !rows.some(p => p.id === prefillPart.data?.id)
      ? [prefillPart.data]
      : []
    return [...extra, ...rows].map(p => ({ value: p.id, label: `${p.model} · ${p.vendor}` }))
  }, [parts.data, prefillPart.data])

  const create = useMutation({
    mutationFn: (body: unknown) => api.createPost(body),
    onSuccess: (post) => {
      // 先停掉待写入的自动保存，否则它会在清草稿之后把旧内容写回去。
      flushDraftTimer()
      message.success('已发布')
      clearDraft()
      setDraft(null)
      recordActivity({
        kind: 'post',
        title: post.title,
        href: siteHref(`/post.html?id=${post.id}`),
      })
      qc.invalidateQueries({ queryKey: ['posts'] })
      form.resetFields()
      onClose()
    },
    onError: (e: Error) => message.error(e.message),
  })

  const restoreDraft = () => {
    if (!draft) return
    form.setFieldsValue({
      kind: draft.kind,
      title: draft.title,
      body: draft.body,
      tags: draft.tags,
      part_id: draft.part_id ?? undefined,
      rating: draft.rating ?? 5,
      use_case: draft.use_case ?? undefined,
      own_hardware: draft.own_hardware,
      total_price_cny: draft.total_price_cny ?? undefined,
      price_scope: draft.price_scope ?? undefined,
    })
    setDraft(null)
  }

  const discardDraft = () => {
    clearDraft()
    setDraft(null)
    message.success('已丢弃本地草稿')
  }

  // 还在询问是否恢复时，用户直接开始写 = 以新内容为准，旧草稿不再提示。
  const onValuesChange = (_changed: unknown, all: Record<string, unknown>) => {
    if (draft) setDraft(null)
    flushDraftTimer()
    saveTimer.current = window.setTimeout(() => {
      // 清空表单即清掉草稿，下次打开不再提示。
      saveDraft(normalizeDraft(all))
    }, 700)
  }

  // 直接关窗时立刻落盘，不等防抖计时器。
  const persistNow = () => {
    flushDraftTimer()
    if (draft) return
    saveDraft(normalizeDraft(form.getFieldsValue(true) as Record<string, unknown>))
  }

  return (
    <Modal open={open} onCancel={() => { persistNow(); onClose() }}
      title="发帖" width={720} destroyOnHidden
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
      {draft && (
        <div role="status"
          className="mb-3 flex flex-wrap items-center gap-2 rounded-md border border-warning/35 bg-warning-soft px-3 py-2 text-sm text-ink-2">
          <span className="min-w-0 flex-1">
            发现 {ago(draft.updated_at)}的本地草稿《{draft.title.trim().slice(0, 40) || '未命名'}》。
          </span>
          <button type="button" onClick={restoreDraft}
            className="inline-flex min-h-9 items-center rounded-md border border-line bg-surface px-3 text-xs font-semibold text-brand transition-colors hover:border-brand sm:min-h-7">
            恢复
          </button>
          <button type="button" onClick={discardDraft}
            className="inline-flex min-h-9 items-center rounded-md px-2 text-xs text-ink-3 transition-colors hover:text-danger sm:min-h-7">
            丢弃
          </button>
        </div>
      )}
      <Form form={form} layout="vertical" initialValues={{ kind: 'discussion', rating: 5 }}
        requiredMark={false} className="space-y-4 pt-1"
        onValuesChange={onValuesChange}>
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
                options={partOptions} />
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

        <p className="m-0 text-xs leading-5 text-ink-3">
          发布后仍可编辑；被举报并核实的内容会被隐藏，作者可申诉。未发布的草稿只存在本机浏览器。
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
  /** 当前登录用户：判断「我的评论」；站务可编辑/撤回他人的评论。 */
  viewerId?: number | null
  isStaff?: boolean
  /** 顶层帖子标题，只用于本地发言记录的可读标题。 */
  postTitle?: string
  /** 二级评论不能继续回复，引用时交给底部顶层评论框。 */
  onQuoteTop?: (comment: Comment) => void
}

/** 引用块：正文快照为空表示原评论已撤回，只显示占位且不可点。 */
function QuoteBlock({ author, excerpt, href, onRemove, className = 'mt-1.5' }: {
  author?: string
  excerpt: string
  href?: string
  onRemove?: () => void
  className?: string
}) {
  const text = (
    <span className="block min-w-0">
      {author && <span className="font-medium text-ink-3">{author}：</span>}
      <span className={`line-clamp-2 whitespace-pre-wrap ${excerpt ? '' : 'text-ink-3'}`}>
        {excerpt || '引用的评论已撤回'}
      </span>
    </span>
  )
  return (
    <div className={`flex items-start gap-2 rounded-md border border-line bg-surface-2 px-2.5 py-2 text-xs leading-5 text-ink-2 ${className}`}>
      {excerpt && href ? (
        <a href={href} className="min-w-0 flex-1 transition-colors hover:text-brand">{text}</a>
      ) : (
        <span className="min-w-0 flex-1">{text}</span>
      )}
      {onRemove && (
        <button type="button" onClick={onRemove} aria-label="取消引用"
          className="shrink-0 rounded px-1 text-ink-3 transition-colors hover:text-danger">
          取消
        </button>
      )}
    </div>
  )
}

function CommentNode({ c, postId, depth = 0, acceptedId, canAccept, onAccept, acceptingId,
  viewerId = null, isStaff = false, postTitle, onQuoteTop }: {
  c: Comment; postId: number; depth?: number
} & AcceptProps) {
  const qc = useQueryClient()
  const { message, modal } = AntApp.useApp()
  const [replying, setReplying] = useState(false)
  const [text, setText] = useState('')
  const [quote, setQuote] = useState<Comment | null>(null)
  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState('')
  // 撤回后采纳状态由后端清掉；这里再做一层兜底，避免占位旁边还挂着「已采纳」。
  const accepted = !c.withdrawn && (c.accepted === true || c.id === acceptedId)
  const canEdit = !c.withdrawn && viewerId != null &&
    (viewerId === c.author?.id || isStaff)

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['comments', postId] })
    qc.invalidateQueries({ queryKey: ['post', postId] })
    qc.invalidateQueries({ queryKey: ['posts'] })
  }

  const vote = useMutation({
    mutationFn: (v: number) => api.vote('comment', c.id, v),
    onSuccess: refresh,
    onError: (e: Error) => message.error(e.message),
  })
  const reply = useMutation({
    mutationFn: () => api.createComment(postId, {
      body: text,
      parent_id: c.id,
      ...(quote ? { quote_id: quote.id } : {}),
    }),
    onSuccess: () => {
      setText('')
      setReplying(false)
      setQuote(null)
      refresh()
      recordActivity({
        kind: 'comment',
        title: postTitle ? `回复《${postTitle}》` : '回复了一条评论',
        href: siteHref(`/post.html?id=${postId}#comments`),
      })
    },
    onError: (e: Error) => message.error(e.message),
  })
  const edit = useMutation({
    mutationFn: (body: string) => api.updateComment(c.id, body),
    onSuccess: () => {
      setEditing(false)
      refresh()
      message.success('已保存修改')
    },
    onError: (e: Error) => message.error(e.message),
  })
  const withdraw = useMutation({
    mutationFn: () => api.withdrawComment(c.id),
    onSuccess: () => {
      setEditing(false)
      setReplying(false)
      setQuote(null)
      refresh()
      message.success('已撤回，回复仍保留')
    },
    onError: (e: Error) => message.error(e.message),
  })

  const toggleReply = () => {
    if (replying) {
      setQuote(null)
      setReplying(false)
    } else {
      setReplying(true)
    }
  }

  // 引用与回复互相独立：顶层评论打开自己的回复框；二级评论交给底部
  // 顶层评论框，避免出现第三级回复。
  const startQuote = () => {
    if (depth === 0) {
      setReplying(true)
      setQuote(c)
    } else {
      onQuoteTop?.(c)
    }
  }

  const startEdit = () => {
    setEditText(c.body)
    setEditing(true)
  }

  const saveEdit = () => {
    const body = editText.trim()
    if (body.length < 2) {
      message.warning('评论至少 2 个字')
      return
    }
    if (body === c.body.trim()) {
      setEditing(false)
      return
    }
    edit.mutate(body)
  }

  // 撤回不可恢复：二次确认；已采纳的评论还要说明会取消采纳。
  const askWithdraw = () => {
    modal.confirm({
      title: '撤回这条评论？',
      content: accepted
        ? '这条评论已被采纳，撤回后会同时取消采纳。正文会替换为「该评论已撤回」，已有回复仍保留，且不能恢复。'
        : '正文会替换为「该评论已撤回」，已有回复仍保留，且不能恢复。',
      okText: '撤回评论',
      cancelText: '再想想',
      okButtonProps: { danger: true },
      onOk: () => withdraw.mutateAsync().catch(() => {}),
    })
  }

  const nested = depth > 0
  const action = 'inline-flex min-h-11 items-center rounded px-1 text-xs transition-colors sm:min-h-8'

  return (
    <div id={`c${c.id}`} className={nested ? 'mt-3 scroll-mt-24 border-l border-line pl-3 sm:pl-4' : 'mt-3 scroll-mt-24'}>
      <div className={accepted ? 'rounded-lg border border-success/35 bg-success-soft/55 p-2.5 sm:p-3' : ''}>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-xs text-ink-3">
            <UserBadge user={c.author} size={20} />
            <span className="mono tabular">{ago(c.created_at)}</span>
            {c.edited_at && !c.withdrawn && (
              <span className="mono tabular" title={new Date(c.edited_at).toLocaleString('zh-CN')}>
                已编辑
              </span>
            )}
            {c.withdrawn && (
              <span className="inline-flex items-center rounded-full border border-line bg-surface-2 px-2 py-0.5 text-xs text-ink-3">
                已撤回
              </span>
            )}
            {accepted && (
              <span className="inline-flex items-center gap-1 rounded-full border border-success/35 bg-success-soft px-2 py-0.5 text-xs font-semibold text-success">
                <CheckCircleFilled aria-hidden="true" />
                已采纳
              </span>
            )}
            {!c.withdrawn && depth === 0 && (
              <button type="button" onClick={toggleReply}
                aria-expanded={replying}
                className={`${action} text-ink-3 hover:text-brand`}>
                回复
              </button>
            )}
            {!c.withdrawn && (
              <button type="button" onClick={startQuote}
                className={`${action} text-ink-3 hover:text-brand`}>
                引用
              </button>
            )}
            {!c.withdrawn && canAccept && (
              <button type="button" disabled={acceptingId === c.id}
                onClick={() => onAccept(c.id, accepted)}
                aria-pressed={accepted}
                className={`${action} disabled:cursor-not-allowed disabled:opacity-50 ${
                  accepted ? 'text-ink-3 hover:text-danger' : 'font-medium text-brand hover:bg-brand-soft'
                }`}>
                {acceptingId === c.id ? '处理中…' : accepted ? '取消采纳' : '采纳'}
              </button>
            )}
            {canEdit && !editing && (
              <>
                <button type="button" onClick={startEdit}
                  className={`${action} text-ink-3 hover:text-brand`}>
                  编辑
                </button>
                <button type="button" onClick={askWithdraw} disabled={withdraw.isPending}
                  className={`${action} text-ink-3 hover:text-danger disabled:cursor-not-allowed disabled:opacity-50`}>
                  {withdraw.isPending ? '撤回中…' : '撤回'}
                </button>
              </>
            )}
          </div>

          {!c.withdrawn && c.quote_id != null && (
            <QuoteBlock
              author={c.quote_author}
              excerpt={c.quote_excerpt}
              href={c.quote_excerpt ? `#c${c.quote_id}` : undefined} />
          )}

          {c.withdrawn ? (
            <p className="mt-1 rounded-md border border-dashed border-line bg-surface-2 px-3 py-2 text-sm leading-6 text-ink-3">
              该评论已撤回{c.replies?.length ? '，下方回复仍保留' : ''}
            </p>
          ) : editing ? (
            <div className="mt-2 space-y-2">
              <Input.TextArea autoSize={{ minRows: 2, maxRows: 8 }} value={editText}
                maxLength={4000} onChange={e => setEditText(e.target.value)}
                aria-label="编辑评论正文" />
              <div className="flex flex-wrap items-center gap-2">
                <Button type="primary" size="small" loading={edit.isPending} onClick={saveEdit}>
                  保存
                </Button>
                <Button size="small" disabled={edit.isPending} onClick={() => setEditing(false)}>
                  取消
                </Button>
                <span className="text-xs text-ink-3">至少 2 个字，保存后标记已编辑</span>
              </div>
            </div>
          ) : (
            <div className="mt-1 whitespace-pre-wrap text-sm leading-6 text-ink-2">{c.body}</div>
          )}

          {!c.withdrawn && replying && (
            <div className="mt-2 space-y-2">
              {quote && (
                <QuoteBlock
                  author={quote.author?.display_name || quote.author?.handle || '匿名'}
                  excerpt={quote.body}
                  onRemove={() => setQuote(null)}
                  className="" />
              )}
              <div className="flex flex-col gap-2 sm:flex-row">
                <Input.TextArea autoSize={{ minRows: 1, maxRows: 4 }} value={text}
                  onChange={e => setText(e.target.value)}
                  placeholder={quote ? '回复并引用…' : '回复…'} />
                <Button type="primary" loading={reply.isPending}
                  onClick={() => text.trim().length >= 2 && reply.mutate()}>发送</Button>
              </div>
            </div>
          )}

          {!c.withdrawn && !editing && (
            <div className="mt-1.5 flex justify-end">
              <VoteButtons compact score={c.score} myVote={c.my_vote} onVote={v => vote.mutate(v)} />
            </div>
          )}
        </div>
      </div>

      {c.replies?.length > 0 && (
        <div className="mt-1">
          {c.replies.map(r => (
            <CommentNode key={r.id} c={r} postId={postId} depth={depth + 1}
              acceptedId={acceptedId} canAccept={canAccept}
              onAccept={onAccept} acceptingId={acceptingId}
              viewerId={viewerId} isStaff={isStaff} postTitle={postTitle}
              onQuoteTop={onQuoteTop} />
          ))}
        </div>
      )}
    </div>
  )
}

export function CommentList({ postId, acceptedId = null, canAccept = false, canComment = true,
  viewerId = null, isStaff = false, postTitle }: {
  postId: number
  acceptedId?: number | null
  canAccept?: boolean
  canComment?: boolean
  viewerId?: number | null
  isStaff?: boolean
  postTitle?: string
}) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [text, setText] = useState('')
  const [quote, setQuote] = useState<Comment | null>(null)
  const [acceptingId, setAcceptingId] = useState<number | null>(null)
  const boxRef = useRef<HTMLTextAreaElement | null>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['comments', postId], queryFn: () => api.comments(postId),
  })
  const add = useMutation({
    mutationFn: () => api.createComment(postId, {
      body: text,
      ...(quote ? { quote_id: quote.id } : {}),
    }),
    onSuccess: () => {
      setText('')
      setQuote(null)
      qc.invalidateQueries({ queryKey: ['comments', postId] })
      qc.invalidateQueries({ queryKey: ['post', postId] })
      recordActivity({
        kind: 'comment',
        title: postTitle ? `评论《${postTitle}》` : '评论了一条帖子',
        href: siteHref(`/post.html?id=${postId}#comments`),
      })
    },
    onError: (e: Error) => message.error(e.message),
  })

  // 二级评论没有自己的回复框，引用它时落到顶部评论框（仍是最外层评论）。
  const startQuoteTop = (comment: Comment) => {
    setQuote(comment)
    window.requestAnimationFrame(() => boxRef.current?.focus())
  }

  // 已采纳的评论排在最前：读者先看到结论，再看讨论过程。
  const ordered = useMemo(() => {
    const rows = [...(data || [])]
    rows.sort((a, b) => {
      const aa = !a.withdrawn && (a.accepted === true || a.id === acceptedId) ? 1 : 0
      const bb = !b.withdrawn && (b.accepted === true || b.id === acceptedId) ? 1 : 0
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
      {canComment ? (
        <div className="rounded-lg border border-line bg-surface-2 p-2.5">
          {quote && (
            <QuoteBlock
              author={quote.author?.display_name || quote.author?.handle || '匿名'}
              excerpt={quote.body}
              onRemove={() => setQuote(null)}
              className="mb-2" />
          )}
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input.TextArea ref={el => {
              boxRef.current = (el?.nativeElement as HTMLTextAreaElement | null) ?? null
            }} autoSize={{ minRows: 2, maxRows: 6 }} value={text}
              onChange={e => setText(e.target.value)}
              placeholder={quote ? '评论并引用…' : '补充实测数据、提问或反驳…'} />
            <Button type="primary" loading={add.isPending} className="sm:self-end"
              onClick={() => text.trim().length >= 2 && add.mutate()}>评论</Button>
          </div>
          <p className="m-0 mt-1.5 text-xs text-ink-3">
            评论至少 2 个字；写清工况比下结论有用。
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm text-ink-2">
          帖子已锁定，暂时不能回复。
        </div>
      )}

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
              onAccept={accept} acceptingId={acceptingId}
              viewerId={viewerId} isStaff={isStaff} postTitle={postTitle}
              onQuoteTop={startQuoteTop} />
          ))}
        </div>
      )}
    </div>
  )
}
