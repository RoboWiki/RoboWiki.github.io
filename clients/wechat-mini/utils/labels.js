// 参数展示名。与主站 pipeline/build_site.py 的 SPEC_LABEL 保持同一口径；
// 小程序只负责显示，不改写数据，也不推断缺失值。
const PART = {
  tau_peak_Nm: '峰值扭矩 (N·m)', tau_rated_Nm: '额定扭矩 (N·m)',
  tau_basis: '扭矩口径', speed_noload_rpm: '空载转速 (rpm)',
  speed_rated_rpm: '额定转速 (rpm)', gear: '减速比',
  mass_kg: '质量 (kg)', od_mm: '外径 (mm)', l_mm: '长度 (mm)',
  rotor_inertia_kgm2: '转子惯量 (kg·m²)', inertia_basis: '惯量口径',
  armature_kgm2: '折算惯量 (kg·m²)', voltage_V: '额定电压 (V)',
  voltage_range_V: '电压范围 (V)', kt_Nm_per_A: '转矩常数 (N·m/A)',
  r_phase_ohm: '相电阻 (Ω)', l_phase_uh: '相电感 (µH)',
  pole_pairs: '极对数', i_peak_A: '峰值电流 (A)', i_rated_A: '额定电流 (A)',
  encoder: '编码器', comm: '通信', driver_integrated: '内置驱动',
  ip: '防护等级', frictionloss_Nm: '摩擦 (N·m)',
  damping_Nms_rad: '阻尼 (N·m·s/rad)', soc: 'SoC',
  cuda_cores: 'CUDA 核', npu_tops: 'NPU (TOPS)', ram_gb: '内存 (GB)',
  power_max_w: '峰值功耗 (W)', mcu: 'MCU', can: 'CAN 路数',
  canfd: 'CAN-FD', current_loop_khz: '电流环 (kHz)',
  voltage_max_V: '最高电压 (V)', foc_axes: 'FOC 轴数',
  iface: '接口', bits: '分辨率 (bit)', fps: '帧率 (fps)',
  odr_hz: 'ODR (Hz)', range_m: '量程 (m)', depth_range_m: '深度量程 (m)',
  gyro_range_dps: '陀螺量程 (°/s)', gyro_range_opts: '陀螺量程档位',
  gyro_bw_hz: '陀螺带宽 (Hz)', accel_range_g: '加计量程 (g)',
  accel_range_opts: '加计量程档位', accel_bw: '加计带宽',
  sampling_hz: '内部采样率 (Hz)', attitude: '姿态输出',
  temp_control: '温控', temp_range: '工作温度', temp_range_C: '工作温度',
  dims: '尺寸', mount_orientations: '安装方向数', hw_versions: '硬件版本',
  firmware: '适用固件', odr_note: '输出周期说明', fov: '视场',
  resolution: '分辨率', points_per_s: '点频 (点/s)',
  current_cont_A: '持续电流 (A)', current_peak_A: '峰值电流 (A)',
  ctrl_khz: '控制频率 (kHz)', battery: '支持电池',
  voltage_in_V: '额定电压 (V)', clock_mhz: '主频 (MHz)',
  flash_kb: 'Flash (KB)', ram_kb: 'RAM (KB)', can_speed_mbps: 'CAN 速率 (Mbps)',
  ram_bw_gbs: '带宽 (GB/s)', channels: '通道数', frequency_ghz: '频段 (GHz)',
  control_range_m: '遥控距离 (m)', isolation: '电气隔离', connector: '接头',
  gpu: 'GPU', package: '封装', protection: '保护', pwm: 'PWM 路数',
  uart: 'UART 路数', imu: '板载 IMU',
  // 连接器
  contact_layout: '针位布局', current_rated_A: '额定电流 (A)',
  voltage_rated_V: '额定电压 (V)', wire_awg: '适线 (AWG)', awg: '线规 (AWG)',
  positions: '位数', pitch_mm: '间距 (mm)', lock_type: '锁扣',
  mount_type: '安装方式', current_basis: '电流口径', polarity: '极性',
  lcsc_part: '立创编号', doc_url: '资料', doc_pdf: '手册',
  // 芯片 / 模块 / 电池
  chip_function: '芯片功能', logic: '逻辑', switch_type: '开关类型',
  output_type: '输出类型', function_type: '功能类型', battery_type: '电池类型',
  chem: '化学体系', capacity_Ah: '容量 (Ah)', voltage_nominal_V: '标称电压 (V)',
  energy_Wh: '能量 (Wh)', discharge_C: '放电倍率 (C)', charge_C: '充电倍率 (C)',
  pulse_A: '脉冲电流 (A)', internal_mohm: '内阻 (mΩ)', cycles: '循环寿命',
  // 立创/芯片条目里常见的结构化字段
  params: '参数', price_tiers: '价格阶梯', price_lead: '起步价',
  stock: '库存', stock_lead: '库存交期', lead_time: '交期',
  jlc_library: '立创库', coupon: '优惠', category_cn: '类别',
  // 通用
  image_url: '产品图', image_source: '图片来源', notes: '备注', url: '来源',
}

const DERIVED = {
  torque_density_Nm_per_kg: '扭矩密度 (N·m/kg)',
  peak_rated_ratio: '峰值/额定',
  speed_noload_rad_s: '空载角速度 (rad/s)',
  peak_power_W: '峰值功率 (W)',
  envelope_cm3: '包络体积 (cm³)',
  armature_check_kgm2: '惯量校验值 (kg·m²)',
  armature_ok: '惯量不变量通过',
}

const MATERIAL = {
  density_g_cm3: '密度 (g/cm³)', modulus_GPa: '弹性模量 (GPa)',
  tensile_MPa: '抗拉强度 (MPa)', yield_MPa: '屈服强度 (MPa)',
  elongation_pct: '断裂延伸率 (%)', hardness: '硬度',
  service_temp_C: '长期工作温度 (°C)', low_temp_C: '低温下限 (°C)',
  melting_C: '熔点 (°C)', thermal_cond_W_mK: '导热系数 (W/(m·K))',
  cte_um_mK: '线膨胀系数 (µm/(m·K))', tolerance_mm: '可达公差 (mm)',
  surface_ra_um: '表面粗糙度 Ra (µm)', layer_height_mm: '层高 (mm)',
  min_wall_mm: '最小壁厚 (mm)', max_size: '最大尺寸',
  cost_level: '成本档', lead_time: '参考交期', price_level: '价格档',
  stock_form: '供货形态', colors: '常见颜色', finish: '表面处理',
  machinability: '可加工性', weldability: '可焊性', recyclable: '可回收',
}

function humanize(key) {
  return String(key || '')
    .replace(/_/g, ' ')
    .replace(/\bNm\b/g, 'N·m')
    .replace(/\bkgm2\b/g, 'kg·m²')
}

function partLabel(key) {
  return PART[key] || humanize(key)
}

function materialLabel(key) {
  return MATERIAL[key] || humanize(key)
}

module.exports = { PART, DERIVED, MATERIAL, partLabel, materialLabel, humanize }
