import { App as AntApp, Modal, Select, Table, Tag, Empty, Spin } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { api, auth, type Part } from './api'
import { useAuth } from './App'

/** 后台专用请求：带 token，且不走前台缓存 */
async function adminReq<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...(init?.headers as any) }
  if (init?.body) headers['Content-Type'] = 'application/json'
  const t = auth.token
  if (t) headers['Authorization'] = `Bearer ${t}`
  const r = await fetch(`/api/admin${path}`, { ...init, headers })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) {
    const d = data?.detail
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? d.map((x: any) => x.msg).join('；') : `HTTP ${r.status}`)
  }
  return data as T
}

const GAPS = [
  { k: 'no_image', label: '缺产品图', hint: '全部零件；无图时用示意图占位' },
  { k: 'no_url', label: '缺来源 URL', hint: '全部零件；没有来源的数等于编造' },
  { k: 'no_rated_torque', label: '缺额定扭矩', hint: '仅执行器；峰值/额定比因此算不出' },
  { k: 'no_armature', label: '缺 armature', hint: '仅执行器；缺则仿真不可用' },
  { k: 'no_price', label: '缺报价', hint: '全部零件；选型无法做预算' },
  { k: 'unverified', label: '未核对', hint: '全部零件；标了等级但没人逐项对过' },
]

/** 可编辑字段：分组只是为了好找，保存时拍平成 specs.xxx */
const EDIT_GROUPS: { title: string; fields: [string, string, string?][] }[] = [
  {
    title: '扭矩与转速',
    fields: [
      ['specs.tau_peak_Nm', '峰值扭矩', 'N·m'],
      ['specs.tau_rated_Nm', '额定扭矩', 'N·m'],
      ['specs.tau_basis', '扭矩口径（peak/rated）'],
      ['specs.speed_noload_rpm', '空载转速', 'rpm'],
      ['specs.speed_rated_rpm', '额定转速', 'rpm'],
    ],
  },
  {
    title: '机械与仿真',
    fields: [
      ['specs.gear', '减速比'],
      ['specs.mass_kg', '质量', 'kg'],
      ['specs.od_mm', '直径', 'mm'],
      ['specs.l_mm', '长度', 'mm'],
      ['specs.rotor_inertia_kgm2', '转子惯量', 'kg·m²'],
      ['specs.inertia_basis', '惯量口径（rotor/output）'],
      ['specs.armature_kgm2', 'armature（N²·J）', 'kg·m²'],
    ],
  },
  {
    title: '电气与接口',
    fields: [
      ['specs.voltage_V', '额定电压', 'V'],
      ['specs.kt_Nm_per_A', '转矩常数', 'N·m/A'],
      ['specs.r_phase_ohm', '相电阻', 'Ω'],
      ['specs.l_phase_uh', '相电感', 'µH'],
      ['specs.encoder', '编码器'],
      ['specs.comm', '通信'],
      ['specs.ip', '防护等级'],
    ],
  },
  {
    title: '来源与展示',
    fields: [
      ['url', '来源 URL'],
      ['origin', '来源说明（哪份手册/哪一页）'],
      ['source_tier', '来源等级（A/B/C）'],
      ['specs.image_url', '产品图路径'],
      ['notes', '备注'],
    ],
  },
]

function GapCard({ label, hint, n, scope, active, onClick }: {
  label: string; hint: string; n: number; scope?: string; active: boolean; onClick: () => void
}) {
  return (
    <button onClick={onClick}
      className={`rounded-lg border px-3 py-2.5 text-left transition
        ${active ? 'border-amber-300 bg-amber-50'
                 : 'border-slate-200 bg-slate-50 hover:border-slate-300'}`}>
      <div className="text-[10.5px] uppercase tracking-wider text-slate-400">{label}</div>
      <div className={`mt-0.5 text-[18px] font-semibold ${n ? 'text-amber-600' : 'text-blue-600'}`}>{n}</div>
      <div className="mt-0.5 text-[10px] leading-tight text-slate-400">{hint}</div>
      {scope && <div className="mt-1 text-[9.5px] leading-tight text-slate-300">{scope}</div>}
    </button>
  )
}

