import {
  App as AntApp, Avatar, Button, Card, Empty, Form, Input, Modal, Rate, Select, Space, Spin, Tag, Tooltip,
} from 'antd'
import {
  ArrowDownOutlined, ArrowUpOutlined, CommentOutlined, EyeOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Markdown, { type Components } from 'react-markdown'
import { useState, type ReactNode } from 'react'
import {
  KIND_COLOR, KIND_LABEL, api, siteHref, type Comment, type Post, type User,
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

// ── Markdown 正文 ─────────────────────────────────────────────────────────
const MD_COMPONENTS: Components = {
  h1: ({ children }) => <h2 className="mt-5 mb-2 text-[20px] font-bold text-slate-900">{children}</h2>,
  h2: ({ children }) => <h3 className="mt-4 mb-2 text-[17px] font-bold text-slate-900">{children}</h3>,
  h3: ({ children }) => <h4 className="mt-3 mb-1.5 text-[15px] font-semibold text-slate-900">{children}</h4>,
  p: ({ children }) => <p className="my-2 leading-7 text-slate-800">{children}</p>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer noopener" className="text-blue-600 underline hover:text-blue-700">
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="my-2 list-disc pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal pl-5">{children}</ol>,
  li: ({ children }) => <li className="my-0.5">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-2 border-slate-300 pl-3 text-slate-600">{children}</blockquote>
  ),
  code: ({ className, children }) => (
    className
      ? <code className={`${className} block overflow-x-auto rounded-lg bg-slate-50 p-3 text-[12.5px]`}>{children}</code>
      : <code className="rounded bg-slate-100 px-1 py-[1px] text-[12.5px] text-slate-800">{children}</code>
  ),
  pre: ({ children }) => <pre className="my-3 overflow-x-auto">{children}</pre>,
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto"><table className="w-full border-collapse text-[13px]">{children}</table></div>
  ),
  th: ({ children }) => <th className="border border-slate-200 bg-slate-50 px-2 py-1 text-left">{children}</th>,
  td: ({ children }) => <td className="border border-slate-200 px-2 py-1">{children}</td>,
  img: ({ src, alt }) => (
    <img src={typeof src === 'string' ? src : undefined} alt={alt || ''} loading="lazy"
      className="my-3 max-w-full rounded-lg border border-slate-200" />
  ),
  hr: () => <hr className="my-4 border-slate-200" />,
}

export function MarkdownBody({ children }: { children: ReactNode }) {
  const source = typeof children === 'string' ? children : ''
  return <div className="min-w-0 text-[14px] leading-7"><Markdown components={MD_COMPONENTS}>{source}</Markdown></div>
}

// ── 头像 ──────────────────────────────────────────────────────────────────
export function UserBadge({ user, size = 24 }: { user?: User | null; size?: number }) {
  if (!user) return <span className="text-slate-400">已注销</span>
  return (
    <Tooltip title={`${user.display_name} · 声望 ${user.reputation}${user.badges?.length ? ' · ' + user.badges.join('/') : ''}`}>
      <span className="inline-flex items-center gap-1.5">
        <Avatar size={size} style={{ background: 'hsl(212 72% 40%)', fontSize: size * 0.5, flex: '0 0 auto' }}>
          {user.display_name.slice(0, 1)}
        </Avatar>
        <span className="font-medium">{user.display_name}</span>
        <span className="text-[12px] text-slate-400">{user.reputation}</span>
      </span>
    </Tooltip>
  )
}

