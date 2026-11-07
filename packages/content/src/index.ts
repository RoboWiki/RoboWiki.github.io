/**
 * 双端共用的信息架构与文案。
 *
 * 只放「两端必须一致」的东西：一级入口、页面命名、空态/错误/加载文案、
 * 讨论区措辞。组件实现仍各自留在 apps/web 与 apps/app。
 */

export type WebNavItem = {
  key: 'learn' | 'builds' | 'catalog' | 'community' | 'suppliers'
  label: string
  desc: string
  href: string
  match: string[]
}

/** 网页端一级导航：学习 / 方案 / 部件 / 社区 / 采购 */
export const WEB_NAV: WebNavItem[] = [
  {
    key: 'learn',
    label: '学习',
    desc: '从零到跑通，按天给判据',
    href: '/start.html',
    match: ['/start', '/paths', '/learn'],
  },
  {
    key: 'builds',
    label: '方案',
    desc: '可复现方案，含 BOM 与步骤',
    href: '/builds.html',
    match: ['/builds', '/robots', '/competitions'],
  },
  {
    key: 'catalog',
    label: '部件',
    desc: '参数带来源，缺失写 null',
    href: '/catalog.html',
    match: ['/catalog', '/parts', '/materials'],
  },
  {
    key: 'community',
    label: '社区',
    desc: '写实测，不写「好用」',
    href: '/community.html',
    match: ['/community', '/post', '/u', '/top', '/contributors'],
  },
  {
    key: 'suppliers',
    label: '采购',
    desc: '报价、交期与真实反馈',
    href: '/suppliers.html',
    match: ['/suppliers'],
  },
]

export type AppTab = {
  key: 'home' | 'catalog' | 'builds' | 'community' | 'account'
  label: string
  pagePath: string
}

/** 小程序 tabBar：首页 / 部件 / 方案 / 社区 / 我的 */
export const APP_TABS: AppTab[] = [
  { key: 'home', label: '首页', pagePath: 'pages/home/index' },
  { key: 'catalog', label: '部件', pagePath: 'pages/index/index' },
  { key: 'builds', label: '方案', pagePath: 'pages/builds/index' },
  { key: 'community', label: '社区', pagePath: 'pages/community/index' },
  { key: 'account', label: '我的', pagePath: 'pages/account/index' },
]

export const DISCUSSION = {
  title: '讨论',
  collapsedHint: '展开查看讨论与纠错',
  empty: '还没有讨论，成为第一个留下实测记录的人',
  loginHint: '登录后可以参与讨论',
}

export const EMPTY = {
  catalog: {
    title: '没有匹配的部件',
    hint: '换个关键词，或切回全部品类',
    action: '清除筛选',
  },
  builds: {
    title: '没有匹配的方案',
    hint: '换个关键词，或切回全部形态',
    action: '清除筛选',
  },
  community: {
    title: '还没有帖子',
    hint: '第一条实测，从你开始',
    action: '去发帖',
  },
  learn: {
    title: '还没有指南',
    hint: '内容正在整理，先去看看部件库',
    action: '去部件库',
  },
} as const

export const PAGE_SIZE = {
  catalog: 20,
  builds: 12,
  community: 20,
} as const

export const SECTION_TITLES = {
  catalog: '部件库',
  builds: '方案库',
  community: '社区',
  learn: '学习',
  suppliers: '采购渠道',
} as const

// ── 项目定位与能力骨架 ────────────────────────────────────────────────
// 四层是「骨架」，系统集成是「大脑」：前者可逐层选型，后者负责把四层装进
// 同一台机器并收口。两端、文档、数据页都从这里取同一套命名，避免各写一套。

export const POSITIONING = {
  short: '面向机器人制作全流程的可追溯工程知识库',
  full: '以「机械—硬件—嵌入式—算法」四层能力为骨架，以系统集成能力为大脑，以社区共建方式汇聚部件选型与评价、加工与采购经验、教程、案例与开源索引，贯通需求定义、方案设计、工程实现、测试验证与迭代优化，让机器人制作经验沉淀为可检索、可复现、可追溯的工程知识。',
  tagline: '每一步都有来源，每一套都能复现。',
} as const

export type LayerId = 'mechanical' | 'hardware' | 'embedded' | 'algorithm' | 'system'

export type Layer = {
  id: LayerId
  index: string
  name: string
  en: string
  tagline: string
  desc: string
  /** layer = 四层骨架之一；brain = 横贯四层的系统集成 */
  role: 'layer' | 'brain'
  /** 覆盖的部件品类 id（对应 data/taxonomy.json） */
  categories: string[]
  /** 相关指南 slug（对应 apps/web/src/content/learn） */
  guides: string[]
  /** 该层要回答的关键问题 */
  questions: string[]
  /** Tailwind 令牌色类名 */
  tone: string
  hint: string
}

