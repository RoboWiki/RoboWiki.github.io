import { useEffect, useMemo, useRef, useState } from 'react'
import { imageUrl, type CatalogPart } from '@/lib/catalog'
import { effectivePrice, formatPrice, partHref } from '@/lib/utils'
import {
  DEFAULT_NEEDS, PRESETS, SIZE_LABEL, STATUS_LABEL, TYPE_DEFAULT, TYPE_LABEL,
  buildBomPayload, recommend, toCsv,
  type Compat, type ControlMode, type Needs, type RobotType, type SelectorInput,
  type SelectorModel, type SizeClass,
} from '@/lib/selector'

type Props = { parts: CatalogPart[]; models: SelectorModel[] }

type Override = { partId?: string; qty?: number }

const SIZE_ORDER: SizeClass[] = ['tiny', 'small', 'medium', 'large', 'xlarge']
const CONTROL_ORDER: ControlMode[] = ['classical', 'rl', 'teleop', 'autonomy']

const statusClass: Record<Compat, string> = {
  declared: 'border-success/30 bg-success-soft text-success',
  partial: 'border-warning/30 bg-warning-soft text-warning',
  not_declared: 'border-line bg-surface-3 text-ink-3',
  n_a: 'border-line bg-surface text-ink-3',
}

const b64url = (s: string) =>
  btoa(unescape(encodeURIComponent(s))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')

const unb64url = (s: string) =>
  decodeURIComponent(escape(atob(s.replace(/-/g, '+').replace(/_/g, '/'))))

function StatusBadge({ status }: { status: Compat }) {
  return (
    <span className={`inline-flex shrink-0 items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium ${statusClass[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  )
}

function PartThumb({ part }: { part: CatalogPart | null }) {
  if (!part?.image) return <span className="grid h-9 w-9 shrink-0 place-items-center rounded border border-line bg-surface-2 text-[9px] text-ink-3">无图</span>
  return (
    <img
      src={imageUrl(part)}
      alt=""
      loading="lazy"
      className="h-9 w-9 shrink-0 rounded border border-line bg-surface-2 object-contain p-0.5"
    />
  )
}

export default function SelectorConsole({ parts, models }: Props) {
  const first = models.find(m => m.type === 'quadruped' && m.size === 'small') ?? models[0]
  const [type, setType] = useState<RobotType>(first?.type ?? 'quadruped')
  const [size, setSize] = useState<SizeClass>(first?.size ?? 'small')
  const [modelId, setModelId] = useState<string | null>(first?.id ?? null)
  const [needs, setNeeds] = useState<Needs>(DEFAULT_NEEDS)
  const [manual, setManual] = useState(TYPE_DEFAULT[first?.type ?? 'quadruped'])
  const [overrides, setOverrides] = useState<Record<string, Override>>({})
  const [notice, setNotice] = useState('')
  const [codeOpen, setCodeOpen] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const modelOptions = useMemo(
    () => models.filter(m => m.type === type && m.size === size),
    [models, type, size],
  )
  const selected = useMemo(() => models.find(m => m.id === modelId) ?? null, [models, modelId])

  useEffect(() => {
    if (modelId && modelOptions.some(m => m.id === modelId)) return
    setModelId(modelOptions[0]?.id ?? null)
  }, [modelOptions, modelId])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const hash = window.location.hash
    if (!hash.startsWith('#b=')) return
    try {
      const data = JSON.parse(unb64url(hash.slice(3)))
      if (data.type) setType(data.type)
      if (data.size) setSize(data.size)
      if (data.modelId !== undefined) setModelId(data.modelId)
      if (data.needs) setNeeds({ ...DEFAULT_NEEDS, ...data.needs })
      if (data.manual) setManual(data.manual)
      if (data.overrides) setOverrides(data.overrides)
    } catch { /* 坏链接就当没带参数 */ }
  }, [])

  const input: SelectorInput = useMemo(
    () => ({ type, size, modelId, needs, manual }),
    [type, size, modelId, needs, manual],
  )
  const result = useMemo(() => recommend(input, models, parts), [input, models, parts])

  const displayLines = useMemo(() => result.lines.map(line => {
    const ov = overrides[line.role] ?? {}
    const part = ov.partId
      ? line.alternates.find(p => p.id === ov.partId) ?? line.part
      : line.part
    const qty = ov.qty ?? line.qty
    const unit = part ? effectivePrice(part.price, part.offers) : line.unitPrice
    return { ...line, part, qty, unitPrice: unit }
  }), [result.lines, overrides])

  const known = displayLines.reduce((sum, l) => sum + (l.unitPrice !== null ? l.unitPrice * l.qty : 0), 0)
  const unknown = displayLines.filter(l => l.unitPrice === null).length

  const selectType = (next: RobotType) => {
    setType(next)
    setOverrides({})
    const sameType = models.filter(m => m.type === next)
    const preferred = sameType.find(m => m.size === size) ?? sameType[0]
    if (preferred) {
      setSize(preferred.size)
      setModelId(preferred.id)
      setManual({
        mass_kg: preferred.mass_kg,
        dof: preferred.dof,
        effort_min_Nm: preferred.effort_min_Nm,
        effort_max_Nm: preferred.effort_max_Nm,
      })
    } else {
      setModelId(null)
      setManual(TYPE_DEFAULT[next])
    }
  }

  const selectSize = (next: SizeClass) => {
    setSize(next)
    setOverrides({})
    const preferred = models.find(m => m.type === type && m.size === next)
    setModelId(preferred?.id ?? null)
    if (preferred) {
      setManual({
        mass_kg: preferred.mass_kg,
        dof: preferred.dof,
        effort_min_Nm: preferred.effort_min_Nm,
        effort_max_Nm: preferred.effort_max_Nm,
      })
    }
  }

  const patchNeeds = (patch: Partial<Needs>) => setNeeds(prev => ({ ...prev, ...patch }))

  const toggleControl = (mode: ControlMode) => {
    setNeeds(prev => {
      const on = prev.controls.includes(mode)
      const next = on ? prev.controls.filter(c => c !== mode) : [...prev.controls, mode]
      return { ...prev, controls: next.length ? next : ['classical'] }
    })
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

  const payload = () => buildBomPayload(input, result, overrides)

  const exportJson = () => {
    download(`robowiki-bom-${type}-${result.reference?.model ?? 'custom'}.json`, JSON.stringify(payload(), null, 2), 'application/json')
    setNotice('已导出 BOM JSON')
  }

  const exportCsv = () => {
    download(`robowiki-bom-${type}-${result.reference?.model ?? 'custom'}.csv`, '\ufeff' + toCsv(payload()), 'text/csv;charset=utf-8')
    setNotice('已导出 CSV（Excel 可直接打开）')
  }

  const copyShare = async () => {
    const data = { type, size, modelId, needs, manual, overrides }
    const url = `${window.location.origin}${window.location.pathname}#b=${b64url(JSON.stringify(data))}`
    try {
      await navigator.clipboard.writeText(url)
      setNotice('分享链接已复制（含当前配置，不含 BOM 行覆盖以外的自定义项）')
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
      } else if (conf.type) {
        setType(conf.type)
        if (conf.size) setSize(conf.size)
        setModelId(null)
      }
      if (conf.needs) setNeeds({ ...DEFAULT_NEEDS, ...conf.needs })
      const ov: Record<string, Override> = {}
      for (const line of data.lines ?? []) {
        if (!line?.role) continue
        ov[line.role] = { partId: line.part_id ?? undefined, qty: line.qty }
      }
      setOverrides(ov)
      setNotice(`已导入 ${data.lines?.length ?? 0} 行 BOM；未匹配的型号保留为原选型。`)
    } catch {
      setNotice('导入失败：不是有效的 RoboWiki BOM JSON。')
    }
  }

  const setQty = (role: string, qty: number) => {
    const safe = Math.max(0, Math.min(999, Math.floor(qty)))
    setOverrides(prev => ({ ...prev, [role]: { ...prev[role], qty: safe } }))
  }

  const swapPart = (role: string, partId: string) => {
    setOverrides(prev => ({ ...prev, [role]: { ...prev[role], partId } }))
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)] lg:items-start">
      <aside className="space-y-3 lg:sticky lg:top-20">
        <section className="rounded-lg border border-line bg-surface">
          <div className="flex items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-[13px] font-semibold text-ink">1. 机型</h2>
            <span className="text-[11px] text-ink-3">54 个可信型号</span>
          </div>
          <div className="space-y-3 p-3">
            <div className="chip-row" role="group" aria-label="机器人类型">
              {(Object.keys(TYPE_LABEL) as RobotType[]).map(t => (
                <button key={t} type="button" className="chip h-8 px-3 text-[12px]" aria-pressed={type === t} onClick={() => selectType(t)}>
                  {TYPE_LABEL[t]}
                  <span className="mono tabular opacity-60">{models.filter(m => m.type === t).length}</span>
                </button>
              ))}
            </div>
            <div className="chip-row" role="group" aria-label="机器人档位">
              {SIZE_ORDER.map(s => {
                const count = models.filter(m => m.type === type && m.size === s).length
                return (
                  <button key={s} type="button" className="chip h-7 px-2.5 text-[11px]" aria-pressed={size === s} onClick={() => selectSize(s)}>
                    {SIZE_LABEL[s]}
                    <span className="mono tabular opacity-60">{count}</span>
                  </button>
                )
              })}
            </div>
            <label className="block text-[11px] text-ink-3">
              参考机型
              <select
                value={modelId ?? ''}
                onChange={e => {
                  const id = e.target.value || null
                  setModelId(id)
                  setOverrides({})
                  const m = models.find(x => x.id === id)
                  const base = m ?? selected
                  if (base) setManual({ mass_kg: base.mass_kg, dof: base.dof, effort_min_Nm: base.effort_min_Nm, effort_max_Nm: base.effort_max_Nm })
                }}
                className="mt-1 h-9 w-full rounded-md border border-line bg-surface px-2 text-[12px] text-ink"
              >
                <option value="">自定义（按下方质量/DOF/扭矩）</option>
                {modelOptions.map(m => (
                  <option key={m.id} value={m.id}>{m.model} · {m.mass_kg} kg · {m.dof} DOF · {m.motor_tier}</option>
                ))}
              </select>
            </label>
            {modelOptions.length === 0 && (
              <p className="rounded-md bg-warning-soft px-2.5 py-2 text-[11px] leading-5 text-warning">
                这个构型/档位没有公开可信 URDF。可改档位或直接用下方自定义参数占位。
              </p>
            )}
            {selected ? (
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 rounded-md border border-line bg-surface-2 p-2.5 text-[11px]">
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
                  <label key={k} className="text-[11px] text-ink-3">
                    {label}
                    <input
                      type="number"
                      min={0}
                      step={step}
                      value={manual[k]}
                      onChange={e => setManual(prev => ({ ...prev, [k]: Math.max(0, Number(e.target.value) || 0) }))}
                      className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-[12px] text-ink"
                    />
                  </label>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="rounded-lg border border-line bg-surface">
          <div className="flex items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-[13px] font-semibold text-ink">2. 功能需求</h2>
            <button type="button" onClick={() => setNeeds(DEFAULT_NEEDS)} className="text-[11px] text-ink-3 hover:text-ink">重置</button>
          </div>
          <div className="space-y-3 p-3">
            <div>
              <p className="mb-1.5 text-[11px] text-ink-3">预设</p>
              <div className="flex flex-wrap gap-1.5">
                {PRESETS.map(p => (
                  <button key={p.id} type="button" title={p.hint} onClick={() => patchNeeds(p.needs)} className="chip h-7 px-2.5 text-[11px]">
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-1.5 text-[11px] text-ink-3">控制方式（可多选）</p>
              <div className="flex flex-wrap gap-1.5">
                {CONTROL_ORDER.map(c => (
                  <button key={c} type="button" className="chip h-7 px-2.5 text-[11px]" aria-pressed={needs.controls.includes(c)} onClick={() => toggleControl(c)}>
                    {c === 'classical' ? '传统控制' : c === 'rl' ? '强化学习' : c === 'teleop' ? '遥操作' : '自主导航'}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[12px] text-ink-2">
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
              <label className="text-[11px] text-ink-3">
                供电
                <select value={needs.power} onChange={e => patchNeeds({ power: e.target.value as Needs['power'] })} className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-[12px] text-ink">
                  <option value="battery">电池</option>
                  <option value="tethered">外接电源</option>
                </select>
              </label>
              <label className="text-[11px] text-ink-3">
                备件
                <select value={needs.sparePct} onChange={e => patchNeeds({ sparePct: Number(e.target.value) })} className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-[12px] text-ink">
                  <option value={0}>0%</option>
                  <option value={10}>10%</option>
                  <option value={20}>20%</option>
                </select>
              </label>
            </div>
            <label className="block text-[11px] text-ink-3">
              预算上限（CNY，可空）
              <input
                type="number"
                min={0}
                step={100}
                value={needs.budget ?? ''}
                onChange={e => patchNeeds({ budget: e.target.value === '' ? null : Math.max(0, Number(e.target.value)) })}
                className="mt-1 h-8 w-full rounded-md border border-line bg-surface px-2 text-[12px] text-ink"
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
              <p className="mt-0.5 text-[12px] text-ink-3">
                {result.effective.mass_kg} kg · {result.effective.dof} DOF · effort {result.effective.effort_min_Nm}–{result.effective.effort_max_Nm} N·m
                {selected ? ` · ${selected.motor_tier}` : ''}
              </p>
            </div>
            <div className="text-right">
              <p className="text-[11px] text-ink-3">已知小计</p>
              <p className="mono tabular text-xl font-bold text-ink">{formatPrice(known)}</p>
              <p className="text-[10px] text-ink-3">{unknown ? `另有 ${unknown} 条询价` : '全部有价'}</p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            <button type="button" className="chip h-8 px-3 text-[12px]" onClick={exportJson}>导出 BOM JSON</button>
            <button type="button" className="chip h-8 px-3 text-[12px]" onClick={exportCsv}>导出 CSV</button>
            <button type="button" className="chip h-8 px-3 text-[12px]" onClick={copyShare}>复制分享链接</button>
            <button type="button" className="chip h-8 px-3 text-[12px]" onClick={() => fileRef.current?.click()}>导入 BOM</button>
            <input ref={fileRef} type="file" accept="application/json,.json" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) void importJson(f); e.target.value = '' }} />
          </div>
          {notice && <p className="mt-2 break-all rounded bg-surface-2 px-2 py-1.5 text-[11px] text-ink-2">{notice}</p>}
        </section>

        {result.warnings.length > 0 && (
          <section className="rounded-lg border border-warning/30 bg-warning-soft p-3">
            <h2 className="text-[12px] font-semibold text-warning">需要复核</h2>
            <ul className="mt-1.5 list-disc space-y-1 pl-4 text-[11px] leading-5 text-warning">
              {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </section>
        )}

        <section className="overflow-hidden rounded-lg border border-line bg-surface">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-[13px] font-semibold text-ink">推荐 BOM</h2>
            <span className="text-[11px] text-ink-3">换主选/备选、改数量后，导出会跟着变</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] border-collapse text-left text-[12px]">
              <thead>
                <tr className="border-b border-line text-[11px] text-ink-3">
                  <th className="p-2 font-medium">角色 / 主选</th>
                  <th className="p-2 font-medium">备选</th>
                  <th className="p-2 font-medium">数量</th>
                  <th className="p-2 font-medium">单价</th>
                  <th className="p-2 font-medium">小计</th>
                  <th className="p-2 font-medium">状态</th>
                </tr>
              </thead>
              <tbody>
                {displayLines.map((line, idx) => (
                  <tr key={`${line.role}-${idx}`} className="border-b border-line align-top">
                    <td className="p-2">
                      <div className="flex gap-2">
                        <PartThumb part={line.part} />
                        <div className="min-w-0">
                          <p className="text-[10px] text-ink-3">{line.group} · {line.role}</p>
                          {line.part ? (
                            <a href={partHref(line.part)} className="block truncate font-medium text-ink hover:text-brand">{line.part.model}</a>
                          ) : (
                            <span className="block truncate font-medium text-ink">{line.manual?.model}</span>
                          )}
                          <p className="truncate text-[10px] text-ink-3">{line.part?.vendor ?? line.manual?.vendor}</p>
                          <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-ink-3" title={line.note}>{line.note}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-2">
                      {line.alternates.length > 0 ? (
                        <select
                          value={line.part?.id ?? ''}
                          onChange={e => swapPart(line.role, e.target.value)}
                          aria-label={`${line.role}主选与备选`}
                          className="h-7 w-full max-w-[180px] rounded border border-line bg-surface px-1.5 text-[11px] text-ink"
                        >
                          {line.part && <option value={line.part.id}>{line.part.model}</option>}
                          {line.alternates.map(p => <option key={p.id} value={p.id}>{p.model}</option>)}
                        </select>
                      ) : <span className="text-ink-3">—</span>}
                    </td>
                    <td className="p-2">
                      <input
                        type="number"
                        min={0}
                        max={999}
                        value={line.qty}
                        onChange={e => setQty(line.role, Number(e.target.value))}
                        aria-label={`${line.role}数量`}
                        className="mono tabular h-7 w-14 rounded border border-line bg-surface px-1.5 text-[11px] text-ink"
                      />
                    </td>
                    <td className="p-2 mono tabular whitespace-nowrap text-ink-2">{formatPrice(line.unitPrice)}</td>
                    <td className="p-2 mono tabular whitespace-nowrap text-ink">{formatPrice(line.unitPrice !== null ? line.unitPrice * line.qty : null)}</td>
                    <td className="p-2"><StatusBadge status={line.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-lg border border-line bg-surface">
          <div className="flex items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-[13px] font-semibold text-ink">线束与接口</h2>
            <span className="text-[11px] text-ink-3">按额定电流 ×70% 选线规</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-left text-[12px]">
              <thead>
                <tr className="border-b border-line text-[11px] text-ink-3">
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
          <div className="space-y-1 border-t border-line px-3 py-2 text-[11px] leading-5 text-ink-3">
            {result.harness.map((row, i) => <p key={i}><span className="text-ink-2">{row.motor}：</span>{row.note}</p>)}
            <p>电机端统一 XT30PW(2+2)：2 电源 + 2 信号（CANH/CANL），功率针 20A MAX、信号针 1A；线束最大推荐 14AWG。多电机共母线时，母线线规按下游电流总和重新计算。</p>
          </div>
        </section>

        <section className="rounded-lg border border-line bg-surface">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2">
            <h2 className="text-[13px] font-semibold text-ink">基础 MJCF</h2>
            <div className="flex gap-1.5">
              <button type="button" className="chip h-7 px-2.5 text-[11px]" onClick={() => { void navigator.clipboard.writeText(result.mjcf); setNotice('MJCF 已复制') }}>复制</button>
              <button type="button" className="chip h-7 px-2.5 text-[11px]" onClick={() => download(`robowiki-${type}-${result.reference?.model ?? 'custom'}.xml`, result.mjcf, 'application/xml')}>下载 XML</button>
              <button type="button" className="chip h-7 px-2.5 text-[11px]" onClick={() => setCodeOpen(v => !v)} aria-expanded={codeOpen}>{codeOpen ? '收起' : '预览'}</button>
            </div>
          </div>
          <p className="px-3 pt-2 text-[11px] leading-5 text-ink-3">
            按参考机型的质量、DOF 和所选执行器峰值扭矩生成；几何是胶囊/盒体占位，不是 CAD。可直接用 MuJoCo 打开改尺寸、惯量和碰撞。
          </p>
          {codeOpen && (
            <pre className="m-3 max-h-80 overflow-auto rounded-md border border-line bg-surface-2 p-3 text-[10px] leading-4 text-ink-2">
              {result.mjcf}
            </pre>
          )}
        </section>

        <section className="rounded-lg border border-line bg-surface p-3 text-[11px] leading-5 text-ink-3">
          <p><span className="text-ink-2">选型口径：</span>执行器按参考机型的 URDF effort 上限选，优先 CAN/CANFD；没有覆盖时退到 0.7 倍阈值并标「部分声明」，仍不够则列最大扭矩并标「未声明」。上/下位机、感知、电池都从部件库现有条目里选；站内没有的（如 12S 整包）会明确标缺口，不拿估算值冒充。</p>
          <p className="mt-1"><span className="text-ink-2">范围：</span>只含执行器、主控、电池、传感器与关键线束；结构件、紧固件、3D 打印件不在选型台内。</p>
          <p className="mt-1"><span className="text-ink-2">参考：</span>54 个可信型号来自 enkeebot 的 URDF 解析与交叉验证；线束规则来自 ENCOS《电机线束推荐说明》（2026-06-22）。</p>
        </section>
      </div>
    </div>
  )
}
