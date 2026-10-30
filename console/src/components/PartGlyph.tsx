/**
 * PartGlyph — 按零件真实尺寸画的技术示意图。
 *
 * 为什么不用真照片：188 个件里只有极少数有可用的授权产品图，随便抓图会挂、
 * 会有版权问题、也无法离线。所以这里**用参数画**：
 *   - 关节电机：机身长径比来自真实的 l_mm / od_mm，谐波画得更细长、QDD 更扁
 *   - 板卡：接口位置固定，芯片大小按 SoC 名称哈希
 *   - 传感器：按 subtype 画不同形态
 *
 * 数据里补了 image_url 的真照片会优先用（见 PartCard）。
 * 配色来自厂商名的哈希，同一家的件看起来是一族。
 */

const HUE_OVERRIDE: Record<string, number> = {
  CubeMars: 205, '灵足 RobStride': 152, '达妙 DM': 28, MyActuator: 268,
  ZeroErr: 12, HEBI: 190, maxon: 340, Unitree: 96, SteadyWin: 42,
  NVIDIA: 118, Intel: 210, Raspberry: 350, Radxa: 24, '地平线 Horizon': 200,
  '算能 Sophgo': 275, Bosch: 168, 'TDK InvenSense': 300, Xsens: 45,
  Livox: 8, '速腾 RoboSense': 190, 'ams OSRAM': 130, 'MagnTek 麦歌恩': 250,
}

function hashHue(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360
  return h
}

export function hueOf(vendor: string): number {
  return HUE_OVERRIDE[vendor] ?? hashHue(vendor)
}

/** 把 OD/L 换算成画布上的宽高（保留真实比例，夹在可读范围内） */
function motorBox(od?: number, l?: number) {
  const W = 168
  const ratio = od && l ? Math.min(3.2, Math.max(0.42, l / od)) : 1.0
  const h = Math.max(30, Math.min(96, 58 * ratio))
  const w = Math.max(46, Math.min(132, 118 / Math.max(0.75, ratio * 0.85)))
  return { w, h, cx: W / 2, cy: 60 }
}

const f = (v: any, d = 0) => (typeof v === 'number' ? v : d)