function EditModal({ partId, onClose }: { partId: string; onClose: () => void }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const [draft, setDraft] = useState<Record<string, any>>({})
  const [note, setNote] = useState('')
  const [srcUrl, setSrcUrl] = useState('')

  const { data: p, isLoading } = useQuery({
    queryKey: ['admin-part', partId],
    queryFn: () => adminReq<Part & { history: any[] }>(`/parts/${encodeURIComponent(partId)}`),
  })

  const save = useMutation({
    mutationFn: () => adminReq('/parts/' + encodeURIComponent(partId), {
      method: 'PATCH',
      body: JSON.stringify({ changes: draft, note, source_url: srcUrl || null }),
    }),
    onSuccess: (r: any) => {
      message.success(r.changed ? `已改 ${r.changed} 个字段，留痕 ${r.changed} 条` : '没有实际变化')
      qc.invalidateQueries({ queryKey: ['admin-part', partId] })
      qc.invalidateQueries({ queryKey: ['admin-stats'] })
      qc.invalidateQueries({ queryKey: ['admin-parts'] })
      qc.invalidateQueries({ queryKey: ['parts'] })
      setDraft({})
      setNote('')
    },
    onError: (e: any) => message.error(e.message),
  })

  const val = (path: string) => {
    if (path in draft) return draft[path]
    if (path.startsWith('specs.')) return (p?.specs || {})[path.slice(6)] ?? ''
    return (p as any)?.[path] ?? ''
  }
  const set = (path: string, v: any) => setDraft(d => ({ ...d, [path]: v }))

  return (
    <Modal open onCancel={onClose} width={860} title={null} footer={null} destroyOnHidden>
      {isLoading || !p ? <Spin /> : (
        <div>
          <div className="mb-3 flex items-baseline gap-2">
            <h3 className="m-0 text-[17px] font-bold">{p.model}</h3>
            <span className="text-[12px] text-slate-500">{p.vendor} · {p.id}</span>
            <Tag color={p.source_tier === 'A' ? 'blue' : p.source_tier === 'B' ? 'default' : 'orange'}>
              {p.source_tier}{p.verified ? ' ✓' : ''}
            </Tag>
          </div>

          {EDIT_GROUPS.map(g => (
            <div key={g.title} className="mb-4">
              <div className="mb-1.5 text-[11px] uppercase tracking-wider text-slate-400">{g.title}</div>
              <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                {g.fields.map(([path, label, unit]) => {
                  const changed = path in draft
                  return (
                    <label key={path}
                      className={`flex items-center gap-2 rounded-lg border px-2 py-1
                        ${changed ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-slate-50'}`}>
                      <span className="w-[152px] shrink-0 text-[11.5px] text-slate-500">
                        {label}{unit ? <span className="text-slate-400"> ({unit})</span> : null}
                      </span>
                      <input
                        value={val(path) ?? ''}
                        onChange={e => set(path, e.target.value)}
                        className="w-full bg-transparent text-[12.5px] text-slate-900 outline-none"
                        placeholder="—"
                      />
                    </label>
                  )
                })}
              </div>
            </div>
          ))}

          <div className="mb-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <div className="mb-1.5 text-[11px] uppercase tracking-wider text-amber-700">
              改动依据（必填，会写进修改记录）
            </div>
            <textarea value={note} onChange={e => setNote(e.target.value)} rows={2}
              placeholder="例：据 CubeMars AK80-9 V3 官方 datasheet 第 2 页扭矩曲线，额定 8 N·m @ 25℃"
              className="w-full resize-none rounded-md border border-slate-200 bg-[var(--surface)] p-2
                         text-[12.5px] text-slate-900 outline-none focus:border-amber-300" />
            <input value={srcUrl} onChange={e => setSrcUrl(e.target.value)}
              placeholder="来源链接（建议填官方页面或 PDF 地址）"
              className="mt-1.5 w-full rounded-md border border-slate-200 bg-[var(--surface)] px-2 py-1.5
                         text-[12.5px] text-slate-900 outline-none focus:border-amber-300" />
            <div className="mt-2 flex items-center gap-2">
              <button onClick={() => { if (note.trim().length < 2) return message.warning('至少写清依据'); save.mutate() }}
                disabled={!Object.keys(draft).length || save.isPending}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-[12.5px] font-semibold
                           text-white disabled:opacity-40">
                保存 {Object.keys(draft).length ? `(${Object.keys(draft).length} 个字段)` : ''}
              </button>
              <button onClick={() => setDraft({})}
                className="rounded-md border border-slate-200 px-3 py-1.5 text-[12.5px] text-slate-600">
                撤销改动
              </button>
              <span className="text-[11px] text-slate-400">保存后 last_checked 自动更新为今天</span>
            </div>
          </div>

          <div>
            <div className="mb-1.5 text-[11px] uppercase tracking-wider text-slate-400">
              修改记录（{p.history.length}）
            </div>
            {!p.history.length ? <div className="text-[12px] text-slate-400">还没有改动记录</div> : (
              <div className="max-h-[190px] overflow-y-auto">
                {p.history.map(h => (
                  <div key={h.id} className="border-b border-slate-100 py-1.5 text-[11.5px]">
                    <span className="text-slate-500">{h.created_at.slice(0, 16).replace('T', ' ')}</span>
                    <span className="mx-1.5 text-slate-400">·</span>
                    <span className="text-slate-600">{h.editor || '?'}</span>
                    <span className="mx-1.5 text-slate-400">·</span>
                    <code className="text-[11px] text-sky-700">{h.field}</code>
                    <span className="mx-1 text-slate-400">{h.old_value ?? '—'} → </span>
                    <span className="text-blue-600">{h.new_value ?? '—'}</span>
                    <div className="text-slate-400">{h.note}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}

export default function Admin() {
  const { user } = useAuth()
  const [gap, setGap] = useState<string | undefined>()
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [editId, setEditId] = useState<string | null>(null)
  const pageSize = 20

  const stats = useQuery({ queryKey: ['admin-stats'], queryFn: () => adminReq<any>('/stats') })
  const list = useQuery({
    queryKey: ['admin-parts', gap, q, page],
    queryFn: () => adminReq<any>(`/parts?${new URLSearchParams({
      ...(gap ? { gap } : {}), ...(q ? { q } : {}),
      limit: String(pageSize), offset: String((page - 1) * pageSize),
    })}`),
  })

  const cols = useMemo(() => [
    {
      title: '型号', width: 220,
      render: (_: any, r: Part) => (
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-semibold">{r.model}</span>
            {!r.image_url && <span className="rounded bg-slate-100 px-1 text-[9.5px] text-slate-500">示意图</span>}
          </div>
          <div className="text-[11px] text-slate-400">{r.vendor}</div>
        </div>
      ),
    },
    {
      title: '来源', width: 150,
      render: (_: any, r: Part) => (
        <div className="flex items-center gap-1">
          <Tag color={r.source_tier === 'A' ? 'blue' : r.source_tier === 'B' ? 'default' : 'orange'}
            style={{ marginInlineEnd: 0 }}>{r.source_tier}{r.verified ? ' ✓' : ''}</Tag>
          {!r.url && <span className="text-[10px] text-red-600">无链接</span>}
        </div>
      ),
    },
    { title: '核对', width: 110, render: (_: any, r: Part) => <span className="text-[11px] text-slate-500">{r.last_checked || '—'}</span> },
    {
      title: 'armature', width: 100,
      render: (_: any, r: Part) => r.category !== 'actuator'
        ? <span className="text-slate-300" title="该字段只对关节电机有意义">—</span>
        : r.specs?.armature_kgm2
          ? <span className="text-blue-600">有</span>
          : <span className="text-amber-600">缺</span>,
    },
    {
      title: '额定τ', width: 80,
      render: (_: any, r: Part) => r.category !== 'actuator'
        ? <span className="text-slate-300" title="该字段只对关节电机有意义">—</span>
        : r.specs?.tau_rated_Nm
          ? <span className="text-blue-600">有</span>
          : <span className="text-amber-600">缺</span>,
    },
    { title: '价', width: 80, render: (_: any, r: Part) => r.price_cny ? `¥${r.price_cny}` : <span className="text-slate-400">—</span> },
    {
      title: '', width: 70,
      render: (_: any, r: Part) => (
        <button onClick={() => setEditId(r.id)}
          className="rounded-md border border-slate-200 px-2 py-0.5 text-[11.5px] text-slate-600
                     hover:border-blue-300 hover:text-blue-600">
          编辑
        </button>
      ),
    },
  ], [])

  if (!user?.is_staff) {
    return <Empty description={<span className="text-slate-500">需要站务权限（用 lcs 登录）</span>} />
  }

  return (
    <div>
      <h1 className="text-[20px] font-bold tracking-tight text-slate-900">数据后台</h1>
      <p className="mb-4 mt-1 text-[12.5px] text-slate-500">
        每个字段都能改，但<strong className="text-amber-700">每次改动都要写清依据</strong>
        ——依据和来源会存进修改记录，成为这条数据的可追溯部分。
      </p>

      <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {GAPS.map(g => (
          <GapCard key={g.k} label={g.label} hint={g.hint}
            n={stats.data?.[g.k] ?? 0}
            scope={stats.data?.scopes?.[g.k]}
            active={gap === g.k}
            onClick={() => { setGap(gap === g.k ? undefined : g.k); setPage(1) }} />
        ))}
      </div>

      <div className="mb-3 flex items-center gap-2">
        <input value={q} onChange={e => { setQ(e.target.value); setPage(1) }}
          placeholder="搜型号 / 厂商"
          className="w-[240px] rounded-lg border border-slate-200 bg-slate-50 px-3 py-2
                     text-[13px] text-slate-900 placeholder:text-slate-400 outline-none
                     focus:border-blue-300" />
        {gap && (
          <button onClick={() => setGap(undefined)}
            className="rounded-lg border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-[12px] text-amber-600">
            筛选中：{GAPS.find(g => g.k === gap)?.label} ✕
          </button>
        )}
        <span className="ml-auto text-[12px] text-slate-400">
          共 {list.data?.total ?? 0} 项 · 已留痕 {stats.data?.edits ?? 0} 条
        </span>
      </div>

      <Table size="small" rowKey="id" loading={list.isLoading}
        dataSource={list.data?.items || []} columns={cols as any}
        pagination={{
          current: page, pageSize, total: list.data?.total ?? 0, showSizeChanger: false,
          onChange: setPage, showTotal: t => `共 ${t} 项`,
        }} />

      {editId && <EditModal partId={editId} onClose={() => setEditId(null)} />}
    </div>
  )
}