export const LAYERS: Layer[] = [
  {
    id: 'mechanical',
    index: '01',
    name: '机械',
    en: 'Mechanical',
    tagline: '构型、传动与材料边界',
    desc: '从自由度与载荷倒推结构，先把传动链、材料与加工工艺的边界算清楚，再谈装配。',
    role: 'layer',
    categories: ['structural', 'actuator', 'servo'],
    guides: ['selection-order', 'motor-specs'],
    questions: ['需要多大扭矩与转速余量？', '传动方案与背隙能不能接受？', '材料与工艺的能力边界在哪？'],
    tone: 'text-layer-mech',
    hint: '结构件、关节电机与舵机',
  },
  {
    id: 'hardware',
    index: '02',
    name: '硬件',
    en: 'Hardware',
    tagline: '供电、驱动与板级设计',
    desc: '按电流回路、接口与散热设计硬件，把电池、电源、驱动与连接器的余量写成可核对的值。',
    role: 'layer',
    categories: [
      'controller_high', 'battery', 'power', 'connector', 'module',
      'chip', 'open_hw', 'remote_controller', 'esc',
    ],
    guides: ['motor-specs', 'control-chain'],
    questions: ['峰值电流与母线压降够不够？', '接口、连接器与散热余量够不够？', '器件供货与替代方案是否可查？'],
    tone: 'text-layer-hw',
    hint: '上位机、电池、电源、连接器、芯片与开源硬件',
  },
  {
    id: 'embedded',
    index: '03',
    name: '嵌入式',
    en: 'Embedded',
    tagline: '固件、总线与实时性',
    desc: '把主控、驱动器、总线与固件放在一条时间线上，算清周期、带宽与实时性预算。',
    role: 'layer',
    categories: ['controller_low', 'motor_driver'],
    guides: ['control-chain'],
    questions: ['控制周期与实时性够不够？', '总线带宽与节点数上限是多少？', '固件、驱动与工具链是否成熟？'],
    tone: 'text-layer-emb',
    hint: '下位机、电机驱动板、电调与固件 / 总线',
  },
  {
    id: 'algorithm',
    index: '04',
    name: '算法',
    en: 'Algorithm',
    tagline: '感知、估计与控制',
    desc: '算法决定传感器的精度与频率要求，反过来传感器也限制能跑什么算法。',
    role: 'layer',
    categories: ['sensor', 'imu', 'lidar', 'camera'],
    guides: ['control-chain', 'open-source-reading'],
    questions: ['需要多高的更新率与精度？', '标定与噪声模型怎么验证？', '算力预算能不能覆盖整套估计？'],
    tone: 'text-layer-algo',
    hint: 'IMU、激光雷达、深度相机与传感器',
  },
  {
    id: 'system',
    index: '★',
    name: '系统集成',
    en: 'System Integration',
    tagline: '需求、接口、联调与迭代',
    desc: '把四层选择装进同一台机器，用整机方案、接口契约、联调记录与迭代复盘收口。',
    role: 'brain',
    categories: [],
    guides: ['selection-order', 'open-source-reading'],
    questions: ['整机质量与重心是否可接受？', '接口契约与预算冲突时砍谁？', '出问题能不能定位到具体一层？'],
    tone: 'text-layer-sys',
    hint: '整机方案、接口契约与联调记录',
  },
]

export const LAYER_BY_ID = Object.fromEntries(LAYERS.map((l) => [l.id, l])) as Record<LayerId, Layer>

/** 品类 → 层级 的反查表；系统集成不挂具体品类。 */
export const LAYER_OF_CATEGORY: Record<string, LayerId> = LAYERS.reduce(
  (acc, layer) => {
    for (const c of layer.categories) acc[c] = layer.id
    return acc
  },
  {} as Record<string, LayerId>,
)

export const layerOfCategory = (category: string): Layer | undefined => {
  const id = LAYER_OF_CATEGORY[category]
  return id ? LAYER_BY_ID[id] : undefined
}

/** 四层骨架（不含系统集成），用于「四层 + 大脑」的页面排版。 */
export const SKELETON_LAYERS = LAYERS.filter((l) => l.role === 'layer')
export const BRAIN_LAYER = LAYERS.find((l) => l.role === 'brain')

