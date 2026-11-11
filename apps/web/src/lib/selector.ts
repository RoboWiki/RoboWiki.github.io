import type { CatalogPart } from './catalog'
import { effectivePrice } from './utils'
import { buildMjcf } from './mjcf'

export type RobotType = 'quadruped' | 'wheel_legged' | 'humanoid' | 'arm'
export type SizeClass = 'tiny' | 'small' | 'medium' | 'large' | 'xlarge'
export type ControlMode = 'classical' | 'rl' | 'teleop' | 'autonomy'
export type Compat = 'declared' | 'partial' | 'not_declared' | 'n_a'

export type SelectorModel = {
  id: string
  type: RobotType
  size: SizeClass
  model: string
  vendor: string
  mass_kg: number
  dof: number
  effort_min_Nm: number
  effort_max_Nm: number
  torque_density_Nm_per_kg: number
  motor_tier: string
  verification: string
  urdf_source: string
}

export type Needs = {
  controls: ControlMode[]
  depth: boolean
  lidar: boolean
  camera: boolean
  remote: boolean
  compute: boolean
  power: 'battery' | 'tethered'
  hollow: boolean
  budget: number | null
  sparePct: number
  mixedLimbs: boolean
}

export type SelectorInput = {
  type: RobotType
  size: SizeClass
  modelId: string | null
  needs: Needs
  manual: { mass_kg: number; dof: number; effort_min_Nm: number; effort_max_Nm: number }
}

export type BomLine = {
  role: string
  group: '执行器' | '主控' | '感知' | '电源' | '线束' | '其他'
  part: CatalogPart | null
  qty: number
  unitPrice: number | null
  note: string
  status: Compat
  alternates: CatalogPart[]
  manual?: { model: string; vendor: string; price: number | null }
}

export type HarnessRow = {
  motor: string
  qty: number
  current_A: number
  awg: number
  connector: string
  requiredBore_mm: number
  status: Compat
  note: string
}

export type SelectionResult = {
  reference: SelectorModel | null
  effective: { type: RobotType; mass_kg: number; dof: number; effort_min_Nm: number; effort_max_Nm: number }
  lines: BomLine[]
  harness: HarnessRow[]
  warnings: string[]
  mjcf: string
  totals: { known_cny: number; unknown_lines: number; currency: 'CNY' }
}

export const TYPE_LABEL: Record<RobotType, string> = {
  quadruped: '四足',
  wheel_legged: '四轮足',
  humanoid: '人形',
  arm: '机械臂',
}

export const SIZE_LABEL: Record<SizeClass, string> = {
  tiny: '桌面 <5kg',
  small: '小型 5–15kg',
  medium: '中型 15–50kg',
  large: '大型 50–150kg',
  xlarge: '超大 >150kg',
}

export const CONTROL_LABEL: Record<ControlMode, string> = {
  classical: '传统控制',
  rl: '强化学习',
  teleop: '遥操作',
  autonomy: '自主导航',
}

export const STATUS_LABEL: Record<Compat, string> = {
  declared: '已声明',
  partial: '部分声明',
  not_declared: '未声明',
  n_a: '不适用',
}

export const DEFAULT_NEEDS: Needs = {
  controls: ['classical'],
  depth: false,
  lidar: false,
  camera: false,
  remote: false,
  compute: false,
  power: 'battery',
  hollow: false,
  budget: null,
  sparePct: 0,
  mixedLimbs: false,
}

export const TYPE_DEFAULT: Record<RobotType, { dof: number; mass_kg: number; effort_min_Nm: number; effort_max_Nm: number }> = {
  quadruped: { dof: 12, mass_kg: 15, effort_min_Nm: 20, effort_max_Nm: 40 },
  wheel_legged: { dof: 16, mass_kg: 25, effort_min_Nm: 20, effort_max_Nm: 45 },
  humanoid: { dof: 23, mass_kg: 35, effort_min_Nm: 20, effort_max_Nm: 80 },
  arm: { dof: 6, mass_kg: 5, effort_min_Nm: 7, effort_max_Nm: 30 },
}

