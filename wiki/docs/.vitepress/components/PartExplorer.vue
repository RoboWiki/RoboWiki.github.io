<script setup lang="ts">
/**
 * 部件库：搜索 / 分类 / 厂商 / 排序 / 对比，全在浏览器里跑，没有一个 API 请求。
 *
 * 卡片按「以后要扩到各类机器人部件」来设计：图片 → 品牌型号 → 4 个关键参数 →
 * 价格与优惠 → 平均评分。关键参数按品类取，不是写死关节电机那四个。
 *
 * 术语：卡片上用「转子惯量」而不是 armature —— 对读者友好；但部件页里会写清
 * 它是**折算到输出端**的等效惯量（与电机本体的转子惯量差 N² 倍），口径不丢。
 */
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

interface Offer {
  title: string | null
  kind: string | null
  price: number | null
  condition: string | null
  url: string | null
  expires: string | null
  demo: boolean
}

interface Part {
  id: string
  slug: string
  category: string
  subtype: string
  subtypeLabel: string
  vendor: string
  model: string
  tier: string
  verified: boolean
  price: number | null
  image: string | null
  rating: { avg: number | null; count: number }
  offer: Offer | null
  tauPeak: number | null
  tauRated: number | null
  gear: number | null
  mass: number | null
  armature: number | null
  rpm: number | null
  soc: string | null
  npuTops: number | null
  ramGb: number | null
  mcu: string | null
  can: number | null
  iface: string | null
  bits: number | null
  odrHz: number | null
  fps: number | null
  depthRange: string | null
  rangeM: number | null
  od: number | null
  len: number | null
  notes: string
  specs: Record<string, any>
}

const all = ref<Part[]>([])
const loading = ref(true)
const fail = ref('')

const q = ref('')
const cat = ref('actuator')
const vendor = ref('')
const sort = ref<'rating' | 'peak' | 'armature' | 'mass' | 'price' | 'vendor'>('peak')
const order = ref<'desc' | 'asc'>('desc')
const picked = ref<Part[]>([])
const detail = ref<Part | null>(null)

const CATS = [
  { v: 'actuator', t: '关节电机' },
  { v: 'controller_high', t: '上位机' },
  { v: 'controller_low', t: '下位机' },
  { v: 'structure', t: '机械结构' },
  { v: 'imu', t: 'IMU' },
  { v: 'lidar', t: '激光雷达' },
  { v: 'camera', t: '深度相机' },
  { v: 'battery', t: '电池' },
  { v: 'wiring', t: '线束' },
  { v: 'module', t: '其余模块' },
]

const SORTS = [
  { v: 'peak', t: '峰值扭矩' },
  { v: 'rating', t: '评分' },
  { v: 'armature', t: '转子惯量' },
  { v: 'mass', t: '质量' },
  { v: 'price', t: '价格' },
  { v: 'vendor', t: '品牌' },
] as const

onMounted(async () => {
  try {
    const r = await fetch(withBase('/catalog.json'))
    if (!r.ok) throw new Error(String(r.status))
    all.value = (await r.json()).parts
  } catch (e: any) {
    fail.value = `部件库加载失败（${e.message}）`
  } finally {
    loading.value = false
  }
})

const catCount = (v: string) => all.value.filter(p => p.category === v).length
const vendors = computed(() =>
  [...new Set(all.value.filter(p => p.category === cat.value).map(p => p.vendor))].sort())

const SORT_KEY: Record<string, (p: Part) => any> = {
  peak: p => p.tauPeak,
  rating: p => p.rating.avg,
  armature: p => p.armature,
  mass: p => p.mass,
  price: p => p.offer?.price ?? p.price,
  vendor: p => p.vendor,
}

const rows = computed(() => {
  const key = SORT_KEY[sort.value]
  let out = all.value.filter(
    p => p.category === cat.value
      && (!vendor.value || p.vendor === vendor.value)
      && (!q.value || `${p.model} ${p.vendor} ${p.subtypeLabel}`
        .toLowerCase().includes(q.value.toLowerCase())),
  )
  out = [...out].sort((a, b) => {
    const va = key(a), vb = key(b)
    // null 永远排最后：缺失就是缺失，不该混进排序
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb), 'zh')
    return order.value === 'desc' ? -cmp : cmp
  })
  return out
})