export default function PartGlyph({ part, size = 180 }:
  { part: any; size?: number }) {
  // 配色走 CSS 变量：明暗切换时 SVG 自动跟着变，
  // 不需要重渲染，也不用往这里传 theme prop（见 index.css 的 --g-*）。
  const accent = 'var(--g-accent)'
  const accentDim = 'var(--g-accent-dim)'
  const body = 'var(--g-body)'
  const bodyLo = 'var(--g-body-lo)'
  const s = part.specs || {}
  const st = part.subtype
  const gid = `g-${part.id}`.replace(/[^a-zA-Z0-9-]/g, '')
  const uid = `u-${gid}`

  const shell = (children: React.ReactNode) => (
    <svg viewBox="0 0 168 120" width={size} height={size * (120 / 168)}
      style={{ display: 'block' }} aria-label={`${part.model} 示意图`}>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={body} />
          <stop offset="100%" stopColor={bodyLo} />
        </linearGradient>
        <linearGradient id={`${uid}-acc`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={accent} stopOpacity="0.85" />
          <stop offset="100%" stopColor={accentDim} stopOpacity="0.35" />
        </linearGradient>
        <radialGradient id={`${uid}-glow`} cx="50%" cy="45%" r="60%">
          <stop offset="0%" stopColor={accent} stopOpacity="0.10" />
          <stop offset="100%" stopColor={accent} stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="168" height="120" fill={`url(#${uid}-glow)`} />
      {children}
    </svg>
  )

  // ── 关节电机：圆柱机身 + 端面法兰 + 输出轴 ────────────────────────────
  if (part.category === 'actuator') {
    const { w, h, cx, cy } = motorBox(f(s.od_mm, 70), f(s.l_mm, 60))
    const rings = st === 'harmonic' ? 5 : st === 'planetary' ? 3 : 2
    const x0 = cx - w / 2
    const y0 = cy - h / 2
    const r = h / 2
    return shell(
      <g>
        {/* 机身 */}
        <rect x={x0} y={y0} width={w} height={h} rx={r * 0.55}
          fill={`url(#${gid})`} stroke={accentDim} strokeWidth="1.2" />
        {/* 散热/齿槽环 */}
        {Array.from({ length: rings }).map((_, i) => {
          const x = x0 + (w / (rings + 1)) * (i + 1)
          return <line key={i} x1={x} y1={y0 + 4} x2={x} y2={y0 + h - 4}
            stroke={accent} strokeOpacity={0.35} strokeWidth="1.6" />
        })}
        {/* 高光 */}
        <rect x={x0 + 3} y={y0 + 3} width={w - 6} height={h * 0.32} rx={r * 0.35}
          fill="#fff" opacity="0.55" />
        {/* 输出法兰 + 轴 */}
        <ellipse cx={x0} cy={cy} rx={r * 0.62} ry={r * 0.86}
          fill={`url(#${uid}-acc)`} stroke={accent} strokeWidth="1.1" />
        <circle cx={x0} cy={cy} r={r * 0.22} fill={bodyLo} stroke={accent} strokeWidth="1" />
        {/* 出线 */}
        <path d={`M ${x0 + w * 0.25} ${y0 + h} q 0 10 12 12`} stroke={accent}
          strokeWidth="2" fill="none" opacity="0.55" strokeLinecap="round" />
        {/* 谐波：机身上的柔轮齿 */}
        {st === 'harmonic' &&
          Array.from({ length: 14 }).map((_, i) => {
            const x = x0 + 8 + i * ((w - 16) / 13)
            return <line key={i} x1={x} y1={y0 + 1} x2={x} y2={y0 + 6}
              stroke={accent} strokeOpacity="0.5" strokeWidth="1.2" />
          })}
      </g>
    )
  }

  // ── 上位机 / SBC：板卡 + 芯片 + 接口 ──────────────────────────────────
  if (part.category === 'controller_high') {
    const w = 116, h = 74, x0 = 26, y0 = 24
    const hasCuda = !!s.cuda_cores
    return shell(
      <g>
        <rect x={x0} y={y0} width={w} height={h} rx="6" fill={`url(#${gid})`}
          stroke={accentDim} strokeWidth="1.2" />
        {/* 散热片（有 CUDA 的板子都有） */}
        {hasCuda && (
          <g opacity="0.9">
            <rect x={x0 + 12} y={y0 + 8} width={w * 0.46} height={h * 0.44} rx="3"
              fill={bodyLo} stroke={accent} strokeWidth="0.8" />
            {Array.from({ length: 6 }).map((_, i) => (
              <line key={i} x1={x0 + 15} y1={y0 + 12 + i * 4.6}
                x2={x0 + 12 + w * 0.44} y2={y0 + 12 + i * 4.6}
                stroke={accent} strokeOpacity="0.45" strokeWidth="1.2" />
            ))}
          </g>
        )}
        {/* 接口排 */}
        <rect x={x0 + w - 18} y={y0 + 8} width="12" height="8" rx="1.5"
          fill={`url(#${uid}-acc)`} />
        <rect x={x0 + w - 18} y={y0 + 22} width="12" height="6" rx="1.5"
          fill={accentDim} />
        <rect x={x0 + w - 18} y={y0 + 34} width="12" height="6" rx="1.5"
          fill={accentDim} />
        {/* GPIO 排针 */}
        {Array.from({ length: 14 }).map((_, i) => (
          <rect key={i} x={x0 + 6 + i * 3.6} y={y0 + h - 9} width="2" height="5"
            fill={accent} opacity="0.5" />
        ))}
        {/* 卡缘 */}
        <rect x={x0 + 20} y={y0 + h - 4} width={w - 40} height="3" rx="1"
          fill={accent} opacity="0.35" />
      </g>
    )
  }

  // ── 下位机 / MCU：小板 + 主控 + 端子 ──────────────────────────────────
  if (part.category === 'controller_low') {
    const w = 96, h = 62, x0 = 36, y0 = 30
    return shell(
      <g>
        <rect x={x0} y={y0} width={w} height={h} rx="5" fill={`url(#${gid})`}
          stroke={accentDim} strokeWidth="1.2" />
        {/* 主控芯片 */}
        <rect x={x0 + 26} y={y0 + 14} width="40" height="30" rx="2"
          fill={bodyLo} stroke={accent} strokeWidth="1" />
        {Array.from({ length: 8 }).map((_, i) => (
          <g key={i}>
            <rect x={x0 + 28 + i * 4.6} y={y0 + 9} width="2" height="4" fill={accent} opacity="0.6" />
            <rect x={x0 + 28 + i * 4.6} y={y0 + 45} width="2" height="4" fill={accent} opacity="0.6" />
          </g>
        ))}
        {/* CAN 端子 */}
        <rect x={x0 - 10} y={y0 + 8} width="9" height="12" rx="1.5"
          fill={`url(#${uid}-acc)`} />
        <rect x={x0 - 10} y={y0 + 26} width="9" height="12" rx="1.5"
          fill={accentDim} />
        {/* 电解电容 */}
        <circle cx={x0 + w - 14} cy={y0 + h - 14} r="8" fill={bodyLo}
          stroke={accent} strokeWidth="1" opacity="0.9" />
      </g>
    )
  }

  // ── 传感器 ────────────────────────────────────────────────────────────
  if (part.category === 'sensor') {
    if (st === 'camera') {
      return shell(
        <g>
          <rect x="34" y="30" width="100" height="60" rx="9" fill={`url(#${gid})`}
            stroke={accentDim} strokeWidth="1.2" />
          {[62, 106].map((cx, i) => (
            <g key={i}>
              <circle cx={cx} cy="60" r="19" fill={bodyLo} stroke={accent} strokeWidth="1.2" />
              <circle cx={cx} cy="60" r="12" fill={`url(#${uid}-acc)`} />
              <circle cx={cx} cy="60" r="5" fill="var(--g-lens)" />
              <circle cx={cx - 4} cy="56" r="2.4" fill="#fff" opacity="0.5" />
            </g>
          ))}
        </g>
      )
    }
    if (st === 'lidar') {
      return shell(
        <g>
          <ellipse cx="84" cy="88" rx="46" ry="13" fill={bodyLo} stroke={accentDim} strokeWidth="1" />
          <rect x="38" y="46" width="92" height="42" rx="14" fill={`url(#${gid})`}
            stroke={accentDim} strokeWidth="1.2" />
          <rect x="48" y="54" width="72" height="12" rx="6" fill={`url(#${uid}-acc)`} />
          {Array.from({ length: 5 }).map((_, i) => (
            <line key={i} x1="60" y1={72 + i * 3} x2="108" y2={72 + i * 3}
              stroke={accent} strokeOpacity="0.25" strokeWidth="1" />
          ))}
          <ellipse cx="84" cy="46" rx="46" ry="12" fill={body} stroke={accent} strokeWidth="1.2" />
        </g>
      )
    }
    if (st === 'imu' || st === 'encoder') {
      const squares = st === 'imu'
      return shell(
        <g>
          <rect x="54" y="36" width="60" height="48" rx="4" fill={`url(#${gid})`}
            stroke={accentDim} strokeWidth="1.2" />
          {Array.from({ length: squares ? 7 : 0 }).map((_, i) => (
            <g key={i}>
              <rect x={56 + i * 8} y="30" width="3" height="7" fill={accent} opacity="0.6" />
              <rect x={56 + i * 8} y="83" width="3" height="7" fill={accent} opacity="0.6" />
            </g>
          ))}
          <rect x="70" y="52" width="28" height="20" rx="2" fill={bodyLo}
            stroke={accent} strokeWidth="0.9" />
          <circle cx="84" cy="62" r="3" fill={accent} opacity="0.8" />
          {st === 'encoder' && (
            <circle cx="84" cy="60" r="21" fill="none" stroke={accent}
              strokeWidth="1.4" strokeDasharray="4 3" opacity="0.7" />
          )}
        </g>
      )
    }
    // force / 其他
    return shell(
      <g>
        <circle cx="84" cy="60" r="34" fill={`url(#${gid})`} stroke={accentDim} strokeWidth="1.3" />
        <circle cx="84" cy="60" r="22" fill="none" stroke={accent} strokeWidth="1.2" opacity="0.7" />
        {[0, 90, 180, 270].map(a => (
          <line key={a} x1={84 + 22 * Math.cos(a * Math.PI / 180)}
            y1={60 + 22 * Math.sin(a * Math.PI / 180)}
            x2={84 + 34 * Math.cos(a * Math.PI / 180)}
            y2={60 + 34 * Math.sin(a * Math.PI / 180)}
            stroke={accent} strokeOpacity="0.5" strokeWidth="1.4" />
        ))}
        <circle cx="84" cy="60" r="6" fill={accent} opacity="0.85" />
      </g>
    )
  }

  // 兜底
  return shell(<rect x="44" y="34" width="80" height="52" rx="8"
    fill={`url(#${gid})`} stroke={accentDim} strokeWidth="1.2" />)
}
