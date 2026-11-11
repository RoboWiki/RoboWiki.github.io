/**
 * 双端共用的信息架构与文案。
 *
 * 只放「两端必须一致」的东西：一级入口、页面命名、空态/错误/加载文案、
 * 讨论区措辞。组件实现仍各自留在 apps/web 与 apps/app。
 */

export type WebNavItem = {
  key: 'home' | 'learn' | 'builds' | 'catalog' | 'selector' | 'equipment' | 'suppliers' | 'community'
  label: string
  desc: string
  href: string
  match: string[]
}

/** 网页端一级导航：首页 / 教程库 / 选型台 / 部件库 / 方案库 / 采购库 / 设备库 / 社区 */
export const WEB_NAV: WebNavItem[] = [
  {
    key: 'home',
    label: '首页',
    desc: '本站定位、使用说明与入口',
    href: '/',
    match: ['/'],
  },
  {
    key: 'learn',
    label: '教程库',
    desc: '经典 PDF 与本站导读，按方向筛选',
    href: '/learn/index.html',
    match: ['/learn', '/paths'],
  },
  {
    key: 'selector',
    label: '选型台',
    desc: '按构型与功能推导 BOM 和 MJCF',
    href: '/selector.html',
    match: ['/selector'],
  },
  {
    key: 'catalog',
    label: '部件库',
    desc: '参数带来源，缺失写 null',
    href: '/catalog.html',
    match: ['/catalog', '/parts', '/materials'],
  },
  {
    key: 'builds',
    label: '方案库',
    desc: '可复现方案，含 BOM 与步骤',
    href: '/builds.html',
    match: ['/builds', '/robots', '/competitions'],
  },
  {
    key: 'suppliers',
    label: '采购库',
    desc: '按加工品类找店，先看有没有坑',
    href: '/suppliers.html',
    match: ['/suppliers'],
  },
  {
    key: 'equipment',
    label: '设备库',
    desc: '做机器人的工具与仪器',
    href: '/equipment.html',
    match: ['/equipment'],
  },
  {
    key: 'community',
    label: '社区',
    desc: '写实测，不写「好用」',
    href: '/community.html',
    match: ['/community', '/post', '/u', '/top', '/contributors'],
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
  { key: 'catalog', label: '部件库', pagePath: 'pages/index/index' },
  { key: 'builds', label: '方案库', pagePath: 'pages/builds/index' },
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
  equipment: {
    title: '没有匹配的设备',
    hint: '换个关键词，或切回全部类型',
    action: '清除筛选',
  },
} as const

export const PAGE_SIZE = {
  catalog: 20,
  builds: 12,
  community: 20,
} as const

export const SECTION_TITLES = {
  catalog: '部件库',
  equipment: '设备库',
  builds: '方案库',
  community: '社区',
  learn: '教程库',
  suppliers: '采购库',
} as const

// ── 项目定位与能力骨架 ────────────────────────────────────────────────
// 四层是「骨架」，系统集成是「大脑」：前者可逐层选型，后者负责把四层装进
// 同一台机器并收口。两端、文档、数据页都从这里取同一套命名，避免各写一套。

export const POSITIONING = {
  short: '机器人制作工程知识库',
  full: '教程、方案、采购、设备、社区与部件库在同一站；部件页保留参数、价格、来源和实测评价。',
  tagline: '教程、方案、采购、设备、社区与部件库在同一站。',
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
    categories: ['structural', 'wheel', 'actuator', 'servo'],
    guides: ['mechanical-transmission-pdf', 'structural-design-logic-pdf', 'lightweight-design-pdf', 'machining-guide-pdf'],
    questions: ['需要多大扭矩与转速余量？', '传动方案与背隙能不能接受？', '材料与工艺的能力边界在哪？'],
    tone: 'text-layer-mech',
    hint: '结构件、轮组、关节电机与舵机',
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
      'controller_high', 'battery', 'charger', 'power', 'connector', 'module',
      'chip', 'open_hw', 'remote_controller', 'esc', 'referee', 'equipment',
    ],
    guides: [],
    questions: ['峰值电流与母线压降够不够？', '接口、连接器与散热余量够不够？', '器件供货与替代方案是否可查？'],
    tone: 'text-layer-hw',
    hint: '上位机、电池、充电器、电源、连接器、芯片与开源硬件',
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
    guides: [],
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
    guides: [],
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
    guides: ['rp1-whitepaper'],
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
  // 测距 / 工业传感器与通用硬件字段
  meas_range: ['测量范围', ''],
  accuracy: ['准确度', ''],
  repeatability_mm: ['重复精度', 'mm'],
  resolution: ['分辨率', ''],
  bits: ['模拟输出位数', 'bit'],
  response_time: ['响应时间', ''],
  scan_freq_hz: ['开关频率', 'Hz'],
  spot_size_mm: ['光斑尺寸', ''],
  laser_class: ['激光等级', ''],
  wavelength_nm: ['波长', 'nm'],
  ambient_light_klx: ['抗环境光', 'klx'],
  connector: ['接头', ''],
  ip: ['防护等级', ''],
  housing_material: ['外壳材料', ''],
  package: ['封装', ''],
  protocol: ['协议', ''],
  dims: ['尺寸', ''],
  weight_g: ['重量', 'g'],
  temp_range: ['工作温度', ''],
  storage_temp_range: ['存储温度', ''],
  doc_url: ['资料链接', ''],
  doc_pdf: ['数据表 PDF', ''],
  diameter_mm: ['直径', 'mm'],
  width_mm: ['宽度', 'mm'],
  bore_mm: ['轴孔', 'mm'],
  load_kg: ['额定负载', 'kg'],
  module_type: ['模块类型', ''],
  current_A: ['电流', 'A'],
  led_count: ['灯珠数', '颗'],
  sensor: ['传感器', ''],
  mount: ['镜头接口', ''],
  material: ['材料', ''],
  // 旧生成器词表补齐（2026-11-09）；key 仍保留原字段名，便于追溯数据。
  absolute: ['绝对精度', ''],
  accel_bw: ['加计带宽', ''],
  accel_range_g: ['加计量程', 'g'],
  accel_range_opts: ['加计量程档位', ''],
  ambient_light_lux: ['抗环境光', 'lux'],
  angular_resolution: ['角分辨率', ''],
  attitude: ['姿态输出', ''],
  balance_current_ma: ['平衡电流', 'mA'],
  bandwidth_mhz: ['带宽', 'MHz'],
  battery: ['支持电池', ''],
  battery_type: ['电池类型', ''],
  bearing: ['轴承', ''],
  bias_instability: ['零偏不稳定性', ''],
  blind_m: ['盲区', 'm'],
  build_volume_mm: ['成型尺寸', 'mm'],
  canfd: ['CAN-FD', ''],
  capacity_f: ['单节容量', 'F'],
  capacity_mah: ['容量', 'mAh'],
  case: ['外壳', ''],
  category_cn: ['类目', ''],
  cell_range: ['支持串数', ''],
  cells: ['电池节数', ''],
  channel: ['通道数', ''],
  channels: ['通道数', ''],
  charge_current: ['最大充电电流', ''],
  charge_current_a: ['充电电流', 'A'],
  charge_power_w: ['充电功率', 'W'],
  chem: ['电芯', ''],
  chemistries: ['支持电芯', ''],
  chip_function: ['芯片类型', ''],
  clock_mhz: ['主频', 'MHz'],
  comm_upper: ['上位通信', ''],
  connector_wire: ['线长', ''],
  connectors: ['接口 / 连接器', ''],
  control_range_m: ['遥控距离', 'm'],
  cores: ['核心数', ''],
  coupon: ['优惠券 / 标签', ''],
  cpu: ['CPU', ''],
  cpu_arch: ['CPU 架构', ''],
  csi: ['CSI', ''],
  ctrl_khz: ['控制频率', 'kHz'],
  cuda: ['CUDA', ''],
  cuda_cores: ['CUDA 核', ''],
  current_cont_A: ['持续电流', 'A'],
  current_out: ['输出电流', 'A'],
  cut_area_mm: ['切割幅面', 'mm'],
  data_4d: ['4D 成像', ''],
  depth_resolution: ['深度分辨率', ''],
  discharge_current_a: ['放电电流', 'A'],
  discharge_power_w: ['放电功率', 'W'],
  discharge_rate_c: ['额定放电倍率', 'C'],
  display: ['显示', ''],
  driver_integrated: ['内置驱动', ''],
  effective_points_per_s: ['有效点频', '点/s'],
  energy_j: ['储能', 'J'],
  energy_wh: ['能量', 'Wh'],
  eth: ['以太网', ''],
  eye_safety: ['人眼安全等级', ''],
  features: ['功能特性', ''],
  feedback: ['反馈', ''],
  fetched_at: ['采集日期', ''],
  firmware: ['适用固件', ''],
  flash_kb: ['Flash', 'KB'],
  foc_axes: ['FOC 轴数', ''],
  focal_mm: ['焦距', 'mm'],
  fps_note: ['帧率说明', ''],
  freq: ['开关频率', ''],
  frequency_ghz: ['频段', 'GHz'],
  function_type: ['功能类型', ''],
  gpu: ['GPU', ''],
  gyro_bw_hz: ['陀螺带宽', 'Hz'],
  gyro_range_dps: ['陀螺量程', '°/s'],
  gyro_range_opts: ['陀螺量程档位', ''],
  hw_versions: ['硬件版本', ''],
  i_idle_mA: ['待机电流', 'mA'],
  i_noload_mA: ['空载电流', 'mA'],
  i_peak_A: ['峰值电流', 'A'],
  i_rated_A: ['额定电流', 'A'],
  i_rated_mA: ['额定电流', 'mA'],
  i_stall_A: ['堵转电流', 'A'],
  imu: ['板载 IMU', ''],
  imu_rate_hz: ['IMU 频率', 'Hz'],
  input_voltage: ['输入电压', ''],
  isolation: ['电气隔离', ''],
  baud_max_bps: ['最高波特率', 'bps'],
  debug_baud_bps: ['调试波特率', 'bps'],
  rs485_voltage_V: ['485 电平', 'V'],
  chip: ['核心芯片', ''],
  driver: ['驱动', ''],
  indicator: ['指示灯', ''],
  module_id: ['模块 ID', ''],
  frame_rate: ['CAN 帧率', ''],
  rated_power_W: ['额定功率', 'W'],
  noise_dB: ['噪音', 'dB'],
  insulation_class: ['绝缘等级', ''],
  insulation_voltage: ['绝缘电压', ''],
  storage_temp_C: ['储藏温度', '℃'],
  humidity: ['工作湿度', ''],
  jlc_library: ['SMT 库', ''],
  l_phase_uh: ['相电感', 'µH'],
  laser_power_w: ['激光功率', 'W'],
  lcsc_part: ['立创编号', ''],
  lead_time: ['交期', ''],
  license: ['开源协议', ''],
  limit_angle: ['限位角度', ''],
  logic: ['输入控制逻辑', ''],
  mag_range_gauss: ['磁力计量程', 'Gauss'],
  mass_g: ['质量', 'g'],
  materials: ['材料', ''],
  max_freq_mhz: ['最高频率', 'MHz'],
  max_speed_mms: ['最大速度', 'mm/s'],
  mcu: ['MCU', ''],
  motor: ['电机', ''],
  mount_orientations: ['安装方向数', ''],
  noise: ['噪声', ''],
  odr_hz: ['ODR', 'Hz'],
  odr_note: ['输出周期说明', ''],
  os: ['系统', ''],
  output: ['输出', ''],
  output_type: ['输出类型', ''],
  params: ['参数', ''],
  pcie: ['PCIe', ''],
  points_per_s: ['点频', '点/s'],
  polarity: ['输出极性', ''],
  pole_pairs: ['极对数', ''],
  power_idle_w: ['待机功耗', 'W'],
  power_note: ['功耗说明', ''],
  power_peak_w: ['峰值功耗', 'W'],
  price_lead: ['立推价', '元'],
  price_tiers: ['价格梯度（含税）', ''],
  protection: ['保护', ''],
  pwm: ['PWM 路数', ''],
  r_phase_ohm: ['相电阻', 'Ω'],
  ram_bw_gbs: ['内存带宽', 'GB/s'],
  ram_kb: ['RAM', 'KB'],
  ram_options: ['内存选项', ''],
  range_min_m: ['最小量程', 'm'],
  range_note: ['量程说明', ''],
  range_resolution: ['距离分辨率', ''],
  rated_torque_Nm: ['额定扭矩', 'N·m'],
  repo_license: ['仓库许可', ''],
  repo_urls: ['开源仓库', ''],
  rgb_fov: ['RGB 视场', ''],
  rgb_resolution: ['RGB 分辨率', ''],
  rgb_sensor: ['RGB 传感器', ''],
  rgb_shutter: ['RGB 快门', ''],
  ros2: ['ROS 2', ''],
  sample_rate_msps: ['采样率', 'MS/s'],
  sampling_hz: ['内部采样率', 'Hz'],
  scan: ['扫描方式', ''],
  shock_g: ['抗冲击', 'g'],
  slam_accuracy: ['SLAM 精度', ''],
  smart_features: ['智能功能', ''],
  speed_raw: ['原始速度标注', ''],
  speed_rpm: ['转速', 'rpm'],
  speed_s_60deg: ['速度', 's/60°'],
  spline: ['花键', ''],
  stall_torque_Nm: ['堵转扭矩', 'N·m'],
  stock: ['库存', ''],
  stock_lead: ['立推库存', ''],
  storage_gb: ['存储', 'GB'],
  switch_type: ['开关类型', ''],
  tags: ['标签', ''],
  temp_control: ['温控', ''],
  temp_max_C: ['最高温度', '℃'],
  temp_range_C: ['工作温度', '℃'],
  torque_mode: ['扭矩模式', ''],
  torque_raw: ['原始扭矩标注', ''],
  uart: ['UART 路数', ''],
  usb: ['USB', ''],
  usb_output: ['USB 输出', ''],
  v_charge_V: ['充电截止电压', 'V'],
  v_float: ['充电饱和电压', ''],
  voltage_in: ['工作电压', ''],
  voltage_max_V: ['最高电压', 'V'],
  voltage_out: ['输出电压', ''],
  voltage_range: ['电压范围', ''],
  waveform: ['波形', ''],
  wireless_charge_w: ['无线充电功率', 'W'],
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

// 数据里的口径枚举仍是英文（tau_basis / inertia_basis），展示时统一成中文。
// 只收词义明确的短值，避免误伤型号、协议名等专有名词。
const VALUE_LABELS: Record<string, string> = {
  peak: '峰值',
  rated: '额定',
  rotor: '电机侧',
  output: '输出侧',
  stall: '堵转',
  hold: '保持',
  '1pcs': '1 个',
  '2pcs': '2 个',
}

/** 数值最多保留 4 位有效数字：1.1604938271604938e-05 → 0.0000116。 */
function formatNumber(value: number): string {
  if (!Number.isFinite(value) || Number.isInteger(value)) return String(value)
  return String(Number(value.toPrecision(4)))
}

/** 统一值展示：null/空写「—」，布尔写是/否，枚举与数值归一，单位不重复追加。 */
export function formatSpecValue(value: unknown, unit = ''): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => formatSpecValue(item)).join('、') : '—'
  }
  if (typeof value === 'object') return JSON.stringify(value)
  const text = typeof value === 'number' ? formatNumber(value) : (VALUE_LABELS[String(value)] ?? String(value))
  return unit && !text.includes(unit) ? `${text} ${unit}` : text
}

export * from './ratingTags'
