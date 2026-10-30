import { App as AntApp, Avatar as AntAvatar, Button, Card, Descriptions, Divider, Drawer, Empty, Form, Input, Modal, Rate, Select, Space, Spin, Tag, Tooltip, Typography } from 'antd'
import { ArrowDownOutlined, ArrowUpOutlined, CommentOutlined, EyeOutlined, FireOutlined, MessageOutlined, PlusOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import Markdown from 'react-markdown'
import { useState } from 'react'
import { KIND_COLOR, KIND_LABEL, api, type Comment, type Part, type Post, type User } from './api'
import { DERIVED, F, SENSOR_HERO, fmtField } from './fields'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

export const ago = (t: string) => dayjs(t).fromNow()

// ── 头像 ──────────────────────────────────────────────────────────────────
export function UserBadge({ user, size = 24 }: { user?: User | null; size?: number }) {
  if (!user) return <span style={{ color: '#6b7c93' }}>已注销</span>
  const bg = `hsl(212 72% 40%)`
  return (
    <Tooltip title={`${user.display_name} · 声望 ${user.reputation}${user.badges.length ? ' · ' + user.badges.join('/') : ''}`}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <AntAvatar size={size} style={{ background: bg, fontSize: size * 0.5, flex: '0 0 auto' }}>
          {user.display_name.slice(0, 1)}
        </AntAvatar>
        <span style={{ fontWeight: 500 }}>{user.display_name}</span>
        <span style={{ color: '#6b7c93', fontSize: 12 }}>{user.reputation}</span>
      </span>
    </Tooltip>
  )
}

// ── 投票 ──────────────────────────────────────────────────────────────────
export function VoteButtons({ score, myVote, onVote, disabled }: {
  score: number; myVote: number; onVote: (v: number) => void; disabled?: boolean
}) {
  const btn = (dir: 1 | -1, icon: any) => (
    <Button
      type="text" size="small" icon={icon} disabled={disabled}
      style={{ color: myVote === dir ? (dir === 1 ? '#3ddc97' : '#ff6b6b') : undefined }}
      onClick={e => { e.stopPropagation(); onVote(myVote === dir ? 0 : dir) }}
    />
  )
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0, minWidth: 40 }}>
      {btn(1, <ArrowUpOutlined />)}
      <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600, fontSize: 13 }}>{score}</span>
      {btn(-1, <ArrowDownOutlined />)}
    </div>
  )
}

