import { App as AntApp, Alert, Button, Card, Col, Empty, Input, Pagination, Row, Segmented, Select, Skeleton, Space, Statistic, Table, Tag, Typography } from 'antd'
import { DownloadOutlined, FireOutlined, RocketOutlined, SearchOutlined, StarOutlined, TrophyOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { KIND_COLOR, KIND_LABEL, api, type Part, type Post } from './api'
import { F, SENSOR_HERO, fmtField } from './fields'
import { CommentList, PartDrawer, PostCard, UserBadge } from './ui'
import { useAuth } from './App'
import Markdown from 'react-markdown'
import { ArrowDownOutlined, ArrowUpOutlined, EyeOutlined, MessageOutlined } from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

// ── 选型台 ────────────────────────────────────────────────────────────────
const CATS = [
  { value: 'actuator', label: '关节电机' },
  { value: 'controller_high', label: '上位机' },
  { value: 'controller_low', label: '下位机' },
  { value: 'sensor', label: '传感器' },
]

function columnsFor(cat: string, open: (id: string) => void) {
  const num = (v: any) => <span style={{ fontVariantNumeric: 'tabular-nums' }}>{v}</span>
  const tierTag = (t: string) => (
    <Tag color={t === 'A' ? 'blue' : t === 'B' ? 'default' : 'orange'} style={{ marginInlineEnd: 0 }}>
      {t}
    </Tag>
  )
  const base = [
    {
      title: '型号', dataIndex: 'model', key: 'model', width: 220, fixed: 'left' as const,
      render: (_: any, r: Part) => (
        <div>
          <div style={{ fontWeight: 600 }}>{r.model}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>{r.subtype_label}</Text>
        </div>
      ),
    },
    { title: '厂商', dataIndex: 'vendor', key: 'vendor', width: 130 },
  ]
  if (cat === 'actuator') {
    return [...base,
      { title: '峰值 τ', key: 'tp', width: 96, align: 'right' as const, render: (_: any, r: Part) => num(fmtField('tau_peak_Nm', r.specs.tau_peak_Nm) ?? '—') },
      { title: '额定 τ', key: 'tr', width: 96, align: 'right' as const, render: (_: any, r: Part) => num(fmtField('tau_rated_Nm', r.specs.tau_rated_Nm) ?? '—') },
      { title: '减速比', key: 'gear', width: 90, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.gear ?? '—') },
      { title: '空载 rpm', key: 'spd', width: 100, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.speed_noload_rpm ?? '—') },
      { title: '质量 kg', key: 'm', width: 90, align: 'right' as const, render: (_: any, r: Part) => num(fmtField('mass_kg', r.specs.mass_kg) ?? '—') },
      {
        title: 'armature', key: 'arm', width: 118, align: 'right' as const,
        render: (_: any, r: Part) => r.specs.armature_kgm2
          ? <span style={{ color: '#3ddc97', fontVariantNumeric: 'tabular-nums' }}>{fmtField('armature_kgm2', r.specs.armature_kgm2)}</span>
          : <Text type="secondary">—</Text>,
      },
      { title: '扭矩密度', key: 'td', width: 110, align: 'right' as const, render: (_: any, r: Part) => num(r.derived.torque_density_Nm_per_kg ?? '—') },
      { title: '价', key: 'p', width: 80, align: 'right' as const, render: (_: any, r: Part) => r.price_cny ? `¥${r.price_cny}` : <Text type="secondary">—</Text> },
      { title: '源', key: 't', width: 56, render: (_: any, r: Part) => tierTag(r.source_tier) },
    ]
  }
  if (cat === 'controller_high') {
    return [...base,
      { title: 'SoC', key: 'soc', width: 170, render: (_: any, r: Part) => r.specs.soc ?? '—' },
      { title: 'CUDA', key: 'cuda', width: 80, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.cuda_cores ?? '—') },
      { title: 'NPU TOPS', key: 'tops', width: 100, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.npu_tops ?? '—') },
      { title: '内存 GB', key: 'ram', width: 90, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.ram_gb ?? '—') },
      { title: '峰值 W', key: 'pw', width: 90, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.power_max_w ?? '—') },
      { title: '价', key: 'p', width: 84, align: 'right' as const, render: (_: any, r: Part) => r.price_cny ? `¥${r.price_cny}` : '—' },
      { title: '源', key: 't', width: 56, render: (_: any, r: Part) => tierTag(r.source_tier) },
    ]
  }
  if (cat === 'controller_low') {
    return [...base,
      { title: 'MCU', key: 'mcu', width: 180, render: (_: any, r: Part) => r.specs.mcu ?? '—' },
      { title: 'FOC 轴', key: 'foc', width: 84, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.foc_axes ?? '—') },
      { title: 'CAN', key: 'can', width: 70, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.can ?? '—') },
      { title: 'FD', key: 'fd', width: 60, render: (_: any, r: Part) => r.specs.canfd ? '✓' : '—' },
      { title: '电流环 kHz', key: 'cl', width: 110, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.current_loop_khz ?? '—') },
      { title: '最高 V', key: 'v', width: 90, align: 'right' as const, render: (_: any, r: Part) => num(r.specs.voltage_max_V ?? '—') },
      { title: '价', key: 'p', width: 84, align: 'right' as const, render: (_: any, r: Part) => r.price_cny ? `¥${r.price_cny}` : '—' },
      { title: '源', key: 't', width: 56, render: (_: any, r: Part) => tierTag(r.source_tier) },
    ]
  }
  return [...base,
    { title: '类型', key: 'st', width: 120, render: (_: any, r: Part) => r.subtype_label },
    {
      title: '关键参数', key: 'hero', render: (_: any, r: Part) => {
        const fn = SENSOR_HERO[r.subtype]
        return <Text type="secondary" style={{ fontSize: 13 }}>{fn ? fn(r) : (r.notes || '')}</Text>
      },
    },
    { title: '价', key: 'p', width: 84, align: 'right' as const, render: (_: any, r: Part) => r.price_cny ? `¥${r.price_cny}` : '—' },
    { title: '源', key: 't', width: 56, render: (_: any, r: Part) => tierTag(r.source_tier) },
  ]
}

