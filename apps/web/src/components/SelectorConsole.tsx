import { useEffect, useMemo, useRef, useState } from 'react'
import { imageUrl, type CatalogPart } from '@/lib/catalog'
import { effectivePrice, formatPrice, partHref } from '@/lib/utils'
import {
  DEFAULT_NEEDS, PRESETS, SIZE_LABEL, STATUS_LABEL, TYPE_DEFAULT, TYPE_LABEL,
  buildBomPayload, plan, toCsv,
  type Choices, type Compat, type ControlMode, type EvalItem, type Needs,
  type RoleOption, type RolePlan, type RobotType, type SelectorInput,
  type SelectorModel, type SizeClass, type Verdict,
} from '@/lib/selector'

type Props = { parts: CatalogPart[]; models: SelectorModel[] }

const SIZE_ORDER: SizeClass[] = ['tiny', 'small', 'medium', 'large', 'xlarge']
const CONTROL_ORDER: ControlMode[] = ['classical', 'rl', 'teleop', 'autonomy']

const statusClass: Record<Compat, string> = {
  declared: 'border-success/30 bg-success-soft text-success',
  partial: 'border-warning/30 bg-warning-soft text-warning',
  not_declared: 'border-line bg-surface-3 text-ink-3',
  n_a: 'border-line bg-surface text-ink-3',
}

const verdictClass: Record<Verdict, string> = {
  ok: 'border-success/30 bg-success-soft text-success',
  warn: 'border-warning/30 bg-warning-soft text-warning',
  bad: 'border-danger/30 bg-danger-soft text-danger',
  info: 'border-line bg-surface-2 text-ink-3',
}

const V1_LABEL_TO_KEY: Record<string, string> = {
  '执行器': 'actuator',
  '执行器（腿）': 'actuator_leg',
  '执行器（臂）': 'actuator_arm',
  '下位机 / 实时控制': 'low',
  '上位机 / 感知计算': 'high',
  'IMU': 'imu',
  '深度相机': 'depth',
  '激光雷达': 'lidar',
  '相机': 'camera',
  '遥控器': 'remote',
  '电池': 'battery',
  '电池组（2×6S 串联）': 'battery',
}