export const PRESETS: Array<{ id: string; label: string; hint: string; needs: Partial<Needs> }> = [
  { id: 'blind', label: '盲走', hint: 'IMU + 主控 + 执行器，不带感知和上位机', needs: { controls: ['classical'], depth: false, lidar: false, camera: false, remote: false, compute: false } },
  { id: 'teleop', label: '遥控', hint: '盲走 + 遥控器', needs: { controls: ['classical', 'teleop'], depth: false, lidar: false, camera: false, remote: true, compute: false } },
  { id: 'perception', label: '感知', hint: '加深度相机或雷达，需要上位机', needs: { controls: ['classical'], depth: true, lidar: true, camera: false, remote: false, compute: true } },
  { id: 'rl', label: 'RL', hint: '强化学习部署，必须上位机', needs: { controls: ['rl'], depth: false, lidar: false, camera: false, remote: false, compute: true } },
  { id: 'autonomy', label: '自主', hint: '雷达 + 上位机，可不要遥控器', needs: { controls: ['autonomy'], depth: false, lidar: true, camera: false, remote: false, compute: true } },
  { id: 'full', label: '全功能', hint: 'RL + 遥操作 + 自主 + 深度/雷达', needs: { controls: ['rl', 'teleop', 'autonomy'], depth: true, lidar: true, camera: false, remote: true, compute: true } },
]

const n = (v: unknown): number | null => {
  if (typeof v === 'number' && Number.isFinite(v)) return v
  if (typeof v === 'string' && /^\s*-?\d+(?:\.\d+)?\s*$/.test(v)) {
    const x = Number(v)
    return Number.isFinite(x) ? x : null
  }
  return null
}

const specs = (p: CatalogPart) => (p.specs ?? {}) as Record<string, unknown>
const priceOf = (p: CatalogPart) => effectivePrice(p.price, p.offers)
const canText = (p: CatalogPart) => String(specs(p).comm ?? specs(p).iface ?? '').toUpperCase()
const hasCan = (p: CatalogPart) => /CAN/.test(canText(p))
const hasCanFd = (p: CatalogPart) => /CAN\s*FD|CANFD|FD\s*CAN/.test(canText(p))
const via = (p: CatalogPart) => p.vendor || ''

function byPriceKnownThenAsc(a: CatalogPart, b: CatalogPart): number {
  const pa = priceOf(a)
  const pb = priceOf(b)
  if (pa === null && pb !== null) return 1
  if (pa !== null && pb === null) return -1
  if (pa !== null && pb !== null && pa !== pb) return pa - pb
  return a.model.localeCompare(b.model, 'zh-CN')
}

function uniqueTop(list: CatalogPart[], count: number): CatalogPart[] {
  const seen = new Set<string>()
  const out: CatalogPart[] = []
  for (const p of list) {
    if (seen.has(p.id)) continue
    seen.add(p.id)
    out.push(p)
    if (out.length >= count) break
  }
  return out
}

type PartPick = { primary: CatalogPart | null; alternates: CatalogPart[]; status: Compat; note: string }

function pickActuator(parts: CatalogPart[], type: RobotType, requirement: number, mixed: boolean): PartPick {
  const subtypes = type === 'arm'
    ? ['harmonic', 'planetary', 'qdd', 'direct']
    : ['qdd', 'planetary', 'direct']
  let pool = parts.filter(p => p.category === 'actuator' && subtypes.includes(String(p.subtype ?? '')))
  pool = pool.filter(p => {
    const tau = n(specs(p).tau_peak_Nm)
    return tau !== null && tau > 0
  })
  if (!pool.length) {
    return { primary: null, alternates: [], status: 'not_declared', note: '执行器库为空' }
  }
  const tauOf = (p: CatalogPart) => n(specs(p).tau_peak_Nm) ?? 0
  let status: Compat = 'declared'
  let meet = pool.filter(p => tauOf(p) >= requirement)
  if (!meet.length) {
    status = 'partial'
    meet = pool.filter(p => tauOf(p) >= requirement * 0.7)
  }
  if (!meet.length) {
    status = 'not_declared'
    meet = [...pool].sort((a, b) => tauOf(b) - tauOf(a)).slice(0, 3)
  }
  const ranked = [...meet].sort((a, b) => {
    if (hasCanFd(a) !== hasCanFd(b)) return hasCanFd(a) ? -1 : 1
    if (hasCan(a) !== hasCan(b)) return hasCan(a) ? -1 : 1
    const price = byPriceKnownThenAsc(a, b)
    if (price !== 0) return price
    return tauOf(a) - tauOf(b)
  })
  const primary = ranked[0] ?? null
  const note = status === 'declared'
    ? `按参考机型峰值 ${requirement.toFixed(1)} N·m 选型，留有余量；优先 CAN/CANFD。`
    : status === 'partial'
      ? `没有完全覆盖 ${requirement.toFixed(1)} N·m 的型号，退到 0.7 倍阈值；需复核峰值/散热。`
      : `站内没有覆盖 ${requirement.toFixed(1)} N·m 的型号，列出最大扭矩作为超档方案；建议换参考机型或定制。`
  return { primary, alternates: uniqueTop(ranked.slice(1), 3), status, note: mixed ? note + ' 腿/臂混搭时按各自扭矩需求分别选。' : note }
}

