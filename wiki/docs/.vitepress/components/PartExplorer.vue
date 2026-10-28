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

const props = withDefaults(defineProps<{ lang?: 'zh' | 'en' }>(), { lang: 'zh' })
const en = computed(() => props.lang === 'en')
/** 只翻界面壳；型号与参数值保持原文。 */
const L = computed(() => en.value
  ? { search: 'Search model / brand / type', compare: 'Compare', all: 'All params',
      none: 'No photo yet', count: 'items', sort: 'Sort by' }
  : { search: '搜型号 / 品牌 / 类型', compare: '对比', all: '全部参数',
      none: '暂无产品图', count: '件', sort: '按' })

const all = ref<Part[]>([])
const loading = ref(true)
const fail = ref('')

const q = ref('')
const cat = ref('actuator')
const vendor = ref('')
const sort = ref<string>('tau_peak_Nm')
const order = ref<'desc' | 'asc'>('desc')
const picked = ref<Part[]>([])
const detail = ref<Part | null>(null)

//: 品类表来自 catalog.json（构建时由 data/taxonomy.json 生成）——
//: 这里只留一份「加载失败时的兜底」，不再硬编码全量。
interface Cat {
  v: string
  t: string
  keys: { k: string; label: string; unit?: string }[]
  sorts: { k: string; label: string }[]
}

const FALLBACK_CATS = [
  { v: 'actuator', t: '关节电机' },
  { v: 'controller_high', t: '上位机' },
  { v: 'controller_low', t: '下位机' },
  { v: 'module', t: '其余模块' },
  { v: 'chip', t: '硬件芯片' },
]
const CATS = ref<Cat[]>(FALLBACK_CATS.map(c => ({ ...c, keys: [], sorts: [] })))

//: 排序项按品类来（data/taxonomy.json 的 sorts）。
//: 「按峰值扭矩」对芯片毫无意义 —— 每类该有自己的默认排序。
const FALLBACK_SORTS = [{ k: 'price', label: '价格' }, { k: 'rating', label: '评分' }]

onMounted(async () => {
  try {
    // no-cache = 每次用 ETag 重新验证，不是禁用缓存。
    // 静态站的 catalog.json 会随部署变化，纯强缓存会让读者看到上一版的价格/图片。
    const r = await fetch(withBase('/catalog.json'), { cache: 'no-cache' })
    if (!r.ok) throw new Error(String(r.status))
    const d = await r.json()
    all.value = d.parts
    if (Array.isArray(d.categories) && d.categories.length) {
      CATS.value = d.categories.map((c: any) => ({
        v: c.id, t: c.name, keys: c.keys || [], sorts: c.sorts || [],
      }))
      if (!CATS.value.some(c => c.v === cat.value)) cat.value = CATS.value[0].v
    }
  } catch (e: any) {
    fail.value = `部件库加载失败（${e.message}）`
  } finally {
    loading.value = false
  }
})

/** 换品类时重置筛选与排序。
 *  「按峰值扭矩」对芯片/雷达毫无意义 —— 默认排序应该跟着品类走。 */
function setCat(v: string) {
  cat.value = v
  vendor.value = ''
  q.value = ''
  const m = CATS.value.find(c => c.v === v)
  sort.value = m?.sorts?.[0]?.k || 'price'
}

const catCount = (v: string) => all.value.filter(p => p.category === v).length

/** 当前品类的元数据：卡片显示哪些参数、能按什么排序，都来自这里。 */
const meta = computed(() => CATS.value.find(c => c.v === cat.value))
const catName = computed(() => meta.value?.t || '部件')
const sortOpts = computed(() =>
  (meta.value?.sorts?.length ? meta.value.sorts : FALLBACK_SORTS))
const vendors = computed(() =>
  [...new Set(all.value.filter(p => p.category === cat.value).map(p => p.vendor))].sort())

/** 排序取值器：specs 里的键、或内置的 price / rating。
 *  空值统一返回 null，排序时沉底（缺失就是缺失，不该混进比较）。 */
function sortValue(p: Part, k: string): any {
  if (k === 'price') return p.offer?.price ?? p.price ?? null
  if (k === 'rating') return p.rating?.avg ?? null
  const v = (p as any).specs?.[k]
  return v === undefined || v === '' ? null : v
}