const b64url = (s: string) =>
  btoa(unescape(encodeURIComponent(s))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')

const unb64url = (s: string) =>
  decodeURIComponent(escape(atob(s.replace(/-/g, '+').replace(/_/g, '/'))))

const manualOf = (m: SelectorModel) => ({
  mass_kg: m.mass_kg, dof: m.dof, effort_min_Nm: m.effort_min_Nm, effort_max_Nm: m.effort_max_Nm,
})

function StatusBadge({ status }: { status: Compat }) {
  return (
    <span className={`inline-flex shrink-0 items-center rounded-full border px-1.5 py-0.5 text-xs font-medium ${statusClass[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  )
}

function PartThumb({ part, size = 'h-9 w-9' }: { part: CatalogPart | null; size?: string }) {
  if (!part?.image) return <span className={`grid ${size} shrink-0 place-items-center rounded border border-line bg-surface-2 text-xs text-ink-3`}>无图</span>
  return (
    <img
      src={imageUrl(part)}
      alt=""
      loading="lazy"
      className={`${size} shrink-0 rounded border border-line bg-surface-2 object-contain p-0.5`}
    />
  )
}

function EvalChips({ evals }: { evals: EvalItem[] }) {
  const notes = evals.filter(e => e.note && (e.verdict === 'warn' || e.verdict === 'bad'))
  return (
    <div className="min-w-0">
      <div className="flex flex-wrap gap-1">
        {evals.map((e, i) => (
          <span
            key={i}
            title={e.note}
            className={`inline-flex items-center rounded border px-1.5 py-0.5 text-xs leading-4 ${verdictClass[e.verdict]}`}
          >
            {e.label} {e.value}
          </span>
        ))}
      </div>
      {notes.length > 0 && (
        <p className="mt-0.5 text-xs leading-4 text-warning">
          {notes.map(e => `${e.label}：${e.note}`).join('；')}
        </p>
      )}
    </div>
  )
}

function OptionRow({ opt, selected, onSelect }: { opt: RoleOption; selected: boolean; onSelect: () => void }) {
  return (
    <div className={`flex flex-wrap items-start gap-2 rounded-md border p-2 ${selected ? 'border-brand/50 bg-brand-soft' : 'border-line bg-surface'}`}>
      <PartThumb part={opt.part} size="h-10 w-10" />
      <div className="min-w-0 flex-1 basis-52">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <a href={partHref(opt.part)} className="truncate text-xs font-medium text-ink hover:text-brand">{opt.part.model}</a>
          <span className="truncate text-xs text-ink-3">{opt.part.vendor}</span>
        </div>
        <div className="mt-1"><EvalChips evals={opt.evals} /></div>
        {opt.risk && <p className="mt-1 text-xs leading-4 text-danger">{opt.risk}</p>}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <span className="mono tabular text-xs font-semibold text-ink">{formatPrice(opt.price)}</span>
        <button
          type="button"
          onClick={onSelect}
          aria-pressed={selected}
          className={`chip h-7 px-2.5 text-xs ${selected ? 'border-brand/50 text-brand' : ''}`}
        >
          {selected ? '已选' : '选择'}
        </button>
      </div>
    </div>
  )
}

function RoleCard({ role, choice, selectedPart, expanded, onToggle, onSelect, onRestore, onQty }: {
  role: RolePlan
  choice: { partId?: string | null; qty?: number } | undefined
  selectedPart: CatalogPart | null
  expanded: boolean
  onToggle: () => void
  onSelect: (partId: string) => void
  onRestore: () => void
  onQty: (qty: number) => void
}) {
  const selectedOpt = selectedPart ? role.options.find(o => o.part.id === selectedPart.id) ?? null : null
  const selectedPrice = selectedPart ? (selectedOpt?.price ?? effectivePrice(selectedPart.price, selectedPart.offers)) : null
  const qty = Math.max(0, Math.min(999, Math.floor(choice?.qty ?? role.qty)))
  const subtotal = selectedPrice !== null ? selectedPrice * qty : null
  return (
    <section className="rounded-lg border border-line bg-surface">
      <div className="flex flex-wrap items-center gap-2 border-b border-line px-3 py-2">
        <span className="rounded bg-surface-2 px-1.5 py-0.5 text-xs text-ink-3">{role.group}</span>
        <h3 className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">{role.label}</h3>
        {selectedPart ? (
          <button type="button" onClick={onRestore} className="text-xs text-ink-3 hover:text-brand">恢复虚拟件</button>
        ) : (
          <span className="rounded-full border border-line bg-surface-2 px-1.5 py-0.5 text-xs text-ink-3">虚拟件</span>
        )}
        <label className="inline-flex items-center gap-1 text-xs text-ink-3">
          数量
          <input
            type="number"
            min={0}
            max={999}
            value={qty}
            onChange={e => onQty(Number(e.target.value))}
            aria-label={`${role.label}数量`}
            className="mono tabular h-7 w-14 rounded border border-line bg-surface px-1.5 text-xs text-ink"
          />
        </label>
      </div>

      <div className="space-y-2 px-3 py-2.5">
        <div className="rounded-md border border-dashed border-line bg-surface-2 px-2.5 py-2">
          <p className="text-xs font-medium text-ink-2">{role.virtual.summary}</p>
          <dl className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-ink-3">
            {role.virtual.fields.map((f, i) => (
              <div key={i} className="inline-flex gap-1"><dt>{f.label}</dt><dd className="text-ink-2">{f.value}</dd></div>
            ))}
          </dl>
        </div>

        {selectedPart && (
          <div className="flex flex-wrap items-center gap-2 rounded-md border border-brand/40 bg-brand-soft px-2.5 py-2">
            <PartThumb part={selectedPart} />
            <div className="min-w-0 flex-1">
              <a href={partHref(selectedPart)} className="block truncate text-xs font-medium text-ink hover:text-brand">{selectedPart.model}</a>
              <p className="truncate text-xs text-ink-3">
                {selectedPart.vendor}
                {!selectedOpt && ' · 不在当前参考列表（来自导入/分享），参数以详情页为准'}
              </p>
            </div>
            <div className="text-right text-xs">
              <p className="mono tabular text-ink-2">{formatPrice(selectedPrice)} × {qty}</p>
              <p className="mono tabular font-semibold text-ink">{subtotal !== null ? formatPrice(subtotal) : '询价'}</p>
            </div>
          </div>
        )}

        {role.advice.length > 0 && (
          <ul className="list-disc space-y-0.5 pl-4 text-xs leading-5 text-ink-3">
            {role.advice.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        )}

        {role.options.length > 0 ? (
          <div>
            <button
              type="button"
              onClick={onToggle}
              aria-expanded={expanded}
              className="flex w-full flex-wrap items-center gap-x-2 rounded-md border border-line bg-surface px-2.5 py-1.5 text-left text-xs text-ink-2 hover:border-brand/40"
            >
              <span className="font-medium text-brand">{expanded ? '收起参考选项' : `参考选项（${role.options.length}）`}</span>
              <span className="min-w-0 flex-1 truncate text-xs text-ink-3">{role.sortNote}</span>
              <span aria-hidden="true" className="text-ink-3">{expanded ? '▴' : '▾'}</span>
            </button>
            {expanded && (
              <div className="mt-1.5 space-y-1.5">
                {role.options.map(opt => (
                  <OptionRow
                    key={opt.part.id}
                    opt={opt}
                    selected={selectedPart?.id === opt.part.id}
                    onSelect={() => onSelect(opt.part.id)}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-ink-3">站内暂无条目，按上方虚拟件需求外购。{role.sortNote}</p>
        )}
      </div>
    </section>
  )
}

export default function SelectorConsole({ parts, models }: Props) {
  const first = models.find(m => m.type === 'quadruped' && m.size === 'small') ?? models[0]
  const [type, setType] = useState<RobotType>(first?.type ?? 'quadruped')
  const [size, setSize] = useState<SizeClass>(first?.size ?? 'small')
  const [modelId, setModelId] = useState<string | null>(first?.id ?? null)
  const [needs, setNeeds] = useState<Needs>(DEFAULT_NEEDS)
  const [manual, setManual] = useState(first ? manualOf(first) : TYPE_DEFAULT.quadruped)
  const [choices, setChoices] = useState<Choices>({})
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ actuator: true, actuator_leg: true })
  const [notice, setNotice] = useState('')
  const [codeOpen, setCodeOpen] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const modelOptions = useMemo(
    () => models.filter(m => m.type === type && m.size === size),
    [models, type, size],
  )
  const selected = useMemo(() => models.find(m => m.id === modelId) ?? null, [models, modelId])
  const byId = useMemo(() => new Map(parts.map(p => [p.id, p])), [parts])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const hash = window.location.hash
    if (!hash.startsWith('#b=')) return
    try {
      const data = JSON.parse(unb64url(hash.slice(3)))
      const m = data.modelId ? models.find(x => x.id === data.modelId) : null
      if (m) {
        setType(m.type)
        setSize(m.size)
        setModelId(m.id)
        setManual(manualOf(m))
      } else {
        if (data.type) setType(data.type)
        if (data.size) setSize(data.size)
        setModelId(null)
        if (data.manual) setManual({ ...TYPE_DEFAULT[(data.type ?? 'quadruped') as RobotType], ...data.manual })
      }
      if (data.needs) setNeeds({ ...DEFAULT_NEEDS, ...data.needs })
      if (data.choices) setChoices(data.choices)
    } catch { /* 坏链接就当没带参数 */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const input: SelectorInput = useMemo(
    () => ({ type, size, modelId, needs, manual }),
    [type, size, modelId, needs, manual],
  )
  const result = useMemo(() => plan(input, models, parts, choices), [input, models, parts, choices])

  const chosenCount = result.roles.filter(r => choices[r.key]?.partId).length
  const allExpanded = result.roles.every(r => r.options.length === 0 || expanded[r.key])

  const selectType = (next: RobotType) => {
    if (next === type) return
    setType(next)
    const m = models.find(x => x.type === next && x.size === size) ?? null
    setModelId(m?.id ?? null)
    setManual(m ? manualOf(m) : TYPE_DEFAULT[next])
    setChoices({})
  }

  const selectSize = (next: SizeClass) => {
    if (next === size) return
    setSize(next)
    const m = models.find(x => x.type === type && x.size === next) ?? null
    setModelId(m?.id ?? null)
    if (m) setManual(manualOf(m))
    setChoices({})
  }

  const selectModel = (id: string | null) => {
    if (id === modelId) return
    setModelId(id)
    const m = models.find(x => x.id === id)
    if (m) setManual(manualOf(m))
    setChoices({})
  }

  const patchNeeds = (patch: Partial<Needs>) => setNeeds(prev => ({ ...prev, ...patch }))

  const toggleControl = (mode: ControlMode) => {
    setNeeds(prev => {
      const on = prev.controls.includes(mode)
      const next = on ? prev.controls.filter(c => c !== mode) : [...prev.controls, mode]
      return { ...prev, controls: next.length ? next : ['classical'] }
    })
  }

  const setQty = (key: string, qty: number) => {
    const safe = Math.max(0, Math.min(999, Math.floor(Number.isFinite(qty) ? qty : 0)))
    setChoices(prev => ({ ...prev, [key]: { ...prev[key], qty: safe } }))
  }

  const selectPart = (key: string, partId: string) => {
    setChoices(prev => ({ ...prev, [key]: { ...prev[key], partId } }))
    setExpanded(prev => ({ ...prev, [key]: true }))
  }

  const restoreVirtual = (key: string) => {
    setChoices(prev => ({ ...prev, [key]: { ...prev[key], partId: null } }))
  }

  const download = (name: string, text: string, kind: string) => {
    const blob = new Blob([text], { type: kind })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
  }

  const payload = () => buildBomPayload(input, result, choices, parts)

  const exportJson = () => {
    download(`robowiki-bom-${type}-${result.reference?.model ?? 'custom'}.json`, JSON.stringify(payload(), null, 2), 'application/json')
    setNotice('已导出 BOM JSON（含虚拟件需求与评价）')
  }

  const exportCsv = () => {
    download(`robowiki-bom-${type}-${result.reference?.model ?? 'custom'}.csv`, '\ufeff' + toCsv(payload()), 'text/csv;charset=utf-8')
    setNotice('已导出 CSV（Excel 可直接打开）')
  }

  const copyShare = async () => {
    const data = { type, size, modelId, needs, manual, choices }
    const url = `${window.location.origin}${window.location.pathname}#b=${b64url(JSON.stringify(data))}`
    try {
      await navigator.clipboard.writeText(url)
      setNotice('分享链接已复制（含当前配置与已选部件）')
    } catch {
      setNotice(url)
    }
  }

  const importJson = async (file: File) => {
    try {
      const data = JSON.parse(await file.text())
      const conf = data.config ?? {}
      const model = models.find(m => m.model === conf.reference_model)
      if (model) {
        setType(model.type)
        setSize(model.size)
        setModelId(model.id)
        setManual(manualOf(model))
      } else if (conf.type) {
        setType(conf.type)
        if (conf.size) setSize(conf.size)
        setModelId(null)
        setManual({
          mass_kg: Number(conf.mass_kg) || TYPE_DEFAULT[conf.type as RobotType].mass_kg,
          dof: Number(conf.dof) || TYPE_DEFAULT[conf.type as RobotType].dof,
          effort_min_Nm: Number(conf.effort_min_Nm) || TYPE_DEFAULT[conf.type as RobotType].effort_min_Nm,
          effort_max_Nm: Number(conf.effort_max_Nm) || TYPE_DEFAULT[conf.type as RobotType].effort_max_Nm,
        })
      }
      if (conf.needs) setNeeds({ ...DEFAULT_NEEDS, ...conf.needs })

      const byId = new Map(parts.map(p => [p.id, p]))
      const labelToKey = new Map(result.roles.map(r => [r.label, r.key]))
      const ov: Choices = {}
      let unmatched = 0
      for (const line of data.lines ?? []) {
        if (!line?.role) continue
        const key = data.version === 2 ? String(line.role) : (V1_LABEL_TO_KEY[line.role] ?? labelToKey.get(line.role) ?? String(line.role))
        const pid = line.part_id ?? null
        if (pid && !byId.has(pid)) {
          unmatched += 1
          ov[key] = { partId: null, qty: line.qty }
          continue
        }
        ov[key] = { partId: pid, qty: line.qty }
      }
      setChoices(ov)
      setNotice(unmatched > 0
        ? `已导入 ${data.lines?.length ?? 0} 行；${unmatched} 行的部件站内找不到，已退回虚拟件。`
        : `已导入 ${data.lines?.length ?? 0} 行 BOM。`)
    } catch {
      setNotice('导入失败：不是有效的 RoboWiki BOM JSON。')
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)] lg:items-start">
      <aside className="space-y-3 lg:sticky lg:top-20">
        <section className="rounded-lg border border-line bg-surface">
          <div className="flex items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-sm font-semibold text-ink">1. 机型</h2>
            <span className="text-xs text-ink-3">{models.length} 个可信型号</span>
          </div>
          <div className="space-y-3 p-3">
            <div className="chip-row" role="group" aria-label="机器人类型">
              {(Object.keys(TYPE_LABEL) as RobotType[]).map(t => (
                <button key={t} type="button" className="chip h-8 px-3 text-xs" aria-pressed={type === t} onClick={() => selectType(t)}>
                  {TYPE_LABEL[t]}
                  <span className="mono tabular opacity-60">{models.filter(m => m.type === t).length}</span>
                </button>
              ))}
            </div>
            <div className="chip-row" role="group" aria-label="机器人档位">
              {SIZE_ORDER.map(s => {
                const count = models.filter(m => m.type === type && m.size === s).length
                return (
                  <button key={s} type="button" className="chip h-7 px-2.5 text-xs" aria-pressed={size === s} onClick={() => selectSize(s)}>
                    {SIZE_LABEL[s]}
                    <span className="mono tabular opacity-60">{count}</span>
                  </button>
                )
              })}
            </div>
            <label className="block text-xs text-ink-3">
              参考机型
              <select
                data-guide="selector-model"
                value={modelId ?? ''}
                onChange={e => selectModel(e.target.value || null)}
                className="mt-1 h-9 w-full rounded-md border border-line bg-surface px-2 text-xs text-ink"
              >
                <option value="">自定义（按下方质量/DOF/扭矩）</option>
                {modelOptions.map(m => (
                  <option key={m.id} value={m.id}>{m.model} · {m.mass_kg} kg · {m.dof} DOF · {m.motor_tier}</option>
                ))}
              </select>
            </label>
            {modelOptions.length === 0 && (
              <p className="rounded-md bg-warning-soft px-2.5 py-2 text-xs leading-5 text-warning">
                这个构型/档位没有公开可信 URDF。可换档位，或直接用下方自定义参数占位。
              </p>
            )}
            {selected ? (
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 rounded-md border border-line bg-surface-2 p-2.5 text-xs">
                <div><dt className="text-ink-3">质量</dt><dd className="mono tabular text-ink">{selected.mass_kg} kg</dd></div>
                <div><dt className="text-ink-3">DOF</dt><dd className="mono tabular text-ink">{selected.dof}</dd></div>
                <div><dt className="text-ink-3">关节 effort</dt><dd className="mono tabular text-ink">{selected.effort_min_Nm}–{selected.effort_max_Nm} N·m</dd></div>
                <div><dt className="text-ink-3">电机档</dt><dd className="mono tabular text-ink">{selected.motor_tier}</dd></div>
                <div className="col-span-2"><dt className="text-ink-3">验证</dt><dd className="text-ink">{selected.verification} · {selected.urdf_source}</dd></div>
              </dl>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {([
                  ['mass_kg', '质量 kg', 0.5],
                  ['dof', 'DOF', 1],
                  ['effort_min_Nm', '最小 effort', 1],
                  ['effort_max_Nm', '最大 effort', 1],
                ] as const).map(([k, label, step]) => (
                  <label key={k} className="text-xs text-ink-3">
                    {label}
                    <input
                      type="number"
                      min={0}
                      step={step}
                      value={manual[k]}
                      onChange={e => setManual(prev => ({ ...prev, [k]: Math.max(0, Number(e.target.value) || 0) }))}
                      className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-xs text-ink"
                    />
                  </label>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="rounded-lg border border-line bg-surface">
          <div className="flex items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-sm font-semibold text-ink">2. 功能需求</h2>
            <button type="button" onClick={() => setNeeds(DEFAULT_NEEDS)} className="text-xs text-ink-3 hover:text-ink">重置</button>
          </div>
          <div className="space-y-3 p-3">
            <div>
              <p className="mb-1.5 text-xs text-ink-3">预设</p>
              <div className="flex flex-wrap gap-1.5">
                {PRESETS.map(p => (
                  <button key={p.id} type="button" title={p.hint} onClick={() => patchNeeds(p.needs)} className="chip h-7 px-2.5 text-xs">
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-1.5 text-xs text-ink-3">控制方式（可多选）</p>
              <div className="flex flex-wrap gap-1.5">
                {CONTROL_ORDER.map(c => (
                  <button key={c} type="button" className="chip h-7 px-2.5 text-xs" aria-pressed={needs.controls.includes(c)} onClick={() => toggleControl(c)}>
                    {c === 'classical' ? '传统控制' : c === 'rl' ? '强化学习' : c === 'teleop' ? '遥操作' : '自主导航'}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs text-ink-2">
              {([
                ['depth', '深度相机'],
                ['lidar', '激光雷达'],
                ['camera', '普通相机'],
                ['remote', '遥控器'],
                ['compute', '上位机'],
                ['hollow', '中空走线'],
                ['mixedLimbs', '腿/臂混搭'],
              ] as const).map(([k, label]) => (
                <label key={k} className="inline-flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={Boolean(needs[k])}
                    onChange={e => patchNeeds({ [k]: e.target.checked } as Partial<Needs>)}
                    className="h-3.5 w-3.5 accent-[var(--rw-primary)]"
                  />
                  {label}
                </label>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <label className="text-xs text-ink-3">
                供电
                <select value={needs.power} onChange={e => patchNeeds({ power: e.target.value as Needs['power'] })} className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-xs text-ink">
                  <option value="battery">电池</option>
                  <option value="tethered">外接电源</option>
                </select>
              </label>
              <label className="text-xs text-ink-3">
                备件
                <select value={needs.sparePct} onChange={e => patchNeeds({ sparePct: Number(e.target.value) })} className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-xs text-ink">
                  <option value={0}>0%</option>
                  <option value={10}>10%</option>
                  <option value={20}>20%</option>
                </select>
              </label>
            </div>
            <label className="block text-xs text-ink-3">
              预算上限（CNY，可空）
              <input
                type="number"
                min={0}
                step={100}
                value={needs.budget ?? ''}
                onChange={e => patchNeeds({ budget: e.target.value === '' ? null : Math.max(0, Number(e.target.value)) })}
                className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-xs text-ink"
                placeholder="例如 8000"
              />
            </label>
          </div>
        </section>
      </aside>

      <div className="min-w-0 space-y-3">
        <section className="rounded-lg border border-line bg-surface p-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="text-base font-bold text-ink">
                {selected ? `${selected.model} 方案` : `${TYPE_LABEL[type]} · 自定义方案`}
              </h2>
              <p className="mt-0.5 text-xs text-ink-3">
                {result.effective.mass_kg} kg · {result.effective.dof} DOF · effort {result.effective.effort_min_Nm}–{result.effective.effort_max_Nm} N·m
                {selected ? ` · ${selected.motor_tier}` : ''}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-ink-3">已知小计</p>
              <p className="mono tabular text-xl font-bold text-ink">{formatPrice(result.totals.known_cny)}</p>
              <p className="text-xs text-ink-3">{result.totals.virtual_lines ? `另有 ${result.totals.virtual_lines} 项虚拟/询价` : '全部已选且有价'}</p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            <button type="button" className="chip h-8 px-3 text-xs" onClick={exportJson}>导出 BOM JSON</button>
            <button type="button" className="chip h-8 px-3 text-xs" onClick={exportCsv}>导出 CSV</button>
            <button type="button" className="chip h-8 px-3 text-xs" onClick={copyShare}>复制分享链接</button>
            <button type="button" className="chip h-8 px-3 text-xs" onClick={() => fileRef.current?.click()}>导入 BOM</button>
            <input ref={fileRef} type="file" accept="application/json,.json" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) void importJson(f); e.target.value = '' }} />
          </div>
          {notice && <p className="mt-2 break-all rounded bg-surface-2 px-2 py-1.5 text-xs text-ink-2">{notice}</p>}
        </section>

        {result.warnings.length > 0 && (
          <section className="rounded-lg border border-warning/30 bg-warning-soft p-3">
            <h2 className="text-xs font-semibold text-warning">需要复核</h2>
            <ul className="mt-1.5 list-disc space-y-1 pl-4 text-xs leading-5 text-warning">
              {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </section>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2 px-0.5">
          <h2 className="text-sm font-semibold text-ink" data-guide="selector-roles">
            BOM · 虚拟件打底，参考选项自选
            <span className="ml-2 text-xs font-normal text-ink-3">已选 {chosenCount}/{result.roles.length} 项</span>
          </h2>
          <button
            type="button"
            className="text-xs text-ink-3 hover:text-brand"
            onClick={() => setExpanded(allExpanded ? {} : Object.fromEntries(result.roles.map(r => [r.key, true])))}
          >
            {allExpanded ? '全部收起' : '全部展开'}
          </button>
        </div>

        {result.roles.map(role => (
          <RoleCard
            key={role.key}
            role={role}
            choice={choices[role.key]}
            selectedPart={choices[role.key]?.partId ? byId.get(choices[role.key].partId!) ?? null : null}
            expanded={Boolean(expanded[role.key])}
            onToggle={() => setExpanded(prev => ({ ...prev, [role.key]: !prev[role.key] }))}
            onSelect={partId => selectPart(role.key, partId)}
            onRestore={() => restoreVirtual(role.key)}
            onQty={qty => setQty(role.key, qty)}
          />
        ))}

        <section className="rounded-lg border border-line bg-surface">
          <div className="flex items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-sm font-semibold text-ink">线束与接口</h2>
            <span className="text-xs text-ink-3">按额定电流 ×70% 选线规</span>
          </div>
          {result.harness.length === 0 ? (
            <p className="px-3 py-3 text-xs leading-5 text-ink-3">
              先在「执行器」角色选一个真实型号，再按它的额定/峰值电流生成线束计算；虚拟件阶段不猜电流。
            </p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b border-line text-xs text-ink-3">
                      <th className="p-2 font-medium">对象</th>
                      <th className="p-2 font-medium">数量</th>
                      <th className="p-2 font-medium">额定电流</th>
                      <th className="p-2 font-medium">线规</th>
                      <th className="p-2 font-medium">连接器</th>
                      <th className="p-2 font-medium">孔径要求</th>
                      <th className="p-2 font-medium">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.harness.map((row, i) => (
                      <tr key={i} className="border-b border-line align-top">
                        <td className="p-2 text-ink">{row.motor}</td>
                        <td className="p-2 mono tabular">{row.qty}</td>
                        <td className="p-2 mono tabular">{row.current_A.toFixed(1)} A</td>
                        <td className="p-2 mono tabular">{row.awg} AWG</td>
                        <td className="p-2">{row.connector}</td>
                        <td className="p-2 mono tabular">{row.requiredBore_mm ? `≥${row.requiredBore_mm.toFixed(1)} mm` : '—'}</td>
                        <td className="p-2"><StatusBadge status={row.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="space-y-1 border-t border-line px-3 py-2 text-xs leading-5 text-ink-3">
                {result.harness.map((row, i) => <p key={i}><span className="text-ink-2">{row.motor}：</span>{row.note}</p>)}
                <p>电机端统一 XT30PW(2+2)：2 电源 + 2 信号（CANH/CANL），功率针 20A MAX、信号针 1A；线束最大推荐 14AWG。多电机共母线时，母线线规按下游电流总和重新计算。</p>
              </div>
            </>
          )}
        </section>

        <section className="rounded-lg border border-line bg-surface">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-sm font-semibold text-ink">基础 MJCF</h2>
            <div className="flex gap-1.5">
              <button type="button" className="chip h-7 px-2.5 text-xs" onClick={() => { void navigator.clipboard.writeText(result.mjcf); setNotice('MJCF 已复制') }}>复制</button>
              <button type="button" className="chip h-7 px-2.5 text-xs" onClick={() => download(`robowiki-${type}-${result.reference?.model ?? 'custom'}.xml`, result.mjcf, 'application/xml')}>下载 XML</button>
              <button type="button" className="chip h-7 px-2.5 text-xs" onClick={() => setCodeOpen(v => !v)} aria-expanded={codeOpen}>{codeOpen ? '收起' : '预览'}</button>
            </div>
          </div>
          <p className="px-3 pt-2 text-xs leading-5 text-ink-3">
            按参考机型的质量、DOF 生成；选了真实执行器时用它的峰值扭矩，否则用参考 effort 上限。几何是胶囊/盒体占位，不是 CAD。可直接用 MuJoCo 打开改尺寸、惯量和碰撞。
          </p>
          {codeOpen && (
            <pre className="m-3 max-h-80 overflow-auto rounded-md border border-line bg-surface-2 p-3 text-xs leading-4 text-ink-2">
              {result.mjcf}
            </pre>
          )}
        </section>

        <section className="rounded-lg border border-line bg-surface p-3 text-xs leading-5 text-ink-3">
          <p><span className="text-ink-2">选型口径：</span>每个角色先给虚拟件（按参考机型推导的需求占位），不默认推荐具体型号；参考选项附评价供对比，排序规则写在每个角色里。电池电压档、下位机/桥接总线、分线板输入范围随所选执行器联动。站内没有的（12S 整包、USB-485/UART 转换器、大电流急停等）明确标缺口，不拿估算值冒充。</p>
          <p className="mt-1"><span className="text-ink-2">范围：</span>执行器、电源、主控、感知与关键线束小件；结构件、紧固件、3D 打印件不在选型台内。</p>
          <p className="mt-1"><span className="text-ink-2">参考：</span>{models.length} 个可信型号来自 enkeebot 的 URDF 解析与交叉验证；线束规则来自 ENCOS《电机线束推荐说明》（2026-06-22）。</p>
        </section>
      </div>
    </div>
  )
}