// ── 参数字段名 → 中文标签 / 单位 ──────────────────────────────────────
// 数据里的 specs 是原始字段名（od_mm、voltage_V、kt_Nm_per_A…）。
// 后端 key_specs 只覆盖卡片要用的少数项，详情页仍需一个通用兜底，
// 避免把 snake_case 直接丢给用户。
const SPEC_LABELS: Record<string, [string, string]> = {
  od_mm: ['外径', 'mm'],
  l_mm: ['长度', 'mm'],
  w_mm: ['宽度', 'mm'],
  h_mm: ['高度', 'mm'],
  size_mm: ['尺寸', 'mm'],
  voltage_V: ['电压', 'V'],
  voltage_in_V: ['输入电压', 'V'],
  voltage_out_V: ['输出电压', 'V'],
  voltage_range_V: ['电压范围', 'V'],
  kt_Nm_per_A: ['转矩常数', 'N·m/A'],
  ke_V_per_krpm: ['反电动势常数', 'V/krpm'],
  tau_peak_Nm: ['峰值扭矩', 'N·m'],
  tau_rated_Nm: ['额定扭矩', 'N·m'],
  mass_kg: ['质量', 'kg'],
  gear: ['减速比', ''],
  speed_noload_rpm: ['空载转速', 'rpm'],
  speed_rated_rpm: ['额定转速', 'rpm'],
  current_rated_A: ['额定电流', 'A'],
  current_peak_A: ['峰值电流', 'A'],
  power_w: ['功率', 'W'],
  power_max_w: ['最大功率', 'W'],
  encoder_bits: ['编码器位数', 'bit'],
  encoder: ['编码器', ''],
  comm: ['通信接口', ''],
  iface: ['接口', ''],
  can: ['CAN', ''],
  can_speed_mbps: ['CAN 速率', 'Mbps'],
  dof: ['自由度', ''],
  payload_kg: ['额定负载', 'kg'],
  endurance_h: ['续航', 'h'],
  range_m: ['量程', 'm'],
  fov: ['视场角', ''],
  fps: ['帧率', 'fps'],
  depth_range_m: ['深度量程', 'm'],
  npu_tops: ['NPU 算力', 'TOPS'],
  ram_gb: ['内存', 'GB'],
  soc: ['SoC', ''],
  armature_kgm2: ['电枢惯量', 'kg·m²'],
  rotor_inertia_kgm2: ['转子惯量', 'kg·m²'],
  torque_density_Nm_per_kg: ['扭矩密度', 'N·m/kg'],
  peak_rated_ratio: ['峰额比', ''],
  speed_noload_rad_s: ['空载角速度', 'rad/s'],
}

// 顺序重要：长后缀在前，避免 `_mm` 被 `_m` 先匹配。
const UNIT_SUFFIXES: Array<[string, string]> = [
  ['_kgm2', 'kg·m²'],
  ['_mm2', 'mm²'],
  ['_mm', 'mm'],
  ['_cm', 'cm'],
  ['_km', 'km'],
  ['_kg', 'kg'],
  ['_g', 'g'],
  ['_Nm', 'N·m'],
  ['_rpm', 'rpm'],
  ['_Mbps', 'Mbps'],
  ['_kHz', 'kHz'],
  ['_Hz', 'Hz'],
  ['_V', 'V'],
  ['_A', 'A'],
  ['_W', 'W'],
  ['_deg', '°'],
  ['_pct', '%'],
  ['_TOPS', 'TOPS'],
  ['_GB', 'GB'],
  ['_bit', 'bit'],
  ['_h', 'h'],
  ['_s', 's'],
  ['_m', 'm'],
]

function prettifyKey(key: string): string {
  return key
    .replace(/[._-]+/g, ' ')
    .replace(/\b[a-z]/g, (c) => c.toUpperCase())
    .trim()
}

/** 已知字段用中文名；未知字段剥掉单位后缀，再把 snake_case 变成可读词。 */
export function specLabel(key: string): { label: string; unit: string } {
  const known = SPEC_LABELS[key]
  if (known) return { label: known[0], unit: known[1] }
  for (const [suffix, unit] of UNIT_SUFFIXES) {
    if (key.endsWith(suffix) && key.length > suffix.length) {
      return { label: prettifyKey(key.slice(0, -suffix.length)), unit }
    }
  }
  return { label: prettifyKey(key), unit: '' }
}

/** 统一值展示：null/空写「—」，布尔写是/否，数值补单位。 */
export function formatSpecValue(value: unknown, unit = ''): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (Array.isArray(value)) return value.length ? value.join('、') : '—'
  if (typeof value === 'object') return JSON.stringify(value)
  const text = String(value)
  return unit && !text.includes(unit) ? `${text} ${unit}` : text
}