function pickLowController(parts: CatalogPart[], actuator: CatalogPart | null): PartPick {
  const fd = actuator ? hasCanFd(actuator) : false
  const pool = parts.filter(p => p.category === 'controller_low' && (n(specs(p).can) ?? 0) >= 1)
  if (!pool.length) return { primary: null, alternates: [], status: 'not_declared', note: '站内没有带 CAN 的下位机' }
  const ranked = [...pool].sort((a, b) => {
    if (fd && hasCanFd(a) !== hasCanFd(b)) return hasCanFd(a) ? -1 : 1
    const ca = n(specs(a).can) ?? 0
    const cb = n(specs(b).can) ?? 0
    if (ca !== cb) return cb - ca
    return byPriceKnownThenAsc(a, b)
  })
  return {
    primary: ranked[0] ?? null,
    alternates: uniqueTop(ranked.slice(1), 3),
    status: fd && ranked[0] && hasCanFd(ranked[0]) ? 'declared' : 'partial',
    note: fd ? '执行器支持 CANFD，下位机优先选 FDCAN。' : '执行器以 CAN/RS-485 为主，下位机需保留对应总线。',
  }
}

function pickHighController(parts: CatalogPart[], needs: Needs): PartPick | null {
  const needHigh = needs.compute
    || needs.controls.some(c => c === 'rl' || c === 'autonomy')
    || needs.depth || needs.lidar || needs.camera
  if (!needHigh) return null
  const heavy = needs.controls.includes('autonomy') && (needs.depth || needs.lidar)
  const threshold = heavy ? 100 : needs.controls.includes('rl') ? 40 : 8
  const pool = parts.filter(p => p.category === 'controller_high')
  const withNpu = pool.map(p => ({ p, npu: n(specs(p).npu_tops) ?? 0 })).filter(x => x.npu > 0)
  let candidates = withNpu.filter(x => x.npu >= threshold)
  if (!candidates.length) candidates = withNpu
  candidates.sort((a, b) => {
    if (a.npu !== b.npu) return a.npu - b.npu
    return byPriceKnownThenAsc(a.p, b.p)
  })
  const ranked = candidates.map(x => x.p)
  return {
    primary: ranked[0] ?? null,
    alternates: uniqueTop(ranked.slice(1), 3),
    status: 'partial',
    note: heavy
      ? '感知 + 自主建议 100 TOPS 级；训练在 PC/服务器，机上只跑推理。'
      : needs.controls.includes('rl')
        ? 'RL 机上推理建议 40 TOPS 级；训练仍用 PC。'
        : '视觉/上位机功能建议 8 TOPS 以上。',
  }
}

function pickImu(parts: CatalogPart[]): PartPick {
  const pool = parts.filter(p => p.category === 'imu')
  const ranked = [...pool].sort((a, b) => {
    const ca = /CAN/.test(canText(a)) ? 1 : 0
    const cb = /CAN/.test(canText(b)) ? 1 : 0
    if (ca !== cb) return cb - ca
    return byPriceKnownThenAsc(a, b)
  })
  return {
    primary: ranked[0] ?? null,
    alternates: uniqueTop(ranked.slice(1), 3),
    status: ranked[0] && /CAN/.test(canText(ranked[0])) ? 'declared' : 'partial',
    note: '腿部机器人至少 1 个 IMU；优先 CAN 输出，方便与下位机同总线。',
  }
}