function num(v: any, d = 3): string {
  if (v == null || v === '') return '—'
  const n = Number(v)
  if (!isFinite(n)) return String(v)
  const a = Math.abs(n)
  if (a && (a < 0.001 || a >= 100000)) return n.toExponential(1)
  return String(Number(n.toFixed(d)))
}

const money = (v: number | null) => (v == null ? null : `¥${Math.round(v).toLocaleString('en-US')}`)

/** 卡片上的 4 个关键参数 —— 按品类取，不是写死关节电机那四个 */
function chips(p: Part): { k: string; v: string }[] {
  const out: { k: string; v: string }[] = []
  const push = (k: string, v: any, unit = '') => {
    if (v != null && v !== '') out.push({ k, v: `${v}${unit}` })
  }
  if (p.category === 'actuator') {
    push('峰值', num(p.tauPeak), ' N·m')
    push('减速比', num(p.gear), ':1')
    push('质量', num(p.mass), ' kg')
    if (p.armature != null) push('转子惯量', num(p.armature))
  } else if (p.category === 'controller_high') {
    push('SoC', p.soc)
    push('NPU', num(p.npuTops), ' TOPS')
    push('内存', num(p.ramGb), ' GB')
  } else if (p.category === 'controller_low') {
    push('MCU', p.mcu)
    push('CAN', p.can, ' 路')
    if (p.specs?.current_loop_khz) push('电流环', num(p.specs.current_loop_khz), ' kHz')
  } else if (p.category === 'imu') {
    push('ODR', num(p.odrHz), ' Hz')
    push('接口', p.iface)
  } else if (p.category === 'lidar' || p.category === 'camera') {
    push('量程', p.rangeM ?? p.depthRange, p.rangeM ? ' m' : '')
    push('帧率', num(p.fps), ' fps')
  } else {
    push('接口', p.iface)
    push('分辨率', p.bits, ' bit')
  }
  return out.slice(0, 4)
}

function toggleCompare(p: Part) {
  const i = picked.value.findIndex(x => x.id === p.id)
  if (i >= 0) picked.value.splice(i, 1)
  else if (picked.value.length < 3) picked.value.push(p)
}
const isPicked = (p: Part) => picked.value.some(x => x.id === p.id)

const COMPARE_FIELDS: { t: string; f: (p: Part) => string }[] = [
  { t: '峰值扭矩', f: p => num(p.tauPeak) },
  { t: '额定扭矩', f: p => num(p.tauRated) },
  { t: '减速比', f: p => num(p.gear) },
  { t: '质量', f: p => num(p.mass) },
  { t: '转子惯量', f: p => num(p.armature) },
  { t: '空载转速', f: p => num(p.rpm) },
  { t: '价格', f: p => money(p.offer?.price ?? p.price) ?? '询价' },
  { t: '评分', f: p => (p.rating.avg == null ? '暂无' : `${p.rating.avg} (${p.rating.count})`) },
]

function glyphBox(p: Part) {
  const w = p.od && p.len ? Math.min(2.6, Math.max(0.5, p.len / p.od)) : 1
  return { h: Math.max(16, Math.min(44, 24 * w)), w: Math.max(26, Math.min(72, 58 / Math.max(0.8, w * 0.9))) }
}
</script>