// ── 投票 ──────────────────────────────────────────────────────────────────
export function VoteButtons({ score, myVote, onVote, disabled }: {
  score: number; myVote: number; onVote: (v: number) => void; disabled?: boolean
}) {
  const btn = (dir: 1 | -1, icon: ReactNode) => (
    <Button type="text" size="small" icon={icon} disabled={disabled}
      style={{ color: myVote === dir ? (dir === 1 ? '#16a34a' : '#dc2626') : undefined }}
      aria-label={dir === 1 ? '赞同' : '反对'}
      onClick={e => { e.stopPropagation(); onVote(myVote === dir ? 0 : dir) }} />
  )
  return (
    <div className="flex min-w-10 flex-col items-center">
      {btn(1, <ArrowUpOutlined />)}
      <span className="text-[13px] font-semibold tabular-nums">{score}</span>
      {btn(-1, <ArrowDownOutlined />)}
    </div>
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
    <Card hoverable size="small" className="mb-3"
      styles={{ body: { display: 'flex', gap: 12, alignItems: 'flex-start' } }}
      onClick={() => { window.location.href = href }}>
      <VoteButtons score={post.score} myVote={post.my_vote} onVote={v => vote.mutate(v)} />
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex flex-wrap items-center gap-1.5">
          {post.pinned && <Tag color="gold">置顶</Tag>}
          <Tag color={KIND_COLOR[post.kind]}>{KIND_LABEL[post.kind]}</Tag>
          {post.part_title && <Tag>{post.part_title}</Tag>}
          {post.own_hardware && <Tag color="blue">实测</Tag>}
          {post.rating != null && <Rate disabled value={post.rating} style={{ fontSize: 12 }} />}
          {post.tags.map(t => <Tag key={t} variant="filled" style={{ color: '#7f8fa4' }}>#{t}</Tag>)}
        </div>
        <a href={href} className="text-[15px] font-semibold text-slate-900 hover:text-blue-700">
          {post.title}
        </a>
        <div className="mt-1 text-[13px] leading-6 text-slate-500">{excerpt}…</div>
        <div className="mt-2 flex flex-wrap items-center gap-3.5 text-[12px] text-slate-500">
          <UserBadge user={post.author} size={20} />
          <span>{ago(post.created_at)}</span>
          <span><CommentOutlined /> {post.comment_count}</span>
          <span><EyeOutlined /> {post.view_count}</span>
        </div>
      </div>
    </Card>
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
      <Form form={form} layout="vertical" initialValues={{ kind: 'discussion', rating: 5 }}>
        <Form.Item name="kind" label="类型" rules={[{ required: true }]}>
          <Select options={[
            { value: 'discussion', label: '讨论 — 问题、方法论、踩坑' },
            { value: 'review', label: '评价 — 挂在某个零件上的真实使用反馈' },
            { value: 'build', label: '整机方案 — 一台机器的 BOM 与取舍' },
          ]} />
        </Form.Item>
        <Form.Item name="title" label="标题" rules={[{ required: true, min: 4, max: 120 }]}>
          <Input placeholder="一句话说清这条的核心" showCount maxLength={120} />
        </Form.Item>
        <Form.Item name="body" label="正文（支持 Markdown）" rules={[{ required: true, min: 10 }]}>
          <Input.TextArea rows={9} maxLength={20000} showCount
            placeholder="写实测数据比写“好用”有用：哪个关节、多大负载、跑多久、出了什么问题。" />
        </Form.Item>
        <Space size={12} wrap>
          <Form.Item name="part_id" label="关联零件（评价必填）" style={{ minWidth: 260 }}>
            <Select allowClear showSearch filterOption={false}
              onSearch={setPartQuery}
              loading={parts.isLoading}
              placeholder="搜型号 / 厂商"
              options={(parts.data?.items || []).map(p => ({
                value: p.id, label: `${p.model} · ${p.vendor}`,
              }))} />
          </Form.Item>
          {kind === 'review' && (
            <>
              <Form.Item name="rating" label="评分" rules={[{ required: true }]}>
                <Rate />
              </Form.Item>
              <Form.Item name="use_case" label="用在">
                <Select style={{ width: 110 }} allowClear
                  options={['四足', '人形', '机械臂', '其他'].map(v => ({ value: v, label: v }))} />
              </Form.Item>
              <Form.Item name="own_hardware" label="我实际用过" valuePropName="checked">
                <input type="checkbox" style={{ width: 18, height: 18 }} />
              </Form.Item>
            </>
          )}
        </Space>
        {kind === 'build' && (
          <>
            <div className="mb-2 mt-1 text-[12px] text-slate-500">
              整机报价必须说明<strong>覆盖范围</strong>——只给一个数字比不给更有害。
            </div>
            <Space size={12} wrap>
              <Form.Item name="total_price_cny" label="整机报价（¥）">
                <Input type="number" style={{ width: 150 }} placeholder="30000" />
              </Form.Item>
              <Form.Item name="price_verified" label="价格已核实" valuePropName="checked">
                <input type="checkbox" style={{ width: 18, height: 18 }} />
              </Form.Item>
            </Space>
            <Form.Item name="price_scope" label="覆盖范围（必填，若有报价）"
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
          </>
        )}
        <Form.Item name="tags" label="标签">
          <Select mode="tags" placeholder="回车添加，如 温升 / 背隙 / CAN-FD" tokenSeparators={[',', '，']} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

// ── 评论 ──────────────────────────────────────────────────────────────────
function CommentNode({ c, postId, depth = 0 }: { c: Comment; postId: number; depth?: number }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [replying, setReplying] = useState(false)
  const [text, setText] = useState('')

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

  return (
    <div style={{ marginLeft: depth * 22, marginTop: 10 }}>
      <div className="flex gap-2.5">
        <VoteButtons score={c.score} myVote={c.my_vote} onVote={v => vote.mutate(v)} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2.5 text-[12px] text-slate-500">
            <UserBadge user={c.author} size={20} />
            <span>{ago(c.created_at)}</span>
            {depth === 0 && (
              <Button type="link" size="small" style={{ padding: 0, fontSize: 12 }}
                onClick={() => setReplying(v => !v)}>回复</Button>
            )}
          </div>
          <div className="mt-1 whitespace-pre-wrap text-[13.5px] leading-6 text-slate-800">{c.body}</div>
          {replying && (
            <div className="mt-2 flex gap-2">
              <Input.TextArea autoSize={{ minRows: 1, maxRows: 4 }} value={text}
                onChange={e => setText(e.target.value)} placeholder="回复…" />
              <Button type="primary" loading={reply.isPending}
                onClick={() => text.trim().length >= 2 && reply.mutate()}>发送</Button>
            </div>
          )}
        </div>
      </div>
      {c.replies?.map(r => <CommentNode key={r.id} c={r} postId={postId} depth={depth + 1} />)}
    </div>
  )
}

export function CommentList({ postId }: { postId: number }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [text, setText] = useState('')
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

  return (
    <div>
      <div className="flex w-full gap-2">
        <Input.TextArea autoSize={{ minRows: 2, maxRows: 6 }} value={text}
          onChange={e => setText(e.target.value)} placeholder="补充实测数据、提问或反驳…" />
        <Button type="primary" loading={add.isPending}
          onClick={() => text.trim().length >= 2 && add.mutate()}>评论</Button>
      </div>
      {isLoading ? <Spin className="mt-4" /> :
        !data?.length ? (
          <Empty className="mt-4" description="还没有回复，来说第一句" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : data.map(c => <CommentNode key={c.id} c={c} postId={postId} />)}
    </div>
  )
}