function pickDepth(parts: CatalogPart[]): PartPick {
  const pool = parts.filter(p => p.category === 'camera' && specs(p).depth_range_m !== null && specs(p).depth_range_m !== '')
  const ranked = [...pool].sort(byPriceKnownThenAsc)
  return {
    primary: ranked[0] ?? null,
    alternates: uniqueTop(ranked.slice(1), 3),
    status: 'declared',
    note: '深度相机量程与基线要按使用距离核对；室内 0.2–3 m 够用。',
  }
}

function pickRgb(parts: CatalogPart[]): PartPick {
  const pool = parts.filter(p => p.category === 'camera' && /USB/i.test(canText(p)))
  const ranked = [...pool].sort(byPriceKnownThenAsc)
  return {
    primary: ranked[0] ?? null,
    alternates: uniqueTop(ranked.slice(1), 3),
    status: 'partial',
    note: '只做视觉时可用 USB 相机；需要深度再换深度相机。',
  }
}

function pickLidar(parts: CatalogPart[], threeD: boolean): PartPick {
  const pool = parts.filter(p => p.category === 'lidar')
  const filtered = threeD
    ? pool.filter(p => String(specs(p).fov ?? '').includes('360') && (n(specs(p).range_m) ?? 0) >= 20)
    : pool
  const ranked = [...(filtered.length ? filtered : pool)].sort(byPriceKnownThenAsc)
  return {
    primary: ranked[0] ?? null,
    alternates: uniqueTop(ranked.slice(1), 3),
    status: threeD ? 'declared' : 'partial',
    note: threeD ? '导航/建图优先 3D 360° 雷达；注意以太网与供电。' : '室内小机型可先用 2D 雷达；量程和 FOV 按场景核对。',
  }
}

function pickRemote(parts: CatalogPart[]): PartPick {
  const pool = parts.filter(p => p.category === 'remote_controller')
  const ranked = [...pool].sort((a, b) => {
    const ca = n(specs(a).channels) ?? 0
    const cb = n(specs(b).channels) ?? 0
    if (ca !== cb) return cb - ca
    return byPriceKnownThenAsc(a, b)
  })
  return {
    primary: ranked[0] ?? null,
    alternates: uniqueTop(ranked.slice(1), 3),
    status: 'partial',
    note: '遥控器按通道数和 SBUS/CRSF 选；自主方案可保留一个急停/接管开关。',
  }
}

const AWG_TABLE = [
  { awg: 26, refA: 1.5, od: 1.5 },
  { awg: 24, refA: 2, od: 1.6 },
  { awg: 22, refA: 3, od: 1.7 },
  { awg: 20, refA: 5, od: 1.8 },
  { awg: 18, refA: 8, od: 2.3 },
  { awg: 16, refA: 13, od: 3.0 },
  { awg: 14, refA: 20, od: 3.5 },
  { awg: 12, refA: 34, od: 4.5 },
  { awg: 10, refA: 50, od: 5.45 },
  { awg: 8, refA: 66, od: 6.3 },
]

function awgFor(current: number, cap14: boolean): { awg: number; od: number; capped: boolean } {
  const need = current / 0.7
  let pick = AWG_TABLE[AWG_TABLE.length - 1]
  for (const row of AWG_TABLE) {
    if (row.refA >= need) { pick = row; break }
  }
  if (cap14 && pick.awg < 14) return { awg: 14, od: 3.5, capped: true }
  return { awg: pick.awg, od: pick.od, capped: false }
}