export function CatalogPage({ onOpenPost, onCompose, openAuth }: {
  onOpenPost: (id: number) => void
  onCompose: (partId: string) => void
  openAuth: () => void
}) {
  const { user } = useAuth()
  const { message } = AntApp.useApp()
  const qc = useQueryClient()
  const [cat, setCat] = useState('actuator')
  const [vendor, setVendor] = useState<string | undefined>()
  const [subtype, setSubtype] = useState<string | undefined>()
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('vendor')
  const [order, setOrder] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [openId, setOpenId] = useState<string | null>(null)

  const catalog = useQuery({ queryKey: ['catalog', cat], queryFn: () => api.catalog(cat) })
  const stats = useQuery({ queryKey: ['stats'], queryFn: api.stats })

  const query = useMemo(() => ({
    category: cat, vendor, subtype, q, sort, order,
    limit: pageSize, offset: (page - 1) * pageSize,
  }), [cat, vendor, subtype, q, sort, order, page, pageSize])

  const parts = useQuery({ queryKey: ['parts', query], queryFn: () => api.parts(query) })

  useEffect(() => { setPage(1) }, [cat, vendor, subtype, q, sort, order])

  const doExport = async () => {
    try {
      const r = await api.exportDraft()
      const blob = new Blob([r.actuators_yaml + '\n\n# ── MuJoCo 关节参数 ──\n'
        + r.mjcf_joints.map(j => [j.part_id, j.model, j.armature, j.actuatorfrcrange, j.velocity_limit_rad_s].join(' | ')).join('\n')],
        { type: 'text/plain;charset=utf-8' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = 'roboselect-export.yaml'
      a.click()
      URL.revokeObjectURL(a.href)
      message.success(`已导出 ${r.n} 个执行器`)
    } catch (e: any) { message.error(e.message) }
  }

  return (
    <div>
      <Row gutter={12} style={{ marginBottom: 16 }}>
        {[
          { label: '零件', value: stats.data?.parts, suffix: '件' },
          { label: '有 armature', value: stats.data?.with_armature, suffix: '件' },
          { label: '社区成员', value: stats.data?.users, suffix: '人' },
          { label: '讨论 / 评价', value: stats.data?.posts, suffix: '条' },
        ].map(s => (
          <Col key={s.label} xs={12} md={6}>
            <Card size="small"><Statistic title={s.label} value={s.value ?? 0} suffix={s.suffix} /></Card>
          </Col>
        ))}
      </Row>

      <Alert type="info" showIcon style={{ marginBottom: 14 }}
        message="参数带口径才可比"
        description="每个执行器都标了扭矩口径（峰值/额定）与惯量口径（电机侧/输出侧）。armature = N²·J，读错口径会差到 10⁴ 倍。缺失一律留空，不填假数。"
      />

      <Space wrap style={{ marginBottom: 12 }}>
        <Segmented value={cat} onChange={v => { setCat(v as string); setVendor(undefined); setSubtype(undefined) }}
          options={CATS} />
        <Select allowClear placeholder="厂商" style={{ minWidth: 160 }} value={vendor}
          onChange={setVendor}
          options={(catalog.data?.vendors || []).map(v => ({ value: v.vendor, label: `${v.vendor} (${v.n})` }))} />
        <Select allowClear placeholder="子类" style={{ minWidth: 140 }} value={subtype}
          onChange={setSubtype}
          options={(catalog.data?.facets || []).filter(f => f.category === cat)
            .map(f => ({ value: f.subtype, label: `${f.subtype_label} (${f.n})` }))} />
        <Input allowClear prefix={<SearchOutlined />} placeholder="搜型号 / 厂商" style={{ width: 220 }}
          value={q} onChange={e => setQ(e.target.value)} />
        <Select value={sort} onChange={setSort} style={{ width: 130 }}
          options={[
            { value: 'vendor', label: '按厂商' },
            { value: 'armature', label: '按 armature' },
            { value: 'tau_peak', label: '按峰值扭矩' },
            { value: 'mass', label: '按质量' },
            { value: 'price', label: '按价格' },
          ]} />
        <Button onClick={() => setOrder(o => o === 'asc' ? 'desc' : 'asc')}>
          {order === 'asc' ? '升序' : '降序'}
        </Button>
        <Button icon={<DownloadOutlined />} onClick={doExport}>导出 Draft / MuJoCo</Button>
      </Space>

      <Table
        size="small" rowKey="id"
        loading={parts.isLoading}
        dataSource={parts.data?.items || []}
        columns={columnsFor(cat, setOpenId) as any}
        scroll={{ x: 1100 }}
        pagination={{
          current: page, pageSize, total: parts.data?.total || 0,
          showSizeChanger: true, pageSizeOptions: [20, 50, 100],
          showTotal: t => `共 ${t} 项`,
          onChange: (p, ps) => { setPage(p); setPageSize(ps) },
        }}
        onRow={r => ({
          onClick: () => setOpenId(r.id),
          style: { cursor: 'pointer' },
        })}
      />

      <PartDrawer partId={openId} open={!!openId} onClose={() => setOpenId(null)}
        onOpenPost={id => { setOpenId(null); onOpenPost(id) }}
        onCompose={partId => {
          setOpenId(null)
          if (!user) return openAuth()
          onCompose(partId)
        }} />
    </div>
  )
}

// ── 社区 ──────────────────────────────────────────────────────────────────
export function CommunityPage({ onOpenPost, openAuth }: {
  onOpenPost: (id: number) => void; openAuth: () => void
}) {
  const { user } = useAuth()
  const [kind, setKind] = useState<string>('all')
  const [sort, setSort] = useState<'new' | 'hot' | 'top'>('new')
  const [page, setPage] = useState(1)
  const pageSize = 10

  const query = useMemo(() => ({
    kind: kind === 'all' ? undefined : kind,
    sort, limit: pageSize, offset: (page - 1) * pageSize,
  }), [kind, sort, page])

  const posts = useQuery({ queryKey: ['posts', query], queryFn: () => api.posts(query) })
  const board = useQuery({ queryKey: ['leaderboard'], queryFn: () => api.leaderboard(6) })

  return (
    <Row gutter={20}>
      <Col xs={24} lg={17}>
        <Space wrap style={{ marginBottom: 14 }}>
          <Segmented value={kind} onChange={v => { setKind(v as string); setPage(1) }}
            options={[
              { value: 'all', label: '全部' },
              { value: 'discussion', label: '讨论' },
              { value: 'review', label: '评价' },
              { value: 'build', label: '整机方案' },
            ]} />
          <Segmented value={sort} onChange={v => { setSort(v as any); setPage(1) }}
            options={[
              { value: 'new', label: '最新' },
              { value: 'hot', label: <span><FireOutlined /> 热门</span> },
              { value: 'top', label: '最高分' },
            ]} />
        </Space>

        {posts.isLoading ? <Skeleton active /> :
          !posts.data?.items.length ? <Empty description="还没有帖子" /> :
            posts.data.items.map(p => <PostCard key={p.id} post={p} onOpen={onOpenPost} />)}

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Pagination current={page} pageSize={pageSize} total={posts.data?.total || 0}
            onChange={setPage} showSizeChanger={false} hideOnSinglePage />
        </div>
      </Col>

      <Col xs={24} lg={7}>
        <Card size="small" title={<span><TrophyOutlined /> 贡献榜</span>}
          extra={<Link to="/top">全部</Link>}>
          <Space direction="vertical" style={{ width: '100%' }} size={10}>
            {(board.data || []).map((u, i) => (
              <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <Space size={6}>
                  <Text type="secondary" style={{ width: 16 }}>{i + 1}</Text>
                  <Link to={`/u/${u.handle}`}><UserBadge user={u} size={20} /></Link>
                </Space>
                <Text strong>{u.reputation}</Text>
              </div>
            ))}
          </Space>
        </Card>
        <Card size="small" title="社区怎么用" style={{ marginTop: 12 }}>
          <Paragraph type="secondary" style={{ fontSize: 13, marginBottom: 0 }}>
            写<strong>实测</strong>比写"好用"有用：哪个关节、多大负载、跑多久、出了什么问题。
            评价挂在零件上，会自动出现在该零件的详情里。
          </Paragraph>
          {!user && <Button type="primary" block style={{ marginTop: 10 }} onClick={openAuth}>加入</Button>}
        </Card>
      </Col>
    </Row>
  )
}

// ── 帖子详情 ──────────────────────────────────────────────────────────────
export function PostPage() {
  const { id } = useParams()
  const postId = Number(id)
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const { user, openAuth } = useAuth()
  const post = useQuery({ queryKey: ['post', postId], queryFn: () => api.post(postId) })

  const vote = async (v: number) => {
    if (!user) return openAuth()
    try {
      await api.vote('post', postId, v)
      qc.invalidateQueries({ queryKey: ['post', postId] })
    } catch (e: any) { message.error(e.message) }
  }

  if (post.isLoading) return <Skeleton active />
  if (!post.data) return <Empty description="帖子不存在" />
  const p = post.data

  return (
    <Row gutter={20}>
      <Col xs={24} lg={18}>
        <Card>
          <Space size={6} wrap style={{ marginBottom: 8 }}>
            <Tag color={KIND_COLOR[p.kind]}>{KIND_LABEL[p.kind]}</Tag>
            {p.part_title && <Tag>{p.part_title}</Tag>}
            {p.own_hardware && <Tag color="blue">实测</Tag>}
            {p.tags.map(t => <Tag key={t} bordered={false}>#{t}</Tag>)}
          </Space>
          <Title level={3} style={{ marginTop: 0 }}>{p.title}</Title>
          <Space size={12} style={{ marginBottom: 16 }}>
            <UserBadge user={p.author} />
            <Text type="secondary">{new Date(p.created_at).toLocaleString('zh-CN')}</Text>
            <Text type="secondary"><EyeOutlined /> {p.view_count}</Text>
          </Space>

          <div style={{ display: 'flex', gap: 14 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <Button type="text" icon={<ArrowUpOutlined />} onClick={() => vote(1)}
                style={{ color: p.my_vote === 1 ? '#3ddc97' : undefined }} />
              <Text strong>{p.score}</Text>
              <Button type="text" icon={<ArrowDownOutlined />} onClick={() => vote(-1)}
                style={{ color: p.my_vote === -1 ? '#ff6b6b' : undefined }} />
            </div>
            <div style={{ flex: 1, minWidth: 0, lineHeight: 1.75 }}>
              <Markdown>{p.body}</Markdown>
            </div>
          </div>
        </Card>

        <Card title={<span><MessageOutlined /> 评论（{p.comment_count}）</span>} style={{ marginTop: 16 }}>
          {user ? <CommentList postId={postId} />
            : <Button type="primary" onClick={openAuth}>登录后参与讨论</Button>}
        </Card>
      </Col>
    </Row>
  )
}

// ── 个人页 ────────────────────────────────────────────────────────────────
export function ProfilePage({ onOpenPost }: { onOpenPost: (id: number) => void }) {
  const { handle } = useParams()
  const u = useQuery({ queryKey: ['user', handle], queryFn: () => api.user(handle!) })
  const posts = useQuery({
    queryKey: ['posts', 'by', handle],
    queryFn: () => api.posts({ author: handle, limit: 30 }),
  })

  if (u.isLoading) return <Skeleton active />
  if (!u.data) return <Empty description="用户不存在" />
  const user = u.data

  return (
    <Row gutter={20}>
      <Col xs={24} lg={7}>
        <Card>
          <Space direction="vertical" size={10} style={{ width: '100%' }}>
            <Space size={12}>
              <span style={{
                width: 54, height: 54, borderRadius: 27, display: 'inline-flex',
                alignItems: 'center', justifyContent: 'center', fontSize: 22,
                background: `hsl(212 72% 40%)`,
              }}>{user.display_name.slice(0, 1)}</span>
              <div>
                <Title level={4} style={{ margin: 0 }}>{user.display_name}</Title>
                <Text type="secondary">@{user.handle}</Text>
              </div>
            </Space>
            {user.bio && <Paragraph type="secondary" style={{ marginBottom: 0 }}>{user.bio}</Paragraph>}
            <Row gutter={8}>
              <Col span={8}><Statistic title="声望" value={user.reputation} /></Col>
              <Col span={8}><Statistic title="帖子" value={user.post_count} /></Col>
              <Col span={8}><Statistic title="评论" value={user.comment_count} /></Col>
            </Row>
            <Space wrap size={4}>
              {user.badges.map(b => <Tag key={b} color="blue">{b}</Tag>)}
            </Space>
          </Space>
        </Card>
      </Col>
      <Col xs={24} lg={17}>
        <Title level={5}><StarOutlined /> 他的帖子（{posts.data?.total ?? 0}）</Title>
        {posts.data?.items.map(p => <PostCard key={p.id} post={p} onOpen={onOpenPost} />)}
        {!posts.data?.items.length && <Empty description="还没发过帖" />}
      </Col>
    </Row>
  )
}

// ── 贡献榜 ────────────────────────────────────────────────────────────────
export function TopPage() {
  const board = useQuery({ queryKey: ['leaderboard', 30], queryFn: () => api.leaderboard(30) })
  return (
    <div>
      <Title level={4}><TrophyOutlined /> 贡献榜</Title>
      <Paragraph type="secondary">按声望排序（收到的赞之和）。写实测、回答问题都会涨。</Paragraph>
      <Card>
        <Table size="small" rowKey="id" pagination={false}
          loading={board.isLoading}
          dataSource={board.data || []}
          columns={[
            { title: '#', width: 56, render: (_: any, __: any, i: number) => i + 1 },
            {
              title: '成员', render: (_: any, u: any) => <Link to={`/u/${u.handle}`}><UserBadge user={u} /></Link>,
            },
            { title: '声望', dataIndex: 'reputation', width: 90, align: 'right' },
            { title: '帖子', dataIndex: 'post_count', width: 80, align: 'right' },
            { title: '评论', dataIndex: 'comment_count', width: 80, align: 'right' },
            { title: '徽章', render: (_: any, u: any) => <Space wrap size={4}>{u.badges.map((b: string) => <Tag key={b} color="blue">{b}</Tag>)}</Space> },
          ]}
        />
      </Card>
    </div>
  )
}

// ── 口径说明（机读规范的展示层）────────────────────────────────────────────
export function SemanticsPage() {
  const { data } = useQuery({ queryKey: ["semantics"], queryFn: () => fetch("/api/semantics").then(r => r.json()) })
  const { data: proto } = useQuery({ queryKey: ["protocols"], queryFn: () => fetch("/api/protocols").then(r => r.json()) })
  if (!data) return <Skeleton active />

  const card = (title: string, children: any, extra?: any) => (
    <Card size="small" title={title} extra={extra} style={{ marginBottom: 14 }}>{children}</Card>
  )

  return (
    <div>
      <Title level={4}>参数口径说明</Title>
      <Paragraph type="secondary" style={{ maxWidth: 820 }}>
        这一页是机器可读的口径规范（<code>GET /api/semantics</code>），也被 MCP 工具
        <code> get_parameter_semantics</code> 直接复用。本站所有判定只有三种结论：
        <Tag color="blue">yes</Tag><Tag color="red">no</Tag><Tag>unknown</Tag>
        —— <strong>unknown 表示证据不足，既不算兼容也不算不兼容</strong>。
      </Paragraph>

      {card("物理红线（超阈值需人工复核）", (
        <Table size="small" rowKey="id" pagination={false} dataSource={data.red_lines}
          columns={[
            { title: "编号", dataIndex: "id", width: 80 },
            { title: "项目", dataIndex: "name", width: 150 },
            { title: "公式 / 判据", dataIndex: "formula", width: 200, render: (v: any) => v ? <code>{v}</code> : "—" },
            { title: "阈值", width: 150, render: (_: any, r: any) =>
              r.review_above != null ? `>${r.review_above} 需复核 / >${r.absurd_above} 不可信` : "见说明" },
            { title: "为什么", dataIndex: "why" },
            { title: "怎么核", dataIndex: "how_to_check", render: (v: any) => <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text> },
          ]} />
      ))}

      {card("单位换算（可无损）", (
        <Table size="small" rowKey="from" pagination={false} dataSource={data.conversions}
          columns={[
            { title: "从", dataIndex: "from", width: 130 },
            { title: "到", dataIndex: "to", width: 130 },
            { title: "公式", dataIndex: "formula", render: (v: any) => <code>{v}</code> },
            { title: "注意", dataIndex: "warning", render: (v: any) => v ? <Text type="warning" style={{ fontSize: 12 }}>{v}</Text> : "—" },
          ]} />
      ))}

      {card("可比性分级", (
        <Table size="small" rowKey="grade" pagination={false} dataSource={data.comparability}
          columns={[
            { title: "级", dataIndex: "grade", width: 60, render: (v: any) => <Tag color={v === "A" ? "blue" : v === "D" ? "red" : "default"}>{v}</Tag> },
            { title: "含义", dataIndex: "name", width: 160 },
            { title: "成立条件", dataIndex: "condition" },
          ]} />
      ))}

      {card("向供应商问询清单（可直接写进技术协议）", (
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          {data.supplier_questions.map((q: string) => <li key={q} style={{ marginBottom: 6 }}>{q}</li>)}
        </ul>
      ))}

      {proto && proto.protocols.length > 0 && card("总线与协议口径（同一个「电流」在四个驱动里是四个量）", (
        <>
          <Table size="small" rowKey="id" pagination={false} dataSource={proto.protocols}
            columns={[
              { title: '驱动', width: 130, render: (_: any, r: any) => (
                <div><div className="font-semibold">{r.driver}</div>
                  <div style={{ fontSize: 11, color: '#7f8fa4' }}>{r.vendor}</div></div>) },
              { title: '适用电机', width: 130, render: (_: any, r: any) => <span style={{ fontSize: 11.5 }}>{r.motors.join('、')}</span> },
              { title: '电流编码 / 满量程', render: (_: any, r: any) => (
                <div style={{ fontSize: 11.5 }}>
                  <div>{r.current_encoding}</div>
                  <div style={{ color: '#3ddc97' }}>满量程 {r.current_full_scale_A} A</div>
                </div>) },
              { title: '减速比（协议 / 名义）', width: 160, render: (_: any, r: any) => (
                <div style={{ fontSize: 11.5 }}>
                  <div>{r.gear_protocol == null ? '—' : Number(r.gear_protocol).toFixed(4)}</div>
                  <div style={{ color: '#7f8fa4' }}>名义 {r.gear_nominal}</div>
                </div>) },
              { title: '控制模式', width: 150, render: (_: any, r: any) => <span style={{ fontSize: 11 }}>{r.control_modes.join(' / ')}</span> },
            ]}
            expandable={{
              expandedRowRender: (r: any) => (
                <div style={{ fontSize: 12, lineHeight: 1.65, paddingLeft: 8 }}>
                  <div><Text type="warning">{r.notes}</Text></div>
                  <div style={{ marginTop: 4, color: '#7f8fa4' }}>
                    证据：<code>{r.evidence}</code>
                  </div>
                </div>
              ),
            }} />
          <ul style={{ margin: '10px 0 0', paddingLeft: 20, fontSize: 12, color: '#93a3b8' }}>
            {proto.checklist.map((q: string) => <li key={q} style={{ marginBottom: 4 }}>{q}</li>)}
          </ul>
        </>
      ))}

      {card("字段语义", (
        <Table size="small" rowKey="k" pagination={false}
          dataSource={Object.entries(data.fields).map(([k, v]: any) => ({ k, ...v }))}
          columns={[
            { title: "字段", dataIndex: "k", width: 190, render: (v: any) => <code>{v}</code> },
            { title: "名称", dataIndex: "label", width: 130 },
            { title: "方向", width: 80, render: (_: any, r: any) =>
              r.higher_is_better === true ? <Tag color="blue">越高越好</Tag>
                : r.higher_is_better === false ? <Tag color="orange">越低越好</Tag> : <Tag>不判</Tag> },
            { title: "含义", dataIndex: "meaning" },
            { title: "缺失意味着", dataIndex: "missing_means", render: (v: any) => <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text> },
          ]} />
      ))}

      {card("不变量", (
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          {data.invariants.map((q: string) => <li key={q} style={{ marginBottom: 6 }}><code>{q}</code></li>)}
        </ul>
      ))}
    </div>
  )
}
