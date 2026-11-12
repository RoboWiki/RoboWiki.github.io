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

export type Choice = { partId: string | null; qty?: number }
export type Choices = Record<string, Choice>

export type Verdict = 'ok' | 'warn' | 'bad' | 'info'

export type EvalItem = { label: string; value: string; verdict: Verdict; note?: string }

export type RoleOption = {
  part: CatalogPart
  price: number | null
  evals: EvalItem[]
  risk?: string
}

export type VirtualSpec = {
  summary: string
  fields: Array<{ label: string; value: string }>
}

export type RoleGroup = '执行器' | '电源' | '主控' | '感知' | '线束' | '其他'

export type RolePlan = {
  key: string
  label: string
  group: RoleGroup
  virtual: VirtualSpec
  qty: number
  options: RoleOption[]
  advice: string[]
  sortNote: string
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

export type Plan = {
  reference: SelectorModel | null
  effective: { type: RobotType; mass_kg: number; dof: number; effort_min_Nm: number; effort_max_Nm: number }
  roles: RolePlan[]
  harness: HarnessRow[]
  warnings: string[]
  mjcf: string
  totals: { known_cny: number; virtual_lines: number; currency: 'CNY' }
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
  if (typeof v === 'string') {
    const m = v.match(/-?\d+(?:\.\d+)?/)
    if (m) {
      const x = Number(m[0])
      return Number.isFinite(x) ? x : null
    }
  }
  return null
}

const specs = (p: CatalogPart) => (p.specs ?? {}) as Record<string, unknown>
const priceOf = (p: CatalogPart) => effectivePrice(p.price, p.offers)
const commText = (p: CatalogPart) => String(specs(p).comm ?? specs(p).iface ?? specs(p).protocol ?? '').toUpperCase()
const hasCan = (p: CatalogPart) => /CAN/.test(commText(p))
const hasCanFd = (p: CatalogPart) => specs(p).canfd === true || /CAN\s*FD|CANFD|FD\s*CAN/.test(commText(p))
const fmt = (v: number, d = 1) => v.toFixed(d).replace(/\.0$/, '')

export type ActuatorBus = 'canfd' | 'can' | 'rs485' | 'uart' | 'other'

export function actuatorBus(p: CatalogPart | null): ActuatorBus {
  if (!p) return 'other'
  const t = commText(p)
  if (hasCanFd(p)) return 'canfd'
  if (/CAN/.test(t)) return 'can'
  if (/485/.test(t)) return 'rs485'
  if (/UART|串口|TTL/.test(t)) return 'uart'
  return 'other'
}

const BUS_LABEL: Record<ActuatorBus, string> = {
  canfd: 'CANFD',
  can: 'CAN',
  rs485: 'RS-485',
  uart: 'TTL 串口',
  other: '未公布',
}

function rangeOf(v: unknown): [number, number] | null {
  if (typeof v === 'number' && Number.isFinite(v)) return [v, v]
  const nums = String(v ?? '').match(/\d+(?:\.\d+)?/g)?.map(Number)
  if (!nums?.length) return null
  if (nums.length === 1) return [nums[0], nums[0]]
  return [Math.min(nums[0], nums[1]), Math.max(nums[0], nums[1])]
}

function priceEval(p: CatalogPart): EvalItem {
  const price = priceOf(p)
  return { label: '价格', value: price !== null ? `¥${price.toLocaleString('zh-CN')}` : '询价', verdict: 'info' }
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

const byPriceKnownThenAsc = (a: CatalogPart, b: CatalogPart): number => {
  const pa = priceOf(a)
  const pb = priceOf(b)
  if (pa === null && pb !== null) return 1
  if (pa !== null && pb === null) return -1
  if (pa !== null && pb !== null && pa !== pb) return pa - pb
  return a.model.localeCompare(b.model, 'zh-CN')
}

/** 电池能量：优先用录入值，缺了就按 mAh × V / 1000 折算。 */
const energyWhOf = (p: CatalogPart): number | null => {
  const direct = n(specs(p).energy_wh)
  if (direct !== null) return direct
  const mah = n(specs(p).capacity_mah)
  const v = n(specs(p).voltage_V)
  return mah !== null && v !== null ? (mah * v) / 1000 : null
}

/** CPU 粗评分：算法/RL 场景优先看核心数与频率，x86 迷你主机额外加权。 */
function cpuInfoOf(p: CatalogPart) {
  const s = specs(p)
  const cpu = String(s.cpu ?? '')
  const coresMatch = cpu.match(/(\d+)\s*[×xX*]\s*(?:Zen|Cortex|core|Core)/) ?? cpu.match(/(\d+)[-\s]?core/i)
  const cores = coresMatch ? Number(coresMatch[1]) : n(s.cores)
  const ghzMatch = cpu.match(/(\d+(?:\.\d+)?)\s*GHz/i)
  const ghz = ghzMatch ? Number(ghzMatch[1]) : null
  const mini = String(p.subtype ?? '') === 'mini_pc' || /Ryzen|Intel|Core i|7840|x86/i.test(cpu)
  const score = (cores ?? 0) * (ghz ?? 2) + (mini ? 30 : 0)
  const label = [cores ? `${cores}C` : null, ghz ? `${fmt(ghz, 1)} GHz` : null].filter(Boolean).join(' / ') || cpu || '未公布'
  return { cores, ghz, mini, score, label }
}

function option(p: CatalogPart, evals: EvalItem[], risk?: string): RoleOption {
  return { part: p, price: priceOf(p), evals: [...evals, priceEval(p)], risk }
}

// ── 执行器 ────────────────────────────────────────────────────────────────

function actuatorRole(
  parts: CatalogPart[],
  type: RobotType,
  requirement: number | null,
  qty: number,
  key: string,
  label: string,
  extraAdvice: string[] = [],
): RolePlan {
  const subtypes = type === 'arm'
    ? ['harmonic', 'planetary', 'qdd', 'direct']
    : ['qdd', 'planetary', 'direct']
  const pool = parts.filter(p => {
    if (p.category === 'actuator') return subtypes.includes(String(p.subtype ?? '')) && (n(specs(p).tau_peak_Nm) ?? 0) > 0
    if (p.category === 'servo') return /串口|TTL|单总线/.test(String(specs(p).protocol ?? specs(p).iface ?? '')) && (n(specs(p).stall_torque_Nm) ?? 0) > 0
    return false
  })
  const tauOf = (p: CatalogPart) => n(specs(p).tau_peak_Nm) ?? n(specs(p).stall_torque_Nm) ?? 0
  const isServo = (p: CatalogPart) => p.category === 'servo'
  const meets = (p: CatalogPart) => requirement !== null && tauOf(p) >= requirement
  const gearOf = (p: CatalogPart) => n(specs(p).gear)
  const densityOf = (p: CatalogPart) => {
    const mass = n(specs(p).mass_kg)
    return mass !== null && mass > 0 ? tauOf(p) / mass : -1
  }
  const valueOf = (p: CatalogPart) => {
    const price = priceOf(p)
    return price !== null && price > 0 ? tauOf(p) / price : -1
  }
  const ranked = [...pool].sort((a, b) => {
    if (requirement !== null && meets(a) !== meets(b)) return meets(a) ? -1 : 1
    const pa = priceOf(a)
    const pb = priceOf(b)
    if (pa === null && pb !== null) return 1
    if (pa !== null && pb === null) return -1
    if (pa !== null && pb !== null && pa !== pb) return pa - pb
    const ga = gearOf(a) ?? 999
    const gb = gearOf(b) ?? 999
    if (ga !== gb) return ga - gb
    const da = densityOf(a)
    const db = densityOf(b)
    if (da !== db) return db - da
    const va = valueOf(a)
    const vb = valueOf(b)
    if (va !== vb) return vb - va
    return a.model.localeCompare(b.model, 'zh-CN')
  })
  const qualified = requirement === null ? ranked : ranked.filter(meets)
  const fallback = requirement === null
    ? ranked.slice(0, 3)
    : [...pool].sort((a, b) => Math.abs(tauOf(a) - requirement) - Math.abs(tauOf(b) - requirement)).slice(0, 3)
  const shownPool = qualified.length > 0 ? qualified : fallback
  const options = shownPool.map(p => {
    const tau = tauOf(p)
    const evals: EvalItem[] = []
    let risk: string | undefined
    if (requirement !== null) {
      const verdict: Verdict = tau >= requirement ? 'ok' : tau >= requirement * 0.7 ? 'warn' : 'bad'
      evals.push({
        label: isServo(p) ? '堵转扭矩' : '峰值扭矩',
        value: `${fmt(tau)} N·m`,
        verdict,
        note: verdict === 'ok' ? `满足 ≥${fmt(requirement)}` : verdict === 'warn' ? '接近下限，复核峰值/散热' : `低于需求 ${fmt(requirement)}`,
      })
      if (verdict !== 'ok') risk = '扭矩余量不足：峰值/堵转扭矩都是瞬时值，持续运行按额定扭矩与散热复核。'
    } else {
      evals.push({ label: isServo(p) ? '堵转扭矩' : '峰值扭矩', value: `${fmt(tau)} N·m`, verdict: 'info', note: '按关节表核对' })
    }
    if (isServo(p)) {
      risk = (risk ? risk + ' ' : '') + '总线舵机标的是堵转扭矩，持续输出要按占空比降额；TTL 串口需 USB-UART 桥接。'
    }
    const v = n(specs(p).voltage_V)
    evals.push({ label: '电压', value: v !== null ? `${fmt(v, 0)} V` : '未公布', verdict: 'info' })
    const bus = actuatorBus(p)
    evals.push({
      label: '总线',
      value: BUS_LABEL[bus],
      verdict: bus === 'canfd' || bus === 'can' ? 'ok' : bus === 'other' ? 'warn' : 'info',
      note: bus === 'rs485' ? '宇树系 RS-485' : bus === 'uart' ? '总线舵机串口' : bus === 'other' ? '需额外转换' : undefined,
    })
    const mass = n(specs(p).mass_kg)
    if (mass !== null) evals.push({ label: '质量', value: `${fmt(mass, 2)} kg`, verdict: 'info' })
    const gear = n(specs(p).gear)
    if (gear !== null && gear > 1) evals.push({ label: '减速比', value: `${fmt(gear, 1)}:1`, verdict: 'info', note: '注意背隙' })
    return option(p, evals, risk)
  })
  const fields: Array<{ label: string; value: string }> = []
  fields.push({ label: '构型平均需求', value: requirement !== null ? `≥${fmt(requirement)} N·m（min–max 中值）` : '按关节表' })
  fields.push({ label: '总线', value: 'CAN/CANFD 优先，RS-485/串口按型号' }, { label: '电压', value: '随型号（12/24/48V 常见）' })
  const advice = [
    '按参考机型 min–max 中值筛选；达标后先按价格，再看减速比、扭矩密度与扭矩/价格。',
    '峰值/堵转扭矩是瞬时值，持续运行按额定扭矩与散热复核；减速模组注意背隙与效率。',
    '执行器总线决定下位机/桥接与电池电压档，先定执行器再往下选。',
    ...extraAdvice,
  ]
  if (requirement !== null && !options.some(o => o.evals.some(e => (e.label === '峰值扭矩' || e.label === '堵转扭矩') && e.verdict === 'ok'))) {
    advice.unshift(`站内没有覆盖 ${fmt(requirement)} N·m 的型号，以上为最接近的参考，需换参考机型或定制。`)
  }
  return {
    key,
    label,
    group: '执行器',
    virtual: {
      summary: requirement !== null
        ? `构型平均需求 ≥${fmt(requirement)} N·m · CAN/CANFD 优先 · ×${qty}`
        : `扭矩按关节表 · CAN/CANFD 优先 · ×${qty}`,
      fields,
    },
    qty,
    options,
    advice,
    sortNote: requirement !== null
      ? '达标型号按价格升序；同价优先减速比小、扭矩密度高、扭矩/价格高。默认显示前 4 个，可继续展开。'
      : '按价格优先，再看减速比、扭矩密度与扭矩/价格；默认显示前 4 个。',
  }
}

// ── 电池 / 外接供电 ───────────────────────────────────────────────────────

function batteryRole(parts: CatalogPart[], voltageClass: 12 | 24 | 48, estimatedWh: number, referenceVendor: string, actuatorChosen: boolean): RolePlan {
  const batteries = parts.filter(p => p.category === 'battery')
  const proprietary = (p: CatalogPart) =>
    /DJI|大疆|Unitree|宇树/i.test(p.vendor)
    || /^BT\d/i.test(p.model)
    || /专用/.test(String(specs(p).iface ?? ''))
  const usable = batteries.filter(p => !proprietary(p) || (referenceVendor && p.vendor === referenceVendor))
  const packs6s = usable.filter(p => {
    const v = n(specs(p).voltage_V) ?? 0
    return v >= 18 && v <= 30
  })
  const classLabel = voltageClass === 48 ? '48V（12S）' : voltageClass === 24 ? '24V（6S）' : '12V（3S）'
  const fields = [
    { label: '电压', value: `${classLabel} 级` },
    { label: '能量', value: `估算 ≥${fmt(estimatedWh, 0)} Wh（约 1h）` },
  ]
  const advice = [
    '能量按质量 ×8 Wh/kg 粗估，续航必须按实测功耗复核；低温/大倍率会缩短续航。',
    '电池未填能量时，按 mAh × V / 1000 折算后再参与筛选。',
  ]
  let options: RoleOption[]
  if (voltageClass === 48) {
    options = [...packs6s].sort((a, b) => (energyWhOf(b) ?? 0) - (energyWhOf(a) ?? 0))
      .map(p => {
        const wh = energyWhOf(p)
        return option(p, [
          { label: '电压', value: `${fmt(n(specs(p).voltage_V) ?? 0)} V`, verdict: 'bad', note: '需 2 块同批次串联成 12S' },
          { label: '能量', value: wh !== null ? `${fmt(wh, 0)} Wh` : '未公布', verdict: 'info', note: '单块值，串联后容量不变' },
          { label: '接口', value: proprietary(p) ? '专用' : '通用', verdict: proprietary(p) ? 'warn' : 'info' },
        ], '站内无 12S 整包。2×6S 串联必须同批次同容量电芯，BMS 按 12S 选；不能直接串两块带板电池。')
      })
    advice.unshift('48V 级站内暂无 12S 整包：以下为 6S 串联参考，风险见每条标注；也可外购 12S 整包。')
  } else if (voltageClass === 12) {
    options = [...packs6s].sort((a, b) => (energyWhOf(b) ?? 0) - (energyWhOf(a) ?? 0))
      .map(p => {
        const wh = energyWhOf(p)
        return option(p, [
          { label: '电压', value: `${fmt(n(specs(p).voltage_V) ?? 0)} V`, verdict: 'bad', note: '超压，需降压到 12V' },
          { label: '能量', value: wh !== null ? `${fmt(wh, 0)} Wh` : '未公布', verdict: 'info' },
        ], '站内电池均为 6S 22V 级：12V 舵机/执行器需 3S 电池（外购）或经降压模块供电，见「供电分线 / 降压」。')
      })
    advice.unshift('12V 级站内暂无 3S 整包：可外购 3S 电池，或用 6S 电池 + 降压模块（见供电分线 / 降压）。')
  } else {
    const ranked = [...packs6s].sort((a, b) => {
      const ea = energyWhOf(a) ?? 0
      const eb = energyWhOf(b) ?? 0
      const aOk = ea >= estimatedWh
      const bOk = eb >= estimatedWh
      if (aOk !== bOk) return aOk ? -1 : 1
      if (aOk && bOk) return byPriceKnownThenAsc(a, b)
      if (Math.abs(ea - estimatedWh) !== Math.abs(eb - estimatedWh)) return Math.abs(ea - estimatedWh) - Math.abs(eb - estimatedWh)
      return byPriceKnownThenAsc(a, b)
    })
    options = ranked.map(p => {
      const wh = energyWhOf(p)
      const v = n(specs(p).voltage_V) ?? 0
      return option(p, [
        { label: '电压', value: `${fmt(v)} V`, verdict: 'ok', note: '6S 级，匹配 24V 执行器' },
        { label: '能量', value: wh !== null ? `${fmt(wh, 0)} Wh` : '未公布', verdict: wh !== null && wh >= estimatedWh ? 'ok' : 'warn', note: wh !== null && wh >= estimatedWh ? '覆盖估算' : '低于估算或未知' },
        { label: '接口', value: proprietary(p) ? '专用' : '通用', verdict: proprietary(p) ? 'warn' : 'ok', note: proprietary(p) ? '仅适配同厂机型' : undefined },
      ], proprietary(p) ? '专用电池接口/协议不通用，只建议用于同厂参考机型。' : undefined)
    })
    if (!actuatorChosen) advice.unshift('未选执行器，按 24V（6S）档展示；选 48V/12V 执行器后自动切换电压档。')
  }
  return {
    key: 'battery',
    label: '电池',
    group: '电源',
    virtual: { summary: `${classLabel} 级 · 估算 ≥${fmt(estimatedWh, 0)} Wh`, fields },
    qty: 1,
    options,
    advice,
    sortNote: voltageClass === 24
      ? '覆盖估算能量的按价格升序；不足的按接近程度排后。默认显示前 4 个，可继续展开。'
      : '按单块能量降序展示参考（电压不匹配，需串联/降压/外购）。默认显示前 4 个。',
  }
}

function psuRole(parts: CatalogPart[]): RolePlan {
  const pool = parts.filter(p => p.category === 'power' && /LM2596|UBEC/i.test(p.model))
  return {
    key: 'psu',
    label: '外接供电',
    group: '电源',
    virtual: {
      summary: '外接稳压电源 · 母线电压随执行器 · 电流按母线总和',
      fields: [{ label: '电压', value: '随执行器（12/24/48V）' }, { label: '电流', value: '≥ 母线电流总和' }],
    },
    qty: 1,
    options: pool.map(p => {
      const vout = String(specs(p).voltage_out ?? '?').replace(/\s*V\s*$/i, '')
      const iout = String(specs(p).current_out ?? '?').replace(/\s*A\s*$/i, '')
      return option(p, [
        { label: '输出', value: `${vout} V / ${iout} A`, verdict: 'warn', note: '仅小电流逻辑供电' },
      ], '站内无大功率稳压电源条目；LM2596/UBEC 只适合逻辑供电，电机母线需外购电源并加急停。')
    }),
    advice: ['外接供电省去电池与 BMS，但必须核对母线电压、电流余量，并保留急停开关。'],
    sortNote: '站内现有小功率模块仅作参考，主电源需外购。',
  }
}

// ── 下位机 / 总线桥接 ─────────────────────────────────────────────────────

function lowRole(parts: CatalogPart[], actuator: CatalogPart | null, hasHigh: boolean, dof: number): RolePlan {
  const bus = actuatorBus(actuator)
  const fd = bus === 'canfd'
  const needChannels = Math.max(1, Math.min(8, Math.ceil(dof / 6)))
  const canCount = (p: CatalogPart) => n(specs(p).can) ?? (/CAN/.test(commText(p)) ? 1 : 0)
  const boards = parts.filter(p => {
    if (p.category !== 'controller_low') return false
    if (bus === 'rs485') return /485/.test(commText(p)) || canCount(p) >= 1
    if (bus === 'uart') return /UART|串口/.test(commText(p)) || canCount(p) >= 1
    return canCount(p) >= 1
  })
  const bridges = (bus === 'can' || bus === 'canfd')
    ? parts.filter(p => p.category === 'module' && String(p.subtype ?? '') === 'can')
    : []
  const boardRank = [...boards].sort((a, b) => {
    if (fd && hasCanFd(a) !== hasCanFd(b)) return hasCanFd(a) ? -1 : 1
    if (canCount(a) !== canCount(b)) return canCount(b) - canCount(a)
    return byPriceKnownThenAsc(a, b)
  })
  const bridgeRank = [...bridges].sort((a, b) => {
    if (fd && hasCanFd(a) !== hasCanFd(b)) return hasCanFd(a) ? -1 : 1
    const ca = canCount(a)
    const cb = canCount(b)
    const oka = ca >= needChannels
    const okb = cb >= needChannels
    if (oka !== okb) return oka ? -1 : 1
    if (Math.abs(ca - needChannels) !== Math.abs(cb - needChannels)) return Math.abs(ca - needChannels) - Math.abs(cb - needChannels)
    return byPriceKnownThenAsc(a, b)
  })
  const boardOptions = boardRank.map(p => {
    const evals: EvalItem[] = [
      { label: '类型', value: '实时 MCU', verdict: 'ok', note: '独立电流环/实时控制' },
      { label: 'CAN 通道', value: `${canCount(p)}`, verdict: 'info', note: '单总线可挂多电机' },
      {
        label: 'CANFD',
        value: hasCanFd(p) ? '支持' : '仅 CAN',
        verdict: fd ? (hasCanFd(p) ? 'ok' : 'warn') : 'ok',
        note: fd && !hasCanFd(p) ? '执行器为 CANFD，此板仅 CAN' : undefined,
      },
    ]
    if (bus === 'rs485') evals.push({ label: 'RS-485', value: /485/.test(commText(p)) ? '有' : '无', verdict: /485/.test(commText(p)) ? 'ok' : 'warn', note: /485/.test(commText(p)) ? undefined : '需外接 USB-485' })
    return option(p, evals)
  })
  const bridgeOptions = bridgeRank.map(p => {
    const evals: EvalItem[] = [
      { label: '类型', value: '总线桥接', verdict: 'warn', note: '无 MCU，需上位机直驱' },
      { label: 'USB 转接通道', value: `${canCount(p)} 路`, verdict: canCount(p) >= needChannels ? 'ok' : 'warn', note: `本构型建议约 ${needChannels} 路（每路 4–6 台，最多 8 台）` },
      { label: 'CANFD', value: hasCanFd(p) ? '支持' : '仅 CAN', verdict: fd ? (hasCanFd(p) ? 'ok' : 'warn') : 'ok' },
    ]
    const vin = rangeOf(specs(p).voltage_in_V ?? specs(p).voltage_in ?? specs(p).voltage_V)
    if (vin) evals.push({ label: '供电', value: vin[0] === vin[1] ? `${fmt(vin[0], 0)} V` : `${fmt(vin[0], 0)}–${fmt(vin[1], 0)} V`, verdict: 'info', note: '功率板需外接' })
    return option(p, evals, hasHigh
      ? '上位机直驱总线：Linux 非实时，建议 PREEMPT_RT 内核，或保留下位机做电流环。'
      : '当前方案没有上位机：桥接器没有主机，需改选带 MCU 的下位机或启用上位机。')
  })
  const options = [...boardOptions, ...bridgeOptions]
  const advice = [
    '单条 CAN 总线可按 ID 挂多个电机，通道数不够不等于带不满 DOF；波特率、供电与分线要核对。',
    '无下位机方案：上位机 + USB-CAN(FD) 桥接直驱；无上位机方案：必须选带 MCU 的下位机。',
  ]
  if (bus === 'rs485') advice.push('宇树系执行器为 RS-485：站内暂无 USB-485 转接器，需外购（常见 CH340/CP2102/FT232 方案）；带 RS-485 的下位机可直接接。')
  if (bus === 'uart') advice.push('总线舵机为 TTL 半双工串口：站内暂无 USB-UART 调试板，需外购（Feetech 官方调试板或 CH340 方案），注意半双工方向控制。')
  if (fd) advice.push('所选执行器支持 CANFD，下位机/桥接优先 FDCAN。')
  advice.push(needChannels <= 2
    ? 'USB 转接按每条总线 4–6 台、最多 8 台：本构型约 1–2 路，可优先 2×1 路或 1×2 路。'
    : `USB 转接按每条总线 4–6 台、最多 8 台：本构型约 ${needChannels} 路，优先多通道适配器，单路别超 8 台。`)
  return {
    key: 'low',
    label: '下位机 / 总线桥接',
    group: '主控',
    virtual: {
      summary: `实时控制或总线桥接 · ${BUS_LABEL[bus]}（随执行器）`,
      fields: [
        { label: '总线', value: BUS_LABEL[bus] },
        { label: '形态', value: '带 MCU 下位机，或上位机 + USB 桥接' },
      ],
    },
    qty: 1,
    options,
    advice,
    sortNote: `实时 MCU 板在前；USB 桥接按所需通道数接近、CANFD、价格排序。默认显示前 4 个，可继续展开。`,
  }
}

// ── 上位机 ────────────────────────────────────────────────────────────────

function highRole(parts: CatalogPart[], needs: Needs): RolePlan {
  const heavy = needs.controls.includes('autonomy') && (needs.depth || needs.lidar)
  const rl = needs.controls.includes('rl')
  const cpuFirst = rl
  const tier: 'high' | 'mid' | 'entry' = heavy ? 'high' : rl ? 'mid' : 'entry'
  const tierLabel = cpuFirst ? 'RL / 规划（CPU 与内存优先）' : tier === 'high' ? '高算力（80 TOPS 级以上参考）' : tier === 'mid' ? '进阶（20–40 TOPS 参考）' : '入门（<20 TOPS，轻量视觉/逻辑）'
  const tierMin = tier === 'high' ? 80 : tier === 'mid' ? 20 : 0
  const npuOf = (p: CatalogPart) => n(specs(p).npu_tops)
  const tierOf = (p: CatalogPart): 'high' | 'mid' | 'entry' => {
    const npu = npuOf(p) ?? 0
    return npu >= 80 ? 'high' : npu >= 20 ? 'mid' : 'entry'
  }
  const dist = (t: 'high' | 'mid' | 'entry') => Math.abs(['entry', 'mid', 'high'].indexOf(t) - ['entry', 'mid', 'high'].indexOf(tier))
  // 载板本身不算力，算力由所插模组决定，不能当整机候选；计算模组（如 Orin NX/Nano）有 npu，保留
  const isCarrier = (p: CatalogPart) => String(p.subtype ?? '') === 'module' && npuOf(p) === null
  const pool = parts.filter(p => p.category === 'controller_high' && !isCarrier(p))
  const carriers = parts.filter(p => p.category === 'controller_high' && isCarrier(p))
  const ranked = [...pool].sort((a, b) => {
    if (cpuFirst) {
      const sa = cpuInfoOf(a).score
      const sb = cpuInfoOf(b).score
      if (sa !== sb) return sb - sa
    } else {
      const da = dist(tierOf(a))
      const db = dist(tierOf(b))
      if (da !== db) return da - db
    }
    const na = npuOf(a)
    const nb = npuOf(b)
    if (na !== nb) return (nb ?? -1) - (na ?? -1)
    return byPriceKnownThenAsc(a, b)
  })
  const options = ranked.map(p => {
    const npu = npuOf(p)
    const ram = n(specs(p).ram_gb)
    const cpu = cpuInfoOf(p)
    const evals: EvalItem[] = []
    evals.push({ label: 'CPU', value: cpu.label, verdict: 'info', note: cpuFirst ? 'RL/规划优先看 CPU 与内存' : undefined })
    if (npu === null) {
      evals.push({ label: '算力', value: '无 NPU（CPU）', verdict: cpuFirst ? 'info' : 'warn', note: cpuFirst ? 'RL/规划可接受；视觉推理另配加速' : '适合逻辑/轻量视觉，重感知需外加加速' })
    } else if (npu < 10) {
      evals.push({ label: '算力', value: `${fmt(npu, 0)} TOPS`, verdict: 'info', note: cpuFirst ? 'TOPS 不影响 RL 主循环；视觉模型另看' : '算力偏低：适合巡线/轻量识别；激光/深度感知建议 40 TOPS 以上' })
    } else if (!cpuFirst && tierMin > 0 && npu < tierMin) {
      evals.push({ label: '算力', value: `${fmt(npu, 0)} TOPS`, verdict: 'warn', note: `低于「${tierLabel}」参考档，重感知可能不够` })
    } else {
      evals.push({ label: '算力', value: `${fmt(npu, 0)} TOPS`, verdict: 'ok' })
    }
    if (ram !== null) evals.push({ label: '内存', value: `${fmt(ram, 0)} GB`, verdict: 'info' })
    const can = n(specs(p).can)
    if (can !== null) evals.push({ label: 'CAN', value: `${can} 路`, verdict: can > 0 ? 'info' : 'warn', note: can > 0 ? (/RK3588/.test(String(specs(p).iface ?? '')) ? '集成下位机/分线，可少配独立下位机' : undefined) : '无原生 CAN，需 USB-CAN(FD) 桥接' })
    return option(p, evals)
  })
  const advice = [
    'RL、规划与传统算法主要吃 CPU 单核/多核与内存；TOPS 只影响神经网络推理，不要只按 TOPS 选。',
    '7840H 这类 x86 迷你主机 CPU 强，适合 RL/规划/仿真；无原生 CAN，功耗、散热与实时性要另算。',
    '训练在 PC/服务器，机上只跑推理；TOPS 为厂商标称，实际吞吐看模型与量化。',
    '集成盒子（如 RoboBox-7C）自带下位机与电机分线，可少配独立下位机/分线板；供电按「供电分线 / 降压」核对。',
  ]
  if (carriers.length > 0) {
    advice.push(`载板本身不含算力（如 ${carriers.map(p => p.model).join('、')}）：选 NVIDIA Orin 计算模组时需另配载板，算力按所插模组核对。`)
  }
  return {
    key: 'high',
    label: '上位机 / 感知计算',
    group: '主控',
    virtual: {
      summary: tierLabel,
      fields: [{ label: cpuFirst ? 'CPU' : '算力档', value: cpuFirst ? 'CPU 与内存优先' : tierLabel }, { label: '接口', value: '网口/USB 接下位机与传感器' }, { label: '供电', value: '见「供电分线 / 降压」' }],
    },
    qty: 1,
    options,
    advice,
    sortNote: cpuFirst
      ? 'RL/规划按 CPU 评分优先，再看 NPU 与价格；默认显示前 4 个，可继续展开。'
      : '同档按算力降序（无 NPU 在后）、同算力价格升序；裸载板不进候选。默认显示前 4 个。',
  }
}

// ── 供电分线 / 降压 ───────────────────────────────────────────────────────

function powerDistRole(parts: CatalogPart[], busVoltage: number, hasHigh: boolean, bus: ActuatorBus): RolePlan {
  const pool = parts.filter(p =>
    (p.category === 'open_hw' && String(p.subtype ?? '') === 'power')
    || (p.category === 'power' && String(p.subtype ?? '') === 'dcdc'))
  const covers = (p: CatalogPart) => {
    const r = rangeOf(specs(p).voltage_in)
    return r !== null && r[0] <= busVoltage && r[1] >= busVoltage
  }
  const isPdb = (p: CatalogPart) => /分电|分线/.test(p.model)
  const ranked = [...pool].sort((a, b) => {
    if (covers(a) !== covers(b)) return covers(a) ? -1 : 1
    if (bus === 'rs485') {
      const ra = /485/.test(commText(a)) ? 0 : 1
      const rb = /485/.test(commText(b)) ? 0 : 1
      if (ra !== rb) return ra - rb
    }
    const ca = n(specs(a).current_out) ?? 0
    const cb = n(specs(b).current_out) ?? 0
    if (ca !== cb) return cb - ca
    return byPriceKnownThenAsc(a, b)
  })
  const options = uniqueTop(ranked, 4).map(p => {
    const r = rangeOf(specs(p).voltage_in)
    const ok = covers(p)
    const evals: EvalItem[] = [
      {
        label: '输入',
        value: r ? (r[0] === r[1] ? `${fmt(r[0], 0)} V` : `${fmt(r[0], 0)}–${fmt(r[1], 0)} V`) : String(specs(p).voltage_in ?? '未公布'),
        verdict: ok ? 'ok' : 'bad',
        note: ok ? `覆盖 ${fmt(busVoltage, 0)}V 母线` : `不覆盖 ${fmt(busVoltage, 0)}V 母线`,
      },
      { label: '输出', value: String(specs(p).voltage_out ?? '未公布'), verdict: 'info' },
      { label: '类型', value: isPdb(p) ? '分线板' : '降压模块', verdict: 'info', note: isPdb(p) ? '只分配不降压' : undefined },
    ]
    const cur = n(specs(p).current_out)
    if (cur !== null) evals.push({ label: '电流', value: `${fmt(cur, 0)} A`, verdict: 'info', note: '按负载 ×1.5 留余量' })
    if (bus === 'rs485' && /485/.test(commText(p))) evals.push({ label: 'RS-485', value: '带接口', verdict: 'ok', note: '适合宇树总线' })
    return option(p, evals, !ok
      ? `输入范围不覆盖 ${fmt(busVoltage, 0)}V 母线，直接接入会超压/欠压，需换模块或调整母线。`
      : isPdb(p) ? '分线板只分配母线电压，不降压；上位机/逻辑供电仍需降压模块。' : undefined)
  })
  return {
    key: 'power_dist',
    label: '供电分线 / 降压',
    group: '电源',
    virtual: {
      summary: `${fmt(busVoltage, 0)}V 母线 → ${hasHigh ? '上位机（19/12V）+ ' : ''}逻辑（5V）· 电流留余量`,
      fields: [
        { label: '输入', value: `${fmt(busVoltage, 0)}V 母线` },
        { label: '输出', value: hasHigh ? '算力 19/12V + 逻辑 5V' : '逻辑 5V/3.3V' },
        { label: '电流', value: '按负载 ×1.5' },
      ],
    },
    qty: 1,
    options,
    advice: [
      '48V 母线不能直接给 24V/19V/5V 设备供电；LM2596 上限 40V，48V 母线会超压。',
      '分线板只分配不降压；降压模块电流按负载 ×1.5 留余量，注意散热与 TVS 防反接。',
      '算力设备常见 19V/12V（Jetson/NUC），树莓派 5V/5A USB-C；按实际设备核对，芯片级 DC-DC 需自行画板。',
    ],
    sortNote: `输入范围覆盖 ${fmt(busVoltage, 0)}V 母线的优先${bus === 'rs485' ? '，带 RS-485 接口的优先' : ''}，再按输出电流降序。`,
  }
}

// ── IMU ───────────────────────────────────────────────────────────────────

function imuRole(parts: CatalogPart[]): RolePlan {
  const pool = parts.filter(p => p.category === 'imu')
  const kind = (p: CatalogPart): number => {
    const t = commText(p)
    if (/CAN/.test(t)) return 0
    if (/UART|USB/.test(t)) return 1
    return 2
  }
  const ranked = [...pool].sort((a, b) => {
    if (kind(a) !== kind(b)) return kind(a) - kind(b)
    return byPriceKnownThenAsc(a, b)
  })
  const options = uniqueTop(ranked, 3).map(p => {
    const t = commText(p)
    const isChip = kind(p) === 2
    const gyro = specs(p).gyro_range_dps
    const odr = n(specs(p).odr_hz)
    const evals: EvalItem[] = [
      {
        label: '输出',
        value: String(specs(p).iface ?? '未公布'),
        verdict: /CAN/.test(t) ? 'ok' : isChip ? 'warn' : 'info',
        note: isChip ? '芯片级，需载板与标定' : /CAN/.test(t) ? '可与下位机同总线' : undefined,
      },
    ]
    if (gyro !== undefined && gyro !== null && gyro !== '') evals.push({ label: '陀螺量程', value: `${gyro} °/s`, verdict: 'info' })
    if (odr !== null) evals.push({ label: 'ODR', value: `${fmt(odr, 0)} Hz`, verdict: 'info' })
    return option(p, evals, isChip ? '芯片级 IMU 需自行画载板、做温度与零偏标定；整机验证优先带外壳模块。' : undefined)
  })
  return {
    key: 'imu',
    label: 'IMU',
    group: '感知',
    virtual: {
      summary: '≥1 个 · ±2000°/s 级 · 总线随下位机',
      fields: [{ label: '数量', value: '≥1（躯干）' }, { label: '输出', value: 'CAN 优先，UART/USB 次之' }],
    },
    qty: 1,
    options,
    advice: ['腿部机器人至少 1 个 IMU；CAN 输出方便与下位机同总线。安装位置远离电机磁干扰。'],
    sortNote: 'CAN 模块优先，其次 UART/USB 模块，芯片级最后；同类价格升序。',
  }
}

// ── 深度相机 ──────────────────────────────────────────────────────────────

function depthRole(parts: CatalogPart[]): RolePlan {
  const pool = parts.filter(p => p.category === 'camera' && specs(p).depth_range_m != null && specs(p).depth_range_m !== '')
  const ranked = [...pool].sort(byPriceKnownThenAsc)
  const options = uniqueTop(ranked, 3).map(p => {
    const iface = String(specs(p).iface ?? '')
    const evals: EvalItem[] = [
      { label: '量程', value: String(specs(p).depth_range_m), verdict: 'info', note: '按使用距离核对' },
      { label: '接口', value: iface || '未公布', verdict: /GMSL|FAKRA/i.test(iface) ? 'warn' : 'info', note: /GMSL|FAKRA/i.test(iface) ? '需解串器，非普通 USB' : undefined },
    ]
    const fps = n(specs(p).fps)
    if (fps !== null) evals.push({ label: '帧率', value: `${fmt(fps, 0)} fps`, verdict: 'info' })
    return option(p, evals)
  })
  return {
    key: 'depth',
    label: '深度相机',
    group: '感知',
    virtual: {
      summary: '深度相机 · 室内 0.2–3 m 常用',
      fields: [{ label: '量程', value: '按场景（室内 0.2–3 m）' }, { label: '接口', value: 'USB 优先' }],
    },
    qty: 1,
    options,
    advice: ['量程与基线按使用距离核对；强光、玻璃、白墙场景深度会退化，需实测。'],
    sortNote: '价格升序，量程/接口逐条标注。',
  }
}

// ── 激光雷达 ──────────────────────────────────────────────────────────────

function lidarRole(parts: CatalogPart[], prefer3D: boolean): RolePlan {
  const pool = parts.filter(p => p.category === 'lidar')
  const is3D = (p: CatalogPart) => {
    const ch = n(specs(p).channel)
    if (ch !== null && ch > 1) return true
    const fov = String(specs(p).fov ?? '')
    return /\d+\s*°?\s*[×x]\s*\d+/.test(fov) && !/单线/.test(fov)
  }
  const ranked = [...pool].sort((a, b) => {
    if (prefer3D && is3D(a) !== is3D(b)) return is3D(a) ? -1 : 1
    return byPriceKnownThenAsc(a, b)
  })
  const options = uniqueTop(ranked, 3).map(p => {
    const three = is3D(p)
    const range = n(specs(p).range_m)
    const iface = String(specs(p).iface ?? '')
    const evals: EvalItem[] = [
      { label: '类型', value: three ? '3D' : '2D 单线', verdict: prefer3D ? (three ? 'ok' : 'warn') : 'info', note: prefer3D && !three ? '建图/越野建议 3D' : undefined },
      { label: '量程', value: range !== null ? `${fmt(range, 0)} m` : '未公布', verdict: 'info' },
      { label: '接口', value: iface || '未公布', verdict: 'info', note: /以太网|ENET/i.test(iface) ? '需上位机网口' : undefined },
    ]
    return option(p, evals)
  })
  return {
    key: 'lidar',
    label: '激光雷达',
    group: '感知',
    virtual: {
      summary: prefer3D ? '3D 360° 参考（导航/建图）' : '2D/3D 按场景',
      fields: [{ label: '类型', value: prefer3D ? '3D 优先' : '按场景' }, { label: '量程', value: '按场地' }],
    },
    qty: 1,
    options,
    advice: ['2D 只能平面避障；建图/越野选 3D。以太网雷达需上位机网口与独立供电，注意时间同步。'],
    sortNote: prefer3D ? '3D 优先，其余价格升序。' : '价格升序，类型逐条标注。',
  }
}

// ── 普通相机 ──────────────────────────────────────────────────────────────

function cameraRole(parts: CatalogPart[]): RolePlan {
  const pool = parts.filter(p =>
    p.category === 'camera'
    && (specs(p).depth_range_m == null || specs(p).depth_range_m === '')
    && !/^MVL-/i.test(p.model))
  const ranked = [...pool].sort(byPriceKnownThenAsc)
  const options = uniqueTop(ranked, 3).map(p => {
    const evals: EvalItem[] = [
      { label: '分辨率', value: String(specs(p).resolution ?? '未公布'), verdict: 'info' },
      { label: '接口', value: String(specs(p).iface ?? '未公布'), verdict: 'info' },
    ]
    const fps = n(specs(p).fps)
    if (fps !== null) evals.push({ label: '帧率', value: `${fmt(fps, 0)} fps`, verdict: 'info' })
    return option(p, evals)
  })
  return {
    key: 'camera',
    label: '相机',
    group: '感知',
    virtual: {
      summary: 'RGB/工业相机 · USB 优先',
      fields: [{ label: '接口', value: 'USB 优先' }, { label: '分辨率', value: '按视觉任务' }],
    },
    qty: 1,
    options,
    advice: ['工业相机需另配镜头与光源；USB 带宽按分辨率×帧率核对。需要深度时改选深度相机。'],
    sortNote: '价格升序；已排除镜头类条目。',
  }
}

// ── 遥控器 ────────────────────────────────────────────────────────────────

function remoteRole(parts: CatalogPart[]): RolePlan {
  const pool = parts.filter(p => p.category === 'remote_controller')
  const ranked = [...pool].sort((a, b) => {
    const ca = n(specs(a).channels) ?? 0
    const cb = n(specs(b).channels) ?? 0
    if (ca !== cb) return cb - ca
    return byPriceKnownThenAsc(a, b)
  })
  const options = uniqueTop(ranked, 3).map(p => {
    const ch = n(specs(p).channels)
    const proto = String(specs(p).protocol ?? '')
    const evals: EvalItem[] = [
      { label: '通道', value: ch !== null ? `${ch}` : '未公布', verdict: 'info' },
      { label: '协议', value: proto || '未公布', verdict: /D-?Bus/i.test(proto) ? 'warn' : 'info', note: /D-?Bus/i.test(proto) ? 'D-Bus 为 DJI 专用' : undefined },
    ]
    const range = n(specs(p).control_range_m)
    if (range !== null) evals.push({ label: '距离', value: `${fmt(range, 0)} m`, verdict: 'info' })
    return option(p, evals)
  })
  return {
    key: 'remote',
    label: '遥控器',
    group: '感知',
    virtual: {
      summary: '遥操作/急停接管 · 协议随下位机',
      fields: [{ label: '协议', value: 'SBUS/CRSF/D-Bus 按接收机' }, { label: '通道', value: '≥6 常用' }],
    },
    qty: 1,
    options,
    advice: ['自主方案也建议留一个急停/接管通道；D-Bus 与 SBUS 不通用，接收机要配对。'],
    sortNote: '通道数降序、价格升序；参数未公布的排在后面。',
  }
}

// ── 线束 / 小件 ───────────────────────────────────────────────────────────

function connectorRole(parts: CatalogPart[], qty: number): RolePlan {
  const primary = parts.find(p => p.id === 'amass-xt30-2p2')
    ?? parts.find(p => p.category === 'connector' && /XT30\(2\+2\)/.test(p.model))
  const alts = parts.filter(p => p.category === 'connector' && /XT30/.test(p.model) && p.id !== primary?.id)
  const list = primary ? [primary, ...alts] : alts
  const options = uniqueTop(list, 3).map(p => option(p, [
    { label: '针脚', value: /2\+2/.test(p.model) ? '2 电源 + 2 信号' : '见详情', verdict: /2\+2/.test(p.model) ? 'ok' : 'info' },
    { label: '电流', value: '功率针 20A MAX', verdict: 'info', note: '线束最大 14AWG' },
  ]))
  return {
    key: 'connector',
    label: '电机连接器 XT30(2+2)',
    group: '线束',
    virtual: {
      summary: `XT30(2+2) · 2 电源 + 2 信号（CANH/CANL）· ×${qty}`,
      fields: [{ label: '针脚', value: '2 电源 + 2 信号' }, { label: '限制', value: '功率针 20A MAX，线束 ≤14AWG' }],
    },
    qty,
    options,
    advice: ['多电机共母线时，母线线规按下游电流总和重新计算，不能沿用单电机线规。'],
    sortNote: 'XT30(2+2) 在前，其余 XT30 变体作参考。',
  }
}

function busConnectorRole(parts: CatalogPart[], busCurrent: number | null): RolePlan {
  const pool = parts.filter(p => p.category === 'connector' && /^XT(60|90)/.test(p.model))
  const ranked = [...pool].sort((a, b) => (n(specs(a).current_rated_A) ?? 0) - (n(specs(b).current_rated_A) ?? 0))
  const options = uniqueTop(ranked, 3).map(p => {
    const rated = n(specs(p).current_rated_A) ?? 0
    const ok = busCurrent === null || rated >= busCurrent
    return option(p, [
      { label: '额定电流', value: `${fmt(rated, 0)} A`, verdict: ok ? 'ok' : 'warn', note: busCurrent !== null ? (ok ? `覆盖母线 ${fmt(busCurrent, 0)} A` : `低于母线 ${fmt(busCurrent, 0)} A`) : '按母线电流核对' },
      { label: '针脚', value: /2\+2/.test(p.model) ? '2 电源 + 2 信号' : '2 电源', verdict: 'info' },
    ], ok ? undefined : '额定电流低于母线电流总和，大负载会发热，需换更大规格或分路。')
  })
  return {
    key: 'bus_connector',
    label: '母线连接器 XT60/XT90',
    group: '线束',
    virtual: {
      summary: '电池 → 母线 · 按母线电流选 XT60/XT90',
      fields: [{ label: '电流', value: busCurrent !== null ? `母线约 ${fmt(busCurrent, 0)} A` : '按母线电流总和' }],
    },
    qty: 2,
    options,
    advice: ['电池侧与母线侧各一对；压接/焊接要可靠，大电流优先 XT90。'],
    sortNote: '按额定电流升序，对照母线电流标注覆盖情况。',
  }
}

function fuseRole(parts: CatalogPart[]): RolePlan {
  const fuse = parts.find(p => p.category === 'power' && /保险丝/i.test(p.model))
  return {
    key: 'fuse',
    label: '保险丝座',
    group: '电源',
    virtual: {
      summary: '保险丝座 + 保险丝 · 按母线电流 1.5–2 倍',
      fields: [{ label: '规格', value: '母线电流 ×1.5–2' }],
    },
    qty: 1,
    options: fuse ? [option(fuse, [{ label: '规格', value: '按母线电流选', verdict: 'info' }])] : [],
    advice: ['保险丝按母线电流的 1.5–2 倍选；电池主线与母线分支分别保护。'],
    sortNote: '站内现有条目仅作参考。',
  }
}

function switchRole(parts: CatalogPart[], busCurrent: number | null): RolePlan {
  const pool = parts.filter(p =>
    (p.category === 'power' && String(p.subtype ?? '') === 'switch')
    || (p.category === 'open_hw' && /MOS开关|电源开关/.test(p.model)))
  const options = pool.map(p => {
    const rated = n(specs(p).current_rated_A)
    const isMos = /MOS/.test(p.model)
    const evals: EvalItem[] = [
      { label: '类型', value: isMos ? 'MOS 电子开关' : '机械开关', verdict: 'info', note: isMos ? '需 PWM 控制信号' : undefined },
    ]
    if (rated !== null) evals.push({ label: '额定', value: `${fmt(rated, 0)} A`, verdict: busCurrent !== null && rated < busCurrent ? 'warn' : 'info', note: busCurrent !== null && rated < busCurrent ? '低于母线电流，只适合逻辑支路' : undefined })
    if (isMos) evals.push({ label: '耐压', value: '24V 级', verdict: 'info', note: '48V 母线需核对耐压' })
    return option(p, evals, isMos ? 'MOS 开关需控制信号与失效安全设计（默认断开），急停回路不能只依赖软件。' : undefined)
  })
  return {
    key: 'switch',
    label: '电源开关 / 急停',
    group: '电源',
    virtual: {
      summary: '动力母线开关 + 急停 · 逻辑电可保留',
      fields: [{ label: '位置', value: '电池 → 母线之间' }, { label: '电流', value: '≥ 母线电流' }],
    },
    qty: 1,
    options,
    advice: ['急停要断动力母线，逻辑电可保留以便记录；机械开关电流不够时只切逻辑、动力用接触器/MOS。'],
    sortNote: '站内现有条目仅作参考，大电流急停开关需外购。',
  }
}

// ── 线束计算 ──────────────────────────────────────────────────────────────

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

// ── 主入口 ────────────────────────────────────────────────────────────────

export function plan(input: SelectorInput, models: SelectorModel[], parts: CatalogPart[], choices: Choices): Plan {
  const reference = models.find(m => m.id === input.modelId) ?? null
  const effective = reference
    ? { type: reference.type, mass_kg: reference.mass_kg, dof: reference.dof, effort_min_Nm: reference.effort_min_Nm, effort_max_Nm: reference.effort_max_Nm }
    : { type: input.type, mass_kg: input.manual.mass_kg, dof: input.manual.dof, effort_min_Nm: input.manual.effort_min_Nm, effort_max_Nm: input.manual.effort_max_Nm }
  const needs = input.needs
  const warnings: string[] = []
  const byId = new Map(parts.map(p => [p.id, p]))
  const chosen = (key: string): CatalogPart | null => {
    const id = choices[key]?.partId
    return id ? byId.get(id) ?? null : null
  }
  const qtyOf = (role: RolePlan) => Math.max(0, Math.min(999, Math.floor(choices[role.key]?.qty ?? role.qty)))

  const spare = Math.ceil(effective.dof * Math.max(0, Math.min(50, needs.sparePct)) / 100)
  const mixed = needs.mixedLimbs && effective.type === 'humanoid' && effective.dof > 12
  const actuatorKey = mixed ? 'actuator_leg' : 'actuator'
  const actuator = chosen(actuatorKey)
  const bus = actuatorBus(actuator)

  const needHigh = needs.compute
    || needs.controls.some(c => c === 'rl' || c === 'autonomy')
    || needs.depth || needs.lidar || needs.camera

  const roles: RolePlan[] = []
  const effortAvg = (effective.effort_min_Nm + effective.effort_max_Nm) / 2

  if (mixed) {
    roles.push(actuatorRole(parts, effective.type, effortAvg, 12 + spare, 'actuator_leg', '执行器（腿）', [
      '腿关节数默认按 12 估算，请按关节表修改数量。',
    ]))
    roles.push(actuatorRole(parts, 'arm', null, Math.max(0, effective.dof - 12), 'actuator_arm', '执行器（臂）', [
      '臂部扭矩不做估算：按关节表逐关节核对，数量默认 DOF−12，可改。',
    ]))
    warnings.push('腿/臂混搭：腿部按参考机型 min–max 中值、臂部按关节表分别选；数量默认 12 + (DOF−12)，需复核。')
  } else {
    roles.push(actuatorRole(parts, effective.type, effortAvg, effective.dof + spare, 'actuator', '执行器',
      spare > 0 ? [`含备件 ${spare} 台（${needs.sparePct}%）。`] : []))
  }
  if (reference && /^M8/.test(reference.motor_tier)) {
    warnings.push(`${reference.model} 的峰值需求 ${reference.effort_max_Nm} N·m 属于 M8 档，站内没有对应执行器。`)
  }

  const motorVolt = actuator ? n(specs(actuator).voltage_V) : null
  const voltageClass: 12 | 24 | 48 = motorVolt === null ? 24 : motorVolt >= 30 ? 48 : motorVolt < 15 ? 12 : 24
  const estimatedWh = Math.min(800, Math.max(50, effective.mass_kg * 8))
  if (needs.power === 'battery') {
    roles.push(batteryRole(parts, voltageClass, estimatedWh, reference?.vendor ?? '', actuator !== null))
    if (voltageClass === 48) warnings.push('48V 级电池站内暂无整包；2×6S 串联需要同批次同容量电芯，BMS 必须按 12S 选。')
    if (voltageClass === 12) warnings.push('12V 级站内暂无 3S 整包；需外购 3S 电池或用 6S + 降压模块。')
  } else {
    roles.push(psuRole(parts))
  }

  roles.push(lowRole(parts, actuator, needHigh, effective.dof + spare))
  const lowPart = chosen('low')
  if (lowPart && lowPart.category === 'module' && !needHigh) {
    warnings.push('当前没有上位机，但下位机选了总线桥接：桥接器没有主机无法工作，请改选带 MCU 的下位机或启用上位机。')
  }

  if (needHigh) roles.push(highRole(parts, needs))

  const busVoltage = voltageClass === 48 ? 48 : voltageClass === 12 ? 22 : 24
  roles.push(powerDistRole(parts, needs.power === 'tethered' ? 24 : busVoltage, needHigh, bus))

  if (effective.type !== 'arm') roles.push(imuRole(parts))
  if (needs.depth) roles.push(depthRole(parts))
  if (needs.lidar || needs.controls.includes('autonomy')) {
    const prefer3D = effective.mass_kg > 20 || input.size === 'medium' || input.size === 'large' || input.size === 'xlarge'
    roles.push(lidarRole(parts, prefer3D))
  }
  if (needs.camera && !needs.depth) roles.push(cameraRole(parts))
  if (needs.remote || needs.controls.includes('teleop')) roles.push(remoteRole(parts))

  roles.push(connectorRole(parts, effective.dof + spare))

  // 线束：只在选了真实执行器后计算
  const harness: HarnessRow[] = []
  let busCurrent: number | null = null
  const harnessActuator = actuator ?? (mixed ? chosen('actuator_arm') : null)
  if (harnessActuator) {
    const ir = n(specs(harnessActuator).i_rated_A)
    const ip = n(specs(harnessActuator).i_peak_A)
    const perMotorCurrent = ir ?? (ip !== null ? Math.max(1, ip * 0.4) : null)
    if (perMotorCurrent !== null) {
      const motorGauge = awgFor(perMotorCurrent, true)
      busCurrent = perMotorCurrent * effective.dof
      const busGauge = awgFor(busCurrent, false)
      const requiredBore = 2 * motorGauge.od + 2 * 1.7
      harness.push({
        motor: `${harnessActuator.model} × ${effective.dof}`,
        qty: effective.dof,
        current_A: perMotorCurrent,
        awg: motorGauge.awg,
        connector: 'XT30(2+2)',
        requiredBore_mm: requiredBore,
        status: motorGauge.capped ? 'partial' : 'declared',
        note: motorGauge.capped
          ? `额定 ${perMotorCurrent.toFixed(1)} A 本应更粗，但 XT30(2+2) 外壳限制最大 14AWG；高占空比需复核温升。`
          : '按硅胶线参考电流 ×70% ≥ 额定电流；2 电源 + 2 信号。',
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
    } else {
      warnings.push(`${harnessActuator.model} 未公布额定/峰值电流，线束按 datasheet 复核后再生成。`)
    }
  }

  roles.push(busConnectorRole(parts, busCurrent))
  roles.push(fuseRole(parts))
  roles.push(switchRole(parts, busCurrent))

  // 预算与待定统计
  let known = 0
  let virtualLines = 0
  for (const role of roles) {
    const part = chosen(role.key)
    const qty = qtyOf(role)
    if (part) {
      const price = priceOf(part)
      if (price !== null) known += price * qty
      else virtualLines += 1
    } else {
      virtualLines += 1
    }
  }
  if (needs.budget !== null && known > needs.budget) {
    warnings.push(`已知小计 ¥${known.toFixed(0)} 超过预算 ¥${needs.budget}；虚拟件与询价条目还未计入。`)
  }

  const tau = actuator ? (n(specs(actuator).tau_peak_Nm) ?? n(specs(actuator).stall_torque_Nm) ?? effective.effort_max_Nm) : effective.effort_max_Nm
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
    roles,
    harness,
    warnings: [...new Set(warnings)],
    mjcf,
    totals: { known_cny: known, virtual_lines: virtualLines, currency: 'CNY' },
  }
}

// ── 导出 / 导入 ───────────────────────────────────────────────────────────

export type BomPayload = ReturnType<typeof buildBomPayload>

export function buildBomPayload(input: SelectorInput, result: Plan, choices: Choices, parts: CatalogPart[]) {
  const byId = new Map(parts.map(p => [p.id, p]))
  const lines = result.roles.map(role => {
    const ch = choices[role.key] ?? {}
    const part = ch.partId ? byId.get(ch.partId) ?? null : null
    const qty = Math.max(0, Math.min(999, Math.floor(ch.qty ?? role.qty)))
    const unit = part ? priceOf(part) : null
    const opt = part ? role.options.find(o => o.part.id === part.id) : undefined
    return {
      role: role.key,
      label: role.label,
      group: role.group,
      selection: part ? 'part' : 'virtual',
      part_id: part?.id ?? null,
      model: part?.model ?? `虚拟${role.label}`,
      vendor: part?.vendor ?? null,
      requirement: role.virtual.fields,
      qty,
      unit_price_cny: unit,
      subtotal_cny: unit !== null ? unit * qty : null,
      evals: opt?.evals ?? [],
      risk: opt?.risk ?? null,
      advice: role.advice,
      alternates: role.options.map(o => o.part.id),
    }
  })
  return {
    version: 2,
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
      virtual_lines: lines.filter(l => l.selection === 'virtual' || l.unit_price_cny === null).length,
      currency: 'CNY',
    },
    warnings: result.warnings,
  }
}

export function toCsv(payload: BomPayload): string {
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const rows = [
    ['分组', '角色', '选型', '型号', '厂商', '虚拟件需求', '数量', '单价(CNY)', '小计(CNY)', '评价', '备注'],
    ...payload.lines.map(l => [
      l.group,
      l.label,
      l.selection === 'part' ? '已选' : '虚拟件',
      l.model,
      l.vendor,
      l.requirement.map((f: { label: string; value: string }) => `${f.label}: ${f.value}`).join('；'),
      l.qty,
      l.unit_price_cny,
      l.subtotal_cny,
      l.evals.map((e: EvalItem) => `${e.label} ${e.value}${e.note ? `（${e.note}）` : ''}`).join('；'),
      [l.risk, ...l.advice].filter(Boolean).join('；'),
    ]),
    ...payload.harness.map(h => ['线束明细', h.motor, '', h.connector, '', '', h.qty, '', '', `${h.awg} AWG / ${h.current_A.toFixed(1)} A${h.requiredBore_mm ? ` / 孔径≥${h.requiredBore_mm.toFixed(1)} mm` : ''}`, h.note]),
  ]
  return rows.map(r => r.map(esc).join(',')).join('\n')
}
