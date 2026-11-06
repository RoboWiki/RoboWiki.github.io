/**
 * 四层能力骨架：机械结构 → 电气与嵌入式 → 算法控制 → 系统集成。
 *
 * 这是站点的信息架构主干，不是营销文案：每个层都绑定到具体品类、
 * 指南文章与整机，避免「四层」只停留在首页的一句话。
 */
export type LayerId = 'mechanical' | 'electrical' | 'algorithm' | 'system'

export type Layer = {
  id: LayerId
  index: string
  name: string
  en: string
  tagline: string
  desc: string
  /** 该层覆盖的部件品类 id（对应 catalog.categories[].id） */
  categories: string[]
  /** 该层相关的指南 slug（对应 content/learn/*.md 的文件名） */
  guides: string[]
  /** 该层在实现阶段要回答的关键问题 */
  questions: string[]
  /** tailwind 令牌色类名 */
  tone: string
  hint: string
}

export const LAYERS: Layer[] = [
  {
    id: 'mechanical',
    index: '01',
    name: '机械结构',
    en: 'Mechanical',
    tagline: '传动、构型与材料边界',
    desc: '从自由度与载荷倒推结构，先把传动链、材料与加工工艺的边界算清楚，再谈装配。',
    categories: ['actuator', 'servo', 'connector'],
    guides: ['selection-order', 'motor-specs'],
    questions: ['需要多大扭矩与转速余量？', '传动方案与背隙能不能接受？', '材料与工艺的能力边界在哪？'],
    tone: 'text-layer-mech',
    hint: '关节电机、舵机与连接结构件',
  },
  {
    id: 'electrical',
    index: '02',
    name: '电气与嵌入式',
    en: 'Electrical & Embedded',
    tagline: '供电、驱动与总线的真实余量',
    desc: '按电流回路与通信拓扑设计电气，把电池、电调、主控与总线的余量写成可核对的值。',
    categories: ['controller_high', 'controller_low', 'esc', 'battery', 'chip', 'module', 'open_hw', 'remote_controller'],
    guides: ['control-chain'],
    questions: ['峰值电流与母线压降够不够？', '总线带宽与节点数上限是多少？', '主控算力与实时性是否够用？'],
    tone: 'text-layer-elec',
    hint: '主控、电调、电池、芯片与开源硬件',
  },
  {
    id: 'algorithm',
    index: '03',
    name: '算法控制',
    en: 'Algorithm & Control',
    tagline: '感知、估计与控制的选型依赖',
    desc: '算法决定传感器的精度与频率要求，反过来传感器也限制了能跑什么算法。',
    categories: ['sensor', 'imu', 'lidar', 'camera'],
    guides: ['control-chain', 'open-source-reading'],
    questions: ['需要多高的更新率与精度？', '标定与噪声模型怎么验证？', '算力预算能不能覆盖整套估计？'],
    tone: 'text-layer-algo',
    hint: 'IMU、激光雷达、深度相机与传感器',
  },
  {
    id: 'system',
    index: '04',
    name: '系统集成',
    en: 'System Integration',
    tagline: '整机方案、联调与迭代',
    desc: '把前三个层的选择装进同一台机器，用整机方案、联调记录与迭代复盘收口。',
    categories: [],
    guides: ['open-source-reading'],
    questions: ['整机质量与重心是否可接受？', '各层预算冲突时砍谁？', '出问题能不能定位到具体一层？'],
    tone: 'text-layer-sys',
    hint: '整机方案、软件工具与渠道',
  },
]

export const LAYER_BY_ID = Object.fromEntries(LAYERS.map(l => [l.id, l])) as Record<LayerId, Layer>

/** 品类 → 层级 的反查表，用于在部件页标注「属于哪一层」。 */
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
