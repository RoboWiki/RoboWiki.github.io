import type { CatalogPart } from './catalog'

/**
 * 卡片上的「常见参数」按品类定义，而不是一张全局优先级表：
 * 芯片没有扭矩、电机没有量程，共用一张表会让每个品类都露出一排无意义的「—」。
 * 每张卡片取该品类的固定槽位，厂商没公布就写「—」（与部件页口径一致：缺失写 null，不是 0）。
 */
export type PartFact = {
  label: string
  /** 仅在值为数字时拼接，字符串值自带单位，避免出现「12–24 V V」。 */
  unit?: string
  keys: string[]
  derived?: (specs: Record<string, unknown>) => number | string | null
}

const num = (v: unknown): number | null => {
  const n = typeof v === 'number' ? v : Number(v)
  return Number.isFinite(n) ? n : null
}

const trim = (v: number): string =>
  Number.isInteger(v) ? String(v) : String(parseFloat(v.toPrecision(4)))

/** 峰值扭矩 / 质量 —— 本站选型最常用的单一派生指标。 */
const torqueDensity = (s: Record<string, unknown>): number | null => {
  const tau = num(s.tau_peak_Nm)
  const mass = num(s.mass_kg)
  if (tau === null || mass === null || mass <= 0) return null
  return Math.round((tau / mass) * 10) / 10
}

/** CAN 路数与是否 FD 合成一格：「4 · CAN FD」比拆成两行更好读。 */
const canCell = (s: Record<string, unknown>): string | null => {
  const can = num(s.can)
  if (can === null) return null
  return s.canfd ? `${can} · CAN FD` : String(can)
}