export function recommend(input: SelectorInput, models: SelectorModel[], parts: CatalogPart[]): SelectionResult {
  const reference = models.find(m => m.id === input.modelId) ?? null
  const fallback = TYPE_DEFAULT[input.type]
  const effective = reference
    ? {
        type: reference.type,
        mass_kg: reference.mass_kg,
        dof: reference.dof,
        effort_min_Nm: reference.effort_min_Nm,
        effort_max_Nm: reference.effort_max_Nm,
      }
    : {
        type: input.type,
        mass_kg: input.manual.mass_kg,
        dof: input.manual.dof,
        effort_min_Nm: input.manual.effort_min_Nm,
        effort_max_Nm: input.manual.effort_max_Nm,
      }
  const needs = input.needs
  const warnings: string[] = []
  const lines: BomLine[] = []
  const harness: HarnessRow[] = []

  if (reference && /^M8/.test(reference.motor_tier)) {
    warnings.push(`${reference.model} 的峰值需求 ${reference.effort_max_Nm} N·m 属于 M8，站内没有对应执行器。`)
  }

  // 执行器
  let actuatorPick: PartPick
  let actuatorQty = effective.dof
  const spare = Math.ceil(effective.dof * Math.max(0, Math.min(50, needs.sparePct)) / 100)
  const mainSeed = (() => {
    if (needs.mixedLimbs && input.type === 'humanoid' && effective.dof > 12) {
      const legs = pickActuator(parts, input.type, effective.effort_max_Nm, false)
      const armReq = Math.max(effective.effort_min_Nm * 2, effective.effort_max_Nm * 0.3)
      const arms = pickActuator(parts, input.type, armReq, false)
      if (legs.primary) {
        lines.push({
          role: '执行器（腿）', group: '执行器', part: legs.primary, qty: 12 + spare,
          unitPrice: priceOf(legs.primary), note: legs.note, status: legs.status, alternates: legs.alternates,
        })
      }
      if (arms.primary) {
        lines.push({
          role: '执行器（臂）', group: '执行器', part: arms.primary, qty: effective.dof - 12,
          unitPrice: priceOf(arms.primary), note: arms.note, status: arms.status, alternates: arms.alternates,
        })
      }
      warnings.push('腿/臂混搭为估算：腿部按 effort_max，臂部按 max(2×effort_min, 0.3×effort_max)；需按关节表复核。')
      return legs
    }
    return pickActuator(parts, input.type, effective.effort_max_Nm, false)
  })()
  actuatorPick = mainSeed
  if (!(needs.mixedLimbs && input.type === 'humanoid' && effective.dof > 12)) {
    if (actuatorPick.primary) {
      lines.push({
        role: '执行器', group: '执行器', part: actuatorPick.primary, qty: actuatorQty + spare,
        unitPrice: priceOf(actuatorPick.primary), note: actuatorPick.note, status: actuatorPick.status,
        alternates: actuatorPick.alternates,
      })
    } else {
      warnings.push('没有可用的执行器条目。')
    }
  }
  if (actuatorPick.status !== 'declared') {
    warnings.push(actuatorPick.note)
  }
  const actuator = actuatorPick.primary

  // 下位机
  const low = pickLowController(parts, actuator)
  if (low.primary) {
    lines.push({ role: '下位机 / 实时控制', group: '主控', part: low.primary, qty: 1, unitPrice: priceOf(low.primary), note: low.note, status: low.status, alternates: low.alternates })
  } else {
    warnings.push('没有带 CAN 的下位机，需外接 USB-CAN 或更换方案。')
  }

  // 上位机
  const high = pickHighController(parts, needs)
  if (high?.primary) {
    lines.push({ role: '上位机 / 感知计算', group: '主控', part: high.primary, qty: 1, unitPrice: priceOf(high.primary), note: high.note, status: high.status, alternates: high.alternates })
  }

  // IMU
  if (input.type !== 'arm') {
    const imu = pickImu(parts)
    if (imu.primary) {
      lines.push({ role: 'IMU', group: '感知', part: imu.primary, qty: 1, unitPrice: priceOf(imu.primary), note: imu.note, status: imu.status, alternates: imu.alternates })
    } else {
      warnings.push('没有 IMU 条目，腿部控制不可用。')
    }
  }

  // 感知
  if (needs.depth) {
    const depth = pickDepth(parts)
    if (depth.primary) lines.push({ role: '深度相机', group: '感知', part: depth.primary, qty: 1, unitPrice: priceOf(depth.primary), note: depth.note, status: depth.status, alternates: depth.alternates })
    else warnings.push('站内没有深度相机条目。')
  }
  if (needs.lidar || needs.controls.includes('autonomy')) {
    const threeD = effective.mass_kg > 20 || input.size === 'medium' || input.size === 'large' || input.size === 'xlarge'
    const lidar = pickLidar(parts, threeD)
    if (lidar.primary) lines.push({ role: '激光雷达', group: '感知', part: lidar.primary, qty: 1, unitPrice: priceOf(lidar.primary), note: lidar.note, status: lidar.status, alternates: lidar.alternates })
    else warnings.push('站内没有激光雷达条目。')
  }
  if (needs.camera && !needs.depth) {
    const cam = pickRgb(parts)
    if (cam.primary) lines.push({ role: '相机', group: '感知', part: cam.primary, qty: 1, unitPrice: priceOf(cam.primary), note: cam.note, status: cam.status, alternates: cam.alternates })
  }

  // 遥控
  if (needs.remote || needs.controls.includes('teleop')) {
    const remote = pickRemote(parts)
    if (remote.primary) lines.push({ role: '遥控器', group: '感知', part: remote.primary, qty: 1, unitPrice: priceOf(remote.primary), note: remote.note, status: remote.status, alternates: remote.alternates })
  }

  // 电池
  const motorVolt = n(specs(actuator ?? ({} as CatalogPart)).voltage_V)
  const highVolt = motorVolt !== null && motorVolt >= 40
  if (needs.power === 'battery') {
    const estimatedWh = Math.min(800, Math.max(50, effective.mass_kg * 8))
    const batteries = parts.filter(p => p.category === 'battery')
    const refVendor = reference?.vendor ?? ''
    const packOk = (p: CatalogPart) => {
      const iface = String(specs(p).iface ?? '')
      const proprietary = /DJI|Go2|专用/.test(iface)
        || /DJI|大疆|Unitree|宇树/i.test(p.vendor)
        || /^BT\d/i.test(p.model)
      return !proprietary || (refVendor && p.vendor === refVendor)
    }
    const genericFirst = (a: CatalogPart, b: CatalogPart) => {
      const pa = packOk(a) ? 0 : 1
      const pb = packOk(b) ? 0 : 1
      return pa - pb
    }
    if (highVolt) {
      const packs = batteries
        .filter(p => (n(specs(p).voltage_V) ?? 0) >= 18 && (n(specs(p).voltage_V) ?? 0) <= 30)
        .sort((a, b) => genericFirst(a, b) || (n(specs(b).energy_wh) ?? 0) - (n(specs(a).energy_wh) ?? 0))
      const pack = packs[0] ?? null
      if (pack) {
        lines.push({
          role: '电池组（2×6S 串联）', group: '电源', part: pack, qty: 2, unitPrice: priceOf(pack),
          note: `所选执行器为 ${motorVolt?.toFixed(0)}V 级；站内暂无 12S 整包，用 2 块 6S 同批次串联。估算能耗约 ${estimatedWh.toFixed(0)} Wh/1h。`,
          status: 'partial', alternates: uniqueTop(packs.slice(1), 3),
        })
      }
      warnings.push('48V 级电池站内暂无整包；2×6S 串联需要同批次同容量电芯，BMS 必须按 12S 选，不能直接串两块带板电池。')
    } else {
      const packs = batteries
        .filter(p => {
          const v = n(specs(p).voltage_V) ?? 0
          return v >= 18 && v <= 30
        })
        .sort((a, b) => {
          const pa = packOk(a) ? 0 : 1
          const pb = packOk(b) ? 0 : 1
          if (pa !== pb) return pa - pb
          const ea = n(specs(a).energy_wh) ?? 0
          const eb = n(specs(b).energy_wh) ?? 0
          const aOk = ea >= estimatedWh
          const bOk = eb >= estimatedWh
          if (aOk !== bOk) return aOk ? -1 : 1
          if (aOk && bOk && ea !== eb) return ea - eb
          return byPriceKnownThenAsc(a, b)
        })
      const pack = packs[0] ?? null
      if (pack) {
        const wh = n(specs(pack).energy_wh) ?? 0
        lines.push({
          role: '电池', group: '电源', part: pack, qty: 1, unitPrice: priceOf(pack),
          note: `按 ${effective.mass_kg.toFixed(1)} kg、约 ${estimatedWh.toFixed(0)} Wh/1h 估算；该包 ${wh ? wh.toFixed(0) + ' Wh' : '能量未公布'}，续航需按实测功耗复核。`,
          status: wh >= estimatedWh ? 'declared' : 'partial', alternates: uniqueTop(packs.slice(1), 3),
        })
      } else {
        warnings.push('没有 24V 级电池条目。')
      }
    }
  } else {
    const psu = parts.find(p => p.category === 'power' && /LM2596|UBEC/i.test(p.model))
    if (psu) lines.push({ role: '外接供电模块', group: '电源', part: psu, qty: 1, unitPrice: priceOf(psu), note: '外接供电，省去电池与 BMS；注意母线电压和急停。', status: 'partial', alternates: [] })
  }

  // 电源小件
  const fuse = parts.find(p => p.category === 'power' && /保险丝/i.test(p.model))
  if (fuse) lines.push({ role: '保险丝座', group: '电源', part: fuse, qty: 1, unitPrice: priceOf(fuse), note: '按母线电流的 1.5–2 倍选保险丝。', status: 'partial', alternates: [] })

  // 线束：连接器
  const connector = parts.find(p => p.id === 'amass-xt30-2p2') ?? parts.find(p => p.category === 'connector' && /XT30\(2\+2\)/.test(p.model))
  const connectorAlts = parts.filter(p => p.category === 'connector' && /XT30/.test(p.model) && p.id !== connector?.id)
  if (connector) {
    lines.push({
      role: '电机连接器 XT30(2+2)', group: '线束', part: connector, qty: effective.dof + spare,
      unitPrice: priceOf(connector), note: '2 电源 + 2 信号（CANH/CANL），功率针 20A MAX、信号针 1A；线束最大推荐 14AWG。',
      status: 'declared', alternates: uniqueTop(connectorAlts, 3),
    })
  }

  // 线束：逐电机线规
  const perMotorCurrent = (() => {
    if (!actuator) return 10
    const ir = n(specs(actuator).i_rated_A)
    if (ir !== null) return ir
    const ip = n(specs(actuator).i_peak_A)
    if (ip !== null) return Math.max(1, ip * 0.4)
    return 10
  })()
  const motorGauge = awgFor(perMotorCurrent, true)
  const busCurrent = perMotorCurrent * effective.dof
  const busGauge = awgFor(busCurrent, false)
  const requiredBore = 2 * motorGauge.od + 2 * 1.7
  harness.push({
    motor: actuator ? `${actuator.model} × ${effective.dof}` : `执行器 × ${effective.dof}`,
    qty: effective.dof,
    current_A: perMotorCurrent,
    awg: motorGauge.awg,
    connector: 'XT30(2+2)',
    requiredBore_mm: requiredBore,
    status: motorGauge.capped ? 'partial' : 'declared',
    note: motorGauge.capped
      ? `额定 ${perMotorCurrent.toFixed(1)} A 本应更粗，但 XT30(2+2) 外壳限制最大 14AWG；高占空比需复核温升。`
      : `按硅胶线参考电流 ×70% ≥ 额定电流；2 电源 + 2 信号。`,
  })
  harness.push({
    motor: '公共母线', qty: 1, current_A: busCurrent, awg: busGauge.awg, connector: 'XT60 / XT90',
    requiredBore_mm: 0, status: 'declared',
    note: `下游 ${effective.dof} 台额定电流之和 ${busCurrent.toFixed(1)} A；保险丝建议 ${(busCurrent * 1.5).toFixed(0)} A。`,
  })
  if (needs.hollow) {
    warnings.push(`中空走线：按 14AWG 外径计算，2 电源 + 2 信号约需 ≥${requiredBore.toFixed(1)} mm 孔径；所选执行器未声明中空孔径，需按 datasheet 复核。`)
  }
  if (motorGauge.capped) {
    warnings.push(`单电机电流 ${perMotorCurrent.toFixed(1)} A 超过 XT30(2+2) 的 14AWG 上限，长时间高占空比会发热。`)
  }

  // 其他小件
  lines.push({
    role: 'CAN 终端电阻 120Ω', group: '线束', part: null, qty: 2, unitPrice: null,
    note: 'CAN 总线两端各 1 个；总线长度 >1 m 或高波特率时必须装。',
    status: 'declared', alternates: [], manual: { model: '120Ω 1/4W 电阻', vendor: '通用', price: null },
  })

  // 预算
  const known = lines.reduce((sum, l) => sum + (l.unitPrice !== null ? l.unitPrice * l.qty : 0), 0)
  const unknown = lines.filter(l => l.unitPrice === null).length
  if (needs.budget !== null && known > needs.budget) {
    warnings.push(`已知小计 ¥${known.toFixed(0)} 超过预算 ¥${needs.budget}；未标价条目还未计入。`)
  }
  if (unknown) warnings.push(`${unknown} 条未公开价格，导出 BOM 时按询价处理。`)

  const tau = actuator ? (n(specs(actuator).tau_peak_Nm) ?? effective.effort_max_Nm) : effective.effort_max_Nm
  const mjcf = buildMjcf({
    type: effective.type,
    dof: effective.dof,
    mass_kg: effective.mass_kg,
    tau_peak_Nm: tau,
    modelName: `robowiki-${effective.type}`,
  })

  if (!reference) {
    warnings.push('未选可信参考机型，质量/DOF/扭矩使用手动值或类型默认值；MJCF 只是骨架。')
  }
  if (effective.type === 'humanoid' && (effective.dof < 19 || effective.dof > 23)) {
    warnings.push(`MJCF 使用 19–23 DOF 人形模板；参考机型为 ${effective.dof} DOF，需按实际关节表增删。`)
  }

  return {
    reference,
    effective,
    lines,
    harness,
    warnings: [...new Set(warnings)],
    mjcf,
    totals: { known_cny: known, unknown_lines: unknown, currency: 'CNY' },
  }
}