<template>
  <div class="pd">
    <p v-if="loading" class="pd-muted">加载部件库…</p>
    <p v-else-if="fail" class="pd-muted">{{ fail }}</p>

    <template v-else>
      <!-- 分类 -->
      <div class="pd-row">
        <button v-for="c in CATS" :key="c.v"
                :class="['pd-chip', cat === c.v ? 'on' : '', catCount(c.v) ? '' : 'empty']"
                :title="catCount(c.v) ? `${catCount(c.v)} 件` : '还没有收录（没有可信来源，不编数据）'"
                @click="cat = c.v; vendor = ''; q = ''">
          {{ c.t }}<span class="pd-n">{{ catCount(c.v) || '—' }}</span>
        </button>
      </div>

      <!-- 工具条 -->
      <div class="pd-row">
        <input v-model="q" class="pd-input" placeholder="搜型号 / 品牌 / 类型" />
        <select v-model="sort" class="pd-sel">
          <option v-for="s in SORTS" :key="s.v" :value="s.v">按{{ s.t }}</option>
        </select>
        <button class="pd-btn" @click="order = order === 'desc' ? 'asc' : 'desc'">
          {{ order === 'desc' ? '↓ 降序' : '↑ 升序' }}
        </button>
        <span class="pd-sep" />
        <button v-for="v in vendors" :key="v"
                :class="['pd-chip', 'sm', vendor === v ? 'on' : '']"
                @click="vendor = vendor === v ? '' : v">{{ v }}</button>
        <span class="pd-count">{{ rows.length }} 件</span>
      </div>

      <!-- 对比 -->
      <div v-if="picked.length" class="pd-compare">
        <div class="pd-compare-head">
          对比 {{ picked.length }} / 3
          <button class="pd-link" @click="picked = []">清空</button>
        </div>
        <table>
          <tr><th></th><th v-for="p in picked" :key="p.id">{{ p.model }}</th></tr>
          <tr v-for="f in COMPARE_FIELDS" :key="f.t">
            <td class="pd-k">{{ f.t }}</td>
            <td v-for="p in picked" :key="p.id">{{ f.f(p) }}</td>
          </tr>
        </table>
      </div>

      <!-- 卡片 -->
      <div class="pd-grid">
        <article v-for="p in rows" :key="p.id" class="card">
          <a class="card-img" :href="withBase('/parts/' + p.category + '/' + p.slug)">
            <img v-if="p.image" :src="withBase(p.image)" :alt="p.model" loading="lazy" />
            <svg v-else viewBox="0 0 120 74" aria-hidden="true">
              <rect x="6" y="6" width="108" height="62" rx="7"
                    fill="var(--vp-c-bg-soft)" stroke="var(--vp-c-divider)" />
              <rect :x="60 - glyphBox(p).w / 2" :y="37 - glyphBox(p).h / 2"
                    :width="glyphBox(p).w" :height="glyphBox(p).h" rx="5"
                    fill="var(--vp-c-brand-soft)" stroke="var(--vp-c-brand-1)" />
            </svg>
            <span :class="['card-tier', p.tier === 'A' ? 'a' : '']">{{ p.tier }}{{ p.verified ? ' ✓' : '' }}</span>
            <span v-if="p.offer?.price != null" class="card-promo">优惠</span>
          </a>

          <div class="card-body">
            <a class="card-model" :href="withBase('/parts/' + p.category + '/' + p.slug)">{{ p.model }}</a>
            <div class="card-vendor">{{ p.vendor }}<span v-if="p.subtypeLabel"> · {{ p.subtypeLabel }}</span></div>

            <div class="card-chips">
              <span v-for="c in chips(p)" :key="c.k"><b>{{ c.k }}</b>{{ c.v }}</span>
            </div>

            <div class="card-foot">
              <div class="card-price">
                <template v-if="p.offer?.price != null">
                  <span class="promo">{{ money(p.offer.price) }}</span>
                  <s v-if="p.price" class="orig">{{ money(p.price) }}</s>
                </template>
                <template v-else-if="p.price">{{ money(p.price) }}</template>
                <span v-else class="ask">询价</span>
              </div>
              <div class="card-rate">
                <template v-if="p.rating.avg != null">
                  <span class="stars">★</span>{{ p.rating.avg.toFixed(1) }}
                  <span class="cnt">({{ p.rating.count }})</span>
                </template>
                <span v-else class="cnt">暂无评分</span>
              </div>
            </div>

            <div class="card-acts">
              <button class="pd-link" @click="toggleCompare(p)">{{ isPicked(p) ? '取消对比' : '对比' }}</button>
              <button class="pd-link" @click="detail = p">全部参数</button>
            </div>
          </div>
        </article>
      </div>

      <p v-if="!rows.length" class="pd-muted" style="padding:2rem 0;text-align:center">
        {{ catCount(cat) ? '没有符合条件的部件' : '这一类还没有收录 —— 没有可信来源，宁缺不编' }}
      </p>

      <!-- 全部参数 -->
      <div v-if="detail" class="pd-modal" @click.self="detail = null">
        <div class="pd-panel">
          <div class="pd-panel-head">
            <b>{{ detail.model }}</b>
            <span class="pd-muted">{{ detail.vendor }}</span>
            <button class="pd-link" @click="detail = null">关闭</button>
          </div>
          <table class="pd-specs">
            <tr v-for="(v, k) in detail.specs" :key="k">
              <td class="pd-k">{{ k }}</td>
              <td>{{ num(v) }}</td>
            </tr>
          </table>
          <p v-if="detail.offer" class="pd-offer">
            <b>{{ detail.offer.title }}</b> —— {{ detail.offer.condition }}
            <span v-if="detail.offer.expires">（至 {{ detail.offer.expires }}）</span>
          </p>
          <a class="pd-link" :href="withBase('/parts/' + detail.category + '/' + detail.slug)">
            打开部件页（来源 / 选型指标 / 使用建议 / 评分）→
          </a>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.pd { margin-top: 0.4rem; }