const FACTS: Record<string, PartFact[]> = {
  actuator: [
    { label: '额定扭矩', unit: ' N·m', keys: ['tau_rated_Nm'] },
    { label: '峰值扭矩', unit: ' N·m', keys: ['tau_peak_Nm'] },
    { label: '空载转速', unit: ' rpm', keys: ['speed_noload_rpm'] },
    { label: '额定转速', unit: ' rpm', keys: ['speed_rated_rpm'] },
    { label: '减速比', unit: ':1', keys: ['gear'] },
    { label: '质量', unit: ' kg', keys: ['mass_kg'] },
    { label: '扭矩密度', unit: ' N·m/kg', keys: [], derived: torqueDensity },
    { label: '电压范围', keys: ['voltage_range_V', 'voltage_V'], unit: ' V' },
  ],
  servo: [
    { label: '额定扭矩', unit: ' N·m', keys: ['rated_torque_Nm'] },
    { label: '堵转扭矩', unit: ' N·m', keys: ['stall_torque_Nm'] },
    { label: '空载转速', unit: ' rpm', keys: ['speed_rpm'] },
    { label: '60° 用时', unit: ' s', keys: ['speed_s_60deg'] },
    { label: '工作电压', keys: ['voltage_range', 'voltage_V'], unit: ' V' },
    { label: '反馈协议', keys: ['protocol', 'comm'] },
  ],
  esc: [
    { label: '持续电流', unit: ' A', keys: ['current_cont_A'] },
    { label: '峰值电流', unit: ' A', keys: ['current_peak_A'] },
    { label: '输入电压', keys: ['voltage_in_V'], unit: ' V' },
    { label: '最高电压', unit: ' V', keys: ['voltage_max_V'] },
    { label: '控制频率', unit: ' kHz', keys: ['ctrl_khz'] },
    { label: '通信', keys: ['comm', 'iface'] },
  ],
  motor_driver: [
    { label: 'MCU', keys: ['mcu'] },
    { label: 'FOC 轴数', keys: ['foc_axes'] },
    { label: 'CAN', keys: ['can'], derived: canCell },
    { label: '供电', keys: ['voltage_in_V'], unit: ' V' },
    { label: '最高电压', unit: ' V', keys: ['voltage_max_V'] },
    { label: '接口', keys: ['iface'] },
  ],
  controller_high: [
    { label: 'SoC', keys: ['soc'] },
    { label: 'CPU', keys: ['cpu'] },
    { label: 'NPU', unit: ' TOPS', keys: ['npu_tops'] },
    { label: '内存', unit: ' GB', keys: ['ram_gb'] },
    { label: '网口', keys: ['eth'] },
    { label: '系统', keys: ['os'] },
  ],
  controller_low: [
    { label: 'MCU', keys: ['mcu'] },
    { label: '主频', unit: ' MHz', keys: ['clock_mhz'] },
    { label: 'CAN', keys: ['can'], derived: canCell },
    { label: '最高电压', unit: ' V', keys: ['voltage_max_V'] },
    { label: '上位通信', keys: ['comm_upper'] },
    { label: '接口', keys: ['iface'] },
  ],
  remote_controller: [
    { label: '通道', unit: ' 路', keys: ['channels'] },
    { label: '频段', unit: ' GHz', keys: ['frequency_ghz'] },
    { label: '遥控距离', unit: ' m', keys: ['control_range_m'] },
    { label: '协议', keys: ['protocol'] },
    { label: '电池', keys: ['battery'] },
    { label: '接口', keys: ['iface'] },
  ],
  imu: [
    { label: '陀螺量程', unit: ' °/s', keys: ['gyro_range_dps'] },
    { label: '加计量程', unit: ' g', keys: ['accel_range_g'] },
    { label: 'ODR', unit: ' Hz', keys: ['odr_hz'] },
    { label: '接口', keys: ['iface'] },
    { label: '封装', keys: ['package'] },
    { label: '噪声', keys: ['noise'] },
  ],
  sensor: [
    { label: '量程', unit: ' m', keys: ['range_m'] },
    { label: '测量范围', keys: ['meas_range'] },
    { label: '准确度', keys: ['accuracy'] },
    { label: '重复精度', unit: ' mm', keys: ['repeatability_mm'] },
    { label: '分辨率', keys: ['resolution'] },
    { label: '接口 / 输出', keys: ['iface'] },
  ],
  lidar: [
    { label: '量程', unit: ' m', keys: ['range_m'] },
    { label: '点频', unit: ' 点/s', keys: ['points_per_s'] },
    { label: '帧率', unit: ' Hz', keys: ['fps'] },
    { label: '视场', keys: ['fov'] },
    { label: '接口', keys: ['iface'] },
    { label: '电压', unit: ' V', keys: ['voltage_V'] },
  ],
  camera: [
    { label: '深度量程', keys: ['depth_range_m'], unit: ' m' },
    { label: '帧率', unit: ' fps', keys: ['fps'] },
    { label: '视场', keys: ['fov'] },
    { label: '分辨率', keys: ['resolution'] },
    { label: '接口', keys: ['iface'] },
    { label: '重量', unit: ' g', keys: ['weight_g'] },
  ],
  battery: [
    { label: '容量', unit: ' mAh', keys: ['capacity_mah'] },
    { label: '电压', unit: ' V', keys: ['voltage_V'] },
    { label: '能量', unit: ' Wh', keys: ['energy_wh'] },
    { label: '放电倍率', unit: ' C', keys: ['discharge_rate_c'] },
    { label: '质量', unit: ' g', keys: ['mass_g'] },
    { label: '体系', keys: ['chem'] },
  ],
  module: [
    { label: 'CAN', keys: ['can'], derived: canCell },
    { label: '速率', unit: ' Mbps', keys: ['can_speed_mbps'] },
    { label: '接口', keys: ['iface'] },
    { label: '电气隔离', keys: ['isolation'], derived: s => (s.isolation === undefined ? null : s.isolation ? '是' : '否') },
    { label: '尺寸', keys: ['dims'] },
    { label: '电压', unit: ' V', keys: ['voltage_V'] },
  ],
  chip: [
    { label: '类型', keys: ['category_cn', 'chip_function'] },
    { label: '封装', keys: ['package'] },
    { label: '通道', keys: ['channels'] },
    { label: '输出电流', unit: ' A', keys: ['current_out'] },
    { label: '库存', keys: ['stock'] },
    { label: '交期', keys: ['lead_time'] },
  ],
  connector: [
    { label: '位数', unit: ' P', keys: ['positions'] },
    { label: '间距', unit: ' mm', keys: ['pitch_mm'] },
    { label: '额定电流', unit: ' A', keys: ['current_rated_A'] },
    { label: '额定电压', unit: ' V', keys: ['voltage_rated_V'] },
    { label: '安装', keys: ['mount_type'] },
    { label: '接口', keys: ['iface'] },
  ],
  power: [
    { label: '输入电压', keys: ['voltage_in'] },
    { label: '输出电压', keys: ['voltage_out'] },
    { label: '输出电流', keys: ['current_out'] },
    { label: '通道', keys: ['channels'] },
    { label: '类型', keys: ['function_type', 'switch_type'] },
    { label: '接口', keys: ['iface'] },
  ],
  open_hw: [
    { label: 'CAN', keys: ['can'], derived: canCell },
    { label: '接口', keys: ['iface'] },
    { label: '输入电压', keys: ['voltage_in'] },
    { label: '输出电流', keys: ['current_out'] },
    { label: '保护', keys: ['protection'] },
    { label: '许可', keys: ['license'] },
  ],
}

/** 没单独定义口径的品类（结构件等）：退到通用硬件字段。 */
const GENERIC: PartFact[] = [
  { label: '接口', keys: ['iface'] },
  { label: '电压', unit: ' V', keys: ['voltage_V'] },
  { label: '尺寸', keys: ['dims', 'size_mm'] },
  { label: '质量', unit: ' kg', keys: ['mass_kg'] },
  { label: '重量', unit: ' g', keys: ['weight_g'] },
  { label: '功率', unit: ' W', keys: ['power_w'] },
]

export type FactCell = { label: string; value: string }

export function partFacts(p: CatalogPart): FactCell[] {
  const specs = (p.specs ?? {}) as Record<string, unknown>
  const table = FACTS[p.category] || GENERIC
  return table.map(fact => {
    let raw: number | string | null = null
    if (fact.derived) {
      raw = fact.derived(specs)
    } else {
      for (const key of fact.keys) {
        const v = specs[key]
        if (v !== null && v !== undefined && v !== '') {
          raw = v as number | string
          break
        }
      }
    }
    if (raw === null || raw === undefined || raw === '') return { label: fact.label, value: '—' }
    if (typeof raw === 'number') return { label: fact.label, value: `${trim(raw)}${fact.unit ?? ''}` }
    const text = String(raw)
    // 纯数字或区间（15~52）补单位；自带单位的字符串（DC 12 … 30、15-60V）不再重复拼。
    const value = fact.unit && !/[A-Za-zµ°]/.test(text) ? `${text}${fact.unit}` : text
    return { label: fact.label, value }
  })
}