export function buildBomPayload(input: SelectorInput, result: SelectionResult, overrides: Record<string, { partId?: string; qty?: number }> = {}) {
  const lines = result.lines.map(line => {
    const ov = overrides[line.role] ?? {}
    const part = ov.partId
      ? line.alternates.find(p => p.id === ov.partId) ?? line.part
      : line.part
    const qty = ov.qty ?? line.qty
    const unit = part ? priceOf(part) : line.unitPrice
    return {
      role: line.role,
      group: line.group,
      part_id: part?.id ?? null,
      model: part?.model ?? line.manual?.model ?? null,
      vendor: part?.vendor ?? line.manual?.vendor ?? null,
      qty,
      unit_price_cny: unit,
      subtotal_cny: unit !== null ? unit * qty : null,
      note: line.note,
      status: line.status,
      alternates: line.alternates.map(p => p.id),
    }
  })
  return {
    version: 1,
    generator: 'RoboWiki selector',
    created_at: new Date().toISOString(),
    config: {
      type: input.type,
      size: input.size,
      reference_model: result.reference?.model ?? null,
      reference_urdf: result.reference?.urdf_source ?? null,
      dof: result.effective.dof,
      mass_kg: result.effective.mass_kg,
      effort_min_Nm: result.effective.effort_min_Nm,
      effort_max_Nm: result.effective.effort_max_Nm,
      needs: input.needs,
    },
    lines,
    harness: result.harness,
    totals: {
      known_cny: lines.reduce((s, l) => s + (l.subtotal_cny ?? 0), 0),
      unknown_lines: lines.filter(l => l.unit_price_cny === null).length,
      currency: 'CNY',
    },
    warnings: result.warnings,
  }
}

export function toCsv(payload: ReturnType<typeof buildBomPayload>): string {
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const rows = [
    ['分组', '角色', '型号', '厂商', '数量', '单价(CNY)', '小计(CNY)', '状态', '备注'],
    ...payload.lines.map(l => [l.group, l.role, l.model, l.vendor, l.qty, l.unit_price_cny, l.subtotal_cny, STATUS_LABEL[l.status], l.note]),
    ...payload.harness.map(h => ['线束明细', h.motor, h.connector, '', h.qty, '', '', STATUS_LABEL[h.status], `${h.awg} AWG / ${h.current_A.toFixed(1)} A${h.requiredBore_mm ? ` / 孔径≥${h.requiredBore_mm.toFixed(1)} mm` : ''}；${h.note}`]),
  ]
  return rows.map(r => r.map(esc).join(',')).join('\n')
}