.pd-muted { color: var(--vp-c-text-3); font-size: 0.85rem; }
.pd-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin-bottom: 0.6rem; }
.pd-input, .pd-sel {
  font-size: 0.82rem; padding: 0.36rem 0.7rem; border-radius: 999px;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg);
  color: var(--vp-c-text-1); outline: none;
}
.pd-input { width: 200px; }
.pd-input:focus, .pd-sel:focus { border-color: var(--vp-c-brand-1); }
.pd-btn {
  font-size: 0.8rem; padding: 0.36rem 0.75rem; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2);
}
.pd-chip {
  font-size: 0.8rem; padding: 0.3rem 0.7rem; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2);
}
.pd-chip.sm { font-size: 0.75rem; padding: 0.22rem 0.55rem; }
.pd-chip.on {
  border-color: var(--vp-c-brand-1); background: var(--vp-c-brand-1); color: #fff; font-weight: 600;
}
.pd-chip.empty { border-style: dashed; color: var(--vp-c-text-3); }
.pd-n { margin-left: 0.35rem; opacity: 0.6; font-variant-numeric: tabular-nums; }
.pd-sep { width: 1px; height: 18px; background: var(--vp-c-divider); margin: 0 0.25rem; }
.pd-count { margin-left: auto; font-size: 0.78rem; color: var(--vp-c-text-3); }

/* 卡片网格：铺满宽度，列数随窗口自适应 */
.pd-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(212px, 1fr));
  gap: 0.75rem;
}
.card {
  display: flex; flex-direction: column; overflow: hidden;
  border: 1px solid var(--vp-c-divider); border-radius: 10px;
  background: var(--vp-c-bg);
  transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
}
.card:hover {
  transform: translateY(-2px); border-color: var(--vp-c-brand-1);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}
.card-img {
  position: relative; display: flex; align-items: center; justify-content: center;
  height: 112px; background: var(--vp-c-bg-alt);
  border-bottom: 1px solid var(--vp-c-divider);
}
.card-img img {
  max-height: 96px; max-width: 86%; object-fit: contain; mix-blend-mode: multiply;
}
html.dark .card-img img { mix-blend-mode: normal; background: #fff; border-radius: 4px; padding: 2px; }
.card-img svg { width: 74%; height: auto; }
.card-tier {
  position: absolute; top: 6px; right: 6px; font-size: 0.62rem; font-weight: 700;
  padding: 1px 5px; border-radius: 999px;
  background: var(--vp-c-default-soft); color: var(--vp-c-text-2);
}
.card-tier.a { background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); }
.card-promo {
  position: absolute; top: 6px; left: 6px; font-size: 0.62rem; font-weight: 700;
  padding: 1px 5px; border-radius: 999px; background: #a06a00; color: #fff;
}

