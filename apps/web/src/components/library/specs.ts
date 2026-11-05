export type Specs = Record<string, unknown>
export type SpecRow = { label: string; value: string }

const MATERIAL: Array<[string, string]> = [
  ['density_g_cm3', '密度 (g/cm³)'],
  ['modulus_GPa', '弹性模量 (GPa)'],
  ['modulus_kind', '模量类型'],
  ['tensile_MPa', '抗拉强度 (MPa)'],
  ['yield_MPa', '屈服强度 (MPa)'],
  ['elongation_pct', '断裂延伸率 (%)'],
  ['hardness', '硬度'],
  ['service_temp_C', '长期工作温度 (°C)'],
  ['low_temp_C', '低温下限 (°C)'],
  ['melting_C', '熔点 (°C)'],
  ['thermal_cond_W_mK', '导热系数 (W/(m·K))'],
  ['cte_um_mK', '线膨胀系数 (µm/(m·K))'],
  ['price_level', '参考价格档'],
]

const PROCESS: Array<[string, string]> = [
  ['tolerance_mm', '标准公差 (mm)'],
  ['surface_ra_um', '表面粗糙度 Ra (µm)'],
  ['layer_height_mm', '层高 (mm)'],
  ['min_wall_mm', '最小壁厚 (mm)'],
  ['max_size', '最大尺寸'],
  ['cost_level', '成本档'],
  ['lead_time', '交期'],
]

const ROBOT: Array<[string, string]> = [
  ['dof', '自由度'],
  ['mass_kg', '整机质量 (kg)'],
  ['payload_kg', '额定负载 (kg)'],
  ['speed_max_mps', '最大速度 (m/s)'],
  ['size_mm', '尺寸 (mm)'],
  ['climb_height_mm', '越障高度 (mm)'],
  ['climb_angle_deg', '爬坡角度 (°)'],
  ['battery', '电池'],
  ['endurance_h', '续航 (h)'],
  ['voltage_V', '电压 (V)'],
  ['voltage_range_V', '电压范围 (V)'],
  ['iface', '对外接口'],
  ['compute', '算力平台'],
  ['sensors', '传感器'],
]

// Values that are links/metadata, rendered in their own sections instead of the spec table.
const HIDDEN = new Set([
  'image_url',
  'image_source',
  'doc_url',
  'doc_pdf',
  'repo_urls',
  'urdf_urls',
  'repo_license',
  'ecosystem_id',
  'ecosystem_count',
  'price_note',
  'sim_note',
  'tolerance_note',
  'materials',
])

function display(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (Array.isArray(value)) return value.length ? value.join('、') : '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function specRows(kind: 'material' | 'process' | 'robot', specs: Specs = {}): SpecRow[] {
  const labels = kind === 'process' ? PROCESS : kind === 'robot' ? ROBOT : MATERIAL
  const known = new Set(labels.map(([key]) => key))
  const rows: SpecRow[] = labels.map(([key, label]) => ({ label, value: display(specs[key]) }))
  for (const [key, value] of Object.entries(specs)) {
    if (known.has(key) || HIDDEN.has(key)) continue
    rows.push({ label: key, value: display(value) })
  }
  return rows
}