// ── 帖子卡片 ──────────────────────────────────────────────────────────────
export function PostCard({ post, onOpen }: { post: Post; onOpen: (id: number) => void }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const vote = useMutation({
    mutationFn: (v: number) => api.vote('post', post.id, v),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['posts'] }); qc.invalidateQueries({ queryKey: ['post', post.id] }) },
    onError: (e: any) => message.error(e.message),
  })
  const excerpt = post.body.replace(/[#>*`\-|]/g, ' ').replace(/\s+/g, ' ').slice(0, 180)

  return (
    <Card
      hoverable size="small"
      style={{ marginBottom: 12 }}
      styles={{ body: { display: 'flex', gap: 12, alignItems: 'flex-start' } }}
      onClick={() => onOpen(post.id)}
    >
      <VoteButtons score={post.score} myVote={post.my_vote}
        onVote={v => vote.mutate(v)} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <Space size={6} wrap style={{ marginBottom: 4 }}>
          {post.pinned && <Tag color="gold">置顶</Tag>}
          <Tag color={KIND_COLOR[post.kind]}>{KIND_LABEL[post.kind]}</Tag>
          {post.part_title && <Tag color="default">{post.part_title}</Tag>}
          {post.own_hardware && <Tag color="blue">实测</Tag>}
          {post.rating != null && <Rate disabled value={post.rating} style={{ fontSize: 12 }} />}
          {post.tags.map(t => <Tag key={t} bordered={false} style={{ color: '#7f8fa4' }}>#{t}</Tag>)}
        </Space>
        <Typography.Title level={5} style={{ margin: '2px 0 4px', fontSize: 15 }}>
          {post.title}
        </Typography.Title>
        <div style={{ color: '#8b9bb0', fontSize: 13, lineHeight: 1.6 }}>{excerpt}…</div>
        <div style={{ display: 'flex', gap: 14, marginTop: 8, fontSize: 12, color: '#6b7c93', alignItems: 'center' }}>
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
export function Composer({ open, onClose, defaultPartId, defaultKind }: {
  open: boolean; onClose: () => void; defaultPartId?: string; defaultKind?: string
}) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const kind = Form.useWatch('kind', form) || defaultKind || 'discussion'

  const [partQuery, setPartQuery] = useState('')
  const parts = useQuery({
    queryKey: ['parts-lite', partQuery],
    queryFn: () => api.parts({ q: partQuery, limit: 20 }),
    enabled: open,
  })

  const create = useMutation({
    mutationFn: (body: any) => api.createPost(body),
    onSuccess: () => {
      message.success('已发布')
      qc.invalidateQueries({ queryKey: ['posts'] })
      form.resetFields()
      onClose()
    },
    onError: (e: any) => message.error(e.message),
  })

  return (
    <Modal
      open={open} onCancel={onClose} title="发帖" width={720} destroyOnHidden
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
      }}
    >
      <Form form={form} layout="vertical"
        initialValues={{ kind: defaultKind || 'discussion', part_id: defaultPartId, rating: 5 }}>
        <Form.Item name="kind" label="类型" rules={[{ required: true }]}>
          <Select options={[
            { value: 'discussion', label: '讨论 — 问题、方法论、踩坑' },
            { value: 'review', label: '评价 — 挂在某个零件上的真实使用反馈' },
            { value: 'build', label: '整机方案 — 一台四足的 BOM 与取舍' },
          ]} />
        </Form.Item>
        <Form.Item name="title" label="标题" rules={[{ required: true, min: 4, max: 120 }]}>
          <Input placeholder="一句话说清这条的核心" showCount maxLength={120} />
        </Form.Item>
        <Form.Item name="body" label="正文（支持 Markdown）"
          rules={[{ required: true, min: 10 }]}>
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
            <div style={{ fontSize: 12, color: '#7f8fa4', margin: '4px 0 8px' }}>
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
    onError: (e: any) => message.error(e.message),
  })
  const reply = useMutation({
    mutationFn: () => api.createComment(postId, { body: text, parent_id: c.id }),
    onSuccess: () => {
      setText(''); setReplying(false)
      qc.invalidateQueries({ queryKey: ['comments', postId] })
      qc.invalidateQueries({ queryKey: ['post', postId] })
    },
    onError: (e: any) => message.error(e.message),
  })

  return (
    <div style={{ marginLeft: depth * 22, marginTop: 10 }}>
      <div style={{ display: 'flex', gap: 10 }}>
        <VoteButtons score={c.score} myVote={c.my_vote} onVote={v => vote.mutate(v)} />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 12, color: '#6b7c93' }}>
            <UserBadge user={c.author} size={20} />
            <span>{ago(c.created_at)}</span>
            {depth === 0 && (
              <Button type="link" size="small" style={{ padding: 0, fontSize: 12 }}
                onClick={() => setReplying(v => !v)}>回复</Button>
            )}
          </div>
          <div style={{ marginTop: 4, whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>{c.body}</div>
          {replying && (
            <Space.Compact style={{ width: '100%', marginTop: 8 }}>
              <Input.TextArea autoSize={{ minRows: 1, maxRows: 4 }} value={text}
                onChange={e => setText(e.target.value)} placeholder="回复…" />
              <Button type="primary" loading={reply.isPending}
                onClick={() => text.trim().length >= 2 && reply.mutate()}>发送</Button>
            </Space.Compact>
          )}
        </div>
      </div>
      {c.replies.map(r => <CommentNode key={r.id} c={r} postId={postId} depth={depth + 1} />)}
    </div>
  )
}

export function CommentList({ postId }: { postId: number }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [text, setText] = useState('')
  const { data, isLoading } = useQuery({ queryKey: ['comments', postId], queryFn: () => api.comments(postId) })
  const add = useMutation({
    mutationFn: () => api.createComment(postId, { body: text }),
    onSuccess: () => {
      setText('')
      qc.invalidateQueries({ queryKey: ['comments', postId] })
      qc.invalidateQueries({ queryKey: ['post', postId] })
    },
    onError: (e: any) => message.error(e.message),
  })

  return (
    <div>
      <Space.Compact style={{ width: '100%' }}>
        <Input.TextArea autoSize={{ minRows: 2, maxRows: 6 }} value={text}
          onChange={e => setText(e.target.value)} placeholder="补充实测数据、提问或反驳…" />
        <Button type="primary" loading={add.isPending}
          onClick={() => text.trim().length >= 2 && add.mutate()}>评论</Button>
      </Space.Compact>
      {isLoading ? <Spin style={{ marginTop: 16 }} /> :
        !data?.length ? <Empty style={{ marginTop: 18 }} description="还没有回复，来说第一句" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
          data.map(c => <CommentNode key={c.id} c={c} postId={postId} />)}
    </div>
  )
}

// ── 零件详情抽屉 ──────────────────────────────────────────────────────────
export function PartDrawer({ partId, open, onClose, onOpenPost, onCompose }: {
  partId: string | null; open: boolean; onClose: () => void
  onOpenPost: (id: number) => void; onCompose: (partId: string) => void
}) {
  const { data: p, isLoading } = useQuery({
    queryKey: ['part', partId], queryFn: () => api.part(partId!), enabled: open && !!partId,
  })

  const desc = (specs: Record<string, any>, keys: string[]) => (
    <Descriptions size="small" column={2} bordered
      items={keys.map(k => ({
        key: k,
        label: F[k]?.label || k,
        children: <span style={{ fontVariantNumeric: 'tabular-nums' }}>{fmtField(k, specs[k]) ?? '—'}</span>,
      }))} />
  )

  const deriveItems = p ? Object.keys(DERIVED).filter(k => p.derived[k] !== undefined) : []

  return (
    <Drawer open={open} onClose={onClose} width={720} destroyOnHidden
      title={p ? `${p.model} · ${p.vendor}` : '载入中'}>
      {isLoading || !p ? <Spin /> : (
        <div>
          <Space wrap size={6} style={{ marginBottom: 12 }}>
            <Tag color={p.source_tier === 'A' ? 'blue' : p.source_tier === 'B' ? 'default' : 'orange'}>
              来源 {p.source_tier}
            </Tag>
            {p.verified && <Tag color="blue">已核对 {p.last_checked}</Tag>}
            <Tag>{p.subtype_label}</Tag>
            {p.price_cny && <Tag color="gold">¥{p.price_cny}</Tag>}
            {p.url && <a href={p.url} target="_blank" rel="noreferrer">官方资料 ↗</a>}
            <Button size="small" type="primary" icon={<PlusOutlined />}
              onClick={() => onCompose(p.id)}>写评价</Button>
          </Space>

          {!!deriveItems.length && (
            <>
              <Typography.Title level={5}>仿真 / 选型关键量</Typography.Title>
              <Descriptions size="small" column={2} bordered
                items={deriveItems.map(k => ({
                  key: k, label: DERIVED[k].label,
                  children: <b style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {fmtField(k, p.derived[k], DERIVED[k])}
                  </b>,
                }))} />
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                派生量在读取时计算，不落库
              </Typography.Text>
              <Divider />
            </>
          )}

          <Typography.Title level={5}>全部参数</Typography.Title>
          {desc(p.specs, Object.keys(p.specs))}

          {p.notes && <><Divider /><Typography.Paragraph type="secondary" style={{ fontSize: 13 }}>
            {p.notes}</Typography.Paragraph>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>来源：{p.origin}</Typography.Text></>}

          <Divider />
          <Space style={{ marginBottom: 8 }}>
            <Typography.Title level={5} style={{ margin: 0 }}>
              <MessageOutlined /> 关于这个件的讨论（{p.posts?.length ?? 0}）
            </Typography.Title>
          </Space>
          {!p.posts?.length
            ? <Empty description="还没有人评价过这个件" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            : p.posts.map(post => <PostCard key={post.id} post={post} onOpen={onOpenPost} />)}
        </div>
      )}
    </Drawer>
  )
}