.card-body { padding: 0.55rem 0.65rem 0.6rem; display: flex; flex-direction: column; gap: 0.28rem; }
.card-model {
  font-size: 0.88rem; font-weight: 700; color: var(--vp-c-text-1); text-decoration: none;
  line-height: 1.3;
}
.card-model:hover { color: var(--vp-c-brand-1); }
.card-vendor { font-size: 0.71rem; color: var(--vp-c-text-3); }

.card-chips { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 6px; margin-top: 0.15rem; }
.card-chips span {
  font-size: 0.68rem; color: var(--vp-c-text-2);
  font-variant-numeric: tabular-nums; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}
.card-chips b { color: var(--vp-c-text-3); font-weight: 500; margin-right: 3px; }

.card-foot {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-top: 0.4rem; padding-top: 0.4rem; border-top: 1px solid var(--vp-c-divider);
}
.card-price { display: flex; align-items: baseline; gap: 0.3rem; font-variant-numeric: tabular-nums; }
.card-price .promo { font-size: 0.88rem; font-weight: 700; color: #a06a00; }
html.dark .card-price .promo { color: #e0b159; }
.card-price .orig { font-size: 0.7rem; color: var(--vp-c-text-3); }
.card-price { font-size: 0.82rem; color: var(--vp-c-text-1); }
.card-price .ask { color: var(--vp-c-text-3); font-size: 0.74rem; }
.card-rate { font-size: 0.76rem; color: var(--vp-c-text-1); font-variant-numeric: tabular-nums; }
.card-rate .stars { color: #d97706; margin-right: 2px; }
html.dark .card-rate .stars { color: #e0b159; }
.card-rate .cnt { font-size: 0.68rem; color: var(--vp-c-text-3); }

.card-acts { display: flex; gap: 0.7rem; margin-top: 0.15rem; }
.pd-link {
  font-size: 0.72rem; border: none; background: none; padding: 0; cursor: pointer;
  color: var(--vp-c-brand-1); text-decoration: none;
}
.pd-link:hover { text-decoration: underline; }

.pd-compare {
  border: 1px solid var(--vp-c-brand-1); border-radius: 10px; padding: 0.6rem 0.75rem;
  margin-bottom: 0.75rem; background: var(--vp-c-brand-soft); overflow-x: auto;
}
.pd-compare-head {
  display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600;
  color: var(--vp-c-brand-1); margin-bottom: 0.35rem;
}
.pd-compare table { border-collapse: collapse; font-size: 0.76rem; width: 100%; }
.pd-compare th, .pd-compare td {
  border: 1px solid var(--vp-c-divider); padding: 3px 8px; text-align: left;
  white-space: nowrap; font-variant-numeric: tabular-nums;
}
.pd-compare th { background: var(--vp-c-bg); }
.pd-k { color: var(--vp-c-text-3); }

.pd-modal {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.35); z-index: 60;
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.pd-panel {
  background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 12px;
  padding: 0.95rem 1.05rem; max-width: 560px; width: 100%; max-height: 82vh; overflow: auto;
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.25);
}
.pd-panel-head { display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.5rem; }
.pd-panel-head b { font-size: 0.95rem; color: var(--vp-c-text-1); }
.pd-panel-head .pd-link { margin-left: auto; }
.pd-specs { border-collapse: collapse; width: 100%; font-size: 0.78rem; }
.pd-specs td { border-bottom: 1px solid var(--vp-c-divider); padding: 3px 6px;
  font-variant-numeric: tabular-nums; }
.pd-offer {
  margin: 0.6rem 0; font-size: 0.76rem; line-height: 1.7;
  color: var(--vp-c-text-2); padding: 0.5rem 0.6rem;
  border-left: 3px solid #a06a00; background: var(--vp-c-bg-soft);
}
</style>