const rows = computed(() => {
  const key = (p: Part) => sortValue(p, sort.value)
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
/** 卡片上的关键参数：完全按品类定义渲染（4–6 个），不再写 if-else 分支。
 *  加品类只需要在 data/taxonomy.json 里写 keys。 */
function chips(p: Part): { k: string; v: string }[] {
  const out: { k: string; v: string }[] = []
  for (const key of meta.value?.keys || []) {
    const raw = sortValue(p, key.k)
    if (raw === null || raw === 0 || raw === '') continue
    if (typeof raw === 'boolean') {
      if (raw) out.push({ k: key.label, v: '支持' })
      continue
    }
    const val = typeof raw === 'number' ? num(raw) : String(raw)
    out.push({ k: key.label, v: `${val}${key.unit || ''}` })
    if (out.length >= 6) break
  }
  return out
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
                @click="setCat(c.v)">
          {{ c.t }}<span class="pd-n">{{ catCount(c.v) || '—' }}</span>
        </button>
      </div>

      <!-- 工具条 -->
      <div class="pd-row">
        <input v-model="q" class="pd-input" :placeholder="L.search" />
        <select v-model="sort" class="pd-sel">
          <option v-for="s in sortOpts" :key="s.k" :value="s.k">按{{ s.label }}</option>
        </select>
        <button class="pd-btn" @click="order = order === 'desc' ? 'asc' : 'desc'">
          {{ order === 'desc' ? '↓ 降序' : '↑ 升序' }}
        </button>
        <span class="pd-sep" />
        <button v-for="v in vendors" :key="v"
                :class="['pd-chip', 'sm', vendor === v ? 'on' : '']"
                @click="vendor = vendor === v ? '' : v">{{ v }}</button>
        <span class="pd-count">{{ rows.length }} {{ L.count }}</span>
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
            <!-- 没图就如实说没图。错图（整机宣传图）比没图更糟，所以不做抽象方块充数 -->
            <span v-else class="ph" :aria-label="`暂无${catName}产品图`">
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"
                   fill="none" stroke="currentColor" stroke-width="1.6"
                   stroke-linecap="round" stroke-linejoin="round">
                <template v-if="p.category === 'camera'">
                  <path d="M3 7h4l2-3h6l2 3h4v12H3z" /><circle cx="12" cy="13" r="3.4" />
                </template>
                <template v-else-if="p.category === 'lidar'">
                  <circle cx="12" cy="12" r="2" />
                  <path d="M12 4a8 8 0 0 1 8 8M12 20a8 8 0 0 1-8-8" />
                  <path d="M12 7.5a4.5 4.5 0 0 1 4.5 4.5" />
                </template>
                <template v-else-if="p.category === 'controller_high' || p.category === 'controller_low'">
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <path d="M7 9h4M7 13h6M16 9v6" />
                </template>
                <template v-else-if="p.category === 'chip'">
                  <rect x="7" y="7" width="10" height="10" rx="1.5" />
                  <path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4" />
                </template>
                <template v-else-if="p.category === 'actuator'">
                  <circle cx="12" cy="12" r="6.5" /><circle cx="12" cy="12" r="2" />
                </template>
                <template v-else>
                  <path d="M3 7h4l2-3h6l2 3h4v12H3z" /><circle cx="12" cy="13" r="3.4" />
                </template>
              </svg>
              <em>{{ L.none }}</em>
            </span>
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
                <!-- 原价与优惠价并列，不划掉原价：优惠要资格，不是人人都能用 -->
                <span class="list">{{ money(p.price) ?? '询价' }}</span>
                <template v-if="p.offer?.price != null">
                  <span class="promo">{{ money(p.offer.price) }}</span>
                </template>
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
              <button class="pd-link" @click="detail = p">{{ L.all }}</button>
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

/* 卡片网格：固定 4 列。auto-fill 在宽屏会排到 6 列，卡片被压得太窄 ——
   参数两列排不下、型号名折行、价格和「优惠需资格」挤成两行。 */
.pd-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
}
@media (max-width: 1180px) { .pd-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 860px)  { .pd-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 540px)  { .pd-grid { grid-template-columns: 1fr; } }
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
  /* 托板高度固定，图片/SVG 都不能撑出边界 —— 否则会压到下面的型号名上 */
  overflow: hidden;
}
.card-img img {
  max-height: 96px; max-width: 86%; object-fit: contain; mix-blend-mode: multiply;
}
html.dark .card-img img { mix-blend-mode: normal; background: #fff; border-radius: 4px; padding: 2px; }
/* 占位图按**高度**约束（不是宽度）：SVG 有 viewBox，给定高度后宽度按比例走，
   在 112px 高的托板里永远不会顶出来。按宽度给百分比会算出 136px 高再溢出。 */
.card-img svg { height: 78px; width: auto; max-width: 88%; display: block; }

/* 缺图的占位：图标 + 一句说明，克制到不抢注意力，但比抽象方块能读懂 */
.ph {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  color: var(--vp-c-text-3);
}
.ph svg { height: 18px; width: auto; max-width: none; opacity: 0.7; }
.ph em { font-size: 0.66rem; font-style: normal; letter-spacing: 0.02em; }
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
.card-price { display: flex; align-items: baseline; gap: 0.35rem; flex-wrap: wrap;
  font-variant-numeric: tabular-nums; }
/* 原价：中性灰，尺寸略小。不做删除线 —— 优惠要资格，原价仍是真实价格 */
.card-price .list { font-size: 0.8rem; color: var(--vp-c-text-2); }
/* 优惠价：琥珀色，最醒目 */
.card-price .promo { font-size: 0.9rem; font-weight: 700; color: #a06a00; }
html.dark .card-price .promo { color: #e0b159; }
.card-price .hint {
  font-size: 0.62rem; color: #a06a00; border: 1px solid currentColor;
  border-radius: 999px; padding: 0 4px; opacity: 0.85;
}
html.dark .card-price .hint { color: #e0b159; }
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
